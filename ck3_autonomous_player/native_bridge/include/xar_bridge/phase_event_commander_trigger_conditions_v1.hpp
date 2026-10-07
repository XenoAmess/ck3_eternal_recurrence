#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
struct PhaseEventCommanderTriggerConditionV1 {
  std::uint32_t loaded_row_index = 0;
  std::optional<bool> role_compatible, native_trigger_valid, role_and_trigger_valid;
  std::string unavailable_reason;
  friend bool operator==(const PhaseEventCommanderTriggerConditionV1 &,
                         const PhaseEventCommanderTriggerConditionV1 &) = default;
};
struct PhaseEventCommanderTriggerOccurrenceV1 {
  std::uint32_t occurrence_index = 0, character_id = 0;
  std::int32_t source_public_cunit_id = -1;
  std::optional<std::int32_t> source_native_carmy_id;
  std::string encounter_role;
  std::uint32_t requested_role_raw = 0;
  std::optional<std::uint32_t> actual_combat_full_id_raw, actual_side_index;
  bool current_commander_context_ready = false;
  std::optional<std::int32_t> loaded_named_side_key_raw;
  std::vector<PhaseEventCommanderTriggerConditionV1> conditions;
  std::uint32_t role_compatible_count = 0, evaluated_count = 0, admitted_count = 0, unknown_count = 0;
  bool role_trigger_observation_ready = false;
  std::string status = "unavailable", unavailable_reason;
  friend bool operator==(const PhaseEventCommanderTriggerOccurrenceV1 &,
                         const PhaseEventCommanderTriggerOccurrenceV1 &) = default;
};
struct PhaseEventCommanderTriggerConditionsV1 {
  std::string status = "unavailable", unavailable_reason;
  std::string source_ck3_sha256 =
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  bool trigger_source_closed = false;
  bool native_role_and_trigger_evaluation_observed = false;
  std::vector<PhaseEventCommanderTriggerOccurrenceV1> occurrences;
  friend bool operator==(const PhaseEventCommanderTriggerConditionsV1 &,
                         const PhaseEventCommanderTriggerConditionsV1 &) = default;
};
} // namespace xar::game
