#include "xar_bridge/ck3_12004_residual_parent_hook.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <cstring>
#include <intrin.h>

namespace xar::ck3_12004 {
namespace {
std::atomic<ActualResidualNonzeroOriginal12004> g_original{nullptr};
std::uintptr_t g_image_base=0;
bool g_attempted=false;
bool GuardedRead(void*,const void *address,void *out,std::size_t bytes) noexcept {
  if(!address)return false;
  __try{std::memcpy(out,address,bytes);return true;}
  __except(EXCEPTION_EXECUTE_HANDLER){return false;}
}
void Jump(std::uint8_t *at,std::uintptr_t target) noexcept {
  constexpr std::uint8_t op[6]{0xFF,0x25,0,0,0,0};
  std::memcpy(at,op,sizeof op);std::memcpy(at+sizeof op,&target,sizeof target);
}
bool Exact(const void *at) noexcept {
  std::array<std::uint8_t,kActualResidualContinuationPrefix12004.size()> b{};
  return GuardedRead(nullptr,at,b.data(),b.size())&&b==kActualResidualContinuationPrefix12004;
}
bool ExactZeroBypass(const void *at) noexcept {
  constexpr std::array<std::uint8_t,8> expected{0x85,0xD2,0x0F,0x84,0x58,0x01,0,0};
  std::array<std::uint8_t,8> actual{};
  return GuardedRead(nullptr,at,actual.data(),actual.size())&&actual==expected;
}
}
extern "C" std::uintptr_t __fastcall XarActualResidualNonzeroHook12004(
    void *array,std::int32_t budget,std::uint8_t flags) noexcept {
  const auto pc=reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto *natural_return_slot=_AddressOfReturnAddress();
  std::optional<std::uint64_t> caller;
  if(g_image_base&&pc>=g_image_base)caller=pc-g_image_base;
  return InvokeActualResidualNonzeroParent12004(
      {nullptr,&GuardedRead},g_original.load(std::memory_order_acquire),
      array,budget,flags,caller,GetCurrentThreadId(),natural_return_slot);
}
bool InstallActualResidualParentHook12004(std::uintptr_t base,
    std::string_view sha,bool suspended) noexcept {
  if(!base||sha!=kExecutableSha256||!suspended||g_attempted)return false;
  g_attempted=true;
  auto *target=reinterpret_cast<std::uint8_t*>(base+kActualResidualNonzeroContinuation12004);
  if(!Exact(target)||!ExactZeroBypass(reinterpret_cast<const void*>(base+kActualResidualEntry12004)))return false;
  HMODULE owning=nullptr;
  if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
      reinterpret_cast<LPCWSTR>(&XarActualResidualNonzeroHook12004),&owning))return false;
  constexpr auto prefix=kActualResidualContinuationPrefix12004.size();
  auto *trampoline=static_cast<std::uint8_t*>(VirtualAlloc(nullptr,prefix+14,
      MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  if(!trampoline)return false;
  std::memcpy(trampoline,kActualResidualContinuationPrefix12004.data(),prefix);
  Jump(trampoline+prefix,reinterpret_cast<std::uintptr_t>(target)+prefix);
  DWORD previous=0;
  if(!VirtualProtect(trampoline,prefix+14,PAGE_EXECUTE_READ,&previous)||
      !FlushInstructionCache(GetCurrentProcess(),trampoline,prefix+14)){
    VirtualFree(trampoline,0,MEM_RELEASE);return false;
  }
  g_image_base=base;
  g_original.store(reinterpret_cast<ActualResidualNonzeroOriginal12004>(trampoline),std::memory_order_release);
  std::array<std::uint8_t,prefix> patch{};patch.fill(0x90);
  Jump(patch.data(),reinterpret_cast<std::uintptr_t>(&XarActualResidualNonzeroHook12004));
  DWORD old=0;
  if(!Exact(target)||!VirtualProtect(target,prefix,PAGE_EXECUTE_READWRITE,&old))return false;
  std::memcpy(target,patch.data(),prefix);
  const bool flushed=FlushInstructionCache(GetCurrentProcess(),target,prefix)!=FALSE;
  DWORD ignored=0;
  const bool restored=VirtualProtect(target,prefix,old,&ignored)!=FALSE;
  if(flushed&&restored)return true;
  // Startup stays suspended on failure. Keep the pinned hook/trampoline alive
  // even when rollback fails, because patched bytes may still reference them.
  DWORD rollback=0;
  if(VirtualProtect(target,prefix,PAGE_EXECUTE_READWRITE,&rollback)){
    std::memcpy(target,kActualResidualContinuationPrefix12004.data(),prefix);
    (void)FlushInstructionCache(GetCurrentProcess(),target,prefix);
    (void)VirtualProtect(target,prefix,old,&ignored);
  }
  return false;
}
}
