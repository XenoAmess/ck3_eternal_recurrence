#pragma once

// Include after game_contract.hpp. This writer emits the raw admission contract.
namespace xar::game {
namespace daily_assault_roster_admission_json_detail {
template <class Number, class JsonString> struct Writer {
  std::string &out;
  Number number;
  JsonString string;
  bool first = true;
  void Key(std::string_view key) {
    if (!first) out += ',';
    first = false;
    string(out, key);
    out += ':';
  }
  void Text(std::string_view key, const std::string &value) {
    Key(key); string(out, value);
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
  void Boolean(std::string_view key, bool value) {
    Key(key); out += value ? "true" : "false";
  }
  void Boolean(std::string_view key, const std::optional<bool> &value) {
    Key(key); out += value ? (*value ? "true" : "false") : "null";
  }
  template <typename T> void Status(const T &p) {
    Text("status", p.status); Boolean("ready", p.ready);
    Text("unavailable_reason", p.unavailable_reason);
  }
};
template <class Number, class JsonString>
inline void OperandResolution(std::string &out, const ArmyDailyAssaultOperandResolutionV1 &p,
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
  w.Boolean("selected_object_ready", p.selected_object_ready);
  w.Boolean("selected_full_id_read_ready", p.selected_full_id_read_ready);
  out += '}';
}
template <class Number, class JsonString>
inline void RawReferenceOccurrence(std::string &out, const ArmyDailyAssaultRawReferenceOccurrenceV1 &p,
                                  Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p);
  w.Integer("native_index", p.native_index);
  w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  out += '}';
}
template <class Number, class JsonString>
inline void RawReferences(std::string &out, const ArmyDailyAssaultRawReferencesV1 &p,
                          Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p); w.Boolean("references_ready", p.references_ready);
  w.Integer("count_raw_i32", p.count_raw_i32);
  w.Text("data_identity", p.data_identity); w.Boolean("data_present", p.data_present);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    RawReferenceOccurrence(out, p.occurrences[i], number, string);
  }
  out += ']';
  w.Integer("observed_occurrence_count", p.observed_occurrence_count);
  out += '}';
}
template <class Number, class JsonString>
inline void RelationProbe(std::string &out, const ArmyDailyAssaultRelationProbeV1 &p,
                          Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index); w.Text("kind", p.kind);
  w.Integer("slot_index_i64", p.slot_index_i64);
  w.Integer("key_character_id_raw_u32", p.key_character_id_raw_u32);
  out += '}';
}
template <class Number, class JsonString>
inline void RelationLookup(std::string &out, const ArmyDailyAssaultRelationLookupV1 &p,
                           Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p);
  w.Text("component_identity", p.component_identity);
  w.Boolean("component_present", p.component_present);
  w.Text("table_data_identity", p.table_data_identity);
  w.Boolean("table_data_present", p.table_data_present);
  w.Integer("table_count_raw_i32", p.table_count_raw_i32);
  w.Integer("target_character_full_id_raw_u32", p.target_character_full_id_raw_u32);
  w.Key("probes"); out += '[';
  for (std::size_t i = 0; i < p.probes.size(); ++i) {
    if (i) out += ',';
    RelationProbe(out, p.probes[i], number, string);
  }
  out += ']';
  w.Integer("candidate_slot_index_i64", p.candidate_slot_index_i64);
  w.Text("selection", p.selection);
  w.Text("default_relationship_identity", p.default_relationship_identity);
  w.Boolean("default_relationship_present", p.default_relationship_present);
  w.Text("selected_relationship_identity", p.selected_relationship_identity);
  w.Boolean("selected_relationship_present", p.selected_relationship_present);
  w.Integer("selected_relationship_war_id_raw_u32", p.selected_relationship_war_id_raw_u32);
  out += '}';
}
template <class Number, class JsonString>
inline void AdmissionGate(std::string &out, const ArmyDailyAssaultAdmissionGateV1 &p,
                          Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p); w.Boolean("verdict", p.verdict);
  w.Integer("original_army_unit_id_raw_u32", p.original_army_unit_id_raw_u32);
  w.Key("original_unit_resolution"); OperandResolution(out, p.original_unit_resolution, number, string);
  w.Integer("original_unit_kind_raw_u32", p.original_unit_kind_raw_u32);
  w.Text("original_unit_province_identity", p.original_unit_province_identity);
  w.Boolean("original_unit_province_present", p.original_unit_province_present);
  w.Integer("original_province_identity_raw_u32", p.original_province_identity_raw_u32);
  w.Text("selected_province_comparison_identity", p.selected_province_comparison_identity);
  w.Integer("selected_province_comparison_identity_raw_u32", p.selected_province_comparison_identity_raw_u32);
  w.Integer("original_unit_counter_170_raw_i32", p.original_unit_counter_170_raw_i32);
  w.Integer("associated_army_id_raw_u32", p.associated_army_id_raw_u32);
  w.Key("associated_army_resolution"); OperandResolution(out, p.associated_army_resolution, number, string);
  w.Integer("province_siege_id_raw_u32", p.province_siege_id_raw_u32);
  w.Integer("province_counter_850_raw_i32", p.province_counter_850_raw_i32);
  w.Integer("associated_army_flag_1d4_raw_u8", p.associated_army_flag_1d4_raw_u8);
  w.Integer("associated_army_flag_1ec_raw_u8", p.associated_army_flag_1ec_raw_u8);
  w.Integer("associated_army_unit_id_raw_u32", p.associated_army_unit_id_raw_u32);
  w.Key("associated_unit_resolution"); OperandResolution(out, p.associated_unit_resolution, number, string);
  w.Integer("associated_unit_character_id_raw_u32", p.associated_unit_character_id_raw_u32);
  w.Key("associated_character_resolution"); OperandResolution(out, p.associated_character_resolution, number, string);
  w.Integer("province_character_id_73c_raw_u32", p.province_character_id_73c_raw_u32);
  w.Text("native_2c099f0_character_identity", p.native_2c099f0_character_identity);
  w.Text("native_2c099f0_province_identity", p.native_2c099f0_province_identity);
  w.Boolean("native_2c099f0_third_argument_is_null", p.native_2c099f0_third_argument_is_null);
  w.Boolean("native_2c099f0_returned", p.native_2c099f0_returned);
  w.Integer("native_2c099f0_classification_raw_i32", p.native_2c099f0_classification_raw_i32);
  w.Key("province_character_resolution"); OperandResolution(out, p.province_character_resolution, number, string);
  w.Integer("associated_character_full_id_raw_u32", p.associated_character_full_id_raw_u32);
  w.Integer("province_character_full_id_raw_u32", p.province_character_full_id_raw_u32);
  w.Key("relation_lookup"); RelationLookup(out, p.relation_lookup, number, string);
  w.Key("selected_war_resolution"); OperandResolution(out, p.selected_war_resolution, number, string);
  w.Integer("selected_war_ended_358_raw_u8", p.selected_war_ended_358_raw_u8);
  out += '}';
}
template <class Number, class JsonString>
inline void PendingProbe(std::string &out, const ArmyDailyAssaultPendingProbeV1 &p,
                         Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Integer("native_index", p.native_index);
  w.Integer("physical_slot_i64", p.physical_slot_i64);
  w.Integer("distance_raw_u8", p.distance_raw_u8);
  w.Integer("control_raw_u8", p.control_raw_u8);
  w.Integer("key_raw_full_id_u32", p.key_raw_full_id_u32);
  out += '}';
}
template <class Number, class JsonString>
inline void PendingSelection(std::string &out, const ArmyDailyAssaultPendingSelectionV1 &p,
                             Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p);
  w.Text("entries_identity", p.entries_identity); w.Boolean("entries_present", p.entries_present);
  w.Integer("mask_raw_i32", p.mask_raw_i32);
  w.Integer("tail_distance_raw_u8", p.tail_distance_raw_u8);
  w.Integer("end_slot_raw_i32", p.end_slot_raw_i32);
  w.Integer("target_army_full_id_u32", p.target_army_full_id_u32);
  w.Integer("hash_raw_u32", p.hash_raw_u32); w.Integer("home_slot_i64", p.home_slot_i64);
  w.Key("probes"); out += '[';
  for (std::size_t i = 0; i < p.probes.size(); ++i) {
    if (i) out += ',';
    PendingProbe(out, p.probes[i], number, string);
  }
  out += ']';
  w.Integer("selected_physical_slot_i64", p.selected_physical_slot_i64);
  w.Boolean("selected_is_end_marker", p.selected_is_end_marker);
  w.Integer("selected_control_raw_u8", p.selected_control_raw_u8);
  w.Key("suppression_references"); RawReferences(out, p.suppression_references, number, string);
  out += '}';
}
template <class Number, class JsonString>
inline void ArRgAdmissionOccurrence(std::string &out, const ArmyDailyAssaultArRgAdmissionOccurrenceV1 &p,
                                   Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p); w.Integer("native_index", p.native_index);
  w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Boolean("pending_contains", p.pending_contains); w.Boolean("append", p.append);
  out += '}';
}
template <class Number, class JsonString>
inline void RosterAdmissionOccurrence(std::string &out, const ArmyDailyAssaultRosterAdmissionOccurrenceV1 &p,
                                     Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string};
  w.Status(p); w.Integer("native_index", p.native_index);
  w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("original_army_resolution"); OperandResolution(out, p.original_army_resolution, number, string);
  w.Key("gate"); AdmissionGate(out, p.gate, number, string);
  w.Integer("caller_army_unit_id_raw_u32", p.caller_army_unit_id_raw_u32);
  w.Key("caller_unit_resolution"); OperandResolution(out, p.caller_unit_resolution, number, string);
  w.Text("caller_province_identity", p.caller_province_identity);
  w.Boolean("caller_province_present", p.caller_province_present);
  w.Boolean("caller_used_province_fallback", p.caller_used_province_fallback);
  w.Integer("caller_province_siege_id_raw_u32", p.caller_province_siege_id_raw_u32);
  w.Key("siege_resolution"); OperandResolution(out, p.siege_resolution, number, string);
  w.Integer("siege_flag_44c_raw_u8", p.siege_flag_44c_raw_u8);
  w.Integer("selected_army_full_id_raw_u32", p.selected_army_full_id_raw_u32);
  w.Boolean("removal_contains_selected_army", p.removal_contains_selected_army);
  w.Boolean("army_append_ready", p.army_append_ready); w.Boolean("army_append", p.army_append);
  w.Integer("army_append_siege_full_id_u32", p.army_append_siege_full_id_u32);
  w.Integer("army_append_full_id_u32", p.army_append_full_id_u32);
  w.Key("pending_selection"); PendingSelection(out, p.pending_selection, number, string);
  w.Key("original_arrg_references"); RawReferences(out, p.original_arrg_references, number, string);
  w.Key("arrg_occurrences"); out += '[';
  for (std::size_t i = 0; i < p.arrg_occurrences.size(); ++i) {
    if (i) out += ',';
    ArRgAdmissionOccurrence(out, p.arrg_occurrences[i], number, string);
  }
  out += ']';
  w.Boolean("arrg_append_ready", p.arrg_append_ready);
  w.Key("arrg_append_full_ids_u32");
  if (!p.arrg_append_full_ids_u32) out += "null";
  else {
    out += '[';
    const auto &ids = *p.arrg_append_full_ids_u32;
    for (std::size_t i = 0; i < ids.size(); ++i) {
      if (i) out += ',';
      out += number(ids[i]);
    }
    out += ']';
  }
  out += '}';
}
} // namespace daily_assault_roster_admission_json_detail
template <class Number, class JsonString>
inline void AppendArmyCurrentDailyAssaultRosterAdmissionV1(std::string &out,
    const ArmyCurrentDailyAssaultRosterAdmissionV1 &p, Number number, JsonString jsonstr) {
  using namespace daily_assault_roster_admission_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, jsonstr};
  w.Status(p); w.Integer("schema_version", p.schema_version);
  w.Text("source", p.source); w.Text("stage", p.stage);
  w.Boolean("manager_loaded", p.manager_loaded); w.Text("manager_identity", p.manager_identity);
  w.Key("original_roster"); RawReferences(out, p.original_roster, number, jsonstr);
  w.Key("removal_queue"); RawReferences(out, p.removal_queue, number, jsonstr);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    RosterAdmissionOccurrence(out, p.occurrences[i], number, jsonstr);
  }
  out += ']';
  w.Boolean("raw_roster_references_ready", p.raw_roster_references_ready);
  w.Boolean("original_army_selections_ready", p.original_army_selections_ready);
  w.Boolean("army_appends_ready", p.army_appends_ready);
  w.Boolean("arrg_appends_ready", p.arrg_appends_ready);
  w.Boolean("conditional_admission_ready", p.conditional_admission_ready);
  w.Boolean("actual_next_callback_ready", p.actual_next_callback_ready);
  w.Boolean("actual_tomorrow_roster_ready", p.actual_tomorrow_roster_ready);
  w.Boolean("full_future_table_placement_ready", p.full_future_table_placement_ready);
  w.Boolean("full_daily_assault_ready", p.full_daily_assault_ready);
  out += '}';
}
} // namespace xar::game
