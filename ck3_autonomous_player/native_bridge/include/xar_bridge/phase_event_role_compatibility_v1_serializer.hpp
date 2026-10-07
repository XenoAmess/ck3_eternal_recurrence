#pragma once

#include "xar_bridge/phase_event_role_compatibility_v1.hpp"
#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"

namespace xar::game {
template <class T> inline void AppendPhaseRoleIntegerV1(
    std::string &out, const std::optional<T> &value) {
  out += value ? std::to_string(*value) : "null";
}
inline void AppendPhaseRoleReasonV1(std::string &out, const std::string &reason) {
  if (reason.empty()) out += "null";
  else AppendPhaseRiteStringV1(out, reason);
}
inline void AppendPhaseEventRoleCompatibilityV1(
    std::string &out, const PhaseEventRoleCompatibilityV1 &value) {
  out += "{\"schema_version\":1,\"scope\":\"v2_roster_loaded_event_role_condition\",\"status\":";
  AppendPhaseRiteStringV1(out, value.status);
  out += ",\"loaded_registry_source_closed\":";
  out += value.loaded_registry_source_closed ? "true" : "false";
  out += ",\"role_compare_source_closed\":";
  out += value.role_compare_source_closed ? "true" : "false";
  out += ",\"native_candidate_admission_observed\":false,\"complete_phase_effects_ready\":false,\"source_ck3_sha256\":";
  AppendPhaseRiteStringV1(out, value.source_ck3_sha256);
  out += ",\"unavailable_reason\":"; AppendPhaseRoleReasonV1(out, value.unavailable_reason);
  out += ",\"loaded_registry\":{\"status\":";
  AppendPhaseRiteStringV1(out, value.loaded_registry.status);
  out += ",\"count_raw\":"; AppendPhaseRoleIntegerV1(out, value.loaded_registry.count_raw);
  out += ",\"unavailable_reason\":"; AppendPhaseRoleReasonV1(out, value.loaded_registry.unavailable_reason);
  out += ",\"rows\":[";
  for (std::size_t index = 0; index < value.loaded_registry.rows.size(); ++index) {
    if (index) out += ',';
    const auto &row = value.loaded_registry.rows[index];
    out += "{\"loaded_row_index\":" + std::to_string(row.loaded_row_index);
    out += ",\"role_operand_raw\":"; AppendPhaseRoleIntegerV1(out, row.role_operand_raw);
    out += ",\"status\":"; AppendPhaseRiteStringV1(out, row.status);
    out += ",\"unavailable_reason\":"; AppendPhaseRoleReasonV1(out, row.unavailable_reason);
    out += '}';
  }
  out += "]},\"occurrences\":[";
  for (std::size_t index = 0; index < value.occurrences.size(); ++index) {
    if (index) out += ',';
    const auto &row = value.occurrences[index];
    out += "{\"occurrence_index\":" + std::to_string(row.occurrence_index);
    out += ",\"character_id\":" + std::to_string(row.character_id);
    out += ",\"source_public_cunit_id\":" + std::to_string(row.source_public_cunit_id);
    out += ",\"source_native_carmy_id\":"; AppendPhaseRoleIntegerV1(out, row.source_native_carmy_id);
    out += ",\"source_regiment_id\":"; AppendPhaseRoleIntegerV1(out, row.source_regiment_id);
    out += ",\"encounter_role\":"; AppendPhaseRiteStringV1(out, row.encounter_role);
    out += ",\"phase_role\":"; AppendPhaseRiteStringV1(out, row.phase_role);
    out += ",\"requested_role_raw\":" + std::to_string(row.requested_role_raw);
    out += ",\"native_role_argument_source_closed\":";
    out += row.native_role_argument_source_closed ? "true" : "false";
    out += ",\"conditions\":[";
    for (std::size_t condition_index = 0; condition_index < row.conditions.size(); ++condition_index) {
      if (condition_index) out += ',';
      const auto &condition = row.conditions[condition_index];
      out += "{\"loaded_row_index\":" + std::to_string(condition.loaded_row_index);
      out += ",\"role_compatible\":";
      out += condition.role_compatible ? (*condition.role_compatible ? "true" : "false") : "null";
      out += ",\"unavailable_reason\":"; AppendPhaseRoleReasonV1(out, condition.unavailable_reason);
      out += '}';
    }
    out += "]}";
  }
  out += "]}";
}
} // namespace xar::game
