#include "xar_bridge/actual_army_compiled_effect_observer_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <mutex>
#if defined(_MSC_VER)
#include <intrin.h>
#endif

namespace xar::ck3_12004 {
namespace {

// Held full wrapper252B: first 5+5+1+7 byte instructions, no RIP or
// relative operand. The trampoline resumes at3765772 with original ABI/stack.
constexpr std::array<std::uint8_t, kActualArmyCompiledEffectPatchBytes12004>
    kCallbackPrologue{0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,
                      0x57,0x48,0x81,0xEC,0x30,0x04,0x00,0x00};

using Event = game::ArmyActualCompiledEffectObservationV1;
struct JournalSlot {
  std::uint64_t sequence = 0;
  Event event{};
};
std::array<JournalSlot, game::kArmyActualCompiledEffectJournalCapacityV1> g_slots{};
std::mutex g_journal_mutex;
std::uint64_t g_latest_sequence = 0;
std::uint64_t g_unattributed_failures = 0;
std::atomic<std::uint64_t> g_entry_sequence{0};
std::atomic<bool> g_fixture_mode{false};
ActualArmyCompiledEffectBindingsV1 g_bindings{};
std::atomic<bool> g_available{false};
std::atomic<ActualArmyCompiledEffectOriginalV1> g_original{nullptr};
std::atomic<ActualArmyCompiledEffectDetourStateV1 *> g_active_state{nullptr};

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

std::optional<game::ArmyCompiledEffectSourceV1> Classify(std::uint64_t rva) noexcept {
  if (rva == 0x2639CA4) return game::ArmyCompiledEffectSourceV1::positive_1e0;
  if (rva == 0x24DD7B6) return game::ArmyCompiledEffectSourceV1::flag30;
  return std::nullopt;
}
bool IncomingRead(void *, const void *address, void *output, std::size_t size) noexcept {
  return ReadMemory(address, output, size);
}
bool CaptureScope(const void *scope, ArmyLateContextCopy12004 &out) noexcept {
  out = CopyActualArmyLateContext12004(scope, &IncomingRead, nullptr);
  return out.root_copy_ready && out.context_seed_10_raw_u32.has_value() &&
      out.named_rows_copy_ready && !out.named_rows_truncated;
}
bool ArmyIdentity(const ArmyLateContextCopy12004 &scope) noexcept {
  return scope.root_copy_ready && scope.root_kind_raw_u16 == 27 &&
      scope.root_subtype_raw_u16 == 0 && scope.root_payload_raw_u64 &&
      *scope.root_payload_raw_u64 <= UINT32_MAX &&
      static_cast<std::uint32_t>(*scope.root_payload_raw_u64) != UINT32_MAX;
}
void CaptureReceiver(const void *receiver, Event &event) noexcept {
  std::uint64_t vptr = 0;
  if (ReadAt(receiver, 0, vptr)) event.receiver_vptr_raw_u64 = vptr;
  else event.capture_failure_flags |= actual_army_compiled_effect_capture_receiver;
  if (event.before.context_seed_10_raw_u32 &&
      (*event.before.context_seed_10_raw_u32 & 0x80000000U) != 0) {
    std::uint32_t key = 0;
    if (ReadAt(receiver, 0x2C, key)) event.negative_seed_receiver_key_2c_raw_u32 = key;
    else event.capture_failure_flags |= actual_army_compiled_effect_capture_receiver;
  }
  std::uint8_t flag = 0;
  if (ReadMemory(reinterpret_cast<const void *>(g_bindings.image_base + 0x5D1DADC), &flag, sizeof(flag)))
    event.effect_flag_raw_u8 = flag;
  else event.capture_failure_flags |= actual_army_compiled_effect_capture_flag;
}

bool InitializeRuntime(const ActualArmyCompiledEffectBindingsV1 &bindings,
                       ActualArmyCompiledEffectOriginalV1 original) noexcept {
  if (!bindings.enabled || original == nullptr) return false;
  g_available.store(false, std::memory_order_release);
  {
    const std::lock_guard lock(g_journal_mutex);
    g_bindings = bindings;
    g_latest_sequence = 0;
    g_unattributed_failures = 0;
    g_entry_sequence.store(0, std::memory_order_relaxed);
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
void Fail(ActualArmyCompiledEffectDetourStateV1 &state,
          ActualArmyCompiledEffectInstallFailureV1 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_acq_rel);
}

bool WritePatch(ActualArmyCompiledEffectDetourStateV1 &state,
                const std::array<std::uint8_t, kActualArmyCompiledEffectPatchBytes12004> &expected,
                const std::array<std::uint8_t, kActualArmyCompiledEffectPatchBytes12004> &desired) noexcept {
  auto *target = reinterpret_cast<void *>(state.callback_target);
  if (!FaultBoundary([&]() noexcept {
        return std::memcmp(target, expected.data(), expected.size()) == 0;
      })) {
    Fail(state, actual_army_compiled_effect_install_anchor);
    return false;
  }
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, target, desired.size(),
                             PAGE_EXECUTE_READWRITE, old)) {
    Fail(state, actual_army_compiled_effect_install_protection);
    return false;
  }
  std::memcpy(target, desired.data(), desired.size());
  const bool flushed = state.flush_instruction_cache(
      state.memory_context, target, desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, target,
                                              desired.size(), old, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? actual_army_compiled_effect_install_protection
                     : actual_army_compiled_effect_install_flush);
  DWORD rollback_old = 0;
  const bool writable = state.virtual_protect(state.memory_context, target,
      expected.size(), PAGE_EXECUTE_READWRITE, rollback_old);
  if (writable) std::memcpy(target, expected.data(), expected.size());
  const bool rollback_flushed = writable && state.flush_instruction_cache(
      state.memory_context, target, expected.size());
  const bool rollback_restored = writable && state.virtual_protect(
      state.memory_context, target, expected.size(), old, ignored);
  if (!rollback_flushed || !rollback_restored)
    Fail(state, actual_army_compiled_effect_install_rollback);
  return false;
}

std::array<std::uint8_t, kActualArmyCompiledEffectPatchBytes12004> HookPatch() noexcept {
  std::array<std::uint8_t, kActualArmyCompiledEffectPatchBytes12004> patch{};
  patch.fill(0x90);
  WriteAbsoluteJump(patch.data(), reinterpret_cast<std::uintptr_t>(
      &XarActualArmyCompiledEffectHook12004V1));
  return patch;
}

} // namespace

ActualArmyCompiledEffectBindingsV1 BindActualArmyCompiledEffectImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ActualArmyCompiledEffectBindingsV1 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.enabled = true;
  result.image_base = image_base;
  return result;
}

bool InitializeActualArmyCompiledEffectFixture12004(
    const ActualArmyCompiledEffectBindingsV1 &bindings,
    ActualArmyCompiledEffectOriginalV1 original) noexcept {
  if (g_active_state.load(std::memory_order_acquire) != nullptr) return false;
  const bool ready = InitializeRuntime(bindings, original);
  if (ready) g_fixture_mode.store(true, std::memory_order_release);
  return ready;
}

bool InstallActualArmyCompiledEffectObserver12004(
    ActualArmyCompiledEffectDetourStateV1 &state,
    const ActualArmyCompiledEffectInstallEnvironmentV1 &environment,
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
  state.failure_flags.store(actual_army_compiled_effect_install_none, std::memory_order_relaxed);
  if (executable_sha256 != kExecutableSha256 || !environment.bindings.enabled ||
      environment.bindings.image_base == 0) {
    Fail(state, actual_army_compiled_effect_install_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, actual_army_compiled_effect_install_quiescence);
    return false;
  }
  ActualArmyCompiledEffectDetourStateV1 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                               std::memory_order_acq_rel)) {
    Fail(state, actual_army_compiled_effect_install_already_installed);
    return false;
  }
  state.callback_target = environment.callback_target_override != 0
      ? environment.callback_target_override
      : environment.bindings.image_base + kActualArmyCompiledEffectRva12004;
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
    Fail(state, actual_army_compiled_effect_install_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  const auto allocate = environment.virtual_alloc_override != nullptr
      ? environment.virtual_alloc_override : &DefaultAlloc;
  constexpr auto trampoline_bytes = kActualArmyCompiledEffectPatchBytes12004 +
      kActualArmyCompiledEffectAbsoluteJumpBytes12004;
  state.trampoline = allocate(state.memory_context, trampoline_bytes,
                               MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (state.trampoline == nullptr) {
    Fail(state, actual_army_compiled_effect_install_allocation);
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
      reinterpret_cast<ActualArmyCompiledEffectOriginalV1>(state.trampoline));
  if (!executable || !flushed || !initialized ||
      !WritePatch(state, kCallbackPrologue, HookPatch())) {
    if (!executable) Fail(state, actual_army_compiled_effect_install_protection);
    else if (!flushed) Fail(state, actual_army_compiled_effect_install_flush);
    if ((state.failure_flags.load(std::memory_order_acquire) &
         actual_army_compiled_effect_install_rollback) != 0) {
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

std::optional<game::ArmyActualCompiledEffectObservationsV1>
ReadActualArmyCompiledEffectObservations12004(
    std::int32_t native_carmy_id) noexcept {
  if (!g_available.load(std::memory_order_acquire)) return std::nullopt;
  const auto *active = g_active_state.load(std::memory_order_acquire);
  const bool guarded = active != nullptr && g_bindings.enabled && g_bindings.image_base != 0 &&
      active->installed.load(std::memory_order_acquire) != 0 &&
      active->failure_flags.load(std::memory_order_acquire) == 0;
  if (!guarded && !g_fixture_mode.load(std::memory_order_acquire)) return std::nullopt;
  try {
    game::ArmyActualCompiledEffectObservationsV1 result{};
    result.observer_installed = guarded;
    result.current_session_guard = guarded;
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
std::uint64_t Observe(std::uint64_t caller_return_rva, const void *receiver,
                      const void *scope) noexcept {
  const auto original = g_original.load(std::memory_order_acquire);
  if (original == nullptr) return 0; // Unreachable for an installed/pinned hook.
  const auto source = Classify(caller_return_rva);
  if (!source) return original(receiver, scope);
  Event event{};
  event.entry_sequence = g_entry_sequence.fetch_add(1, std::memory_order_relaxed) + 1;
  event.thread_id = GetCurrentThreadId();
  event.caller_return_rva = caller_return_rva;
  event.callsite_rva = caller_return_rva - 5;
  event.source = *source;
  event.receiver_owner_offset = *source == game::ArmyCompiledEffectSourceV1::positive_1e0 ? 0x40 : 0x230;
  event.incoming_receiver_address = reinterpret_cast<std::uintptr_t>(receiver);
  event.incoming_context_address = reinterpret_cast<std::uintptr_t>(scope);
  if (!CaptureScope(scope, event.before)) event.capture_failure_flags |= actual_army_compiled_effect_capture_before;
  const bool identity = ArmyIdentity(event.before);
  if (identity) event.native_carmy_id = static_cast<std::int32_t>(*event.before.root_payload_raw_u64);
  CaptureReceiver(receiver, event);
  // The genuine RCX/RDX call executes exactly once. No fault boundary or catch
  // encloses native effects. Retain and return every original RAX bit unchanged.
  const std::uint64_t returned = original(receiver, scope);
  event.original_rax_raw_u64 = returned;
  event.original_returned = true;
  if (!CaptureScope(scope, event.after)) event.capture_failure_flags |= actual_army_compiled_effect_capture_after;
  event.same_root_after = identity && ArmyIdentity(event.after) &&
      event.before.root_kind_raw_u16 == event.after.root_kind_raw_u16 &&
      event.before.root_subtype_raw_u16 == event.after.root_subtype_raw_u16 &&
      event.before.root_payload_raw_u64 == event.after.root_payload_raw_u64;
  if (!event.same_root_after) event.capture_failure_flags |= actual_army_compiled_effect_capture_identity_changed;
  Publish(event, identity);
  return returned;
}
} // namespace
std::uint64_t InvokeActualArmyCompiledEffectFixture12004(
    std::uint64_t caller_return_rva, const void *receiver, const void *incoming_context) noexcept {
  return Observe(caller_return_rva, receiver, incoming_context);
}
extern "C" std::uint64_t __fastcall XarActualArmyCompiledEffectHook12004V1(
    const void *receiver, const void *incoming_context) noexcept {
#if defined(_MSC_VER)
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
#else
  const auto caller = reinterpret_cast<std::uintptr_t>(__builtin_return_address(0));
#endif
  const auto rva = g_bindings.image_base && caller >= g_bindings.image_base
      ? caller - g_bindings.image_base : 0;
  return Observe(rva, receiver, incoming_context);
}
} // namespace xar::ck3_12004
