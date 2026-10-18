#include "xar_bridge/county_primary_owner_at_writer_12004.hpp"
#include <limits>
namespace xar::ck3_12004 {
namespace {
game::ArmyCountyWriterEventTokenV1 Token(const ArmyNaturalPhaseEvent12004 &e) noexcept {
  return {e.clock_identity,e.sequence,e.thread_id};
}
bool Later(const ArmyNaturalPhaseEvent12004 &a,const ArmyNaturalPhaseEvent12004 &b,
    std::uint32_t tid) noexcept {
  return a.clock_identity&&a.clock_identity==b.clock_identity&&a.sequence&&a.sequence<b.sequence&&
    a.thread_id&&b.thread_id&&*a.thread_id==tid&&*b.thread_id==tid&&tid;
}
struct Reader {
  CountyPrimaryOwnerRead12004 read;void *context;
  template<class T> bool At(const void *p,std::size_t offset,T &v) const noexcept {
    const auto a=reinterpret_cast<std::uintptr_t>(p);
    return a&&read&&offset<=(std::numeric_limits<std::uintptr_t>::max)()-a&&
      read(context,reinterpret_cast<const void*>(a+offset),&v,sizeof v);
  }
};
struct Army {std::int32_t native=-1,unit=-1,count=-1,capacity=-1;std::uint32_t magic=0;const void *data=nullptr;};
bool ReadArmy(const Reader &r,const void *p,Army &a) noexcept {
  return r.At(p,0x10,a.native)&&r.At(p,0x14,a.magic)&&r.At(p,0x124,a.unit)&&
    r.At(p,0x38,a.data)&&r.At(p,0x40,a.capacity)&&r.At(p,0x44,a.count)&&
    a.native!=-1&&a.unit!=-1&&a.magic==0x41726D79U&&a.count>=0&&a.count<=4096&&
    a.capacity>=a.count&&(!a.count||a.data);
}
}
std::optional<game::ArmyCountyPrimaryOwnerAtWriterV1> CaptureCountyPrimaryOwnerAtWriter12004(
    CountyPrimaryOwnerRead12004 read,void *context,const CountyPrimaryWriterRegisters12004 &call,
    const CountyPrimaryPhaseCapture12004 &active,std::int32_t writer_full_id,
    std::optional<std::int32_t> writer_date,std::uintptr_t current_state) noexcept {
  const auto &s=active.scope;
  // Never lend a post-date/core/periodic or nearest unrelated scope to county primary.
  if(call.caller_return_rva!=0x24E25EE||!s.observed||
     s.phase!=ArmyNaturalPhaseKind12004::pre_date||s.actual_entry_rva!=0x2A99DA0)
    return std::nullopt;
  game::ArmyCountyPrimaryOwnerAtWriterV1 v{};
  v.writer_invocation_token=call.writer_invocation_token;
  v.writer_receiver_identity=reinterpret_cast<std::uintptr_t>(call.writer_receiver);
  v.source_carmy_identity=reinterpret_cast<std::uintptr_t>(call.source_carmy_r13);
  v.phase_primary_manager_identity=s.primary_manager_identity;v.phase_game_state_identity=s.game_state_identity;
  v.phase_entry_event=Token(s.entry_event);v.writer_event=Token(active.writer_event);
  v.phase_prefix_roster_event=Token(s.original_army_roster.capture_event);
  if(!call.writer_invocation_token||!Later(s.entry_event,active.writer_event,call.native_thread_id))v.capture_failure_flags|=1U;
  const Reader r{read,context};Army before{},after{};
  const bool a=ReadArmy(r,call.source_carmy_r13,before);
  if(a){v.army_id=before.unit;v.native_carmy_id=before.native;}
  std::int32_t rid=-1,rid_again=-1;std::uint32_t magic=0,magic_again=0;
  const bool writer=r.At(call.writer_receiver,0x10,rid)&&r.At(call.writer_receiver,0x14,magic)&&
    r.At(call.writer_receiver,0x10,rid_again)&&r.At(call.writer_receiver,0x14,magic_again);
  if(writer)v.writer_full_regiment_id=rid;
  v.writer_identity_matches=writer&&writer_full_id!=-1&&rid==writer_full_id&&rid_again==rid&&
    magic==0x41725267U&&magic_again==magic;
  if(!v.writer_identity_matches)v.capture_failure_flags|=4U;
  if(a&&v.writer_identity_matches){
    for(std::int32_t i=0;i<before.count;++i){std::int32_t id=-1;
      if(!r.At(before.data,static_cast<std::size_t>(i)*4U,id)){v.capture_failure_flags|=8U;break;}
      if(id==rid&&!v.army_roster_occurrence){v.actual_array_contains_writer=true;v.army_roster_occurrence=i;}
    }
  }
  const bool b=ReadArmy(r,call.source_carmy_r13,after);
  v.receiver_identity_matches=a&&b&&before.native==after.native&&before.unit==after.unit&&
    before.data==after.data&&before.count==after.count&&before.capacity==after.capacity;
  if(!v.receiver_identity_matches)v.capture_failure_flags|=2U;
  if(!v.actual_array_contains_writer)v.capture_failure_flags|=16U;
  const auto &roster=s.original_army_roster;
  if(a&&roster.complete&&roster.boundary==ArmyNaturalRosterBoundary12004::pre_date_prefix_return&&
     roster.capture_rva==0x2A99E76&&Later(s.entry_event,roster.capture_event,call.native_thread_id)&&
     Later(roster.capture_event,active.writer_event,call.native_thread_id)){
    for(std::size_t i=0;i<roster.ordered_full_ids.size();++i)
      if(roster.ordered_full_ids[i]==static_cast<std::uint32_t>(before.native)){
        v.source_phase_roster_membership=true;v.phase_roster_occurrence=static_cast<std::int32_t>(i);break;}
  }
  if(!v.source_phase_roster_membership)v.capture_failure_flags|=32U;
  std::uint64_t date=0;
  if(!s.primary_manager_identity||!s.game_state_identity||current_state!=s.game_state_identity||!writer_date||!s.prefix_date_raw||
     !r.At(reinterpret_cast<const void*>(current_state),8,date)||date!=*s.prefix_date_raw||
     static_cast<std::uint32_t>(date)!=static_cast<std::uint32_t>(*writer_date))
    v.capture_failure_flags|=64U;
  v.source_complete=v.capture_failure_flags==0;
  return v;
}
} // namespace xar::ck3_12004
