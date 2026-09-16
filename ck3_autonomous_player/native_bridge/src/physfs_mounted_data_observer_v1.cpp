#include "xar_bridge/physfs_mounted_data_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <intrin.h>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "PhysFS Mounted Data observer is x64-only");
static_assert(kPhysfsMountedDataPathBytesV1 % sizeof(std::uint64_t) == 0);

constexpr std::array<std::uint8_t, kPhysfsMountedDataPatchBytesV1> kCallAnchor{
    0xE8, 0x9E, 0x4A, 0x08, 0x00};
constexpr std::size_t kMaximumStubBytes = 128;

std::atomic<PhysfsMountedDataObserverV1State *> g_active{nullptr};

void AddFailure(PhysfsMountedDataObserverV1State &state,
                PhysfsMountedDataObserverFailureV1 failure) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
}

bool SafeAdd(std::uintptr_t base, std::uintptr_t offset,
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
  return SafeAdd(module_base, rva, output) ? output : 0;
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

bool BytesEqual(std::uintptr_t address, const std::uint8_t *expected,
                std::size_t size) noexcept {
  std::array<std::uint8_t, kPhysfsMountedDataPatchBytesV1> actual{};
  return expected != nullptr && size <= actual.size() &&
      SafeCopyFrom(address, actual.data(), size) &&
      std::memcmp(actual.data(), expected, size) == 0;
}

std::uint32_t CurrentThreadIdFast() noexcept {
#if defined(_M_X64)
  return __readgsdword(0x48);
#else
  return 0;
#endif
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
void EmitRelocatedCall(std::array<std::uint8_t, Size> &output,
                       std::size_t &cursor,
                       std::uintptr_t target) noexcept {
  // call qword ptr [rip+2]; jmp short +8; dq target.  This preserves the
  // incoming RAX value that the original direct call did not modify.
  Emit(output, cursor, {0xFF, 0x15, 0x02, 0x00, 0x00, 0x00, 0xEB, 0x08});
  EmitU64(output, cursor, target);
}

extern "C" void PhysfsMountedDataThunkV1(
    std::uintptr_t path, std::uint32_t raw_result) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state == nullptr) return;
  RecordPhysfsMountedDataV1(*state, path, raw_result, CurrentThreadIdFast());
}

std::size_t BuildStub(
    const PhysfsMountedDataObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  Emit(stub, cursor, {0x48, 0x83, 0xEC, 0x38});       // sub rsp,38h
  Emit(stub, cursor, {0x48, 0x89, 0x54, 0x24, 0x28}); // save path
  EmitRelocatedCall(stub, cursor, state.publisher_target);
  Emit(stub, cursor, {0x89, 0x44, 0x24, 0x20});       // save eax
  Emit(stub, cursor, {0x48, 0x8B, 0x4C, 0x24, 0x28}); // rcx=path
  Emit(stub, cursor, {0x8B, 0x54, 0x24, 0x20});       // edx=result
  Emit(stub, cursor, {0x48, 0xB8});
  EmitU64(stub, cursor,
          reinterpret_cast<std::uintptr_t>(&PhysfsMountedDataThunkV1));
  Emit(stub, cursor, {0xFF, 0xD0});                   // call thunk
  Emit(stub, cursor, {0x8B, 0x44, 0x24, 0x20});       // restore eax
  Emit(stub, cursor, {0x48, 0x83, 0xC4, 0x38, 0xC3}); // add rsp,38h; ret
  return cursor;
}

bool BuildRelativeCall(std::uintptr_t source, std::uintptr_t destination,
                       std::array<std::uint8_t,
                                  kPhysfsMountedDataPatchBytesV1> &patch)
    noexcept {
  const auto next = source + kPhysfsMountedDataPatchBytesV1;
  const auto delta = static_cast<std::int64_t>(destination) -
      static_cast<std::int64_t>(next);
  if (delta < std::numeric_limits<std::int32_t>::min() ||
      delta > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  patch[0] = 0xE8;
  const auto displacement = static_cast<std::int32_t>(delta);
  std::memcpy(patch.data() + 1, &displacement, sizeof(displacement));
  return true;
}

bool BoundsForBranch(std::uintptr_t source, std::uintptr_t &lower,
                     std::uintptr_t &upper) noexcept {
  std::uintptr_t next = 0;
  if (!SafeAdd(source, kPhysfsMountedDataPatchBytesV1, next)) return false;
  constexpr auto backward = static_cast<std::uintptr_t>(0x80000000ULL);
  constexpr auto forward = static_cast<std::uintptr_t>(0x7FFFFFFFULL);
  lower = next >= backward ? next - backward : 0;
  if (next > std::numeric_limits<std::uintptr_t>::max() - forward) return false;
  upper = next + forward;
  return true;
}

void *DefaultAllocNear(void *, std::uintptr_t lower_bound,
                       std::uintptr_t upper_bound, std::size_t size,
                       DWORD allocation_type, DWORD protection) noexcept {
  SYSTEM_INFO info{};
  GetSystemInfo(&info);
  const auto granularity = static_cast<std::uintptr_t>(
      info.dwAllocationGranularity == 0 ? 0x10000
                                        : info.dwAllocationGranularity);
  const auto align_up = [granularity](std::uintptr_t value) noexcept {
    const auto remainder = value % granularity;
    if (remainder == 0) return value;
    const auto add = granularity - remainder;
    return value > std::numeric_limits<std::uintptr_t>::max() - add
        ? std::numeric_limits<std::uintptr_t>::max()
        : value + add;
  };
  std::uintptr_t cursor = align_up(std::max<std::uintptr_t>(
      lower_bound,
      reinterpret_cast<std::uintptr_t>(info.lpMinimumApplicationAddress)));
  const auto maximum = std::min<std::uintptr_t>(
      upper_bound,
      reinterpret_cast<std::uintptr_t>(info.lpMaximumApplicationAddress));
  while (cursor <= maximum && size <= maximum - cursor + 1) {
    MEMORY_BASIC_INFORMATION region{};
    if (VirtualQuery(reinterpret_cast<const void *>(cursor), &region,
                     sizeof(region)) == 0) {
      break;
    }
    const auto region_base =
        reinterpret_cast<std::uintptr_t>(region.BaseAddress);
    std::uintptr_t region_end = 0;
    if (!SafeAdd(region_base, region.RegionSize, region_end) ||
        region_end <= cursor) {
      break;
    }
    if (region.State == MEM_FREE) {
      const auto candidate = align_up(std::max(cursor, region_base));
      if (candidate <= maximum && size <= maximum - candidate + 1 &&
          size <= region_end - candidate) {
        if (auto *allocation = VirtualAlloc(
                reinterpret_cast<void *>(candidate), size, allocation_type,
                protection)) {
          return allocation;
        }
      }
    }
    cursor = align_up(region_end);
  }
  return nullptr;
}

bool DefaultFree(void *, void *address, std::size_t size,
                 DWORD free_type) noexcept {
  return VirtualFree(address, size, free_type) != FALSE;
}

bool DefaultProtect(void *, void *address, std::size_t size,
                    DWORD protection, DWORD &old_protection) noexcept {
  old_protection = 0;
  return VirtualProtect(address, size, protection, &old_protection) != FALSE;
}

bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool Executable(DWORD protection) noexcept {
  return protection == PAGE_EXECUTE_READ ||
      protection == PAGE_EXECUTE_READWRITE ||
      protection == PAGE_EXECUTE_WRITECOPY;
}

bool Flush(PhysfsMountedDataObserverV1State &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, physfs_mounted_data_observer_failure_flush);
    return false;
  }
  return true;
}

bool WritePatch(PhysfsMountedDataObserverV1State &state,
                const std::uint8_t *expected,
                const std::uint8_t *desired) noexcept {
  if (!BytesEqual(state.patch_target, expected,
                  kPhysfsMountedDataPatchBytesV1)) {
    AddFailure(state,
               physfs_mounted_data_observer_failure_target_identity);
    return false;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kPhysfsMountedDataPatchBytesV1, PAGE_EXECUTE_READWRITE, previous);
  if (!writable || !Executable(previous)) {
    if (writable) {
      DWORD ignored = 0;
      if (!state.virtual_protect(
              state.memory_context,
              reinterpret_cast<void *>(state.patch_target),
              kPhysfsMountedDataPatchBytesV1, previous, ignored)) {
        AddFailure(state, physfs_mounted_data_observer_failure_rollback);
      }
    }
    AddFailure(state,
               physfs_mounted_data_observer_failure_target_protection);
    return false;
  }
  const bool copied = SafeCopyTo(state.patch_target, desired,
                                 kPhysfsMountedDataPatchBytesV1);
  const bool identity = copied &&
      BytesEqual(state.patch_target, desired, kPhysfsMountedDataPatchBytesV1);
  const bool flushed = identity &&
      Flush(state, reinterpret_cast<const void *>(state.patch_target),
            kPhysfsMountedDataPatchBytesV1);
  DWORD ignored = 0;
  const bool protected_again = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kPhysfsMountedDataPatchBytesV1, previous, ignored);
  if (identity && flushed && protected_again) return true;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(state.patch_target),
      kPhysfsMountedDataPatchBytesV1, PAGE_EXECUTE_READWRITE,
      rollback_previous);
  const bool rollback_written = rollback_writable &&
      SafeCopyTo(state.patch_target, expected, kPhysfsMountedDataPatchBytesV1);
  const bool rollback_identity = rollback_written &&
      BytesEqual(state.patch_target, expected, kPhysfsMountedDataPatchBytesV1);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kPhysfsMountedDataPatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable &&
      state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(state.patch_target),
          kPhysfsMountedDataPatchBytesV1, previous, rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state, physfs_mounted_data_observer_failure_rollback);
  }
  return false;
}

bool HasOverrides(
    const PhysfsMountedDataObserverEnvironmentV1 &environment) noexcept {
  return environment.patch_target_override != 0 ||
      environment.publisher_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_near_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

void ClearRuntime(PhysfsMountedDataObserverV1State &state) noexcept {
  state.module_base = 0;
  state.patch_target = 0;
  state.publisher_target = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
}

void ReleaseStub(PhysfsMountedDataObserverV1State &state) noexcept {
  if (state.stub_allocation == nullptr) return;
  if (state.virtual_free == nullptr ||
      !state.virtual_free(state.memory_context, state.stub_allocation, 0,
                          MEM_RELEASE)) {
    AddFailure(state, physfs_mounted_data_observer_failure_rollback);
    return;
  }
  state.stub_allocation = nullptr;
}

PhysfsMountedDataRowDiagnosticsV1 ReadRow(
    const PhysfsMountedDataSlotV1 &slot) noexcept {
  PhysfsMountedDataRowDiagnosticsV1 row{};
  row.ordinal = slot.published_ordinal.load(std::memory_order_acquire);
  row.thread_id = slot.thread_id.load(std::memory_order_relaxed);
  row.raw_result = slot.raw_result.load(std::memory_order_relaxed);
  row.success = row.raw_result != 0;
  row.preview_length = slot.preview_length.load(std::memory_order_relaxed);
  row.terminated = slot.terminated.load(std::memory_order_relaxed) != 0;
  row.null_pointer = slot.null_pointer.load(std::memory_order_relaxed) != 0;
  row.read_fault = slot.read_fault.load(std::memory_order_relaxed) != 0;
  for (std::size_t index = 0; index < slot.preview.size(); ++index) {
    const auto word = slot.preview[index].load(std::memory_order_relaxed);
    std::memcpy(row.preview.data() + index * sizeof(word), &word,
                sizeof(word));
  }
  return row;
}

} // namespace

void RecordPhysfsMountedDataV1(PhysfsMountedDataObserverV1State &state,
                               std::uintptr_t path,
                               std::uint32_t raw_result,
                               std::uint32_t thread_id) noexcept {
  const auto ordinal = state.call_count.fetch_add(1, std::memory_order_relaxed) + 1;
  auto &slot = state.slots[(ordinal - 1) % state.slots.size()];
  if (slot.published_ordinal.load(std::memory_order_acquire) != 0) {
    state.slot_overwrite_count.fetch_add(1, std::memory_order_relaxed);
  }
  slot.published_ordinal.store(0, std::memory_order_release);
  slot.thread_id.store(thread_id, std::memory_order_relaxed);
  slot.raw_result.store(raw_result, std::memory_order_relaxed);
  slot.preview_length.store(0, std::memory_order_relaxed);
  slot.terminated.store(0, std::memory_order_relaxed);
  slot.null_pointer.store(path == 0 ? 1U : 0U, std::memory_order_relaxed);
  slot.read_fault.store(0, std::memory_order_relaxed);
  for (auto &word : slot.preview) word.store(0, std::memory_order_relaxed);
  if (path != 0) {
    std::array<std::uint8_t, kPhysfsMountedDataPathBytesV1> preview{};
    std::uint32_t length = 0;
    bool terminated = false;
    bool read_fault = false;
    for (std::size_t index = 0; index < preview.size(); ++index) {
      std::uint8_t value = 0;
      std::uintptr_t address = 0;
      if (!SafeAdd(path, index, address) ||
          !SafeCopyFrom(address, &value, sizeof(value))) {
        read_fault = true;
        break;
      }
      if (value == 0) {
        terminated = true;
        break;
      }
      preview[index] = value;
      ++length;
    }
    for (std::size_t index = 0; index < slot.preview.size(); ++index) {
      std::uint64_t word = 0;
      std::memcpy(&word, preview.data() + index * sizeof(word), sizeof(word));
      slot.preview[index].store(word, std::memory_order_relaxed);
    }
    slot.preview_length.store(length, std::memory_order_relaxed);
    slot.terminated.store(terminated ? 1U : 0U, std::memory_order_relaxed);
    slot.read_fault.store(read_fault ? 1U : 0U, std::memory_order_relaxed);
  }
  slot.published_ordinal.store(ordinal, std::memory_order_release);
  (raw_result != 0 ? state.success_count : state.failure_count)
      .fetch_add(1, std::memory_order_release);
}

bool InstallPhysfsMountedDataObserverV1(
    PhysfsMountedDataObserverV1State &state,
    const PhysfsMountedDataObserverEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(physfs_mounted_data_observer_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, physfs_mounted_data_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        physfs_mounted_data_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture && HasOverrides(environment)) {
    AddFailure(state,
               physfs_mounted_data_observer_failure_unsupported_override);
    return false;
  }
  PhysfsMountedDataObserverV1State *expected = nullptr;
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      !g_active.compare_exchange_strong(expected, &state,
                                        std::memory_order_acq_rel,
                                        std::memory_order_acquire)) {
    AddFailure(state,
               physfs_mounted_data_observer_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.patch_target = Resolve(environment.patch_target_override,
                               environment.module_base,
                               kPhysfsMountedDataCallRvaV1);
  state.publisher_target = Resolve(environment.publisher_target_override,
                                   environment.module_base,
                                   kPhysfsMountedDataPublisherRvaV1);
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override
      : &DefaultFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override
      : &DefaultProtect;
  state.flush_instruction_cache =
      environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override
      : &DefaultFlush;
  if (state.patch_target == 0 || state.publisher_target == 0 ||
      !BytesEqual(state.patch_target, kCallAnchor.data(), kCallAnchor.size()) ||
      !SafeCopyFrom(state.patch_target, state.original.data(),
                    state.original.size())) {
    AddFailure(state, physfs_mounted_data_observer_failure_anchor);
    ClearRuntime(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }

  std::uintptr_t lower = 0;
  std::uintptr_t upper = 0;
  if (!BoundsForBranch(state.patch_target, lower, upper)) {
    AddFailure(state, physfs_mounted_data_observer_failure_stub_range);
    ClearRuntime(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_near_override != nullptr
      ? environment.virtual_alloc_near_override
      : &DefaultAllocNear;
  state.stub_allocation = allocate(
      state.memory_context, lower, upper, kPhysfsMountedDataStubBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub_allocation == nullptr) {
    AddFailure(state, physfs_mounted_data_observer_failure_allocation);
    ClearRuntime(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }

  std::array<std::uint8_t, kMaximumStubBytes> stub{};
  const auto used = BuildStub(state, stub);
  const auto stub_address =
      reinterpret_cast<std::uintptr_t>(state.stub_allocation);
  if (used == 0 || used > stub.size() ||
      !BuildRelativeCall(state.patch_target, stub_address,
                         state.installed_patch) ||
      !SafeCopyTo(stub_address, stub.data(), used)) {
    AddFailure(state, physfs_mounted_data_observer_failure_stub_range);
    ReleaseStub(state);
    ClearRuntime(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, state.stub_allocation,
                             kPhysfsMountedDataStubBytesV1,
                             PAGE_EXECUTE_READ, old) ||
      !Flush(state, state.stub_allocation, kPhysfsMountedDataStubBytesV1)) {
    AddFailure(state,
               physfs_mounted_data_observer_failure_stub_protection);
    ReleaseStub(state);
    ClearRuntime(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  if (!WritePatch(state, state.original.data(),
                  state.installed_patch.data())) {
    ReleaseStub(state);
    ClearRuntime(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallPhysfsMountedDataObserverV1(
    PhysfsMountedDataObserverV1State &state) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 ||
      g_active.load(std::memory_order_acquire) != &state) {
    AddFailure(state,
               physfs_mounted_data_observer_failure_already_installed);
    return false;
  }
  if (!WritePatch(state, state.installed_patch.data(), state.original.data())) {
    AddFailure(state, physfs_mounted_data_observer_failure_rollback);
    return false;
  }
  state.installed.store(0, std::memory_order_release);
  g_active.store(nullptr, std::memory_order_release);
  ReleaseStub(state);
  const bool released = state.stub_allocation == nullptr;
  if (released) ClearRuntime(state);
  return released;
}

PhysfsMountedDataObserverV1Diagnostics
ReadPhysfsMountedDataObserverV1Diagnostics(
    const PhysfsMountedDataObserverV1State &state) noexcept {
  PhysfsMountedDataObserverV1Diagnostics result{};
  result.installed = state.installed.load(std::memory_order_acquire) != 0;
  result.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  result.call_count = state.call_count.load(std::memory_order_acquire);
  result.success_count = state.success_count.load(std::memory_order_acquire);
  result.failure_count = state.failure_count.load(std::memory_order_acquire);
  result.slot_overwrite_count =
      state.slot_overwrite_count.load(std::memory_order_acquire);
  for (const auto &slot : state.slots) {
    const auto first = slot.published_ordinal.load(std::memory_order_acquire);
    if (first == 0) continue;
    const auto row = ReadRow(slot);
    const auto second = slot.published_ordinal.load(std::memory_order_acquire);
    if (first != second || row.ordinal != second ||
        result.row_count >= result.rows.size()) {
      continue;
    }
    result.rows[result.row_count++] = row;
  }
  std::sort(result.rows.begin(), result.rows.begin() + result.row_count,
            [](const PhysfsMountedDataRowDiagnosticsV1 &left,
               const PhysfsMountedDataRowDiagnosticsV1 &right) {
              return left.ordinal < right.ordinal;
            });
  return result;
}

} // namespace xar::bridge
