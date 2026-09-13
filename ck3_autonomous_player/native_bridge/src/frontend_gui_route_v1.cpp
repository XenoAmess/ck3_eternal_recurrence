#include "xar_bridge/frontend_gui_route_v1.hpp"

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

bool InspectActiveRouteTree(FrontendGuiRouteMailboxContextV1 &query) noexcept {
  if (!ResolveRoute(query, query.result)) return false;
  ZhongguoScoreboardAccessV1 access{};
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
  if (query->operation == FrontendGuiRouteOperationV1::inspect_tree) {
    return InspectActiveRouteTree(*query);
  }
  if (!ResolveRoute(*query, query->result)) return false;
  if (query->operation == FrontendGuiRouteOperationV1::query) return true;
  if (query->operation == FrontendGuiRouteOperationV1::open_new_game) {
    return DispatchOpenNewGame(*query);
  }
  if (query->operation == FrontendGuiRouteOperationV1::pick_any_character) {
    return DispatchPickAnyCharacter(*query);
  }
  if (query->operation ==
      FrontendGuiRouteOperationV1::select_random_playable) {
    return DispatchSelectRandomPlayable(*query);
  }
  return query->operation == FrontendGuiRouteOperationV1::open_ruler_designer &&
         DispatchOpenRulerDesigner(*query);
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
