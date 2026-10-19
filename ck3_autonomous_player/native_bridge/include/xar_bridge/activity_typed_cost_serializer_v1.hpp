#pragma once
#include "xar_bridge/activity_typed_full_cost_v1.hpp"
#include <string>

namespace xar::bridge {
// Observed-only typed quote; failure or inconsistent evidence returns empty.
// Serializes bounded values and logical identities only, never native addresses.
std::string SerializeActivityTypedPlannerFullCostV1(
    const ActivityTypedFullCostResultV1 &result);
} // namespace xar::bridge
