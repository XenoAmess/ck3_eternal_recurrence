#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace xar::game {

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

  friend bool operator==(const ArmyCapturedTargetLandSupplyInputsV1 &,
                         const ArmyCapturedTargetLandSupplyInputsV1 &) = default;
};

} // namespace xar::game
