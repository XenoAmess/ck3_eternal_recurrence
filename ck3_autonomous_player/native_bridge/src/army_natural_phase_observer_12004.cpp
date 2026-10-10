#include "xar_bridge/army_natural_phase_observer_12004.hpp"

#include <array>
#include <cstring>
#include <mutex>
#include <intrin.h>
#include <windows.h>

namespace xar::ck3_12004 {
namespace {
ArmyNaturalPhaseObserverEnvironment12004 g_environment;
ArmyNaturalPhaseOriginal12004 g_pre_original = nullptr;
ArmyNaturalPhaseOriginal12004 g_post_original = nullptr;
bool g_install_attempted = false;
std::mutex g_state_mutex;
ArmyNaturalPhaseObserverState12004 g_owned_state;
struct PublishState {
  ArmyNaturalPhaseObserverState12004 &state;
  ~PublishState() {
    try { std::lock_guard<std::mutex> lock(g_state_mutex); g_owned_state = state; }
    catch (...) {}
  }
};
constexpr std::array<std::uint8_t, 17> kPreBytes{
    0x48,0x89,0x4c,0x24,0x08,0x55,0x53,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56,0x41,0x57};
constexpr std::array<std::uint8_t, 19> kPostBytes{
    0x48,0x89,0x5c,0x24,0x20,0x48,0x89,0x4c,0x24,0x08,0x55,0x56,0x57,0x41,0x54,0x41,0x55,0x41,0x56};

ArmyNaturalPhaseBindings12004 Bind() noexcept {
  ArmyNaturalPhaseBindings12004 b{};
  b.read = g_environment.read;
  b.read_context = g_environment.read_context;
  b.next_event = NextArmyNaturalPhaseEvent12004;
  std::uintptr_t state = 0;
  if (b.read && b.read(b.read_context, g_environment.module_base + 0x5C68C50,
      &state, sizeof state)) b.game_state_identity = state;
  return b;
}
std::uintptr_t ReturnRva(void *address) noexcept {
  const auto pc = reinterpret_cast<std::uintptr_t>(address);
  return pc >= g_environment.module_base ? pc - g_environment.module_base : 0;
}
std::uintptr_t __fastcall Pre(void *secondary) noexcept {
  const auto return_rva = ReturnRva(_ReturnAddress());
  return InvokeArmyNaturalPhaseScope12004(Bind(), g_pre_original, secondary,
      ArmyNaturalPhaseKind12004::pre_date, return_rva).raw_return_bits;
}
std::uintptr_t __fastcall Post(void *secondary) noexcept {
  const auto return_rva = ReturnRva(_ReturnAddress());
  return InvokeArmyNaturalPhaseScope12004(Bind(), g_post_original, secondary,
      ArmyNaturalPhaseKind12004::post_date, return_rva).raw_return_bits;
}
void Jump(std::byte *destination, std::uintptr_t target) noexcept {
  const std::array<std::uint8_t, 6> instruction{0xff,0x25,0,0,0,0};
  std::memcpy(destination, instruction.data(), instruction.size());
  std::memcpy(destination + 6, &target, sizeof target);
}
template<std::size_t N> bool Verify(std::uintptr_t target,
    const std::array<std::uint8_t, N> &expected) noexcept {
  std::array<std::uint8_t, N> bytes{};
  return g_environment.read && g_environment.read(g_environment.read_context,
      target, bytes.data(), bytes.size()) && bytes == expected;
}
template<std::size_t N> ArmyNaturalPhaseOriginal12004 Trampoline(
    std::uintptr_t target, const std::array<std::uint8_t, N> &expected) noexcept {
  auto *memory = static_cast<std::byte *>(VirtualAlloc(nullptr, N + 14,
      MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE));
  if (!memory) return nullptr;
  std::memcpy(memory, expected.data(), N);
  Jump(memory + N, target + N);
  DWORD previous = 0;
  if (!VirtualProtect(memory, N + 14, PAGE_EXECUTE_READ, &previous) ||
      !FlushInstructionCache(GetCurrentProcess(), memory, N + 14)) {
    VirtualFree(memory, 0, MEM_RELEASE);
    return nullptr;
  }
  return reinterpret_cast<ArmyNaturalPhaseOriginal12004>(memory);
}
template<std::size_t N> bool Patch(std::uintptr_t target,
    const std::array<std::uint8_t, N> &, std::uintptr_t hook, bool &applied) noexcept {
  DWORD previous = 0;
  auto *memory = reinterpret_cast<std::byte *>(target);
  if (!VirtualProtect(memory, N, PAGE_EXECUTE_READWRITE, &previous)) return false;
  std::array<std::byte, N> patch{};
  patch.fill(std::byte{0x90});
  Jump(patch.data(), hook);
  std::memcpy(memory, patch.data(), N);
  applied = true;
  DWORD discarded = 0;
  const bool protected_again = VirtualProtect(memory, N, previous, &discarded) != FALSE;
  const bool flushed = FlushInstructionCache(GetCurrentProcess(), memory, N) != FALSE;
  return protected_again && flushed;
}
} // namespace

bool InstallArmyNaturalPhaseObserver12004(
    const ArmyNaturalPhaseObserverEnvironment12004 &environment,
    ArmyNaturalPhaseObserverState12004 &state) noexcept {
  if (g_install_attempted) { state.reason = "install_attempt_already_owned"; return false; }
  if (!environment.module_base || !environment.read ||
      !environment.primary_thread_suspended_proven ||
      environment.actual_exe_sha256 !=
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518") {
    state.reason = "exact_build_read_or_suspended_primary_missing";
    return false;
  }
  g_install_attempted = true;
  PublishState publish{state};
  g_environment = environment;
  const auto pre = environment.module_base + kArmyNaturalPreDateRva12004;
  const auto post = environment.module_base + kArmyNaturalPostDateRva12004;
  if (!Verify(pre, kPreBytes) || !Verify(post, kPostBytes)) {
    state.reason = "literal_callback_prologue_mismatch";
    return false;
  }
  state.source_bytes_verified = true;
  HMODULE owning_module = nullptr;
  if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_PIN,
      reinterpret_cast<LPCWSTR>(&Pre), &owning_module)) {
    state.reason = "callback_module_lifetime_pin_failed";
    return false;
  }
  state.module_lifetime_pinned = true;
  g_pre_original = Trampoline(pre, kPreBytes);
  g_post_original = Trampoline(post, kPostBytes);
  if (!g_pre_original || !g_post_original) {
    state.reason = "callback_trampoline_unavailable";
    return false;
  }
  // If any write fails Root keeps the primary suspended and rejects startup.
  // A partial install remains explicitly recorded, never relabeled as complete.
  state.pre_date_installed = Patch(pre, kPreBytes, reinterpret_cast<std::uintptr_t>(&Pre),
      state.pre_date_patch_applied);
  if (!state.pre_date_installed) { state.reason = "pre_date_patch_failed"; return false; }
  state.post_date_installed = Patch(post, kPostBytes, reinterpret_cast<std::uintptr_t>(&Post),
      state.post_date_patch_applied);
  state.installed = state.pre_date_installed && state.post_date_installed;
  state.reason = state.installed ? "installed_process_lifetime" : "post_date_patch_failed_partial_install";
  return state.installed;
}
ArmyNaturalPhaseObserverState12004 ReadArmyNaturalPhaseObserverState12004() noexcept {
  try { std::lock_guard<std::mutex> lock(g_state_mutex); return g_owned_state; }
  catch (...) {
    ArmyNaturalPhaseObserverState12004 out{};
    out.reason = "observer_state_unread";
    return out;
  }
}
} // namespace xar::ck3_12004
