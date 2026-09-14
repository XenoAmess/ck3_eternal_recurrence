#include "active_scheme_paused_live_native_glue_v1_private.hpp"

namespace xar::bridge {
namespace {

using Failure = ActiveSchemePausedLiveNativeGlueV1PrivateFailure;
using State = ActiveSchemePausedLiveNativeGlueV1PrivateState;
using Execution = ActiveSchemePausedLiveNativeGlueV1PrivateExecution;

bool CompleteSourceAccess(
    const ActiveSchemeStateV1PrivateSourceAccess &access) noexcept {
  return access.exact_build_admitted &&
         access.admitted_executable_sha256 ==
             kActiveSchemeStateV1PrivateObserverExecutableSha256 &&
         access.capture_frame != nullptr && access.resolve_root != nullptr &&
         access.resolve_container != nullptr && access.read_row != nullptr;
}

bool Begin(State &state, const Execution &execution,
           Failure &failure) noexcept {
  failure = Failure::not_bound;
  if (!state.attached || !state.readiness.candidate_core_ready) return false;
  if (state.execution_active) {
    failure = Failure::reentrant_execution;
    return false;
  }
  if (execution.current_thread_id == 0 ||
      execution.application_main_thread_id == 0 ||
      execution.current_thread_id != execution.application_main_thread_id) {
    failure = Failure::not_application_main_thread;
    return false;
  }
  state.execution_active = true;
  state.active_current_thread_id = execution.current_thread_id;
  state.active_application_main_thread_id =
      execution.application_main_thread_id;
  failure = Failure::none;
  return true;
}

void End(State &state) noexcept {
  state.active_current_thread_id = 0;
  state.active_application_main_thread_id = 0;
  state.execution_active = false;
}

bool CaptureObservationThunk(
    void *context, ActiveSchemeStateV1PrivateObservation &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  if (!state.attached || !state.execution_active) return false;
  auto access = state.source_access;
  access.current_thread_id = state.active_current_thread_id;
  access.application_main_thread_id =
      state.active_application_main_thread_id;
  ActiveSchemeStateV1PrivateSourceResult result{};
  const bool ok = ObserveActiveSchemeStateV1PrivateSource(access, result);
  state.last_source_failure = result.failure;
  output = result.observation;
  return ok;
}

bool CapturePreconditionThunk(
    void *context,
    ActiveSchemeSemanticActionV1PrivatePrecondition &output) noexcept {
  auto &state = *static_cast<State *>(context);
  output = {};
  return state.attached && state.execution_active &&
         state.capture_precondition != nullptr &&
         state.capture_precondition(state.precondition_context, output);
}

bool ResolveDefinitionInternal(
    State &state, std::string_view interaction_key,
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease
        &output) noexcept {
  output = {};
  const auto operation = state.command_state.operations.resolve_interaction;
  return operation != nullptr &&
         operation(state.command_state.operation_context, interaction_key,
                   output);
}

} // namespace

bool BindActiveSchemePausedLiveNativeGlueV1Private(
    const ActiveSchemePausedLiveNativeGlueV1PrivateEnvironment &environment,
    State &state,
    ActiveSchemePausedLiveNativeGlueV1PrivateReadiness &readiness) noexcept {
  readiness = {};
  readiness.failure = Failure::binding_contract;
  if (!environment.binding_enabled || state.attached) return false;
  if (environment.source_access.admitted_executable_sha256 !=
          kActiveSchemeStateV1PrivateObserverExecutableSha256 ||
      environment.command_binding.admitted_executable_sha256 !=
          kActiveSchemeSemanticActionV1PrivateExecutableSha256 ||
      environment.definition_binding.admitted_executable_sha256 !=
          kActiveSchemeInteractionDefinitionResolverV1PrivateExecutableSha256 ||
      environment.command_binding.admitted_game_version !=
          kActiveSchemeSemanticActionV1PrivateNativeCommandGameVersion ||
      environment.definition_binding.admitted_game_version !=
          kActiveSchemeInteractionDefinitionResolverV1PrivateGameVersion) {
    readiness.failure = Failure::exact_build_mismatch;
    return false;
  }
  readiness.exact_build_bound = true;
  if (!CompleteSourceAccess(environment.source_access)) {
    readiness.failure = Failure::source_access_unavailable;
    return false;
  }
  readiness.paused_observation_bound = true;
  if (environment.capture_precondition == nullptr) {
    readiness.failure = Failure::precondition_access_unavailable;
    return false;
  }
  readiness.native_precondition_bound = true;

  state = {};
  state.source_access = environment.source_access;
  state.precondition_context = environment.precondition_context;
  state.capture_precondition = environment.capture_precondition;
  state.action_access = {&state, &CaptureObservationThunk,
                         &CapturePreconditionThunk, nullptr};

  auto command_binding = environment.command_binding;
  if (!BindActiveSchemeInteractionDefinitionResolverV1Private(
          environment.definition_binding, state.definition_state,
          command_binding)) {
    state = {};
    readiness.failure = Failure::definition_binding_rejected;
    return false;
  }
  readiness.stable_definition_bound = true;
  if (!BindActiveSchemeSemanticActionV1PrivateNativeCommand(
          command_binding, state.command_state, state.action_access,
          state.action_environment)) {
    state = {};
    readiness.failure = Failure::command_binding_rejected;
    return false;
  }
  readiness.native_single_submit_bound = true;
  readiness.candidate_core_ready = true;
  readiness.failure = Failure::none;
  state.readiness = readiness;
  state.last_source_failure =
      ActiveSchemeStateV1PrivateSourceFailure::none;
  state.last_action_failure = ActiveSchemeSemanticActionV1PrivateFailure::none;
  state.attached = true;
  return true;
}

bool CaptureActiveSchemePausedLiveSnapshotV1Private(
    State &state, const Execution &execution,
    ActiveSchemeStateV1PrivateObservation &output,
    Failure &failure) noexcept {
  output = {};
  if (!Begin(state, execution, failure)) return false;
  const bool ok = CaptureObservationThunk(&state, output);
  End(state);
  if (!ok || output.status != ActiveSchemeStateV1PrivateStatus::available) {
    failure = Failure::observation_red;
    return false;
  }
  failure = Failure::none;
  return true;
}

bool ResolveActiveSchemePausedLiveDefinitionV1Private(
    State &state, const Execution &execution,
    std::string_view interaction_key,
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease &output,
    Failure &failure) noexcept {
  output = {};
  if (!Begin(state, execution, failure)) return false;
  const bool ok = ResolveDefinitionInternal(state, interaction_key, output);
  End(state);
  if (!ok) {
    failure = Failure::definition_red;
    return false;
  }
  failure = Failure::none;
  return true;
}

bool CaptureActiveSchemePausedLivePreconditionV1Private(
    State &state, const Execution &execution,
    ActiveSchemeSemanticActionV1PrivatePrecondition &output,
    Failure &failure) noexcept {
  output = {};
  if (!Begin(state, execution, failure)) return false;
  const bool ok = CapturePreconditionThunk(&state, output);
  End(state);
  if (!ok || !output.available) {
    failure = Failure::precondition_red;
    return false;
  }
  failure = Failure::none;
  return true;
}

ActiveSchemeSemanticActionV1PrivateAckStatus
ExecuteActiveSchemePausedLiveNativeGlueV1Private(
    State &state, const Execution &execution,
    const ActiveSchemeSemanticActionV1PrivateRequest &request,
    ActiveSchemeSemanticActionV1PrivateAck &ack,
    Failure &failure) noexcept {
  ack = {};
  if (!Begin(state, execution, failure)) return ack.status;
  const auto status = ExecuteActiveSchemeSemanticActionV1Private(
      state.action_environment, state.action_access, request, ack);
  End(state);
  state.last_action_failure = ack.failure;
  if (status != ActiveSchemeSemanticActionV1PrivateAckStatus::
                    submitted_verification_pending ||
      !ack.verification_pending || !ack.submit_attempted ||
      ack.submit_call_count != 1) {
    failure = Failure::action_red;
    return status;
  }
  failure = Failure::none;
  return status;
}

ActiveSchemeSemanticActionV1PrivateReceiptStatus
VerifyActiveSchemePausedLiveNativeGlueReceiptV1Private(
    State &state, const Execution &execution,
    const ActiveSchemeSemanticActionV1PrivateAck &ack,
    ActiveSchemeSemanticActionV1PrivateReceipt &receipt,
    Failure &failure) noexcept {
  receipt = {};
  if (!Begin(state, execution, failure)) return receipt.status;
  const auto status = VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
      state.action_access, ack, receipt);
  End(state);
  state.last_action_failure = receipt.failure;
  if (status != ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied ||
      !receipt.postcondition_verified) {
    failure = Failure::receipt_red;
    return status;
  }
  failure = Failure::none;
  return status;
}

std::string_view ActiveSchemePausedLiveNativeGlueV1PrivateFailureName(
    Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::binding_contract: return "binding_contract";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::source_access_unavailable: return "source_access_unavailable";
  case Failure::precondition_access_unavailable:
    return "precondition_access_unavailable";
  case Failure::definition_binding_rejected:
    return "definition_binding_rejected";
  case Failure::command_binding_rejected:
    return "command_binding_rejected";
  case Failure::not_bound: return "not_bound";
  case Failure::reentrant_execution: return "reentrant_execution";
  case Failure::not_application_main_thread:
    return "not_application_main_thread";
  case Failure::observation_red: return "observation_red";
  case Failure::definition_red: return "definition_red";
  case Failure::precondition_red: return "precondition_red";
  case Failure::action_red: return "action_red";
  case Failure::receipt_red: return "receipt_red";
  }
  return "unknown";
}

} // namespace xar::bridge
