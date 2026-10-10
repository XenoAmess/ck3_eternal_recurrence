#include "xar_bridge/army_natural_phase_scope_12004.hpp"

#include <limits>
#include <atomic>
#include <mutex>
#include <utility>

namespace xar::ck3_12004 {
namespace {
struct Active {
  ArmyNaturalPhaseScope12004 *scope = nullptr;
  const ArmyNaturalPhaseBindings12004 *bindings = nullptr;
};
thread_local Active g_active;
std::mutex g_journal_mutex;
std::vector<ArmyNaturalPhaseRecord12004> g_journal;
constexpr std::size_t kMaximumJournalRecords = 64;
ArmyNaturalPhaseJournalStatus12004 g_journal_status;
std::atomic<std::uint64_t> g_failed_appends{0};

template<class T> std::optional<T> Read(const ArmyNaturalPhaseBindings12004 &b,
    std::uintptr_t address) noexcept {
  if (!address || !b.read) return std::nullopt;
  T value{};
  if (!b.read(b.read_context, address, &value, sizeof value)) return std::nullopt;
  return value;
}
ArmyNaturalPhaseEvent12004 Event(const ArmyNaturalPhaseBindings12004 &b) noexcept {
  return b.next_event ? b.next_event(b.event_context) : NextArmyNaturalPhaseEvent12004();
}
bool SameThread(const ArmyNaturalPhaseEvent12004 &a,
    const ArmyNaturalPhaseEvent12004 &b) noexcept {
  return a.clock_identity && a.sequence && b.sequence && a.clock_identity == b.clock_identity &&
      a.thread_id && b.thread_id && a.thread_id == b.thread_id;
}
ArmyNaturalPhaseRoster12004 Roster(const ArmyNaturalPhaseBindings12004 &b,
    std::uintptr_t primary, ArmyNaturalRosterBoundary12004 boundary,
    std::uintptr_t rva, const ArmyNaturalPhaseEvent12004 &event) noexcept {
  ArmyNaturalPhaseRoster12004 out{};
  out.boundary = boundary;
  out.capture_rva = rva;
  out.capture_event = event;
  if (!primary) return out;
  out.begin_identity = Read<std::uintptr_t>(b, primary + 0x50);
  out.count = Read<std::int32_t>(b, primary + 0x5C);
  if (!out.begin_identity || !out.count || *out.count < 0 ||
      static_cast<std::size_t>(*out.count) > b.maximum_roster_occurrences ||
      *out.count > 65536) return out;
  const auto bytes = static_cast<std::size_t>(*out.count) * sizeof(std::uint32_t);
  if (*out.begin_identity > (std::numeric_limits<std::uintptr_t>::max)() - bytes ||
      (bytes && !*out.begin_identity)) return out;
  out.end_identity = *out.begin_identity + bytes;
  try { out.ordered_full_ids.resize(static_cast<std::size_t>(*out.count)); }
  catch (...) { return out; }
  out.complete = !bytes || (b.read && b.read(b.read_context, *out.begin_identity,
      out.ordered_full_ids.data(), bytes));
  if (!out.complete) out.ordered_full_ids.clear();
  return out;
}
struct RestoreActive {
  Active previous;
  ~RestoreActive() { g_active = previous; }
};
void Journal(const ArmyNaturalPhaseRecord12004 &record) noexcept {
  try {
    std::lock_guard<std::mutex> lock(g_journal_mutex);
    if (g_journal.size() == kMaximumJournalRecords) {
      g_journal.erase(g_journal.begin()); ++g_journal_status.overwritten_records;
    }
    g_journal.push_back(record);
    ++g_journal_status.appended_records;
  } catch (...) { ++g_failed_appends; /* Observation loss never suppresses native code. */ }
}
} // namespace

ArmyNaturalPhaseEvent12004 NextArmyNaturalPhaseEvent12004(void *) noexcept {
  return NextPersonNaturalLineageEvent12004();
}
ArmyNaturalPhaseScope12004 CopyActiveArmyNaturalPhaseScope12004() noexcept {
  try { return g_active.scope ? *g_active.scope : ArmyNaturalPhaseScope12004{}; }
  catch (...) { return {}; }
}

ArmyNaturalPhaseRecord12004 InvokeArmyNaturalPhaseScope12004(
    const ArmyNaturalPhaseBindings12004 &b, ArmyNaturalPhaseOriginal12004 original,
    void *secondary_manager, ArmyNaturalPhaseKind12004 phase,
    std::uintptr_t caller_return_rva) noexcept {
  ArmyNaturalPhaseRecord12004 out{};
  auto &scope = out.scope;
  const auto secondary = reinterpret_cast<std::uintptr_t>(secondary_manager);
  // Only the literal closed callback entries grant this scope. A query never does.
  if (original && secondary >= 8 &&
      (phase == ArmyNaturalPhaseKind12004::pre_date ||
       phase == ArmyNaturalPhaseKind12004::post_date)) {
    scope.observed = true;
    scope.phase = phase;
    scope.actual_entry_rva = phase == ArmyNaturalPhaseKind12004::pre_date ?
        kArmyNaturalPreDateRva12004 : kArmyNaturalPostDateRva12004;
    scope.caller_return_rva = caller_return_rva;
    scope.secondary_manager_identity = secondary;
    scope.primary_manager_identity = secondary - 8;
    scope.game_state_identity = b.game_state_identity;
    scope.session_identity = b.session_identity;
    scope.entry_event = Event(b);
    if (scope.game_state_identity) {
      scope.date_raw = Read<std::uint64_t>(b, scope.game_state_identity + 8);
      scope.absolute_day_raw = Read<std::uint32_t>(b, scope.game_state_identity + 0x9C);
      scope.entry_c0_raw = Read<std::uint8_t>(b, scope.game_state_identity + 0xC0);
    }
    scope.original_army_roster = Roster(b, scope.primary_manager_identity,
        ArmyNaturalRosterBoundary12004::parent_entry, scope.actual_entry_rva,
        scope.entry_event);
  }
  {
    RestoreActive restore{g_active};
    // Invalid invocations cannot inherit the surrounding parent's identity.
    g_active = {scope.observed ? &scope : nullptr, scope.observed ? &b : nullptr};
    if (original) {
      out.original_called = true;
      out.raw_return_bits = original(secondary_manager);
      out.original_returned = true;
    }
  }
  if (scope.observed && out.original_returned) {
    out.returned_event = Event(b);
    if (scope.game_state_identity) {
      out.returned_date_raw = Read<std::uint64_t>(b, scope.game_state_identity + 8);
      out.returned_absolute_day_raw = Read<std::uint32_t>(b, scope.game_state_identity + 0x9C);
      out.returned_c0_raw = Read<std::uint8_t>(b, scope.game_state_identity + 0xC0);
    }
    if (scope.entry_event.clock_identity && scope.entry_event.thread_id &&
        out.returned_event.clock_identity && out.returned_event.thread_id)
      out.same_clock_thread_order = SameThread(scope.entry_event, out.returned_event) &&
          scope.entry_event.sequence < out.returned_event.sequence;
    Journal(out);
  }
  return out;
}

bool ObserveArmyNaturalPhaseOriginalRoster12004(std::uintptr_t primary,
    std::uintptr_t return_rva, std::optional<std::uint64_t> actual_prefix_date_raw) noexcept {
  if (!g_active.scope || !g_active.bindings ||
      g_active.scope->phase != ArmyNaturalPhaseKind12004::pre_date ||
      g_active.scope->primary_manager_identity != primary ||
      return_rva != kArmyNaturalOriginalRosterCaptureRva12004) return false;
  const auto event = Event(*g_active.bindings);
  if (!SameThread(g_active.scope->entry_event, event) ||
      event.sequence <= g_active.scope->entry_event.sequence) return false;
  auto roster = Roster(*g_active.bindings, primary,
      ArmyNaturalRosterBoundary12004::pre_date_prefix_return, return_rva, event);
  g_active.scope->prefix_date_raw = actual_prefix_date_raw;
  g_active.scope->original_army_roster = std::move(roster);
  return g_active.scope->original_army_roster.complete;
}

bool ObserveArmyNaturalPhaseSavedC012004(std::uintptr_t secondary,
    std::uintptr_t save_rva, std::uint8_t c0) noexcept {
  if (!g_active.scope || !g_active.bindings ||
      g_active.scope->phase != ArmyNaturalPhaseKind12004::post_date ||
      g_active.scope->secondary_manager_identity != secondary || save_rva != 0x2A9A65D)
    return false;
  const auto event = Event(*g_active.bindings);
  if (!SameThread(g_active.scope->entry_event, event) ||
      event.sequence <= g_active.scope->entry_event.sequence) return false;
  g_active.scope->saved_c0_raw = c0;
  g_active.scope->saved_c0_observed_rva = save_rva;
  g_active.scope->saved_mask02_admitted = (c0 & 2U) != 0;
  g_active.scope->saved_c0_event = event;
  return true;
}
bool ObserveArmyNaturalPhaseSavedMask12004(std::uintptr_t secondary,
    std::uintptr_t return_rva, std::uint8_t mask) noexcept {
  if (!g_active.scope || !g_active.bindings ||
      g_active.scope->phase != ArmyNaturalPhaseKind12004::post_date ||
      g_active.scope->secondary_manager_identity != secondary || (mask != 0 && mask != 2) ||
      (return_rva != 0x2A9A672 && return_rva != 0x2A9A67D &&
       return_rva != 0x2A9A8E2 && return_rva != 0x2A9A8EA) ||
      ((return_rva == 0x2A9A672 || return_rva == 0x2A9A8E2) && mask != 2)) return false;
  const bool admitted = mask != 0;
  if (g_active.scope->saved_mask02_admitted &&
      *g_active.scope->saved_mask02_admitted != admitted) return false;
  const auto event = Event(*g_active.bindings);
  if (!SameThread(g_active.scope->entry_event, event) ||
      event.sequence <= g_active.scope->entry_event.sequence) return false;
  g_active.scope->saved_mask02_admitted = admitted;
  g_active.scope->saved_c0_observed_rva = return_rva;
  g_active.scope->saved_c0_event = event;
  return true;
}

std::vector<ArmyNaturalPhaseRecord12004> ReadArmyNaturalPhaseJournal12004() {
  std::lock_guard<std::mutex> lock(g_journal_mutex);
  return g_journal;
}
void ClearArmyNaturalPhaseJournal12004() noexcept {
  try {
    std::lock_guard<std::mutex> lock(g_journal_mutex);
    g_journal.clear(); ++g_journal_status.clear_operations;
  }
  catch (...) {}
}
ArmyNaturalPhaseJournalStatus12004 ReadArmyNaturalPhaseJournalStatus12004() noexcept {
  try {
    std::lock_guard<std::mutex> lock(g_journal_mutex);
    auto out = g_journal_status;
    out.read_complete = true;
    out.retained_records = g_journal.size();
    out.failed_appends = g_failed_appends.load(std::memory_order_relaxed);
    return out;
  } catch (...) {
    ArmyNaturalPhaseJournalStatus12004 out{};
    out.failed_appends = g_failed_appends.load(std::memory_order_relaxed);
    return out;
  }
}
bool ArmyNaturalPhaseCurrentContextMatches12004(const ArmyNaturalPhaseScope12004 &scope,
    std::uintptr_t primary, std::uintptr_t state, std::uintptr_t clock) noexcept {
  return scope.observed && primary && state && clock &&
      scope.primary_manager_identity == primary && scope.game_state_identity == state &&
      scope.secondary_manager_identity == primary + 8 &&
      scope.entry_event.clock_identity == clock && scope.entry_event.sequence &&
      scope.entry_event.thread_id.has_value();
}
std::optional<bool> ArmyNaturalPhaseSessionMatches12004(const ArmyNaturalPhaseScope12004 &scope,
    std::optional<std::uintptr_t> current) noexcept {
  if (!scope.session_identity || !*scope.session_identity || !current || !*current)
    return std::nullopt;
  return scope.session_identity == current;
}
} // namespace xar::ck3_12004
