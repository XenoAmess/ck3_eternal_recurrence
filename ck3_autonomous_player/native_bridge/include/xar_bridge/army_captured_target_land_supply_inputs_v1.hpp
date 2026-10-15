#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {

// Optional .4 operands, observed from the selected Army commander, independent
// of its current sea/land branch. No target monthly-rate getter is invoked.
struct ArmyTargetLossAdjustmentOperandsV1 {
  std::string status = "unavailable";
  bool observation_ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::int32_t> commander_raw_full_id;
  std::optional<std::int32_t> commander_resolved_full_id;
  std::optional<bool> commander_used_native_fallback;
  std::optional<std::int64_t> commander_modifier_1a9_raw;
  std::optional<std::int64_t> loaded_excess_slope_raw;
  std::optional<std::int64_t> loaded_min_loss_raw;
  std::optional<std::int64_t> loaded_max_loss_raw;
  std::optional<std::int64_t> loaded_divisor_floor_raw;
  friend bool operator==(const ArmyTargetLossAdjustmentOperandsV1 &,
                         const ArmyTargetLossAdjustmentOperandsV1 &) = default;
};

// Current numerical context of an explicitly selected target Province. This
// does not assert that the subject is on land or that movement has completed.
struct ArmyCapturedTargetLandSupplyInputsV1 {
  std::string status = "unavailable";
  bool current_inputs_ready = false;
  std::optional<std::string> unavailable_reason;
  std::optional<std::int32_t> subject_army_id;
  std::optional<std::int32_t> subject_carmy_id;
  std::optional<std::int32_t> owner_character_id;
  std::optional<std::int32_t> province_id;
  bool province_component_observation_ready = false;
  std::optional<std::string> province_component_unavailable_reason;
  std::optional<bool> native_province_component_applicable;
  std::optional<std::int64_t> province_component_raw;
  bool resupply_observation_ready = false;
  std::optional<std::string> resupply_unavailable_reason;
  std::optional<bool> native_resupply_eligible;
  std::optional<std::int64_t> loaded_gain_raw;

  std::optional<ArmyTargetLossAdjustmentOperandsV1> loss_adjustment_operands_v1;

  friend bool operator==(const ArmyCapturedTargetLandSupplyInputsV1 &,
                         const ArmyCapturedTargetLandSupplyInputsV1 &) = default;
};

} // namespace xar::game
