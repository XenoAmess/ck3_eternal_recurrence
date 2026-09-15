#include "xar_bridge/realm_law_application_main_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <atomic>
#include <string_view>

namespace xar::bridge {
namespace {

using Completion = RealmLawApplicationMainCompletionV1;
using Failure = RealmLawApplicationMainFailureV1;
using MailboxState = ck3_11906::MainThreadQueryMailboxStateV1;
using Operation = RealmLawApplicationMainOperationV1;

template <std::size_t Size>
std::string_view FixedView(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

void SetFailure(RealmLawApplicationMainContextV1 &context,
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
    const RealmLawApplicationMainContextV1 &context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (context.mailbox == nullptr || context.ticket.sequence == 0 ||
      context.operation == Operation::none || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused || stamp.date_raw <= 0 ||
      stamp.tls_initialized_flag_address == 0 ||
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
      mailbox.module_base == context.configuration.module_base &&
      mailbox.permitted_executor_septentrigintary ==
          &ExecuteRealmLawApplicationMainV1 &&
      mailbox.executor == &ExecuteRealmLawApplicationMainV1 &&
      mailbox.executor_context ==
          const_cast<RealmLawApplicationMainContextV1 *>(&context);
}

bool EnsureNativeBinding(RealmLawApplicationMainContextV1 &context) noexcept {
  auto &state = *context.shared_state;
  if (state.initialized) {
    return state.native_glue.prepared && state.native_binder.attached;
  }
  if (state.native_glue.prepared || state.native_binder.attached) return false;
  if (!PrepareRealmLawNativeSharedGlueV1(context.configuration,
                                         state.native_glue)) {
    return false;
  }
  const auto environment =
      MakeRealmLawNativeSharedGlueEnvironmentV1(state.native_glue);
  if (!BindRealmLawNativeV1(environment, state.native_binder)) return false;
  state.initialized = true;
  return true;
}

bool ExecuteSubmit(RealmLawApplicationMainContextV1 &context,
                   const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &state = *context.shared_state;
  if (context.request.expected_date_raw != stamp.date_raw) {
    SetFailure(context, Completion::action_red, Failure::stamp_mismatch,
               "submit_request_date_not_bound_to_mailbox_stamp");
    return true;
  }
  if (!EnsureNativeBinding(context)) {
    SetFailure(context, Completion::binding_red, Failure::native_binding,
               "law7_native_binding_failed");
    return true;
  }
  if (state.has_pending_ack || state.native_binder.submit_pending) {
    SetFailure(context, Completion::action_red, Failure::pending_ack,
               "previous_submission_verification_pending");
    return true;
  }

  context.attempt_ack = {};
  const auto status = ExecuteBoundRealmLawNativeEnactV1(
      state.native_binder, context.request, context.attempt_ack);
  context.action_failure = context.attempt_ack.failure;
  if (status !=
      RealmLawEnactActionAckStatusV1::submitted_verification_pending) {
    SetFailure(context, Completion::action_red, Failure::action_rejected,
               RealmLawEnactActionFailureNameV1(
                   context.attempt_ack.failure));
    return true;
  }
  state.pending_ack = context.attempt_ack;
  state.pending_submit_sequence = context.ticket.sequence;
  state.has_pending_ack = true;
  context.failure = Failure::none;
  context.failure_reason.clear();
  context.completion = Completion::submitted_verification_pending;
  return true;
}

bool ExecuteReceipt(RealmLawApplicationMainContextV1 &context,
                    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &state = *context.shared_state;
  if (!state.initialized || !state.has_pending_ack ||
      !state.native_binder.submit_pending ||
      state.pending_submit_sequence == 0 ||
      context.ticket.sequence <= state.pending_submit_sequence) {
    SetFailure(context, Completion::receipt_red, Failure::pending_ack,
               "independent_pending_submission_unavailable");
    return true;
  }

  context.receipt = {};
  const auto status = VerifyBoundRealmLawNativeReceiptV1(
      state.native_binder, state.pending_ack, context.receipt);
  context.receipt_failure = context.receipt.failure;
  if (status != RealmLawEnactActionReceiptStatusV1::enacted) {
    SetFailure(context, Completion::receipt_red, Failure::receipt_rejected,
               RealmLawEnactActionReceiptFailureNameV1(
                   context.receipt.failure));
    return true;
  }
  if (context.receipt.post_date_raw != stamp.date_raw) {
    // LAW5 cleared this only because its postconditions were otherwise
    // complete. The transport stamp is part of LAW8's receipt contract, so
    // retain the original pending transaction for a fresh independent read.
    state.native_binder.submit_pending = true;
    SetFailure(context, Completion::receipt_red, Failure::stamp_mismatch,
               "receipt_date_not_bound_to_mailbox_stamp");
    return true;
  }
  state.has_pending_ack = false;
  state.pending_submit_sequence = 0;
  context.failure = Failure::none;
  context.failure_reason.clear();
  context.completion = Completion::receipt_enacted;
  return true;
}

} // namespace

bool ConfigureRealmLawApplicationMainV1(
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const RealmLawNativeSharedGlueConfigurationV1 &configuration,
    RealmLawApplicationMainStateV1 &shared_state,
    RealmLawApplicationMainContextV1 &context) noexcept {
  if (context.ticket.sequence != 0 || context.configured ||
      shared_state.initialized || shared_state.has_pending_ack ||
      shared_state.native_glue.prepared ||
      shared_state.native_binder.attached || !configuration.enabled ||
      configuration.module_base == 0 ||
      configuration.admitted_executable_sha256 !=
          kRealmLawNativeSharedGlueV1ExecutableSha256 ||
      !AssignRealmLawNativeDigestV1(
          configuration.expected_source_signature_manifest_sha256,
          context.source_signature_manifest_sha256)) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured,
               "application_main_configuration_invalid");
    return false;
  }
  context.mailbox = &mailbox;
  context.shared_state = &shared_state;
  context.configuration = configuration;
  context.configuration.admitted_executable_sha256 =
      kRealmLawNativeSharedGlueV1ExecutableSha256;
  context.configuration.expected_source_signature_manifest_sha256 =
      FixedView(context.source_signature_manifest_sha256);
  context.configured = true;
  context.completion = Completion::not_executed;
  context.failure = Failure::none;
  context.failure_reason.clear();
  return true;
}

bool PrepareRealmLawApplicationMainSubmitV1(
    RealmLawApplicationMainContextV1 &context,
    const RealmLawEnactActionRequestV1 &request) noexcept {
  if (!context.configured || context.mailbox == nullptr ||
      context.shared_state == nullptr || context.ticket.sequence != 0) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "submit_prepare_not_configured");
    return false;
  }
  try {
    context.request = request;
    context.operation = Operation::submit;
    context.attempt_ack = {};
    context.receipt = {};
    context.action_failure = RealmLawEnactActionFailureV1::none;
    context.receipt_failure = RealmLawEnactActionReceiptFailureV1::none;
    context.execution_stamp = {};
    context.completion = Completion::not_executed;
    context.failure = Failure::none;
    context.failure_reason.clear();
    return true;
  } catch (...) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "submit_prepare_exception");
    return false;
  }
}

bool PrepareRealmLawApplicationMainReceiptV1(
    RealmLawApplicationMainContextV1 &context) noexcept {
  if (!context.configured || context.mailbox == nullptr ||
      context.shared_state == nullptr || context.ticket.sequence != 0) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "receipt_prepare_not_configured");
    return false;
  }
  context.operation = Operation::verify_receipt;
  context.receipt = {};
  context.receipt_failure = RealmLawEnactActionReceiptFailureV1::none;
  context.execution_stamp = {};
  context.completion = Completion::not_executed;
  context.failure = Failure::none;
  context.failure_reason.clear();
  return true;
}

ck3_11906::MainThreadQuerySubmitResultV1 TryQueueRealmLawApplicationMainV1(
    RealmLawApplicationMainContextV1 &context) noexcept {
  if (!context.configured || context.mailbox == nullptr ||
      context.shared_state == nullptr || context.operation == Operation::none ||
      context.ticket.sequence != 0) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "mailbox_queue_contract_failed");
    return ck3_11906::MainThreadQuerySubmitResultV1::invalid_request;
  }
  const auto result = ck3_11906::TrySubmitMainThreadQueryV1(
      *context.mailbox, &ExecuteRealmLawApplicationMainV1, &context,
      context.ticket);
  if (result != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "mailbox_submit_rejected");
  }
  return result;
}

ck3_11906::MainThreadQueryReclaimResultV1 ReclaimRealmLawApplicationMainV1(
    RealmLawApplicationMainContextV1 &context) noexcept {
  if (context.mailbox == nullptr) {
    return ck3_11906::MainThreadQueryReclaimResultV1::ticket_mismatch;
  }
  const auto result =
      ck3_11906::ReclaimMainThreadQueryV1(*context.mailbox, context.ticket);
  if (result == ck3_11906::MainThreadQueryReclaimResultV1::reclaimed) {
    context.ticket = {};
    context.operation = Operation::none;
  }
  return result;
}

bool ExecuteRealmLawApplicationMainV1(
    void *opaque_context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context =
      static_cast<RealmLawApplicationMainContextV1 *>(opaque_context);
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
    case Operation::submit: return ExecuteSubmit(*context, stamp);
    case Operation::verify_receipt: return ExecuteReceipt(*context, stamp);
    case Operation::none: break;
    }
  } catch (...) {
    SetFailure(*context, Completion::infrastructure_red, Failure::transport,
               "application_main_executor_exception");
    return false;
  }
  SetFailure(*context, Completion::infrastructure_red, Failure::transport,
             "application_main_operation_invalid");
  return false;
}

std::string_view RealmLawApplicationMainFailureNameV1(
    Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::not_configured: return "not_configured";
  case Failure::mailbox_identity: return "mailbox_identity";
  case Failure::native_binding: return "native_binding";
  case Failure::stamp_mismatch: return "stamp_mismatch";
  case Failure::pending_ack: return "pending_ack";
  case Failure::action_rejected: return "action_rejected";
  case Failure::receipt_rejected: return "receipt_rejected";
  case Failure::transport: return "transport";
  }
  return "transport";
}

} // namespace xar::bridge
