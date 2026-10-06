#pragma once
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"
#include "xar_bridge/army_current_rule24_source_pins_serializer_v1.inc.hpp"
namespace xar::game {
#include "xar_bridge/army_current_flag31_inputs_v1.inc.hpp"
namespace flag31_json_detail {
using namespace daily_assault_roster_admission_json_detail;
template <class Number, class JsonString>
inline void Selection(std::string &out, const ArmyFlag31SelectionV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Boolean("registry_loaded", p.registry_loaded); w.Integer("requested_full_id_u32", p.requested_full_id_u32);
  w.Integer("registry_capacity_u32", p.registry_capacity_u32); w.Integer("registry_index_u32", p.registry_index_u32);
  w.Text("indexed_identity", p.indexed_identity); w.Integer("indexed_full_id_u32", p.indexed_full_id_u32);
  w.Text("selection", p.selection); w.Boolean("used_fallback", p.used_fallback);
  w.Text("object_identity", p.object_identity); w.Boolean("selected_object_ready", p.selected_object_ready); out += '}';
}
template <class Number, class JsonString>
inline void Occurrence(std::string &out, const ArmyFlag31OccurrenceV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("original_army_resolution"); OperandResolution(out, p.original_army_resolution, number, string);
  w.Boolean("same_query_army_selection_matched", p.same_query_army_selection_matched);
  w.Integer("actual_army_31_raw_u8", p.actual_army_31_raw_u8); w.Integer("army_1d4_raw_u8", p.army_1d4_raw_u8);
  w.Integer("army_128_raw_u32", p.army_128_raw_u32);
  w.Key("combat_resolution"); Selection(out, p.combat_resolution, number, string);
  w.Integer("selected_combat_magic_0c_raw_u32", p.selected_combat_magic_0c_raw_u32);
  w.Integer("selected_combat_full_id_08_raw_u32", p.selected_combat_full_id_08_raw_u32);
  w.Boolean("source_active_combat", p.source_active_combat);
  w.Boolean("active_combat_inputs_ready", p.active_combat_inputs_ready);
  w.Integer("army_124_raw_u32", p.army_124_raw_u32);
  w.Key("unit_resolution"); Selection(out, p.unit_resolution, number, string);
  w.Integer("unit_owner_174_raw_u32", p.unit_owner_174_raw_u32);
  w.Key("character_resolution"); Selection(out, p.character_resolution, number, string);
  w.Integer("selected_character_18_raw_u32", p.selected_character_18_raw_u32);
  w.Integer("rule_selector_i32", p.rule_selector_i32); w.Integer("rule_inline_offset_u32", p.rule_inline_offset_u32);
  w.Text("rule_provider_identity", p.rule_provider_identity); w.Text("rule_array_identity", p.rule_array_identity);
  w.Text("inline_rule_identity", p.inline_rule_identity);
  if (p.rule24_source_pins_v1) {
    w.Key("rule24_source_pins_v1");
    AppendArmyCurrentRule24SourcePinsV1(
        out, *p.rule24_source_pins_v1, number, nullptr, string);
  }
  w.Integer("root_kind", p.root_kind); w.Integer("root_subtype", p.root_subtype);
  w.Integer("root_payload_u64", p.root_payload_u64); w.Text("root_construction", p.root_construction);
  w.Boolean("native_rule_evaluation_returned", p.native_rule_evaluation_returned);
  w.Boolean("native_current_rule24_passed", p.native_current_rule24_passed);
  w.Integer("derived_current_31_raw_u8", p.derived_current_31_raw_u8);
  w.Boolean("current_flag31_inputs_ready", p.current_flag31_inputs_ready); out += '}';
}
}
template <class Number, class AppendIds, class JsonString>
inline void AppendArmyCurrentFlag31InputsV1(std::string &out, const ArmyCurrentFlag31InputsV1 &p,
    Number number, AppendIds /*append_ids*/, JsonString string) {
  using namespace flag31_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Boolean("manager_loaded", p.manager_loaded); w.Text("manager_identity", p.manager_identity);
  w.Key("original_roster"); RawReferences(out, p.original_roster, number, string);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    Occurrence(out, p.occurrences[i], number, string);
  }
  out += ']';
  w.Boolean("raw_roster_references_ready", p.raw_roster_references_ready);
  w.Boolean("original_army_selections_ready", p.original_army_selections_ready);
  w.Boolean("current_flag31_inputs_ready", p.current_flag31_inputs_ready);
  w.Boolean("actual_refresh_execution_ready", p.actual_refresh_execution_ready);
  w.Boolean("actual_next_occurrence_ready", p.actual_next_occurrence_ready);
  w.Boolean("full_callback_ready", p.full_callback_ready);
  w.Boolean("full_daily_assault_ready", p.full_daily_assault_ready);
  w.Boolean("full_monthly_ready", p.full_monthly_ready); out += '}';
}
}
