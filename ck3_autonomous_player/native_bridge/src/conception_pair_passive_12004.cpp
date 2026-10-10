#include "xar_bridge/conception_pair_passive_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"

#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {
// Full instructions 5/1/1/1/4/7B; the indirect jump preserves the magic CMP
// flags subsequently used by original JNE2929B5F. Resume at2929B53.
constexpr std::array<std::uint8_t, kConceptionPairPassivePatchBytes12004>
    kCallbackPrologue{0x48,0x89,0x5C,0x24,0x18,0x55,0x56,0x57,0x48,0x83,
                      0xEC,0x30,0x81,0x79,0x1C,0x72,0x61,0x68,0x43};
using Event = ConceptionPairPassiveEvent12004;
struct JournalSlot { std::uint64_t sequence = 0; Event event{}; };
std::array<JournalSlot, kConceptionPairPassiveJournalCapacity12004> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0, g_unattributed_failures = 0;
std::uintptr_t g_clock_identity = 0;
ConceptionPairPassiveBindingsV1 g_bindings{};
std::atomic<bool> g_available{false}, g_fixture_mode{false};
std::atomic<ConceptionPairPassiveOriginalV1> g_original{nullptr};
std::atomic<ConceptionPairPassiveDetourStateV1 *> g_active_state{nullptr};
struct ActiveParent { ConceptionSampleParentScope12004 scope{}; Event *event = nullptr; };
thread_local ActiveParent *g_parent = nullptr;

template <typename Callback> bool FaultBoundary(Callback callback) noexcept {
#if defined(_MSC_VER)
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  return callback();
#endif
}
template <typename T> std::optional<T> Copy(std::uintptr_t address) noexcept {
  T value{};
  if (address == 0 || !g_bindings.read_memory || !FaultBoundary([&]() noexcept {
        return g_bindings.read_memory(g_bindings.read_context,
            reinterpret_cast<const void *>(address), &value, sizeof(value));
      })) return std::nullopt;
  return value;
}
bool Qualified(const ConceptionPairCharacterFacts12004 &facts) noexcept {
  return facts.full_id && *facts.full_id != UINT32_MAX && facts.magic &&
      *facts.magic == 0x43686172U;
}
ConceptionPairCharacterFacts12004 Character(std::uintptr_t address) noexcept {
  ConceptionPairCharacterFacts12004 result;
  result.character = address;
  if (address == 0) return result;
  result.magic = Copy<std::uint32_t>(address + 0x1C);
  result.full_id = Copy<std::uint32_t>(address + 0x18);
  result.native_sex_1a1 = Copy<std::uint8_t>(address + 0x1A1);
  result.extended_pointer = Copy<std::uintptr_t>(address + 0x1B0);
  if (result.extended_pointer && *result.extended_pointer != 0) {
    const auto extended = *result.extended_pointer;
    result.extended_288_raw = Copy<std::uint64_t>(extended + 0x288);
    result.pending_3e8_raw = Copy<std::uint8_t>(extended + 0x3E8);
    result.pending_3f0_raw = Copy<std::uintptr_t>(extended + 0x3F0);
    if (Qualified(result) && result.extended_288_raw)
      result.extended_288_blocks = *result.extended_288_raw != 0;
  } else if (Qualified(result) && result.extended_pointer) {
    result.extended_288_blocks = false; // Actual native null-extended skip.
  }
  return result;
}
ConceptionPairSourceCopies12004 SourceCopies() noexcept {
  ConceptionPairSourceCopies12004 result;
  result.scalar_5c69ec8_raw = Copy<std::int64_t>(g_bindings.image_base + 0x5C69EC8);
  result.lower_5c69f00_raw = Copy<std::int64_t>(g_bindings.image_base + 0x5C69F00);
  result.upper_5c69f10_raw = Copy<std::int64_t>(g_bindings.image_base + 0x5C69F10);
  return result; // Raw copies, never marked actual consumed MOV values.
}
PersonInstalledTransferEvent12004 Clock() noexcept {
  return g_bindings.next_event ? g_bindings.next_event(g_bindings.event_context)
                               : NextPersonNaturalLineageEvent12004();
}
bool InitializeRuntime(const ConceptionPairPassiveBindingsV1 &bindings,
                       ConceptionPairPassiveOriginalV1 original) noexcept {
  if (!bindings.enabled || !bindings.read_memory || original == nullptr) return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_journal_mutex);
    g_bindings = bindings;
    g_latest_sequence = 0;
    g_unattributed_failures = 0;
    g_clock_identity = 0;
    g_fixture_mode.store(false, std::memory_order_release);
    for (auto &slot : g_slots) slot = {};
  }
  g_original.store(original, std::memory_order_release);
  g_available.store(true, std::memory_order_release);
  return true;
}
void Publish(Event &event) noexcept {
  const std::lock_guard lock(g_journal_mutex);
  if (!Qualified(event.first_before) || !Qualified(event.second_before))
    ++g_unattributed_failures;
  event.journal_sequence = ++g_latest_sequence;
  g_clock_identity = event.before_event.clock_identity;
  auto &slot = g_slots[(event.journal_sequence - 1) % g_slots.size()];
  slot.event = event;
  slot.sequence = event.journal_sequence;
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
void Fail(ConceptionPairPassiveDetourStateV1 &state,
          ConceptionPairPassiveInstallFailureV1 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ConceptionPairPassiveDetourStateV1 &state,
                const std::array<std::uint8_t, kConceptionPairPassivePatchBytes12004> &expected,
                const std::array<std::uint8_t, kConceptionPairPassivePatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, conception_pair_passive_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, conception_pair_passive_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? conception_pair_passive_install_protection
                     : conception_pair_passive_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, conception_pair_passive_install_rollback);
  return false;
}

std::array<std::uint8_t, kConceptionPairPassivePatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kConceptionPairPassivePatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarConceptionPairPassiveHook12004V1));
  return patch;
}


} // namespace

ConceptionPairPassiveBindingsV1 BindConceptionPairPassiveImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    ConceptionPairPassiveReadMemoryV1 read_memory, void *read_context) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256 || !read_memory)
    return {};
  return {true, image_base, read_context, read_memory};
}
bool InitializeConceptionPairPassiveFixture12004(
    const ConceptionPairPassiveBindingsV1 &bindings,
    ConceptionPairPassiveOriginalV1 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  const bool ready = InitializeRuntime(bindings, original);
  if (ready) g_fixture_mode.store(true, std::memory_order_release);
  return ready;
}
bool InstallConceptionPairPassiveObserver12004(
    ConceptionPairPassiveDetourStateV1 &state,
    const ConceptionPairPassiveInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept {
  if (state.installed.load(std::memory_order_acquire) != 0) {
    // A retained failed rollback cannot become a successful installation by
    // resetting flags on a second call. Startup installation owns this state.
    return state.failure_flags.load(std::memory_order_acquire) == 0 &&
        g_active_state.load(std::memory_order_acquire) == &state &&
        environment.primary_thread_suspended_proven && environment.bindings.enabled &&
        environment.bindings.image_base == g_bindings.image_base &&
        executable_sha256 == kExecutableSha256;
  }
  state.failure_flags.store(conception_pair_passive_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, conception_pair_passive_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, conception_pair_passive_install_quiescence);
    return false;
  }
  ConceptionPairPassiveDetourStateV1 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, conception_pair_passive_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kConceptionPairPassiveRva12004;
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
    Fail(state, conception_pair_passive_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kConceptionPairPassivePatchBytes12004 +
      kConceptionPairPassiveAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, conception_pair_passive_install_allocation);
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
      reinterpret_cast<ConceptionPairPassiveOriginalV1>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch())) {
    if (!executable) Fail(state, conception_pair_passive_install_protection);
    else if (!flushed) Fail(state, conception_pair_passive_install_flush);
    if ((state.failure_flags.load(std::memory_order_acquire) &
         conception_pair_passive_install_rollback) != 0) {
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


bool ReadConceptionPairParentScope12004(
    void *, ConceptionSampleParentScope12004 &output) noexcept {
  output = {};
  if (!g_parent || !g_parent->scope.active ||
      g_parent->scope.thread_id != GetCurrentThreadId()) return false;
  output = g_parent->scope;
  return true;
}
namespace {
bool SameParent(const ConceptionSampleParentScope12004 &parent) noexcept {
  return g_parent && g_parent->scope.active &&
      parent.active && parent.clock_identity == g_parent->scope.clock_identity &&
      parent.parent_scope_id == g_parent->scope.parent_scope_id &&
      parent.process_clock == g_parent->scope.process_clock &&
      parent.thread_id == GetCurrentThreadId() &&
      parent.thread_id == g_parent->scope.thread_id &&
      parent.first_character == g_parent->scope.first_character &&
      parent.second_character == g_parent->scope.second_character &&
      parent.first_full_id == g_parent->scope.first_full_id &&
      parent.second_full_id == g_parent->scope.second_full_id &&
      parent.sample_receiver == g_parent->scope.sample_receiver;
}
}
bool AttachConceptionPairProviderFacts12004(
    void *, const ConceptionPairProviderObservation12004 &observation) noexcept {
  if (!SameParent(observation.parent) || !g_parent->event) return false;
  if (g_parent->event->provider) {
    ++g_parent->event->duplicate_provider_returns;
    return false;
  }
  g_parent->event->provider = observation;
  return true;
}
void AttachConceptionPairSampleFacts12004(
    void *, const ConceptionSampleObservation12004 &observation) noexcept {
  if (!SameParent(observation.parent) || !g_parent->event) return;
  if (g_parent->event->sample) {
    ++g_parent->event->duplicate_sample_returns;
    return;
  }
  g_parent->event->sample = observation;
}
namespace {
std::uint64_t Observe(std::uintptr_t caller_return_pc, void *first, void *second,
                      void *sample_receiver, std::int64_t modifier) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return 0; // Not reachable for an installed hook.
  Event event;
  event.caller_return_pc = caller_return_pc;
  if (caller_return_pc >= g_bindings.image_base)
    event.caller_return_rva = caller_return_pc - g_bindings.image_base;
  event.process_id = GetCurrentProcessId();
  event.thread_id = GetCurrentThreadId();
  event.before_event = Clock();
  event.first_character = reinterpret_cast<std::uintptr_t>(first);
  event.second_character = reinterpret_cast<std::uintptr_t>(second);
  event.sample_receiver = reinterpret_cast<std::uintptr_t>(sample_receiver);
  event.original_r9_modifier = modifier;
  event.fixture_origin = g_fixture_mode.load(std::memory_order_acquire);
  event.first_before = Character(event.first_character);
  event.second_before = Character(event.second_character);
  event.sample_state_before = Copy<std::array<std::uint32_t, 2>>(event.sample_receiver);
  event.source_before = SourceCopies();
  ActiveParent parent;
  parent.scope = {true, event.before_event.sequence, event.thread_id,
      event.before_event.sequence, event.before_event.clock_identity,
      event.first_character, event.second_character,
      event.first_before.full_id.value_or(UINT32_MAX),
      event.second_before.full_id.value_or(UINT32_MAX), event.sample_receiver};
  parent.event = &event;
  auto *previous_parent = g_parent;
  g_parent = &parent;
  event.original_called_once = true;
  // No fault boundary or catch encloses native execution. Preserve the full
  // RAX returned by exactly this original invocation, not a normalized bool.
  const std::uint64_t returned = original(first, second, sample_receiver, modifier);
  g_parent = previous_parent;
  event.original_returned = true;
  event.original_rax_bits = returned;
  event.original_al = static_cast<std::uint8_t>(returned & 0xFFU);
  event.first_after = Character(event.first_character);
  event.second_after = Character(event.second_character);
  event.sample_state_after = Copy<std::array<std::uint32_t, 2>>(event.sample_receiver);
  event.source_after = SourceCopies();
  event.completed_event = Clock();
  if (Qualified(event.first_before) && Qualified(event.second_before) &&
      Qualified(event.first_after) && Qualified(event.second_after))
    event.generation_unchanged =
        event.first_before.full_id == event.first_after.full_id &&
        event.second_before.full_id == event.second_after.full_id;
  if (event.first_after.pending_3e8_raw && event.first_after.pending_3f0_raw)
    event.first_post_pending_matches_write_pattern =
        *event.first_after.pending_3e8_raw == 1 &&
        *event.first_after.pending_3f0_raw == event.second_character;
  event.event_clock_and_thread_match = event.before_event.clock_identity != 0 &&
      event.before_event.clock_identity == event.completed_event.clock_identity &&
      event.before_event.sequence != 0 &&
      event.completed_event.sequence > event.before_event.sequence &&
      event.before_event.thread_id == event.thread_id &&
      event.completed_event.thread_id == event.thread_id;
  Publish(event);
  return returned;
}
bool PairMatches(const Event &event, std::uint32_t first,
                 std::uint32_t second) noexcept {
  const auto matches = [&](const auto &a, const auto &b) noexcept {
    return Qualified(a) && Qualified(b) &&
        ((*a.full_id == first && *b.full_id == second) ||
         (*a.full_id == second && *b.full_id == first));
  };
  return matches(event.first_before, event.second_before) ||
      matches(event.first_after, event.second_after);
}
}
std::optional<ConceptionPairPassiveJournal12004> ReadConceptionPairPassiveForPair12004(
    std::uint32_t first, std::uint32_t second, std::uint64_t after_sequence) noexcept {
  if (!g_available.load(std::memory_order_acquire) || first == UINT32_MAX ||
      second == UINT32_MAX) return std::nullopt;
  const auto *active = g_active_state.load(std::memory_order_acquire);
  const bool guarded = active && g_bindings.enabled &&
      active->installed.load(std::memory_order_acquire) != 0 &&
      active->failure_flags.load(std::memory_order_acquire) == 0;
  if (!guarded && !g_fixture_mode.load(std::memory_order_acquire)) return std::nullopt;
  try {
    ConceptionPairPassiveJournal12004 result;
    result.image_base = g_bindings.image_base;
    result.observer_installed = guarded;
    result.current_session_guard = guarded;
    const std::lock_guard lock(g_journal_mutex);
    result.clock_identity = g_clock_identity;
    result.latest_sequence = g_latest_sequence;
    result.oldest_available_sequence = g_latest_sequence == 0 ? 0 :
        g_latest_sequence <= g_slots.size() ? 1 : g_latest_sequence - g_slots.size() + 1;
    result.overwritten_events = g_latest_sequence > g_slots.size() ?
        g_latest_sequence - g_slots.size() : 0;
    result.unattributed_identity_events = g_unattributed_failures;
    for (auto sequence = result.oldest_available_sequence;
         sequence != 0 && sequence <= g_latest_sequence; ++sequence) {
      const auto &slot = g_slots[(sequence - 1) % g_slots.size()];
      if (sequence > after_sequence && slot.sequence == sequence &&
          PairMatches(slot.event, first, second)) result.events.push_back(slot.event);
    }
    return result;
  } catch (...) { return std::nullopt; }
}
std::uint64_t InvokeConceptionPairPassiveFixture12004(
    std::uintptr_t caller_return_pc, void *first, void *second,
    void *sample_receiver, std::int64_t modifier) noexcept {
  return Observe(caller_return_pc, first, second, sample_receiver, modifier);
}
extern "C" std::uint64_t __fastcall XarConceptionPairPassiveHook12004V1(
    void *first, void *second, void *sample_receiver, std::int64_t modifier) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  return Observe(caller, first, second, sample_receiver, modifier);
}
} // namespace xar::ck3_12004
