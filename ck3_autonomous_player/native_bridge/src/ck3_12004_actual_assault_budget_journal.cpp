#include "xar_bridge/ck3_12004_actual_assault_budget_journal.hpp"
#include "xar_bridge/ck3_12004_actual_assault_consumer_journal.hpp"
#include <bit>
#include <cstring>
#include <limits>
#include <mutex>
#include <intrin.h>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kSha = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::array<std::uint8_t, kActualAssaultBudgetPatchBytes12004> kPrefix{
    0x40,0x53,0x48,0x83,0xEC,0x20,0x48,0x8B,0xD9,0x48,0x8B,0x89,0x00,0x02,0x00,0x00};
ActualAssaultBudgetBindings12004 g_bindings;
std::atomic<std::uintptr_t> g_original{0};
std::atomic<bool> g_installed{false};
std::mutex g_journal_mutex;
std::array<ArmyActualAssaultBudgetObservationV1, kActualAssaultBudgetJournalEvents12004> g_journal{};
std::uint64_t g_sequence = 0;
std::size_t g_count = 0, g_next = 0;
thread_local bool g_observing = false;

bool EqualSha(std::string_view value) noexcept {
  if (value.size() != kSha.size()) return false;
  for (std::size_t i = 0; i < value.size(); ++i) {
    auto c = value[i]; if (c >= 'a' && c <= 'f') c = static_cast<char>(c - 'a' + 'A');
    if (c != kSha[i]) return false;
  }
  return true;
}
bool GuardedRead(void *, const void *address, void *out, std::size_t size) noexcept {
  if (!address || !out || size == 0) return false;
  SIZE_T copied = 0;
  return ReadProcessMemory(GetCurrentProcess(), address, out, size, &copied) && copied == size;
}
template<class T> std::optional<T> Read(const ActualAssaultBudgetBindings12004 &b,
    std::uintptr_t object, std::size_t offset) noexcept {
  if (!object || !b.read_memory || offset > (std::numeric_limits<std::uintptr_t>::max)() - object)
    return std::nullopt;
  T value{};
  if (!b.read_memory(b.read_context, reinterpret_cast<const void *>(object + offset), &value, sizeof value))
    return std::nullopt;
  return value;
}
ActualAssaultBudgetReceiver12004 Capture(const ActualAssaultBudgetBindings12004 &b,
    std::uintptr_t siege) noexcept {
  ActualAssaultBudgetReceiver12004 out{};
  out.siege_full_id = Read<std::uint32_t>(b, siege, 8);
  out.province_identity = Read<std::uintptr_t>(b, siege, 0x200);
  out.breach_level = Read<std::int32_t>(b, siege, 0x3D8);
  if (out.province_identity && *out.province_identity) {
    out.province_full_id = Read<std::uint32_t>(b, *out.province_identity, 0x10);
    out.province_magic = Read<std::uint32_t>(b, *out.province_identity, 0x85C);
  }
  out.identity_complete = out.siege_full_id.has_value() && out.province_identity &&
      *out.province_identity != 0 && out.province_full_id.has_value();
  return out;
}
bool SameParent(const ArmyAssaultConsumerParent12004 &a,
    const ArmyAssaultConsumerParent12004 &b) noexcept {
  return a.active && b.active && a.exact_post_date_parent && b.exact_post_date_parent &&
      a.actual_entry_rva == b.actual_entry_rva && a.caller_return_rva == b.caller_return_rva &&
      a.manager_identity == b.manager_identity && a.entry_event.clock_identity == b.entry_event.clock_identity &&
      a.entry_event.sequence == b.entry_event.sequence && a.entry_event.thread_id == b.entry_event.thread_id;
}
bool Ordered(const ArmyAssaultConsumerParent12004 &p, const ArmyNaturalPhaseEvent12004 &a,
    const ArmyNaturalPhaseEvent12004 &b, std::uint32_t thread) noexcept {
  return p.entry_event.clock_identity != 0 && p.entry_event.clock_identity == a.clock_identity &&
      a.clock_identity == b.clock_identity && p.entry_event.sequence != 0 &&
      p.entry_event.sequence < a.sequence && a.sequence < b.sequence &&
      p.entry_event.thread_id == thread && a.thread_id == thread && b.thread_id == thread;
}
void Publish(ArmyActualAssaultBudgetObservationV1 value) noexcept {
  try {
    const std::lock_guard lock(g_journal_mutex);
    value.journal_sequence = ++g_sequence;
    g_journal[g_next] = value;
    g_next = (g_next + 1) % g_journal.size();
    if (g_count < g_journal.size()) ++g_count;
  } catch (...) { /* Observation failure never replaces the native result. */ }
}
void *Allocate(void *, std::size_t size, DWORD type, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool Free(void *, void *address, std::size_t size, DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
bool Protect(void *, void *address, std::size_t size, DWORD protection, DWORD &old) noexcept {
  return VirtualProtect(address, size, protection, &old) != FALSE;
}
bool Flush(void *, const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}
void Jump(std::uint8_t *out, std::uintptr_t target) noexcept {
  out[0] = 0xFF; out[1] = 0x25; std::memset(out + 2, 0, 4); std::memcpy(out + 6, &target, 8);
}
} // namespace

ActualAssaultBudgetBindings12004 BindActualAssaultBudgetJournalImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  ActualAssaultBudgetBindings12004 out{};
  if (!base || !EqualSha(sha)) return out;
  out.enabled = true; out.image_base = base; out.read_memory = GuardedRead;
  out.copy_parent = CopyActiveArmyAssaultConsumerParent12004;
  out.next_event = NextArmyNaturalPhaseEvent12004;
  out.record_parent_budget = RecordActualAssaultConsumerBudget12004;
  return out;
}
bool InitializeActualAssaultBudgetJournalFixture12004(
    const ActualAssaultBudgetBindings12004 &b, ActualAssaultBudgetOriginal12004 original) noexcept {
  if (!original || g_installed.load()) return false;
  g_bindings = b; g_original.store(reinterpret_cast<std::uintptr_t>(original));
  return true;
}
std::uintptr_t InvokeActualAssaultBudgetObserver12004(void *siege,
    std::optional<std::uintptr_t> caller) noexcept {
  const auto original = reinterpret_cast<ActualAssaultBudgetOriginal12004>(g_original.load());
  if (!original) return 0; // Uninstalled fixture route; installed hook cannot reach this state.
  const auto b = g_bindings;
  ArmyAssaultConsumerParent12004 parent{};
  const bool eligible = !g_observing && b.enabled && caller == kActualAssaultBudgetCallerReturnRva12004 &&
      b.copy_parent && b.copy_parent(parent) && parent.active && parent.exact_post_date_parent &&
      parent.actual_entry_rva == 0x2A97EB0 && parent.caller_return_rva == 0x2A9A8EA &&
      parent.manager_identity != 0;
  if (!eligible) return original(siege);
  const auto entry_last_error = GetLastError();
  struct ObservingGuard { ObservingGuard() { g_observing = true; } ~ObservingGuard() { g_observing = false; } } guard;
  ArmyActualAssaultBudgetObservationV1 out{};
  out.parent = parent; out.observed_thread_id = GetCurrentThreadId();
  out.getter_entry_rva = kActualAssaultBudgetRva12004; out.actual_caller_return_rva = *caller;
  out.selected_siege_identity = reinterpret_cast<std::uintptr_t>(siege);
  if (b.next_event) out.entry_event = b.next_event(b.event_context);
  out.entry_receiver = Capture(b, out.selected_siege_identity);
  out.original_called = true;
  SetLastError(entry_last_error);
  const auto result = original(siege); // Exactly one naturally reached call.
  const auto native_last_error = GetLastError();
  out.original_returned = true; out.raw_return_bits = result;
  out.consumed_eax_u32 = static_cast<std::uint32_t>(result);
  out.native_expected_loss_i32 = std::bit_cast<std::int32_t>(out.consumed_eax_u32);
  out.returned_receiver = Capture(b, out.selected_siege_identity);
  if (b.next_event) out.returned_event = b.next_event(b.event_context);
  ArmyAssaultConsumerParent12004 after{};
  out.parent_still_active = b.copy_parent && b.copy_parent(after) && SameParent(parent, after);
  out.same_clock_thread_order = Ordered(parent, out.entry_event, out.returned_event, out.observed_thread_id);
  const auto &a = out.entry_receiver; const auto &z = out.returned_receiver;
  out.receiver_identity_unchanged = a.identity_complete && z.identity_complete &&
      a.siege_full_id == z.siege_full_id && a.province_identity == z.province_identity &&
      a.province_full_id == z.province_full_id;
  if (out.parent_still_active && out.same_clock_thread_order && out.receiver_identity_unchanged &&
      b.record_parent_budget)
    out.parent_group_budget_recorded = b.record_parent_budget(out.selected_siege_identity,
        *caller, out.entry_event, out.returned_event, out.native_expected_loss_i32,
        a.siege_full_id, a.province_identity, a.province_full_id);
  Publish(out);
  SetLastError(native_last_error);
  return result;
}
extern "C" std::uintptr_t __fastcall XarActualAssaultBudgetHook12004(void *siege) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto base = g_bindings.image_base;
  return InvokeActualAssaultBudgetObserver12004(siege,
      base && address >= base ? std::optional<std::uintptr_t>(address - base) : std::nullopt);
}
ArmyActualAssaultBudgetObservationsV1 ReadActualAssaultBudgetObservations12004(
    const ArmyNaturalPhaseEvent12004 &parent_entry) noexcept {
  ArmyActualAssaultBudgetObservationsV1 out{};
  out.observer_installed = g_installed.load();
  try {
    const std::lock_guard lock(g_journal_mutex);
    out.latest_journal_sequence = g_sequence;
    out.overwritten_events = g_sequence > g_journal.size() ? g_sequence - g_journal.size() : 0;
    if (!parent_entry.clock_identity || !parent_entry.sequence || !parent_entry.thread_id) return out;
    for (std::size_t i = 0; i < g_count; ++i) {
      const auto &value = g_journal[(g_next + g_journal.size() - g_count + i) % g_journal.size()];
      const auto &entry = value.parent.entry_event;
      if (entry.clock_identity == parent_entry.clock_identity && entry.sequence == parent_entry.sequence &&
          entry.thread_id == parent_entry.thread_id) out.events.push_back(value);
    }
  } catch (...) { out.events.clear(); }
  return out;
}
bool InstallActualAssaultBudgetJournal12004(ActualAssaultBudgetDetourState12004 &state,
    const ActualAssaultBudgetInstallEnvironment12004 &env, std::string_view sha) noexcept {
  if (!env.primary_thread_suspended_proven || !env.bindings.enabled || !EqualSha(sha) ||
      state.installed.load() || g_installed.load() || !env.bindings.copy_parent ||
      !env.bindings.next_event || !env.bindings.record_parent_budget || !env.bindings.read_memory) {
    state.failure_flags.fetch_or(1); return false;
  }
  const auto target = env.budget_target_override ? env.budget_target_override :
      env.bindings.image_base + kActualAssaultBudgetRva12004;
  std::array<std::uint8_t, kActualAssaultBudgetPatchBytes12004> prefix{};
  if (!target || !env.bindings.read_memory(env.bindings.read_context,
      reinterpret_cast<const void *>(target), prefix.data(), prefix.size()) || prefix != kPrefix) {
    state.failure_flags.fetch_or(2); return false;
  }
  const auto allocate = env.virtual_alloc_override ? env.virtual_alloc_override : Allocate;
  const auto release = env.virtual_free_override ? env.virtual_free_override : Free;
  const auto protect = env.virtual_protect_override ? env.virtual_protect_override : Protect;
  const auto flush = env.flush_instruction_cache_override ? env.flush_instruction_cache_override : Flush;
  auto *trampoline = static_cast<std::uint8_t *>(allocate(env.memory_context, prefix.size() + 14,
      MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE));
  if (!trampoline) { state.failure_flags.fetch_or(4); return false; }
  std::memcpy(trampoline, prefix.data(), prefix.size()); Jump(trampoline + prefix.size(), target + prefix.size());
  if (!flush(env.memory_context, trampoline, prefix.size() + 14)) {
    release(env.memory_context, trampoline, 0, MEM_RELEASE); state.failure_flags.fetch_or(8); return false;
  }
  DWORD old = 0;
  if (!protect(env.memory_context, reinterpret_cast<void *>(target), prefix.size(), PAGE_EXECUTE_READWRITE, old)) {
    release(env.memory_context, trampoline, 0, MEM_RELEASE); state.failure_flags.fetch_or(16); return false;
  }
  std::array<std::uint8_t, kActualAssaultBudgetPatchBytes12004> jump{};
  jump.fill(0x90); Jump(jump.data(), reinterpret_cast<std::uintptr_t>(&XarActualAssaultBudgetHook12004));
  const auto previous_bindings = g_bindings;
  const auto previous_original = g_original.load();
  g_bindings = env.bindings; g_original.store(reinterpret_cast<std::uintptr_t>(trampoline));
  std::memcpy(reinterpret_cast<void *>(target), jump.data(), jump.size());
  DWORD ignored = 0;
  const bool protected_again = protect(env.memory_context, reinterpret_cast<void *>(target), prefix.size(), old, ignored);
  const bool flushed = flush(env.memory_context, reinterpret_cast<void *>(target), prefix.size());
  if (!protected_again || !flushed) {
    DWORD writable_old = 0;
    if (protect(env.memory_context, reinterpret_cast<void *>(target), prefix.size(), PAGE_EXECUTE_READWRITE, writable_old)) {
      std::memcpy(reinterpret_cast<void *>(target), prefix.data(), prefix.size());
      protect(env.memory_context, reinterpret_cast<void *>(target), prefix.size(), old, ignored);
      flush(env.memory_context, reinterpret_cast<void *>(target), prefix.size());
      g_bindings = previous_bindings; g_original.store(previous_original);
      release(env.memory_context, trampoline, 0, MEM_RELEASE);
    } else {
      // Keep the valid original trampoline reachable if rollback is unavailable.
      state.trampoline = trampoline; state.budget_target = target; state.original = prefix;
      state.memory_context = env.memory_context; state.virtual_free = release;
      state.virtual_protect = protect; state.flush_instruction_cache = flush;
      state.installed.store(1); g_installed.store(true);
    }
    state.failure_flags.fetch_or(32); return false;
  }
  state.trampoline = trampoline; state.budget_target = target; state.original = prefix;
  state.memory_context = env.memory_context; state.virtual_free = release;
  state.virtual_protect = protect; state.flush_instruction_cache = flush;
  state.installed.store(1); g_installed.store(true); return true;
}
bool UninstallActualAssaultBudgetJournal12004(ActualAssaultBudgetDetourState12004 &state,
    bool suspended) noexcept {
  if (!suspended || !state.installed.load() || !state.virtual_protect || !state.virtual_free ||
      !state.flush_instruction_cache) return false;
  DWORD old = 0;
  if (!state.virtual_protect(state.memory_context, reinterpret_cast<void *>(state.budget_target),
      state.original.size(), PAGE_EXECUTE_READWRITE, old)) return false;
  std::memcpy(reinterpret_cast<void *>(state.budget_target), state.original.data(), state.original.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context, reinterpret_cast<void *>(state.budget_target),
      state.original.size(), old, ignored);
  const bool flushed = state.flush_instruction_cache(state.memory_context,
      reinterpret_cast<void *>(state.budget_target), state.original.size());
  if (!restored || !flushed) { state.failure_flags.fetch_or(64); return false; }
  g_installed.store(false); g_original.store(0);
  const bool freed = state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE);
  if (!freed) { state.failure_flags.fetch_or(128); return false; }
  state.trampoline = nullptr; state.installed.store(0); return true;
}
} // namespace xar::ck3_12004
