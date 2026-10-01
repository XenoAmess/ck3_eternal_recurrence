#include "xar_bridge/scoped_character_variable_monitor_v1.hpp"
#include "xar_bridge/scoped_observer_lifetime_v1.hpp"
#include <windows.h>
#include <cassert>
#include <cstring>
#include <iostream>
#include <memory>
#include <thread>
using namespace xar::ck3_11906;
namespace {
template<class T> void Put(void *p,std::size_t offset,T value){std::memcpy(static_cast<std::byte*>(p)+offset,&value,sizeof(value));}
template<class T> T Get(const void *p,std::size_t offset){T value{};std::memcpy(&value,static_cast<const std::byte*>(p)+offset,sizeof(value));return value;}
void Key(void *p,const char *value){const auto n=std::strlen(value);if(n<16)std::memcpy(p,value,n+1);else Put(p,0,reinterpret_cast<std::uintptr_t>(value));Put(p,0x10,std::uint64_t(n));Put(p,0x18,std::uint64_t(n<16?15:n));}
struct Fixture {
 std::array<std::byte,0x40> storage{},table{},date{},type{};
 std::array<std::array<std::byte,0x1D0>,2> chars{};
 std::array<std::array<std::byte,0x10>,202> slots{};
 std::array<std::array<std::byte,0x50>,3> owners{};
 std::array<std::array<std::byte,0x20>,3> rows{};
 std::array<std::array<std::byte,0x20>,3> names{};
 std::array<std::array<std::uint64_t,2>,3> scopes{{{4,101},{4,201},{4,102}}};
 std::array<std::byte,0x70> node{},context{};
 std::array<std::array<std::byte,0x20>,2> houses{};
 std::array<std::byte,0x50> event_manager{};
 std::array<std::array<std::byte,0x240>,8> event_defs{};
 std::array<std::array<std::byte,0x50>,8> event_roots{};
 std::array<std::uintptr_t,8> event_ptrs{};
 std::uintptr_t event_manager_slot=0;
 void *storage_slot=nullptr;std::uintptr_t date_slot=0;
 Bindings bindings{};
 Fixture(){
  storage_slot=storage.data();bindings.character_storage_slot=&storage_slot;
  Put(storage.data(),0x20,reinterpret_cast<std::uintptr_t>(slots.data()));Put(storage.data(),0x2C,std::int32_t(202));
  for(std::size_t i=0;i<2;++i){const auto id=101+std::int32_t(i)*100;Put(chars[i].data(),0x18,id);Put(chars[i].data(),0x150,std::int32_t(31+i));Put(slots[id].data(),8,reinterpret_cast<std::uintptr_t>(chars[i].data()));Put(houses[i].data(),0x10,std::int32_t(31+i));}
  date_slot=reinterpret_cast<std::uintptr_t>(date.data());Put(date.data(),8,std::int32_t(53146848));
  Key(names[0].data(),"other");Key(names[1].data(),"signature_weapon");Key(names[2].data(),"axe");Put(table.data(),0,std::uint8_t(1));Put(table.data(),0x30,reinterpret_cast<std::uintptr_t>(names.data()));Put(table.data(),0x3C,std::int32_t(3));
  for(std::size_t i=0;i<3;++i){Put(owners[i].data(),0x10,reinterpret_cast<std::uintptr_t>(rows[i].data()));Put(owners[i].data(),0x18,std::int32_t(1));Put(owners[i].data(),0x1C,std::int32_t(0));}
  Put(node.data(),0,std::uintptr_t(0x1444D19B0));Put(node.data(),0x38,std::uint32_t(771));Put(context.data(),0,reinterpret_cast<std::uintptr_t>(scopes[1].data()));
  Put(type.data(),0x10,std::int32_t(9));Key(type.data()+0x18,"default_house_relation");
 }
 void Events(std::uintptr_t module){
  static constexpr std::array<const char*,7> keys{"death_management.1200","death_management.1201","death_management.1202","death_management.1204","death_management.1205","death_management.1206","death_management.1207"};
  for(std::size_t i=0;i<7;++i){auto *def=event_defs[i].data();auto *root=event_roots[i].data();
   Put(def,0,module+0x42F5710);Put(def,8,std::uint32_t(1200+i));Put(def,0xC,std::uint32_t(i));Key(def+0x10,keys[i]);Put(def,0x230,reinterpret_cast<std::uintptr_t>(root));
   Put(root,0,module+0x44CF030);Put(root,0x38,std::uint32_t(700+i));event_ptrs[i]=reinterpret_cast<std::uintptr_t>(def);
  }
  auto *foreign=event_defs[7].data();Put(foreign,0,module+0x42F5710);Put(foreign,8,std::uint32_t(9999));Put(foreign,0xC,std::uint32_t(7));Key(foreign+0x10,"foreign_event.1");Put(foreign,0x230,reinterpret_cast<std::uintptr_t>(event_roots[7].data()));Put(event_roots[7].data(),0,module+0x44CF030);event_ptrs[7]=reinterpret_cast<std::uintptr_t>(foreign);
  Put(event_manager.data(),0x40,reinterpret_cast<std::uintptr_t>(event_ptrs.data()));Put(event_manager.data(),0x48,std::int32_t(8));Put(event_manager.data(),0x4C,std::int32_t(8));
  event_manager_slot=reinterpret_cast<std::uintptr_t>(event_manager.data());
  Put(reinterpret_cast<void*>(module+0x44CF030),0xB0,module+0x3380EC0);
 }
};
Fixture *g_fixture=nullptr;std::size_t g_owner_index=1;std::uint32_t g_owner_calls=0,g_setter_calls=0,g_effect_calls=0,g_house_calls=0;
std::array<std::uint64_t,2> g_value{3,0xABCD00000002ULL};std::int32_t g_key=0x01000001;std::uintptr_t g_house_return=0xC0DE00;
void *Owner(const void *scope){++g_owner_calls;const auto id=Get<std::int64_t>(scope,8);return id==101?g_fixture->owners[0].data():g_fixture->owners[g_owner_index].data();}
std::uintptr_t Setter(void *container,std::int32_t key,const void *value,std::int32_t duration){++g_setter_calls;const auto data=Get<std::uintptr_t>(container,8);Put(reinterpret_cast<void*>(data),8,key);Put(reinterpret_cast<void*>(data),0xC,duration);std::memcpy(reinterpret_cast<void*>(data+0x10),value,16);Put(container,0x14,std::int32_t(1));return 0xABCDEF123ULL;}
std::uintptr_t Effect(void *,void *context){++g_effect_calls;auto *owner=ObservedCharacterVariableOwnerV1(reinterpret_cast<void*>(Get<std::uintptr_t>(context,0)));(void)ObservedCharacterVariableSetterV1(static_cast<std::byte*>(owner)+8,g_key,g_value.data(),-1);return 0x987654321ULL;}
std::uintptr_t House(void *,void *,void *){++g_house_calls;return g_house_return;}
bool Arm(ScopedCharacterVariableMonitorV1 &m,Fixture &f){g_fixture=&f;assert(BindScopedVariableMonitorOfflineOriginalsV1(Owner,Setter,Effect,House));return StartScopedCharacterVariableMonitorV1(m,f.bindings,0x140000000,{101,201},17,true,true,reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot));}
const ScopedVariableMonitorRecordV1 &Find(const ScopedCharacterVariableMonitorV1 &m,ScopedVariableMonitorBoundaryV1 b,bool last=false){const ScopedVariableMonitorRecordV1 *found=nullptr;for(std::uint32_t i=0;i<m.count.load()&&i<m.records.size();++i)if(m.records[i].boundary==b){found=&m.records[i];if(!last)return *found;}assert(found);return *found;}
void Observation(){
 Fixture f;auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();assert(Arm(*m,f));
 const auto old_count=m->count.load();(void)ObservedCharacterVariableOwnerV1(f.scopes[2].data());assert(m->count.load()==old_count);
 const auto old_setter=g_setter_calls;const auto old_effect=g_effect_calls;const auto old_owner=g_owner_calls;
 assert(ObservedCharacterVariableEffectV1(f.node.data(),f.context.data())==0x987654321ULL);
 assert(g_setter_calls==old_setter+1&&g_effect_calls==old_effect+1&&g_owner_calls==old_owner+1);
 const auto &before=Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_enter);const auto &after=Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_return);
 assert(before.character_id==201&&before.full_identity_matches&&!before.value.present&&before.value.read);
 assert(before.owner_from_same_setter_invocation&&before.setter_node_hash==771&&before.native_scope_words[1]==201);
 assert(after.value.present&&after.value.words==g_value&&after.original_return_bits==0xABCDEF123ULL);
 assert(after.value.flag_name_read&&after.value.flag_index==2&&after.value.flag_identifier_epoch==1&&std::string(after.value.flag_name.bytes.data(),after.value.flag_name.size)=="axe");
 // Dead storage retains full ID; actual original getter migrates the owner.
 Put(f.chars[1].data(),0x1C8,std::uintptr_t(123));g_owner_index=2;g_value={3,0xBEEF00000002ULL};
 Put(f.date.data(),8,std::int32_t(53146872));assert(ObservedCharacterVariableEffectV1(f.node.data(),f.context.data())==0x987654321ULL);
 const auto &migrated=Find(*m,ScopedVariableMonitorBoundaryV1::original_owner_return,true);
 assert(migrated.victim_dead&&migrated.full_identity_matches&&migrated.previous_owner!=migrated.owner);
 const auto before_house=g_house_calls;assert(ObservedScopedHousePredicateV1(f.type.data(),f.houses[0].data(),f.houses[1].data())==g_house_return);
 const auto &house=Find(*m,ScopedVariableMonitorBoundaryV1::house_predicate_return);
 assert(g_house_calls==before_house+1&&house.original_boolean_read&&!house.original_boolean&&house.original_return_bits==g_house_return);
 assert(house.relation_type_id==9&&std::string(house.relation_type_key.bytes.data(),house.relation_type_key.size)=="default_house_relation");
 assert(FinishScopedCharacterVariableMonitorV1(*m,true)&&m->detours_uninstalled&&m->failure_flags.load()==0);
 const auto &final=Find(*m,ScopedVariableMonitorBoundaryV1::final_paused,true);assert(!final.value.read);
 const auto wire=SerializeScopedCharacterVariableMonitorV1(*m);assert(wire.find("\"whole_game_mutable_bundle_complete\":false")!=std::string::npos);
 std::cout<<"{\"kind\":\"OFFLINE_FIXTURE_NOT_NATIVE_GAME_TRUTH\",\"scoped_variable_monitor\":"<<wire<<"}\n";
 g_owner_index=1;g_value={3,0xABCD00000002ULL};
}
void Guards(){
 Fixture f;auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();g_fixture=&f;assert(BindScopedVariableMonitorOfflineOriginalsV1(Owner,Setter,Effect,House));
 assert(!StartScopedCharacterVariableMonitorV1(*m,f.bindings,0x140000000,{101,201},17,false,true,reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot)));
 assert(!StartScopedCharacterVariableMonitorV1(*m,f.bindings,0x140000000,{101,101},17,true,true,reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot)));
 Put(f.chars[1].data(),0x18,std::int32_t(0x010000C9));assert(!Arm(*m,f));Put(f.chars[1].data(),0x18,std::int32_t(201));assert(Arm(*m,f));
 const auto start=m->count.load();g_key=0x01000000;(void)ObservedCharacterVariableEffectV1(f.node.data(),f.context.data());
 assert(m->count.load()==start+1);g_key=0x01000001;
 // Unexpected date is retained as failed evidence, never promoted.
 Put(f.date.data(),8,std::int32_t(53146896));(void)ObservedCharacterVariableEffectV1(f.node.data(),f.context.data());
 assert((m->failure_flags.load()&scoped_chain_failure_thread_or_date)!=0);
 assert(!FinishScopedCharacterVariableMonitorV1(*m,false));assert(FinishScopedCharacterVariableMonitorV1(*m,true));
 auto invalid=std::make_unique<ScopedCharacterVariableMonitorV1>();Put(f.names[0].data(),0,std::uintptr_t("signature_weapon"));Put(f.names[0].data(),0x10,std::uint64_t(16));Put(f.names[0].data(),0x18,std::uint64_t(16));assert(!Arm(*invalid,f));
 ScopedVariableMonitorQueryV1 query{};MainThreadExecutionStampV1 stamp{};assert(!ExecuteScopedVariableMonitorQueryV1(&query,stamp));
}
void ExactAnchorsAndRollback(){
 constexpr std::array<std::uintptr_t,5> rvas{0x3329A40,0x3346BE0,0x3393530,0x2DF7030,0x3380EC0};
 const std::array<std::string,5> anchors{
  std::string("\x48\x89\x5C\x24\x08\x57\x48\x83\xEC\x20\x0F\xB7\x39\x48\x8B\xD9",16),
  std::string("\x48\x89\x5C\x24\x20\x56\x48\x83\xEC\x40\x4C\x63\x51\x14",14),
  std::string("\x48\x89\x5C\x24\x08\x48\x89\x74\x24\x18\x57\x48\x81\xEC\x70\x02\0\0",18),
  std::string("\x48\x89\x5C\x24\x08\x48\x89\x6C\x24\x10\x48\x89\x74\x24\x18",15),
  std::string("\x48\x89\x5C\x24\x08\x48\x89\x74\x24\x10\x57\x48\x83\xEC\x20",15)};
 auto *space=static_cast<std::byte*>(VirtualAlloc(nullptr,0x6000000,MEM_RESERVE,PAGE_NOACCESS));assert(space);
 for(std::size_t i=0;i<5;++i){assert(VirtualAlloc(space+(rvas[i]&~0xFFFULL),4096,MEM_COMMIT,PAGE_EXECUTE_READWRITE));std::memcpy(space+rvas[i],anchors[i].data(),anchors[i].size());}
 assert(VirtualAlloc(space+0x585F000,4096,MEM_COMMIT,PAGE_READWRITE));assert(VirtualAlloc(space+0x570E000,4096,MEM_COMMIT,PAGE_READWRITE));
 assert(VirtualAlloc(space+0x44CF000,4096,MEM_COMMIT,PAGE_READWRITE));assert(VirtualAlloc(space+0x570F000,4096,MEM_COMMIT,PAGE_READWRITE));
 Fixture f;f.Events(reinterpret_cast<std::uintptr_t>(space));std::memcpy(space+0x585F240,f.table.data(),f.table.size());Put(space,0x570E068,f.date_slot);Put(space,0x570F790,f.event_manager_slot);
 auto first=std::make_unique<ScopedCharacterVariableMonitorV1>();assert(StartScopedCharacterVariableMonitorV1(*first,f.bindings,reinterpret_cast<std::uintptr_t>(space),{101,201},18,true,true));
 for(const auto &site:first->detours)assert(site.installed&&site.trampoline);
 assert(FinishScopedCharacterVariableMonitorV1(*first,true));for(std::size_t i=0;i<5;++i)assert(std::memcmp(space+rvas[i],anchors[i].data(),anchors[i].size())==0);
 space[rvas[3]]=std::byte{0};auto second=std::make_unique<ScopedCharacterVariableMonitorV1>();assert(!StartScopedCharacterVariableMonitorV1(*second,f.bindings,reinterpret_cast<std::uintptr_t>(space),{101,201},19,true,true));
 assert(!ScopedVariableMonitorHasInstalledHooksV1(*second)&&second->detours_uninstalled);
 for(std::size_t i=0;i<3;++i)assert(std::memcmp(space+rvas[i],anchors[i].data(),anchors[i].size())==0);
 assert(VirtualFree(space,0,MEM_RELEASE));
}
}
namespace {
HANDLE g_callback_entered=nullptr,g_callback_release=nullptr;
void *BlockedOwner(const void *scope) {
  SetEvent(g_callback_entered);
  assert(WaitForSingleObject(g_callback_release,5000)==WAIT_OBJECT_0);
  return Owner(scope);
}
struct ResidentParent {
  int plan=73;int *child_plan=&plan;bool *destroyed=nullptr;
  ~ResidentParent(){*destroyed=true;}
};
std::uint32_t g_root_calls=0;
bool g_nested_matched=false;
std::array<std::byte,0x50> g_ordinary_nested_root{};
void RootOriginal(void *root,void *context){
  ++g_root_calls;
  if(g_nested_matched&&root==g_fixture->event_roots[0].data()) {
    ObservedScopedEventImmediateRootV1(g_fixture->event_roots[2].data(),context);
    (void)ObservedCharacterVariableEffectV1(g_fixture->node.data(),context);
  } else if(root==g_ordinary_nested_root.data()||root==g_fixture->event_roots[7].data())
    (void)ObservedCharacterVariableEffectV1(g_fixture->node.data(),context);
  else if(root==g_fixture->event_roots[1].data())
    ObservedScopedEventImmediateRootV1(g_fixture->event_roots[7].data(),context);
  else ObservedScopedEventImmediateRootV1(g_ordinary_nested_root.data(),context);
}
void EventProducerIdentity() {
  auto *space=static_cast<std::byte*>(VirtualAlloc(nullptr,0x6000000,MEM_RESERVE,PAGE_NOACCESS));assert(space);
  assert(VirtualAlloc(space+0x44CF000,4096,MEM_COMMIT,PAGE_READWRITE));
  const auto module=reinterpret_cast<std::uintptr_t>(space);Fixture f;f.Events(module);g_fixture=&f;
  Put(f.node.data(),0,module+0x44D19B0);Put(g_ordinary_nested_root.data(),0,module+0x44CF030);
  assert(BindScopedVariableMonitorOfflineOriginalsV1(Owner,Setter,Effect,House,RootOriginal));
  auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();
  assert(StartScopedCharacterVariableMonitorV1(*m,f.bindings,module,{101,201},29,true,true,
      reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot),
      reinterpret_cast<std::uintptr_t>(&f.event_manager_slot)));
  const auto calls=g_root_calls;
  ObservedScopedEventImmediateRootV1(f.event_roots[0].data(),f.context.data());
  assert(g_root_calls==calls+2);
  const auto &before=Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_enter);
  const auto &after=Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_return);
  assert(before.event_producer.read&&before.event_producer.invocation!=0&&
      before.event_producer.definition==reinterpret_cast<std::uintptr_t>(f.event_defs[0].data())&&
      before.event_producer.immediate_root==reinterpret_cast<std::uintptr_t>(f.event_roots[0].data()));
  assert(before.event_producer.invocation==after.event_producer.invocation&&
      before.event_producer.definition_id==1200&&before.event_producer.runtime_stats_ordinal==0&&
      before.event_producer.original_execute_rva==0x3380EC0);
  assert(before.event_producer.matched_root_execution_depth==1&&before.event_producer.active_effect_group_depth==2);
  assert(before.requested_value_decoding.flag_name_read&&before.requested_value_decoding.flag_name.size==3&&
      after.value.flag_name_read&&after.value.flag_name.size==3);
  ObservedScopedEventImmediateRootV1(f.event_roots[1].data(),f.context.data());
  assert(!Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_return,true).event_producer.read);
  g_nested_matched=true;ObservedScopedEventImmediateRootV1(f.event_roots[0].data(),f.context.data());g_nested_matched=false;
  const auto &outer=Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_return,true);
  assert(outer.event_producer.read&&outer.event_producer.definition_id==1200&&outer.event_producer.matched_root_execution_depth==1);
  bool inner=false;for(std::uint32_t i=0;i<m->count.load();++i){const auto &r=m->records[i];
    if(r.boundary==ScopedVariableMonitorBoundaryV1::variable_write_return&&r.event_producer.definition_id==1202)
      inner=r.event_producer.matched_root_execution_depth==2&&r.event_producer.active_effect_group_depth==3;
  }assert(inner);
  // Outside the actual root's call its TLS must be restored, not cached.
  (void)ObservedCharacterVariableEffectV1(f.node.data(),f.context.data());
  assert(!Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_return,true).event_producer.read);
  assert(FinishScopedCharacterVariableMonitorV1(*m,true)&&m->failure_flags.load()==0);
  std::cout<<"{\"kind\":\"OFFLINE_PRODUCER_FIXTURE_NOT_GAME_TRUTH\",\"scoped_variable_monitor\":"
           <<SerializeScopedCharacterVariableMonitorV1(*m)<<"}\n";
  // Same compiled root for two definitions is ambiguous and must not arm.
  Put(f.event_defs[1].data(),0x230,reinterpret_cast<std::uintptr_t>(f.event_roots[0].data()));
  auto ambiguous=std::make_unique<ScopedCharacterVariableMonitorV1>();
  assert(!StartScopedCharacterVariableMonitorV1(*ambiguous,f.bindings,module,{101,201},30,true,true,
      reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot),
      reinterpret_cast<std::uintptr_t>(&f.event_manager_slot)));
  assert(!ScopedVariableMonitorHasInstalledHooksV1(*ambiguous));
  assert(VirtualFree(space,0,MEM_RELEASE));
  std::cout<<"actual root / nested inheritance / exact event definition / TLS restoration / shared root rejection PASS\n";
}
std::uint32_t g_commit_calls=0;
bool g_nested_death=false,g_raise_commit=false;
std::array<std::byte,0x1D0> g_unrelated_victim{};
void CommitForProducer(void *manager,void *victim,void *reason,void *date,void *killer,void *artifact){
  ++g_commit_calls;
  CombatScopedDeathCommitContextV1 current{};
  if(victim==g_unrelated_victim.data()){
    assert(!ReadCurrentCombatScopedDeathCommitContextV1(current)&&!current.read);
    ObservedScopedEventImmediateRootV1(g_fixture->event_roots[2].data(),g_fixture->context.data());
    return;
  }
  assert(ReadCurrentCombatScopedDeathCommitContextV1(current)&&current.read);
  assert(current.victim_id==101&&current.killer_id==201&&current.invocation!=0&&
      current.victim_full_identity_matches&&current.killer_full_identity_matches&&
      current.thread_id==GetCurrentThreadId()&&current.reason_key_read);
  if(g_raise_commit)RaiseException(0xE0420037,0,0,nullptr);
  if(g_nested_death){
    ScopedDeathCommit(manager,g_unrelated_victim.data(),reason,date,killer,nullptr);
    CombatScopedDeathCommitContextV1 restored{};
    assert(ReadCurrentCombatScopedDeathCommitContextV1(restored)&&restored==current);
  }
  ObservedScopedEventImmediateRootV1(g_fixture->event_roots[0].data(),g_fixture->context.data());
  CombatScopedDeathCommitContextV1 after{};
  assert(ReadCurrentCombatScopedDeathCommitContextV1(after)&&after==current);
  assert(current.artifact==reinterpret_cast<std::uintptr_t>(artifact));
}
void UnusedDeath(void *,void *,void *,void *,void *,void *){}
std::uintptr_t UnusedQueue(void *,const void *){return 0;}
std::uintptr_t UnusedCasualty(void *,std::int64_t,void *){return 0;}
bool RaisedCommitContextRestored(void *manager,void *victim,void *reason,void *date,void *killer) {
  bool caught=false;
  __try {ScopedDeathCommit(manager,victim,reason,date,killer,nullptr);}
  __except(GetExceptionCode()==0xE0420037?EXCEPTION_EXECUTE_HANDLER:EXCEPTION_CONTINUE_SEARCH){caught=true;}
  CombatScopedDeathCommitContextV1 current{};
  return caught&&!ReadCurrentCombatScopedDeathCommitContextV1(current)&&!current.read;
}
void SynchronousDeathCommitAttribution() {
  auto *space=static_cast<std::byte*>(VirtualAlloc(nullptr,0x6000000,MEM_RESERVE,PAGE_NOACCESS));assert(space);
  assert(VirtualAlloc(space+0x44CF000,4096,MEM_COMMIT,PAGE_READWRITE));
  const auto module=reinterpret_cast<std::uintptr_t>(space);Fixture f;f.Events(module);g_fixture=&f;
  Put(f.node.data(),0,module+0x44D19B0);Put(g_ordinary_nested_root.data(),0,module+0x44CF030);
  assert(BindScopedVariableMonitorOfflineOriginalsV1(Owner,Setter,Effect,House,RootOriginal));
  assert(BindCombatScopedOriginalsForOfflineFixtureV1(UnusedDeath,CommitForProducer,UnusedQueue,UnusedCasualty));
  auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();
  assert(StartScopedCharacterVariableMonitorV1(*m,f.bindings,module,{101,201},37,true,true,
      reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot),
      reinterpret_cast<std::uintptr_t>(&f.event_manager_slot)));
  std::array<std::byte,0x720> combat{};
  std::array<std::byte,0x80> trait_db{};std::array<std::byte,0x298> trait_def{};std::array<std::byte,0x40> reason{};
  std::array<std::byte,0x18> artifact{};std::uintptr_t defptr=reinterpret_cast<std::uintptr_t>(trait_def.data());
  Put(trait_def.data(),0x10,std::int32_t(1));Key(trait_def.data()+0x18,"brave");
  Put(trait_db.data(),0x68,reinterpret_cast<std::uintptr_t>(&defptr));Put(trait_db.data(),0x74,std::int32_t(1));
  Key(reason.data()+0x18,"death_battle");Put(artifact.data(),0x10,std::int32_t(51));
  std::int64_t requested_date=53146872;
  CombatPhaseEventTraceCapturePlanV1 plan{};
  plan.module_base=module;plan.managed_daily_sequence_token=73;plan.combat_id=0x01000002;
  plan.combat=reinterpret_cast<std::uintptr_t>(combat.data());Put(combat.data(),8,plan.combat_id);
  plan.current_date_slot=reinterpret_cast<std::uintptr_t>(&f.date_slot);plan.expected_current_date_object=f.date_slot;
  plan.character_count=2;plan.loaded_event_row_objects_available=true;
  for(std::size_t i=0;i<2;++i){plan.characters[i]={std::int32_t(101+i*100),reinterpret_cast<std::uintptr_t>(f.chars[i].data())};
    plan.sides[i]=plan.combat+(i==0?0x20:0x368);Put(reinterpret_cast<void*>(plan.sides[i]),0xB8,plan.combat);}
  auto chain=std::make_unique<CombatScopedChainV1>();
  assert(ArmCombatScopedChainV1(*chain,plan,101,201,11,reinterpret_cast<std::uintptr_t>(trait_db.data())));
  const auto original_calls=g_commit_calls;
  // Original commit -> exact notification root -> actual signature setter.
  ScopedDeathCommit(combat.data(),f.chars[0].data(),reason.data(),&requested_date,f.chars[1].data(),artifact.data());
  assert(g_commit_calls==original_calls+1);
  const auto &sync=Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_return,true);
  assert(sync.event_producer.activation_death_commit_context.read&&sync.current_death_commit_context.read);
  assert(sync.current_death_commit_context==sync.event_producer.activation_death_commit_context&&
      sync.current_death_commit_context.managed_daily_sequence_token==73&&
      sync.current_death_commit_context.artifact_id_read&&sync.current_death_commit_context.artifact_id==51&&
      !sync.current_death_commit_context.artifact_actual_null);
  CombatScopedDeathCommitContextV1 outside{};
  assert(!ReadCurrentCombatScopedDeathCommitContextV1(outside)&&!outside.read);
  // Same matched producer outside a currently active commit remains unclaimed.
  ObservedScopedEventImmediateRootV1(f.event_roots[0].data(),f.context.data());
  const auto &async=Find(*m,ScopedVariableMonitorBoundaryV1::variable_write_return,true);
  assert(async.event_producer.read&&!async.event_producer.activation_death_commit_context.read&&
      !async.current_death_commit_context.read);
  Put(g_unrelated_victim.data(),0x18,std::int32_t(301));g_nested_death=true;
  const auto nested_start=m->count.load();
  ScopedDeathCommit(combat.data(),f.chars[0].data(),reason.data(),&requested_date,f.chars[1].data(),nullptr);
  g_nested_death=false;assert(g_commit_calls==original_calls+3);
  bool unrelated=false,outer_restored=false;
  for(std::uint32_t i=nested_start;i<m->count.load();++i){const auto &r=m->records[i];
    if(r.boundary!=ScopedVariableMonitorBoundaryV1::variable_write_return)continue;
    if(r.event_producer.definition_id==1202){unrelated=true;assert(!r.current_death_commit_context.read&&!r.event_producer.activation_death_commit_context.read);}
    if(r.event_producer.definition_id==1200){outer_restored=true;assert(r.current_death_commit_context.read&&
        r.current_death_commit_context==r.event_producer.activation_death_commit_context&&
        r.current_death_commit_context.artifact_actual_null&&!r.current_death_commit_context.artifact_id_read);}
  }assert(unrelated&&outer_restored);
  assert(!ReadCurrentCombatScopedDeathCommitContextV1(outside));
  FinishCombatScopedChainV1(*chain);assert(chain->failure_flags.load()==0);
  assert(FinishScopedCharacterVariableMonitorV1(*m,true)&&m->failure_flags.load()==0);
  std::cout<<"{\"kind\":\"OFFLINE_COMMIT_PRODUCER_FIXTURE_NOT_GAME_TRUTH\",\"scoped_transition_chain\":"
           <<SerializeCombatScopedChainV1(*chain)<<",\"scoped_variable_monitor\":"<<SerializeScopedCharacterVariableMonitorV1(*m)<<"}\n";
  // SEH unwind restores TLS and the shared callback gate; no fabricated return.
  auto raised=std::make_unique<CombatScopedChainV1>();
  assert(ArmCombatScopedChainV1(*raised,plan,101,201,11,reinterpret_cast<std::uintptr_t>(trait_db.data())));
  g_raise_commit=true;assert(RaisedCommitContextRestored(combat.data(),f.chars[0].data(),reason.data(),&requested_date,f.chars[1].data()));g_raise_commit=false;
  assert(g_commit_calls==original_calls+4);CancelCombatScopedChainV1(*raised);
  assert(TryEnterScopedObserverMutationV1());LeaveScopedObserverMutationV1();
  assert(VirtualFree(space,0,MEM_RELEASE));
  std::cout<<"same original commit / async unclaimed / unrelated nested death isolation / restored outer tuple / actual null artifact / SEH restoration / forward once PASS\n";
}
void WholeCallbackAndParentLifetime() {
  Fixture f;auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();g_fixture=&f;
  assert(BindScopedVariableMonitorOfflineOriginalsV1(BlockedOwner,Setter,Effect,House));
  assert(StartScopedCharacterVariableMonitorV1(*m,f.bindings,0x140000000,{101,201},18,true,true,
      reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot)));
  g_callback_entered=CreateEventW(nullptr,TRUE,FALSE,nullptr);
  g_callback_release=CreateEventW(nullptr,TRUE,FALSE,nullptr);
  const auto calls=g_owner_calls;void *returned=nullptr;
  std::thread original([&]{returned=ObservedCharacterVariableOwnerV1(f.scopes[1].data());});
  assert(WaitForSingleObject(g_callback_entered,5000)==WAIT_OBJECT_0);
  // An original call is still running. Finish must reject immediately while
  // leaving the complete session armed, rather than freeing/unpatching it.
  assert(m->active_callbacks.load()==1);
  assert(!FinishScopedCharacterVariableMonitorV1(*m,true));
  assert(m->stage==ScopedVariableMonitorStageV1::armed&&m->armed.load()==1);
  assert(!TryEnterScopedObserverMutationV1());
  SetEvent(g_callback_release);original.join();
  assert(returned==f.owners[1].data()&&g_owner_calls==calls+1&&m->active_callbacks.load()==0);
  assert(FinishScopedCharacterVariableMonitorV1(*m,true));
  const auto count=m->count.load();
  // A branch that had already selected its wrapper still forwards exactly
  // once after drain. Session was unpublished; there is no new journal row.
  assert(ObservedCharacterVariableOwnerV1(f.scopes[1].data())==returned);
  assert(g_owner_calls==calls+2&&m->count.load()==count);
  CloseHandle(g_callback_entered);CloseHandle(g_callback_release);
  bool destroyed=false;auto parent=std::make_unique<ResidentParent>();parent->destroyed=&destroyed;
  auto *raw=parent.get();RetainScopedObserverParentUntilProcessExitV1(parent,true);
  assert(parent==nullptr&&!destroyed&&*raw->child_plan==73);
  // Offline test owns all references; only it can reclaim its fake parent.
  delete raw;assert(destroyed);
  std::cout<<"whole-original callback drain rejection / late forwarding / whole parent retention PASS\n";
}
}
namespace {
std::atomic<std::uint32_t> g_null_original_calls{0};
std::atomic<bool> g_null_return_nonnull{false};
void *NullOwner(const void *) {
  g_null_original_calls.fetch_add(1);
  return g_null_return_nonnull.load()?g_fixture->owners[1].data():nullptr;
}
__declspec(noinline) void NullCalls(Fixture &f,std::uint32_t count) {
  for(std::uint32_t i=0;i<count;++i)(void)ObservedCharacterVariableOwnerV1(f.scopes[1].data());
}
std::uintptr_t NullEffect(void *,void *){NullCalls(*g_fixture,2);return 0x1234;}
void NullRoot(void *,void *){NullCalls(*g_fixture,2);}
void NullCommit(void *,void *,void *,void *,void *,void *){NullCalls(*g_fixture,2);}
bool NullArm(ScopedCharacterVariableMonitorV1 &m,Fixture &f) {
  g_fixture=&f;g_null_return_nonnull.store(false);g_null_original_calls.store(0);
  Put(f.chars[1].data(),0x1C8,std::uintptr_t(123));
  assert(BindScopedVariableMonitorOfflineOriginalsV1(NullOwner,Setter,NullEffect,House,NullRoot));
  return StartScopedCharacterVariableMonitorV1(m,f.bindings,0x140000000,{101,201},61,true,true,
      reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot));
}
void DeadNullRepeatedAndTransitions() {
  Fixture f;auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();assert(NullArm(*m,f));
  NullCalls(f,1000);
  assert(g_null_original_calls.load()==1000&&m->owner_getter_observed.load()==1000);
  assert(m->owner_getter_retained.load()==1&&m->owner_getter_coalesced.load()==999);
  const auto &first=Find(*m,ScopedVariableMonitorBoundaryV1::original_owner_return);
  assert(first.victim_dead&&!first.value.read&&first.owner==0&&first.full_identity_matches);
  assert(first.owner_observation_count==1000&&first.owner_observation_first_call_index==0&&first.owner_observation_last_call_index==999);
  // Never reuse a null row across null -> nonnull -> null transitions.
  g_null_return_nonnull.store(true);NullCalls(f,1);
  g_null_return_nonnull.store(false);NullCalls(f,1);NullCalls(f,10);
  assert(m->owner_getter_retained.load()==4&&m->owner_getter_coalesced.load()==1008);
  const auto &last=Find(*m,ScopedVariableMonitorBoundaryV1::original_owner_return,true);
  assert(last.owner_state_epoch==3&&last.owner_observation_count==10&&last.previous_owner==0);
  // An actual house invocation cuts the aggregate interval; both edges remain.
  const auto kept=m->owner_getter_retained.load();
  for(int i=0;i<5;++i)(void)ObservedScopedHousePredicateV1(f.type.data(),f.houses[0].data(),f.houses[1].data());
  NullCalls(f,10);assert(m->owner_getter_retained.load()==kept+1);
  // Dead-state change, source scope pointer and source callsite must not aggregate.
  Put(f.chars[1].data(),0x1C8,std::uintptr_t(0));NullCalls(f,3);
  assert(m->owner_getter_retained.load()==kept+4);
  Put(f.chars[1].data(),0x1C8,std::uintptr_t(123));
  std::array<std::uint64_t,2> other_scope{4,201};
  (void)ObservedCharacterVariableOwnerV1(other_scope.data());
  assert(m->owner_getter_retained.load()==kept+5);
  Put(f.date.data(),8,std::int32_t(53146872));NullCalls(f,2);
  assert(FinishScopedCharacterVariableMonitorV1(*m,true)&&m->failure_flags.load()==0);
  std::cout<<"{\"kind\":\"OFFLINE_DEAD_NULL_COMPRESSION_FIXTURE_NOT_GAME_TRUTH\",\"scoped_variable_monitor\":"<<SerializeScopedCharacterVariableMonitorV1(*m)<<"}\n";
  std::cout<<"exact repeated null / original forward once / owner-dead-date-source transitions / house edges PASS\n";
}
void ConcurrentDeadNullReturns() {
  Fixture f;auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();assert(NullArm(*m,f));
  std::array<std::thread,8> workers;
  for(auto &worker:workers)worker=std::thread([&]{NullCalls(f,250);});
  for(auto &worker:workers)worker.join();
  assert(g_null_original_calls.load()==2000&&m->owner_getter_observed.load()==2000);
  assert(m->owner_getter_retained.load()==8&&m->owner_getter_coalesced.load()==1992);
  std::array<DWORD,8> threads{};std::uint32_t n=0;
  for(std::uint32_t i=0;i<m->count.load();++i){const auto &r=m->records[i];
    if(r.boundary!=ScopedVariableMonitorBoundaryV1::original_owner_return)continue;
    assert(r.owner_observation_count==250&&r.owner_observation_last_call_index>=r.owner_observation_first_call_index);
    threads[n++]=r.thread_id;
  }
  assert(n==8);for(std::size_t i=0;i<n;++i)for(std::size_t j=0;j<i;++j)assert(threads[i]!=threads[j]);
  assert(FinishScopedCharacterVariableMonitorV1(*m,true)&&m->failure_flags.load()==0);
  std::cout<<"eight concurrent original GUI-like threads / locked state and aggregation / separate thread first rows PASS\n";
}
void ContextsWritersAndOverflow() {
  Fixture f;auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();assert(NullArm(*m,f));
  (void)ObservedCharacterVariableEffectV1(f.node.data(),f.context.data());
  auto other_context=f.context;
  (void)ObservedCharacterVariableEffectV1(f.node.data(),other_context.data());
  assert(m->owner_getter_retained.load()==2&&m->owner_getter_coalesced.load()==2);
  assert(FinishScopedCharacterVariableMonitorV1(*m,true)&&m->failure_flags.load()==0);
  // Real setters are never compressed, even when requested/current values repeat.
  auto writers=std::make_unique<ScopedCharacterVariableMonitorV1>();assert(Arm(*writers,f));
  for(int i=0;i<30;++i)(void)ObservedCharacterVariableEffectV1(f.node.data(),f.context.data());
  std::uint32_t enters=0,returns=0;
  for(std::uint32_t i=0;i<writers->count.load();++i){const auto b=writers->records[i].boundary;
    enters+=b==ScopedVariableMonitorBoundaryV1::variable_write_enter;returns+=b==ScopedVariableMonitorBoundaryV1::variable_write_return;}
  assert(enters==30&&returns==30&&writers->owner_getter_coalesced.load()==0);
  assert(FinishScopedCharacterVariableMonitorV1(*writers,true)&&writers->failure_flags.load()==0);
  auto overflow=std::make_unique<ScopedCharacterVariableMonitorV1>();assert(NullArm(*overflow,f));
  for(int i=0;i<70;++i)(void)ObservedScopedHousePredicateV1(f.type.data(),f.houses[0].data(),f.houses[1].data());
  assert((overflow->failure_flags.load()&scoped_chain_failure_capacity)!=0&&overflow->records.size()==128);
  assert(FinishScopedCharacterVariableMonitorV1(*overflow,true));
  assert(SerializeScopedCharacterVariableMonitorV1(*overflow).find("\"truncated\":true")!=std::string::npos);
  std::cout<<"different original effect contexts retained / 30 identical setters preserve60edges / capacity128 overflow staysRED PASS\n";
}
void NullProducerContexts() {
  auto *space=static_cast<std::byte*>(VirtualAlloc(nullptr,0x6000000,MEM_RESERVE,PAGE_NOACCESS));assert(space);
  assert(VirtualAlloc(space+0x44CF000,4096,MEM_COMMIT,PAGE_READWRITE));
  const auto module=reinterpret_cast<std::uintptr_t>(space);Fixture f;f.Events(module);g_fixture=&f;
  Put(f.chars[1].data(),0x1C8,std::uintptr_t(123));g_null_return_nonnull.store(false);
  assert(BindScopedVariableMonitorOfflineOriginalsV1(NullOwner,Setter,NullEffect,House,NullRoot));
  auto m=std::make_unique<ScopedCharacterVariableMonitorV1>();
  assert(StartScopedCharacterVariableMonitorV1(*m,f.bindings,module,{101,201},71,true,true,
      reinterpret_cast<std::uintptr_t>(f.table.data()),reinterpret_cast<std::uintptr_t>(&f.date_slot),reinterpret_cast<std::uintptr_t>(&f.event_manager_slot)));
  ObservedScopedEventImmediateRootV1(f.event_roots[0].data(),f.context.data());
  ObservedScopedEventImmediateRootV1(f.event_roots[0].data(),f.context.data());
  ObservedScopedEventImmediateRootV1(f.event_roots[1].data(),f.context.data());
  assert(m->owner_getter_retained.load()==3&&m->owner_getter_coalesced.load()==3);
  const auto &last=Find(*m,ScopedVariableMonitorBoundaryV1::original_owner_return,true);
  assert(last.event_producer.read&&last.event_producer.definition_id==1201);
  // Same null return on the same thread/source, but different original commits.
  assert(BindCombatScopedOriginalsForOfflineFixtureV1(UnusedDeath,NullCommit,UnusedQueue,UnusedCasualty));
  std::array<std::byte,0x720> combat{};std::array<std::byte,0x80> trait_db{};
  std::array<std::byte,0x298> trait_def{};std::array<std::byte,0x40> reason{};std::uintptr_t defptr=reinterpret_cast<std::uintptr_t>(trait_def.data());
  Put(trait_def.data(),0x10,std::int32_t(1));Key(trait_def.data()+0x18,"brave");
  Put(trait_db.data(),0x68,reinterpret_cast<std::uintptr_t>(&defptr));Put(trait_db.data(),0x74,std::int32_t(1));
  Key(reason.data()+0x18,"death_battle");std::int64_t requested_date=53146848;
  std::array<std::byte,0x30> death_data{};
  Put(death_data.data(),4,requested_date);Put(death_data.data(),0x10,reinterpret_cast<std::uintptr_t>(reason.data()));
  Put(death_data.data(),0x18,std::int32_t(101));Put(death_data.data(),0x1C,std::int32_t(-1));
  Put(f.chars[1].data(),0x1C8,reinterpret_cast<std::uintptr_t>(death_data.data()));
  CombatPhaseEventTraceCapturePlanV1 plan{};plan.module_base=module;plan.managed_daily_sequence_token=81;
  plan.combat_id=0x01000002;plan.combat=reinterpret_cast<std::uintptr_t>(combat.data());Put(combat.data(),8,plan.combat_id);
  plan.current_date_slot=reinterpret_cast<std::uintptr_t>(&f.date_slot);plan.expected_current_date_object=f.date_slot;
  plan.character_count=2;plan.loaded_event_row_objects_available=true;
  for(std::size_t i=0;i<2;++i){plan.characters[i]={std::int32_t(101+i*100),reinterpret_cast<std::uintptr_t>(f.chars[i].data())};
    plan.sides[i]=plan.combat+(i==0?0x20:0x368);Put(reinterpret_cast<void*>(plan.sides[i]),0xB8,plan.combat);}
  auto chain=std::make_unique<CombatScopedChainV1>();assert(ArmCombatScopedChainV1(*chain,plan,101,201,11,reinterpret_cast<std::uintptr_t>(trait_db.data())));
  ScopedDeathCommit(combat.data(),f.chars[0].data(),reason.data(),&requested_date,f.chars[1].data(),nullptr);
  const auto commit1=Find(*m,ScopedVariableMonitorBoundaryV1::original_owner_return,true).current_death_commit_context;
  ScopedDeathCommit(combat.data(),f.chars[0].data(),reason.data(),&requested_date,f.chars[1].data(),nullptr);
  const auto commit2=Find(*m,ScopedVariableMonitorBoundaryV1::original_owner_return,true).current_death_commit_context;
  assert(commit1.read&&commit2.read&&commit1.invocation!=commit2.invocation);
  assert(m->owner_getter_retained.load()==5&&m->owner_getter_coalesced.load()==5);
  FinishCombatScopedChainV1(*chain);assert(chain->failure_flags.load()==0);
  assert(FinishScopedCharacterVariableMonitorV1(*m,true)&&m->failure_flags.load()==0);
  assert(VirtualFree(space,0,MEM_RELEASE));
  std::cout<<"different actual notification producer invocations / definitions / current commit tuples never aggregate PASS\n";
}
}
int main(){Observation();Guards();ExactAnchorsAndRollback();WholeCallbackAndParentLifetime();EventProducerIdentity();SynchronousDeathCommitAttribution();DeadNullRepeatedAndTransitions();ConcurrentDeadNullReturns();ContextsWritersAndOverflow();NullProducerContexts();std::cout<<"passive monitor offline checks passed; no CK3 process invoked\n";}
