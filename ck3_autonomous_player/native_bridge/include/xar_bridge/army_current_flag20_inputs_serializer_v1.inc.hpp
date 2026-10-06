#pragma once
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"
namespace xar::game {
#include "xar_bridge/army_current_flag20_inputs_v1.inc.hpp"
namespace flag20_json_detail {
using namespace daily_assault_roster_admission_json_detail;
template <class Number, class JsonString>
inline void Occurrence(std::string &out, const ArmyFlag20OccurrenceV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("original_army_resolution"); OperandResolution(out, p.original_army_resolution, number, string);
  w.Boolean("same_query_army_selection_matched", p.same_query_army_selection_matched);
  w.Integer("actual_army_20_raw_u8", p.actual_army_20_raw_u8); w.Integer("army_1d4_raw_u8", p.army_1d4_raw_u8);
  w.Boolean("native_getter_returned", p.native_getter_returned);
  w.Integer("native_getter_20_raw_u8", p.native_getter_20_raw_u8);
  w.Integer("derived_current_20_raw_u8", p.derived_current_20_raw_u8);
  w.Boolean("current_flag20_inputs_ready", p.current_flag20_inputs_ready); out += '}';
}
}
template <class Number, class JsonString>
inline void AppendArmyCurrentFlag20InputsV1(std::string &out, const ArmyCurrentFlag20InputsV1 &p,
    Number number, JsonString string) {
  using namespace flag20_json_detail;
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
  w.Boolean("current_flag20_inputs_ready", p.current_flag20_inputs_ready);
  w.Boolean("actual_refresh_execution_ready", p.actual_refresh_execution_ready);
  w.Boolean("actual_next_occurrence_ready", p.actual_next_occurrence_ready);
  w.Boolean("full_callback_ready", p.full_callback_ready);
  w.Boolean("full_daily_assault_ready", p.full_daily_assault_ready);
  w.Boolean("full_monthly_ready", p.full_monthly_ready); out += '}';
}
}
