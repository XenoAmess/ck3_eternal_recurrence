#include "xar_bridge/ck3_12002_council_runtime.hpp"
#include <algorithm>
#include <cstring>

namespace xar::ck3_12002 {
namespace {
using Operation = bridge::CouncilApplicationMainOperationV1;
using Completion = bridge::CouncilApplicationMainCompletionV1;
using Failure = game::CouncilAssignCouncillorFailureV1;
template<std::size_t N> std::string_view Fixed(const std::array<char,N>& value) {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return end == value.end() ? std::string_view{} :
      std::string_view(value.data(), static_cast<std::size_t>(end-value.begin()));
}
bool ActionFrame(CouncilMailboxContext12002& context,
    game::CouncilAssignCouncillorFrameV1& output,
    std::string_view position_key = kCouncilCandidatesStewardPosition12002) noexcept {
  output = {};
  CouncilCandidatesFrameV1 source{};
  if (!CaptureCouncilCandidatesFrame12002(context.candidates_environment,
      context.candidates_access, source, position_key)) return false;
  std::int32_t incumbent = -1;
  if (!ReadCouncilMemory12002(context.candidates_access,
      reinterpret_cast<const void*>(source.active_task+kCouncilCandidatesTaskIncumbentOffset12002),
      &incumbent, sizeof(incumbent))) return false;
  const void* resolved = nullptr;
  if (incumbent != -1 && !ResolveCouncilCharacter12002(context.candidates_environment,
      context.candidates_access, incumbent, resolved)) return false;
  output.available = true;
  output.paused = source.paused;
  output.map_ready = source.map_ready;
  output.snapshot_id.assign(Fixed(source.snapshot_id));
  output.public_revision = source.public_revision;
  output.native_revision = source.native_revision;
  output.date_raw = source.date_raw;
  output.owner_character_id = source.played_character_id;
  output.owner_identity_round_trip = source.played_character_identity_round_trip;
  output.position_key.assign(Fixed(source.position_key));
  output.active_task_id = source.active_task_id;
  output.active_task_identity_round_trip = source.active_task_identity_round_trip;
  output.has_incumbent = incumbent != -1;
  output.incumbent_character_id = incumbent;
  output.incumbent_identity_round_trip = output.has_incumbent && resolved != nullptr;
  return true;
}
bool CaptureAction(void* raw, game::CouncilAssignCouncillorFrameV1& output) noexcept {
  return raw != nullptr && ActionFrame(*static_cast<CouncilMailboxContext12002*>(raw), output);
}
CouncilCandidatesRequestV1 RequestFor(const game::CouncilAssignCouncillorFrameV1& frame) {
  return {frame.snapshot_id, frame.public_revision, frame.native_revision,
      frame.date_raw, frame.owner_character_id, frame.position_key};
}
bool GatesFor(CouncilMailboxContext12002& context,
    const game::CouncilAssignCouncillorFrameV1& frame, std::int32_t candidate,
    const game::CouncilCompositionCandidatesPublicV1& candidates,
    game::CouncilAssignCouncillorFinalLegalityV1& output) noexcept {
  output = {};
  output.owner_character_id = frame.owner_character_id;
  output.active_task_id = frame.active_task_id;
  output.position_key = frame.position_key;
  output.candidate_character_id = candidate;
  for (std::uint32_t i=0; i<candidates.candidate_count; ++i)
    if (candidates.candidates[i].character_id == candidate) ++output.candidate_match_count;
  const void* resolved = nullptr;
  output.candidate_identity_round_trip = ResolveCouncilCharacter12002(
      context.candidates_environment, context.candidates_access, candidate, resolved);
  if (output.candidate_match_count != 1 || !output.candidate_identity_round_trip) {
    output.available = true;
    return true; // typed action retains exact-collection failure.
  }
  return EvaluateCouncilGates12002(context.gates_environment, frame, candidate,
      const_cast<void*>(resolved), output);
}
bool RecheckAction(void* raw, const game::CouncilAssignCouncillorFrameV1& frame,
    std::int32_t candidate, game::CouncilAssignCouncillorFinalLegalityV1& output) noexcept {
  if (raw == nullptr) return false;
  auto& context = *static_cast<CouncilMailboxContext12002*>(raw);
  game::CouncilCompositionCandidatesPublicV1 candidates{};
  if (ReadCouncilCandidates12002(context.candidates_environment, context.candidates_access,
      RequestFor(frame), candidates) !=
      ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1::available) return false;
  return GatesFor(context, frame, candidate, candidates, output);
}
bool InvokeAction(void* raw,
    const game::CouncilAssignCouncillorNativeSubmissionV1& submission) noexcept {
  return raw != nullptr && InvokeCouncilAssign12002(
      &static_cast<CouncilMailboxContext12002*>(raw)->submit, submission);
}
void RejectPending(CouncilMailboxContext12002& context) {
  auto& ack=context.wire.action_ack;
  ack = {};
  ack.status = game::CouncilAssignCouncillorAckStatusV1::rejected_before_submit;
  ack.failure = Failure::callbacks_unavailable;
  ack.request_id = context.action_request.request_id;
  ack.position_key = context.action_request.position_key;
  ack.candidate_character_id = context.action_request.candidate_character_id;
  ack.native_reason_key = "pending_assignment_unresolved";
  context.wire.completion = Completion::action_rejected;
}
} // namespace

bool ExecuteCouncilMailbox12002(void* raw,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept {
  if (raw == nullptr) return false;
  auto& context = *static_cast<CouncilMailboxContext12002*>(raw);
  context.wire.operation = context.operation;
  context.wire.ticket = context.ticket;
  context.wire.completion = Completion::infrastructure_red;
  context.wire.failure_reason.clear();
  context.active_stamp = &stamp;
  struct Clear { CouncilMailboxContext12002& c; ~Clear(){c.active_stamp=nullptr;} } clear{context};
  try {
    if (stamp.thread_id == 0 || !stamp.paused || stamp.game_state == 0 ||
        !context.candidates_environment.exact_build_admitted ||
        context.candidates_environment.admitted_executable_sha256 != kExecutableSha256) {
      context.wire.failure_reason = "requires_exact_paused_application_main";
      return true;
    }
    context.gates_environment.current_thread_id = stamp.thread_id;
    context.gates_environment.application_main_thread_id = stamp.thread_id;
    context.submit.environment.current_thread_id = stamp.thread_id;
    context.submit.environment.application_main_thread_id = stamp.thread_id;
    context.submit.environment.private_candidate_admitted = context.private_action_enabled;
    if (context.operation == Operation::query_candidates ||
        context.operation == Operation::query_final_gates) {
      context.wire.query_result = {};
      const bool available = ReadCouncilCandidates12002(context.candidates_environment,
          context.candidates_access, context.query_request, context.wire.query_result) ==
          ck3_11906::ProjectCouncilCompositionCandidatesPublicResultV1::available;
      context.wire.completion = available ? Completion::query_available : Completion::query_unavailable;
      if (context.operation == Operation::query_candidates || !available) return true;
      game::CouncilAssignCouncillorFrameV1 frame{};
      const auto& candidates=context.wire.query_result;
      if (!ActionFrame(context, frame, context.query_request.position_key) ||
          frame.snapshot_id != Fixed(candidates.snapshot_id) ||
          frame.public_revision != candidates.public_revision || frame.native_revision != candidates.native_revision ||
          frame.date_raw != candidates.date_raw || frame.owner_character_id != candidates.owner_character_id ||
          frame.position_key != Fixed(candidates.position_key) ||
          frame.incumbent_character_id != candidates.incumbent_character_id) {
        context.wire.completion = Completion::query_unavailable;
        context.wire.failure_reason = "final_gate_frame_changed";
        return true;
      }
      context.wire.final_gate_row_count = 0;
      for(std::uint32_t i=0; i<candidates.candidate_count; ++i) {
        game::CouncilAssignCouncillorFinalLegalityV1 gates{};
        const auto id=candidates.candidates[i].character_id;
        if (!GatesFor(context, frame, id, candidates, gates) || !gates.available) {
          context.wire.completion = Completion::query_unavailable;
          context.wire.failure_reason = "native_final_gates_unavailable";
          context.wire.final_gate_row_count = 0;
          return true;
        }
        context.wire.final_gate_rows[i] = {id,true,gates.candidate_already_councillor,
            gates.candidate_is_guest,gates.pending_character_interaction,
            gates.incumbent_fireability_evaluated,gates.incumbent_can_be_fired};
        ++context.wire.final_gate_row_count;
      }
      game::CouncilAssignCouncillorFrameV1 after{};
      if (!ActionFrame(context, after, context.query_request.position_key) || after != frame) {
        context.wire.completion = Completion::query_unavailable;
        context.wire.failure_reason = "final_gate_frame_changed";
        context.wire.final_gate_row_count = 0;
      }
      return true;
    }
    if (context.operation == Operation::submit_assignment) {
      if (context.shared_state == nullptr || context.shared_state->has_pending_ack) {
        RejectPending(context); return true;
      }
      const CouncilAssignAccess12002 access{&context,CaptureAction,RecheckAction,InvokeAction};
      const auto status = ExecuteCouncilAssign12002(context.submit.environment, access,
          context.action_request, context.wire.action_ack);
      const bool pending = status == game::CouncilAssignCouncillorAckStatusV1::native_helper_invoked_verification_pending;
      context.wire.completion = pending ? Completion::submitted_verification_pending : Completion::action_rejected;
      if (pending) {
        context.shared_state->pending_ack = context.wire.action_ack;
        context.shared_state->pending_submit_sequence = context.ticket.sequence;
        context.shared_state->has_pending_ack = true;
      }
      return true;
    }
    if (context.operation == Operation::verify_assignment_receipt) {
      if (context.shared_state == nullptr || !context.shared_state->has_pending_ack ||
          context.ticket.sequence <= context.shared_state->pending_submit_sequence) {
        context.wire.action_receipt = {};
        context.wire.action_receipt.reason = "pending_ack_unavailable";
        context.wire.completion = Completion::receipt_rejected;
        return true;
      }
      game::CouncilAssignCouncillorFrameV1 after{};
      if (!ActionFrame(context, after)) after = {};
      const auto status = ck3_11906::VerifyCouncilAssignCouncillorActionReceiptV1(
          context.shared_state->pending_ack, after, context.wire.action_receipt);
      context.wire.completion = status == game::CouncilAssignCouncillorReceiptStatusV1::applied ?
          Completion::receipt_applied : Completion::receipt_rejected;
      if (status == game::CouncilAssignCouncillorReceiptStatusV1::applied)
        context.shared_state->has_pending_ack = false;
      return true;
    }
    context.wire.failure_reason = "operation_unavailable";
    return true;
  } catch (...) {
    context.wire.failure_reason = "council_executor_exception";
    return false;
  }
}

std::string SerializeCouncilMailbox12002(const CouncilMailboxContext12002& context,
    std::string_view request_id) {
  const auto candidates=SerializeCouncilCandidates12002(context.wire.query_result);
  return bridge::SerializeCouncilApplicationMainResultEnvelopeWithCandidatesV1(
      context.wire, request_id, candidates);
}
} // namespace xar::ck3_12002
