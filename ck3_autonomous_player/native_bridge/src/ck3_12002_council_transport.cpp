#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12002_council_transport.hpp"

#include "xar_bridge/council_application_main_private_transport_v1.hpp"
#include "xar_bridge/protocol.hpp"

#include <algorithm>
#include <limits>

namespace xar::ck3_12002 {
namespace {
using Operation = bridge::CouncilApplicationMainOperationV1;
using Completion = bridge::CouncilApplicationMainCompletionV1;
using Failure = bridge::CouncilApplicationMainFailureV1;
using MailboxState = ck3_11906::MainThreadQueryMailboxStateV1;

template<std::size_t N> std::string_view Fixed(const std::array<char,N>& value) {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return end == value.end() ? std::string_view{} :
      std::string_view(value.data(), static_cast<std::size_t>(end-value.begin()));
}

std::string Result(std::string_view request_id, std::string_view step,
                   std::string_view status) {
  std::string result;
  result.reserve(256);
  result += "{\"type\":\"command_result\",\"protocol_version\":1,";
  result += "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":true,\"result\":{\"private_council_transport\":true,";
  result += "\"advertised\":false,\"step\":\"";
  result += step;
  result += "\",\"status\":\"";
  result += status;
  result += "\"}}";
  return result;
}

bool ReadySnapshot(const game::Snapshot& snapshot) noexcept {
  return snapshot.paused && snapshot.map_ready &&
      snapshot.has_played_character && snapshot.played_character_alive &&
      snapshot.played_character_id > 0;
}

bool IsApplicationMain(void* opaque) noexcept {
  const auto* state = static_cast<CouncilTransportState12002*>(opaque);
  return state != nullptr && state->configured &&
      state->context.active_stamp != nullptr &&
      state->context.active_stamp->thread_id != 0 &&
      state->context.active_stamp->thread_id == GetCurrentThreadId();
}

bool CaptureSourceFrame(void* opaque,
    CouncilCandidatesFrameV1& output) noexcept {
  output = {};
  auto* state = static_cast<CouncilTransportState12002*>(opaque);
  if (!IsApplicationMain(opaque) || !state->core.enabled ||
      !ReadySnapshot(state->expected_snapshot)) return false;
  const auto& context = state->context;
  const auto& request = context.query_request;
  const auto& stamp = *context.active_stamp;
  if (!stamp.paused || stamp.game_state == 0 || stamp.jomini_state == 0 ||
      state->expected_revision == 0 ||
      request.expected_snapshot_id != state->expected_snapshot_id ||
      request.expected_public_revision != state->expected_revision ||
      request.expected_native_revision != state->expected_revision ||
      state->expected_snapshot_id.empty() ||
      state->expected_snapshot_id.size() >= output.snapshot_id.size())
    return false;

  CoreSnapshotPrefix current{};
  if (!ReadCoreSnapshot(state->core, current)) return false;
  const auto& published = state->expected_snapshot;
  if (current.clock.date_raw != published.date_raw ||
      current.clock.date_raw != stamp.date_raw ||
      current.clock.date_raw != request.expected_date_raw ||
      current.clock.paused != published.paused ||
      current.local_player_id != published.player_id ||
      current.map_ready != published.map_ready ||
      current.has_played_character != published.has_played_character ||
      current.played_character_alive != published.played_character_alive ||
      current.played_character_id != published.played_character_id ||
      current.played_character_id != request.expected_owner_character_id)
    return false;

  const void* owner = nullptr;
  if (!ResolveCouncilCharacter12002(context.candidates_environment,
      context.candidates_access, current.played_character_id, owner) ||
      owner == nullptr) return false;

  // The version provider resolves the requested active task in this same frame.
  // This callback supplies only the campaign-root source fields.
  std::copy(state->expected_snapshot_id.begin(),
      state->expected_snapshot_id.end(), output.snapshot_id.begin());
  output.public_revision = request.expected_public_revision;
  output.native_revision = request.expected_native_revision;
  output.date_raw = current.clock.date_raw;
  output.paused = current.clock.paused;
  output.map_ready = current.map_ready;
  output.has_played_character = current.has_played_character;
  output.played_character_alive = current.played_character_alive;
  output.played_character_id = current.played_character_id;
  output.played_character = reinterpret_cast<std::uintptr_t>(owner);
  output.played_character_identity_round_trip = true;
  return true;
}

void PrepareOperation(CouncilTransportState12002& state,
    Operation operation) noexcept {
  auto& context = state.context;
  context.operation = operation;
  context.ticket = {};
  context.active_stamp = nullptr;
  context.wire.operation = operation;
  context.wire.ticket = {};
  context.wire.completion = Completion::not_executed;
  context.wire.failure = Failure::none;
  context.wire.failure_reason.clear();
  context.wire.final_gate_row_count = 0;
  context.wire.action_ack = {};
  context.wire.action_receipt = {};
}

void SnapshotRequest(CouncilTransportState12002& state,
    const game::Snapshot& snapshot, std::uint64_t revision,
    std::string_view position_key = kCouncilCandidatesStewardPosition12002) {
  state.expected_snapshot = snapshot;
  state.expected_snapshot_id = "native:" + std::to_string(revision);
  state.expected_revision = revision;
  state.query_position_key.assign(position_key);
  state.context.query_request = {state.expected_snapshot_id, revision,
      revision, snapshot.date_raw, snapshot.played_character_id, state.query_position_key};
}

bool Queue(CouncilTransportState12002& state) noexcept {
  if (state.mailbox == nullptr ||
      ck3_11906::TrySubmitMainThreadQueryV1(*state.mailbox,
          &ExecuteCouncilMailbox12002, &state.context,
          state.context.ticket) !=
          ck3_11906::MainThreadQuerySubmitResultV1::submitted) return false;
  state.in_flight = true;
  return true;
}
} // namespace

bool IsCouncilPrivate12002(std::string_view step) noexcept {
  return step == bridge::kCouncilPrivateQueryStepV1 ||
      step == bridge::kCouncilFinalGatesPrivateStepV1 ||
      step == bridge::kCouncilPrivateAssignStepV1 ||
      step == bridge::kCouncilPrivateReceiptStepV1 ||
      step == bridge::kCouncilPrivateStatusStepV1;
}

bool ConfigureCouncilTransport12002(CouncilTransportState12002& state,
    ck3_11906::MainThreadQueryMailboxV1& mailbox,
    std::uintptr_t module_base, std::string_view executable_sha256,
    bool action_enabled, bool gate_query_enabled) noexcept {
  if (state.configured || state.in_flight || module_base == 0 ||
      executable_sha256 != kExecutableSha256) return false;
  state.core = BindCoreImage(module_base, kExecutableSha256);
  state.context.candidates_environment =
      BindCouncilCandidates12002(module_base, kExecutableSha256);
  state.context.gates_environment =
      BindCouncilGates12002(module_base, kExecutableSha256);
  state.context.submit.environment =
      BindCouncilAssign12002(module_base, kExecutableSha256);
  if (!state.core.enabled ||
      !state.context.candidates_environment.exact_build_admitted ||
      !state.context.gates_environment.exact_build_admitted ||
      !state.context.submit.environment.exact_build_admitted) return false;
  state.mailbox = &mailbox;
  state.context.shared_state = &state.shared;
  state.context.candidates_access.context = &state;
  state.context.candidates_access.capture_frame = &CaptureSourceFrame;
  state.context.candidates_access.is_main_thread = &IsApplicationMain;
  state.context.private_action_enabled = action_enabled;
  state.context.wire.mailbox = &mailbox;
  state.action_enabled = action_enabled;
  state.gate_query_enabled = gate_query_enabled;
  state.configured = true;
  return true;
}

void PollCouncilTransport12002(CouncilTransportState12002& state) noexcept {
  if (!state.in_flight || state.mailbox == nullptr ||
      state.context.ticket.sequence == 0) return;
  const auto sequence = state.context.ticket.sequence;
  const auto& mailbox = *state.mailbox;
  if (mailbox.published_sequence.load(std::memory_order_acquire) != sequence)
    return;
  const auto terminal = mailbox.state.load(std::memory_order_acquire);
  if (terminal == MailboxState::queued || terminal == MailboxState::executing ||
      terminal == MailboxState::publishing) return;
  if (terminal != MailboxState::completed ||
      mailbox.completed_sequence.load(std::memory_order_acquire) != sequence) {
    state.context.wire.operation = state.context.operation;
    state.context.wire.ticket = state.context.ticket;
    state.context.wire.completion = Completion::infrastructure_red;
    state.context.wire.failure = Failure::transport;
    state.context.wire.failure_reason = "private_mailbox_terminal_failure";
  }
  try {
    state.completed = state.context;
    state.has_completed = true;
  } catch (...) {
    state.has_completed = false;
  }
  if (ck3_11906::ReclaimMainThreadQueryV1(*state.mailbox,
      state.context.ticket) ==
      ck3_11906::MainThreadQueryReclaimResultV1::reclaimed)
    state.in_flight = false;
}

bool HandleCouncilPrivate12002(const game::GameAdapter& adapter,
    ck3_11906::MainThreadQueryMailboxV1& mailbox,
    const game::Snapshot& published, std::uint64_t revision,
    std::string_view step, std::string_view payload,
    std::string_view request_id, CouncilTransportState12002& state,
    std::string& serialized, std::string& failure) noexcept {
  serialized.clear();
  failure.clear();
  try {
    if (!IsCouncilPrivate12002(step)) {
      failure = "private_step_unknown"; return false;
    }
    if (xar::game::ReviewedCrozierAbiVersion(adapter.descriptor()) != "1.20.0.2" ||
        xar::game::ReviewedCrozierAbiSha256(adapter.descriptor()) != kExecutableSha256 ||
        !state.configured || state.mailbox != &mailbox) {
      failure = "private_transport_not_configured_for_exact_build";
      return false;
    }
    PollCouncilTransport12002(state);
    if (step == bridge::kCouncilPrivateStatusStepV1) {
      if (state.has_completed) {
        serialized = SerializeCouncilMailbox12002(state.completed, request_id);
        if (serialized.empty()) {
          failure = "private_result_serialization_failed"; return false;
        }
        state.completed = {};
        state.has_completed = false;
      } else {
        serialized = Result(request_id, step, state.in_flight ? "pending" : "idle");
      }
      return true;
    }
    if (state.in_flight || state.has_completed) {
      failure = "private_transport_not_ready_or_busy"; return false;
    }
    std::uint64_t expected_revision = 0;
    if (revision == 0 ||
        !bridge::JsonUnsignedField(payload, "expected_revision", expected_revision) ||
        expected_revision != revision || !ReadySnapshot(published)) {
      failure = "private_snapshot_revision_or_state_invalid"; return false;
    }

    if (step == bridge::kCouncilPrivateQueryStepV1 ||
        step == bridge::kCouncilFinalGatesPrivateStepV1) {
      if (step == bridge::kCouncilFinalGatesPrivateStepV1 &&
          !state.gate_query_enabled) {
        failure = "private_final_gate_query_not_admitted"; return false;
      }
      std::string position_key{kCouncilCandidatesStewardPosition12002};
      if (payload.find("\"position_key\"") != std::string_view::npos &&
          !bridge::JsonStringField(payload, "position_key", position_key,
              game::kCouncilCompositionStewardPositionKeyCapacityV1 - 1)) {
        failure = "private_position_key_invalid"; return false;
      }
      if (CouncilCandidatesProfile12002(position_key).position_key.empty()) {
        failure = "private_position_outside_coverage"; return false;
      }
      SnapshotRequest(state, published, revision, position_key);
      PrepareOperation(state, step == bridge::kCouncilPrivateQueryStepV1 ?
          Operation::query_candidates : Operation::query_final_gates);
      if (!Queue(state)) {
        failure = step == bridge::kCouncilPrivateQueryStepV1 ?
            "private_query_queue_unavailable" :
            "private_final_gate_query_queue_unavailable";
        return false;
      }
      serialized = Result(request_id, step, "pending");
      return true;
    }
    if (!state.action_enabled) {
      failure = "complete_native_action_gates_not_bound"; return false;
    }
    if (step == bridge::kCouncilPrivateAssignStepV1) {
      std::uint64_t candidate = 0;
      if (!bridge::JsonUnsignedField(payload, "candidate_character_id", candidate) ||
          candidate == 0 || candidate > static_cast<std::uint64_t>(
              (std::numeric_limits<std::int32_t>::max)())) {
        failure = "private_candidate_id_invalid"; return false;
      }
      game::CouncilAssignCouncillorActionRequestV1 request{};
      const auto& observed = state.context.wire.query_result;
      const auto position = Fixed(observed.position_key);
      const bool supported = position == kCouncilCandidatesStewardPosition12002 ||
          position == kCouncilCandidatesChancellorPosition12002;
      if (!supported || !ck3_11906::PrepareCouncilAssignCouncillorActionRequestV1(
          observed, static_cast<std::int32_t>(candidate),
          request_id, request, position) || request.expected_native_revision != revision ||
          request.expected_public_revision != revision ||
          request.expected_owner_character_id != published.played_character_id ||
          request.expected_date_raw != published.date_raw) {
        failure = "private_candidate_frame_changed"; return false;
      }
      state.expected_snapshot = published;
      state.expected_snapshot_id = request.expected_snapshot_id;
      state.expected_revision = revision;
      state.context.action_request = request;
      state.context.query_request = {state.expected_snapshot_id,
          request.expected_public_revision, request.expected_native_revision,
          request.expected_date_raw, request.expected_owner_character_id,
          state.context.action_request.position_key};
      PrepareOperation(state, Operation::submit_assignment);
      if (!Queue(state)) {
        failure = "private_assignment_queue_unavailable"; return false;
      }
      serialized = Result(request_id, step, "pending");
      return true;
    }
    // The ACK remains pending until a later independent paused frame proves
    // the incumbent changed. A command helper invocation is never a receipt.
    if (!state.shared.has_pending_ack ||
        revision <= state.shared.pending_ack.pre_native_revision) {
      failure = "private_independent_receipt_frame_unavailable"; return false;
    }
    SnapshotRequest(state, published, revision, state.shared.pending_ack.position_key);
    PrepareOperation(state, Operation::verify_assignment_receipt);
    if (!Queue(state)) {
      failure = "private_receipt_queue_unavailable"; return false;
    }
    serialized = Result(request_id, step, "pending");
    return true;
  } catch (...) {
    failure = "private_council_transport_exception";
    return false;
  }
}
} // namespace xar::ck3_12002
