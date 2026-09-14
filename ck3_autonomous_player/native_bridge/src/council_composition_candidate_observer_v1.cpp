#include "xar_bridge/council_composition_candidate_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "council composition candidate observer is x64-only");

std::atomic<CouncilCompositionCandidateObserverStateV1 *>
    g_active_observer{nullptr};

constexpr std::array<
    std::uint8_t, kCouncilCompositionCandidateObserverPatchBytesV1>
    kPatchAnchor{0x4C, 0x8D, 0x4D, 0x80, 0x41, 0xB0, 0x01, 0x49,
                 0x8B, 0xD2, 0xE8, 0xF1, 0x3A, 0x8E, 0x01};
constexpr std::size_t kRelocatedPrefixBytes = kPatchAnchor.size() - 5;
constexpr std::size_t kCharacterIdOffset = 0x18;
constexpr std::size_t kActiveCouncilTaskIdOffset = 0x10;
constexpr std::size_t kActiveCouncilTaskTypeOffset = 0x18;
constexpr std::size_t kCouncilTaskTypePositionTypeOffset = 0x38;
constexpr std::size_t kCouncilTaskTypeKeyOffset = 0x18;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 16;

struct RawVector {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

void AddFailure(CouncilCompositionCandidateObserverStateV1 &state,
                CouncilCompositionCandidateObserverFailureV1
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
             kCouncilCompositionCandidateObserverPatchBytesV1>
      actual{};
  if (size > actual.size() ||
      !SafeCopyFrom(address, actual.data(), size)) {
    return false;
  }
  return std::memcmp(actual.data(), expected, size) == 0;
}

bool ReadStableKey(
    std::uintptr_t native_string,
    std::array<char,
               kCouncilCompositionCandidateObserverPositionKeyCapacityV1>
        &output,
    std::uint32_t &output_size) noexcept {
  std::uint64_t size = 0;
  std::uint64_t capacity = 0;
  if (!SafeCopyFrom(native_string + kMsvcStringSizeOffset, &size,
                    sizeof(size)) ||
      !SafeCopyFrom(native_string + kMsvcStringCapacityOffset, &capacity,
                    sizeof(capacity)) ||
      capacity < size || size == 0 || size >= output.size()) {
    return false;
  }
  std::uintptr_t data = native_string;
  if (capacity >= kMsvcStringInlineCapacity &&
      !SafeCopyFrom(native_string, &data, sizeof(data))) {
    return false;
  }
  if (!SafeCopyFrom(data, output.data(), static_cast<std::size_t>(size))) {
    return false;
  }
  for (std::size_t index = 0; index < size; ++index) {
    const char character = output[index];
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  output_size = static_cast<std::uint32_t>(size);
  return true;
}

void RejectCapture(CouncilCompositionCandidateObserverStateV1 &state,
                   std::uint32_t failures) noexcept {
  state.observation.last_capture_failure_flags.store(
      failures, std::memory_order_relaxed);
  state.observation.rejected_count.fetch_add(1, std::memory_order_release);
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

extern "C" void CouncilCompositionCandidatePostThunkV1(
    std::uintptr_t owner_character, std::uintptr_t active_task,
    std::uintptr_t vector_header) noexcept {
  auto *state = g_active_observer.load(std::memory_order_acquire);
  if (state == nullptr) return;
  LARGE_INTEGER timestamp{};
  (void)QueryPerformanceCounter(&timestamp);
  (void)CaptureCouncilCompositionCandidatePostCallV1(
      *state, owner_character, active_task, vector_header,
      GetCurrentThreadId(),
      static_cast<std::uint64_t>(timestamp.QuadPart));
}

bool BuildStub(
    CouncilCompositionCandidateObserverStateV1 &state,
    std::array<std::uint8_t,
               kCouncilCompositionCandidateObserverStubCapacityV1>
        &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  for (std::size_t index = 0; index < kRelocatedPrefixBytes; ++index) {
    stub[cursor++] = kPatchAnchor[index];
  }
  // Preserve the owner and active-task arguments across the native producer.
  // The extra 0x20 bytes are a fresh Windows x64 shadow space; the caller's
  // original shadow space must not be reused after the two pushes.
  Emit(stub, cursor, {0x51, 0x52});             // push rcx; push rdx
  Emit(stub, cursor, {0x48, 0x83, 0xEC, 0x20}); // sub rsp,0x20
  EmitRelocatedNativeCall(stub, cursor, state.producer_target);
  Emit(stub, cursor, {0x48, 0x83, 0xC4, 0x20}); // add rsp,0x20
  Emit(stub, cursor, {0x5A, 0x59});             // pop rdx; pop rcx
  EmitPreserveVolatile(stub, cursor);
  Emit(stub, cursor, {0x4C, 0x8D, 0x45, 0x80}); // lea r8,[rbp-0x80]
  Emit(stub, cursor, {0x48, 0xB8});
  EmitU64(stub, cursor, reinterpret_cast<std::uintptr_t>(
                            &CouncilCompositionCandidatePostThunkV1));
  Emit(stub, cursor, {0xFF, 0xD0});
  EmitRestoreVolatile(stub, cursor);
  EmitAbsoluteJump(stub, cursor, state.continue_target);
  return cursor <= stub.size();
}

void BuildPatch(
    std::uintptr_t stub_address,
    std::array<std::uint8_t,
               kCouncilCompositionCandidateObserverPatchBytesV1>
        &patch) noexcept {
  patch.fill(0x90);
  std::size_t cursor = 0;
  EmitAbsoluteJump(patch, cursor, stub_address);
}

bool HasUnsupportedProductionOverride(
    const CouncilCompositionCandidateObserverEnvironmentV1
        &environment) noexcept {
  return environment.patch_target_override != 0 ||
      environment.continue_target_override != 0 ||
      environment.producer_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

bool Flush(CouncilCompositionCandidateObserverStateV1 &state,
           const void *address, std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state,
               council_composition_candidate_observer_failure_flush);
    return false;
  }
  return true;
}

enum class TargetWriteResult { success, original_preserved, rollback_unproven };

TargetWriteResult WriteTarget(
    CouncilCompositionCandidateObserverStateV1 &state,
    const std::uint8_t *expected, const std::uint8_t *desired) noexcept {
  if (!SafeBytesEqual(state.patch_target, expected,
                      kCouncilCompositionCandidateObserverPatchBytesV1)) {
    AddFailure(
        state,
        council_composition_candidate_observer_failure_target_identity);
    return TargetWriteResult::original_preserved;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kCouncilCompositionCandidateObserverPatchBytesV1,
          PAGE_EXECUTE_READWRITE, previous);
  if (!writable || !IsExecutableProtection(previous)) {
    if (writable) {
      DWORD ignored = 0;
      (void)state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kCouncilCompositionCandidateObserverPatchBytesV1, previous,
          ignored);
    }
    AddFailure(
        state,
        council_composition_candidate_observer_failure_target_protection);
    return TargetWriteResult::original_preserved;
  }
  const bool wrote = SafeCopyTo(
      state.patch_target, desired,
      kCouncilCompositionCandidateObserverPatchBytesV1);
  const bool identity = wrote && SafeBytesEqual(
      state.patch_target, desired,
      kCouncilCompositionCandidateObserverPatchBytesV1);
  const bool flushed = identity && Flush(
      state, reinterpret_cast<const void *>(state.patch_target),
      kCouncilCompositionCandidateObserverPatchBytesV1);
  DWORD ignored = 0;
  const bool protected_again = flushed && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kCouncilCompositionCandidateObserverPatchBytesV1, previous, ignored);
  if (identity && flushed && protected_again) return TargetWriteResult::success;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect != nullptr &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kCouncilCompositionCandidateObserverPatchBytesV1,
          PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable && SafeCopyTo(
      state.patch_target, expected,
      kCouncilCompositionCandidateObserverPatchBytesV1);
  const bool rollback_identity = rollback_written && SafeBytesEqual(
      state.patch_target, expected,
      kCouncilCompositionCandidateObserverPatchBytesV1);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kCouncilCompositionCandidateObserverPatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kCouncilCompositionCandidateObserverPatchBytesV1, previous,
      rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state,
               council_composition_candidate_observer_failure_rollback);
    return TargetWriteResult::rollback_unproven;
  }
  return TargetWriteResult::original_preserved;
}

bool ReleaseStub(CouncilCompositionCandidateObserverStateV1 &state) noexcept {
  if (state.stub == nullptr) return true;
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE)) {
    AddFailure(state,
               council_composition_candidate_observer_failure_rollback);
    return false;
  }
  state.stub = nullptr;
  return true;
}

void ClearResolved(
    CouncilCompositionCandidateObserverStateV1 &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.continue_target = 0;
  state.producer_target = 0;
  state.ui_thread_id_source = nullptr;
  state.paused_source = nullptr;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

} // namespace

bool CaptureCouncilCompositionCandidatePostCallV1(
    CouncilCompositionCandidateObserverStateV1 &state,
    std::uintptr_t owner_character, std::uintptr_t active_task,
    std::uintptr_t vector_header,
    std::uint32_t thread_id, std::uint64_t timestamp_qpc) noexcept {
  auto &observation = state.observation;
  observation.call_count.fetch_add(1, std::memory_order_relaxed);
  if (observation.capture_complete.load(std::memory_order_acquire) != 0) {
    observation.ignored_after_capture_count.fetch_add(
        1, std::memory_order_release);
    return false;
  }

  std::uint32_t failures = council_composition_candidate_capture_failure_none;
  const auto ui_thread_id = state.ui_thread_id_source == nullptr
      ? 0U
      : state.ui_thread_id_source->load(std::memory_order_acquire);
  if (ui_thread_id == 0) {
    failures |= council_composition_candidate_capture_failure_ui_thread_unavailable;
  } else if (thread_id != ui_thread_id) {
    failures |= council_composition_candidate_capture_failure_wrong_thread;
  }
  if (state.paused_source == nullptr ||
      !state.paused_source->load(std::memory_order_acquire)) {
    failures |= council_composition_candidate_capture_failure_not_paused;
  }
  if (failures != council_composition_candidate_capture_failure_none) {
    RejectCapture(state, failures);
    return false;
  }

  std::uint32_t owner_character_id = 0;
  std::uint32_t active_task_id = 0;
  std::uintptr_t task_type = 0;
  std::uintptr_t position_type = 0;
  std::array<char, kCouncilCompositionCandidateObserverPositionKeyCapacityV1>
      position_key{};
  std::uint32_t position_key_size = 0;
  if (!SafeCopyFrom(owner_character + kCharacterIdOffset,
                    &owner_character_id, sizeof(owner_character_id))) {
    failures |= council_composition_candidate_capture_failure_owner_id_unreadable;
  }
  if (!SafeCopyFrom(active_task + kActiveCouncilTaskIdOffset,
                    &active_task_id, sizeof(active_task_id))) {
    failures |= council_composition_candidate_capture_failure_task_id_unreadable;
  }
  if (!SafeCopyFrom(active_task + kActiveCouncilTaskTypeOffset,
                    &task_type, sizeof(task_type)) ||
      task_type == 0 ||
      !SafeCopyFrom(task_type + kCouncilTaskTypePositionTypeOffset,
                    &position_type, sizeof(position_type)) ||
      position_type == 0 ||
      !ReadStableKey(position_type + kCouncilTaskTypeKeyOffset,
                     position_key, position_key_size)) {
    failures |= council_composition_candidate_capture_failure_position_key_unreadable;
  }

  RawVector vector{};
  if (!SafeCopyFrom(vector_header, &vector, sizeof(vector))) {
    failures |= council_composition_candidate_capture_failure_header_unreadable;
  }
  std::size_t byte_count = 0;
  if (vector.count < 0 || vector.capacity < vector.count ||
      vector.capacity > kCouncilCompositionCandidateObserverMaxNativeCapacityV1 ||
      vector.count > static_cast<std::int32_t>(
          kCouncilCompositionCandidateObserverMaxRowsV1) ||
      (vector.count > 0 && vector.data == 0) ||
      (vector.count > 0 &&
       static_cast<std::size_t>(vector.count) >
           (std::numeric_limits<std::size_t>::max)() / sizeof(std::uintptr_t))) {
    failures |= council_composition_candidate_capture_failure_invalid_span;
  } else {
    byte_count = static_cast<std::size_t>(vector.count) *
                 sizeof(std::uintptr_t);
    if (vector.data > (std::numeric_limits<std::uintptr_t>::max)() -
                          byte_count) {
      failures |= council_composition_candidate_capture_failure_invalid_span;
    }
  }

  std::array<std::uint32_t,
             kCouncilCompositionCandidateObserverMaxRowsV1> character_ids{};
  std::array<std::uint64_t,
             kCouncilCompositionCandidateObserverMaxRowsV1> raw_rows{};
  std::uint32_t captured_row_count = 0;
  if ((failures & council_composition_candidate_capture_failure_invalid_span) ==
      0) {
    for (std::int32_t index = 0; index < vector.count; ++index) {
      std::uintptr_t candidate = 0;
      if (!SafeCopyFrom(vector.data +
                            static_cast<std::uintptr_t>(index) *
                                sizeof(candidate),
                        &candidate, sizeof(candidate)) || candidate == 0) {
        failures |= council_composition_candidate_capture_failure_row_unreadable;
        break;
      }
      std::uint32_t candidate_id = 0;
      if (!SafeCopyFrom(candidate + kCharacterIdOffset, &candidate_id,
                        sizeof(candidate_id))) {
        failures |=
            council_composition_candidate_capture_failure_character_id_unreadable;
        break;
      }
      raw_rows[static_cast<std::size_t>(index)] =
          static_cast<std::uint64_t>(candidate);
      character_ids[static_cast<std::size_t>(index)] = candidate_id;
      ++captured_row_count;
    }
  }
  if (failures != council_composition_candidate_capture_failure_none) {
    RejectCapture(state, failures);
    return false;
  }

  std::uint32_t duplicate_count = 0;
  for (std::uint32_t left = 0; left < captured_row_count; ++left) {
    for (std::uint32_t right = left + 1; right < captured_row_count; ++right) {
      if (character_ids[left] == character_ids[right]) ++duplicate_count;
    }
  }
  observation.capture_sequence.fetch_add(1, std::memory_order_acq_rel);
  observation.last_ui_thread_id.store(ui_thread_id, std::memory_order_relaxed);
  observation.last_thread_id.store(thread_id, std::memory_order_relaxed);
  observation.last_timestamp_qpc.store(timestamp_qpc,
                                        std::memory_order_relaxed);
  observation.last_owner_character_id.store(owner_character_id,
                                             std::memory_order_relaxed);
  observation.last_active_task_id.store(active_task_id,
                                         std::memory_order_relaxed);
  observation.last_vector_capacity.store(vector.capacity,
                                          std::memory_order_relaxed);
  observation.last_vector_count.store(vector.count, std::memory_order_relaxed);
  observation.last_captured_row_count.store(captured_row_count,
                                             std::memory_order_relaxed);
  observation.last_duplicate_character_id_count.store(
      duplicate_count, std::memory_order_relaxed);
  observation.last_position_key_size.store(position_key_size,
                                             std::memory_order_relaxed);
  for (std::size_t index = 0;
       index < kCouncilCompositionCandidateObserverPositionKeyCapacityV1;
       ++index) {
    observation.last_position_key[index].store(
        static_cast<std::uint8_t>(position_key[index]),
        std::memory_order_relaxed);
  }
  for (std::size_t index = 0;
       index < kCouncilCompositionCandidateObserverMaxRowsV1; ++index) {
    observation.last_character_ids[index].store(character_ids[index],
                                                  std::memory_order_relaxed);
    observation.last_raw_row_bytes[index].store(raw_rows[index],
                                                 std::memory_order_relaxed);
  }
  observation.last_capture_failure_flags.store(
      council_composition_candidate_capture_failure_none,
      std::memory_order_relaxed);
  observation.capture_complete.store(1, std::memory_order_release);
  observation.capture_sequence.fetch_add(1, std::memory_order_release);
  observation.accepted_count.fetch_add(1, std::memory_order_release);
  return true;
}

bool InstallCouncilCompositionCandidateObserverV1(
    CouncilCompositionCandidateObserverStateV1 &state,
    const CouncilCompositionCandidateObserverEnvironmentV1
        &environment) noexcept {
  state.failure_flags.store(
      council_composition_candidate_observer_failure_none,
      std::memory_order_release);
  if (!environment.exact_build_admitted) {
    AddFailure(state,
               council_composition_candidate_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        council_composition_candidate_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture &&
      HasUnsupportedProductionOverride(environment)) {
    AddFailure(
        state,
        council_composition_candidate_observer_failure_unsupported_override);
    return false;
  }
  if (environment.ui_thread_id_source == nullptr) {
    AddFailure(state,
               council_composition_candidate_observer_failure_thread_source);
  }
  if (environment.paused_source == nullptr) {
    AddFailure(state,
               council_composition_candidate_observer_failure_paused_source);
  }
  if (state.failure_flags.load(std::memory_order_acquire) != 0) return false;
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.stub != nullptr) {
    AddFailure(
        state,
        council_composition_candidate_observer_failure_already_installed);
    return false;
  }
  CouncilCompositionCandidateObserverStateV1 *expected = nullptr;
  if (!g_active_observer.compare_exchange_strong(
          expected, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(
        state,
        council_composition_candidate_observer_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.patch_target = Resolve(
      environment.patch_target_override, environment.module_base,
      kCouncilCompositionCandidateObserverPatchRvaV1);
  state.continue_target = Resolve(
      environment.continue_target_override, environment.module_base,
      kCouncilCompositionCandidateObserverContinueRvaV1);
  state.producer_target = Resolve(
      environment.producer_target_override, environment.module_base,
      kCouncilCompositionCandidateProducerRvaV1);
  state.ui_thread_id_source = environment.ui_thread_id_source;
  state.paused_source = environment.paused_source;
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
      state.continue_target !=
          state.patch_target + kCouncilCompositionCandidateObserverPatchBytesV1 ||
      state.producer_target == 0 ||
      !SafeBytesEqual(state.patch_target, kPatchAnchor.data(),
                      kPatchAnchor.size()) ||
      !SafeCopyFrom(state.patch_target, state.original_patch_bytes.data(),
                    state.original_patch_bytes.size())) {
    AddFailure(state,
               council_composition_candidate_observer_failure_anchor);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }

  state.stub = virtual_alloc(
      state.memory_context,
      kCouncilCompositionCandidateObserverStubCapacityV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state,
               council_composition_candidate_observer_failure_allocation);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  std::array<std::uint8_t,
             kCouncilCompositionCandidateObserverStubCapacityV1>
      stub{};
  if (!BuildStub(state, stub) ||
      !SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stub), stub.data(),
                  stub.size())) {
    AddFailure(state,
               council_composition_candidate_observer_failure_allocation);
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
        council_composition_candidate_observer_failure_stub_protection);
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

bool UninstallCouncilCompositionCandidateObserverV1(
    CouncilCompositionCandidateObserverStateV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_observer.load(std::memory_order_acquire) != &state) {
    AddFailure(
        state,
        council_composition_candidate_observer_failure_already_installed);
    return false;
  }
  const auto write = WriteTarget(
      state, state.installed_patch_bytes.data(),
      state.original_patch_bytes.data());
  if (write != TargetWriteResult::success) {
    AddFailure(state,
               council_composition_candidate_observer_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active_observer.store(nullptr, std::memory_order_release);
  const bool released = ReleaseStub(state);
  if (released) ClearResolved(state);
  return released;
}

CouncilCompositionCandidateObserverDiagnosticsV1
ReadCouncilCompositionCandidateObserverDiagnosticsV1(
    const CouncilCompositionCandidateObserverStateV1 &state) noexcept {
  CouncilCompositionCandidateObserverDiagnosticsV1 output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  const auto &source = state.observation;
  auto &target = output.observation;
  target.call_count = source.call_count.load(std::memory_order_acquire);
  target.accepted_count = source.accepted_count.load(std::memory_order_acquire);
  target.rejected_count = source.rejected_count.load(std::memory_order_acquire);
  target.ignored_after_capture_count =
      source.ignored_after_capture_count.load(std::memory_order_acquire);
  target.last_capture_failure_flags =
      source.last_capture_failure_flags.load(std::memory_order_acquire);
  for (int attempt = 0; attempt < 4; ++attempt) {
    const auto before = source.capture_sequence.load(std::memory_order_acquire);
    if ((before & 1U) != 0) continue;
    target.capture_complete =
        source.capture_complete.load(std::memory_order_acquire) != 0;
    target.last_ui_thread_id =
        source.last_ui_thread_id.load(std::memory_order_relaxed);
    target.last_thread_id =
        source.last_thread_id.load(std::memory_order_relaxed);
    target.last_timestamp_qpc =
        source.last_timestamp_qpc.load(std::memory_order_relaxed);
    target.last_owner_character_id =
        source.last_owner_character_id.load(std::memory_order_relaxed);
    target.last_active_task_id =
        source.last_active_task_id.load(std::memory_order_relaxed);
    target.last_vector_capacity =
        source.last_vector_capacity.load(std::memory_order_relaxed);
    target.last_vector_count =
        source.last_vector_count.load(std::memory_order_relaxed);
    target.last_captured_row_count = std::min<std::uint32_t>(
        source.last_captured_row_count.load(std::memory_order_relaxed),
        static_cast<std::uint32_t>(target.rows.size()));
    target.last_duplicate_character_id_count =
        source.last_duplicate_character_id_count.load(
            std::memory_order_relaxed);
    const auto key_size = std::min<std::uint32_t>(
        source.last_position_key_size.load(std::memory_order_relaxed),
        static_cast<std::uint32_t>(target.last_position_key.size() - 1));
    for (std::size_t index = 0; index < target.last_position_key.size();
         ++index) {
      target.last_position_key[index] = static_cast<char>(
          source.last_position_key[index].load(std::memory_order_relaxed));
    }
    target.last_position_key[key_size] = '\0';
    for (std::size_t index = 0; index < target.rows.size(); ++index) {
      target.rows[index].character_id =
          source.last_character_ids[index].load(std::memory_order_relaxed);
      target.rows[index].raw_row_bytes =
          source.last_raw_row_bytes[index].load(std::memory_order_relaxed);
    }
    const auto after = source.capture_sequence.load(std::memory_order_acquire);
    if (before == after && (after & 1U) == 0) {
      target.capture_consistent = true;
      break;
    }
  }
  return output;
}

} // namespace xar::bridge
