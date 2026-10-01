#include "xar_bridge/ck3_12002_family_ranked_mailbox.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002_semantic_adapter.hpp"

#include <algorithm>
#include <string>
#include <windows.h>

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
namespace {
struct RankedMailboxContext {
  QueryMailboxEnvelope envelope{};
  FamilyRankedBindings bindings{};
  FamilyRankedDiagnosticsV1 diagnostics{};
  bridge::MarriageMatchmakingObserverRequestV1 request{};
  bridge::MarriageMatchmakingObservationV1 observation{};
  std::string snapshot_id;
  bool completed = false;
};

bool CaptureRankedFrame(void *opaque,
    bridge::MarriageMatchmakingFrameV1 &output) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  game::Snapshot snapshot{};
  if (!envelope || !envelope->typed_context ||
      !CaptureQuerySnapshot(envelope, snapshot)) return false;
  const auto &query = *static_cast<const RankedMailboxContext *>(envelope->typed_context);
  output = {};
  if (query.snapshot_id.size() >= output.snapshot_id.size()) return false;
  std::copy(query.snapshot_id.begin(), query.snapshot_id.end(), output.snapshot_id.begin());
  output.public_revision = envelope->expected_snapshot_revision;
  output.native_revision = envelope->expected_snapshot_revision;
  output.proof_epoch = envelope->execution_stamp.pump_epoch;
  output.date_raw = snapshot.date_raw;
  output.paused = snapshot.paused;
  output.map_ready = snapshot.map_ready;
  output.has_played_character = snapshot.has_played_character;
  output.played_character_alive = snapshot.played_character_alive;
  output.played_character_id = static_cast<std::uint32_t>(snapshot.played_character_id);
  output.played_character_identity_round_trip = snapshot.has_played_character &&
      snapshot.played_character_alive && snapshot.played_character_id > 0;
  return true;
}
} // namespace

bool ExecuteFamilyRankedMailboxV1(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context ||
      !EnterQueryMailbox(*envelope, stamp, &ExecuteFamilyRankedMailboxV1)) return true;
  auto &query = *static_cast<RankedMailboxContext *>(envelope->typed_context);
  FamilyRankedAccessV1 access{envelope, &CaptureRankedFrame, &IsQueryOwningThread};
  query.completed = ReadMarriageMatchmakingObservationV1(
      query.bindings, access, query.request, query.observation, &query.diagnostics);
  (void)FinishQueryMailbox(*envelope);
  return true;
}

bridge::MarriageCandidateWorkerReadResultV1 ReadFamilyRankedOnApplicationMainV1(
    const game::GameAdapter &adapter, ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    const game::Snapshot &published, std::uint64_t revision, std::uint32_t limit,
    std::uint32_t candidate_filter, bridge::MarriageCandidateInternalQueryV1 &output) noexcept {
  using Status = bridge::MarriageCandidateWorkerReadStatusV1;
  bridge::MarriageCandidateWorkerReadResultV1 result{};
  output = {};
  if (adapter.descriptor().game_version != "1.20.0.2" || revision == 0 ||
      !published.paused || published.played_character_id <= 0 || limit == 0 ||
      limit > bridge::kMarriageMatchmakingMaximumCandidatesV1) {
    result.status = Status::unavailable;
    return result;
  }
  RankedMailboxContext query{};
  query.envelope.game = &NativeAdapter12002(adapter);
  query.envelope.mailbox = &mailbox;
  query.envelope.expected_snapshot = published;
  query.envelope.expected_snapshot_revision = revision;
  query.envelope.typed_context = &query;
  query.bindings = BindFamilyRankedImage(
      reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr)),
      adapter.descriptor().executable_sha256);
  query.snapshot_id = "native:" + std::to_string(revision);
  query.request = {query.snapshot_id, revision, revision, published.date_raw,
      static_cast<std::uint32_t>(published.played_character_id),
      static_cast<std::uint32_t>(published.played_character_id), limit, candidate_filter};
  result.submit = ck3_11906::TrySubmitMainThreadQueryV1(mailbox,
      &ExecuteFamilyRankedMailboxV1, &query.envelope, query.envelope.ticket);
  if (result.submit != ck3_11906::MainThreadQuerySubmitResultV1::submitted) {
    result.status = Status::unavailable;
    return result;
  }
  result.wait = ck3_11906::WaitForMainThreadQueryV1(mailbox,
      query.envelope.ticket, bridge::kMarriageCandidateQueuedWaitBudgetMsV1);
  while (result.wait == ck3_11906::MainThreadQueryWaitResultV1::timeout_executor_already_running) {
    result.wait = ck3_11906::WaitForMainThreadQueryV1(mailbox,
        query.envelope.ticket, bridge::kMarriageCandidateExecutingWaitSliceMsV1);
  }
  result.reclaim = ck3_11906::ReclaimMainThreadQueryV1(mailbox, query.envelope.ticket);
  output.candidates = query.observation;
  result.observer_failure = query.observation.unavailable_reason;
  result.source_adapter_failure_after = query.diagnostics.source_failure;
  result.executor_invocations = query.envelope.entered ? 1 : 0;
  output.executor_invocations = result.executor_invocations;
  const bool stable = result.wait == ck3_11906::MainThreadQueryWaitResultV1::completed &&
      result.reclaim == ck3_11906::MainThreadQueryReclaimResultV1::reclaimed &&
      query.envelope.frame_stable;
  output.completion = stable && query.completed
      ? bridge::MarriageCandidateInternalCompletionV1::candidates_available
      : bridge::MarriageCandidateInternalCompletionV1::query_unavailable;
  result.completion = output.completion;
  result.status = stable && query.completed ? Status::available : Status::unavailable;
  return result;
}
#endif
} // namespace xar::ck3_12002
