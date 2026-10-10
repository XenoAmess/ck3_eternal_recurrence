#include "xar_bridge/person_installed_transfer_capture_12004.hpp"

#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"

#include <algorithm>
#include <cstring>
#include <intrin.h>
#include <limits>
#include <mutex>

namespace xar::ck3_12004 {
namespace {
constexpr std::array<std::uint8_t, 15> kAnchor{
    0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x6C,0x24,0x18,
    0x48,0x89,0x74,0x24,0x20};
std::atomic<PersonInstalledTransferCaptureState12004 *> g_active_state{nullptr};
std::atomic<PersonInstalledTransferOriginal12004> g_original{nullptr};
std::atomic<std::uint32_t> g_in_flight{0};
std::atomic<bool> g_available{false};
PersonInstalledTransferBindings12004 g_bindings;
std::uintptr_t g_module_base = 0;
bool g_offline_fixture = false;
std::mutex g_records_mutex;
std::array<std::optional<PersonInstalledTransferCaptureRecord12004>,
           kPersonInstalledTransferCaptureCapacity12004> g_records;
std::uint64_t g_record_sequence = 0;

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

void Fail(PersonInstalledTransferCaptureState12004 &state,
          PersonInstalledTransferCaptureFailure12004 flag) noexcept {
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
  Jump(result.data(), reinterpret_cast<std::uintptr_t>(&XarPersonInstalledTransferHook12004V1));
  return result;
}
bool TargetEquals(const PersonInstalledTransferBindings12004 &bindings,
                  std::uintptr_t target,
                  const std::array<std::uint8_t, 15> &expected) noexcept {
  std::array<std::uint8_t, 15> actual{};
  return bindings.read && bindings.read(bindings.read_context, target,
      actual.data(), actual.size()) && actual == expected;
}
bool WritePatch(PersonInstalledTransferCaptureState12004 &state,
                const PersonInstalledTransferBindings12004 &bindings,
                const std::array<std::uint8_t, 15> &expected,
                const std::array<std::uint8_t, 15> &desired,
                bool *bytes_written = nullptr) noexcept {
  if (bytes_written) *bytes_written = false;
  if (!TargetEquals(bindings, state.target, expected)) {
    Fail(state, transfer_capture_anchor);
    return false;
  }
  DWORD previous = 0;
  if (!state.virtual_protect(state.memory_context,
      reinterpret_cast<void *>(state.target), desired.size(),
      PAGE_EXECUTE_READWRITE, previous)) {
    Fail(state, transfer_capture_protection);
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
  Fail(state, flushed ? transfer_capture_protection : transfer_capture_flush);
  return false;
}
PersonInstalledTransferEvent12004 Clock(void *) noexcept {
  return NextPersonNaturalLineageEvent12004();
}
PersonInstalledTransferPreparation12004 Preparation(
    void *, std::uintptr_t owner, std::uint32_t full_id) noexcept {
  const auto capture = ReadPersonSixStageCaptureForCharacter12004(owner, full_id);
  PersonInstalledTransferPreparation12004 out;
  out.observed = capture.capture_observed;
  out.preparation_capture_complete = capture.capture_complete;
  out.preparation_capture_sequence = capture.capture_sequence;
  out.preparation_capture_thread_id = capture.capture_thread_id;
  if (capture.capture_complete)
    out.preparation_completion_thread_id = capture.query_thread_id;
  out.preparation_character_identity = capture.character_identity;
  out.preparation_model_identity = capture.preparation_model.model_identity;
  out.preparation_context_identity = capture.context_identity;
  out.preparation_owner_character_identity = capture.preparation_model.owner_character_identity;
  out.preparation_owner_character_id = capture.preparation_model.owner_character_id;
  return out;
}
struct Flight {
  Flight() noexcept { g_in_flight.fetch_add(1, std::memory_order_acq_rel); }
  ~Flight() { g_in_flight.fetch_sub(1, std::memory_order_acq_rel); }
};
void Record(const PersonInstalledTransferStage12004 &stage) noexcept {
  if (!stage.observed || !stage.original_returned) return;
  try {
    const std::lock_guard lock(g_records_mutex);
    const auto sequence = ++g_record_sequence;
    g_records[(sequence - 1) % g_records.size()] =
        PersonInstalledTransferCaptureRecord12004{sequence, g_offline_fixture, stage};
  } catch (...) {
    // Auxiliary retention failure must not change the original return value.
  }
}
} // namespace

PersonInstalledTransferBindings12004 BindPersonInstalledTransferCaptureImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  PersonInstalledTransferBindings12004 bindings;
  if (module_base == 0 || executable_sha256 != kPersonInstalledTransferCaptureExeSha12004)
    return bindings;
  bindings.read = NativeRead;
  bindings.read_preparation = Preparation;
  bindings.next_event = Clock;
  return bindings;
}

bool InstallPersonInstalledTransferCapture12004(
    PersonInstalledTransferCaptureState12004 &state,
    const PersonInstalledTransferCaptureInstall12004 &environment,
    std::string_view executable_sha256) noexcept {
  state.failure_flags.store(transfer_capture_none, std::memory_order_relaxed);
  if (executable_sha256 != kPersonInstalledTransferCaptureExeSha12004 ||
      environment.module_base == 0 ||
      (!environment.offline_fixture && environment.target_override != 0) ||
      environment.module_base > std::numeric_limits<std::uintptr_t>::max() -
          kPersonInstalledTransferRva12004 - kAnchor.size()) {
    Fail(state, transfer_capture_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, transfer_capture_quiescence);
    return false;
  }
  if (!environment.bindings.read) {
    Fail(state, transfer_capture_memory_binding);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  if (state.trampoline != nullptr) {
    Fail(state, transfer_capture_allocation);
    return false;
  }
  PersonInstalledTransferCaptureState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                              std::memory_order_acq_rel)) {
    Fail(state, transfer_capture_already_installed);
    return false;
  }
  state.target_protection_known = false;
  state.original_target_protection = 0;
  state.target = environment.target_override != 0 ? environment.target_override :
      environment.module_base + kPersonInstalledTransferRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override ? environment.virtual_free_override : Free;
  state.virtual_protect = environment.virtual_protect_override ? environment.virtual_protect_override : Protect;
  state.flush = environment.flush_override ? environment.flush_override : Flush;
  const auto allocate = environment.virtual_alloc_override ? environment.virtual_alloc_override : Allocate;
  auto bindings = environment.bindings;
  if (!bindings.read_preparation) bindings.read_preparation = Preparation;
  // Production always uses the shared process clock. No private counter can
  // accidentally be supplied by a caller of this install API.
  if (!environment.offline_fixture || !bindings.next_event) {
    bindings.event_context = nullptr;
    bindings.next_event = Clock;
  }
  if (!TargetEquals(bindings, state.target, kAnchor)) {
    Fail(state, transfer_capture_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.trampoline = allocate(state.memory_context, 29,
                             MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
  if (!state.trampoline) {
    Fail(state, transfer_capture_allocation);
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
    g_original.store(reinterpret_cast<PersonInstalledTransferOriginal12004>(code),
                     std::memory_order_release);
    g_available.store(true, std::memory_order_release);
  } else {
    Fail(state, protected_code ? transfer_capture_flush : transfer_capture_protection);
  }
  bool target_written = false;
  const bool patched = flushed_code && WritePatch(state, bindings, kAnchor, Patch(), &target_written);
  if (!patched) {
    // WritePatch can fail after writing. Restore iff the hook bytes are present;
    // never free a trampoline while a surviving entry patch references it.
    if (target_written && !WritePatch(state, bindings, Patch(), kAnchor)) {
      Fail(state, transfer_capture_rollback);
      state.original = kAnchor;
      state.installed.store(1, std::memory_order_release);
      return false;
    }
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    if (!state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
      Fail(state, transfer_capture_allocation);
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

bool UninstallPersonInstalledTransferCapture12004(
    PersonInstalledTransferCaptureState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 && state.trampoline == nullptr)
    return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, transfer_capture_quiescence);
    return false;
  }
  const bool installed = state.installed.load(std::memory_order_acquire) != 0;
  if ((installed && g_active_state.load(std::memory_order_acquire) != &state) ||
      g_in_flight.load(std::memory_order_acquire) != 0) {
    Fail(state, transfer_capture_callback_active);
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
        Fail(state, transfer_capture_rollback);
      return false;
    }
  }
  state.installed.store(0, std::memory_order_release);
  g_available.store(false, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  g_active_state.store(nullptr, std::memory_order_release);
  // Immutable history deliberately survives uninstall. The clock also survives.
  if (!state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
    Fail(state, transfer_capture_allocation);
    return false;
  }
  state.trampoline = nullptr;
  return true;
}

std::uintptr_t InvokePersonInstalledTransferCapture12004(
    void *a, void *b, std::uintptr_t original_return_address) noexcept {
  Flight flight;
  const auto original = g_original.load(std::memory_order_acquire);
  if (!original) return 0;
  if (!g_available.load(std::memory_order_acquire)) return original(a, b);
  const auto return_rva = original_return_address >= g_module_base ?
      original_return_address - g_module_base : 0;
  auto invocation = InvokePersonInstalledTransferStage12004(
      g_bindings, original, a, b, return_rva);
  Record(invocation.stage);
  return invocation.raw_return_bits;
}

PersonInstalledTransferCaptureQuery12004 ReadPersonInstalledTransferCapture12004() {
  PersonInstalledTransferCaptureQuery12004 query;
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

PersonInstalledTransferCaptureQuery12004 CollectPersonInstalledTransferCaptureForOwners12004(
    const PersonSixStageQuery12004DTO &owners) {
  auto query = ReadPersonInstalledTransferCapture12004();
  query.request_filtered = true;
  query.snapshot_revision = owners.snapshot_revision;
  query.observed_date_raw = owners.observed_date_raw;
  query.requested_receiver_count = owners.character_captures.size();
  for (const auto &owner : owners.character_captures)
    if (!owner.character_identity || *owner.character_identity == 0 || !owner.character_id)
      ++query.unresolved_receiver_count;
  query.records.erase(std::remove_if(query.records.begin(), query.records.end(),
      [&](const auto &record) {
        return std::none_of(owners.character_captures.begin(), owners.character_captures.end(),
            [&](const auto &owner) {
              return owner.character_identity && *owner.character_identity != 0 && owner.character_id &&
                  record.stage.before.observed_owner_identity == *owner.character_identity &&
                  record.stage.before.observed_owner_character_id == *owner.character_id;
            });
      }), query.records.end());
  return query;
}

std::optional<PersonInstalledTransferCaptureRecord12004>
ReadPersonInstalledTransferCaptureForOwner12004(
    std::uintptr_t owner, std::uint32_t full_character_id) {
  const std::lock_guard lock(g_records_mutex);
  const auto count = static_cast<std::size_t>(
      g_record_sequence < g_records.size() ? g_record_sequence : g_records.size());
  for (std::size_t i = 0; i != count; ++i) {
    const auto &record = g_records[(g_record_sequence - 1 - i) % g_records.size()];
    if (record && owner != 0 &&
        record->stage.before.observed_owner_identity == owner &&
        record->stage.before.observed_owner_character_id == full_character_id)
      return record;
  }
  return std::nullopt;
}

extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarPersonInstalledTransferHook12004V1(void *a, void *b) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  return InvokePersonInstalledTransferCapture12004(a, b, caller);
}

} // namespace xar::ck3_12004
