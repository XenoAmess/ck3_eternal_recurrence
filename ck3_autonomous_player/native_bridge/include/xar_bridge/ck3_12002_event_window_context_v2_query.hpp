#pragma once

#include "xar_bridge/ck3_12002_event_window_context_v2.hpp"
#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/event_window_gui_request_v2.hpp"

namespace xar::ck3_12002 {

// Called inside the existing typed event-window executor. The v2 collector
// receives the actual mailbox ownership predicate before any dynamic GUI gate.
// v1 retains its original collector and never invokes the new GUI predicate.
inline game::ReadEventWindowContextResultV1 ReadVersionedEventWindowInQueryV2(
    EventWindowGuiRequestVersionV2 version,
    const EventWindowGuiBindingsV2 &bindings,
    QueryMailboxEnvelope &envelope, std::int32_t event_instance_id,
    game::EventWindowContextV1 &presentation,
    game::EventWindowContextV2 &gui) {
  if (version == EventWindowGuiRequestVersionV2::presentation_v1) {
    return ReadEventWindowContextV1(bindings.presentation,
        envelope.expected_snapshot_revision, event_instance_id, presentation);
  }
  EventWindowGuiAccessV2 access{&envelope, &IsQueryOwningThread};
  const auto result = ReadEventWindowContextV2(bindings, access,
      envelope.expected_snapshot_revision, event_instance_id, gui);
  presentation = gui.presentation;
  return result;
}

} // namespace xar::ck3_12002
