#pragma once
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
namespace xar::ck3_11906 {
// Exact4 original typed GUI only. No business adoption or arbitrary dispatcher.
bool ReadHolySiteUi12004(const ZhongguoScoreboardNativeEnvironmentV1 &, void *handler,
    IngameUiResultV1 &) noexcept;
bool HolySiteUiCanOpen12004(const ZhongguoScoreboardNativeEnvironmentV1 &, void *handler,
    std::uint32_t full_id) noexcept;
bool InvokeHolySiteUi12004(const ZhongguoScoreboardNativeEnvironmentV1 &, void *handler,
    std::uint32_t full_id, bool &attempted) noexcept;
// A provider-private identity binding for the original adopted-decision GUI.
bool ResolveHolySiteUiSelection12004(const ZhongguoScoreboardNativeEnvironmentV1 &,
    void *handler, std::uint32_t full_id, void *&window, void *&root) noexcept;
}
