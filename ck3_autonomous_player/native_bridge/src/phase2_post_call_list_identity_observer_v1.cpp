#include "xar_bridge/phase2_post_call_list_identity_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "phase2 post-call list identity observer is x64-only");

std::atomic<Phase2PostCallListIdentityStateV1 *> g_active_observer{nullptr};

constexpr std::array<std::uint8_t,
                     kPhase2PostCallListIdentityPatchBytesV1>
    kPatchAnchor{0x90, 0x48, 0x8B, 0x4C, 0x24, 0x68, 0x48,
                 0x85, 0xC9, 0x74, 0x11, 0x48, 0x8B, 0x01};

struct Capture {
  std::uint64_t producer_list = 0;
  std::uint64_t list_begin = 0;
  std::uint32_t list_count = 0;
  std::uint32_t scan_count = 0;
  std::uint32_t read_failure_count = 0;
  std::uint32_t scan_truncated_count = 0;
  std::uint32_t sample_count = 0;
  std::uint32_t sample_overflow_count = 0;
  std::uint32_t histogram_bin_count = 0;
  std::uint32_t histogram_overflow_count = 0;
  std::uint32_t selected_target_count = 0;
  std::uint32_t thread_id = 0;
  std::uint64_t timestamp_qpc = 0;
  std::array<Phase2PostCallListIdentitySampleV1,
             kPhase2PostCallListIdentitySampleCapacityV1>
      samples{};
  std::array<Phase2PostCallListIdentityHistogramBinV1,
             kPhase2PostCallListIdentityHistogramCapacityV1>
      histogram{};
};

void AddFailure(Phase2PostCallListIdentityStateV1 &state,
                Phase2PostCallListIdentityFailureV1 failure) noexcept {
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
                           DWORD protection, DWORD &old_protection) noexcept {
  return VirtualProtect(address, size, protection, &old_protection) != FALSE;
}

bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool Add(std::uintptr_t base, std::uintptr_t offset,
         std::uintptr_t &output) noexcept {
  if (base == 0 || offset > std::numeric_limits<std::uintptr_t>::max() - base) {
    output = 0;
    return false;
  }
  output = base + offset;
  return true;
}

std::uintptr_t Resolve(std::uintptr_t override_address,
                       std::uintptr_t module_base,
                       std::uintptr_t rva) noexcept {
  if (override_address != 0) return override_address;
  std::uintptr_t output = 0;
  (void)Add(module_base, rva, output);
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
    std::memcpy(&output, reinterpret_cast<const void *>(address), sizeof(output));
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
    std::memcpy(&output, reinterpret_cast<const void *>(address), sizeof(output));
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

extern "C" void Phase2PostCallListIdentityThunkV1(
    std::uintptr_t frame_base) noexcept {
  auto *state = g_active_observer.load(std::memory_order_acquire);
  if (state == nullptr) return;
  LARGE_INTEGER timestamp{};
  (void)QueryPerformanceCounter(&timestamp);
  RecordPhase2PostCallListIdentityObservationV1(
      *state, frame_base, GetCurrentThreadId(),
      static_cast<std::uint64_t>(timestamp.QuadPart));
}

bool BuildStub(
    Phase2PostCallListIdentityStateV1 &state,
    std::array<std::uint8_t, kPhase2PostCallListIdentityStubBytesV1>
        &stub) noexcept {
  std::size_t cursor = 0;
  Emit(stub, cursor,
       {0x50, 0x51, 0x52, 0x41, 0x50, 0x41, 0x51,
        0x41, 0x52, 0x41, 0x53});
  Emit(stub, cursor, {0x48, 0x83, 0xEC, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0xCD});
  Emit(stub, cursor, {0x48, 0xB8});
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&Phase2PostCallListIdentityThunkV1));
  Emit(stub, cursor, {0xFF, 0xD0});
  Emit(stub, cursor, {0x48, 0x83, 0xC4, 0x20});
  Emit(stub, cursor,
       {0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
        0x41, 0x58, 0x5A, 0x59, 0x58});
  Emit(stub, cursor, {0x90});
  Emit(stub, cursor, {0x48, 0x8B, 0x4C, 0x24, 0x68});
  Emit(stub, cursor, {0x48, 0x85, 0xC9});
  Emit(stub, cursor, {0x75, 0x0E});
  EmitAbsoluteJump(stub, cursor, state.null_target);
  Emit(stub, cursor, {0x48, 0x8B, 0x01});
  EmitAbsoluteJump(stub, cursor, state.continue_target);
  return cursor == stub.size();
}

void BuildPatch(
    std::uintptr_t stub,
    std::array<std::uint8_t, kPhase2PostCallListIdentityPatchBytesV1>
        &patch) noexcept {
  std::size_t cursor = 0;
  EmitAbsoluteJump(patch, cursor, stub);
}

bool HasUnsupportedOverride(
    const Phase2PostCallListIdentityEnvironmentV1 &environment) noexcept {
  return environment.patch_target_override != 0 ||
      environment.continue_target_override != 0 ||
      environment.null_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

bool Flush(Phase2PostCallListIdentityStateV1 &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, phase2_post_call_list_identity_failure_flush);
    return false;
  }
  return true;
}

enum class WriteResult { success, original_preserved, rollback_unproven };

WriteResult WriteTarget(Phase2PostCallListIdentityStateV1 &state,
                        const std::uint8_t *expected,
                        const std::uint8_t *desired) noexcept {
  if (!SafeBytesEqual(state.patch_target, expected,
                      kPhase2PostCallListIdentityPatchBytesV1)) {
    AddFailure(state, phase2_post_call_list_identity_failure_target_identity);
    return WriteResult::original_preserved;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(state.patch_target),
                            kPhase2PostCallListIdentityPatchBytesV1,
                            PAGE_EXECUTE_READWRITE, previous);
  if (!writable || !IsExecutableProtection(previous)) {
    if (writable) {
      DWORD ignored = 0;
      (void)state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kPhase2PostCallListIdentityPatchBytesV1, previous, ignored);
    }
    AddFailure(state, phase2_post_call_list_identity_failure_target_protection);
    return WriteResult::original_preserved;
  }
  const bool wrote = SafeCopyTo(state.patch_target, desired,
                                kPhase2PostCallListIdentityPatchBytesV1);
  const bool identity = wrote && SafeBytesEqual(
      state.patch_target, desired, kPhase2PostCallListIdentityPatchBytesV1);
  const bool flushed = identity && Flush(
      state, reinterpret_cast<const void *>(state.patch_target),
      kPhase2PostCallListIdentityPatchBytesV1);
  DWORD ignored = 0;
  const bool protected_again = flushed && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kPhase2PostCallListIdentityPatchBytesV1, previous, ignored);
  if (identity && flushed && protected_again) return WriteResult::success;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(state.patch_target),
                            kPhase2PostCallListIdentityPatchBytesV1,
                            PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable && SafeCopyTo(
      state.patch_target, expected, kPhase2PostCallListIdentityPatchBytesV1);
  const bool rollback_identity = rollback_written && SafeBytesEqual(
      state.patch_target, expected, kPhase2PostCallListIdentityPatchBytesV1);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kPhase2PostCallListIdentityPatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable && state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kPhase2PostCallListIdentityPatchBytesV1, previous, rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state, phase2_post_call_list_identity_failure_rollback);
    return WriteResult::rollback_unproven;
  }
  return WriteResult::original_preserved;
}

bool ReleaseStub(Phase2PostCallListIdentityStateV1 &state) noexcept {
  if (state.stub == nullptr) return true;
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub, 0, MEM_RELEASE)) {
    AddFailure(state, phase2_post_call_list_identity_failure_rollback);
    return false;
  }
  state.stub = nullptr;
  return true;
}

void ClearResolved(Phase2PostCallListIdentityStateV1 &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.continue_target = 0;
  state.null_target = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

void AddHistogram(Capture &capture,
                  const Phase2PostCallListIdentitySampleV1 &sample) noexcept {
  if (!sample.read_complete || sample.callback_slot2_target == 0) return;
  for (std::uint32_t index = 0; index < capture.histogram_bin_count; ++index) {
    auto &bin = capture.histogram[index];
    if (bin.callback_slot2_target != sample.callback_slot2_target) continue;
    ++bin.count;
    bin.last_task = sample.task;
    bin.last_owner = sample.owner;
    return;
  }
  if (capture.histogram_bin_count >=
      kPhase2PostCallListIdentityHistogramCapacityV1) {
    ++capture.histogram_overflow_count;
    return;
  }
  auto &bin = capture.histogram[capture.histogram_bin_count++];
  bin.callback_slot2_target = sample.callback_slot2_target;
  bin.callback_slot2_rva = sample.callback_slot2_rva;
  bin.count = 1;
  bin.first_task = sample.task;
  bin.first_owner = sample.owner;
  bin.last_task = sample.task;
  bin.last_owner = sample.owner;
}

void Publish(Phase2PostCallListIdentityStateV1 &state,
             const Capture &capture) noexcept {
  state.last_producer_list.store(capture.producer_list,
                                 std::memory_order_relaxed);
  state.last_list_begin.store(capture.list_begin, std::memory_order_relaxed);
  state.last_list_count.store(capture.list_count, std::memory_order_relaxed);
  state.last_scan_count.store(capture.scan_count, std::memory_order_relaxed);
  state.last_read_failure_count.store(capture.read_failure_count,
                                       std::memory_order_relaxed);
  state.last_scan_truncated_count.store(capture.scan_truncated_count,
                                        std::memory_order_relaxed);
  state.last_sample_count.store(capture.sample_count,
                                std::memory_order_relaxed);
  state.last_sample_overflow_count.store(capture.sample_overflow_count,
                                         std::memory_order_relaxed);
  state.last_histogram_bin_count.store(capture.histogram_bin_count,
                                       std::memory_order_relaxed);
  state.last_histogram_overflow_count.store(capture.histogram_overflow_count,
                                            std::memory_order_relaxed);
  state.last_selected_target_count.store(capture.selected_target_count,
                                         std::memory_order_relaxed);
  state.last_thread_id.store(capture.thread_id, std::memory_order_relaxed);
  state.last_timestamp_qpc.store(capture.timestamp_qpc,
                                 std::memory_order_relaxed);
  for (std::size_t index = 0; index < state.samples.size(); ++index) {
    const auto &source = capture.samples[index];
    auto &target = state.samples[index];
    target.descriptor_index.store(source.descriptor_index,
                                  std::memory_order_relaxed);
    target.read_complete.store(source.read_complete ? 1U : 0U,
                               std::memory_order_relaxed);
    target.descriptor.store(source.descriptor, std::memory_order_relaxed);
    target.task.store(source.task, std::memory_order_relaxed);
    target.owner.store(source.owner, std::memory_order_relaxed);
    target.callback.store(source.callback, std::memory_order_relaxed);
    target.callback_slot2_target.store(source.callback_slot2_target,
                                       std::memory_order_relaxed);
    target.callback_slot2_rva.store(source.callback_slot2_rva,
                                    std::memory_order_relaxed);
    target.state.store(source.state, std::memory_order_relaxed);
  }
  for (std::size_t index = 0; index < state.histogram.size(); ++index) {
    const auto &source = capture.histogram[index];
    auto &target = state.histogram[index];
    target.callback_slot2_target.store(source.callback_slot2_target,
                                       std::memory_order_relaxed);
    target.callback_slot2_rva.store(source.callback_slot2_rva,
                                    std::memory_order_relaxed);
    target.count.store(source.count, std::memory_order_relaxed);
    target.first_task.store(source.first_task, std::memory_order_relaxed);
    target.first_owner.store(source.first_owner, std::memory_order_relaxed);
    target.last_task.store(source.last_task, std::memory_order_relaxed);
    target.last_owner.store(source.last_owner, std::memory_order_relaxed);
  }
}

void ResetTelemetry(Phase2PostCallListIdentityStateV1 &state) noexcept {
  state.hit_count.store(0, std::memory_order_relaxed);
  state.capture_count.store(0, std::memory_order_relaxed);
  state.capture_contention_count.store(0, std::memory_order_relaxed);
  state.snapshot_sequence.store(0, std::memory_order_relaxed);
  state.capture_lock.clear(std::memory_order_release);
  Publish(state, Capture{});
}

void LoadDiagnostics(const Phase2PostCallListIdentityStateV1 &state,
                     Phase2PostCallListIdentityDiagnosticsV1 &output) noexcept {
  output.last_producer_list =
      state.last_producer_list.load(std::memory_order_relaxed);
  output.last_list_begin = state.last_list_begin.load(std::memory_order_relaxed);
  output.last_list_count = state.last_list_count.load(std::memory_order_relaxed);
  output.last_scan_count = state.last_scan_count.load(std::memory_order_relaxed);
  output.last_read_failure_count =
      state.last_read_failure_count.load(std::memory_order_relaxed);
  output.last_scan_truncated_count =
      state.last_scan_truncated_count.load(std::memory_order_relaxed);
  output.last_sample_count =
      state.last_sample_count.load(std::memory_order_relaxed);
  output.last_sample_overflow_count =
      state.last_sample_overflow_count.load(std::memory_order_relaxed);
  output.last_histogram_bin_count =
      state.last_histogram_bin_count.load(std::memory_order_relaxed);
  output.last_histogram_overflow_count =
      state.last_histogram_overflow_count.load(std::memory_order_relaxed);
  output.last_selected_target_count =
      state.last_selected_target_count.load(std::memory_order_relaxed);
  output.last_thread_id = state.last_thread_id.load(std::memory_order_relaxed);
  output.last_timestamp_qpc =
      state.last_timestamp_qpc.load(std::memory_order_relaxed);
  for (std::size_t index = 0; index < output.samples.size(); ++index) {
    const auto &source = state.samples[index];
    auto &target = output.samples[index];
    target.descriptor_index =
        source.descriptor_index.load(std::memory_order_relaxed);
    target.read_complete =
        source.read_complete.load(std::memory_order_relaxed) != 0;
    target.descriptor = source.descriptor.load(std::memory_order_relaxed);
    target.task = source.task.load(std::memory_order_relaxed);
    target.owner = source.owner.load(std::memory_order_relaxed);
    target.callback = source.callback.load(std::memory_order_relaxed);
    target.callback_slot2_target =
        source.callback_slot2_target.load(std::memory_order_relaxed);
    target.callback_slot2_rva =
        source.callback_slot2_rva.load(std::memory_order_relaxed);
    target.state = source.state.load(std::memory_order_relaxed);
  }
  for (std::size_t index = 0; index < output.histogram.size(); ++index) {
    const auto &source = state.histogram[index];
    auto &target = output.histogram[index];
    target.callback_slot2_target =
        source.callback_slot2_target.load(std::memory_order_relaxed);
    target.callback_slot2_rva =
        source.callback_slot2_rva.load(std::memory_order_relaxed);
    target.count = source.count.load(std::memory_order_relaxed);
    target.first_task = source.first_task.load(std::memory_order_relaxed);
    target.first_owner = source.first_owner.load(std::memory_order_relaxed);
    target.last_task = source.last_task.load(std::memory_order_relaxed);
    target.last_owner = source.last_owner.load(std::memory_order_relaxed);
  }
}

} // namespace

void RecordPhase2PostCallListIdentityObservationV1(
    Phase2PostCallListIdentityStateV1 &state, std::uintptr_t frame_base,
    std::uint32_t thread_id, std::uint64_t timestamp_qpc) noexcept {
  state.hit_count.fetch_add(1, std::memory_order_relaxed);
  if (state.capture_lock.test_and_set(std::memory_order_acquire)) {
    state.capture_contention_count.fetch_add(1, std::memory_order_relaxed);
    return;
  }
  state.snapshot_sequence.fetch_add(1, std::memory_order_acq_rel);
  Capture capture{};
  capture.thread_id = thread_id;
  capture.timestamp_qpc = timestamp_qpc;
  std::uintptr_t producer_list = 0;
  if (!Add(frame_base, 0xE0, producer_list)) {
    ++capture.read_failure_count;
  } else {
    capture.producer_list = producer_list;
    if (!SafeReadU64(producer_list, capture.list_begin) ||
        !SafeReadU32(producer_list + 0xC, capture.list_count)) {
      ++capture.read_failure_count;
    } else if (capture.list_count > 0 && capture.list_begin == 0) {
      ++capture.read_failure_count;
    } else {
      capture.scan_count = std::min(
          capture.list_count, kPhase2PostCallListIdentityMaxDescriptorsV1);
      if (capture.scan_count != capture.list_count) {
        capture.scan_truncated_count = 1;
      }
      for (std::uint32_t index = 0; index < capture.scan_count; ++index) {
        Phase2PostCallListIdentitySampleV1 sample{};
        sample.descriptor_index = index;
        std::uint64_t descriptor = 0;
        if (!SafeReadU64(static_cast<std::uintptr_t>(capture.list_begin) +
                             static_cast<std::uintptr_t>(index) * 8ULL,
                         descriptor) ||
            descriptor == 0) {
          ++capture.read_failure_count;
          continue;
        }
        sample.descriptor = descriptor;
        std::uint64_t vtable = 0;
        const bool read =
            SafeReadU64(static_cast<std::uintptr_t>(descriptor) + 0x18,
                        sample.task) &&
            SafeReadU64(static_cast<std::uintptr_t>(descriptor) + 0x20,
                        sample.owner) &&
            sample.task != 0 &&
            SafeReadU64(static_cast<std::uintptr_t>(sample.task) + 0x38,
                        sample.callback) &&
            SafeReadU32(static_cast<std::uintptr_t>(sample.task) + 0x60,
                        sample.state) &&
            sample.callback != 0 &&
            SafeReadU64(static_cast<std::uintptr_t>(sample.callback), vtable) &&
            vtable != 0 &&
            SafeReadU64(static_cast<std::uintptr_t>(vtable) + 0x10,
                        sample.callback_slot2_target);
        sample.read_complete = read;
        if (!read) {
          ++capture.read_failure_count;
        } else if (sample.callback_slot2_target >= state.module_base) {
          sample.callback_slot2_rva =
              sample.callback_slot2_target - state.module_base;
          if (sample.callback_slot2_rva ==
              kPhase2PostCallListIdentitySelectedTargetRvaV1) {
            ++capture.selected_target_count;
          }
        }
        if (capture.sample_count <
            kPhase2PostCallListIdentitySampleCapacityV1) {
          capture.samples[capture.sample_count++] = sample;
        } else {
          ++capture.sample_overflow_count;
        }
        AddHistogram(capture, sample);
      }
    }
  }
  Publish(state, capture);
  state.capture_count.fetch_add(1, std::memory_order_relaxed);
  state.snapshot_sequence.fetch_add(1, std::memory_order_release);
  state.capture_lock.clear(std::memory_order_release);
}

bool InstallPhase2PostCallListIdentityObserverV1(
    Phase2PostCallListIdentityStateV1 &state,
    const Phase2PostCallListIdentityEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(phase2_post_call_list_identity_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, phase2_post_call_list_identity_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        phase2_post_call_list_identity_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture && HasUnsupportedOverride(environment)) {
    AddFailure(state,
               phase2_post_call_list_identity_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      state.stub != nullptr) {
    AddFailure(state,
               phase2_post_call_list_identity_failure_already_installed);
    return false;
  }
  Phase2PostCallListIdentityStateV1 *expected = nullptr;
  if (!g_active_observer.compare_exchange_strong(
          expected, &state, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    AddFailure(state,
               phase2_post_call_list_identity_failure_already_installed);
    return false;
  }
  state.module_base = environment.module_base;
  state.patch_target = Resolve(environment.patch_target_override,
                               state.module_base,
                               kPhase2PostCallListIdentityPatchRvaV1);
  state.continue_target = Resolve(environment.continue_target_override,
                                  state.module_base,
                                  kPhase2PostCallListIdentityContinueRvaV1);
  state.null_target = Resolve(environment.null_target_override,
                              state.module_base,
                              kPhase2PostCallListIdentityNullTargetRvaV1);
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
      : &DefaultFlush;
  const auto virtual_alloc = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override
      : &DefaultVirtualAlloc;
  if (state.patch_target == 0 || state.continue_target == 0 ||
      state.null_target == 0 ||
      state.continue_target !=
          state.patch_target + kPhase2PostCallListIdentityPatchBytesV1 ||
      !SafeBytesEqual(state.patch_target, kPatchAnchor.data(),
                      kPatchAnchor.size()) ||
      !SafeCopyFrom(state.patch_target, state.original_patch_bytes.data(),
                    state.original_patch_bytes.size())) {
    AddFailure(state, phase2_post_call_list_identity_failure_anchor);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  ResetTelemetry(state);
  state.stub = virtual_alloc(state.memory_context,
                             kPhase2PostCallListIdentityStubBytesV1,
                             MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub == nullptr) {
    AddFailure(state, phase2_post_call_list_identity_failure_allocation);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  std::array<std::uint8_t, kPhase2PostCallListIdentityStubBytesV1> stub{};
  if (!BuildStub(state, stub) ||
      !SafeCopyTo(reinterpret_cast<std::uintptr_t>(state.stub), stub.data(),
                  stub.size())) {
    AddFailure(state, phase2_post_call_list_identity_failure_allocation);
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
    AddFailure(state,
               phase2_post_call_list_identity_failure_stub_protection);
    (void)ReleaseStub(state);
    ClearResolved(state);
    g_active_observer.store(nullptr, std::memory_order_release);
    return false;
  }
  BuildPatch(reinterpret_cast<std::uintptr_t>(state.stub),
             state.installed_patch_bytes);
  const auto write = WriteTarget(state, state.original_patch_bytes.data(),
                                 state.installed_patch_bytes.data());
  if (write != WriteResult::success) {
    if (write == WriteResult::original_preserved) {
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

bool UninstallPhase2PostCallListIdentityObserverV1(
    Phase2PostCallListIdentityStateV1 &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active_observer.load(std::memory_order_acquire) != &state ||
      state.stub == nullptr) {
    AddFailure(state,
               phase2_post_call_list_identity_failure_already_installed);
    return false;
  }
  const auto write = WriteTarget(state, state.installed_patch_bytes.data(),
                                 state.original_patch_bytes.data());
  if (write != WriteResult::success) {
    AddFailure(state, phase2_post_call_list_identity_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active_observer.store(nullptr, std::memory_order_release);
  const bool released = ReleaseStub(state);
  if (released) ClearResolved(state);
  return released;
}

Phase2PostCallListIdentityDiagnosticsV1
ReadPhase2PostCallListIdentityDiagnosticsV1(
    const Phase2PostCallListIdentityStateV1 &state) noexcept {
  Phase2PostCallListIdentityDiagnosticsV1 output{};
  output.installed = state.installed.load(std::memory_order_acquire) != 0;
  output.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  output.hit_count = state.hit_count.load(std::memory_order_relaxed);
  output.capture_count = state.capture_count.load(std::memory_order_relaxed);
  output.capture_contention_count =
      state.capture_contention_count.load(std::memory_order_relaxed);
  for (int attempt = 0; attempt < 4; ++attempt) {
    const auto before = state.snapshot_sequence.load(std::memory_order_acquire);
    if ((before & 1U) != 0) continue;
    LoadDiagnostics(state, output);
    const auto after = state.snapshot_sequence.load(std::memory_order_acquire);
    if (before == after && (after & 1U) == 0) {
      output.snapshot_sequence = after;
      output.snapshot_consistent = true;
      break;
    }
  }
  return output;
}

} // namespace xar::bridge
