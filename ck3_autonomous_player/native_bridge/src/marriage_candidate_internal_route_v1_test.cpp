#include "xar_bridge/marriage_candidate_internal_route_v1.hpp"

#include <cassert>
#include <cstring>
#include <iostream>

namespace bridge = xar::bridge;
namespace native = xar::ck3_11906;

namespace {

constexpr std::uint32_t kSubject = 0x01000001;
constexpr std::uint32_t kCandidate = 0x02000002;

bool DirectMemory(void *, std::uintptr_t address, void *output,
                  std::size_t size) noexcept {
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool FakeRankedInvoke(void *, const bridge::MarriageNativeRankedInvocationV1 &,
                      std::uintptr_t &) noexcept {
  return false;
}
bool FakeRankedView(void *, std::uintptr_t,
                    bridge::MarriageNativeRankedContainerViewV1 &) noexcept {
  return false;
}
void FakeRankedRelease(void *, std::uintptr_t) noexcept {}
bool FakeOutcome(void *, std::uintptr_t, std::uintptr_t, const void *,
                 bridge::MarriagePredictedOutcomeV1 &) noexcept {
  return false;
}

void PrepareGlue(bridge::MarriageSharedGlueStateV1 &glue) {
  auto binder = bridge::BindMarriageProposalNativeBinderEnvironmentV1(
      1, true, bridge::kMarriageProposalNativeBinderExecutableSha256V1);
  binder.offline_fixture = true;
  binder.source_adapter.offline_fixture = true;
  binder.source_adapter.read_memory = &DirectMemory;
  binder.source_adapter.invoke_ranked_source = &FakeRankedInvoke;
  binder.source_adapter.read_ranked_container_view = &FakeRankedView;
  binder.source_adapter.release_ranked_container = &FakeRankedRelease;
  binder.source_adapter.classify_outcome = &FakeOutcome;
  binder.ranked_container_lifecycle_certified = true;
  binder.outcome_classifier_certified = true;
  glue.binder.environment = binder;
  glue.installed.store(1);
  glue.receipt_frames.enabled.store(1);
}

native::MainThreadExecutionStampV1 PrepareExecutingMailbox(
    native::MainThreadQueryMailboxV1 &mailbox,
    bridge::MarriageCandidateInternalQueryV1 &query) {
  const auto thread = GetCurrentThreadId();
  native::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 11;
  stamp.thread_id = thread;
  stamp.tls_initialized = 1;
  stamp.tls_main_thread_marker = 1;
  stamp.tls_context = 0x1111;
  stamp.jomini_state = 0x2222;
  stamp.game_state = 0x3333;
  stamp.date_raw = query.input.date_raw;
  stamp.paused = true;
  query.ticket.sequence = 7;
  mailbox.module_base = 1;
  mailbox.state.store(native::MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(query.ticket.sequence);
  mailbox.owner_thread_id.store(thread);
  mailbox.observed_current_thread_id.store(thread);
  mailbox.observed_tls_initialized.store(1);
  mailbox.observed_tls_main_thread_marker.store(1);
  mailbox.observed_tls_context.store(stamp.tls_context);
  mailbox.observed_jomini_state.store(stamp.jomini_state);
  mailbox.observed_game_state.store(stamp.game_state);
  mailbox.observed_date_raw.store(stamp.date_raw);
  mailbox.observed_paused.store(true);
  mailbox.observed_stamp_read_success.store(true);
  mailbox.pump_epochs.store(stamp.pump_epoch);
  mailbox.executor_started_pump_epoch.store(stamp.pump_epoch);
  mailbox.paused_owner_verified_pump_epochs.store(
      native::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor = &bridge::ExecuteMarriageCandidateInternalRouteV1;
  mailbox.executor_context = &query;
  return stamp;
}

bridge::MarriageCandidateInternalFrameInputV1 Input(
    std::uint32_t candidate = 0) {
  bridge::MarriageCandidateInternalFrameInputV1 input{};
  input.snapshot_revision = 81;
  input.date_raw = 12345;
  input.paused = true;
  input.map_ready = true;
  input.has_played_character = true;
  input.played_character_alive = true;
  input.played_character_identity_round_trip = true;
  input.subject_character_id = kSubject;
  input.matchmaker_character_id = kSubject;
  input.candidate_character_id = candidate;
  return input;
}

bool ReadCandidate(
    void *, const bridge::MarriageMatchmakingObserverEnvironmentV1 &,
    const bridge::MarriageMatchmakingObserverAccessV1 &access,
    const bridge::MarriageMatchmakingObserverRequestV1 &request,
    bridge::MarriageMatchmakingObservationV1 &output) noexcept {
  bridge::MarriageMatchmakingFrameV1 frame{};
  if (!access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, frame) ||
      request.expected_snapshot_id != "native:81" ||
      request.subject_character_id != kSubject) {
    return false;
  }
  output = {};
  output.status = bridge::MarriageMatchmakingObserverStatusV1::available;
  output.snapshot_id = frame.snapshot_id;
  output.public_revision = frame.public_revision;
  output.native_revision = frame.native_revision;
  output.proof_epoch = frame.proof_epoch;
  output.date_raw = frame.date_raw;
  output.subject_character_id = kSubject;
  output.matchmaker_character_id = kSubject;
  output.candidate_count = 1;
  output.candidates[0].rank = 1;
  output.candidates[0].candidate_character_id = kCandidate;
  output.readiness.same_frame_ready = true;
  return true;
}

bridge::MarriageProposalNativeReadbackResultV1 ReadBilateral(
    void *, std::uint32_t subject, std::uint32_t candidate,
    bridge::MarriageProposalRelationshipObservationV1 &output) noexcept {
  if (subject != kSubject || candidate != kCandidate) {
    return bridge::MarriageProposalNativeReadbackResultV1::failed;
  }
  output = {};
  output.available = true;
  output.paused = true;
  std::memcpy(output.snapshot_id.data(), "native:81", 9);
  output.public_revision = 81;
  output.native_revision = 81;
  output.proof_epoch = 11;
  output.date_raw = 12345;
  output.subject_character_id = subject;
  output.candidate_character_id = candidate;
  output.subject_identity_round_trip = true;
  output.candidate_identity_round_trip = true;
  output.subject_alive = true;
  output.candidate_alive = true;
  output.relationship_state_ready = true;
  output.subject_has_candidate_as_spouse = true;
  output.candidate_has_subject_as_spouse = true;
  output.alliance_state_ready = true;
  output.subject_has_alliance_with_candidate = true;
  output.candidate_has_alliance_with_subject = true;
  output.native_resolution =
      bridge::MarriageProposalNativeResolutionV1::accepted;
  return bridge::MarriageProposalNativeReadbackResultV1::available;
}

bool ReadCandidateUnavailable(
    void *, const bridge::MarriageMatchmakingObserverEnvironmentV1 &,
    const bridge::MarriageMatchmakingObserverAccessV1 &,
    const bridge::MarriageMatchmakingObserverRequestV1 &,
    bridge::MarriageMatchmakingObservationV1 &) noexcept {
  return false;
}

void TestCandidateAndActualReceiptRoutes() {
  bridge::MarriageSharedGlueStateV1 glue{};
  PrepareGlue(glue);
  native::MainThreadQueryMailboxV1 mailbox{};
  mailbox.module_base = 1;
  bridge::MarriageCandidateInternalRouteStateV1 route{};
  assert(bridge::ConfigureMarriageCandidateInternalRouteV1(
      route, glue, mailbox));
  route.candidate_reader = &ReadCandidate;
  route.bilateral_reader = &ReadBilateral;
  route.bilateral_reader_context = nullptr;

  // An ACK has no field or callback on this route. Without an application-main
  // execution, the shared source remains empty.
  bridge::InvalidateMarriageSharedReceiptFrameV1(glue);
  bridge::MarriageProposalReceiptFrameV1 frame{};
  assert(!bridge::CaptureMarriageSharedReceiptFrameV1(
      &glue.receipt_frames, frame));

  bridge::MarriageCandidateInternalQueryV1 candidates{};
  assert(bridge::PrepareMarriageCandidateInternalQueryV1(
      route, bridge::MarriageCandidateInternalOperationV1::candidates,
      Input(), candidates));
  const auto candidate_stamp = PrepareExecutingMailbox(mailbox, candidates);
  assert(bridge::ExecuteMarriageCandidateInternalRouteV1(
      &candidates, candidate_stamp));
  assert(candidates.completion ==
         bridge::MarriageCandidateInternalCompletionV1::candidates_available);
  assert(candidates.candidates.candidate_count == 1 &&
         candidates.candidates.candidates[0].candidate_character_id ==
             kCandidate);
  assert(bridge::CaptureMarriageSharedReceiptFrameV1(
      &glue.receipt_frames, frame));
  assert(std::strcmp(frame.snapshot_id.data(), "native:81") == 0);

  mailbox.state.store(native::MainThreadQueryMailboxStateV1::idle);
  bridge::MarriageCandidateInternalQueryV1 actual{};
  assert(bridge::PrepareMarriageCandidateInternalQueryV1(
      route,
      bridge::MarriageCandidateInternalOperationV1::actual_bilateral_receipt,
      Input(kCandidate), actual));
  const auto actual_stamp = PrepareExecutingMailbox(mailbox, actual);
  assert(bridge::ExecuteMarriageCandidateInternalRouteV1(&actual,
                                                         actual_stamp));
  assert(actual.completion == bridge::MarriageCandidateInternalCompletionV1::
                                  actual_bilateral_receipt_available);
  assert(actual.bilateral_receipt.relationship_state_ready &&
         actual.bilateral_receipt.subject_has_candidate_as_spouse &&
         actual.bilateral_receipt.candidate_has_subject_as_spouse &&
         actual.bilateral_receipt.alliance_state_ready &&
         actual.bilateral_receipt.native_resolution ==
             bridge::MarriageProposalNativeResolutionV1::accepted);
}

void TestUnavailableIsBusinessResultAndIdentityDriftIsInfrastructure() {
  bridge::MarriageSharedGlueStateV1 glue{};
  PrepareGlue(glue);
  native::MainThreadQueryMailboxV1 mailbox{};
  mailbox.module_base = 1;
  bridge::MarriageCandidateInternalRouteStateV1 route{};
  assert(bridge::ConfigureMarriageCandidateInternalRouteV1(
      route, glue, mailbox));
  route.candidate_reader = &ReadCandidateUnavailable;

  bridge::MarriageCandidateInternalQueryV1 query{};
  assert(bridge::PrepareMarriageCandidateInternalQueryV1(
      route, bridge::MarriageCandidateInternalOperationV1::candidates,
      Input(), query));
  const auto stamp = PrepareExecutingMailbox(mailbox, query);
  assert(bridge::ExecuteMarriageCandidateInternalRouteV1(&query, stamp));
  assert(query.completion ==
         bridge::MarriageCandidateInternalCompletionV1::query_unavailable);
  assert(bridge::ReadMarriageCandidateInternalRouteFailureV1(route) ==
         bridge::MarriageCandidateInternalRouteFailureV1::
             candidate_observer_unavailable);

  mailbox.state.store(native::MainThreadQueryMailboxStateV1::idle);
  bridge::MarriageCandidateInternalQueryV1 drift{};
  assert(bridge::PrepareMarriageCandidateInternalQueryV1(
      route, bridge::MarriageCandidateInternalOperationV1::candidates,
      Input(), drift));
  auto drift_stamp = PrepareExecutingMailbox(mailbox, drift);
  mailbox.executor_context = nullptr;
  assert(!bridge::ExecuteMarriageCandidateInternalRouteV1(&drift,
                                                          drift_stamp));
  assert(drift.completion == bridge::MarriageCandidateInternalCompletionV1::
                                 infrastructure_rejected);
}

void TestWorkerTransportDoesNotPromoteUnreadyOrUninstalledFrames() {
  bridge::MarriageSharedGlueStateV1 glue{};
  PrepareGlue(glue);
  native::MainThreadQueryMailboxV1 mailbox{};
  mailbox.module_base = 1;
  mailbox.executor_submission_enabled = true;
  mailbox.permitted_executor_octotrigintary =
      &bridge::ExecuteMarriageCandidateInternalRouteV1;
  bridge::MarriageCandidateInternalRouteStateV1 route{};
  assert(bridge::ConfigureMarriageCandidateInternalRouteV1(
      route, glue, mailbox));
  xar::game::Snapshot snapshot{};
  snapshot.date_raw = 12345;
  snapshot.paused = true;
  snapshot.map_ready = true;
  snapshot.has_played_character = true;
  snapshot.played_character_alive = true;
  snapshot.played_character_id = static_cast<std::int32_t>(kSubject);
  bridge::MarriageCandidateInternalQueryV1 query{};
  snapshot.paused = false;
  const auto unready = bridge::ReadMarriageCandidatesOnApplicationMainV1(
      route, snapshot, 81, 8, 0, query);
  assert(unready.status ==
         bridge::MarriageCandidateWorkerReadStatusV1::unavailable);
  assert(query.ticket.sequence == 0);
  snapshot.paused = true;
  const auto uninstalled = bridge::ReadMarriageCandidatesOnApplicationMainV1(
      route, snapshot, 81, 8, 0, query);
  assert(uninstalled.status ==
         bridge::MarriageCandidateWorkerReadStatusV1::infrastructure_red);
  assert(uninstalled.submit ==
         native::MainThreadQuerySubmitResultV1::mailbox_not_installed);
  assert(query.ticket.sequence == 0);
}

} // namespace

int main() {
  TestCandidateAndActualReceiptRoutes();
  TestUnavailableIsBusinessResultAndIdentityDriftIsInfrastructure();
  TestWorkerTransportDoesNotPromoteUnreadyOrUninstalledFrames();
  std::cout << "marriage_candidate_internal_route_v1 tests passed\n";
  return 0;
}
