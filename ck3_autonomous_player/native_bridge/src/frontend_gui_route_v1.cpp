#include "xar_bridge/frontend_gui_route_v1.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <windows.h>

#include <array>
#include <charconv>
#include <cstdint>
#include <string>

namespace xar::ck3_11906 {
namespace {

struct FixedWidgetProbeV1 {
  std::string_view root_name;
  std::string_view widget_name;
  FrontendGuiRouteV1 route;
};

constexpr std::array<FixedWidgetProbeV1, 5> kRoutePriority{{
    {"ruler_designer", "coat_of_arms_page",
     FrontendGuiRouteV1::coat_of_arms_designer},
    {"ruler_designer", "ruler_designer",
     FrontendGuiRouteV1::ruler_designer},
    {"lobbyview", "lobbyview", FrontendGuiRouteV1::lobby},
    {"frontend_bookmarks", "frontend_bookmarks",
     FrontendGuiRouteV1::bookmarks},
    {"mainmenu_panel_bottom", "mainmenu_panel_bottom",
     FrontendGuiRouteV1::main_menu},
}};

bool IsExecutingFrontendSlot(
    const FrontendGuiRouteMailboxContextV1 &query,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  if (query.mailbox == nullptr || query.ticket.sequence == 0 ||
      stamp.pump_epoch == 0 || stamp.thread_id == 0 ||
      stamp.tls_initialized_flag_address == 0 || stamp.tls_initialized != 1 ||
      stamp.tls_context == 0 || stamp.tls_main_thread_marker != 1 ||
      GetCurrentThreadId() != stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.owner_verified_pump_epochs.load(std::memory_order_acquire) >=
             kMainThreadQueryMinimumOwnerVerifiedPumpEpochs &&
         mailbox.executor == &ExecuteFrontendGuiRouteMailboxV1 &&
         mailbox.executor_context ==
             const_cast<FrontendGuiRouteMailboxContextV1 *>(&query);
}

std::string FormatPointer(void *value) {
  if (value == nullptr) return {};
  std::array<char, 2 + sizeof(std::uintptr_t) * 2 + 1> buffer{};
  buffer[0] = '0';
  buffer[1] = 'x';
  const auto converted = std::to_chars(
      buffer.data() + 2, buffer.data() + buffer.size() - 1,
      reinterpret_cast<std::uintptr_t>(value), 16);
  if (converted.ec != std::errc{}) return {};
  for (char *cursor = buffer.data() + 2; cursor < converted.ptr; ++cursor) {
    if (*cursor >= 'a' && *cursor <= 'f') *cursor -= ('a' - 'A');
  }
  return std::string(buffer.data(), converted.ptr);
}

bool ResolveRoute(const FrontendGuiRouteMailboxContextV1 &query,
                  FrontendGuiRouteResultV1 &result) noexcept {
  ZhongguoScoreboardAccessV1 access{};
  for (const auto &probe : kRoutePriority) {
    void *root = nullptr;
    void *widget = nullptr;
    if (!ResolveNamedGuiWidgetV1(query.environment, access,
                                 probe.root_name, probe.widget_name,
                                 root, widget)) {
      return false;
    }
    if (widget == nullptr) continue;
    std::string runtime_name;
    void *vtable = nullptr;
    bool visible = false;
    bool enabled = false;
    if (!ReadGuiWidgetRuntimeV1(access, widget, runtime_name, vtable,
                                visible, enabled)) {
      return false;
    }
    if (visible && runtime_name == probe.widget_name) {
      result.route = probe.route;
      return true;
    }
  }
  result.route = FrontendGuiRouteV1::unavailable;
  return true;
}

bool InspectGuiWindowTree(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  const auto root_name = GuiWindowTreeRootForV1(query.gui_window_tree_scope);
  if (root_name.empty()) return false;
  auto &out = query.result.tree_inspection;
  out = {};
  out.scope_root_name.assign(root_name);
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *widget = nullptr;
  if (!ResolveNamedGuiWidgetV1(query.environment, access, root_name,
                               root_name, root, widget)) return false;
  // A missing/preloaded-hidden window is an observation, never "opened".
  if (root == nullptr) return widget == nullptr;
  if (widget != root) return false;
  return InspectNamedGuiSubtreeV1(access, query.environment.module_base,
                                  root, root_name, out);
}

bool InspectActiveRouteTree(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (!ResolveRoute(query, query.result)) return false;
  ZhongguoScoreboardAccessV1 access{};
#if defined(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1)
  if (query.result.route == FrontendGuiRouteV1::bookmarks &&
      query.environment.gui_abi_revision == GuiAbiRevisionV1::crozier12003) {
    void *root = nullptr;
    void *widget = nullptr;
    if (!ResolveNamedGuiWidgetV1(query.environment, access, "game_rules",
                                 "game_rules", root, widget)) return false;
    if (root != nullptr && widget == root) {
      std::string name;
      void *vtable = nullptr;
      bool visible = false, enabled = false;
      if (!ReadGuiWidgetRuntimeV1(access, root, name, vtable, visible, enabled) ||
          name != "game_rules") return false;
      if (visible) {
        return InspectNamedGuiSubtreeV1(access, query.environment.module_base,
                                        root, "game_rules",
                                        query.result.tree_inspection);
      }
    }
  }
#endif
  for (const auto &probe : kRoutePriority) {
    if (probe.route != query.result.route) continue;
    void *root = nullptr;
    void *widget = nullptr;
    if (!ResolveNamedGuiWidgetV1(query.environment, access, probe.root_name,
                                 probe.root_name, root, widget)) {
      return false;
    }
    return root != nullptr && widget == root &&
           InspectNamedGuiSubtreeV1(access, query.environment.module_base,
                                    root, probe.root_name,
                                    query.result.tree_inspection);
  }
  return InspectNamedGuiTreeV1(query.environment, access,
                               query.result.tree_inspection);
}

#if defined(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1)
bool ResolveRulesControlRoot(FrontendGuiRouteMailboxContextV1 &query,
                             void *&root) noexcept {
  auto &o = query.result.game_rules_control;
  root = nullptr;
  if (!ResolveRoute(query, query.result) ||
      query.result.route != FrontendGuiRouteV1::bookmarks) {
    o.unavailable_reason = "bookmarks_route_unavailable"; return true;
  }
  ZhongguoScoreboardAccessV1 access{};
  void *widget = nullptr, *vtable = nullptr;
  std::string name;
  bool visible = false, enabled = false;
  if (!ResolveNamedGuiWidgetV1(query.environment, access, "game_rules", "game_rules",
                               root, widget) || !root || widget != root ||
      !ReadGuiWidgetRuntimeV1(access, root, name, vtable, visible, enabled) ||
      name != "game_rules") {
    o.unavailable_reason = "current_named_game_rules_root_unverified"; return true;
  }
  if (!ProbeFrontendGameRulesControlV1(query.environment, access, root, o)) return false;
  if (!o.ready) return true;
  void *after_root = nullptr, *after_widget = nullptr, *after_vtable = nullptr;
  std::string after_name;
  bool after_visible = false, after_enabled = false;
  if (!ResolveNamedGuiWidgetV1(query.environment, access, "game_rules", "game_rules",
                               after_root, after_widget) || after_root != root ||
      after_widget != root ||
      !ReadGuiWidgetRuntimeV1(access, root, after_name, after_vtable,
                              after_visible, after_enabled) ||
      after_name != name || after_vtable != vtable || after_visible != visible ||
      after_enabled != enabled || o.window_visible != visible ||
      o.window_enabled != enabled) {
    o = {}; o.unavailable_reason = "game_rules_named_root_changed_during_observation";
  }
  return true;
}

bool InspectAppliedRules(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (!ResolveRoute(query, query.result) || query.result.route != FrontendGuiRouteV1::bookmarks) {
    query.result.applied_game_rules.unavailable_reason = "bookmarks_route_unavailable"; return true;
  }
  ZhongguoScoreboardAccessV1 access{};
  return ProbeFrontendAppliedGameRulesV1(query.environment, access, query.result.applied_game_rules);
}

bool InspectRulesControl(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  void *root = nullptr; return ResolveRulesControlRoot(query, root);
}

bool DispatchRulesMutation(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  void *root = nullptr;
  if (!ResolveRulesControlRoot(query, root)) return false;
  if (!query.result.game_rules_control.ready) {
    query.result.game_rules_mutation.unavailable_reason =
        query.result.game_rules_control.unavailable_reason; return true;
  }
  ZhongguoScoreboardAccessV1 access{};
  FrontendGameRulesCallsV1 calls{};
  if (query.operation == FrontendGuiRouteOperationV1::select_game_rule)
    return SelectFrontendGameRuleV1(query.environment, access, root,
        query.rule_key, query.expected_current_setting_key, query.desired_setting_key,
        calls, query.result.game_rules_mutation);
  return ApplyAndHideFrontendGameRulesV1(query.environment, access, root,
      query.operation == FrontendGuiRouteOperationV1::apply_and_hide_game_rules,
      calls, query.result.game_rules_mutation);
}

bool InspectGameRules(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  auto &result = query.result.game_rules;
  if (query.environment.gui_abi_revision != GuiAbiRevisionV1::crozier12003) {
    result.unavailable_reason = "exact_12003_game_rules_environment_unverified";
    return true;
  }
  if (!ResolveRoute(query, query.result) ||
      query.result.route != FrontendGuiRouteV1::bookmarks) {
    result.unavailable_reason = "bookmarks_route_unavailable";
    return true;
  }
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *widget = nullptr;
  std::string name;
  void *vtable = nullptr;
  bool visible = false, enabled = false;
  if (!ResolveNamedGuiWidgetV1(query.environment, access, "game_rules",
                               "game_rules", root, widget) || !root ||
      widget != root ||
      !ReadGuiWidgetRuntimeV1(access, root, name, vtable, visible, enabled) ||
      name != "game_rules" || !visible) {
    result.unavailable_reason = "visible_game_rules_root_unverified";
    return true;
  }
  return ProbeFrontendGameRulesV1(query.environment, access, root, result);
}
#endif

bool InspectBookmarkModel(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (!ResolveRoute(query, query.result) ||
      query.result.route != FrontendGuiRouteV1::bookmarks) {
    query.result.bookmark_model_probe.unavailable_reason =
        "bookmarks_route_unavailable";
    return true;
  }
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *widget = nullptr;
  if (!ResolveNamedGuiWidgetV1(query.environment, access,
                               "frontend_bookmarks", "frontend_bookmarks",
                               root, widget) || root == nullptr ||
      widget != root) {
    query.result.bookmark_model_probe.unavailable_reason =
        "bookmarks_root_unverified";
    return true;
  }
  return ProbeFrontendBookmarkModelV1(
      query.environment, access, root, query.result.bookmark_model_probe,
      nullptr, query.bookmark_seed_target);
}

bool InspectCoatOfArmsTree(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (!ResolveRoute(query, query.result) ||
      query.result.route != FrontendGuiRouteV1::coat_of_arms_designer) {
    return false;
  }
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *target = nullptr;
  if (!ResolveNamedGuiWidgetV1(query.environment, access, "ruler_designer",
                               "coat_of_arms_page", root, target) ||
      target == nullptr) {
    return false;
  }
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  return ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable, visible,
                                enabled) &&
         runtime_name == "coat_of_arms_page" && visible && enabled &&
         InspectNamedGuiSubtreeV1(access, query.environment.module_base,
                                  target, "coat_of_arms_page",
                                  query.result.tree_inspection);
}

bool InspectCoatOfArmsPatternGrid(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (!ResolveRoute(query, query.result) ||
      query.result.route != FrontendGuiRouteV1::coat_of_arms_designer) {
    return false;
  }

  // CK3 1.19.0.6 coa_designer.gui, verified against the live custom-mode
  // background page. Every index remains native-owned and compile-time fixed;
  // callers cannot substitute a path, name, pointer, or traversal limit.
  constexpr std::array<std::uint32_t, 2> kCoatOfArmsPagePath{{0, 2}};
  constexpr std::array<std::uint32_t, 8> kBackgroundPanelPath{{
      0, 2, 0, 3, 0, 2, 1, 1,
  }};
  constexpr std::array<std::uint32_t, 9> kPatternsPath{{
      0, 2, 0, 3, 0, 2, 1, 1, 2,
  }};
  constexpr std::array<std::uint32_t, 11> kPatternsScrollboxPath{{
      0, 2, 0, 3, 0, 2, 1, 1, 2, 0, 0,
  }};
  constexpr std::array<std::uint32_t, 13> kPatternGridPath{{
      0, 2, 0, 3, 0, 2, 1, 1, 2, 0, 0, 0, 0,
  }};

  struct FixedAncestor {
    const std::uint32_t *path;
    std::size_t path_size;
    std::string_view runtime_name;
  };
  const std::array<FixedAncestor, 4> kAncestors{{
      {kCoatOfArmsPagePath.data(), kCoatOfArmsPagePath.size(),
       "coat_of_arms_page"},
      {kBackgroundPanelPath.data(), kBackgroundPanelPath.size(),
       "background_panel"},
      {kPatternsPath.data(), kPatternsPath.size(), "patterns"},
      {kPatternsScrollboxPath.data(), kPatternsScrollboxPath.size(),
       "patterns_scrollbox"},
  }};

  ZhongguoScoreboardAccessV1 access{};
  for (const auto &ancestor : kAncestors) {
    void *root = nullptr;
    void *target = nullptr;
    if (!ResolveFixedGuiChildPathV1(
            query.environment, access, "ruler_designer", ancestor.path,
            ancestor.path_size, root, target) ||
        root == nullptr || target == nullptr) {
      return false;
    }
    std::string runtime_name;
    void *vtable = nullptr;
    bool visible = false;
    bool enabled = false;
    if (!ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable, visible,
                                enabled) ||
        runtime_name != ancestor.runtime_name || !visible || !enabled) {
      return false;
    }
  }

  void *root = nullptr;
  void *grid = nullptr;
  if (!ResolveFixedGuiChildPathV1(
          query.environment, access, "ruler_designer", kPatternGridPath.data(),
          kPatternGridPath.size(), root, grid) ||
      root == nullptr || grid == nullptr) {
    return false;
  }
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, grid, runtime_name, vtable, visible,
                              enabled) ||
      !runtime_name.empty() || !visible || !enabled) {
    return false;
  }
  return InspectNamedGuiSubtreeV1(
             access, query.environment.module_base, grid,
             "coat_of_arms_pattern_grid", query.result.tree_inspection) &&
         query.result.tree_inspection.widget_count > 1 &&
         query.result.tree_inspection.widgets[0].child_count > 0;
}

bool DispatchFixedNamedWidget(FrontendGuiRouteMailboxContextV1 &query,
                              FrontendGuiRouteV1 expected_route,
                              std::string_view root_name,
                              std::string_view target_name) noexcept {
  if (query.result.route != expected_route) return false;
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *target = nullptr;
  if (!ResolveNamedGuiWidgetV1(query.environment, access,
                               root_name, target_name,
                               root, target) ||
      target == nullptr) {
    return false;
  }
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable,
                              visible, enabled) ||
      runtime_name != target_name || !visible || !enabled) {
    return false;
  }
  query.result.target_resolved = true;
  const auto instance_pointer = FormatPointer(target);
  const auto vtable_pointer = FormatPointer(vtable);
  if (instance_pointer.empty() || vtable_pointer.empty()) return false;
  query.result.dispatch_invoked = DispatchZhongguoScoreboardActionNativeV1(
      &query.dispatch_environment, game::ZhongguoScoreboardActionV1::open,
      target_name, runtime_name, instance_pointer,
      vtable_pointer, query.result.native_handled);
  return query.result.dispatch_invoked;
}

bool DispatchOpenNewGame(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  return DispatchFixedNamedWidget(query, FrontendGuiRouteV1::main_menu,
                                  "mainmenu_panel_bottom",
                                  "new_game_button");
}

bool DispatchPickAnyCharacter(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  return DispatchFixedNamedWidget(query, FrontendGuiRouteV1::bookmarks,
                                  "frontend_bookmarks",
                                  "pick_any_character_button");
}

bool DispatchStartSelectedBookmark(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::bookmarks) return false;
  // Do not infer the target from HasSelectedCharacter/CanStart. The current
  // native model must still select the unique key-derived stock role.
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *selected = nullptr;
  if (!ResolveNamedGuiWidgetV1(query.environment, access,
                               "frontend_bookmarks", "character_selection",
                               root, selected) ||
      selected == nullptr) {
    return false;
  }
  FrontendBookmarkModelProbeV1 model{};
  if (!ProbeFrontendBookmarkModelV1(query.environment, access, root,
                                    model, nullptr,
                                    query.bookmark_seed_target) ||
      !model.candidate_identity_ready ||
      model.selected_character_index !=
          model.supported_1066_candidate_index) {
    return false;
  }
  // frontend_bookmarks.gui:144 and 2023-2029. The selected-character
  // projection must be visible before the exact StartGame button is used.
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, selected, runtime_name, vtable,
                              visible, enabled) ||
      runtime_name != "character_selection" || !visible) {
    return false;
  }
  return DispatchFixedNamedWidget(query, FrontendGuiRouteV1::bookmarks,
                                  "frontend_bookmarks", "start_button");
}

bool DispatchSelectSupported1066Character(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::bookmarks) return false;
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *widget = nullptr;
  if (!ResolveNamedGuiWidgetV1(query.environment, access,
                               "frontend_bookmarks",
                               "frontend_bookmarks", root, widget) ||
      root == nullptr || widget != root) {
    return false;
  }
  if (!SelectSupportedFeudalBookmarkCharacterV1(
          query.environment, access, root,
          query.result.bookmark_selection, nullptr, nullptr,
          query.bookmark_seed_target)) {
    return false;
  }
  query.result.target_resolved =
      query.result.bookmark_selection.target_resolved;
  query.result.dispatch_invoked =
      query.result.bookmark_selection.setter_invoked;
  query.result.native_handled =
      query.result.bookmark_selection.same_frame_index_matches;
  // An already selected or rejected current model never submits a new
  // setter call. A submitted call remains unverified until a new frame.
  return true;
}

bool DispatchSelectRandomPlayable(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::lobby) return false;
  // multiplayer_lobby.gui: bottom controls -> button column -> the second
  // button.  Vanilla binds this exact unnamed widget to
  // SetRandomPlayableObserverCharacter.  The adjacent first button is the
  // debug-only title finder and the third toggles observer mode.
  constexpr std::array<std::uint32_t, 5> kRandomPlayablePath{{4, 0, 1, 0, 1}};
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *target = nullptr;
  if (!ResolveFixedGuiChildPathV1(
          query.environment, access, "lobbyview", kRandomPlayablePath.data(),
          kRandomPlayablePath.size(), root, target) ||
      target == nullptr) {
    return false;
  }
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable, visible,
                              enabled) ||
      !runtime_name.empty() || !visible || !enabled) {
    return false;
  }
  query.result.target_resolved = true;
  query.result.dispatch_invoked = DispatchFixedGuiWidgetNativeV1(
      &query.dispatch_environment, game::ZhongguoScoreboardActionV1::open,
      target, vtable, query.result.native_handled);
  return query.result.dispatch_invoked;
}

bool DispatchSelectSupportedBookmark(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::bookmarks) return false;
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *widget = nullptr;
  if (!ResolveNamedGuiWidgetV1(query.environment, access,
                               "frontend_bookmarks", "frontend_bookmarks",
                               root, widget) ||
      root == nullptr || widget != root) {
    return false;
  }
  if (!SelectSupportedBookmarkV1(
          query.environment, access, root, query.result.bookmark_change,
          query.bookmark_seed_target)) {
    return false;
  }
  query.result.target_resolved = query.result.bookmark_change.target_resolved;
  query.result.dispatch_invoked = query.result.bookmark_change.setter_invoked;
  // Complete the model request so its domain rejection reaches the existing
  // result formatter. Setter invocation remains a separate acknowledgement.
  return true;
}

bool DispatchOpenRulerDesigner(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::lobby) return false;
  constexpr std::array<std::uint32_t, 4> kDefaultRulerDesignerPath{{3, 0, 2,
                                                                    3}};
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *target = nullptr;
  if (!ResolveFixedGuiChildPathV1(
          query.environment, access, "lobbyview",
          kDefaultRulerDesignerPath.data(), kDefaultRulerDesignerPath.size(),
          root, target) ||
      target == nullptr) {
    return false;
  }
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable, visible,
                              enabled) ||
      !runtime_name.empty() || !visible || !enabled) {
    return false;
  }
  query.result.target_resolved = true;
  query.result.dispatch_invoked = DispatchFixedGuiWidgetNativeV1(
      &query.dispatch_environment, game::ZhongguoScoreboardActionV1::open,
      target, vtable, query.result.native_handled);
  return query.result.dispatch_invoked;
}

bool DispatchOpenCoatOfArmsDesigner(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::ruler_designer) return false;
  // window_ruler_designer.gui:514-548: dynasty_house -> content vbox ->
  // preview row -> second child. Vanilla binds this exact unnamed
  // button_edit_text to OpenDynastyCoatOfArmsDesigner and then sets
  // coat_of_arms_customization_open='dynasty'. The live ruler-designer tree
  // proves the parent chain through depth 10; the source fixes this leaf.
  constexpr std::array<std::uint32_t, 11> kDynastyCoatOfArmsButtonPath{{
      0, 0, 0, 0, 0, 0, 0, 3, 1, 0, 1,
  }};
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *target = nullptr;
  if (!ResolveFixedGuiChildPathV1(
          query.environment, access, "ruler_designer",
          kDynastyCoatOfArmsButtonPath.data(),
          kDynastyCoatOfArmsButtonPath.size(), root, target) ||
      target == nullptr) {
    return false;
  }
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable, visible,
                              enabled) ||
      !runtime_name.empty() || !visible || !enabled) {
    return false;
  }
  query.result.target_resolved = true;
  query.result.dispatch_invoked = DispatchFixedGuiWidgetNativeV1(
      &query.dispatch_environment, game::ZhongguoScoreboardActionV1::open,
      target, vtable, query.result.native_handled);
  return query.result.dispatch_invoked;
}

bool DispatchCommitDynastyCoatOfArms(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  // window_ruler_designer.gui:3318-3351 binds this exact named button to
  // FinishDynastyCoatOfArmsDesigner, followed by clearing the variable that
  // owns the dedicated CoA page. Resolve it from the live ruler-designer tree
  // so callers cannot substitute another button or a raw widget pointer.
  return DispatchFixedNamedWidget(
      query, FrontendGuiRouteV1::coat_of_arms_designer, "ruler_designer",
      "dynasty_finish_button");
}

bool DispatchRandomizeRulerFirstName(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  // window_ruler_designer.gui:495-504 binds this exact named control to
  // RandomizeFirstNameCulture. It supplies a valid first name without text
  // input, which is the only missing default required by CanFinalize.
  return DispatchFixedNamedWidget(query, FrontendGuiRouteV1::ruler_designer,
                                  "ruler_designer",
                                  "random_culture_name");
}

bool DispatchFinalizeCustomRuler(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::ruler_designer) return false;
  // window_ruler_designer.gui:1739-1750: footer vbox -> spacer -> unnamed
  // button_primary_big bound to FinalizeOverwrite. The live 1.19.0.6 tree
  // fixes this leaf at 0/0/6/0/2/2; enabled is required so an incomplete
  // ruler can never be submitted.
  constexpr std::array<std::uint32_t, 6> kFinalizeCustomRulerPath{{
      0, 0, 6, 0, 2, 2,
  }};
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *target = nullptr;
  if (!ResolveFixedGuiChildPathV1(
          query.environment, access, "ruler_designer",
          kFinalizeCustomRulerPath.data(), kFinalizeCustomRulerPath.size(),
          root, target) ||
      target == nullptr) {
    return false;
  }
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable, visible,
                              enabled) ||
      !runtime_name.empty() || !visible || !enabled) {
    return false;
  }
  query.result.target_resolved = true;
  query.result.dispatch_invoked = DispatchFixedGuiWidgetNativeV1(
      &query.dispatch_environment, game::ZhongguoScoreboardActionV1::open,
      target, vtable, query.result.native_handled);
  return query.result.dispatch_invoked;
}

bool DispatchConfirmCustomRuler(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  // shared/dialogs.gui:78-112 instantiates basic_confirmation_popup with the
  // unique accept_button bound to GameDialog.Accept. FinalizeOverwrite opens
  // this modal using RULER_DESIGNER_FINALIZE_OVERWRITE_ACCEPT; resolve the
  // named popup root and button rather than any screen coordinate.
  return DispatchFixedNamedWidget(query, FrontendGuiRouteV1::ruler_designer,
                                  "basic_confirmation_popup",
                                  "accept_button");
}

bool DispatchStartLobbySelectedCharacter(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::lobby) return false;
  // multiplayer_types.gui:1898-2124 defines JominiLobbyViewPreparation.
  // Its final two children are the preparation-host Start button and the
  // ordinary single-player selected-character Start button. The live
  // 1.19.0.6 lobby fixes the latter at 3/0/2/6. It calls LobbyView.Control,
  // then LobbyView.Ready; visibility and enabled state are both mandatory.
  // The template button itself is 3/0/2/6; do not descend into a generated
  // visual child.
  constexpr std::array<std::uint32_t, 4> kStartButtonPath{{3, 0, 2, 6}};
  ZhongguoScoreboardAccessV1 access{};
  void *root = nullptr;
  void *target = nullptr;
  if (!ResolveFixedGuiChildPathV1(
          query.environment, access, "lobbyview", kStartButtonPath.data(),
          kStartButtonPath.size(), root, target) ||
      target == nullptr) {
    return false;
  }
  std::string runtime_name;
  void *vtable = nullptr;
  bool visible = false;
  bool enabled = false;
  if (!ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable, visible,
                              enabled) ||
      !runtime_name.empty() || !visible || !enabled) {
    return false;
  }
  query.result.target_resolved = true;
  query.result.dispatch_invoked = DispatchFixedGuiWidgetNativeV1(
      &query.dispatch_environment, game::ZhongguoScoreboardActionV1::open,
      target, vtable, query.result.native_handled);
  return query.result.dispatch_invoked;
}

bool DispatchEnterCoatOfArmsCustomMode(
    FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (query.result.route != FrontendGuiRouteV1::coat_of_arms_designer) {
    return false;
  }
  // coa_designer.gui:351-437 contains two mutually exclusive custom-mode
  // buttons. The first continues an already-custom design; the second
  // converts an adjusted design. Both enter the background page and call the
  // engine's UpdatePatternPreviewColors data-model path. Resolve only these
  // exact source-owned leaves and dispatch the one live visible target.
  constexpr std::array<std::uint32_t, 12> kContinueCustomPath{{
      0, 2, 0, 3, 0, 2, 1, 0, 0, 1, 1, 0,
  }};
  constexpr std::array<std::uint32_t, 12> kConvertToCustomPath{{
      0, 2, 0, 3, 0, 2, 1, 0, 0, 2, 1, 0,
  }};
  const std::array<const std::array<std::uint32_t, 12> *, 2> kPaths{{
      &kContinueCustomPath,
      &kConvertToCustomPath,
  }};
  ZhongguoScoreboardAccessV1 access{};
  void *selected = nullptr;
  void *selected_vtable = nullptr;
  for (const auto *path : kPaths) {
    void *root = nullptr;
    void *target = nullptr;
    if (!ResolveFixedGuiChildPathV1(
            query.environment, access, "ruler_designer", path->data(),
            path->size(), root, target) ||
        target == nullptr) {
      return false;
    }
    std::string runtime_name;
    void *vtable = nullptr;
    bool visible = false;
    bool enabled = false;
    if (!ReadGuiWidgetRuntimeV1(access, target, runtime_name, vtable, visible,
                                enabled) ||
        runtime_name != "button_custom_mode") {
      return false;
    }
    if (!visible) continue;
    if (!enabled || selected != nullptr) return false;
    selected = target;
    selected_vtable = vtable;
  }
  if (selected == nullptr || selected_vtable == nullptr) return false;
  query.result.target_resolved = true;
  query.result.dispatch_invoked = DispatchFixedGuiWidgetNativeV1(
      &query.dispatch_environment, game::ZhongguoScoreboardActionV1::open,
      selected, selected_vtable, query.result.native_handled);
  return query.result.dispatch_invoked;
}

} // namespace

bool ExecuteFrontendGuiRouteMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept {
  auto *query = static_cast<FrontendGuiRouteMailboxContextV1 *>(
      opaque_context);
  if (query == nullptr || !IsExecutingFrontendSlot(*query, stamp)) {
    return false;
  }
  query->result = {};
#if defined(XAR_CK3_ENABLE_GRANT_TITLE_PICKER_PRIVATE_V1)
  if(query->operation==FrontendGuiRouteOperationV1::grant_title_picker)
    return ck3_12003::ExecuteGrantTitlePickerV1(query->grant_title_picker,*query->mailbox,stamp,query->environment);
#endif
#if defined(XAR_CK3_ENABLE_PLAYER_CONTROL_PRIVATE_V1)
  if(query->operation==FrontendGuiRouteOperationV1::player_control_readonly) {
    query->player_control_readonly.ticket=query->ticket;
    query->player_control_readonly.owner_executor_context=query;
    return ck3_12003::ExecutePlayerControlReadonlyV1(query->player_control_readonly,
        *query->mailbox,stamp,query->environment);
  }
#endif
  if (query->operation == FrontendGuiRouteOperationV1::inspect_gui_window_tree) {
    return InspectGuiWindowTree(*query);
  }
#if defined(XAR_CK3_ENABLE_NORMAL_EXIT_MAP_PRIVATE_V1)
  if (query->operation == FrontendGuiRouteOperationV1::normal_exit_map) {
    query->normal_exit_map.ticket = query->ticket;
    query->normal_exit_map.owner_executor_context = query;
    return ck3_12003::ExecuteNormalExitMapV1(query->normal_exit_map, *query->mailbox,
        stamp, query->environment, query->dispatch_environment);
  }
#endif
  if (query->operation == FrontendGuiRouteOperationV1::open_ingame_decisions) {
    return ExecuteIngameDecisionsOpenV1(query->ingame_decisions, *query->mailbox, stamp,
        query->environment, query->dispatch_environment);
  }
  if (query->operation == FrontendGuiRouteOperationV1::query_ingame_decision_item) {
    return ExecuteIngameDecisionItemQueryV1(query->ingame_decision_item, *query->mailbox, stamp, query->environment);
  }
  if (query->operation == FrontendGuiRouteOperationV1::action_ingame_decision_item) {
    return ExecuteIngameDecisionItemActionV1(query->ingame_decision_action, *query->mailbox, stamp,
        query->environment, query->dispatch_environment);
  }
#if defined(XAR_CK3_ENABLE_WHITE_PLAYER_BUSINESS_VARIABLES_PRIVATE_V1)
  if (query->operation == FrontendGuiRouteOperationV1::query_white_player_business_variables) {
    return ExecuteWhitePlayerBusinessVariablesV1(query->white_player_business_variables, *query->mailbox, stamp);
  }
#endif
#if defined(XAR_CK3_ENABLE_AUB_CONFIRM_STATE_PRIVATE_V1)
  if (query->operation == FrontendGuiRouteOperationV1::aub_business_state)
    return ck3_12003::ExecuteAubBusinessStateQueryV1(query->aub_business_state,*query->mailbox,stamp,query->environment);
  if (query->operation == FrontendGuiRouteOperationV1::aub_confirm)
    return ck3_12003::ExecuteAubConfirmV1(query->aub_confirm,*query->mailbox,stamp,query->environment,query->dispatch_environment);
#endif
#if defined(XAR_CK3_ENABLE_AUB_POLICY_OPTIONS_PRIVATE_V1)
  if (query->operation == FrontendGuiRouteOperationV1::aub_policy_options) {
    return ck3_12003::ExecuteAubPolicyOptionsMailboxV1(query->aub_policy_options, *query->mailbox, stamp, query->environment);
  }
#endif
#if defined(XAR_CK3_ENABLE_WHITE_RENDERED_TEXT_PRIVATE_V1)
  if (query->operation == FrontendGuiRouteOperationV1::query_white_rendered_text) {
    return ExecuteWhiteRenderedTextV1(query->white_rendered_text, *query->mailbox, stamp, query->environment);
  }
#endif
#if defined(XAR_CK3_ENABLE_WHITE_CONTROL_ACTIONS_PRIVATE_V1)
  if (query->operation == FrontendGuiRouteOperationV1::action_white_control) {
    return ExecuteWhiteControlActionV1(query->white_control_action, *query->mailbox, stamp, query->environment, query->dispatch_environment);
  }
#endif
  if (query->operation == FrontendGuiRouteOperationV1::ingame_ui) {
    // Failure metadata is observed at this original application event boundary,
    // never copied from the caller's expected snapshot.
    query->ingame_result = {};
    query->ingame_result.gui_abi_revision = query->environment.gui_abi_revision;
    query->ingame_result.army_tooltip.requested = !query->ingame_request.army_tooltip_kind.empty();
    query->ingame_result.army_tooltip.semantic_kind = query->ingame_request.army_tooltip_kind;
    query->ingame_result.date_raw = stamp.date_raw;
    query->ingame_result.paused = stamp.paused;
    query->ingame_result.pump_epoch = stamp.pump_epoch;
    query->ingame_result.thread_id = stamp.thread_id;
    query->ingame_result.rng_owner_thread_id = stamp.rng_owner_thread_id;
    const bool current_ui=query->environment.gui_abi_revision==GuiAbiRevisionV1::crozier12003;
    const auto read_ui_snapshot=[&](game::Snapshot &value) noexcept {
      if(!current_ui)return ReadSnapshot(query->ingame_bindings,value);
      return query->ingame_game &&
          query->ingame_game->descriptor().game_version==ck3_12003::kGameVersion &&
          query->ingame_game->descriptor().executable_sha256==ck3_12003::kExecutableSha256 &&
          game::ReadSnapshot(*query->ingame_game,value);
    };
    game::Snapshot before{};
    if (!IsIngameUiPausedOwnerStampV1(*query->mailbox, stamp, GetCurrentThreadId())) {
      query->ingame_result.unavailable_reason = "application_paused_owner_stamp_unverified";
      return true;
    }
    query->ingame_result.application_owner_thread_verified = true;
    if (!read_ui_snapshot(before)) {
      query->ingame_result.unavailable_reason = "owner_fresh_snapshot_read_failed";
      return true;
    }
    query->ingame_result.played_character_id = before.played_character_id;
    if (before != query->ingame_expected_snapshot || !before.paused ||
        !before.map_ready || !before.has_played_character || before.date_raw != stamp.date_raw) {
      query->ingame_result.unavailable_reason = "owner_fresh_snapshot_admission_failed";
      return true;
    }
    IngameUiGuiOwnerBindingV1 gui_before{};
    if (!ReadIngameUiGuiOwnerBindingV1(query->environment, gui_before)) {
      query->ingame_result.unavailable_reason = "current_gui_owner_binding_unverified";
      return true;
    }
    const bool ran = ExecuteIngameUiNavigationV1(query->environment,
        query->ingame_request, before, stamp, gui_before, query->ingame_result);
    query->ingame_result.application_owner_thread_verified = true;
    query->ingame_result.rng_owner_thread_id = stamp.rng_owner_thread_id;
    query->ingame_result.gui_context_address = reinterpret_cast<std::uintptr_t>(gui_before.context);
    query->ingame_result.gui_owner_address = reinterpret_cast<std::uintptr_t>(gui_before.owner);
    IngameUiGuiOwnerBindingV1 gui_after{};
    const bool same_gui = ReadIngameUiGuiOwnerBindingV1(query->environment, gui_after) && gui_after == gui_before;
    query->ingame_result.gui_owner_binding_verified = same_gui;
    game::Snapshot after{};
    if (!ran || !read_ui_snapshot(after) || after != before) {
      query->ingame_result.available = false;
      query->ingame_result.status = "unavailable";
      query->ingame_result.unavailable_reason = "owner_post_navigation_snapshot_changed";
    } else if (!same_gui) {
      query->ingame_result.available = false;
      query->ingame_result.status = "unavailable";
      query->ingame_result.unavailable_reason = "current_gui_owner_binding_changed_after_navigation";
    }
    if(!query->ingame_result.available && query->ingame_result.army_tooltip.requested) {
      const auto kind=query->ingame_request.army_tooltip_kind;
      query->ingame_result.army_tooltip={};
      query->ingame_result.army_tooltip.requested=true;
      query->ingame_result.army_tooltip.semantic_kind=kind;
      query->ingame_result.army_tooltip.unavailable_reason=query->ingame_result.unavailable_reason;
    }
    return true;
  }
#if defined(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1)
  if (query->operation == FrontendGuiRouteOperationV1::query_game_rules) {
    return InspectGameRules(*query);
  }
  if (query->operation == FrontendGuiRouteOperationV1::query_applied_game_rules)
    return InspectAppliedRules(*query);
  if (query->operation == FrontendGuiRouteOperationV1::query_game_rules_control)
    return InspectRulesControl(*query);
  if (query->operation == FrontendGuiRouteOperationV1::select_game_rule ||
      query->operation == FrontendGuiRouteOperationV1::apply_and_hide_game_rules ||
      query->operation == FrontendGuiRouteOperationV1::hide_game_rules)
    return DispatchRulesMutation(*query);
#endif
  if (query->operation == FrontendGuiRouteOperationV1::inspect_tree) {
    return InspectActiveRouteTree(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::probe_bookmark_model) {
    return InspectBookmarkModel(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::inspect_coat_of_arms_tree) {
    return InspectCoatOfArmsTree(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::inspect_coat_of_arms_pattern_grid) {
    return InspectCoatOfArmsPatternGrid(*query);
  }
  if (!ResolveRoute(*query, query->result)) return false;
  if (query->operation == FrontendGuiRouteOperationV1::query) return true;
  if (query->operation ==
      FrontendGuiRouteOperationV1::select_supported_1066_character) {
    return DispatchSelectSupported1066Character(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::select_supported_bookmark) {
    return DispatchSelectSupportedBookmark(*query);
  }
#if defined(XAR_CK3_ENABLE_FRONTEND_GAME_RULES_PRIVATE_V1)
  if (query->operation == FrontendGuiRouteOperationV1::open_game_rules) {
    if (query->environment.gui_abi_revision != GuiAbiRevisionV1::crozier12003)
      return false;
    return DispatchFixedNamedWidget(*query, FrontendGuiRouteV1::bookmarks,
                                    "frontend_bookmarks", "game_rules_button");
  }
#endif
  if (query->operation == FrontendGuiRouteOperationV1::open_new_game) {
    return DispatchOpenNewGame(*query);
  }
  if (query->operation == FrontendGuiRouteOperationV1::pick_any_character) {
    return DispatchPickAnyCharacter(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::start_selected_bookmark) {
    return DispatchStartSelectedBookmark(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::select_random_playable) {
    return DispatchSelectRandomPlayable(*query);
  }
  if (query->operation == FrontendGuiRouteOperationV1::open_ruler_designer) {
    return DispatchOpenRulerDesigner(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::open_coat_of_arms_designer) {
    return DispatchOpenCoatOfArmsDesigner(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::enter_coat_of_arms_custom_mode) {
    return DispatchEnterCoatOfArmsCustomMode(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::randomize_ruler_first_name) {
    return DispatchRandomizeRulerFirstName(*query);
  }
  if (query->operation == FrontendGuiRouteOperationV1::finalize_custom_ruler) {
    return DispatchFinalizeCustomRuler(*query);
  }
  if (query->operation == FrontendGuiRouteOperationV1::confirm_custom_ruler) {
    return DispatchConfirmCustomRuler(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::start_lobby_selected_character) {
    return DispatchStartLobbySelectedCharacter(*query);
  }
  return query->operation ==
             FrontendGuiRouteOperationV1::commit_dynasty_coat_of_arms &&
         DispatchCommitDynastyCoatOfArms(*query);
}

std::string_view FrontendGuiRouteNameV1(FrontendGuiRouteV1 route) noexcept {
  switch (route) {
  case FrontendGuiRouteV1::main_menu:
    return "main_menu";
  case FrontendGuiRouteV1::bookmarks:
    return "bookmarks";
  case FrontendGuiRouteV1::lobby:
    return "lobby";
  case FrontendGuiRouteV1::ruler_designer:
    return "ruler_designer";
  case FrontendGuiRouteV1::coat_of_arms_designer:
    return "coat_of_arms_designer";
  case FrontendGuiRouteV1::unavailable:
  default:
    return "unavailable";
  }
}

} // namespace xar::ck3_11906
