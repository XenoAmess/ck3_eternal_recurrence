#include "xar_bridge/current_timeline_blocker_context_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"

#include <windows.h>

#include <array>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

struct NativeSourceContextV1 {
  const Bindings *bindings = nullptr;
  const ZhongguoScoreboardNativeEnvironmentV1 *environment = nullptr;
  const ZhongguoScoreboardAccessV1 *access = nullptr;
};

constexpr std::uintptr_t kIsPausedBySuccessionRva = 0xA05A90;
constexpr std::uintptr_t kHasOpenSuccessionRva = 0xA05B20;

using IsPausedBySuccessionV1 = bool(__fastcall *)();
using HasOpenSuccessionV1 = bool(__fastcall *)(void *);

bool ReadCurrent(const void *address, void *output, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != nullptr && output != nullptr && size > 0 &&
         ReadProcessMemory(GetCurrentProcess(), address, output, size, &read) !=
             FALSE &&
         read == size;
}

bool ResolveCharacter(const Bindings &bindings, std::int32_t character_id,
                      void *&output) noexcept {
  output = nullptr;
  if (character_id <= 0 || bindings.character_storage_slot == nullptr)
    return false;
  void *storage = nullptr;
  void *slots = nullptr;
  std::int32_t capacity = 0;
  if (!ReadCurrent(bindings.character_storage_slot, &storage,
                   sizeof(storage)) ||
      storage == nullptr ||
      !ReadCurrent(static_cast<const std::byte *>(storage) + 0x20, &slots,
                   sizeof(slots)) ||
      slots == nullptr ||
      !ReadCurrent(static_cast<const std::byte *>(storage) + 0x2C, &capacity,
                   sizeof(capacity)) ||
      capacity <= 0) {
    return false;
  }
  const auto index = static_cast<std::uint32_t>(character_id) & 0x00FFFFFFU;
  if (index >= static_cast<std::uint32_t>(capacity)) return false;
  void *character = nullptr;
  const auto slot = static_cast<const std::byte *>(slots) +
                    static_cast<std::size_t>(index) * 0x10 + 0x08;
  std::int32_t round_trip = -1;
  if (!ReadCurrent(slot, &character, sizeof(character)) ||
      character == nullptr ||
      !ReadCurrent(static_cast<const std::byte *>(character) + 0x18,
                   &round_trip, sizeof(round_trip)) ||
      round_trip != character_id) {
    return false;
  }
  output = character;
  return true;
}

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

bool ObserveSuccessionPredicatesNative(void *opaque,
                                       std::int32_t played_character_id,
                                       bool &is_paused,
                                       bool &has_open) noexcept {
  is_paused = false;
  has_open = false;
  auto *context = static_cast<NativeSourceContextV1 *>(opaque);
  if (context == nullptr || context->bindings == nullptr ||
      context->environment == nullptr ||
      !context->environment->exact_build_admitted ||
      context->environment->module_base == 0 || played_character_id <= 0) {
    return false;
  }
  void *character = nullptr;
  if (!ResolveCharacter(*context->bindings, played_character_id, character)) {
    return false;
  }
  const auto is_paused_by_succession =
      reinterpret_cast<IsPausedBySuccessionV1>(
          context->environment->module_base + kIsPausedBySuccessionRva);
  const auto has_open_succession = reinterpret_cast<HasOpenSuccessionV1>(
      context->environment->module_base + kHasOpenSuccessionRva);
  is_paused = is_paused_by_succession();
  has_open = has_open_succession(character);
  return true;
}

} // namespace

game::ReadCurrentTimelineBlockerContextResultV1
ReadCurrentTimelineBlockerContextNativeV1(
    const Bindings &bindings,
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
  NativeSourceContextV1 context{&bindings, &environment, &access};
  CurrentTimelineBlockerSourceV1 source{
      &context, &ObserveNative, &ObserveSuccessionPredicatesNative};
  return ReadCurrentTimelineBlockerContextV1(request, source, output);
}

} // namespace xar::ck3_11906
