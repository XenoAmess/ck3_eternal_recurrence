#include "xar_bridge/ck3_12004_county_relation_inputs_hook.hpp"
#include "xar_bridge/ck3_12004_county_relation_inputs_context.hpp"
#include "xar_bridge/ck3_12004_county_predicate_trace_hook.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include <array>
#include <atomic>
#include <cstring>
#include <intrin.h>
#include <limits>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
constexpr std::uintptr_t kEntry = 0x2C09620;
// Held actual191B body: four complete prologue instructions, exactly15B.
constexpr std::array<std::uint8_t,15> kPrefix{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,
    0x24,0x10,0x57,0x48,0x83,0xEC,0x20};
std::atomic<CountyRelationOriginal12004> g_original{nullptr};
std::atomic<bool> g_installed{false};
bool g_attempted = false;
std::uintptr_t g_base = 0;
HMODULE g_bridge_module = nullptr;
RUNTIME_FUNCTION g_trampoline_unwind{};
struct ReadBudget { std::size_t remaining = 96; };
bool GuardedRead(void *context, std::uintptr_t address, void *destination,
    std::size_t bytes) noexcept {
  auto &budget = *static_cast<ReadBudget *>(context);
  if (!budget.remaining || !address || !destination || !bytes || bytes > 8 ||
      address > std::numeric_limits<std::uintptr_t>::max() - bytes) return false;
  --budget.remaining;
  __try { std::memcpy(destination, reinterpret_cast<const void *>(address), bytes); }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
  return true;
}
bool Exact(const void *address) noexcept {
  std::array<std::uint8_t,15> bytes{};
  __try { std::memcpy(bytes.data(), address, bytes.size()); }
  __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
  return bytes == kPrefix;
}
void Jump(std::uint8_t *at, std::uintptr_t target) noexcept {
  constexpr std::uint8_t op[6]{0xFF,0x25,0,0,0,0};
  std::memcpy(at,op,6);std::memcpy(at+6,&target,8);
}
void TrampolineJump(std::uint8_t *at, std::uintptr_t target) noexcept {
  // The held complete 2C09620 body never reads R11. A register JMP with
  // ModRM mod3 is not the memory-jump epilogue pattern of the old FF25 tail.
  constexpr std::uint8_t move[2]{0x49,0xBB};
  constexpr std::uint8_t jump[3]{0x41,0xFF,0xE3};
  std::memcpy(at,move,2);std::memcpy(at+2,&target,8);std::memcpy(at+10,jump,3);
}
}
extern "C" bool __fastcall XarCountyRelationInputsHook12004(void *receiver,
    void *actor, std::uintptr_t auxiliary, std::uintptr_t opaque_r9) {
  const auto original = g_original.load(std::memory_order_acquire);
  auto *const frame = g_county_predicate_trace12004;
  // Ordinary game relation calls pay no module lookup or sampling setup.
  if (!frame || !frame->trace.scope_entered || !frame->active_relation_stage ||
      frame->callback_depth != 1 || frame->relation_callback_depth != 0)
    return original ? original(receiver, actor, auxiliary, opaque_r9) : false;
  const auto pc = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  HMODULE caller_module = nullptr;
  std::optional<std::uint64_t> bridge_caller;
  if (g_bridge_module && GetModuleHandleExW(
      GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
      reinterpret_cast<LPCWSTR>(pc), &caller_module) && caller_module == g_bridge_module)
    bridge_caller = pc - reinterpret_cast<std::uintptr_t>(g_bridge_module);
  ReadBudget budget{};
  const ArmyRegularCoreReadonlyAccess12004 access{g_base, &budget, &GuardedRead};
  return InvokeCountyRelationInputs12004(original,
      receiver, actor, auxiliary, opaque_r9, bridge_caller, GetCurrentThreadId(), access);
}
bool CountyRelationInputsHookInstalled12004() noexcept {
  return g_installed.load(std::memory_order_acquire);
}
bool InstallCountyRelationInputsHook12004(std::uintptr_t base,
    std::string_view sha, bool suspended) noexcept {
  if (!base || sha != kExecutableSha256 || !suspended || g_attempted ||
      !CountyPredicateTraceHookInstalled12004()) return false;
  g_attempted = true;
  auto *const target = reinterpret_cast<std::uint8_t *>(base+kEntry);
  if (!Exact(target)) return false;
  HMODULE module = nullptr;
  if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
      reinterpret_cast<LPCWSTR>(&XarCountyRelationInputsHook12004), &module)) return false;
  // 15B copied prologue +13B MOV R11/JMP R11, pad32, then held16B xdata.
  auto *const trampoline = static_cast<std::uint8_t *>(VirtualAlloc(nullptr,48,
      MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
  if (!trampoline) return false;
  std::memcpy(trampoline,kPrefix.data(),kPrefix.size());
  TrampolineJump(trampoline+15,reinterpret_cast<std::uintptr_t>(target)+15);
  // Exact held native xdata at5109E4C. Offsets remain valid for the copied
  // prologue (RBX/RSI saves, pushRDI, alloc32), including partial unwinds.
  constexpr std::array<std::uint8_t,16> unwind{
      0x01,0x0F,0x06,0x00,0x0F,0x64,0x07,0x00,
      0x0F,0x34,0x06,0x00,0x0F,0x32,0x0B,0x70};
  std::memcpy(trampoline+32,unwind.data(),unwind.size());
  g_trampoline_unwind.BeginAddress=0;
  g_trampoline_unwind.EndAddress=28;
  g_trampoline_unwind.UnwindData=32;
  if (!RtlAddFunctionTable(&g_trampoline_unwind,1,reinterpret_cast<DWORD64>(trampoline))) {
    VirtualFree(trampoline,0,MEM_RELEASE);return false;
  }
  DWORD ignored=0;
  if (!VirtualProtect(trampoline,48,PAGE_EXECUTE_READ,&ignored) ||
      !FlushInstructionCache(GetCurrentProcess(),trampoline,48)) {
    (void)RtlDeleteFunctionTable(&g_trampoline_unwind);
    VirtualFree(trampoline,0,MEM_RELEASE);return false;
  }
  g_base=base;g_bridge_module=module;
  g_original.store(reinterpret_cast<CountyRelationOriginal12004>(trampoline),std::memory_order_release);
  std::array<std::uint8_t,15> patch{};patch.fill(0x90);
  Jump(patch.data(),reinterpret_cast<std::uintptr_t>(&XarCountyRelationInputsHook12004));
  DWORD old=0;
  if (!Exact(target) || !VirtualProtect(target,15,PAGE_EXECUTE_READWRITE,&old)) return false;
  std::memcpy(target,patch.data(),patch.size());
  const bool flushed=FlushInstructionCache(GetCurrentProcess(),target,15)!=FALSE;
  const bool restored=VirtualProtect(target,15,old,&ignored)!=FALSE;
  if (flushed && restored) {g_installed.store(true,std::memory_order_release);return true;}
  DWORD rollback=0;
  if (VirtualProtect(target,15,PAGE_EXECUTE_READWRITE,&rollback)) {
    std::memcpy(target,kPrefix.data(),kPrefix.size());
    (void)FlushInstructionCache(GetCurrentProcess(),target,15);
    (void)VirtualProtect(target,15,old,&ignored);
  }
  return false;
}
}
