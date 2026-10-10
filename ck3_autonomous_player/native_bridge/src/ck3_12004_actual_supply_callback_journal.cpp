#include "xar_bridge/ck3_12004_actual_supply_callback_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {

// Frozen 24E3410 entry: 5+4+5+5 whole instructions; no RIP/branch relocation.
constexpr std::array<std::uint8_t, kActualSupplyCallbackPatchBytes12004>
    kCallbackPrologue{0x48, 0x89, 0x4C, 0x24, 0x08, 0x48, 0x83, 0xEC, 0x68,
                      0x48, 0x89, 0x5C, 0x24, 0x78, 0x48, 0x89, 0x74, 0x24, 0x58};

using Event = game::ArmyActualSupplyCallbackObservationV1;
struct JournalSlot {
  std::uint64_t sequence = 0;
  Event event{};
};
std::array<JournalSlot, game::kArmyActualSupplyCallbackJournalCapacityV1> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0;
std::uint64_t g_unattributed_failures = 0;
ActualSupplyCallbackJournalBindingsV1 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<ActualSupplyCallbackOriginalV1> g_original{nullptr};
std::atomic<ActualSupplyCallbackJournalDetourStateV1 *> g_active_state{nullptr};

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
  return object != nullptr && ReadMemory(
      static_cast<const std::byte *>(object) + offset, &output, sizeof(output));
}

struct ArmyIdentity {
  std::int32_t army_id = -1;
  std::int32_t native_carmy_id = -1;
};

bool CaptureIdentity(const void *army, ArmyIdentity &identity) noexcept {
  const bool native_read = ReadAt(army, 0x10, identity.native_carmy_id);
  const bool public_read = ReadAt(army, 0x124, identity.army_id);
  return native_read && public_read && identity.native_carmy_id != -1 &&
      identity.army_id != -1;
}

// Keep individually readable values even when another scalar cannot be read.
bool CaptureValues(const void *army,
                   game::ArmyActualSupplyCallbackValuesV1 &values) noexcept {
  std::int64_t stock = 0;
  std::uint64_t date = 0;
  std::uint8_t updated = 0;
  const bool stock_read = ReadAt(army, 0x180, stock);
  const bool date_read = ReadAt(army, 0x188, date);
  const bool updated_read = ReadAt(army, 0x22, updated);
  if (stock_read) values.supply_raw = stock;
  if (date_read) values.last_supply_update_date_raw64 = date;
  if (updated_read) values.supply_updated_byte_raw = updated;
  return stock_read && date_read && updated_read;
}

bool InitializeRuntime(const ActualSupplyCallbackJournalBindingsV1 &bindings,
                       ActualSupplyCallbackOriginalV1 original) noexcept {
  if (!bindings.enabled || original == nullptr) return false;
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

void Publish(Event &event, bool before_identity_complete) noexcept {
  const std::lock_guard lock(g_journal_mutex);
  if (!before_identity_complete) {
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
void Fail(ActualSupplyCallbackJournalDetourStateV1 &state,
          ActualSupplyCallbackJournalInstallFailureV1 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ActualSupplyCallbackJournalDetourStateV1 &state,
                const std::array<std::uint8_t, kActualSupplyCallbackPatchBytes12004> &expected,
                const std::array<std::uint8_t, kActualSupplyCallbackPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, actual_supply_callback_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_supply_callback_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_supply_callback_install_protection
                     : actual_supply_callback_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, actual_supply_callback_install_rollback);
  return false;
}

std::array<std::uint8_t, kActualSupplyCallbackPatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kActualSupplyCallbackPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarActualSupplyCallbackHook12004V1));
  return patch;
}

} // namespace

ActualSupplyCallbackJournalBindingsV1 BindActualSupplyCallbackJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ActualSupplyCallbackJournalBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = image_base;
  return result;
}

bool InitializeActualSupplyCallbackJournalFixture12004(
    const ActualSupplyCallbackJournalBindingsV1 &bindings,
    ActualSupplyCallbackOriginalV1 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  return InitializeRuntime(bindings, original);
}

bool InstallActualSupplyCallbackJournal12004(
    ActualSupplyCallbackJournalDetourStateV1 &state,
    const ActualSupplyCallbackJournalInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(actual_supply_callback_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_supply_callback_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_supply_callback_install_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  ActualSupplyCallbackJournalDetourStateV1 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_supply_callback_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kActualSupplyCallbackRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override : &DefaultFree;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override : &DefaultProtect;
  state.flush_instruction_cache = environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override : &DefaultFlush;
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(reinterpret_cast<const void *>(state.callback_target),
                            kCallbackPrologue.data(), kCallbackPrologue.size()) == 0;
      })) {
    Fail(state, actual_supply_callback_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kActualSupplyCallbackPatchBytes12004 +
      kActualSupplyCallbackAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_supply_callback_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(bytes, kCallbackPrologue.data(), kCallbackPrologue.size());
  WriteAbsoluteJump(bytes + kCallbackPrologue.size(),
                    state.callback_target + kCallbackPrologue.size());
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, trampoline_bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, trampoline_bytes);
  const bool initialized = flushed && InitializeRuntime(environment.bindings,
      reinterpret_cast<ActualSupplyCallbackOriginalV1>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch())) {
    if (!executable) Fail(state, actual_supply_callback_install_protection);
    else if (!flushed) Fail(state, actual_supply_callback_install_flush);
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.original = kCallbackPrologue;
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallActualSupplyCallbackJournal12004(
    ActualSupplyCallbackJournalDetourStateV1 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, actual_supply_callback_install_quiescence);
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
  else Fail(state, actual_supply_callback_install_allocation);
  return freed;
}

std::optional<game::ArmyActualSupplyCallbackObservationsV1>
ReadActualSupplyCallbackObservations12004(
    std::int32_t army_id, std::int32_t native_carmy_id) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  try {
    game::ArmyActualSupplyCallbackObservationsV1 result{};
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
      if (slot.sequence == sequence && slot.event.army_id == army_id &&
          slot.event.native_carmy_id == native_carmy_id)
        result.events.push_back(slot.event);
    }
    return result;
  } catch (...) {
    return std::nullopt;
  }
}

extern "C" void __fastcall XarActualSupplyCallbackHook12004V1(
    void *army, const void *date) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return;
  Event event{};
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  if (g_bindings.image_base != 0 && caller >= g_bindings.image_base)
    event.caller_return_rva = caller - g_bindings.image_base;
  std::uint64_t passed_date = 0;
  if (ReadMemory(date, &passed_date, sizeof(passed_date)))
    event.passed_date_raw64 = passed_date;
  else event.capture_failure_flags |= actual_supply_callback_capture_date;

  ArmyIdentity before{};
  const bool before_identity_complete = CaptureIdentity(army, before);
  event.army_id = before.army_id;
  event.native_carmy_id = before.native_carmy_id;
  const bool before_values_complete = CaptureValues(army, event.before);
  if (!before_identity_complete || !before_values_complete)
    event.capture_failure_flags |= actual_supply_callback_capture_before;

  // Forward this actual native invocation exactly once, outside capture fault
  // boundaries. Queries never invoke this callback or the supply updater.
  original(army, date);

  ArmyIdentity after{};
  const bool after_identity_complete = CaptureIdentity(army, after);
  const bool after_values_complete = CaptureValues(army, event.after);
  event.same_instance_after = before_identity_complete && after_identity_complete &&
      before.army_id == after.army_id &&
      before.native_carmy_id == after.native_carmy_id;
  if (!after_identity_complete || !after_values_complete)
    event.capture_failure_flags |= actual_supply_callback_capture_after;
  if (before_identity_complete && after_identity_complete &&
      !event.same_instance_after)
    event.capture_failure_flags |= actual_supply_callback_capture_identity_changed;
  Publish(event, before_identity_complete);
}

} // namespace xar::ck3_12004
