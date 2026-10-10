#include "xar_bridge/actual_army_compiled_effect_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <cstdio>
#include <cstring>

using namespace xar::ck3_12004;
namespace {
std::array<std::byte,0x40> scope{}, receiver{};
std::array<std::byte,24> named{};
int original_calls = 0, reads = 0;
bool arguments_equal = true, fail_seed = false, fail_identity = false;
std::uintptr_t image_base = 0;
constexpr std::uint64_t kReturnBits = 0xF123456789ABCDEFULL;
template <typename T, std::size_t N>
void Put(std::array<std::byte,N> &object,std::size_t offset,T value) {
  std::memcpy(object.data()+offset,&value,sizeof(value));
}
template <std::size_t N>
bool In(const std::array<std::byte,N> &object,std::uintptr_t address,std::size_t size) {
  const auto start=reinterpret_cast<std::uintptr_t>(object.data());
  return address>=start && size<=N && address-start<=N-size;
}
bool Reader(void *,const void *address,void *out,std::size_t size) noexcept {
  ++reads;
  if (fail_seed && address==scope.data()+0x10) return false;
  if (fail_identity && address==scope.data()) return false;
  const auto raw=reinterpret_cast<std::uintptr_t>(address);
  if(raw==image_base+0x5D1DADC && size==1) {
    *static_cast<std::uint8_t *>(out)=0xA5; return true;
  }
  if(!(In(scope,raw,size)||In(receiver,raw,size)||In(named,raw,size))) return false;
  std::memcpy(out,address,size); return true;
}
std::uint64_t __fastcall Original(const void *r,const void *s) {
  ++original_calls;
  arguments_equal=arguments_equal && r==receiver.data() && s==scope.data();
  Put(scope,0x10,std::uint32_t{29});
  return kReturnBits;
}
// A tiny owned Win64 caller invokes the actual hook. Its return address is a
// literal recognized RVA relative to the owned reservation, not an injected
// event. There is no CK3 module, native effect body or game process here.
ActualArmyCompiledEffectOriginalV1 MakeCaller(void *reservation,std::uintptr_t return_rva) {
  auto *code=static_cast<std::uint8_t *>(reservation)+return_rva-16;
  const auto page=reinterpret_cast<std::uintptr_t>(code)&~std::uintptr_t{0xFFF};
  if(!VirtualAlloc(reinterpret_cast<void *>(page),0x1000,MEM_COMMIT,PAGE_READWRITE)) return nullptr;
  constexpr std::array<std::uint8_t,21> bytes{
      0x48,0x83,0xEC,0x28,0x48,0xB8,0,0,0,0,0,0,0,0,
      0xFF,0xD0,0x48,0x83,0xC4,0x28,0xC3};
  std::memcpy(code,bytes.data(),bytes.size());
  const auto hook=reinterpret_cast<std::uintptr_t>(&XarActualArmyCompiledEffectHook12004V1);
  std::memcpy(code+6,&hook,sizeof(hook));
  DWORD old=0;
  if(!VirtualProtect(reinterpret_cast<void *>(page),0x1000,PAGE_EXECUTE_READ,&old) ||
     !FlushInstructionCache(GetCurrentProcess(),code,bytes.size())) return nullptr;
  return reinterpret_cast<ActualArmyCompiledEffectOriginalV1>(code);
}
struct PatchMemory {
  std::array<std::uint8_t,18> target{0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,
      0x57,0x48,0x81,0xEC,0x30,0x04,0x00,0x00};
  std::array<std::uint8_t,32> trampoline{};
  bool fail_patch_flush=false;
  int free_count=0;
};
void *Alloc(void *context,std::size_t size,DWORD,DWORD) noexcept {
  auto &memory=*static_cast<PatchMemory *>(context);
  return size==memory.trampoline.size()?memory.trampoline.data():nullptr;
}
bool Free(void *context,void *,std::size_t,DWORD) noexcept {
  ++static_cast<PatchMemory *>(context)->free_count; return true;
}
bool Protect(void *,void *,std::size_t,DWORD,DWORD &old) noexcept {
  old=PAGE_EXECUTE_READ; return true;
}
bool Flush(void *context,const void *address,std::size_t) noexcept {
  auto &memory=*static_cast<PatchMemory *>(context);
  if(memory.fail_patch_flush && address==memory.target.data()) {
    memory.fail_patch_flush=false; return false;
  }
  return true;
}
ActualArmyCompiledEffectInstallEnvironmentV1 Environment(PatchMemory &memory) {
  ActualArmyCompiledEffectInstallEnvironmentV1 out;
  out.primary_thread_suspended_proven=true;
  out.bindings=BindActualArmyCompiledEffectImage12004(image_base,kExecutableSha256);
  out.bindings.read_memory=&Reader;
  out.callback_target_override=reinterpret_cast<std::uintptr_t>(memory.target.data());
  out.memory_context=&memory; out.virtual_alloc_override=&Alloc; out.virtual_free_override=&Free;
  out.virtual_protect_override=&Protect; out.flush_instruction_cache_override=&Flush;
  return out;
}
}
int main() {
  if(BindActualArmyCompiledEffectImage12004(1,"wrong-build").enabled) return 1;
  auto *reservation=VirtualAlloc(nullptr,0x2640000,MEM_RESERVE,PAGE_NOACCESS);
  if(!reservation) return 2;
  image_base=reinterpret_cast<std::uintptr_t>(reservation);
  const auto positive=MakeCaller(reservation,0x2639CA4);
  const auto flag30=MakeCaller(reservation,0x24DD7B6);
  if(!positive || !flag30) return 3;
  Put(scope,0,std::uint16_t{27}); Put(scope,2,std::uint16_t{0});
  Put(scope,8,std::uint64_t{0x81000021}); Put(scope,0x10,std::uint32_t{17});
  Put(scope,0x18,reinterpret_cast<std::uintptr_t>(named.data()));
  Put(scope,0x20,std::int32_t{1}); Put(scope,0x24,std::int32_t{1});
  Put(named,0,std::uint32_t{7}); Put(named,8,std::uint16_t{4});
  Put(named,16,std::uint64_t{0x80000123});
  Put(receiver,0,std::uint64_t{0x1122334455667788}); Put(receiver,0x2C,std::uint32_t{0x76543210});
  auto bindings=BindActualArmyCompiledEffectImage12004(image_base,kExecutableSha256);
  bindings.read_memory=&Reader;
  if(!InitializeActualArmyCompiledEffectFixture12004(bindings,&Original)) return 4;
  if(positive(receiver.data(),scope.data())!=kReturnBits) return 5;
  Put(scope,0x10,std::uint32_t{0x80000009});
  if(flag30(receiver.data(),scope.data())!=kReturnBits) return 6;
  const auto id=static_cast<std::int32_t>(0x81000021U);
  auto journal=ReadActualArmyCompiledEffectObservations12004(id);
  if(original_calls!=2 || !arguments_equal || !journal || journal->events.size()!=2) return 7;
  const auto &first=journal->events[0]; const auto &second=journal->events[1];
  if(first.caller_return_rva!=0x2639CA4 || second.caller_return_rva!=0x24DD7B6 ||
      first.callsite_rva!=0x2639C9F || second.callsite_rva!=0x24DD7B1 ||
      first.receiver_owner_offset!=0x40 || second.receiver_owner_offset!=0x230) return 8;
  if(first.before.context_seed_10_raw_u32!=17 || first.after.context_seed_10_raw_u32!=29 ||
      second.before.context_seed_10_raw_u32!=0x80000009U ||
      second.negative_seed_receiver_key_2c_raw_u32!=0x76543210U || first.negative_seed_receiver_key_2c_raw_u32) return 9;
  for(const auto &row:journal->events)
    if(!row.original_returned || !row.same_root_after || row.original_rax_raw_u64!=kReturnBits ||
       row.thread_id!=GetCurrentThreadId() || row.receiver_vptr_raw_u64!=0x1122334455667788ULL ||
       row.effect_flag_raw_u8!=0xA5 || row.before.copied_row_count!=1 || row.capture_failure_flags) return 10;
  if(first.entry_sequence!=1 || second.entry_sequence!=2 || journal->observer_installed || journal->current_session_guard) return 11;
  const auto reads_before_query=reads; const auto calls_before_query=original_calls;
  std::string family;
  xar::game::AppendArmyActualCompiledEffectObservationsV1(family,*ReadActualArmyCompiledEffectObservations12004(id));
  if(reads!=reads_before_query || original_calls!=calls_before_query ||
      ReadActualArmyCompiledEffectObservations12004(static_cast<std::int32_t>(0x82000021U))->events.size()!=0) return 12;
  if(family.find("\"complete_effects_observed\":false")==std::string::npos ||
     family.find("\"builder_called\":null")==std::string::npos ||
     family.find("\"derived_seed_raw_u32\":null")==std::string::npos ||
     family.find("\"frame_at_invocation\":null")==std::string::npos) return 13;
  // Actual emitted family for the separate strict Service field consumer.
  std::puts(family.c_str());
  fail_seed=true;
  if(positive(receiver.data(),scope.data())!=kReturnBits) return 14;
  fail_seed=false;
  journal=ReadActualArmyCompiledEffectObservations12004(id);
  if(original_calls!=3 || !journal || journal->events.size()!=3 || journal->events.back().capture_failure_flags!=5) return 15;
  fail_identity=true;
  if(flag30(receiver.data(),scope.data())!=kReturnBits) return 16;
  fail_identity=false;
  journal=ReadActualArmyCompiledEffectObservations12004(id);
  if(original_calls!=4 || journal->events.size()!=3 || journal->unattributed_capture_failures!=1) return 17;
  const auto reads_before_other=reads;
  if(InvokeActualArmyCompiledEffectFixture12004(0x123,receiver.data(),scope.data())!=kReturnBits ||
     original_calls!=5 || reads!=reads_before_other) return 18;
  for(int i=0;i<257;++i) if(positive(receiver.data(),scope.data())!=kReturnBits) return 19;
  journal=ReadActualArmyCompiledEffectObservations12004(id);
  if(journal->events.size()!=256 || journal->latest_sequence!=260 || journal->overwritten_events!=4 ||
      journal->oldest_available_sequence!=5 || original_calls!=262) return 20;
  PatchMemory memory; const auto pristine=memory.target;
  ActualArmyCompiledEffectDetourStateV1 state; auto environment=Environment(memory);
  environment.primary_thread_suspended_proven=false;
  if(InstallActualArmyCompiledEffectObserver12004(state,environment,kExecutableSha256) || memory.target!=pristine) return 21;
  environment.primary_thread_suspended_proven=true; memory.fail_patch_flush=true;
  if(InstallActualArmyCompiledEffectObserver12004(state,environment,kExecutableSha256) || memory.target!=pristine ||
      state.installed!=0 || state.trampoline || memory.free_count!=1) return 22;
  if(!InstallActualArmyCompiledEffectObserver12004(state,environment,kExecutableSha256) ||
      state.installed!=1 || memory.target[0]!=0xFF || memory.target[1]!=0x25) return 23;
  for(std::size_t i=14;i<18;++i) if(memory.target[i]!=0x90) return 24;
  if(std::memcmp(memory.trampoline.data(),pristine.data(),18)!=0 ||
      memory.trampoline[18]!=0xFF || memory.trampoline[19]!=0x25) return 25;
  std::uintptr_t resume=0;
  std::memcpy(&resume,memory.trampoline.data()+24,sizeof(resume));
  if(resume!=reinterpret_cast<std::uintptr_t>(memory.target.data())+18 || memory.free_count!=1) return 26;
  journal=ReadActualArmyCompiledEffectObservations12004(id);
  if(!journal || !journal->observer_installed || !journal->current_session_guard || !journal->events.empty()) return 27;
  // The installed synthetic target/trampoline and state remain alive until
  // process exit. No live uninstall or unproven unload is attempted.
  std::puts("PASS compiled-effect natural hook: two real return-PC routes, exact original-once RAX, partial owned journal, query serialization, guarded startup anchor/rollback; no Game or historical effects credit");
  return 0;
}
