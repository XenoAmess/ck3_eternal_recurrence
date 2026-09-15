#include "xar_bridge/council_application_main_private_transport_v1.hpp"

#include "xar_bridge/protocol.hpp"

#include <algorithm>
#include <limits>
#include <utility>

namespace xar::bridge {
namespace {

using MailboxState = ck3_11906::MainThreadQueryMailboxStateV1;

std::string Result(std::string_view request_id, std::string_view step,
                   bool ok, std::string_view detail) {
  std::string result;
  result.reserve(256);
  result += "{\"type\":\"command_result\",\"protocol_version\":1,";
  result += "\"request_id\":\"";
  result += request_id;
  result += "\",\"ok\":";
  result += ok ? "true" : "false";
  if (ok) {
    result += ",\"result\":{\"private_council_transport\":true,";
    result += "\"advertised\":false,\"step\":\"";
    result += step;
    result += "\",\"status\":\"";
    result += detail;
    result += "\"}}";
  } else {
    result += ",\"error\":\"";
    result += detail;
    result += "\"}";
  }
  return result;
}

bool CaptureSourceFrame(
    void *opaque,
    const ck3_11906::CouncilCompositionStewardCandidatesRequestV1 &request,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    ck3_11906::CouncilCompositionStewardCandidatesFrameV1 &output) noexcept {
  auto *transport =
      static_cast<CouncilApplicationMainPrivateTransportV1 *>(opaque);
  if (transport == nullptr || !transport->configured ||
      !transport->shared.binding.attached ||
      request.expected_snapshot_id != transport->expected_snapshot_id ||
      request.expected_public_revision == 0 ||
      request.expected_native_revision == 0) {
    return false;
  }
  game::Snapshot current{};
  if (!ck3_11906::ReadSnapshot(transport->bindings, current) ||
      current != transport->expected_snapshot || !current.paused ||
      !current.map_ready || !current.has_played_character ||
      !current.played_character_alive ||
      current.played_character_id <= 0 ||
      current.date_raw != stamp.date_raw ||
      current.date_raw != request.expected_date_raw ||
      current.played_character_id != request.expected_owner_character_id) {
    return false;
  }
  auto &binding = transport->shared.binding;
  std::uintptr_t owner = 0;
  if (binding.operations.resolve_character == nullptr ||
      !binding.operations.resolve_character(
          binding.operation_context, binding.module_base,
          current.played_character_id, owner) ||
      owner == 0 ||
      transport->expected_snapshot_id.size() >= output.snapshot_id.size()) {
    return false;
  }
  output = {};
  std::copy(transport->expected_snapshot_id.begin(),
            transport->expected_snapshot_id.end(), output.snapshot_id.begin());
  output.public_revision = request.expected_public_revision;
  output.native_revision = request.expected_native_revision;
  output.date_raw = current.date_raw;
  output.paused = current.paused;
  output.map_ready = current.map_ready;
  output.has_played_character = current.has_played_character;
  output.played_character_alive = current.played_character_alive;
  output.played_character_id = current.played_character_id;
  output.played_character = owner;
  output.played_character_identity_round_trip = true;
  return true;
}

bool ReadySnapshot(const game::Snapshot &snapshot) noexcept {
  return snapshot.paused && snapshot.map_ready &&
         snapshot.has_played_character && snapshot.played_character_alive &&
         snapshot.played_character_id > 0;
}

bool Revision(std::string_view payload, std::uint64_t expected) noexcept {
  std::uint64_t value = 0;
  return expected != 0 &&
         JsonUnsignedField(payload, "expected_revision", value) &&
         value == expected;
}

ck3_11906::CouncilCompositionStewardCandidatesRequestV1 SnapshotRequest(
    CouncilApplicationMainPrivateTransportV1 &transport,
    const game::Snapshot &snapshot, std::uint64_t revision) {
  transport.expected_snapshot = snapshot;
  transport.expected_snapshot_id = "native:" + std::to_string(revision);
  ck3_11906::CouncilCompositionStewardCandidatesRequestV1 request{};
  request.expected_snapshot_id = transport.expected_snapshot_id;
  request.expected_public_revision = revision;
  request.expected_native_revision = revision;
  request.expected_date_raw = snapshot.date_raw;
  request.expected_owner_character_id = snapshot.played_character_id;
  return request;
}

bool Queue(CouncilApplicationMainPrivateTransportV1 &transport) noexcept {
  if (TryQueueCouncilApplicationMainV1(transport.context) !=
      ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
    return false;
  }
  transport.in_flight = true;
  return true;
}

} // namespace

bool IsCouncilApplicationMainPrivateStepV1(std::string_view step) noexcept {
  return step == kCouncilPrivateQueryStepV1 ||
         step == kCouncilPrivateAssignStepV1 ||
         step == kCouncilPrivateReceiptStepV1 ||
         step == kCouncilPrivateStatusStepV1;
}

bool ConfigureCouncilApplicationMainPrivateTransportV1(
    CouncilApplicationMainPrivateTransportV1 &transport,
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const ck3_11906::Bindings &bindings, std::uintptr_t module_base,
    bool action_admitted,
    EvaluateCouncilAssignCouncillorNativeGatesV1 evaluate_action_gates,
    void *action_gate_context) noexcept {
  if (transport.configured || module_base == 0) return false;
  transport.mailbox = &mailbox;
  transport.bindings = bindings;
  auto &adapter = transport.submit_adapter;
  adapter.environment.exact_build_admitted = true;
  adapter.environment.admitted_executable_sha256 =
      ck3_11906::kCouncilAssignCouncillorExecutableSha256V1;
  adapter.environment.module_base = module_base;
  adapter.environment.native_command_abi_certified = action_admitted;
  adapter.environment.private_candidate_admitted = action_admitted;
  adapter.environment.offline_fixture = false;
  adapter.helper_override = nullptr;

  CouncilApplicationMainConfigurationV1 configuration{};
  configuration.enabled = true;
  configuration.query_runtime_enabled = true;
  configuration.action_runtime_enabled =
      action_admitted && evaluate_action_gates != nullptr;
  configuration.exact_build_admitted = true;
  configuration.private_candidate_admitted = action_admitted;
  configuration.native_command_abi_certified = action_admitted;
  configuration.offline_fixture = false;
  configuration.module_base = module_base;
  configuration.admitted_executable_sha256 =
      ck3_11906::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  configuration.source_context = &transport;
  configuration.capture_source_frame = &CaptureSourceFrame;
  configuration.action_gate_context = action_gate_context;
  configuration.evaluate_action_gates = evaluate_action_gates;
  configuration.submit_adapter = &adapter;
  transport.configured = ConfigureCouncilApplicationMainV1(
      mailbox, configuration, transport.shared, transport.context);
  return transport.configured;
}

void PollCouncilApplicationMainPrivateTransportV1(
    CouncilApplicationMainPrivateTransportV1 &transport) noexcept {
  if (!transport.in_flight || transport.mailbox == nullptr ||
      transport.context.ticket.sequence == 0) return;
  const auto sequence = transport.context.ticket.sequence;
  const auto &mailbox = *transport.mailbox;
  if (mailbox.published_sequence.load(std::memory_order_acquire) != sequence)
    return;
  const auto state = mailbox.state.load(std::memory_order_acquire);
  if (state == MailboxState::queued || state == MailboxState::executing ||
      state == MailboxState::publishing) return;

  if (state != MailboxState::completed ||
      mailbox.completed_sequence.load(std::memory_order_acquire) != sequence) {
    transport.context.completion =
        CouncilApplicationMainCompletionV1::infrastructure_red;
    transport.context.failure = CouncilApplicationMainFailureV1::transport;
    transport.context.failure_reason = "private_mailbox_terminal_failure";
  }
  try {
    transport.completed = transport.context;
    transport.has_completed = true;
  } catch (...) {
    transport.has_completed = false;
  }
  if (ReclaimCouncilApplicationMainV1(transport.context) ==
      ck3_11906::MainThreadQueryReclaimResultV1::reclaimed) {
    transport.in_flight = false;
  }
}

std::string ExecuteCouncilApplicationMainPrivateStepV1(
    CouncilApplicationMainPrivateTransportV1 &transport,
    std::string_view step, std::string_view payload,
    std::string_view protocol_request_id,
    const game::Snapshot &published_snapshot,
    std::uint64_t published_revision) {
  if (!IsCouncilApplicationMainPrivateStepV1(step))
    return Result(protocol_request_id, step, false, "private_step_unknown");
  PollCouncilApplicationMainPrivateTransportV1(transport);
  if (step == kCouncilPrivateStatusStepV1) {
    if (transport.has_completed) {
      auto response = SerializeCouncilApplicationMainResultEnvelopeV1(
          transport.completed, protocol_request_id);
      transport.completed = {};
      transport.has_completed = false;
      return response.empty()
                 ? Result(protocol_request_id, step, false,
                          "private_result_serialization_failed")
                 : response;
    }
    return Result(protocol_request_id, step, true,
                  transport.in_flight ? "pending" : "idle");
  }
  if (!transport.configured || transport.in_flight || transport.has_completed)
    return Result(protocol_request_id, step, false,
                  "private_transport_not_ready_or_busy");
  if (!Revision(payload, published_revision) ||
      !ReadySnapshot(published_snapshot))
    return Result(protocol_request_id, step, false,
                  "private_snapshot_revision_or_state_invalid");
  game::Snapshot current{};
  if (!ck3_11906::ReadSnapshot(transport.bindings, current) ||
      current != published_snapshot)
    return Result(protocol_request_id, step, false,
                  "private_snapshot_changed");

  if (step == kCouncilPrivateQueryStepV1) {
    const auto request =
        SnapshotRequest(transport, current, published_revision);
    if (!PrepareCouncilApplicationMainQueryV1(transport.context, request) ||
        !Queue(transport))
      return Result(protocol_request_id, step, false,
                    "private_query_queue_unavailable");
    return Result(protocol_request_id, step, true, "pending");
  }
  if (!CouncilApplicationMainActionRuntimeReadyV1(transport.shared))
    return Result(protocol_request_id, step, false,
                  "complete_native_action_gates_not_bound");

  if (step == kCouncilPrivateAssignStepV1) {
    std::uint64_t candidate = 0;
    if (!JsonUnsignedField(payload, "candidate_character_id", candidate) ||
        candidate == 0 ||
        candidate > static_cast<std::uint64_t>(
                        (std::numeric_limits<std::int32_t>::max)()))
      return Result(protocol_request_id, step, false,
                    "private_candidate_id_invalid");
    game::CouncilAssignCouncillorActionRequestV1 request{};
    if (!ck3_11906::PrepareCouncilAssignCouncillorActionRequestV1(
            transport.context.query_result,
            static_cast<std::int32_t>(candidate), protocol_request_id,
            request) ||
        request.expected_native_revision != published_revision ||
        request.expected_owner_character_id != current.played_character_id ||
        request.expected_date_raw != current.date_raw)
      return Result(protocol_request_id, step, false,
                    "private_candidate_frame_changed");
    transport.expected_snapshot = current;
    transport.expected_snapshot_id = request.expected_snapshot_id;
    if (!PrepareCouncilApplicationMainSubmitV1(transport.context, request) ||
        !Queue(transport))
      return Result(protocol_request_id, step, false,
                    "private_assignment_queue_unavailable");
    return Result(protocol_request_id, step, true, "pending");
  }

  // Receipt must read a later independent paused snapshot. The shared runtime
  // keeps the helper-only ACK pending until that post-frame is observed.
  if (!transport.shared.has_pending_ack ||
      published_revision <= transport.shared.pending_ack.pre_native_revision)
    return Result(protocol_request_id, step, false,
                  "private_independent_receipt_frame_unavailable");
  const auto request = SnapshotRequest(transport, current, published_revision);
  if (!PrepareCouncilApplicationMainReceiptV1(transport.context, request) ||
      !Queue(transport))
    return Result(protocol_request_id, step, false,
                  "private_receipt_queue_unavailable");
  return Result(protocol_request_id, step, true, "pending");
}

} // namespace xar::bridge
