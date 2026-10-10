#pragma once
#include "xar_bridge/army_natural_phase_json_12004.hpp"
#include "xar_bridge/actual_army_daily_assault_preparation_observer_12004.hpp"
#include "xar_bridge/actual_army_assault_placement_observer_12004.hpp"
#include "xar_bridge/army_daily_assault_active_table_serializer_v1.inc.hpp"
#include "xar_bridge/army_daily_assault_roster_admission_serializer_v1.inc.hpp"
#include <sstream>

namespace xar::game::observed_assault_json_12004 {
template<class N, class S> using Writer = daily_assault_roster_admission_json_detail::Writer<N,S>;
template<class T, class F> void Array(std::string &out, const std::vector<T> &items, F emit) {
  out += '['; bool first = true;
  for (const auto &item : items) { if (!first) out += ','; first = false; emit(item); }
  out += ']';
}
inline void Token(std::string &out, const ck3_12004::ArmyNaturalPhaseEvent12004 &event) {
  std::ostringstream stream; ck3_12004::AppendArmyNaturalPhaseEvent12004(stream,event); out += stream.str();
}
inline void Scope(std::string &out, const ck3_12004::ArmyNaturalPhaseScope12004 &scope) {
  std::ostringstream stream; ck3_12004::AppendArmyNaturalPhaseScope12004(stream,scope); out += stream.str();
}
template<class N, class S> void Boundary(std::string &out, const ck3_12004::DailyAssaultPreparationBoundary12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("query_sequence",v.query_sequence);
  w.Integer("game_date_raw_i32",v.game_date_raw_i32);
  w.Integer("absolute_day_raw_i32",v.absolute_day_raw_i32);
  w.Integer("calendar_flags_raw_u8",v.calendar_flags_raw_u8);
  w.Integer("callsite_rva",v.callsite_rva);
  w.Integer("native_occurrence_index",v.native_occurrence_index);
  w.Text("executable_sha256",v.executable_sha256);
  w.Text("frame_identity",v.frame_identity);
  w.Text("primary_manager_identity",v.primary_manager_identity);
  w.Text("original_roster_capture_identity",v.original_roster_capture_identity);
  w.Text("selected_army_identity",v.selected_army_identity);
  w.Text("stage",v.stage == ck3_12004::DailyAssaultPreparationStage12004::pre_date_assault_call ? std::string("pre_date_assault_call") : std::string("current_query"));
  out += '}';
}
template<class N, class S> void AppendInput(std::string &out, const ck3_12004::DailyAssaultPreparationAppendInput12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("native_occurrence_index",v.native_occurrence_index);
  w.Integer("requested_army_full_id_u32",v.requested_army_full_id_u32);
  w.Integer("selected_siege_full_id_u32",v.selected_siege_full_id_u32);
  w.Integer("selected_army_full_id_u32",v.selected_army_full_id_u32);
  w.Integer("selected_siege_fnv1a_u32",v.selected_siege_fnv1a_u32);
  w.Boolean("army_append_input_ready",v.army_append_input_ready);
  w.Boolean("army_append",v.army_append);
  w.Boolean("arrg_append_inputs_ready",v.arrg_append_inputs_ready);
  w.Key("ordered_arrg_full_ids_u32");
  if (!v.ordered_arrg_full_ids_u32) out += "null";
  else Array(out,*v.ordered_arrg_full_ids_u32,[&](auto id){out += number(id);});
  out += '}';
}
template<class N, class S> void PreparationInput(std::string &out, const ck3_12004::DailyAssaultPreparationInput12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Boolean("boundary_binding_ready",v.boundary_binding_ready);
  w.Boolean("ordered_append_inputs_ready",v.ordered_append_inputs_ready);
  w.Boolean("current_group_frame_matches",v.current_group_frame_matches);
  w.Boolean("current_group_records_ready",v.current_group_records_ready);
  w.Boolean("actual_callback_execution_observed",v.actual_callback_execution_observed);
  w.Boolean("full_future_table_placement_ready",v.full_future_table_placement_ready);
  w.Boolean("full_daily_assault_ready",v.full_daily_assault_ready);
  w.Boolean("full_monthly_execution_ready",v.full_monthly_execution_ready);
  w.Text("source",v.source);
  w.Text("unavailable_reason",v.unavailable_reason);
  w.Key("boundary"); Boundary(out,v.boundary,number,string);
  w.Key("original_roster"); daily_assault_roster_admission_json_detail::RawReferences(out,v.original_roster,number,string);
  w.Key("removal_queue"); daily_assault_roster_admission_json_detail::RawReferences(out,v.removal_queue,number,string);
  w.Key("occurrence_inputs"); Array(out,v.occurrence_inputs,[&](const auto &x){daily_assault_roster_admission_json_detail::RosterAdmissionOccurrence(out,x,number,string);});
  w.Key("ordered_append_inputs"); Array(out,v.ordered_append_inputs,[&](const auto &x){AppendInput(out,x,number,string);});
  w.Key("current_group_records"); if(v.current_group_records) AppendArmyCurrentDailyAssaultTableV1(out,*v.current_group_records,number,string); else out += "null";
  out += '}';
}
template<class N, class S> void PreparationActive(std::string &out, const ck3_12004::ActualArmyDailyAssaultPreparationActive12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("incoming_primary_manager",v.incoming_primary_manager);
  w.Integer("incoming_selected_army",v.incoming_selected_army);
  w.Integer("caller_return_rva",v.caller_return_rva);
  w.Integer("callsite_rva",v.callsite_rva);
  w.Integer("actual_caller_iterator",v.actual_caller_iterator);
  w.Integer("actual_caller_end",v.actual_caller_end);
  w.Integer("native_occurrence_index",v.native_occurrence_index);
  w.Integer("local_start_index",v.local_start_index);
  w.Integer("requested_army_full_id_u32",v.requested_army_full_id_u32);
  w.Integer("iterator_entry_full_id_u32",v.iterator_entry_full_id_u32);
  w.Integer("selected_army_full_id_raw_u32",v.selected_army_full_id_raw_u32);
  w.Boolean("observed",v.observed);
  w.Boolean("parent_bound",v.parent_bound);
  w.Boolean("original_occurrence_bound",v.original_occurrence_bound);
  w.Key("parent"); Scope(out,v.parent);
  w.Key("entry_event"); Token(out,v.entry_event);
  out += '}';
}
template<class N, class S> void PreparationSnapshot(std::string &out, const ck3_12004::ActualArmyDailyAssaultPreparationSnapshot12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("selected_army_full_id_raw_u32",v.selected_army_full_id_raw_u32);
  w.Integer("game_state_identity_raw",v.game_state_identity_raw);
  w.Integer("game_date_raw_u64",v.game_date_raw_u64);
  w.Integer("absolute_day_raw_u32",v.absolute_day_raw_u32);
  w.Integer("calendar_flags_raw_u8",v.calendar_flags_raw_u8);
  w.Boolean("game_state_matches_parent",v.game_state_matches_parent);
  w.Boolean("source_inputs_ready",v.source_inputs_ready);
  w.Key("selected_occurrence"); daily_assault_roster_admission_json_detail::RosterAdmissionOccurrence(out,v.selected_occurrence,number,string);
  w.Key("removal_queue"); daily_assault_roster_admission_json_detail::RawReferences(out,v.removal_queue,number,string);
  w.Key("copied_stage_input"); if(v.copied_stage_input) PreparationInput(out,*v.copied_stage_input,number,string); else out += "null";
  out += '}';
}
template<class N, class S> void PreparationEvent(std::string &out, const ck3_12004::ActualArmyDailyAssaultPreparationObservation12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("sequence",v.sequence);
  w.Integer("original_rax_raw_u64",v.original_rax_raw_u64);
  w.Integer("capture_failure_flags",v.capture_failure_flags);
  w.Boolean("original_called",v.original_called);
  w.Boolean("original_returned",v.original_returned);
  w.Boolean("same_selected_army_generation_after",v.same_selected_army_generation_after);
  w.Key("active"); PreparationActive(out,v.active,number,string);
  w.Key("before"); PreparationSnapshot(out,v.before,number,string);
  w.Key("after"); PreparationSnapshot(out,v.after,number,string);
  w.Key("returned_event"); Token(out,v.returned_event);
  out += '}';
}
template<class N, class S> void PlacementSnapshot(std::string &out, const ck3_12004::ActualArmyAssaultPlacementSnapshot12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("receiver_table_identity",v.receiver_table_identity);
  w.Integer("entries_identity",v.entries_identity);
  w.Integer("occupied_count_raw_i32",v.occupied_count_raw_i32);
  w.Integer("mask_raw_i32",v.mask_raw_i32);
  w.Integer("tail_distance_raw_u8",v.tail_distance_raw_u8);
  w.Integer("load_factor_f32_bits_u32",v.load_factor_f32_bits_u32);
  w.Integer("table_allocator_identity",v.table_allocator_identity);
  w.Integer("read_calls",v.read_calls);
  w.Integer("read_bytes",v.read_bytes);
  w.Integer("admitted_reference_count",v.admitted_reference_count);
  w.Boolean("native_empty_storage_matches",v.native_empty_storage_matches);
  w.Boolean("current_primary_table_matches_receiver",v.current_primary_table_matches_receiver);
  w.Boolean("capture_complete",v.capture_complete);
  w.Boolean("budget_exhausted",v.budget_exhausted);
  w.Text("stage",v.stage);
  w.Key("capture_event"); Token(out,v.capture_event);
  w.Key("physical_table"); AppendArmyCurrentDailyAssaultTableV1(out,v.physical_table,number,string);
  w.Key("denied_vector_counts"); Array(out,v.denied_vector_counts,[&](const auto &x){out += '{'; Writer<N,S> d{out,number,string}; d.Integer("physical_slot_i64",x.physical_slot_i64); d.Boolean("arrg",x.arrg); d.Integer("actual_count_raw_i32",x.actual_count_raw_i32); out += '}';});
  out += '}';
}
template<class N, class S> void PlacementEvent(std::string &out, const ck3_12004::ActualArmyAssaultPlacementObservation12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("sequence",v.sequence);
  w.Integer("caller_return_rva",v.caller_return_rva);
  w.Integer("incoming_table_identity",v.incoming_table_identity);
  w.Integer("incoming_output_identity",v.incoming_output_identity);
  w.Integer("incoming_key_identity",v.incoming_key_identity);
  w.Integer("incoming_hash_raw_u32",v.incoming_hash_raw_u32);
  w.Integer("incoming_key_raw_u32",v.incoming_key_raw_u32);
  w.Integer("selected_army_full_id_at_placement_u32",v.selected_army_full_id_at_placement_u32);
  w.Integer("original_rax_raw_u64",v.original_rax_raw_u64);
  w.Integer("returned_entry_identity",v.returned_entry_identity);
  w.Integer("returned_inserted_raw_u8",v.returned_inserted_raw_u8);
  w.Integer("returned_physical_slot_i64",v.returned_physical_slot_i64);
  w.Integer("capture_failure_flags",v.capture_failure_flags);
  w.Boolean("entries_identity_changed",v.entries_identity_changed);
  w.Boolean("parent_bound",v.parent_bound);
  w.Boolean("recursive",v.recursive);
  w.Boolean("original_called",v.original_called);
  w.Boolean("original_returned",v.original_returned);
  w.Key("preparation"); PreparationActive(out,v.preparation,number,string);
  w.Key("entry_event"); Token(out,v.entry_event); w.Key("returned_event"); Token(out,v.returned_event);
  w.Key("before"); PlacementSnapshot(out,v.before,number,string);
  w.Key("after"); PlacementSnapshot(out,v.after,number,string);
  out += '}';
}
template<class N, class S> void PlacementResult(std::string &out, const ck3_12004::AssaultPlacementResult12004 &v, N number, S string) {
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("applied_request_count",v.applied_request_count);
  w.Integer("zero_control_extent_end_i64",v.zero_control_extent_end_i64);
  w.Boolean("ready",v.ready);
  w.Boolean("unspecified_controls_zero",v.unspecified_controls_zero);
  w.Boolean("projected_physical_group_order_ready",v.projected_physical_group_order_ready);
  w.Boolean("normal_return_premise",v.normal_return_premise);
  w.Boolean("actual_callback_execution_observed",v.actual_callback_execution_observed);
  w.Boolean("full_future_table_placement_ready",v.full_future_table_placement_ready);
  w.Boolean("full_daily_assault_ready",v.full_daily_assault_ready);
  w.Boolean("full_monthly_execution_ready",v.full_monthly_execution_ready);
  w.Text("source",v.source);
  w.Text("stage",v.stage);
  w.Text("frame_identity",v.frame_identity);
  w.Text("source_provenance",v.source_provenance);
  w.Text("unavailable_reason",v.unavailable_reason);
  w.Key("observed_current_table"); if(v.observed_current_table) AppendArmyCurrentDailyAssaultTableV1(out,*v.observed_current_table,number,string); else out += "null";
  w.Key("projected_header"); daily_assault_table_json_detail::Header(out,v.projected_header,number,string);
  w.Key("projected_physical_controls"); Array(out,v.projected_physical_controls,[&](const auto &x){out += '{'; Writer<N,S> d{out,number,string};d.Integer("physical_slot_i64",x.physical_slot_i64);d.Integer("control_raw_u8",x.control_raw_u8);d.Text("unavailable_reason",x.unavailable_reason);out += '}';});
  w.Key("projected_groups"); Array(out,v.projected_groups,[&](const auto &x){out += '{'; Writer<N,S> d{out,number,string};d.Key("value");daily_assault_table_json_detail::Group(out,x.value,number,string);d.Boolean("army_allocator_canonical_by_source",x.army_allocator_canonical_by_source);d.Boolean("arrg_allocator_canonical_by_source",x.arrg_allocator_canonical_by_source);out += '}';});
  w.Key("growth"); Array(out,v.growth,[&](const auto &x){out += '{'; Writer<N,S> d{out,number,string};d.Integer("source_rva",x.source_rva);d.Integer("index_i32",x.index_i32);d.Integer("old_occupied_count_i32",x.old_occupied_count_i32);d.Integer("new_mask_i32",x.new_mask_i32);d.Integer("new_end_slot_i32",x.new_end_slot_i32);d.Integer("new_tail_u8",x.new_tail_u8);d.Integer("allocated_record_count",x.allocated_record_count);d.Integer("allocated_bytes",x.allocated_bytes);d.Text("symbolic_storage_identity",x.symbolic_storage_identity);d.Boolean("old_table_release_selected",x.old_table_release_selected);d.Key("old_reinsert_physical_order");Array(out,x.old_reinsert_physical_order,[&](auto id){out += number(id);});out += '}';});
  w.Key("growth_release_inputs"); Array(out,v.growth_release_inputs,[&](const auto &x){out += '{';Writer<N,S>d{out,number,string};d.Integer("growth_index",x.growth_index);d.Integer("old_physical_slot_i64",x.old_physical_slot_i64);d.Integer("callsite_rva",x.callsite_rva);d.Text("stage",x.stage);d.Boolean("source_value_moved",x.source_value_moved);d.Key("armies_after_transfer");daily_assault_table_json_detail::References(out,x.armies_after_transfer,number,string);d.Key("arrgs_after_transfer");daily_assault_table_json_detail::References(out,x.arrgs_after_transfer,number,string);out += '}';});
  w.Key("requests"); Array(out,v.requests,[&](const auto &x){out += '{'; Writer<N,S>d{out,number,string};d.Integer("native_occurrence_index",x.native_occurrence_index);d.Text("status",x.status);d.Text("branch",x.branch);d.Text("unavailable_reason",x.unavailable_reason);d.Integer("returned_physical_slot_i64",x.returned_physical_slot_i64);d.Boolean("inserted",x.inserted);out += '}';});
  out += '}';
}
} // namespace xar::game::observed_assault_json_12004
namespace xar::game {
template<class N,class S> void AppendActualArmyDailyAssaultPreparationObservations12004(std::string &out,
    const ck3_12004::ActualArmyDailyAssaultPreparationObservations12004 &v,N number,S string) {
  using namespace observed_assault_json_12004;
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("schema_version",1); w.Text("source",std::string("native_natural_army_daily_assault_preparation_entry_return"));
  w.Text("membership_basis",std::string("captured_before_selected_CArmy_full_id"));
  w.Boolean("observer_installed",v.observer_installed); w.Boolean("current_session_guard",v.current_session_guard);
  w.Integer("oldest_available_sequence",v.oldest_available_sequence); w.Integer("latest_sequence",v.latest_sequence);
  w.Integer("overwritten_events",v.overwritten_events); w.Integer("unattributed_capture_failures",v.unattributed_capture_failures);
  w.Integer("dropped_owned_copy_events",v.dropped_owned_copy_events);
  w.Key("events"); Array(out,v.events,[&](const auto &x){PreparationEvent(out,x,number,string);}); out += '}';
}
template<class N,class S> void AppendActualArmyAssaultPlacementObservations12004(std::string &out,
    const ck3_12004::ActualArmyAssaultPlacementObservations12004 &v,
    const std::optional<ck3_12004::ActualArmyDailyAssaultPreparationObservations12004> &preparation,N number,S string) {
  using namespace observed_assault_json_12004;
  out += '{'; Writer<N,S> w{out,number,string};
  w.Integer("schema_version",1); w.Text("source",std::string("native_natural_army_assault_placement_entry_return"));
  w.Text("membership_basis",std::string("captured_selected_CArmy_full_id"));
  w.Boolean("observer_installed",v.observer_installed); w.Boolean("current_session_guard",v.current_session_guard);
  w.Integer("oldest_available_sequence",v.oldest_available_sequence); w.Integer("latest_sequence",v.latest_sequence);
  w.Integer("overwritten_events",v.overwritten_events); w.Integer("unattributed_capture_failures",v.unattributed_capture_failures);
  w.Key("events"); Array(out,v.events,[&](const auto &x){PlacementEvent(out,x,number,string);});
  w.Key("conditional_preparation_append_projections"); Array(out,v.events,[&](const auto &x){
    out += '{'; Writer<N,S> d{out,number,string};d.Integer("placement_sequence",x.sequence);
    ck3_12004::ActualArmyAssaultPlacementProjection12004 mapped;
    mapped.unavailable_reason = "installed_owned_preparation_and_placement_join_unavailable";
    const ck3_12004::ActualArmyDailyAssaultPreparationObservation12004 *matched = nullptr;
    if (v.observer_installed && v.current_session_guard && preparation && preparation->observer_installed && preparation->current_session_guard) {
      for (const auto &p : preparation->events) {
        const auto &a = p.active.entry_event; const auto &b = x.preparation.entry_event;
        if (a.clock_identity == b.clock_identity && a.sequence == b.sequence && a.thread_id == b.thread_id) {
          if (matched) { matched = nullptr; mapped.unavailable_reason = "ambiguous_owned_preparation_event"; break; }
          matched = &p;
        }
      }
      if (matched) mapped = ck3_12004::ProjectActualArmyAssaultPlacementObservation12004(x,*matched);
    }
    d.Key("matched_preparation_event");
    if(matched) PreparationEvent(out,*matched,number,string); else out += "null";
    d.Boolean("mapping_ready",mapped.mapping_ready);d.Text("unavailable_reason",mapped.unavailable_reason);
    d.Text("projected_stage",mapped.projected_stage);d.Key("projection");
    if(mapped.projection) PlacementResult(out,*mapped.projection,number,string); else out += "null";
    out += '}';
  }); out += '}';
}
} // namespace xar::game
