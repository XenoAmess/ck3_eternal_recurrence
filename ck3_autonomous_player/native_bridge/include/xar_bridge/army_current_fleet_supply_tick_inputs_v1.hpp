#pragma once
#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {
struct ArmyCurrentFleetSupplyTickInputsV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::string> unavailable_reason;
  std::int32_t scale = 100000;
  std::optional<std::int32_t> subject_army_id;
  std::optional<std::int32_t> subject_carmy_id;
  std::optional<std::int32_t> province_id;
  std::optional<bool> native_fleet_branch_applicable;
  std::optional<std::int32_t> current_native_date_low32;
  std::optional<std::int32_t> fleet_raw_full_id;
  std::optional<std::int32_t> fleet_resolved_full_id;
  std::optional<bool> fleet_used_native_fallback;
  std::optional<std::int32_t> fleet_day_raw;
  std::optional<std::int32_t> loaded_fleet_day_sentinel_raw;
  std::optional<std::uint32_t> terrain_magic_38_raw;
  std::optional<std::uint16_t> terrain_modifier_772_id;
  std::optional<std::int64_t> terrain_modifier_772_raw;
  std::optional<std::int32_t> commander_raw_full_id;
  std::optional<std::int32_t> commander_resolved_full_id;
  std::optional<bool> commander_used_native_fallback;
  std::optional<std::int64_t> loaded_fleet_loss_raw;
  std::optional<std::int64_t> commander_modifier_1a9_raw;
  std::optional<std::int64_t> loaded_divisor_floor_raw;
  std::optional<std::int64_t> loaded_max_loss_raw;
  friend bool operator==(const ArmyCurrentFleetSupplyTickInputsV1 &,
                         const ArmyCurrentFleetSupplyTickInputsV1 &) = default;
};
} // namespace xar::game

namespace xar::ck3_12003 {
// Kept in this dependency-free header so ArmyBindings can own it at its tail
// without including a reader which itself depends on ArmyBindings.
struct CurrentFleetSupplyTickBindings12003 {
  bool enabled = false;
  const std::int64_t *loaded_fleet_loss_raw = nullptr;
  const std::int64_t *loaded_divisor_floor_raw = nullptr;
  const std::int64_t *loaded_max_loss_raw = nullptr;
};
} // namespace xar::ck3_12003
