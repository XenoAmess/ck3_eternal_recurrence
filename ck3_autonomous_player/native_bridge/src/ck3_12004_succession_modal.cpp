#include "xar_bridge/ck3_12004_succession_modal.hpp"
#include "xar_bridge/ck3_12004_succession_modal_pins.hpp"

#include <windows.h>

#include <cstddef>
#include <array>
#include <string>

namespace xar::ck3_12004 {
namespace {

struct FixedGuiRoute {
  std::string_view root;
  std::string_view descendant;
  bool first_visible_enabled = false;
};
constexpr std::array<FixedGuiRoute, ck3_11906::kCurrentTimelineFixedWidgetCountV1>
    kFixedGuiRoutes12004{{
      {"succession_event_window", "succession_event_window", false},
      {"succession_event_window", "bottom", false},
      {"succession_event_window", "close_button", true},
      {"succession_event_window", "menu_button", false},
      {"succession_select_destiny_window", "succession_select_destiny_window", false},
      {"succession_select_destiny_window", "continue_button", false},
      {"succession_select_destiny_window", "continue_button_random", false},
      {"succession_select_destiny_window", "cancel_button", false},
    }};

bool ObserveActual4GuiWidget(void *opaque,
    ck3_11906::CurrentTimelineFixedWidgetV1 identity,
    ck3_11906::CurrentTimelineWidgetObservationV1 &output) noexcept {
  output = {};
  const auto *context = static_cast<const SuccessionModalGuiObservationContext12004 *>(opaque);
  const auto index = static_cast<std::size_t>(identity);
  if (context == nullptr || !context->actual4_bindings_ready ||
      context->environment.gui_abi_revision != ck3_11906::GuiAbiRevisionV1::crozier12004 ||
      index >= kFixedGuiRoutes12004.size()) return false;
  const auto &route = kFixedGuiRoutes12004[index];
  void *root = nullptr;
  void *widget = nullptr;
  const bool resolved = route.first_visible_enabled
      ? ck3_11906::ResolveFirstVisibleEnabledNamedGuiWidgetV1(
          context->environment, context->access, route.root, route.descendant, root, widget)
      : ck3_11906::ResolveNamedGuiWidgetV1(
          context->environment, context->access, route.root, route.descendant, root, widget);
  if (!resolved) return false;
  if (widget == nullptr) return true;
  std::string name;
  void *vtable = nullptr;
  if (!ck3_11906::ReadGuiWidgetRuntimeV1(context->access, widget, name, vtable,
          output.effective_visible, output.enabled) || name != route.descendant) return false;
  output.exists = true;
  return true;
}

template <typename T>
bool ReadAt(std::uintptr_t address, T &output) noexcept {
  SIZE_T read = 0;
  return address != 0 &&
         ReadProcessMemory(GetCurrentProcess(), reinterpret_cast<const void *>(address),
                           &output, sizeof(T), &read) != FALSE && read == sizeof(T);
}

bool ObserveWidget(void *opaque, ck3_11906::CurrentTimelineFixedWidgetV1 identity,
                   ck3_11906::CurrentTimelineWidgetObservationV1 &output) noexcept {
  output = {};
  const auto *bindings = static_cast<const SuccessionModalBindings12004 *>(opaque);
  return bindings != nullptr && bindings->enabled &&
         bindings->gui.actual4_bindings_ready &&
         bindings->gui.image_base == bindings->image_base &&
         bindings->gui.observe_fixed_widget != nullptr &&
         bindings->gui.observe_fixed_widget(bindings->gui.context, identity, output);
}

bool ObservePredicates(void *opaque, std::int32_t character_id,
                       bool &paused, bool &has_open) noexcept {
  paused = false;
  has_open = false;
  const auto *bindings = static_cast<const SuccessionModalBindings12004 *>(opaque);
  if (bindings == nullptr || !bindings->enabled ||
      bindings->is_paused_by_succession == nullptr ||
      bindings->has_open_succession == nullptr) return false;
  void *const character = ResolveCoreCharacter(bindings->core, character_id);
  if (character == nullptr) return false;
  paused = bindings->is_paused_by_succession();
  has_open = bindings->has_open_succession(character);
  return true;
}

bool ResolveController(void *opaque, void *&output) noexcept {
  output = nullptr;
  const auto *bindings = static_cast<const SuccessionModalBindings12004 *>(opaque);
  if (bindings == nullptr || !bindings->enabled || bindings->image_base == 0 ||
      bindings->dynamic_cast_function == nullptr ||
      bindings->handler_primary_vtable == 0 || bindings->controller_primary_vtable == 0)
    return false;
  const auto image = bindings->image_base;
  std::uintptr_t root = 0;
  std::uintptr_t idler = 0;
  if (!ReadAt(image + kJominiStateSlotRva, root) || root == 0 ||
      !ReadAt(root + kSuccessionIdlerBaseOffset12004, idler) || idler == 0) return false;
  void *const ingame = bindings->dynamic_cast_function(reinterpret_cast<void *>(idler), 0,
      reinterpret_cast<void *>(image + kSuccessionIdlerBaseTypeDescriptorRva12004),
      reinterpret_cast<void *>(image + kSuccessionIngameIdlerTypeDescriptorRva12004), 0);
  if (ingame == nullptr) return false;
  std::uintptr_t handler = 0;
  std::uintptr_t handler_vtable = 0;
  std::uintptr_t controller = 0;
  std::uintptr_t controller_vtable = 0;
  if (!ReadAt(reinterpret_cast<std::uintptr_t>(ingame) + kSuccessionIngameHandlerOffset12004,
              handler) || handler == 0 || !ReadAt(handler, handler_vtable) ||
      handler_vtable != bindings->handler_primary_vtable ||
      !ReadAt(handler + kSuccessionHandlerControllerOffset12004, controller) ||
      controller == 0 || !ReadAt(controller, controller_vtable) ||
      controller_vtable != bindings->controller_primary_vtable) return false;
  output = reinterpret_cast<void *>(controller);
  return true;
}

bool ReadControllerOpen(void *opaque, void *controller, bool &open) noexcept {
  open = false;
  const auto *bindings = static_cast<const SuccessionModalBindings12004 *>(opaque);
  if (bindings == nullptr || !bindings->enabled || controller == nullptr ||
      bindings->controller_open == nullptr) return false;
  std::uintptr_t vtable = 0;
  std::uintptr_t target = 0;
  if (!ReadAt(reinterpret_cast<std::uintptr_t>(controller), vtable) ||
      vtable != bindings->controller_primary_vtable ||
      !ReadAt(vtable + kSuccessionControllerOpenVslot12004, target) ||
      target != reinterpret_cast<std::uintptr_t>(bindings->controller_open)) return false;
  open = bindings->controller_open(controller);
  return true;
}

bool CloseController(void *opaque, void *controller) noexcept {
  const auto *bindings = static_cast<const SuccessionModalBindings12004 *>(opaque);
  if (bindings == nullptr || !bindings->enabled || controller == nullptr ||
      bindings->controller_close == nullptr) return false;
  std::uintptr_t vtable = 0;
  std::uintptr_t target = 0;
  if (!ReadAt(reinterpret_cast<std::uintptr_t>(controller), vtable) ||
      vtable != bindings->controller_primary_vtable ||
      !ReadAt(vtable + kSuccessionControllerCloseVslot12004, target) ||
      target != reinterpret_cast<std::uintptr_t>(bindings->controller_close)) return false;
  bindings->controller_close(controller);
  return true;
}

} // namespace

SuccessionModalGuiObservationContext12004
BindSuccessionModalGuiObservationContext12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  SuccessionModalGuiObservationContext12004 result{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256) return result;
  result.environment = ck3_11906::BindZhongguoScoreboardNativeEnvironmentV1(
      image_base, true, ck3_11906::GuiAbiRevisionV1::crozier12004,
      executable_sha256);
  result.actual4_bindings_ready = result.environment.exact_build_admitted &&
      result.environment.gui_abi_revision == ck3_11906::GuiAbiRevisionV1::crozier12004 &&
      result.environment.gui_global_slot != nullptr &&
      result.environment.find_top_level_widget != nullptr;
  return result;
}

SuccessionModalGuiProfile12004 MakeSuccessionModalGuiProfile12004(
    SuccessionModalGuiObservationContext12004 &context) noexcept {
  if (!context.actual4_bindings_ready) return {};
  return {true, context.environment.module_base, &context, &ObserveActual4GuiWidget};
}

SuccessionModalBindings12004 BindSuccessionModalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const SuccessionModalGuiProfile12004 &gui) noexcept {
  SuccessionModalBindings12004 result{};
  if (!kSuccessionModalNativePinsReady12004 || image_base == 0 ||
      executable_sha256 != kExecutableSha256 || !gui.actual4_bindings_ready ||
      gui.image_base != image_base || gui.observe_fixed_widget == nullptr) return result;
  result.image_base = image_base;
  result.core = BindCoreImage(image_base, executable_sha256);
  result.gui = gui;
  result.dynamic_cast_function = reinterpret_cast<SuccessionDynamicCast12004>(
      image_base + kSuccessionRuntimeDynamicCastRva12004);
  result.is_paused_by_succession = reinterpret_cast<IsPausedBySuccession12004>(
      image_base + kIsPausedBySuccessionRva12004);
  result.has_open_succession = reinterpret_cast<HasOpenSuccession12004>(
      image_base + kHasOpenSuccessionRva12004);
  result.controller_open = reinterpret_cast<SuccessionControllerOpen12004>(
      image_base + kSuccessionControllerOpenRva12004);
  result.controller_close = reinterpret_cast<SuccessionControllerClose12004>(
      image_base + kSuccessionControllerCloseRva12004);
  result.handler_primary_vtable = image_base + kSuccessionHandlerPrimaryVtableRva12004;
  result.controller_primary_vtable = image_base + kSuccessionControllerPrimaryVtableRva12004;
  result.enabled = result.core.enabled;
  return result;
}

game::ReadCurrentTimelineBlockerContextResultV1
ReadCurrentTimelineBlockerContextNative12004V1(
    const SuccessionModalBindings12004 &bindings,
    const ck3_11906::CurrentTimelineBlockerReadRequestV1 &request,
    game::CurrentTimelineBlockerContextV1 &output) noexcept {
  ck3_11906::CurrentTimelineBlockerSourceV1 source{};
  if (bindings.enabled) {
    source = {const_cast<SuccessionModalBindings12004 *>(&bindings),
              &ObserveWidget, &ObservePredicates};
  }
  return ck3_11906::ReadCurrentTimelineBlockerContextV1(request, source, output);
}

game::DeathSuccessionModalContinueStatusV1
ExecuteDeathSuccessionModalContinueNative12004V1(
    const SuccessionModalBindings12004 &bindings,
    const ck3_11906::DeathSuccessionModalContinueRequestV1 &request,
    const game::CurrentTimelineBlockerContextV1 &timeline,
    game::DeathSuccessionModalContinueReceiptV1 &receipt) noexcept {
  ck3_11906::DeathSuccessionModalContinueSourceV1 source{};
  if (bindings.enabled) {
    source = {const_cast<SuccessionModalBindings12004 *>(&bindings),
              &ResolveController, &ReadControllerOpen, &CloseController};
  }
  return ck3_11906::ExecuteDeathSuccessionModalContinueV1(request, timeline, source, receipt);
}

} // namespace xar::ck3_12004
