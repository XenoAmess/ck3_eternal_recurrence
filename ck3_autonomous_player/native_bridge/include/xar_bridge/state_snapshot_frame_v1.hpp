#pragma once

#include "xar_bridge/game_adapter.hpp"

#include <string>

namespace xar::bridge {

// Existing production state_snapshot formatter with no checkpoint submission.
std::string SerializeStateSnapshotFrameV1(const game::Snapshot &snapshot,
                                        std::uint64_t revision);

} // namespace xar::bridge
