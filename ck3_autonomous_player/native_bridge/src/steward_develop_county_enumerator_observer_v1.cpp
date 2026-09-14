#include "xar_bridge/steward_develop_county_enumerator_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "steward develop county enumerator observer is x64-only");

std::atomic<StewardDevelopCountyEnumeratorObserverStateV1 *>
    g_active_observer{nullptr};

constexpr std::array<
    std::uint8_t, kStewardDevelopCountyEnumeratorObserverPatchBytesV1>
    kPatchAnchor{0x41, 0x0F, 0x11, 0x01,
                 0x89, 0x87, 0x0C, 0x01, 0x00, 0x00,
                 0x41, 0x0F, 0x11, 0x49, 0x10,
                 0x88, 0x44, 0x24, 0x20,
                 0xE8, 0xFF, 0x53, 0x00, 0x00};
constexpr std::size_t kRelocatedPrefixBytes = kPatchAnchor.size() - 5;
constexpr std::size_t kCouncilTaskTypeKeyOffset = 0x18;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 16;
constexpr std::size_t kGuiTaskVectorOffset = 0x100;
constexpr std::size_t kGuiTaskScopeOffset = 0x120;
constexpr char kDevelopCountyTaskKey[] = "task_develop_county";

struct RawVector {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

enum class TaskKeyMatch { unreadable, other, develop_county };

void AddFailure(StewardDevelopCountyEnumeratorObserverStateV1 &state,
                StewardDevelopCountyEnumeratorObserverFailureV1
                    failure) noexcept {
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

bool SafeCopyFrom(std::uintptr_t address, void *output,
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

bool SafeCopyTo(std::uintptr_t address, const void *source,
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

bool SafeBytesEqual(std::uintptr_t address, const std::uint8_t *expected,
                    std::size_t size) noexcept {
  std::array<std::uint8_t,
             kStewardDevelopCountyEnumeratorObserverPatchBytesV1>
      actual{};
  if (size > actual.size() ||
      !SafeCopyFrom(address, actual.data(), size)) {
    return false;
  }
  return std::memcmp(actual.data(), expected, size) == 0;
}

TaskKeyMatch ReadTaskKeyMatch(std::uintptr_t task_type) noexcept {
  std::uintptr_t native_string = 0;
  if (!AddRva(task_type, kCouncilTaskTypeKeyOffset, native_string)) {
    return TaskKeyMatch::unreadable;
  }
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!SafeCopyFrom(native_string + kMsvcStringSizeOffset, &size,
                    sizeof(size)) ||
      !SafeCopyFrom(native_string + kMsvcStringCapacityOffset, &capacity,
                    sizeof(capacity)) ||
      capacity < size || size > 255) {
    return TaskKeyMatch::unreadable;
  }
  constexpr std::size_t expected_size = sizeof(kDevelopCountyTaskKey) - 1;
  if (size != expected_size) return TaskKeyMatch::other;
  std::uintptr_t data = native_string;
  if (capacity >= kMsvcStringInlineCapacity &&
      !SafeCopyFrom(native_string, &data, sizeof(data))) {
    return TaskKeyMatch::unreadable;
  }
  std::array<char, expected_size> key{};
  if (!SafeCopyFrom(data, key.data(), key.size())) {
    return TaskKeyMatch::unreadable;
  }
  return std::memcmp(key.data(), kDevelopCountyTaskKey, key.size()) == 0
      ? TaskKeyMatch::develop_county
      : TaskKeyMatch::other;
}

bool ReadObservationInputs(
    std::uintptr_t gui_task_state, std::uint32_t &scope_word0,
    std::uint32_t &scope_word1, RawVector &vector,
    std::array<StewardDevelopCountyEnumeratorRawRowV1,
               kStewardDevelopCountyEnumeratorObserverMaxRowsV1>
        &rows,
    std::uint32_t &captured_row_count) noexcept {
  std::uintptr_t vector_address = 0;
  std::uintptr_t scope_address = 0;
  if (!AddRva(gui_task_state, kGuiTaskVectorOffset, vector_address) ||
      !AddRva(gui_task_state, kGuiTaskScopeOffset, scope_address) ||
      !SafeCopyFrom(scope_address, &scope_word0, sizeof(scope_word0)) ||
      !SafeCopyFrom(scope_address + sizeof(scope_word0), &scope_word1,
                    sizeof(scope_word1)) ||
      !SafeCopyFrom(vector_address, &vector, sizeof(vector)) ||
      vector.count < 0 || vector.capacity < vector.count ||
      vector.capacity > 4096 || (vector.count != 0 && vector.data == 0)) {
    return false;
  }
  captured_row_count = static_cast<std::uint32_t>(std::min<std::int32_t>(
      vector.count,
      static_cast<std::int32_t>(
          kStewardDevelopCountyEnumeratorObserverMaxRowsV1)));
  for (std::uint32_t index = 0; index < captured_row_count; ++index) {
    const auto offset =
        static_cast<std::uintptr_t>(index) * sizeof(rows[index]);
    if (offset > std::numeric_limits<std::uintptr_t>::max() - vector.data ||
        !SafeCopyFrom(vector.data + offset, &rows[index],
                      sizeof(rows[index]))) {
      return false;
    }
  }
  return true;
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

extern "C" void StewardDevelopCountyEnumeratorPostThunkV1(
    std::uintptr_t task_type, std::uintptr_t gui_task_state) noexcept {
  auto *state = g_active_observer.load(std::memory_order_acquire);
  if (state == nullptr) return;
  LARGE_INTEGER timestamp{};
  (void)QueryPerformanceCounter(&timestamp);
  (void)CaptureStewardDevelopCountyEnumeratorPostCallV1(
      *state, task_type, gui_task_state, GetCurrentThreadId(),
      static_cast<std::uint64_t>(timestamp.QuadPart));
}

bool BuildStub(
    StewardDevelopCountyEnumeratorObserverStateV1 &state,
    std::array<std::uint8_t,
               kStewardDevelopCountyEnumeratorObserverStubCapacityV1>
        &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  for (std::size_t index = 0; index < kRelocatedPrefixBytes; ++index) {
    stub[cursor++] = kPatchAnchor[index];
  }
  EmitRelocatedNativeCall(stub, cursor, state.enumerator_target);
  EmitPreserveVolatile(stub, cursor);
  Emit(stub, cursor, {0x48, 0x8B, 0xCE}); // mov rcx,rsi task type
  Emit(stub, cursor, {0x48, 0x8B, 0xD7}); // mov rdx,rdi GUI task state
  Emit(stub, cursor, {0x48, 0xB8});
  EmitU64(stub, cursor, reinterpret_cast<std::uintptr_t>(
                            &StewardDevelopCountyEnumeratorPostThunkV1));
  Emit(stub, cursor, {0xFF, 0xD0});
  EmitRestoreVolatile(stub, cursor);
  EmitAbsoluteJump(stub, cursor, state.continue_target);
  return cursor <= stub.size();
}

void BuildPatch(
    std::uintptr_t stub_address,
    std::array<std::uint8_t,
               kStewardDevelopCountyEnumeratorObserverPatchBytesV1>
        &patch) noexcept {
  patch.fill(0x90);
  std::size_t cursor = 0;
  EmitAbsoluteJump(patch, cursor, stub_address);
}

bool HasUnsupportedProductionOverride(
    const StewardDevelopCountyEnumeratorObserverEnvironmentV1
        &environment) noexcept {
  return environment.patch_target_override != 0 ||
      environment.continue_target_override != 0 ||
      environment.enumerator_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

bool Flush(StewardDevelopCountyEnumeratorObserverStateV1 &state,
           const void *address, std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state,
               steward_develop_county_enumerator_observer_failure_flush);
    return false;
  }
  return true;
}

enum class TargetWriteResult { success, original_preserved, rollback_unproven };

TargetWriteResult WriteTarget(
    StewardDevelopCountyEnumeratorObserverStateV1 &state,
    const std::uint8_t *expected, const std::uint8_t *desired) noexcept {
  if (!SafeBytesEqual(state.patch_target, expected,
                      kStewardDevelopCountyEnumeratorObserverPatchBytesV1)) {
    AddFailure(
        state,
        steward_develop_county_enumerator_observer_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kStewardDevelopCountyEnumeratorObserverPatchBytesV1,
          PAGE_EXECUTE_READWRITE, previous);
  if (!writable || !IsExecutableProtection(previous)) {
    if (writable) {
      DWORD ignored = 0;
      (void)state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kStewardDevelopCountyEnumeratorObserverPatchBytesV1, previous,
          ignored);
    }
    AddFailure(
        state,
        steward_develop_county_enumerator_observer_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  const bool wrote = SafeCopyTo(
      state.patch_target, desired,
      kStewardDevelopCountyEnumeratorObserverPatchBytesV1);
  const bool identity = wrote && SafeBytesEqual(
      state.patch_target, desired,
      kStewardDevelopCountyEnumeratorObserverPatchBytesV1);
  const bool flushed = identity && Flush(
      state, reinterpret_cast<const void *>(state.patch_target),
      kStewardDevelopCountyEnumeratorObserverPatchBytesV1);
  DWORD ignored = 0;
  const bool protected_again = flushed && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kStewardDevelopCountyEnumeratorObserverPatchBytesV1, previous, ignored);
  if (identity && flushed && protected_again) return TargetWriteResult::success;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect != nullptr &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kStewardDevelopCountyEnumeratorObserverPatchBytesV1,
          PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable && SafeCopyTo(
      state.patch_target, expected,
      kStewardDevelopCountyEnumeratorObserverPatchBytesV1);
  const bool rollback_identity = rollback_written && SafeBytesEqual(
      state.patch_target, expected,
      kStewardDevelopCountyEnumeratorObserverPatchBytesV1);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kStewardDevelopCountyEnumeratorObserverPatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kStewardDevelopCountyEnumeratorObserverPatchBytesV1, previous,
      rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state,
               steward_develop_county_enumerator_observer_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::original_preserved;
}

bool ReleaseStub(StewardDevelopCountyEnumeratorObserverStateV1 &state) noexcept {
  if (state.stub == nullptr) return true;
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE)) {
    AddFailure(state,
               steward_develop_county_enumerator_observer_failure_rollback);
    return false;
  }
  state.stub = nullptr;
  return true;
}

void ClearResolved(
    StewardDevelopCountyEnumeratorObserverStateV1 &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.continue_target = 0;
  state.enumerator_target = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

} // namespace

bool CaptureStewardDevelopCountyEnumeratorPostCallV1(
    StewardDevelopCountyEnumeratorObserverStateV1 &state,
    std::uintptr_t task_type, std::uintptr_t gui_task_state,
    std::uint32_t thread_id, std::uint64_t timestamp_qpc) noexcept {
  const auto match = ReadTaskKeyMatch(task_type);
  std::uint32_t scope_word0 = 0;
  std::uint32_t scope_word1 = 0;
  RawVector vector{};
  std::array<StewardDevelopCountyEnumeratorRawRowV1,
             kStewardDevelopCountyEnumeratorObserverMaxRowsV1>
      rows{};
  std::uint32_t captured_row_count = 0;
  const bool inputs_readable = ReadObservationInputs(
      gui_task_state, scope_word0, scope_word1, vector, rows,
      captured_row_count);
  RecordStewardDevelopCountyEnumeratorObservationV1(
      state, match != TaskKeyMatch::unreadable,
      match == TaskKeyMatch::develop_county, inputs_readable, task_type,
      gui_task_state, scope_word0, scope_word1, vector.data, vector.capacity,
      vector.count, rows.data(), captured_row_count, thread_id, timestamp_qpc);
  return match == TaskKeyMatch::develop_county && inputs_readable;
}

void RecordStewardDevelopCountyEnumeratorObservationV1(
    StewardDevelopCountyEnumeratorObserverStateV1 &state,
    bool task_key_readable, bool task_is_develop_county,
    bool capture_readable,
    std::uintptr_t task_type, std::uintptr_t gui_task_state,
    std::uint32_t scope_word0, std::uint32_t scope_word1,
    std::uintptr_t vector_data, std::int32_t vector_capacity,
    std::int32_t vector_count,
    const StewardDevelopCountyEnumeratorRawRowV1 *rows,
    std::uint32_t captured_row_count, std::uint32_t thread_id,
    std::uint64_t timestamp_qpc) noexcept {
  auto &observation = state.observation;
  observation.call_count.fetch_add(1, std::memory_order_relaxed);
  if (!task_key_readable) {
    observation.task_key_read_failure_count.fetch_add(
        1, std::memory_order_release);
    return;
  }
  if (!task_is_develop_county) return;
  if (!capture_readable) {
    observation.capture_read_failure_count.fetch_add(
        1, std::memory_order_release);
    return;
  }

  captured_row_count = static_cast<std::uint32_t>(std::min<std::size_t>(
      captured_row_count,
      kStewardDevelopCountyEnumeratorObserverMaxRowsV1));
  for (std::size_t index = 0;
       index < kStewardDevelopCountyEnumeratorObserverMaxRowsV1; ++index) {
    const StewardDevelopCountyEnumeratorRawRowV1 row =
        rows != nullptr && index < captured_row_count
        ? rows[index]
        : StewardDevelopCountyEnumeratorRawRowV1{};
    observation.last_candidate_pointers[index].store(row.candidate,
                                                      std::memory_order_relaxed);
    observation.last_row_task_types[index].store(row.task_type,
                                                  std::memory_order_relaxed);
    observation.last_row_query_owners[index].store(row.query_owner,
                                                    std::memory_order_relaxed);
  }
  observation.last_task_type.store(task_type, std::memory_order_relaxed);
  observation.last_gui_task_state.store(gui_task_state,
                                         std::memory_order_relaxed);
  observation.last_scope_word0.store(scope_word0, std::memory_order_relaxed);
  observation.last_scope_word1.store(scope_word1, std::memory_order_relaxed);
  observation.last_vector_data.store(vector_data, std::memory_order_relaxed);
  observation.last_vector_capacity.store(vector_capacity,
                                          std::memory_order_relaxed);
  observation.last_vector_count.store(vector_count, std::memory_order_relaxed);
  observation.last_captured_row_count.store(captured_row_count,
                                             std::memory_order_relaxed);
  observation.last_rows_truncated.store(
      vector_count > static_cast<std::int32_t>(captured_row_count) ? 1U : 0U,
      std::memory_order_relaxed);
  observation.last_thread_id.store(thread_id, std::memory_order_relaxed);
  observation.last_timestamp_qpc.store(timestamp_qpc,
                                        std::memory_order_relaxed);
  observation.develop_capture_count.fetch_add(1, std::memory_order_release);
}

bool InstallStewardDevelopCountyEnumeratorObserverV1(
    StewardDevelopCountyEnumeratorObserverStateV1 &state,
    const StewardDevelopCountyEnumeratorObserverEnvironmentV1
        &environment) noexcept {
  state.failure_flags.store(
      steward_develop_county_enumerator_observer_failure_none,
      std::memory_order_release);
  if (!environment.exact_build_admitted) {
    AddFailure(state,
               steward_develop_county_enumerator_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        steward_develop_county_enumerator_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture &&
      HasUnsupportedProductionOverride(environment)) {
    AddFailure(
        state,
        steward_develop_county_enumerator_observer_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.stub != nullptr) {
    AddFailure(
        state,
        steward_develop_county_enumerator_observer_failure_already_installed);
    return false;
  }
  StewardDevelopCountyEnumeratorObserverStateV1 *expected = nullptr;
  if (!g_active_observer.compare_exchange_strong(
          expected, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(
        state,
        steward_develop_county_enumerator_observer_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.patch_target = Resolve(
      environment.patch_target_override, environment.module_base,
      kStewardDevelopCountyEnumeratorObserverPatchRvaV1);
  state.continue_target = Resolve(
      environment.continue_target_override, environment.module_base,
      kStewardDevelopCountyEnumeratorObserverContinueRvaV1);
  state.enumerator_target = Resolve(
      environment.enumerator_target_override, environment.module_base,
      kStewardDevelopCountyEnumeratorRvaV1);
  state.memory_context = environment.memory_context;
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
  if (state.patch_target == 0 || state.continue_target == 0 ||
      state.enumerator_target == 0 ||
      !SafeBytesEqual(state.patch_target, kPatchAnchor.data(),
                      kPatchAnchor.size()) ||
      !SafeCopyFrom(state.patch_target, state.original_patch_bytes.data(),
                    state.original_patch_bytes.size())) {
    AddFailure(state,
               steward_develop_county_enumerator_observer_failure_anchor);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }

  state.stub = virtual_alloc(
      state.memory_context,
      kStewardDevelopCountyEnumeratorObserverStubCapacityV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state,
               steward_develop_county_enumerator_observer_failure_allocation);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  std::array<std::uint8_t,
             kStewardDevelopCountyEnumeratorObserverStubCapacityV1>
      stub{};
  if (!BuildStub(state, stub) ||
      !SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stub), stub.data(),
                  stub.size())) {
    AddFailure(state,
               steward_develop_county_enumerator_observer_failure_allocation);
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
    AddFailure(
        state,
        steward_develop_county_enumerator_observer_failure_stub_protection);
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

bool UninstallStewardDevelopCountyEnumeratorObserverV1(
    StewardDevelopCountyEnumeratorObserverStateV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_observer.load(std::memory_order_acquire) != &state) {
    AddFailure(
        state,
        steward_develop_county_enumerator_observer_failure_already_installed);
    return false;
  }
  const auto write = WriteTarget(
      state, state.installed_patch_bytes.data(),
      state.original_patch_bytes.data());
  if (write != TargetWriteResult::success) {
    AddFailure(state,
               steward_develop_county_enumerator_observer_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active_observer.store(nullptr, std::memory_order_release);
  const bool released = ReleaseStub(state);
  if (released) ClearResolved(state);
  return released;
}

StewardDevelopCountyEnumeratorObserverDiagnosticsV1
ReadStewardDevelopCountyEnumeratorObserverDiagnosticsV1(
    const StewardDevelopCountyEnumeratorObserverStateV1 &state) noexcept {
  StewardDevelopCountyEnumeratorObserverDiagnosticsV1 output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  const auto &source = state.observation;
  auto &target = output.observation;
  target.call_count = source.call_count.load(std::memory_order_acquire);
  target.task_key_read_failure_count =
      source.task_key_read_failure_count.load(std::memory_order_acquire);
  target.capture_read_failure_count =
      source.capture_read_failure_count.load(std::memory_order_acquire);
  target.develop_capture_count =
      source.develop_capture_count.load(std::memory_order_acquire);
  target.last_task_type =
      source.last_task_type.load(std::memory_order_relaxed);
  target.last_gui_task_state =
      source.last_gui_task_state.load(std::memory_order_relaxed);
  target.last_scope_word0 =
      source.last_scope_word0.load(std::memory_order_relaxed);
  target.last_scope_word1 =
      source.last_scope_word1.load(std::memory_order_relaxed);
  target.last_vector_data =
      source.last_vector_data.load(std::memory_order_relaxed);
  target.last_vector_capacity =
      source.last_vector_capacity.load(std::memory_order_relaxed);
  target.last_vector_count =
      source.last_vector_count.load(std::memory_order_relaxed);
  target.last_captured_row_count =
      source.last_captured_row_count.load(std::memory_order_relaxed);
  target.last_rows_truncated =
      source.last_rows_truncated.load(std::memory_order_relaxed) != 0;
  for (std::size_t index = 0; index < target.rows.size(); ++index) {
    target.rows[index].candidate =
        source.last_candidate_pointers[index].load(std::memory_order_relaxed);
    target.rows[index].task_type =
        source.last_row_task_types[index].load(std::memory_order_relaxed);
    target.rows[index].query_owner =
        source.last_row_query_owners[index].load(std::memory_order_relaxed);
  }
  target.last_thread_id =
      source.last_thread_id.load(std::memory_order_relaxed);
  target.last_timestamp_qpc =
      source.last_timestamp_qpc.load(std::memory_order_relaxed);
  return output;
}

} // namespace xar::bridge
