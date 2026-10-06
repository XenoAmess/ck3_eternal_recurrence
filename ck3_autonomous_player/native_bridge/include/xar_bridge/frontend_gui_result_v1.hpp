#pragma once

#include "xar_bridge/frontend_gui_route_v1.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_11906 {

// Shared existing wire producers, extracted from the bridge for whole native
// qualification. They do not select an executable or add a new wire route.
std::string GenericGuiCommandResultFrameV1(
    std::string_view request_id, std::string_view step,
    bool ok, std::string_view status);
std::string FrontendGuiTreeInspectionResultFrameV1(
    std::string_view request_id, std::string_view step,
    const NamedGuiTreeInspectionV1 &inspection);

} // namespace xar::ck3_11906
