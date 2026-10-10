#include "xar_bridge/ck3_12004_actual_assault_consumer_journal.hpp"
#include "xar_bridge/army_actual_assault_consumer_observations_v1_serializer.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "../tests/actual_assault_budget_focus_12004.hpp"
#include <array>
#include <bit>
#include <cstring>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

void PrepareArmySiegeChildNaturalFocus12004(void *);
void RunArmySiegeChildNaturalFocus12004();
void VerifyArmySiegeChildNaturalFocus12004();
namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase=0x140000000ULL;
constexpr std::uintptr_t kBits=0xF765432112345678ULL;
constexpr std::uint32_t kArRg=0x80000002U, kRegi=0x80000001U, kSiege=0x01000001U;
struct Range{std::uintptr_t address;std::size_t size;};
std::vector<Range> g_ranges;
std::map<std::uintptr_t,std::array<std::byte,8>> g_slots;
alignas(8) std::array<std::byte,0x1A0> g_manager;
alignas(8) std::array<std::byte,0xC8> g_state;
alignas(8) std::array<std::byte,0x180> g_table;
alignas(8) std::array<std::byte,0x160> g_army;
alignas(8) std::array<std::byte,0x150> g_arrg;
alignas(8) std::array<std::byte,0x120> g_regi;
alignas(8) std::array<std::byte,0x2A8> g_definition;
alignas(8) std::array<std::byte,0x400> g_siege;
alignas(8) std::array<std::byte,0x860> g_province;
alignas(8) std::array<std::byte,0x20> g_data;
std::array<std::array<std::byte,0x30>,4> g_registries;
std::array<std::array<std::byte,0x300>,4> g_registry_tables;
std::array<std::uint32_t,3> g_army_ids{42,UINT32_MAX,42};
std::array<std::uint32_t,2> g_arrg_ids{kArRg,kArRg};
std::array<std::uint32_t,1> g_roster{kArRg};
std::array<std::uint32_t,4> g_pending{17,17,UINT32_MAX,0};
unsigned g_calls=0;
bool g_release_scene=false, g_deny_after_current=false;
void Require(bool value,const char *reason){if(!value)throw std::runtime_error(reason);}
template<class T> void Store(void *object,std::size_t off,T value){std::memcpy(static_cast<std::byte*>(object)+off,&value,sizeof(value));}
template<class T> void Add(T &blob){g_ranges.push_back({reinterpret_cast<std::uintptr_t>(blob.data()),sizeof(blob)});}
void Slot(std::uintptr_t rva,std::uintptr_t value){auto &bytes=g_slots[kBase+rva];std::memcpy(bytes.data(),&value,8);}
bool ReadOwned(void *,const void *p,void *out,std::size_t n) noexcept {
  auto a=reinterpret_cast<std::uintptr_t>(p);
  if(g_deny_after_current && g_calls && a==reinterpret_cast<std::uintptr_t>(g_regi.data())+0x1C)return false;
  auto it=g_slots.find(a);if(it!=g_slots.end() && n<=8){std::memcpy(out,it->second.data(),n);return true;}
  for(auto r:g_ranges)if(a>=r.address && n<=r.size && a-r.address<=r.size-n){std::memcpy(out,p,n);return true;}
  return false;
}
bool PhaseRead(void *ctx,std::uintptr_t a,void *out,std::size_t n) noexcept{return ReadOwned(ctx,reinterpret_cast<const void*>(a),out,n);}
void Registry(std::size_t index,std::uintptr_t registry_rva,std::uintptr_t fallback_rva,
    std::uint32_t full,std::uintptr_t object){
  auto &r=g_registries[index];auto &t=g_registry_tables[index];
  Store(r.data(),0x20,reinterpret_cast<std::uintptr_t>(t.data()));Store(r.data(),0x2C,std::uint32_t{48});
  Store(t.data(),std::size_t(full&0xFFFFFFU)*16+8,object);
  Slot(registry_rva,reinterpret_cast<std::uintptr_t>(r.data()));Slot(fallback_rva,object);
}
void Header(void *record,std::size_t offset,const void *payload,std::int32_t count,std::uintptr_t allocator){
  Store(record,offset,reinterpret_cast<std::uintptr_t>(payload));Store(record,offset+8,count);
  Store(record,offset+12,count);Store(record,offset+16,allocator);
}
void Reset(){
  g_ranges.clear();g_slots.clear();g_calls=0;g_release_scene=false;g_deny_after_current=false;
  g_manager.fill({});g_state.fill({});g_table.fill({});g_army.fill({});g_arrg.fill({});g_regi.fill({});
  g_definition.fill({});g_siege.fill({});g_province.fill({});g_data.fill({});
  for(auto &r:g_registries)r.fill({});for(auto &r:g_registry_tables)r.fill({});
  Add(g_manager);Add(g_state);Add(g_table);Add(g_army);Add(g_arrg);Add(g_regi);Add(g_definition);Add(g_siege);Add(g_province);Add(g_data);
  Add(g_army_ids);Add(g_arrg_ids);Add(g_roster);Add(g_pending);for(auto &r:g_registries)Add(r);for(auto &r:g_registry_tables)Add(r);
  Store(g_state.data(),8,std::uint64_t{0x1234567800000011ULL});Store(g_state.data(),0x9C,std::uint32_t{17});Store(g_state.data(),0xC0,std::uint8_t{2});
  Header(g_manager.data(),0x50,g_army_ids.data(),3,0);
  Header(g_manager.data(),0x68,g_pending.data(),2,0);
  Store(g_manager.data(),0x178,reinterpret_cast<std::uintptr_t>(g_table.data()));
  Store(g_manager.data(),0x180,std::int32_t{2});Store(g_manager.data(),0x184,std::int32_t{3});
  Store(g_manager.data(),0x188,std::uint8_t{1});Store(g_manager.data(),0x18C,std::uint32_t{0x3F000000});
  Store(g_table.data(),5*0x40+4,std::uint8_t{255});
  for(auto slot:{1,3}){auto *record=g_table.data()+slot*0x40;
    Store(record,0,std::uint32_t{123});Store(record,4,std::uint8_t{2});Store(record,8,kSiege);
    Header(record,0x10,g_army_ids.data(),3,kBase+0x54E0570);Header(record,0x28,g_arrg_ids.data(),2,kBase+0x54DEB68);
  }
  Store(g_army.data(),0x10,std::uint32_t{42});Header(g_army.data(),0x38,g_roster.data(),1,0);
  Store(g_arrg.data(),0x10,kArRg);Store(g_arrg.data(),0x14,std::uint32_t{0x41725267});
  Store(g_arrg.data(),0x18,reinterpret_cast<std::uintptr_t>(g_definition.data()));Store(g_definition.data(),0x2A0,std::int32_t{0});
  Store(g_arrg.data(),0x20,reinterpret_cast<std::uintptr_t>(g_data.data()));Store(g_arrg.data(),0x28,std::int32_t{2});Store(g_arrg.data(),0x2C,std::int32_t{2});
  Store(g_arrg.data(),0x38,std::int32_t{100});Store(g_arrg.data(),0x3C,std::int32_t{200});Store(g_arrg.data(),0x148,UINT32_MAX);
  Store(g_regi.data(),0x10,kRegi);Store(g_regi.data(),0x14,std::uint32_t{0x52656769});
  auto *chunk=g_regi.data()+0x18;Store(chunk,0,std::int32_t{100});Store(chunk,4,std::int32_t{50});
  Store(chunk,8,std::bit_cast<std::int32_t>(kRegi));Store(chunk,12,std::int32_t{6});
  Store(chunk,16,std::bit_cast<std::int32_t>(kArRg));Store(chunk,24,std::int32_t{0});
  for(auto i:{0,1}){Store(g_data.data(),i*16+8,kRegi);Store(g_data.data(),i*16+12,std::int32_t{0});}
  Store(g_siege.data(),8,kSiege);Store(g_siege.data(),0x200,reinterpret_cast<std::uintptr_t>(g_province.data()));Store(g_siege.data(),0x3D8,std::int32_t{1});
  Store(g_province.data(),0x10,std::uint32_t{55});Store(g_province.data(),0x85C,std::uint32_t{0x50726F76});
  Registry(0,0x5D1DE48,0x5D1DE50,42,reinterpret_cast<std::uintptr_t>(g_army.data()));
  Registry(1,0x5D1F340,0x5D1F338,kArRg,reinterpret_cast<std::uintptr_t>(g_arrg.data()));
  Registry(2,0x5D1EB68,0x5D1EB58,kRegi,reinterpret_cast<std::uintptr_t>(g_regi.data()));
  Registry(3,0x5D1EC88,0x5D1EC60,kSiege,reinterpret_cast<std::uintptr_t>(g_siege.data()));
}
std::uintptr_t __fastcall OwnedConsumer(void *manager){
  ++g_calls;ArmyAssaultConsumerParent12004 parent;
  Require(CopyActiveArmyAssaultConsumerParent12004(parent)&&parent.exact_post_date_parent,"consumer parent missing");
  Require(parent.manager_identity==reinterpret_cast<std::uintptr_t>(manager),"manager changed");
  if(g_release_scene){RunArmySiegeChildNaturalFocus12004();return kBits;}
  Require(focus::RunActualAssaultBudgetFocus12004(g_siege.data())==focus::kActualBudgetFocusRawReturn12004,
    "real budget child raw RAX changed");
  focus::RunExcludedActualAssaultBudgetFocus12004(g_siege.data());
  auto entry=NextArmyNaturalPhaseEvent12004();auto returned=NextArmyNaturalPhaseEvent12004();
  Require(RecordActualAssaultConsumerBudget12004(reinterpret_cast<std::uintptr_t>(g_siege.data()),0x2A97F64,
    entry,returned,-1,kSiege,reinterpret_cast<std::uintptr_t>(g_province.data()),55),"signed budget plumbing attachment failed");
  Store(g_regi.data(),0x1C,std::int32_t{35});Store(g_arrg.data(),0x38,std::int32_t{70});
  Store(g_manager.data(),0x74,std::int32_t{3});Store(g_manager.data(),0x70,std::int32_t{4});
  for(auto slot:{1,3}){auto *record=g_table.data()+slot*0x40;Store(record,4,std::uint8_t{0});
    for(auto off:{0x10,0x28}){Store(record,off,std::uintptr_t{0});Store(record,off+8,std::int32_t{0});Store(record,off+12,std::int32_t{0});}}
  Store(g_manager.data(),0x180,std::int32_t{0});return kBits;
}
std::uintptr_t __fastcall OwnedPhase(void *secondary){
  return InvokeActualAssaultConsumerObserver12004(static_cast<std::byte*>(secondary)-8,0x2A9A8EA);
}
ArmyNaturalPhaseRecord12004 RunPhase(){
  ArmyNaturalPhaseBindings12004 b;b.read=&PhaseRead;b.game_state_identity=reinterpret_cast<std::uintptr_t>(g_state.data());
  return InvokeArmyNaturalPhaseScope12004(b,&OwnedPhase,g_manager.data()+8,ArmyNaturalPhaseKind12004::post_date,0x123);
}
}

// Unique central33 connected compound fragment; no main, private clock or TLS injection.
void RunArmyAssaultConsumerNaturalFocus12004(){
  using namespace xar::ck3_12004;
  Reset();auto binding=BindActualAssaultConsumerJournalImage12004(kBase,kExecutableSha256);binding.read_memory=&ReadOwned;
  focus::PrepareActualAssaultBudgetFocus12004();
  Require(InitializeActualAssaultConsumerJournalFixture12004(binding,&OwnedConsumer),"consumer fixture initialization failed");
  auto phase=RunPhase();Require(phase.original_called&&phase.original_returned&&phase.raw_return_bits==kBits&&g_calls==1,"original count/RAX changed");
  ArmyAssaultConsumerParent12004 parent;Require(!CopyActiveArmyAssaultConsumerParent12004(parent),"consumer TLS escaped original");
  auto observed=ReadActualAssaultConsumerObservations12004(42);Require(observed&&observed->events.size()==1,"owned Army membership missing");
  const auto &e=observed->events.front();Require(!e.current_session_guard&&!observed->observer_installed,"fixture gained native install credit");
  Require(e.parent.phase_entry_event.sequence==phase.scope.entry_event.sequence&&e.parent.entry_event.clock_identity==phase.scope.entry_event.clock_identity,"phase clock mismatch");
  Require(e.parent.date_raw==std::uint64_t{0x1234567800000011ULL}&&e.parent.absolute_day_raw==std::uint32_t{17},"full parent date truncated");
  Require(e.entry_table.groups.size()==2&&e.entry_table.groups[0].physical_slot==1&&e.entry_table.groups[1].physical_slot==3,"occupied physical order changed");
  Require(e.entry_table.groups[0].armies.ordered_full_ids[1]==UINT32_MAX&&e.entry_table.groups[0].arrgs.ordered_full_ids[0]==kArRg&&e.entry_table.groups[0].arrgs.ordered_full_ids[1]==kArRg,"raw FullID/repeat lost");
  Require(e.entry_regiments.size()==1&&e.entry_regiments[0].data_records.size()==2,"target identity union wrong");
  auto &a=e.entry_regiments[0].data_records;Require(a[0].physical->object_identity==a[1].physical->object_identity&&a[0].data_ordinal==0&&a[0].physical->own_ordinal==6,"DATA/physical alias or ordinal conflated");
  Require(a[0].physical->current==50&&e.returned_regiments[0].data_records[0].physical->current==35&&e.entry_regiments[0].current==100&&e.returned_regiments[0].current==70,"entry overwritten by return/query");
  Require(e.entry_pending_queue.count==2&&e.returned_pending_queue.count==3&&e.returned_pending_queue.ordered_full_ids[2]==UINT32_MAX,"ordered pending append not copied");
  Require(e.entry_table.groups[0].native_current_expected_loss==7&&e.entry_table.groups[1].native_current_expected_loss==-1&&e.entry_table.groups[0].natural_budget_observed,"captured native scalar lost");
  Require(e.entry_dependencies_complete&&e.returned_dependencies_complete&&!e.conditional_stage_binding_ready&&!e.entry_table.groups[0].besieging_dependencies_complete,"missing B/priorwrites promoted to complete stage");
  Require(ReadActualAssaultConsumerObservations12004(UINT32_MAX)->events.size()==1&&ReadActualAssaultConsumerObservations12004(7)->events.empty(),"query manufactured historical membership");
  std::string json;xar::game::AppendArmyActualAssaultConsumerObservations12004(json,*observed);
  Require(json.find("\"actual\":false")!=std::string::npos&&json.find("\"native_current_expected_loss\":-1")!=std::string::npos&&json.find("\"conditional_stage_binding_ready\":false")!=std::string::npos,"serialized facts/unknowns changed");
  focus::VerifyActualAssaultBudgetFocus12004(e.parent.entry_event);
  focus::RunExcludedActualAssaultBudgetFocus12004(g_siege.data());

  Reset();Require(InitializeActualAssaultConsumerJournalFixture12004(binding,&OwnedConsumer),"partial fixture initialization failed");
  focus::PrepareActualAssaultBudgetFocus12004();
  g_deny_after_current=true;RunPhase();auto partial=ReadActualAssaultConsumerObservations12004(42);
  Require(partial->events.size()==1&&!partial->events[0].returned_regiments[0].data_records[0].physical->current&&!partial->events[0].returned_dependencies_complete,"failed raw post read invented value");

  Reset();Require(InitializeActualAssaultConsumerJournalFixture12004(binding,&OwnedConsumer),"bounded fixture initialization failed");
  focus::PrepareActualAssaultBudgetFocus12004();Store(g_manager.data(),0x184,std::int32_t{512});RunPhase();
  auto bounded=ReadActualAssaultConsumerObservations12004(42);
  Require(bounded->events.size()==1&&bounded->events[0].entry_table.physical_controls.size()==512&&
    !bounded->events[0].entry_table.controls_complete&&!bounded->events[0].entry_dependencies_complete,"bounded copy gained completeness");

  Reset();g_release_scene=true;PrepareArmySiegeChildNaturalFocus12004(g_manager.data());
  //39 owns this separate synthetic table and payload. Register exactly those
  // two owned ranges; no arbitrary/freed pointer is accepted by our reader.
  std::uintptr_t child_table=0;std::memcpy(&child_table,g_manager.data()+0x178,8);
  g_ranges.push_back({child_table,0x80});std::uintptr_t child_ids=0;
  std::memcpy(&child_ids,reinterpret_cast<const void*>(child_table+0x10),8);g_ranges.push_back({child_ids,12});
  Store(g_manager.data(),0x184,std::int32_t{0});Store(g_manager.data(),0x188,std::uint8_t{0});
  Require(InitializeActualAssaultConsumerJournalFixture12004(binding,&OwnedConsumer),"release connected initialization failed");
  RunPhase();auto release=ReadActualAssaultConsumerObservations12004(42);
  Require(release&&release->events.size()==1&&!release->events[0].entry_dependencies_complete,"partial null/count release inputs promoted");
  Require(release->events[0].entry_table.groups[0].armies.ordered_full_ids.size()==3&&release->events[0].returned_table.occupied_count==0,"owned entry after child release missing");
  VerifyArmySiegeChildNaturalFocus12004();
}
