#include "xar_bridge/ck3_12003_army_supply_timing.hpp"

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <cstddef>
#include <cstring>

namespace xar::ck3_12003 {
namespace {

template <class T> T Load(const void *object, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof value);
  return value;
}

// Same native storage capacity bound used by the existing army reader.
constexpr std::int32_t kMaximumCapacity = 1'000'000;
constexpr std::size_t kArmyManagerSecondaryOffset = 0x2A548;
constexpr std::size_t kBucketOffset = 0x190;
constexpr std::size_t kBucketStride = 0x18;
constexpr std::int32_t kBucketCount = 30;

} // namespace

ArmySupplyTimingBindings BindArmySupplyTimingImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ArmySupplyTimingBindings result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.loaded_grace_days = reinterpret_cast<const std::int32_t *>(
      image_base + kArmySupplyGraceDaysRva12003);
  return result;
}

game::ArmySupplyTimingSnapshot ReadArmySupplyTiming(
    const ck3_12002::ArmyBindings &army_bindings,
    const ArmySupplyTimingBindings &timing_bindings,
    const void *resolved_army) noexcept {
  game::ArmySupplyTimingSnapshot result{};
  if (!army_bindings.enabled || !timing_bindings.enabled ||
      timing_bindings.loaded_grace_days == nullptr) {
    result.unavailable_reason = "native_supply_timing_bindings_unavailable";
    return result;
  }
  if (resolved_army == nullptr) {
    result.unavailable_reason = "native_carmy_not_found";
    return result;
  }
  if (army_bindings.game_state_slot == nullptr ||
      *army_bindings.game_state_slot == nullptr) {
    result.unavailable_reason = "game_state_unavailable";
    return result;
  }
  const void *const game_state = *army_bindings.game_state_slot;
  result.current_date_raw = Load<std::int32_t>(game_state, 0x08);
  const auto native_day = Load<std::int32_t>(game_state, 0x9C);
  result.native_day_index = native_day;
  result.selected_bucket_phase = static_cast<std::int32_t>(
      static_cast<std::uint32_t>(native_day) %
      static_cast<std::uint32_t>(kBucketCount));
  result.last_supply_update_date_storage_raw64 =
      Load<std::int64_t>(resolved_army, 0x188);
  result.last_supply_update_date_raw =
      Load<std::int32_t>(resolved_army, 0x188);
  result.grace_anchor_date_storage_raw64 =
      Load<std::int64_t>(resolved_army, 0x190);
  result.grace_anchor_date_raw = Load<std::int32_t>(resolved_army, 0x190);
  result.loaded_grace_days = *timing_bindings.loaded_grace_days;

  const void *const game_data = Load<const void *>(game_state, 0xA0);
  if (game_data == nullptr) {
    result.unavailable_reason = "game_data_unavailable";
    return result;
  }
  const auto *const manager = static_cast<const std::byte *>(game_data) +
                             kArmyManagerSecondaryOffset;
  for (std::int32_t phase = 0; phase < kBucketCount; ++phase) {
    const auto *const bucket = manager + kBucketOffset +
        static_cast<std::size_t>(phase) * kBucketStride;
    const void *const data = Load<const void *>(bucket, 0);
    const auto capacity = Load<std::int32_t>(bucket, 0x08);
    const auto count = Load<std::int32_t>(bucket, 0x0C);
    if (capacity < 0 || capacity > kMaximumCapacity || count < 0 ||
        count > capacity || (count > 0 && data == nullptr)) {
      result.unavailable_reason = "supply_update_bucket_header_invalid";
      return result;
    }
    for (std::int32_t index = 0; index < count; ++index) {
      if (Load<const void *>(data, static_cast<std::size_t>(index) *
                                 sizeof(void *)) == resolved_army) {
        result.observed_army_bucket_phase = phase;
        result.status = game::ArmySupplyTimingStatus::available;
        result.ready = true;
        return result;
      }
    }
  }
  // A complete readable scan with no matching pointer is an observed absence.
  // It preserves the clock/date/grace operands and does not invent an ID phase.
  result.status = game::ArmySupplyTimingStatus::not_registered;
  result.ready = true;
  return result;
}

} // namespace xar::ck3_12003
