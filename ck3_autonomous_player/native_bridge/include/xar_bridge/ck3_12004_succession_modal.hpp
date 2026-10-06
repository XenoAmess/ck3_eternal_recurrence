#pragma once

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/current_timeline_blocker_context_v1.hpp"
#include "xar_bridge/death_succession_modal_continue_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12004 {

// Produced by the shared actual-.4 GUI owner. The callback observes only the
// existing eight fixed widget identities; there are no wire names or pointers.
// This is a caller-owned software DTO, not an old GUI image/profile alias.
struct SuccessionModalGuiProfile12004 {
  bool actual4_bindings_ready = false;
  std::uintptr_t image_base = 0;
  void *context = nullptr;
  ck3_11906::ObserveCurrentTimelineFixedWidgetV1 observe_fixed_widget = nullptr;
};

struct SuccessionModalGuiObservationContext12004 {
  bool actual4_bindings_ready = false;
  ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ck3_11906::ZhongguoScoreboardAccessV1 access{};
};

SuccessionModalGuiObservationContext12004
BindSuccessionModalGuiObservationContext12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
SuccessionModalGuiProfile12004 MakeSuccessionModalGuiProfile12004(
    SuccessionModalGuiObservationContext12004 &context) noexcept;

using SuccessionDynamicCast12004 = void *(__cdecl *)(void *, long, void *, void *, int);
using IsPausedBySuccession12004 = bool(__fastcall *)();
using HasOpenSuccession12004 = bool(__fastcall *)(void *);
using SuccessionControllerOpen12004 = bool(__fastcall *)(void *);
using SuccessionControllerClose12004 = void(__fastcall *)(void *);

struct SuccessionModalBindings12004 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  CoreBindings core{};
  SuccessionModalGuiProfile12004 gui{};
  SuccessionDynamicCast12004 dynamic_cast_function = nullptr;
  IsPausedBySuccession12004 is_paused_by_succession = nullptr;
  HasOpenSuccession12004 has_open_succession = nullptr;
  SuccessionControllerOpen12004 controller_open = nullptr;
  SuccessionControllerClose12004 controller_close = nullptr;
  std::uintptr_t handler_primary_vtable = 0;
  std::uintptr_t controller_primary_vtable = 0;
};

SuccessionModalBindings12004 BindSuccessionModalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const SuccessionModalGuiProfile12004 &gui) noexcept;

game::ReadCurrentTimelineBlockerContextResultV1
ReadCurrentTimelineBlockerContextNative12004V1(
    const SuccessionModalBindings12004 &bindings,
    const ck3_11906::CurrentTimelineBlockerReadRequestV1 &request,
    game::CurrentTimelineBlockerContextV1 &output) noexcept;

game::DeathSuccessionModalContinueStatusV1
ExecuteDeathSuccessionModalContinueNative12004V1(
    const SuccessionModalBindings12004 &bindings,
    const ck3_11906::DeathSuccessionModalContinueRequestV1 &request,
    const game::CurrentTimelineBlockerContextV1 &timeline,
    game::DeathSuccessionModalContinueReceiptV1 &receipt) noexcept;

} // namespace xar::ck3_12004
