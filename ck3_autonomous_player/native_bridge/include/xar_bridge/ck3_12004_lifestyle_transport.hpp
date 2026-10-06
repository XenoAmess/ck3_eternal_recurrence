#pragma once
#include "xar_bridge/ck3_12004_lifestyle.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include <optional>
namespace xar::ck3_12004::lifestyle {
struct PlayerLifestyleTransport12004 {
  std::optional<game::PlayerLifestyleSelectionActionAckV1> pending_ack{};
  bool action_may_have_submitted = false;
  std::uint64_t last_query_revision = 0;
  std::string last_query_episode{};
  std::int32_t last_query_player = -1;
  bool last_query_stock_focus = false;
  std::string last_query_focus_target{};
};
bool AcceptsPlayerLifestyleStep12004(std::string_view step) noexcept;
std::string RenderPlayerLifestyle12004(
    std::string_view request_id, std::string_view step,
    const ck3_11906::PlayerLifestyleFormalWireContextV1 &context,
    const game::AdapterDescriptor &descriptor);
std::string HandlePlayerLifestyle12004(
    PlayerLifestyleTransport12004 &transport, std::string_view request_id,
    std::string_view step, std::string_view payload,
    const game::GameAdapter &adapter, const PlayerLifestyleBindings12004 &bindings,
    const game::Snapshot &published, std::uint64_t published_revision,
    MainThreadQueryMailboxV1 &mailbox);
bool PlayerLifestyleNeedsPostSubmitSnapshot12004(
    const PlayerLifestyleTransport12004 &transport, std::string_view request_id) noexcept;
}
