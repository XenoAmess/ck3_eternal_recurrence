#include "xar_bridge/ck3_12003_succession_modal.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <string>

namespace xar::ck3_12003 {
namespace {

using WidgetIdentity = ck3_11906::CurrentTimelineFixedWidgetV1;
using WidgetObservation = ck3_11906::CurrentTimelineWidgetObservationV1;

bool ReadCurrent(const void *address, void *output, std::size_t size) noexcept {
  SIZE_T read = 0;
  return address != nullptr && output != nullptr && size > 0 &&
         ReadProcessMemory(GetCurrentProcess(), address, output, size, &read) != FALSE &&
         read == size;
}

template <typename T>
bool ReadAt(std::uintptr_t address, T &output) noexcept {
  return address != 0 &&
         ReadCurrent(reinterpret_cast<const void *>(address), &output, sizeof(T));
}

struct FixedRoute {
  std::string_view root;
  std::string_view descendant;
  bool first_visible_enabled = false;
};

constexpr std::array<FixedRoute, ck3_11906::kCurrentTimelineFixedWidgetCountV1> kRoutes{{
    {"succession_event_window", "succession_event_window", false},
    {"succession_event_window", "bottom", false},
    {"succession_event_window", "close_button", true},
    {"succession_event_window", "menu_button", false},
    {"succession_select_destiny_window", "succession_select_destiny_window", false},
    {"succession_select_destiny_window", "continue_button", false},
    {"succession_select_destiny_window", "continue_button_random", false},
    {"succession_select_destiny_window", "cancel_button", false},
}};

bool ObserveWidget(void *opaque, WidgetIdentity identity,
                   WidgetObservation &output) noexcept {
  output = {};
  const auto *bindings = static_cast<const SuccessionModalBindings12003 *>(opaque);
  const auto index = static_cast<std::size_t>(identity);
  if (bindings == nullptr || !bindings->enabled || index >= kRoutes.size()) return false;
  const auto &route = kRoutes[index];
  void *root = nullptr;
  void *widget = nullptr;
  const bool resolved = route.first_visible_enabled
      ? ck3_11906::ResolveFirstVisibleEnabledNamedGuiWidgetV1(
            bindings->gui, bindings->gui_access, route.root, route.descendant, root, widget)
      : ck3_11906::ResolveNamedGuiWidgetV1(
            bindings->gui, bindings->gui_access, route.root, route.descendant, root, widget);
  if (!resolved) return false;
  if (widget == nullptr) return true;
  std::string runtime_name;
  void *vtable = nullptr;
  if (!ck3_11906::ReadGuiWidgetRuntimeV1(bindings->gui_access, widget, runtime_name,
          vtable, output.effective_visible, output.enabled) || runtime_name != route.descendant)
    return false;
  output.exists = true;
  return true;
}

bool ObservePredicates(void *opaque, std::int32_t played_character_id,
                       bool &paused, bool &has_open) noexcept {
  paused = false;
  has_open = false;
  const auto *bindings = static_cast<const SuccessionModalBindings12003 *>(opaque);
  if (bindings == nullptr || !bindings->enabled ||
      bindings->is_paused_by_succession == nullptr || bindings->has_open_succession == nullptr)
    return false;
  void *const character = ck3_12002::ResolveCoreCharacter(bindings->core, played_character_id);
  if (character == nullptr) return false;
  paused = bindings->is_paused_by_succession();
  has_open = bindings->has_open_succession(character);
  return true;
}

bool ResolveController(void *opaque, void *&output) noexcept {
  output = nullptr;
  const auto *bindings = static_cast<const SuccessionModalBindings12003 *>(opaque);
  if (bindings == nullptr || !bindings->enabled || bindings->image_base == 0 ||
      bindings->dynamic_cast_function == nullptr || bindings->handler_primary_vtable == 0 ||
      bindings->controller_primary_vtable == 0) return false;
  const auto image = bindings->image_base;
  std::uintptr_t root = 0;
  std::uintptr_t idler = 0;
  if (!ReadAt(image + kSuccessionIdlerRootSlotRva12003, root) || root == 0 ||
      !ReadAt(root + 0x10, idler) || idler == 0) return false;
  void *const ingame = bindings->dynamic_cast_function(reinterpret_cast<void *>(idler), 0,
      reinterpret_cast<void *>(image + kSuccessionIdlerBaseTypeDescriptorRva12003),
      reinterpret_cast<void *>(image + kSuccessionIngameIdlerTypeDescriptorRva12003), 0);
  if (ingame == nullptr) return false;
  std::uintptr_t handler = 0;
  std::uintptr_t handler_vtable = 0;
  std::uintptr_t controller = 0;
  std::uintptr_t controller_vtable = 0;
  if (!ReadAt(reinterpret_cast<std::uintptr_t>(ingame) + 0x88, handler) || handler == 0 ||
      !ReadAt(handler, handler_vtable) || handler_vtable != bindings->handler_primary_vtable ||
      !ReadAt(handler + 0x260, controller) || controller == 0 ||
      !ReadAt(controller, controller_vtable) ||
      controller_vtable != bindings->controller_primary_vtable) return false;
  output = reinterpret_cast<void *>(controller);
  return true;
}

bool ReadControllerOpen(void *opaque, void *controller, bool &open) noexcept {
  open = false;
  const auto *bindings = static_cast<const SuccessionModalBindings12003 *>(opaque);
  if (bindings == nullptr || !bindings->enabled || controller == nullptr ||
      bindings->controller_open == nullptr) return false;
  std::uintptr_t vtable = 0;
  std::uintptr_t target = 0;
  if (!ReadAt(reinterpret_cast<std::uintptr_t>(controller), vtable) ||
      vtable != bindings->controller_primary_vtable || !ReadAt(vtable + 0x38, target) ||
      target != reinterpret_cast<std::uintptr_t>(bindings->controller_open)) return false;
  open = bindings->controller_open(controller);
  return true;
}

bool CloseController(void *opaque, void *controller) noexcept {
  const auto *bindings = static_cast<const SuccessionModalBindings12003 *>(opaque);
  if (bindings == nullptr || !bindings->enabled || controller == nullptr ||
      bindings->controller_close == nullptr) return false;
  std::uintptr_t vtable = 0;
  std::uintptr_t target = 0;
  if (!ReadAt(reinterpret_cast<std::uintptr_t>(controller), vtable) ||
      vtable != bindings->controller_primary_vtable || !ReadAt(vtable + 0x88, target) ||
      target != reinterpret_cast<std::uintptr_t>(bindings->controller_close)) return false;
  bindings->controller_close(controller);
  return true;
}

} // namespace

SuccessionModalBindings12003 BindSuccessionModalImage12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  SuccessionModalBindings12003 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.image_base = image_base;
  // The exact .3 adapter already reuses the reviewed .2 core layout. Keep that
  // binder strict; admit this .3 caller here, then use the same core addresses.
  result.core = ck3_12002::BindCoreImage(image_base, ck3_12002::kExecutableSha256);
  result.gui = ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(
      image_base, true, ck3_11906::GuiAbiRevisionV1::crozier12003);
  result.dynamic_cast_function = reinterpret_cast<SuccessionDynamicCast12003>(
      image_base + kSuccessionRuntimeDynamicCastRva12003);
  result.is_paused_by_succession = reinterpret_cast<IsPausedBySuccession12003>(
      image_base + kIsPausedBySuccessionRva12003);
  result.has_open_succession = reinterpret_cast<HasOpenSuccession12003>(
      image_base + kHasOpenSuccessionRva12003);
  result.controller_open = reinterpret_cast<SuccessionControllerOpen12003>(
      image_base + kSuccessionControllerOpenRva12003);
  result.controller_close = reinterpret_cast<SuccessionControllerClose12003>(
      image_base + kSuccessionControllerCloseRva12003);
  result.handler_primary_vtable = image_base + kSuccessionHandlerPrimaryVtableRva12003;
  result.controller_primary_vtable = image_base + kSuccessionControllerPrimaryVtableRva12003;
  result.enabled = result.core.enabled;
  return result;
}

game::ReadCurrentTimelineBlockerContextResultV1
ReadCurrentTimelineBlockerContextNative12003V1(
    const SuccessionModalBindings12003 &bindings,
    const ck3_11906::CurrentTimelineBlockerReadRequestV1 &request,
    game::CurrentTimelineBlockerContextV1 &output) noexcept {
  ck3_11906::CurrentTimelineBlockerSourceV1 source{};
  if (bindings.enabled && bindings.gui.gui_abi_revision ==
          ck3_11906::GuiAbiRevisionV1::crozier12003) {
    source = {const_cast<SuccessionModalBindings12003 *>(&bindings),
              &ObserveWidget, &ObservePredicates};
  }
  return ck3_11906::ReadCurrentTimelineBlockerContextV1(request, source, output);
}

game::DeathSuccessionModalContinueStatusV1
ExecuteDeathSuccessionModalContinueNative12003V1(
    const SuccessionModalBindings12003 &bindings,
    const ck3_11906::DeathSuccessionModalContinueRequestV1 &request,
    const game::CurrentTimelineBlockerContextV1 &timeline,
    game::DeathSuccessionModalContinueReceiptV1 &receipt) noexcept {
  ck3_11906::DeathSuccessionModalContinueSourceV1 source{};
  if (bindings.enabled) {
    source = {const_cast<SuccessionModalBindings12003 *>(&bindings),
              &ResolveController, &ReadControllerOpen, &CloseController};
  }
  return ck3_11906::ExecuteDeathSuccessionModalContinueV1(request, timeline, source, receipt);
}

} // namespace xar::ck3_12003
