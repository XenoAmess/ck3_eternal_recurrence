#include "domain_construction_shared_glue_v1.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <string>
#include <utility>

namespace {

using namespace xar::ck3;

research::DomainConstructionCostLegalityPublicationV1 Publication(
    std::string candidate_id,
    const research::DomainConstructionCandidateKindV1 kind) {
  research::DomainConstructionCostLegalityPublicationV1 publication{};
  publication.available = true;
  publication.publication_generation = 2U;
  auto& candidate = publication.candidate;
  candidate.ready = true;
  candidate.actionable = true;
  candidate.candidate_id = std::move(candidate_id);
  candidate.candidate_kind = kind;
  candidate.binding = {42U, 91U, 777};
  candidate.cost_raw = {10, 0, -1, 0, 0, 0, 0, 0};
  candidate.resource_balance_raw = {100, 0, 9, 0, 0, 0, 0, 0};
  candidate.resource_affordable.fill(true);
  candidate.native_affordable = true;
  candidate.native_final_legal = true;
  candidate.first_blocking_resource_slot =
      research::kDomainConstructionNoBlockingResourceSlotV1;
  candidate.rejection_reason =
      research::DomainConstructionCandidateRejectionReasonV1::none;
  candidate.unavailable =
      research::DomainConstructionCandidateCostLegalityUnavailableV1::none;
  return publication;
}

struct BackendFixture final {
  std::uint32_t validator_calls = 0U;
  std::uint32_t materialize_calls = 0U;
  std::uint32_t receiver_calls = 0U;
  std::uint32_t release_calls = 0U;
  bool validator_transport = true;
  bool validator_allowed = true;
  bool materialize_transport = true;
  bool receiver_transport = true;
  bool receiver_accepted = true;
  bool receiver_zeroes_holder = true;
  bool release_succeeds = true;
  std::uint64_t sequence = 7001U;
  std::uint32_t observed_receiver_flags = 0U;
};

bool Validate(
    void* opaque,
    const research::DomainConstructionNativeCommandContextV1&,
    const research::DomainConstructionTransientNativeSubmitContextV1&,
    bool& allowed) noexcept {
  auto& fixture = *static_cast<BackendFixture*>(opaque);
  ++fixture.validator_calls;
  allowed = fixture.validator_allowed;
  return fixture.validator_transport;
}

bool Materialize(
    void* opaque,
    const research::DomainConstructionNativeCommandContextV1&,
    const research::DomainConstructionTransientNativeSubmitContextV1&,
    std::uintptr_t& command) noexcept {
  auto& fixture = *static_cast<BackendFixture*>(opaque);
  ++fixture.materialize_calls;
  if (fixture.materialize_transport) command = 0xCAFEU;
  return fixture.materialize_transport;
}

bool Receive(void* opaque, std::uintptr_t& command,
             const std::uint32_t flags, bool& accepted,
             std::uint64_t& sequence) noexcept {
  auto& fixture = *static_cast<BackendFixture*>(opaque);
  ++fixture.receiver_calls;
  fixture.observed_receiver_flags = flags;
  accepted = fixture.receiver_accepted;
  sequence = fixture.sequence;
  if (fixture.receiver_zeroes_holder) command = 0U;
  return fixture.receiver_transport;
}

bool Release(void* opaque, std::uintptr_t& command) noexcept {
  auto& fixture = *static_cast<BackendFixture*>(opaque);
  ++fixture.release_calls;
  if (fixture.release_succeeds) command = 0U;
  return fixture.release_succeeds;
}

shared::DomainConstructionNativeBackendAccessV1 Access(
    BackendFixture& fixture) {
  return {&fixture, Validate, Materialize, Receive, Release};
}

shared::DomainConstructionNativeBackendEnvironmentV1 OfflineEnvironment() {
  return {true, true, false, true};
}

shared::DomainConstructionSharedGlueStateV1 PreparedBuilding() {
  const std::array first{
      Publication("holding:867:3",
                  research::DomainConstructionCandidateKindV1::new_holding),
      Publication("building:17:4:16777258",
                  research::DomainConstructionCandidateKindV1::
                      building_in_holding)};
  const std::array second{first[1], first[0]};
  shared::DomainConstructionSharedGlueStateV1 state{};
  assert(shared::PrepareDomainConstructionSharedCandidateV1(state, first,
                                                             second));
  assert(state.phase == shared::DomainConstructionSharedPhaseV1::candidate_ready);
  assert(state.candidate_ready);
  assert(!state.candidate_live);
  assert(state.candidate.candidate_id == "building:17:4:16777258");
  return state;
}

void TestConcreteCandidatePreparationAndSingleSubmit() {
  auto state = PreparedBuilding();
  BackendFixture fixture{};
  const auto access = Access(fixture);
  assert(shared::SubmitDomainConstructionSharedCandidateV1(
      state, OfflineEnvironment(), access, state.candidate.binding, 1337, 0U));
  assert(state.phase ==
         shared::DomainConstructionSharedPhaseV1::pending_receipt);
  assert(state.native_submit.executor_call_count == 1U);
  assert(state.native_submit.pending_ack);
  assert(!state.native_submit.production_native_path);
  assert(fixture.validator_calls == 1U);
  assert(fixture.materialize_calls == 1U);
  assert(fixture.receiver_calls == 1U);
  assert(fixture.release_calls == 0U);
  assert(fixture.observed_receiver_flags == 7U);

  assert(!shared::SubmitDomainConstructionSharedCandidateV1(
      state, OfflineEnvironment(), access, state.candidate.binding, 1337, 0U));
  assert(shared::DomainConstructionSharedGlueHasRedV1(
      state, shared::DomainConstructionSharedRedV1::duplicate_submit));
  assert(fixture.validator_calls == 1U);
  assert(fixture.materialize_calls == 1U);
  assert(fixture.receiver_calls == 1U);
}

void TestPendingAckRequiresFreshReceipt() {
  auto state = PreparedBuilding();
  BackendFixture fixture{};
  assert(shared::SubmitDomainConstructionSharedCandidateV1(
      state, OfflineEnvironment(), Access(fixture), state.candidate.binding,
      1337, 0U));

  research::DomainConstructionFreshReceiptV1 receipt{};
  receipt.ack_token = state.native_submit.semantic_action.ack_token;
  receipt.candidate_id = state.candidate.candidate_id;
  receipt.candidate_kind = state.candidate.candidate_kind;
  receipt.binding = state.candidate.binding;
  receipt.target_building_state_observed = true;
  assert(!shared::ObserveDomainConstructionSharedReceiptV1(
      state,
      research::DomainConstructionNativeReceiptSourceV1::target_building_state,
      receipt));
  assert(state.phase ==
         shared::DomainConstructionSharedPhaseV1::pending_receipt);
  assert(shared::DomainConstructionSharedGlueHasRedV1(
      state, shared::DomainConstructionSharedRedV1::receipt));
  assert(!state.native_submit.semantic_action.applied);

  receipt.binding = {44U, 92U, 778};
  assert(shared::ObserveDomainConstructionSharedReceiptV1(
      state,
      research::DomainConstructionNativeReceiptSourceV1::target_building_state,
      receipt));
  assert(state.phase == shared::DomainConstructionSharedPhaseV1::applied);
  assert(state.native_submit.semantic_action.applied);
}

void TestBackendUnwiredIsTypedRedAfterCandidateReady() {
  auto state = PreparedBuilding();
  BackendFixture fixture{};
  const shared::DomainConstructionNativeBackendEnvironmentV1 environment{
      true, true, false, false};
  assert(!shared::SubmitDomainConstructionSharedCandidateV1(
      state, environment, Access(fixture), state.candidate.binding, 1337, 0U));
  assert(state.phase == shared::DomainConstructionSharedPhaseV1::red);
  assert(shared::DomainConstructionSharedGlueHasRedV1(
      state, shared::DomainConstructionSharedRedV1::native_backend_unwired));
  assert(state.candidate_ready);
  assert(!state.candidate_live);
  assert(fixture.validator_calls == 0U);
}

void TestBindingDriftAndReceiverRejectionRemainTypedRed() {
  auto state = PreparedBuilding();
  auto observed = state.candidate.binding;
  observed.date_raw += 1;
  BackendFixture fixture{};
  assert(!shared::SubmitDomainConstructionSharedCandidateV1(
      state, OfflineEnvironment(), Access(fixture), observed, 1337, 0U));
  assert(state.native_failure ==
         research::DomainConstructionNativeSubmitFailureV1::binding);
  assert(shared::DomainConstructionSharedGlueHasRedV1(
      state, shared::DomainConstructionSharedRedV1::candidate_binding));
  assert(fixture.validator_calls == 0U);

  state = PreparedBuilding();
  fixture = {};
  fixture.receiver_accepted = false;
  assert(!shared::SubmitDomainConstructionSharedCandidateV1(
      state, OfflineEnvironment(), Access(fixture), state.candidate.binding,
      1337, 0U));
  assert(state.native_failure ==
         research::DomainConstructionNativeSubmitFailureV1::receiver_rejected);
  assert(shared::DomainConstructionSharedGlueHasRedV1(
      state, shared::DomainConstructionSharedRedV1::receiver));
  assert(fixture.validator_calls == 1U);
  assert(fixture.materialize_calls == 1U);
  assert(fixture.receiver_calls == 1U);
}

void TestOwnershipLifecycleFailureIsRedAndReleased() {
  auto state = PreparedBuilding();
  BackendFixture fixture{};
  fixture.receiver_zeroes_holder = false;
  assert(!shared::SubmitDomainConstructionSharedCandidateV1(
      state, OfflineEnvironment(), Access(fixture), state.candidate.binding,
      1337, 0U));
  assert(shared::DomainConstructionSharedGlueHasRedV1(
      state, shared::DomainConstructionSharedRedV1::ownership_lifecycle));
  assert(fixture.release_calls == 1U);
}

void TestCandidateDriftIsTypedBeforeBackend() {
  const std::array first{Publication(
      "building:17:4:16777258",
      research::DomainConstructionCandidateKindV1::building_in_holding)};
  auto second = first;
  second[0].candidate.binding.proof_epoch += 1U;
  shared::DomainConstructionSharedGlueStateV1 state{};
  assert(!shared::PrepareDomainConstructionSharedCandidateV1(state, first,
                                                              second));
  assert(state.selection_failure ==
         research::DomainConstructionActionSelectionFailureV1::
             proof_epoch_drift);
  assert(shared::DomainConstructionSharedGlueHasRedV1(
      state, shared::DomainConstructionSharedRedV1::candidate_selection));
}

void TestNewHoldingRequiresBorrowedNativeObject() {
  const std::array sample{Publication(
      "holding:867:3",
      research::DomainConstructionCandidateKindV1::new_holding)};
  shared::DomainConstructionSharedGlueStateV1 state{};
  assert(shared::PrepareDomainConstructionSharedCandidateV1(state, sample,
                                                             sample));
  BackendFixture fixture{};
  assert(!shared::SubmitDomainConstructionSharedCandidateV1(
      state, OfflineEnvironment(), Access(fixture), state.candidate.binding,
      1337, 0U));
  assert(shared::DomainConstructionSharedGlueHasRedV1(
      state, shared::DomainConstructionSharedRedV1::candidate_binding));
  assert(fixture.validator_calls == 0U);

  state = {};
  fixture = {};
  assert(shared::PrepareDomainConstructionSharedCandidateV1(state, sample,
                                                             sample));
  assert(shared::SubmitDomainConstructionSharedCandidateV1(
      state, OfflineEnvironment(), Access(fixture), state.candidate.binding,
      1337, 0x12345000U));
  assert(state.phase ==
         shared::DomainConstructionSharedPhaseV1::pending_receipt);
  assert(fixture.validator_calls == 1U);
}

}  // namespace

int main() {
  TestConcreteCandidatePreparationAndSingleSubmit();
  TestPendingAckRequiresFreshReceipt();
  TestBackendUnwiredIsTypedRedAfterCandidateReady();
  TestBindingDriftAndReceiverRejectionRemainTypedRed();
  TestOwnershipLifecycleFailureIsRedAndReleased();
  TestCandidateDriftIsTypedBeforeBackend();
  TestNewHoldingRequiresBorrowedNativeObject();
  return 0;
}
