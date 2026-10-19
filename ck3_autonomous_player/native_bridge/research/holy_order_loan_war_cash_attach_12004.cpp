#include "holy_order_loan_war_cash_attach_12004.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

#include <utility>

namespace xar::ck3_12004::religion::loan_war_cash {
namespace {
bool EnteredCurrentOwner(ck3_12002::QueryMailboxEnvelope &owner) noexcept {
  if (!ck3_12002::IsQueryOwningThread(&owner) ||
      owner.snapshot_comparison !=
          ck3_12002::QuerySnapshotComparison12002::full_snapshot ||
      !game::IsCk3_12004Descriptor(owner.game->descriptor())) return false;
  const auto &snapshot = owner.expected_snapshot;
  const auto &stamp = owner.execution_stamp;
  return owner.expected_snapshot_revision != 0 && owner.ticket.sequence != 0 &&
      stamp.pump_epoch != 0 && stamp.thread_id != 0 && stamp.paused &&
      snapshot.paused && snapshot.map_ready && snapshot.has_played_character &&
      snapshot.played_character_alive && snapshot.played_character_id > 0 &&
      snapshot.date_raw == stamp.date_raw;
}
template <typename Provider>
bool MatchesOwner(const Provider &value, const NativeSourceFrame &frame) noexcept {
  return value.available &&
      value.capture_epoch == frame.execution_stamp.pump_epoch &&
      value.played_character_id == frame.played_character_id &&
      value.date_raw == frame.date_raw;
}
bool RetainsOwner(ck3_12002::QueryMailboxEnvelope &owner,
                  const NativeSourceFrame &frame) noexcept {
  const auto &snapshot = owner.expected_snapshot;
  return EnteredCurrentOwner(owner) &&
      owner.expected_snapshot_revision == frame.snapshot_revision &&
      owner.ticket.sequence == frame.ticket_sequence &&
      owner.execution_stamp == frame.execution_stamp &&
      snapshot.player_id == frame.local_player_id &&
      snapshot.played_character_id == frame.played_character_id &&
      snapshot.date_raw == frame.date_raw;
}
} // namespace

Bindings BindHolyOrderLoanWarCashAttachImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != ck3_12004::kExecutableSha256) return b;
  b.image_base = base;
  b.decision_costs = loan_decision_costs::BindHolyOrderLoanDecisionCostsImage12004(base, sha);
  b.principal = loan_principal::BindHolyOrderLoanPrincipalImage12004(base, sha);
  // One unavailable provider does not erase the other's independent input.
  b.enabled = b.decision_costs.enabled || b.principal.enabled;
  return b;
}

bool ReadHolyOrderLoanWarCashAttach12004(const Bindings &b,
    ck3_12002::QueryMailboxEnvelope &owner, Observation &out) noexcept {
  out = {};
  if (!EnteredCurrentOwner(owner)) return false;
  const auto &snapshot = owner.expected_snapshot;
  auto &frame = out.source_frame;
  frame.snapshot_revision = owner.expected_snapshot_revision;
  frame.ticket_sequence = owner.ticket.sequence;
  frame.execution_stamp = owner.execution_stamp;
  frame.local_player_id = snapshot.player_id;
  frame.played_character_id = snapshot.played_character_id;
  frame.date_raw = snapshot.date_raw;
  if (!b.enabled || !b.image_base) {
    out.completed = true;
    out.unavailable_reason = "loan_readers_unavailable";
    out.decision_costs_unavailable_reason = "bindings_unavailable";
    out.principal_unavailable_reason = "bindings_unavailable";
    frame.full_snapshot_owner_retained = true;
    return true;
  }

  loan_decision_costs::Observation decisions{};
  loan_principal::Observation principal{};
  // Existing readers own their scopes/scratch. Each reader is called once;
  // neither this collector nor its future caller retries an unknown result.
  const bool decision_read = loan_decision_costs::ReadPlayerHolyOrderLoanDecisionCosts12004(
      b.decision_costs, frame.execution_stamp.pump_epoch, decisions);
  const bool principal_read = loan_principal::ReadPlayerHolyOrderLoanPrincipal12004(
      b.principal, frame.execution_stamp.pump_epoch, principal);
  if (!RetainsOwner(owner, frame)) {
    out.unavailable_reason = "loan_cash_owner_frame_changed";
    out.decision_costs_unavailable_reason = "owner_frame_changed";
    out.principal_unavailable_reason = "owner_frame_changed";
    return false;
  }
  frame.full_snapshot_owner_retained = true;
  if (decision_read && MatchesOwner(decisions, frame)) {
    out.decision_costs.emplace(std::move(decisions));
    out.decision_costs_unavailable_reason.clear();
  } else {
    out.decision_costs_unavailable_reason = decisions.available
        ? "decision_costs_owner_frame_mismatch"
        : decisions.unavailable_reason.empty() ? "decision_costs_unavailable"
                                             : decisions.unavailable_reason;
  }
  if (principal_read && MatchesOwner(principal, frame) &&
      principal.owned_temporaries_released) {
    out.principal.emplace(std::move(principal));
    out.principal_unavailable_reason.clear();
  } else {
    out.principal_unavailable_reason = principal.available
        ? !principal.owned_temporaries_released ? "principal_cleanup_unverified"
                                              : "principal_owner_frame_mismatch"
        : principal.unavailable_reason.empty() ? "principal_unavailable"
                                              : principal.unavailable_reason;
  }
  out.completed = true;
  out.unavailable_reason = out.decision_costs || out.principal ? std::string_view{}
      : std::string_view{"loan_inputs_unavailable"};
  return true;
}

} // namespace xar::ck3_12004::religion::loan_war_cash
