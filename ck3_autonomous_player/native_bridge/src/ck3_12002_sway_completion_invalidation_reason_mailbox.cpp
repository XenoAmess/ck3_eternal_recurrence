#include "xar_bridge/ck3_12002_sway_completion_invalidation_reason_mailbox.hpp"

namespace xar::ck3_12002 {

bool ExecuteSwayCompletionInvalidationReasonMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) {
    return false;
  }
  auto &query = *static_cast<SwayCompletionInvalidationReasonMailboxContextV1 *>(envelope->typed_context);
  if (!EnterQueryMailbox(*envelope, stamp, &ExecuteSwayCompletionInvalidationReasonMailboxV1)) {
    query.failure = "sway_invalidation_reason_published_frame_changed";
    query.completed = true;
    return true;
  }
  if (query.recorder == nullptr) {
    query.failure = "sway_invalidation_reason_recorder_unavailable";
  } else {
    (void)query.recorder->Query(query.request, query.result);
  }
  query.completed = true;
  (void)FinishQueryMailbox(*envelope);
  return true;
}

} // namespace xar::ck3_12002
