#include "domain_construction_semantic_action_core_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <string>
#include <utility>

namespace {

using namespace xar::ck3::research;

DomainConstructionCostLegalityPublicationV1 ActionablePublication(
    std::string candidate_id, const DomainConstructionCandidateKindV1 kind,
    const std::int64_t primary_cost, const std::int64_t primary_balance) {
  DomainConstructionCostLegalityPublicationV1 publication{};
  publication.available = true;
  publication.publication_generation = 2U;
  auto& candidate = publication.candidate;
  candidate.ready = true;
  candidate.actionable = true;
  candidate.candidate_id = std::move(candidate_id);
  candidate.candidate_kind = kind;
  candidate.binding = {42U, 91U, 777};
  candidate.cost_raw = {primary_cost, 0, -1, 0, 0, 0, 0, 0};
  candidate.resource_balance_raw = {
      primary_balance, 0, 9, 0, 0, 0, 0, 0};
  candidate.resource_affordable.fill(true);
  candidate.native_affordable = true;
  candidate.native_final_legal = true;
  candidate.first_blocking_resource_slot =
      kDomainConstructionNoBlockingResourceSlotV1;
  candidate.blocking_resource_mask = 0U;
  candidate.rejection_reason =
      DomainConstructionCandidateRejectionReasonV1::none;
  candidate.unavailable =
      DomainConstructionCandidateCostLegalityUnavailableV1::none;
  return publication;
}

DomainConstructionCostLegalityPublicationV1 RejectedPublication() {
  auto publication = ActionablePublication(
      "holding:900:1", DomainConstructionCandidateKindV1::new_holding, 100,
      100);
  publication.candidate.actionable = false;
  publication.candidate.native_affordable = false;
  publication.candidate.resource_affordable[0] = false;
  publication.candidate.first_blocking_resource_slot = 0U;
  publication.candidate.blocking_resource_mask = 1U;
  publication.candidate.rejection_reason =
      DomainConstructionCandidateRejectionReasonV1::insufficient_resource;
  return publication;
}

struct SubmitFixture final {
  std::uint64_t call_count = 0;
  bool transport_success = true;
  bool accepted = true;
  std::uint64_t ack_token = 7001U;
  std::string received_candidate_id;
};

bool Submit(void* context,
            const DomainConstructionSemanticActionRequestV1& request,
            DomainConstructionSubmitAckV1& ack) {
  auto& fixture = *static_cast<SubmitFixture*>(context);
  ++fixture.call_count;
  fixture.received_candidate_id = request.candidate_id;
  ack.accepted = fixture.accepted;
  ack.ack_token = fixture.ack_token;
  return fixture.transport_success;
}

std::array<DomainConstructionCostLegalityPublicationV1, 3> FirstSample() {
  return {
      ActionablePublication(
          "holding:867:3", DomainConstructionCandidateKindV1::new_holding,
          20, 200),
      RejectedPublication(),
      ActionablePublication(
          "building:17:4:16777258",
          DomainConstructionCandidateKindV1::building_in_holding, 10, 100),
  };
}

std::array<DomainConstructionCostLegalityPublicationV1, 3> SecondSample() {
  return {
      ActionablePublication(
          "building:17:4:16777258",
          DomainConstructionCandidateKindV1::building_in_holding, 10, 100),
      ActionablePublication(
          "holding:867:3", DomainConstructionCandidateKindV1::new_holding,
          20, 200),
      RejectedPublication(),
  };
}

void TestDeterministicSingleSubmitAckRemainsPending() {
  const auto first = FirstSample();
  const auto second = SecondSample();
  const auto selection = SelectDeterministicDomainConstructionActionV1(
      first, second);
  assert(selection.ready);
  assert(selection.request.candidate_id == "building:17:4:16777258");

  SubmitFixture submit{};
  DomainConstructionSemanticActionStateV1 state{};
  assert(BeginDomainConstructionSemanticActionV1(
      state, first, second, Submit, &submit));
  assert(submit.call_count == 1U);
  assert(state.submit_call_count == 1U);
  assert(submit.received_candidate_id == "building:17:4:16777258");
  assert(state.ack_received);
  assert(state.phase == DomainConstructionActionPhaseV1::pending_receipt);
  assert(!state.applied);

  assert(!BeginDomainConstructionSemanticActionV1(
      state, first, second, Submit, &submit));
  assert(submit.call_count == 1U);
  assert(state.submit_call_count == 1U);

  DomainConstructionFreshReceiptV1 stale{};
  stale.ack_token = state.ack_token;
  stale.candidate_id = state.request.candidate_id;
  stale.candidate_kind = state.request.candidate_kind;
  stale.binding = state.request.binding;
  stale.target_building_state_observed = true;
  assert(!ObserveDomainConstructionFreshReceiptV1(state, stale));
  assert(state.receipt_failure ==
         DomainConstructionReceiptFailureV1::stale_generation);
  assert(state.phase == DomainConstructionActionPhaseV1::pending_receipt);
  assert(!state.applied);

  auto fresh = stale;
  fresh.binding = {44U, 92U, 777};
  assert(ObserveDomainConstructionFreshReceiptV1(state, fresh));
  assert(state.phase == DomainConstructionActionPhaseV1::applied);
  assert(state.applied);
}

void TestFreshExactResourceDeductionAppliesHolding() {
  const std::array first{
      ActionablePublication(
          "holding:867:3", DomainConstructionCandidateKindV1::new_holding,
          20, 200)};
  const auto second = first;
  SubmitFixture submit{};
  DomainConstructionSemanticActionStateV1 state{};
  assert(BeginDomainConstructionSemanticActionV1(
      state, first, second, Submit, &submit));

  DomainConstructionFreshReceiptV1 receipt{};
  receipt.ack_token = state.ack_token;
  receipt.candidate_id = state.request.candidate_id;
  receipt.candidate_kind = state.request.candidate_kind;
  receipt.binding = {44U, 92U, 778};
  receipt.resource_balances_observed = true;
  receipt.resource_balance_after = state.request.resource_balance_before;
  receipt.resource_balance_after[0] -= 20;
  assert(ObserveDomainConstructionFreshReceiptV1(state, receipt));
  assert(state.applied);
}

void TestAckAndNonExactReceiptNeverMasqueradeAsApplied() {
  const std::array first{
      ActionablePublication(
          "holding:867:3", DomainConstructionCandidateKindV1::new_holding,
          20, 200)};
  const auto second = first;
  SubmitFixture submit{};
  DomainConstructionSemanticActionStateV1 state{};
  assert(BeginDomainConstructionSemanticActionV1(
      state, first, second, Submit, &submit));
  assert(state.ack_received && !state.applied);

  DomainConstructionFreshReceiptV1 receipt{};
  receipt.ack_token = state.ack_token;
  receipt.candidate_id = state.request.candidate_id;
  receipt.candidate_kind = state.request.candidate_kind;
  receipt.binding = {44U, 92U, 778};
  receipt.resource_balances_observed = true;
  receipt.resource_balance_after = state.request.resource_balance_before;
  assert(!ObserveDomainConstructionFreshReceiptV1(state, receipt));
  assert(state.receipt_failure ==
         DomainConstructionReceiptFailureV1::evidence_missing);
  assert(state.phase == DomainConstructionActionPhaseV1::pending_receipt);
  assert(!state.applied);

  SubmitFixture rejected_submit{};
  rejected_submit.accepted = false;
  DomainConstructionSemanticActionStateV1 rejected_state{};
  assert(!BeginDomainConstructionSemanticActionV1(
      rejected_state, first, second, Submit, &rejected_submit));
  assert(rejected_state.phase ==
         DomainConstructionActionPhaseV1::submit_rejected);
  assert(!rejected_state.applied);
}

void TestDoubleSampleDriftIsRejectedBeforeSubmit() {
  const std::array first{
      ActionablePublication(
          "building:17:4:16777258",
          DomainConstructionCandidateKindV1::building_in_holding, 10, 100)};
  auto second = first;

  second[0].candidate.candidate_id = "building:17:5:16777258";
  auto selection = SelectDeterministicDomainConstructionActionV1(first, second);
  assert(selection.failure ==
         DomainConstructionActionSelectionFailureV1::identity_drift);

  second = first;
  second[0].candidate.binding.generation = 44U;
  selection = SelectDeterministicDomainConstructionActionV1(first, second);
  assert(selection.failure ==
         DomainConstructionActionSelectionFailureV1::generation_drift);

  second = first;
  second[0].candidate.binding.proof_epoch = 92U;
  selection = SelectDeterministicDomainConstructionActionV1(first, second);
  assert(selection.failure ==
         DomainConstructionActionSelectionFailureV1::proof_epoch_drift);

  second = first;
  second[0].candidate.binding.date_raw = 778;
  selection = SelectDeterministicDomainConstructionActionV1(first, second);
  assert(selection.failure ==
         DomainConstructionActionSelectionFailureV1::date_drift);

  second = first;
  second[0].candidate.cost_raw[0] = 11;
  selection = SelectDeterministicDomainConstructionActionV1(first, second);
  assert(selection.failure ==
         DomainConstructionActionSelectionFailureV1::cost_drift);

  second = first;
  second[0].candidate.resource_balance_raw[0] = 101;
  selection = SelectDeterministicDomainConstructionActionV1(first, second);
  assert(selection.failure ==
         DomainConstructionActionSelectionFailureV1::resource_drift);

  second = first;
  second[0].candidate.native_final_legal = false;
  selection = SelectDeterministicDomainConstructionActionV1(first, second);
  assert(selection.failure ==
         DomainConstructionActionSelectionFailureV1::native_final_drift);

  SubmitFixture submit{};
  DomainConstructionSemanticActionStateV1 state{};
  assert(!BeginDomainConstructionSemanticActionV1(
      state, first, second, Submit, &submit));
  assert(submit.call_count == 0U);
  assert(state.submit_call_count == 0U);
}

}  // namespace

int main() {
  TestDeterministicSingleSubmitAckRemainsPending();
  TestFreshExactResourceDeductionAppliesHolding();
  TestAckAndNonExactReceiptNeverMasqueradeAsApplied();
  TestDoubleSampleDriftIsRejectedBeforeSubmit();
  return 0;
}
