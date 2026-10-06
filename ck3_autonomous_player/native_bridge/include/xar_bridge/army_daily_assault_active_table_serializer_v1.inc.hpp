#pragma once

// Include after game_contract.hpp; all names are existing game DTOs.
namespace xar::game {
namespace daily_assault_table_json_detail {
template <class Number, class JsonString> struct Writer {
  std::string &out;
  Number number;
  JsonString string;
  bool first = true;
  void Key(std::string_view key) {
    if (!first) out += ',';
    first = false; string(out, key); out += ':';
  }
  void Text(std::string_view key, const std::string &value, bool nullable = false) {
    Key(key);
    if (nullable && value.empty()) out += "null";
    else string(out, value);
  }
  void Text(std::string_view key, const std::optional<std::string> &value) {
    Key(key); if (value) string(out, *value); else out += "null";
  }
  template <typename T> void Integer(std::string_view key, const T &value) {
    Key(key); out += number(value);
  }
  template <typename T> void Integer(std::string_view key, const std::optional<T> &value) {
    Key(key); out += value ? number(*value) : "null";
  }
  void Boolean(std::string_view key, bool value) { Key(key); out += value ? "true" : "false"; }
  void Boolean(std::string_view key, const std::optional<bool> &value) {
    Key(key); out += value ? (*value ? "true" : "false") : "null";
  }
  template <typename T> void Status(const T &p) {
    Text("status", p.status); Boolean("ready", p.ready);
    Text("unavailable_reason", p.unavailable_reason, true);
  }
};
template <class Number, class JsonString>
inline void Resolution(std::string &out, const ArmyDailyAssaultResolutionV1 &p,
                       Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p);
  w.Integer("requested_full_id_u32", p.requested_full_id_u32);
  w.Boolean("registry_loaded", p.registry_loaded);
  w.Integer("registry_capacity_u32", p.registry_capacity_u32);
  w.Integer("registry_index_u32", p.registry_index_u32);
  w.Text("indexed_identity", p.indexed_identity);
  w.Integer("indexed_full_id_u32", p.indexed_full_id_u32);
  w.Text("selection", p.selection);
  w.Boolean("used_fallback", p.used_fallback);
  w.Text("object_identity", p.object_identity);
  w.Integer("selected_full_id_u32", p.selected_full_id_u32);
  out += '}';
}
template <class Number, class JsonString, typename Occurrence>
inline void OccurrenceJson(std::string &out, const Occurrence &p,
                           Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index);
  w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("resolution"); Resolution(out, p.resolution, number, string);
  w.Status(p);
  if constexpr (requires { p.magic_raw_u32; }) {
    w.Integer("magic_raw_u32", p.magic_raw_u32);
    w.Boolean("identity_valid", p.identity_valid);
    w.Text("definition_identity", p.definition_identity);
    w.Integer("definition_type_raw_i32", p.definition_type_raw_i32);
    w.Integer("current_raw_i32", p.current_raw_i32);
    w.Boolean("denominator_included", p.denominator_included);
  }
  out += '}';
}
template <class Number, class JsonString, typename Occurrence>
inline void References(std::string &out, const ArmyDailyAssaultReferencesV1<Occurrence> &p,
                       Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p); w.Boolean("references_ready", p.references_ready);
  w.Integer("count_raw_i32", p.count_raw_i32);
  w.Text("data_identity", p.data_identity); w.Boolean("data_present", p.data_present);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    OccurrenceJson(out, p.occurrences[i], number, string);
  }
  out += ']';
  w.Integer("observed_occurrence_count", p.observed_occurrence_count);
  out += '}';
}
template <class Number, class JsonString>
inline void Header(std::string &out, const ArmyDailyAssaultTableHeaderV1 &p,
                   Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p);
  w.Text("entries_identity", p.entries_identity); w.Boolean("entries_present", p.entries_present);
  w.Integer("occupied_count_raw_i32", p.occupied_count_raw_i32);
  w.Integer("mask_raw_i32", p.mask_raw_i32); w.Integer("tail_distance_raw_u8", p.tail_distance_raw_u8);
  w.Integer("load_factor_f32_bits_u32", p.load_factor_f32_bits_u32);
  w.Integer("end_slot_raw_i32", p.end_slot_raw_i32);
  w.Integer("end_marker_control_raw_u8", p.end_marker_control_raw_u8);
  out += '}';
}
template <class Number, class JsonString>
inline void Group(std::string &out, const ArmyDailyAssaultGroupV1 &p,
                  Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index); w.Integer("physical_slot_i64", p.physical_slot_i64);
  w.Status(p);
  w.Integer("hash_raw_u32", p.hash_raw_u32); w.Integer("control_raw_u8", p.control_raw_u8);
  w.Integer("siege_full_id_u32", p.siege_full_id_u32);
  w.Key("siege_resolution"); Resolution(out, p.siege_resolution, number, string);
  w.Key("armies"); References(out, p.armies, number, string);
  w.Key("arrgs"); References(out, p.arrgs, number, string);
  w.Boolean("denominator_ready", p.denominator_ready);
  out += '}';
}
} // namespace daily_assault_table_json_detail
template <class Number, class JsonString>
inline void AppendArmyCurrentDailyAssaultTableV1(std::string &output,
    const ArmyCurrentDailyAssaultTableV1 &p, Number number, JsonString append_json_string) {
  using namespace daily_assault_table_json_detail;
  output += '{'; Writer<Number, JsonString> w{output, number, append_json_string};
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Status(p); w.Boolean("manager_loaded", p.manager_loaded); w.Text("manager_identity", p.manager_identity);
  w.Key("header"); Header(output, p.header, number, append_json_string);
  w.Key("physical_controls"); output += '[';
  for (std::size_t i = 0; i < p.physical_controls.size(); ++i) {
    if (i) output += ',';
    output += '{'; Writer<Number, JsonString> c{output, number, append_json_string};
    const auto &control = p.physical_controls[i];
    c.Integer("physical_slot_i64", control.physical_slot_i64); c.Integer("control_raw_u8", control.control_raw_u8);
    c.Text("unavailable_reason", control.unavailable_reason, true);
    output += '}';
  }
  output += ']';
  w.Key("groups"); output += '[';
  for (std::size_t i = 0; i < p.groups.size(); ++i) {
    if (i) output += ',';
    Group(output, p.groups[i], number, append_json_string);
  }
  output += ']';
  w.Integer("observed_occupied_group_count", p.observed_occupied_group_count);
  w.Boolean("physical_scan_ready", p.physical_scan_ready); w.Boolean("raw_groups_ready", p.raw_groups_ready);
  output += '}';
}
} // namespace xar::game
