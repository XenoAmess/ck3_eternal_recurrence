#pragma once
#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include <string>

namespace xar::ck3_11906 {
inline constexpr std::string_view kIngameMilitaryOpen12004Step = "activate-ingame-military-v1";
inline constexpr std::string_view kIngameMilitaryOpen12004Capability = "game.command.activate-ingame-military-v1";
struct IngameMilitaryOpenResult12004 {
  std::string game_version = "1.20.0.4";
  std::string executable_sha256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  std::uint64_t native_revision = 0, connection_generation = 0;
  std::uint32_t game_pid = 0;
  std::int32_t played_character_id = -1, date_raw = 0;
  bool owner_thread_verified = false, frame_verified = false;
  bool source_abi_pins_verified = false, gui_owner_binding_verified = false;
  bool topbar_tree_complete = false, receiver_qualified = false;
  bool before_visible = false, dispatch_attempted = false, dispatch_invoked = false, native_handled = false;
  bool native_after_read = false, native_after_visible = false;
  bool native_after_tree_complete = false, postcondition_verified = false;
  std::size_t topbar_widget_count = 0, after_widget_count = 0;
  std::string target_child_path, status = "unavailable", unavailable_reason;
};
struct IngameMilitaryOpenContext12004 {
  const game::GameAdapter *game = nullptr;
  game::Snapshot expected_snapshot{};
  std::uint64_t native_revision = 0, connection_generation = 0;
  IngameMilitaryOpenResult12004 result{};
};
bool ExecuteIngameMilitaryOpen12004(IngameMilitaryOpenContext12004 &query,
    MainThreadQueryMailboxV1 &mailbox, const MainThreadExecutionStampV1 &stamp,
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    ZhongguoScoreboardActionDispatchEnvironmentV1 &dispatch_environment) noexcept;
std::string SerializeIngameMilitaryOpen12004(const IngameMilitaryOpenResult12004 &result);
} // namespace xar::ck3_11906
