#pragma once

#include "xar_bridge/faction_targeting_row_observer_v1.hpp"

#include <string>

namespace xar::bridge {

std::string SerializeFactionTargetingRowObserverV1(
    const FactionTargetingRowObserverDiagnosticsV1 &diagnostics);

} // namespace xar::bridge
