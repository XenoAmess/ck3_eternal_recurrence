#pragma once

#include "holy_order_loan_decision_costs_12004.hpp"
#include "holy_order_loan_principal_12004.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004::religion::loan_war_cash {

struct Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  loan_decision_costs::Bindings decision_costs{};
  loan_principal::Bindings principal{};
};

// Native part of the existing cash-query frame. The envelope continues to own
// its complete expected_snapshot; this small record does not copy the world.
struct NativeSourceFrame {
  std::uint64_t snapshot_revision = 0, ticket_sequence = 0;
  ck3_11906::MainThreadExecutionStampV1 execution_stamp{};
  std::int32_t local_player_id = -1, played_character_id = -1, date_raw = 0;
  bool full_snapshot_owner_retained = false;
};

struct Observation {
  bool completed = false;
  std::string_view unavailable_reason = "owner_not_captured";
  NativeSourceFrame source_frame{};
  // Engaged only for an available original provider value with this exact
  // owner actor/date/pump epoch. A zero principal stays an engaged native zero.
  std::optional<loan_decision_costs::Observation> decision_costs;
  std::optional<loan_principal::Observation> principal;
  std::string decision_costs_unavailable_reason = "not_sampled";
  std::string principal_unavailable_reason = "not_sampled";
  // Typed debt and attributable payment have no provider in this collector.
  std::optional<std::int64_t> existing_debt_principal_raw;
  static constexpr bool complete_loan_terms = false;
  static constexpr bool typed_debt_readback_verified = false;
  static constexpr bool independently_attributed_received_funds_verified = false;
  static constexpr bool submit_planned = false;
  static constexpr std::int64_t funding_credit_raw = 0;
};

Bindings BindHolyOrderLoanWarCashAttachImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// Source candidate only: no new query step/permission or registration.
// Call inside the already-entered .4 current-cash mailbox, before its existing
// FinishQueryMailbox. No extra snapshot, Enter/Finish, action or retry is done.
// true means collection completed, including independently unavailable fields.
// Publication still requires the ORIGINAL cash envelope's successful Finish,
// worker post-snapshot equality, plus the complete planning-source-frame held
// by the existing transport's CALLER (episode, snapshot/public/native revisions,
// actor/date, PID/connection). The transport alone does not check all of these.
// This native leaf cannot manufacture those Python identities or cash credit.
bool ReadHolyOrderLoanWarCashAttach12004(const Bindings &,
    ck3_12002::QueryMailboxEnvelope &already_entered_cash_owner,
    Observation &) noexcept;

} // namespace xar::ck3_12004::religion::loan_war_cash
