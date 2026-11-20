#pragma once
#include "xar_bridge/ck3_121003_gui_controls26785313_v2.hpp"
namespace xar::ck3_121003::build26785313 {
inline constexpr char kGuiControlsRequestSchema267V2[]="ck3.scripted_widget_controls_request.v2";
inline constexpr char kGuiControlsResultSchema267V2[]="ck3.scripted_widget_controls.v2";
inline constexpr char kGuiControlsBackend267V2[]="ck3-1.21.0.3-native-headless-main-thread";
struct GuiControlsWireRequest267V2 {
 std::string_view request_id;
 GuiWindowRequestV1 owner_request;
 std::uint32_t expected_source_rite_id=0xFFFFFFFFU;
 ck3_1210::GuiControlRequestV1 control;
};
bool ParseGuiControlsRequest267V2(std::string_view,GuiControlsWireRequest267V2&) noexcept;
bool GuiControlsRouteEnabled267V2(const game::AdapterDescriptor&,bool activate) noexcept;
std::string SerializeGuiControlsCommandResult267V2(std::string_view,const GuiControlsContext267V2&,const game::AdapterDescriptor&);
} // namespace
