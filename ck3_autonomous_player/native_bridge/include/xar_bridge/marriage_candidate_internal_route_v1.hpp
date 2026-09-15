#pragma once

#include "xar_bridge/marriage_application_main_receipt_v1.hpp"
#include "xar_bridge/marriage_matchmaking_observer_v1.hpp"
#include "xar_bridge/game_contract.hpp"

#include <atomic>
#include <cstdint>

namespace xar::bridge {

enum class MarriageCandidateInternalOperationV1 : std::uint32_t {
  candidates = 0,
  actual_bilateral_receipt = 1,
};

enum class MarriageCandidateInternalCompletionV1 : std::uint32_t {
  not_executed = 0,
  candidates_available,
  actual_bilateral_receipt_available,
  query_unavailable,
  infrastructure_rejected,
};

enum class MarriageCandidateInternalRouteFailureV1 : std::uint32_t {
  none = 0,
  invalid_environment,
  shared_glue_unavailable,
  receipt_adapter_configuration_failed,
  source_adapter_configuration_failed,
  invalid_request,
  mailbox_identity_unproven,
  receipt_publish_failed,
  candidate_observer_unavailable,
  bilateral_receipt_unavailable,
};

// The worker prepares this identity from its already-published exact-build
// snapshot. It contains no protocol command or action ACK. The application-main
// executor must independently publish the same revision before any native read.
struct MarriageCandidateInternalFrameInputV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  bool played_character_identity_round_trip = false;
  std::uint32_t subject_character_id = 0;
  std::uint32_t matchmaker_character_id = 0;
  std::uint32_t candidate_character_id = 0;
  std::uint32_t limit = kMarriageMatchmakingMaximumCandidatesV1;
};

using ReadMarriageCandidateInternalObservationV1 = bool (*)(
    void *context,
    const MarriageMatchmakingObserverEnvironmentV1 &environment,
    const MarriageMatchmakingObserverAccessV1 &access,
    const MarriageMatchmakingObserverRequestV1 &request,
    MarriageMatchmakingObservationV1 &output) noexcept;
using ReadMarriageCandidateInternalBilateralReceiptV1 =
    MarriageProposalNativeReadbackResultV1 (*)(
        void *context, std::uint32_t subject_character_id,
        std::uint32_t candidate_character_id,
        MarriageProposalRelationshipObservationV1 &output) noexcept;

struct MarriageCandidateInternalRouteStateV1 {
  MarriageSharedGlueStateV1 *shared_glue = nullptr;
  xar::ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  MarriageApplicationMainReceiptStateV1 receipt_adapter{};
  MarriageMatchmakingSourceAdapterStateV1 source_adapter{};
  MarriageMatchmakingObserverEnvironmentV1 observer_environment{};
  void *candidate_reader_context = nullptr;
  ReadMarriageCandidateInternalObservationV1 candidate_reader = nullptr;
  void *bilateral_reader_context = nullptr;
  ReadMarriageCandidateInternalBilateralReceiptV1 bilateral_reader = nullptr;
  std::atomic<std::uint32_t> configured{0};
  std::atomic<std::uint32_t> last_failure{static_cast<std::uint32_t>(
      MarriageCandidateInternalRouteFailureV1::none)};
};

struct MarriageCandidateInternalQueryV1 {
  MarriageCandidateInternalRouteStateV1 *route = nullptr;
  xar::ck3_11906::MainThreadQueryTicketV1 ticket{};
  MarriageCandidateInternalOperationV1 operation =
      MarriageCandidateInternalOperationV1::candidates;
  MarriageCandidateInternalFrameInputV1 input{};
  MarriageMatchmakingObservationV1 candidates{};
  MarriageProposalRelationshipObservationV1 bilateral_receipt{};
  MarriageCandidateInternalCompletionV1 completion =
      MarriageCandidateInternalCompletionV1::not_executed;
  std::uint32_t executor_invocations = 0;
};

bool ConfigureMarriageCandidateInternalRouteV1(
    MarriageCandidateInternalRouteStateV1 &state,
    MarriageSharedGlueStateV1 &shared_glue,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept;

bool PrepareMarriageCandidateInternalQueryV1(
    MarriageCandidateInternalRouteStateV1 &state,
    MarriageCandidateInternalOperationV1 operation,
    const MarriageCandidateInternalFrameInputV1 &input,
    MarriageCandidateInternalQueryV1 &query) noexcept;

bool ExecuteMarriageCandidateInternalRouteV1(
    void *context,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

// The controlled worker-facing read-only transport uses the already-published
// gameplay snapshot. Public capability registration remains a separate live
// gate; the protocol cannot supply or override this input.
inline constexpr std::uint32_t kMarriageCandidateQueuedWaitBudgetMsV1 = 5000;
inline constexpr std::uint32_t kMarriageCandidateExecutingWaitSliceMsV1 = 1000;

enum class MarriageCandidateWorkerReadStatusV1 : std::uint32_t {
  available = 0,
  unavailable = 1,
  infrastructure_red = 2,
};

struct MarriageCandidateWorkerReadResultV1 {
  MarriageCandidateWorkerReadStatusV1 status =
      MarriageCandidateWorkerReadStatusV1::infrastructure_red;
  xar::ck3_11906::MainThreadQuerySubmitResultV1 submit =
      xar::ck3_11906::MainThreadQuerySubmitResultV1::invalid_request;
  xar::ck3_11906::MainThreadQueryWaitResultV1 wait =
      xar::ck3_11906::MainThreadQueryWaitResultV1::ticket_mismatch;
  xar::ck3_11906::MainThreadQueryReclaimResultV1 reclaim =
      xar::ck3_11906::MainThreadQueryReclaimResultV1::ticket_mismatch;
  MarriageCandidateInternalCompletionV1 completion =
      MarriageCandidateInternalCompletionV1::not_executed;
  MarriageCandidateInternalRouteFailureV1 route_failure =
      MarriageCandidateInternalRouteFailureV1::none;
  std::uint32_t executor_invocations = 0;
};

MarriageCandidateWorkerReadResultV1 ReadMarriageCandidatesOnApplicationMainV1(
    MarriageCandidateInternalRouteStateV1 &route,
    const xar::game::Snapshot &published_snapshot,
    std::uint64_t published_native_revision,
    std::uint32_t limit,
    std::uint32_t candidate_filter,
    MarriageCandidateInternalQueryV1 &query) noexcept;

MarriageCandidateInternalRouteFailureV1
ReadMarriageCandidateInternalRouteFailureV1(
    const MarriageCandidateInternalRouteStateV1 &state) noexcept;

} // namespace xar::bridge
