#include "domain_construction_shared_glue_v1.hpp"

#include <utility>

namespace xar::ck3::shared {
namespace {

using NativeFailure = research::DomainConstructionNativeSubmitFailureV1;
using NativePhase = research::DomainConstructionNativeSubmitPhaseV1;
using Red = DomainConstructionSharedRedV1;

constexpr std::uint32_t Bit(const Red value) noexcept {
  return static_cast<std::uint32_t>(value);
}

void AddRed(DomainConstructionSharedGlueStateV1& state,
            const Red value) noexcept {
  state.red_flags |= Bit(value);
}

Red NativeFailureRed(const NativeFailure failure) noexcept {
  switch (failure) {
    case NativeFailure::candidate_identity:
    case NativeFailure::binding:
    case NativeFailure::native_context:
      return Red::candidate_binding;
    case NativeFailure::exact_build:
      return Red::exact_build;
    case NativeFailure::application_main_thread:
      return Red::application_main_thread;
    case NativeFailure::executor_missing:
      return Red::native_backend_unwired;
    case NativeFailure::validator_rejected:
      return Red::validator;
    case NativeFailure::materialize_failed:
      return Red::materialize;
    case NativeFailure::receiver_rejected:
      return Red::receiver;
    case NativeFailure::execution_trace:
      return Red::ownership_lifecycle;
    case NativeFailure::not_idle:
      return Red::duplicate_submit;
    case NativeFailure::none:
      return Red::none;
  }
  return Red::ownership_lifecycle;
}

struct BackendExecutorContext final {
  const DomainConstructionNativeBackendEnvironmentV1* environment = nullptr;
  const DomainConstructionNativeBackendAccessV1* backend = nullptr;
  Red stage_red = Red::none;
};

bool ExecuteBackend(
    void* opaque,
    const research::DomainConstructionNativeCommandContextV1& command,
    const research::DomainConstructionTransientNativeSubmitContextV1&
        transient,
    research::DomainConstructionNativeExecutionTraceV1& trace) {
  auto& execution = *static_cast<BackendExecutorContext*>(opaque);
  const auto& environment = *execution.environment;
  const auto& backend = *execution.backend;
  trace = {};
  trace.executor_kind = environment.offline_fixture_backend
                            ? research::DomainConstructionNativeExecutorKindV1::
                                  offline_fixture
                            : research::DomainConstructionNativeExecutorKindV1::
                                  exact_build_application_main;
  trace.exact_contract_addresses_used =
      environment.concrete_native_backend_bound &&
      environment.exact_build_admitted && environment.application_main_thread &&
      !environment.offline_fixture_backend;

  ++trace.validator_call_count;
  bool allowed = false;
  if (!backend.validate(backend.context, command, transient, allowed)) {
    execution.stage_red = Red::validator;
    return false;
  }
  trace.validator_allowed = allowed;
  if (!allowed) {
    trace.leftover_wrapper_lifecycle_complete = true;
    return true;
  }

  ++trace.materialize_call_count;
  std::uintptr_t owned_command = 0U;
  if (!backend.materialize(backend.context, command, transient,
                           owned_command) ||
      owned_command == 0U) {
    execution.stage_red = Red::materialize;
    return true;
  }
  trace.command_materialized = true;

  ++trace.receiver_call_count;
  bool accepted = false;
  std::uint64_t sequence = 0U;
  const bool receive_completed = backend.receive(
      backend.context, owned_command, command.receiver_flags, accepted,
      sequence);
  if (!receive_completed) execution.stage_red = Red::receiver;
  trace.receiver_accepted = receive_completed && accepted;
  trace.receiver_command_sequence =
      trace.receiver_accepted ? sequence : 0U;
  trace.transfer_holder_zeroed = owned_command == 0U;

  bool lifecycle_complete = trace.transfer_holder_zeroed;
  if (owned_command != 0U) {
    execution.stage_red = Red::ownership_lifecycle;
    lifecycle_complete =
        backend.release != nullptr &&
        backend.release(backend.context, owned_command) && owned_command == 0U;
  }
  trace.leftover_wrapper_lifecycle_complete = lifecycle_complete;
  trace.raw_pointer_persisted = false;
  return receive_completed;
}

bool BackendAccessComplete(
    const DomainConstructionNativeBackendAccessV1& backend) noexcept {
  return backend.validate != nullptr && backend.materialize != nullptr &&
         backend.receive != nullptr && backend.release != nullptr;
}

}  // namespace

bool PrepareDomainConstructionSharedCandidateV1(
    DomainConstructionSharedGlueStateV1& state,
    const std::span<
        const research::DomainConstructionCostLegalityPublicationV1>
        first_sample,
    const std::span<
        const research::DomainConstructionCostLegalityPublicationV1>
        second_sample) noexcept {
  try {
    if (state.phase != DomainConstructionSharedPhaseV1::idle) {
      AddRed(state, Red::duplicate_submit);
      return false;
    }
    const auto selection =
        research::SelectDeterministicDomainConstructionActionV1(first_sample,
                                                                second_sample);
    state.selection_failure = selection.failure;
    if (!selection.ready) {
      AddRed(state, Red::candidate_selection);
      state.phase = DomainConstructionSharedPhaseV1::red;
      return false;
    }
    state.candidate = selection.request;
    state.candidate_ready = true;
    // Until a retained CK3 candidate passes through this shared glue, the
    // generated request remains fixture/static-ready rather than live.
    state.candidate_live = false;
    state.phase = DomainConstructionSharedPhaseV1::candidate_ready;
    return true;
  } catch (...) {
    AddRed(state, Red::candidate_selection);
    state.phase = DomainConstructionSharedPhaseV1::red;
    return false;
  }
}

bool SubmitDomainConstructionSharedCandidateV1(
    DomainConstructionSharedGlueStateV1& state,
    const DomainConstructionNativeBackendEnvironmentV1& environment,
    const DomainConstructionNativeBackendAccessV1& backend,
    const research::DomainConstructionCandidateSnapshotBindingV1&
        observed_binding,
    const std::int32_t actor_or_holder_id,
    const std::uintptr_t new_holding_candidate_object) noexcept {
  try {
    if (state.phase != DomainConstructionSharedPhaseV1::candidate_ready) {
      AddRed(state, Red::duplicate_submit);
      return false;
    }
    const bool one_backend = environment.concrete_native_backend_bound !=
                             environment.offline_fixture_backend;
    if (!one_backend || !BackendAccessComplete(backend)) {
      AddRed(state, Red::native_backend_unwired);
      state.phase = DomainConstructionSharedPhaseV1::red;
      return false;
    }

    research::DomainConstructionTransientNativeSubmitContextV1 transient{};
    transient.observed_binding = observed_binding;
    transient.actor_or_holder_id = actor_or_holder_id;
    transient.new_holding_candidate_object = new_holding_candidate_object;
    transient.exact_build_identity_matches = environment.exact_build_admitted;
    transient.application_main_thread = environment.application_main_thread;

    BackendExecutorContext execution{&environment, &backend, Red::none};
    const auto executor_kind =
        environment.offline_fixture_backend
            ? research::DomainConstructionNativeExecutorKindV1::offline_fixture
            : research::DomainConstructionNativeExecutorKindV1::
                  exact_build_application_main;
    if (!research::BeginDomainConstructionNativeSubmitV1(
            state.native_submit, state.candidate, transient, executor_kind,
            ExecuteBackend, &execution)) {
      state.native_failure = state.native_submit.failure;
      AddRed(state, execution.stage_red == Red::none
                        ? NativeFailureRed(state.native_failure)
                        : execution.stage_red);
      state.phase = DomainConstructionSharedPhaseV1::red;
      return false;
    }
    state.native_failure = NativeFailure::none;
    state.phase = DomainConstructionSharedPhaseV1::pending_receipt;
    return true;
  } catch (...) {
    AddRed(state, Red::ownership_lifecycle);
    state.phase = DomainConstructionSharedPhaseV1::red;
    return false;
  }
}

bool ObserveDomainConstructionSharedReceiptV1(
    DomainConstructionSharedGlueStateV1& state,
    const research::DomainConstructionNativeReceiptSourceV1 source,
    const research::DomainConstructionFreshReceiptV1& receipt) noexcept {
  try {
    if (state.phase != DomainConstructionSharedPhaseV1::pending_receipt) {
      AddRed(state, Red::receipt);
      return false;
    }
    if (!research::ObserveDomainConstructionNativeReceiptV1(
            state.native_submit, source, receipt)) {
      state.receipt_failure = state.native_submit.semantic_action.receipt_failure;
      AddRed(state, Red::receipt);
      return false;
    }
    state.receipt_failure = research::DomainConstructionReceiptFailureV1::none;
    state.phase = DomainConstructionSharedPhaseV1::applied;
    return true;
  } catch (...) {
    AddRed(state, Red::receipt);
    return false;
  }
}

bool DomainConstructionSharedGlueHasRedV1(
    const DomainConstructionSharedGlueStateV1& state,
    const DomainConstructionSharedRedV1 red) noexcept {
  return (state.red_flags & Bit(red)) != 0U;
}

}  // namespace xar::ck3::shared
