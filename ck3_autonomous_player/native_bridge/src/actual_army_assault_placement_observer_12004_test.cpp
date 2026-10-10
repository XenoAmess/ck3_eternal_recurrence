#include "xar_bridge/actual_army_assault_placement_observer_12004.hpp"
#include <array>
#include <cstring>
#include <stdexcept>
#include <vector>

bool ReadArmyPreparationNaturalFocus12004(void *,const void *,void *,std::size_t) noexcept;
namespace {
using namespace xar::ck3_12004;
constexpr std::uintptr_t kBase=0x10000000;
constexpr std::uint64_t kReturned=0xF123456789ABCDEFULL;
constexpr std::uint32_t kKey=0x72000003U, kHash=0x12345678U;
struct PlacementFixture {
  std::array<std::byte,0x28> table{};
  std::array<std::byte,7*0x40> before{};
  std::array<std::byte,12*0x40> after{};
  std::array<std::byte,0x20> siege{};
  std::array<std::byte,16> output{};
  std::uint32_t key=kKey;
  std::uintptr_t manager=0,state=0,army=0;
  std::size_t calls=0;
  bool all_arguments_exact=false;
};
PlacementFixture g;
void Require(bool value,const char *message){if(!value)throw std::runtime_error(message);}
template<class T,std::size_t N> void Put(std::array<std::byte,N> &bytes,std::size_t offset,T value){std::memcpy(bytes.data()+offset,&value,sizeof value);}
template<std::size_t N> bool Region(std::uintptr_t address,void *out,std::size_t size,const std::array<std::byte,N> &bytes,std::uintptr_t identity=0) noexcept {
  const auto start=identity ? identity : reinterpret_cast<std::uintptr_t>(bytes.data());
  if(address<start || address-start>N || size>N-(address-start))return false;
  std::memcpy(out,bytes.data()+(address-start),size);return true;
}
bool ReadOwned(void *context,const void *address,void *out,std::size_t size) noexcept {
  const auto raw=reinterpret_cast<std::uintptr_t>(address);
  std::uintptr_t pointer=0; bool slot=false;
  if(raw==kBase+0x5C68C50){pointer=g.state;slot=true;}
  if(raw==g.state+0xA0){pointer=g.manager-0x2A540;slot=true;}
  if(raw==kBase+0x5D1EC88){pointer=0;slot=true;}
  if(raw==kBase+0x5D1EC60){pointer=reinterpret_cast<std::uintptr_t>(g.siege.data());slot=true;}
  if(slot && size==sizeof pointer){std::memcpy(out,&pointer,size);return true;}
  if(Region(raw,out,size,g.table,g.manager+0x170) || Region(raw,out,size,g.before) || Region(raw,out,size,g.after) ||
      Region(raw,out,size,g.siege) || Region(raw,out,size,g.output))return true;
  if(raw==reinterpret_cast<std::uintptr_t>(&g.key) && size==4){std::memcpy(out,&g.key,4);return true;}
  return ReadArmyPreparationNaturalFocus12004(context,address,out,size);
}
template<std::size_t N> void Record(std::array<std::byte,N> &bytes,std::size_t slot,std::uint32_t hash,std::uint32_t key,std::uint8_t control) {
  const auto offset=slot*0x40;Put(bytes,offset,hash);Put(bytes,offset+4,control);Put(bytes,offset+8,key);
  Put(bytes,offset+0x20,kBase+0x54E0570);Put(bytes,offset+0x38,kBase+0x54DEB68);
}
std::uint64_t __fastcall Original(const void *table,void *output,std::uint32_t hash,const std::uint32_t *key) {
  ++g.calls;g.all_arguments_exact=reinterpret_cast<std::uintptr_t>(table)==g.manager+0x170 && output==g.output.data() && hash==kHash && key==&g.key;
  // Fixed owned postimage, not insertion/allocator/native body replay.
  Put(g.table,8,reinterpret_cast<std::uintptr_t>(g.after.data()));Put(g.table,0x10,std::int32_t{3});
  Put(g.table,0x14,std::int32_t{7});Put(g.table,0x18,std::uint8_t{3});
  Put(g.output,0,reinterpret_cast<std::uintptr_t>(g.after.data()+2*0x40));Put(g.output,8,std::uint8_t{1});
  return kReturned;
}
ActualArmyAssaultPlacementObservation12004 HeldEvent() {
  const auto observations=ReadActualArmyAssaultPlacementObservations12004(0xA1000001U);
  Require(observations && observations->events.size()==1,"placement full generation journal");return observations->events.front();
}
void InstalledOwnedCode() {
  auto *code=static_cast<std::uint8_t *>(VirtualAlloc(nullptr,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  Require(code!=nullptr,"placement owned code allocate");
  constexpr std::array<std::uint8_t,19> prefix{0x48,0x89,0x5C,0x24,0x10,0x55,0x56,0x57,0x41,0x56,0x41,0x57,0x48,0x81,0xEC,0x80,0,0,0};
  std::memcpy(code,prefix.data(),prefix.size());code[19]=0x48;code[20]=0xB8;std::memcpy(code+21,&kReturned,8);
  constexpr std::array<std::uint8_t,15> tail{0x48,0x81,0xC4,0x80,0,0,0,0x41,0x5F,0x41,0x5E,0x5F,0x5E,0x5D,0xC3};std::memcpy(code+29,tail.data(),tail.size());
  auto *caller=code+128;constexpr std::array<std::uint8_t,6> head{0x48,0x83,0xEC,0x28,0x48,0xB8};std::memcpy(caller,head.data(),head.size());
  const auto target=reinterpret_cast<std::uintptr_t>(code);std::memcpy(caller+6,&target,8);caller[14]=0xFF;caller[15]=0xD0;
  constexpr std::array<std::uint8_t,5> ret{0x48,0x83,0xC4,0x28,0xC3};std::memcpy(caller+16,ret.data(),ret.size());
  DWORD old=0;Require(VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old)!=FALSE,"placement owned code protect");
  Require(FlushInstructionCache(GetCurrentProcess(),code,4096)!=FALSE,"placement owned code flush");
  ActualArmyAssaultPlacementInstallEnvironment12004 environment{};environment.primary_thread_suspended_proven=true;
  environment.bindings=BindActualArmyAssaultPlacementImage12004(reinterpret_cast<std::uintptr_t>(caller+16)-kActualArmyAssaultPlacementDirectReturnRva12004,kDailyAssaultPreparationExecutableSha256);
  environment.bindings.read_memory=&ReadOwned;environment.callback_target_override=target;
  static ActualArmyAssaultPlacementDetourState12004 state;
  Require(InstallActualArmyAssaultPlacementObserver12004(state,environment,kDailyAssaultPreparationExecutableSha256),"placement exact19 detour install");
  using Caller=ActualArmyAssaultPlacementOriginal12004;
  Require(reinterpret_cast<Caller>(caller)(reinterpret_cast<const void *>(g.manager+0x170),g.output.data(),kHash,&g.key)==kReturned,"placement installed trampoline RAX");
  const auto journal=ReadActualArmyAssaultPlacementObservations12004(0xA1000001U);
  Require(journal && journal->observer_installed && journal->current_session_guard && journal->events.empty() && journal->unattributed_capture_failures==1,"placement absent natural parent stays unattributed");
  Require(!BindActualArmyAssaultPlacementImage12004(kBase,"wrong-build").enabled,"placement binder exact build");
  // Process-lifetime installed backing remains held, matching production.
}
} // namespace

void InvokeArmyPlacementNaturalFocus12004(const void *manager,const void *selected_army) {
  g={};g.manager=reinterpret_cast<std::uintptr_t>(manager);g.army=reinterpret_cast<std::uintptr_t>(selected_army);
  const auto parent=CopyActiveArmyNaturalPhaseScope12004();g.state=parent.game_state_identity;
  Put(g.siege,8,kKey);Put(g.table,8,reinterpret_cast<std::uintptr_t>(g.before.data()));
  Put(g.table,0x10,std::int32_t{2});Put(g.table,0x14,std::int32_t{3});Put(g.table,0x18,std::uint8_t{2});Put(g.table,0x1C,std::uint32_t{0x3F800000U});
  Record(g.before,0,0x101U,0x72000001U,1);Record(g.before,3,0x102U,0x72000002U,1);Put(g.before,6*0x40+4,std::uint8_t{0xFF});
  Record(g.after,0,0x102U,0x72000002U,1);Record(g.after,2,kHash,kKey,1);Record(g.after,4,0x101U,0x72000001U,1);Put(g.after,11*0x40+4,std::uint8_t{0xFF});
  // A positive count beyond this capture's reference budget is retained raw.
  Put(g.after,2*0x40+0x1C,std::int32_t{1025});
  auto bindings=BindActualArmyAssaultPlacementImage12004(kBase,kDailyAssaultPreparationExecutableSha256);bindings.read_memory=&ReadOwned;
  Require(InitializeActualArmyAssaultPlacementFixture12004(bindings,&Original),"placement connected fixture init");
  const auto returned=InvokeActualArmyAssaultPlacementFixture12004(kActualArmyAssaultPlacementDirectReturnRva12004,reinterpret_cast<const void *>(g.manager+0x170),g.output.data(),kHash,&g.key);
  Require(returned==kReturned && g.calls==1 && g.all_arguments_exact,"placement original four inputs once and opaque RAX");
}
void RunArmyPlacementNaturalFocus12004() {
  const auto event=HeldEvent();
  Require(event.parent_bound && !event.recursive && event.preparation.native_occurrence_index==std::int32_t{2} && event.preparation.local_start_index==std::int32_t{2},"placement natural bound occurrence");
  Require(event.preparation.parent.entry_event.clock_identity==event.entry_event.clock_identity && event.preparation.entry_event.sequence<event.entry_event.sequence && event.entry_event.sequence<event.returned_event.sequence,"placement one shared phase clock");
  Require(event.before.capture_complete && event.before.native_empty_storage_matches==false && event.before.physical_table.groups.size()==2,"placement before complete physical table");
  Require(event.before.physical_table.groups[0].physical_slot_i64==0 && event.before.physical_table.groups[1].physical_slot_i64==3,"placement before physical slot order");
  Require(event.after.entries_identity!=event.before.entries_identity && event.after.physical_table.groups.size()==3 && event.after.physical_table.groups[0].physical_slot_i64==0 && event.after.physical_table.groups[1].physical_slot_i64==2 && event.after.physical_table.groups[2].physical_slot_i64==4,"placement actual after physical order");
  Require(event.after.budget_exhausted && !event.after.capture_complete && !event.after.physical_table.ready && !event.after.physical_table.raw_groups_ready && event.after.denied_vector_counts.size()==1 && event.after.denied_vector_counts[0].actual_count_raw_i32==1025,"placement oversized reference remains partial raw count");
  Require(event.returned_entry_identity==reinterpret_cast<std::uintptr_t>(g.after.data()+2*0x40) && event.returned_inserted_raw_u8==std::uint8_t{1} && event.returned_physical_slot_i64==std::int64_t{2},"placement actual outputpair");
  Require(event.original_called && event.original_returned && event.original_rax_raw_u64==kReturned && event.after.stage=="actual_2AA2010_after_original_before_preparation_append","placement before append stage");
  Require(ReadActualArmyAssaultPlacementObservations12004(0xA2000001U)->events.empty(),"placement exact generation query");
  ActualArmyDailyAssaultPreparationObservation12004 missing{};
  Require(!ProjectActualArmyAssaultPlacementObservation12004(event,missing).mapping_ready,"placement missing natural preparation projection unknown");
  InstalledOwnedCode();
}
