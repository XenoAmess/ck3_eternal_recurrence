#include "domain_construction_native_submit_adapter_v1.hpp"

#include <cassert>
#include <cstdint>
#include <string>

namespace {

using namespace xar::ck3::research;

DomainConstructionSemanticActionRequestV1 Request(
    std::string candidate_id, const DomainConstructionCandidateKindV1 kind) {
  DomainConstructionSemanticActionRequestV1 request{};
  request.candidate_id = std::move(candidate_id);
  request.candidate_kind = kind;
  request.binding = {42U, 91U, 777};
  request.cost_raw = {10, 0, -1, 0, 0, 0, 0, 0};
  request.resource_balance_before = {100, 0, 9, 0, 0, 0, 0, 0};
  return request;
}

DomainConstructionTransientNativeSubmitContextV1 Transient(
    const bool new_holding = false) {
  DomainConstructionTransientNativeSubmitContextV1 context{};
  context.observed_binding = {42U, 91U, 777};
  context.actor_or_holder_id = 1337;
  context.new_holding_candidate_object = new_holding ? 0x12345000U : 0U;
  context.exact_build_identity_matches = true;
  context.application_main_thread = true;
  return context;
}

struct ExecutorFixture final {
  std::uint64_t calls = 0U;
  bool return_value = true;
  bool validator_allowed = true;
  bool materialized = true;
  bool receiver_accepted = true;
  std::uint64_t sequence = 7001U;
  bool exact_addresses = false;
  std::uint32_t observed_validator_rva = 0U;
  std::uint32_t observed_receiver_rva = 0U;
  std::int32_t observed_actor_or_holder_id = -1;
};

bool OfflineExecutor(
    void* context, const DomainConstructionNativeCommandContextV1& command,
    const DomainConstructionTransientNativeSubmitContextV1&,
    DomainConstructionNativeExecutionTraceV1& trace) {
  auto& fixture = *static_cast<ExecutorFixture*>(context);
  ++fixture.calls;
  fixture.observed_validator_rva = command.validator_rva;
  fixture.observed_receiver_rva = command.receiver_rva;
  fixture.observed_actor_or_holder_id = command.actor_or_holder_id;
  trace.executor_kind = DomainConstructionNativeExecutorKindV1::offline_fixture;
  trace.exact_contract_addresses_used = fixture.exact_addresses;
  trace.validator_call_count = 1U;
  trace.validator_allowed = fixture.validator_allowed;
  trace.materialize_call_count = fixture.validator_allowed ? 1U : 0U;
  trace.command_materialized =
      fixture.validator_allowed && fixture.materialized;
  trace.receiver_call_count = trace.command_materialized ? 1U : 0U;
  trace.receiver_accepted =
      trace.command_materialized && fixture.receiver_accepted;
  trace.receiver_command_sequence = trace.receiver_accepted ? fixture.sequence : 0U;
  trace.transfer_holder_zeroed = trace.receiver_call_count == 1U;
  trace.leftover_wrapper_lifecycle_complete =
      trace.validator_call_count == 1U;
  trace.raw_pointer_persisted = false;
  return fixture.return_value;
}

void TestBuildingContextAndExactlyOnePendingAck() {
  const auto request = Request(
      "building:17:4:16777258",
      DomainConstructionCandidateKindV1::building_in_holding);
  const auto transient = Transient();
  DomainConstructionNativeCommandContextV1 command{};
  DomainConstructionNativeSubmitFailureV1 failure{};
  assert(BuildDomainConstructionNativeCommandContextV1(
      request, transient, command, failure));
  assert(failure == DomainConstructionNativeSubmitFailureV1::none);
  assert(command.actor_or_holder_id == 1337);
  assert(command.holding_province_id == 17);
  assert(command.candidate_selector == 4);
  assert(command.building_type_id == 16777258);
  assert(command.candidate_province_id == -1);
  assert(command.validator_rva == kDomainConstructionBuildingValidatorRvaV1);
  assert(command.receiver_rva == kDomainConstructionReceiverRvaV1);
  assert(command.receiver_flags == 7U);

  ExecutorFixture executor{};
  DomainConstructionNativeSubmitStateV1 state{};
  assert(BeginDomainConstructionNativeSubmitV1(
      state, request, transient,
      DomainConstructionNativeExecutorKindV1::offline_fixture,
      OfflineExecutor, &executor));
  assert(executor.calls == 1U);
  assert(state.executor_call_count == 1U);
  assert(state.phase ==
         DomainConstructionNativeSubmitPhaseV1::pending_receipt);
  assert(state.pending_ack);
  assert(!state.production_native_path);
  assert(!state.semantic_action.applied);
  assert(state.semantic_action.ack_token == 7001U);

  assert(!BeginDomainConstructionNativeSubmitV1(
      state, request, transient,
      DomainConstructionNativeExecutorKindV1::offline_fixture,
      OfflineExecutor, &executor));
  assert(executor.calls == 1U);
  assert(state.executor_call_count == 1U);
}

void TestNewHoldingContextAndFreshHoldingReceipt() {
  const auto request = Request(
      "holding:867:3", DomainConstructionCandidateKindV1::new_holding);
  const auto transient = Transient(true);
  ExecutorFixture executor{};
  DomainConstructionNativeSubmitStateV1 state{};
  assert(BeginDomainConstructionNativeSubmitV1(
      state, request, transient,
      DomainConstructionNativeExecutorKindV1::offline_fixture,
      OfflineExecutor, &executor));
  assert(state.command.candidate_province_id == 867);
  assert(state.command.candidate_selector == 3);
  assert(state.command.holding_province_id == -1);
  assert(state.command.building_type_id == -1);
  assert(state.command.validator_rva ==
         kDomainConstructionHoldingValidatorRvaV1);
  assert(executor.observed_actor_or_holder_id == 1337);

  DomainConstructionFreshReceiptV1 stale{};
  stale.ack_token = state.semantic_action.ack_token;
  stale.candidate_id = request.candidate_id;
  stale.candidate_kind = request.candidate_kind;
  stale.binding = request.binding;
  stale.target_holding_state_observed = true;
  assert(!ObserveDomainConstructionNativeReceiptV1(
      state, DomainConstructionNativeReceiptSourceV1::target_holding_state,
      stale));
  assert(state.phase ==
         DomainConstructionNativeSubmitPhaseV1::pending_receipt);

  auto fresh = stale;
  fresh.binding = {44U, 92U, 778};
  assert(ObserveDomainConstructionNativeReceiptV1(
      state, DomainConstructionNativeReceiptSourceV1::target_holding_state,
      fresh));
  assert(state.phase == DomainConstructionNativeSubmitPhaseV1::applied);
  assert(state.semantic_action.applied);
  assert(!state.pending_ack);
  assert(state.applied_receipt_source_observed);
  assert(state.applied_receipt_source ==
         DomainConstructionNativeReceiptSourceV1::target_holding_state);
}

void TestAckCannotMasqueradeAsApplied() {
  const auto request = Request(
      "building:17:4:16777258",
      DomainConstructionCandidateKindV1::building_in_holding);
  ExecutorFixture executor{};
  DomainConstructionNativeSubmitStateV1 state{};
  assert(BeginDomainConstructionNativeSubmitV1(
      state, request, Transient(),
      DomainConstructionNativeExecutorKindV1::offline_fixture,
      OfflineExecutor, &executor));
  assert(state.pending_ack && !state.semantic_action.applied);

  DomainConstructionFreshReceiptV1 receipt{};
  receipt.ack_token = state.semantic_action.ack_token;
  receipt.candidate_id = request.candidate_id;
  receipt.candidate_kind = request.candidate_kind;
  receipt.binding = {44U, 92U, 778};
  assert(!ObserveDomainConstructionNativeReceiptV1(
      state, DomainConstructionNativeReceiptSourceV1::target_building_state,
      receipt));
  assert(state.phase ==
         DomainConstructionNativeSubmitPhaseV1::pending_receipt);
  assert(!state.semantic_action.applied);

  receipt.resource_balances_observed = true;
  receipt.resource_balance_after = request.resource_balance_before;
  receipt.resource_balance_after[0] -= 10;
  assert(ObserveDomainConstructionNativeReceiptV1(
      state, DomainConstructionNativeReceiptSourceV1::exact_resource_deduction,
      receipt));
  assert(state.phase == DomainConstructionNativeSubmitPhaseV1::applied);
  assert(state.applied_receipt_source ==
         DomainConstructionNativeReceiptSourceV1::exact_resource_deduction);
}

void TestTypedPreSubmitAndNativeStageFailures() {
  auto request = Request(
      "building:17:4:16777258",
      DomainConstructionCandidateKindV1::building_in_holding);
  auto transient = Transient();
  ExecutorFixture executor{};
  DomainConstructionNativeSubmitStateV1 state{};

  request.binding.date_raw = 778;
  assert(!BeginDomainConstructionNativeSubmitV1(
      state, request, transient,
      DomainConstructionNativeExecutorKindV1::offline_fixture,
      OfflineExecutor, &executor));
  assert(state.failure == DomainConstructionNativeSubmitFailureV1::binding);
  assert(executor.calls == 0U);

  request = Request("holding:867:3",
                    DomainConstructionCandidateKindV1::new_holding);
  transient = Transient(false);
  state = {};
  assert(!BeginDomainConstructionNativeSubmitV1(
      state, request, transient,
      DomainConstructionNativeExecutorKindV1::offline_fixture,
      OfflineExecutor, &executor));
  assert(state.failure ==
         DomainConstructionNativeSubmitFailureV1::native_context);
  assert(executor.calls == 0U);

  request = Request("building:17:4:16777258",
                    DomainConstructionCandidateKindV1::building_in_holding);
  transient = Transient();
  executor.validator_allowed = false;
  state = {};
  assert(!BeginDomainConstructionNativeSubmitV1(
      state, request, transient,
      DomainConstructionNativeExecutorKindV1::offline_fixture,
      OfflineExecutor, &executor));
  assert(state.failure ==
         DomainConstructionNativeSubmitFailureV1::validator_rejected);
  assert(state.phase == DomainConstructionNativeSubmitPhaseV1::rejected);

  executor.validator_allowed = true;
  executor.receiver_accepted = false;
  state = {};
  assert(!BeginDomainConstructionNativeSubmitV1(
      state, request, transient,
      DomainConstructionNativeExecutorKindV1::offline_fixture,
      OfflineExecutor, &executor));
  assert(state.failure ==
         DomainConstructionNativeSubmitFailureV1::receiver_rejected);
  assert(state.phase == DomainConstructionNativeSubmitPhaseV1::rejected);
}

void TestOfflineCallbackCannotClaimProduction() {
  const auto request = Request(
      "building:17:4:16777258",
      DomainConstructionCandidateKindV1::building_in_holding);
  ExecutorFixture executor{};
  executor.exact_addresses = true;
  DomainConstructionNativeSubmitStateV1 state{};
  assert(!BeginDomainConstructionNativeSubmitV1(
      state, request, Transient(),
      DomainConstructionNativeExecutorKindV1::exact_build_application_main,
      OfflineExecutor, &executor));
  assert(state.failure ==
         DomainConstructionNativeSubmitFailureV1::execution_trace);
  assert(!state.production_native_path);
  assert(!state.semantic_action.applied);
}

}  // namespace

int main() {
  TestBuildingContextAndExactlyOnePendingAck();
  TestNewHoldingContextAndFreshHoldingReceipt();
  TestAckCannotMasqueradeAsApplied();
  TestTypedPreSubmitAndNativeStageFailures();
  TestOfflineCallbackCannotClaimProduction();
  return 0;
}
