#include "xar_bridge/named_path_583_root_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <initializer_list>
#include <intrin.h>
#include <limits>

namespace xar::bridge {
namespace {

static_assert(sizeof(void *) == 8,
              "named-path 0x583 root observer is x64-only");

constexpr std::size_t kResolverStubOffset = 0;
constexpr std::size_t kMoveStubOffset = 256;
constexpr std::size_t kMaximumStubBytes = 256;
constexpr std::array<std::uint8_t, kNamedPath583ResolverPatchBytesV1>
    kResolverCallAnchor{0xE8, 0xE9, 0x61, 0x87, 0x00};
constexpr std::array<std::uint8_t, kNamedPath583MovePatchBytesV1>
    kMoveCallAnchor{0x48, 0x8B, 0xD0, 0x48, 0x8B, 0xCF,
                    0xE8, 0x11, 0x72, 0x4C, 0xFD};

std::atomic<NamedPath583RootObserverV1State *> g_active{nullptr};

struct StringSnapshot {
  std::uint64_t object = 0;
  std::uint64_t effective_data = 0;
  std::uint64_t length = 0;
  std::uint64_t capacity = 0;
  std::uint64_t word0 = 0;
  std::uint64_t word1 = 0;
  bool null_result = false;
  bool read_fault = false;
};

void AddFailure(NamedPath583RootObserverV1State &state,
                NamedPath583RootObserverFailureV1 failure) noexcept {
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
  std::array<std::uint8_t, kNamedPath583MovePatchBytesV1> actual{};
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
  // TEB.ClientId.UniqueThread. This is a caller-local register read: no Win32
  // API, allocation, lock, or syscall occurs on either observer fast path.
  return __readgsdword(0x48);
#else
  return 0;
#endif
}

StringSnapshot CaptureString(std::uintptr_t object) noexcept {
  StringSnapshot result{};
  result.object = object;
  if (object == 0) {
    result.null_result = true;
    return result;
  }
  std::uintptr_t length_address = 0;
  std::uintptr_t capacity_address = 0;
  if (!SafeAdd(object, 0x10, length_address) ||
      !SafeAdd(object, 0x18, capacity_address) ||
      !SafeCopyFrom(length_address, &result.length, sizeof(result.length)) ||
      !SafeCopyFrom(capacity_address, &result.capacity,
                    sizeof(result.capacity))) {
    result.read_fault = true;
    return result;
  }
  if (result.capacity < 0x10) {
    result.effective_data = object;
  } else if (!SafeCopyFrom(object, &result.effective_data,
                           sizeof(result.effective_data)) ||
             result.effective_data == 0) {
    result.read_fault = true;
    return result;
  }
  std::array<std::uint8_t, 16> first{};
  if (!SafeCopyFrom(static_cast<std::uintptr_t>(result.effective_data),
                    first.data(), first.size())) {
    result.read_fault = true;
    return result;
  }
  std::memcpy(&result.word0, first.data(), sizeof(result.word0));
  std::memcpy(&result.word1, first.data() + sizeof(result.word0),
              sizeof(result.word1));
  return result;
}

void StoreString(NamedPath583StringObservationV1 &destination,
                 const StringSnapshot &source) noexcept {
  destination.object.store(source.object, std::memory_order_relaxed);
  destination.effective_data.store(source.effective_data,
                                   std::memory_order_relaxed);
  destination.length.store(source.length, std::memory_order_relaxed);
  destination.capacity.store(source.capacity, std::memory_order_relaxed);
  destination.word0.store(source.word0, std::memory_order_relaxed);
  destination.word1.store(source.word1, std::memory_order_relaxed);
  destination.null_result.store(source.null_result ? 1U : 0U,
                                std::memory_order_relaxed);
  destination.read_fault.store(source.read_fault ? 1U : 0U,
                               std::memory_order_relaxed);
}

void ClearString(NamedPath583StringObservationV1 &value) noexcept {
  StoreString(value, {});
}

NamedPath583CorrelationSlotV1 *FindLatestThreadSlot(
    NamedPath583RootObserverV1State &state, std::uint32_t thread_id,
    bool require_pre) noexcept {
  NamedPath583CorrelationSlotV1 *result = nullptr;
  std::uint64_t best = 0;
  for (auto &slot : state.slots) {
    const auto first = slot.published_sequence.load(std::memory_order_acquire);
    if (first == 0 || slot.thread_id.load(std::memory_order_relaxed) != thread_id ||
        (require_pre &&
         slot.move_pre_seen.load(std::memory_order_relaxed) == 0)) {
      continue;
    }
    const auto second = slot.published_sequence.load(std::memory_order_acquire);
    if (first == second && first > best) {
      best = first;
      result = &slot;
    }
  }
  return result;
}

NamedPath583CorrelationSlotV1 *FindSequenceSlot(
    const NamedPath583RootObserverV1State &state,
    std::uint64_t sequence) noexcept {
  if (sequence == 0) return nullptr;
  auto &slot = const_cast<NamedPath583CorrelationSlotV1 &>(
      state.slots[(sequence - 1) % state.slots.size()]);
  return slot.published_sequence.load(std::memory_order_acquire) == sequence
      ? &slot
      : nullptr;
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
  // Preserve incoming RAX while making the relocated native call.
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
void EmitPreserveVolatile(std::array<std::uint8_t, Size> &output,
                          std::size_t &cursor) noexcept {
  Emit(output, cursor,
       {0x9C, 0x50, 0x51, 0x52, 0x41, 0x50,
        0x41, 0x51, 0x41, 0x52, 0x41, 0x53,
        0x48, 0x83, 0xEC, 0x20});
}

template <std::size_t Size>
void EmitRestoreVolatile(std::array<std::uint8_t, Size> &output,
                         std::size_t &cursor) noexcept {
  Emit(output, cursor,
       {0x48, 0x83, 0xC4, 0x20,
        0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59,
        0x41, 0x58, 0x5A, 0x59, 0x58, 0x9D});
}

extern "C" void NamedPath583ResolverThunkV1(
    std::uintptr_t resolver_result) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordNamedPath583ResolverV1(*state, resolver_result,
                                 CurrentThreadIdFast());
  }
}

extern "C" void NamedPath583MovePreThunkV1(
    std::uintptr_t root, std::uintptr_t temporary) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordNamedPath583MovePreV1(*state, root, temporary,
                                CurrentThreadIdFast());
  }
}

extern "C" void NamedPath583MovePostThunkV1(
    std::uintptr_t root, std::uintptr_t temporary,
    std::uintptr_t move_result) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state != nullptr) {
    RecordNamedPath583MovePostV1(*state, root, temporary, move_result,
                                 CurrentThreadIdFast());
  }
}

std::size_t BuildResolverStub(
    const NamedPath583RootObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  // The patched CALL supplies the original return address. Make a correctly
  // aligned nested resolver call, retain its RAX, record, then RET to A+5.
  Emit(stub, cursor, {0x48, 0x83, 0xEC, 0x28});
  EmitAbsoluteCall(stub, cursor, state.resolver_target);
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0xC8});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(&NamedPath583ResolverThunkV1));
  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x83, 0xC4, 0x28, 0xC3});
  return cursor;
}

std::size_t BuildMoveStub(
    const NamedPath583RootObserverV1State &state,
    std::array<std::uint8_t, kMaximumStubBytes> &stub) noexcept {
  stub.fill(0x90);
  std::size_t cursor = 0;
  // At B, RAX is the formatted temporary and RDI is CMap+0x18. Preserve the
  // incoming volatile register set around the pre-snapshot so the original
  // two MOVs feed the native move-assign exactly as before.
  EmitPreserveVolatile(stub, cursor);
  Emit(stub, cursor, {0x48, 0x8B, 0x54, 0x24, 0x50});
  Emit(stub, cursor, {0x48, 0x8B, 0xCF});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(&NamedPath583MovePreThunkV1));
  EmitRestoreVolatile(stub, cursor);

  // Reserve fresh shadow space plus two private qwords. The native call may
  // use its shadow space; the observer keeps the temporary above it.
  Emit(stub, cursor, {0x48, 0x83, 0xEC, 0x30});
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0xD0});
  Emit(stub, cursor, {0x48, 0x8B, 0xCF});
  EmitAbsoluteCall(stub, cursor, state.move_target);
  Emit(stub, cursor, {0x48, 0x89, 0x44, 0x24, 0x28});
  Emit(stub, cursor, {0x4C, 0x8B, 0x44, 0x24, 0x28});
  Emit(stub, cursor, {0x48, 0x8B, 0x54, 0x24, 0x20});
  Emit(stub, cursor, {0x48, 0x8B, 0xCF});
  EmitThunkCall(stub, cursor,
                reinterpret_cast<std::uintptr_t>(&NamedPath583MovePostThunkV1));
  Emit(stub, cursor, {0x48, 0x8B, 0x44, 0x24, 0x28});
  Emit(stub, cursor, {0x48, 0x83, 0xC4, 0x30});
  EmitAbsoluteJump(stub, cursor, state.move_continue_target);
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
  const auto backward = static_cast<std::uintptr_t>(0x80000000ULL);
  const auto forward = static_cast<std::uintptr_t>(0x7FFFFFFFULL);
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
  std::uintptr_t cursor = align_up(std::max<std::uintptr_t>(lower_bound,
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
    const auto region_base = reinterpret_cast<std::uintptr_t>(region.BaseAddress);
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

bool Flush(NamedPath583RootObserverV1State &state, const void *address,
           std::size_t size) noexcept {
  if (state.flush_instruction_cache == nullptr ||
      !state.flush_instruction_cache(state.memory_context, address, size)) {
    AddFailure(state, named_path_583_root_observer_failure_flush);
    return false;
  }
  return true;
}

bool WriteHook(NamedPath583RootObserverV1State &state, std::size_t index,
               const std::uint8_t *expected,
               const std::uint8_t *desired) noexcept {
  auto &hook = state.hooks[index];
  if (!SafeBytesEqual(hook.patch_target, expected, hook.patch_size)) {
    AddFailure(state, named_path_583_root_observer_failure_target_identity);
    return false;
  }
  DWORD previous = 0;
  const bool writable = state.virtual_protect != nullptr &&
      state.virtual_protect(state.memory_context,
                            reinterpret_cast<void *>(hook.patch_target),
                            hook.patch_size, PAGE_EXECUTE_READWRITE,
                            previous);
  if (!writable || !Executable(previous)) {
    if (writable) {
      DWORD ignored = 0;
      (void)state.virtual_protect(
          state.memory_context, reinterpret_cast<void *>(hook.patch_target),
          hook.patch_size, previous, ignored);
    }
    AddFailure(state, named_path_583_root_observer_failure_target_protection);
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
    AddFailure(state, named_path_583_root_observer_failure_rollback);
  }
  return false;
}

bool HasOverrides(const NamedPath583RootObserverEnvironmentV1 &environment) {
  return environment.patch_target_overrides !=
             std::array<std::uintptr_t, 2>{} ||
      environment.move_continue_target_override != 0 ||
      environment.resolver_target_override != 0 ||
      environment.move_target_override != 0 ||
      environment.memory_context != nullptr ||
      environment.virtual_alloc_near_override != nullptr ||
      environment.virtual_free_override != nullptr ||
      environment.virtual_protect_override != nullptr ||
      environment.flush_instruction_cache_override != nullptr;
}

void ClearRuntime(NamedPath583RootObserverV1State &state) noexcept {
  state.module_base = 0;
  state.resolver_target = 0;
  state.move_target = 0;
  state.move_continue_target = 0;
  state.memory_context = nullptr;
  state.virtual_free = nullptr;
  state.virtual_protect = nullptr;
  state.flush_instruction_cache = nullptr;
  for (auto &hook : state.hooks) {
    hook.patch_target = 0;
    hook.patch_size = 0;
  }
}

NamedPath583StringDiagnosticsV1 ReadString(
    const NamedPath583StringObservationV1 &source) noexcept {
  NamedPath583StringDiagnosticsV1 result{};
  result.object = source.object.load(std::memory_order_acquire);
  result.effective_data = source.effective_data.load(std::memory_order_acquire);
  result.length = source.length.load(std::memory_order_acquire);
  result.capacity = source.capacity.load(std::memory_order_acquire);
  result.word0 = source.word0.load(std::memory_order_acquire);
  result.word1 = source.word1.load(std::memory_order_acquire);
  result.null_result =
      source.null_result.load(std::memory_order_acquire) != 0;
  result.read_fault = source.read_fault.load(std::memory_order_acquire) != 0;
  return result;
}

} // namespace

void RecordNamedPath583ResolverV1(NamedPath583RootObserverV1State &state,
                                  std::uintptr_t resolver_result,
                                  std::uint32_t thread_id) noexcept {
  const auto sequence =
      state.next_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  auto &slot = state.slots[(sequence - 1) % state.slots.size()];
  slot.published_sequence.store(0, std::memory_order_release);
  slot.thread_id.store(thread_id, std::memory_order_relaxed);
  slot.move_pre_seen.store(0, std::memory_order_relaxed);
  slot.move_post_seen.store(0, std::memory_order_relaxed);
  slot.move_result.store(0, std::memory_order_relaxed);
  StoreString(slot.resolver, CaptureString(resolver_result));
  ClearString(slot.temporary_before);
  ClearString(slot.root_before);
  ClearString(slot.temporary_after);
  ClearString(slot.root_after);
  slot.published_sequence.store(sequence, std::memory_order_release);
  state.last_resolver_sequence.store(sequence, std::memory_order_release);
  state.resolver_count.fetch_add(1, std::memory_order_release);
}

void RecordNamedPath583MovePreV1(NamedPath583RootObserverV1State &state,
                                 std::uintptr_t root,
                                 std::uintptr_t temporary,
                                 std::uint32_t thread_id) noexcept {
  auto *slot = FindLatestThreadSlot(state, thread_id, false);
  if (slot == nullptr) {
    state.correlation_miss_count.fetch_add(1, std::memory_order_release);
    return;
  }
  const auto sequence =
      slot->published_sequence.load(std::memory_order_acquire);
  StoreString(slot->temporary_before, CaptureString(temporary));
  StoreString(slot->root_before, CaptureString(root));
  slot->move_pre_seen.store(1, std::memory_order_release);
  state.last_move_pre_sequence.store(sequence, std::memory_order_release);
  state.move_pre_count.fetch_add(1, std::memory_order_release);
}

void RecordNamedPath583MovePostV1(NamedPath583RootObserverV1State &state,
                                  std::uintptr_t root,
                                  std::uintptr_t temporary,
                                  std::uintptr_t move_result,
                                  std::uint32_t thread_id) noexcept {
  auto *slot = FindLatestThreadSlot(state, thread_id, true);
  if (slot == nullptr) {
    state.correlation_miss_count.fetch_add(1, std::memory_order_release);
    return;
  }
  const auto sequence =
      slot->published_sequence.load(std::memory_order_acquire);
  StoreString(slot->temporary_after, CaptureString(temporary));
  StoreString(slot->root_after, CaptureString(root));
  slot->move_result.store(move_result, std::memory_order_relaxed);
  slot->move_post_seen.store(1, std::memory_order_release);
  state.last_move_post_sequence.store(sequence, std::memory_order_release);
  state.move_post_count.fetch_add(1, std::memory_order_release);
}

bool InstallNamedPath583RootObserverV1(
    NamedPath583RootObserverV1State &state,
    const NamedPath583RootObserverEnvironmentV1 &environment) noexcept {
  state.failure_flags.store(named_path_583_root_observer_failure_none,
                            std::memory_order_relaxed);
  if (!environment.exact_build_admitted || environment.module_base == 0) {
    AddFailure(state, named_path_583_root_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    AddFailure(state,
               named_path_583_root_observer_failure_primary_thread_suspended);
    return false;
  }
  if (!environment.offline_fixture && HasOverrides(environment)) {
    AddFailure(state, named_path_583_root_observer_failure_unsupported_override);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0 ||
      g_active.load(std::memory_order_acquire) != nullptr) {
    AddFailure(state, named_path_583_root_observer_failure_already_installed);
    return false;
  }

  state.module_base = environment.module_base;
  state.hooks[0].patch_size = kNamedPath583ResolverPatchBytesV1;
  state.hooks[0].patch_target = Resolve(environment.patch_target_overrides[0],
                                        environment.module_base,
                                        kNamedPath583ResolverCallRvaV1);
  state.hooks[1].patch_size = kNamedPath583MovePatchBytesV1;
  state.hooks[1].patch_target = Resolve(environment.patch_target_overrides[1],
                                        environment.module_base,
                                        kNamedPath583MovePatchRvaV1);
  state.move_continue_target = Resolve(
      environment.move_continue_target_override, environment.module_base,
      kNamedPath583MoveContinueRvaV1);
  state.resolver_target = Resolve(environment.resolver_target_override,
                                  environment.module_base,
                                  kNamedPath583ResolverTargetRvaV1);
  state.move_target = Resolve(environment.move_target_override,
                              environment.module_base,
                              kNamedPath583MoveTargetRvaV1);
  if (state.hooks[0].patch_target == 0 ||
      state.hooks[1].patch_target == 0 || state.move_continue_target == 0 ||
      state.resolver_target == 0 || state.move_target == 0 ||
      !SafeBytesEqual(state.hooks[0].patch_target, kResolverCallAnchor.data(),
                      kResolverCallAnchor.size()) ||
      !SafeBytesEqual(state.hooks[1].patch_target, kMoveCallAnchor.data(),
                      kMoveCallAnchor.size()) ||
      !SafeCopyFrom(state.hooks[0].patch_target,
                    state.hooks[0].original.data(),
                    state.hooks[0].patch_size) ||
      !SafeCopyFrom(state.hooks[1].patch_target,
                    state.hooks[1].original.data(),
                    state.hooks[1].patch_size)) {
    AddFailure(state, named_path_583_root_observer_failure_anchor);
    ClearRuntime(state);
    return false;
  }

  std::uintptr_t lower0 = 0, upper0 = 0, lower1 = 0, upper1 = 0;
  if (!BaseBoundsForBranch(state.hooks[0].patch_target, kResolverStubOffset,
                           lower0, upper0) ||
      !BaseBoundsForBranch(state.hooks[1].patch_target, kMoveStubOffset,
                           lower1, upper1)) {
    AddFailure(state, named_path_583_root_observer_failure_stub_range);
    ClearRuntime(state);
    return false;
  }
  const auto lower = std::max(lower0, lower1);
  const auto upper = std::min(upper0, upper1);
  if (lower > upper) {
    AddFailure(state, named_path_583_root_observer_failure_stub_range);
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
      state.memory_context, lower, upper, kNamedPath583StubAllocationBytesV1,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.stub_allocation == nullptr) {
    AddFailure(state, named_path_583_root_observer_failure_allocation);
    ClearRuntime(state);
    return false;
  }

  const auto stub_base =
      reinterpret_cast<std::uintptr_t>(state.stub_allocation);
  std::array<std::uint8_t, kMaximumStubBytes> resolver_stub{};
  std::array<std::uint8_t, kMaximumStubBytes> move_stub{};
  const auto resolver_used = BuildResolverStub(state, resolver_stub);
  const auto move_used = BuildMoveStub(state, move_stub);
  const auto resolver_address = stub_base + kResolverStubOffset;
  const auto move_address = stub_base + kMoveStubOffset;
  if (resolver_used == 0 || resolver_used > resolver_stub.size() ||
      move_used == 0 || move_used > move_stub.size() ||
      !BuildRelativeBranch(state.hooks[0].patch_target, resolver_address,
                           0xE8, state.hooks[0].installed_patch.data(),
                           state.hooks[0].patch_size) ||
      !BuildRelativeBranch(state.hooks[1].patch_target, move_address,
                           0xE9, state.hooks[1].installed_patch.data(),
                           state.hooks[1].patch_size) ||
      !SafeCopyTo(resolver_address, resolver_stub.data(), resolver_used) ||
      !SafeCopyTo(move_address, move_stub.data(), move_used)) {
    AddFailure(state, named_path_583_root_observer_failure_stub_range);
    (void)UninstallNamedPath583RootObserverV1(state);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, state.stub_allocation,
                             kNamedPath583StubAllocationBytesV1,
                             PAGE_EXECUTE_READ, old) ||
      !Flush(state, state.stub_allocation,
             kNamedPath583StubAllocationBytesV1)) {
    AddFailure(state, named_path_583_root_observer_failure_stub_protection);
    (void)UninstallNamedPath583RootObserverV1(state);
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
      (void)UninstallNamedPath583RootObserverV1(state);
      return false;
    }
    state.installed_mask.fetch_or(1U << index, std::memory_order_release);
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallNamedPath583RootObserverV1(
    NamedPath583RootObserverV1State &state) noexcept {
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
      AddFailure(state, named_path_583_root_observer_failure_rollback);
      result = false;
    } else {
      state.stub_allocation = nullptr;
    }
  }
  state.installed.store(0, std::memory_order_release);
  if (result) ClearRuntime(state);
  return result;
}

NamedPath583RootObserverV1Diagnostics
ReadNamedPath583RootObserverV1Diagnostics(
    const NamedPath583RootObserverV1State &state) noexcept {
  NamedPath583RootObserverV1Diagnostics result{};
  result.installed = state.installed.load(std::memory_order_acquire) != 0;
  result.installed_mask =
      state.installed_mask.load(std::memory_order_acquire);
  result.failure_flags =
      state.failure_flags.load(std::memory_order_acquire);
  result.resolver_count = state.resolver_count.load(std::memory_order_acquire);
  result.move_pre_count = state.move_pre_count.load(std::memory_order_acquire);
  result.move_post_count = state.move_post_count.load(std::memory_order_acquire);
  result.correlation_miss_count =
      state.correlation_miss_count.load(std::memory_order_acquire);
  result.sequence =
      state.last_move_post_sequence.load(std::memory_order_acquire);
  if (result.sequence == 0) {
    result.sequence =
        state.last_move_pre_sequence.load(std::memory_order_acquire);
  }
  if (result.sequence == 0) {
    result.sequence =
        state.last_resolver_sequence.load(std::memory_order_acquire);
  }
  auto *slot = FindSequenceSlot(state, result.sequence);
  if (slot == nullptr) return result;
  result.thread_id = slot->thread_id.load(std::memory_order_acquire);
  result.move_pre_seen =
      slot->move_pre_seen.load(std::memory_order_acquire) != 0;
  result.move_post_seen =
      slot->move_post_seen.load(std::memory_order_acquire) != 0;
  result.move_result = slot->move_result.load(std::memory_order_acquire);
  result.resolver = ReadString(slot->resolver);
  result.temporary_before = ReadString(slot->temporary_before);
  result.root_before = ReadString(slot->root_before);
  result.temporary_after = ReadString(slot->temporary_after);
  result.root_after = ReadString(slot->root_after);
  return result;
}

} // namespace xar::bridge
