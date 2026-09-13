#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kFrontendGuiRouteV1Capability =
    "game.command.query-frontend-gui-route-v1";
inline constexpr std::string_view kFrontendGuiRouteV1Step =
    "query-frontend-gui-route-v1";
inline constexpr std::string_view kFrontendGuiOpenNewGameV1Capability =
    "game.command.activate-frontend-new-game-v1";
inline constexpr std::string_view kFrontendGuiOpenNewGameV1Step =
    "activate-frontend-new-game-v1";
inline constexpr std::string_view kFrontendGuiRouteV1BackendId =
    "ck3-1.19.0.6-native-frontend-gui-route-v1";

enum class FrontendGuiRouteOperationV1 : std::uint32_t {
  query = 0,
  open_new_game = 1,
};

enum class FrontendGuiRouteV1 : std::uint32_t {
  unavailable = 0,
  main_menu = 1,
  bookmarks = 2,
  ruler_designer = 3,
  coat_of_arms_designer = 4,
};

struct FrontendGuiRouteResultV1 {
  FrontendGuiRouteV1 route = FrontendGuiRouteV1::unavailable;
  bool target_resolved = false;
  bool dispatch_invoked = false;
  bool native_handled = false;
};

struct FrontendGuiRouteMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  FrontendGuiRouteOperationV1 operation =
      FrontendGuiRouteOperationV1::query;
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ZhongguoScoreboardActionDispatchEnvironmentV1 dispatch_environment{};
  FrontendGuiRouteResultV1 result{};
};

bool ExecuteFrontendGuiRouteMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view FrontendGuiRouteNameV1(FrontendGuiRouteV1 route) noexcept;

} // namespace xar::ck3_11906
