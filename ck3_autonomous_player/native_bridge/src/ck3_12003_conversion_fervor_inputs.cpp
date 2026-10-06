#include "xar_bridge/ck3_12003_conversion_fervor_inputs.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion::conversion_fervor {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}

bool Matches(const void *object, std::uint32_t reference) noexcept {
  return object && Load<std::uint32_t>(object, kReferenceIdentityOffset) == reference;
}

Failure ReadOnce(const conversion_gates::Bindings &b, std::uint32_t target,
                 std::uint64_t epoch, Context &out) noexcept {
  out.capture_epoch = epoch;
  out.requested_target_rite_id = target;
  const auto &context = b.state.context;
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(context.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = static_cast<std::uint32_t>(frame.played_character_id);
  if (!frame.clock.paused) return Failure::frame_not_paused;
  auto *actor = ResolveCoreCharacter(context.core, frame.played_character_id);
  if (!actor) return Failure::played_character_unavailable;

  // Read the played actor's actual current Rite -> Faith chain. Realm state
  // religion, conversion knowledge and recent-conversion flags are unrelated
  // to obtaining these two scalar inputs.
  const auto actor_rite_id = Load<std::uint32_t>(actor, kCharacterRiteIdOffset);
  if (actor_rite_id == kAbsentReference) return Failure::actor_rite_unavailable;
  auto *actor_rite = context.character_rite(actor);
  if (!Matches(actor_rite, actor_rite_id)) return Failure::actor_rite_unavailable;
  const auto actor_faith_id = Load<std::uint32_t>(actor_rite, kRiteFaithIdOffset);
  if (actor_faith_id == kAbsentReference) return Failure::actor_faith_unavailable;
  auto *actor_faith = context.rite_faith(actor_rite);
  if (!Matches(actor_faith, actor_faith_id) ||
      context.character_faith(actor) != actor_faith)
    return Failure::actor_faith_unavailable;
  out.actor_faith_id = actor_faith_id;

  // This thin public seam reuses the existing gates' complete-generation
  // target resolver; no second storage traversal is introduced here.
  auto *target_rite = conversion_gates::ResolveConversionTargetRite12002(b, target);
  if (!target_rite) return Failure::target_rite_unavailable;
  const auto target_faith_id = Load<std::uint32_t>(target_rite, kRiteFaithIdOffset);
  if (target_faith_id == kAbsentReference) return Failure::target_faith_unavailable;
  auto *target_faith = context.rite_faith(target_rite);
  if (!Matches(target_faith, target_faith_id)) return Failure::target_faith_unavailable;
  out.target_faith_id = target_faith_id;

  // The getter writes signed Q100000 into caller-owned output. A zero or an
  // identical Faith receiver is a valid observation.
  std::int64_t actor_fervor{}, target_fervor{};
  if (context.faith_fervor(actor_faith, &actor_fervor) != &actor_fervor)
    return Failure::actor_fervor_unavailable;
  if (context.faith_fervor(target_faith, &target_fervor) != &target_fervor)
    return Failure::target_fervor_unavailable;
  out.actor_fervor_raw = actor_fervor;
  out.target_fervor_raw = target_fervor;
  if (ResolveCoreCharacter(context.core, frame.played_character_id) != actor ||
      conversion_gates::ResolveConversionTargetRite12002(b, target) != target_rite)
    return Failure::state_changed;
  out.available = true;
  out.failure = Failure::none;
  return Failure::none;
}

bool Same(const Context &a, const Context &b) noexcept {
  return a.date_raw == b.date_raw &&
      a.played_character_id == b.played_character_id &&
      a.requested_target_rite_id == b.requested_target_rite_id &&
      a.actor_faith_id == b.actor_faith_id &&
      a.target_faith_id == b.target_faith_id &&
      a.actor_fervor_raw == b.actor_fervor_raw &&
      a.target_fervor_raw == b.target_fervor_raw;
}

template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
} // namespace

bool ReadPlayedConversionFervorInputs12003(
    const conversion_gates::Bindings &b, std::uint32_t target,
    std::uint64_t epoch, Context &output) noexcept {
  output = {};
  output.capture_epoch = epoch;
  output.requested_target_rite_id = target;
  const auto &context = b.state.context;
  if (!b.enabled || !context.enabled || !context.core.enabled ||
      !context.character_rite || !context.character_faith || !context.rite_faith ||
      !context.faith_fervor || !b.rite_storage_slot)
    return false;

  Context first{}, second{};
  auto failure = ReadOnce(b, target, epoch, first);
  if (failure == Failure::none) failure = ReadOnce(b, target, epoch, second);
  if (failure == Failure::none && !Same(first, second))
    failure = Failure::state_changed;
  output = std::move(first);
  if (failure != Failure::none) {
    // Retain observed identity/frame fields for the independent child, but
    // publish neither scalar as a usable pair after a failed observation.
    output.available = false;
    output.failure = failure;
    output.actor_fervor_raw.reset();
    output.target_fervor_raw.reset();
    return false;
  }
  return true;
}

const char *ConversionFervorInputsFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::actor_rite_unavailable: return "actor_rite_unavailable";
  case Failure::actor_faith_unavailable: return "actor_faith_unavailable";
  case Failure::target_rite_unavailable: return "target_rite_unavailable";
  case Failure::target_faith_unavailable: return "target_faith_unavailable";
  case Failure::actor_fervor_unavailable: return "actor_fervor_unavailable";
  case Failure::target_fervor_unavailable: return "target_fervor_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}

std::string SerializeConversionFervorInputs12003(const Context &c) {
  return "{\"schema\":\"ck3_12003_conversion_fervor_inputs_v1\",\"read_only\":true,"
      "\"available\":" + std::string(c.available ? "true" : "false") +
      ",\"unavailable_reason\":" +
      (c.available ? "null" :
          '\"' + std::string(ConversionFervorInputsFailureKey(c.failure)) + '\"') +
      ",\"capture_epoch\":" + std::to_string(c.capture_epoch) +
      ",\"date_raw\":" + std::to_string(c.date_raw) +
      ",\"played_character_id\":" + std::to_string(c.played_character_id) +
      ",\"requested_target_rite_id\":" + std::to_string(c.requested_target_rite_id) +
      ",\"actor_faith_id\":" + Number(c.actor_faith_id) +
      ",\"target_faith_id\":" + Number(c.target_faith_id) +
      ",\"actor_fervor_raw\":" + Number(c.actor_fervor_raw) +
      ",\"target_fervor_raw\":" + Number(c.target_fervor_raw) +
      ",\"raw_scale\":100000,\"unit\":\"fervor_points\","
      "\"is_final_conversion_cost\":false,\"is_final_conversion_desire\":false}";
}
} // namespace xar::ck3_12002::religion::conversion_fervor
