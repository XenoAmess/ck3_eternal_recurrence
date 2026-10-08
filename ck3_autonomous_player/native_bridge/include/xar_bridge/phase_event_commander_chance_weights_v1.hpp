#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
struct PhaseEventCommanderChanceConditionV1 {
  std::uint32_t loaded_row_index = 0;
  std::optional<bool> role_and_trigger_valid;
  std::optional<std::int64_t> chance_raw;
  std::optional<std::int32_t> selection_weight_raw;
  std::string unavailable_reason;
  std::optional<std::uint32_t> effect_empty_operand_raw;
  std::optional<bool> native_effect_empty;
  std::string effect_emptiness_unavailable_reason;
  friend bool operator==(const PhaseEventCommanderChanceConditionV1 &,
                         const PhaseEventCommanderChanceConditionV1 &) = default;
};
struct PhaseEventCommanderChanceOccurrenceV1 {
  std::uint32_t occurrence_index = 0, character_id = 0;
  std::int32_t source_public_cunit_id = -1;
  std::optional<std::int32_t> source_native_carmy_id;
  std::string encounter_role;
  std::optional<std::uint32_t> actual_combat_full_id_raw, actual_side_index;
  bool current_commander_context_ready = false;
  std::optional<std::int32_t> loaded_named_side_key_raw;
  std::vector<PhaseEventCommanderChanceConditionV1> conditions;
  std::uint32_t admitted_count = 0, evaluated_count = 0, not_admitted_count = 0, unknown_count = 0;
  bool chance_weight_observation_ready = false;
  std::string status = "unavailable", unavailable_reason;
  friend bool operator==(const PhaseEventCommanderChanceOccurrenceV1 &,
                         const PhaseEventCommanderChanceOccurrenceV1 &) = default;
};
struct PhaseEventCommanderChanceWeightsV1 {
  std::string status = "unavailable", unavailable_reason;
  std::string source_ck3_sha256 =
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  bool chance_source_closed = false, native_chance_evaluation_observed = false;
  // Omitted by earlier software factories/frames. This qualification is
  // independent of the existing numerical observation and its readiness.
  std::optional<bool> effect_emptiness_source_closed;
  std::vector<PhaseEventCommanderChanceOccurrenceV1> occurrences;
  friend bool operator==(const PhaseEventCommanderChanceWeightsV1 &,
                         const PhaseEventCommanderChanceWeightsV1 &) = default;
};
} // namespace xar::game
