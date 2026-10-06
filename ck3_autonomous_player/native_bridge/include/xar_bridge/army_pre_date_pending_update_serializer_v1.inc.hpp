#pragma once

#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"

namespace xar::game {
namespace pre_date_pending_update_json_detail {
using namespace daily_assault_roster_admission_json_detail;
template <class Number, class JsonString>
inline void PendingPhysicalRecord(std::string &out, const ArmyPreDatePendingPhysicalRecordV1 &p,
    Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("physical_slot_i64", p.physical_slot_i64);
  w.Integer("control_raw_u8", p.control_raw_u8); w.Integer("stored_hash_raw_u32", p.stored_hash_raw_u32);
  w.Integer("key_raw_full_id_u32", p.key_raw_full_id_u32);
  w.Integer("vector_capacity_raw_i32", p.vector_capacity_raw_i32);
  w.Text("vector_allocator_identity", p.vector_allocator_identity);
  w.Boolean("vector_allocator_matches_expected", p.vector_allocator_matches_expected);
  w.Key("references"); RawReferences(out, p.references, number, string); out += '}';
}
template <class Number, class JsonString>
inline void PendingTableFrame(std::string &out, const ArmyPreDatePendingTableFrameV1 &p,
    Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("schema_version", p.schema_version);
  w.Text("entries_identity", p.entries_identity); w.Boolean("entries_present", p.entries_present);
  w.Boolean("data_is_native_empty_buffer", p.data_is_native_empty_buffer);
  w.Integer("map_count_raw_i32", p.map_count_raw_i32); w.Integer("mask_raw_i32", p.mask_raw_i32);
  w.Integer("tail_raw_u8", p.tail_raw_u8); w.Integer("threshold_bits_u32", p.threshold_bits_u32);
  w.Integer("physical_control_extent_last_slot_i64", p.physical_control_extent_last_slot_i64);
  w.Boolean("physical_controls_complete", p.physical_controls_complete);
  w.Boolean("rehash_prefix_complete", p.rehash_prefix_complete);
  w.Integer("rehash_nonzero_records_observed_i32", p.rehash_nonzero_records_observed_i32);
  w.Key("records"); out += '[';
  for (std::size_t i = 0; i < p.records.size(); ++i) {
    if (i) out += ',';
    PendingPhysicalRecord(out, p.records[i], number, string);
  }
  out += ']'; out += '}';
}
template <class Number, class JsonString>
inline void PendingArRg(std::string &out, const ArmyPreDatePendingArRgV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("arrg_resolution"); OperandResolution(out, p.arrg_resolution, number, string);
  w.Integer("current_38_raw_i32", p.current_38_raw_i32);
  w.Integer("contract_id_144_raw_u32", p.contract_id_144_raw_u32);
  w.Key("contract_resolution"); OperandResolution(out, p.contract_resolution, number, string);
  w.Integer("contract_flag_b9_raw_u8", p.contract_flag_b9_raw_u8);
  w.Integer("state_14c_raw_i32", p.state_14c_raw_i32);
  w.Text("original_data_identity", p.original_data_identity); w.Boolean("original_data_present", p.original_data_present);
  w.Integer("first_persistent_id_raw_u32", p.first_persistent_id_raw_u32);
  w.Key("persistent_resolution"); OperandResolution(out, p.persistent_resolution, number, string);
  w.Integer("persistent_war_id_13c_raw_u32", p.persistent_war_id_13c_raw_u32);
  w.Key("war_resolution"); OperandResolution(out, p.war_resolution, number, string);
  w.Integer("war_magic_0c_raw_u32", p.war_magic_0c_raw_u32);
  w.Boolean("append_to_pending", p.append_to_pending); w.Integer("append_full_id_u32", p.append_full_id_u32);
  out += '}';
}
template <class Number, class JsonString>
inline void PendingSetup(std::string &out, const ArmyPreDatePendingSetupV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Text("entries_identity", p.entries_identity); w.Boolean("entries_present", p.entries_present);
  w.Integer("mask_raw_i32", p.mask_raw_i32);
  w.Integer("target_army_full_id_u32", p.target_army_full_id_u32); w.Integer("hash_raw_u32", p.hash_raw_u32);
  w.Integer("home_slot_i64", p.home_slot_i64); w.Integer("terminal_physical_slot_i64", p.terminal_physical_slot_i64);
  w.Key("probes"); out += '[';
  for (std::size_t i = 0; i < p.probes.size(); ++i) {
    if (i) out += ',';
    PendingProbe(out, p.probes[i], number, string);
  }
  out += ']'; w.Boolean("existing_key", p.existing_key);
  w.Key("existing_references"); RawReferences(out, p.existing_references, number, string);
  w.Integer("map_count_raw_i32", p.map_count_raw_i32);
  w.Integer("insertion_tail_raw_u8", p.insertion_tail_raw_u8);
  w.Integer("insertion_threshold_bits_u32", p.insertion_threshold_bits_u32); out += '}';
}
template <class Number, class JsonString>
inline void PendingOccurrence(std::string &out, const ArmyPreDatePendingOccurrenceV1 &p, Number number, JsonString string) {
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Integer("raw_full_id_u32", p.raw_full_id_u32);
  w.Key("original_army_resolution"); OperandResolution(out, p.original_army_resolution, number, string);
  w.Integer("combat_id_128_raw_u32", p.combat_id_128_raw_u32);
  w.Key("combat_resolution"); OperandResolution(out, p.combat_resolution, number, string);
  w.Integer("combat_magic_0c_raw_u32", p.combat_magic_0c_raw_u32);
  w.Integer("army_counter_5c_raw_i32", p.army_counter_5c_raw_i32);
  w.Boolean("pending_mutator_selected", p.pending_mutator_selected);
  w.Key("pending_setup"); PendingSetup(out, p.pending_setup, number, string);
  w.Key("original_arrg_references"); RawReferences(out, p.original_arrg_references, number, string);
  w.Key("arrg_occurrences"); out += '[';
  for (std::size_t i = 0; i < p.arrg_occurrences.size(); ++i) {
    if (i) out += ',';
    PendingArRg(out, p.arrg_occurrences[i], number, string);
  }
  out += ']'; out += '}';
}
} // namespace pre_date_pending_update_json_detail
template <class Number, class JsonString>
inline void AppendArmyCurrentPreDatePendingUpdateInputsV1(std::string &out,
    const ArmyCurrentPreDatePendingUpdateInputsV1 &p, Number number, JsonString string) {
  using namespace pre_date_pending_update_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, number, string}; w.Status(p);
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Boolean("manager_loaded", p.manager_loaded); w.Text("manager_identity", p.manager_identity);
  w.Key("original_roster"); RawReferences(out, p.original_roster, number, string);
  w.Key("removal_queue"); RawReferences(out, p.removal_queue, number, string);
  w.Key("occurrences"); out += '[';
  for (std::size_t i = 0; i < p.occurrences.size(); ++i) {
    if (i) out += ',';
    PendingOccurrence(out, p.occurrences[i], number, string);
  }
  out += ']';
  w.Boolean("raw_roster_references_ready", p.raw_roster_references_ready);
  w.Boolean("source_operands_ready", p.source_operands_ready);
  w.Boolean("actual_pre_date_callback_ready", p.actual_pre_date_callback_ready);
  w.Boolean("actual_tomorrow_roster_ready", p.actual_tomorrow_roster_ready);
  w.Boolean("full_daily_assault_ready", p.full_daily_assault_ready); w.Boolean("full_monthly_ready", p.full_monthly_ready);
  if (p.pending_table_frame_v1) {
    w.Key("pending_table_frame_v1"); PendingTableFrame(out, *p.pending_table_frame_v1, number, string);
  }
  out += '}';
}
} // namespace xar::game
