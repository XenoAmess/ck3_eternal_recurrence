#pragma once
#include "xar_bridge/actual_army_pre_date_prefix_observer_12004.hpp"
#include <sstream>
#include <string>
namespace xar::ck3_12004 {
inline std::string SerializeActualArmyPreDatePrefixObservations12004(const ActualArmyPreDatePrefixObservations12004 &journal) {
  std::ostringstream out;out<<std::boolalpha;
  const auto optional=[&](const auto &v){if(v)out<<+*v;else out<<"null";};
  const auto event=[&](const ArmyNaturalPhaseEvent12004 &e){out<<"{\"clock_identity\":"<<e.clock_identity<<",\"sequence\":"<<e.sequence<<",\"thread_id\":";optional(e.thread_id);out<<'}';};
  const auto ids=[&](const auto &v){out<<'[';for(std::size_t i=0;i<v.size();++i){if(i)out<<',';out<<v[i];}out<<']';};
  const auto queue=[&](const ActualArmyPreDatePrefixQueue12004 &q){
    out<<"{\"data_identity\":";optional(q.data_identity);out<<",\"end_identity\":";optional(q.end_identity);
    out<<",\"capacity_raw_i32\":";optional(q.capacity);out<<",\"count_raw_i32\":";optional(q.count);
    out<<",\"bounds_valid\":";if(q.bounds_valid)out<<*q.bounds_valid;else out<<"null";
    out<<",\"copy_bound_admitted\":";if(q.copy_bound_admitted)out<<*q.copy_bound_admitted;else out<<"null";
    out<<",\"copied_complete\":"<<q.copied_complete<<",\"ordered_full_ids\":";ids(q.ordered_full_ids);out<<'}';
  };
  const auto snapshot=[&](const ActualArmyPreDatePrefixSnapshot12004 &s){
    out<<"{\"source_c8\":";queue(s.source_c8);out<<",\"destination_158\":";queue(s.destination_158);
    out<<",\"supplied_date_raw_u64\":";optional(s.supplied_date_raw_u64);out<<",\"game_date_raw_u64\":";optional(s.game_date_raw_u64);
    out<<",\"absolute_day_raw_u32\":";optional(s.absolute_day_raw_u32);out<<",\"calendar_c0_raw_u8\":";optional(s.calendar_c0_raw_u8);
    out<<",\"conditional_no_work_arm\":";if(s.conditional_no_work_arm)out<<*s.conditional_no_work_arm;else out<<"null";
    out<<",\"positive_physical_transition_complete\":"<<s.positive_physical_transition_complete<<'}';
  };
  out<<"{\"observer_installed\":"<<journal.observer_installed<<",\"current_session_guard\":"<<journal.current_session_guard
    <<",\"oldest_available_sequence\":"<<journal.oldest_available_sequence<<",\"latest_sequence\":"<<journal.latest_sequence
    <<",\"overwritten_events\":"<<journal.overwritten_events<<",\"unattributed_capture_failures\":"<<journal.unattributed_capture_failures<<",\"events\":[";
  for(std::size_t i=0;i<journal.events.size();++i){const auto &e=journal.events[i];if(i)out<<',';
    out<<"{\"sequence\":"<<e.sequence<<",\"primary_manager_identity\":"<<e.primary_manager_identity<<",\"date_argument_identity\":"<<e.date_argument_identity
      <<",\"caller_return_rva\":"<<e.caller_return_rva<<",\"parent_bound\":"<<e.parent_bound<<",\"parent_entry_event\":";event(e.parent.entry_event);
    out<<",\"parent\":{\"observed\":"<<e.parent.observed<<",\"phase_raw\":"<<static_cast<unsigned>(e.parent.phase)
      <<",\"actual_entry_rva\":"<<e.parent.actual_entry_rva<<",\"caller_return_rva\":"<<e.parent.caller_return_rva
      <<",\"primary_manager_identity\":"<<e.parent.primary_manager_identity<<",\"secondary_manager_identity\":"<<e.parent.secondary_manager_identity
      <<",\"game_state_identity\":"<<e.parent.game_state_identity<<",\"date_raw_u64\":";optional(e.parent.date_raw);
    out<<",\"absolute_day_raw_u32\":";optional(e.parent.absolute_day_raw);out<<'}';
    out<<",\"entry_event\":";event(e.entry_event);out<<",\"returned_event\":";event(e.returned_event);
    out<<",\"original_called\":"<<e.original_called<<",\"original_returned\":"<<e.original_returned<<",\"incoming_rax_raw_u64\":"<<e.incoming_rax_raw_u64
      <<",\"original_rax_raw_u64\":"<<e.original_rax_raw_u64<<",\"capture_failure_flags\":"<<e.capture_failure_flags<<",\"before\":";snapshot(e.before);
    out<<",\"after\":";snapshot(e.after);const auto &r=e.captured_original_roster;
    out<<",\"original_roster_capture_complete\":"<<e.original_roster_capture_complete<<",\"captured_original_roster\":{\"boundary_raw\":"<<static_cast<unsigned>(r.boundary)
      <<",\"capture_rva\":"<<r.capture_rva<<",\"capture_event\":";event(r.capture_event);out<<",\"begin_identity\":";optional(r.begin_identity);
    out<<",\"end_identity\":";optional(r.end_identity);out<<",\"count_raw_i32\":";optional(r.count);
    out<<",\"complete\":"<<r.complete<<",\"ordered_full_ids\":";ids(r.ordered_full_ids);out<<"}}";
  }out<<"]}";return out.str();
}
} // namespace xar::ck3_12004
