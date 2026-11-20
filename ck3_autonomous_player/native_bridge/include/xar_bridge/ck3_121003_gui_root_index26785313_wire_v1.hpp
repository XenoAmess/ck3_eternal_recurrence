#pragma once
#include "xar_bridge/ck3_121003_readonly26785313_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <string>

namespace xar::ck3_121003::build26785313 {
inline constexpr char kGuiRootIndexStepV1[]="query-scripted-gui-root-index-v1";
inline constexpr char kGuiRootIndexRequestSchemaV1[]="ck3.scripted_gui_root_index_request.v1";
inline constexpr char kGuiRootIndexSchemaV1[]="ck3.scripted_gui_root_index.v1";
inline constexpr char kGuiRootIndexBackendV1[]="ck3-1.21.0.3-native-headless-main-thread";
struct GuiRootIndexWireRequestV1 {
  std::string_view request_id;
  GuiRootIndexRequestV1 owner_request;
};
bool ParseGuiRootIndexRequestV1(std::string_view,GuiRootIndexWireRequestV1&) noexcept;
bool GuiRootIndexRouteEnabledV1(const game::AdapterDescriptor&) noexcept;
std::string SerializeGuiRootIndexCommandResultV1(std::string_view,
    const ReadonlyObservation&,const game::AdapterDescriptor&);
} // namespace xar::ck3_121003::build26785313
