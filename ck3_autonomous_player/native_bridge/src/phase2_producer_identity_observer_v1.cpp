#include "xar_bridge/phase2_producer_identity_observer_v1.hpp"

#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8, "phase2 producer identity observer is x64-only");
static_assert(sizeof(std::atomic<std::uint64_t>) == sizeof(std::uint64_t));

std::atomic<Phase2ProducerIdentityStateV1 *> g_active_observer{nullptr};

constexpr std::array<std::uint8_t, kPhase2ProducerIdentityPatchBytesV1>
    kPatchAnchor{0xB8, 0x02, 0x00, 0x00, 0x00, 0x87, 0x43, 0x60,
                 0xE8, 0x61, 0x70, 0x28, 0x00, 0x48, 0x8B, 0xF8};

void AddFailure(Phase2ProducerIdentityStateV1 &state,
                Phase2ProducerIdentityFailureV1 failure) noexcept {
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

bool SafeReadU64(std::uintptr_t address, std::uint64_t &output) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&output, reinterpret_cast<const void *>(address),
                sizeof(output));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = 0;
    return false;
  }
#endif
}

bool SafeReadU32(std::uintptr_t address, std::uint32_t &output) noexcept {
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&output, reinterpret_cast<const void *>(address),
                sizeof(output));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = 0;
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

extern "C" void Phase2ProducerIdentityThunkV1(
    std::uintptr_t task, std::uint32_t stage) noexcept {
  auto *state = g_active_observer.load(std::memory_order_acquire);
  if (state == nullptr) return;
  LARGE_INTEGER timestamp{};
  (void)QueryPerformanceCounter(&timestamp);
  RecordPhase2ProducerIdentityObservationV1(
      *state, task, stage, GetCurrentThreadId(),
      static_cast<std::uint64_t>(timestamp.QuadPart));
}

bool BuildStub(Phase2ProducerIdentityStateV1 &state,
               std::array<std::uint8_t,
                          kPhase2ProducerIdentityStubBytesV1> &stub) noexcept {
  std::size_t cursor = 0;
  const auto emit_observation = [&](std::uint32_t stage) {
    Emit(stub, cursor,
         {0x51, 0x52, 0x41, 0x50, 0x41, 0x51,
          0x41, 0x52, 0x41, 0x53});              // save volatile GPRs
    Emit(stub, cursor, {0x48, 0x83, 0xEC, 0x20}); // shadow space
    Emit(stub, cursor, {0xBA});                    // mov edx, stage
    std::memcpy(stub.data() + cursor, &stage, sizeof(stage));
    cursor += sizeof(stage);
    Emit(stub, cursor, {0x48, 0x8B, 0xCB});       // mov rcx, rbx
    Emit(stub, cursor, {0x48, 0xB8});             // mov rax, thunk
    EmitU64(stub, cursor,
            reinterpret_cast<std::uintptr_t>(&Phase2ProducerIdentityThunkV1));
    Emit(stub, cursor, {0xFF, 0xD0});
    Emit(stub, cursor, {0x48, 0x83, 0xC4, 0x20});
    Emit(stub, cursor,
         {0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
          0x41, 0x58, 0x5A, 0x59});              // restore volatile GPRs
  };
  emit_observation(0);                            // logical 0x3B9CFD2
  Emit(stub, cursor, {0xB8, 0x02, 0x00, 0x00, 0x00}); // mov eax, 2
  Emit(stub, cursor, {0x87, 0x43, 0x60});              // xchg [rbx+60], eax
  emit_observation(1);                            // logical 0x3B9CFD7
  Emit(stub, cursor, {0x48, 0xB8});               // original relative call
  EmitU64(stub, cursor, state.original_call_target);
  Emit(stub, cursor, {0xFF, 0xD0});
  Emit(stub, cursor, {0x48, 0x8B, 0xF8});        // mov rdi, rax
  EmitAbsoluteJump(stub, cursor, state.continue_target);
  return cursor == stub.size();
}

void BuildPatch(std::uintptr_t stub_address,
                std::array<std::uint8_t,
                           kPhase2ProducerIdentityPatchBytesV1> &patch) {
  std::size_t cursor = 0;
  EmitAbsoluteJump(patch, cursor, stub_address);
  while (cursor < patch.size()) patch[cursor++] = 0x90;
}

bool HasUnsupportedProductionOverride(
    const Phase2ProducerIdentityEnvironmentV1 &environment) noexcept {
  return environment.patch_target_override != 0 ||
      environment.continue_target_override != 0 ||
      environment.original_call_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

bool Flush(Phase2ProducerIdentityStateV1 &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, phase2_producer_identity_failure_flush);
    return false;
  }
  return true;
}

enum class TargetWriteResult { success, original_preserved, rollback_unproven };

TargetWriteResult WriteTarget(
    Phase2ProducerIdentityStateV1 &state, const std::uint8_t *expected,
    const std::uint8_t *desired) noexcept {
  if (!SafeBytesEqual(state.patch_target, expected,
                      kPhase2ProducerIdentityPatchBytesV1)) {
    AddFailure(state, phase2_producer_identity_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(state.patch_target),
                            kPhase2ProducerIdentityPatchBytesV1,
                            PAGE_EXECUTE_READWRITE, previous);
  if (!writable) {
    AddFailure(state, phase2_producer_identity_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  if (!IsExecutableProtection(previous)) {
    DWORD ignored = 0;
    (void)state.virtual_protect(
        state.memory_context, reinterpret_cast<void *>(state.patch_target),
        kPhase2ProducerIdentityPatchBytesV1, previous, ignored);
    AddFailure(state, phase2_producer_identity_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  const bool wrote = SafeCopyTo(state.patch_target, desired,
                                kPhase2ProducerIdentityPatchBytesV1);
  const bool identity = wrote && SafeBytesEqual(
      state.patch_target, desired, kPhase2ProducerIdentityPatchBytesV1);
  const bool flushed = identity && Flush(
      state, reinterpret_cast<const void *>(state.patch_target),
      kPhase2ProducerIdentityPatchBytesV1);
  DWORD ignored = 0;
  const bool protected_again = flushed && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kPhase2ProducerIdentityPatchBytesV1, previous, ignored);
  if (identity && flushed && protected_again) return TargetWriteResult::success;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(state.patch_target),
                            kPhase2ProducerIdentityPatchBytesV1,
                            PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable && SafeCopyTo(
      state.patch_target, expected, kPhase2ProducerIdentityPatchBytesV1);
  const bool rollback_identity = rollback_written && SafeBytesEqual(
      state.patch_target, expected, kPhase2ProducerIdentityPatchBytesV1);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context,
          reinterpret_cast<const void *>(state.patch_target),
          kPhase2ProducerIdentityPatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(state.patch_target),
                            kPhase2ProducerIdentityPatchBytesV1, previous,
                            rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state, phase2_producer_identity_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::original_preserved;
}

bool ReleaseStub(Phase2ProducerIdentityStateV1 &state) noexcept {
  if (state.stub == nullptr) return true;
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE)) {
    AddFailure(state, phase2_producer_identity_failure_rollback);
    return false;
  }
  state.stub = nullptr;
  return true;
}

void ClearResolved(Phase2ProducerIdentityStateV1 &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.continue_target = 0;
  state.original_call_target = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

} // namespace

void RecordPhase2ProducerIdentityObservationV1(
    Phase2ProducerIdentityStateV1 &state, std::uintptr_t task,
    std::uint32_t stage, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept {
  if (stage > 1) return;
  if (stage == 0) {
    state.producer_0x3B9CFD2_entry_count.fetch_add(1,
                                                   std::memory_order_relaxed);
  } else {
    state.producer_0x3B9CFD7_entry_count.fetch_add(1,
                                                   std::memory_order_relaxed);
  }
  std::uint64_t callback = 0;
  std::uint64_t vtable = 0;
  std::uint64_t slot2_target = 0;
  std::uint64_t owner = 0;
  std::uint32_t observed_state = 0;
  const bool callback_read = SafeReadU64(task + 0x38, callback);
  const bool vtable_read = callback_read && callback != 0 &&
      SafeReadU64(static_cast<std::uintptr_t>(callback), vtable);
  const bool slot2_read = vtable_read && vtable != 0 &&
      SafeReadU64(static_cast<std::uintptr_t>(vtable) + 0x10, slot2_target);
  const bool owner_read = SafeReadU64(task + 0x58, owner);
  const bool state_read = SafeReadU32(task + 0x60, observed_state);
  state.last_task_pointer.store(task, std::memory_order_relaxed);
  state.last_callback_pointer.store(callback, std::memory_order_relaxed);
  state.last_callback_vptr.store(vtable, std::memory_order_relaxed);
  state.last_callback_slot2.store(slot2_target, std::memory_order_relaxed);
  state.last_callback_slot2_rva.store(
      slot2_target >= state.module_base ? slot2_target - state.module_base : 0,
      std::memory_order_relaxed);
  state.last_owner_pointer.store(owner, std::memory_order_relaxed);
  if (stage == 0) {
    state.last_state_before_publish.store(observed_state,
                                           std::memory_order_relaxed);
  } else {
    state.last_state_after_publish.store(observed_state,
                                          std::memory_order_relaxed);
  }
  state.last_thread_id.store(thread_id, std::memory_order_relaxed);
  state.last_timestamp_qpc.store(timestamp_qpc, std::memory_order_relaxed);
  const std::uint64_t failures = (!callback_read ? 1U : 0U) +
      (!vtable_read ? 1U : 0U) + (!slot2_read ? 1U : 0U) +
      (!owner_read ? 1U : 0U) + (!state_read ? 1U : 0U);
  if (failures != 0) {
    state.read_failure_count.fetch_add(failures, std::memory_order_relaxed);
  }
}

bool InstallPhase2ProducerIdentityObserverV1(
    Phase2ProducerIdentityStateV1 &state,
    const Phase2ProducerIdentityEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(phase2_producer_identity_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, phase2_producer_identity_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(state,
               phase2_producer_identity_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture &&
      HasUnsupportedProductionOverride(environment)) {
    AddFailure(state, phase2_producer_identity_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.stub != nullptr) {
    AddFailure(state, phase2_producer_identity_failure_already_installed);
    return false;
  }
  Phase2ProducerIdentityStateV1 *expected = nullptr;
  if (!g_active_observer.compare_exchange_strong(
          expected, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(state, phase2_producer_identity_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.patch_target = Resolve(environment.patch_target_override,
                               state.module_base,
                               kPhase2ProducerIdentityPreRvaV1);
  state.continue_target = Resolve(environment.continue_target_override,
                                  state.module_base,
                                  kPhase2ProducerIdentityContinueRvaV1);
  state.original_call_target = Resolve(environment.original_call_target_override,
                                state.module_base,
                                kPhase2ProducerIdentityOriginalCallRvaV1);
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
  if (state.patch_target == 0 || state.continue_target == 0 ||
      state.original_call_target == 0 ||
      state.continue_target !=
          state.patch_target + kPhase2ProducerIdentityPatchBytesV1 ||
      !SafeBytesEqual(state.patch_target, kPatchAnchor.data(),
                      kPatchAnchor.size()) ||
      !SafeCopyFrom(state.patch_target, state.original_patch_bytes.data(),
                    state.original_patch_bytes.size())) {
    AddFailure(state, phase2_producer_identity_failure_anchor);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }

  state.producer_0x3B9CFD2_entry_count.store(0, std::memory_order_relaxed);
  state.producer_0x3B9CFD7_entry_count.store(0, std::memory_order_relaxed);
  state.read_failure_count.store(0, std::memory_order_relaxed);
  state.last_task_pointer.store(0, std::memory_order_relaxed);
  state.last_callback_pointer.store(0, std::memory_order_relaxed);
  state.last_callback_vptr.store(0, std::memory_order_relaxed);
  state.last_callback_slot2.store(0, std::memory_order_relaxed);
  state.last_callback_slot2_rva.store(0, std::memory_order_relaxed);
  state.last_owner_pointer.store(0, std::memory_order_relaxed);
  state.last_state_before_publish.store(0, std::memory_order_relaxed);
  state.last_state_after_publish.store(0, std::memory_order_relaxed);
  state.last_thread_id.store(0, std::memory_order_relaxed);
  state.last_timestamp_qpc.store(0, std::memory_order_relaxed);
  state.stub = virtual_alloc(state.memory_context,
                             kPhase2ProducerIdentityStubBytesV1,
                             MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state, phase2_producer_identity_failure_allocation);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  std::array<std::uint8_t, kPhase2ProducerIdentityStubBytesV1> stub{};
  if (!BuildStub(state, stub) ||
      !SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stub), stub.data(),
                  stub.size())) {
    AddFailure(state, phase2_producer_identity_failure_allocation);
    (void)ReleaseStub(state);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  DWORD previous = 0;
  const bool protected_stub = state.virtual_protect(
      state.memory_context, state.stub, stub.size(), PAGE_EXECUTE_READ,
      previous);
  const bool flushed_stub = protected_stub && Flush(state, state.stub,
                                                     stub.size());
  if (!protected_stub || previous != PAGE_READWRITE || !flushed_stub) {
    AddFailure(state, phase2_producer_identity_failure_stub_protection);
    (void)ReleaseStub(state);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  BuildPatch(reinterpret_cast<std::uintptr_t>(state.stub),
             state.installed_patch_bytes);
  const auto write = WriteTarget(state, state.original_patch_bytes.data(),
                                 state.installed_patch_bytes.data());
  if (write != TargetWriteResult::success) {
    if (write == TargetWriteResult::original_preserved) {
      (void)ReleaseStub(state);
      ClearResolved(state);
      g_active_observer.store(nullptr, std::memory_order_release);
    } else {
      state.installed.store(1, std::memory_order_release);
    }
    return false;
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallPhase2ProducerIdentityObserverV1(
    Phase2ProducerIdentityStateV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_observer.load(std::memory_order_acquire) != &state ||
      state.stub == nullptr) {
    AddFailure(state, phase2_producer_identity_failure_already_installed);
    return false;
  }
  const auto write = WriteTarget(state, state.installed_patch_bytes.data(),
                                 state.original_patch_bytes.data());
  if (write != TargetWriteResult::success) {
    AddFailure(state, phase2_producer_identity_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active_observer.store(nullptr, std::memory_order_release);
  const bool released = ReleaseStub(state);
  if (released) ClearResolved(state);
  return released;
}

Phase2ProducerIdentityDiagnosticsV1 ReadPhase2ProducerIdentityDiagnosticsV1(
    const Phase2ProducerIdentityStateV1 &state) noexcept {
  Phase2ProducerIdentityDiagnosticsV1 output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  output.producer_0x3B9CFD2_entry_count =
      state.producer_0x3B9CFD2_entry_count.load(std::memory_order_relaxed);
  output.producer_0x3B9CFD7_entry_count =
      state.producer_0x3B9CFD7_entry_count.load(std::memory_order_relaxed);
  output.read_failure_count = state.read_failure_count.load(std::memory_order_relaxed);
  output.last_task_pointer = state.last_task_pointer.load(std::memory_order_relaxed);
  output.last_callback_pointer = state.last_callback_pointer.load(std::memory_order_relaxed);
  output.last_callback_vptr = state.last_callback_vptr.load(std::memory_order_relaxed);
  output.last_callback_slot2 = state.last_callback_slot2.load(std::memory_order_relaxed);
  output.last_callback_slot2_rva = state.last_callback_slot2_rva.load(std::memory_order_relaxed);
  output.last_owner_pointer = state.last_owner_pointer.load(std::memory_order_relaxed);
  output.last_state_before_publish = state.last_state_before_publish.load(std::memory_order_relaxed);
  output.last_state_after_publish = state.last_state_after_publish.load(std::memory_order_relaxed);
  output.last_thread_id = state.last_thread_id.load(std::memory_order_relaxed);
  output.last_timestamp_qpc = state.last_timestamp_qpc.load(std::memory_order_relaxed);
  return output;
}

} // namespace xar::bridge
