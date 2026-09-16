#include "xar_bridge/current_timeline_blocker_context_v1.hpp"

#include <array>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

struct NativeSourceContextV1 {
  const ZhongguoScoreboardNativeEnvironmentV1 *environment = nullptr;
  const ZhongguoScoreboardAccessV1 *access = nullptr;
};

struct FixedRouteV1 {
  std::string_view root;
  std::string_view descendant;
  bool first_visible_enabled = false;
};

constexpr std::array<FixedRouteV1, kCurrentTimelineFixedWidgetCountV1> kRoutes{{
    {"succession_event_window", "succession_event_window", false},
    {"succession_event_window", "bottom", false},
    {"succession_event_window", "close_button", true},
    {"succession_event_window", "menu_button", false},
    {"succession_select_destiny_window", "succession_select_destiny_window",
     false},
    {"succession_select_destiny_window", "continue_button", false},
    {"succession_select_destiny_window", "continue_button_random", false},
    {"succession_select_destiny_window", "cancel_button", false},
}};

bool ObserveNative(void *opaque, CurrentTimelineFixedWidgetV1 identity,
                   CurrentTimelineWidgetObservationV1 &output) noexcept {
  output = {};
  const auto index = static_cast<std::size_t>(identity);
  auto *context = static_cast<NativeSourceContextV1 *>(opaque);
  if (context == nullptr || context->environment == nullptr ||
      context->access == nullptr || index >= kRoutes.size()) {
    return false;
  }
  const auto &route = kRoutes[index];
  void *root = nullptr;
  void *widget = nullptr;
  const bool resolved =
      route.first_visible_enabled
          ? ResolveFirstVisibleEnabledNamedGuiWidgetV1(
                *context->environment, *context->access, route.root,
                route.descendant, root, widget)
          : ResolveNamedGuiWidgetV1(*context->environment, *context->access,
                                    route.root, route.descendant, root, widget);
  if (!resolved)
    return false;
  if (widget == nullptr)
    return true;
  std::string runtime_name;
  void *vtable = nullptr;
  if (!ReadGuiWidgetRuntimeV1(*context->access, widget, runtime_name, vtable,
                              output.effective_visible, output.enabled) ||
      runtime_name != route.descendant) {
    return false;
  }
  output.exists = true;
  return true;
}

} // namespace

game::ReadCurrentTimelineBlockerContextResultV1
ReadCurrentTimelineBlockerContextNativeV1(
    const ZhongguoScoreboardNativeEnvironmentV1 &environment,
    const ZhongguoScoreboardAccessV1 &access,
    const CurrentTimelineBlockerReadRequestV1 &request,
    game::CurrentTimelineBlockerContextV1 &output) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.offline_fixture_function_overrides ||
      reinterpret_cast<std::uintptr_t>(environment.find_top_level_widget) !=
          environment.module_base + kZhongguoGuiFindTopLevelWidgetRva) {
    CurrentTimelineBlockerSourceV1 invalid{};
    return ReadCurrentTimelineBlockerContextV1(request, invalid, output);
  }
  NativeSourceContextV1 context{&environment, &access};
  CurrentTimelineBlockerSourceV1 source{&context, &ObserveNative};
  return ReadCurrentTimelineBlockerContextV1(request, source, output);
}

} // namespace xar::ck3_11906
