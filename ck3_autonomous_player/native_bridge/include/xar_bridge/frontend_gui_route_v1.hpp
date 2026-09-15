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
inline constexpr std::string_view kFrontendGuiTreeInspectionV1Capability =
    "game.command.inspect-frontend-gui-tree-v1";
inline constexpr std::string_view kFrontendGuiTreeInspectionV1Step =
    "inspect-frontend-gui-tree-v1";
inline constexpr std::string_view
    kFrontendCoatOfArmsTreeInspectionV1Capability =
        "game.command.inspect-frontend-coat-of-arms-tree-v1";
inline constexpr std::string_view
    kFrontendCoatOfArmsTreeInspectionV1Step =
        "inspect-frontend-coat-of-arms-tree-v1";
inline constexpr std::string_view
    kFrontendCoatOfArmsPatternGridInspectionV1Capability =
        "game.command.inspect-frontend-coat-of-arms-pattern-grid-v1";
inline constexpr std::string_view
    kFrontendCoatOfArmsPatternGridInspectionV1Step =
        "inspect-frontend-coat-of-arms-pattern-grid-v1";
inline constexpr std::string_view kFrontendGuiOpenNewGameV1Capability =
    "game.command.activate-frontend-new-game-v1";
inline constexpr std::string_view kFrontendGuiOpenNewGameV1Step =
    "activate-frontend-new-game-v1";
inline constexpr std::string_view kFrontendGuiPickAnyCharacterV1Capability =
    "game.command.activate-frontend-pick-any-character-v1";
inline constexpr std::string_view kFrontendGuiPickAnyCharacterV1Step =
    "activate-frontend-pick-any-character-v1";
inline constexpr std::string_view kFrontendGuiStartSelectedBookmarkV1Capability =
    "game.command.activate-frontend-start-selected-bookmark-v1";
inline constexpr std::string_view kFrontendGuiStartSelectedBookmarkV1Step =
    "activate-frontend-start-selected-bookmark-v1";
inline constexpr std::string_view kFrontendGuiSelectRandomPlayableV1Capability =
    "game.command.activate-frontend-select-random-playable-v1";
inline constexpr std::string_view kFrontendGuiSelectRandomPlayableV1Step =
    "activate-frontend-select-random-playable-v1";
inline constexpr std::string_view kFrontendGuiOpenRulerDesignerV1Capability =
    "game.command.activate-frontend-ruler-designer-v1";
inline constexpr std::string_view kFrontendGuiOpenRulerDesignerV1Step =
    "activate-frontend-ruler-designer-v1";
inline constexpr std::string_view kFrontendGuiOpenCoatOfArmsDesignerV1Capability =
    "game.command.activate-frontend-coat-of-arms-designer-v1";
inline constexpr std::string_view kFrontendGuiOpenCoatOfArmsDesignerV1Step =
    "activate-frontend-coat-of-arms-designer-v1";
inline constexpr std::string_view
    kFrontendGuiCommitDynastyCoatOfArmsV1Capability =
        "game.command.commit-frontend-dynasty-coat-of-arms-v1";
inline constexpr std::string_view kFrontendGuiCommitDynastyCoatOfArmsV1Step =
    "commit-frontend-dynasty-coat-of-arms-v1";
inline constexpr std::string_view
    kFrontendGuiEnterCoatOfArmsCustomModeV1Capability =
        "game.command.activate-frontend-coat-of-arms-custom-mode-v1";
inline constexpr std::string_view
    kFrontendGuiEnterCoatOfArmsCustomModeV1Step =
        "activate-frontend-coat-of-arms-custom-mode-v1";
inline constexpr std::string_view kFrontendGuiRouteV1BackendId =
    "ck3-1.19.0.6-native-frontend-gui-route-v1";

enum class FrontendGuiRouteOperationV1 : std::uint32_t {
  query = 0,
  open_new_game = 1,
  pick_any_character = 2,
  inspect_tree = 3,
  select_random_playable = 4,
  open_ruler_designer = 5,
  open_coat_of_arms_designer = 6,
  commit_dynasty_coat_of_arms = 7,
  inspect_coat_of_arms_tree = 8,
  enter_coat_of_arms_custom_mode = 9,
  inspect_coat_of_arms_pattern_grid = 10,
  start_selected_bookmark = 11,
};

enum class FrontendGuiRouteV1 : std::uint32_t {
  unavailable = 0,
  main_menu = 1,
  bookmarks = 2,
  ruler_designer = 3,
  coat_of_arms_designer = 4,
  lobby = 5,
};

struct FrontendGuiRouteResultV1 {
  FrontendGuiRouteV1 route = FrontendGuiRouteV1::unavailable;
  bool target_resolved = false;
  bool dispatch_invoked = false;
  bool native_handled = false;
  NamedGuiTreeInspectionV1 tree_inspection{};
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
