#include "xar_bridge/ck3_12004_actual_loss_writer_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
#include "xar_bridge/ck3_12002_army.hpp"
#endif
#include "xar_bridge/ck3_12004_supply_parent_join_context.hpp"
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
#include "xar_bridge/ck3_12004_residual_parent_context.hpp"
#endif

#include <algorithm>
#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
extern "C" void XarActualLossWriterCountyEntryThunk12004V1(void *,std::int64_t) noexcept;
#endif
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
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
thread_local const CountyPrimaryWriterRegisters12004 *g_county_writer_registers=nullptr;
ck3_12002::ArmyBindings g_county_registry_bindings{};
std::array<game::ArmyCountyPrimaryDirectOwnerAtWriterV2,64> g_county_unbound_slots{};
std::size_t g_county_unbound_count=0,g_county_unbound_next=0;
std::uint64_t g_county_unbound_overwritten=0;
struct RestoreCountyWriterRegisters {
  const CountyPrimaryWriterRegisters12004 *previous;
  ~RestoreCountyWriterRegisters(){g_county_writer_registers=previous;}
};
#endif

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
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
    g_county_registry_bindings={};
    g_county_registry_bindings.enabled=bindings.county_direct_source_qualified;
    g_county_registry_bindings.internal_army_storage_slot=bindings.county_army_registry_slot;
    g_county_registry_bindings.unit_storage_slot=bindings.county_unit_registry_slot;
    g_county_registry_bindings.regiment_storage_slot=bindings.county_arrg_registry_slot;
    g_county_registry_bindings.persistent_regiment_storage_slot=bindings.county_regi_registry_slot;
    for(auto &slot:g_county_unbound_slots)slot={};
    g_county_unbound_count=0;g_county_unbound_next=0;g_county_unbound_overwritten=0;
#endif
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
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
    if(event.county_primary_direct_owner_at_writer_v2){
      auto diagnostic=*event.county_primary_direct_owner_at_writer_v2;
      diagnostic.source_complete=false;
      if(!diagnostic.capture_failure_flags)diagnostic.capture_failure_flags=county_direct_writer_identity;
      g_county_unbound_slots[g_county_unbound_next]=diagnostic;
      g_county_unbound_next=(g_county_unbound_next+1)%g_county_unbound_slots.size();
      if(g_county_unbound_count<g_county_unbound_slots.size())++g_county_unbound_count;
      else if(g_county_unbound_overwritten!=UINT64_MAX)++g_county_unbound_overwritten;
    }
#endif
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
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
      &XarActualLossWriterCountyEntryThunk12004V1));
#else
      &XarActualLossWriterHook12004V1));
#endif
  return patch;
}

} // namespace

ActualLossWriterJournalBindingsV1 BindActualLossWriterJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ActualLossWriterJournalBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = image_base;
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
  // Exact-.4 binder mapping, adopted from ck3_12004_army.cpp/support.
  // This is build/source binding, never a claim of live business acceptance.
  result.county_direct_source_qualified=true;
  result.county_army_registry_slot=reinterpret_cast<void **>(image_base+0x5D1DE48);
  result.county_unit_registry_slot=reinterpret_cast<void **>(image_base+0x5D1E380);
  result.county_arrg_registry_slot=reinterpret_cast<void **>(image_base+0x5D1F340);
  result.county_regi_registry_slot=reinterpret_cast<void **>(image_base+0x5D1EB68);
#endif
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
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
    result.unbound_county_primary_direct_diagnostics_overwritten_v2=g_county_unbound_overwritten;
    const auto first=g_county_unbound_count<g_county_unbound_slots.size()?0:g_county_unbound_next;
    for(std::size_t i=0;i<g_county_unbound_count;++i)
      result.unbound_county_primary_direct_diagnostics_v2.push_back(
          g_county_unbound_slots[(first+i)%g_county_unbound_slots.size()]);
#endif
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

#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
// The MASM entry owns the original return slot and caller R13 before
// a C++ prologue can reuse them. This is not a new native detour location.
extern "C" void __fastcall XarActualLossWriterHookCapturedCounty12004V1(
    void *regiment,std::int64_t request_raw,const void *return_slot,
    const void *source_carmy) noexcept {
  std::uintptr_t caller=0;
  const bool readable=ReadMemory(return_slot,&caller,sizeof caller);
  const auto rva=readable&&g_bindings.image_base&&caller>=g_bindings.image_base
      ?std::optional<std::uint64_t>(caller-g_bindings.image_base):std::nullopt;
  const auto token=rva==0x24E25EE
      ?native_invocation_detail_12004::AllocateToken(native_invocation_detail_12004::next_token):0;
  const CountyPrimaryWriterRegisters12004 registers{regiment,source_carmy,
      rva.value_or(0),token,GetCurrentThreadId()};
  RestoreCountyWriterRegisters restore{g_county_writer_registers};
  // Unknown/nested callers mask an outer register context instead of borrowing it.
  g_county_writer_registers=&registers;
  InvokeActualLossWriterJournalWithCaller12004V1(regiment,request_raw,rva,return_slot);
}
#endif

extern "C" void __fastcall XarActualLossWriterHook12004V1(
    void *regiment, std::int64_t request_raw) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  std::optional<std::uint64_t> caller_return_rva;
  if (caller >= g_bindings.image_base && g_bindings.image_base != 0) {
    caller_return_rva = caller - g_bindings.image_base;
  }
  // Capture the REAL natural hook incoming return slot before entering the
  // shared typed producer. Its own helper return frame is a different stack.
  const void *natural_writer_return_address_slot = nullptr;
#if defined(_MSC_VER) && XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004
  natural_writer_return_address_slot = _AddressOfReturnAddress();
#endif
  InvokeActualLossWriterJournalWithCaller12004V1(regiment, request_raw,
      caller_return_rva, natural_writer_return_address_slot);
}

void InvokeActualLossWriterJournalWithCaller12004V1(
    void *regiment, std::int64_t request_raw,
    std::optional<std::uint64_t> caller_return_rva,
    const void *natural_writer_return_address_slot) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return;
  Event event{};
  event.request_raw = request_raw;
  event.caller_return_rva = caller_return_rva;
  if (caller_return_rva)
    event.caller = ClassifyActualLossWriterCallerV1(*caller_return_rva);
  CaptureClock(event);
#if XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004
  const auto supply_read_at = [](const void *receiver, std::size_t offset,
                                void *output, std::size_t size) noexcept {
    return receiver != nullptr && ReadMemory(
        static_cast<const std::byte *>(receiver) + offset, output, size);
  };
  event.supply_parent_context_v1 = CaptureSupplyParentWriterContext12004(
      static_cast<std::uint32_t>(GetCurrentThreadId()), supply_read_at);
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
  if (!event.supply_parent_context_v1)
    event.supply_parent_context_v1 = CaptureResidualEnclosingSupplyWriterContext12004(
        static_cast<std::uint32_t>(GetCurrentThreadId()), event.caller_return_rva, supply_read_at);
#endif
  if (event.supply_parent_context_v1)
    event.siege_budget_at_writer_v1 = CaptureSiegeBudgetAtNaturalWriter12004(
        event.caller_return_rva, natural_writer_return_address_slot, supply_read_at);
#else
  (void)natural_writer_return_address_slot;
#endif
  RegimentValues before{};
  const bool before_read = ReadRegiment(regiment, before);
  PhysicalContext physical{};
  if (before_read) {
    event.army_regiment_id = before.id;
    event.before_current_soldiers = before.current;
    event.before_maximum_soldiers = before.maximum;
    CapturePhysicalBefore(regiment, event, physical);
  } else event.capture_failure_flags |= game::army_actual_loss_capture_before;
#if defined(XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004)
  if (before_read) event.residual_parent_context_v1 = CaptureResidualParentWriterContext12004(
      static_cast<std::uint32_t>(GetCurrentThreadId()), before.id, event.caller_return_rva);
#endif

#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
  if(caller_return_rva==0x24E25EE&&g_bindings.county_primary_phase_reader){
    // Actual sampling is read before any owner registry/native-memory capture.
    const auto active=g_bindings.county_primary_phase_reader();
    if(active.sampling.enabled){
      void *current_state=nullptr;
      (void)ReadMemory(g_bindings.game_state_slot,&current_state,sizeof current_state);
      const auto reader=[](void *,const void *p,void *out,std::size_t n) noexcept {
        return ReadMemory(p,out,n);
      };
      const auto lookup=[](void *,CountyDirectRegistryKind12004 kind,std::int32_t id) noexcept -> const void * {
        const void *result=nullptr;
        (void)FaultBoundary([&]() noexcept {
          switch(kind){
          case CountyDirectRegistryKind12004::army:result=ck3_12002::ResolveInternalArmy(g_county_registry_bindings,id);break;
          case CountyDirectRegistryKind12004::unit:result=ck3_12002::ResolveArmyUnit(g_county_registry_bindings,id);break;
          case CountyDirectRegistryKind12004::army_regiment:result=ck3_12002::ResolveArmyRegimentStrict(g_county_registry_bindings,id);break;
          case CountyDirectRegistryKind12004::persistent_regiment:result=ck3_12002::ResolvePersistentRegimentStrict(g_county_registry_bindings,id);break;
          }
          return true;
        });
        return result;
      };
      CountyDirectPhysicalInputs12004 inputs{};
      for(std::size_t i=0;i<inputs.selected_slots.size();++i)inputs.selected_slots[i]=physical.slots[i];
      event.county_primary_direct_owner_at_writer_v2=CaptureCountyPrimaryDirectOwnerAtWriter12004(
          reader,nullptr,lookup,nullptr,g_county_writer_registers,active,event,inputs,regiment,
          static_cast<std::uint32_t>(GetCurrentThreadId()),reinterpret_cast<std::uintptr_t>(current_state),
          g_bindings.county_direct_source_qualified);
      // The v1 producer and its strict pre-date/phase roster contract are intact.
      if(before_read&&g_county_writer_registers&&g_county_writer_registers->writer_receiver==regiment)
        event.county_primary_owner_at_writer_v1=CaptureCountyPrimaryOwnerAtWriter12004(
            reader,nullptr,*g_county_writer_registers,active,before.id,event.observed_date_raw,
            reinterpret_cast<std::uintptr_t>(current_state));
    }
  }
#endif

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
#if defined(XAR_ENABLE_ACTUAL_COUNTY_PRIMARY_OWNER_12004)
  if(event.county_primary_direct_owner_at_writer_v2){
    const auto sampling=g_bindings.county_direct_sampling_reader
        ?g_bindings.county_direct_sampling_reader():ArmyObserverResearchSamplingState12004{};
    FinishCountyPrimaryDirectOwnerAtWriter12004(*event.county_primary_direct_owner_at_writer_v2,event,sampling);
  }
#endif
  Publish(event);
  if (const auto observer = g_completion_observer.load(std::memory_order_acquire))
    observer(regiment, event);
}

} // namespace xar::ck3_12004
