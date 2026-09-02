#include "xar_bridge/g2_truce_native_callsite_observer_v1.hpp"

#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "G2 truce native callsite observer is x64-only");

std::atomic<G2TruceNativeCallsiteObserverV1State *> g_active_observer{nullptr};

constexpr std::array<std::uint8_t, 19> kCallsite0Anchor{
    0x48, 0x8D, 0x8E, 0x08, 0x01, 0x00, 0x00,
    0x4D, 0x8B, 0x47, 0x28,
    0x49, 0x8B, 0xD7,
    0xE8, 0xEC, 0x80, 0x49, 0x00};
constexpr std::array<std::uint8_t, 20> kCallsite1Anchor{
    0x48, 0x8D, 0x8E, 0x08, 0x01, 0x00, 0x00,
    0x4D, 0x8B, 0x44, 0x24, 0x28,
    0x49, 0x8B, 0xD4,
    0xE8, 0x5D, 0x7A, 0x49, 0x00};

void AddFailure(G2TruceNativeCallsiteObserverV1State &state,
                G2TruceNativeCallsiteObserverFailureV1 failure) noexcept {
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
  return VirtualProtect(address, size, new_protection, &old_protection) != FALSE;
}

bool DefaultFlushInstructionCache(void *, const void *address,
                                  std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool AddRva(std::uintptr_t base, std::uintptr_t rva,
            std::uintptr_t &output) noexcept {
  if (base == 0 || rva > std::numeric_limits<std::uintptr_t>::max() - base) {
    output = 0;
    return false;
  }
  output = base + rva;
  return true;
}

std::uintptr_t Resolve(std::uintptr_t override_address,
                       std::uintptr_t module_base,
                       std::uintptr_t rva) noexcept {
  if (override_address != 0) return override_address;
  std::uintptr_t output = 0;
  (void)AddRva(module_base, rva, output);
  return output;
}

bool SafeBytesEqual(std::uintptr_t address, const std::uint8_t *expected,
                    std::size_t size) noexcept {
  if (address == 0 || expected == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(address), expected,
                       size) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool SafeCopyFrom(std::uintptr_t address, std::uint8_t *output,
                  std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(output, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool SafeCopyTo(std::uintptr_t address, const std::uint8_t *source,
                std::size_t size) noexcept {
  if (address == 0 || source == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(reinterpret_cast<void *>(address), source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#endif
}

bool IsExecutableProtection(DWORD protection) noexcept {
  return protection == PAGE_EXECUTE_READ ||
      protection == PAGE_EXECUTE_READWRITE ||
      protection == PAGE_EXECUTE_WRITECOPY;
}

template <std::size_t Size>
void Emit(std::array<std::uint8_t, Size> &output, std::size_t &cursor,
          std::initializer_list<std::uint8_t> bytes) noexcept {
  for (const auto byte : bytes) output[cursor++] = byte;
}

template <std::size_t Size>
void EmitU32(std::array<std::uint8_t, Size> &output, std::size_t &cursor,
             std::uint32_t value) noexcept {
  std::memcpy(output.data() + cursor, &value, sizeof(value));
  cursor += sizeof(value);
}

template <std::size_t Size>
void EmitU64(std::array<std::uint8_t, Size> &output, std::size_t &cursor,
             std::uintptr_t value) noexcept {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(output.data() + cursor, &encoded, sizeof(encoded));
  cursor += sizeof(encoded);
}

template <std::size_t Size>
void EmitAbsoluteJump(std::array<std::uint8_t, Size> &output,
                      std::size_t &cursor, std::uintptr_t target) noexcept {
  Emit(output, cursor, {0xFF, 0x25, 0x00, 0x00, 0x00, 0x00});
  EmitU64(output, cursor, target);
}

template <std::size_t Size>
void EmitRelocatedNativeCall(std::array<std::uint8_t, Size> &output,
                             std::size_t &cursor,
                             std::uintptr_t target) noexcept {
  // call qword ptr [rip+2]; jmp short +8; dq target.  Unlike mov rax/call rax,
  // this preserves the original callsite's incoming RAX value.
  Emit(output, cursor, {0xFF, 0x15, 0x02, 0x00, 0x00, 0x00, 0xEB, 0x08});
  EmitU64(output, cursor, target);
}

template <std::size_t Size>
void EmitPreserveVolatile(std::array<std::uint8_t, Size> &output,
                          std::size_t &cursor) noexcept {
  Emit(output, cursor,
       {0x9C, 0x50, 0x51, 0x52, 0x41, 0x50,
        0x41, 0x51, 0x41, 0x52, 0x41, 0x53});
  Emit(output, cursor, {0x48, 0x83, 0xEC, 0x20});
}

template <std::size_t Size>
void EmitRestoreVolatile(std::array<std::uint8_t, Size> &output,
                         std::size_t &cursor) noexcept {
  Emit(output, cursor, {0x48, 0x83, 0xC4, 0x20});
  Emit(output, cursor,
       {0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
        0x41, 0x58, 0x5A, 0x59, 0x58, 0x9D});
}

extern "C" void G2TruceNativeCallsitePreThunkV1(
    std::uint32_t site_index, std::uintptr_t script_value,
    std::uintptr_t effect_context, std::uintptr_t evaluation_context) noexcept {
  auto *state = g_active_observer.load(std::memory_order_acquire);
  if (state == nullptr) return;
  LARGE_INTEGER timestamp{};
  (void)QueryPerformanceCounter(&timestamp);
  RecordG2TruceNativeCallsitePreV1(
      *state, site_index, script_value, effect_context, evaluation_context,
      GetCurrentThreadId(), static_cast<std::uint64_t>(timestamp.QuadPart));
}

extern "C" void G2TruceNativeCallsitePostThunkV1(
    std::uint32_t site_index, std::int32_t return_eax) noexcept {
  auto *state = g_active_observer.load(std::memory_order_acquire);
  if (state == nullptr) return;
  LARGE_INTEGER timestamp{};
  (void)QueryPerformanceCounter(&timestamp);
  RecordG2TruceNativeCallsitePostV1(
      *state, site_index, return_eax, GetCurrentThreadId(),
      static_cast<std::uint64_t>(timestamp.QuadPart));
}

bool BuildStub(
    G2TruceNativeCallsiteObserverV1State &state, std::size_t site_index,
    std::array<std::uint8_t, kG2TruceNativeCallsiteStubCapacityV1>
        &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  if (site_index == 0) {
    for (std::size_t index = 0; index < kCallsite0Anchor.size() - 5; ++index) {
      stub[cursor++] = kCallsite0Anchor[index];
    }
  } else if (site_index == 1) {
    for (std::size_t index = 0; index < kCallsite1Anchor.size() - 5; ++index) {
      stub[cursor++] = kCallsite1Anchor[index];
    }
  } else {
    return false;
  }

  EmitPreserveVolatile(stub, cursor);
  Emit(stub, cursor, {0x4D, 0x8B, 0xC8}); // mov r9,r8
  Emit(stub, cursor, {0x4C, 0x8B, 0xC2}); // mov r8,rdx
  Emit(stub, cursor, {0x48, 0x8B, 0xD1}); // mov rdx,rcx
  Emit(stub, cursor, {0xB9});             // mov ecx,site_index
  EmitU32(stub, cursor, static_cast<std::uint32_t>(site_index));
  Emit(stub, cursor, {0x48, 0xB8});
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&G2TruceNativeCallsitePreThunkV1));
  Emit(stub, cursor, {0xFF, 0xD0});
  EmitRestoreVolatile(stub, cursor);

  // This is the relocated original native direct call covered by the exact
  // anchor.  The observer never submits a separate evaluator request.
  EmitRelocatedNativeCall(stub, cursor, state.evaluator_target);

  EmitPreserveVolatile(stub, cursor);
  Emit(stub, cursor, {0x8B, 0x54, 0x24, 0x50}); // mov edx,[rsp+0x50]
  Emit(stub, cursor, {0xB9});                    // mov ecx,site_index
  EmitU32(stub, cursor, static_cast<std::uint32_t>(site_index));
  Emit(stub, cursor, {0x48, 0xB8});
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&G2TruceNativeCallsitePostThunkV1));
  Emit(stub, cursor, {0xFF, 0xD0});
  EmitRestoreVolatile(stub, cursor);
  EmitAbsoluteJump(stub, cursor, state.continue_targets[site_index]);
  return cursor <= stub.size();
}

void BuildPatch(
    std::uintptr_t stub_address, std::size_t site_index,
    std::array<std::uint8_t, kG2TruceNativeCallsiteMaxPatchBytesV1>
        &patch) noexcept {
  patch.fill(0x90);
  std::size_t cursor = 0;
  EmitAbsoluteJump(patch, cursor, stub_address);
  while (cursor < kG2TruceNativeCallsitePatchSizesV1[site_index]) {
    patch[cursor++] = 0x90;
  }
}

bool HasUnsupportedProductionOverride(
    const G2TruceNativeCallsiteObserverV1Environment &environment) noexcept {
  for (const auto value : environment.patch_target_overrides) {
    if (value != 0) return true;
  }
  for (const auto value : environment.continue_target_overrides) {
    if (value != 0) return true;
  }
  return environment.evaluator_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

bool Flush(G2TruceNativeCallsiteObserverV1State &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, g2_truce_native_callsite_observer_failure_flush);
    return false;
  }
  return true;
}

enum class TargetWriteResult { success, original_preserved, rollback_unproven };

TargetWriteResult WriteTarget(
    G2TruceNativeCallsiteObserverV1State &state, std::size_t site_index,
    const std::uint8_t *expected, const std::uint8_t *desired) noexcept {
  const auto target = state.patch_targets[site_index];
  const auto size = kG2TruceNativeCallsitePatchSizesV1[site_index];
  if (!SafeBytesEqual(target, expected, size)) {
    AddFailure(state, g2_truce_native_callsite_observer_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(target), size,
                            PAGE_EXECUTE_READWRITE, previous);
  if (!writable || !IsExecutableProtection(previous)) {
    if (writable) {
      DWORD ignored = 0;
      (void)state.virtual_protect(state.memory_context,
                                  reinterpret_cast<void *>(target), size,
                                  previous, ignored);
    }
    AddFailure(state,
               g2_truce_native_callsite_observer_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  const bool wrote = SafeCopyTo(target, desired, size);
  const bool identity = wrote && SafeBytesEqual(target, desired, size);
  const bool flushed = identity &&
      Flush(state, reinterpret_cast<const void *>(target), size);
  DWORD ignored = 0;
  const bool protected_again = flushed && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(target), size, previous,
      ignored);
  if (identity && flushed && protected_again) return TargetWriteResult::success;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(target), size,
                            PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable &&
      SafeCopyTo(target, expected, size);
  const bool rollback_identity = rollback_written &&
      SafeBytesEqual(target, expected, size);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context, reinterpret_cast<const void *>(target), size);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(target), size, previous,
      rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state, g2_truce_native_callsite_observer_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::original_preserved;
}

bool ReleaseStubs(G2TruceNativeCallsiteObserverV1State &state) noexcept {
  bool result = true;
  for (auto &stub : state.stubs) {
    if (stub == nullptr) continue;
    if (state.virtual_free == nullptr ||
        !state.virtual_free(state.memory_context, stub, 0, MEM_RELEASE)) {
      AddFailure(state, g2_truce_native_callsite_observer_failure_rollback);
      result = false;
      continue;
    }
    stub = nullptr;
  }
  return result;
}

void ClearResolved(G2TruceNativeCallsiteObserverV1State &state) noexcept {
  state.module_base = 0;
  state.evaluator_target = 0;
  state.patch_targets.fill(0);
  state.continue_targets.fill(0);
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

const std::uint8_t *Anchor(std::size_t site_index) noexcept {
  return site_index == 0 ? kCallsite0Anchor.data() : kCallsite1Anchor.data();
}

} // namespace

void RecordG2TruceNativeCallsitePreV1(
    G2TruceNativeCallsiteObserverV1State &state, std::uint32_t site_index,
    std::uintptr_t script_value, std::uintptr_t effect_context,
    std::uintptr_t evaluation_context, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept {
  if (site_index >= state.observations.size()) return;
  auto &row = state.observations[site_index];
  row.last_script_value.store(script_value, std::memory_order_relaxed);
  row.last_effect_context.store(effect_context, std::memory_order_relaxed);
  row.last_evaluation_context.store(evaluation_context,
                                    std::memory_order_relaxed);
  row.last_pre_thread_id.store(thread_id, std::memory_order_relaxed);
  row.last_pre_timestamp_qpc.store(timestamp_qpc, std::memory_order_relaxed);
  row.pre_call_count.fetch_add(1, std::memory_order_release);
}

void RecordG2TruceNativeCallsitePostV1(
    G2TruceNativeCallsiteObserverV1State &state, std::uint32_t site_index,
    std::int32_t return_eax, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept {
  if (site_index >= state.observations.size()) return;
  auto &row = state.observations[site_index];
  row.last_return_eax.store(return_eax, std::memory_order_relaxed);
  row.last_post_thread_id.store(thread_id, std::memory_order_relaxed);
  row.last_post_timestamp_qpc.store(timestamp_qpc, std::memory_order_relaxed);
  row.post_call_count.fetch_add(1, std::memory_order_release);
}

bool InstallG2TruceNativeCallsiteObserverV1(
    G2TruceNativeCallsiteObserverV1State &state,
    const G2TruceNativeCallsiteObserverV1Environment &environment) noexcept {
  state.failure_flags.store(g2_truce_native_callsite_observer_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, g2_truce_native_callsite_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        g2_truce_native_callsite_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture &&
      HasUnsupportedProductionOverride(environment)) {
    AddFailure(state,
               g2_truce_native_callsite_observer_failure_unsupported_override);
    return false;
  }
  if (state.installed_mask.load(std::memory_order_acquire) != 0) {
    AddFailure(state,
               g2_truce_native_callsite_observer_failure_already_installed);
    return false;
  }
  G2TruceNativeCallsiteObserverV1State *expected = nullptr;
  if (!g_active_observer.compare_exchange_strong(
          expected, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(state,
               g2_truce_native_callsite_observer_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.evaluator_target = Resolve(environment.evaluator_target_override,
                                   state.module_base, kG2TruceEvaluatorRvaV1);
  for (std::size_t index = 0; index < kG2TruceNativeCallsiteCountV1; ++index) {
    state.patch_targets[index] = Resolve(
        environment.patch_target_overrides[index], state.module_base,
        kG2TruceNativeCallsitePatchRvasV1[index]);
    state.continue_targets[index] = Resolve(
        environment.continue_target_overrides[index], state.module_base,
        kG2TruceNativeCallsiteContinueRvasV1[index]);
  }
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

  bool anchors_ok = state.evaluator_target != 0;
  for (std::size_t index = 0; index < kG2TruceNativeCallsiteCountV1; ++index) {
    const auto size = kG2TruceNativeCallsitePatchSizesV1[index];
    anchors_ok = anchors_ok && state.patch_targets[index] != 0 &&
        state.continue_targets[index] == state.patch_targets[index] + size &&
        SafeBytesEqual(state.patch_targets[index], Anchor(index), size) &&
        SafeCopyFrom(state.patch_targets[index],
                     state.original_patch_bytes[index].data(), size);
  }
  if (!anchors_ok) {
    AddFailure(state, g2_truce_native_callsite_observer_failure_anchor);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }

  for (auto &row : state.observations) {
    row.pre_call_count.store(0, std::memory_order_relaxed);
    row.post_call_count.store(0, std::memory_order_relaxed);
    row.last_script_value.store(0, std::memory_order_relaxed);
    row.last_effect_context.store(0, std::memory_order_relaxed);
    row.last_evaluation_context.store(0, std::memory_order_relaxed);
    row.last_pre_thread_id.store(0, std::memory_order_relaxed);
    row.last_pre_timestamp_qpc.store(0, std::memory_order_relaxed);
    row.last_return_eax.store(0, std::memory_order_relaxed);
    row.last_post_thread_id.store(0, std::memory_order_relaxed);
    row.last_post_timestamp_qpc.store(0, std::memory_order_relaxed);
  }

  for (std::size_t index = 0; index < kG2TruceNativeCallsiteCountV1; ++index) {
    state.stubs[index] = virtual_alloc(
        state.memory_context, kG2TruceNativeCallsiteStubCapacityV1,
        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (state.stubs[index] == nullptr) {
      AddFailure(state, g2_truce_native_callsite_observer_failure_allocation);
      (void)ReleaseStubs(state);
      ClearResolved(state);
      g_active_observer.store(nullptr, std::memory_order_release);
      return false;
    }
    std::array<std::uint8_t, kG2TruceNativeCallsiteStubCapacityV1> stub{};
    if (!BuildStub(state, index, stub) ||
        !SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stubs[index]),
                    stub.data(), stub.size())) {
      AddFailure(state, g2_truce_native_callsite_observer_failure_allocation);
      (void)ReleaseStubs(state);
      ClearResolved(state);
      g_active_observer.store(nullptr, std::memory_order_release);
      return false;
    }
    DWORD previous = 0;
    const bool protected_stub = state.virtual_protect(
        state.memory_context, state.stubs[index], stub.size(),
        PAGE_EXECUTE_READ, previous);
    const bool flushed_stub = protected_stub &&
        Flush(state, state.stubs[index], stub.size());
    if (!protected_stub || previous != PAGE_READWRITE || !flushed_stub) {
      AddFailure(
          state, g2_truce_native_callsite_observer_failure_stub_protection);
      (void)ReleaseStubs(state);
      ClearResolved(state);
      g_active_observer.store(nullptr, std::memory_order_release);
      return false;
    }
    BuildPatch(reinterpret_cast<std::uintptr_t>(state.stubs[index]), index,
               state.installed_patch_bytes[index]);
  }

  std::uint32_t installed_mask = 0;
  for (std::size_t index = 0; index < kG2TruceNativeCallsiteCountV1; ++index) {
    const auto write = WriteTarget(
        state, index, state.original_patch_bytes[index].data(),
        state.installed_patch_bytes[index].data());
    if (write == TargetWriteResult::success) {
      installed_mask |= (1U << index);
      continue;
    }
    if (write == TargetWriteResult::rollback_unproven) {
      // The current target may still contain all or part of the detour.  Keep
      // its ownership bit so diagnostics never misreport an uncertain site as
      // restored.
      installed_mask |= (1U << index);
    }
    bool rollback_ok = write != TargetWriteResult::rollback_unproven;
    for (std::size_t prior = index; prior-- > 0;) {
      if ((installed_mask & (1U << prior)) == 0) continue;
      const auto rollback = WriteTarget(
          state, prior, state.installed_patch_bytes[prior].data(),
          state.original_patch_bytes[prior].data());
      if (rollback == TargetWriteResult::success) {
        installed_mask &= ~(1U << prior);
      } else {
        rollback_ok = false;
      }
    }
    if (!rollback_ok || installed_mask != 0) {
      AddFailure(state, g2_truce_native_callsite_observer_failure_rollback);
      state.installed_mask.store(installed_mask, std::memory_order_release);
      return false;
    }
    (void)ReleaseStubs(state);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }

  state.installed_mask.store(installed_mask, std::memory_order_release);
  return installed_mask == 0x3U;
}

bool UninstallG2TruceNativeCallsiteObserverV1(
    G2TruceNativeCallsiteObserverV1State &state) noexcept {
  std::uint32_t installed_mask =
      state.installed_mask.load(std::memory_order_acquire);
  if (installed_mask == 0 ||
      g_active_observer.load(std::memory_order_acquire) != &state) {
    AddFailure(state,
               g2_truce_native_callsite_observer_failure_already_installed);
    return false;
  }
  for (std::size_t index = kG2TruceNativeCallsiteCountV1; index-- > 0;) {
    if ((installed_mask & (1U << index)) == 0) continue;
    const auto write = WriteTarget(
        state, index, state.installed_patch_bytes[index].data(),
        state.original_patch_bytes[index].data());
    if (write != TargetWriteResult::success) {
      AddFailure(state, g2_truce_native_callsite_observer_failure_rollback);
      state.installed_mask.store(installed_mask, std::memory_order_release);
      return false;
    }
    installed_mask &= ~(1U << index);
    state.installed_mask.store(installed_mask, std::memory_order_release);
  }
  g_active_observer.store(nullptr, std::memory_order_release);
  const bool released = ReleaseStubs(state);
  if (released) ClearResolved(state);
  return released;
}

G2TruceNativeCallsiteObserverV1Diagnostics
ReadG2TruceNativeCallsiteObserverV1Diagnostics(
    const G2TruceNativeCallsiteObserverV1State &state) noexcept {
  G2TruceNativeCallsiteObserverV1Diagnostics output{};
  output.installed_mask =
      state.installed_mask.load(std::memory_order_acquire);
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  for (std::size_t index = 0; index < output.callsites.size(); ++index) {
    const auto &source = state.observations[index];
    auto &target = output.callsites[index];
    target.pre_call_count =
        source.pre_call_count.load(std::memory_order_acquire);
    target.post_call_count =
        source.post_call_count.load(std::memory_order_acquire);
    target.last_script_value =
        source.last_script_value.load(std::memory_order_relaxed);
    target.last_effect_context =
        source.last_effect_context.load(std::memory_order_relaxed);
    target.last_evaluation_context =
        source.last_evaluation_context.load(std::memory_order_relaxed);
    target.last_pre_thread_id =
        source.last_pre_thread_id.load(std::memory_order_relaxed);
    target.last_pre_timestamp_qpc =
        source.last_pre_timestamp_qpc.load(std::memory_order_relaxed);
    target.last_return_eax =
        source.last_return_eax.load(std::memory_order_relaxed);
    target.last_post_thread_id =
        source.last_post_thread_id.load(std::memory_order_relaxed);
    target.last_post_timestamp_qpc =
        source.last_post_timestamp_qpc.load(std::memory_order_relaxed);
  }
  return output;
}

} // namespace xar::bridge
