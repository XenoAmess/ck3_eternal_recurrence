#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/frontend_game_rules_v1.hpp"
#include "xar_bridge/frontend_bookmark_model_probe_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
#include "xar_bridge/ingame_decisions_opener_v1.hpp"
#include "xar_bridge/ingame_decision_item_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"

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
inline constexpr std::string_view kFrontendBookmarkModelProbeV1Capability =
    "game.command.probe-frontend-bookmark-model-v1";
inline constexpr std::string_view kFrontendBookmarkModelProbeV1Step =
    "probe-frontend-bookmark-model-v1";
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
inline constexpr std::string_view
    kFrontendGuiSelectSupported1066CharacterV1Capability =
        "game.command.activate-frontend-select-supported-1066-character-v1";
inline constexpr std::string_view
    kFrontendGuiSelectSupported1066CharacterV1Step =
        "select-frontend-supported-1066-character-v1";
// These fixed private seed steps keep the existing public frontend surface
// unchanged. Each step names a stock source profile, never a runtime actor ID.
enum class FrontendBookmarkPrivateStepKindV1 : std::uint32_t {
  none = 0,
  probe = 1,
  select_character = 2,
  start_bookmark = 3,
  select_bookmark = 4,
};

inline FrontendBookmarkPrivateStepKindV1
FrontendBookmarkPrivateStepKindForV1(std::string_view step) noexcept {
  if (step == "probe-frontend-bookmark-model-yahya-v1" ||
      step == "probe-frontend-bookmark-model-rurik-v1") {
    return FrontendBookmarkPrivateStepKindV1::probe;
  }
  if (step == "select-frontend-bookmark-character-yahya-v1" ||
      step == "select-frontend-bookmark-character-rurik-v1") {
    return FrontendBookmarkPrivateStepKindV1::select_character;
  }
  if (step == "activate-frontend-start-selected-bookmark-yahya-v1" ||
      step == "activate-frontend-start-selected-bookmark-rurik-v1") {
    return FrontendBookmarkPrivateStepKindV1::start_bookmark;
  }
  if (step == "activate-frontend-select-bookmark-rurik-v1") {
    return FrontendBookmarkPrivateStepKindV1::select_bookmark;
  }
  return FrontendBookmarkPrivateStepKindV1::none;
}

inline bool IsFrontendBookmarkPrivateActionStepV1(
    std::string_view step) noexcept {
  const auto kind = FrontendBookmarkPrivateStepKindForV1(step);
  return kind == FrontendBookmarkPrivateStepKindV1::select_character ||
         kind == FrontendBookmarkPrivateStepKindV1::start_bookmark ||
         kind == FrontendBookmarkPrivateStepKindV1::select_bookmark;
}

inline FrontendBookmarkSeedTargetV1
FrontendBookmarkPrivateTargetForV1(std::string_view step) noexcept {
  if (step == "probe-frontend-bookmark-model-yahya-v1" ||
      step == "select-frontend-bookmark-character-yahya-v1" ||
      step == "activate-frontend-start-selected-bookmark-yahya-v1") {
    return FrontendBookmarkSeedTargetV1::yahya_1066;
  }
  if (step == "probe-frontend-bookmark-model-rurik-v1" ||
      step == "select-frontend-bookmark-character-rurik-v1" ||
      step == "activate-frontend-start-selected-bookmark-rurik-v1" ||
      step == "activate-frontend-select-bookmark-rurik-v1") {
    return FrontendBookmarkSeedTargetV1::rurik_867;
  }
  return FrontendBookmarkSeedTargetV1::configured_1066;
}
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
inline constexpr std::string_view
    kFrontendGuiRandomizeRulerFirstNameV1Capability =
        "game.command.activate-frontend-randomize-ruler-first-name-v1";
inline constexpr std::string_view
    kFrontendGuiRandomizeRulerFirstNameV1Step =
        "activate-frontend-randomize-ruler-first-name-v1";
inline constexpr std::string_view
    kFrontendGuiFinalizeCustomRulerV1Capability =
        "game.command.activate-frontend-finalize-custom-ruler-v1";
inline constexpr std::string_view kFrontendGuiFinalizeCustomRulerV1Step =
    "activate-frontend-finalize-custom-ruler-v1";
inline constexpr std::string_view
    kFrontendGuiConfirmCustomRulerV1Capability =
        "game.command.activate-frontend-confirm-custom-ruler-v1";
inline constexpr std::string_view kFrontendGuiConfirmCustomRulerV1Step =
    "activate-frontend-confirm-custom-ruler-v1";
inline constexpr std::string_view
    kFrontendGuiStartLobbySelectedCharacterV1Capability =
        "game.command.activate-frontend-start-lobby-selected-character-v1";
inline constexpr std::string_view
    kFrontendGuiStartLobbySelectedCharacterV1Step =
        "activate-frontend-start-lobby-selected-character-v1";
inline constexpr std::string_view kFrontendGuiRouteV1BackendId =
    "ck3-1.19.0.6-native-frontend-gui-route-v1";

// Bounded window census reuses the already migrated named GUI primitives.
// It does not read a decision model, selected/down, rendered text or tooltip.
inline constexpr std::string_view kGuiWindowTreeInspectionV1Capability =
    "game.command.inspect-gui-window-tree-v1";
inline constexpr std::string_view kGuiWindowTreeInspectionV1Step =
    "inspect-gui-window-tree-v1";
enum class GuiWindowTreeScopeV1 : std::uint32_t {
  unavailable = 0, decisions = 1, decision_detail = 2,
  courtier = 3, vivhite_courtier = 4, ingame_topbar = 5,
};
inline GuiWindowTreeScopeV1 GuiWindowTreeScopeForV1(
    std::string_view kind) noexcept {
  if (kind == "ingame_topbar") return GuiWindowTreeScopeV1::ingame_topbar;
  if (kind == "decisions") return GuiWindowTreeScopeV1::decisions;
  if (kind == "decision_detail") return GuiWindowTreeScopeV1::decision_detail;
  if (kind == "courtier") return GuiWindowTreeScopeV1::courtier;
  if (kind == "vivhite_courtier") return GuiWindowTreeScopeV1::vivhite_courtier;
  return GuiWindowTreeScopeV1::unavailable;
}
inline std::string_view GuiWindowTreeRootForV1(
    GuiWindowTreeScopeV1 scope) noexcept {
  switch (scope) {
  case GuiWindowTreeScopeV1::ingame_topbar: return "ingame_topbar";
  case GuiWindowTreeScopeV1::decisions: return "decisions_view";
  case GuiWindowTreeScopeV1::decision_detail: return "decisiondetail_view";
  case GuiWindowTreeScopeV1::courtier: return "xar_courtier_creator_window";
  case GuiWindowTreeScopeV1::vivhite_courtier: return "ervc_courtier_creator_window";
  default: return {};
  }
}

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
  probe_bookmark_model = 12,
  select_supported_1066_character = 13,
  randomize_ruler_first_name = 14,
  finalize_custom_ruler = 15,
  confirm_custom_ruler = 16,
  start_lobby_selected_character = 17,
  select_supported_bookmark = 18,
  ingame_ui = 19,
  query_game_rules = 20,
  open_game_rules = 21,
  query_game_rules_control = 22,
  select_game_rule = 23,
  apply_and_hide_game_rules = 24,
  hide_game_rules = 25,
  query_applied_game_rules = 26,
  inspect_gui_window_tree = 27,
  open_ingame_decisions = 29, // 28 reserved for the independent DecisionView observer.
  query_ingame_decision_item = 30,
  action_ingame_decision_item = 31,
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
  FrontendBookmarkModelProbeV1 bookmark_model_probe{};
  FrontendBookmarkSelectionV1 bookmark_selection{};
  FrontendBookmarkChangeV1 bookmark_change{};
  FrontendGameRulesObservationV1 game_rules{};
  FrontendGameRulesControlV1 game_rules_control{};
  FrontendGameRulesMutationV1 game_rules_mutation{};
  FrontendAppliedGameRulesV1 applied_game_rules{};
};

struct FrontendGuiRouteMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  FrontendGuiRouteOperationV1 operation =
      FrontendGuiRouteOperationV1::query;
  FrontendBookmarkSeedTargetV1 bookmark_seed_target =
      FrontendBookmarkSeedTargetV1::configured_1066;
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ZhongguoScoreboardActionDispatchEnvironmentV1 dispatch_environment{};
  FrontendGuiRouteResultV1 result{};
  GuiWindowTreeScopeV1 gui_window_tree_scope = GuiWindowTreeScopeV1::unavailable;
  std::string rule_key;
  std::string expected_current_setting_key;
  std::string desired_setting_key;
  Bindings ingame_bindings{};
  game::Snapshot ingame_expected_snapshot{};
  IngameUiRequestV1 ingame_request{};
  IngameUiResultV1 ingame_result{};
  IngameDecisionsOpenContextV1 ingame_decisions{};
  IngameDecisionItemContextV1 ingame_decision_item{};
  IngameDecisionItemActionContextV1 ingame_decision_action{};
};

bool ExecuteFrontendGuiRouteMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view FrontendGuiRouteNameV1(FrontendGuiRouteV1 route) noexcept;

} // namespace xar::ck3_11906
