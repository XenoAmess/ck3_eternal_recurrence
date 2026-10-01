#include "xar_bridge/ck3_12002_sway_completion_execution_mailbox.hpp"

namespace xar::ck3_12002 {

bool ExecuteSwayCompletionExecutionMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) {
    return false;
  }
  auto &query = *static_cast<SwayCompletionExecutionMailboxContextV1 *>(envelope->typed_context);
  if (!EnterQueryMailbox(*envelope, stamp, &ExecuteSwayCompletionExecutionMailboxV1)) {
    query.failure = "sway_execution_published_frame_changed";
    query.completed = true;
    return true;
  }
  if (query.recorder == nullptr) {
    query.failure = "sway_execution_recorder_unavailable";
  } else {
    (void)query.recorder->Query(query.request, query.result);
  }
  query.completed = true;
  (void)FinishQueryMailbox(*envelope);
  return true;
}

} // namespace xar::ck3_12002
