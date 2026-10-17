#pragma once
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
namespace xar::ck3_11906 {
// Called only after the existing native UI owner/TLS/paused/modal admission.
bool ExecuteHolySiteRelicNavigation12004(const ZhongguoScoreboardNativeEnvironmentV1&,
 void*handler,const IngameUiRequestV1&,const game::Snapshot&,const MainThreadExecutionStampV1&,
 const IngameUiGuiOwnerBindingV1&,IngameUiResultV1&) noexcept;
}
