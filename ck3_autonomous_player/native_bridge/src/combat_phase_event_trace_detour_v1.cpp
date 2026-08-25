#include "xar_bridge/combat_phase_event_trace_detour_v1.hpp"

#include <intrin.h>

#include <array>
#include <cstring>

namespace xar::ck3_11906 {
namespace {

std::atomic<CombatPhaseEventTraceDetourStateV1 *> g_active_detours{nullptr};

constexpr std::array<std::uint8_t, 15> kSchedulePrologue{
    0x4C, 0x89, 0x44, 0x24, 0x18, 0x48, 0x89, 0x54,
    0x24, 0x10, 0x53, 0x56, 0x57, 0x41, 0x55};
constexpr std::array<std::uint8_t, 15> kFirePrologue{
    0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
    0x24, 0x10, 0x48, 0x89, 0x7C, 0x24, 0x18};
constexpr std::array<std::uint8_t, 5> kScheduleSide0Call{
    0xE8, 0xBC, 0xD1, 0xBC, 0xFF};
constexpr std::array<std::uint8_t, 5> kScheduleSide1Call{
    0xE8, 0xA4, 0xD1, 0xBC, 0xFF};
constexpr std::array<std::uint8_t, 5> kFireSide0Call{
    0xE8, 0xF9, 0x03, 0x0C, 0x00};
constexpr std::array<std::uint8_t, 5> kFireSide1Call{
    0xE8, 0xF1, 0x03, 0x0C, 0x00};
constexpr std::array<std::uint8_t, 5> kFireTailJump{
    0xE9, 0xAD, 0xF5, 0xFF, 0xFF};

void AddFailure(CombatPhaseEventTraceDetourStateV1 &state,
                CombatPhaseEventTraceDetourFailureV1 failure) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

void *DefaultVirtualAlloc(void *, std::size_t size, DWORD allocation_type,
                          DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, allocation_type, protection);
}

bool DefaultVirtualFree(void *, void *address, std::size_t size,
                        DWORD free_type) noexcept {
  return VirtualFree(address, size, free_type) != FALSE;
}

bool DefaultVirtualProtect(void *, void *address, std::size_t size,
                           DWORD new_protection,
                           DWORD &old_protection) noexcept {
  old_protection = 0;
  return VirtualProtect(address, size, new_protection, &old_protection) !=
         FALSE;
}

bool DefaultFlushInstructionCache(void *, const void *address,
                                  std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

template <std::size_t Size>
bool BytesMatch(std::uintptr_t address,
                const std::array<std::uint8_t, Size> &expected) noexcept {
  if (address == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(address),
                       expected.data(), expected.size()) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

std::uintptr_t Resolve(std::uintptr_t override_address,
                       std::uintptr_t module_base,
                       std::uintptr_t rva) noexcept {
  return override_address != 0 ? override_address : module_base + rva;
}

void WriteAbsoluteJump(std::uint8_t *destination,
                       std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{
      0xFF, 0x25, 0x00, 0x00, 0x00, 0x00};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}

bool FillTrampoline(void *storage,
                    const std::array<std::uint8_t, 15> &original,
                    std::uintptr_t resume) noexcept {
  if (storage == nullptr || resume == 0) {
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(storage);
  std::memcpy(bytes, original.data(), original.size());
  WriteAbsoluteJump(bytes + original.size(), resume);
  return true;
}

bool Flush(CombatPhaseEventTraceDetourStateV1 &state,
           const void *address, std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, trace_detour_failure_flush);
    return false;
  }
  return true;
}

bool MakeTrampolineExecutable(
    CombatPhaseEventTraceDetourStateV1 &state, void *trampoline) noexcept {
  DWORD previous = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(state.memory_context, trampoline,
                             kCombatPhaseEventTraceTrampolineBytesV1,
                             PAGE_EXECUTE_READ, previous) ||
      previous != PAGE_READWRITE ||
      !Flush(state, trampoline,
             kCombatPhaseEventTraceTrampolineBytesV1)) {
    AddFailure(state, trace_detour_failure_trampoline_protection);
    return false;
  }
  return true;
}

bool WriteTargetBytes(CombatPhaseEventTraceDetourStateV1 &state,
                      std::uintptr_t target,
                      const std::uint8_t *expected,
                      const std::uint8_t *desired) noexcept {
  if (target == 0 || expected == nullptr || desired == nullptr ||
      std::memcmp(reinterpret_cast<const void *>(target), expected,
                  kCombatPhaseEventTraceDetourPatchBytesV1) != 0) {
    AddFailure(state, trace_detour_failure_target_identity);
    return false;
  }
  DWORD previous = 0;
  if (state.virtual_protect == nullptr ||
      !state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(target),
          kCombatPhaseEventTraceDetourPatchBytesV1,
          PAGE_EXECUTE_READWRITE, previous) ||
      (previous != PAGE_EXECUTE_READ &&
       previous != PAGE_EXECUTE_READWRITE &&
       previous != PAGE_EXECUTE_WRITECOPY)) {
    AddFailure(state, trace_detour_failure_target_protection);
    return false;
  }
  std::memcpy(reinterpret_cast<void *>(target), desired,
              kCombatPhaseEventTraceDetourPatchBytesV1);
  const bool identity_after =
      std::memcmp(reinterpret_cast<const void *>(target), desired,
                  kCombatPhaseEventTraceDetourPatchBytesV1) == 0;
  const bool flushed = Flush(
      state, reinterpret_cast<const void *>(target),
      kCombatPhaseEventTraceDetourPatchBytesV1);
  DWORD writable = 0;
  const bool restored = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(target),
      kCombatPhaseEventTraceDetourPatchBytesV1, previous, writable);
  if (!restored) {
    AddFailure(state, trace_detour_failure_target_protection);
  }
  if (!identity_after) {
    AddFailure(state, trace_detour_failure_target_identity);
  }
  if (identity_after && flushed && restored) {
    return true;
  }

  // A post-write cache/protection failure must not silently leave the desired
  // hook bytes behind while the caller believes installation failed.  The
  // page was made writable successfully above, so restore the exact expected
  // bytes before returning.  If even this recovery cannot be proven, surface
  // rollback failure and keep all trampoline storage alive at the caller.
  std::memcpy(reinterpret_cast<void *>(target), expected,
              kCombatPhaseEventTraceDetourPatchBytesV1);
  const bool rollback_identity =
      std::memcmp(reinterpret_cast<const void *>(target), expected,
                  kCombatPhaseEventTraceDetourPatchBytesV1) == 0;
  const bool rollback_flushed = state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context, reinterpret_cast<const void *>(target),
          kCombatPhaseEventTraceDetourPatchBytesV1);
  DWORD rollback_previous = 0;
  const bool rollback_protection = state.virtual_protect != nullptr &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(target),
          kCombatPhaseEventTraceDetourPatchBytesV1, previous,
          rollback_previous);
  if (!rollback_identity || !rollback_flushed || !rollback_protection) {
    AddFailure(state, trace_detour_failure_rollback);
  }
  return false;
}

bool RestoreTarget(CombatPhaseEventTraceDetourStateV1 &state,
                   std::uintptr_t target, const std::uint8_t *patch,
                   const std::uint8_t *original) noexcept {
  if (WriteTargetBytes(state, target, patch, original)) {
    return true;
  }
  AddFailure(state, trace_detour_failure_rollback);
  return false;
}

void FreeTrampolines(CombatPhaseEventTraceDetourStateV1 &state) noexcept {
  if (state.virtual_free != nullptr) {
    if (state.schedule_trampoline != nullptr) {
      (void)state.virtual_free(state.memory_context,
                               state.schedule_trampoline, 0, MEM_RELEASE);
    }
    if (state.fire_trampoline != nullptr) {
      (void)state.virtual_free(state.memory_context,
                               state.fire_trampoline, 0, MEM_RELEASE);
    }
  }
  state.schedule_trampoline = nullptr;
  state.fire_trampoline = nullptr;
}

bool ExactAnchorsMatch(
    const CombatPhaseEventTraceDetourEnvironmentV1 &environment,
    std::uintptr_t schedule_target, std::uintptr_t fire_target) noexcept {
  const auto module = environment.module_base;
  return BytesMatch(schedule_target, kSchedulePrologue) &&
         BytesMatch(fire_target, kFirePrologue) &&
         BytesMatch(Resolve(environment.schedule_side0_call_override, module,
                            0x27FB58F),
                    kScheduleSide0Call) &&
         BytesMatch(Resolve(environment.schedule_side1_call_override, module,
                            0x27FB5A7),
                    kScheduleSide1Call) &&
         BytesMatch(Resolve(environment.fire_side0_call_override, module,
                            0x2309EF2),
                    kFireSide0Call) &&
         BytesMatch(Resolve(environment.fire_side1_call_override, module,
                            0x2309EFA),
                    kFireSide1Call) &&
         BytesMatch(Resolve(environment.fire_tail_jump_override, module,
                            0x23CA34E),
                    kFireTailJump);
}

} // namespace

bool InstallCombatPhaseEventTraceDetoursV1(
    CombatPhaseEventTraceDetourStateV1 &state,
    const CombatPhaseEventTraceDetourEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(trace_detour_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, trace_detour_failure_exact_build);
    return false;
  }
  if (!environment.managed_paused_quiescence_proven) {
    AddFailure(state, trace_detour_failure_paused_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) {
    AddFailure(state, trace_detour_failure_already_installed);
    return false;
  }
  if (IsCombatPhaseEventTraceRingV1Armed()) {
    AddFailure(state, trace_detour_failure_capture_active);
    return false;
  }

  CombatPhaseEventTraceDetourStateV1 *expected_active = nullptr;
  if (!g_active_detours.compare_exchange_strong(
          expected_active, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(state, trace_detour_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.schedule_target = Resolve(environment.schedule_target_override,
                                  environment.module_base,
                                  kCombatPhaseEventScheduleFunctionRva);
  state.fire_target = Resolve(environment.fire_target_override,
                              environment.module_base,
                              kCombatPhaseEventFireFunctionRva);
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
                           ? environment.virtual_free_override
                           : &DefaultVirtualFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
                              ? environment.virtual_protect_override
                              : &DefaultVirtualProtect;
  state.flush_instruction_cache =
      environment.flush_instruction_cache_override != nullptr
          ? environment.flush_instruction_cache_override
          : &DefaultFlushInstructionCache;
  const auto virtual_alloc = environment.virtual_alloc_override != nullptr
                                 ? environment.virtual_alloc_override
                                 : &DefaultVirtualAlloc;

  if (!ExactAnchorsMatch(environment, state.schedule_target,
                         state.fire_target)) {
    AddFailure(state, trace_detour_failure_anchor);
    g_active_detours.store(nullptr, std::memory_order_release);
    return false;
  }
  std::memcpy(state.schedule_original.data(),
              reinterpret_cast<const void *>(state.schedule_target),
              state.schedule_original.size());
  std::memcpy(state.fire_original.data(),
              reinterpret_cast<const void *>(state.fire_target),
              state.fire_original.size());

  state.schedule_trampoline = virtual_alloc(
      state.memory_context, kCombatPhaseEventTraceTrampolineBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  state.fire_trampoline = virtual_alloc(
      state.memory_context, kCombatPhaseEventTraceTrampolineBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.schedule_trampoline == nullptr ||
      state.fire_trampoline == nullptr) {
    AddFailure(state, trace_detour_failure_allocation);
    FreeTrampolines(state);
    g_active_detours.store(nullptr, std::memory_order_release);
    return false;
  }
  if (!FillTrampoline(
          state.schedule_trampoline, state.schedule_original,
          state.schedule_target + kCombatPhaseEventTraceDetourPatchBytesV1) ||
      !FillTrampoline(
          state.fire_trampoline, state.fire_original,
          state.fire_target + kCombatPhaseEventTraceDetourPatchBytesV1) ||
      !MakeTrampolineExecutable(state, state.schedule_trampoline) ||
      !MakeTrampolineExecutable(state, state.fire_trampoline)) {
    FreeTrampolines(state);
    g_active_detours.store(nullptr, std::memory_order_release);
    return false;
  }

  if (!BindCombatPhaseEventTraceOriginalTrampolinesV1(
          reinterpret_cast<CombatPhaseEventScheduleOriginalV1>(
              state.schedule_trampoline),
          reinterpret_cast<CombatPhaseEventFireOriginalV1>(
              state.fire_trampoline))) {
    AddFailure(state, trace_detour_failure_original_binding);
    FreeTrampolines(state);
    g_active_detours.store(nullptr, std::memory_order_release);
    return false;
  }

  std::array<std::uint8_t, kCombatPhaseEventTraceDetourPatchBytesV1>
      schedule_patch{};
  std::array<std::uint8_t, kCombatPhaseEventTraceDetourPatchBytesV1>
      fire_patch{};
  WriteAbsoluteJump(schedule_patch.data(),
                    reinterpret_cast<std::uintptr_t>(
                        &XarCombatPhaseEventScheduleHookV1));
  WriteAbsoluteJump(fire_patch.data(),
                    reinterpret_cast<std::uintptr_t>(
                        &XarCombatPhaseEventFireHookV1));
  schedule_patch.back() = 0x90;
  fire_patch.back() = 0x90;

  const bool schedule_installed = WriteTargetBytes(
      state, state.schedule_target, state.schedule_original.data(),
      schedule_patch.data());
  const bool fire_installed =
      schedule_installed &&
      WriteTargetBytes(state, state.fire_target,
                       state.fire_original.data(), fire_patch.data());
  if (!schedule_installed || !fire_installed) {
    if (schedule_installed) {
      (void)RestoreTarget(state, state.schedule_target,
                          schedule_patch.data(),
                          state.schedule_original.data());
    }
    (void)BindCombatPhaseEventTraceOriginalTrampolinesV1(
        reinterpret_cast<CombatPhaseEventScheduleOriginalV1>(
            state.schedule_target),
        reinterpret_cast<CombatPhaseEventFireOriginalV1>(
            state.fire_target));
    FreeTrampolines(state);
    g_active_detours.store(nullptr, std::memory_order_release);
    return false;
  }

  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallCombatPhaseEventTraceDetoursV1(
    CombatPhaseEventTraceDetourStateV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_detours.load(std::memory_order_acquire) != &state) {
    return false;
  }
  if (IsCombatPhaseEventTraceRingV1Armed()) {
    AddFailure(state, trace_detour_failure_capture_active);
    return false;
  }
  if (state.schedule_target == 0 || state.fire_target == 0 ||
      state.schedule_trampoline == nullptr ||
      state.fire_trampoline == nullptr) {
    AddFailure(state, trace_detour_failure_target_identity);
    return false;
  }

  std::array<std::uint8_t, kCombatPhaseEventTraceDetourPatchBytesV1>
      schedule_patch{};
  std::array<std::uint8_t, kCombatPhaseEventTraceDetourPatchBytesV1>
      fire_patch{};
  WriteAbsoluteJump(schedule_patch.data(),
                    reinterpret_cast<std::uintptr_t>(
                        &XarCombatPhaseEventScheduleHookV1));
  WriteAbsoluteJump(fire_patch.data(),
                    reinterpret_cast<std::uintptr_t>(
                        &XarCombatPhaseEventFireHookV1));
  schedule_patch.back() = 0x90;
  fire_patch.back() = 0x90;

  // Restore both entrypoints before invalidating either trampoline.  A failed
  // restore deliberately leaves the installation owned and the trampolines
  // alive; the caller may retry from another verified paused pump.
  if (!RestoreTarget(state, state.fire_target, fire_patch.data(),
                     state.fire_original.data())) {
    return false;
  }
  if (!RestoreTarget(state, state.schedule_target,
                     schedule_patch.data(),
                     state.schedule_original.data())) {
    // Keep the pair transactional: if schedule restoration fails after fire
    // was restored, put fire back on the hook before returning ownership to
    // the caller.  A later verified paused pump can retry uninstallation.
    if (!WriteTargetBytes(state, state.fire_target,
                          state.fire_original.data(), fire_patch.data())) {
      AddFailure(state, trace_detour_failure_rollback);
    }
    return false;
  }
  if (!BindCombatPhaseEventTraceOriginalTrampolinesV1(
          reinterpret_cast<CombatPhaseEventScheduleOriginalV1>(
              state.schedule_target),
          reinterpret_cast<CombatPhaseEventFireOriginalV1>(
              state.fire_target))) {
    AddFailure(state, trace_detour_failure_original_binding);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active_detours.store(nullptr, std::memory_order_release);
  FreeTrampolines(state);
  return true;
}

} // namespace xar::ck3_11906
