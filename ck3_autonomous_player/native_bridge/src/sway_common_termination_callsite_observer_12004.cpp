#include "xar_bridge/sway_common_termination_callsite_observer_12004.hpp"

#include <windows.h>

#include <array>
#include <cstring>
#include <initializer_list>
#include <limits>

namespace xar::ck3_12004 {
namespace {

static_assert(sizeof(void *) == 8, "The fixed Sway common callsite is x64-only");
using State = SwayCommonTerminationCallsiteObserver12004State;
using Stub = std::array<std::uint8_t, kSwayCommonTerminationObserverStubCapacity12004>;
std::atomic<State *> g_active{nullptr};

// Actual12004 parent2A48660, instructions520..540. The preceding2A4F100
// CALL is only checked; all15 preceding bytes stay in place. Only the final
// five-byte CALL2A4ADF0 is replaced by a near JMP to the owned stub.
constexpr std::array<std::uint8_t, 20> kActualAnchor{
    0x48, 0x8B, 0xCF, 0xE8, 0x90, 0x68, 0x00, 0x00,
    0x40, 0x0F, 0xB6, 0xD6, 0x48, 0x8B, 0xCF,
    0xE8, 0x74, 0x25, 0x00, 0x00};

void Fail(State &state, SwayCommonTerminationCallsiteObserverFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(static_cast<std::uint32_t>(flag), std::memory_order_acq_rel);
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

// This allocation is specific to the one five-byte fixed JMP. Walk only its
// signed-rel32 address window; skip occupied regions rather than probing every
// page or changing the15 surrounding source instructions.
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
          kSwayCommonTerminationObserverStubCapacity12004 <= end - candidate &&
          Relative32(candidate, next_pc, relative)) {
        auto *allocated = VirtualAlloc(reinterpret_cast<void *>(candidate),
            kSwayCommonTerminationObserverStubCapacity12004, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
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

void Emit(Stub &code, std::size_t &cursor, std::initializer_list<std::uint8_t> bytes) noexcept {
  for (const auto value : bytes) code[cursor++] = value;
}

void U64(Stub &code, std::size_t &cursor, std::uintptr_t value) noexcept {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(code.data() + cursor, &encoded, sizeof(encoded));
  cursor += sizeof(encoded);
}

void Preserve(Stub &code, std::size_t &cursor) noexcept {
  // Eight pushes =64B. At the actual CALL boundary RSP is16-aligned. Keep
  // that alignment and reserve32B shadow plus96B for volatile XMM0..5.
  Emit(code, cursor, {0x9C, 0x50, 0x51, 0x52, 0x41, 0x50, 0x41, 0x51, 0x41, 0x52, 0x41, 0x53});
  Emit(code, cursor, {0x48, 0x81, 0xEC, 0x80, 0x00, 0x00, 0x00});
  for (std::uint8_t reg = 0; reg != 6; ++reg)
    Emit(code, cursor, {0xF3, 0x0F, 0x7F, static_cast<std::uint8_t>(0x44 + 8 * reg), 0x24,
                        static_cast<std::uint8_t>(0x20 + 0x10 * reg)});
}

void Restore(Stub &code, std::size_t &cursor) noexcept {
  for (std::uint8_t reg = 0; reg != 6; ++reg)
    Emit(code, cursor, {0xF3, 0x0F, 0x6F, static_cast<std::uint8_t>(0x44 + 8 * reg), 0x24,
                        static_cast<std::uint8_t>(0x20 + 0x10 * reg)});
  Emit(code, cursor, {0x48, 0x81, 0xC4, 0x80, 0x00, 0x00, 0x00});
  Emit(code, cursor, {0x41, 0x5B, 0x41, 0x5A, 0x41, 0x59, 0x41, 0x58, 0x5A, 0x59, 0x58, 0x9D});
}

extern "C" void SwayCommonTerminationBeforeThunk12004(
    void *context, std::uintptr_t rcx, std::uint64_t rdx) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state == nullptr) return;
  state->before_count.fetch_add(1, std::memory_order_relaxed);
  if (state->environment.before != nullptr) state->environment.before(context, rcx, rdx);
}

extern "C" void SwayCommonTerminationAfterThunk12004(
    void *context, std::uint64_t rax) noexcept {
  auto *state = g_active.load(std::memory_order_acquire);
  if (state == nullptr) return;
  state->returned_count.fetch_add(1, std::memory_order_relaxed);
  if (state->environment.after != nullptr) state->environment.after(context, rax);
}

std::size_t BuildStub(State &state, Stub &code) noexcept {
  code.fill(0x90);
  std::size_t cursor = 0;
  Preserve(code, cursor);
  Emit(code, cursor, {0x4C, 0x8B, 0xC2}); // R8=actual incoming RDX, all64 bits
  Emit(code, cursor, {0x48, 0x8B, 0xD1}); // RDX=actual incoming RCX
  Emit(code, cursor, {0x48, 0xB9});
  U64(code, cursor, reinterpret_cast<std::uintptr_t>(state.environment.callback_context));
  Emit(code, cursor, {0x48, 0xB8});
  U64(code, cursor, reinterpret_cast<std::uintptr_t>(&SwayCommonTerminationBeforeThunk12004));
  Emit(code, cursor, {0xFF, 0xD0});
  Restore(code, cursor);

  // Exactly one relocated native CALL, with no MOV into an argument or RAX:
  // call qword ptr [rip+2]; jmp+8; dq actual2A4ADF0.
  Emit(code, cursor, {0xFF, 0x15, 0x02, 0x00, 0x00, 0x00, 0xEB, 0x08});
  U64(code, cursor, state.native_target);

  Preserve(code, cursor);
  // Saved native RAX is192-16=176 (B0) bytes above this callback RSP.
  Emit(code, cursor, {0x48, 0x8B, 0x94, 0x24, 0xB0, 0x00, 0x00, 0x00});
  Emit(code, cursor, {0x48, 0xB9});
  U64(code, cursor, reinterpret_cast<std::uintptr_t>(state.environment.callback_context));
  Emit(code, cursor, {0x48, 0xB8});
  U64(code, cursor, reinterpret_cast<std::uintptr_t>(&SwayCommonTerminationAfterThunk12004));
  Emit(code, cursor, {0xFF, 0xD0});
  Restore(code, cursor);
  Emit(code, cursor, {0xFF, 0x25, 0x00, 0x00, 0x00, 0x00});
  U64(code, cursor, state.continue_target);
  return cursor <= code.size() ? cursor : 0;
}

enum class WriteResult { success, original_preserved, restore_unproven };

WriteResult WritePatch(State &state, const std::uint8_t *expected,
                      const std::uint8_t *desired) noexcept {
  constexpr auto size = kSwayCommonTerminationObserverPatchBytes12004;
  if (!Equal(state.patch_target, expected, size)) {
    Fail(state, sway_common_observer_failure_target_identity);
    return WriteResult::original_preserved;
  }
  DWORD previous = 0;
  auto *target = reinterpret_cast<void *>(state.patch_target);
  const bool writable = VirtualProtect(target, size, PAGE_EXECUTE_READWRITE, &previous) != FALSE;
  if (!writable || !Executable(previous)) {
    if (writable) { DWORD ignored = 0; (void)VirtualProtect(target, size, previous, &ignored); }
    Fail(state, sway_common_observer_failure_target_protection);
    return WriteResult::original_preserved;
  }
  const bool wrote = CopyTo(state.patch_target, desired, size);
  const bool identity = wrote && Equal(state.patch_target, desired, size);
  const bool flushed = identity && Flush(target, size);
  DWORD ignored = 0;
  const bool protected_again = VirtualProtect(target, size, previous, &ignored) != FALSE;
  if (identity && flushed && protected_again) return WriteResult::success;
  if (!flushed) Fail(state, sway_common_observer_failure_flush);
  if (!protected_again) Fail(state, sway_common_observer_failure_target_protection);

  DWORD rollback_previous = 0;
  const bool rollback_writable = VirtualProtect(target, size, PAGE_EXECUTE_READWRITE, &rollback_previous) != FALSE;
  const bool restored = rollback_writable && CopyTo(state.patch_target, expected, size) && Equal(state.patch_target, expected, size);
  const bool restore_flushed = restored && Flush(target, size);
  DWORD rollback_ignored = 0;
  const bool restore_protected = rollback_writable && VirtualProtect(target, size, previous, &rollback_ignored) != FALSE;
  if (!restored || !restore_flushed || !restore_protected) {
    Fail(state, sway_common_observer_failure_restore);
    return WriteResult::restore_unproven;
  }
  return WriteResult::original_preserved;
}

bool ReleaseUnusedBacking(State &state) noexcept {
  if (state.stub != nullptr && VirtualFree(state.stub, 0, MEM_RELEASE) == FALSE) {
    Fail(state, sway_common_observer_failure_restore);
    return false;
  }
  state.stub = nullptr;
  state.stub_bytes = 0;
  state.patch_target = 0;
  state.native_target = 0;
  state.continue_target = 0;
  state.environment = {};
  return true;
}

} // namespace

bool InstallSwayCommonTerminationCallsiteObserver12004(
    State &state, const SwayCommonTerminationCallsiteObserver12004Environment &environment) noexcept {
  if (state.installed.load(std::memory_order_acquire) || state.stub != nullptr) {
    Fail(state, sway_common_observer_failure_already_owned);
    return false;
  }
  state.failure_flags.store(0, std::memory_order_relaxed);
  if (!environment.exact_12004_build_admitted || environment.module_base == 0) {
    Fail(state, sway_common_observer_failure_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, sway_common_observer_failure_suspension);
    return false;
  }
  if (environment.before == nullptr || environment.after == nullptr) {
    Fail(state, sway_common_observer_failure_callbacks);
    return false;
  }
  std::uintptr_t anchor = 0;
  if (!Add(environment.module_base, kSwayCommonTerminationObserverAnchorRva12004, anchor) ||
      !Add(environment.module_base, kSwayCommonTerminationObserverCallRva12004, state.patch_target) ||
      !Add(environment.module_base, kSwayCommonTerminationObserverCalleeRva12004, state.native_target) ||
      !Add(environment.module_base, kSwayCommonTerminationObserverContinueRva12004, state.continue_target) ||
      !Equal(anchor, kActualAnchor.data(), kActualAnchor.size()) ||
      !CopyFrom(state.patch_target, state.original_patch.data(), state.original_patch.size())) {
    Fail(state, sway_common_observer_failure_anchor);
    return false;
  }
  State *expected = nullptr;
  if (!g_active.compare_exchange_strong(expected, &state, std::memory_order_acq_rel)) {
    Fail(state, sway_common_observer_failure_already_owned);
    return false;
  }
  state.environment = environment;
  state.before_count.store(0, std::memory_order_relaxed);
  state.returned_count.store(0, std::memory_order_relaxed);
  state.stub = AllocateFixedNearStub(state.continue_target);
  if (state.stub == nullptr) {
    Fail(state, sway_common_observer_failure_near_allocation);
    (void)ReleaseUnusedBacking(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  Stub bytes{};
  state.stub_bytes = BuildStub(state, bytes);
  DWORD previous = 0;
  const bool wrote = state.stub_bytes != 0 && CopyTo(reinterpret_cast<std::uintptr_t>(state.stub), bytes.data(), bytes.size());
  const bool protected_stub = wrote && VirtualProtect(state.stub, bytes.size(), PAGE_EXECUTE_READ, &previous) != FALSE;
  if (!protected_stub || previous != PAGE_READWRITE || !Flush(state.stub, bytes.size())) {
    Fail(state, sway_common_observer_failure_stub);
    (void)ReleaseUnusedBacking(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  std::int32_t relative = 0;
  if (!Relative32(reinterpret_cast<std::uintptr_t>(state.stub), state.continue_target, relative)) {
    Fail(state, sway_common_observer_failure_near_allocation);
    (void)ReleaseUnusedBacking(state);
    g_active.store(nullptr, std::memory_order_release);
    return false;
  }
  state.installed_patch[0] = 0xE9;
  std::memcpy(state.installed_patch.data() + 1, &relative, sizeof(relative));
  const auto written = WritePatch(state, state.original_patch.data(), state.installed_patch.data());
  if (written == WriteResult::success) {
    state.installed.store(true, std::memory_order_release);
    return true;
  }
  if (written == WriteResult::restore_unproven) {
    state.installed.store(true, std::memory_order_release);
    return false; // Retain backing/ownership for an uncertain installed patch.
  }
  (void)ReleaseUnusedBacking(state);
  g_active.store(nullptr, std::memory_order_release);
  return false;
}

bool UninstallSwayCommonTerminationCallsiteObserver12004(
    State &state, bool primary_thread_suspended_proven) noexcept {
  if (!primary_thread_suspended_proven) {
    Fail(state, sway_common_observer_failure_suspension);
    return false;
  }
  if (!state.installed.load(std::memory_order_acquire) || g_active.load(std::memory_order_acquire) != &state) {
    Fail(state, sway_common_observer_failure_already_owned);
    return false;
  }
  const auto restored = WritePatch(state, state.installed_patch.data(), state.original_patch.data());
  if (restored != WriteResult::success) {
    Fail(state, sway_common_observer_failure_restore);
    return false;
  }
  state.installed.store(false, std::memory_order_release);
  g_active.store(nullptr, std::memory_order_release);
  return ReleaseUnusedBacking(state);
}

SwayCommonTerminationCallsiteObserver12004Diagnostics
ReadSwayCommonTerminationCallsiteObserver12004Diagnostics(const State &state) noexcept {
  SwayCommonTerminationCallsiteObserver12004Diagnostics result{};
  result.installed = state.installed.load(std::memory_order_acquire);
  result.failure_flags = state.failure_flags.load(std::memory_order_acquire);
  result.before_count = state.before_count.load(std::memory_order_relaxed);
  result.returned_count = state.returned_count.load(std::memory_order_relaxed);
  return result;
}

} // namespace xar::ck3_12004
