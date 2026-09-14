#include "domain_construction_semantic_action_core_v1.hpp"

#include <algorithm>
#include <vector>

namespace xar::ck3::research {
namespace {

using Publication = DomainConstructionCostLegalityPublicationV1;

bool CandidateConsistentlyActionable(
    const DomainConstructionCandidateCostLegalityV1& candidate) {
  if (!(candidate.ready && candidate.actionable &&
         candidate.native_affordable && candidate.native_final_legal &&
         candidate.rejection_reason ==
             DomainConstructionCandidateRejectionReasonV1::none &&
         candidate.unavailable ==
             DomainConstructionCandidateCostLegalityUnavailableV1::none &&
         !candidate.candidate_id.empty() &&
         candidate.first_blocking_resource_slot ==
             kDomainConstructionNoBlockingResourceSlotV1 &&
         candidate.blocking_resource_mask == 0U)) {
    return false;
  }
  for (std::size_t slot = 0; slot < candidate.cost_raw.size(); ++slot) {
    if (!candidate.resource_affordable[slot] ||
        !(candidate.cost_raw[slot] <= 0 ||
          candidate.cost_raw[slot] < candidate.resource_balance_raw[slot])) {
      return false;
    }
  }
  return true;
}

DomainConstructionActionSelectionFailureV1 ValidateSample(
    const std::span<const Publication> sample,
    std::vector<const Publication*>& actionable) {
  actionable.clear();
  actionable.reserve(sample.size());
  for (const auto& publication : sample) {
    if (!publication.available ||
        publication.publication_generation == 0U ||
        (publication.publication_generation & 1U) != 0U) {
      return DomainConstructionActionSelectionFailureV1::
          publication_unavailable;
    }
    if (!publication.candidate.ready) {
      return DomainConstructionActionSelectionFailureV1::candidate_unready;
    }
    if (publication.candidate.candidate_kind !=
            DomainConstructionCandidateKindV1::building_in_holding &&
        publication.candidate.candidate_kind !=
            DomainConstructionCandidateKindV1::new_holding) {
      return DomainConstructionActionSelectionFailureV1::candidate_unready;
    }
    if (publication.candidate.binding.generation == 0U ||
        (publication.candidate.binding.generation & 1U) != 0U) {
      return DomainConstructionActionSelectionFailureV1::generation_drift;
    }
    if (publication.candidate.binding.proof_epoch == 0U) {
      return DomainConstructionActionSelectionFailureV1::proof_epoch_drift;
    }
    if (publication.candidate.actionable &&
        !CandidateConsistentlyActionable(publication.candidate)) {
      return DomainConstructionActionSelectionFailureV1::native_final_drift;
    }
    if (CandidateConsistentlyActionable(publication.candidate)) {
      actionable.push_back(&publication);
    }
  }
  std::sort(actionable.begin(), actionable.end(),
            [](const Publication* left, const Publication* right) {
              return left->candidate.candidate_id <
                     right->candidate.candidate_id;
            });
  if (std::adjacent_find(
          actionable.begin(), actionable.end(),
          [](const Publication* left, const Publication* right) {
            return left->candidate.candidate_id ==
                   right->candidate.candidate_id;
          }) != actionable.end()) {
    return DomainConstructionActionSelectionFailureV1::duplicate_identity;
  }
  return actionable.empty()
             ? DomainConstructionActionSelectionFailureV1::
                   no_actionable_candidate
             : DomainConstructionActionSelectionFailureV1::none;
}

DomainConstructionActionSelectionFailureV1 CompareCandidate(
    const Publication& first, const Publication& second) {
  const auto& left = first.candidate;
  const auto& right = second.candidate;
  if (left.candidate_id != right.candidate_id ||
      left.candidate_kind != right.candidate_kind) {
    return DomainConstructionActionSelectionFailureV1::identity_drift;
  }
  if (first.publication_generation != second.publication_generation ||
      left.binding.generation != right.binding.generation) {
    return DomainConstructionActionSelectionFailureV1::generation_drift;
  }
  if (left.binding.proof_epoch != right.binding.proof_epoch) {
    return DomainConstructionActionSelectionFailureV1::proof_epoch_drift;
  }
  if (left.binding.date_raw != right.binding.date_raw) {
    return DomainConstructionActionSelectionFailureV1::date_drift;
  }
  if (left.cost_raw != right.cost_raw ||
      left.resource_affordable != right.resource_affordable ||
      left.first_blocking_resource_slot !=
          right.first_blocking_resource_slot ||
      left.blocking_resource_mask != right.blocking_resource_mask) {
    return DomainConstructionActionSelectionFailureV1::cost_drift;
  }
  if (left.resource_balance_raw != right.resource_balance_raw) {
    return DomainConstructionActionSelectionFailureV1::resource_drift;
  }
  if (left.native_affordable != right.native_affordable ||
      left.native_final_legal != right.native_final_legal ||
      left.actionable != right.actionable ||
      left.rejection_reason != right.rejection_reason ||
      left.unavailable != right.unavailable) {
    return DomainConstructionActionSelectionFailureV1::native_final_drift;
  }
  return DomainConstructionActionSelectionFailureV1::none;
}

DomainConstructionSemanticActionRequestV1 MakeRequest(
    const DomainConstructionCandidateCostLegalityV1& candidate) {
  DomainConstructionSemanticActionRequestV1 request{};
  request.candidate_id = candidate.candidate_id;
  request.candidate_kind = candidate.candidate_kind;
  request.binding = candidate.binding;
  request.cost_raw = candidate.cost_raw;
  request.resource_balance_before = candidate.resource_balance_raw;
  return request;
}

bool ExactResourceDeduction(
    const DomainConstructionSemanticActionRequestV1& request,
    const DomainConstructionFreshReceiptV1& receipt) {
  if (!receipt.resource_balances_observed) return false;
  for (std::size_t slot = 0; slot < request.cost_raw.size(); ++slot) {
    const auto cost = request.cost_raw[slot];
    const auto before = request.resource_balance_before[slot];
    const auto expected_after = cost > 0 ? before - cost : before;
    if (receipt.resource_balance_after[slot] != expected_after) return false;
  }
  return true;
}

}  // namespace

DomainConstructionActionSelectionV1
SelectDeterministicDomainConstructionActionV1(
    const std::span<const DomainConstructionCostLegalityPublicationV1>
        first_sample,
    const std::span<const DomainConstructionCostLegalityPublicationV1>
        second_sample) {
  DomainConstructionActionSelectionV1 output{};
  std::vector<const Publication*> first_actionable;
  std::vector<const Publication*> second_actionable;
  output.failure = ValidateSample(first_sample, first_actionable);
  if (output.failure != DomainConstructionActionSelectionFailureV1::none) {
    return output;
  }
  output.failure = ValidateSample(second_sample, second_actionable);
  if (output.failure != DomainConstructionActionSelectionFailureV1::none) {
    return output;
  }
  if (first_actionable.size() != second_actionable.size()) {
    output.failure =
        DomainConstructionActionSelectionFailureV1::candidate_set_drift;
    return output;
  }
  for (std::size_t index = 0; index < first_actionable.size(); ++index) {
    output.failure =
        CompareCandidate(*first_actionable[index], *second_actionable[index]);
    if (output.failure != DomainConstructionActionSelectionFailureV1::none) {
      return output;
    }
  }

  output.ready = true;
  output.request = MakeRequest(first_actionable.front()->candidate);
  return output;
}

bool BeginDomainConstructionSemanticActionV1(
    DomainConstructionSemanticActionStateV1& state,
    const std::span<const DomainConstructionCostLegalityPublicationV1>
        first_sample,
    const std::span<const DomainConstructionCostLegalityPublicationV1>
        second_sample,
    const DomainConstructionSubmitV1 submit, void* submit_context) {
  if (state.phase != DomainConstructionActionPhaseV1::idle) return false;
  const auto selection = SelectDeterministicDomainConstructionActionV1(
      first_sample, second_sample);
  state.selection_failure = selection.failure;
  if (!selection.ready || submit == nullptr) {
    state.phase = DomainConstructionActionPhaseV1::submit_failed;
    return false;
  }

  state.request = selection.request;
  ++state.submit_call_count;
  DomainConstructionSubmitAckV1 ack{};
  if (!submit(submit_context, state.request, ack)) {
    state.phase = DomainConstructionActionPhaseV1::submit_failed;
    return false;
  }
  state.ack_received = ack.accepted;
  state.ack_token = ack.ack_token;
  if (!ack.accepted || ack.ack_token == 0U) {
    state.phase = DomainConstructionActionPhaseV1::submit_rejected;
    return false;
  }
  state.phase = DomainConstructionActionPhaseV1::pending_receipt;
  state.applied = false;
  return true;
}

bool ObserveDomainConstructionFreshReceiptV1(
    DomainConstructionSemanticActionStateV1& state,
    const DomainConstructionFreshReceiptV1& receipt) {
  state.receipt_failure = DomainConstructionReceiptFailureV1::none;
  if (state.phase != DomainConstructionActionPhaseV1::pending_receipt) {
    state.receipt_failure = DomainConstructionReceiptFailureV1::not_pending;
    return false;
  }
  if (receipt.ack_token == 0U || receipt.ack_token != state.ack_token) {
    state.receipt_failure = DomainConstructionReceiptFailureV1::ack_token;
    return false;
  }
  if (receipt.binding.generation <= state.request.binding.generation ||
      receipt.binding.generation == 0U ||
      (receipt.binding.generation & 1U) != 0U) {
    state.receipt_failure =
        DomainConstructionReceiptFailureV1::stale_generation;
    return false;
  }
  if (receipt.binding.proof_epoch <= state.request.binding.proof_epoch) {
    state.receipt_failure =
        DomainConstructionReceiptFailureV1::stale_proof_epoch;
    return false;
  }
  if (receipt.binding.date_raw < state.request.binding.date_raw) {
    state.receipt_failure = DomainConstructionReceiptFailureV1::stale_date;
    return false;
  }
  if (receipt.candidate_id != state.request.candidate_id ||
      receipt.candidate_kind != state.request.candidate_kind) {
    state.receipt_failure = DomainConstructionReceiptFailureV1::identity;
    return false;
  }

  const bool target_state_observed =
      state.request.candidate_kind ==
              DomainConstructionCandidateKindV1::building_in_holding
          ? receipt.target_building_state_observed
          : receipt.target_holding_state_observed;
  if (!target_state_observed && !ExactResourceDeduction(state.request, receipt)) {
    state.receipt_failure =
        DomainConstructionReceiptFailureV1::evidence_missing;
    return false;
  }
  state.phase = DomainConstructionActionPhaseV1::applied;
  state.applied = true;
  return true;
}

}  // namespace xar::ck3::research
