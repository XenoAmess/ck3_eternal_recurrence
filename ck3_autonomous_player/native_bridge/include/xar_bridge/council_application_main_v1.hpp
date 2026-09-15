#pragma once

#include "xar_bridge/council_assign_councillor_action_v1.hpp"
#include "xar_bridge/council_composition_candidates_enrichment_v1.hpp"
#include "xar_bridge/council_composition_steward_candidates_binding_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kCouncilCompositionCandidatesStepV1 =
    "query-council-composition-candidates-v1";
inline constexpr std::string_view kCouncilAssignCouncillorStepV1 =
    "assign-councillor-v1";
inline constexpr std::string_view kCouncilAssignCouncillorReceiptStepV1 =
    "query-assign-councillor-receipt-v1";
inline constexpr std::string_view kCouncilApplicationMainEnvelopeSchemaV1 =
    "xar.ck3.council-application-main/v1";

// The public bridge must not advertise either capability merely because this
// shared runtime is linked. Query advertisement additionally requires a real
// worker transport. Action advertisement additionally requires every final
// native gate below, including incumbent fireability, to be production-bound.
inline constexpr bool kCouncilApplicationMainAdvertisedByDefaultV1 = false;

enum class CouncilApplicationMainOperationV1 : std::uint8_t {
  none = 0,
  query_candidates,
  submit_assignment,
  verify_assignment_receipt,
};

enum class CouncilApplicationMainCompletionV1 : std::uint8_t {
  not_executed = 0,
  query_available,
  query_unavailable,
  submitted_verification_pending,
  action_rejected,
  receipt_applied,
  receipt_rejected,
  infrastructure_red,
};

enum class CouncilApplicationMainFailureV1 : std::uint8_t {
  none = 0,
  not_configured,
  mailbox_identity,
  source_capture_unavailable,
  private_reader_unavailable,
  enrichment_unavailable,
  projection_unavailable,
  action_runtime_unavailable,
  action_rejected,
  pending_ack_unavailable,
  receipt_rejected,
  transport,
};

// Supplies only the campaign-root portion of the source frame. Council7's
// exact-build binding resolves and round-trips the active steward task before
// the private reader sees it. The callback executes synchronously on the
// mailbox-owned application-main thread and must not retain native pointers.
using CaptureCouncilApplicationMainSourceFrameV1 = bool (*)(
    void *context,
    const ck3_11906::CouncilCompositionStewardCandidatesRequestV1 &request,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    ck3_11906::CouncilCompositionStewardCandidatesFrameV1 &output) noexcept;

// This is the only extension seam left around the Council22 semantic action.
// A production implementation must evaluate candidate-already-councillor,
// guest, pending-interaction and (for replacement) the exact incumbent
// fireability branch in the same application-main transaction. Returning true
// means the typed fields were evaluated, not that the assignment is legal.
using EvaluateCouncilAssignCouncillorNativeGatesV1 = bool (*)(
    void *context,
    const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept;

struct CouncilApplicationMainConfigurationV1 {
  bool enabled = false;
  bool query_runtime_enabled = false;
  bool action_runtime_enabled = false;
  bool exact_build_admitted = false;
  bool private_candidate_admitted = false;
  bool native_command_abi_certified = false;
  bool offline_fixture = false;
  std::uintptr_t module_base = 0;
  std::string_view admitted_executable_sha256{};
  ck3_11906::CouncilCompositionStewardCandidatesBindingEnvironmentV1
      binding{};
  void *source_context = nullptr;
  CaptureCouncilApplicationMainSourceFrameV1 capture_source_frame = nullptr;
  void *action_gate_context = nullptr;
  EvaluateCouncilAssignCouncillorNativeGatesV1 evaluate_action_gates =
      nullptr;
  ck3_11906::CouncilAssignCouncillorNativeSubmitAdapterV1 *submit_adapter =
      nullptr;
};

struct CouncilApplicationMainStateV1 {
  ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1 binding{};
  ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1
      reader_environment{};
  ck3_11906::CouncilCompositionStewardCandidatesAccessV1 reader_access{};
  game::CouncilAssignCouncillorActionAckV1 pending_ack{};
  std::uint64_t pending_submit_sequence = 0;
  bool configured = false;
  bool query_runtime_ready = false;
  bool action_runtime_ready = false;
  bool has_pending_ack = false;
};

struct CouncilApplicationMainContextV1 {
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  CouncilApplicationMainStateV1 *shared_state = nullptr;
  CouncilApplicationMainConfigurationV1 configuration{};
  ck3_11906::CouncilCompositionStewardCandidatesRequestV1 query_request{};
  std::string query_snapshot_id;
  game::CouncilAssignCouncillorActionRequestV1 action_request{};
  game::CouncilCompositionCandidatesPublicV1 query_result{};
  game::CouncilAssignCouncillorActionAckV1 action_ack{};
  game::CouncilAssignCouncillorActionReceiptV1 action_receipt{};
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  const ck3_11906::MainThreadExecutionStampV1 *active_stamp = nullptr;
  CouncilApplicationMainOperationV1 operation =
      CouncilApplicationMainOperationV1::none;
  CouncilApplicationMainCompletionV1 completion =
      CouncilApplicationMainCompletionV1::not_executed;
  CouncilApplicationMainFailureV1 failure =
      CouncilApplicationMainFailureV1::none;
  std::string failure_reason;
  std::uint64_t executor_invocations = 0;
};

bool ConfigureCouncilApplicationMainV1(
    ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const CouncilApplicationMainConfigurationV1 &configuration,
    CouncilApplicationMainStateV1 &shared_state,
    CouncilApplicationMainContextV1 &context) noexcept;

bool PrepareCouncilApplicationMainQueryV1(
    CouncilApplicationMainContextV1 &context,
    const ck3_11906::CouncilCompositionStewardCandidatesRequestV1
        &request) noexcept;
bool PrepareCouncilApplicationMainSubmitV1(
    CouncilApplicationMainContextV1 &context,
    const game::CouncilAssignCouncillorActionRequestV1 &request) noexcept;
bool PrepareCouncilApplicationMainReceiptV1(
    CouncilApplicationMainContextV1 &context,
    const ck3_11906::CouncilCompositionStewardCandidatesRequestV1
        &fresh_snapshot_request) noexcept;

ck3_11906::MainThreadQuerySubmitResultV1 TryQueueCouncilApplicationMainV1(
    CouncilApplicationMainContextV1 &context) noexcept;
ck3_11906::MainThreadQueryReclaimResultV1 ReclaimCouncilApplicationMainV1(
    CouncilApplicationMainContextV1 &context) noexcept;

bool ExecuteCouncilApplicationMainV1(
    void *context,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// These predicates are suitable for the later bridge registration point.
// They remain false until configuration proves the complete corresponding
// runtime. Merely linking this file never changes the hello capability list.
bool CouncilApplicationMainQueryRuntimeReadyV1(
    const CouncilApplicationMainStateV1 &state) noexcept;
bool CouncilApplicationMainActionRuntimeReadyV1(
    const CouncilApplicationMainStateV1 &state) noexcept;

std::string SerializeCouncilApplicationMainResultEnvelopeV1(
    const CouncilApplicationMainContextV1 &context,
    std::string_view protocol_request_id);

std::string_view CouncilApplicationMainFailureNameV1(
    CouncilApplicationMainFailureV1 failure) noexcept;

} // namespace xar::bridge
