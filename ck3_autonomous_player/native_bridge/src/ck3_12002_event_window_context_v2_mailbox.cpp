#include "xar_bridge/ck3_12002_event_window_context_v2_mailbox.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_event_window_context_v2.hpp"

namespace xar::ck3_12002 {

bool ExecuteEventWindowContextMailboxV2(
    void *opaque,
    const ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *envelope = static_cast<QueryMailboxEnvelope *>(opaque);
  if (envelope == nullptr || envelope->typed_context == nullptr) return false;
  auto &query =
      *static_cast<EventWindowMailboxContextV2 *>(envelope->typed_context);
  query.executor_enter = EnterQueryMailbox(
      query.envelope, stamp, &ExecuteEventWindowContextMailboxV2);
  if (!*query.executor_enter) return false;
  if (query.kind != EventWindowMailboxKindV2::event_window) return false;
  try {
    const bool actual4 = game::IsCk3_12004Descriptor(
        query.envelope.game->descriptor());
    const auto sha = actual4
        ? query.envelope.game->descriptor().executable_sha256
        : game::ReviewedCrozierAbiSha256(query.envelope.game->descriptor());
    const auto bindings = actual4
        ? ck3_12004::BindEventWindowImage12004(query.image_base, sha)
        : BindEventWindowImage(query.image_base, sha);
    EventWindowGuiBindingsV2 gui_bindings{bindings};
    if (actual4 && query.version == EventWindowGuiRequestVersionV2::gui_v2)
      gui_bindings = ck3_12004::BindEventWindowImage12004V2(
          query.image_base, sha);
    (void)ReadVersionedEventWindowInQueryV2(
        query.version, gui_bindings, query.envelope, query.event_instance_id,
        query.presentation, query.gui);
    query.typed_result = true;
    query.executor_typed_result = query.typed_result;
    query.executor_finish = FinishQueryMailbox(query.envelope);
    return *query.executor_finish;
  } catch (...) {
    return false;
  }
}

} // namespace xar::ck3_12002
