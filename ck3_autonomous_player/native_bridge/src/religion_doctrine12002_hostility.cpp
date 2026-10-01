#include "xar_bridge/religion_doctrine12002_hostility.hpp"

#include <cstring>

namespace xar::ck3_12002::religion::doctrine12002 {
namespace {
template <typename T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
bool Matches(const void *object, std::uint32_t id) noexcept {
  return object && id != kAbsentReference &&
      Load<std::uint32_t>(object, kReferenceIdentityOffset) == id;
}
bool RiteMatches(const void *object, std::uint32_t id) noexcept {
  return Matches(object, id) && Load<std::uint32_t>(object, 0x0C) == kHostilityRiteTypeTag;
}
void *ResolveRite(const HostilityBindings &b, std::uint32_t id) noexcept {
  if (id == kAbsentReference || !b.rite_storage_slot || !*b.rite_storage_slot) return nullptr;
  const auto *storage = *b.rite_storage_slot;
  const auto index = id & 0xFFFFFFU;
  const auto count = Load<std::uint32_t>(storage, 0x2C);
  if (index >= count) return nullptr;
  const auto *slots = Load<const std::byte *>(storage, 0x20);
  if (!slots) return nullptr;
  auto *object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return RiteMatches(object, id) ? object : nullptr;
}
struct PairObjects {
  void *rite = nullptr, *faith = nullptr, *religion = nullptr, *main_rite = nullptr;
  std::uint32_t faith_id = kAbsentReference, religion_id = kAbsentReference;
  std::uint32_t main_rite_id = kAbsentReference;
};
HostilityFailure ReadObjects(const HostilityBindings &b, void *rite, PairObjects &out) {
  out.rite = rite;
  out.faith_id = Load<std::uint32_t>(rite, kRiteFaithIdOffset);
  out.faith = b.context.rite_faith(rite);
  if (!Matches(out.faith, out.faith_id)) return HostilityFailure::faith_unavailable;
  out.religion_id = Load<std::uint32_t>(out.faith, kFaithReligionIdOffset);
  out.religion = b.context.faith_religion(out.faith);
  if (!Matches(out.religion, out.religion_id)) return HostilityFailure::religion_unavailable;
  out.main_rite_id = Load<std::uint32_t>(out.faith, kFaithMainRiteIdOffset);
  out.main_rite = b.context.faith_main_rite(out.faith);
  if (!RiteMatches(out.main_rite, out.main_rite_id)) return HostilityFailure::main_rite_unavailable;
  return HostilityFailure::none;
}
HostilityFailure ReadOnce(const HostilityBindings &b, std::uint32_t target_id,
                         std::uint64_t epoch, HostilityObservation &out) {
  CoreSnapshotPrefix frame{};
  if (!ReadCoreSnapshot(b.context.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return HostilityFailure::played_character_unavailable;
  if (!frame.clock.paused) return HostilityFailure::frame_not_paused;
  auto *character = ResolveCoreCharacter(b.context.core, frame.played_character_id);
  if (!character) return HostilityFailure::played_character_unavailable;
  const auto actor_id = Load<std::uint32_t>(character, kCharacterRiteIdOffset);
  auto *actor_rite = b.context.character_rite(character);
  if (!RiteMatches(actor_rite, actor_id)) return HostilityFailure::actor_rite_unavailable;
  auto *target_rite = ResolveRite(b, target_id);
  if (!target_rite) return HostilityFailure::target_rite_unavailable;
  PairObjects actor{}, target{};
  auto failure = ReadObjects(b, actor_rite, actor);
  if (failure != HostilityFailure::none) return failure;
  failure = ReadObjects(b, target_rite, target);
  if (failure != HostilityFailure::none) return failure;
  if (b.context.character_faith(character) != actor.faith)
    return HostilityFailure::faith_unavailable;
  const auto forward_rite = b.rite_hostility(static_cast<std::byte *>(actor.rite) +
      kHostilityRiteComponentOffset, actor.rite, target.rite);
  const auto reverse_rite = b.rite_hostility(static_cast<std::byte *>(target.rite) +
      kHostilityRiteComponentOffset, target.rite, actor.rite);
  const auto forward_faith = b.faith_hostility(actor.faith, target.faith, false);
  const auto reverse_faith = b.faith_hostility(target.faith, actor.faith, false);
  if (forward_rite > 3 || reverse_rite > 3 || forward_faith > 3 || reverse_faith > 3)
    return HostilityFailure::native_level_unavailable;
  out.capture_epoch = epoch;
  out.date_raw = frame.clock.date_raw;
  out.played_character_id = frame.played_character_id;
  out.actor_rite_id = actor_id; out.target_rite_id = target_id;
  out.actor_faith_id = actor.faith_id; out.target_faith_id = target.faith_id;
  out.actor_religion_id = actor.religion_id; out.target_religion_id = target.religion_id;
  out.actor_main_rite_id = actor.main_rite_id; out.target_main_rite_id = target.main_rite_id;
  out.actor_rite_towards_target = static_cast<HostilityLevel>(forward_rite);
  out.target_rite_towards_actor = static_cast<HostilityLevel>(reverse_rite);
  out.actor_faith_towards_target = static_cast<HostilityLevel>(forward_faith);
  out.target_faith_towards_actor = static_cast<HostilityLevel>(reverse_faith);
  out.same_faith = actor.faith_id == target.faith_id;
  out.same_religion = actor.religion_id == target.religion_id;
  out.available = true; out.failure = HostilityFailure::none;
  return HostilityFailure::none;
}
bool Same(const HostilityObservation &a, const HostilityObservation &b) {
  return a.date_raw == b.date_raw && a.played_character_id == b.played_character_id &&
      a.actor_rite_id == b.actor_rite_id && a.target_rite_id == b.target_rite_id &&
      a.actor_faith_id == b.actor_faith_id && a.target_faith_id == b.target_faith_id &&
      a.actor_religion_id == b.actor_religion_id && a.target_religion_id == b.target_religion_id &&
      a.actor_main_rite_id == b.actor_main_rite_id && a.target_main_rite_id == b.target_main_rite_id &&
      a.actor_rite_towards_target == b.actor_rite_towards_target &&
      a.target_rite_towards_actor == b.target_rite_towards_actor &&
      a.actor_faith_towards_target == b.actor_faith_towards_target &&
      a.target_faith_towards_actor == b.target_faith_towards_actor;
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
std::string LevelNumber(const std::optional<HostilityLevel> &value) {
  return value ? std::to_string(static_cast<std::uint8_t>(*value)) : "null";
}
std::string LevelText(const std::optional<HostilityLevel> &value) {
  return value ? '"' + std::string(HostilityLevelKey(*value)) + '"' : "null";
}
std::string Boolean(const std::optional<bool> &value) {
  return value ? (*value ? "true" : "false") : "null";
}
} // namespace

HostilityBindings BindHostilityImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  HostilityBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.context = BindReligionContextImage12002(base, sha);
  b.rite_storage_slot = reinterpret_cast<void **>(base + kHostilityRiteStorageSlotRva);
  b.rite_hostility = reinterpret_cast<RiteHostilityGetter>(base + kHostilityRiteFinalRva);
  b.faith_hostility = reinterpret_cast<FaithHostilityGetter>(base + kHostilityFaithFinalRva);
  return b;
}
bool ReadPlayedHostilityTowardsRite12002(const HostilityBindings &b, std::uint32_t target,
                                        std::uint64_t epoch, HostilityObservation &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  if (!b.enabled || !b.context.enabled || !b.context.core.enabled ||
      !b.context.character_rite || !b.context.character_faith || !b.context.rite_faith ||
      !b.context.faith_religion || !b.context.faith_main_rite || !b.rite_storage_slot ||
      !b.rite_hostility || !b.faith_hostility) return false;
  HostilityObservation first{}, second{};
  auto failure = ReadOnce(b, target, epoch, first);
  if (failure == HostilityFailure::none) failure = ReadOnce(b, target, epoch, second);
  if (failure == HostilityFailure::none && !Same(first, second)) failure = HostilityFailure::state_changed;
  if (failure != HostilityFailure::none) { out.failure = failure; return false; }
  out = std::move(first); return true;
}
const char *HostilityLevelKey(HostilityLevel level) noexcept {
  switch (level) {
  case HostilityLevel::righteous: return "righteous";
  case HostilityLevel::astray: return "astray";
  case HostilityLevel::hostile: return "hostile";
  case HostilityLevel::evil: return "evil";
  }
  return "unavailable";
}
const char *HostilityFailureKey(HostilityFailure failure) noexcept {
  switch (failure) {
  case HostilityFailure::none: return "none";
  case HostilityFailure::bindings_unavailable: return "bindings_unavailable";
  case HostilityFailure::played_character_unavailable: return "played_character_unavailable";
  case HostilityFailure::frame_not_paused: return "frame_not_paused";
  case HostilityFailure::actor_rite_unavailable: return "actor_rite_unavailable";
  case HostilityFailure::target_rite_unavailable: return "target_rite_unavailable";
  case HostilityFailure::faith_unavailable: return "faith_unavailable";
  case HostilityFailure::religion_unavailable: return "religion_unavailable";
  case HostilityFailure::main_rite_unavailable: return "main_rite_unavailable";
  case HostilityFailure::native_level_unavailable: return "native_level_unavailable";
  case HostilityFailure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializeHostilityObservation12002(const HostilityObservation &o) {
  return "{\"schema\":\"ck3_12002_religion_hostility_v1\",\"game_version\":\"1.20.0.2\","
      "\"executable_sha256\":\"" + std::string(kExecutableSha256) +
      "\",\"available\":" + (o.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (o.available ? "null" : '"' + std::string(HostilityFailureKey(o.failure)) + '"') +
      ",\"capture_epoch\":" + std::to_string(o.capture_epoch) +
      ",\"date_raw\":" + std::to_string(o.date_raw) +
      ",\"played_character_id\":" + std::to_string(o.played_character_id) +
      ",\"actor_rite_id\":" + Number(o.actor_rite_id) + ",\"target_rite_id\":" + Number(o.target_rite_id) +
      ",\"actor_faith_id\":" + Number(o.actor_faith_id) + ",\"target_faith_id\":" + Number(o.target_faith_id) +
      ",\"actor_religion_id\":" + Number(o.actor_religion_id) + ",\"target_religion_id\":" + Number(o.target_religion_id) +
      ",\"actor_main_rite_id\":" + Number(o.actor_main_rite_id) + ",\"target_main_rite_id\":" + Number(o.target_main_rite_id) +
      ",\"actor_rite_towards_target\":" + LevelNumber(o.actor_rite_towards_target) +
      ",\"actor_rite_towards_target_key\":" + LevelText(o.actor_rite_towards_target) +
      ",\"target_rite_towards_actor\":" + LevelNumber(o.target_rite_towards_actor) +
      ",\"target_rite_towards_actor_key\":" + LevelText(o.target_rite_towards_actor) +
      ",\"actor_faith_towards_target\":" + LevelNumber(o.actor_faith_towards_target) +
      ",\"actor_faith_towards_target_key\":" + LevelText(o.actor_faith_towards_target) +
      ",\"target_faith_towards_actor\":" + LevelNumber(o.target_faith_towards_actor) +
      ",\"target_faith_towards_actor_key\":" + LevelText(o.target_faith_towards_actor) +
      ",\"same_faith\":" + Boolean(o.same_faith) + ",\"same_religion\":" + Boolean(o.same_religion) + '}';
}
} // namespace xar::ck3_12002::religion::doctrine12002
