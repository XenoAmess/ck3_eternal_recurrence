#include "xar_bridge/ck3_12004_county_predicate_trace_hook.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <atomic>
#include <cstring>
#include <intrin.h>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kEntry = 0x2C09DF0;
// Actual held131B source, first three complete instructions: push RBX,
// sub RSP,32, cmp DWORD[ RDX+3E0 ],CoDa. No RIP/branch relocation.
constexpr std::array<std::uint8_t,16> kPrefix{
    0x40,0x53,0x48,0x83,0xEC,0x20,0x81,0xBA,
    0xE0,0x03,0x00,0x00,0x61,0x44,0x6F,0x43};
std::atomic<CountyPredicateOriginal12004> g_original{nullptr};
std::atomic<bool> g_installed{false};
std::uintptr_t g_base = 0;
bool g_attempted = false;
RUNTIME_FUNCTION g_trampoline_unwind{};
bool Exact(const void *address) noexcept {
  std::array<std::uint8_t,16> bytes{};
  __try { std::memcpy(bytes.data(), address, bytes.size()); }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
  return bytes == kPrefix;
}
void Jump(std::uint8_t *at,std::uintptr_t target) noexcept {
  constexpr std::uint8_t op[6]{0xFF,0x25,0,0,0,0};
  std::memcpy(at,op,6);std::memcpy(at+6,&target,8);
}
}
extern "C" bool __fastcall XarCountyPredicateTraceHook12004(void *actor,void *county,
    std::uintptr_t opaque_r8,std::uintptr_t opaque_r9) {
  const auto pc = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  std::optional<std::uint64_t> caller;
  if (g_base && pc >= g_base) caller = pc-g_base;
  return InvokeCountyPredicateTrace12004(g_original.load(std::memory_order_acquire),
      actor,county,caller,GetCurrentThreadId(),opaque_r8,opaque_r9);
}
bool CountyPredicateTraceHookInstalled12004() noexcept {
  return g_installed.load(std::memory_order_acquire);
}
bool InstallCountyPredicateTraceHook12004(std::uintptr_t base,
    std::string_view sha,bool suspended) noexcept {
  if (!base || sha != kExecutableSha256 || !suspended || g_attempted) return false;
  g_attempted = true;
  auto *const target = reinterpret_cast<std::uint8_t *>(base+kEntry);
  if (!Exact(target)) return false;
  HMODULE module = nullptr;
  if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
      reinterpret_cast<LPCWSTR>(&XarCountyPredicateTraceHook12004),&module)) return false;
  // 16B native prefix +14B flag-preserving absolute jump; pad to32 for xdata.
  auto *const trampoline = static_cast<std::uint8_t *>(VirtualAlloc(nullptr,40,
      MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  if (!trampoline) return false;
  std::memcpy(trampoline,kPrefix.data(),kPrefix.size());
  Jump(trampoline+16,reinterpret_cast<std::uintptr_t>(target)+16);
  // x64 UNWIND_INFO v1/prolog6/count2/frame0: alloc_small32 at+6,
  // push_nonvolRBX at+2. Covers the faultable copied CMP as well as the jump.
  constexpr std::array<std::uint8_t,8> unwind{1,6,2,0,6,0x32,2,0x30};
  std::memcpy(trampoline+32,unwind.data(),unwind.size());
  g_trampoline_unwind.BeginAddress=0;
  g_trampoline_unwind.EndAddress=30;
  g_trampoline_unwind.UnwindData=32;
  if (!RtlAddFunctionTable(&g_trampoline_unwind,1,reinterpret_cast<DWORD64>(trampoline))) {
    VirtualFree(trampoline,0,MEM_RELEASE);return false;
  }
  DWORD ignored=0;
  if (!VirtualProtect(trampoline,40,PAGE_EXECUTE_READ,&ignored) ||
      !FlushInstructionCache(GetCurrentProcess(),trampoline,40)) {
    (void)RtlDeleteFunctionTable(&g_trampoline_unwind);
    VirtualFree(trampoline,0,MEM_RELEASE);return false;
  }
  g_base=base;
  g_original.store(reinterpret_cast<CountyPredicateOriginal12004>(trampoline),std::memory_order_release);
  std::array<std::uint8_t,16> patch{};patch.fill(0x90);
  Jump(patch.data(),reinterpret_cast<std::uintptr_t>(&XarCountyPredicateTraceHook12004));
  DWORD old=0;
  if (!Exact(target) || !VirtualProtect(target,16,PAGE_EXECUTE_READWRITE,&old)) return false;
  std::memcpy(target,patch.data(),patch.size());
  const bool flushed=FlushInstructionCache(GetCurrentProcess(),target,16)!=FALSE;
  const bool restored=VirtualProtect(target,16,old,&ignored)!=FALSE;
  if (flushed && restored) {g_installed.store(true,std::memory_order_release);return true;}
  // PrepareStartup fails while primary remains suspended. Keep pinned code and
  // unwind table alive even if rollback fails; never unload a reachable hook.
  DWORD rollback=0;
  if (VirtualProtect(target,16,PAGE_EXECUTE_READWRITE,&rollback)) {
    std::memcpy(target,kPrefix.data(),kPrefix.size());
    (void)FlushInstructionCache(GetCurrentProcess(),target,16);
    (void)VirtualProtect(target,16,old,&ignored);
  }
  return false;
}
}
