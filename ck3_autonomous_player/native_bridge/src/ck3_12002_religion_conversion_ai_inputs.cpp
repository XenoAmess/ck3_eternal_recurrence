#include "xar_bridge/ck3_12002_religion_conversion_ai_inputs.hpp"

#include <cstring>

namespace xar::ck3_12002::religion_conversion_ai_inputs {
namespace {
template <typename T> T Load(const void *object, std::size_t at) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + at, sizeof(value));
  return value;
}
void *ResolveRite(const Bindings &b, std::uint32_t id) noexcept {
  if (!b.rite_storage_slot || !*b.rite_storage_slot || id == 0xFFFFFFFFU) return nullptr;
  const auto *storage = *b.rite_storage_slot;
  const auto index = id & 0xFFFFFFU;
  if (index >= Load<std::uint32_t>(storage, 0x2C)) return nullptr;
  const auto *slots = Load<const std::byte *>(storage, 0x20);
  if (!slots) return nullptr;
  auto *object = Load<void *>(slots, static_cast<std::size_t>(index) * 0x10 + 8);
  return object && Load<std::uint32_t>(object, kRiteIdentityOffset) == id ? object : nullptr;
}
template <typename T> std::string Number(const std::optional<T> &value) {
  return value ? std::to_string(*value) : "null";
}
} // namespace

Bindings BindConversionAIInputsImage12002(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.core = BindCoreImage(base, sha);
  b.rite_storage_slot = reinterpret_cast<void **>(base + kRiteStorageSlotRva);
  b.base_fulfillment = reinterpret_cast<BaseFulfillment>(base + kRiteBaseFulfillmentRva);
  return b;
}

bool ReadExpectedRiteFulfillment12002(const Bindings &b, std::uint64_t epoch,
    std::uint32_t target_id, FulfillmentInput &out) noexcept {
  out = {}; out.capture_epoch = epoch; out.target_rite_id = target_id;
  if (!b.enabled || !b.core.enabled || !b.rite_storage_slot || !b.base_fulfillment) return false;
  CoreSnapshotPrefix first{};
  if (!ReadCoreSnapshot(b.core, first) || !first.map_ready ||
      !first.has_played_character || !first.played_character_alive) {
    out.failure = Failure::played_character_unavailable; return false;
  }
  out.date_raw = first.clock.date_raw; out.played_character_id = first.played_character_id;
  if (!first.clock.paused) { out.failure = Failure::frame_not_paused; return false; }
  auto *actor = ResolveCoreCharacter(b.core, first.played_character_id);
  if (!actor) { out.failure = Failure::played_character_unavailable; return false; }
  const auto current_id = Load<std::uint32_t>(actor, kCharacterRiteOffset);
  auto *current = ResolveRite(b, current_id);
  if (!current) { out.failure = Failure::current_rite_unavailable; return false; }
  out.current_rite_id = current_id;
  auto *target = ResolveRite(b, target_id);
  if (!target) { out.failure = Failure::target_rite_unavailable; return false; }
  std::int64_t target_base{}, current_base{};
  // Same order and signatures as expected_rite_fulfillment_change's evaluator.
  if (b.base_fulfillment(&target_base, actor, target) != &target_base ||
      b.base_fulfillment(&current_base, actor, current) != &current_base) {
    out.failure = Failure::base_fulfillment_unavailable; return false;
  }
  CoreSnapshotPrefix after{};
  if (!ReadCoreSnapshot(b.core, after) || !after.clock.paused || !after.map_ready ||
      !after.has_played_character || !after.played_character_alive ||
      after.clock.date_raw != first.clock.date_raw ||
      after.played_character_id != first.played_character_id ||
      ResolveCoreCharacter(b.core, first.played_character_id) != actor ||
      Load<std::uint32_t>(actor, kCharacterRiteOffset) != current_id ||
      ResolveRite(b, current_id) != current || ResolveRite(b, target_id) != target) {
    out.failure = Failure::state_changed; return false;
  }
  out.current_rite_base_raw = current_base;
  out.target_rite_base_raw = target_base;
  // The exact native function clamps each base to the frozen -100..100 range.
  out.expected_base_change_raw = target_base - current_base;
  out.available = true; out.failure = Failure::none; return true;
}

const char *ConversionAIInputsFailureKey(Failure f) noexcept {
  switch (f) {
  case Failure::none: return "none";
  case Failure::bindings_unavailable: return "bindings_unavailable";
  case Failure::played_character_unavailable: return "played_character_unavailable";
  case Failure::frame_not_paused: return "frame_not_paused";
  case Failure::current_rite_unavailable: return "current_rite_unavailable";
  case Failure::target_rite_unavailable: return "target_rite_unavailable";
  case Failure::base_fulfillment_unavailable: return "base_fulfillment_unavailable";
  case Failure::state_changed: return "state_changed";
  }
  return "bindings_unavailable";
}

std::string SerializeExpectedRiteFulfillment12002(const FulfillmentInput &v) {
  return std::string{"{\"schema\":\"ck3_12002_expected_rite_base_fulfillment_v1\","}
      + "\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"" + kExecutableSha256 +
      "\",\"read_only\":true,\"available\":" + (v.available ? "true" : "false") +
      ",\"unavailable_reason\":" + (v.available ? std::string{"null"} :
          std::string{"\""} + ConversionAIInputsFailureKey(v.failure) + "\"") +
      ",\"capture_epoch\":" + std::to_string(v.capture_epoch) +
      ",\"date_raw\":" + std::to_string(v.date_raw) +
      ",\"played_character_id\":" + std::to_string(v.played_character_id) +
      ",\"current_rite_id\":" + Number(v.current_rite_id) +
      ",\"target_rite_id\":" + std::to_string(v.target_rite_id) +
      ",\"current_rite_base_raw\":" + Number(v.current_rite_base_raw) +
      ",\"target_rite_base_raw\":" + Number(v.target_rite_base_raw) +
      ",\"expected_base_change_raw\":" + Number(v.expected_base_change_raw) +
      ",\"raw_scale\":100000,\"is_current_fulfillment\":false,"
      "\"is_observed_conversion_gain\":false,\"is_final_ai_desire\":false}";
}
} // namespace xar::ck3_12002::religion_conversion_ai_inputs
