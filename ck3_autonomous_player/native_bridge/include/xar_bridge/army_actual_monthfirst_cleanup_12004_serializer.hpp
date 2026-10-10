#pragma once

#include "xar_bridge/army_actual_monthfirst_cleanup_12004.hpp"
#include <charconv>
#include <string>

namespace xar::ck3_12004::army_actual_monthfirst_cleanup_json_detail {
template<class T> inline void Number(std::string &out,T value) {
  char buffer[32];const auto converted=std::to_chars(buffer,buffer+sizeof(buffer),value);
  out.append(buffer,converted.ptr);
}
inline void Value(std::string &out,bool value) {out+=value ? "true" : "false";}
template<class T> inline void Value(std::string &out,T value) {Number(out,value);}
template<class T> inline void Optional(std::string &out,const std::optional<T> &value) {
  if(value)Value(out,*value);else out+="null";
}
inline void String(std::string &out,std::string_view value) {
  constexpr char digits[]="0123456789abcdef";
  out+='"';
  for(const char raw:value) {
    const auto c=static_cast<unsigned char>(raw);
    if(c=='"' || c=='\\') {out+='\\';out+=static_cast<char>(c);}
    else if(c<0x20U) {out+="\\u00";out+=digits[c>>4];out+=digits[c&0xFU];}
    else out+=static_cast<char>(c);
  }
  out+='"';
}
inline void Event(std::string &out,const ArmyNaturalPhaseEvent12004 &e) {
  out+="{\"clock_identity\":";Number(out,e.clock_identity);
  out+=",\"sequence\":";Number(out,e.sequence);
  out+=",\"thread_id\":";Optional(out,e.thread_id);out+='}';
}
inline void Phase(std::string &out,const ArmyNaturalPhaseScope12004 &p) {
  out+="{\"observed\":";Value(out,p.observed);
  out+=",\"phase\":";
  String(out,p.phase==ArmyNaturalPhaseKind12004::post_date ? "post_date" :
             p.phase==ArmyNaturalPhaseKind12004::pre_date ? "pre_date" : "unknown");
  out+=",\"actual_entry_rva\":";Number(out,p.actual_entry_rva);
  out+=",\"caller_return_rva\":";Number(out,p.caller_return_rva);
  out+=",\"primary_manager_identity\":";Number(out,p.primary_manager_identity);
  out+=",\"secondary_manager_identity\":";Number(out,p.secondary_manager_identity);
  out+=",\"game_state_identity\":";Number(out,p.game_state_identity);
  out+=",\"session_identity\":";Optional(out,p.session_identity);
  out+=",\"entry_event\":";Event(out,p.entry_event);
  out+=",\"date_raw\":";Optional(out,p.date_raw);
  out+=",\"prefix_date_raw\":";Optional(out,p.prefix_date_raw);
  out+=",\"absolute_day_raw\":";Optional(out,p.absolute_day_raw);
  out+=",\"entry_c0_raw\":";Optional(out,p.entry_c0_raw);
  out+=",\"saved_c0_raw\":";Optional(out,p.saved_c0_raw);
  out+=",\"saved_mask02_admitted\":";Optional(out,p.saved_mask02_admitted);
  out+=",\"saved_c0_observed_rva\":";Number(out,p.saved_c0_observed_rva);
  out+=",\"saved_c0_event\":";Event(out,p.saved_c0_event);
  const auto &r=p.original_army_roster;
  out+=",\"original_army_roster\":{\"boundary\":";
  String(out,r.boundary==ArmyNaturalRosterBoundary12004::parent_entry ? "parent_entry" :
             r.boundary==ArmyNaturalRosterBoundary12004::pre_date_prefix_return ? "pre_date_prefix_return" : "unavailable");
  out+=",\"capture_rva\":";Number(out,r.capture_rva);
  out+=",\"capture_event\":";Event(out,r.capture_event);
  out+=",\"begin_identity\":";Optional(out,r.begin_identity);
  out+=",\"end_identity\":";Optional(out,r.end_identity);
  out+=",\"count\":";Optional(out,r.count);
  out+=",\"complete\":";Value(out,r.complete);
  out+=",\"copied_occurrence_count\":";Number(out,r.ordered_full_ids.size());
  out+=",\"ordered_full_ids\":[";
  bool first=true;for(const auto id:r.ordered_full_ids) {if(!first)out+=',';first=false;Number(out,id);}
  out+="]}}";
}
inline void Slot(std::string &out,const ArmyActualMonthfirstCleanupSlot12004 &s) {
  out+="{\"physical_index\":";Number(out,s.physical_index);
  out+=",\"record_identity\":";Number(out,s.record_identity);
  out+=",\"vtable_identity\":";Optional(out,s.vtable_identity);
  out+=",\"slot0_target_identity\":";Optional(out,s.slot0_target_identity);
  out+=",\"slot0_matches_known_mode0_source\":";Optional(out,s.slot0_matches_known_mode0_source);
  out+=",\"requested_regi_full_id\":";Optional(out,s.requested_regi_full_id);
  out+=",\"ordinal\":";Optional(out,s.ordinal);
  out+=",\"selection\":";
  String(out,s.selection==ArmyActualMonthfirstCleanupSelection12004::registry_full_generation ? "registry_full_generation" :
             s.selection==ArmyActualMonthfirstCleanupSelection12004::native_fallback ? "native_fallback" : "unavailable");
  out+=",\"indexed_regi_full_id\":";Optional(out,s.indexed_regi_full_id);
  out+=",\"selected_regi_full_id\":";Optional(out,s.selected_regi_full_id);
  out+=",\"selected_magic_14\":";Optional(out,s.selected_magic_14);
  out+=",\"selected_regi_identity\":";Optional(out,s.selected_regi_identity);
  out+=",\"selected_regi_valid\":";Optional(out,s.selected_regi_valid);
  out+=",\"computed_chunk_identity\":";Optional(out,s.computed_chunk_identity);
  out+=",\"date_1c_raw64\":";Optional(out,s.date_1c_raw64);
  out+=",\"complete\":";Value(out,s.complete);
  out+=",\"unavailable_reason\":";String(out,s.unavailable_reason);out+='}';
}
inline void Frame(std::string &out,const ArmyActualMonthfirstCleanupFrame12004 &f) {
  out+="{\"primary_manager_identity\":";Number(out,f.primary_manager_identity);
  out+=",\"header_identity\":";Number(out,f.header_identity);
  out+=",\"passed_date_pointer_identity\":";Number(out,f.passed_date_pointer_identity);
  out+=",\"passed_date_raw64\":";Optional(out,f.passed_date_raw64);
  out+=",\"buffer_identity\":";Optional(out,f.buffer_identity);
  out+=",\"live_count_raw_i32\":";Optional(out,f.live_count_raw_i32);
  out+=",\"copied_physical_extent\":";Number(out,f.copied_physical_extent);
  out+=",\"header_complete\":";Value(out,f.header_complete);
  out+=",\"physical_copy_complete\":";Value(out,f.physical_copy_complete);
  out+=",\"complete\":";Value(out,f.complete);
  out+=",\"truncated\":";Value(out,f.truncated);
  out+=",\"original_backing_address_preserved\":";Optional(out,f.original_backing_address_preserved);
  out+=",\"unavailable_reason\":";String(out,f.unavailable_reason);
  out+=",\"physical_slots\":[";
  bool first=true;for(const auto &slot:f.physical_slots){if(!first)out+=',';first=false;Slot(out,slot);}out+="]}";
}
} // namespace xar::ck3_12004::army_actual_monthfirst_cleanup_json_detail

namespace xar::ck3_12004 {

// Owned data only; selected CArmy filtering/strict joins are59d's responsibility.
// A parent-entry roster match proves that earlier frame's membership only.
inline void AppendArmyActualMonthfirstCleanupObservations12004(std::string &out,
    const ArmyActualMonthfirstCleanupJournal12004 &journal) {
  using namespace army_actual_monthfirst_cleanup_json_detail;
  out+="{\"status\":";String(out,journal.owned_copy_complete ? "available" : "partial");
  out+=",\"source\":\"native_natural_monthfirst_cleanup_entry_return\",\"actual_entry_rva\":";
  Number(out,kArmyActualMonthfirstCleanupRva12004);
  out+=",\"literal_caller_return_rva\":";Number(out,kArmyActualMonthfirstCleanupReturnRva12004);
  out+=",\"snapshot_basis\":\"actual_readonly_boundary_copies\",\"conditional_predictor_executed\":false,"
       "\"observer_installed\":";
  Value(out,journal.observer_installed);
  out+=",\"oldest_available_ordinal\":";Number(out,journal.oldest_available_ordinal);
  out+=",\"latest_ordinal\":";Number(out,journal.latest_ordinal);
  out+=",\"overwritten_records\":";Number(out,journal.overwritten_records);
  out+=",\"unattributed_invocations\":";Number(out,journal.unattributed_invocations);
  out+=",\"dropped_record_copies\":";Number(out,journal.dropped_record_copies);
  out+=",\"event_count\":";Number(out,journal.events.size());out+=",\"events\":[";
  bool first=true;
  for(const auto &r:journal.events) {
    if(!first)out+=',';first=false;
    out+="{\"journal_ordinal\":";Number(out,r.journal_ordinal);
    out+=",\"actual_entry_rva\":";Number(out,r.actual_entry_rva);
    out+=",\"caller_return_rva\":";Number(out,r.caller_return_rva);
    out+=",\"source_call_admitted\":";Value(out,r.source_call_admitted);
    out+=",\"saved_mask02_admitted_by_literal_call\":";Optional(out,r.saved_mask02_admitted_by_literal_call);
    out+=",\"phase\":";Phase(out,r.phase);
    out+=",\"before_event\":";Event(out,r.before_event);
    out+=",\"before_copied_event\":";Event(out,r.before_copied_event);
    out+=",\"returned_event\":";Event(out,r.returned_event);
    out+=",\"after_copied_event\":";Event(out,r.after_copied_event);
    out+=",\"before\":";Frame(out,r.before);
    out+=",\"after\":";Frame(out,r.after);
    out+=",\"original_called\":";Value(out,r.original_called);
    out+=",\"original_returned\":";Value(out,r.original_returned);
    out+=",\"raw_return_bits\":";Optional(out,r.raw_return_bits);
    out+=",\"same_clock_thread_order\":";Optional(out,r.same_clock_thread_order);
    out+=",\"phase_date_matches_passed_date\":";Optional(out,r.phase_date_matches_passed_date);
    out+=",\"capture_failure_flags\":";Number(out,r.capture_failure_flags);out+='}';
  }
  out+="]}";
}
} // namespace xar::ck3_12004
