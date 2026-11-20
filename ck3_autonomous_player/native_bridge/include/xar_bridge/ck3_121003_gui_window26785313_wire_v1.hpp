#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
namespace xar::ck3_121003::build26785313 {
struct GuiWindowWireRequestV1 {std::string_view request_id;GuiWindowRequestV1 owner_request;};
bool ParseGuiWindowRequestV1(std::string_view,GuiWindowWireRequestV1&) noexcept;
bool GuiWindowRouteEnabledV1(const game::AdapterDescriptor&) noexcept;
std::string SerializeGuiWindowCommandResultV1(std::string_view,const ReadonlyObservation&,const game::AdapterDescriptor&);
}
