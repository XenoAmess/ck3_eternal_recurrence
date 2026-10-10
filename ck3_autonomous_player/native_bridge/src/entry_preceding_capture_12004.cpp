#include "xar_bridge/entry_preceding_capture_12004.hpp"


#include <algorithm>
#include <cstring>
#include <intrin.h>
#include <limits>
#include <mutex>

namespace xar::ck3_12004 {
namespace {
constexpr std::array<std::uint8_t, 15> kAnchor{
    0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x6C,0x24,0x10,
    0x48,0x89,0x74,0x24,0x18};
std::atomic<EntryPrecedingState12004 *> g_active_state{nullptr};
std::atomic<EntryPrecedingOriginal12004> g_original{nullptr};
std::atomic<std::uint32_t> g_in_flight{0};
std::atomic<bool> g_available{false};
EntryPrecedingBindings12004 g_bindings;
std::uintptr_t g_module_base = 0;
bool g_offline_fixture = false;
std::mutex g_records_mutex;
std::array<std::optional<EntryPrecedingRecord12004>,
           kEntryPrecedingCapacity12004> g_records;
std::uint64_t g_record_sequence = 0;
std::atomic<std::uint64_t> g_install_epoch{0};
thread_local std::optional<EntryPrecedingRecord12004> g_completion;
thread_local bool g_side0_claimed = false;

template <class Callback>
bool FaultBoundary(Callback callback) noexcept {
  __try { return callback(); }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
bool NativeRead(void *, std::uintptr_t address, void *output,
                std::size_t bytes) noexcept {
  if (address == 0 || !output ||
      address > std::numeric_limits<std::uintptr_t>::max() - bytes)
    return false;
  return FaultBoundary([&]() noexcept {
    std::memcpy(output, reinterpret_cast<const void *>(address), bytes);
    return true;
  });
}

void Fail(EntryPrecedingState12004 &state,
          EntryPrecedingFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_relaxed);
}
void *Allocate(void *, std::size_t bytes, DWORD type, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, bytes, type, protection);
}
bool Free(void *, void *address, std::size_t bytes, DWORD type) noexcept {
  return VirtualFree(address, bytes, type) != FALSE;
}
bool Protect(void *, void *address, std::size_t bytes, DWORD protection,
             DWORD &previous) noexcept {
  return VirtualProtect(address, bytes, protection, &previous) != FALSE;
}
bool Flush(void *, const void *address, std::size_t bytes) noexcept {
  return FlushInstructionCache(GetCurrentProcess(), address, bytes) != FALSE;
}
void Jump(std::uint8_t *output, std::uintptr_t target) noexcept {
  constexpr std::array<std::uint8_t, 6> prefix{0xFF,0x25,0,0,0,0};
  std::memcpy(output, prefix.data(), prefix.size());
  std::memcpy(output + prefix.size(), &target, sizeof(target));
}
std::array<std::uint8_t, 15> Patch() noexcept {
  std::array<std::uint8_t, 15> result;
  result.fill(0x90);
  Jump(result.data(), reinterpret_cast<std::uintptr_t>(&XarEntryPrecedingHook12004V1));
  return result;
}
bool TargetEquals(const EntryPrecedingBindings12004 &bindings,
                  std::uintptr_t target,
                  const std::array<std::uint8_t, 15> &expected) noexcept {
  std::array<std::uint8_t, 15> actual{};
  return bindings.read && bindings.read(bindings.read_context, target,
      actual.data(), actual.size()) && actual == expected;
}
bool WritePatch(EntryPrecedingState12004 &state,
                const EntryPrecedingBindings12004 &bindings,
                const std::array<std::uint8_t, 15> &expected,
                const std::array<std::uint8_t, 15> &desired,
                bool *bytes_written = nullptr) noexcept {
  if (bytes_written) *bytes_written = false;
  if (!TargetEquals(bindings, state.target, expected)) {
    Fail(state, preceding_anchor);
    return false;
  }
  DWORD previous = 0;
  if (!state.virtual_protect(state.memory_context,
      reinterpret_cast<void *>(state.target), desired.size(),
      PAGE_EXECUTE_READWRITE, previous)) {
    Fail(state, preceding_protection);
    return false;
  }
  if (!state.target_protection_known) {
    state.original_target_protection = previous;
    state.target_protection_known = true;
  }
  std::memcpy(reinterpret_cast<void *>(state.target), desired.data(), desired.size());
  if (bytes_written) *bytes_written = true;
  const bool flushed = state.flush(state.memory_context,
      reinterpret_cast<void *>(state.target), desired.size());
  DWORD ignored = 0;
  const bool restored = state.virtual_protect(state.memory_context,
      reinterpret_cast<void *>(state.target), desired.size(),
      state.original_target_protection, ignored);
  if (flushed && restored) return true;
  Fail(state, flushed ? preceding_protection : preceding_flush);
  return false;
}
PersonInstalledTransferEvent12004 Clock(void *) noexcept {
  return NextPersonNaturalLineageEvent12004();
}
std::optional<std::uint32_t> CombatIdentity(std::uintptr_t combat) noexcept {
  if (combat == 0 || combat > std::numeric_limits<std::uintptr_t>::max() - 0x10)
    return std::nullopt;
  std::uint32_t magic = 0, id = 0;
  if (!g_bindings.read(g_bindings.read_context, combat + 0x0C, &magic, sizeof(magic)) ||
      magic != 0x436F6D62U ||
      !g_bindings.read(g_bindings.read_context, combat + 0x08, &id, sizeof(id)) ||
      id == 0xFFFFFFFFU) return std::nullopt;
  return id;
}
bool OrderedEvents(const PersonInstalledTransferEvent12004 &a,
                   const PersonInstalledTransferEvent12004 &b) noexcept {
  return a.clock_identity != 0 && a.clock_identity == b.clock_identity &&
      a.thread_id && b.thread_id && *a.thread_id != 0U && a.thread_id == b.thread_id &&
      a.sequence != 0 && b.sequence > a.sequence;
}
struct Flight {
  Flight() noexcept { g_in_flight.fetch_add(1, std::memory_order_acq_rel); }
  ~Flight() { g_in_flight.fetch_sub(1, std::memory_order_acq_rel); }
};
void Record(EntryPrecedingRecord12004 &record) noexcept {
  try {
    const std::lock_guard lock(g_records_mutex);
    record.record_sequence = ++g_record_sequence;
    g_records[(record.record_sequence - 1) % g_records.size()] = record;
  } catch (...) {
    // Observation retention never changes original return bits.
  }
}
} // namespace

EntryPrecedingBindings12004 BindEntryPrecedingCaptureImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  EntryPrecedingBindings12004 bindings;
  if (module_base == 0 || executable_sha256 != kEntryPrecedingExeSha12004)
    return bindings;
  bindings.read = NativeRead;
  bindings.next_event = Clock;
  return bindings;
}

bool InstallEntryPrecedingCapture12004(
    EntryPrecedingState12004 &state,
    const EntryPrecedingInstall12004 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(preceding_none, std::memory_order_relaxed);
  if (executable_sha256 != kEntryPrecedingExeSha12004 ||
      environment.module_base == 0 ||
      (!environment.offline_fixture && environment.target_override != 0) ||
      environment.module_base > std::numeric_limits<std::uintptr_t>::max() -
          kEntryPrecedingRva12004 - kAnchor.size()) {
    Fail(state, preceding_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, preceding_quiescence);
    return false;
  }
  if (!environment.bindings.read) {
    Fail(state, preceding_memory_binding);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  if (state.trampoline != nullptr) {
    Fail(state, preceding_allocation);
    return false;
  }
  EntryPrecedingState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                              std::memory_order_acq_rel)) {
    Fail(state, preceding_already_installed);
    return false;
  }
  state.target_protection_known = false;
  state.original_target_protection = 0;
  state.target = environment.target_override != 0 ? environment.target_override :
      environment.module_base + kEntryPrecedingRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override ? environment.virtual_free_override : Free;
  state.virtual_protect = environment.virtual_protect_override ? environment.virtual_protect_override : Protect;
  state.flush = environment.flush_override ? environment.flush_override : Flush;
  const auto allocate = environment.virtual_alloc_override ? environment.virtual_alloc_override : Allocate;
  auto bindings = environment.bindings;
  // Production always uses the shared process clock. No private counter can
  // accidentally be supplied by a caller of this install API.
  if (!environment.offline_fixture || !bindings.next_event) {
    bindings.event_context = nullptr;
    bindings.next_event = Clock;
  }
  if (!TargetEquals(bindings, state.target, kAnchor)) {
    Fail(state, preceding_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.trampoline = allocate(state.memory_context, 29,
                             MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
  if (!state.trampoline) {
    Fail(state, preceding_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *code = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(code, kAnchor.data(), kAnchor.size());
  Jump(code + kAnchor.size(), state.target + kAnchor.size());
  DWORD previous = 0;
  const bool protected_code = state.virtual_protect(state.memory_context,
      code, 29, PAGE_EXECUTE_READ, previous);
  const bool flushed_code = protected_code && state.flush(state.memory_context, code, 29);
  if (flushed_code) {
    g_bindings = bindings;
    g_module_base = environment.module_base;
    g_offline_fixture = environment.offline_fixture;
    g_original.store(reinterpret_cast<EntryPrecedingOriginal12004>(code),
                     std::memory_order_release);
    g_install_epoch.fetch_add(1, std::memory_order_acq_rel);
    g_available.store(true, std::memory_order_release);
  } else {
    Fail(state, protected_code ? preceding_flush : preceding_protection);
  }
  bool target_written = false;
  const bool patched = flushed_code && WritePatch(state, bindings, kAnchor, Patch(), &target_written);
  if (!patched) {
    // WritePatch can fail after writing. Restore iff the hook bytes are present;
    // never free a trampoline while a surviving entry patch references it.
    if (target_written && !WritePatch(state, bindings, Patch(), kAnchor)) {
      Fail(state, preceding_rollback);
      state.original = kAnchor;
      state.installed.store(1, std::memory_order_release);
      return false;
    }
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    if (!state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
      Fail(state, preceding_allocation);
      // Retain allocation pointer for Root's explicit later disposal.
    } else {
      state.trampoline = nullptr;
    }
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.original = kAnchor;
  state.installed.store(1, std::memory_order_release);
  return true;
}

bool UninstallEntryPrecedingCapture12004(
    EntryPrecedingState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 && state.trampoline == nullptr)
    return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, preceding_quiescence);
    return false;
  }
  const bool installed = state.installed.load(std::memory_order_acquire) != 0;
  if (!installed) {
    // A previously detached state may retain only its failed-free allocation.
    // Another state may now own the hook globals; dispose this allocation alone.
    if (!state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
      Fail(state, preceding_allocation);
      return false;
    }
    state.trampoline = nullptr;
    return true;
  }
  if ((installed && g_active_state.load(std::memory_order_acquire) != &state) ||
      g_in_flight.load(std::memory_order_acquire) != 0) {
    Fail(state, preceding_callback_active);
    return false;
  }
  if (installed) {
    // A prior rollback can leave the restored original bytes with an unproven
    // flush. Revalidate that exact state, then repeat only the required flush/
    // protection transaction before releasing its retained backing.
    const auto expected = TargetEquals(g_bindings, state.target, Patch()) ?
        Patch() : state.original;
    bool bytes_written = false;
    if (!WritePatch(state, g_bindings, expected, state.original, &bytes_written)) {
      if (bytes_written && expected == Patch() &&
          !WritePatch(state, g_bindings, state.original, Patch()))
        Fail(state, preceding_rollback);
      return false;
    }
  }
  state.installed.store(0, std::memory_order_release);
  g_available.store(false, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  g_active_state.store(nullptr, std::memory_order_release);
  // Immutable history deliberately survives uninstall. The clock also survives.
  if (!state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
    Fail(state, preceding_allocation);
    return false;
  }
  state.trampoline = nullptr;
  return true;
}

std::uintptr_t InvokeEntryPrecedingCapture12004(
    void *combat, std::uintptr_t original_return_address,
    std::uintptr_t original_return_slot) noexcept {
  Flight flight;
  const auto original = g_original.load(std::memory_order_acquire);
  if (!original) return 0;
  g_completion.reset();
  g_side0_claimed = false;
  if (!g_available.load(std::memory_order_acquire)) return original(combat);
  EntryPrecedingRecord12004 record;
  record.install_epoch = g_install_epoch.load(std::memory_order_acquire);
  record.offline_fixture = g_offline_fixture;
  record.combat_identity = reinterpret_cast<std::uintptr_t>(combat);
  record.caller_return_rva = original_return_address >= g_module_base ?
      original_return_address - g_module_base : 0;
  record.caller_return_slot = original_return_slot;
  record.combat_full_id_before = CombatIdentity(record.combat_identity);
  record.original_begin = g_bindings.next_event(g_bindings.event_context);
  const auto raw = original(combat); // Sole original execution.
  record.original_returned = true;
  record.raw_return_bits = raw;
  record.original_completion = g_bindings.next_event(g_bindings.event_context);
  record.combat_full_id_after = CombatIdentity(record.combat_identity);
  record.identity_stable = record.combat_full_id_before && record.combat_full_id_after &&
      record.combat_full_id_before == record.combat_full_id_after;
  Record(record);
  if (record.caller_return_rva == kEntryPrecedingReturnRva12004 &&
      record.caller_return_slot != 0 && record.identity_stable &&
      OrderedEvents(record.original_begin, record.original_completion) &&
      record.original_completion.thread_id == GetCurrentThreadId())
    g_completion = record;
  return raw;
}

std::optional<EntryPrecedingRecord12004>
ReadCurrentEntryPrecedingCompletion12004() noexcept {
  if (!g_available.load(std::memory_order_acquire) || !g_completion ||
      g_completion->install_epoch != g_install_epoch.load(std::memory_order_acquire) ||
      g_completion->original_completion.thread_id != GetCurrentThreadId())
    return std::nullopt;
  return g_completion;
}

std::optional<EntryPrecedingRecord12004> ClaimEntryPrecedingForFinalSide12004(
    std::uint32_t side_index, std::uintptr_t actual_side,
    std::uintptr_t actual_return_rva, std::uintptr_t actual_return_slot,
    const PersonInstalledTransferEvent12004 &side_begin) noexcept {
  auto record = ReadCurrentEntryPrecedingCompletion12004();
  const auto invalidate = []() noexcept {
    g_completion.reset(); g_side0_claimed = false;
    return std::optional<EntryPrecedingRecord12004>{};
  };
  if (!record || side_index > 1 || !actual_return_slot ||
      actual_return_slot != record->caller_return_slot ||
      actual_return_rva != (side_index == 0 ? 0x247AB17U : 0x247AB26U) ||
      record->combat_identity > std::numeric_limits<std::uintptr_t>::max() - 0x368 ||
      actual_side != record->combat_identity + (side_index == 0 ? 0x20U : 0x368U) ||
      !OrderedEvents(record->original_completion, side_begin) ||
      side_begin.thread_id != GetCurrentThreadId() ||
      (side_index == 0 ? g_side0_claimed : !g_side0_claimed)) return invalidate();
  // The same full identity must still be present at this exact natural Side.
  if (CombatIdentity(record->combat_identity) != record->combat_full_id_after)
    return invalidate();
  if (side_index == 0) g_side0_claimed = true;
  else { g_completion.reset(); g_side0_claimed = false; }
  return record;
}

EntryPrecedingQuery12004 ReadEntryPrecedingCapture12004() {
  EntryPrecedingQuery12004 query;
  query.configured = g_available.load(std::memory_order_acquire);
  const auto *state = g_active_state.load(std::memory_order_acquire);
  query.installed = state && state->installed.load(std::memory_order_acquire) != 0;
  if (state) query.install_failure_flags = state->failure_flags.load(std::memory_order_relaxed);
  const std::lock_guard lock(g_records_mutex);
  query.latest_record_sequence = g_record_sequence;
  query.overwritten_records = g_record_sequence > g_records.size() ?
      g_record_sequence - g_records.size() : 0;
  const auto count = static_cast<std::size_t>(
      g_record_sequence < g_records.size() ? g_record_sequence : g_records.size());
  query.records.reserve(count);
  const auto first = g_record_sequence - count;
  for (std::size_t i = 0; i != count; ++i) {
    const auto &record = g_records[(first + i) % g_records.size()];
    if (record) query.records.push_back(*record);
  }
  return query;
}

EntryPrecedingQuery12004 CollectEntryPrecedingCaptureForCombats12004(
    std::span<const EntryPrecedingCombatOwner12004> owners) {
  auto query = ReadEntryPrecedingCapture12004();
  query.request_filtered = true;
  query.records.erase(std::remove_if(query.records.begin(), query.records.end(),
      [&](const auto &record) {
        return std::none_of(owners.begin(), owners.end(), [&](const auto &owner) {
          return owner.combat_identity != 0 && owner.full_combat_id != 0xFFFFFFFFU &&
              record.combat_identity == owner.combat_identity &&
              record.combat_full_id_before == owner.full_combat_id;
        });
      }), query.records.end());
  return query;
}

extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarEntryPrecedingHook12004V1(void *combat) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto slot = reinterpret_cast<std::uintptr_t>(_AddressOfReturnAddress());
  return InvokeEntryPrecedingCapture12004(combat, caller, slot);
}

} // namespace xar::ck3_12004
