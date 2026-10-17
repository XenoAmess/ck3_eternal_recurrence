#pragma once
#include "xar_bridge/religion_ui12004.hpp"
#include "xar_bridge/ingame_ui_navigation_v1.hpp"
namespace xar::ck3_11906 {
bool ReadReligionPresentation12004(const ZhongguoScoreboardNativeEnvironmentV1&,void*handler,
    ck3_12004::religion_ui::Window,IngameUiResultV1&) noexcept;
bool CanOpenReligionPresentation12004(const ZhongguoScoreboardNativeEnvironmentV1&,void*handler,
    ck3_12004::religion_ui::Window,std::uint32_t full_id) noexcept;
bool InvokeReligionPresentation12004(const ZhongguoScoreboardNativeEnvironmentV1&,void*handler,
    ck3_12004::religion_ui::Window,std::uint32_t full_id,bool&attempted) noexcept;
}
