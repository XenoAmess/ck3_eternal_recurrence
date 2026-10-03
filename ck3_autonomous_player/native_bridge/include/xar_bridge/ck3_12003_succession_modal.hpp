#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/current_timeline_blocker_context_v1.hpp"
#include "xar_bridge/death_succession_modal_continue_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_12003 {

inline constexpr std::uintptr_t kSuccessionIdlerRootSlotRva12003 = 0x5C6A520;
inline constexpr std::uintptr_t kSuccessionRuntimeDynamicCastRva12003 = 0x4260E94;
inline constexpr std::uintptr_t kSuccessionIdlerBaseTypeDescriptorRva12003 = 0x5514438;
inline constexpr std::uintptr_t kSuccessionIngameIdlerTypeDescriptorRva12003 = 0x5514460;
inline constexpr std::uintptr_t kSuccessionHandlerPrimaryVtableRva12003 = 0x44BA890;
inline constexpr std::uintptr_t kSuccessionControllerPrimaryVtableRva12003 = 0x4522D90;
inline constexpr std::uintptr_t kSuccessionControllerCloseRva12003 = 0x10D8900;
inline constexpr std::uintptr_t kSuccessionControllerOpenRva12003 = 0x10D8BC0;
inline constexpr std::uintptr_t kIsPausedBySuccessionRva12003 = 0xA7C440;
inline constexpr std::uintptr_t kHasOpenSuccessionRva12003 = 0xA7C4D0;

using SuccessionDynamicCast12003 = void *(__cdecl *)(void *, long, void *, void *, int);
using IsPausedBySuccession12003 = bool(__fastcall *)();
using HasOpenSuccession12003 = bool(__fastcall *)(void *);
using SuccessionControllerOpen12003 = bool(__fastcall *)(void *);
using SuccessionControllerClose12003 = void(__fastcall *)(void *);

// Internal native-image bindings only. No address or callback comes from wire
// data. Fixtures can own the mapped image and substitute function pointers.
struct SuccessionModalBindings12003 {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  ck3_12002::CoreBindings core{};
  ck3_11906::ZhongguoScoreboardNativeEnvironmentV1 gui{};
  ck3_11906::ZhongguoScoreboardAccessV1 gui_access{};
  SuccessionDynamicCast12003 dynamic_cast_function = nullptr;
  IsPausedBySuccession12003 is_paused_by_succession = nullptr;
  HasOpenSuccession12003 has_open_succession = nullptr;
  SuccessionControllerOpen12003 controller_open = nullptr;
  SuccessionControllerClose12003 controller_close = nullptr;
  std::uintptr_t handler_primary_vtable = 0;
  std::uintptr_t controller_primary_vtable = 0;
};

SuccessionModalBindings12003 BindSuccessionModalImage12003(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

game::ReadCurrentTimelineBlockerContextResultV1
ReadCurrentTimelineBlockerContextNative12003V1(
    const SuccessionModalBindings12003 &bindings,
    const ck3_11906::CurrentTimelineBlockerReadRequestV1 &request,
    game::CurrentTimelineBlockerContextV1 &output) noexcept;

game::DeathSuccessionModalContinueStatusV1
ExecuteDeathSuccessionModalContinueNative12003V1(
    const SuccessionModalBindings12003 &bindings,
    const ck3_11906::DeathSuccessionModalContinueRequestV1 &request,
    const game::CurrentTimelineBlockerContextV1 &timeline,
    game::DeathSuccessionModalContinueReceiptV1 &receipt) noexcept;

} // namespace xar::ck3_12003
