#pragma once

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12002 {
struct ArmyBindings;
}

namespace xar::game {

enum class ArmySupplyTimingStatus : std::uint8_t {
  unavailable,
  available,
  not_registered,
};

constexpr std::string_view ArmySupplyTimingStatusName(
    ArmySupplyTimingStatus status) noexcept {
  switch (status) {
  case ArmySupplyTimingStatus::available: return "available";
  case ArmySupplyTimingStatus::not_registered: return "not_registered";
  default: return "unavailable";
  }
}

struct ArmySupplyTimingSnapshot {
  ArmySupplyTimingStatus status = ArmySupplyTimingStatus::unavailable;
  bool ready = false;
  std::string_view unavailable_reason{};
  // The low32 raw date and the actual stored signed absolute native day D.
  // D is written by the date stage; the reader does not reconstruct it.
  std::optional<std::int32_t> current_date_raw;
  std::optional<std::int32_t> native_day_index;
  std::optional<std::int32_t> selected_bucket_phase;
  // Observed CArmy* membership, never inferred from its public/native ID.
  std::optional<std::int32_t> observed_army_bucket_phase;
  // CDate64 storage copies and their low32 date operands are kept distinct.
  std::optional<std::int64_t> last_supply_update_date_storage_raw64;
  std::optional<std::int32_t> last_supply_update_date_raw;
  std::optional<std::int64_t> grace_anchor_date_storage_raw64;
  std::optional<std::int32_t> grace_anchor_date_raw;
  std::optional<std::int32_t> loaded_grace_days;
  friend bool operator==(const ArmySupplyTimingSnapshot &,
                         const ArmySupplyTimingSnapshot &) = default;
};

} // namespace xar::game

namespace xar::ck3_12003 {

inline constexpr std::uintptr_t kArmySupplyGraceDaysRva12003 = 0x5C69AA0;

struct ArmySupplyTimingBindings {
  bool enabled = false;
  const std::int32_t *loaded_grace_days = nullptr;
};

ArmySupplyTimingBindings BindArmySupplyTimingImage(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Read on the existing paused owning-thread strength path, after it resolves
// the CArmy full ID and validates its public CUnit backlink. No native action.
game::ArmySupplyTimingSnapshot ReadArmySupplyTiming(
    const ck3_12002::ArmyBindings &army_bindings,
    const ArmySupplyTimingBindings &timing_bindings,
    const void *resolved_army) noexcept;

} // namespace xar::ck3_12003
