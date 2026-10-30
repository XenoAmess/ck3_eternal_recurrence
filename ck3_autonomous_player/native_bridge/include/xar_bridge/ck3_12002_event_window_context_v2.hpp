#pragma once

#include "xar_bridge/ck3_12002_event_window_context.hpp"
#include "xar_bridge/event_window_context_v2.hpp"

namespace xar::ck3_12002 {

using EventGuiOwnerGateV2 = bool (*)(const void *owner, const void *reason);

struct EventWindowGuiBindingsV2 {
  EventWindowBindings presentation;
  // Only an independently verified exact-build factory may provide this.
  EventGuiOwnerGateV2 read_owner_gate = nullptr;
};

struct EventWindowGuiAccessV2 {
  void *context = nullptr;
  // The actual bridge may supply QueryMailboxEnvelope/IsQueryOwningThread.
  // A missing/false callback grants no native gate invocation.
  bool (*is_owning_thread)(void *context) noexcept = nullptr;
};

game::ReadEventWindowContextResultV1 ReadEventWindowContextV2(
    const EventWindowGuiBindingsV2 &bindings,
    const EventWindowGuiAccessV2 &access,
    std::uint64_t expected_snapshot_revision,
    std::int32_t expected_event_instance_id,
    game::EventWindowContextV2 &output) noexcept;

std::string SerializeEventWindowContextV2(
    const game::EventWindowContextV2 &context,
    bool allow_null_saved_character_scope = false);

} // namespace xar::ck3_12002
