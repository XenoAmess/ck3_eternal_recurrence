#pragma once
#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"

namespace xar::game {
namespace pre_date_dated_append_json_detail {
using daily_assault_roster_admission_json_detail::Writer;
template <class Number, class JsonString>
inline void IdList(std::string &out, const ArmyPreDateDatedIdListV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Boolean("ready", p.ready); w.Text("unavailable_reason", p.unavailable_reason);
  w.Text("source", p.source); w.Integer("count_raw_i32", p.count_raw_i32);
  w.Key("ordered_ids_u32");
  if (!p.ordered_ids_u32) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < p.ordered_ids_u32->size(); ++i) {
      if (i) out += ',';
      const auto &id = p.ordered_ids_u32->at(i);
      out += id ? number(*id) : "null";
    }
    out += ']';
  }
  out += '}';
}
template <class Number, class JsonString>
inline void Occurrence(std::string &out, const ArmyPreDateDatedOccurrenceV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p); w.Integer("native_index", p.native_index);
  w.Integer("original_request_full_id_u32", p.original_request_full_id_u32);
  w.Key("army_resolution");
  daily_assault_roster_admission_json_detail::OperandResolution(out, p.army_resolution, number, string);
  w.Integer("combat_request_full_id_u32", p.combat_request_full_id_u32);
  w.Key("combat_resolution");
  daily_assault_roster_admission_json_detail::OperandResolution(out, p.combat_resolution, number, string);
  w.Integer("combat_magic_0c_raw_u32", p.combat_magic_0c_raw_u32);
  w.Integer("army_date_count_5c_raw_i32", p.army_date_count_5c_raw_i32);
  w.Text("date_array_identity", p.date_array_identity); w.Boolean("date_array_present", p.date_array_present);
  w.Key("date_entries"); out += '[';
  for (std::size_t i = 0; i < p.date_entries.size(); ++i) {
    if (i) out += ',';
    out += '{'; Writer<Number, JsonString> entry{out, number, string};
    const auto &d = p.date_entries[i];
    entry.Integer("native_index", d.native_index); entry.Text("pointer_identity", d.pointer_identity);
    entry.Boolean("pointer_present", d.pointer_present); entry.Integer("date_low_raw_i32", d.date_low_raw_i32);
    out += '}';
  }
  out += ']'; w.Boolean("date_scan_ready", p.date_scan_ready); out += '}';
}
} // namespace pre_date_dated_append_json_detail

template <class Number, class JsonString>
inline void AppendArmyPreDateDatedAppendInputsV1(std::string &out,
    const ArmyPreDateDatedAppendInputsV1 &p, Number number, JsonString string) {
  using namespace pre_date_dated_append_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Status(p); w.Boolean("manager_loaded", p.manager_loaded); w.Text("manager_identity", p.manager_identity);
  w.Text("clock_source", p.clock_source); w.Boolean("clock_ready", p.clock_ready);
  w.Integer("current_date_raw_i32", p.current_date_raw_i32); w.Integer("tomorrow_date_low_i32", p.tomorrow_date_low_i32);
  w.Key("source_c8"); IdList(out, p.source_c8, number, string);
  w.Key("initial_158"); IdList(out, p.initial_158, number, string);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    Occurrence(out, p.occurrences[i], number, string);
  }
  out += "]}";
}
} // namespace xar::game
