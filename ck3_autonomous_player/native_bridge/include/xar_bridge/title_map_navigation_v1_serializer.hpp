#pragma once

#include "xar_bridge/title_map_navigation_v1_camera.hpp"

#include <cstdint>
#include <string>

namespace xar::ck3_11906 {

// Serializes only the strict v1 result object.  The named-pipe bridge owns the
// outer command_result transport envelope and request_id.
std::string SerializeTitleMapNavigationResultV1(
    const game::TitleMapNavigationCommandV1 &command,
    std::uint64_t dispatch_ticket_sequence);

} // namespace xar::ck3_11906
