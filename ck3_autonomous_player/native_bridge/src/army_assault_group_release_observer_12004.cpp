#include "xar_bridge/army_assault_group_release_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {

// Held actual92B: whole 5+1+4+4 byte prologue, no RIP/relative operand.
// Trampoline resumes9D11FE with the genuine record+10 RCX and native stack.
constexpr std::array<std::uint8_t, kArmyAssaultGroupReleasePatchBytes12004>
    kCallbackPrologue{0x48,0x89,0x5C,0x24,0x08,0x57,0x48,0x83,0xEC,0x20,
                      0x48,0x8B,0x51,0x18};

using Event = game::ArmyAssaultGroupReleaseObservation12004;
struct JournalSlot {
  std::uint64_t sequence = 0;
  Event event{};
};
std::array<JournalSlot, game::kArmyAssaultReleaseJournalCapacity12004> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0;
std::uint64_t g_unattributed_failures = 0;
std::uint64_t g_ignored_noncanonical = 0;
std::atomic<bool> g_fixture_mode{false};
ArmyAssaultGroupReleaseBindings12004 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<ArmyAssaultGroupReleaseOriginal12004> g_original{nullptr};
std::atomic<ArmyAssaultGroupReleaseDetourState12004 *> g_active_state{nullptr};

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

bool ActiveParent(void *, game::ArmyAssaultReleaseParent12004 &out) noexcept {
  return CopyActiveArmyAssaultConsumerParent12004(out);
}
bool EventValid(const ArmyNaturalPhaseEvent12004 &e, DWORD thread) noexcept {
  return e.clock_identity != 0 && e.sequence != 0 && e.thread_id && *e.thread_id == thread;
}
bool ParentValid(const game::ArmyAssaultReleaseParent12004 &p, DWORD thread) noexcept {
  return p.active && p.exact_post_date_parent && p.actual_entry_rva == 0x2A97EB0 &&
      p.caller_return_rva == 0x2A9A8EA && p.manager_identity != 0 &&
      EventValid(p.entry_event, thread) && EventValid(p.phase_entry_event, thread) &&
      p.entry_event.clock_identity == p.phase_entry_event.clock_identity &&
      p.phase_entry_event.sequence < p.entry_event.sequence;
}
bool SameParent(const game::ArmyAssaultReleaseParent12004 &a,
                const game::ArmyAssaultReleaseParent12004 &b) noexcept {
  return a.active && b.active && a.manager_identity == b.manager_identity &&
      a.entry_event.clock_identity == b.entry_event.clock_identity &&
      a.entry_event.sequence == b.entry_event.sequence && a.entry_event.thread_id == b.entry_event.thread_id &&
      a.phase_entry_event.clock_identity == b.phase_entry_event.clock_identity &&
      a.phase_entry_event.sequence == b.phase_entry_event.sequence &&
      a.actual_entry_rva == b.actual_entry_rva && a.caller_return_rva == b.caller_return_rva;
}

void CaptureVector(const void *record, std::size_t offset, std::uint32_t expected,
                   game::ArmyAssaultReleaseVectorSnapshot12004 &out,
                   Event &event, bool after) noexcept {
  out.expected_allocator_rva_u32 = expected;
  const auto header_flag = after ? game::assault_release_capture_header_after : game::assault_release_capture_header_before;
  const auto payload_flag = after ? game::assault_release_capture_payload_after : game::assault_release_capture_payload_before;
  std::uint64_t data = 0, allocator = 0;
  std::int32_t count = 0, capacity = 0;
  if (ReadAt(record, offset, data)) out.data_address = data; else event.capture_failure_flags |= header_flag;
  if (ReadAt(record, offset + 8, capacity)) out.capacity_raw_i32 = capacity; else event.capture_failure_flags |= header_flag;
  if (ReadAt(record, offset + 12, count)) out.count_raw_i32 = count; else event.capture_failure_flags |= header_flag;
  if (ReadAt(record, offset + 16, allocator)) {
    out.allocator_address = allocator;
    out.allocator_matches_expected = allocator == g_bindings.image_base + expected;
  } else event.capture_failure_flags |= header_flag;
  if (!out.data_address || !out.count_raw_i32) return;
  if (*out.count_raw_i32 <= 0) { out.payload_complete = true; return; }
  if (*out.data_address == 0) { event.capture_failure_flags |= payload_flag; return; }
  const auto wanted = static_cast<std::uint32_t>(*out.count_raw_i32);
  const auto bounded = std::min(wanted, static_cast<std::uint32_t>(out.raw_full_ids_u32.size()));
  for (std::uint32_t i = 0; i < bounded; ++i) {
    const auto address = *out.data_address + static_cast<std::uint64_t>(i) * 4;
    std::uint32_t raw = 0;
    if (address < *out.data_address || !ReadMemory(reinterpret_cast<const void *>(address), &raw, sizeof(raw))) {
      event.capture_failure_flags |= payload_flag; break;
    }
    out.raw_full_ids_u32[out.payload_count++] = raw;
  }
  out.payload_complete = out.payload_count == wanted;
  if (wanted > bounded) event.capture_failure_flags |= game::assault_release_capture_payload_truncated;
}
bool SelectedCanonical(const game::ArmyAssaultReleaseVectorSnapshot12004 &v) noexcept {
  // Null data takes the native no-store branch; its receiver is not consumed.
  return !v.data_address || *v.data_address == 0 || v.allocator_matches_expected == true;
}
bool AssociateSlot(const void *record, Event &event) noexcept {
  std::uintptr_t entries = 0;
  std::int32_t occupied = 0;
  const auto manager = reinterpret_cast<const void *>(event.parent.manager_identity);
  if (!ReadAt(manager, 0x178, entries) || !ReadAt(manager, 0x180, occupied)) return false;
  event.entries_address = entries; event.occupied_count_before = occupied;
  const auto receiver = reinterpret_cast<std::uintptr_t>(record);
  if (entries == 0 || occupied <= 0 || receiver < entries || receiver - entries < 0x10) return false;
  const auto delta = receiver - entries - 0x10;
  if (delta % 0x40 != 0) return false;
  event.physical_slot = delta / 0x40;
  std::uint8_t control = 0;
  if (!ReadMemory(reinterpret_cast<const void *>(receiver - 0xC), &control, sizeof(control)) || control == 0) return false;
  event.control_before = control;
  return true;
}
void CaptureRecordReturn(const void *record, Event &event) noexcept {
  CaptureVector(record, 0x18, 0x54DEB68, event.arrgs_after, event, true);
  CaptureVector(record, 0, 0x54E0570, event.armies_after, event, true);
  std::uint8_t control = 0;
  if (ReadMemory(reinterpret_cast<const void *>(event.record_plus10_address - 0xC), &control, sizeof(control)))
    event.control_at_record_return = control;
  else event.capture_failure_flags |= game::assault_release_capture_slot;
  std::int32_t count = 0;
  if (ReadAt(reinterpret_cast<const void *>(event.parent.manager_identity), 0x180, count))
    event.occupied_count_at_record_return = count;
  else event.capture_failure_flags |= game::assault_release_capture_slot;
}

bool InitializeRuntime(const ArmyAssaultGroupReleaseBindings12004 &bindings,
                       ArmyAssaultGroupReleaseOriginal12004 original) noexcept {
  if (!bindings.enabled || original == nullptr || bindings.read_active_parent == nullptr || bindings.next_phase_clock == nullptr) return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_journal_mutex);
    g_bindings = bindings;
    g_latest_sequence = 0;
    g_unattributed_failures = 0;
    g_ignored_noncanonical = 0;
    g_fixture_mode.store(false, std::memory_order_release);
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
void Fail(ArmyAssaultGroupReleaseDetourState12004 &state,
          ArmyAssaultGroupReleaseInstallFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ArmyAssaultGroupReleaseDetourState12004 &state,
                const std::array<std::uint8_t, kArmyAssaultGroupReleasePatchBytes12004> &expected,
                const std::array<std::uint8_t, kArmyAssaultGroupReleasePatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, assault_release_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, assault_release_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? assault_release_install_protection
                     : assault_release_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, assault_release_install_rollback);
  return false;
}

std::array<std::uint8_t, kArmyAssaultGroupReleasePatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kArmyAssaultGroupReleasePatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarArmyAssaultGroupReleaseHook12004));
  return patch;
}

} // namespace

ArmyAssaultGroupReleaseBindings12004 BindArmyAssaultGroupReleaseImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ArmyAssaultGroupReleaseBindings12004 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = image_base;
  result.read_active_parent = &ActiveParent;
  result.next_phase_clock = &NextArmyNaturalPhaseEvent12004;
  return result;
}

bool InitializeArmyAssaultGroupReleaseFixture12004(
    const ArmyAssaultGroupReleaseBindings12004 &bindings,
    ArmyAssaultGroupReleaseOriginal12004 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  const bool ready = InitializeRuntime(bindings, original);
  if (ready) g_fixture_mode.store(true, std::memory_order_release);
  return ready;
}

bool InstallArmyAssaultGroupReleaseObserver12004(
    ArmyAssaultGroupReleaseDetourState12004 &state,
    const ArmyAssaultGroupReleaseInstallEnvironment12004 &environment,
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
  state.failure_flags.store(assault_release_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, assault_release_install_exact_build);
    return false;
  }
  if (environment.bindings.read_active_parent == nullptr || environment.bindings.next_phase_clock == nullptr) {
    Fail(state, assault_release_install_parent_clock_binding);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, assault_release_install_quiescence);
    return false;
  }
  ArmyAssaultGroupReleaseDetourState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, assault_release_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kArmyAssaultGroupReleaseRva12004;
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
    Fail(state, assault_release_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kArmyAssaultGroupReleasePatchBytes12004 +
      kArmyAssaultGroupReleaseAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, assault_release_install_allocation);
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
      reinterpret_cast<ArmyAssaultGroupReleaseOriginal12004>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch())) {
    if (!executable) Fail(state, assault_release_install_protection);
    else if (!flushed) Fail(state, assault_release_install_flush);
    if ((state.failure_flags.load(std::memory_order_acquire) &
         assault_release_install_rollback) != 0) {
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

std::optional<game::ArmyAssaultGroupReleaseObservations12004>
ReadArmyAssaultGroupReleaseObservations12004(std::uint32_t exact_native_carmy_full_id) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  const auto *active = g_active_state.load(std::memory_order_acquire);
  const bool guarded = active != nullptr && g_bindings.enabled && g_bindings.image_base != 0 &&
      active->installed.load(std::memory_order_acquire) != 0 && active->failure_flags.load(std::memory_order_acquire) == 0;
  if (!guarded && !g_fixture_mode.load(std::memory_order_acquire)) return std::nullopt;
  try {
    game::ArmyAssaultGroupReleaseObservations12004 result{};
    result.observer_installed = guarded; result.current_session_guard = guarded;
    const std::lock_guard lock(g_journal_mutex);
    result.latest_sequence = g_latest_sequence;
    result.oldest_available_sequence = g_latest_sequence == 0 ? 0 :
        g_latest_sequence <= g_slots.size() ? 1 : g_latest_sequence - g_slots.size() + 1;
    result.overwritten_events = g_latest_sequence > g_slots.size() ? g_latest_sequence - g_slots.size() : 0;
    result.unattributed_capture_failures = g_unattributed_failures;
    result.ignored_noncanonical_receivers = g_ignored_noncanonical;
    for (auto sequence = result.oldest_available_sequence; sequence != 0 && sequence <= g_latest_sequence; ++sequence) {
      const auto &slot = g_slots[(sequence - 1) % g_slots.size()];
      if (slot.sequence != sequence) continue;
      const auto &before = slot.event.armies_before;
      const auto end = before.raw_full_ids_u32.begin() + before.payload_count;
      if (std::find(before.raw_full_ids_u32.begin(), end, exact_native_carmy_full_id) != end)
        result.events.push_back(slot.event);
    }
    return result;
  } catch (...) { return std::nullopt; }
}

namespace {
std::uint64_t Observe(std::uint64_t caller_return_rva, const void *record) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return 0; // Unreachable for an installed process-lifetime hook.
  if (caller_return_rva != 0x2A981AE) return original(record);
  Event event{};
  event.thread_id = GetCurrentThreadId();
  if (!g_bindings.read_active_parent(g_bindings.parent_context, event.parent) || !ParentValid(event.parent, event.thread_id))
    return original(record);
  event.caller_return_rva = caller_return_rva; event.callsite_rva = 0x2A981A9;
  event.record_plus10_address = reinterpret_cast<std::uintptr_t>(record);
  if (!AssociateSlot(record, event)) {
    { const std::lock_guard lock(g_journal_mutex); ++g_unattributed_failures; }
    return original(record);
  }
  event.entry_event = g_bindings.next_phase_clock(g_bindings.clock_context);
  CaptureVector(record, 0x18, 0x54DEB68, event.arrgs_before, event, false);
  CaptureVector(record, 0, 0x54E0570, event.armies_before, event, false);
  if (!SelectedCanonical(event.arrgs_before) || !SelectedCanonical(event.armies_before)) {
    { const std::lock_guard lock(g_journal_mutex); ++g_ignored_noncanonical; }
    return original(record);
  }
  // Native execution is neither caught nor replayed. Keep every original RAX
  // bit, and never reread a freed pre-buffer after this single call.
  const std::uint64_t returned = original(record);
  event.original_rax_raw_u64 = returned; event.original_returned = true;
  event.returned_event = g_bindings.next_phase_clock(g_bindings.clock_context);
  CaptureRecordReturn(record, event);
  game::ArmyAssaultReleaseParent12004 after_parent{};
  event.same_parent_at_return = g_bindings.read_active_parent(g_bindings.parent_context, after_parent) &&
      ParentValid(after_parent, event.thread_id) && SameParent(event.parent, after_parent);
  if (!event.same_parent_at_return) event.capture_failure_flags |= game::assault_release_capture_parent;
  event.same_clock_thread_order = EventValid(event.entry_event, event.thread_id) &&
      EventValid(event.returned_event, event.thread_id) &&
      event.entry_event.clock_identity == event.parent.entry_event.clock_identity &&
      event.returned_event.clock_identity == event.entry_event.clock_identity &&
      event.parent.entry_event.sequence < event.entry_event.sequence &&
      event.entry_event.sequence < event.returned_event.sequence;
  if (event.same_clock_thread_order != true) event.capture_failure_flags |= game::assault_release_capture_clock;
  Publish(event, true);
  return returned;
}
} // namespace

std::uint64_t InvokeArmyAssaultGroupReleaseFixture12004(std::uint64_t caller_return_rva, const void *record_plus10) noexcept {
  if (!g_fixture_mode.load(std::memory_order_acquire) ||
      g_active_state.load(std::memory_order_acquire) != nullptr) return 0;
  return Observe(caller_return_rva, record_plus10);
}
extern "C" std::uint64_t __fastcall XarArmyAssaultGroupReleaseHook12004(const void *record_plus10) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva = g_bindings.image_base && caller >= g_bindings.image_base ? caller - g_bindings.image_base : 0;
  return Observe(rva, record_plus10);
}
} // namespace xar::ck3_12004
