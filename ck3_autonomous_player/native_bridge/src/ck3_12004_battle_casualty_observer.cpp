#include "xar_bridge/ck3_12004_battle_casualty_observer.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <mutex>

namespace xar::ck3_12004 {
namespace {

constexpr std::array<std::uint8_t, kBattleCasualtyApplicationPatchBytes12004>
    kPrologue{0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74,
              0x24, 0x10, 0x57, 0x48, 0x83, 0xEC, 0x20};
using Event = game::ArmyBattleCasualtyObservationV1;
struct Slot { std::uint64_t sequence = 0; Event event{}; };
std::array<Slot, game::kArmyBattleCasualtyJournalCapacityV1> g_slots{};
std::mutex g_mutex;
std::uint64_t g_latest = 0;
BattleCasualtyObserverBindings12004 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<BattleCasualtyOriginal12004> g_original{nullptr};
std::atomic<BattleCasualtyObserverDetourState12004 *> g_active_state{nullptr};

struct ApplicationScope {
  Event event{};
  ApplicationScope *previous = nullptr;
};
thread_local ApplicationScope *g_scope = nullptr;

template <typename Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
bool Read(const void *address, void *output, std::size_t bytes) noexcept {
  if (address == nullptr) return false;
  return FaultBoundary([&]() noexcept {
    if (g_bindings.read_memory != nullptr)
      return g_bindings.read_memory(g_bindings.read_context, address, output, bytes);
    std::memcpy(output, address, bytes);
    return true;
  });
}
template <typename Value>
bool At(const void *object, std::size_t offset, Value &output) noexcept {
  return object != nullptr && Read(static_cast<const std::byte *>(object) + offset,
                                  &output, sizeof(output));
}
template <typename Value>
void OptionalAt(const void *object, std::size_t offset,
                std::optional<Value> &output) noexcept {
  Value value{};
  if (At(object, offset, value)) output = value;
}

// Exactly the two generation-checked source lookups following2634190. When
// the storage is null, native does not demand the reference field at all.
void *ResolveOwner(const void *source, std::size_t reference_offset,
                   void **storage_slot, void **fallback_slot,
                   game::ArmyBattleCasualtyOwnerResolutionV1 &result) noexcept {
  void *storage = nullptr;
  if (!Read(storage_slot, &storage, sizeof(storage))) return nullptr;
  void *object = nullptr;
  bool fallback = true;
  if (storage != nullptr) {
    result.reference_demanded = true;
    std::int32_t reference = 0;
    std::uint32_t capacity = 0;
    if (!At(source, reference_offset, reference) || !At(storage, 0x2C, capacity))
      return nullptr;
    result.requested_full_id = reference;
    const auto index = static_cast<std::uint32_t>(reference) & 0xFFFFFFU;
    if (index < capacity) {
      void *rows = nullptr;
      if (!At(storage, 0x20, rows) || rows == nullptr ||
          !At(rows, static_cast<std::size_t>(index) * 0x10 + 0x08, object))
        return nullptr;
      if (object != nullptr) {
        std::int32_t full_id = 0;
        if (!At(object, 0x10, full_id)) return nullptr;
        fallback = full_id != reference;
      }
    }
  }
  result.used_fallback = fallback;
  if (fallback && !Read(fallback_slot, &object, sizeof(object))) return nullptr;
  if (object == nullptr) return nullptr;
  OptionalAt(object, 0x10, result.resolved_full_id);
  result.read_complete = result.resolved_full_id.has_value();
  return result.read_complete ? object : nullptr;
}

bool Initialize(const BattleCasualtyObserverBindings12004 &bindings,
                BattleCasualtyOriginal12004 original) noexcept {
  if (!bindings.enabled || original == nullptr) return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_mutex);
    g_bindings = bindings;
    g_latest = 0;
    for (auto &slot : g_slots) slot = {};
  }
  g_original.store(original, std::memory_order_release);
  SetActualLossWriterCompletionObserver12004(&ObserveNestedBattleCasualtyWriter12004);
  g_available.store(true, std::memory_order_release);
  return true;
}

void Publish(Event &event) noexcept {
  const std::lock_guard lock(g_mutex);
  event.sequence = ++g_latest;
  auto &slot = g_slots[(event.sequence - 1) % g_slots.size()];
  slot.event = event;
  slot.sequence = event.sequence;
}
void Jump(std::uint8_t *destination, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF, 0x25, 0, 0, 0, 0};
  std::memcpy(destination, prefix.data(), prefix.size());
  std::memcpy(destination + prefix.size(), &target, sizeof(target));
}
void *Allocate(void *, std::size_t bytes, DWORD type, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, bytes, type, protection);
}
bool Free(void *, void *address, std::size_t bytes, DWORD type) noexcept {
  return VirtualFree(address, bytes, type) != FALSE;
}
bool Protect(void *, void *address, std::size_t bytes, DWORD protection,
             DWORD &old) noexcept {
  return VirtualProtect(address, bytes, protection, &old) != FALSE;
}
bool Flush(void *, const void *address, std::size_t bytes) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, bytes) != FALSE;
}
void Fail(BattleCasualtyObserverDetourState12004 &state,
          std::uint32_t value) noexcept {
  state.failure_flags.fetch_or(value, std::memory_order_relaxed);
}
std::array<std::uint8_t, kBattleCasualtyApplicationPatchBytes12004>
HookPatch() noexcept {
  std::array<std::uint8_t, kBattleCasualtyApplicationPatchBytes12004> result{};
  result.fill(0x90);
  Jump(result.data(), reinterpret_cast<std::uintptr_t>(
                          &XarBattleCasualtyApplicationHook12004));
  return result;
}
bool Patch(BattleCasualtyObserverDetourState12004 &state,
           const std::array<std::uint8_t, kBattleCasualtyApplicationPatchBytes12004> &expected,
           const std::array<std::uint8_t, kBattleCasualtyApplicationPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.target);
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
  DWORD rollback = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored) Fail(state, actual_loss_install_rollback);
  return false;
}

} // namespace

BattleCasualtyObserverBindings12004 BindBattleCasualtyObserverImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  BattleCasualtyObserverBindings12004 result{};
  if (base == 0 || sha != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = base;
  result.game_state_slot = reinterpret_cast<void **>(base + kGameStateSlotRva);
  result.army_storage_slot = reinterpret_cast<void **>(base + 0x5D1DE48);
  result.army_fallback_slot = reinterpret_cast<void **>(base + 0x5D1DE50);
  result.unit_storage_slot = reinterpret_cast<void **>(base + 0x5D1E380);
  result.unit_fallback_slot = reinterpret_cast<void **>(base + 0x5D1E378);
  return result;
}

bool InitializeBattleCasualtyObserverFixture12004(
    const BattleCasualtyObserverBindings12004 &bindings,
    BattleCasualtyOriginal12004 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  return Initialize(bindings, original);
}

void ObserveNestedBattleCasualtyWriter12004(
    void *actual_regiment,
    const game::ArmyActualLossWriterObservationV1 &writer) noexcept {
  if (g_scope == nullptr) return;
  auto &event = g_scope->event;
  ++event.nested_writer_event_count;
  if (event.nested_writer_event_count != 1) {
    event.entry_writer_association_proven = false;
    event.physical_capture_complete = false;
    event.actual_physical_soldier_debit.reset();
    return;
  }
  if (writer.sequence != 0) event.writer_sequence = writer.sequence;
  if (writer.army_regiment_id != -1)
    event.writer_army_regiment_id = writer.army_regiment_id;
  event.writer_request_raw = writer.request_raw;
  event.entry_writer_association_proven = event.entry_army_regiment_id &&
      event.writer_army_regiment_id && event.writer_sequence &&
      *event.entry_army_regiment_id == *event.writer_army_regiment_id &&
      writer.request_raw == event.hard_request_raw;
  if (event.entry_writer_association_proven) {
    event.physical_capture_complete = writer.physical_capture_complete;
    event.actual_physical_soldier_debit = writer.actual_physical_soldier_debit;
  }
  // At this exact return point native next resolves these same owner operands.
  auto *army = ResolveOwner(actual_regiment, 0x140,
      g_bindings.army_storage_slot, g_bindings.army_fallback_slot, event.owner_army);
  auto *unit = ResolveOwner(army, 0x124, g_bindings.unit_storage_slot,
      g_bindings.unit_fallback_slot, event.owner_unit);
  OptionalAt(unit, 0x174, event.owner_character_id);
}

extern "C" void *__fastcall XarBattleCasualtyApplicationHook12004(
    void *side, std::int64_t soft_raw, std::int64_t hard_raw, void *entry) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return nullptr;
  ApplicationScope scope{};
  auto &event = scope.event;
  event.entry_identity = reinterpret_cast<std::uintptr_t>(entry);
  event.soft_request_raw = soft_raw;
  event.hard_request_raw = hard_raw;
  OptionalAt(entry, 0x08, event.entry_army_regiment_id);
  OptionalAt(entry, 0x18, event.before_fighting_raw);
  OptionalAt(entry, 0x20, event.before_soft_raw);
  void *game_state = nullptr;
  if (Read(g_bindings.game_state_slot, &game_state, sizeof(game_state)))
    OptionalAt(game_state, 0x08, event.observed_date_raw);
  scope.previous = g_scope;
  g_scope = &scope;
  // Preserve this actual application and its RAX; no query calls the writer.
  void *returned = original(side, soft_raw, hard_raw, entry);
  g_scope = scope.previous;
  std::int32_t after_id = 0;
  event.same_entry_after = event.entry_army_regiment_id &&
      At(entry, 0x08, after_id) && after_id == *event.entry_army_regiment_id;
  OptionalAt(entry, 0x18, event.after_fighting_raw);
  OptionalAt(entry, 0x20, event.after_soft_raw);
  event.original_return_identity = reinterpret_cast<std::uintptr_t>(returned);
  OptionalAt(returned, 0x10, event.owner_hard_ledger_after_raw);
  Publish(event);
  return returned;
}

std::optional<game::ArmyBattleCasualtyObservationsV1>
ReadBattleCasualtyObservations12004(
    std::span<const std::int32_t> current_full_regiment_ids) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  try {
    game::ArmyBattleCasualtyObservationsV1 result{};
    const auto *active = g_active_state.load(std::memory_order_acquire);
    result.observer_installed = active != nullptr &&
        active->installed.load(std::memory_order_acquire) != 0;
    const std::lock_guard lock(g_mutex);
    result.latest_sequence = g_latest;
    result.oldest_available_sequence = g_latest == 0 ? 0
        : g_latest <= g_slots.size() ? 1 : g_latest - g_slots.size() + 1;
    result.overwritten_events = g_latest > g_slots.size()
        ? g_latest - g_slots.size() : 0;
    for (auto sequence = result.oldest_available_sequence;
         sequence != 0 && sequence <= g_latest; ++sequence) {
      const auto &slot = g_slots[(sequence - 1) % g_slots.size()];
      if (slot.sequence != sequence || !slot.event.entry_army_regiment_id) continue;
      if (std::find(current_full_regiment_ids.begin(), current_full_regiment_ids.end(),
                    *slot.event.entry_army_regiment_id) != current_full_regiment_ids.end())
        result.events.push_back(slot.event);
    }
    return result;
  } catch (...) { return std::nullopt; }
}

bool InstallBattleCasualtyObserver12004(
    BattleCasualtyObserverDetourState12004 &state,
    const BattleCasualtyObserverInstallEnvironment12004 &environment,
    std::string_view sha) noexcept {
  state.failure_flags.store(actual_loss_install_none, std::memory_order_relaxed);
  if (sha != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_loss_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  BattleCasualtyObserverDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_loss_install_already_installed);
    return false;
  }
  state.target = environment.target_override != 0 ? environment.target_override
      : environment.bindings.image_base + kBattleCasualtyApplicationRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override != nullptr
      ? environment.virtual_free_override : &Free;
  state.virtual_protect = environment.virtual_protect_override != nullptr
      ? environment.virtual_protect_override : &Protect;
  state.flush_instruction_cache = environment.flush_instruction_cache_override != nullptr
      ? environment.flush_instruction_cache_override : &Flush;
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(reinterpret_cast<void *>(state.target),
                           kPrologue.data(), kPrologue.size()) == 0;
      })) {
    Fail(state, actual_loss_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &Allocate;
  constexpr auto bytes = kBattleCasualtyApplicationPatchBytes12004 +
                         kActualLossWriterAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, bytes,
                             MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_loss_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *trampoline = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(trampoline, kPrologue.data(), kPrologue.size());
  Jump(trampoline + kPrologue.size(), state.target + kPrologue.size());
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, bytes);
  const bool initialized = flushed && Initialize(environment.bindings,
      reinterpret_cast<BattleCasualtyOriginal12004>(state.trampoline));
  if (!initialized || !Patch(state, kPrologue, HookPatch())) {
    if (!executable) Fail(state, actual_loss_install_protection);
    else if (!flushed) Fail(state, actual_loss_install_flush);
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    SetActualLossWriterCompletionObserver12004(nullptr);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallBattleCasualtyObserver12004(
    BattleCasualtyObserverDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, actual_loss_install_quiescence);
    return false;
  }
  if (!Patch(state, HookPatch(), kPrologue)) return false;
  state.installed.store(0, std::memory_order_release);
  g_available.store(false, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  SetActualLossWriterCompletionObserver12004(nullptr);
  g_active_state.store(nullptr, std::memory_order_release);
  const bool freed = state.virtual_free(state.memory_context, state.trampoline,
                                       0, MEM_RELEASE);
  if (freed) state.trampoline = nullptr;
  else Fail(state, actual_loss_install_allocation);
  return freed;
}

} // namespace xar::ck3_12004
