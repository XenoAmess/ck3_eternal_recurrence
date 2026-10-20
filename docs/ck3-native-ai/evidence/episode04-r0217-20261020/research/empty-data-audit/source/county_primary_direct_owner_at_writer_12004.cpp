#include "xar_bridge/county_primary_direct_owner_at_writer_v2.hpp"
#include "xar_bridge/army_actual_loss_writer_observations_v1.hpp"
#include <limits>

namespace xar::game {
const char *CountyPrimaryDirectCaptureSkipReasonV2(std::uint32_t flags) noexcept {
  static constexpr const char *reasons[]={"writer_registers_missing","writer_register_arguments_mismatch",
    "writer_event_clock_thread_invalid","game_state_date_unavailable_or_mismatch",
    "source_army_identity_unreadable_or_unstable","native_army_registry_mismatch",
    "public_unit_registry_mismatch","public_native_bidirectional_mismatch",
    "writer_identity_mismatch","writer_registry_mismatch","army_roster_unreadable_or_unstable",
    "writer_not_unique_in_actual_army_array","physical_association_incomplete",
    "physical_capture_incomplete","natural_sampling_changed_or_disabled","actual4_source_unqualified"};
  for(unsigned i=0;i<16;++i)if(flags&(1U<<i))return reasons[i];
  return flags?"unknown_capture_failure":"";
}
void AppendArmyCountyPrimaryDirectOwnerAtWriterV2(std::string &out,
    const ArmyCountyPrimaryDirectOwnerAtWriterV2 &v) {
  using namespace army_actual_loss_writer_json_v1;
  out+="{\"schema_version\":2,\"source\":\"native_county_primary_R13_direct_writer_v2\"";
  const auto n=[&](const char *key,auto value){out+=",\"";out+=key;out+="\":";Number(out,value);};
  const auto o=[&](const char *key,const auto &value){out+=",\"";out+=key;out+="\":";OptionalNumber(out,value);};
  const auto b=[&](const char *key,bool value){out+=",\"";out+=key;out+="\":";out+=value?"true":"false";};
  n("caller_return_rva",v.caller_return_rva);n("writer_invocation_token",v.writer_invocation_token);
  n("writer_receiver_identity",v.writer_receiver_identity);n("source_carmy_identity",v.source_carmy_identity);
  n("current_game_state_identity",v.current_game_state_identity);n("public_unit_identity",v.public_unit_identity);
  n("writer_thread_id",v.writer_thread_id);
  out+=",\"writer_event\":{\"clock_identity\":";Number(out,v.writer_event.clock_identity);
  out+=",\"sequence\":";Number(out,v.writer_event.sequence);out+=",\"thread_id\":";
  OptionalNumber(out,v.writer_event.thread_id);out+='}';
  o("observed_date_raw64",v.observed_date_raw64);b("natural_sampling_enabled",v.natural_sampling_enabled);
  b("actual4_source_qualified",v.actual4_source_qualified);n("natural_sampling_epoch",v.natural_sampling_epoch);
  o("army_id",v.army_id);o("native_carmy_id",v.native_carmy_id);o("writer_full_regiment_id",v.writer_full_regiment_id);
  n("native_army_registry_identity",v.native_army_registry_identity);
  n("public_unit_registry_identity",v.public_unit_registry_identity);n("writer_registry_identity",v.writer_registry_identity);
  o("army_roster_occurrence",v.army_roster_occurrence);o("army_roster_count",v.army_roster_count);
  b("receiver_identity_matches",v.receiver_identity_matches);b("writer_identity_matches",v.writer_identity_matches);
  b("native_army_registry_matches",v.native_army_registry_matches);b("public_unit_registry_matches",v.public_unit_registry_matches);
  b("public_native_bidirectional_matches",v.public_native_bidirectional_matches);
  b("writer_registry_matches",v.writer_registry_matches);b("actual_array_contains_writer",v.actual_array_contains_writer);
  b("physical_association_complete",v.physical_association_complete);b("physical_capture_complete",v.physical_capture_complete);
  n("captured_physical_association_count",v.captured_physical_association_count);
  out+=",\"physical_associations\":[";
  for(std::uint32_t i=0;i<v.captured_physical_association_count&&i<v.physical_associations.size();++i){
    if(i)out+=',';const auto &p=v.physical_associations[i];out+='{';
    out+="\"data_record_index\":";Number(out,p.data_record_index);
    n("persistent_regiment_id",p.persistent_regiment_id);n("data_chunk_ordinal",p.data_chunk_ordinal);
    n("physical_slot_index",p.physical_slot_index);n("persistent_registry_identity",p.persistent_registry_identity);
    n("selected_physical_identity",p.selected_physical_identity);n("expected_physical_identity",p.expected_physical_identity);
    o("physical_persistent_regiment_id",p.physical_persistent_regiment_id);
    o("physical_own_ordinal",p.physical_own_ordinal);o("physical_army_regiment_id",p.physical_army_regiment_id);
    b("registry_matches",p.registry_matches);b("physical_identity_matches",p.physical_identity_matches);out+='}';
  }
  out+=']';b("active_phase_observed",v.active_phase_observed);n("active_phase_kind",v.active_phase_kind);
  n("active_phase_entry_rva",v.active_phase_entry_rva);n("capture_failure_flags",v.capture_failure_flags);
  out+=",\"capture_skip_reason\":\"";out+=CountyPrimaryDirectCaptureSkipReasonV2(v.capture_failure_flags);out+='"';
  b("source_complete",v.source_complete);out+='}';
}
} // namespace xar::game

namespace xar::ck3_12004 {
namespace {
struct Reader {
  CountyPrimaryOwnerRead12004 read;void *context;
  template<class T>bool At(const void *p,std::size_t off,T &v)const noexcept {
    const auto a=reinterpret_cast<std::uintptr_t>(p);
    return a&&read&&off<=(std::numeric_limits<std::uintptr_t>::max)()-a&&
      read(context,reinterpret_cast<const void *>(a+off),&v,sizeof v);
  }
};
struct Army {
  std::int32_t native=-1,unit=-1,count=-1,capacity=-1;std::uint32_t magic=0;const void *data=nullptr;
  bool operator==(const Army &)const=default;
};
bool ArmyAt(const Reader &r,const void *p,Army &a)noexcept {
  return r.At(p,0x10,a.native)&&r.At(p,0x14,a.magic)&&r.At(p,0x124,a.unit)&&
    r.At(p,0x38,a.data)&&r.At(p,0x40,a.capacity)&&r.At(p,0x44,a.count)&&
    a.native!=-1&&a.unit!=-1&&a.magic==0x41726D79U&&a.count>=0&&a.capacity>=a.count&&
    a.capacity<=65536&&(!a.count||a.data);
}
bool Identity(const Reader &r,const void *p,std::int32_t id,std::uint32_t magic)noexcept {
  std::int32_t actual=-1;std::uint32_t tag=0;
  return id!=-1&&r.At(p,0x10,actual)&&r.At(p,0x14,tag)&&actual==id&&tag==magic;
}
}
game::ArmyCountyPrimaryDirectOwnerAtWriterV2 CaptureCountyPrimaryDirectOwnerAtWriter12004(
    CountyPrimaryOwnerRead12004 read,void *read_context,CountyDirectRegistryLookup12004 lookup,void *lookup_context,
    const CountyPrimaryWriterRegisters12004 *call,const CountyPrimaryPhaseCapture12004 &active,
    const game::ArmyActualLossWriterObservationV1 &event,const CountyDirectPhysicalInputs12004 &physical,
    const void *receiver,std::uint32_t tid,std::uintptr_t state,bool source_qualified) noexcept {
  game::ArmyCountyPrimaryDirectOwnerAtWriterV2 v{};
  v.caller_return_rva=event.caller_return_rva.value_or(0);
  v.writer_receiver_identity=reinterpret_cast<std::uintptr_t>(receiver);
  v.current_game_state_identity=state;v.writer_thread_id=tid;v.actual4_source_qualified=source_qualified;
  v.writer_event={active.writer_event.clock_identity,active.writer_event.sequence,active.writer_event.thread_id};
  v.natural_sampling_enabled=active.sampling.enabled;v.natural_sampling_epoch=active.sampling.epoch;
  v.active_phase_observed=active.scope.observed;v.active_phase_kind=static_cast<std::uint32_t>(active.scope.phase);
  v.active_phase_entry_rva=active.scope.actual_entry_rva;
  const auto fail=[&](std::uint32_t f){v.capture_failure_flags|=f;};
  if(!source_qualified)fail(county_direct_source_unqualified);
  if(!active.sampling.enabled||!active.sampling.epoch)fail(county_direct_sampling_changed);
  if(!call)fail(county_direct_registers_missing);
  else {
    v.writer_invocation_token=call->writer_invocation_token;
    v.source_carmy_identity=reinterpret_cast<std::uintptr_t>(call->source_carmy_r13);
    if(call->writer_receiver!=receiver||call->caller_return_rva!=0x24E25EE||
       v.caller_return_rva!=0x24E25EE||!call->writer_invocation_token||call->native_thread_id!=tid||!tid)
      fail(county_direct_register_argument);
  }
  if(!v.writer_event.clock_identity||!v.writer_event.sequence||!v.writer_event.thread_id||
     !tid||*v.writer_event.thread_id!=tid)fail(county_direct_writer_event);
  const Reader r{read,read_context};std::uint64_t date=0,date_again=0;
  if(r.At(reinterpret_cast<const void *>(state),8,date))v.observed_date_raw64=date;
  if(!v.observed_date_raw64||!event.observed_date_raw||
     static_cast<std::uint32_t>(date)!=static_cast<std::uint32_t>(*event.observed_date_raw)||
     !r.At(reinterpret_cast<const void *>(state),8,date_again)||date_again!=date)fail(county_direct_game_state_date);
  const void *army=reinterpret_cast<const void *>(v.source_carmy_identity);Army before{},after{};
  const bool army_read=ArmyAt(r,army,before);
  if(army_read){v.army_id=before.unit;v.native_carmy_id=before.native;v.army_roster_count=before.count;}
  const auto resolve=[&](CountyDirectRegistryKind12004 kind,std::int32_t id){
    return lookup&&id!=-1?lookup(lookup_context,kind,id):nullptr;
  };
  const void *registered_army=army_read?resolve(CountyDirectRegistryKind12004::army,before.native):nullptr;
  v.native_army_registry_identity=reinterpret_cast<std::uintptr_t>(registered_army);
  v.native_army_registry_matches=army_read&&registered_army==army&&registered_army&&
    resolve(CountyDirectRegistryKind12004::army,before.native)==army;
  if(!v.native_army_registry_matches)fail(county_direct_army_registry);
  const void *unit=army_read?resolve(CountyDirectRegistryKind12004::unit,before.unit):nullptr;
  v.public_unit_identity=reinterpret_cast<std::uintptr_t>(unit);v.public_unit_registry_identity=v.public_unit_identity;
  std::int32_t unit_id=-1,link=-1,link_again=-1;
  v.public_unit_registry_matches=unit&&r.At(unit,0x10,unit_id)&&unit_id==before.unit&&
    resolve(CountyDirectRegistryKind12004::unit,before.unit)==unit;
  if(!v.public_unit_registry_matches)fail(county_direct_unit_registry);
  v.public_native_bidirectional_matches=v.native_army_registry_matches&&v.public_unit_registry_matches&&
    r.At(unit,0x178,link)&&r.At(unit,0x178,link_again)&&link==before.native&&link_again==link;
  if(!v.public_native_bidirectional_matches)fail(county_direct_bidirectional);
  const auto rid=event.army_regiment_id;
  if(rid!=-1)v.writer_full_regiment_id=rid;
  v.writer_identity_matches=Identity(r,receiver,rid,0x41725267U)&&Identity(r,receiver,rid,0x41725267U);
  if(!v.writer_identity_matches)fail(county_direct_writer_identity);
  const void *registered_writer=resolve(CountyDirectRegistryKind12004::army_regiment,rid);
  v.writer_registry_identity=reinterpret_cast<std::uintptr_t>(registered_writer);
  v.writer_registry_matches=registered_writer&&registered_writer==receiver&&
    resolve(CountyDirectRegistryKind12004::army_regiment,rid)==receiver;
  if(!v.writer_registry_matches)fail(county_direct_writer_registry);
  bool roster_read=army_read;std::int32_t occurrences=0;
  if(army_read)for(std::int32_t i=0;i<before.count;++i){std::int32_t id=-1;
    if(!r.At(before.data,static_cast<std::size_t>(i)*4U,id)){roster_read=false;break;}
    if(id==rid){++occurrences;v.army_roster_occurrence=i;}
  }
  std::int32_t member_again=-1;
  v.actual_array_contains_writer=roster_read&&occurrences==1&&v.army_roster_occurrence&&
    r.At(before.data,static_cast<std::size_t>(*v.army_roster_occurrence)*4U,member_again)&&member_again==rid;
  if(!roster_read)fail(county_direct_roster_read);
  if(!v.actual_array_contains_writer)fail(county_direct_roster_membership);
  v.receiver_identity_matches=army_read&&ArmyAt(r,army,after)&&before==after;
  if(!v.receiver_identity_matches)fail(county_direct_army_identity);
  const void *data=nullptr;std::int32_t count=-1,cap=-1;
  bool physical_ok=r.At(receiver,0x20,data)&&r.At(receiver,0x28,cap)&&r.At(receiver,0x2C,count)&&
    data&&count>0&&count<=64&&cap>=count&&event.native_data_record_count&&
    count==*event.native_data_record_count&&event.captured_data_record_count==static_cast<std::uint32_t>(count)&&
    event.physical_slot_count>0&&event.physical_slot_count<=64;
  if(physical_ok){
    v.captured_physical_association_count=static_cast<std::uint32_t>(count);
    for(std::int32_t i=0;i<count;++i){
      auto &p=v.physical_associations[static_cast<std::size_t>(i)];const auto &alias=event.data_aliases[static_cast<std::size_t>(i)];
      p.data_record_index=i;p.persistent_regiment_id=alias.persistent_regiment_id.value_or(-1);
      p.data_chunk_ordinal=alias.data_chunk_ordinal.value_or(-1);p.physical_slot_index=alias.physical_slot_index.value_or(-1);
      const auto off=static_cast<std::size_t>(i)*0x10U;std::int32_t pid=-1,ord=-1,pid2=-1,ord2=-1;
      const bool record=r.At(data,off+8,pid)&&r.At(data,off+12,ord)&&pid==p.persistent_regiment_id&&
        ord==p.data_chunk_ordinal&&pid!=-1&&ord>=0&&ord<7&&alias.data_record_index==i;
      const void *persistent=record?resolve(CountyDirectRegistryKind12004::persistent_regiment,pid):nullptr;
      p.persistent_registry_identity=reinterpret_cast<std::uintptr_t>(persistent);
      p.registry_matches=persistent&&Identity(r,persistent,pid,0x52656769U)&&
        resolve(CountyDirectRegistryKind12004::persistent_regiment,pid)==persistent;
      if(p.physical_slot_index>=0&&static_cast<std::uint32_t>(p.physical_slot_index)<event.physical_slot_count)
        p.selected_physical_identity=reinterpret_cast<std::uintptr_t>(physical.selected_slots[static_cast<std::size_t>(p.physical_slot_index)]);
      if(p.registry_matches&&ord>=0&&ord<7){const auto delta=0x18U+static_cast<std::size_t>(ord)*0x24U;
        if(delta<=(std::numeric_limits<std::uintptr_t>::max)()-p.persistent_registry_identity)
          p.expected_physical_identity=p.persistent_registry_identity+delta;
      }
      const auto *slot=reinterpret_cast<const void *>(p.selected_physical_identity);
      std::int32_t sp=-1,so=-1,sr=-1,sp2=-1,so2=-1,sr2=-1;
      const bool slot_read=r.At(slot,8,sp)&&r.At(slot,12,so)&&r.At(slot,16,sr);
      if(slot_read){p.physical_persistent_regiment_id=sp;p.physical_own_ordinal=so;p.physical_army_regiment_id=sr;}
      p.physical_identity_matches=record&&p.registry_matches&&p.selected_physical_identity&&
        p.selected_physical_identity==p.expected_physical_identity&&slot_read&&sp==pid&&so==ord&&sr==rid&&
        r.At(slot,8,sp2)&&r.At(slot,12,so2)&&r.At(slot,16,sr2)&&sp2==sp&&so2==so&&sr2==sr&&
        r.At(data,off+8,pid2)&&r.At(data,off+12,ord2)&&pid2==pid&&ord2==ord&&
        Identity(r,persistent,pid,0x52656769U);
      physical_ok=physical_ok&&p.physical_identity_matches;
    }
  }
  const void *data2=nullptr;std::int32_t count2=-1,cap2=-1;
  v.physical_association_complete=physical_ok&&r.At(receiver,0x20,data2)&&r.At(receiver,0x28,cap2)&&
    r.At(receiver,0x2C,count2)&&data2==data&&count2==count&&cap2==cap;
  if(!v.physical_association_complete)fail(county_direct_physical_association);
  // Final qualification is intentionally delayed until the original writer's
  // existing physical-before/after capture has returned and sampling is reread.
  return v;
}
void FinishCountyPrimaryDirectOwnerAtWriter12004(game::ArmyCountyPrimaryDirectOwnerAtWriterV2 &v,
    const game::ArmyActualLossWriterObservationV1 &event,const ArmyObserverResearchSamplingState12004 &sampling) noexcept {
  v.physical_capture_complete=event.physical_capture_complete&&event.actual_physical_soldier_debit.has_value();
  if(!v.physical_capture_complete)v.capture_failure_flags|=county_direct_physical_post;
  if(!sampling.enabled||sampling.epoch!=v.natural_sampling_epoch)v.capture_failure_flags|=county_direct_sampling_changed;
  v.source_complete=v.capture_failure_flags==0;
}
} // namespace xar::ck3_12004
