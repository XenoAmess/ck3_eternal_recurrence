#include "xar_bridge/actual_army_pre_date_prefix_observer_12004.hpp"
#include "xar_bridge/actual_army_pre_date_prefix_observations12004_serializer.hpp"
#include <cstring>
#include <stdexcept>
#include <string>
namespace {
using namespace xar::ck3_12004;
std::array<std::uint8_t,0x200> primary{};
std::array<std::uint8_t,0xD0> state{};
std::array<std::uint32_t,3> pre_roster{0x01000001,0x01000001,0x02000002};
std::array<std::uint32_t,3> post_roster{0x03000003,0x03000003,0x04000004};
std::array<std::uint32_t,2> source_ids{0x05000005,0x05000005};
std::array<std::uint32_t,4> destination{};
std::uint64_t date=0x1234567800000420ULL;
std::size_t native_calls=0;
bool fail_d4=false,mutate=true,wrong_return=false;
constexpr std::uint64_t incoming_bits=0xFEDCBA9876543210ULL;
void Check(bool ok,const char *reason){if(!ok)throw std::runtime_error(reason);}
template<class T> void Put(std::size_t offset,T value){std::memcpy(primary.data()+offset,&value,sizeof value);}
bool PrefixRead(void *,const void *address,void *out,std::size_t size) noexcept {
  if(fail_d4 && address==primary.data()+0xD4)return false;
  std::memcpy(out,address,size);return true;
}
bool PhaseRead(void *,std::uintptr_t address,void *out,std::size_t size) noexcept {
  std::memcpy(out,reinterpret_cast<const void *>(address),size);return address!=0;
}
std::uint64_t __fastcall NativePrefix(const void *manager,const void *passed,std::uint64_t rax) {
  ++native_calls;
  if(manager!=primary.data() || passed!=&date || rax!=incoming_bits)throw std::runtime_error("prefix natural argument or RAX forwarding changed");
  if(mutate){Put(0x50,reinterpret_cast<std::uintptr_t>(post_roster.data()));Put<std::int32_t>(0x5C,3);destination[0]=source_ids[0];Put<std::int32_t>(0x164,1);}
  return rax;
}
std::uintptr_t __fastcall Parent(void *secondary) {
  Check(secondary==primary.data()+8,"phase secondary identity changed");
  return InvokeActualArmyPreDatePrefixFixture12004(wrong_return?0x2A99E77:0x2A99E76,primary.data(),&date,incoming_bits);
}
void Setup(std::int32_t d4) {
  primary.fill(0);destination.fill(0);native_calls=0;fail_d4=false;mutate=true;wrong_return=false;
  Put(0x50,reinterpret_cast<std::uintptr_t>(pre_roster.data()));Put<std::int32_t>(0x58,3);Put<std::int32_t>(0x5C,3);
  Put(0xC8,reinterpret_cast<std::uintptr_t>(source_ids.data()));Put<std::int32_t>(0xD0,2);Put(0xD4,d4);
  Put(0x158,reinterpret_cast<std::uintptr_t>(destination.data()));Put<std::int32_t>(0x160,4);Put<std::int32_t>(0x164,0);
  const std::uint64_t game_date=date-24;std::memcpy(state.data()+8,&game_date,sizeof game_date);
  auto bindings=BindActualArmyPreDatePrefixImage12004(0x10000000,kActualArmyPreDatePrefixSha12004);
  bindings.read_memory=&PrefixRead;
  Check(InitializeActualArmyPreDatePrefixFixture12004(bindings,&NativePrefix),"prefix fixture initialization failed");
}
ArmyNaturalPhaseRecord12004 InvokeParent() {
  ArmyNaturalPhaseBindings12004 b{};b.read=&PhaseRead;b.game_state_identity=reinterpret_cast<std::uintptr_t>(state.data());
  return InvokeArmyNaturalPhaseScope12004(b,&Parent,primary.data()+8,ArmyNaturalPhaseKind12004::pre_date,0x77);
}
ActualArmyPreDatePrefixObservation12004 OnlyRecord() {
  auto journal=ReadActualArmyPreDatePrefixObservations12004(reinterpret_cast<std::uintptr_t>(primary.data()));
  Check(journal && journal->events.size()==1,"expected exactly one copied prefix record");
  const auto wire=SerializeActualArmyPreDatePrefixObservations12004(*journal);
  Check(wire.find("\"positive_physical_transition_complete\":false")!=std::string::npos,"wire promoted partial positive footprint");
  return journal->events.front();
}
}
void RunArmyPrefixNaturalFocus12004() {
  Setup(2);const auto parent=InvokeParent();const auto e=OnlyRecord();
  Check(native_calls==1 && parent.original_returned && parent.raw_return_bits==incoming_bits,"natural original not exactly once / opaque return lost");
  Check(e.parent_bound && e.original_returned && e.original_rax_raw_u64==incoming_bits,"actual prefix parent/return facts unavailable");
  Check(e.before.source_c8.count==2 && e.before.destination_158.count==0 && e.after.destination_158.count==1,"descriptor before/after copied at wrong boundary");
  Check(e.before.source_c8.ordered_full_ids==std::vector<std::uint32_t>(source_ids.begin(),source_ids.end()),"source duplicate keys lost");
  Check(e.before.supplied_date_raw_u64==date && parent.scope.prefix_date_raw==date,"full supplied prospective CDate lost");
  Check(e.original_roster_capture_complete && e.captured_original_roster.capture_rva==0x2A99E76 &&
    e.captured_original_roster.ordered_full_ids==std::vector<std::uint32_t>(post_roster.begin(),post_roster.end()),"roster reconstructed from parent entry instead of actual prefix return");
  Check(e.parent.original_army_roster.ordered_full_ids==std::vector<std::uint32_t>(pre_roster.begin(),pre_roster.end()),"entry and returned roster frames collapsed");
  Check(e.before.conditional_no_work_arm==false && !e.before.positive_physical_transition_complete,"positive original return incorrectly grants physical projection");
  Setup(2);InvokeActualArmyPreDatePrefixFixture12004(0x2A99E76,primary.data(),&date,incoming_bits);const auto absent=OnlyRecord();
  Check(native_calls==1 && !absent.parent_bound && absent.original_returned && !absent.original_roster_capture_complete,"missing parent suppressed native or invented phase frame");
  Setup(2);wrong_return=true;const auto wrong=InvokeParent();const auto wrong_journal=ReadActualArmyPreDatePrefixObservations12004(reinterpret_cast<std::uintptr_t>(primary.data()));
  Check(native_calls==1 && wrong.raw_return_bits==incoming_bits && wrong_journal && wrong_journal->events.empty() &&
    wrong.scope.original_army_roster.boundary==ArmyNaturalRosterBoundary12004::parent_entry,"wrong literal return created prefix provenance");
  Setup(2);fail_d4=true;InvokeParent();const auto failed=OnlyRecord();
  Check(native_calls==1 && failed.original_returned && !failed.before.source_c8.count && !failed.before.conditional_no_work_arm &&
    failed.before.destination_158.count==0 && failed.original_roster_capture_complete,"D4 read fault converted unknown to zero or erased independent roster capture");
  Setup(0);mutate=false;InvokeParent();const auto zero=OnlyRecord();
  Check(zero.before.conditional_no_work_arm==true && zero.original_rax_raw_u64==incoming_bits && native_calls==1,"no-work natural entry RAX not preserved");
  // New owned executable thunk qualification, not CK3 or the old header cases.
  // Exact displaced17B and exact source no-work epilogue10B preserve native ABI.
  static ActualArmyPreDatePrefixDetourState12004 installed;
  auto *target=static_cast<std::uint8_t *>(VirtualAlloc(nullptr,64,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  Check(target!=nullptr,"owned thunk target allocation failed");
  constexpr std::array<std::uint8_t,27> original{
    0x40,0x53,0x41,0x54,0x41,0x55,0x48,0x83,0xEC,0x40,0x4C,0x63,0xA1,0xD4,0,0,0,
    0x48,0x83,0xC4,0x40,0x41,0x5D,0x41,0x5C,0x5B,0xC3};
  std::memcpy(target,original.data(),original.size());DWORD old=0;
  Check(VirtualProtect(target,64,PAGE_EXECUTE_READ, &old)!=FALSE,"owned thunk target protection failed");
  ActualArmyPreDatePrefixInstallEnvironment12004 env{};env.primary_thread_suspended_proven=true;
  env.bindings=BindActualArmyPreDatePrefixImage12004(0x10000000,kActualArmyPreDatePrefixSha12004);env.bindings.read_memory=&PrefixRead;
  env.callback_target_override=reinterpret_cast<std::uintptr_t>(target);
  Check(!InstallActualArmyPreDatePrefixObserver12004(installed,env,"wrong"),"wrong-build prefix installation accepted");
  Check(InstallActualArmyPreDatePrefixObserver12004(installed,env,kActualArmyPreDatePrefixSha12004),"owned prefix installation failed");
  const auto *bytes=static_cast<const std::uint8_t *>(installed.trampoline);
  Check(std::memcmp(bytes,original.data(),17)==0 && bytes[31]==0x4C && bytes[32]==0x89 && bytes[33]==0xC0 &&
    bytes[48]==0x49 && bytes[49]==0x89 && bytes[50]==0xC0,"prefix incoming-RAX save/restore machine bytes changed");
  Check(InvokeActualArmyPreDatePrefixFixture12004(0,primary.data(),&date,incoming_bits)==incoming_bits,"executable original-call thunk failed opaque native RAX preservation");
  // Both owned backing allocations remain valid until this sole fixture exits,
  // matching production's process-lifetime trampoline custody.
}
