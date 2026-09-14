#include "xar_bridge/domain_construction_runtime_callsite_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "domain construction runtime callsite observer is x64-only");
static_assert(sizeof(DomainConstructionRuntimeRawRowV1) == 0x28,
              "the frozen producer row has an exact 0x28-byte stride");

std::atomic<DomainConstructionRuntimeObserverStateV1 *>
    g_active_observer{nullptr};

constexpr std::array<
    std::uint8_t, kDomainConstructionRuntimeObserverPatchBytesV1>
    kPatchAnchor{0x48, 0x8D, 0x55, 0x60,
                 0x48, 0x8B, 0xCE,
                 0xE8, 0xBC, 0xEE, 0x04, 0x00,
                 0x48, 0x8D, 0x45, 0xD0};

struct NativeVectorHeaderV1 {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

static_assert(sizeof(NativeVectorHeaderV1) == 16);

void AddFailure(DomainConstructionRuntimeObserverStateV1 &state,
                DomainConstructionRuntimeObserverFailureV1
                    failure) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

bool DefaultMemoryRead(void *, std::uintptr_t address, void *output,
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

bool DefaultMemoryWrite(void *, std::uintptr_t address, const void *source,
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
  if (base == 0 ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
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

bool ReadMemory(const DomainConstructionRuntimeObserverStateV1 &state,
                std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  return state.memory_read != nullptr &&
      state.memory_read(state.memory_context, address, output, size);
}

bool WriteMemory(const DomainConstructionRuntimeObserverStateV1 &state,
                 std::uintptr_t address, const void *source,
                 std::size_t size) noexcept {
  return state.memory_write != nullptr &&
      state.memory_write(state.memory_context, address, source, size);
}

bool BytesEqual(const DomainConstructionRuntimeObserverStateV1 &state,
                std::uintptr_t address, const std::uint8_t *expected,
                std::size_t size) noexcept {
  std::array<std::uint8_t,
             kDomainConstructionRuntimeObserverPatchBytesV1>
      actual{};
  if (size > actual.size() ||
      !ReadMemory(state, address, actual.data(), size)) {
    return false;
  }
  return std::memcmp(actual.data(), expected, size) == 0;
}

std::uint64_t Fnv1a64(const std::uint8_t *bytes,
                      std::size_t size) noexcept {
  std::uint64_t value = 14695981039346656037ULL;
  for (std::size_t index = 0; index < size; ++index) {
    value ^= bytes[index];
    value *= 1099511628211ULL;
  }
  return value;
}

bool IsExecutableProtection(DWORD protection) noexcept {
  protection &= 0xFF;
  return protection == PAGE_EXECUTE || protection == PAGE_EXECUTE_READ ||
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

template <std::size_t Size>
void EmitRelocatedNativeCall(std::array<std::uint8_t, Size> &output,
                             std::size_t &cursor,
                             std::uintptr_t target) noexcept {
  // call qword ptr [rip+2]; jmp short +8; dq target. This preserves the
  // original callsite's incoming RAX value.
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

extern "C" void DomainConstructionRuntimePostThunkV1(
    std::uintptr_t output_vector_address) noexcept {
  auto *state = g_active_observer.load(std::memory_order_acquire);
  if (state == nullptr) return;
  LARGE_INTEGER timestamp{};
  (void)QueryPerformanceCounter(&timestamp);
  (void)CaptureDomainConstructionRuntimePostCallV1(
      *state, output_vector_address, GetCurrentThreadId(),
      static_cast<std::uint64_t>(timestamp.QuadPart));
}

bool BuildStub(
    DomainConstructionRuntimeObserverStateV1 &state,
    std::array<std::uint8_t,
               kDomainConstructionRuntimeObserverStubCapacityV1>
        &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;

  // Relocated exact native-runtime callsite. The producer is invoked exactly
  // once with the original owner and caller-local RawVector40.
  Emit(stub, cursor, {0x48, 0x8D, 0x55, 0x60});
  Emit(stub, cursor, {0x48, 0x8B, 0xCE});
  EmitRelocatedNativeCall(stub, cursor, state.producer_target);

  // RBP is non-volatile, so the same caller-local vector remains addressable
  // after preserving the volatile frame. Capture is synchronous; no pointer
  // to the caller's stack frame is retained.
  EmitPreserveVolatile(stub, cursor);
  Emit(stub, cursor, {0x48, 0x8D, 0x4D, 0x60});
  Emit(stub, cursor, {0x48, 0xB8});
  EmitU64(stub, cursor, reinterpret_cast<std::uintptr_t>(
                            &DomainConstructionRuntimePostThunkV1));
  Emit(stub, cursor, {0xFF, 0xD0});
  EmitRestoreVolatile(stub, cursor);

  // Replay the final overwritten instruction at 0x18D2954.
  Emit(stub, cursor, {0x48, 0x8D, 0x45, 0xD0});
  EmitAbsoluteJump(stub, cursor, state.continue_target);
  return cursor <= stub.size();
}

void BuildPatch(
    std::uintptr_t stub_address,
    std::array<std::uint8_t,
               kDomainConstructionRuntimeObserverPatchBytesV1>
        &patch) noexcept {
  patch.fill(0x90);
  std::size_t cursor = 0;
  EmitAbsoluteJump(patch, cursor, stub_address);
}

bool HasUnsupportedProductionOverride(
    const DomainConstructionRuntimeObserverEnvironmentV1
        &environment) noexcept {
  return environment.patch_target_override != 0 ||
      environment.continue_target_override != 0 ||
      environment.producer_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.memory_read_override != nullptr ||
      environment.memory_write_override != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

bool Flush(DomainConstructionRuntimeObserverStateV1 &state,
           const void *address, std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state,
               domain_construction_runtime_observer_failure_flush);
    return false;
  }
  return true;
}

enum class TargetWriteResult { success, original_preserved, rollback_unproven };

TargetWriteResult WriteTarget(
    DomainConstructionRuntimeObserverStateV1 &state,
    const std::uint8_t *expected, const std::uint8_t *desired) noexcept {
  if (!BytesEqual(state, state.patch_target, expected,
                  kDomainConstructionRuntimeObserverPatchBytesV1)) {
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kDomainConstructionRuntimeObserverPatchBytesV1,
          PAGE_EXECUTE_READWRITE, previous);
  if (!writable || !IsExecutableProtection(previous)) {
    if (writable) {
      DWORD ignored = 0;
      (void)state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kDomainConstructionRuntimeObserverPatchBytesV1, previous,
          ignored);
    }
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  const bool wrote = WriteMemory(
      state, state.patch_target, desired,
      kDomainConstructionRuntimeObserverPatchBytesV1);
  const bool identity = wrote && BytesEqual(
      state, state.patch_target, desired,
      kDomainConstructionRuntimeObserverPatchBytesV1);
  const bool flushed = identity && Flush(
      state, reinterpret_cast<const void *>(state.patch_target),
      kDomainConstructionRuntimeObserverPatchBytesV1);
  DWORD ignored = 0;
  const bool protected_again = flushed && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kDomainConstructionRuntimeObserverPatchBytesV1, previous, ignored);
  if (identity && flushed && protected_again) return TargetWriteResult::success;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect != nullptr &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kDomainConstructionRuntimeObserverPatchBytesV1,
          PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable && WriteMemory(
      state, state.patch_target, expected,
      kDomainConstructionRuntimeObserverPatchBytesV1);
  const bool rollback_identity = rollback_written && BytesEqual(
      state, state.patch_target, expected,
      kDomainConstructionRuntimeObserverPatchBytesV1);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kDomainConstructionRuntimeObserverPatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kDomainConstructionRuntimeObserverPatchBytesV1, previous,
      rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state,
               domain_construction_runtime_observer_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::original_preserved;
}

bool ReleaseStub(DomainConstructionRuntimeObserverStateV1 &state) noexcept {
  if (state.stub == nullptr) return true;
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE)) {
    AddFailure(state,
               domain_construction_runtime_observer_failure_rollback);
    return false;
  }
  state.stub = nullptr;
  return true;
}

void ClearResolved(
    DomainConstructionRuntimeObserverStateV1 &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.continue_target = 0;
  state.producer_target = 0;
  state.memory_context = nullptr;
  state.memory_read = nullptr;
  state.memory_write = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
  state.capture_admission_context = nullptr;
  state.capture_admission_probe = nullptr;
}

} // namespace

bool CaptureDomainConstructionRuntimePostCallV1(
    DomainConstructionRuntimeObserverStateV1 &state,
    std::uintptr_t output_vector_address, std::uint32_t current_thread_id,
    std::uint64_t timestamp_qpc) noexcept {
  auto &observation = state.observation;
  observation.producer_call_count.fetch_add(1, std::memory_order_relaxed);

  DomainConstructionRuntimeCaptureAdmissionV1 admission{};
  if (state.capture_admission_probe == nullptr ||
      !state.capture_admission_probe(state.capture_admission_context,
                                     admission) ||
      admission.application_main_thread_id == 0 ||
      admission.application_main_thread_id != current_thread_id) {
    observation.rejected_application_main_count.fetch_add(
        1, std::memory_order_release);
    return false;
  }
  if (!admission.session_live) {
    observation.rejected_session_count.fetch_add(1,
                                                  std::memory_order_release);
    return false;
  }

  NativeVectorHeaderV1 vector{};
  if (output_vector_address == 0 ||
      !ReadMemory(state, output_vector_address, &vector, sizeof(vector)) ||
      vector.count < 0 || vector.capacity < vector.count ||
      vector.capacity > 4096 || (vector.count != 0 && vector.data == 0)) {
    observation.capture_read_failure_count.fetch_add(
        1, std::memory_order_release);
    return false;
  }

  const auto captured_row_count = static_cast<std::uint32_t>(
      std::min<std::int32_t>(
          vector.count,
          static_cast<std::int32_t>(
              kDomainConstructionRuntimeObserverMaximumRowsV1)));
  std::array<DomainConstructionRuntimeRawRowV1,
             kDomainConstructionRuntimeObserverMaximumRowsV1>
      rows{};
  for (std::uint32_t index = 0; index < captured_row_count; ++index) {
    const auto offset = static_cast<std::uintptr_t>(index) *
        kDomainConstructionRuntimeRowBytesV1;
    if (offset > (std::numeric_limits<std::uintptr_t>::max)() - vector.data ||
        !ReadMemory(state, vector.data + offset, rows[index].bytes.data(),
                    rows[index].bytes.size())) {
      observation.capture_read_failure_count.fetch_add(
          1, std::memory_order_release);
      return false;
    }
  }

  // Odd while publishing, even once the full POD copy is visible.
  observation.published_generation.fetch_add(1, std::memory_order_acq_rel);
  for (std::size_t index = 0;
       index < kDomainConstructionRuntimeObserverMaximumRowsV1; ++index) {
    const auto row = index < captured_row_count
        ? rows[index]
        : DomainConstructionRuntimeRawRowV1{};
    std::int64_t score_raw = 0;
    std::memcpy(&score_raw, row.bytes.data(), sizeof(score_raw));
    observation.last_scores_raw[index].store(score_raw,
                                              std::memory_order_relaxed);
    for (std::size_t byte_index = 0; byte_index < row.bytes.size();
         ++byte_index) {
      observation.last_row_bytes[index][byte_index].store(
          row.bytes[byte_index], std::memory_order_relaxed);
    }
    observation.last_row_bytes_fnv1a64[index].store(
        Fnv1a64(row.bytes.data(), row.bytes.size()),
        std::memory_order_relaxed);
  }
  observation.last_proof_epoch.store(admission.proof_epoch,
                                      std::memory_order_relaxed);
  observation.last_date_raw.store(admission.date_raw,
                                   std::memory_order_relaxed);
  observation.last_paused.store(admission.paused ? 1U : 0U,
                                 std::memory_order_relaxed);
  observation.last_vector_capacity.store(vector.capacity,
                                          std::memory_order_relaxed);
  observation.last_vector_count.store(vector.count,
                                       std::memory_order_relaxed);
  observation.last_captured_row_count.store(captured_row_count,
                                             std::memory_order_relaxed);
  observation.last_rows_truncated.store(
      vector.count > static_cast<std::int32_t>(captured_row_count) ? 1U : 0U,
      std::memory_order_relaxed);
  observation.last_thread_id.store(current_thread_id,
                                    std::memory_order_relaxed);
  observation.last_timestamp_qpc.store(timestamp_qpc,
                                        std::memory_order_relaxed);
  observation.accepted_capture_count.fetch_add(1,
                                                std::memory_order_relaxed);
  observation.published_generation.fetch_add(1, std::memory_order_release);
  return true;
}

bool InstallDomainConstructionRuntimeObserverV1(
    DomainConstructionRuntimeObserverStateV1 &state,
    const DomainConstructionRuntimeObserverEnvironmentV1
        &environment) noexcept {
  state.failure_flags.store(
      domain_construction_runtime_observer_failure_none,
      std::memory_order_release);
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kDomainConstructionRuntimeObserverExecutableSha256V1) {
    AddFailure(state,
               domain_construction_runtime_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_primary_thread_suspended);
    return false;
  }
  if (environment.capture_admission_probe == nullptr) {
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_capture_admission);
    return false;
  }
  if (!environment.offline_fixture &&
      HasUnsupportedProductionOverride(environment)) {
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.stub != nullptr) {
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_already_installed);
    return false;
  }
  DomainConstructionRuntimeObserverStateV1 *expected = nullptr;
  if (!g_active_observer.compare_exchange_strong(
          expected, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_already_installed);
    return false;
  }

  state.offline_fixture = environment.offline_fixture;
  state.module_base = environment.module_base;
  state.patch_target = Resolve(
      environment.patch_target_override, environment.module_base,
      kDomainConstructionRuntimeObserverPatchRvaV1);
  state.continue_target = Resolve(
      environment.continue_target_override, environment.module_base,
      kDomainConstructionRuntimeObserverContinueRvaV1);
  state.producer_target = Resolve(
      environment.producer_target_override, environment.module_base,
      kDomainConstructionRuntimeProducerRvaV1);
  state.memory_context = environment.memory_context;
  state.memory_read = environment.memory_read_override != nullptr
      ? environment.memory_read_override
      : &DefaultMemoryRead;
  state.memory_write = environment.memory_write_override != nullptr
      ? environment.memory_write_override
      : &DefaultMemoryWrite;
  const auto virtual_alloc = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override
      : &DefaultVirtualAlloc;
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
  state.capture_admission_context = environment.capture_admission_context;
  state.capture_admission_probe = environment.capture_admission_probe;

  if (state.patch_target == 0 || state.continue_target == 0 ||
      state.producer_target == 0 ||
      !BytesEqual(state, state.patch_target, kPatchAnchor.data(),
                  kPatchAnchor.size()) ||
      !ReadMemory(state, state.patch_target,
                  state.original_patch_bytes.data(),
                  state.original_patch_bytes.size())) {
    AddFailure(state,
               domain_construction_runtime_observer_failure_anchor);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }

  state.stub = virtual_alloc(
      state.memory_context,
      kDomainConstructionRuntimeObserverStubCapacityV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state,
               domain_construction_runtime_observer_failure_allocation);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  std::array<std::uint8_t,
             kDomainConstructionRuntimeObserverStubCapacityV1>
      stub{};
  if (!BuildStub(state, stub) ||
      !WriteMemory(state, reinterpret_cast<std::uintptr_t>(state.stub),
                   stub.data(), stub.size())) {
    AddFailure(state,
               domain_construction_runtime_observer_failure_allocation);
    (void)ReleaseStub(state);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  DWORD previous = 0;
  const bool protected_stub = state.virtual_protect(
      state.memory_context, state.stub, stub.size(), PAGE_EXECUTE_READ,
      previous);
  const bool flushed_stub = protected_stub && Flush(
      state, state.stub, stub.size());
  if (!protected_stub || previous != PAGE_READWRITE || !flushed_stub) {
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_stub_protection);
    (void)ReleaseStub(state);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  BuildPatch(reinterpret_cast<std::uintptr_t>(state.stub),
             state.installed_patch_bytes);
  const auto write = WriteTarget(
      state, state.original_patch_bytes.data(),
      state.installed_patch_bytes.data());
  if (write == TargetWriteResult::success) {
    state.installed.store(1, std::memory_order_release);
    return true;
  }
  if (write == TargetWriteResult::rollback_unproven) {
    state.installed.store(1, std::memory_order_release);
    return false;
  }
  (void)ReleaseStub(state);
  ClearResolved(state);
  g_active_observer.store(nullptr, std::memory_order_release);
  return false;
}

bool UninstallDomainConstructionRuntimeObserverV1(
    DomainConstructionRuntimeObserverStateV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_observer.load(std::memory_order_acquire) != &state) {
    AddFailure(
        state,
        domain_construction_runtime_observer_failure_already_installed);
    return false;
  }
  const auto write = WriteTarget(
      state, state.installed_patch_bytes.data(),
      state.original_patch_bytes.data());
  if (write != TargetWriteResult::success) {
    AddFailure(state,
               domain_construction_runtime_observer_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active_observer.store(nullptr, std::memory_order_release);
  const bool released = ReleaseStub(state);
  if (released) ClearResolved(state);
  return released;
}

DomainConstructionRuntimeObserverDiagnosticsV1
ReadDomainConstructionRuntimeObserverDiagnosticsV1(
    const DomainConstructionRuntimeObserverStateV1 &state) noexcept {
  DomainConstructionRuntimeObserverDiagnosticsV1 output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.offline_fixture = state.offline_fixture;
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  const auto &source = state.observation;
  auto &target = output.observation;
  target.producer_call_count =
      source.producer_call_count.load(std::memory_order_acquire);
  target.rejected_application_main_count =
      source.rejected_application_main_count.load(std::memory_order_acquire);
  target.rejected_session_count =
      source.rejected_session_count.load(std::memory_order_acquire);
  target.capture_read_failure_count =
      source.capture_read_failure_count.load(std::memory_order_acquire);
  target.accepted_capture_count =
      source.accepted_capture_count.load(std::memory_order_acquire);

  for (std::size_t attempt = 0; attempt < 8; ++attempt) {
    const auto before =
        source.published_generation.load(std::memory_order_acquire);
    if ((before & 1U) != 0) continue;
    target.last_proof_epoch =
        source.last_proof_epoch.load(std::memory_order_relaxed);
    target.last_date_raw =
        source.last_date_raw.load(std::memory_order_relaxed);
    target.last_paused =
        source.last_paused.load(std::memory_order_relaxed) != 0;
    target.last_vector_capacity =
        source.last_vector_capacity.load(std::memory_order_relaxed);
    target.last_vector_count =
        source.last_vector_count.load(std::memory_order_relaxed);
    target.last_captured_row_count =
        source.last_captured_row_count.load(std::memory_order_relaxed);
    target.last_rows_truncated =
        source.last_rows_truncated.load(std::memory_order_relaxed) != 0;
    for (std::size_t index = 0; index < target.rows.size(); ++index) {
      target.rows[index].score_raw =
          source.last_scores_raw[index].load(std::memory_order_relaxed);
      for (std::size_t byte_index = 0;
           byte_index < target.rows[index].row_bytes.size(); ++byte_index) {
        target.rows[index].row_bytes[byte_index] =
            source.last_row_bytes[index][byte_index].load(
                std::memory_order_relaxed);
      }
      target.rows[index].row_bytes_fnv1a64 =
          source.last_row_bytes_fnv1a64[index].load(
              std::memory_order_relaxed);
    }
    target.last_thread_id =
        source.last_thread_id.load(std::memory_order_relaxed);
    target.last_timestamp_qpc =
        source.last_timestamp_qpc.load(std::memory_order_relaxed);
    const auto after =
        source.published_generation.load(std::memory_order_acquire);
    if (before == after && (after & 1U) == 0) {
      target.published_generation = after;
      break;
    }
  }
  return output;
}

} // namespace xar::bridge
