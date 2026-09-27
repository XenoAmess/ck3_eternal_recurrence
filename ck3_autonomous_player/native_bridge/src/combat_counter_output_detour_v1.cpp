#include "xar_bridge/combat_counter_output_detour_v1.hpp"

#include <array>
#include <cstring>

namespace xar::ck3_11906 {
namespace {

constexpr std::array<std::uint8_t, kCombatCounterOutputPatchBytesV1>
    kOriginal{0x4D, 0x89, 0x3E, 0x48, 0x8B, 0x3E, 0x48,
              0x63, 0x46, 0x0C, 0x4C, 0x8D, 0x3C, 0x40};

void AbsoluteJump(std::uint8_t *destination, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{
      0xFF, 0x25, 0x00, 0x00, 0x00, 0x00};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}

bool Matches(std::uintptr_t address,
             const std::array<std::uint8_t,
                              kCombatCounterOutputPatchBytesV1> &bytes) noexcept {
  if (address == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(address), bytes.data(),
                       bytes.size()) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool FillTrampoline(void *storage, std::uintptr_t resume) noexcept {
  if (storage == nullptr || resume == 0) return false;
  auto *const bytes = static_cast<std::uint8_t *>(storage);
  std::memset(bytes, 0x90, kCombatCounterOutputTrampolineBytesV1);
  std::size_t cursor = 0;
  const auto append = [&](const auto &source) {
    std::memcpy(bytes + cursor, source.data(), source.size());
    cursor += source.size();
  };
  // At the immediately preceding native helper call RSP is 16-byte aligned.
  // Eight pushes preserve alignment and all volatile GPRs plus RFLAGS; the
  // callback has its required Win64 shadow space. Inputs are still RBP output
  // header, RSI/RDI MAA headers and RBX context before the original MOVs.
  constexpr std::array<std::uint8_t, 16> save{
      0x9C, 0x50, 0x51, 0x52, 0x41, 0x50, 0x41, 0x51,
      0x41, 0x52, 0x41, 0x53, 0x48, 0x83, 0xEC, 0x20};
  append(save);
  constexpr std::array<std::uint8_t, 12> arguments{
      0x48, 0x8B, 0xCD, 0x48, 0x8B, 0xD6,
      0x4C, 0x8B, 0xC7, 0x4C, 0x8B, 0xCB};
  append(arguments);
  constexpr std::array<std::uint8_t, 2> mov_rax{0x48, 0xB8};
  append(mov_rax);
  const auto callback = reinterpret_cast<std::uintptr_t>(
      &XarCaptureCombatCounterOutputV1);
  std::memcpy(bytes + cursor, &callback, sizeof(callback));
  cursor += sizeof(callback);
  constexpr std::array<std::uint8_t, 18> restore{
      0xFF, 0xD0, 0x48, 0x83, 0xC4, 0x20, 0x41, 0x5B,
      0x41, 0x5A, 0x41, 0x59, 0x41, 0x58, 0x5A, 0x59,
      0x58, 0x9D};
  append(restore);
  append(kOriginal);
  if (cursor + kCombatPhaseEventTraceAbsoluteJumpBytesV1 >
      kCombatCounterOutputTrampolineBytesV1) {
    return false;
  }
  AbsoluteJump(bytes + cursor, resume);
  return true;
}

bool WriteTarget(std::uintptr_t target,
                 const std::array<std::uint8_t,
                                  kCombatCounterOutputPatchBytesV1> &expected,
                 const std::array<std::uint8_t,
                                  kCombatCounterOutputPatchBytesV1> &desired)
    noexcept {
  if (!Matches(target, expected)) return false;
  DWORD old_protection = 0;
  if (!VirtualProtect(reinterpret_cast<void *>(target), desired.size(),
                      PAGE_EXECUTE_READWRITE, &old_protection)) {
    return false;
  }
  bool wrote = false;
  if (Matches(target, expected)) {
    std::memcpy(reinterpret_cast<void *>(target), desired.data(),
                desired.size());
    wrote = true;
  }
  const bool flushed = wrote && FlushInstructionCache(
      GetCurrentProcess(), reinterpret_cast<void *>(target), desired.size()) !=
      FALSE;
  DWORD ignored = 0;
  const bool protected_again = VirtualProtect(
      reinterpret_cast<void *>(target), desired.size(), old_protection,
      &ignored) != FALSE;
  return wrote && flushed && protected_again && Matches(target, desired);
}

} // namespace

bool InstallCombatCounterOutputDetourV1(
    CombatCounterOutputDetourV1 &state, std::uintptr_t module_base,
    bool exact_build_admitted, bool paused_quiescence_proven,
    std::uintptr_t offline_target_override) noexcept {
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.trampoline != nullptr) {
    state.failure_flags |= trace_detour_failure_already_installed;
    return false;
  }
  state.failure_flags = 0;
  if (!exact_build_admitted || module_base == 0) {
    state.failure_flags |= trace_detour_failure_exact_build;
    return false;
  }
  if (!paused_quiescence_proven || IsCombatPhaseEventTraceRingV1Armed()) {
    state.failure_flags |= trace_detour_failure_paused_quiescence;
    return false;
  }
  state.target = offline_target_override != 0
                     ? offline_target_override
                     : module_base + kCombatCounterOutputCaptureRva;
  if (!Matches(state.target, kOriginal)) {
    state.failure_flags |= trace_detour_failure_anchor;
    return false;
  }
  state.original = kOriginal;
  state.trampoline = VirtualAlloc(
      nullptr, kCombatCounterOutputTrampolineBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    state.failure_flags |= trace_detour_failure_allocation;
    return false;
  }
  DWORD previous = 0;
  if (!FillTrampoline(state.trampoline,
                      state.target + kCombatCounterOutputPatchBytesV1) ||
      !VirtualProtect(state.trampoline,
                      kCombatCounterOutputTrampolineBytesV1,
                      PAGE_EXECUTE_READ, &previous) ||
      !FlushInstructionCache(GetCurrentProcess(), state.trampoline,
                             kCombatCounterOutputTrampolineBytesV1)) {
    state.failure_flags |= trace_detour_failure_trampoline_protection;
    (void)VirtualFree(state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    return false;
  }
  std::array<std::uint8_t, kCombatCounterOutputPatchBytesV1> patch{};
  AbsoluteJump(patch.data(),
               reinterpret_cast<std::uintptr_t>(state.trampoline));
  if (!WriteTarget(state.target, state.original, patch)) {
    state.failure_flags |= trace_detour_failure_target_protection;
    if (!Matches(state.target, state.original)) {
      // If a partial failure left our patch live, retain its trampoline and
      // ownership so the managed driver can stop CK3 without a dangling jump.
      state.failure_flags |= trace_detour_failure_rollback;
      state.installed.store(1, std::memory_order_release);
      return false;
    }
    (void)VirtualFree(state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    return false;
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallCombatCounterOutputDetourV1(
    CombatCounterOutputDetourV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      state.trampoline == nullptr || state.target == 0 ||
      IsCombatPhaseEventTraceRingV1Armed()) {
    return false;
  }
  std::array<std::uint8_t, kCombatCounterOutputPatchBytesV1> patch{};
  AbsoluteJump(patch.data(),
               reinterpret_cast<std::uintptr_t>(state.trampoline));
  if (!Matches(state.target, patch)) {
    state.failure_flags |= trace_detour_failure_target_identity;
    return false;
  }
  if (!WriteTarget(state.target, patch, state.original)) {
    state.failure_flags |= trace_detour_failure_rollback;
    if (Matches(state.target, state.original)) {
      // Bytes are restored, but a failed flush/protection cannot prove the
      // running instruction stream safe; retain ownership for process stop.
      return false;
    }
    if (!Matches(state.target, patch)) {
      (void)WriteTarget(state.target, state.original, patch);
    }
    return false;
  }
  (void)VirtualFree(state.trampoline, 0, MEM_RELEASE);
  state.trampoline = nullptr;
  state.installed.store(0, std::memory_order_release);
  return true;
}

} // namespace xar::ck3_11906
