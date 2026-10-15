#include "xar_bridge/war_payment_runtime_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <algorithm>
#include <cstring>
#include <intrin.h>
#include <limits>
#include <mutex>

namespace xar::ck3_12004 {
namespace {
constexpr std::size_t kJump = 14;
constexpr std::uint32_t kBinding=1,kAnchor=2,kAllocate=4,kProtection=8,kPublish=16,kRollback=32,kFree=64,kBusy=128,kPin=256;
std::mutex g_install_mutex;
std::atomic<WarPaymentDetourState12004 *> g_owned{nullptr};
std::array<std::atomic<std::uintptr_t>,kWarPaymentHookCount12004> g_original{};
const std::array<WarPaymentHookDescription12004,kWarPaymentHookCount12004> kDescriptions{{
  {0x24E8DB0,16,{0x40,0x53,0x48,0x83,0xEC,0x30,0x81,0xBA,0x5C,0x08,0,0,0x76,0x6F,0x72,0x50}},
  {0x28B9950,15,{0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xEC,0x20}},
  {0x285EE40,15,{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x18}},
  {0x285EED0,15,{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x18}},
  {0x285EFF0,15,{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,0x48,0x89,0x74,0x24,0x18}}
}};
bool EqualSha(std::string_view value) noexcept {
  if(value.size()!=64)return false;
  for(std::size_t i=0;i<value.size();++i) {
    const auto c=static_cast<unsigned char>(value[i]);
    const char lower=static_cast<char>(c>='A'&&c<='F'?c+('a'-'A'):c);
    const auto expected=static_cast<unsigned char>(kExecutableSha256[i]);
    const char expected_lower=static_cast<char>(expected>='A'&&expected<='F'?expected+('a'-'A'):expected);
    if(lower!=expected_lower)return false;
  }
  return true;
}
bool WriteDefault(void *,std::uintptr_t target,const void *data,std::size_t size) noexcept {
#if defined(_MSC_VER)
  __try {std::memcpy(reinterpret_cast<void *>(target),data,size);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER) {return false;}
#else
  (void)target;(void)data;(void)size;return false;
#endif
}
void *AllocateDefault(void *,std::size_t size) noexcept {return VirtualAlloc(nullptr,size,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);}
bool FreeDefault(void *,void *p) noexcept {return VirtualFree(p,0,MEM_RELEASE)!=FALSE;}
bool ProtectDefault(void *,void *p,std::size_t n,DWORD protection,DWORD &old) noexcept {return VirtualProtect(p,n,protection,&old)!=FALSE;}
bool FlushDefault(void *,const void *p,std::size_t n) noexcept {return FlushInstructionCache(GetCurrentProcess(),p,n)!=FALSE;}
bool PinDefault(void *) noexcept {
  HMODULE module=nullptr;
  return GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
      reinterpret_cast<LPCWSTR>(&WarPaymentEntryThunkAddress12004),&module)!=FALSE;
}
void Jump(std::uint8_t *bytes,std::uintptr_t target) noexcept {
  bytes[0]=0xFF;bytes[1]=0x25;std::memset(bytes+2,0,4);std::memcpy(bytes+6,&target,sizeof target);
}
std::array<std::uint8_t,16> Patch(std::size_t index,std::size_t size) noexcept {
  std::array<std::uint8_t,16> bytes{};bytes.fill(0x90);
  Jump(bytes.data(),WarPaymentEntryThunkAddress12004(static_cast<WarPaymentHook12004>(index)));
  (void)size;return bytes;
}
struct ActiveCall {
  WarPaymentDetourState12004 *state=nullptr;
  explicit ActiveCall(WarPaymentDetourState12004 *s) noexcept:state(s) {if(state)state->active_calls.fetch_add(1,std::memory_order_acq_rel);}
  ~ActiveCall(){if(state)state->active_calls.fetch_sub(1,std::memory_order_acq_rel);}
};
std::uintptr_t Rva(WarPaymentDetourState12004 *s,void *pc) noexcept {
  const auto value=reinterpret_cast<std::uintptr_t>(pc);
  return s&&value>=s->environment.module_base?value-s->environment.module_base:0;
}
// Each entry captures its native caller directly. The absolute entry jump does
// not insert another return address; the subsequent C++ seam calls do.
extern "C" __declspec(noinline) std::uintptr_t __fastcall PaymentTransition(void *a,void *p) noexcept {
  void *pc=_ReturnAddress();auto *s=g_owned.load(std::memory_order_acquire);ActiveCall active(s);
  const auto original=reinterpret_cast<WarPaymentTransitionOriginal12004>(g_original[0].load(std::memory_order_acquire));
  if(!s||!original)return 0;
  return InvokeWarPaymentTransition12004(s->environment.bindings,original,a,p,Rva(s,pc));
}
extern "C" __declspec(noinline) std::uintptr_t __fastcall PaymentGateway(void *c,std::int32_t resource,std::int64_t amount,std::int32_t component) noexcept {
  void *pc=_ReturnAddress();auto *s=g_owned.load(std::memory_order_acquire);ActiveCall active(s);
  const auto original=reinterpret_cast<WarPaymentGatewayOriginal12004>(g_original[1].load(std::memory_order_acquire));
  if(!s||!original)return 0;
  return InvokeWarPaymentGateway12004(s->environment.bindings,original,c,resource,amount,component,Rva(s,pc));
}
extern "C" __declspec(noinline) std::uintptr_t __fastcall PaymentAdd(void *w,std::int64_t amount,void *c) noexcept {
  void *pc=_ReturnAddress();auto *s=g_owned.load(std::memory_order_acquire);ActiveCall active(s);
  const auto original=reinterpret_cast<WarPaymentWriterOriginal12004>(g_original[2].load(std::memory_order_acquire));
  if(!s||!original)return 0;
  return InvokeWarPaymentWriter12004(s->environment.bindings,original,WarPaymentKind12004::personal_add,w,amount,c,Rva(s,pc));
}
extern "C" __declspec(noinline) std::uintptr_t __fastcall PaymentSub(void *w,std::int64_t amount,void *c) noexcept {
  void *pc=_ReturnAddress();auto *s=g_owned.load(std::memory_order_acquire);ActiveCall active(s);
  const auto original=reinterpret_cast<WarPaymentWriterOriginal12004>(g_original[3].load(std::memory_order_acquire));
  if(!s||!original)return 0;
  return InvokeWarPaymentWriter12004(s->environment.bindings,original,WarPaymentKind12004::personal_sub,w,amount,c,Rva(s,pc));
}
extern "C" __declspec(noinline) std::uintptr_t __fastcall PaymentLandSub(void *w,std::int64_t amount,void *c) noexcept {
  void *pc=_ReturnAddress();auto *s=g_owned.load(std::memory_order_acquire);ActiveCall active(s);
  const auto original=reinterpret_cast<WarPaymentWriterOriginal12004>(g_original[4].load(std::memory_order_acquire));
  if(!s||!original)return 0;
  return InvokeWarPaymentWriter12004(s->environment.bindings,original,WarPaymentKind12004::land_sub,w,amount,c,Rva(s,pc));
}
bool FreeAll(WarPaymentDetourState12004 &state) noexcept {
  bool ok=true;auto &e=state.environment;
  for(std::size_t i=0;i<state.hooks.size();++i) {
    auto &slot=state.hooks[i];if(!slot.trampoline)continue;
    if(slot.patch_may_be_present){ok=false;continue;}
    if(!e.free(e.memory_context,slot.trampoline)){state.failure_flags.fetch_or(kFree);ok=false;continue;}
    slot.trampoline=nullptr;g_original[i].store(0,std::memory_order_release);
  }
  return ok;
}
void AbortUnpublished(WarPaymentDetourState12004 &state) noexcept {
  // A failed allocator release still owns its exact allocation and callbacks;
  // a subsequent quiescent uninstall can retry it. No entry was patched yet.
  if(!FreeAll(state))g_owned.store(&state,std::memory_order_release);
}
bool RestoreAll(WarPaymentDetourState12004 &state,bool failed_install) noexcept {
  bool ok=true;auto &e=state.environment;
  for(std::size_t n=state.hooks.size();n>0;--n) {
    const auto index=n-1;auto &slot=state.hooks[index];if(!slot.patch_may_be_present)continue;
    if(!failed_install) {
      std::array<std::uint8_t,16> current{};const auto patch=Patch(index,slot.size);
      if(!e.bindings.read(e.bindings.read_context,slot.target,current.data(),slot.size)||
         (!std::equal(current.begin(),current.begin()+slot.size,patch.begin()) &&
          !std::equal(current.begin(),current.begin()+slot.size,slot.original.begin()))) {state.failure_flags.fetch_or(kAnchor);ok=false;continue;}
      // A previous rollback may already have restored the exact original bytes
      // while flush/protection failed. Retry that completion under quiescence;
      // reject every third-party prefix instead of discarding its patch.
    }
    DWORD old=0,ignored=0;
    if(!e.protect(e.memory_context,reinterpret_cast<void *>(slot.target),slot.size,PAGE_EXECUTE_READWRITE,old)) {state.failure_flags.fetch_or(kProtection);ok=false;continue;}
    const bool copied=e.write(e.memory_context,slot.target,slot.original.data(),slot.size);
    const bool flushed=e.flush(e.memory_context,reinterpret_cast<const void *>(slot.target),slot.size);
    const bool protected_again=e.protect(e.memory_context,reinterpret_cast<void *>(slot.target),slot.size,slot.original_protection,ignored);
    if(!copied||!flushed||!protected_again) {state.failure_flags.fetch_or(kRollback);ok=false;continue;}
    slot.patch_may_be_present=false;
  }
  return ok;
}
} // namespace
const std::array<WarPaymentHookDescription12004,kWarPaymentHookCount12004> &WarPaymentHookDescriptions12004() noexcept {return kDescriptions;}
std::uintptr_t WarPaymentEntryThunkAddress12004(WarPaymentHook12004 hook) noexcept {
  switch(hook) {
    case WarPaymentHook12004::transition:return reinterpret_cast<std::uintptr_t>(&PaymentTransition);
    case WarPaymentHook12004::gateway:return reinterpret_cast<std::uintptr_t>(&PaymentGateway);
    case WarPaymentHook12004::personal_add:return reinterpret_cast<std::uintptr_t>(&PaymentAdd);
    case WarPaymentHook12004::personal_sub:return reinterpret_cast<std::uintptr_t>(&PaymentSub);
    case WarPaymentHook12004::land_sub:return reinterpret_cast<std::uintptr_t>(&PaymentLandSub);
  }
  return 0;
}
bool InstallWarPaymentPassive12004(WarPaymentDetourState12004 &state,const WarPaymentInstallEnvironment12004 &input) noexcept {
  try {
    const std::lock_guard lock(g_install_mutex);
    if(!input.primary_thread_suspended_proven||!EqualSha(input.executable_sha256)||!input.module_base||
       !input.bindings.read||!input.bindings.next_event||!input.bindings.session||!input.bindings.journal||
       state.installed.load(std::memory_order_acquire)||g_owned.load(std::memory_order_acquire)) {state.failure_flags.fetch_or(kBinding);return false;}
    for(std::size_t i=0;i<state.hooks.size();++i) {
      if(state.hooks[i].trampoline||state.hooks[i].patch_may_be_present||
         (!input.fixture_targets&&input.target_overrides[i]) ||
         (input.fixture_targets&&!input.target_overrides[i])) {state.failure_flags.fetch_or(kBinding);return false;}
    }
    state.environment=input;auto &e=state.environment;
    e.write=e.write?e.write:&WriteDefault;e.allocate=e.allocate?e.allocate:&AllocateDefault;
    e.free=e.free?e.free:&FreeDefault;e.protect=e.protect?e.protect:&ProtectDefault;
    e.flush=e.flush?e.flush:&FlushDefault;e.pin_module=e.pin_module?e.pin_module:&PinDefault;
    e.bindings.exact_build_and_prefixes_verified=false;
    for(std::size_t i=0;i<state.hooks.size();++i) {
      auto &slot=state.hooks[i];const auto &desc=kDescriptions[i];slot.size=desc.prefix_bytes;
      if(desc.rva>(std::numeric_limits<std::uintptr_t>::max)()-e.module_base) {state.failure_flags.fetch_or(kBinding);return false;}
      slot.target=e.target_overrides[i]?e.target_overrides[i]:e.module_base+desc.rva;
      for(std::size_t k=0;k<i;++k)if(slot.target==state.hooks[k].target) {state.failure_flags.fetch_or(kBinding);return false;}
      if(!e.bindings.read(e.bindings.read_context,slot.target,slot.original.data(),slot.size)||
         !std::equal(slot.original.begin(),slot.original.begin()+slot.size,desc.prefix.begin())) {state.failure_flags.fetch_or(kAnchor);return false;}
    }
    for(auto &slot:state.hooks) {
      const auto bytes=slot.size+kJump;slot.trampoline=e.allocate(e.memory_context,bytes);
      if(!slot.trampoline) {state.failure_flags.fetch_or(kAllocate);AbortUnpublished(state);return false;}
      std::array<std::uint8_t,30> code{};std::copy_n(slot.original.begin(),slot.size,code.begin());Jump(code.data()+slot.size,slot.target+slot.size);
      DWORD old=0;
      if(!e.write(e.memory_context,reinterpret_cast<std::uintptr_t>(slot.trampoline),code.data(),bytes)||
         !e.protect(e.memory_context,slot.trampoline,bytes,PAGE_EXECUTE_READ,old)||
         !e.flush(e.memory_context,slot.trampoline,bytes)) {state.failure_flags.fetch_or(kProtection);AbortUnpublished(state);return false;}
    }
    if(!e.pin_module(e.memory_context)) {state.failure_flags.fetch_or(kPin);AbortUnpublished(state);return false;}
    state.module_pinned=true;e.bindings.exact_build_and_prefixes_verified=true;
    (void)e.bindings.journal->SetEnabled(false);
    for(std::size_t i=0;i<state.hooks.size();++i)g_original[i].store(reinterpret_cast<std::uintptr_t>(state.hooks[i].trampoline),std::memory_order_release);
    g_owned.store(&state,std::memory_order_release);
    for(std::size_t i=0;i<state.hooks.size();++i) {
      auto &slot=state.hooks[i];DWORD old=0,ignored=0;
      if(!e.protect(e.memory_context,reinterpret_cast<void *>(slot.target),slot.size,PAGE_EXECUTE_READWRITE,old)) {
        state.failure_flags.fetch_or(kProtection);
        const bool restored=RestoreAll(state,true);if(restored&&FreeAll(state))g_owned.store(nullptr,std::memory_order_release);
        state.installed.store(!restored,std::memory_order_release);return false;
      }
      slot.original_protection=old;slot.patch_may_be_present=true;const auto patch=Patch(i,slot.size);
      const bool copied=e.write(e.memory_context,slot.target,patch.data(),slot.size);
      const bool flushed=e.flush(e.memory_context,reinterpret_cast<const void *>(slot.target),slot.size);
      const bool protected_again=e.protect(e.memory_context,reinterpret_cast<void *>(slot.target),slot.size,old,ignored);
      if(!copied||!flushed||!protected_again) {
        state.failure_flags.fetch_or(kPublish);const bool restored=RestoreAll(state,true);
        if(restored&&FreeAll(state))g_owned.store(nullptr,std::memory_order_release);
        state.installed.store(!restored,std::memory_order_release);return false;
      }
    }
    state.installed.store(true,std::memory_order_release);return true;
  } catch(...) {state.failure_flags.fetch_or(kBinding);return false;}
}
bool UninstallWarPaymentPassive12004(WarPaymentDetourState12004 &state,bool quiescent) noexcept {
  try {
    const std::lock_guard lock(g_install_mutex);
    if(!quiescent||g_owned.load(std::memory_order_acquire)!=&state||state.active_calls.load(std::memory_order_acquire)!=0) {state.failure_flags.fetch_or(kBusy);return false;}
    (void)state.environment.bindings.journal->SetEnabled(false);
    if(!RestoreAll(state,false))return false;
    state.installed.store(false,std::memory_order_release);
    if(!FreeAll(state))return false;
    g_owned.store(nullptr,std::memory_order_release);state.environment.bindings.exact_build_and_prefixes_verified=false;return true;
  } catch(...) {state.failure_flags.fetch_or(kRollback);return false;}
}
} // namespace xar::ck3_12004
