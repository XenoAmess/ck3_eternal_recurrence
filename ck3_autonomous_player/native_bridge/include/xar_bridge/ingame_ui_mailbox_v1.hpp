#pragma once

#include "xar_bridge/frontend_gui_route_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

// The worker's existing typed UI admission and provider-owned context. Both the
// bridge and offline whole-producer recipe use this constructor.
std::string_view PrepareIngameUiMailboxV1(
    const game::GameAdapter &game, const game::Snapshot *previous_snapshot,
    std::string_view payload, std::string_view step,
    std::uint64_t state_revision, std::uint64_t connection_generation,
    std::uintptr_t module_base, MainThreadQueryMailboxV1 &mailbox,
    FrontendGuiRouteMailboxContextV1 &query) noexcept;

std::string IngameUiCommandResultFrameV1(
    std::string_view request_id, const IngameUiRequestV1 &request,
    const IngameUiResultV1 &result, std::uint64_t state_revision);

} // namespace xar::ck3_11906
