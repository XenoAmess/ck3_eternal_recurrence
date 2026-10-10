#include "xar_bridge/entry_final_side_capture_12004.hpp"
#include "xar_bridge/person_natural_lineage_clock_12004.hpp"


#include <algorithm>
#include <cstring>
#include <intrin.h>
#include <limits>
#include <mutex>

namespace xar::ck3_12004 {
namespace {
constexpr auto kAnchor = kEntryFinalSidePrologue12004;
std::atomic<EntryFinalSideCaptureState12004 *> g_active_state{nullptr};
std::atomic<EntryFinalSideCaptureOriginal12004> g_original{nullptr};
std::atomic<std::uint32_t> g_in_flight{0};
std::atomic<bool> g_available{false};
EntryFinalSideCaptureBindings12004 g_bindings;
std::uintptr_t g_module_base = 0;
bool g_offline_fixture = false;
std::mutex g_records_mutex;
std::array<std::optional<EntryFinalSideCaptureRecord12004>,
           kEntryFinalSideCaptureCapacity12004> g_records;
std::uint64_t g_record_sequence = 0;
std::atomic<std::uint64_t> g_install_epoch{0};
thread_local const EntryFinalSideScope12004 *g_side_scope = nullptr;
thread_local const EntryFinalSideWriterScope12004 *g_writer_scope = nullptr;
thread_local EntryFinalSideCaptureRecord12004 *g_side_record = nullptr;
std::atomic<std::uint32_t> g_last_failure_flags{0};
std::atomic<std::uint64_t> g_capture_retention_failures{0};

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

void Fail(EntryFinalSideCaptureState12004 &state,
          EntryFinalSideCaptureFailure12004 flag) noexcept {
  state.failure_flags.fetch_or(flag, std::memory_order_relaxed);
  g_last_failure_flags.fetch_or(flag, std::memory_order_relaxed);
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
std::array<std::uint8_t, 20> Patch() noexcept {
  std::array<std::uint8_t, 20> result;
  result.fill(0x90);
  Jump(result.data(), reinterpret_cast<std::uintptr_t>(&XarEntryFinalSideCaptureHook12004V1));
  return result;
}
bool TargetEquals(const EntryFinalSideCaptureBindings12004 &bindings,
                  std::uintptr_t target,
                  const std::array<std::uint8_t, 20> &expected) noexcept {
  std::array<std::uint8_t, 20> actual{};
  return bindings.read && bindings.read(bindings.read_context, target,
      actual.data(), actual.size()) && actual == expected;
}
bool WritePatch(EntryFinalSideCaptureState12004 &state,
                const EntryFinalSideCaptureBindings12004 &bindings,
                const std::array<std::uint8_t, 20> &expected,
                const std::array<std::uint8_t, 20> &desired,
                bool *bytes_written = nullptr) noexcept {
  if (bytes_written) *bytes_written = false;
  if (!TargetEquals(bindings, state.target, expected)) {
    Fail(state, side_capture_anchor);
    return false;
  }
  DWORD previous = 0;
  if (!state.virtual_protect(state.memory_context,
      reinterpret_cast<void *>(state.target), desired.size(),
      PAGE_EXECUTE_READWRITE, previous)) {
    Fail(state, side_capture_protection);
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
  Fail(state, flushed ? side_capture_protection : side_capture_flush);
  return false;
}
PersonInstalledTransferEvent12004 Clock(void *) noexcept {
  return NextPersonNaturalLineageEvent12004();
}

struct Flight {
  Flight() noexcept { g_in_flight.fetch_add(1, std::memory_order_acq_rel); }
  ~Flight() { g_in_flight.fetch_sub(1, std::memory_order_acq_rel); }
};
struct ActiveSide {
  const EntryFinalSideScope12004 *previous_scope = g_side_scope;
  const EntryFinalSideWriterScope12004 *previous_writer = g_writer_scope;
  EntryFinalSideCaptureRecord12004 *previous_record = g_side_record;
  explicit ActiveSide(EntryFinalSideCaptureRecord12004 &record) noexcept {
    g_side_scope = &record.scope;
    g_side_record = &record;
    g_writer_scope = nullptr;
  }
  ~ActiveSide() {
    g_side_scope = previous_scope;
    g_side_record = previous_record;
    g_writer_scope = previous_writer;
  }
};
template <typename T>
std::optional<T> Copy(std::uintptr_t address) {
  T value{};
  if (!g_bindings.read(g_bindings.read_context, address, &value, sizeof(value)))
    return std::nullopt;
  return value;
}
bool CopyBucket(EntryFinalSideScope12004 &scope,
                EntryFinalSideBucketHeader12004 &header,
                EntryFinalSideBucket12004 bucket, std::size_t offset,
                std::uintptr_t writer_return_rva) {
  const auto side = scope.identity.side_identity;
  if (side == 0 || side > std::numeric_limits<std::uintptr_t>::max() - offset - 0x10)
    return false;
  header.data_identity = Copy<std::uintptr_t>(side + offset);
  header.count_i32 = Copy<std::int32_t>(side + offset + 0xC);
  if (!header.count_i32 || *header.count_i32 < 0)
    return false;
  if (*header.count_i32 == 0)
    return true;
  const auto count = static_cast<std::size_t>(*header.count_i32);
  if (!header.data_identity || *header.data_identity == 0 ||
      count > g_bindings.maximum_bucket_payload_bytes / 0x60 ||
      *header.data_identity > std::numeric_limits<std::uintptr_t>::max() - count * 0x60)
    return false;
  bool complete = true;
  for (std::size_t index = 0; index != count; ++index) {
    EntryFinalSidePhysicalSlot12004 slot;
    slot.bucket = bucket;
    slot.bucket_index = index;
    slot.traversal_ordinal = scope.physical_slots.size();
    slot.entry_identity = *header.data_identity + index * 0x60;
    slot.writer_return_rva = writer_return_rva;
    slot.raw_before = Copy<std::array<std::uint8_t, 0x60>>(slot.entry_identity);
    complete = slot.raw_before.has_value() && complete;
    scope.physical_slots.push_back(std::move(slot));
  }
  return complete;
}
void CopyScope(EntryFinalSideScope12004 &scope) {
  const auto levy = CopyBucket(scope, scope.levy_header,
      EntryFinalSideBucket12004::levy, 0x28, 0x265108D);
  const auto maa = CopyBucket(scope, scope.maa_header,
      EntryFinalSideBucket12004::men_at_arms, 0x40, 0x26510BB);
  scope.copy_complete = levy && maa;
  if (!scope.copy_complete) scope.reason = "side_physical_copy_partial";
}
void Record(EntryFinalSideCaptureRecord12004 &record) noexcept {
  try {
    auto retained = record;
    const std::lock_guard lock(g_records_mutex);
    record.record_sequence = ++g_record_sequence;
    retained.record_sequence = record.record_sequence;
    g_records[(record.record_sequence - 1) % g_records.size()] = std::move(retained);
  } catch (...) {
    // Observation retention cannot alter the once-returned native RAX bits.
    g_capture_retention_failures.fetch_add(1, std::memory_order_relaxed);
  }
}
bool SameParent(const EntryFinalSideIdentity12004 &a,
                const EntryFinalSideIdentity12004 &b) noexcept {
  return a.side_identity == b.side_identity &&
      a.province_identity == b.province_identity &&
      a.caller_return_rva == b.caller_return_rva &&
      a.caller_return_slot == b.caller_return_slot &&
      a.occurrence.clock_identity == b.occurrence.clock_identity &&
      a.occurrence.sequence == b.occurrence.sequence &&
      a.occurrence.thread_id == b.occurrence.thread_id;
}
void ObserveCoverage(EntryFinalSideCaptureRecord12004 &record) noexcept {
  if (!record.scope.copy_complete || !record.writer_retention_complete)
    return;
  const auto &parent = record.scope.identity;
  const auto &completed = record.completed_event;
  if (parent.occurrence.clock_identity == 0 || parent.occurrence.sequence == 0 ||
      !parent.occurrence.thread_id || *parent.occurrence.thread_id == 0 ||
      completed.clock_identity == 0 || completed.sequence == 0 ||
      !completed.thread_id || *completed.thread_id == 0)
    return;
  bool covered = completed.clock_identity == parent.occurrence.clock_identity &&
      completed.thread_id == parent.occurrence.thread_id &&
      completed.sequence > parent.occurrence.sequence &&
      record.scope.physical_slots.size() == record.writer_records.size();
  for (std::size_t i = 0; covered && i != record.writer_records.size(); ++i) {
    const auto &writer = record.writer_records[i];
    const auto &slot = record.scope.physical_slots[i];
    covered = writer.writer_scope.parent_identity.has_value() &&
        SameParent(*writer.writer_scope.parent_identity, parent) &&
        writer.writer_scope.entry_identity == slot.entry_identity &&
        writer.writer_scope.province_identity == parent.province_identity &&
        writer.writer_scope.writer_return_rva == slot.writer_return_rva &&
        writer.writer_scope.begin_event.clock_identity == parent.occurrence.clock_identity &&
        writer.writer_scope.begin_event.thread_id == parent.occurrence.thread_id &&
        writer.writer_scope.begin_event.sequence > parent.occurrence.sequence &&
        writer.completed_event.clock_identity == parent.occurrence.clock_identity &&
        writer.completed_event.thread_id == parent.occurrence.thread_id &&
        writer.completed_event.sequence > writer.writer_scope.begin_event.sequence &&
        writer.completed_event.sequence < record.completed_event.sequence &&
        writer.original_called && writer.original_returned;
  }
  record.writer_occurrences_cover_copied_slots = covered;
}
} // namespace

EntryFinalSideCaptureBindings12004 BindEntryFinalSideCaptureImage12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  EntryFinalSideCaptureBindings12004 bindings;
  if (module_base == 0 || executable_sha256 != kEntryFinalSideCaptureExeSha12004)
    return bindings;
  bindings.read = NativeRead;
  bindings.next_event = Clock;
  bindings.claim_preceding = ClaimEntryPrecedingForFinalSide12004;
  return bindings;
}

bool InstallEntryFinalSideCapture12004(
    EntryFinalSideCaptureState12004 &state,
    const EntryFinalSideCaptureInstall12004 &environment,
    std::string_view executable_sha256) noexcept {
  if (state.installed.load(std::memory_order_acquire) != 0)
    return state.failure_flags.load(std::memory_order_relaxed) == side_capture_none;
  state.failure_flags.store(side_capture_none, std::memory_order_relaxed);
  g_last_failure_flags.store(0, std::memory_order_relaxed);
  if (executable_sha256 != kEntryFinalSideCaptureExeSha12004 ||
      environment.module_base == 0 ||
      (!environment.offline_fixture && environment.target_override != 0) ||
      environment.module_base > std::numeric_limits<std::uintptr_t>::max() -
          kEntryFinalSideRva12004 - kAnchor.size()) {
    Fail(state, side_capture_exact_build);
    return false;
  }
  if (!environment.primary_thread_suspended_proven) {
    Fail(state, side_capture_quiescence);
    return false;
  }
  if (!environment.bindings.read) {
    Fail(state, side_capture_memory_binding);
    return false;
  }
  if (state.installed.load(std::memory_order_acquire) != 0) return true;
  if (state.trampoline != nullptr) {
    Fail(state, side_capture_allocation);
    return false;
  }
  EntryFinalSideCaptureState12004 *expected = nullptr;
  if (!g_active_state.compare_exchange_strong(expected, &state,
                                              std::memory_order_acq_rel)) {
    Fail(state, side_capture_already_installed);
    return false;
  }
  state.target_protection_known = false;
  state.original_target_protection = 0;
  state.target = environment.target_override != 0 ? environment.target_override :
      environment.module_base + kEntryFinalSideRva12004;
  state.memory_context = environment.memory_context;
  state.virtual_free = environment.virtual_free_override ? environment.virtual_free_override : Free;
  state.virtual_protect = environment.virtual_protect_override ? environment.virtual_protect_override : Protect;
  state.flush = environment.flush_override ? environment.flush_override : Flush;
  const auto allocate = environment.virtual_alloc_override ? environment.virtual_alloc_override : Allocate;
  auto bindings = environment.bindings;
  // Production always uses the shared process clock. No private counter can
  // accidentally be supplied by a caller of this install API.
  if (!environment.offline_fixture || !bindings.claim_preceding)
    bindings.claim_preceding = ClaimEntryPrecedingForFinalSide12004;
  if (!environment.offline_fixture || !bindings.next_event) {
    bindings.event_context = nullptr;
    bindings.next_event = Clock;
  }
  if (!TargetEquals(bindings, state.target, kAnchor)) {
    Fail(state, side_capture_anchor);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  state.trampoline = allocate(state.memory_context, 34,
                             MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
  if (!state.trampoline) {
    Fail(state, side_capture_allocation);
    g_active_state.store(nullptr, std::memory_order_release);
    return false;
  }
  auto *code = static_cast<std::uint8_t *>(state.trampoline);
  std::memcpy(code, kAnchor.data(), kAnchor.size());
  Jump(code + kAnchor.size(), state.target + kAnchor.size());
  DWORD previous = 0;
  const bool protected_code = state.virtual_protect(state.memory_context,
      code, 34, PAGE_EXECUTE_READ, previous);
  const bool flushed_code = protected_code && state.flush(state.memory_context, code, 34);
  if (flushed_code) {
    g_bindings = bindings;
    g_module_base = environment.module_base;
    g_offline_fixture = environment.offline_fixture;
    g_original.store(reinterpret_cast<EntryFinalSideCaptureOriginal12004>(code),
                     std::memory_order_release);
    g_install_epoch.fetch_add(1, std::memory_order_acq_rel);
    g_available.store(true, std::memory_order_release);
  } else {
    Fail(state, protected_code ? side_capture_flush : side_capture_protection);
  }
  bool target_written = false;
  const bool patched = flushed_code && WritePatch(state, bindings, kAnchor, Patch(), &target_written);
  if (!patched) {
    // WritePatch can fail after writing. Restore iff the hook bytes are present;
    // never free a trampoline while a surviving entry patch references it.
    if (target_written && !WritePatch(state, bindings, Patch(), kAnchor)) {
      Fail(state, side_capture_rollback);
      state.original = kAnchor;
      state.installed.store(1, std::memory_order_release);
      return false;
    }
    g_available.store(false, std::memory_order_release);
    g_original.store(nullptr, std::memory_order_release);
    if (!state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
      Fail(state, side_capture_allocation);
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

bool UninstallEntryFinalSideCapture12004(
    EntryFinalSideCaptureState12004 &state,
    bool primary_thread_suspended_proven) noexcept {
  if (state.installed.load(std::memory_order_acquire) == 0 && state.trampoline == nullptr)
    return true;
  if (!primary_thread_suspended_proven) {
    Fail(state, side_capture_quiescence);
    return false;
  }
  const bool installed = state.installed.load(std::memory_order_acquire) != 0;
  if (!installed) {
    // A failed allocation release left this state's detached backing. It is
    // unrelated to any later installation and must not clear its globals.
    if (!state.virtual_free || !state.virtual_free(state.memory_context,
        state.trampoline, 0, MEM_RELEASE)) {
      Fail(state, side_capture_allocation);
      return false;
    }
    state.trampoline = nullptr;
    return true;
  }
  if ((installed && g_active_state.load(std::memory_order_acquire) != &state) ||
      g_in_flight.load(std::memory_order_acquire) != 0) {
    Fail(state, side_capture_callback_active);
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
        Fail(state, side_capture_rollback);
      return false;
    }
  }
  state.installed.store(0, std::memory_order_release);
  g_available.store(false, std::memory_order_release);
  g_original.store(nullptr, std::memory_order_release);
  g_active_state.store(nullptr, std::memory_order_release);
  // Immutable history deliberately survives uninstall. The clock also survives.
  if (!state.virtual_free(state.memory_context, state.trampoline, 0, MEM_RELEASE)) {
    Fail(state, side_capture_allocation);
    return false;
  }
  state.trampoline = nullptr;
  return true;
}


const EntryFinalSideScope12004 *PeekActiveEntryFinalSideScope12004() noexcept {
  return g_side_scope;
}
const EntryFinalSideWriterScope12004 *
PeekActiveEntryFinalSideWriterScope12004() noexcept { return g_writer_scope; }

const EntryFinalSidePhysicalSlot12004 *FindEntryFinalSidePhysicalSlot12004(
    const EntryFinalSideScope12004 &scope, std::uintptr_t entry,
    std::uintptr_t province, std::uintptr_t writer_return_rva) noexcept {
  if (province != scope.identity.province_identity ||
      (writer_return_rva != 0x265108D && writer_return_rva != 0x26510BB))
    return nullptr;
  for (const auto &slot : scope.physical_slots)
    if (slot.entry_identity == entry && slot.writer_return_rva == writer_return_rva)
      return &slot;
  return nullptr;
}
EntryFinalSideWriterSlotScope12004::EntryFinalSideWriterSlotScope12004(
    std::uintptr_t entry, std::uintptr_t province, std::uintptr_t writer_return_rva,
    const PersonInstalledTransferEvent12004 &begin_event) : previous_(g_writer_scope) {
  if (g_side_scope) {
    const auto *slot = FindEntryFinalSidePhysicalSlot12004(
        *g_side_scope, entry, province, writer_return_rva);
    if (slot) current_.emplace(EntryFinalSideWriterScope12004{
        g_side_scope->identity, *slot, begin_event});
  }
  g_writer_scope = current_ ? &*current_ : nullptr;
}
EntryFinalSideWriterSlotScope12004::~EntryFinalSideWriterSlotScope12004() {
  g_writer_scope = previous_;
}
void AppendEntryFinalSideWriterRecord12004(
    const EntryFinalWriterCaptureRecord12004 &record) noexcept {
  if (!g_side_record) return;
  if (!record.writer_scope.parent_identity ||
      !SameParent(*record.writer_scope.parent_identity, g_side_record->scope.identity))
    return;
  try { g_side_record->writer_records.push_back(record); }
  catch (...) { g_side_record->writer_retention_complete = false; }
}

std::uintptr_t InvokeEntryFinalSideCapture12004(void *side, void *province,
    std::uintptr_t original_return_address,
    std::uintptr_t original_return_slot) noexcept {
  Flight flight;
  const auto original = g_original.load(std::memory_order_acquire);
  if (!original) return 0;
  if (!g_available.load(std::memory_order_acquire)) return original(side, province);
  EntryFinalSideCaptureRecord12004 record;
  record.install_epoch = g_install_epoch.load(std::memory_order_acquire);
  record.offline_fixture = g_offline_fixture;
  auto &identity = record.scope.identity;
  identity.side_identity = reinterpret_cast<std::uintptr_t>(side);
  identity.province_identity = reinterpret_cast<std::uintptr_t>(province);
  identity.caller_return_rva = original_return_address >= g_module_base ?
      original_return_address - g_module_base : 0;
  identity.caller_return_slot = original_return_slot;
  if (identity.caller_return_rva == kEntryFinalSideZeroReturn12004)
    identity.source_side_index = 0;
  if (identity.caller_return_rva == kEntryFinalSideOneReturn12004)
    identity.source_side_index = 1;
  identity.occurrence = g_bindings.next_event(g_bindings.event_context);
  if (g_bindings.claim_preceding)
    record.preceding = g_bindings.claim_preceding(
        identity.source_side_index.value_or(2), identity.side_identity,
        identity.caller_return_rva, identity.caller_return_slot,
        identity.occurrence);
  try { CopyScope(record.scope); }
  catch (...) {
    record.scope.copy_complete = false;
    record.scope.reason = "side_physical_copy_failed";
  }
  record.original_called = true;
  std::uintptr_t raw = 0;
  {
    ActiveSide active(record);
    raw = original(side, province); // Exactly one original call.
  }
  record.original_returned = true;
  record.raw_return_bits = raw;
  record.completed_event = g_bindings.next_event(g_bindings.event_context);
  ObserveCoverage(record);
  Record(record);
  return raw;
}

EntryFinalSideCaptureQuery12004 ReadEntryFinalSideCapture12004() {
  EntryFinalSideCaptureQuery12004 query;
  query.configured = g_available.load(std::memory_order_acquire);
  const auto *state = g_active_state.load(std::memory_order_acquire);
  query.installed = state && state->installed.load(std::memory_order_acquire) != 0;
  query.install_failure_flags = g_last_failure_flags.load(std::memory_order_relaxed);
  query.capture_retention_failures = g_capture_retention_failures.load(std::memory_order_relaxed);
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
EntryFinalSideCaptureQuery12004 CollectEntryFinalSideCaptureForCombats12004(
    std::span<const EntryPrecedingCombatOwner12004> owners) {
  auto query = ReadEntryFinalSideCapture12004();
  query.request_filtered = true;
  query.records.erase(std::remove_if(query.records.begin(), query.records.end(),
      [&](const auto &record) {
        return !record.preceding || std::none_of(owners.begin(), owners.end(),
            [&](const auto &owner) {
              return owner.combat_identity != 0 && owner.full_combat_id != 0xFFFFFFFFU &&
                  record.preceding->combat_identity == owner.combat_identity &&
                  record.preceding->combat_full_id_after == owner.full_combat_id;
            });
      }), query.records.end());
  return query;
}

extern "C" __declspec(noinline) std::uintptr_t __fastcall
XarEntryFinalSideCaptureHook12004V1(void *side, void *province) noexcept {
  const auto caller = reinterpret_cast<std::uintptr_t>(_ReturnAddress());
  const auto slot = reinterpret_cast<std::uintptr_t>(_AddressOfReturnAddress());
  return InvokeEntryFinalSideCapture12004(side, province, caller, slot);
}
} // namespace xar::ck3_12004
