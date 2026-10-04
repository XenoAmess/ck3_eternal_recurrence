#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include <string>

namespace xar::ck3_11906 {
inline constexpr std::string_view kIngameDecisionsOpenV1Step = "activate-ingame-decisions-v1";
inline constexpr std::string_view kIngameDecisionsOpenV1Capability = "game.command.activate-ingame-decisions-v1";
struct IngameDecisionsOpenResultV1 {
  std::uint64_t native_revision = 0, connection_generation = 0;
  std::uint32_t game_pid = 0;
  std::int32_t played_character_id = -1, date_raw = 0;
  bool owner_thread_verified = false, frame_verified = false;
  bool source_abi_pins_verified = false, gui_owner_binding_verified = false;
  bool topbar_tree_complete = false, receiver_qualified = false;
  bool before_visible = false, dispatch_invoked = false, native_handled = false;
  bool native_after_read = false, native_after_visible = false;
  bool native_after_tree_complete = false, postcondition_verified = false;
  std::size_t topbar_widget_count = 0, after_widget_count = 0;
  std::string target_child_path, status = "unavailable", unavailable_reason;
};
struct IngameDecisionsOpenContextV1 {
  const game::GameAdapter *game = nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision = 0, connection_generation = 0;
  IngameDecisionsOpenResultV1 result{};
};
bool ExecuteIngameDecisionsOpenV1(IngameDecisionsOpenContextV1 &query,
    MainThreadQueryMailboxV1 &mailbox, const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch_environment) noexcept;
std::string SerializeIngameDecisionsOpenV1(const IngameDecisionsOpenResultV1 &result);
} // namespace xar::ck3_11906
