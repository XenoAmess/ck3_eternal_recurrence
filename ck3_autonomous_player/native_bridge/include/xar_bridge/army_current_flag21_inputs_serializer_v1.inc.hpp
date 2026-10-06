#pragma once
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"
namespace xar::game {
#include "xar_bridge/army_current_flag21_inputs_v1.inc.hpp"
namespace flag21_json_detail {
using namespace daily_assault_roster_admission_json_detail;
template <class Number, class JsonString>
inline void Selection(std::string &out, const ArmyFlag21SelectionV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Boolean("registry_loaded", p.registry_loaded); w.Integer("requested_full_id_u32", p.requested_full_id_u32);
  w.Integer("registry_capacity_u32", p.registry_capacity_u32); w.Integer("registry_index_u32", p.registry_index_u32);
  w.Text("indexed_identity", p.indexed_identity); w.Integer("indexed_full_id_u32", p.indexed_full_id_u32);
  w.Text("selection", p.selection); w.Boolean("used_fallback", p.used_fallback);
  w.Text("object_identity", p.object_identity); w.Boolean("selected_object_ready", p.selected_object_ready); out += '}';
}
template <class Number, class JsonString>
inline void Occurrence(std::string &out, const ArmyFlag21OccurrenceV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("original_army_resolution"); OperandResolution(out, p.original_army_resolution, number, string);
  w.Boolean("same_query_army_selection_matched", p.same_query_army_selection_matched);
  w.Integer("actual_army_21_raw_u8", p.actual_army_21_raw_u8); w.Integer("army_1ec_raw_u8", p.army_1ec_raw_u8);
  w.Integer("army_1f0_raw_i64", p.army_1f0_raw_i64); w.Integer("army_124_raw_u32", p.army_124_raw_u32);
  w.Key("unit_resolution"); Selection(out, p.unit_resolution, number, string);
  w.Integer("unit_owner_174_raw_u32", p.unit_owner_174_raw_u32);
  w.Key("character_resolution"); Selection(out, p.character_resolution, number, string);
  w.Boolean("owner_character_carrier_1c0_present", p.owner_character_carrier_1c0_present);
  w.Text("owner_character_carrier_identity", p.owner_character_carrier_identity);
  w.Text("header_selection", p.header_selection); w.Text("header_identity", p.header_identity);
  w.Integer("header_0c_raw_i32", p.header_0c_raw_i32); w.Boolean("owner_header_inputs_ready", p.owner_header_inputs_ready);
  w.Boolean("native_shared_tail_returned", p.native_shared_tail_returned);
  w.Integer("native_shared_tail_21_raw_u8", p.native_shared_tail_21_raw_u8);
  w.Integer("derived_current_21_raw_u8", p.derived_current_21_raw_u8);
  w.Boolean("current_flag21_inputs_ready", p.current_flag21_inputs_ready); out += '}';
}
}
template <class Number, class JsonString>
inline void AppendArmyCurrentFlag21InputsV1(std::string &out, const ArmyCurrentFlag21InputsV1 &p,
    Number number, JsonString string) {
  using namespace flag21_json_detail;
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
  w.Boolean("current_flag21_inputs_ready", p.current_flag21_inputs_ready);
  w.Boolean("actual_refresh_execution_ready", p.actual_refresh_execution_ready);
  w.Boolean("actual_next_occurrence_ready", p.actual_next_occurrence_ready);
  w.Boolean("full_callback_ready", p.full_callback_ready);
  w.Boolean("full_daily_assault_ready", p.full_daily_assault_ready);
  w.Boolean("full_monthly_ready", p.full_monthly_ready); out += '}';
}
}
