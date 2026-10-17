#pragma once
#include "xar_bridge/ck3_12004_holy_site_ui.hpp"
namespace xar::ck3_11906 {
// Only opens the original parameterized decision detail. No business adoption,
// arbitrary child path or caller-provided callback is exposed.
bool OpenHolySiteAdoptionEntry12004(const ZhongguoScoreboardNativeEnvironmentV1 &,
    void *handler, std::uint32_t full_id, void *gui_context, IngameUiResultV1 &) noexcept;
bool OpenHolySiteDecisionEntry12004(const ZhongguoScoreboardNativeEnvironmentV1 &,
    void *handler, std::uint32_t full_id, void *gui_context,
    ck3_12004::religion::holy_site::DecisionAction,IngameUiResultV1 &) noexcept;
}
