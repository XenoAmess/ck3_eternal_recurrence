#pragma once

#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"

namespace xar::game {
namespace post_admission_refresh_json_detail {
using namespace daily_assault_roster_admission_json_detail;
template <class Number, class JsonString>
inline void ArRg(std::string &out, const ArmyPostAdmissionRefreshArRgV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("arrg_resolution"); OperandResolution(out, p.arrg_resolution, number, string);
  w.Integer("magic_14_raw_u32", p.magic_14_raw_u32); w.Boolean("identity_valid", p.identity_valid);
  w.Integer("current_38_raw_i32", p.current_38_raw_i32); w.Integer("value_40_raw_i64", p.value_40_raw_i64);
  w.Boolean("numeric_24_inputs_ready", p.numeric_24_inputs_ready);
  w.Boolean("numeric_28_inputs_ready", p.numeric_28_inputs_ready); out += '}';
}
template <class Number, class JsonString>
inline void Occurrence(std::string &out, const ArmyPostAdmissionRefreshOccurrenceV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("original_army_resolution"); OperandResolution(out, p.original_army_resolution, number, string);
  w.Key("original_arrg_references"); RawReferences(out, p.original_arrg_references, number, string);
  w.Key("arrg_occurrences"); out += '[';
  for (std::size_t i = 0; i < p.arrg_occurrences.size(); ++i) {
    if (i) out += ',';
    ArRg(out, p.arrg_occurrences[i], number, string);
  }
  out += ']';
  w.Integer("actual_army_24_raw_i32", p.actual_army_24_raw_i32);
  w.Integer("actual_army_28_raw_i64", p.actual_army_28_raw_i64);
  w.Integer("actual_army_20_raw_u8", p.actual_army_20_raw_u8);
  w.Integer("actual_army_21_raw_u8", p.actual_army_21_raw_u8);
  w.Integer("actual_army_30_raw_u8", p.actual_army_30_raw_u8);
  w.Integer("actual_army_31_raw_u8", p.actual_army_31_raw_u8);
  w.Boolean("arrg_rows_ready", p.arrg_rows_ready);
  w.Boolean("numeric_24_inputs_ready", p.numeric_24_inputs_ready);
  w.Boolean("numeric_28_inputs_ready", p.numeric_28_inputs_ready); out += '}';
}
} // namespace post_admission_refresh_json_detail
template <class Number, class JsonString>
inline void AppendArmyCurrentPostAdmissionRefreshInputsV1(std::string &out,
    const ArmyCurrentPostAdmissionRefreshInputsV1 &p, Number number, JsonString string) {
  using namespace post_admission_refresh_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Text("projection_stage", p.projection_stage);
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
  w.Boolean("numeric_24_inputs_ready", p.numeric_24_inputs_ready);
  w.Boolean("numeric_28_inputs_ready", p.numeric_28_inputs_ready);
  w.Boolean("source_operands_ready", p.source_operands_ready);
  w.Boolean("actual_refresh_execution_ready", p.actual_refresh_execution_ready);
  w.Boolean("actual_next_occurrence_ready", p.actual_next_occurrence_ready);
  w.Boolean("full_callback_ready", p.full_callback_ready);
  w.Boolean("full_daily_assault_ready", p.full_daily_assault_ready);
  w.Boolean("full_monthly_ready", p.full_monthly_ready); out += '}';
}
} // namespace xar::game
