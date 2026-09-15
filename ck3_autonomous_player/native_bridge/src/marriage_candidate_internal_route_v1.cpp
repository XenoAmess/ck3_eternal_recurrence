#include "xar_bridge/marriage_candidate_internal_route_v1.hpp"

#include <algorithm>
#include <string_view>

#include <windows.h>

namespace xar::bridge {
namespace {

void SetFailure(MarriageCandidateInternalRouteStateV1 &state,
                MarriageCandidateInternalRouteFailureV1 failure) noexcept {
  state.last_failure.store(static_cast<std::uint32_t>(failure),
                           std::memory_order_release);
}

std::string_view BoundedSnapshotId(
    const std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1> &value)
    noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool DefaultCandidateReader(
    void *, const MarriageMatchmakingObserverEnvironmentV1 &environment,
    const MarriageMatchmakingObserverAccessV1 &access,
    const MarriageMatchmakingObserverRequestV1 &request,
    MarriageMatchmakingObservationV1 &output) noexcept {
  return ReadMarriageMatchmakingObserverV1(environment, access, request,
                                            output);
}

MarriageProposalNativeReadbackResultV1 DefaultBilateralReader(
    void *context, std::uint32_t subject_character_id,
    std::uint32_t candidate_character_id,
    MarriageProposalRelationshipObservationV1 &output) noexcept {
  if (context == nullptr) return MarriageProposalNativeReadbackResultV1::failed;
  return ReadMarriageProposalRelationshipObservationFromNativeBinderV1(
      *static_cast<MarriageProposalNativeBinderStateV1 *>(context),
      subject_character_id, candidate_character_id, output);
}

bool ValidInput(MarriageCandidateInternalOperationV1 operation,
                const MarriageCandidateInternalFrameInputV1 &input) noexcept {
  if (input.snapshot_revision == 0 || input.date_raw <= 0 || !input.paused ||
      !input.map_ready || !input.has_played_character ||
      !input.played_character_alive ||
      !input.played_character_identity_round_trip ||
      input.subject_character_id == 0 ||
      input.matchmaker_character_id != input.subject_character_id ||
      input.limit == 0 ||
      input.limit > kMarriageMatchmakingMaximumCandidatesV1 ||
      input.candidate_character_id == input.subject_character_id) {
    return false;
  }
  return operation !=
             MarriageCandidateInternalOperationV1::actual_bilateral_receipt ||
      input.candidate_character_id != 0;
}

bool IsExecutingExactRoute(
    const MarriageCandidateInternalQueryV1 &query,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.route == nullptr || query.route->mailbox == nullptr ||
      query.ticket.sequence == 0 || query.input.date_raw != stamp.date_raw ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 || !stamp.paused ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.route->mailbox;
  return query.route->configured.load(std::memory_order_acquire) != 0 &&
      mailbox.state.load(std::memory_order_acquire) ==
          xar::ck3_11906::MainThreadQueryMailboxStateV1::executing &&
      !mailbox.stop_requested.load(std::memory_order_acquire) &&
      mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
      mailbox.published_sequence.load(std::memory_order_acquire) ==
          query.ticket.sequence &&
      mailbox.owner_thread_id.load(std::memory_order_acquire) ==
          stamp.thread_id &&
      mailbox.executor == &ExecuteMarriageCandidateInternalRouteV1 &&
      mailbox.executor_context ==
          const_cast<MarriageCandidateInternalQueryV1 *>(&query);
}

struct RouteAccessProxyV1 {
  MarriageCandidateInternalQueryV1 *query = nullptr;
  const xar::ck3_11906::MainThreadExecutionStampV1 *stamp = nullptr;
};

bool ProxyIsMainThread(void *context) noexcept {
  const auto *proxy = static_cast<RouteAccessProxyV1 *>(context);
  return proxy != nullptr && proxy->query != nullptr && proxy->stamp != nullptr &&
      IsExecutingExactRoute(*proxy->query, *proxy->stamp);
}

bool ProxyCaptureFrame(void *context,
                       MarriageMatchmakingFrameV1 &output) noexcept {
  output = {};
  const auto *proxy = static_cast<RouteAccessProxyV1 *>(context);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactRoute(*proxy->query, *proxy->stamp)) {
    return false;
  }
  auto &query = *proxy->query;
  auto &route = *query.route;
  MarriageProposalReceiptFrameV1 receipt{};
  if (route.shared_glue == nullptr ||
      !CaptureMarriageSharedReceiptFrameV1(
          &route.shared_glue->receipt_frames, receipt)) {
    return false;
  }
  output.snapshot_id = receipt.snapshot_id;
  output.public_revision = receipt.public_revision;
  output.native_revision = receipt.native_revision;
  output.proof_epoch = receipt.proof_epoch;
  output.date_raw = receipt.date_raw;
  output.paused = receipt.paused;
  output.map_ready = query.input.map_ready;
  output.has_played_character = query.input.has_played_character;
  output.played_character_alive = query.input.played_character_alive;
  output.played_character_id = query.input.subject_character_id;
  output.played_character_identity_round_trip =
      query.input.played_character_identity_round_trip;
  return true;
}

MarriageNativeSourceResultV1 ProxyReadRankedCandidates(
    void *context,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    std::uint32_t subject_character_id, std::uint32_t limit,
    std::array<MarriageMatchmakingRankedRowV1,
               kMarriageMatchmakingMaximumCandidatesV1> &output,
    std::uint32_t &output_count) noexcept {
  const auto *proxy = static_cast<RouteAccessProxyV1 *>(context);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactRoute(*proxy->query, *proxy->stamp)) {
    return MarriageNativeSourceResultV1::failed;
  }
  return ReadMarriageRankedCandidatesFromSourceAdapterV1(
      &proxy->query->route->source_adapter, native_entry_points,
      subject_character_id, limit, output, output_count);
}

MarriageNativeEvaluationResultV1 ProxyEvaluateCandidate(
    void *context,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    std::uint32_t subject_character_id, std::uint32_t matchmaker_character_id,
    std::uint32_t candidate_character_id,
    MarriageMatchmakingPairEvaluationV1 &output) noexcept {
  const auto *proxy = static_cast<RouteAccessProxyV1 *>(context);
  if (proxy == nullptr || proxy->query == nullptr || proxy->stamp == nullptr ||
      !IsExecutingExactRoute(*proxy->query, *proxy->stamp)) {
    return MarriageNativeEvaluationResultV1::failed;
  }
  return EvaluateMarriageCandidateFromSourceAdapterV1(
      &proxy->query->route->source_adapter, native_entry_points,
      subject_character_id, matchmaker_character_id, candidate_character_id,
      output);
}

} // namespace

bool ConfigureMarriageCandidateInternalRouteV1(
    MarriageCandidateInternalRouteStateV1 &state,
    MarriageSharedGlueStateV1 &shared_glue,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox) noexcept {
  state.configured.store(0, std::memory_order_release);
  state.shared_glue = nullptr;
  state.mailbox = nullptr;
  if (shared_glue.installed.load(std::memory_order_acquire) == 0 ||
      mailbox.module_base == 0 ||
      shared_glue.binder.environment.module_base != mailbox.module_base) {
    SetFailure(state,
               MarriageCandidateInternalRouteFailureV1::invalid_environment);
    return false;
  }
  if (!ConfigureMarriageApplicationMainReceiptV1(
          state.receipt_adapter, shared_glue, mailbox)) {
    SetFailure(state, MarriageCandidateInternalRouteFailureV1::
                          receipt_adapter_configuration_failed);
    return false;
  }
  if (ConfigureMarriageMatchmakingSourceAdapterFromNativeBinderV1(
          shared_glue.binder, state.source_adapter) !=
      MarriageProposalNativeBindResultV1::available) {
    SetFailure(state, MarriageCandidateInternalRouteFailureV1::
                          source_adapter_configuration_failed);
    return false;
  }

  state.shared_glue = &shared_glue;
  state.mailbox = &mailbox;
  state.observer_environment.exact_build_admitted = true;
  state.observer_environment.admitted_executable_sha256 =
      kMarriageMatchmakingObserverExecutableSha256V1;
  state.observer_environment.module_base = mailbox.module_base;
  state.observer_environment.offline_fixture =
      shared_glue.binder.environment.offline_fixture;
  state.observer_environment.native =
      BindMarriageMatchmakingNativeEntryPointsV1(mailbox.module_base);
  state.candidate_reader_context = nullptr;
  state.candidate_reader = &DefaultCandidateReader;
  state.bilateral_reader_context = &shared_glue.binder;
  state.bilateral_reader = &DefaultBilateralReader;
  state.configured.store(1, std::memory_order_release);
  SetFailure(state, MarriageCandidateInternalRouteFailureV1::none);
  return true;
}

bool PrepareMarriageCandidateInternalQueryV1(
    MarriageCandidateInternalRouteStateV1 &state,
    MarriageCandidateInternalOperationV1 operation,
    const MarriageCandidateInternalFrameInputV1 &input,
    MarriageCandidateInternalQueryV1 &query) noexcept {
  query = {};
  if (state.configured.load(std::memory_order_acquire) == 0 ||
      state.shared_glue == nullptr || state.mailbox == nullptr) {
    SetFailure(state,
               MarriageCandidateInternalRouteFailureV1::shared_glue_unavailable);
    return false;
  }
  if (!ValidInput(operation, input)) {
    SetFailure(state, MarriageCandidateInternalRouteFailureV1::invalid_request);
    return false;
  }
  query.route = &state;
  query.operation = operation;
  query.input = input;
  SetFailure(state, MarriageCandidateInternalRouteFailureV1::none);
  return true;
}

bool ExecuteMarriageCandidateInternalRouteV1(
    void *context,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<MarriageCandidateInternalQueryV1 *>(context);
  if (query == nullptr || query->route == nullptr ||
      query->completion != MarriageCandidateInternalCompletionV1::not_executed ||
      query->executor_invocations != 0 ||
      !IsExecutingExactRoute(*query, stamp)) {
    if (query != nullptr) {
      query->completion =
          MarriageCandidateInternalCompletionV1::infrastructure_rejected;
      if (query->route != nullptr) {
        SetFailure(*query->route, MarriageCandidateInternalRouteFailureV1::
                                      mailbox_identity_unproven);
      }
    }
    return false;
  }

  auto &route = *query->route;
  ++query->executor_invocations;
  if (!PublishMarriageApplicationMainReceiptV1(
          route.receipt_adapter, stamp, query->input.snapshot_revision)) {
    query->completion =
        MarriageCandidateInternalCompletionV1::infrastructure_rejected;
    SetFailure(route,
               MarriageCandidateInternalRouteFailureV1::receipt_publish_failed);
    return false;
  }

  if (query->operation == MarriageCandidateInternalOperationV1::candidates) {
    MarriageProposalReceiptFrameV1 receipt{};
    if (route.shared_glue == nullptr || route.candidate_reader == nullptr ||
        !CaptureMarriageSharedReceiptFrameV1(
            &route.shared_glue->receipt_frames, receipt)) {
      query->completion = MarriageCandidateInternalCompletionV1::query_unavailable;
      SetFailure(route, MarriageCandidateInternalRouteFailureV1::
                            candidate_observer_unavailable);
      return true;
    }
    RouteAccessProxyV1 proxy{query, &stamp};
    const MarriageMatchmakingObserverAccessV1 access{
        &proxy, &ProxyCaptureFrame, &ProxyIsMainThread,
        &ProxyReadRankedCandidates, &ProxyEvaluateCandidate};
    const MarriageMatchmakingObserverRequestV1 request{
        BoundedSnapshotId(receipt.snapshot_id), query->input.snapshot_revision,
        query->input.snapshot_revision, query->input.date_raw,
        query->input.subject_character_id,
        query->input.matchmaker_character_id, query->input.limit,
        query->input.candidate_character_id};
    if (!route.candidate_reader(route.candidate_reader_context,
                                route.observer_environment, access, request,
                                query->candidates)) {
      query->completion = MarriageCandidateInternalCompletionV1::query_unavailable;
      SetFailure(route, MarriageCandidateInternalRouteFailureV1::
                            candidate_observer_unavailable);
      return true;
    }
    query->completion =
        MarriageCandidateInternalCompletionV1::candidates_available;
    SetFailure(route, MarriageCandidateInternalRouteFailureV1::none);
    return true;
  }

  MarriageProposalReceiptFrameV1 receipt{};
  if (route.shared_glue == nullptr ||
      !CaptureMarriageSharedReceiptFrameV1(
          &route.shared_glue->receipt_frames, receipt) ||
      route.bilateral_reader == nullptr ||
      route.bilateral_reader(
          route.bilateral_reader_context, query->input.subject_character_id,
          query->input.candidate_character_id, query->bilateral_receipt) !=
          MarriageProposalNativeReadbackResultV1::available ||
      !query->bilateral_receipt.available ||
      !query->bilateral_receipt.paused ||
      BoundedSnapshotId(query->bilateral_receipt.snapshot_id) !=
          BoundedSnapshotId(receipt.snapshot_id) ||
      query->bilateral_receipt.public_revision != receipt.public_revision ||
      query->bilateral_receipt.native_revision != receipt.native_revision ||
      query->bilateral_receipt.proof_epoch != receipt.proof_epoch ||
      query->bilateral_receipt.date_raw != receipt.date_raw ||
      query->bilateral_receipt.subject_character_id !=
          query->input.subject_character_id ||
      query->bilateral_receipt.candidate_character_id !=
          query->input.candidate_character_id) {
    query->completion = MarriageCandidateInternalCompletionV1::query_unavailable;
    SetFailure(route, MarriageCandidateInternalRouteFailureV1::
                          bilateral_receipt_unavailable);
    return true;
  }
  query->completion = MarriageCandidateInternalCompletionV1::
      actual_bilateral_receipt_available;
  SetFailure(route, MarriageCandidateInternalRouteFailureV1::none);
  return true;
}

MarriageCandidateWorkerReadResultV1 ReadMarriageCandidatesOnApplicationMainV1(
    MarriageCandidateInternalRouteStateV1 &route,
    const xar::game::Snapshot &published_snapshot,
    std::uint64_t published_native_revision,
    std::uint32_t limit,
    std::uint32_t candidate_filter,
    MarriageCandidateInternalQueryV1 &query) noexcept {
  MarriageCandidateWorkerReadResultV1 result{};
  query = {};
  if (published_native_revision == 0 || published_snapshot.date_raw <= 0 ||
      !published_snapshot.paused || !published_snapshot.map_ready ||
      !published_snapshot.has_played_character ||
      !published_snapshot.played_character_alive ||
      published_snapshot.played_character_id <= 0 || limit == 0 ||
      limit > kMarriageMatchmakingMaximumCandidatesV1 ||
      candidate_filter ==
          static_cast<std::uint32_t>(published_snapshot.played_character_id)) {
    result.status = MarriageCandidateWorkerReadStatusV1::unavailable;
    result.route_failure = MarriageCandidateInternalRouteFailureV1::invalid_request;
    return result;
  }
  MarriageCandidateInternalFrameInputV1 input{};
  input.snapshot_revision = published_native_revision;
  input.date_raw = published_snapshot.date_raw;
  input.paused = published_snapshot.paused;
  input.map_ready = published_snapshot.map_ready;
  input.has_played_character = published_snapshot.has_played_character;
  input.played_character_alive = published_snapshot.played_character_alive;
  // ReadSnapshot's ReadPlayedCharacter resolves the full generation-bearing
  // CharacterID through the native storage before publishing these fields.
  input.played_character_identity_round_trip = true;
  input.subject_character_id =
      static_cast<std::uint32_t>(published_snapshot.played_character_id);
  input.matchmaker_character_id = input.subject_character_id;
  input.limit = limit;
  input.candidate_character_id = candidate_filter;
  if (!PrepareMarriageCandidateInternalQueryV1(
          route, MarriageCandidateInternalOperationV1::candidates, input,
          query) || route.mailbox == nullptr) {
    result.status = MarriageCandidateWorkerReadStatusV1::unavailable;
    result.route_failure = ReadMarriageCandidateInternalRouteFailureV1(route);
    return result;
  }
  result.pump_epochs_before =
      route.mailbox->pump_epochs.load(std::memory_order_acquire);
  result.paused_owner_pump_epochs_before =
      route.mailbox->paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire);
  result.source_adapter_failure_before =
      ReadMarriageMatchmakingSourceAdapterFailureV1(route.source_adapter);
  result.submit = xar::ck3_11906::TrySubmitMainThreadQueryV1(
      *route.mailbox, &ExecuteMarriageCandidateInternalRouteV1, &query,
      query.ticket);
  if (result.submit !=
      xar::ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
    result.pump_epochs_after =
        route.mailbox->pump_epochs.load(std::memory_order_acquire);
    result.paused_owner_pump_epochs_after =
        route.mailbox->paused_owner_verified_pump_epochs.load(
            std::memory_order_acquire);
    result.status = result.submit ==
                            xar::ck3_11906::MainThreadQuerySubmitResultV1::
                                paused_main_thread_not_observed
                        ? MarriageCandidateWorkerReadStatusV1::unavailable
                        : MarriageCandidateWorkerReadStatusV1::infrastructure_red;
    result.route_failure = ReadMarriageCandidateInternalRouteFailureV1(route);
    return result;
  }
  result.wait = xar::ck3_11906::WaitForMainThreadQueryV1(
      *route.mailbox, query.ticket, kMarriageCandidateQueuedWaitBudgetMsV1);
  while (result.wait == xar::ck3_11906::MainThreadQueryWaitResultV1::
                            timeout_executor_already_running) {
    result.wait = xar::ck3_11906::WaitForMainThreadQueryV1(
        *route.mailbox, query.ticket,
        kMarriageCandidateExecutingWaitSliceMsV1);
  }
  result.pump_epochs_after =
      route.mailbox->pump_epochs.load(std::memory_order_acquire);
  result.paused_owner_pump_epochs_after =
      route.mailbox->paused_owner_verified_pump_epochs.load(
          std::memory_order_acquire);
  result.completion = query.completion;
  result.observer_failure = query.candidates.unavailable_reason;
  result.source_adapter_failure_after =
      ReadMarriageMatchmakingSourceAdapterFailureV1(route.source_adapter);
  result.executor_invocations = query.executor_invocations;
  result.route_failure = ReadMarriageCandidateInternalRouteFailureV1(route);
  result.reclaim =
      xar::ck3_11906::ReclaimMainThreadQueryV1(*route.mailbox, query.ticket);
  if (result.reclaim !=
          xar::ck3_11906::MainThreadQueryReclaimResultV1::reclaimed ||
      result.wait != xar::ck3_11906::MainThreadQueryWaitResultV1::completed ||
      result.executor_invocations != 1) {
    result.status = MarriageCandidateWorkerReadStatusV1::infrastructure_red;
    return result;
  }
  if (result.completion ==
          MarriageCandidateInternalCompletionV1::candidates_available &&
      query.candidates.status == MarriageMatchmakingObserverStatusV1::available) {
    result.status = MarriageCandidateWorkerReadStatusV1::available;
  } else if (result.completion ==
                 MarriageCandidateInternalCompletionV1::query_unavailable ||
             query.candidates.status ==
                 MarriageMatchmakingObserverStatusV1::unavailable) {
    result.status = MarriageCandidateWorkerReadStatusV1::unavailable;
  } else {
    result.status = MarriageCandidateWorkerReadStatusV1::infrastructure_red;
  }
  return result;
}

MarriageCandidateInternalRouteFailureV1
ReadMarriageCandidateInternalRouteFailureV1(
    const MarriageCandidateInternalRouteStateV1 &state) noexcept {
  return static_cast<MarriageCandidateInternalRouteFailureV1>(
      state.last_failure.load(std::memory_order_acquire));
}

} // namespace xar::bridge
