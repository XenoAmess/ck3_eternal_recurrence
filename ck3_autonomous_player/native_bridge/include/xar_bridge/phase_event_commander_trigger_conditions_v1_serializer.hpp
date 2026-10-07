#pragma once

#include "xar_bridge/phase_event_commander_trigger_conditions_v1.hpp"
#include "xar_bridge/phase_event_commander_side_identity_v1_serializer.hpp"

namespace xar::game {
inline void AppendPhaseEventCommanderTriggerConditionsV1(
    std::string &out, const PhaseEventCommanderTriggerConditionsV1 &value) {
  out += "{\"schema_version\":1,\"scope\":\"v2_current_physical_side_commander_loaded_role_trigger_condition\",\"status\":";
  AppendPhaseRiteStringV1(out, value.status);
  out += ",\"source_ck3_sha256\":"; AppendPhaseRiteStringV1(out, value.source_ck3_sha256);
  out += ",\"trigger_source_closed\":"; out += value.trigger_source_closed ? "true" : "false";
  out += ",\"native_role_and_trigger_evaluation_observed\":";
  out += value.native_role_and_trigger_evaluation_observed ? "true" : "false";
  out += ",\"complete_phase_effects_ready\":false,\"unavailable_reason\":";
  AppendCommanderSideReasonV1(out, value.unavailable_reason);
  out += ",\"occurrences\":[";
  for (std::size_t index = 0; index < value.occurrences.size(); ++index) {
    if (index) out += ',';
    const auto &row = value.occurrences[index];
    out += "{\"occurrence_index\":" + std::to_string(row.occurrence_index);
    out += ",\"character_id\":" + std::to_string(row.character_id);
    out += ",\"source_public_cunit_id\":" + std::to_string(row.source_public_cunit_id);
    out += ",\"source_native_carmy_id\":"; AppendCommanderSideIntegerV1(out, row.source_native_carmy_id);
    out += ",\"encounter_role\":"; AppendPhaseRiteStringV1(out, row.encounter_role);
    out += ",\"requested_role_raw\":0,\"actual_combat_full_id_raw\":";
    AppendCommanderSideIntegerV1(out, row.actual_combat_full_id_raw);
    out += ",\"actual_side_index\":"; AppendCommanderSideIntegerV1(out, row.actual_side_index);
    out += ",\"current_commander_context_ready\":"; out += row.current_commander_context_ready ? "true" : "false";
    out += ",\"loaded_named_side_key_raw\":"; AppendCommanderSideIntegerV1(out, row.loaded_named_side_key_raw);
    out += ",\"conditions\":[";
    for (std::size_t entry = 0; entry < row.conditions.size(); ++entry) {
      if (entry) out += ',';
      const auto &condition = row.conditions[entry];
      out += "{\"loaded_row_index\":" + std::to_string(condition.loaded_row_index);
      out += ",\"role_compatible\":"; AppendCommanderSideBoolV1(out, condition.role_compatible);
      out += ",\"native_trigger_valid\":"; AppendCommanderSideBoolV1(out, condition.native_trigger_valid);
      out += ",\"role_and_trigger_valid\":"; AppendCommanderSideBoolV1(out, condition.role_and_trigger_valid);
      out += ",\"unavailable_reason\":"; AppendCommanderSideReasonV1(out, condition.unavailable_reason); out += '}';
    }
    out += "],\"role_compatible_count\":" + std::to_string(row.role_compatible_count);
    out += ",\"evaluated_count\":" + std::to_string(row.evaluated_count);
    out += ",\"admitted_count\":" + std::to_string(row.admitted_count);
    out += ",\"unknown_count\":" + std::to_string(row.unknown_count);
    out += ",\"role_trigger_observation_ready\":"; out += row.role_trigger_observation_ready ? "true" : "false";
    out += ",\"status\":"; AppendPhaseRiteStringV1(out, row.status);
    out += ",\"unavailable_reason\":"; AppendCommanderSideReasonV1(out, row.unavailable_reason); out += '}';
  }
  out += "]}";
}
} // namespace xar::game
