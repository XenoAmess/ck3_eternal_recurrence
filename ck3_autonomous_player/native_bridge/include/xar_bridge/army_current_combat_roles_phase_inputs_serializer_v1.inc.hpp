#pragma once
#include "xar_bridge/army_current_flag31_inputs_serializer_v1.inc.hpp"
namespace xar::game {
#include "xar_bridge/army_current_combat_roles_phase_inputs_v1.inc.hpp"
namespace combat_roles_phase_json_detail {
using namespace daily_assault_roster_admission_json_detail;
template <class Number, class JsonString, class T>
inline void Status(Writer<Number, JsonString> &w, const T &p) {
  w.Text("status", p.status); w.Text("unavailable_reason", p.unavailable_reason);
}
template <class Number, class JsonString>
inline void Roster(std::string &out, const ArmyCurrentCombatRawRosterV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; Status(w, p);
  w.Text("data_identity", p.data_identity); w.Integer("capacity_raw_u32", p.capacity_raw_u32);
  w.Integer("count_raw_i32", p.count_raw_i32); w.Key("references"); out += '[';
  for (std::size_t i = 0; i < p.references.size(); ++i) {
    if (i) out += ',';
    out += '{'; Writer<Number, JsonString> r{out, number, string};
    r.Integer("native_index", p.references[i].native_index); r.Integer("raw_full_id_u32", p.references[i].raw_full_id_u32);
    out += '}';
  }
  out += ']'; w.Boolean("references_ready", p.references_ready); out += '}';
}
template <class Number, class JsonString>
inline void Manager(std::string &out, const ArmyCurrentCombatManagerInputsV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; Status(w, p);
  w.Text("game_state_identity", p.game_state_identity); w.Text("domain_identity", p.domain_identity);
  w.Text("manager_identity", p.manager_identity); w.Text("secondary_vtable_identity", p.secondary_vtable_identity);
  w.Boolean("secondary_vtable_matched", p.secondary_vtable_matched);
  w.Key("roster"); Roster(out, p.roster, number, string);
  w.Boolean("manager_inputs_ready", p.manager_inputs_ready); out += '}';
}
template <class Number, class AppendIds, class JsonString>
inline void Side(std::string &out, const ArmyCurrentCombatSideInputsV1 &p, Number number, AppendIds append_ids, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; Status(w, p);
  w.Text("parent_identity", p.parent_identity); w.Boolean("parent_matches_selected_combat", p.parent_matches_selected_combat);
  w.Key("armies"); Roster(out, p.armies, number, string);
  w.Key("matching_army_indices"); append_ids(out, p.matching_army_indices);
  w.Boolean("matching_membership_ready", p.matching_membership_ready);
  w.Integer("primary_70_raw_u32", p.primary_70_raw_u32); w.Integer("commander_74_raw_u32", p.commander_74_raw_u32);
  w.Boolean("owner_matches_primary", p.owner_matches_primary); w.Boolean("side_inputs_ready", p.side_inputs_ready); out += '}';
}
template <class Number, class AppendIds, class JsonString>
inline void Occurrence(std::string &out, const ArmyCurrentCombatRolesPhaseOccurrenceV1 &p,
    Number number, AppendIds append_ids, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; Status(w, p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("original_army_resolution"); OperandResolution(out, p.original_army_resolution, number, string);
  w.Boolean("same_query_army_selection_matched", p.same_query_army_selection_matched);
  w.Integer("actual_army_10_raw_u32", p.actual_army_10_raw_u32); w.Integer("army_128_raw_u32", p.army_128_raw_u32);
  w.Key("combat_resolution"); flag31_json_detail::Selection(out, p.combat_resolution, number, string);
  w.Integer("selected_combat_magic_0c_raw_u32", p.selected_combat_magic_0c_raw_u32);
  w.Integer("selected_combat_full_id_08_raw_u32", p.selected_combat_full_id_08_raw_u32);
  w.Boolean("source_active_combat", p.source_active_combat); w.Boolean("active_combat_inputs_ready", p.active_combat_inputs_ready);
  w.Key("manager_match_indices"); append_ids(out, p.manager_match_indices);
  w.Boolean("combat_manager_membership_ready", p.combat_manager_membership_ready);
  w.Integer("army_124_raw_u32", p.army_124_raw_u32); w.Integer("unit_owner_174_raw_u32", p.unit_owner_174_raw_u32);
  w.Key("unit_resolution"); flag31_json_detail::Selection(out, p.unit_resolution, number, string);
  w.Key("character_resolution"); flag31_json_detail::Selection(out, p.character_resolution, number, string);
  w.Integer("selected_character_18_raw_u32", p.selected_character_18_raw_u32); w.Boolean("owner_inputs_ready", p.owner_inputs_ready);
  w.Key("attacker_side"); Side(out, p.attacker_side, number, append_ids, string);
  w.Key("defender_side"); Side(out, p.defender_side, number, append_ids, string);
  w.Integer("phase_6b0_raw_i32", p.phase_6b0_raw_i32); w.Integer("day_6b4_raw_i32", p.day_6b4_raw_i32);
  w.Integer("forced_winner_700_raw_i32", p.forced_winner_700_raw_i32);
  w.Integer("finalized_704_raw_u8", p.finalized_704_raw_u8); w.Integer("processing_705_raw_u8", p.processing_705_raw_u8);
  w.Boolean("phase_inputs_ready", p.phase_inputs_ready); w.Boolean("threshold_required", p.threshold_required);
  w.Integer("maneuver_threshold_raw_i32", p.maneuver_threshold_raw_i32); w.Boolean("threshold_inputs_ready", p.threshold_inputs_ready);
  w.Boolean("current_combat_roles_phase_inputs_ready", p.current_combat_roles_phase_inputs_ready); out += '}';
}
}
template <class Number, class AppendIds, class JsonString>
inline void AppendArmyCurrentCombatRolesPhaseInputsV1(std::string &out, const ArmyCurrentCombatRolesPhaseInputsV1 &p,
    Number number, AppendIds append_ids, JsonString string) {
  using namespace combat_roles_phase_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string}; Status(w, p);
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Boolean("original_army_manager_loaded", p.original_army_manager_loaded);
  w.Text("original_army_manager_identity", p.original_army_manager_identity);
  w.Key("original_roster"); RawReferences(out, p.original_roster, number, string);
  w.Key("combat_manager"); Manager(out, p.combat_manager, number, string);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    Occurrence(out, p.occurrences[i], number, append_ids, string);
  }
  out += ']'; w.Boolean("raw_roster_references_ready", p.raw_roster_references_ready);
  w.Boolean("original_army_selections_ready", p.original_army_selections_ready);
  w.Boolean("current_combat_roles_phase_inputs_ready", p.current_combat_roles_phase_inputs_ready);
  w.Boolean("actual_manager_invocation_observed", p.actual_manager_invocation_observed);
  w.Boolean("future_phase_transition_ready", p.future_phase_transition_ready);
  w.Boolean("full_callback_ready", p.full_callback_ready); w.Boolean("full_battle_ready", p.full_battle_ready);
  w.Integer("native_calls_executed", p.native_calls_executed); w.Integer("native_writes_executed", p.native_writes_executed); out += '}';
}
}
