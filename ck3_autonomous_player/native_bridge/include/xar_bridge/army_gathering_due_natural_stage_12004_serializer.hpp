#pragma once
#include "xar_bridge/army_gathering_due_natural_stage_12004.hpp"
#include "xar_bridge/army_natural_phase_json_12004.hpp"
#include <sstream>

namespace xar::ck3_12004::gathering_due_json_detail {
inline void Value(std::ostream &o, bool v) { o << (v ? "true" : "false"); }
inline void Value(std::ostream &o, const std::string &v) {
  o << '"'; for (auto c : v) {
    if (c == '"' || c == '\\') o << '\\' << c;
    else if (c == '\n') o << "\\n";
    else if (static_cast<unsigned char>(c) >= 32) o << c;
  } o << '"';
}
template<class T> void Value(std::ostream &o, const T &v) { o << +v; }
template<class T> void Value(std::ostream &o, const std::optional<T> &v) { if (v) Value(o, *v); else o << "null"; }
template<class T, class F> void Array(std::ostream &o, const std::vector<T> &rows, F emit) {
  o << '['; bool first = true; for (const auto &v : rows) { if (!first) o << ','; first = false; emit(o, v); } o << ']';
}
inline void Event(std::ostream &o, const ArmyNaturalPhaseEvent12004 &v) {
  o << "{\"clock_identity\":" << v.clock_identity << ",\"sequence\":" << v.sequence << ",\"thread_id\":";
  Value(o, v.thread_id); o << '}';
}
inline void List(std::ostream &o, const ArmyGatheringDueNativeList12004 &v) {
  o << "{\"buffer_identity\":"; Value(o,v.buffer_identity);
  o << ",\"capacity\":"; Value(o,v.capacity); o << ",\"count\":"; Value(o,v.count);
  o << ",\"complete\":"; Value(o,v.complete); o << ",\"ordered_full_ids\":";
  Array(o,v.ordered_full_ids,[](auto &s,auto id){s<<id;}); o << '}';
}
inline void Physical(std::ostream &o, const ArmyGatheringDuePhysical12004 &v) {
  o << "{\"requested_full_id\":" << v.requested_full_id << ",\"physical_identity\":" << v.physical_identity;
  o << ",\"resolution_complete\":"; Value(o,v.resolution_complete);
  o << ",\"used_native_fallback\":"; Value(o,v.used_native_fallback);
  o << ",\"selected_full_id\":"; Value(o,v.selected_full_id); o << ",\"magic\":"; Value(o,v.magic); o << '}';
}
inline void Chunk(std::ostream &o, const ArmyGatheringDueChunk12004 &v) {
  o << "{\"ordinal\":" << v.ordinal << ",\"physical_identity\":" << v.physical_identity;
  o << ",\"maximum\":"; Value(o,v.maximum); o << ",\"current\":"; Value(o,v.current);
  o << ",\"owner_full_id\":"; Value(o,v.owner_full_id); o << ",\"stored_ordinal\":"; Value(o,v.stored_ordinal);
  o << ",\"association_full_id\":"; Value(o,v.association_full_id); o << ",\"byte14\":"; Value(o,v.byte14);
  o << ",\"state\":"; Value(o,v.state); o << ",\"date_raw64\":"; Value(o,v.date_raw64); o << '}';
}
inline void Ref(std::ostream &o, const ArmyGatheringDueReference12004 &v) {
  o << "{\"source_ref_identity\":" << v.source_ref_identity << ",\"owner_full_id\":"; Value(o,v.owner_full_id);
  o << ",\"ordinal\":"; Value(o,v.ordinal); o << ",\"receiver\":"; Physical(o,v.receiver);
  o << ",\"chunk\":"; if(v.chunk) Chunk(o,*v.chunk); else o << "null"; o << '}';
}
inline void ArRg(std::ostream &o,const ArmyGatheringDueArRg12004 &v) {
  o << "{\"receiver\":"; Physical(o,v.receiver); o << ",\"current38\":"; Value(o,v.current38);
  o << ",\"maximum3c\":"; Value(o,v.maximum3c); o << ",\"army140\":"; Value(o,v.army140);
  o << ",\"owner144\":"; Value(o,v.owner144); o << ",\"character148\":"; Value(o,v.character148);
  o << ",\"state14c\":"; Value(o,v.state14c); o << ",\"source_refs_identity\":"; Value(o,v.source_refs_identity);
  o << ",\"source_ref_count\":"; Value(o,v.source_ref_count); o << ",\"source_refs_complete\":"; Value(o,v.source_refs_complete);
  o << ",\"source_refs\":"; Array(o,v.source_refs,Ref); o << '}';
}
inline void Record(std::ostream &o, const ArmyGatheringDueRecord12004 &v) {
  o << "{\"physical_identity\":" << v.physical_identity << ",\"date_low32\":"; Value(o,v.date_low32);
  o << ",\"pending_count\":"; Value(o,v.pending_count); o << ",\"character_count\":"; Value(o,v.character_count);
  o << ",\"pending_refs_complete\":"; Value(o,v.pending_refs_complete);
  o << ",\"character_ids_complete\":"; Value(o,v.character_ids_complete);
  o << ",\"pending_refs\":"; Array(o,v.pending_refs,Ref); o << ",\"character_full_ids\":";
  Array(o,v.character_full_ids,[](auto &s,auto id){s<<id;}); o << '}';
}
inline void Army(std::ostream &o, const ArmyGatheringDueArmy12004 &v) {
  o << "{\"receiver\":"; Physical(o,v.receiver); o << ",\"unit124\":"; Value(o,v.unit124);
  o << ",\"combat128\":"; Value(o,v.combat128); o << ",\"combat_receiver\":"; Physical(o,v.combat_receiver);
  o << ",\"source_combat_skip\":"; Value(o,v.source_combat_skip);
  o << ",\"gathering_count\":"; Value(o,v.gathering_count);
  o << ",\"gathering_buffer_identity\":"; Value(o,v.gathering_buffer_identity);
  o << ",\"gathering_records_complete\":"; Value(o,v.gathering_records_complete);
  o << ",\"gathering_records\":"; Array(o,v.gathering_records,Record);
  o << ",\"arrg_roster\":"; List(o,v.arrg_roster); o << ",\"arrg\":"; Array(o,v.arrg,ArRg);
  o << ",\"finished_date190\":"; Value(o,v.finished_date190);
  o << ",\"statistics130_hex\":";
  if (!v.statistics130) o << "null";
  else { o << '"'; constexpr char hex[]="0123456789abcdef"; for(auto b:*v.statistics130) o<<hex[b>>4]<<hex[b&15]; o<<'"'; } o << '}';
}
inline void Snapshot(std::ostream &o, const ArmyGatheringDueSnapshot12004 &v) {
  o << "{\"primary_identity\":" << v.primary_identity << ",\"date_pointer_identity\":" << v.date_pointer_identity;
  o << ",\"event\":"; Event(o,v.event); o << ",\"passed_date_raw64\":"; Value(o,v.passed_date_raw64);
  o << ",\"game_state_date_raw64\":"; Value(o,v.game_state_date_raw64);
  o << ",\"absolute_day_raw\":"; Value(o,v.absolute_day_raw); o << ",\"current_c0_raw\":"; Value(o,v.current_c0_raw);
  o << ",\"queue158\":"; List(o,v.queue158); o << ",\"persistent_roster30\":"; List(o,v.persistent_roster30);
  o << ",\"army_roster50\":"; List(o,v.army_roster50); o << ",\"queued_armies\":"; Array(o,v.queued_armies,Army);
  o << ",\"roster_armies\":"; Array(o,v.roster_armies,Army); o << ",\"persistent\":";
  Array(o,v.persistent,[](auto &s,const auto &p){s<<"{\"receiver\":";Physical(s,p.receiver);s<<",\"prepared148\":";Value(s,p.prepared148);s<<",\"chunks\":";Array(s,p.chunks,Chunk);s<<'}';});
  o << ",\"entry_due_refs_at_return\":";Array(o,v.entry_due_refs_at_return,Ref);
  o << ",\"returned_ref_fields_basis\":\"immutable_entry_source_reference_and_returned_physical_reread\"";
  o << ",\"entry_queue_extent_backing_full_ids\":";Array(o,v.entry_queue_extent_backing_full_ids,[](auto &s,auto id){s<<id;});
  o << ",\"entry_queue_extent_backing_complete\":";Value(o,v.entry_queue_extent_backing_complete);
  o << ",\"all_declared_reads_complete\":"; Value(o,v.all_declared_reads_complete);
  o << ",\"missing_fields\":"; Array(o,v.missing_fields,[](auto &s,const auto &f){Value(s,f);}); o << '}';
}
inline void Stage(std::ostream &o, const ArmyGatheringDueNaturalStage12004 &v) {
  o << "{\"observed\":";Value(o,v.observed);o<<",\"original_called\":";Value(o,v.original_called);
  o << ",\"original_returned\":";Value(o,v.original_returned);o<<",\"actual_boundary_admitted\":";Value(o,v.actual_boundary_admitted);
  o << ",\"actual_poststage_observed\":";Value(o,v.actual_poststage_observed);
  o << ",\"actual_return_rva\":"<<v.actual_return_rva<<",\"raw_return_bits\":"<<v.raw_return_bits;
  o << ",\"actual_saved_mask\":";Value(o,v.actual_saved_mask);o<<",\"saved_mask_parent_observation_admitted\":";Value(o,v.saved_mask_parent_observation_admitted);
  o << ",\"same_clock_thread_order\":";Value(o,v.same_clock_thread_order);o<<",\"active_parent_unchanged\":";Value(o,v.active_parent_unchanged);
  o << ",\"unavailable_reason\":";Value(o,v.unavailable_reason);o<<",\"parent\":";AppendArmyNaturalPhaseScope12004(o,v.parent);
  o << ",\"entry\":";Snapshot(o,v.entry);o<<",\"returned\":";Snapshot(o,v.returned);o<<'}';
}
} // namespace detail

namespace xar::ck3_12004 {
inline void AppendArmyGatheringDueNaturalStage12004Json(std::ostream &out,
    const std::vector<ArmyGatheringDueNaturalStage12004> &records) {
  out << "{\"schema\":\"army_gathering_due_natural_stage_12004.v1\",\"source\":\"native_gathering_due_natural_stage_12004\",\"callee_rva\":" << kArmyGatheringDueNaturalRva12004 << ",\"caller_return_rva\":" << kArmyGatheringDueNaturalReturnRva12004;
  out << ",\"logical_source_end_exclusive\":" << std::uintptr_t{0x2A9B579};
  out << ",\"source_exe_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\",\"refresh_cache_basis\":\"guarded_entry_and_actual_return_fields\",\"internal_refresh_callback_observed\":false";
  out << ",\"source_locations\":{\"queue_count_load\":" << std::uintptr_t{0x2A9AF30} << ",\"queue_fullid_load\":" << std::uintptr_t{0x2A9AF95} << ",\"due_date_compare\":" << std::uintptr_t{0x2A9B0C8} << ",\"chunk_bind_call\":" << std::uintptr_t{0x2A9B15E} << ",\"army_refresh_call\":" << std::uintptr_t{0x2A9B502} << "},\"prediction_ready\":false,\"whole_daily_monthly_ready\":false,\"records\":";
  gathering_due_json_detail::Array(out,records,gathering_due_json_detail::Stage);out<<'}';
}
inline std::string SerializeArmyGatheringDueNaturalStage12004(const std::vector<ArmyGatheringDueNaturalStage12004> &records) {
  std::ostringstream out;AppendArmyGatheringDueNaturalStage12004Json(out,records);return out.str();
}
} // namespace xar::ck3_12004
