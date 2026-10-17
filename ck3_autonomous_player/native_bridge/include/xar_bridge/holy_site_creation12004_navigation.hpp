#pragma once
#include "xar_bridge/ingame_ui_navigation_v1.hpp"

namespace xar::ck3_11906 {
bool HolySiteCreationUiEnabled12004() noexcept;
bool HolySiteCreationCreateOnceEnabled12004() noexcept;
// Only the existing paused GUI owner route calls this, after its unchanged
// exact-build/TLS/revision/owner guards and (for actions) modal admission.
bool ExecuteHolySiteCreationNavigation12004(
    const ZhongguoScoreboardNativeEnvironmentV1&, void* handler,
    const IngameUiRequestV1&, const game::Snapshot&,
    const MainThreadExecutionStampV1&, const IngameUiGuiOwnerBindingV1&,
    IngameUiResultV1&) noexcept;
}
