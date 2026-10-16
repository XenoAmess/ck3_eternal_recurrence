#pragma once

#include <string>

namespace xar::ck3_11906 {

// Dismiss may release the modal pause and permit a forward date transition.
// Only its fixed, returned callback can use this exception. Read-only queries
// and all other owner/runtime fields retain the ordinary boundary contract.
template <class Stamp>
bool WarResultsDismissScopeTransitionAllowedV1(
    bool fixed_close_and_ticket_bound, bool callback_returned,
    const Stamp &before, const Stamp &after) noexcept {
  if (!fixed_close_and_ticket_bound || !callback_returned || !before.paused ||
      after.paused || after.date_raw < before.date_raw) return false;
  auto normalized = after;
  normalized.paused = before.paused;
  normalized.date_raw = before.date_raw;
  return normalized == before;
}

// Keep real begin/end values even when a different identity change still fails
// the mailbox boundary. No success or UI-closure field is inferred here.
template <class Result, class Stamp>
void MarkWarResultsDismissScopeTransitionPendingV1(
    Result &result, const Stamp &before, const Stamp &after,
    bool admitted) {
  result.available = result.accepted = result.closure_verified = false;
  result.scope_unchanged = false;
  result.status = "verification_pending";
  result.unavailable_reason =
      "war_results_ui_scope_transition;begin_date_raw=" +
      std::to_string(before.date_raw) + ";end_date_raw=" +
      std::to_string(after.date_raw) + ";begin_paused=" +
      (before.paused ? "true" : "false") + ";end_paused=" +
      (after.paused ? "true" : "false") + ";owner_boundary_admitted=" +
      (admitted ? "true" : "false");
}

} // namespace xar::ck3_11906
