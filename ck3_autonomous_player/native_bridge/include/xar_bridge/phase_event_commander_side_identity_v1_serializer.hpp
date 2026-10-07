#pragma once

#include "xar_bridge/phase_event_commander_side_identity_v1.hpp"
#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"

namespace xar::game {
template <class T> inline void AppendCommanderSideIntegerV1(std::string &out, const std::optional<T> &value) {
  out += value ? std::to_string(*value) : "null";
}
inline void AppendCommanderSideBoolV1(std::string &out, const std::optional<bool> &value) {
  out += value ? (*value ? "true" : "false") : "null";
}
inline void AppendCommanderSideReasonV1(std::string &out, const std::string &reason) {
  if (reason.empty()) out += "null"; else AppendPhaseRiteStringV1(out, reason);
}
inline void AppendPhaseEventCommanderSideIdentityV1(std::string &out, const PhaseEventCommanderSideIdentityV1 &value) {
  out += "{\"schema_version\":1,\"scope\":\"v2_roster_current_physical_side_commander_identity\",\"status\":";
  AppendPhaseRiteStringV1(out, value.status);
  out += ",\"source_ck3_sha256\":"; AppendPhaseRiteStringV1(out, value.source_ck3_sha256);
  out += ",\"commander_side_identity_source_closed\":";
  out += value.commander_side_identity_source_closed ? "true" : "false";
  out += ",\"native_candidate_admission_observed\":false,\"complete_phase_effects_ready\":false,\"unavailable_reason\":";
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
    out += ",\"status\":"; AppendPhaseRiteStringV1(out, row.status);
    out += ",\"unavailable_reason\":"; AppendCommanderSideReasonV1(out, row.unavailable_reason);
    out += ",\"actual_physical_army_full_id_raw\":"; AppendCommanderSideIntegerV1(out, row.actual_physical_army_full_id_raw);
    out += ",\"actual_selected_combat_full_id_raw\":"; AppendCommanderSideIntegerV1(out, row.actual_selected_combat_full_id_raw);
    out += ",\"source_active_combat\":"; AppendCommanderSideBoolV1(out, row.source_active_combat);
    out += ",\"attacker_membership_count\":"; AppendCommanderSideIntegerV1(out, row.attacker_membership_count);
    out += ",\"defender_membership_count\":"; AppendCommanderSideIntegerV1(out, row.defender_membership_count);
    out += ",\"unique_physical_membership\":"; AppendCommanderSideBoolV1(out, row.unique_physical_membership);
    out += ",\"actual_side_index\":"; AppendCommanderSideIntegerV1(out, row.actual_side_index);
    out += ",\"actual_side_role\":";
    if (row.actual_side_role) AppendPhaseRiteStringV1(out, *row.actual_side_role); else out += "null";
    out += ",\"actual_side_parent_matches_selected_combat\":"; AppendCommanderSideBoolV1(out, row.actual_side_parent_matches_selected_combat);
    out += ",\"actual_side_commander_full_id_raw\":"; AppendCommanderSideIntegerV1(out, row.actual_side_commander_full_id_raw);
    out += ",\"actual_side_commander_present\":"; AppendCommanderSideBoolV1(out, row.actual_side_commander_present);
    out += ",\"full_id_equal\":"; AppendCommanderSideBoolV1(out, row.full_id_equal);
    out += '}';
  }
  out += "]}";
}
} // namespace xar::game
