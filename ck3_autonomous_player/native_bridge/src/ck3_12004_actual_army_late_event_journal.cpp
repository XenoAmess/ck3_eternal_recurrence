#include "xar_bridge/ck3_12004_actual_army_late_event_journal.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {

// Freeze37CCC39 after the original RDX null guard:3+4+4+1+1+1
// whole instructions, no relative/RIP relocation. The original guard is intact.
constexpr std::array<std::uint8_t, kActualArmyLateEventPatchBytes12004>
    kCallbackPrologue{0x48,0x8B,0xC4,0x48,0x89,0x58,0x18,
                      0x48,0x89,0x48,0x08,0x55,0x56,0x57};

using Event = game::ArmyActualLateEventObservationV1;
struct JournalSlot {
  std::uint64_t sequence = 0;
  Event event{};
};
std::array<JournalSlot, game::kArmyActualLateEventJournalCapacityV1> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0;
std::uint64_t g_unattributed_failures = 0;
ActualArmyLateEventJournalBindingsV1 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<ActualArmyLateEventOriginalV1> g_original{nullptr};
std::atomic<ActualArmyLateEventJournalDetourStateV1 *> g_active_state{nullptr};

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

std::optional<game::ArmyLateEventSourceV1> Classify(std::uint64_t rva) noexcept {
  if (rva == 0x2639CF6) return game::ArmyLateEventSourceV1::positive_1e0;
  if (rva == 0x2C448F5) return game::ArmyLateEventSourceV1::flag21;
  if (rva == 0x24DD7A5) return game::ArmyLateEventSourceV1::flag30;
  return std::nullopt;
}
std::size_t DefinitionSlot(game::ArmyLateEventSourceV1 source) noexcept {
  return source == game::ArmyLateEventSourceV1::positive_1e0 ? 0x168 :
         source == game::ArmyLateEventSourceV1::flag21 ? 0x640 : 0x170;
}
bool IncomingRead(void *, const void *address, void *output, std::size_t size) noexcept {
  return ReadMemory(address, output, size);
}
bool CaptureScope(const void *scope, ArmyLateContextCopy12004 &out) noexcept {
  out = CopyActualArmyLateContext12004(scope, &IncomingRead, nullptr);
  return out.root_copy_ready && out.context_seed_10_raw_u32.has_value() &&
      out.named_rows_copy_ready && !out.named_rows_truncated;
}
ArmyLateContextSourceRoles12004 CaptureFlag21Roles(const ArmyLateContextCopy12004 &scope) noexcept {
  std::array<std::uint32_t,3> keys{};
  constexpr std::array<std::uintptr_t,3> slots{0x5D4C27C,0x5D4BE20,0x5D4BE1C};
  for (std::size_t i=0;i<keys.size();++i)
    if (!ReadMemory(reinterpret_cast<const void *>(g_bindings.image_base+slots[i]), &keys[i], sizeof(keys[i])))
      return {};
  return ClassifyActualArmyLateContextRoles12004(scope, keys);
}
bool CaptureDefinition(const void *manager, const void *definition,
                       game::ArmyLateEventSourceV1 source,
                       game::ArmyLateEventDefinitionV1 &out) noexcept {
  out.definition_address = reinterpret_cast<std::uintptr_t>(definition);
  std::uintptr_t table = 0, selected = 0;
  const bool table_read = ReadAt(manager, 0x38, table) && table &&
      ReadMemory(reinterpret_cast<const void *>(table + DefinitionSlot(source)), &selected, sizeof(selected));
  if (table_read) out.actual_loaded_table_slot_equal = selected == out.definition_address;
  out.row_copy_complete = ReadAt(definition, 0x2C, out.row_index_raw) &&
      ReadAt(definition, 0x2F8, out.trigger_address) && ReadAt(definition, 0x300, out.primary_effect_address) &&
      ReadAt(definition, 0x308, out.recursive_definition_address) && ReadAt(definition, 0x310, out.alternate_effect_address);
  return table_read && out.row_copy_complete;
}

bool InitializeRuntime(const ActualArmyLateEventJournalBindingsV1 &bindings,
                       ActualArmyLateEventOriginalV1 original) noexcept {
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
void Fail(ActualArmyLateEventJournalDetourStateV1 &state,
          ActualArmyLateEventJournalInstallFailureV1 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ActualArmyLateEventJournalDetourStateV1 &state,
                const std::array<std::uint8_t, kActualArmyLateEventPatchBytes12004> &expected,
                const std::array<std::uint8_t, kActualArmyLateEventPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, actual_army_late_event_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_army_late_event_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_army_late_event_install_protection
                     : actual_army_late_event_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, actual_army_late_event_install_rollback);
  return false;
}

std::array<std::uint8_t, kActualArmyLateEventPatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kActualArmyLateEventPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarActualArmyLateEventHook12004V1));
  return patch;
}

} // namespace

ActualArmyLateEventJournalBindingsV1 BindActualArmyLateEventJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ActualArmyLateEventJournalBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = image_base;
  return result;
}

bool InitializeActualArmyLateEventJournalFixture12004(
    const ActualArmyLateEventJournalBindingsV1 &bindings,
    ActualArmyLateEventOriginalV1 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  return InitializeRuntime(bindings, original);
}

bool InstallActualArmyLateEventJournal12004(
    ActualArmyLateEventJournalDetourStateV1 &state,
    const ActualArmyLateEventJournalInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(actual_army_late_event_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_army_late_event_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_army_late_event_install_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  ActualArmyLateEventJournalDetourStateV1 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_army_late_event_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kActualArmyLateEventRva12004;
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
    Fail(state, actual_army_late_event_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kActualArmyLateEventPatchBytes12004 +
      kActualArmyLateEventAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_army_late_event_install_allocation);
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
      reinterpret_cast<ActualArmyLateEventOriginalV1>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch())) {
    if (!executable) Fail(state, actual_army_late_event_install_protection);
    else if (!flushed) Fail(state, actual_army_late_event_install_flush);
    if ((state.failure_flags.load(std::memory_order_acquire) &
         actual_army_late_event_install_rollback) != 0) {
      state.original = kCallbackPrologue;
      state.installed.store(1, std::memory_order_release);
      return false; // Keep trampoline/forwarding intact for explicit recovery.
    }
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

bool UninstallActualArmyLateEventJournal12004(
    ActualArmyLateEventJournalDetourStateV1 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, actual_army_late_event_install_quiescence);
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
  else Fail(state, actual_army_late_event_install_allocation);
  return freed;
}

std::optional<game::ArmyActualLateEventObservationsV1>
ReadActualArmyLateEventObservations12004(
    std::int32_t native_carmy_id) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  try {
    game::ArmyActualLateEventObservationsV1 result{};
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
      if (slot.sequence == sequence && slot.event.native_carmy_id == native_carmy_id)
        result.events.push_back(slot.event);
    }
    return result;
  } catch (...) {
    return std::nullopt;
  }
}

namespace {
void Observe(std::uint64_t caller_return_rva, void *manager, const void *definition,
             void *scope, void *extra, void *effect_callback, void *event_callback) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return;
  const auto source = Classify(caller_return_rva);
  if (!source) { original(manager, definition, scope, extra, effect_callback, event_callback); return; }
  Event event{};
  event.caller_return_rva = caller_return_rva;
  event.source = *source;
  event.definition_table_offset = static_cast<std::uint32_t>(DefinitionSlot(*source));
  event.effect_callback_address = reinterpret_cast<std::uintptr_t>(effect_callback);
  event.event_callback_address = reinterpret_cast<std::uintptr_t>(event_callback);
  if (!CaptureScope(scope, event.before)) event.capture_failure_flags |= 1;
  const bool identity = event.before.root_copy_ready && event.before.root_kind_raw_u16 == 27 &&
      event.before.root_payload_raw_u64 && *event.before.root_payload_raw_u64 <= UINT32_MAX &&
      static_cast<std::uint32_t>(*event.before.root_payload_raw_u64) != UINT32_MAX;
  if (identity) event.native_carmy_id = static_cast<std::int32_t>(*event.before.root_payload_raw_u64);
  if (*source == game::ArmyLateEventSourceV1::flag21)
    event.before_roles = CaptureFlag21Roles(event.before);
  if (!CaptureDefinition(manager, definition, *source, event.definition)) event.capture_failure_flags |= 2;
  // Forward the genuine six-argument call exactly once, including stack5/6.
  // No capture fault boundary encloses native effects and no query invokes it.
  original(manager, definition, scope, extra, effect_callback, event_callback);
  event.original_returned = true;
  if (!CaptureScope(scope, event.after)) event.capture_failure_flags |= 4;
  event.same_root_after = identity && event.after.root_copy_ready &&
      event.before.root_kind_raw_u16 == event.after.root_kind_raw_u16 &&
      event.before.root_payload_raw_u64 == event.after.root_payload_raw_u64;
  if (*source == game::ArmyLateEventSourceV1::flag21)
    event.after_roles = CaptureFlag21Roles(event.after);
  if (!event.same_root_after) event.capture_failure_flags |= 8;
  Publish(event, identity);
}
} // namespace
void InvokeActualArmyLateEventJournalFixture12004(
    std::uint64_t caller_return_rva, void *manager, const void *definition,
    void *scope, void *extra, void *effect_callback, void *event_callback) noexcept {
  Observe(caller_return_rva, manager, definition, scope, extra, effect_callback, event_callback);
}
extern "C" void __fastcall XarActualArmyLateEventHook12004V1(
    void *manager, const void *definition, void *scope, void *extra,
    void *effect_callback, void *event_callback) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva = g_bindings.image_base && caller >= g_bindings.image_base
      ? caller - g_bindings.image_base : 0;
  Observe(rva, manager, definition, scope, extra, effect_callback, event_callback);
}
} // namespace xar::ck3_12004
