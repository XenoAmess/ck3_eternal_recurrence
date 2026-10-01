#include "xar_bridge/ck3_12002_sway_completion_mailbox.hpp"

namespace xar::ck3_12002 {

bool ExecuteSwayCompletionMailboxV1(
    void *opaque, const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) {
    return false;
  }
  auto &query = *static_cast<SwayCompletionMailboxContextV1 *>(envelope->typed_context);
  if (!EnterQueryMailbox(*envelope, stamp, &ExecuteSwayCompletionMailboxV1)) {
    query.failure = "sway_completion_published_frame_changed";
    query.completed = true;
    return true;
  }
  (void)ReadSwayCompletion12002(query.bindings, query.request, query.result);
  query.completed = true;
  (void)FinishQueryMailbox(*envelope);
  return true;
}

} // namespace xar::ck3_12002
