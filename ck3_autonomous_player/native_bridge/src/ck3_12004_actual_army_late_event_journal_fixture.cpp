#include "xar_bridge/ck3_12004_actual_army_late_event_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstdio>
#include <cstring>

using namespace xar::ck3_12004;
namespace {
std::array<std::byte,0x168> scope{};
std::array<std::byte,0x320> definition{};
std::array<std::byte,0x680> table{};
std::array<std::byte,0x40> manager{};
std::array<std::byte,24> named{};
int original_calls=0, reads=0;
bool arguments_equal=true, fail_seed=false;
void *extra=reinterpret_cast<void *>(0x1234);
void *effect=reinterpret_cast<void *>(0x5678);
void *event=reinterpret_cast<void *>(0x9ABC);
template <typename T, std::size_t N> void Put(std::array<std::byte,N> &object,std::size_t offset,T value) {
  std::memcpy(object.data()+offset,&value,sizeof(value));
}
template <std::size_t N> bool In(const std::array<std::byte,N> &object,std::uintptr_t address,std::size_t size) {
  const auto start=reinterpret_cast<std::uintptr_t>(object.data());
  return address>=start && size<=N && address-start<=N-size;
}
bool Reader(void *,const void *address,void *out,std::size_t size) noexcept {
  ++reads;
  if(fail_seed && address==scope.data()+0x10)return false;
  const auto raw=reinterpret_cast<std::uintptr_t>(address);
  if(!(In(scope,raw,size)||In(definition,raw,size)||In(table,raw,size)||In(manager,raw,size)||In(named,raw,size)))return false;
  std::memcpy(out,address,size);return true;
}
void __fastcall Original(void *m,const void *d,void *s,void *x,void *e,void *v) {
  ++original_calls;
  arguments_equal=arguments_equal && m==manager.data() && d==definition.data() && s==scope.data() && x==extra && e==effect && v==event;
  Put(scope,0x10,std::uint32_t{29});
}
struct PatchMemory {
  std::array<std::uint8_t,14> target{0x48,0x8B,0xC4,0x48,0x89,0x58,0x18,0x48,0x89,0x48,0x08,0x55,0x56,0x57};
  std::array<std::uint8_t,28> trampoline{};
  bool fail_patch_flush=false;
  int free_count=0;
};
void *Alloc(void *context,std::size_t size,DWORD,DWORD) noexcept {
  auto &memory=*static_cast<PatchMemory *>(context);
  return size==memory.trampoline.size()?memory.trampoline.data():nullptr;
}
bool Free(void *context,void *,std::size_t,DWORD) noexcept {++static_cast<PatchMemory *>(context)->free_count;return true;}
bool Protect(void *,void *,std::size_t,DWORD,DWORD &old) noexcept {old=PAGE_EXECUTE_READ;return true;}
bool Flush(void *context,const void *address,std::size_t) noexcept {
  auto &memory=*static_cast<PatchMemory *>(context);
  if(memory.fail_patch_flush && address==memory.target.data()) {memory.fail_patch_flush=false;return false;}
  return true;
}
ActualArmyLateEventJournalInstallEnvironmentV1 Environment(PatchMemory &memory) {
  ActualArmyLateEventJournalInstallEnvironmentV1 out;
  out.primary_thread_suspended_proven=true;
  out.bindings=BindActualArmyLateEventJournalImage12004(0x100000,kExecutableSha256);
  out.callback_target_override=reinterpret_cast<std::uintptr_t>(memory.target.data());
  out.memory_context=&memory;out.virtual_alloc_override=&Alloc;out.virtual_free_override=&Free;
  out.virtual_protect_override=&Protect;out.flush_instruction_cache_override=&Flush;
  return out;
}
}
int main() {
  // One new focused fixture; local owned memory and native forwarding stubs only.
  if(BindActualArmyLateEventJournalImage12004(1,"wrong-build").enabled)return 1;
  Put(scope,0,std::uint16_t{27});Put(scope,8,std::uint64_t{0x81000021});
  Put(scope,0x10,std::uint32_t{17});Put(scope,0x18,reinterpret_cast<std::uintptr_t>(named.data()));
  Put(scope,0x20,std::int32_t{1});Put(scope,0x24,std::int32_t{1});
  Put(named,0,std::uint32_t{7});Put(named,8,std::uint16_t{4});Put(named,16,std::uint64_t{0x80000123});
  Put(manager,0x38,reinterpret_cast<std::uintptr_t>(table.data()));
  for(const auto offset:{0x168,0x640,0x170})Put(table,offset,reinterpret_cast<std::uintptr_t>(definition.data()));
  Put(definition,0x2C,std::int32_t{3});Put(definition,0x300,std::uintptr_t{0xabc});
  auto bindings=BindActualArmyLateEventJournalImage12004(0x100000,kExecutableSha256);
  bindings.read_memory=&Reader;
  if(!InitializeActualArmyLateEventJournalFixture12004(bindings,&Original))return 2;
  for(const auto rva:{0x2639CF6,0x2C448F5,0x24DD7A5})
    InvokeActualArmyLateEventJournalFixture12004(rva,manager.data(),definition.data(),scope.data(),extra,effect,event);
  const auto id=static_cast<std::int32_t>(0x81000021U);
  auto journal=ReadActualArmyLateEventObservations12004(id);
  if(original_calls!=3 || !arguments_equal || !journal || journal->events.size()!=3)return 3;
  for(const auto &row:journal->events)
    if(!row.original_returned || !row.same_root_after || row.definition.actual_loaded_table_slot_equal!=true || row.before.copied_row_count!=1)return 4;
  const int before_query_reads=reads;
  (void)ReadActualArmyLateEventObservations12004(id);
  if(reads!=before_query_reads || original_calls!=3)return 5;
  fail_seed=true;
  InvokeActualArmyLateEventJournalFixture12004(0x2639CF6,manager.data(),definition.data(),scope.data(),extra,effect,event);
  journal=ReadActualArmyLateEventObservations12004(id);
  if(original_calls!=4 || !journal || journal->events.size()!=4 || journal->events.back().capture_failure_flags!=5)return 6;
  fail_seed=false;
  const int before_other_reads=reads;
  InvokeActualArmyLateEventJournalFixture12004(0x37CD01D,manager.data(),definition.data(),scope.data(),extra,effect,event);
  if(original_calls!=5 || reads!=before_other_reads || ReadActualArmyLateEventObservations12004(id)->events.size()!=4)return 7;
  std::string json;
  xar::game::AppendArmyActualLateEventObservationsV1(json,*journal);
  if(json.find("\"complete_effects_observed\":false")==std::string::npos || json.find("\"builder_called\":null")==std::string::npos)return 8;
  PatchMemory memory;
  const auto pristine=memory.target;
  ActualArmyLateEventJournalDetourStateV1 state;
  auto environment=Environment(memory);
  environment.primary_thread_suspended_proven=false;
  if(InstallActualArmyLateEventJournal12004(state,environment,kExecutableSha256) || memory.target!=pristine)return 9;
  environment.primary_thread_suspended_proven=true;
  memory.fail_patch_flush=true;
  if(InstallActualArmyLateEventJournal12004(state,environment,kExecutableSha256) || memory.target!=pristine || state.installed!=0 || state.trampoline || memory.free_count!=1)return 10;
  if(!InstallActualArmyLateEventJournal12004(state,environment,kExecutableSha256) || state.installed!=1 || memory.target[0]!=0xFF || memory.target[1]!=0x25)return 11;
  if(!UninstallActualArmyLateEventJournal12004(state,true) || memory.target!=pristine || state.installed!=0 || state.trampoline || memory.free_count!=2)return 12;
  std::puts("PASS actual Army late dispatcher owned observer: six-argument original once, three callers, partial scope, owned query, patch rollback; no Game/SDK/live credit");
  return 0;
}
