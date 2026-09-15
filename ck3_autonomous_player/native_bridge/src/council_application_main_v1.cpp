#include "xar_bridge/council_application_main_v1.hpp"

#include <algorithm>
#include <atomic>
#include <utility>

#include <windows.h>

namespace xar::bridge {
namespace {

using Completion = CouncilApplicationMainCompletionV1;
using Failure = CouncilApplicationMainFailureV1;
using Operation = CouncilApplicationMainOperationV1;
using MailboxState = ck3_11906::MainThreadQueryMailboxStateV1;

void SetFailure(CouncilApplicationMainContextV1 &context,
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
    const CouncilApplicationMainContextV1 &context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (!context.shared_state || !context.shared_state->configured ||
      context.mailbox == nullptr || context.ticket.sequence == 0 ||
      context.operation == Operation::none || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      stamp.jomini_state == 0 || stamp.game_state == 0 ||
      GetCurrentThreadId() != stamp.thread_id) {
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
      mailbox.permitted_executor_unquadragintary ==
          &ExecuteCouncilApplicationMainV1 &&
      mailbox.executor == &ExecuteCouncilApplicationMainV1 &&
      mailbox.executor_context ==
          const_cast<CouncilApplicationMainContextV1 *>(&context);
}

bool SourceIsMainThread(void *opaque) noexcept {
  const auto *context =
      static_cast<const CouncilApplicationMainContextV1 *>(opaque);
  return context != nullptr && context->active_stamp != nullptr &&
      IsExecutingExactMailboxSlot(*context, *context->active_stamp);
}

bool CaptureSourceFrame(
    void *opaque,
    ck3_11906::CouncilCompositionStewardCandidatesFrameV1 &output) noexcept {
  auto *context = static_cast<CouncilApplicationMainContextV1 *>(opaque);
  if (context == nullptr || context->active_stamp == nullptr ||
      context->configuration.capture_source_frame == nullptr ||
      !IsExecutingExactMailboxSlot(*context, *context->active_stamp)) {
    return false;
  }
  return context->configuration.capture_source_frame(
      context->configuration.source_context, context->query_request,
      *context->active_stamp, output);
}

bool EnrichmentAccessComplete(
    const ck3_11906::CouncilCompositionCandidatesEnrichmentAccessV1
        &access) noexcept {
  return access.context != nullptr && access.capture_frame != nullptr &&
      access.is_main_thread != nullptr && access.read_memory != nullptr &&
      access.resolve_character != nullptr;
}

bool ReadPublicTransaction(CouncilApplicationMainContextV1 &context) noexcept {
  auto &state = *context.shared_state;
  game::CouncilCompositionStewardCandidatesV1 private_result{};
  const auto private_status =
      ck3_11906::ReadCouncilCompositionStewardCandidatesV1(
          state.reader_environment, state.reader_access,
          context.query_request, private_result);
  if (private_status !=
      game::ReadCouncilCompositionStewardCandidatesResultV1::available) {
    ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1 empty{};
    (void)ck3_11906::ProjectCouncilCompositionCandidatesPublicV1(
        private_result, empty, context.query_result);
    SetFailure(context, Completion::query_unavailable,
               Failure::private_reader_unavailable,
               ck3_11906::CouncilCompositionStewardCandidatesFailureKeyV1(
                   private_result.unavailable_reason));
    return false;
  }

  ck3_11906::CouncilCompositionCandidatesEnrichmentAccessV1 enrichment_access{};
  if (!ck3_11906::BindCouncilCompositionCandidatesEnrichmentAccessV1(
          state.binding, enrichment_access) ||
      !EnrichmentAccessComplete(enrichment_access)) {
    ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1 empty{};
    (void)ck3_11906::ProjectCouncilCompositionCandidatesPublicV1(
        private_result, empty, context.query_result);
    SetFailure(context, Completion::query_unavailable,
               Failure::enrichment_unavailable,
               "enrichment_binding_unavailable");
    return false;
  }

  ck3_11906::CouncilCompositionCandidatesEnrichmentEnvironmentV1
      enrichment_environment{};
  enrichment_environment.exact_build_admitted =
      context.configuration.exact_build_admitted;
  enrichment_environment.admitted_executable_sha256 =
      context.configuration.admitted_executable_sha256;
  ck3_11906::CouncilCompositionCandidatesPublicEnrichmentV1 enrichment{};
  game::CouncilCompositionCandidatesEnrichmentFailureV1 enrichment_failure =
      game::CouncilCompositionCandidatesEnrichmentFailureV1::none;
  if (ck3_11906::ReadCouncilCompositionCandidatesEnrichmentV1(
          enrichment_environment, enrichment_access, private_result,
          enrichment, enrichment_failure) !=
      game::ReadCouncilCompositionCandidatesEnrichmentResultV1::available) {
    (void)ck3_11906::ProjectCouncilCompositionCandidatesPublicV1(
        private_result, enrichment, context.query_result);
    SetFailure(context, Completion::query_unavailable,
               Failure::enrichment_unavailable,
               ck3_11906::CouncilCompositionCandidatesEnrichmentFailureKeyV1(
                   enrichment_failure));
    return false;
  }

  if (ck3_11906::ProjectCouncilCompositionCandidatesPublicV1(
          private_result, enrichment, context.query_result) !=
      ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1::available) {
    SetFailure(context, Completion::query_unavailable,
               Failure::projection_unavailable,
               ck3_11906::CouncilCompositionCandidatesPublicFailureKeyV1(
                   context.query_result.unavailable_reason));
    return false;
  }
  context.completion = Completion::query_available;
  context.failure = Failure::none;
  context.failure_reason.clear();
  return true;
}

bool PublicToActionFrame(
    const CouncilApplicationMainContextV1 &context,
    game::CouncilAssignCouncillorFrameV1 &frame) noexcept {
  const auto &value = context.query_result;
  const auto &binding = context.shared_state->binding;
  if (value.status !=
          game::CouncilCompositionCandidatesPublicStatusV1::available ||
      !value.readiness.ready || !binding.frame_bound ||
      binding.bound_frame.active_task_id <= 0 ||
      !binding.bound_frame.active_task_identity_round_trip) {
    return false;
  }
  const auto fixed = [](const auto &bytes) noexcept -> std::string_view {
    const auto end = std::find(bytes.begin(), bytes.end(), '\0');
    if (end == bytes.end()) return {};
    return {bytes.data(), static_cast<std::size_t>(end - bytes.begin())};
  };
  try {
    frame = {};
    frame.available = true;
    frame.paused = value.paused;
    frame.map_ready = binding.bound_frame.map_ready;
    frame.snapshot_id.assign(fixed(value.snapshot_id));
    frame.public_revision = value.public_revision;
    frame.native_revision = value.native_revision;
    frame.date_raw = value.date_raw;
    frame.owner_character_id = value.owner_character_id;
    frame.owner_identity_round_trip =
        binding.bound_frame.played_character_identity_round_trip;
    frame.position_key.assign(fixed(value.position_key));
    frame.active_task_id = binding.bound_frame.active_task_id;
    frame.active_task_identity_round_trip =
        binding.bound_frame.active_task_identity_round_trip;
    frame.has_incumbent = !value.vacant;
    frame.incumbent_character_id = value.incumbent_character_id;
    frame.incumbent_identity_round_trip =
        value.vacant ? false : value.readiness.incumbent_ready;
    return true;
  } catch (...) {
    frame = {};
    return false;
  }
}

bool CaptureActionFrame(
    void *opaque, game::CouncilAssignCouncillorFrameV1 &frame) noexcept {
  auto *context = static_cast<CouncilApplicationMainContextV1 *>(opaque);
  if (context == nullptr || !ReadPublicTransaction(*context)) return false;
  return PublicToActionFrame(*context, frame);
}

bool RecheckActionLegality(
    void *opaque, const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept {
  auto *context = static_cast<CouncilApplicationMainContextV1 *>(opaque);
  if (context == nullptr ||
      context->configuration.evaluate_action_gates == nullptr ||
      !ReadPublicTransaction(*context)) {
    return false;
  }
  game::CouncilAssignCouncillorFrameV1 current{};
  if (!PublicToActionFrame(*context, current) || current != frame) return false;
  std::uint32_t matches = 0;
  for (std::uint32_t index = 0;
       index < context->query_result.candidate_count; ++index) {
    if (context->query_result.candidates[index].character_id ==
        candidate_character_id) {
      ++matches;
    }
  }
  output = {};
  if (!context->configuration.evaluate_action_gates(
          context->configuration.action_gate_context, current,
          candidate_character_id, output)) {
    return false;
  }
  output.available = true;
  output.owner_character_id = current.owner_character_id;
  output.active_task_id = current.active_task_id;
  output.position_key = current.position_key;
  output.candidate_character_id = candidate_character_id;
  output.candidate_match_count = matches;
  output.candidate_identity_round_trip = matches == 1;
  return true;
}

bool InvokeActionHelper(
    void *opaque,
    const game::CouncilAssignCouncillorNativeSubmissionV1 &submission) noexcept {
  auto *context = static_cast<CouncilApplicationMainContextV1 *>(opaque);
  if (context == nullptr || context->configuration.submit_adapter == nullptr) {
    return false;
  }
  return ck3_11906::InvokeCouncilAssignCouncillorNativeSubmitAdapterV1(
      context->configuration.submit_adapter, submission);
}

bool ExecuteQuery(CouncilApplicationMainContextV1 &context) noexcept {
  (void)ReadPublicTransaction(context);
  // A typed unavailable query is a valid executor completion. The caller sees
  // the unavailable result and reason; mailbox false remains infrastructure.
  return true;
}

bool ExecuteSubmit(CouncilApplicationMainContextV1 &context,
                   const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto &state = *context.shared_state;
  if (!state.action_runtime_ready) {
    SetFailure(context, Completion::action_rejected,
               Failure::action_runtime_unavailable,
               "complete_native_action_gates_not_bound");
    return true;
  }
  if (state.has_pending_ack) {
    SetFailure(context, Completion::action_rejected,
               Failure::pending_ack_unavailable,
               "previous_assignment_verification_pending");
    return true;
  }
  auto environment = context.configuration.submit_adapter->environment;
  environment.current_thread_id = stamp.thread_id;
  environment.application_main_thread_id = stamp.thread_id;
  context.configuration.submit_adapter->environment = environment;
  const ck3_11906::CouncilAssignCouncillorActionAccessV1 access{
      &context, &CaptureActionFrame, &RecheckActionLegality,
      &InvokeActionHelper};
  context.action_ack = {};
  if (ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
          environment, access, context.action_request, context.action_ack) !=
      game::CouncilAssignCouncillorAckStatusV1::
          native_helper_invoked_verification_pending) {
    SetFailure(context, Completion::action_rejected,
               Failure::action_rejected,
               ck3_11906::CouncilAssignCouncillorFailureKeyV1(
                   context.action_ack.failure));
    return true;
  }
  state.pending_ack = context.action_ack;
  state.pending_submit_sequence = context.ticket.sequence;
  state.has_pending_ack = true;
  context.completion = Completion::submitted_verification_pending;
  context.failure = Failure::none;
  context.failure_reason.clear();
  return true;
}

bool ExecuteReceipt(CouncilApplicationMainContextV1 &context) noexcept {
  auto &state = *context.shared_state;
  if (!state.action_runtime_ready || !state.has_pending_ack ||
      state.pending_submit_sequence == 0 ||
      context.ticket.sequence <= state.pending_submit_sequence) {
    SetFailure(context, Completion::receipt_rejected,
               Failure::pending_ack_unavailable,
               "independent_pending_assignment_unavailable");
    return true;
  }
  (void)ReadPublicTransaction(context);
  game::CouncilAssignCouncillorFrameV1 post{};
  if (!PublicToActionFrame(context, post)) {
    SetFailure(context, Completion::receipt_rejected,
               Failure::receipt_rejected,
               "fresh_public_postcondition_unavailable");
    return true;
  }
  context.action_receipt = {};
  if (ck3_11906::VerifyCouncilAssignCouncillorActionReceiptV1(
          state.pending_ack, post, context.action_receipt) !=
      game::CouncilAssignCouncillorReceiptStatusV1::applied) {
    SetFailure(context, Completion::receipt_rejected,
               Failure::receipt_rejected,
               context.action_receipt.reason);
    return true;
  }
  state.has_pending_ack = false;
  state.pending_submit_sequence = 0;
  state.pending_ack = {};
  context.completion = Completion::receipt_applied;
  context.failure = Failure::none;
  context.failure_reason.clear();
  return true;
}

void AppendJsonString(std::string &output, std::string_view value) {
  output.push_back('"');
  constexpr char digits[] = "0123456789ABCDEF";
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20U) {
        output += "\\u00";
        output.push_back(digits[character >> 4U]);
        output.push_back(digits[character & 0x0FU]);
      } else {
        output.push_back(static_cast<char>(character));
      }
    }
  }
  output.push_back('"');
}

std::string_view AckStatusName(
    game::CouncilAssignCouncillorAckStatusV1 status) noexcept {
  return status == game::CouncilAssignCouncillorAckStatusV1::
                       native_helper_invoked_verification_pending
      ? "native_helper_invoked_verification_pending"
      : "rejected_before_submit";
}

std::string_view ReceiptStatusName(
    game::CouncilAssignCouncillorReceiptStatusV1 status) noexcept {
  switch (status) {
  case game::CouncilAssignCouncillorReceiptStatusV1::rejected:
    return "rejected";
  case game::CouncilAssignCouncillorReceiptStatusV1::postcondition_failed:
    return "postcondition_failed";
  case game::CouncilAssignCouncillorReceiptStatusV1::applied:
    return "applied";
  }
  return "postcondition_failed";
}

void AppendBool(std::string &output, bool value) {
  output += value ? "true" : "false";
}

void AppendAck(std::string &output,
               const game::CouncilAssignCouncillorActionAckV1 &ack) {
  output += "{\"status\":";
  AppendJsonString(output, AckStatusName(ack.status));
  output += ",\"failure\":";
  AppendJsonString(output,
                   ck3_11906::CouncilAssignCouncillorFailureKeyV1(ack.failure));
  output += ",\"action_request_id\":";
  AppendJsonString(output, ack.request_id);
  output += ",\"pre_snapshot_id\":";
  AppendJsonString(output, ack.pre_snapshot_id);
  output += ",\"pre_public_revision\":" +
      std::to_string(ack.pre_public_revision);
  output += ",\"pre_native_revision\":" +
      std::to_string(ack.pre_native_revision);
  output += ",\"pre_date_raw\":" + std::to_string(ack.pre_date_raw);
  output += ",\"owner_character_id\":" +
      std::to_string(ack.owner_character_id);
  output += ",\"position_key\":";
  AppendJsonString(output, ack.position_key);
  output += ",\"active_task_id\":" + std::to_string(ack.active_task_id);
  output += ",\"candidate_character_id\":" +
      std::to_string(ack.candidate_character_id);
  output += ",\"had_incumbent\":";
  AppendBool(output, ack.had_incumbent);
  output += ",\"previous_incumbent_character_id\":" +
      std::to_string(ack.previous_incumbent_character_id);
  output += ",\"route\":";
  AppendJsonString(output,
                   ck3_11906::CouncilAssignCouncillorRouteKeyV1(ack.route));
  output += ",\"native_helper_invoked\":";
  AppendBool(output, ack.native_helper_invoked);
  output += ",\"queue_acceptance_observed\":";
  AppendBool(output, ack.queue_acceptance_observed);
  output += ",\"verification_pending\":";
  AppendBool(output, ack.verification_pending);
  output += ",\"native_reason_key\":";
  AppendJsonString(output, ack.native_reason_key);
  output += '}';
}

void AppendReceipt(
    std::string &output,
    const game::CouncilAssignCouncillorActionReceiptV1 &receipt) {
  output += "{\"status\":";
  AppendJsonString(output, ReceiptStatusName(receipt.status));
  output += ",\"rejected_action_failure\":";
  AppendJsonString(
      output, ck3_11906::CouncilAssignCouncillorFailureKeyV1(
                  receipt.rejected_action_failure));
  output += ",\"action_request_id\":";
  AppendJsonString(output, receipt.request_id);
  output += ",\"post_snapshot_id\":";
  AppendJsonString(output, receipt.post_snapshot_id);
  output += ",\"post_public_revision\":" +
      std::to_string(receipt.post_public_revision);
  output += ",\"post_native_revision\":" +
      std::to_string(receipt.post_native_revision);
  output += ",\"post_date_raw\":" + std::to_string(receipt.post_date_raw);
  output += ",\"owner_character_id\":" +
      std::to_string(receipt.owner_character_id);
  output += ",\"position_key\":";
  AppendJsonString(output, receipt.position_key);
  output += ",\"incumbent_character_id\":" +
      std::to_string(receipt.incumbent_character_id);
  output += ",\"incumbent_identity_round_trip\":";
  AppendBool(output, receipt.incumbent_identity_round_trip);
  output += ",\"postcondition_verified\":";
  AppendBool(output, receipt.postcondition_verified);
  output += ",\"reason\":";
  AppendJsonString(output, receipt.reason);
  output += '}';
}

} // namespace

bool ConfigureCouncilApplicationMainV1(
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const CouncilApplicationMainConfigurationV1 &configuration,
    CouncilApplicationMainStateV1 &state,
    CouncilApplicationMainContextV1 &context) noexcept {
  if (state.configured || context.shared_state != nullptr ||
      !configuration.enabled || !configuration.query_runtime_enabled ||
      !configuration.exact_build_admitted || configuration.module_base == 0 ||
      configuration.admitted_executable_sha256 !=
          ck3_11906::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1 ||
      configuration.capture_source_frame == nullptr) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "configuration_invalid");
    return false;
  }
  context.mailbox = &mailbox;
  context.shared_state = &state;
  context.configuration = configuration;
  context.configuration.admitted_executable_sha256 =
      ck3_11906::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;

  auto source_access = ck3_11906::CouncilCompositionStewardCandidatesAccessV1{};
  source_access.context = &context;
  source_access.capture_frame = &CaptureSourceFrame;
  source_access.is_main_thread = &SourceIsMainThread;
  auto binding = configuration.binding;
  binding.binding_enabled = true;
  binding.exact_build_admitted = true;
  binding.admitted_executable_sha256 =
      ck3_11906::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  binding.module_base = configuration.module_base;
  if (!ck3_11906::BindCouncilCompositionStewardCandidatesV1(
          binding, state.binding, state.reader_environment, source_access)) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "private_binding_failed");
    context.mailbox = nullptr;
    context.shared_state = nullptr;
    return false;
  }
  state.reader_access = source_access;
  state.configured = true;
  state.query_runtime_ready = true;
  const auto *adapter = configuration.submit_adapter;
  state.action_runtime_ready =
      configuration.action_runtime_enabled &&
      configuration.private_candidate_admitted &&
      configuration.native_command_abi_certified &&
      configuration.evaluate_action_gates != nullptr && adapter != nullptr &&
      adapter->environment.exact_build_admitted &&
      adapter->environment.admitted_executable_sha256 ==
          ck3_11906::kCouncilAssignCouncillorExecutableSha256V1 &&
      adapter->environment.private_candidate_admitted &&
      adapter->environment.native_command_abi_certified &&
      adapter->environment.offline_fixture == configuration.offline_fixture &&
      adapter->environment.module_base ==
          (configuration.offline_fixture ? 0 : configuration.module_base) &&
      (configuration.offline_fixture ? adapter->helper_override != nullptr
                                     : adapter->helper_override == nullptr);
  context.completion = Completion::not_executed;
  context.failure = Failure::none;
  context.failure_reason.clear();
  return true;
}

bool PrepareCouncilApplicationMainQueryV1(
    CouncilApplicationMainContextV1 &context,
    const ck3_11906::CouncilCompositionStewardCandidatesRequestV1
        &request) noexcept {
  if (!context.shared_state || !context.shared_state->query_runtime_ready ||
      context.ticket.sequence != 0 || request.expected_snapshot_id.empty()) {
    SetFailure(context, Completion::infrastructure_red,
               Failure::not_configured, "query_prepare_invalid");
    return false;
  }
  try {
    context.query_snapshot_id.assign(request.expected_snapshot_id);
    context.query_request = request;
    context.query_request.expected_snapshot_id = context.query_snapshot_id;
    context.operation = Operation::query_candidates;
    context.query_result = {};
    context.action_ack = {};
    context.action_receipt = {};
    context.completion = Completion::not_executed;
    context.failure = Failure::none;
    context.failure_reason.clear();
    return true;
  } catch (...) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "query_prepare_exception");
    return false;
  }
}

bool PrepareCouncilApplicationMainSubmitV1(
    CouncilApplicationMainContextV1 &context,
    const game::CouncilAssignCouncillorActionRequestV1 &request) noexcept {
  if (!context.shared_state || !context.shared_state->action_runtime_ready ||
      context.ticket.sequence != 0) {
    SetFailure(context, Completion::action_rejected,
               Failure::action_runtime_unavailable,
               "submit_prepare_action_runtime_unavailable");
    return false;
  }
  try {
    context.action_request = request;
    context.query_snapshot_id = request.expected_snapshot_id;
    context.query_request.expected_snapshot_id = context.query_snapshot_id;
    context.query_request.expected_public_revision =
        request.expected_public_revision;
    context.query_request.expected_native_revision =
        request.expected_native_revision;
    context.query_request.expected_date_raw = request.expected_date_raw;
    context.query_request.expected_owner_character_id =
        request.expected_owner_character_id;
    context.operation = Operation::submit_assignment;
    context.query_result = {};
    context.action_ack = {};
    context.action_receipt = {};
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

bool PrepareCouncilApplicationMainReceiptV1(
    CouncilApplicationMainContextV1 &context,
    const ck3_11906::CouncilCompositionStewardCandidatesRequestV1
        &request) noexcept {
  if (!context.shared_state || !context.shared_state->action_runtime_ready ||
      !context.shared_state->has_pending_ack || context.ticket.sequence != 0 ||
      request.expected_snapshot_id.empty()) {
    SetFailure(context, Completion::receipt_rejected,
               Failure::pending_ack_unavailable,
               "receipt_prepare_pending_ack_unavailable");
    return false;
  }
  try {
    context.query_snapshot_id.assign(request.expected_snapshot_id);
    context.query_request = request;
    context.query_request.expected_snapshot_id = context.query_snapshot_id;
    context.operation = Operation::verify_assignment_receipt;
    context.query_result = {};
    context.action_ack = context.shared_state->pending_ack;
    context.action_receipt = {};
    context.completion = Completion::not_executed;
    context.failure = Failure::none;
    context.failure_reason.clear();
    return true;
  } catch (...) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "receipt_prepare_exception");
    return false;
  }
}

ck3_11906::MainThreadQuerySubmitResultV1 TryQueueCouncilApplicationMainV1(
    CouncilApplicationMainContextV1 &context) noexcept {
  if (!context.shared_state || !context.shared_state->configured ||
      context.mailbox == nullptr || context.operation == Operation::none ||
      context.ticket.sequence != 0) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "mailbox_queue_contract_failed");
    return ck3_11906::MainThreadQuerySubmitResultV1::invalid_request;
  }
  const auto result = ck3_11906::TrySubmitMainThreadQueryV1(
      *context.mailbox, &ExecuteCouncilApplicationMainV1, &context,
      context.ticket);
  if (result != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
    SetFailure(context, Completion::infrastructure_red, Failure::transport,
               "mailbox_submit_rejected");
  }
  return result;
}

ck3_11906::MainThreadQueryReclaimResultV1 ReclaimCouncilApplicationMainV1(
    CouncilApplicationMainContextV1 &context) noexcept {
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

bool ExecuteCouncilApplicationMainV1(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *context = static_cast<CouncilApplicationMainContextV1 *>(opaque);
  if (context == nullptr || !IsExecutingExactMailboxSlot(*context, stamp)) {
    if (context != nullptr) {
      SetFailure(*context, Completion::infrastructure_red,
                 Failure::mailbox_identity,
                 "executing_mailbox_identity_failed");
    }
    return false;
  }
  try {
    ++context->executor_invocations;
    context->active_stamp = &stamp;
    bool result = false;
    switch (context->operation) {
    case Operation::query_candidates: result = ExecuteQuery(*context); break;
    case Operation::submit_assignment:
      result = ExecuteSubmit(*context, stamp);
      break;
    case Operation::verify_assignment_receipt:
      result = ExecuteReceipt(*context);
      break;
    case Operation::none: break;
    }
    context->active_stamp = nullptr;
    if (result) return true;
  } catch (...) {
    context->active_stamp = nullptr;
    SetFailure(*context, Completion::infrastructure_red, Failure::transport,
               "application_main_executor_exception");
    return false;
  }
  context->active_stamp = nullptr;
  SetFailure(*context, Completion::infrastructure_red, Failure::transport,
             "application_main_operation_invalid");
  return false;
}

bool CouncilApplicationMainQueryRuntimeReadyV1(
    const CouncilApplicationMainStateV1 &state) noexcept {
  return state.configured && state.query_runtime_ready &&
      state.binding.attached;
}

bool CouncilApplicationMainActionRuntimeReadyV1(
    const CouncilApplicationMainStateV1 &state) noexcept {
  return CouncilApplicationMainQueryRuntimeReadyV1(state) &&
      state.action_runtime_ready;
}

std::string SerializeCouncilApplicationMainResultEnvelopeV1(
    const CouncilApplicationMainContextV1 &context,
    std::string_view protocol_request_id) {
  if (protocol_request_id.empty() || context.ticket.sequence == 0 ||
      context.operation == Operation::none) {
    return {};
  }
  std::string output;
  output.reserve(4096);
  output += "{\"type\":\"command_result\",\"protocol_version\":1,";
  output += "\"request_id\":";
  AppendJsonString(output, protocol_request_id);
  output += ",\"ok\":true,\"result\":{\"schema\":";
  AppendJsonString(output, kCouncilApplicationMainEnvelopeSchemaV1);
  output += ",\"step\":";
  switch (context.operation) {
  case Operation::query_candidates:
    AppendJsonString(output, kCouncilCompositionCandidatesStepV1);
    break;
  case Operation::submit_assignment:
    AppendJsonString(output, kCouncilAssignCouncillorStepV1);
    break;
  case Operation::verify_assignment_receipt:
    AppendJsonString(output, kCouncilAssignCouncillorReceiptStepV1);
    break;
  case Operation::none: return {};
  }
  output += ",\"accepted\":true,\"status\":";
  if (context.operation == Operation::query_candidates) {
    AppendJsonString(output,
        context.query_result.status ==
                game::CouncilCompositionCandidatesPublicStatusV1::available
            ? "available" : "unavailable");
  } else if (context.operation == Operation::submit_assignment) {
    AppendJsonString(output, AckStatusName(context.action_ack.status));
  } else {
    AppendJsonString(output, ReceiptStatusName(context.action_receipt.status));
  }
  output += ",\"query_sequence\":" +
      std::to_string(context.ticket.sequence);
  const auto revision = context.operation == Operation::submit_assignment
      ? context.action_ack.pre_public_revision
      : context.operation == Operation::verify_assignment_receipt
          ? context.action_receipt.post_public_revision
          : context.query_result.public_revision;
  output += ",\"snapshot_revision\":" + std::to_string(revision);
  if (context.operation == Operation::query_candidates) {
    const auto payload =
        ck3_11906::SerializeCouncilCompositionCandidatesPublicV1(
            context.query_result);
    if (payload.empty()) return {};
    output += ",\"council_composition_candidates\":" + payload;
  } else if (context.operation == Operation::submit_assignment) {
    output += ",\"council_assign_councillor_ack\":";
    AppendAck(output, context.action_ack);
  } else {
    output += ",\"council_assign_councillor_receipt\":";
    AppendReceipt(output, context.action_receipt);
  }
  output += ",\"backend_id\":\"native-headless\"}}";
  return output;
}

std::string_view CouncilApplicationMainFailureNameV1(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::not_configured: return "not_configured";
  case Failure::mailbox_identity: return "mailbox_identity";
  case Failure::source_capture_unavailable:
    return "source_capture_unavailable";
  case Failure::private_reader_unavailable:
    return "private_reader_unavailable";
  case Failure::enrichment_unavailable: return "enrichment_unavailable";
  case Failure::projection_unavailable: return "projection_unavailable";
  case Failure::action_runtime_unavailable:
    return "action_runtime_unavailable";
  case Failure::action_rejected: return "action_rejected";
  case Failure::pending_ack_unavailable: return "pending_ack_unavailable";
  case Failure::receipt_rejected: return "receipt_rejected";
  case Failure::transport: return "transport";
  }
  return "transport";
}

} // namespace xar::bridge
