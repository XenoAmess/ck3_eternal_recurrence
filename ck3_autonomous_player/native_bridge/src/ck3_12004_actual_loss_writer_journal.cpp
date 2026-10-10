#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {

constexpr std::array<std::uint8_t, kActualLossWriterPatchBytes12004>
    kWriterPrologue{0x40, 0x53, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x38,
                    0x81, 0x79, 0x14, 0x67, 0x52, 0x72, 0x41};
constexpr std::uint32_t kArmyRegimentMagic = 0x41725267;
constexpr std::size_t kPhysicalBytes = 0x1C;
constexpr std::size_t kDataStride = 0x10;

using Event = game::ArmyActualLossWriterObservationV1;
struct JournalSlot {
  std::uint64_t sequence = 0;
  Event event{};
};
std::array<JournalSlot, game::kArmyActualLossWriterJournalCapacityV1> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0;
std::uint64_t g_unattributed_failures = 0;
ActualLossWriterJournalBindingsV1 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<ActualLossWriterOriginalV1> g_original{nullptr};
std::atomic<ActualLossWriterJournalDetourStateV1 *> g_active_state{nullptr};
std::atomic<ActualLossWriterCompletionObserverV1> g_completion_observer{nullptr};

template <typename Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}

bool ReadMemory(const void *address, void *output, std::size_t size) noexcept {
  if (address == nullptr) return false;
  return FaultBoundary([&]() noexcept {
    if (g_bindings.read_memory != nullptr)
      return g_bindings.read_memory(g_bindings.read_context, address, output, size);
    std::memcpy(output, address, size);
    return true;
  });
}

template <typename Value>
bool ReadAt(const void *object, std::size_t offset, Value &output) noexcept {
  return object != nullptr &&
      ReadMemory(static_cast<const std::byte *>(object) + offset,
                 &output, sizeof(output));
}

template <typename Value, std::size_t Size>
Value FromBytes(const std::array<std::byte, Size> &bytes,
                std::size_t offset) noexcept {
  Value value{};
  std::memcpy(&value, bytes.data() + offset, sizeof(value));
  return value;
}

struct RegimentValues {
  std::int32_t id = -1;
  std::int32_t current = 0;
  std::int32_t maximum = 0;
};

bool ReadRegiment(void *regiment, RegimentValues &values) noexcept {
  std::uint32_t magic = 0;
  return ReadAt(regiment, 0x14, magic) && magic == kArmyRegimentMagic &&
      ReadAt(regiment, 0x10, values.id) && values.id != -1 &&
      ReadAt(regiment, 0x38, values.current) &&
      ReadAt(regiment, 0x3C, values.maximum);
}

void CaptureClock(Event &event) noexcept {
  void *game_state = nullptr;
  std::int32_t date = 0;
  if (ReadMemory(g_bindings.game_state_slot, &game_state, sizeof(game_state)) &&
      ReadAt(game_state, 0x08, date))
    event.observed_date_raw = date;
  else event.capture_failure_flags |= game::army_actual_loss_capture_clock;
}

struct PhysicalIdentity {
  std::int32_t persistent_id = -1;
  std::int32_t own_ordinal = -1;
  std::int32_t army_regiment_id = -1;
  friend bool operator==(const PhysicalIdentity &, const PhysicalIdentity &) = default;
};
struct PhysicalContext {
  const std::byte *data = nullptr;
  std::int32_t count = 0;
  bool header_valid = false;
  bool complete = false;
  std::array<std::array<std::byte, kDataStride>,
             game::kArmyActualLossWriterMaximumDataRecordsV1> data_bytes{};
  std::array<bool, game::kArmyActualLossWriterMaximumDataRecordsV1> data_read{};
  std::array<void *, game::kArmyActualLossWriterMaximumDataRecordsV1> slots{};
  std::array<PhysicalIdentity,
             game::kArmyActualLossWriterMaximumDataRecordsV1> identities{};
  std::array<bool, game::kArmyActualLossWriterMaximumDataRecordsV1> before_read{};
};

bool ReadDataHeader(void *regiment, const std::byte *&data,
                    std::int32_t &count) noexcept {
  std::int32_t capacity = 0;
  return ReadAt(regiment, 0x20, data) && ReadAt(regiment, 0x28, capacity) &&
      ReadAt(regiment, 0x2C, count) && capacity >= 0 && count >= 0 &&
      count <= capacity && (count == 0 || data != nullptr);
}

bool ReadPhysical(void *chunk, game::ArmyActualLossWriterPhysicalValuesV1 &values,
                  PhysicalIdentity &identity) noexcept {
  std::array<std::byte, kPhysicalBytes> bytes{};
  if (!ReadMemory(chunk, bytes.data(), bytes.size())) return false;
  values.maximum_soldiers = FromBytes<std::int32_t>(bytes, 0x00);
  values.current_soldiers = FromBytes<std::int32_t>(bytes, 0x04);
  values.state_raw = FromBytes<std::int32_t>(bytes, 0x18);
  identity.persistent_id = FromBytes<std::int32_t>(bytes, 0x08);
  identity.own_ordinal = FromBytes<std::int32_t>(bytes, 0x0C);
  identity.army_regiment_id = FromBytes<std::int32_t>(bytes, 0x10);
  return true;
}

void CapturePhysicalBefore(void *regiment, Event &event,
                           PhysicalContext &context) noexcept {
  context.header_valid = ReadDataHeader(regiment, context.data, context.count);
  if (!context.header_valid) {
    event.capture_failure_flags |= game::army_actual_loss_capture_data_header;
    return;
  }
  event.native_data_record_count = context.count;
  context.complete = true;
  event.captured_data_record_count = static_cast<std::uint32_t>(
      std::min<std::size_t>(static_cast<std::size_t>(context.count),
                          game::kArmyActualLossWriterMaximumDataRecordsV1));
  if (context.count > static_cast<std::int32_t>(
                          game::kArmyActualLossWriterMaximumDataRecordsV1)) {
    context.complete = false;
    event.capture_failure_flags |= game::army_actual_loss_capture_data_truncated;
  }
  for (std::uint32_t index = 0; index < event.captured_data_record_count; ++index) {
    auto &alias = event.data_aliases[index];
    alias.data_record_index = static_cast<std::int32_t>(index);
    auto *record = const_cast<std::byte *>(context.data) + index * kDataStride;
    auto &bytes = context.data_bytes[index];
    context.data_read[index] = ReadMemory(record, bytes.data(), bytes.size());
    if (!context.data_read[index]) {
      context.complete = false;
      event.capture_failure_flags |= game::army_actual_loss_capture_data_record;
      continue;
    }
    alias.persistent_regiment_id = FromBytes<std::int32_t>(bytes, 0x08);
    alias.data_chunk_ordinal = FromBytes<std::int32_t>(bytes, 0x0C);
    void *chunk = nullptr;
    const bool selected = g_bindings.select_physical_slot != nullptr &&
        FaultBoundary([&]() noexcept {
          chunk = g_bindings.select_physical_slot(record);
          return chunk != nullptr;
        });
    if (!selected) {
      context.complete = false;
      event.capture_failure_flags |= game::army_actual_loss_capture_physical_before;
      continue;
    }
    std::uint32_t slot = 0;
    while (slot < event.physical_slot_count && context.slots[slot] != chunk) ++slot;
    alias.physical_slot_index = static_cast<std::int32_t>(slot);
    if (slot != event.physical_slot_count) continue;
    ++event.physical_slot_count;
    context.slots[slot] = chunk;
    context.before_read[slot] = ReadPhysical(
        chunk, event.physical_slots[slot].before, context.identities[slot]);
    if (!context.before_read[slot]) {
      context.complete = false;
      event.capture_failure_flags |= game::army_actual_loss_capture_physical_before;
    }
  }
}

void CapturePhysicalAfter(void *regiment, Event &event,
                          PhysicalContext &context) noexcept {
  if (!context.header_valid) return;
  bool complete = context.complete && event.same_instance_after;
  const std::byte *after_data = nullptr;
  std::int32_t after_count = 0;
  const bool same_header = ReadDataHeader(regiment, after_data, after_count) &&
      after_data == context.data && after_count == context.count;
  if (!same_header) {
    complete = false;
    event.capture_failure_flags |= game::army_actual_loss_capture_data_changed;
  } else {
    for (std::uint32_t index = 0; index < event.captured_data_record_count; ++index) {
      std::array<std::byte, kDataStride> after_bytes{};
      if (!context.data_read[index] ||
          !ReadMemory(after_data + index * kDataStride,
                      after_bytes.data(), after_bytes.size()) ||
          FromBytes<std::int32_t>(after_bytes, 0x08) !=
              FromBytes<std::int32_t>(context.data_bytes[index], 0x08) ||
          FromBytes<std::int32_t>(after_bytes, 0x0C) !=
              FromBytes<std::int32_t>(context.data_bytes[index], 0x0C)) {
        complete = false;
        event.capture_failure_flags |= game::army_actual_loss_capture_data_changed;
      }
    }
  }
  std::int64_t debit = 0;
  for (std::uint32_t index = 0; index < event.physical_slot_count; ++index) {
    auto &slot = event.physical_slots[index];
    PhysicalIdentity after_identity{};
    const bool after_read = ReadPhysical(context.slots[index], slot.after,
                                         after_identity);
    slot.same_instance_after = context.before_read[index] && after_read &&
        context.identities[index] == after_identity;
    if (!slot.same_instance_after) {
      complete = false;
      event.capture_failure_flags |= game::army_actual_loss_capture_physical_after;
    } else {
      debit += static_cast<std::int64_t>(*slot.before.current_soldiers) -
          *slot.after.current_soldiers;
    }
  }
  event.physical_capture_complete = complete;
  if (complete) event.actual_physical_soldier_debit = debit;
}

bool InitializeRuntime(const ActualLossWriterJournalBindingsV1 &bindings,
                       ActualLossWriterOriginalV1 original) noexcept {
  if (!bindings.enabled || original == nullptr)
    return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_journal_mutex);
    g_bindings = bindings;
    g_latest_sequence = 0;
    g_unattributed_failures = 0;
    for (auto &slot : g_slots) slot = {};
  }
  g_original.store(original, std::memory_order_release);
  g_available.store(true, std::memory_order_release);
  return true;
}

void Publish(Event &event) noexcept {
  const std::lock_guard lock(g_journal_mutex);
  if (event.army_regiment_id == -1) {
    ++g_unattributed_failures;
    return;
  }
  event.sequence = ++g_latest_sequence;
  auto &slot = g_slots[(event.sequence - 1) % g_slots.size()];
  slot.event = event;
  slot.sequence = event.sequence;
}

void WriteAbsoluteJump(std::uint8_t *destination, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF, 0x25, 0, 0, 0, 0};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}
bool DefaultFree(void *, void *address, std::size_t size, DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
void *DefaultAlloc(void *, std::size_t size, DWORD type, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool DefaultProtect(void *, void *address, std::size_t size, DWORD protection,
                    DWORD &old) noexcept {
  return VirtualProtect(address, size, protection, &old) != FALSE;
}
bool DefaultFlush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}
void Fail(ActualLossWriterJournalDetourStateV1 &state,
          ActualLossWriterJournalInstallFailureV1 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ActualLossWriterJournalDetourStateV1 &state,
                const std::array<std::uint8_t, kActualLossWriterPatchBytes12004> &expected,
                const std::array<std::uint8_t, kActualLossWriterPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.writer_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, actual_loss_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_loss_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_loss_install_protection : actual_loss_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored) Fail(state, actual_loss_install_rollback);
  return false;
}

std::array<std::uint8_t, kActualLossWriterPatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kActualLossWriterPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarActualLossWriterHook12004V1));
  return patch;
}

} // namespace

ActualLossWriterJournalBindingsV1 BindActualLossWriterJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ActualLossWriterJournalBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = image_base;
  result.game_state_slot = reinterpret_cast<void **>(image_base + kGameStateSlotRva);
  result.select_physical_slot = reinterpret_cast<ActualLossWriterPhysicalSelectorV1>(
      image_base + kActualLossWriterDataSelectorRva12004);
  return result;
}

bool InitializeActualLossWriterJournalFixture12004(
    const ActualLossWriterJournalBindingsV1 &bindings,
    ActualLossWriterOriginalV1 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  return InitializeRuntime(bindings, original);
}

void SetActualLossWriterCompletionObserver12004(
    ActualLossWriterCompletionObserverV1 observer) noexcept {
  g_completion_observer.store(observer, std::memory_order_release);
}

game::ArmyActualLossWriterCallerV1 ClassifyActualLossWriterCallerV1(
    std::uint64_t caller_return_rva) noexcept {
  switch (caller_return_rva) {
  case 0x24E35FF: return game::ArmyActualLossWriterCallerV1::supply_preferred;
  case 0x24E377C: return game::ArmyActualLossWriterCallerV1::siege_or_raid_preferred;
  case 0x2A958E8: return game::ArmyActualLossWriterCallerV1::residual_allocator;
  default: return game::ArmyActualLossWriterCallerV1::other_writer_caller;
  }
}

bool InstallActualLossWriterJournal12004(
    ActualLossWriterJournalDetourStateV1 &state,
    const ActualLossWriterJournalInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(actual_loss_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_loss_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  ActualLossWriterJournalDetourStateV1 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_loss_install_already_installed);
    return false;
  }
  state.writer_target = environment.writer_target_override != 0
      ? environment.writer_target_override
      : environment.bindings.image_base + kActualLossWriterRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override : &DefaultFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override : &DefaultProtect;
  state.flush_instruction_cache = environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override : &DefaultFlush;
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(reinterpret_cast<const void *>(state.writer_target),
                            kWriterPrologue.data(), kWriterPrologue.size()) == 0;
      })) {
    Fail(state, actual_loss_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kActualLossWriterPatchBytes12004 +
      kActualLossWriterAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_loss_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(bytes, kWriterPrologue.data(), kWriterPrologue.size());
  WriteAbsoluteJump(bytes + kWriterPrologue.size(),
                    state.writer_target + kWriterPrologue.size());
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, trampoline_bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, trampoline_bytes);
  const bool initialized = flushed && InitializeRuntime(environment.bindings,
      reinterpret_cast<ActualLossWriterOriginalV1>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kWriterPrologue, HookPatch())) {
    if (!executable) Fail(state, actual_loss_install_protection);
    else if (!flushed) Fail(state, actual_loss_install_flush);
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.original = kWriterPrologue;
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallActualLossWriterJournal12004(
    ActualLossWriterJournalDetourStateV1 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence);
    return false;
  }
  if (!WritePatch(state, HookPatch(), state.original)) return false;
  state.installed.store(0, std::memory_order_release);
  g_available.store(false, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  g_active_state.store(nullptr, std::memory_order_release);
  const bool freed = state.virtual_free(state.memory_context, state.trampoline,
                                         0, MEM_RELEASE);
  if (freed) state.trampoline = nullptr;
  else Fail(state, actual_loss_install_allocation);
  return freed;
}

std::optional<game::ArmyActualLossWriterObservationsV1>
ReadActualLossWriterObservations12004(
    std::span<const std::int32_t> current_full_regiment_ids) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  try {
    game::ArmyActualLossWriterObservationsV1 result{};
    const auto *active = g_active_state.load(std::memory_order_acquire);
    result.observer_installed = active != nullptr &&
        active->installed.load(std::memory_order_acquire) != 0;
    const std::lock_guard lock(g_journal_mutex);
    result.latest_sequence = g_latest_sequence;
    result.oldest_available_sequence = g_latest_sequence == 0 ? 0
        : g_latest_sequence <= g_slots.size() ? 1
        : g_latest_sequence - g_slots.size() + 1;
    result.overwritten_events = g_latest_sequence > g_slots.size()
        ? g_latest_sequence - g_slots.size() : 0;
    result.unattributed_capture_failures = g_unattributed_failures;
    for (auto sequence = result.oldest_available_sequence;
         sequence != 0 && sequence <= g_latest_sequence; ++sequence) {
      const auto &slot = g_slots[(sequence - 1) % g_slots.size()];
      if (slot.sequence != sequence) continue;
      if (std::find(current_full_regiment_ids.begin(), current_full_regiment_ids.end(),
                    slot.event.army_regiment_id) != current_full_regiment_ids.end())
        result.events.push_back(slot.event);
    }
    return result;
  } catch (...) {
    return std::nullopt;
  }
}

extern "C" void __fastcall XarActualLossWriterHook12004V1(
    void *regiment, std::int64_t request_raw) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return;
  Event event{};
  event.request_raw = request_raw;
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  if (caller >= g_bindings.image_base && g_bindings.image_base != 0) {
    event.caller_return_rva = caller - g_bindings.image_base;
    event.caller = ClassifyActualLossWriterCallerV1(*event.caller_return_rva);
  }
  CaptureClock(event);
  RegimentValues before{};
  const bool before_read = ReadRegiment(regiment, before);
  PhysicalContext physical{};
  if (before_read) {
    event.army_regiment_id = before.id;
    event.before_current_soldiers = before.current;
    event.before_maximum_soldiers = before.maximum;
    CapturePhysicalBefore(regiment, event, physical);
  } else event.capture_failure_flags |= game::army_actual_loss_capture_before;

  // The natural native invocation is forwarded exactly once, outside capture
  // fault boundaries. This observer never invokes the writer from a query.
  original(regiment, request_raw);

  RegimentValues after{};
  const bool after_read = ReadRegiment(regiment, after);
  if (after_read) {
    event.after_current_soldiers = after.current;
    event.after_maximum_soldiers = after.maximum;
    event.same_instance_after = before_read && before.id == after.id;
  }
  if (!event.same_instance_after)
    event.capture_failure_flags |= game::army_actual_loss_capture_after;
  if (before_read) CapturePhysicalAfter(regiment, event, physical);
  Publish(event);
  if (const auto observer = g_completion_observer.load(std::memory_order_acquire))
    observer(regiment, event);
}

} // namespace xar::ck3_12004
