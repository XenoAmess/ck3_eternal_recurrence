#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
namespace xar::ck3_121003::build26785313 {
struct RiteDraftWireRequestV2 {std::string_view request_id;RiteDraftRequestV2 owner_request;};
bool ParseRiteDraftRequestV2(std::string_view,RiteDraftWireRequestV2&) noexcept;
bool RiteDraftRouteEnabledV2(const game::AdapterDescriptor&) noexcept;
std::string SerializeRiteDraftCommandResultV2(std::string_view,const ReadonlyObservation&,const game::AdapterDescriptor&);
}
