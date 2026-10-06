#include "xar_bridge/ck3_12002_religion_conversion_rite.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12002::religion_conversion_rite {
namespace {
template <typename T> T Load(const void *object, std::size_t at) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value));
  return value;
}
constexpr std::uint32_t absent = 0xFFFFFFFFU;
void *ResolveRite(const Bindings &b, std::uint32_t id) noexcept {
  if (!b.rite_storage_slot || !*b.rite_storage_slot || id == absent) return nullptr;
  const auto *storage = *b.rite_storage_slot;
  const auto index = id & 0xFFFFFFU;
  if (index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  const auto *slots = Load<const std::byte *>(storage, 0x20);
  if (!slots) return nullptr;
  auto *object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return object && Load<std::uint32_t>(object, 8) == id ? object : nullptr;
}
Failure ReadActor(const Bindings &b, CoreSnapshotPrefix &frame, void *&character) {
  if (!ReadCoreSnapshot(b.core, frame) || !frame.map_ready ||
      !frame.has_played_character || !frame.played_character_alive)
    return Failure::played_character_unavailable;
  if (!frame.clock.paused) return Failure::frame_not_paused;
  character = ResolveCoreCharacter(b.core, frame.played_character_id);
  return character ? Failure::none : Failure::played_character_unavailable;
}
bool SameFrame(const Bindings &b, const CoreSnapshotPrefix &first, void *character) {
  CoreSnapshotPrefix next{};
  return ReadCoreSnapshot(b.core, next) && next.clock.paused && next.map_ready &&
      next.played_character_alive && next.has_played_character &&
      next.clock.date_raw == first.clock.date_raw &&
      next.played_character_id == first.played_character_id &&
      ResolveCoreCharacter(b.core, first.played_character_id) == character;
}
bool HasBindings(const Bindings &b) {
  return b.enabled && b.module_base && b.core.enabled && b.rite_storage_slot &&
      b.validate && b.character_faith && b.faith_rites;
}
std::string Prefix(const char *schema, bool available, Failure failure,
                   std::uint64_t epoch, std::int32_t date, std::int32_t actor) {
  return std::string{"{\"schema\":\""} + schema +
      "\",\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"" +
      kExecutableSha256 + "\",\"read_only\":true,\"available\":" +
      (available ? "true" : "false") + ",\"unavailable_reason\":" +
      (available ? std::string{"null"} : std::string{"\""} + RiteConversionFailureKey(failure) + "\"") +
      ",\"capture_epoch\":" + std::to_string(epoch) +
      ",\"date_raw\":" + std::to_string(date) +
      ",\"played_character_id\":" + std::to_string(actor);
}
const char *Boolean(bool value) { return value ? "true" : "false"; }
} // namespace

Bindings BindRiteConversionImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true; b.module_base = base; b.core = BindCoreImage(base, sha);
  b.rite_storage_slot = reinterpret_cast<void **>(base + kRiteStorageSlotRva);
  b.validate = reinterpret_cast<Validate>(base + kFaithAndRiteValidateRva);
  b.character_faith = reinterpret_cast<ObjectGetter>(base + kCharacterFaithGetterRva);
  b.faith_rites = reinterpret_cast<ContainerGetter>(base + kFaithRitesGetterRva);
  return b;
}
FaithAndRiteConversionCommand MakeReadOnlyConvertRiteValue12002(std::uintptr_t base,
    std::int32_t actor, std::uint32_t target, bool pay) noexcept {
  FaithAndRiteConversionCommand command{};
  command.primary_vtable = base + kFaithAndRitePrimaryVtableRva;
  command.secondary_vtable = base + kFaithAndRiteSecondaryVtableRva;
  command.actor_id = actor; command.target_rite_id = target;
  command.pay_piety = pay ? 1 : 0;
  return command;
}

bool ReadRitePreview12002(const Bindings &b, std::uint64_t epoch,
                         std::uint32_t target_id, Preview &out) noexcept {
  out = {}; out.capture_epoch = epoch; out.target_rite_id = target_id;
  if (!HasBindings(b)) return false;
  CoreSnapshotPrefix frame{}; void *character = nullptr;
  out.failure = ReadActor(b, frame, character);
  if (out.failure != Failure::none) return false;
  out.date_raw = frame.clock.date_raw; out.played_character_id = frame.played_character_id;
  const auto current_id = Load<std::uint32_t>(character, 0xB4);
  auto *current = ResolveRite(b, current_id);
  if (!current) { out.failure = Failure::current_rite_unavailable; return false; }
  auto *target = ResolveRite(b, target_id);
  if (!target) { out.failure = Failure::target_rite_unavailable; return false; }
  out.current_rite_id = current_id;
  out.current_faith_id = Load<std::uint32_t>(current, 0x4B8);
  out.target_faith_id = Load<std::uint32_t>(target, 0x4B8);
  if (out.current_faith_id == absent || out.target_faith_id == absent) {
    out.failure = Failure::faith_unavailable; return false;
  }
  out.same_faith = out.current_faith_id == out.target_faith_id;
  out.different_from_current_rite = current_id != target_id;
  const auto factory = b.read_only_value_factory ? b.read_only_value_factory
                                               : &MakeReadOnlyConvertRiteValue12002;
  auto command = factory(b.module_base,
      frame.played_character_id, target_id, false);
  out.validator_without_payment = b.validate(&command, nullptr);
  command.pay_piety = 1;
  out.validator_with_payment = b.validate(&command, nullptr);
  if (!SameFrame(b, frame, character) || ResolveRite(b, current_id) != current ||
      ResolveRite(b, target_id) != target || Load<std::uint32_t>(character, 0xB4) != current_id) {
    out.failure = Failure::state_changed; return false;
  }
  out.available = true; out.failure = Failure::none; return true;
}

bool ReadCurrentFaithRites12002(const Bindings &b, std::uint64_t epoch,
                               FaithRites &out) noexcept {
  out = {}; out.capture_epoch = epoch;
  if (!HasBindings(b)) return false;
  CoreSnapshotPrefix frame{}; void *character = nullptr;
  out.failure = ReadActor(b, frame, character);
  if (out.failure != Failure::none) return false;
  out.date_raw = frame.clock.date_raw; out.played_character_id = frame.played_character_id;
  const auto current_id = Load<std::uint32_t>(character, 0xB4);
  auto *rite = ResolveRite(b, current_id);
  if (!rite) { out.failure = Failure::current_rite_unavailable; return false; }
  const auto faith_id = Load<std::uint32_t>(rite, 0x4B8);
  auto *faith = b.character_faith(character);
  if (!faith || faith_id == absent || Load<std::uint32_t>(faith, 8) != faith_id) {
    out.failure = Failure::faith_unavailable; return false;
  }
  const auto *container = b.faith_rites(faith);
  if (!container) { out.failure = Failure::rites_unavailable; return false; }
  const auto count = Load<std::int32_t>(container, 0xC);
  const auto capacity = Load<std::int32_t>(container, 8);
  const auto *ids = Load<const std::uint32_t *>(container, 0);
  if (count < 0 || count > capacity || (count && !ids)) {
    out.failure = Failure::rites_unavailable; return false;
  }
  out.faith_id = faith_id;
  out.rite_ids.reserve(static_cast<std::size_t>(count));
  for (std::int32_t i = 0; i < count; ++i) {
    auto *candidate = ResolveRite(b, ids[i]);
    if (!candidate || Load<std::uint32_t>(candidate, 0x4B8) != faith_id) {
      out.rite_ids.clear(); out.failure = Failure::rites_unavailable; return false;
    }
    out.rite_ids.push_back(ids[i]);
  }
  if (!SameFrame(b, frame, character) || Load<std::uint32_t>(character, 0xB4) != current_id) {
    out.rite_ids.clear(); out.failure = Failure::state_changed; return false;
  }
  out.available = true; out.failure = Failure::none; return true;
}

const char *RiteConversionFailureKey(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::current_rite_unavailable: return "current_rite_unavailable";
  case Failure::target_rite_unavailable: return "target_rite_unavailable";
  case Failure::faith_unavailable: return "faith_unavailable";
  case Failure::rites_unavailable: return "rites_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}
std::string SerializeRitePreview12002(const Preview &p) {
  return Prefix("ck3_12002_religion_conversion_rite_preview_v1", p.available,
      p.failure, p.capture_epoch, p.date_raw, p.played_character_id) +
      ",\"current_rite_id\":" + std::to_string(p.current_rite_id) +
      ",\"target_rite_id\":" + std::to_string(p.target_rite_id) +
      ",\"current_faith_id\":" + std::to_string(p.current_faith_id) +
      ",\"target_faith_id\":" + std::to_string(p.target_faith_id) +
      ",\"same_faith\":" + Boolean(p.same_faith) +
      ",\"different_from_current_rite\":" + Boolean(p.different_from_current_rite) +
      ",\"validator_without_payment\":" + (p.available ? Boolean(p.validator_without_payment) : "null") +
      ",\"validator_with_payment\":" + (p.available ? Boolean(p.validator_with_payment) : "null") + "}";
}
std::string SerializeCurrentFaithRites12002(const FaithRites &p) {
  auto json = Prefix("ck3_12002_current_faith_rites_v1", p.available, p.failure,
      p.capture_epoch, p.date_raw, p.played_character_id) +
      ",\"faith_id\":" + std::to_string(p.faith_id) + ",\"rite_ids\":[";
  for (std::size_t i = 0; i < p.rite_ids.size(); ++i) {
    if (i) json += ',';
    json += std::to_string(p.rite_ids[i]);
  }
  return json + "],\"membership_is_legality\":false}";
}
} // namespace xar::ck3_12002::religion_conversion_rite
