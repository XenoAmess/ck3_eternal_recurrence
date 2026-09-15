#include "xar_bridge/major_decision_found_kingdom_shared_glue_v1.hpp"

#include <windows.h>

#include <atomic>
#include <string>
#include <string_view>
#include <utility>

namespace xar::bridge {
namespace {

using Completion = MajorDecisionFoundKingdomSharedCompletionV1;
using Failure = MajorDecisionFoundKingdomSharedFailureV1;
using MailboxState = ck3_11906::MainThreadQueryMailboxStateV1;

bool Known(const MajorDecisionTypedBoolV1 &value) noexcept {
  return value.state == MajorDecisionFieldStateV1::known &&
         value.unknown_reason == MajorDecisionUnknownReasonV1::none;
}

bool ValidBinding(
    const MajorDecisionFoundKingdomActionBindingV1 &binding) noexcept {
  return binding.snapshot_revision != 0 && binding.native_revision != 0 &&
         binding.proof_epoch != 0 && binding.date_raw > 0 &&
         binding.played_character_id > 0 &&
         binding.decision_database_identity != 0 &&
         binding.decision_database_generation != 0 &&
         binding.decision_definition_identity != 0 &&
         binding.decision_definition_generation != 0 &&
         binding.primary_title_id > 0 &&
         binding.primary_title_identity != 0 &&
         binding.primary_title_generation != 0 &&
         binding.world_identity != 0 && binding.world_generation != 0 &&
         binding.world_revision != 0;
}

bool ValidCost(const MajorDecisionEvaluatedCostV1 &cost) noexcept {
  return cost.state == MajorDecisionFieldStateV1::known &&
         cost.source == MajorDecisionCostSourceV1::native_evaluated_cost &&
         cost.unknown_reason == MajorDecisionUnknownReasonV1::none &&
         cost.gold_q100000 >= 0 && cost.treasury_q100000 >= 0 &&
         cost.prestige_q100000 >= 0 && cost.piety_q100000 >= 0;
}

bool ValidConcreteCandidate(
    const MajorDecisionFoundKingdomActionPreconditionV1 &candidate,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return candidate.available && candidate.application_main_thread &&
         candidate.paused && candidate.map_ready &&
         candidate.played_character_alive &&
         candidate.played_character_identity_round_trip &&
         candidate.decision_database_identity_round_trip &&
         candidate.decision_definition_identity_round_trip &&
         candidate.decision_source_block_sha256_round_trip &&
         candidate.decision_id == kMajorDecisionFoundKingdomDecisionIdV1 &&
         ValidBinding(candidate.binding) &&
         candidate.binding.date_raw == stamp.date_raw &&
         Known(candidate.is_shown) && Known(candidate.is_valid) &&
         Known(candidate.is_valid_showing_failures_only) &&
         ValidCost(candidate.evaluated_cost) &&
         Known(candidate.is_affordable) && Known(candidate.can_take) &&
         candidate.effect_preview.state == MajorDecisionFieldStateV1::unknown &&
         candidate.effect_preview.unknown_reason ==
             MajorDecisionUnknownReasonV1::effect_preview_not_provided &&
         !candidate.effect_preview.executable;
}

void SetFailure(MajorDecisionFoundKingdomSharedContextV1 &context,
                Completion completion, Failure failure,
                std::string_view reason) noexcept {
  context.completion = completion;
  context.failure = failure;
  try {
    context.failure_reason.assign(reason);
  } catch (...) {
    context.failure_reason.clear();
  }
}

bool IsExecutingExactMailboxSlot(
    const MajorDecisionFoundKingdomSharedContextV1 &context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (context.mailbox == nullptr || context.ticket.sequence == 0 ||
      context.operation == MajorDecisionFoundKingdomSharedOperationV1::none ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      stamp.date_raw <= 0 || stamp.tls_initialized_flag_address == 0 ||
      stamp.tls_initialized != 1 || stamp.tls_context == 0 ||
      stamp.tls_main_thread_marker != 1 || stamp.jomini_state == 0 ||
      stamp.game_state == 0 || GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *context.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MailboxState::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             context.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor ==
             &ExecuteMajorDecisionFoundKingdomSharedMailboxV1 &&
         mailbox.executor_context == const_cast<
             MajorDecisionFoundKingdomSharedContextV1 *>(&context);
}

bool ExecuteSubmit(
    MajorDecisionFoundKingdomSharedContextV1 &context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  MajorDecisionFoundKingdomActionPreconditionV1 candidate{};
  if (context.action_access.capture_precondition == nullptr ||
      !context.action_access.capture_precondition(context.action_access.context,
                                                  candidate)) {
    SetFailure(context, Completion::candidate_red, Failure::candidate_capture,
               "paused_candidate_capture_failed");
    return true;
  }
  context.concrete_candidate = candidate;
  if (!ValidConcreteCandidate(candidate, stamp)) {
    SetFailure(context, Completion::candidate_red, Failure::candidate_contract,
               "concrete_candidate_contract_failed");
    return true;
  }

  context.concrete_request = {};
  context.concrete_request.request_id = context.request_id;
  context.concrete_request.decision_id = candidate.decision_id;
  context.concrete_request.expected_binding = candidate.binding;
  context.concrete_request.expected_evaluated_cost = candidate.evaluated_cost;
  context.concrete_candidate_generated = true;

  // Preserve the original ACK while its receipt is pending. The action core
  // also rejects duplicates, but its rejection output would otherwise replace
  // the only ACK that the later receipt transaction must verify.
  if (context.shared_state->action.verification_pending ||
      context.shared_state->has_pending_ack) {
    context.action_failure_class =
        MajorDecisionFoundKingdomActionFailureClassV1::pending_action;
    SetFailure(context, Completion::action_red, Failure::action_rejected,
               "previous_submission_verification_pending");
    return true;
  }

  const auto status = ExecuteMajorDecisionFoundKingdomActionCoreV1(
      context.action_environment, context.action_access,
      context.concrete_request, context.shared_state->action,
      context.shared_state->pending_ack);
  if (status != MajorDecisionFoundKingdomActionAckStatusV1::
                    submitted_verification_pending) {
    context.action_failure_class =
        context.shared_state->pending_ack.failure_class;
    SetFailure(context, Completion::action_red, Failure::action_rejected,
               context.shared_state->pending_ack.rejection_reason);
    return true;
  }
  context.shared_state->has_pending_ack = true;
  context.action_failure_class =
      MajorDecisionFoundKingdomActionFailureClassV1::none;
  context.completion = Completion::submitted_verification_pending;
  context.failure = Failure::none;
  context.failure_reason.clear();
  return true;
}

bool ExecuteReceipt(
    MajorDecisionFoundKingdomSharedContextV1 &context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (!context.shared_state->has_pending_ack ||
      !context.shared_state->action.verification_pending) {
    SetFailure(context, Completion::receipt_red, Failure::receipt_rejected,
               "pending_ack_unavailable");
    return true;
  }
  MajorDecisionFoundKingdomActionPostconditionV1 postcondition{};
  if (context.capture_postcondition == nullptr ||
      !context.capture_postcondition(context.postcondition_context,
                                     postcondition)) {
    SetFailure(context, Completion::receipt_red,
               Failure::postcondition_capture,
               "fresh_postcondition_capture_failed");
    return true;
  }
  if (!postcondition.application_main_thread || !postcondition.paused ||
      postcondition.date_raw != stamp.date_raw) {
    SetFailure(context, Completion::receipt_red,
               Failure::postcondition_capture,
               "postcondition_not_bound_to_mailbox_stamp");
    return true;
  }
  const auto status = VerifyMajorDecisionFoundKingdomActionReceiptV1(
      context.shared_state->pending_ack, postcondition,
      context.shared_state->action, context.receipt);
  if (status != MajorDecisionFoundKingdomActionReceiptStatusV1::applied) {
    SetFailure(context, Completion::receipt_red, Failure::receipt_rejected,
               context.receipt.reason);
    return true;
  }
  context.shared_state->has_pending_ack = false;
  context.completion = Completion::receipt_applied;
  context.failure = Failure::none;
  context.failure_reason.clear();
  return true;
}

} // namespace

bool ConfigureMajorDecisionFoundKingdomSharedGlueV1(
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const MajorDecisionFoundKingdomNativeSubmitEnvironmentV1
        &submit_environment,
    MajorDecisionFoundKingdomSharedStateV1 &shared_state,
    const MajorDecisionFoundKingdomActionAccessV1 &upstream_action_access,
    void *postcondition_context,
    CaptureMajorDecisionFoundKingdomActionPostconditionV1
        capture_postcondition,
    MajorDecisionFoundKingdomSharedContextV1 &context) noexcept {
  if (context.ticket.sequence != 0) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "shared_glue_configuration_busy");
    return false;
  }
  // A failed reconfiguration must not leave the previous binding callable.
  context.configured = false;
  if (upstream_action_access.context == nullptr ||
      upstream_action_access.capture_precondition == nullptr ||
      capture_postcondition == nullptr) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "shared_glue_configuration_invalid");
    return false;
  }
  try {
    context.mailbox = &mailbox;
    context.shared_state = &shared_state;
    context.postcondition_context = postcondition_context;
    context.capture_postcondition = capture_postcondition;
    context.action_access = upstream_action_access;
    context.action_access.submit = nullptr;
    context.action_environment = {};
    context.native_submit_state = {};
    if (!BindMajorDecisionFoundKingdomNativeSubmitV1(
            submit_environment, context.native_submit_state,
            context.action_environment, context.action_access)) {
      SetFailure(context, Completion::infrastructure_red,
                 Failure::not_configured,
                 "exact_native_submit_binding_failed");
      return false;
    }
    context.action_environment.action_enabled = true;
    context.configured = true;
    context.completion = Completion::not_executed;
    context.failure = Failure::none;
    context.failure_reason.clear();
    return true;
  } catch (...) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "shared_glue_configuration_exception");
    return false;
  }
}

bool PrepareMajorDecisionFoundKingdomSubmitV1(
    MajorDecisionFoundKingdomSharedContextV1 &context,
    std::string_view request_id) noexcept {
  if (!context.configured || context.mailbox == nullptr ||
      context.shared_state == nullptr || context.ticket.sequence != 0) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "submit_prepare_not_configured");
    return false;
  }
  try {
    context.request_id.assign(request_id);
    context.operation =
        MajorDecisionFoundKingdomSharedOperationV1::submit_candidate;
    context.concrete_candidate = {};
    context.concrete_request = {};
    context.receipt = {};
    context.concrete_candidate_generated = false;
    context.action_failure_class =
        MajorDecisionFoundKingdomActionFailureClassV1::none;
    context.completion = Completion::not_executed;
    context.failure = Failure::none;
    context.failure_reason.clear();
    context.execution_stamp = {};
    return true;
  } catch (...) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "submit_prepare_exception");
    return false;
  }
}

bool PrepareMajorDecisionFoundKingdomReceiptV1(
    MajorDecisionFoundKingdomSharedContextV1 &context) noexcept {
  if (!context.configured || context.mailbox == nullptr ||
      context.shared_state == nullptr || context.ticket.sequence != 0) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "receipt_prepare_not_configured");
    return false;
  }
  context.operation =
      MajorDecisionFoundKingdomSharedOperationV1::verify_receipt;
  context.receipt = {};
  context.completion = Completion::not_executed;
  context.failure = Failure::none;
  context.failure_reason.clear();
  context.execution_stamp = {};
  return true;
}

ck3_11906::MainThreadQuerySubmitResultV1
TryQueueMajorDecisionFoundKingdomSharedV1(
    MajorDecisionFoundKingdomSharedContextV1 &context) noexcept {
  if (!context.configured || context.mailbox == nullptr ||
      context.operation == MajorDecisionFoundKingdomSharedOperationV1::none ||
      context.ticket.sequence != 0) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "mailbox_queue_contract_failed");
    return ck3_11906::MainThreadQuerySubmitResultV1::invalid_request;
  }
  const auto result = ck3_11906::TrySubmitMainThreadQueryV1(
      *context.mailbox,
      &ExecuteMajorDecisionFoundKingdomSharedMailboxV1, &context,
      context.ticket);
  if (result != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "mailbox_submit_rejected");
  }
  return result;
}

ck3_11906::MainThreadQueryReclaimResultV1
ReclaimMajorDecisionFoundKingdomSharedV1(
    MajorDecisionFoundKingdomSharedContextV1 &context) noexcept {
  if (context.mailbox == nullptr) {
    return ck3_11906::MainThreadQueryReclaimResultV1::ticket_mismatch;
  }
  const auto result =
      ck3_11906::ReclaimMainThreadQueryV1(*context.mailbox, context.ticket);
  if (result == ck3_11906::MainThreadQueryReclaimResultV1::reclaimed) {
    context.ticket = {};
    context.operation = MajorDecisionFoundKingdomSharedOperationV1::none;
  }
  return result;
}

bool ExecuteMajorDecisionFoundKingdomSharedMailboxV1(
    void *opaque_context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context =
      static_cast<MajorDecisionFoundKingdomSharedContextV1 *>(opaque_context);
  if (context == nullptr || !context->configured ||
      context->shared_state == nullptr ||
      !IsExecutingExactMailboxSlot(*context, stamp)) {
    if (context != nullptr) {
      SetFailure(*context, Completion::infrastructure_red,
                 Failure::mailbox_identity,
                 "executing_mailbox_identity_failed");
    }
    return false;
  }
  try {
    ++context->executor_invocations;
    context->execution_stamp = stamp;
    switch (context->operation) {
    case MajorDecisionFoundKingdomSharedOperationV1::submit_candidate:
      return ExecuteSubmit(*context, stamp);
    case MajorDecisionFoundKingdomSharedOperationV1::verify_receipt:
      return ExecuteReceipt(*context, stamp);
    case MajorDecisionFoundKingdomSharedOperationV1::none:
      break;
    }
  } catch (...) {
    SetFailure(*context, Completion::infrastructure_red, Failure::transport,
               "shared_mailbox_executor_exception");
    return false;
  }
  SetFailure(*context, Completion::infrastructure_red, Failure::transport,
             "shared_mailbox_operation_invalid");
  return false;
}

std::string_view MajorDecisionFoundKingdomSharedFailureNameV1(
    Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::not_configured: return "not_configured";
  case Failure::mailbox_identity: return "mailbox_identity";
  case Failure::candidate_capture: return "candidate_capture";
  case Failure::candidate_contract: return "candidate_contract";
  case Failure::action_rejected: return "action_rejected";
  case Failure::postcondition_capture: return "postcondition_capture";
  case Failure::receipt_rejected: return "receipt_rejected";
  case Failure::transport: return "transport";
  }
  return "transport";
}

} // namespace xar::bridge
