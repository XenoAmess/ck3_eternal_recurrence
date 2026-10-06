#include "xar_bridge/ck3_12002_sway_mailbox.hpp"

#include <cstring>
#include <windows.h>

namespace xar::ck3_12002 {
namespace {
using namespace bridge;
bool Frame(ActiveSwayMailboxContext12002 &q) noexcept {
  game::Snapshot frame{};
  return CaptureQuerySnapshot(&q.envelope, frame) && frame.map_ready &&
      frame.has_played_character && frame.played_character_alive &&
      frame.played_character_id > 0 && frame.played_character_id != static_cast<std::int64_t>(q.target);
}
bool Capture(void *opaque, ActiveSchemeStateV1PrivateObservation &out) noexcept {
  auto &q = *static_cast<ActiveSwayMailboxContext12002 *>(opaque);
  if (!Frame(q) || !ReadActiveSwayState12002(q.source,
      q.envelope.execution_stamp.pump_epoch, out) || !Frame(q)) return false;
  return out.played_character_id == q.envelope.expected_snapshot.played_character_id &&
      out.date_raw == q.envelope.expected_snapshot.date_raw;
}
bool Preconditions(void *opaque, ActiveSchemeSemanticActionV1PrivatePrecondition &out) noexcept {
  auto &q = *static_cast<ActiveSwayMailboxContext12002 *>(opaque);
  if (!Frame(q) || !ReadSwayCommandTermsV1(q.commands,
      q.envelope.expected_snapshot.played_character_id, q.target,
      q.envelope.execution_stamp.pump_epoch, q.terms) || !Frame(q)) return false;
  out = q.terms.precondition; return true;
}
bool Submit(void *opaque, const ActiveSchemeSemanticActionV1PrivateCommand &command) noexcept {
  auto &q = *static_cast<ActiveSwayMailboxContext12002 *>(opaque);
  std::int32_t opinion{};
  return Frame(q) && ReadSwayTargetOpinion12002(q.source, command.actor_character_id,
      q.target, opinion) && opinion == q.expected_opinion &&
      SubmitSwayCommandV1(q.commands, command) == SwayCommandSubmitResultV1::submitted;
}
bool Matching(const ActiveSchemeStateV1PrivateObservation &active, std::uint32_t target) noexcept {
  for (std::size_t i = 0; i < active.row_count; ++i) {
    const auto &row = active.rows[i];
    if (std::strcmp(row.scheme_type_key.data(), "sway") == 0 &&
        row.owner_character_id == active.played_character_id &&
        row.target_kind == ActiveSchemeStateV1PrivateTargetKind::character && row.target_id == target) return true;
  }
  return false;
}
} // namespace

bool ExecuteActiveSwayMailbox12002(void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (!envelope || !envelope->typed_context) return false;
  auto &q = *static_cast<ActiveSwayMailboxContext12002 *>(envelope->typed_context);
  if (!EnterQueryMailbox(*envelope, stamp, &ExecuteActiveSwayMailbox12002)) {
    q.failure = "published_frame_changed"; q.completed = true; return true;
  }
  try {
    const ActiveSchemeSemanticActionV1PrivateAccess access{&q, &Capture, &Preconditions, &Submit};
    if (q.receipt_mode) {
      if (VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(access, q.prior_ack,
          q.receipt) != ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied) {
        q.failure = "native_sway_receipt_red:";
        q.failure += ActiveSchemeSemanticActionV1PrivateFailureName(q.receipt.failure);
      }
    } else if (!Capture(&q, q.active)) {
      q.failure = "native_sway_observation_red";
    } else {
      q.matching = Matching(q.active, q.target);
      if (!ReadSwayTargetOpinion12002(q.source, q.active.played_character_id, q.target, q.opinion)) {
        q.failure = "native_sway_target_opinion_red";
      } else if (!q.formal) {
        ActiveSchemeSemanticActionV1PrivatePrecondition pre{};
        if (!Preconditions(&q, pre)) q.failure = "native_sway_precondition_red";
      } else if (q.active.capture_epoch <= q.expected_capture_epoch ||
          q.active.container_generation != q.expected_container_generation) {
        q.failure = "sway_source_snapshot_changed";
      } else if (q.opinion != q.expected_opinion) {
        q.failure = "sway_target_opinion_changed_or_red";
      } else {
        ActiveSchemeSemanticActionV1PrivateRequest request{};
        request.request_id = q.action_id; request.interaction_key = "sway_interaction";
        request.actor_character_id = q.active.played_character_id;
        request.target_kind = ActiveSchemeStateV1PrivateTargetKind::character; request.target_id = q.target;
        request.expected_capture_epoch = q.active.capture_epoch;
        request.expected_container_generation = q.active.container_generation;
        request.expected_date_raw = q.active.date_raw;
        const ActiveSchemeSemanticActionV1PrivateEnvironment environment{
            q.source.module_base, q.source.enabled && q.commands.enabled,
            q.source.executable_sha256, q.commands.enabled, false};
        if (ExecuteActiveSchemeSemanticActionV1Private(environment, access, request, q.ack) !=
            ActiveSchemeSemanticActionV1PrivateAckStatus::submitted_verification_pending) {
          q.failure = "native_sway_submit_rejected:";
          q.failure += ActiveSchemeSemanticActionV1PrivateFailureName(q.ack.failure);
        }
      }
    }
    q.completed = true;
    (void)FinishQueryMailbox(*envelope);
    return true;
  } catch (...) { q.failure = "native_sway_executor_exception"; q.completed = true; return false; }
}

} // namespace xar::ck3_12002
