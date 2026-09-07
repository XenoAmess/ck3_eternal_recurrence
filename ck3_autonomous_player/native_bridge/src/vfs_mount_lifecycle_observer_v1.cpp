#include "xar_bridge/vfs_mount_lifecycle_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <intrin.h>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "VFS mount lifecycle observer is x64-only");
static_assert(kVfsMountLifecyclePathPreviewBytesV1 % sizeof(std::uint64_t) ==
              0);

constexpr std::array<std::size_t, kVfsMountLifecycleHookCountV1> kStubOffsets{
    0, 512, 1024, 1536};
constexpr std::size_t kMaximumStubBytes = 512;
constexpr std::array<std::uint8_t, 5> kCoreInitCallAnchor{
    0xE8, 0xD5, 0x52, 0x37, 0x03};
constexpr std::array<std::uint8_t, 5> kPublisherEntryAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08};
constexpr std::array<std::uint8_t, 5> kPublisherReturnAnchor{
    0x4C, 0x8D, 0x5C, 0x24, 0x50};
constexpr std::array<std::uint8_t, 8> kSettingsLookupAnchor{
    0x48, 0x63, 0x4E, 0x08, 0x48, 0x8B, 0x53, 0x38};
constexpr std::array<std::uint8_t, 14> kPathsSettings{
    'p', 'a', 't', 'h', 's', '.', 's', 'e', 't', 't', 'i', 'n', 'g', 's'};
constexpr std::array<std::uint8_t, 26> kChecksummedSettings{
    'p', 'a', 't', 'h', 's', '_', 'c', 'h', 'e', 'c', 'k', 's', 'u',
    'm', 'm', 'e', 'd', '.', 's', 'e', 't', 't', 'i', 'n', 'g', 's'};

std::atomic<VfsMountLifecycleObserverV1State *> g_active{nullptr};

struct ManagerSnapshot {
  std::uint64_t manager = 0;
  std::uint64_t head = 0;
  std::uint32_t ready_flag = 0;
  bool read_fault = false;
};

struct PathSnapshot {
  std::uint64_t pointer = 0;
  std::uint32_t preview_length = 0;
  bool terminated = false;
  bool null_pointer = false;
  bool read_fault = false;
  std::array<std::uint8_t, kVfsMountLifecyclePathPreviewBytesV1> preview{};
};

void AddFailure(VfsMountLifecycleObserverV1State &state,
                VfsMountLifecycleObserverFailureV1 failure) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(failure),
                               std::memory_order_acq_rel);
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

bool SafeAdd(std::uintptr_t base, std::uintptr_t offset,
             std::uintptr_t &output) noexcept {
  if (offset > std::numeric_limits<std::uintptr_t>::max() - base) {
    output = 0;
    return false;
  }
  output = base + offset;
  return true;
}

bool SafeBytesEqual(std::uintptr_t address, const std::uint8_t *expected,
                    std::size_t size) noexcept {
  std::array<std::uint8_t, kVfsMountLifecycleMaximumPatchBytesV1> actual{};
  return expected != nullptr && size <= actual.size() &&
      SafeCopyFrom(address, actual.data(), size) &&
      std::memcmp(actual.data(), expected, size) == 0;
}

std::uintptr_t Resolve(std::uintptr_t override_address,
                       std::uintptr_t module_base,
                       std::uintptr_t rva) noexcept {
  if (override_address != 0) return override_address;
  std::uintptr_t output = 0;
  return SafeAdd(module_base, rva, output) ? output : 0;
}

std::uint32_t CurrentThreadIdFast() noexcept {
#if defined(_M_X64)
  return __readgsdword(0x48);
#else
  return 0;
#endif
}

ManagerSnapshot CaptureManager(std::uintptr_t manager) noexcept {
  ManagerSnapshot result{};
  result.manager = manager;
  if (manager == 0) return result;
  std::uintptr_t head_address = 0;
  std::uintptr_t ready_address = 0;
  std::uint8_t ready = 0;
  if (!SafeAdd(manager, 0x08, head_address) ||
      !SafeAdd(manager, 0xFA, ready_address) ||
      !SafeCopyFrom(head_address, &result.head, sizeof(result.head)) ||
      !SafeCopyFrom(ready_address, &ready, sizeof(ready))) {
    result.read_fault = true;
    return result;
  }
  result.ready_flag = ready;
  return result;
}

PathSnapshot CapturePath(std::uintptr_t pointer) noexcept {
  PathSnapshot result{};
  result.pointer = pointer;
  if (pointer == 0) {
    result.null_pointer = true;
    return result;
  }
  for (std::size_t index = 0; index < result.preview.size(); ++index) {
    std::uint8_t value = 0;
    std::uintptr_t address = 0;
    if (!SafeAdd(pointer, index, address) ||
        !SafeCopyFrom(address, &value, sizeof(value))) {
      result.read_fault = true;
      return result;
    }
    if (value == 0) {
      result.terminated = true;
      return result;
    }
    result.preview[index] = value;
    ++result.preview_length;
  }
  return result;
}

void StoreManager(VfsMountManagerObservationV1 &destination,
                  const ManagerSnapshot &source) noexcept {
  destination.manager.store(source.manager, std::memory_order_relaxed);
  destination.head.store(source.head, std::memory_order_relaxed);
  destination.ready_flag.store(source.ready_flag, std::memory_order_relaxed);
  destination.read_fault.store(source.read_fault ? 1U : 0U,
                               std::memory_order_release);
}

void StorePath(VfsMountPathObservationV1 &destination,
               const PathSnapshot &source) noexcept {
  destination.pointer.store(source.pointer, std::memory_order_relaxed);
  destination.preview_length.store(source.preview_length,
                                   std::memory_order_relaxed);
  destination.terminated.store(source.terminated ? 1U : 0U,
                               std::memory_order_relaxed);
  destination.null_pointer.store(source.null_pointer ? 1U : 0U,
                                 std::memory_order_relaxed);
  destination.read_fault.store(source.read_fault ? 1U : 0U,
                               std::memory_order_relaxed);
  for (std::size_t index = 0; index < destination.preview.size(); ++index) {
    std::uint64_t word = 0;
    std::memcpy(&word, source.preview.data() + index * sizeof(word),
                sizeof(word));
    destination.preview[index].store(word, std::memory_order_relaxed);
  }
}

void ClearPublisherSlot(VfsMountPublisherSlotV1 &slot) noexcept {
  slot.entry_sequence.store(0, std::memory_order_relaxed);
  slot.return_sequence.store(0, std::memory_order_relaxed);
  slot.entry_thread_id.store(0, std::memory_order_relaxed);
  slot.return_thread_id.store(0, std::memory_order_relaxed);
  slot.return_seen.store(0, std::memory_order_relaxed);
  slot.raw_result.store(0, std::memory_order_relaxed);
  slot.raw_rcx.store(0, std::memory_order_relaxed);
  slot.backend.store(0, std::memory_order_relaxed);
  slot.insert_mode.store(0, std::memory_order_relaxed);
  StorePath(slot.path, {});
  StoreManager(slot.manager_before, {});
  StoreManager(slot.manager_after, {});
}

VfsMountPublisherSlotV1 *FindLatestUnreturnedPublisher(
    VfsMountLifecycleObserverV1State &state,
    std::uint32_t thread_id) noexcept {
  VfsMountPublisherSlotV1 *result = nullptr;
  std::uint64_t best = 0;
  for (auto &slot : state.publisher_slots) {
    const auto first = slot.published_ordinal.load(std::memory_order_acquire);
    if (first == 0 ||
        slot.entry_thread_id.load(std::memory_order_relaxed) != thread_id ||
        slot.return_seen.load(std::memory_order_acquire) != 0) {
      continue;
    }
    const auto second = slot.published_ordinal.load(std::memory_order_acquire);
    if (first == second && first > best) {
      best = first;
      result = &slot;
    }
  }
  return result;
}

const VfsMountPublisherSlotV1 *FindPublisherBySequence(
    const VfsMountLifecycleObserverV1State &state,
    std::uint64_t sequence) noexcept {
  if (sequence == 0) return nullptr;
  for (const auto &slot : state.publisher_slots) {
    const auto first = slot.published_ordinal.load(std::memory_order_acquire);
    if (first == 0) continue;
    const auto entry = slot.entry_sequence.load(std::memory_order_relaxed);
    const auto returned = slot.return_sequence.load(std::memory_order_relaxed);
    const auto second = slot.published_ordinal.load(std::memory_order_acquire);
    if (first == second && (entry == sequence || returned == sequence)) {
      return &slot;
    }
  }
  return nullptr;
}

VfsMountManagerDiagnosticsV1 ReadManager(
    const VfsMountManagerObservationV1 &source) noexcept {
  VfsMountManagerDiagnosticsV1 result{};
  result.manager = source.manager.load(std::memory_order_acquire);
  result.head = source.head.load(std::memory_order_acquire);
  result.ready_flag = source.ready_flag.load(std::memory_order_acquire);
  result.read_fault = source.read_fault.load(std::memory_order_acquire) != 0;
  return result;
}

VfsMountPathDiagnosticsV1 ReadPath(
    const VfsMountPathObservationV1 &source) noexcept {
  VfsMountPathDiagnosticsV1 result{};
  result.pointer = source.pointer.load(std::memory_order_acquire);
  result.preview_length = source.preview_length.load(std::memory_order_acquire);
  result.terminated = source.terminated.load(std::memory_order_acquire) != 0;
  result.null_pointer = source.null_pointer.load(std::memory_order_acquire) != 0;
  result.read_fault = source.read_fault.load(std::memory_order_acquire) != 0;
  for (std::size_t index = 0; index < source.preview.size(); ++index) {
    const auto word = source.preview[index].load(std::memory_order_acquire);
    std::memcpy(result.preview.data() + index * sizeof(word), &word,
                sizeof(word));
  }
  return result;
}

VfsMountPublisherDiagnosticsV1 ReadPublisher(
    const VfsMountPublisherSlotV1 &source) noexcept {
  VfsMountPublisherDiagnosticsV1 result{};
  result.ordinal = source.published_ordinal.load(std::memory_order_acquire);
  result.entry_sequence = source.entry_sequence.load(std::memory_order_acquire);
  result.return_sequence =
      source.return_sequence.load(std::memory_order_acquire);
  result.entry_thread_id =
      source.entry_thread_id.load(std::memory_order_acquire);
  result.return_thread_id =
      source.return_thread_id.load(std::memory_order_acquire);
  result.return_seen = source.return_seen.load(std::memory_order_acquire) != 0;
  result.raw_result = source.raw_result.load(std::memory_order_acquire);
  result.raw_rcx = source.raw_rcx.load(std::memory_order_acquire);
  result.backend = source.backend.load(std::memory_order_acquire);
  result.insert_mode = source.insert_mode.load(std::memory_order_acquire);
  result.path = ReadPath(source.path);
  result.manager_before = ReadManager(source.manager_before);
  result.manager_after = ReadManager(source.manager_after);
  return result;
}

VfsSettingsLookupDiagnosticsV1 ReadLookup(
    const VfsSettingsLookupObservationV1 &source) noexcept {
  VfsSettingsLookupDiagnosticsV1 result{};
  result.count = source.count.load(std::memory_order_acquire);
  result.path_view = source.path_view.load(std::memory_order_acquire);
  result.path_data = source.path_data.load(std::memory_order_acquire);
  result.path_length = source.path_length.load(std::memory_order_acquire);
  result.path_flag = source.path_flag.load(std::memory_order_acquire);
  result.thread_id = source.thread_id.load(std::memory_order_acquire);
  result.read_fault = source.read_fault.load(std::memory_order_acquire) != 0;
  result.sequence = source.sequence.load(std::memory_order_acquire);
  result.manager = ReadManager(source.manager);
  return result;
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
void EmitAbsoluteCall(std::array<std::uint8_t, Size> &output,
                      std::size_t &cursor, std::uintptr_t target) noexcept {
  Emit(output, cursor, {0xFF, 0x15, 0x02, 0x00, 0x00, 0x00, 0xEB, 0x08});
  EmitU64(output, cursor, target);
}

template <std::size_t Size>
void EmitAbsoluteJump(std::array<std::uint8_t, Size> &output,
                      std::size_t &cursor, std::uintptr_t target) noexcept {
  Emit(output, cursor, {0xFF, 0x25, 0x00, 0x00, 0x00, 0x00});
  EmitU64(output, cursor, target);
}

template <std::size_t Size>
void EmitThunkCall(std::array<std::uint8_t, Size> &output,
                   std::size_t &cursor, std::uintptr_t target) noexcept {
  Emit(output, cursor, {0x48, 0xB8});
  EmitU64(output, cursor, target);
  Emit(output, cursor, {0xFF, 0xD0});
}

template <std::size_t Size>
void EmitPreserveMidFunctionVolatile(
    std::array<std::uint8_t, Size> &output, std::size_t &cursor) noexcept {
  Emit(output, cursor,
       {0x9C, 0x50, 0x51, 0x52, 0x41, 0x50, 0x41, 0x51,
        0x41, 0x52, 0x41, 0x53, 0x48, 0x81, 0xEC, 0x80,
        0x00, 0x00, 0x00});
  Emit(output, cursor, {0xF3, 0x0F, 0x7F, 0x44, 0x24, 0x20});
  Emit(output, cursor, {0xF3, 0x0F, 0x7F, 0x4C, 0x24, 0x30});
  Emit(output, cursor, {0xF3, 0x0F, 0x7F, 0x54, 0x24, 0x40});
  Emit(output, cursor, {0xF3, 0x0F, 0x7F, 0x5C, 0x24, 0x50});
  Emit(output, cursor, {0xF3, 0x0F, 0x7F, 0x64, 0x24, 0x60});
  Emit(output, cursor, {0xF3, 0x0F, 0x7F, 0x6C, 0x24, 0x70});
}

template <std::size_t Size>
void EmitRestoreMidFunctionVolatile(
    std::array<std::uint8_t, Size> &output, std::size_t &cursor) noexcept {
  Emit(output, cursor, {0xF3, 0x0F, 0x6F, 0x44, 0x24, 0x20});
  Emit(output, cursor, {0xF3, 0x0F, 0x6F, 0x4C, 0x24, 0x30});
  Emit(output, cursor, {0xF3, 0x0F, 0x6F, 0x54, 0x24, 0x40});
  Emit(output, cursor, {0xF3, 0x0F, 0x6F, 0x5C, 0x24, 0x50});
  Emit(output, cursor, {0xF3, 0x0F, 0x6F, 0x64, 0x24, 0x60});
  Emit(output, cursor, {0xF3, 0x0F, 0x6F, 0x6C, 0x24, 0x70});
  Emit(output, cursor,
       {0x48, 0x81, 0xC4, 0x80, 0x00, 0x00, 0x00,
        0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59, 0x41, 0x58,
        0x5A, 0x59, 0x58, 0x9D});
}

extern "C" void VfsMountLifecycleCoreInitThunkV1(
    std::uintptr_t raw_result) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordVfsCoreInitReturnV1(*state, raw_result, CurrentThreadIdFast());
  }
}

extern "C" void VfsMountLifecyclePublisherEntryThunkV1(
    std::uintptr_t raw_rcx, std::uintptr_t path,
    std::uintptr_t backend, std::uint32_t insert_mode) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordVfsMountPublisherEnterV1(*state, raw_rcx, path, backend,
                                   insert_mode, CurrentThreadIdFast());
  }
}

extern "C" void VfsMountLifecyclePublisherReturnThunkV1(
    std::uint32_t raw_result) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordVfsMountPublisherReturnV1(*state, raw_result,
                                    CurrentThreadIdFast());
  }
}

extern "C" void VfsMountLifecycleSettingsLookupThunkV1(
    std::uintptr_t path_view, std::uintptr_t manager) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordVfsSettingsLookupV1(*state, path_view, manager,
                              CurrentThreadIdFast());
  }
}

std::size_t BuildCoreInitCallStub(
    const VfsMountLifecycleObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  Emit(stub, cursor, {0x48, 0x83, 0xEC, 0x28});
  EmitAbsoluteCall(stub, cursor, state.core_init_target);
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0xC8});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(
                    &VfsMountLifecycleCoreInitThunkV1));
  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x83, 0xC4, 0x28, 0xC3});
  return cursor;
}

std::size_t BuildPublisherEntryStub(
    const VfsMountLifecycleObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  Emit(stub, cursor, {0x48, 0x89, 0x5C, 0x24, 0x08});
  Emit(stub, cursor, {0x48, 0x81, 0xEC, 0xA8, 0x00, 0x00, 0x00});
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x89, 0x4C, 0x24, 0x28});
  Emit(stub, cursor, {0x48, 0x89, 0x54, 0x24, 0x30});
  Emit(stub, cursor, {0x4C, 0x89, 0x44, 0x24, 0x38});
  Emit(stub, cursor, {0x4C, 0x89, 0x4C, 0x24, 0x40});
  Emit(stub, cursor, {0x4C, 0x89, 0x54, 0x24, 0x48});
  Emit(stub, cursor, {0x4C, 0x89, 0x5C, 0x24, 0x50});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x44, 0x24, 0x60});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x4C, 0x24, 0x70});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x54, 0x24, 0x80});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x5C, 0x24, 0x90});
  Emit(stub, cursor, {0x48, 0x8B, 0x4C, 0x24, 0x28});
  Emit(stub, cursor, {0x48, 0x8B, 0x54, 0x24, 0x30});
  Emit(stub, cursor, {0x4C, 0x8B, 0x44, 0x24, 0x38});
  Emit(stub, cursor, {0x4C, 0x8B, 0x4C, 0x24, 0x40});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(
                    &VfsMountLifecyclePublisherEntryThunkV1));
  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0x4C, 0x24, 0x28});
  Emit(stub, cursor, {0x48, 0x8B, 0x54, 0x24, 0x30});
  Emit(stub, cursor, {0x4C, 0x8B, 0x44, 0x24, 0x38});
  Emit(stub, cursor, {0x4C, 0x8B, 0x4C, 0x24, 0x40});
  Emit(stub, cursor, {0x4C, 0x8B, 0x54, 0x24, 0x48});
  Emit(stub, cursor, {0x4C, 0x8B, 0x5C, 0x24, 0x50});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x44, 0x24, 0x60});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x4C, 0x24, 0x70});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x54, 0x24, 0x80});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x5C, 0x24, 0x90});
  Emit(stub, cursor, {0x48, 0x81, 0xC4, 0xA8, 0x00, 0x00, 0x00});
  EmitAbsoluteJump(stub, cursor, state.publisher_entry_continue);
  return cursor;
}

std::size_t BuildPublisherReturnStub(
    const VfsMountLifecycleObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  Emit(stub, cursor, {0x48, 0x83, 0xEC, 0x30});
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x8B, 0xC8});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(
                    &VfsMountLifecyclePublisherReturnThunkV1));
  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x83, 0xC4, 0x30});
  Emit(stub, cursor, {0x4C, 0x8D, 0x5C, 0x24, 0x50});
  EmitAbsoluteJump(stub, cursor, state.publisher_return_continue);
  return cursor;
}

std::size_t BuildSettingsLookupStub(
    const VfsMountLifecycleObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  Emit(stub, cursor, {0x48, 0x63, 0x4E, 0x08});
  Emit(stub, cursor, {0x48, 0x8B, 0x53, 0x38});
  EmitPreserveMidFunctionVolatile(stub, cursor);
  Emit(stub, cursor, {0x48, 0x8B, 0xCE});
  Emit(stub, cursor, {0x48, 0x8D, 0x53, 0xF8});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(
                    &VfsMountLifecycleSettingsLookupThunkV1));
  EmitRestoreMidFunctionVolatile(stub, cursor);
  EmitAbsoluteJump(stub, cursor, state.settings_lookup_continue);
  return cursor;
}

bool BuildRelativeBranch(std::uintptr_t source, std::uintptr_t destination,
                         std::uint8_t opcode, std::uint8_t *output,
                         std::size_t size) noexcept {
  if (output == nullptr || size < 5) return false;
  const auto next = source + 5;
  const auto delta = static_cast<std::int64_t>(destination) -
      static_cast<std::int64_t>(next);
  if (delta < std::numeric_limits<std::int32_t>::min() ||
      delta > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  std::memset(output, 0x90, size);
  output[0] = opcode;
  const auto displacement = static_cast<std::int32_t>(delta);
  std::memcpy(output + 1, &displacement, sizeof(displacement));
  return true;
}

bool BaseBoundsForBranch(std::uintptr_t source, std::size_t stub_offset,
                         std::uintptr_t &lower,
                         std::uintptr_t &upper) noexcept {
  std::uintptr_t next = 0;
  if (!SafeAdd(source, 5, next)) return false;
  constexpr auto backward = static_cast<std::uintptr_t>(0x80000000ULL);
  constexpr auto forward = static_cast<std::uintptr_t>(0x7FFFFFFFULL);
  const auto destination_lower = next >= backward ? next - backward : 0;
  if (next > std::numeric_limits<std::uintptr_t>::max() - forward) return false;
  const auto destination_upper = next + forward;
  if (destination_upper < stub_offset) return false;
  lower = destination_lower > stub_offset ? destination_lower - stub_offset : 0;
  upper = destination_upper - stub_offset;
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

bool Flush(VfsMountLifecycleObserverV1State &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_flush);
    return false;
  }
  return true;
}

bool WriteHook(VfsMountLifecycleObserverV1State &state, std::size_t index,
               const std::uint8_t *expected,
               const std::uint8_t *desired) noexcept {
  auto &hook = state.hooks[index];
  if (!SafeBytesEqual(hook.patch_target, expected, hook.patch_size)) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_target_identity);
    return false;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(hook.patch_target),
                            hook.patch_size, PAGE_EXECUTE_READWRITE, previous);
  if (!writable || !Executable(previous)) {
    if (writable) {
      DWORD ignored = 0;
      (void)state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(hook.patch_target),
          hook.patch_size, previous, ignored);
    }
    AddFailure(state,
               vfs_mount_lifecycle_observer_failure_target_protection);
    return false;
  }
  const bool copied = SafeCopyTo(hook.patch_target, desired, hook.patch_size);
  const bool identical = copied &&
      SafeBytesEqual(hook.patch_target, desired, hook.patch_size);
  const bool flushed = identical &&
      Flush(state, reinterpret_cast<const void *>(hook.patch_target),
            hook.patch_size);
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(hook.patch_target),
      hook.patch_size, previous, ignored);
  if (identical && flushed && restored) return true;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(hook.patch_target),
      hook.patch_size, PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable &&
      SafeCopyTo(hook.patch_target, expected, hook.patch_size);
  const bool rollback_identity = rollback_written &&
      SafeBytesEqual(hook.patch_target, expected, hook.patch_size);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context, reinterpret_cast<const void *>(hook.patch_target),
          hook.patch_size);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(hook.patch_target),
                            hook.patch_size, previous, rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_rollback);
  }
  return false;
}

bool AnchorMatches(std::size_t index, std::uintptr_t address) noexcept {
  switch (index) {
    case 0:
      return SafeBytesEqual(address, kCoreInitCallAnchor.data(),
                            kCoreInitCallAnchor.size());
    case 1:
      return SafeBytesEqual(address, kPublisherEntryAnchor.data(),
                            kPublisherEntryAnchor.size());
    case 2:
      return SafeBytesEqual(address, kPublisherReturnAnchor.data(),
                            kPublisherReturnAnchor.size());
    case 3:
      return SafeBytesEqual(address, kSettingsLookupAnchor.data(),
                            kSettingsLookupAnchor.size());
    default:
      return false;
  }
}

bool HasOverrides(
    const VfsMountLifecycleObserverEnvironmentV1 &environment) noexcept {
  return environment.patch_target_overrides !=
             std::array<std::uintptr_t, kVfsMountLifecycleHookCountV1>{} ||
      environment.core_init_target_override != 0 ||
      environment.publisher_entry_continue_override != 0 ||
      environment.publisher_return_continue_override != 0 ||
      environment.settings_lookup_continue_override != 0 ||
      environment.manager_address_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_near_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

void ClearRuntime(VfsMountLifecycleObserverV1State &state) noexcept {
  state.module_base = 0;
  state.core_init_target = 0;
  state.publisher_entry_continue = 0;
  state.publisher_return_continue = 0;
  state.settings_lookup_continue = 0;
  state.manager_address = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
  for (auto &hook : state.hooks) {
    hook.patch_target = 0;
    hook.patch_size = 0;
  }
}

} // namespace

void RecordVfsCoreInitReturnV1(VfsMountLifecycleObserverV1State &state,
                               std::uintptr_t raw_result,
                               std::uint32_t thread_id) noexcept {
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  state.core_init.raw_al.store(static_cast<std::uint32_t>(raw_result & 0xFFU),
                               std::memory_order_relaxed);
  state.core_init.thread_id.store(thread_id, std::memory_order_relaxed);
  StoreManager(state.core_init.manager,
               CaptureManager(state.manager_address));
  state.core_init.sequence.store(sequence, std::memory_order_release);
  state.core_init.count.fetch_add(1, std::memory_order_release);
}

void RecordVfsMountPublisherEnterV1(
    VfsMountLifecycleObserverV1State &state, std::uintptr_t raw_rcx,
    std::uintptr_t path, std::uintptr_t backend, std::uint32_t insert_mode,
    std::uint32_t thread_id) noexcept {
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  const auto ordinal =
      state.publisher_entry_count.fetch_add(1, std::memory_order_relaxed) + 1;
  auto &slot = state.publisher_slots[(ordinal - 1) % state.publisher_slots.size()];
  const auto previous = slot.published_ordinal.load(std::memory_order_acquire);
  if (previous != 0 &&
      slot.return_seen.load(std::memory_order_acquire) == 0) {
    state.publisher_slot_overwrite_count.fetch_add(1,
                                                    std::memory_order_relaxed);
  }
  slot.published_ordinal.store(0, std::memory_order_release);
  ClearPublisherSlot(slot);
  slot.entry_sequence.store(sequence, std::memory_order_relaxed);
  slot.entry_thread_id.store(thread_id, std::memory_order_relaxed);
  slot.raw_rcx.store(raw_rcx, std::memory_order_relaxed);
  slot.backend.store(backend, std::memory_order_relaxed);
  slot.insert_mode.store(insert_mode, std::memory_order_relaxed);
  StorePath(slot.path, CapturePath(path));
  StoreManager(slot.manager_before, CaptureManager(state.manager_address));
  slot.published_ordinal.store(ordinal, std::memory_order_release);
  state.last_publisher_entry_sequence.store(sequence,
                                             std::memory_order_release);
}

void RecordVfsMountPublisherReturnV1(
    VfsMountLifecycleObserverV1State &state, std::uint32_t raw_result,
    std::uint32_t thread_id) noexcept {
  auto *slot = FindLatestUnreturnedPublisher(state, thread_id);
  if (slot == nullptr) {
    state.publisher_correlation_miss_count.fetch_add(
        1, std::memory_order_release);
    return;
  }
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  slot->raw_result.store(raw_result, std::memory_order_relaxed);
  slot->return_thread_id.store(thread_id, std::memory_order_relaxed);
  StoreManager(slot->manager_after, CaptureManager(state.manager_address));
  slot->return_sequence.store(sequence, std::memory_order_relaxed);
  slot->return_seen.store(1, std::memory_order_release);
  state.last_publisher_return_sequence.store(sequence,
                                              std::memory_order_release);
  state.publisher_return_count.fetch_add(1, std::memory_order_release);
  (raw_result != 0 ? state.publisher_success_count
                   : state.publisher_failure_count)
      .fetch_add(1, std::memory_order_release);
}

void RecordVfsSettingsLookupV1(VfsMountLifecycleObserverV1State &state,
                               std::uintptr_t path_view,
                               std::uintptr_t manager,
                               std::uint32_t thread_id) noexcept {
  std::uintptr_t data = 0;
  std::int32_t signed_length = 0;
  std::uint8_t flag = 0;
  std::uintptr_t length_address = 0;
  std::uintptr_t flag_address = 0;
  if (path_view == 0 || !SafeAdd(path_view, 8, length_address) ||
      !SafeAdd(path_view, 0x0C, flag_address) ||
      !SafeCopyFrom(path_view, &data, sizeof(data)) ||
      !SafeCopyFrom(length_address, &signed_length, sizeof(signed_length)) ||
      !SafeCopyFrom(flag_address, &flag, sizeof(flag))) {
    state.lookup_classification_fault_count.fetch_add(
        1, std::memory_order_release);
    return;
  }
  if (signed_length != static_cast<std::int32_t>(kPathsSettings.size()) &&
      signed_length !=
          static_cast<std::int32_t>(kChecksummedSettings.size())) {
    return;
  }
  std::array<std::uint8_t, kChecksummedSettings.size()> bytes{};
  const auto length = static_cast<std::size_t>(signed_length);
  if (data == 0 || !SafeCopyFrom(data, bytes.data(), length)) {
    state.lookup_classification_fault_count.fetch_add(
        1, std::memory_order_release);
    return;
  }
  VfsSettingsLookupObservationV1 *destination = nullptr;
  if (length == kPathsSettings.size() &&
      std::memcmp(bytes.data(), kPathsSettings.data(), length) == 0) {
    destination = &state.paths_lookup;
  } else if (length == kChecksummedSettings.size() &&
             std::memcmp(bytes.data(), kChecksummedSettings.data(), length) ==
                 0) {
    destination = &state.checksummed_lookup;
  } else {
    return;
  }
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  destination->path_view.store(path_view, std::memory_order_relaxed);
  destination->path_data.store(data, std::memory_order_relaxed);
  destination->path_length.store(static_cast<std::uint32_t>(length),
                                 std::memory_order_relaxed);
  destination->path_flag.store(flag, std::memory_order_relaxed);
  destination->thread_id.store(thread_id, std::memory_order_relaxed);
  destination->read_fault.store(0, std::memory_order_relaxed);
  StoreManager(destination->manager, CaptureManager(manager));
  destination->sequence.store(sequence, std::memory_order_release);
  destination->count.fetch_add(1, std::memory_order_release);
}

bool InstallVfsMountLifecycleObserverV1(
    VfsMountLifecycleObserverV1State &state,
    const VfsMountLifecycleObserverEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(vfs_mount_lifecycle_observer_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        vfs_mount_lifecycle_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture && HasOverrides(environment)) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      g_active.load(std::memory_order_acquire) != nullptr) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  constexpr std::array<std::uintptr_t, kVfsMountLifecycleHookCountV1>
      patch_rvas{kVfsMountLifecycleCoreInitCallRvaV1,
                 kVfsMountLifecyclePublisherEntryRvaV1,
                 kVfsMountLifecyclePublisherReturnRvaV1,
                 kVfsMountLifecycleSettingsLookupRvaV1};
  constexpr std::array<std::size_t, kVfsMountLifecycleHookCountV1> patch_sizes{
      5, 5, 5, 8};
  for (std::size_t index = 0; index < state.hooks.size(); ++index) {
    state.hooks[index].patch_target = Resolve(
        environment.patch_target_overrides[index], environment.module_base,
        patch_rvas[index]);
    state.hooks[index].patch_size = patch_sizes[index];
  }
  state.core_init_target = Resolve(environment.core_init_target_override,
                                   environment.module_base,
                                   kVfsMountLifecycleCoreInitTargetRvaV1);
  state.publisher_entry_continue = Resolve(
      environment.publisher_entry_continue_override, environment.module_base,
      kVfsMountLifecyclePublisherEntryContinueRvaV1);
  state.publisher_return_continue = Resolve(
      environment.publisher_return_continue_override, environment.module_base,
      kVfsMountLifecyclePublisherReturnContinueRvaV1);
  state.settings_lookup_continue = Resolve(
      environment.settings_lookup_continue_override, environment.module_base,
      kVfsMountLifecycleSettingsLookupContinueRvaV1);
  state.manager_address = Resolve(environment.manager_address_override,
                                  environment.module_base,
                                  kVfsMountLifecycleManagerRvaV1);
  if (state.core_init_target == 0 || state.publisher_entry_continue == 0 ||
      state.publisher_return_continue == 0 ||
      state.settings_lookup_continue == 0 || state.manager_address == 0) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_anchor);
    ClearRuntime(state);
    return false;
  }
  for (std::size_t index = 0; index < state.hooks.size(); ++index) {
    auto &hook = state.hooks[index];
    if (hook.patch_target == 0 || !AnchorMatches(index, hook.patch_target) ||
        !SafeCopyFrom(hook.patch_target, hook.original.data(),
                      hook.patch_size)) {
      AddFailure(state, vfs_mount_lifecycle_observer_failure_anchor);
      ClearRuntime(state);
      return false;
    }
  }

  std::uintptr_t lower = 0;
  std::uintptr_t upper = std::numeric_limits<std::uintptr_t>::max();
  for (std::size_t index = 0; index < state.hooks.size(); ++index) {
    std::uintptr_t current_lower = 0;
    std::uintptr_t current_upper = 0;
    if (!BaseBoundsForBranch(state.hooks[index].patch_target,
                             kStubOffsets[index], current_lower,
                             current_upper)) {
      AddFailure(state, vfs_mount_lifecycle_observer_failure_stub_range);
      ClearRuntime(state);
      return false;
    }
    lower = std::max(lower, current_lower);
    upper = std::min(upper, current_upper);
  }
  if (lower > upper) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_stub_range);
    ClearRuntime(state);
    return false;
  }

  auto allocate = environment.virtual_alloc_near_override != nullptr
      ? environment.virtual_alloc_near_override
      : &DefaultAllocNear;
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
  state.memory_context = environment.memory_context;
  state.stub_allocation = allocate(
      state.memory_context, lower, upper,
      kVfsMountLifecycleStubAllocationBytesV1, MEM_RESERVE | MEM_COMMIT,
      PAGE_READWRITE);
  if (state.stub_allocation == nullptr) {
    AddFailure(state, vfs_mount_lifecycle_observer_failure_allocation);
    ClearRuntime(state);
    return false;
  }

  std::array<std::array<std::uint8_t, kMaximumStubBytes>,
             kVfsMountLifecycleHookCountV1>
      stubs{};
  std::array<std::size_t, kVfsMountLifecycleHookCountV1> used{};
  used[0] = BuildCoreInitCallStub(state, stubs[0]);
  used[1] = BuildPublisherEntryStub(state, stubs[1]);
  used[2] = BuildPublisherReturnStub(state, stubs[2]);
  used[3] = BuildSettingsLookupStub(state, stubs[3]);
  const auto stub_base =
      reinterpret_cast<std::uintptr_t>(state.stub_allocation);
  constexpr std::array<std::uint8_t, kVfsMountLifecycleHookCountV1> opcodes{
      0xE8, 0xE9, 0xE9, 0xE9};
  for (std::size_t index = 0; index < state.hooks.size(); ++index) {
    const auto stub_address = stub_base + kStubOffsets[index];
    auto &hook = state.hooks[index];
    if (used[index] == 0 || used[index] > stubs[index].size() ||
        !BuildRelativeBranch(hook.patch_target, stub_address, opcodes[index],
                             hook.installed_patch.data(), hook.patch_size) ||
        !SafeCopyTo(stub_address, stubs[index].data(), used[index])) {
      AddFailure(state, vfs_mount_lifecycle_observer_failure_stub_range);
      (void)UninstallVfsMountLifecycleObserverV1(state);
      return false;
    }
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, state.stub_allocation,
                             kVfsMountLifecycleStubAllocationBytesV1,
                             PAGE_EXECUTE_READ, old) ||
      !Flush(state, state.stub_allocation,
             kVfsMountLifecycleStubAllocationBytesV1)) {
    AddFailure(state,
               vfs_mount_lifecycle_observer_failure_stub_protection);
    (void)UninstallVfsMountLifecycleObserverV1(state);
    return false;
  }

  g_active.store(&state, std::memory_order_release);
  for (std::size_t index = 0; index < state.hooks.size(); ++index) {
    auto &hook = state.hooks[index];
    if (!WriteHook(state, index, hook.original.data(),
                   hook.installed_patch.data())) {
      for (std::size_t prior = index; prior-- > 0;) {
        auto &old_hook = state.hooks[prior];
        if (WriteHook(state, prior, old_hook.installed_patch.data(),
                      old_hook.original.data())) {
          state.installed_mask.fetch_and(~(1U << prior),
                                         std::memory_order_release);
        }
      }
      (void)UninstallVfsMountLifecycleObserverV1(state);
      return false;
    }
    state.installed_mask.fetch_or(1U << index, std::memory_order_release);
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallVfsMountLifecycleObserverV1(
    VfsMountLifecycleObserverV1State &state) noexcept {
  bool result = true;
  for (std::size_t index = state.hooks.size(); index-- > 0;) {
    auto &hook = state.hooks[index];
    if ((state.installed_mask.load(std::memory_order_acquire) &
         (1U << index)) == 0) {
      continue;
    }
    if (WriteHook(state, index, hook.installed_patch.data(),
                  hook.original.data())) {
      state.installed_mask.fetch_and(~(1U << index),
                                     std::memory_order_release);
    } else {
      result = false;
    }
  }
  if (state.installed_mask.load(std::memory_order_acquire) != 0) return false;
  g_active.store(nullptr, std::memory_order_release);
  if (state.stub_allocation != nullptr) {
    if (state.virtual_free == nullptr ||
        !state.virtual_free(state.memory_context, state.stub_allocation, 0,
                            MEM_RELEASE)) {
      AddFailure(state, vfs_mount_lifecycle_observer_failure_rollback);
      result = false;
    } else {
      state.stub_allocation = nullptr;
    }
  }
  state.installed.store(0, std::memory_order_release);
  if (result) ClearRuntime(state);
  return result;
}

VfsMountLifecycleObserverV1Diagnostics
ReadVfsMountLifecycleObserverV1Diagnostics(
    const VfsMountLifecycleObserverV1State &state) noexcept {
  VfsMountLifecycleObserverV1Diagnostics result{};
  result.installed = state.installed.load(std::memory_order_acquire) != 0;
  result.installed_mask =
      state.installed_mask.load(std::memory_order_acquire);
  result.failure_flags =
      state.failure_flags.load(std::memory_order_acquire);
  result.next_sequence = state.next_sequence.load(std::memory_order_acquire);
  result.core_init_count = state.core_init.count.load(std::memory_order_acquire);
  result.core_init_raw_al =
      state.core_init.raw_al.load(std::memory_order_acquire);
  result.core_init_thread_id =
      state.core_init.thread_id.load(std::memory_order_acquire);
  result.core_init_sequence =
      state.core_init.sequence.load(std::memory_order_acquire);
  result.core_init_manager = ReadManager(state.core_init.manager);
  result.publisher_entry_count =
      state.publisher_entry_count.load(std::memory_order_acquire);
  result.publisher_return_count =
      state.publisher_return_count.load(std::memory_order_acquire);
  result.publisher_success_count =
      state.publisher_success_count.load(std::memory_order_acquire);
  result.publisher_failure_count =
      state.publisher_failure_count.load(std::memory_order_acquire);
  result.publisher_correlation_miss_count =
      state.publisher_correlation_miss_count.load(std::memory_order_acquire);
  result.publisher_slot_overwrite_count =
      state.publisher_slot_overwrite_count.load(std::memory_order_acquire);
  const auto latest_return =
      state.last_publisher_return_sequence.load(std::memory_order_acquire);
  const auto latest_entry =
      state.last_publisher_entry_sequence.load(std::memory_order_acquire);
  const auto latest = std::max(latest_return, latest_entry);
  if (const auto *slot = FindPublisherBySequence(state, latest)) {
    result.latest_publisher = ReadPublisher(*slot);
  }
  result.paths_lookup = ReadLookup(state.paths_lookup);
  result.checksummed_lookup = ReadLookup(state.checksummed_lookup);
  result.lookup_classification_fault_count =
      state.lookup_classification_fault_count.load(std::memory_order_acquire);
  return result;
}

} // namespace xar::bridge
