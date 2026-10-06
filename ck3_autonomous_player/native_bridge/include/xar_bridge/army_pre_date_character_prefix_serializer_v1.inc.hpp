#pragma once
#include "xar_bridge/army_pre_date_dated_append_serializer_v1.inc.hpp"

namespace xar::game {
namespace pre_date_character_prefix_json_detail {
using daily_assault_roster_admission_json_detail::Writer;
template <class Number, class JsonString>
inline void Predicate(std::string &out, const ArmyPreDateCharacterPredicateV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Boolean("demanded", p.demanded); w.Boolean("observable", p.observable);
  w.Boolean("verdict", p.verdict); w.Text("unavailable_reason", p.unavailable_reason); out += '}';
}
template <class Number, class JsonString>
inline void Occurrence(std::string &out, const ArmyPreDateCharacterOccurrenceV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("original_request_full_id_u32", p.original_request_full_id_u32);
  w.Key("army_resolution"); daily_assault_roster_admission_json_detail::OperandResolution(out, p.army_resolution, number, string);
  w.Boolean("earlier_skip", p.earlier_skip); w.Text("earlier_skip_source", p.earlier_skip_source);
  w.Integer("army_character_120_raw_u32", p.army_character_120_raw_u32);
  w.Key("character_resolution"); daily_assault_roster_admission_json_detail::OperandResolution(out, p.character_resolution, number, string);
  w.Integer("army_unit_124_raw_u32", p.army_unit_124_raw_u32);
  w.Key("unit_resolution"); daily_assault_roster_admission_json_detail::OperandResolution(out, p.unit_resolution, number, string);
  w.Integer("unit_owner_174_raw_u32", p.unit_owner_174_raw_u32);
  w.Integer("character_magic_1c_raw_u32", p.character_magic_1c_raw_u32);
  w.Integer("character_full_id_18_raw_u32", p.character_full_id_18_raw_u32);
  w.Boolean("character_death_1d0_present", p.character_death_1d0_present);
  w.Boolean("character_state_1c8_present", p.character_state_1c8_present);
  w.Boolean("character_state_1c0_present", p.character_state_1c0_present);
  w.Boolean("character_state_1b8_present", p.character_state_1b8_present);
  w.Key("membership"); Predicate(out, p.membership, number, string);
  w.Key("basic_rule"); Predicate(out, p.basic_rule, number, string);
  w.Key("availability"); Predicate(out, p.availability, number, string);
  w.Integer("failure_append_army_10_raw_u32", p.failure_append_army_10_raw_u32); out += '}';
}
} // namespace pre_date_character_prefix_json_detail
template <class Number, class JsonString>
inline void AppendArmyCurrentPreDateCharacterPrefixInputsV1(std::string &out,
    const ArmyCurrentPreDateCharacterPrefixInputsV1 &p, Number number, JsonString string) {
  using namespace pre_date_character_prefix_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage); w.Status(p);
  w.Boolean("manager_loaded", p.manager_loaded); w.Text("manager_identity", p.manager_identity);
  w.Key("original_roster"); daily_assault_roster_admission_json_detail::RawReferences(out, p.original_roster, number, string);
  w.Key("initial_80"); pre_date_dated_append_json_detail::IdList(out, p.initial_80, number, string);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    Occurrence(out, p.occurrences[i], number, string);
  }
  out += "]}";
}
} // namespace xar::game
