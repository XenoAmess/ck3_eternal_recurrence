#include "xar_bridge/activity_completion_effect_counter_observer_12004.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::ck3_12004 {
namespace {

static_assert(sizeof(void *) == 8, "The fixed Activity completion cuts are x64-only");
using State = ActivityCompletionEffectCounterObserver12004State;
using Window = ActivityCompletionEffectCounterObserver12004Window;
using Operands = xar::bridge::ActivityCompletionEffectOperands12004;
using Stub = std::array<std::uint8_t, kActivityCompletionEffectCounterStubCapacity12004>;
std::atomic<State *> g_active{nullptr};

// Actual23F6B75..23F6B8E. Only the LEA at7D and MOV at87 are replaced.
// CALL23F6B82 is neither displaced nor synthesized by either stub.
constexpr std::array<std::uint8_t, 25> kActualAnchor{
    0x49, 0x8D, 0x8C, 0x24, 0x70, 0x03, 0x00, 0x00,
    0x48, 0x8D, 0x54, 0x24, 0x40,
    0xE8, 0xD9, 0xEB, 0x36, 0x01,
    0x49, 0x8B, 0x8D, 0xA0, 0x03, 0x00, 0x00};

struct Pending {
  State *owner = nullptr;
  Operands operands{};
};
struct PendingStack {
  std::array<Pending, 32> entries{};
  std::size_t size = 0;
  State *overflow_owner = nullptr;
  std::uintptr_t overflow_parent_rsp = 0;
};
thread_local PendingStack g_pending{};

void Fail(State &state, ActivityCompletionEffectCounterObserverFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(flag), std::memory_order_acq_rel);
}

bool Active(State *state) noexcept {
  return state != nullptr && g_active.load(std::memory_order_acquire) == state &&
      state->callbacks_enabled.load(std::memory_order_acquire);
}

bool SameOperands(const Operands &a, const Operands &b) noexcept {
  return a.activity == b.activity && a.participant == b.participant &&
      a.effect == b.effect && a.native_context == b.native_context &&
      a.original_parent_rsp == b.original_parent_rsp && a.thread_id == b.thread_id;
}

Operands PhysicalOperands(std::uintptr_t activity, std::uintptr_t participant,
                         std::uintptr_t effect, std::uintptr_t native_context,
                         std::uintptr_t original_parent_rsp) noexcept {
  Operands result{};
  result.activity = activity;
  result.participant = participant;
  result.effect = effect;
  result.native_context = native_context;
  result.original_parent_rsp = original_parent_rsp;
  result.thread_id = GetCurrentThreadId();
  return result;
}

extern "C" void ActivityCompletionEffectCounterBeforeThunk12004(
    State *state, std::uintptr_t activity, std::uintptr_t participant,
    std::uintptr_t effect, std::uintptr_t native_context,
    std::uintptr_t original_parent_rsp, std::uintptr_t) noexcept {
  if (!Active(state)) return;
  auto operands = PhysicalOperands(activity, participant, effect, native_context, original_parent_rsp);
  operands.invocation_sequence = state->before_count.fetch_add(1, std::memory_order_relaxed) + 1;
  auto &pending = g_pending;
  if (pending.overflow_owner != nullptr) {
    state->dropped_before_count.fetch_add(1, std::memory_order_relaxed);
    return;
  }
  // A fresh before at the same physical parent stack supersedes a stale
  // nonlocal-exit record. It cannot borrow that record's sequence.
  for (std::size_t i = 0; i < pending.size; ++i) {
    if (pending.entries[i].owner == state &&
        pending.entries[i].operands.original_parent_rsp == original_parent_rsp) {
      pending.size = i;
      break;
    }
  }
  if (pending.size == pending.entries.size() || operands.invocation_sequence == 0) {
    pending.overflow_owner = state;
    pending.overflow_parent_rsp = original_parent_rsp;
    state->dropped_before_count.fetch_add(1, std::memory_order_relaxed);
    return;
  }
  pending.entries[pending.size++] = {state, operands};
  // Publish the owned correlation before the callback, which can reenter.
  state->environment.before(state->environment.callback_context, operands);
}

extern "C" void ActivityCompletionEffectCounterAfterThunk12004(
    State *state, std::uintptr_t activity, std::uintptr_t participant,
    std::uintptr_t effect, std::uintptr_t native_context,
    std::uintptr_t original_parent_rsp, std::uintptr_t last_native_return_pc) noexcept {
  if (!Active(state)) return;
  auto &pending = g_pending;
  // The post cut is also the first-CALL guard-bypass target. Copy the native
  // return word before stub pushes overwrite it, and reject the bypass even
  // if a previous nonlocal exit left a same-stack pending record.
  if (last_native_return_pc != state->native_return_target) {
    state->bypass_post_count.fetch_add(1, std::memory_order_relaxed);
    return;
  }
  if (pending.overflow_owner != nullptr) {
    if (pending.overflow_owner == state && pending.overflow_parent_rsp == original_parent_rsp) {
      pending.overflow_owner = nullptr;
      pending.overflow_parent_rsp = 0;
    }
    state->uncorrelated_post_count.fetch_add(1, std::memory_order_relaxed);
    return;
  }
  auto operands = PhysicalOperands(activity, participant, effect, native_context, original_parent_rsp);
  // Search from the youngest record so stale nested nonlocal exits cannot
  // obstruct an exact outer return. No unmatched post emits an after callback.
  for (std::size_t i = pending.size; i != 0; --i) {
    const auto &entry = pending.entries[i - 1];
    if (entry.owner != state || entry.operands.original_parent_rsp != original_parent_rsp) continue;
    if (!SameOperands(entry.operands, operands)) {
      pending.size = i - 1;
      state->uncorrelated_post_count.fetch_add(1, std::memory_order_relaxed);
      return;
    }
    operands.invocation_sequence = entry.operands.invocation_sequence;
    pending.size = i - 1;
    state->returned_count.fetch_add(1, std::memory_order_relaxed);
    // Remove the correlation before the callback so reentry owns its record.
    state->environment.after(state->environment.callback_context, operands);
    return;
  }
  state->uncorrelated_post_count.fetch_add(1, std::memory_order_relaxed);
}

bool Add(std::uintptr_t base, std::uintptr_t rva, std::uintptr_t &result) noexcept {
  if (base == 0 || rva > (std::numeric_limits<std::uintptr_t>::max)() - base) return false;
  result = base + rva;
  return true;
}

bool Equal(std::uintptr_t address, const std::uint8_t *expected, std::size_t size) noexcept {
  if (address == 0 || expected == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return std::memcmp(reinterpret_cast<const void *>(address), expected, size) == 0;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool CopyFrom(std::uintptr_t address, std::uint8_t *destination, std::size_t size) noexcept {
  if (address == 0 || destination == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(destination, reinterpret_cast<const void *>(address), size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool CopyTo(std::uintptr_t address, const std::uint8_t *source, std::size_t size) noexcept {
  if (address == 0 || source == nullptr || size == 0) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(reinterpret_cast<void *>(address), source, size);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool Executable(DWORD protection) noexcept {
  return protection == PAGE_EXECUTE_READ || protection == PAGE_EXECUTE_READWRITE ||
      protection == PAGE_EXECUTE_WRITECOPY;
}

bool Flush(const void *address, std::size_t size) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool Relative32(std::uintptr_t target, std::uintptr_t next_pc, std::int32_t &relative) noexcept {
  if (target >= next_pc) {
    const auto distance = target - next_pc;
    if (distance > 0x7FFFFFFFu) return false;
    relative = static_cast<std::int32_t>(distance);
  } else {
    const auto distance = next_pc - target;
    if (distance > 0x80000000u) return false;
    relative = distance == 0x80000000u ? (std::numeric_limits<std::int32_t>::min)()
                                    : -static_cast<std::int32_t>(distance);
  }
  return true;
}

// Same fixed signed-rel32 allocation pattern as the adopted invalidation
// observer; this allocates observer backing, never a native game receiver.
void *AllocateFixedNearStub(std::uintptr_t next_pc) noexcept {
  SYSTEM_INFO info{};
  GetSystemInfo(&info);
  const auto granularity = static_cast<std::uintptr_t>(info.dwAllocationGranularity);
  if (granularity == 0) return nullptr;
  const auto minimum = reinterpret_cast<std::uintptr_t>(info.lpMinimumApplicationAddress);
  const auto maximum = reinterpret_cast<std::uintptr_t>(info.lpMaximumApplicationAddress);
  auto low = next_pc > 0x80000000u ? next_pc - 0x80000000u : minimum;
  auto high = next_pc <= (std::numeric_limits<std::uintptr_t>::max)() - 0x7FFFFFFFu
      ? next_pc + 0x7FFFFFFFu : maximum;
  if (low < minimum) low = minimum;
  if (high > maximum) high = maximum;
  for (auto cursor = low; cursor <= high;) {
    MEMORY_BASIC_INFORMATION region{};
    if (VirtualQuery(reinterpret_cast<const void *>(cursor), &region, sizeof(region)) == 0) break;
    const auto begin = reinterpret_cast<std::uintptr_t>(region.BaseAddress);
    if (region.RegionSize == 0 || region.RegionSize > (std::numeric_limits<std::uintptr_t>::max)() - begin) break;
    const auto end = begin + region.RegionSize;
    if (end <= cursor) break;
    if (region.State == MEM_FREE) {
      auto candidate = cursor > begin ? cursor : begin;
      const auto remainder = candidate % granularity;
      if (remainder != 0) {
        const auto adjustment = granularity - remainder;
        if (candidate > (std::numeric_limits<std::uintptr_t>::max)() - adjustment) break;
        candidate += adjustment;
      }
      std::int32_t relative = 0;
      if (candidate <= high && candidate < end &&
          kActivityCompletionEffectCounterStubCapacity12004 <= end - candidate &&
          Relative32(candidate, next_pc, relative)) {
        auto *allocated = VirtualAlloc(reinterpret_cast<void *>(candidate),
            kActivityCompletionEffectCounterStubCapacity12004, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
        if (allocated != nullptr) {
          if (Relative32(reinterpret_cast<std::uintptr_t>(allocated), next_pc, relative)) return allocated;
          (void)VirtualFree(allocated, 0, MEM_RELEASE);
        }
      }
    }
    cursor = end;
  }
  return nullptr;
}

struct Emitter {
  Stub &code;
  std::size_t cursor = 0;
  bool valid = true;
  void Bytes(std::initializer_list<std::uint8_t> values) noexcept {
    if (!valid || values.size() > code.size() - cursor) { valid = false; return; }
    for (const auto value : values) code[cursor++] = value;
  }
  void U32(std::uint32_t value) noexcept {
    if (!valid || sizeof(value) > code.size() - cursor) { valid = false; return; }
    std::memcpy(code.data() + cursor, &value, sizeof(value));
    cursor += sizeof(value);
  }
  void U64(std::uintptr_t value) noexcept {
    const auto encoded = static_cast<std::uint64_t>(value);
    if (!valid || sizeof(encoded) > code.size() - cursor) { valid = false; return; }
    std::memcpy(code.data() + cursor, &encoded, sizeof(encoded));
    cursor += sizeof(encoded);
  }
};

void Preserve(Emitter &out) noexcept {
  // Copy original[RSP-8] before any push overwrites the native return word.
  // Then eight pushes (flags + seven volatile GPRs) and184B reserve leave
  // RSP at originalRSP-256,16-aligned for the observer callback. Slots20,
  //28,30 are arguments5..7; XMM0..5 are saved at40..90 using disp32.
  out.Bytes({0xFF, 0x74, 0x24, 0xF8});
  out.Bytes({0x9C, 0x50, 0x51, 0x52, 0x41, 0x50, 0x41, 0x51, 0x41, 0x52, 0x41, 0x53});
  out.Bytes({0x48, 0x81, 0xEC, 0xB8, 0x00, 0x00, 0x00});
  for (std::uint8_t reg = 0; reg != 6; ++reg) {
    out.Bytes({0xF3, 0x0F, 0x7F, static_cast<std::uint8_t>(0x84 + 8 * reg), 0x24});
    out.U32(0x40 + 0x10 * reg);
  }
}

void Restore(Emitter &out) noexcept {
  for (std::uint8_t reg = 0; reg != 6; ++reg) {
    out.Bytes({0xF3, 0x0F, 0x6F, static_cast<std::uint8_t>(0x84 + 8 * reg), 0x24});
    out.U32(0x40 + 0x10 * reg);
  }
  out.Bytes({0x48, 0x81, 0xC4, 0xB8, 0x00, 0x00, 0x00});
  out.Bytes({0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59, 0x41, 0x58, 0x5A, 0x59, 0x58, 0x9D});
  out.Bytes({0x48, 0x8D, 0x64, 0x24, 0x08}); // discard copied word without altering flags
}

std::size_t BuildStub(State &state, Window &window, bool after, Stub &code) noexcept {
  code.fill(0x90);
  Emitter out{code};
  Preserve(out);
  out.Bytes({0x48, 0x8D, 0x84, 0x24, 0x00, 0x01, 0x00, 0x00}); // RAX=original parentRSP
  out.Bytes({0x48, 0x89, 0x44, 0x24, 0x28}); // argument6
  out.Bytes({0x48, 0x8D, 0x50, 0x40}); // original context address, never its payload
  out.Bytes({0x48, 0x89, 0x54, 0x24, 0x20}); // argument5
  out.Bytes({0x48, 0x8B, 0x84, 0x24, 0xF8, 0x00, 0x00, 0x00});
  out.Bytes({0x48, 0x89, 0x44, 0x24, 0x30}); // argument7=pre-push native return word
  out.Bytes({0x49, 0x8B, 0xD5}); // RDX=actual Activity R13
  out.Bytes({0x4D, 0x8B, 0xC6}); // R8=actual participant R14
  if (after) out.Bytes({0x4D, 0x8D, 0x8C, 0x24, 0x70, 0x03, 0x00, 0x00});
  else out.Bytes({0x4C, 0x8B, 0x8C, 0x24, 0xE0, 0x00, 0x00, 0x00}); // R9=saved native RCX
  out.Bytes({0x48, 0xB9});
  out.U64(reinterpret_cast<std::uintptr_t>(&state));
  out.Bytes({0x48, 0xB8});
  out.U64(after ? reinterpret_cast<std::uintptr_t>(&ActivityCompletionEffectCounterAfterThunk12004)
               : reinterpret_cast<std::uintptr_t>(&ActivityCompletionEffectCounterBeforeThunk12004));
  out.Bytes({0xFF, 0xD0}); // observer callback only
  Restore(out);
  for (std::size_t i = 0; i < window.patch_bytes; ++i) out.Bytes({window.original_patch[i]});
  out.Bytes({0xFF, 0x25, 0x00, 0x00, 0x00, 0x00});
  out.U64(window.continue_target);
  return out.valid ? out.cursor : 0;
}

enum class WriteResult { success, original_preserved, restore_unproven };

WriteResult WritePatch(State &state, Window &window, const std::uint8_t *expected,
                      const std::uint8_t *desired) noexcept {
  const auto size = window.patch_bytes;
  if (!Equal(window.patch_target, expected, size)) {
    Fail(state, activity_completion_effect_counter_failure_target_identity);
    return WriteResult::original_preserved;
  }
  DWORD previous = 0;
  auto *target = reinterpret_cast<void *>(window.patch_target);
  const bool writable = VirtualProtect(target, size, PAGE_EXECUTE_READWRITE, &previous) != FALSE;
  if (!writable || !Executable(previous)) {
    if (writable) { DWORD ignored = 0; (void)VirtualProtect(target, size, previous, &ignored); }
    Fail(state, activity_completion_effect_counter_failure_target_protection);
    return WriteResult::original_preserved;
  }
  const bool wrote = CopyTo(window.patch_target, desired, size);
  const bool identity = wrote && Equal(window.patch_target, desired, size);
  const bool flushed = identity && Flush(target, size);
  DWORD ignored = 0;
  const bool protected_again = VirtualProtect(target, size, previous, &ignored) != FALSE;
  if (identity && flushed && protected_again) return WriteResult::success;
  if (!flushed) Fail(state, activity_completion_effect_counter_failure_flush);
  if (!protected_again) Fail(state, activity_completion_effect_counter_failure_target_protection);
  DWORD rollback_previous = 0;
  const bool rollback_writable = VirtualProtect(target, size, PAGE_EXECUTE_READWRITE, &rollback_previous) != FALSE;
  const bool restored = rollback_writable && CopyTo(window.patch_target, expected, size) &&
      Equal(window.patch_target, expected, size);
  const bool restore_flushed = restored && Flush(target, size);
  DWORD rollback_ignored = 0;
  const bool restore_protected = rollback_writable && VirtualProtect(target, size, previous, &rollback_ignored) != FALSE;
  if (!restored || !restore_flushed || !restore_protected) {
    Fail(state, activity_completion_effect_counter_failure_restore);
    return WriteResult::restore_unproven;
  }
  return WriteResult::original_preserved;
}

bool RestoreWindow(State &state, Window &window) noexcept {
  if (!window.patch_owned_or_uncertain) return true;
  // Always perform a protected/flush-confirmed write, even if bytes already
  // equal original after an uncertain previous rollback.
  const auto *expected = Equal(window.patch_target, window.original_patch.data(), window.patch_bytes)
      ? window.original_patch.data() : window.installed_patch.data();
  if (WritePatch(state, window, expected, window.original_patch.data()) != WriteResult::success) {
    Fail(state, activity_completion_effect_counter_failure_restore);
    return false;
  }
  window.patch_owned_or_uncertain = false;
  return true;
}

bool ReleaseUnusedBacking(State &state) noexcept {
  bool released = true;
  for (auto &window : state.windows) {
    if (window.patch_owned_or_uncertain) { released = false; continue; }
    if (window.stub != nullptr && VirtualFree(window.stub, 0, MEM_RELEASE) == FALSE) {
      Fail(state, activity_completion_effect_counter_failure_restore);
      released = false;
      continue;
    }
    window = {};
  }
  if (released) {
    state.environment = {};
    state.native_return_target = 0;
  }
  return released;
}

bool HasOwnedPatch(const State &state) noexcept {
  return state.windows[0].patch_owned_or_uncertain || state.windows[1].patch_owned_or_uncertain;
}

void FinishFailedInstall(State &state) noexcept {
  state.callbacks_enabled.store(false, std::memory_order_release);
  // Restore the pre window first so no new original-CALL pair can begin.
  for (auto &window : state.windows) (void)RestoreWindow(state, window);
  if (HasOwnedPatch(state)) {
    state.installed.store(true, std::memory_order_release);
    return; // uncertain target still owns its executable backing and state
  }
  state.installed.store(false, std::memory_order_release);
  g_active.store(nullptr, std::memory_order_release);
  (void)ReleaseUnusedBacking(state);
}

} // namespace

bool InstallActivityCompletionEffectCounterObserver12004(
    State &state, const ActivityCompletionEffectCounterObserver12004Environment &environment) noexcept {
  if (state.installed.load(std::memory_order_acquire) || state.windows[0].stub != nullptr ||
      state.windows[1].stub != nullptr) {
    Fail(state, activity_completion_effect_counter_failure_already_owned);
    return false;
  }
  state.failure_flags.store(0, std::memory_order_relaxed);
  if (!environment.exact_12004_build_admitted || environment.module_base == 0) {
    Fail(state, activity_completion_effect_counter_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, activity_completion_effect_counter_failure_suspension);
    return false;
  }
  if (environment.before == nullptr || environment.after == nullptr) {
    Fail(state, activity_completion_effect_counter_failure_callbacks);
    return false;
  }
  std::uintptr_t anchor = 0;
  auto &pre = state.windows[0];
  auto &post = state.windows[1];
  pre.patch_bytes = 5;
  post.patch_bytes = 7;
  if (!Add(environment.module_base, kActivityCompletionEffectCounterAnchorRva12004, anchor) ||
      !Add(environment.module_base, kActivityCompletionEffectCounterPreRva12004, pre.patch_target) ||
      !Add(environment.module_base, kActivityCompletionEffectCounterCallRva12004, pre.continue_target) ||
      !Add(environment.module_base, kActivityCompletionEffectCounterPostRva12004, post.patch_target) ||
      !Add(environment.module_base, kActivityCompletionEffectCounterContinueRva12004, post.continue_target) ||
      !Equal(anchor, kActualAnchor.data(), kActualAnchor.size()) ||
      !CopyFrom(pre.patch_target, pre.original_patch.data(), pre.patch_bytes) ||
      !CopyFrom(post.patch_target, post.original_patch.data(), post.patch_bytes)) {
    Fail(state, activity_completion_effect_counter_failure_anchor);
    return false;
  }
  State *expected = nullptr;
  if (!g_active.compare_exchange_strong(expected, &state, std::memory_order_acq_rel)) {
    Fail(state, activity_completion_effect_counter_failure_already_owned);
    return false;
  }
  state.environment = environment;
  state.native_return_target = post.patch_target;
  state.callbacks_enabled.store(false, std::memory_order_relaxed);
  state.before_count.store(0, std::memory_order_relaxed);
  state.returned_count.store(0, std::memory_order_relaxed);
  state.bypass_post_count.store(0, std::memory_order_relaxed);
  state.uncorrelated_post_count.store(0, std::memory_order_relaxed);
  state.dropped_before_count.store(0, std::memory_order_relaxed);
  for (std::size_t index = 0; index != state.windows.size(); ++index) {
    auto &window = state.windows[index];
    std::uintptr_t jump_next = 0;
    if (!Add(window.patch_target, 5, jump_next)) {
      Fail(state, activity_completion_effect_counter_failure_anchor);
      FinishFailedInstall(state);
      return false;
    }
    window.stub = AllocateFixedNearStub(jump_next);
    if (window.stub == nullptr) {
      Fail(state, activity_completion_effect_counter_failure_near_allocation);
      FinishFailedInstall(state);
      return false;
    }
    Stub bytes{};
    window.stub_bytes = BuildStub(state, window, index == 1, bytes);
    DWORD previous = 0;
    const bool wrote = window.stub_bytes != 0 &&
        CopyTo(reinterpret_cast<std::uintptr_t>(window.stub), bytes.data(), bytes.size());
    const bool protected_stub = wrote && VirtualProtect(window.stub, bytes.size(), PAGE_EXECUTE_READ, &previous) != FALSE;
    if (!protected_stub || previous != PAGE_READWRITE || !Flush(window.stub, bytes.size())) {
      Fail(state, activity_completion_effect_counter_failure_stub);
      FinishFailedInstall(state);
      return false;
    }
    std::int32_t relative = 0;
    if (!Relative32(reinterpret_cast<std::uintptr_t>(window.stub), jump_next, relative)) {
      Fail(state, activity_completion_effect_counter_failure_near_allocation);
      FinishFailedInstall(state);
      return false;
    }
    window.installed_patch.fill(0x90);
    window.installed_patch[0] = 0xE9;
    std::memcpy(window.installed_patch.data() + 1, &relative, sizeof(relative));
  }
  // The post observer exists before any pre observer can begin a pair.
  for (const auto index : {std::size_t{1}, std::size_t{0}}) {
    auto &window = state.windows[index];
    const auto written = WritePatch(state, window, window.original_patch.data(), window.installed_patch.data());
    window.patch_owned_or_uncertain = written != WriteResult::original_preserved;
    if (written != WriteResult::success) {
      FinishFailedInstall(state);
      return false;
    }
  }
  state.installed.store(true, std::memory_order_release);
  state.callbacks_enabled.store(true, std::memory_order_release);
  return true;
}

bool UninstallActivityCompletionEffectCounterObserver12004(
    State &state, bool primary_thread_suspended_proven) noexcept {
  if (!primary_thread_suspended_proven) {
    Fail(state, activity_completion_effect_counter_failure_suspension);
    return false; // ordinary Stop retains both patches, state, and backing
  }
  if (!state.installed.load(std::memory_order_acquire) || g_active.load(std::memory_order_acquire) != &state) {
    Fail(state, activity_completion_effect_counter_failure_already_owned);
    return false;
  }
  state.callbacks_enabled.store(false, std::memory_order_release);
  bool restored = true;
  for (auto &window : state.windows) if (!RestoreWindow(state, window)) restored = false;
  if (!restored) return false;
  state.installed.store(false, std::memory_order_release);
  g_active.store(nullptr, std::memory_order_release);
  return ReleaseUnusedBacking(state);
}

ActivityCompletionEffectCounterObserver12004Diagnostics
ReadActivityCompletionEffectCounterObserver12004Diagnostics(const State &state) noexcept {
  ActivityCompletionEffectCounterObserver12004Diagnostics result{};
  result.installed = state.installed.load(std::memory_order_acquire);
  result.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  result.before_count = state.before_count.load(std::memory_order_relaxed);
  result.returned_count = state.returned_count.load(std::memory_order_relaxed);
  result.bypass_post_count = state.bypass_post_count.load(std::memory_order_relaxed);
  result.uncorrelated_post_count = state.uncorrelated_post_count.load(std::memory_order_relaxed);
  result.dropped_before_count = state.dropped_before_count.load(std::memory_order_relaxed);
  return result;
}

} // namespace xar::ck3_12004
