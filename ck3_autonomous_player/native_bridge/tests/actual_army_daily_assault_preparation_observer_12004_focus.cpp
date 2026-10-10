#include "xar_bridge/actual_army_daily_assault_preparation_observer_12004.hpp"
#include "xar_bridge/actual_army_pre_date_prefix_observer_12004.hpp"
#include <array>
#include <cstring>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

void InvokeArmyPlacementNaturalFocus12004(const void *, const void *);

namespace {
using namespace xar::ck3_12004;
constexpr std::uint64_t kReturned = 0xFEDCBA9876543210ULL;
struct Region { std::uintptr_t address; const void *bytes; std::size_t size; };
struct PreparationFixture {
  std::uintptr_t base = 0x10000000;
  std::array<std::byte, 0x200> manager{}, army{}, unit{};
  std::array<std::byte, 0x100> game_state{};
  std::array<std::byte,0x900> province{};
  std::array<std::byte,0x500> siege{};
  std::array<std::byte,0x400> war{};
  std::array<std::byte,0x200> character1{},character2{};
  std::array<std::byte,0x40> character_store{},character_table{},relationship_store{},relationship_value{};
  std::array<std::byte,16> relationship_pair{};
  std::array<std::byte,0x50> pending{};
  std::array<std::uint32_t, 3> roster{0x71000001U,0x71000002U,0x71000001U};
  std::uint64_t prefix_date = 24;
  std::map<std::uintptr_t,std::uintptr_t> slots;
  std::vector<Region> regions;
  std::size_t original_calls = 0, prefix_calls = 0;
  std::int32_t index = 2;
  bool capture_prefix = true, change_generation = false, missing_army_id = false, invoke_placement = false;
  bool positive=false, query_placement=false;
  bool (*query_placement_callback)(const void *,const void *) noexcept=nullptr;
  std::uintptr_t query_caller=0;
  std::uintptr_t caller_return = kActualArmyDailyAssaultPreparationReturnRva12004;
  ActualArmyDailyAssaultPreparationActive12004 child_seen;
  void Add(const void *address, std::size_t size) {
    regions.push_back({reinterpret_cast<std::uintptr_t>(address),address,size});
  }
  template<class T,std::size_t N> void Put(std::array<std::byte,N> &object, std::size_t offset, T value) { std::memcpy(object.data()+offset,&value,sizeof value); }
  void SetSlots() {
    slots.clear();
    slots[base+0x5C68C50]=reinterpret_cast<std::uintptr_t>(game_state.data());
    slots[base+0x5D1DE48]=0; slots[base+0x5D1DE50]=reinterpret_cast<std::uintptr_t>(army.data());
    slots[base+0x5D1E380]=0; slots[base+0x5D1E378]=reinterpret_cast<std::uintptr_t>(unit.data());
    if(positive) {
      slots[base+0x5C67568]=reinterpret_cast<std::uintptr_t>(character_store.data()); slots[base+0x5C67570]=0;
      slots[base+0x5D1DE58]=0; slots[base+0x5D1DE40]=reinterpret_cast<std::uintptr_t>(war.data());
      slots[base+0x5D1EC88]=0; slots[base+0x5D1EC60]=reinterpret_cast<std::uintptr_t>(siege.data());
    }
  }
  void Reset() {
    manager.fill(std::byte{0}); army.fill(std::byte{0}); unit.fill(std::byte{0}); game_state.fill(std::byte{0});
    roster={0x71000001U,0x71000002U,0x71000001U}; positive=false; query_placement=false; query_caller=0; query_placement_callback=nullptr;
    Put(manager,0x50,reinterpret_cast<std::uintptr_t>(roster.data())); Put(manager,0x5C,std::int32_t{3});
    Put(army,0x10,std::uint32_t{0xA1000001U}); Put(army,0x124,std::uint32_t{0x01000001U});
    Put(unit,0x10,std::uint32_t{0x01000001U}); Put(unit,0x18,std::uint32_t{1}); // closed no-admission gate
    original_calls=0; prefix_calls=0; child_seen={}; SetSlots();
    regions.clear(); Add(manager.data(),manager.size()); Add(army.data(),army.size()); Add(unit.data(),unit.size());
    Add(game_state.data(),game_state.size()); Add(roster.data(),sizeof roster); Add(&prefix_date,sizeof prefix_date);
  }
  void Positive(std::uint32_t army_id,std::uint32_t siege_id) {
    positive=true;
    province.fill(std::byte{0}); siege.fill(std::byte{0}); war.fill(std::byte{0});
    character1.fill(std::byte{0}); character2.fill(std::byte{0}); character_store.fill(std::byte{0}); character_table.fill(std::byte{0});
    relationship_store.fill(std::byte{0}); relationship_value.fill(std::byte{0}); relationship_pair.fill(std::byte{0}); pending.fill(std::byte{0});
    Put(unit,0x18,std::uint32_t{0}); Put(unit,0x20,reinterpret_cast<std::uintptr_t>(province.data()));
    Put(unit,0x178,army_id); Put(unit,0x174,std::uint32_t{0x11000001U});
    Put(province,0x10,std::uint32_t{0x15000001U}); Put(province,0x788,siege_id); Put(province,0x850,std::int32_t{1});
    Put(province,0x73C,std::uint32_t{0x12000002U}); Put(siege,8,siege_id); Put(siege,0x44C,std::uint8_t{1});
    Put(character_store,0x20,reinterpret_cast<std::uintptr_t>(character_table.data())); Put(character_store,0x2C,std::uint32_t{3});
    Put(character_table,0x18,reinterpret_cast<std::uintptr_t>(character1.data())); Put(character_table,0x28,reinterpret_cast<std::uintptr_t>(character2.data()));
    Put(character1,0x18,std::uint32_t{0x11000001U}); Put(character2,0x18,std::uint32_t{0x12000002U});
    Put(character1,0x1B0,reinterpret_cast<std::uintptr_t>(relationship_store.data()));
    Put(relationship_store,0x20,reinterpret_cast<std::uintptr_t>(relationship_pair.data())); Put(relationship_store,0x2C,std::int32_t{1});
    Put(relationship_pair,0,std::uint32_t{0x12000002U}); Put(relationship_pair,8,reinterpret_cast<std::uintptr_t>(relationship_value.data()));
    Put(relationship_value,0x20,std::uint32_t{0x13000001U}); Put(war,8,std::uint32_t{0x13000001U});
    Put(manager,0x138,reinterpret_cast<std::uintptr_t>(pending.data())); Put(pending,0x2C,std::uint8_t{0xFF});
    Add(province.data(),province.size()); Add(siege.data(),siege.size()); Add(war.data(),war.size());
    Add(character1.data(),character1.size()); Add(character2.data(),character2.size()); Add(character_store.data(),character_store.size()); Add(character_table.data(),character_table.size());
    Add(relationship_store.data(),relationship_store.size()); Add(relationship_value.data(),relationship_value.size()); Add(relationship_pair.data(),relationship_pair.size()); Add(pending.data(),pending.size());
    SetSlots();
  }
};
PreparationFixture g;
void Require(bool value, const char *message) { if(!value)throw std::runtime_error(message); }
bool ReadOwned(void *, const void *address, void *out, std::size_t size) noexcept {
  const auto raw=reinterpret_cast<std::uintptr_t>(address);
  if(g.missing_army_id && raw==reinterpret_cast<std::uintptr_t>(g.army.data())+0x10)return false;
  const auto slot=g.slots.find(raw);
  if(slot!=g.slots.end() && size==sizeof(std::uintptr_t)) { std::memcpy(out,&slot->second,size); return true; }
  for(const auto &region:g.regions) {
    if(raw>=region.address && raw-region.address<=region.size && size<=region.size-(raw-region.address)) {
      std::memcpy(out,static_cast<const std::byte *>(region.bytes)+(raw-region.address),size); return true;
    }
  }
  return false;
}
bool PhaseRead(void *, std::uintptr_t address, void *out, std::size_t size) noexcept {
  return ReadOwned(nullptr,reinterpret_cast<const void *>(address),out,size);
}
std::uint64_t __fastcall PrefixOriginal(const void *,const void *,std::uint64_t incoming) {
  ++g.prefix_calls; return incoming;
}
std::uint64_t __fastcall PreparationOriginal(const void *manager,const void *army) {
  ++g.original_calls; g.child_seen=CopyActiveActualArmyDailyAssaultPreparation12004();
  if(g.invoke_placement) {
    if(g.query_placement && g.query_placement_callback)(void)g.query_placement_callback(manager,army);
    else InvokeArmyPlacementNaturalFocus12004(manager,army);
  }
  if(g.change_generation)g.Put(g.army,0x10,std::uint32_t{0xA2000001U});
  return kReturned;
}
std::uintptr_t __fastcall ParentOriginal(void *) {
  if(g.capture_prefix)InvokeActualArmyPreDatePrefixFixture12004(0x2A99E76,g.manager.data(),&g.prefix_date,0xC0FFEEULL);
  const auto iterator=reinterpret_cast<std::uintptr_t>(g.roster.data()+g.index), end=reinterpret_cast<std::uintptr_t>(g.roster.data()+g.roster.size());
  std::uint64_t returned=0;
  if(g.query_caller) {
    using Caller=std::uint64_t(__fastcall *)(const void *,const void *,std::uintptr_t,std::uintptr_t);
    returned=reinterpret_cast<Caller>(g.query_caller)(g.manager.data(),g.army.data(),iterator,end);
  } else returned=InvokeActualArmyDailyAssaultPreparationFixture12004(g.caller_return,g.manager.data(),g.army.data(),iterator,end);
  return static_cast<std::uintptr_t>(returned);
}
void Initialize() {
  auto b=BindActualArmyDailyAssaultPreparationImage12004(g.base,kDailyAssaultPreparationExecutableSha256); b.read_memory=&ReadOwned;
  Require(InitializeActualArmyDailyAssaultPreparationFixture12004(b,&PreparationOriginal),"preparation fixture init");
  auto p=BindActualArmyPreDatePrefixImage12004(g.base,kDailyAssaultPreparationExecutableSha256); p.read_memory=&ReadOwned;
  Require(InitializeActualArmyPreDatePrefixFixture12004(p,&PrefixOriginal),"prefix fixture init");
}
ArmyNaturalPhaseRecord12004 InvokeParent() {
  ArmyNaturalPhaseBindings12004 b{}; b.read=&PhaseRead; b.game_state_identity=reinterpret_cast<std::uintptr_t>(g.game_state.data());
  return InvokeArmyNaturalPhaseScope12004(b,&ParentOriginal,g.manager.data()+8,ArmyNaturalPhaseKind12004::pre_date,0x12345);
}
ActualArmyDailyAssaultPreparationObservation12004 OnlyEvent() {
  const auto journal=ReadActualArmyDailyAssaultPreparationObservations12004(0xA1000001U);
  Require(journal && journal->events.size()==1,"exact full generation event join"); return journal->events.front();
}
void OwnedInstalledThunk() {
  // New source-specific register-capture machinery is exercised with owned code.
  // These bytes are an ABI fixture, never a replay of a game callback body.
  auto *code=static_cast<std::uint8_t *>(VirtualAlloc(nullptr,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  Require(code!=nullptr,"owned code alloc");
  constexpr std::array<std::uint8_t,16> prefix{0x40,0x56,0x57,0x48,0x83,0xEC,0x48,0x48,0x8B,0xF9,0x48,0x8B,0xF2,0x48,0x8B,0xCA};
  std::memcpy(code,prefix.data(),prefix.size());
  code[16]=0x48; code[17]=0xB8; std::memcpy(code+18,&kReturned,sizeof kReturned);
  constexpr std::array<std::uint8_t,7> tail{0x48,0x83,0xC4,0x48,0x5F,0x5E,0xC3}; std::memcpy(code+26,tail.data(),tail.size());
  auto *caller=code+128;
  constexpr std::array<std::uint8_t,16> caller_head{0x41,0x54,0x41,0x57,0x48,0x83,0xEC,0x28,0x4D,0x8B,0xF8,0x4D,0x8B,0xE1,0x48,0xB8};
  std::memcpy(caller,caller_head.data(),caller_head.size());
  const auto target=reinterpret_cast<std::uintptr_t>(code); std::memcpy(caller+16,&target,sizeof target); caller[24]=0xFF; caller[25]=0xD0;
  constexpr std::array<std::uint8_t,9> caller_tail{0x48,0x83,0xC4,0x28,0x41,0x5F,0x41,0x5C,0xC3}; std::memcpy(caller+26,caller_tail.data(),caller_tail.size());
  DWORD old=0; Require(VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old)!=FALSE,"owned code protect");
  Require(FlushInstructionCache(GetCurrentProcess(),code,4096)!=FALSE,"owned code flush");
  g.base=reinterpret_cast<std::uintptr_t>(caller+26)-kActualArmyDailyAssaultPreparationReturnRva12004; g.SetSlots();
  ActualArmyDailyAssaultPreparationInstallEnvironment12004 environment{};
  environment.primary_thread_suspended_proven=true; environment.bindings=BindActualArmyDailyAssaultPreparationImage12004(g.base,kDailyAssaultPreparationExecutableSha256);
  environment.bindings.read_memory=&ReadOwned; environment.callback_target_override=target;
  static ActualArmyDailyAssaultPreparationDetourState12004 state;
  Require(InstallActualArmyDailyAssaultPreparationObserver12004(state,environment,kDailyAssaultPreparationExecutableSha256),"owned detour install");
  using Caller=std::uint64_t(__fastcall *)(const void *,const void *,std::uintptr_t,std::uintptr_t);
  const auto iterator=reinterpret_cast<std::uintptr_t>(g.roster.data()+2), end=reinterpret_cast<std::uintptr_t>(g.roster.data()+3);
  Require(reinterpret_cast<Caller>(caller)(g.manager.data(),g.army.data(),iterator,end)==kReturned,"installed raw RAX");
  const auto event=OnlyEvent(); Require(event.active.actual_caller_iterator==iterator && event.active.actual_caller_end==end,"installed native register capture");
  Require(!event.active.parent_bound && !event.active.original_occurrence_bound,"owned install absent parent stays partial");
  // Installed state/code is process-lifetime, matching the production contract.
}
} // namespace

bool ReadArmyPreparationNaturalFocus12004(void *context,const void *address,void *out,std::size_t size) noexcept {
  return ReadOwned(context,address,out,size);
}
// Setup-only seam for the new whole-query compound. It never runs a focus,
// asserts, installs, or invents an event; the fresh parent invokes real candidate
// wrappers with owned fake originals exactly once.
bool InitializeArmyPreparationNaturalSetup12004(std::uint32_t exact_full_carmy_id,bool with_placement) noexcept {
  g.base=0x10000000; g.capture_prefix=true; g.change_generation=false;
  g.missing_army_id=false; g.invoke_placement=with_placement;
  g.caller_return=kActualArmyDailyAssaultPreparationReturnRva12004; g.index=2; g.Reset();
  g.Put(g.army,0x10,exact_full_carmy_id);
  g.roster[0]=exact_full_carmy_id; g.roster[2]=exact_full_carmy_id;
  auto b=BindActualArmyDailyAssaultPreparationImage12004(g.base,kDailyAssaultPreparationExecutableSha256); b.read_memory=&ReadOwned;
  auto p=BindActualArmyPreDatePrefixImage12004(g.base,kDailyAssaultPreparationExecutableSha256); p.read_memory=&ReadOwned;
  return InitializeActualArmyDailyAssaultPreparationFixture12004(b,&PreparationOriginal) &&
      InitializeActualArmyPreDatePrefixFixture12004(p,&PrefixOriginal);
}
xar::ck3_12004::ArmyNaturalPhaseBindings12004 ArmyPreparationNaturalSetupBindings12004() noexcept {
  xar::ck3_12004::ArmyNaturalPhaseBindings12004 b{}; b.read=&PhaseRead;
  b.game_state_identity=reinterpret_cast<std::uintptr_t>(g.game_state.data()); return b;
}
void *ArmyPreparationNaturalSetupSecondary12004() noexcept { return g.manager.data()+8; }
xar::ck3_12004::ArmyNaturalPhaseOriginal12004 ArmyPreparationNaturalSetupOriginal12004() noexcept { return &ParentOriginal; }
bool ConfigureArmyPreparationNaturalPositiveSetup12004(std::uint32_t exact_full_carmy_id,std::uint32_t siege_key) noexcept {
  if(exact_full_carmy_id==UINT32_MAX || siege_key==UINT32_MAX)return false;
  g.Positive(exact_full_carmy_id,siege_key); g.query_placement=true; return true;
}
void SetArmyPreparationNaturalSetupImage12004(std::uintptr_t image_base,std::uintptr_t native_caller) noexcept {
  g.base=image_base; g.query_caller=native_caller; g.SetSlots();
}
void SetArmyPreparationNaturalQueryPlacement12004(bool (*callback)(const void *,const void *) noexcept) noexcept { g.query_placement_callback=callback; }
xar::ck3_12004::ActualArmyDailyAssaultPreparationOriginal12004 ArmyPreparationNaturalSetupPreparationOriginal12004() noexcept { return &PreparationOriginal; }
void RunArmyAssaultPreparationNaturalFocus12004() {
  g.Reset(); Initialize(); g.invoke_placement=true;
  const auto parent=InvokeParent(); const auto event=OnlyEvent();
  Require(parent.original_returned && parent.raw_return_bits==kReturned && g.original_calls==1 && g.prefix_calls==1,"natural original once and RAX");
  Require(event.active.parent_bound && event.active.original_occurrence_bound && event.active.native_occurrence_index==2 && event.active.local_start_index==2,"duplicate exact occurrence");
  Require(g.child_seen.observed && g.child_seen.parent_bound && g.child_seen.entry_event.sequence==event.active.entry_event.sequence,"active child original scope");
  Require(event.before.copied_stage_input && event.before.copied_stage_input->boundary_binding_ready && event.before.copied_stage_input->ordered_append_inputs.size()==1 && event.before.copied_stage_input->ordered_append_inputs[0].native_occurrence_index==2,"one bound suffix input");
  Require(event.original_called && event.original_returned && event.original_rax_raw_u64==kReturned && event.returned_event.sequence>event.active.entry_event.sequence,"shared return clock and bits");
  Require(!CopyActiveActualArmyDailyAssaultPreparation12004().observed,"child scope restored");

  g.invoke_placement=false; g.capture_prefix=false; g.Reset(); Initialize(); InvokeParent();
  Require(!OnlyEvent().active.original_occurrence_bound && !OnlyEvent().before.copied_stage_input,"parent entry roster cannot replace prefix capture");
  g.capture_prefix=true; g.change_generation=true; g.Reset(); Initialize(); InvokeParent();
  const auto changed=OnlyEvent(); Require(changed.same_selected_army_generation_after==false && changed.after.selected_army_full_id_raw_u32==0xA2000001U,"generation change remains separate");
  Require(ReadActualArmyDailyAssaultPreparationObservations12004(0xA2000001U)->events.empty(),"query joins entry generation only");
  g.change_generation=false; g.caller_return=0x2A9A087; g.Reset(); Initialize(); InvokeParent();
  Require(g.original_calls==1 && ReadActualArmyDailyAssaultPreparationObservations12004(0xA1000001U)->events.empty(),"other caller forwards once without event");
  g.caller_return=kActualArmyDailyAssaultPreparationReturnRva12004; g.missing_army_id=true; g.Reset(); Initialize(); const auto failed=InvokeParent();
  Require(failed.raw_return_bits==kReturned && g.original_calls==1 && ReadActualArmyDailyAssaultPreparationObservations12004(0xA1000001U)->unattributed_capture_failures==1,"failed capture does not suppress original");
  g.missing_army_id=false; g.Reset(); Initialize();
  for(std::size_t i=0;i<kActualArmyDailyAssaultPreparationJournalCapacity12004+2;++i)InvokeParent();
  const auto wrapped=ReadActualArmyDailyAssaultPreparationObservations12004(0xA1000001U);
  Require(wrapped && wrapped->events.size()==64 && wrapped->overwritten_events==2 && wrapped->oldest_available_sequence==3,"bounded journal overwrite provenance");
  g.Reset(); OwnedInstalledThunk();
}
