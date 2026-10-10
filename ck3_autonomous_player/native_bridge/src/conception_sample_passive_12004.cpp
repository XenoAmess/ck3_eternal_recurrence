#include "xar_bridge/conception_sample_passive_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"

#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#pragma intrinsic(_ReturnAddress)
#endif

namespace xar::ck3_12004 {
namespace {
// Held241B source: E46530/35/3A are three whole five-byte home-slot MOVs.
// Resume E4653F before the fourth home-slot save; no relocation is required.
constexpr std::array<std::uint8_t, kConceptionSamplePatchBytes12004>
    kCallbackPrologue{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,
                      0x24,0x10,0x48,0x89,0x74,0x24,0x18};
constexpr std::size_t kAbsoluteJumpBytes = 14;
constexpr std::size_t kEntryThunkBytes = 17;
using Event = ConceptionSampleObservation12004;
struct JournalSlot { std::uint64_t sequence = 0; Event event{}; };
std::array<JournalSlot, kConceptionSampleJournalCapacity12004> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0;
ConceptionSampleBindings12004 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<ConceptionSampleOriginal12004> g_original{nullptr};
std::atomic<ConceptionSampleDetourState12004 *> g_active_state{nullptr};

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
    if (g_bindings.read_memory)
      return g_bindings.read_memory(g_bindings.read_context, address, output, size);
    std::memcpy(output, address, size);
    return true;
  });
}
bool SourceIdentity(std::uintptr_t character, std::uint32_t expected) noexcept {
  std::uint32_t full_id = UINT32_MAX, magic = 0;
  return character && expected != UINT32_MAX &&
      ReadMemory(reinterpret_cast<const void *>(character + 0x18), &full_id, sizeof(full_id)) &&
      ReadMemory(reinterpret_cast<const void *>(character + 0x1C), &magic, sizeof(magic)) &&
      magic == 0x43686172 && full_id == expected;
}
bool ReadParent(ConceptionSampleParentScope12004 &scope) noexcept {
  return g_bindings.read_parent && FaultBoundary([&]() noexcept {
    return g_bindings.read_parent(g_bindings.parent_context, scope);
  });
}
bool ValidParent(const ConceptionSampleParentScope12004 &scope,
                 std::uintptr_t receiver) noexcept {
  return scope.active && scope.parent_scope_id && scope.clock_identity &&
      scope.process_clock == scope.parent_scope_id &&
      scope.thread_id == GetCurrentThreadId() && receiver &&
      scope.sample_receiver == receiver &&
      SourceIdentity(scope.first_character, scope.first_full_id) &&
      SourceIdentity(scope.second_character, scope.second_full_id);
}
bool SameParent(const ConceptionSampleParentScope12004 &a,
                const ConceptionSampleParentScope12004 &b) noexcept {
  return b.active && a.parent_scope_id == b.parent_scope_id &&
      a.clock_identity == b.clock_identity && a.process_clock == b.process_clock &&
      a.thread_id == b.thread_id && a.first_character == b.first_character &&
      a.second_character == b.second_character && a.first_full_id == b.first_full_id &&
      a.second_full_id == b.second_full_id && a.sample_receiver == b.sample_receiver;
}
PersonInstalledTransferEvent12004 NextEvent() noexcept {
  if (g_bindings.next_event)
    return g_bindings.next_event(g_bindings.event_context);
  return NextPersonNaturalLineageEvent12004();
}
bool ValidCoordinate(const PersonInstalledTransferEvent12004 &event,
                     const ConceptionSampleParentScope12004 &parent) noexcept {
  return event.clock_identity == parent.clock_identity && event.thread_id &&
      *event.thread_id == parent.thread_id && event.sequence > parent.process_clock;
}
std::optional<std::array<std::uint32_t,2>> ReadState(void *receiver) noexcept {
  std::array<std::uint32_t,2> result{};
  if (!ReadMemory(receiver, result.data(), sizeof(result))) return std::nullopt;
  return result;
}
bool InitializeRuntime(const ConceptionSampleBindings12004 &bindings,
                       ConceptionSampleOriginal12004 original,
                       bool reset_journal = false) noexcept {
  if (!bindings.enabled || !bindings.read_parent || original == nullptr) return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_journal_mutex);
    g_bindings = bindings;
    if (reset_journal) {
      g_latest_sequence = 0;
      for (auto &slot : g_slots) slot = {};
    }
  }
  g_original.store(original, std::memory_order_release);
  g_available.store(true, std::memory_order_release);
  return true;
}
void Publish(Event &event) noexcept {
  {
    const std::lock_guard lock(g_journal_mutex);
    event.journal_sequence = ++g_latest_sequence;
    auto &slot = g_slots[(event.journal_sequence - 1) % g_slots.size()];
    slot.event = event;
    slot.sequence = event.journal_sequence;
  }
  // Delivery occurs after releasing the journal lock and after original return.
  if (g_bindings.child_return)
    (void)FaultBoundary([&]() noexcept {
      g_bindings.child_return(g_bindings.child_return_context, event);
      return true;
    });
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
void Fail(ConceptionSampleDetourState12004 &state,
          ConceptionSampleInstallFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ConceptionSampleDetourState12004 &state,
                const std::array<std::uint8_t, kConceptionSamplePatchBytes12004> &expected,
                const std::array<std::uint8_t, kConceptionSamplePatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, conception_sample_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, conception_sample_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? conception_sample_install_protection
                     : conception_sample_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, conception_sample_install_rollback);
  return false;
}

std::array<std::uint8_t, kConceptionSamplePatchBytes12004> HookPatch(
    const ConceptionSampleDetourState12004 &state) noexcept {
  std::array<std::uint8_t, kConceptionSamplePatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(state.entry_thunk));
  return patch;
}

} // namespace

ConceptionSampleBindings12004 BindConceptionSampleImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ConceptionSampleBindings12004 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = image_base;
  return result;
}

bool InitializeConceptionSampleFixture12004(
    const ConceptionSampleBindings12004 &bindings,
    ConceptionSampleOriginal12004 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  return InitializeRuntime(bindings, original, true);
}

bool InstallConceptionSamplePassive12004(
    ConceptionSampleDetourState12004 &state,
    const ConceptionSampleInstallEnvironment12004 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(conception_sample_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0 || !environment.bindings.read_parent) {
    Fail(state, conception_sample_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, conception_sample_install_quiescence);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  ConceptionSampleDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, conception_sample_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kConceptionSampleRva12004;
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
    Fail(state, conception_sample_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kConceptionSamplePatchBytes12004 +
      kAbsoluteJumpBytes;
  constexpr auto allocation_bytes = trampoline_bytes + kEntryThunkBytes;
  state.trampoline = allocate(state.memory_context, allocation_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, conception_sample_install_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *bytes = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(bytes, kCallbackPrologue.data(), kCallbackPrologue.size());
  WriteAbsoluteJump(bytes + kCallbackPrologue.size(),
                    state.callback_target + kCallbackPrologue.size());
  state.entry_thunk = bytes + trampoline_bytes;
  auto *entry = static_cast<std::uint8_t *>(state.entry_thunk);
  // Incoming R9 is overwritten at E4655B before any read in the held body.
  // RBX is saved at E46530 and restored at E465CF. This jump-only thunk copies
  // the genuine caller comparison threshold without changing arguments or RSP.
  constexpr std::array<std::uint8_t,3> copy_rbx_to_r9{0x49,0x89,0xD9};
  std::memcpy(entry, copy_rbx_to_r9.data(), copy_rbx_to_r9.size());
  WriteAbsoluteJump(entry + copy_rbx_to_r9.size(),
                    reinterpret_cast<std::uintptr_t>(&XarConceptionSampleHook12004));
  DWORD old = 0;
  const bool executable = state.virtual_protect(state.memory_context,
      state.trampoline, allocation_bytes, PAGE_EXECUTE_READ, old);
  const bool flushed = executable && state.flush_instruction_cache(
      state.memory_context, state.trampoline, allocation_bytes);
  const bool initialized = flushed && InitializeRuntime(environment.bindings,
      reinterpret_cast<ConceptionSampleOriginal12004>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch(state))) {
    if (!executable) Fail(state, conception_sample_install_protection);
    else if (!flushed) Fail(state, conception_sample_install_flush);
    if ((state.failure_flags.load(std::memory_order_acquire) &
         conception_sample_install_rollback) != 0) {
      state.original = kCallbackPrologue;
      state.installed.store(1, std::memory_order_release);
      return false; // Keep trampoline/forwarding intact for explicit recovery.
    }
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    (void)state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE);
    state.trampoline = nullptr;
    state.entry_thunk = nullptr;
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.original = kCallbackPrologue;
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallConceptionSamplePassive12004(
    ConceptionSampleDetourState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0) return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, conception_sample_install_quiescence);
    return false;
  }
  if (!WritePatch(state, HookPatch(state), state.original)) return false;
  state.installed.store(0, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  g_active_state.store(nullptr, std::memory_order_release);
  const bool freed = state.virtual_free(state.memory_context, state.trampoline,
                                         0, MEM_RELEASE);
  if (freed) { state.trampoline = nullptr; state.entry_thunk = nullptr; }
  else Fail(state, conception_sample_install_allocation);
  return freed;
}

std::optional<ConceptionSampleObservations12004>
ReadConceptionSampleObservations12004(std::uintptr_t clock_identity,
                                    std::uint64_t parent_scope_id) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  if ((clock_identity == 0) != (parent_scope_id == 0)) return std::nullopt;
  try {
    ConceptionSampleObservations12004 result{};
    const auto *active = g_active_state.load(std::memory_order_acquire);
    result.observer_installed = active && active->installed.load(std::memory_order_acquire);
    const std::lock_guard lock(g_journal_mutex);
    result.latest_sequence = g_latest_sequence;
    result.oldest_available_sequence = g_latest_sequence == 0 ? 0 :
        g_latest_sequence <= g_slots.size() ? 1 : g_latest_sequence - g_slots.size() + 1;
    result.overwritten_events = g_latest_sequence > g_slots.size()
        ? g_latest_sequence - g_slots.size() : 0;
    for (auto sequence = result.oldest_available_sequence;
         sequence && sequence <= g_latest_sequence; ++sequence) {
      const auto &slot = g_slots[(sequence - 1) % g_slots.size()];
      if (slot.sequence == sequence && (!clock_identity ||
          (slot.event.parent.clock_identity == clock_identity &&
           slot.event.parent.parent_scope_id == parent_scope_id)))
        result.events.push_back(slot.event);
    }
    return result;
  } catch (...) { return std::nullopt; }
}

namespace {
std::int64_t Observe(std::uintptr_t caller_return_rva, void *receiver,
                     std::int64_t lower, std::int64_t upper,
                     std::optional<std::int64_t> caller_rbx) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (!original) return 0; // No installed hook can exist without its forwarding target.
  ConceptionSampleParentScope12004 parent{};
  const auto raw_receiver = reinterpret_cast<std::uintptr_t>(receiver);
  if (caller_return_rva != kConceptionSampleReturnRva12004 || lower != 0 ||
      upper != 10000000 || !ReadParent(parent) || !ValidParent(parent, raw_receiver))
    return original(receiver, lower, upper);
  Event event{};
  event.parent = parent;
  event.caller_return_rva = caller_return_rva;
  event.receiver = raw_receiver;
  event.original_lower = lower;
  event.original_upper = upper;
  event.threshold_at_sample = caller_rbx;
  event.state_before = ReadState(receiver);
  if (!event.state_before) event.capture_failure_flags |= conception_sample_capture_state_before;
  event.before_event = NextEvent();
  // Always forward the genuine three arguments once. No capture fault boundary
  // encloses the original helper; its state mutation and signed RAX are retained.
  const std::int64_t result = original(receiver, lower, upper);
  event.returned_rax = result;
  event.original_returned = true;
  event.returned_event = NextEvent();
  event.state_after = ReadState(receiver);
  if (!event.state_after) event.capture_failure_flags |= conception_sample_capture_state_after;
  if (event.state_before && event.state_after) {
    event.state_transition_matches_source =
        (*event.state_after)[0] == static_cast<std::uint32_t>((*event.state_before)[0] + 2U) &&
        (*event.state_after)[1] == (*event.state_before)[1];
    if (!*event.state_transition_matches_source)
      event.capture_failure_flags |= conception_sample_capture_state_transition;
  }
  ConceptionSampleParentScope12004 after{};
  event.parent_extent_and_generation_unchanged = ReadParent(after) &&
      SameParent(parent, after) && ValidParent(after, raw_receiver);
  if (!event.parent_extent_and_generation_unchanged)
    event.capture_failure_flags |= conception_sample_capture_parent_changed;
  event.event_clock_and_thread_match = ValidCoordinate(event.before_event, parent) &&
      ValidCoordinate(event.returned_event, parent) &&
      event.returned_event.sequence > event.before_event.sequence;
  if (!event.event_clock_and_thread_match)
    event.capture_failure_flags |= conception_sample_capture_event_coordinate;
  event.sample_within_source_range = result >= 0 && result <= 10000000;
  if (!event.sample_within_source_range)
    event.capture_failure_flags |= conception_sample_capture_return_domain;
  event.causal_sample_ready = event.parent_extent_and_generation_unchanged &&
      event.event_clock_and_thread_match && event.state_before && event.state_after &&
      event.state_transition_matches_source && *event.state_transition_matches_source &&
      event.sample_within_source_range;
  event.threshold_capture_ready = event.parent_extent_and_generation_unchanged &&
      event.event_clock_and_thread_match && caller_rbx && *caller_rbx > 0;
  if (!event.threshold_capture_ready)
    event.capture_failure_flags |= conception_sample_capture_threshold;
  if (event.causal_sample_ready && event.threshold_capture_ready)
    event.comparison_at_sample_passed = result < *caller_rbx;
  Publish(event);
  return result;
}
} // namespace

std::int64_t InvokeConceptionSampleFixture12004(
    std::uintptr_t caller_return_rva, void *receiver,
    std::int64_t lower, std::int64_t upper,
    std::optional<std::int64_t> caller_rbx) noexcept {
  return Observe(caller_return_rva, receiver, lower, upper, caller_rbx);
}
extern "C" std::int64_t __fastcall XarConceptionSampleHook12004(
    void *receiver, std::int64_t lower, std::int64_t upper,
    std::int64_t caller_rbx) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva = g_bindings.image_base && caller >= g_bindings.image_base
      ? caller - g_bindings.image_base : 0;
  return Observe(rva, receiver, lower, upper, caller_rbx);
}
} // namespace xar::ck3_12004
