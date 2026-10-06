#pragma once
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"
namespace xar::game {
#include "xar_bridge/army_current_selected_title_holder_owner_relation_v1.inc.hpp"
namespace selected_holder_owner_json_detail {
using namespace daily_assault_roster_admission_json_detail;
template <class Number, class JsonString>
inline void Selection(std::string &out, const ArmySelectedHolderOperandSelectionV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Boolean("registry_loaded", p.registry_loaded); w.Boolean("used_fallback", p.used_fallback);
  w.Integer("requested_full_id_u32", p.requested_full_id_u32);
  w.Integer("registry_capacity_u32", p.registry_capacity_u32); w.Integer("registry_index_u32", p.registry_index_u32);
  w.Integer("indexed_full_id_u32", p.indexed_full_id_u32); w.Text("indexed_identity", p.indexed_identity);
  w.Text("object_identity", p.object_identity); w.Text("selection", p.selection);
  w.Boolean("selected_object_ready", p.selected_object_ready); out += '}';
}
template <class Number, class JsonString>
inline void UnitSelection(std::string &out, const ArmySelectedHolderUnitSelectionV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index); w.Text("purpose", p.purpose);
  w.Integer("army_124_raw_u32", p.army_124_raw_u32);
  w.Key("unit_resolution"); Selection(out, p.unit_resolution, number, string);
  w.Boolean("province_used_fallback", p.province_used_fallback); w.Text("province_identity", p.province_identity);
  w.Integer("province_magic_85c_raw_u32", p.province_magic_85c_raw_u32); out += '}';
}
template <class Number, class JsonString>
inline void Occurrence(std::string &out, const ArmySelectedTitleHolderOwnerRelationOccurrenceV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("original_army_resolution"); OperandResolution(out, p.original_army_resolution, number, string);
  w.Boolean("same_query_army_selection_matched", p.same_query_army_selection_matched);
  w.Key("unit_selections"); out += '[';
  for (std::size_t i = 0; i < p.unit_selections.size(); ++i) {
    if (i) out += ',';
    UnitSelection(out, p.unit_selections[i], number, string);
  }
  out += ']';
  w.Integer("province_title_738_raw_u32", p.province_title_738_raw_u32);
  w.Integer("title_holder_128_raw_u32", p.title_holder_128_raw_u32);
  w.Key("title_resolution"); Selection(out, p.title_resolution, number, string);
  w.Key("parent_title_resolution"); Selection(out, p.parent_title_resolution, number, string);
  w.Integer("title_definition_64_raw_u32", p.title_definition_64_raw_u32);
  w.Integer("parent_title_e8_raw_u32", p.parent_title_e8_raw_u32);
  w.Integer("parent_holder_128_raw_u32", p.parent_holder_128_raw_u32);
  w.Integer("holder_requested_full_id_u32", p.holder_requested_full_id_u32);
  w.Integer("holder_character_full_id_u32", p.holder_character_full_id_u32);
  w.Key("holder_character_resolution"); Selection(out, p.holder_character_resolution, number, string);
  w.Integer("selected_unit_owner_174_raw_u32", p.selected_unit_owner_174_raw_u32);
  w.Boolean("holder_owner_equal", p.holder_owner_equal);
  w.Boolean("native_relation_demanded", p.native_relation_demanded);
  w.Boolean("native_relation_returned", p.native_relation_returned);
  w.Boolean("native_holder_owner_relation", p.native_holder_owner_relation);
  w.Integer("derived_current_shared_tail_raw_u8", p.derived_current_shared_tail_raw_u8);
  w.Boolean("current_shared_tail_inputs_ready", p.current_shared_tail_inputs_ready); out += '}';
}
}
template <class Number, class JsonString>
inline void AppendArmyCurrentSelectedTitleHolderOwnerRelationV1(std::string &out,
    const ArmyCurrentSelectedTitleHolderOwnerRelationV1 &p, Number number, JsonString string) {
  using namespace selected_holder_owner_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Text("context_basis", p.context_basis);
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
  w.Boolean("current_shared_tail_inputs_ready", p.current_shared_tail_inputs_ready);
  w.Boolean("actual_refresh_execution_ready", p.actual_refresh_execution_ready);
  w.Boolean("actual_next_occurrence_ready", p.actual_next_occurrence_ready);
  w.Boolean("changed_selection_context_ready", p.changed_selection_context_ready);
  w.Boolean("changed_relationship_context_ready", p.changed_relationship_context_ready);
  w.Boolean("full_callback_ready", p.full_callback_ready);
  w.Boolean("full_daily_assault_ready", p.full_daily_assault_ready);
  w.Boolean("full_monthly_ready", p.full_monthly_ready); out += '}';
}
}
