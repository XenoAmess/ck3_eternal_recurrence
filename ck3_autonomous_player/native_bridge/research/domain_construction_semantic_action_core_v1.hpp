#pragma once

#include "domain_construction_cost_legality_live_observer_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>

namespace xar::ck3::research {

enum class DomainConstructionActionSelectionFailureV1 : std::uint8_t {
  none = 0,
  publication_unavailable,
  candidate_unready,
  duplicate_identity,
  candidate_set_drift,
  identity_drift,
  generation_drift,
  proof_epoch_drift,
  date_drift,
  cost_drift,
  resource_drift,
  native_final_drift,
  no_actionable_candidate,
};

enum class DomainConstructionActionPhaseV1 : std::uint8_t {
  idle = 0,
  pending_receipt,
  submit_failed,
  submit_rejected,
  applied,
};

enum class DomainConstructionReceiptFailureV1 : std::uint8_t {
  none = 0,
  not_pending,
  ack_token,
  stale_generation,
  stale_proof_epoch,
  stale_date,
  identity,
  evidence_missing,
};

struct DomainConstructionSemanticActionRequestV1 final {
  std::string candidate_id;
  DomainConstructionCandidateKindV1 candidate_kind =
      DomainConstructionCandidateKindV1::building_in_holding;
  DomainConstructionCandidateSnapshotBindingV1 binding;
  std::array<std::int64_t, kDomainConstructionResourceSlotCountV1> cost_raw{};
  std::array<std::int64_t, kDomainConstructionResourceSlotCountV1>
      resource_balance_before{};
};

struct DomainConstructionActionSelectionV1 final {
  bool ready = false;
  DomainConstructionActionSelectionFailureV1 failure =
      DomainConstructionActionSelectionFailureV1::none;
  DomainConstructionSemanticActionRequestV1 request;
};

struct DomainConstructionSubmitAckV1 final {
  bool accepted = false;
  std::uint64_t ack_token = 0;
};

using DomainConstructionSubmitV1 = bool (*)(
    void* context, const DomainConstructionSemanticActionRequestV1& request,
    DomainConstructionSubmitAckV1& ack);

struct DomainConstructionFreshReceiptV1 final {
  std::uint64_t ack_token = 0;
  std::string candidate_id;
  DomainConstructionCandidateKindV1 candidate_kind =
      DomainConstructionCandidateKindV1::building_in_holding;
  DomainConstructionCandidateSnapshotBindingV1 binding;
  bool target_building_state_observed = false;
  bool target_holding_state_observed = false;
  bool resource_balances_observed = false;
  std::array<std::int64_t, kDomainConstructionResourceSlotCountV1>
      resource_balance_after{};
};

struct DomainConstructionSemanticActionStateV1 final {
  DomainConstructionActionPhaseV1 phase = DomainConstructionActionPhaseV1::idle;
  DomainConstructionActionSelectionFailureV1 selection_failure =
      DomainConstructionActionSelectionFailureV1::none;
  DomainConstructionReceiptFailureV1 receipt_failure =
      DomainConstructionReceiptFailureV1::none;
  std::uint64_t submit_call_count = 0;
  bool ack_received = false;
  bool applied = false;
  std::uint64_t ack_token = 0;
  DomainConstructionSemanticActionRequestV1 request;
};

[[nodiscard]] DomainConstructionActionSelectionV1
SelectDeterministicDomainConstructionActionV1(
    std::span<const DomainConstructionCostLegalityPublicationV1> first_sample,
    std::span<const DomainConstructionCostLegalityPublicationV1> second_sample);

[[nodiscard]] bool BeginDomainConstructionSemanticActionV1(
    DomainConstructionSemanticActionStateV1& state,
    std::span<const DomainConstructionCostLegalityPublicationV1> first_sample,
    std::span<const DomainConstructionCostLegalityPublicationV1> second_sample,
    DomainConstructionSubmitV1 submit, void* submit_context);

[[nodiscard]] bool ObserveDomainConstructionFreshReceiptV1(
    DomainConstructionSemanticActionStateV1& state,
    const DomainConstructionFreshReceiptV1& receipt);

}  // namespace xar::ck3::research
