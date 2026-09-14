#pragma once

#include "xar_bridge/faction_targeting_row_probe_v1.hpp"

#include <string>

namespace xar::bridge {

// Produces the private wire candidate consumed by the later shared bridge
// wiring package. The payload owns only stable scalar identities.
std::string SerializeFactionTargetingRowProbeV1(
    const FactionTargetingRowProbeResultV1 &result);

} // namespace xar::bridge
