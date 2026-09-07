#include "xar_bridge/pdx_paths_583_producer_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <intrin.h>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "pdx_paths 0x583 producer observer is x64-only");

constexpr std::array<std::size_t, kPdxPaths583HookCountV1> kStubOffsets{
    0, 384, 768, 1152, 1536};
constexpr std::size_t kMaximumStubBytes = 384;
constexpr std::array<std::uint8_t, kPdxPaths583PatchBytesV1> kTaskAnchor{
    0x48, 0x89, 0x7C, 0x24, 0x30};
constexpr std::array<std::uint8_t, kPdxPaths583PatchBytesV1>
    kPathsLookupAnchor{0xE8, 0xED, 0xB8, 0x04, 0x00};
constexpr std::array<std::uint8_t, kPdxPaths583PatchBytesV1>
    kChecksummedLookupAnchor{0xE8, 0xD9, 0xB7, 0x04, 0x00};
constexpr std::array<std::uint8_t, kPdxPaths583PatchBytesV1> kParserAnchor{
    0x48, 0x89, 0x4C, 0x24, 0x60};
constexpr std::array<std::uint8_t, kPdxPaths583PatchBytesV1> kInsertAnchor{
    0xE8, 0x54, 0x41, 0x9A, 0xFE};
constexpr std::array<
    const std::array<std::uint8_t, kPdxPaths583PatchBytesV1> *,
    kPdxPaths583HookCountV1>
    kAnchors{&kTaskAnchor, &kPathsLookupAnchor, &kChecksummedLookupAnchor,
             &kParserAnchor, &kInsertAnchor};

std::atomic<PdxPaths583ProducerObserverV1State *> g_active{nullptr};

struct TableSnapshot {
  std::uint64_t map = 0;
  std::uint64_t rows = 0;
  std::uint64_t count = 0;
  std::uint32_t mask = 0;
  std::uint32_t max_probe = 0;
  bool id_583_present = false;
  std::uint64_t id_583_row = 0;
  bool read_fault = false;
};

void AddFailure(PdxPaths583ProducerObserverV1State &state,
                PdxPaths583ProducerObserverFailureV1 failure) noexcept {
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
  std::array<std::uint8_t, kPdxPaths583PatchBytesV1> actual{};
  return size <= actual.size() &&
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
  // TEB.ClientId.UniqueThread: no Win32 call, allocation, lock, or syscall.
  return __readgsdword(0x48);
#else
  return 0;
#endif
}

TableSnapshot CaptureTable(std::uintptr_t map) noexcept {
  TableSnapshot result{};
  result.map = map;
  if (map == 0) return result;
  std::uintptr_t rows_address = 0;
  std::uintptr_t count_address = 0;
  std::uintptr_t mask_address = 0;
  std::uintptr_t max_probe_address = 0;
  std::uint8_t max_probe = 0;
  if (!SafeAdd(map, 0x08, rows_address) ||
      !SafeAdd(map, 0x10, count_address) ||
      !SafeAdd(map, 0x14, mask_address) ||
      !SafeAdd(map, 0x18, max_probe_address) ||
      !SafeCopyFrom(rows_address, &result.rows, sizeof(result.rows)) ||
      !SafeCopyFrom(count_address, &result.count, sizeof(std::uint32_t)) ||
      !SafeCopyFrom(mask_address, &result.mask, sizeof(result.mask)) ||
      !SafeCopyFrom(max_probe_address, &max_probe, sizeof(max_probe))) {
    result.read_fault = true;
    return result;
  }
  result.max_probe = max_probe;
  if (result.rows == 0) {
    result.read_fault = result.count != 0;
    return result;
  }

  const auto initial =
      static_cast<std::uint64_t>(kPdxPaths583NamedPathHashV1 & result.mask);
  if (initial >
      (std::numeric_limits<std::uintptr_t>::max() - result.rows) / 48U) {
    result.read_fault = true;
    return result;
  }
  auto row = static_cast<std::uintptr_t>(result.rows + initial * 48U);
  std::uint16_t distance = 1;
  for (;;) {
    std::uint8_t control = 0;
    std::uint32_t key = 0;
    std::uintptr_t control_address = 0;
    std::uintptr_t key_address = 0;
    if (!SafeAdd(row, 4, control_address) || !SafeAdd(row, 8, key_address) ||
        !SafeCopyFrom(control_address, &control, sizeof(control)) ||
        !SafeCopyFrom(key_address, &key, sizeof(key))) {
      result.read_fault = true;
      return result;
    }
    if (control < distance) return result;
    if (key == kPdxPaths583NamedPathIdV1) {
      result.id_583_present = true;
      result.id_583_row = row;
      return result;
    }
    if (distance > result.max_probe || distance == 0xFFU ||
        row > std::numeric_limits<std::uintptr_t>::max() - 48U) {
      return result;
    }
    ++distance;
    row += 48U;
  }
}

void StoreTable(PdxPaths583TableObservationV1 &destination,
                const TableSnapshot &source) noexcept {
  destination.map.store(source.map, std::memory_order_relaxed);
  destination.rows.store(source.rows, std::memory_order_relaxed);
  destination.count.store(source.count, std::memory_order_relaxed);
  destination.mask.store(source.mask, std::memory_order_relaxed);
  destination.max_probe.store(source.max_probe, std::memory_order_relaxed);
  destination.id_583_present.store(source.id_583_present ? 1U : 0U,
                                   std::memory_order_relaxed);
  destination.id_583_row.store(source.id_583_row, std::memory_order_relaxed);
  destination.read_fault.store(source.read_fault ? 1U : 0U,
                               std::memory_order_release);
}

PdxPaths583TableDiagnosticsV1 ReadTable(
    const PdxPaths583TableObservationV1 &source) noexcept {
  PdxPaths583TableDiagnosticsV1 result{};
  result.map = source.map.load(std::memory_order_acquire);
  result.rows = source.rows.load(std::memory_order_acquire);
  result.count = source.count.load(std::memory_order_acquire);
  result.mask = source.mask.load(std::memory_order_acquire);
  result.max_probe = source.max_probe.load(std::memory_order_acquire);
  result.id_583_present =
      source.id_583_present.load(std::memory_order_acquire) != 0;
  result.id_583_row = source.id_583_row.load(std::memory_order_acquire);
  result.read_fault = source.read_fault.load(std::memory_order_acquire) != 0;
  return result;
}

PdxPaths583LookupObservationV1 &LookupState(
    PdxPaths583ProducerObserverV1State &state,
    PdxPaths583SourceV1 source) noexcept {
  return source == pdx_paths_583_source_checksummed
      ? state.checksummed_lookup
      : state.paths_lookup;
}

PdxPaths583LookupDiagnosticsV1 ReadLookup(
    const PdxPaths583LookupObservationV1 &source) noexcept {
  PdxPaths583LookupDiagnosticsV1 result{};
  result.pre_count = source.pre_count.load(std::memory_order_acquire);
  result.return_count = source.return_count.load(std::memory_order_acquire);
  result.raw_result = source.raw_result.load(std::memory_order_acquire);
  result.null_result = source.null_result.load(std::memory_order_acquire) != 0;
  result.thread_id = source.thread_id.load(std::memory_order_acquire);
  result.sequence = source.sequence.load(std::memory_order_acquire);
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

extern "C" void PdxPaths583TaskThunkV1() noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordPdxPaths583TaskEnterV1(*state, CurrentThreadIdFast());
  }
}

extern "C" void PdxPaths583PathsLookupPreThunkV1() noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordPdxPaths583LookupPreV1(*state, pdx_paths_583_source_paths,
                                 CurrentThreadIdFast());
  }
}

extern "C" void PdxPaths583PathsLookupPostThunkV1(
    std::uintptr_t result) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordPdxPaths583LookupPostV1(*state, pdx_paths_583_source_paths, result,
                                  CurrentThreadIdFast());
  }
}

extern "C" void PdxPaths583ChecksummedLookupPreThunkV1() noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordPdxPaths583LookupPreV1(*state, pdx_paths_583_source_checksummed,
                                 CurrentThreadIdFast());
  }
}

extern "C" void PdxPaths583ChecksummedLookupPostThunkV1(
    std::uintptr_t result) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordPdxPaths583LookupPostV1(*state, pdx_paths_583_source_checksummed,
                                  result, CurrentThreadIdFast());
  }
}

extern "C" void PdxPaths583ParserThunkV1(std::uintptr_t source) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordPdxPaths583ParserEnterV1(*state, source, CurrentThreadIdFast());
  }
}

extern "C" void PdxPaths583InsertPreThunkV1(
    std::uintptr_t map, std::uintptr_t result_pair, std::uint32_t hash,
    std::uintptr_t key_pointer, std::uintptr_t rhs_string) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordPdxPaths583InsertPreV1(*state, map, result_pair, hash, key_pointer,
                                 rhs_string, CurrentThreadIdFast());
  }
}

extern "C" void PdxPaths583InsertPostThunkV1(
    std::uintptr_t map, std::uintptr_t result_pair, std::uint32_t hash,
    std::uintptr_t key_pointer, std::uintptr_t native_result) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordPdxPaths583InsertPostV1(*state, map, result_pair, hash, key_pointer,
                                  native_result, CurrentThreadIdFast());
  }
}

std::size_t BuildTaskStub(
    const PdxPaths583ProducerObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  Emit(stub, cursor, {0x48, 0x89, 0x7C, 0x24, 0x30});
  EmitPreserveMidFunctionVolatile(stub, cursor);
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(&PdxPaths583TaskThunkV1));
  EmitRestoreMidFunctionVolatile(stub, cursor);
  EmitAbsoluteJump(stub, cursor, state.task_continue_target);
  return cursor;
}

std::size_t BuildLookupStub(
    const PdxPaths583ProducerObserverV1State &state,
    std::uintptr_t pre_thunk, std::uintptr_t post_thunk,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  // A patched CALL enters with RSP%16==8. 0xA8 provides fresh shadow space,
  // aligned nested calls, private GPR slots, and XMM0-3 argument snapshots.
  Emit(stub, cursor, {0x48, 0x81, 0xEC, 0xA8, 0x00, 0x00, 0x00});
  Emit(stub, cursor, {0x48, 0x89, 0x4C, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x89, 0x54, 0x24, 0x28});
  Emit(stub, cursor, {0x4C, 0x89, 0x44, 0x24, 0x30});
  Emit(stub, cursor, {0x4C, 0x89, 0x4C, 0x24, 0x38});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x44, 0x24, 0x40});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x4C, 0x24, 0x50});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x54, 0x24, 0x60});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x5C, 0x24, 0x70});
  EmitThunkCall(stub, cursor, pre_thunk);
  Emit(stub, cursor, {0x48, 0x8B, 0x4C, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0x54, 0x24, 0x28});
  Emit(stub, cursor, {0x4C, 0x8B, 0x44, 0x24, 0x30});
  Emit(stub, cursor, {0x4C, 0x8B, 0x4C, 0x24, 0x38});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x44, 0x24, 0x40});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x4C, 0x24, 0x50});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x54, 0x24, 0x60});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x5C, 0x24, 0x70});
  EmitAbsoluteCall(stub, cursor, state.lookup_target);
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0xC8});
  EmitThunkCall(stub, cursor, post_thunk);
  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x20});
  Emit(stub, cursor,
       {0x48, 0x81, 0xC4, 0xA8, 0x00, 0x00, 0x00, 0xC3});
  return cursor;
}

std::size_t BuildParserStub(
    const PdxPaths583ProducerObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  Emit(stub, cursor, {0x48, 0x89, 0x4C, 0x24, 0x60});
  EmitPreserveMidFunctionVolatile(stub, cursor);
  // The saved pre-hook RCX is 0xA8 bytes above the preservation frame.
  Emit(stub, cursor, {0x48, 0x8B, 0x8C, 0x24, 0xA8, 0x00, 0x00, 0x00});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(&PdxPaths583ParserThunkV1));
  EmitRestoreMidFunctionVolatile(stub, cursor);
  EmitAbsoluteJump(stub, cursor, state.parser_continue_target);
  return cursor;
}

std::size_t BuildInsertStub(
    const PdxPaths583ProducerObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  Emit(stub, cursor, {0x48, 0x81, 0xEC, 0xE8, 0x00, 0x00, 0x00});
  Emit(stub, cursor, {0x48, 0x89, 0x4C, 0x24, 0x50});
  Emit(stub, cursor, {0x48, 0x89, 0x54, 0x24, 0x58});
  Emit(stub, cursor, {0x4C, 0x89, 0x44, 0x24, 0x60});
  Emit(stub, cursor, {0x4C, 0x89, 0x4C, 0x24, 0x68});
  // Preserve the caller's unused fifth slot and the RHS string in the sixth
  // slot. At stub entry those are [RSP+0x28] and [RSP+0x30].
  Emit(stub, cursor, {0x48, 0x8B, 0x84, 0x24, 0x10, 0x01, 0x00, 0x00});
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x70});
  Emit(stub, cursor, {0x48, 0x8B, 0x84, 0x24, 0x18, 0x01, 0x00, 0x00});
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x78});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x84, 0x24, 0x80, 0x00, 0x00,
                       0x00});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x8C, 0x24, 0x90, 0x00, 0x00,
                       0x00});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x94, 0x24, 0xA0, 0x00, 0x00,
                       0x00});
  Emit(stub, cursor, {0xF3, 0x0F, 0x7F, 0x9C, 0x24, 0xB0, 0x00, 0x00,
                       0x00});
  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x78});
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0x4C, 0x24, 0x50});
  Emit(stub, cursor, {0x48, 0x8B, 0x54, 0x24, 0x58});
  Emit(stub, cursor, {0x4C, 0x8B, 0x44, 0x24, 0x60});
  Emit(stub, cursor, {0x4C, 0x8B, 0x4C, 0x24, 0x68});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(&PdxPaths583InsertPreThunkV1));

  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x70});
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x78});
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x28});
  Emit(stub, cursor, {0x48, 0x8B, 0x4C, 0x24, 0x50});
  Emit(stub, cursor, {0x48, 0x8B, 0x54, 0x24, 0x58});
  Emit(stub, cursor, {0x4C, 0x8B, 0x44, 0x24, 0x60});
  Emit(stub, cursor, {0x4C, 0x8B, 0x4C, 0x24, 0x68});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x84, 0x24, 0x80, 0x00, 0x00,
                       0x00});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x8C, 0x24, 0x90, 0x00, 0x00,
                       0x00});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x94, 0x24, 0xA0, 0x00, 0x00,
                       0x00});
  Emit(stub, cursor, {0xF3, 0x0F, 0x6F, 0x9C, 0x24, 0xB0, 0x00, 0x00,
                       0x00});
  EmitAbsoluteCall(stub, cursor, state.insert_target);
  Emit(stub, cursor, {0x48, 0x89, 0x84, 0x24, 0xC0, 0x00, 0x00, 0x00});

  Emit(stub, cursor, {0x48, 0x89, 0x84, 0x24, 0x20, 0x00, 0x00, 0x00});
  Emit(stub, cursor, {0x48, 0x8B, 0x4C, 0x24, 0x50});
  Emit(stub, cursor, {0x48, 0x8B, 0x54, 0x24, 0x58});
  Emit(stub, cursor, {0x4C, 0x8B, 0x44, 0x24, 0x60});
  Emit(stub, cursor, {0x4C, 0x8B, 0x4C, 0x24, 0x68});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(&PdxPaths583InsertPostThunkV1));
  Emit(stub, cursor, {0x48, 0x8B, 0x84, 0x24, 0xC0, 0x00, 0x00, 0x00});
  Emit(stub, cursor,
       {0x48, 0x81, 0xC4, 0xE8, 0x00, 0x00, 0x00, 0xC3});
  return cursor;
}

bool BuildRelativeBranch(std::uintptr_t source, std::uintptr_t destination,
                         std::uint8_t opcode, std::uint8_t *output) noexcept {
  const auto next = source + kPdxPaths583PatchBytesV1;
  const auto delta = static_cast<std::int64_t>(destination) -
      static_cast<std::int64_t>(next);
  if (delta < std::numeric_limits<std::int32_t>::min() ||
      delta > std::numeric_limits<std::int32_t>::max()) {
    return false;
  }
  output[0] = opcode;
  const auto displacement = static_cast<std::int32_t>(delta);
  std::memcpy(output + 1, &displacement, sizeof(displacement));
  return true;
}

bool BaseBoundsForBranch(std::uintptr_t source, std::size_t stub_offset,
                         std::uintptr_t &lower,
                         std::uintptr_t &upper) noexcept {
  std::uintptr_t next = 0;
  if (!SafeAdd(source, kPdxPaths583PatchBytesV1, next)) return false;
  constexpr auto backward = static_cast<std::uintptr_t>(0x80000000ULL);
  constexpr auto forward = static_cast<std::uintptr_t>(0x7FFFFFFFULL);
  const auto destination_lower = next >= backward ? next - backward : 0;
  if (next > std::numeric_limits<std::uintptr_t>::max() - forward) return false;
  const auto destination_upper = next + forward;
  if (destination_upper < stub_offset) return false;
  lower = destination_lower > stub_offset
      ? destination_lower - stub_offset
      : 0;
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

bool Flush(PdxPaths583ProducerObserverV1State &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, pdx_paths_583_producer_observer_failure_flush);
    return false;
  }
  return true;
}

bool WriteHook(PdxPaths583ProducerObserverV1State &state, std::size_t index,
               const std::uint8_t *expected,
               const std::uint8_t *desired) noexcept {
  auto &hook = state.hooks[index];
  if (!SafeBytesEqual(hook.patch_target, expected,
                      kPdxPaths583PatchBytesV1)) {
    AddFailure(state, pdx_paths_583_producer_observer_failure_target_identity);
    return false;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(hook.patch_target),
                            kPdxPaths583PatchBytesV1, PAGE_EXECUTE_READWRITE,
                            previous);
  if (!writable || !Executable(previous)) {
    if (writable) {
      DWORD ignored = 0;
      (void)state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(hook.patch_target),
          kPdxPaths583PatchBytesV1, previous, ignored);
    }
    AddFailure(state,
               pdx_paths_583_producer_observer_failure_target_protection);
    return false;
  }
  const bool copied = SafeCopyTo(hook.patch_target, desired,
                                 kPdxPaths583PatchBytesV1);
  const bool identical = copied &&
      SafeBytesEqual(hook.patch_target, desired, kPdxPaths583PatchBytesV1);
  const bool flushed = identical &&
      Flush(state, reinterpret_cast<const void *>(hook.patch_target),
            kPdxPaths583PatchBytesV1);
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(hook.patch_target),
      kPdxPaths583PatchBytesV1, previous, ignored);
  if (identical && flushed && restored) return true;

  DWORD rollback_previous = 0;
  const bool rollback_writable = state.virtual_protect(
      state.memory_context, reinterpret_cast<void *>(hook.patch_target),
      kPdxPaths583PatchBytesV1, PAGE_EXECUTE_READWRITE, rollback_previous);
  const bool rollback_written = rollback_writable &&
      SafeCopyTo(hook.patch_target, expected, kPdxPaths583PatchBytesV1);
  const bool rollback_identity = rollback_written &&
      SafeBytesEqual(hook.patch_target, expected, kPdxPaths583PatchBytesV1);
  const bool rollback_flushed = rollback_identity &&
      state.flush_instruction_cache != nullptr &&
      state.flush_instruction_cache(
          state.memory_context,
          reinterpret_cast<const void *>(hook.patch_target),
          kPdxPaths583PatchBytesV1);
  DWORD rollback_ignored = 0;
  const bool rollback_protected = rollback_writable &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(hook.patch_target),
                            kPdxPaths583PatchBytesV1, previous,
                            rollback_ignored);
  if (!rollback_identity || !rollback_flushed || !rollback_protected) {
    AddFailure(state, pdx_paths_583_producer_observer_failure_rollback);
  }
  return false;
}

bool HasOverrides(
    const PdxPaths583ProducerObserverEnvironmentV1 &environment) noexcept {
  return environment.patch_target_overrides !=
             std::array<std::uintptr_t, kPdxPaths583HookCountV1>{} ||
      environment.task_continue_target_override != 0 ||
      environment.parser_continue_target_override != 0 ||
      environment.lookup_target_override != 0 ||
      environment.insert_target_override != 0 ||
      environment.map_address_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_near_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

void ClearRuntime(PdxPaths583ProducerObserverV1State &state) noexcept {
  state.module_base = 0;
  state.task_continue_target = 0;
  state.parser_continue_target = 0;
  state.lookup_target = 0;
  state.insert_target = 0;
  state.map_address = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
  for (auto &hook : state.hooks) hook.patch_target = 0;
}

} // namespace

void RecordPdxPaths583TaskEnterV1(
    PdxPaths583ProducerObserverV1State &state,
    std::uint32_t thread_id) noexcept {
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  StoreTable(state.task_table, CaptureTable(state.map_address));
  state.task_thread_id.store(thread_id, std::memory_order_relaxed);
  state.task_sequence.store(sequence, std::memory_order_release);
  state.task_enter_count.fetch_add(1, std::memory_order_release);
}

void RecordPdxPaths583LookupPreV1(
    PdxPaths583ProducerObserverV1State &state, PdxPaths583SourceV1 source,
    std::uint32_t thread_id) noexcept {
  auto &lookup = LookupState(state, source);
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  lookup.thread_id.store(thread_id, std::memory_order_relaxed);
  lookup.sequence.store(sequence, std::memory_order_release);
  lookup.pre_count.fetch_add(1, std::memory_order_release);
}

void RecordPdxPaths583LookupPostV1(
    PdxPaths583ProducerObserverV1State &state, PdxPaths583SourceV1 source,
    std::uintptr_t result, std::uint32_t thread_id) noexcept {
  auto &lookup = LookupState(state, source);
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  lookup.raw_result.store(result, std::memory_order_relaxed);
  lookup.null_result.store(result == 0 ? 1U : 0U,
                           std::memory_order_relaxed);
  lookup.thread_id.store(thread_id, std::memory_order_relaxed);
  lookup.sequence.store(sequence, std::memory_order_release);
  lookup.return_count.fetch_add(1, std::memory_order_release);
}

void RecordPdxPaths583ParserEnterV1(
    PdxPaths583ProducerObserverV1State &state, std::uintptr_t source,
    std::uint32_t thread_id) noexcept {
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  std::uintptr_t paths = 0;
  std::uintptr_t checksummed = 0;
  (void)SafeAdd(state.module_base, kPdxPaths583PathsLiteralRvaV1, paths);
  (void)SafeAdd(state.module_base, kPdxPaths583ChecksummedLiteralRvaV1,
                checksummed);
  if (source == paths) {
    state.paths_parser_enter_count.fetch_add(1, std::memory_order_relaxed);
  } else if (source == checksummed) {
    state.checksummed_parser_enter_count.fetch_add(
        1, std::memory_order_relaxed);
  } else {
    state.other_parser_enter_count.fetch_add(1, std::memory_order_relaxed);
  }
  state.parser_source.store(source, std::memory_order_relaxed);
  state.parser_thread_id.store(thread_id, std::memory_order_relaxed);
  state.parser_sequence.store(sequence, std::memory_order_release);
}

void RecordPdxPaths583InsertPreV1(
    PdxPaths583ProducerObserverV1State &state, std::uintptr_t map,
    std::uintptr_t result_pair, std::uint32_t hash,
    std::uintptr_t key_pointer, std::uintptr_t rhs_string,
    std::uint32_t thread_id) noexcept {
  state.insert_call_count.fetch_add(1, std::memory_order_relaxed);
  std::uint32_t key = 0;
  if (!SafeCopyFrom(key_pointer, &key, sizeof(key))) {
    state.key_read_fault_count.fetch_add(1, std::memory_order_release);
    return;
  }
  if (key != kPdxPaths583NamedPathIdV1) return;
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  state.last_key.store(key, std::memory_order_relaxed);
  state.last_hash.store(hash, std::memory_order_relaxed);
  state.insert_thread_id.store(thread_id, std::memory_order_relaxed);
  state.rhs_string.store(rhs_string, std::memory_order_relaxed);
  state.result_pair.store(result_pair, std::memory_order_relaxed);
  state.result_pair_null.store(result_pair == 0 ? 1U : 0U,
                               std::memory_order_relaxed);
  StoreTable(state.table_before, CaptureTable(map));
  state.insert_sequence.store(sequence, std::memory_order_release);
  state.key_583_insert_pre_count.fetch_add(1, std::memory_order_release);
}

void RecordPdxPaths583InsertPostV1(
    PdxPaths583ProducerObserverV1State &state, std::uintptr_t map,
    std::uintptr_t result_pair, std::uint32_t hash,
    std::uintptr_t key_pointer, std::uintptr_t native_result,
    std::uint32_t thread_id) noexcept {
  std::uint32_t key = 0;
  if (!SafeCopyFrom(key_pointer, &key, sizeof(key))) {
    state.key_read_fault_count.fetch_add(1, std::memory_order_release);
    return;
  }
  if (key != kPdxPaths583NamedPathIdV1) return;
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  std::uint64_t row = 0;
  std::uint8_t inserted = 0;
  bool result_fault = false;
  if (result_pair != 0) {
    std::uintptr_t inserted_address = 0;
    result_fault = !SafeAdd(result_pair, 8, inserted_address) ||
        !SafeCopyFrom(result_pair, &row, sizeof(row)) ||
        !SafeCopyFrom(inserted_address, &inserted, sizeof(inserted));
  }
  state.last_key.store(key, std::memory_order_relaxed);
  state.last_hash.store(hash, std::memory_order_relaxed);
  state.insert_thread_id.store(thread_id, std::memory_order_relaxed);
  state.result_pair.store(result_pair, std::memory_order_relaxed);
  state.result_pair_null.store(result_pair == 0 ? 1U : 0U,
                               std::memory_order_relaxed);
  state.native_result.store(native_result, std::memory_order_relaxed);
  state.result_row.store(row, std::memory_order_relaxed);
  state.result_inserted.store(inserted != 0 ? 1U : 0U,
                              std::memory_order_relaxed);
  state.result_read_fault.store(result_fault ? 1U : 0U,
                                std::memory_order_relaxed);
  StoreTable(state.table_after, CaptureTable(map));
  state.insert_sequence.store(sequence, std::memory_order_release);
  state.key_583_insert_post_count.fetch_add(1, std::memory_order_release);
}

bool InstallPdxPaths583ProducerObserverV1(
    PdxPaths583ProducerObserverV1State &state,
    const PdxPaths583ProducerObserverEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(pdx_paths_583_producer_observer_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, pdx_paths_583_producer_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(
        state,
        pdx_paths_583_producer_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture && HasOverrides(environment)) {
    AddFailure(state,
               pdx_paths_583_producer_observer_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      g_active.load(std::memory_order_acquire) != nullptr) {
    AddFailure(state,
               pdx_paths_583_producer_observer_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  constexpr std::array<std::uintptr_t, kPdxPaths583HookCountV1> patch_rvas{
      kPdxPaths583TaskPatchRvaV1, kPdxPaths583PathsLookupCallRvaV1,
      kPdxPaths583ChecksummedLookupCallRvaV1, kPdxPaths583ParserPatchRvaV1,
      kPdxPaths583InsertCallRvaV1};
  for (std::size_t index = 0; index < state.hooks.size(); ++index) {
    state.hooks[index].patch_target = Resolve(
        environment.patch_target_overrides[index], environment.module_base,
        patch_rvas[index]);
  }
  state.task_continue_target = Resolve(
      environment.task_continue_target_override, environment.module_base,
      kPdxPaths583TaskContinueRvaV1);
  state.parser_continue_target = Resolve(
      environment.parser_continue_target_override, environment.module_base,
      kPdxPaths583ParserContinueRvaV1);
  state.lookup_target = Resolve(environment.lookup_target_override,
                                environment.module_base,
                                kPdxPaths583LookupTargetRvaV1);
  state.insert_target = Resolve(environment.insert_target_override,
                                environment.module_base,
                                kPdxPaths583InsertTargetRvaV1);
  state.map_address = Resolve(environment.map_address_override,
                              environment.module_base,
                              kPdxPaths583MapRvaV1);

  if (state.task_continue_target == 0 || state.parser_continue_target == 0 ||
      state.lookup_target == 0 || state.insert_target == 0 ||
      state.map_address == 0) {
    AddFailure(state, pdx_paths_583_producer_observer_failure_anchor);
    ClearRuntime(state);
    return false;
  }
  // All five exact-build anchors are verified and copied before allocation or
  // any target write. This is the observer's first transaction boundary.
  for (std::size_t index = 0; index < state.hooks.size(); ++index) {
    auto &hook = state.hooks[index];
    if (hook.patch_target == 0 ||
        !SafeBytesEqual(hook.patch_target, kAnchors[index]->data(),
                        kPdxPaths583PatchBytesV1) ||
        !SafeCopyFrom(hook.patch_target, hook.original.data(),
                      kPdxPaths583PatchBytesV1)) {
      AddFailure(state, pdx_paths_583_producer_observer_failure_anchor);
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
      AddFailure(state, pdx_paths_583_producer_observer_failure_stub_range);
      ClearRuntime(state);
      return false;
    }
    lower = std::max(lower, current_lower);
    upper = std::min(upper, current_upper);
  }
  if (lower > upper) {
    AddFailure(state, pdx_paths_583_producer_observer_failure_stub_range);
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
      state.memory_context, lower, upper, kPdxPaths583StubAllocationBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub_allocation == nullptr) {
    AddFailure(state, pdx_paths_583_producer_observer_failure_allocation);
    ClearRuntime(state);
    return false;
  }

  std::array<std::array<std::uint8_t, kMaximumStubBytes>,
             kPdxPaths583HookCountV1>
      stubs{};
  std::array<std::size_t, kPdxPaths583HookCountV1> used{};
  used[0] = BuildTaskStub(state, stubs[0]);
  used[1] = BuildLookupStub(
      state,
      reinterpret_cast<std::uintptr_t>(&PdxPaths583PathsLookupPreThunkV1),
      reinterpret_cast<std::uintptr_t>(&PdxPaths583PathsLookupPostThunkV1),
      stubs[1]);
  used[2] = BuildLookupStub(
      state,
      reinterpret_cast<std::uintptr_t>(
          &PdxPaths583ChecksummedLookupPreThunkV1),
      reinterpret_cast<std::uintptr_t>(
          &PdxPaths583ChecksummedLookupPostThunkV1),
      stubs[2]);
  used[3] = BuildParserStub(state, stubs[3]);
  used[4] = BuildInsertStub(state, stubs[4]);
  const auto stub_base =
      reinterpret_cast<std::uintptr_t>(state.stub_allocation);
  for (std::size_t index = 0; index < state.hooks.size(); ++index) {
    const auto stub_address = stub_base + kStubOffsets[index];
    const auto opcode = static_cast<std::uint8_t>(
        (index == 0 || index == 3) ? 0xE9 : 0xE8);
    if (used[index] == 0 || used[index] > stubs[index].size() ||
        !BuildRelativeBranch(state.hooks[index].patch_target, stub_address,
                             opcode,
                             state.hooks[index].installed_patch.data()) ||
        !SafeCopyTo(stub_address, stubs[index].data(), used[index])) {
      AddFailure(state, pdx_paths_583_producer_observer_failure_stub_range);
      (void)UninstallPdxPaths583ProducerObserverV1(state);
      return false;
    }
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, state.stub_allocation,
                             kPdxPaths583StubAllocationBytesV1,
                             PAGE_EXECUTE_READ, old) ||
      !Flush(state, state.stub_allocation,
             kPdxPaths583StubAllocationBytesV1)) {
    AddFailure(state,
               pdx_paths_583_producer_observer_failure_stub_protection);
    (void)UninstallPdxPaths583ProducerObserverV1(state);
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
      (void)UninstallPdxPaths583ProducerObserverV1(state);
      return false;
    }
    state.installed_mask.fetch_or(1U << index, std::memory_order_release);
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallPdxPaths583ProducerObserverV1(
    PdxPaths583ProducerObserverV1State &state) noexcept {
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
      AddFailure(state, pdx_paths_583_producer_observer_failure_rollback);
      result = false;
    } else {
      state.stub_allocation = nullptr;
    }
  }
  state.installed.store(0, std::memory_order_release);
  if (result) ClearRuntime(state);
  return result;
}

PdxPaths583ProducerObserverV1Diagnostics
ReadPdxPaths583ProducerObserverV1Diagnostics(
    const PdxPaths583ProducerObserverV1State &state) noexcept {
  PdxPaths583ProducerObserverV1Diagnostics result{};
  result.installed = state.installed.load(std::memory_order_acquire) != 0;
  result.installed_mask = state.installed_mask.load(std::memory_order_acquire);
  result.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  result.task_enter_count =
      state.task_enter_count.load(std::memory_order_acquire);
  result.task_thread_id = state.task_thread_id.load(std::memory_order_acquire);
  result.task_sequence = state.task_sequence.load(std::memory_order_acquire);
  result.task_table = ReadTable(state.task_table);
  result.paths_lookup = ReadLookup(state.paths_lookup);
  result.checksummed_lookup = ReadLookup(state.checksummed_lookup);
  result.paths_parser_enter_count =
      state.paths_parser_enter_count.load(std::memory_order_acquire);
  result.checksummed_parser_enter_count =
      state.checksummed_parser_enter_count.load(std::memory_order_acquire);
  result.other_parser_enter_count =
      state.other_parser_enter_count.load(std::memory_order_acquire);
  result.parser_source = state.parser_source.load(std::memory_order_acquire);
  result.parser_thread_id =
      state.parser_thread_id.load(std::memory_order_acquire);
  result.parser_sequence =
      state.parser_sequence.load(std::memory_order_acquire);
  result.insert_call_count =
      state.insert_call_count.load(std::memory_order_acquire);
  result.key_583_insert_pre_count =
      state.key_583_insert_pre_count.load(std::memory_order_acquire);
  result.key_583_insert_post_count =
      state.key_583_insert_post_count.load(std::memory_order_acquire);
  result.key_read_fault_count =
      state.key_read_fault_count.load(std::memory_order_acquire);
  result.last_key = state.last_key.load(std::memory_order_acquire);
  result.last_hash = state.last_hash.load(std::memory_order_acquire);
  result.insert_thread_id =
      state.insert_thread_id.load(std::memory_order_acquire);
  result.insert_sequence =
      state.insert_sequence.load(std::memory_order_acquire);
  result.rhs_string = state.rhs_string.load(std::memory_order_acquire);
  result.result_pair = state.result_pair.load(std::memory_order_acquire);
  result.native_result = state.native_result.load(std::memory_order_acquire);
  result.result_row = state.result_row.load(std::memory_order_acquire);
  result.result_inserted =
      state.result_inserted.load(std::memory_order_acquire) != 0;
  result.result_pair_null =
      state.result_pair_null.load(std::memory_order_acquire) != 0;
  result.result_read_fault =
      state.result_read_fault.load(std::memory_order_acquire) != 0;
  result.table_before = ReadTable(state.table_before);
  result.table_after = ReadTable(state.table_after);
  return result;
}

} // namespace xar::bridge
