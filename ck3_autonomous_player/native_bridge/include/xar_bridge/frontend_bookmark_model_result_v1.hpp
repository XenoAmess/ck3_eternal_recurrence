#pragma once

#include "xar_bridge/frontend_bookmark_model_probe_v1.hpp"

#include <string>
#include <string_view>

namespace xar::ck3_11906 {

// Shared by the production private command and its native whole-frame fixture.
std::string FrontendBookmarkModelPrivateResultFrameV1(
    std::string_view request_id, std::string_view step,
    const FrontendBookmarkModelProbeV1 &probe);

} // namespace xar::ck3_11906
