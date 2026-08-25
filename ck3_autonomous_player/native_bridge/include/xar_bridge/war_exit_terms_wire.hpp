#pragma once

#include "xar_bridge/game_contract.hpp"

#include <optional>
#include <string>

namespace xar::game {

// Canonical strict available-only claim_cb exit-terms v2 wire serializer.
// Incomplete DTOs have no JSON representation and therefore cannot be
// published as a partial production observation.
std::optional<std::string> SerializeWarTerminationExitTermsV2(
    const WarTerminationExitTermsSnapshot &terms);

} // namespace xar::game
