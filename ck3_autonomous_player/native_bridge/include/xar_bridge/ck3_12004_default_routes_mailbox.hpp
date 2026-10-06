#pragma once

#include "xar_bridge/loaded_feature_manifest_v1.hpp"
#include "xar_bridge/tactical_daily_sentinel_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_12004 {

// Whole frames used by the actual4 production dispatcher and its focused fixture.
std::string SerializeLoadedFeatureManifestResult12004(
    std::string_view request_id, std::uint64_t query_sequence,
    const game::LoadedFeatureManifestV1 &manifest);
std::string SerializeTacticalDailySentinelResult12004(
    std::string_view request_id, std::string_view step,
    const ck3_11906::TacticalDailySentinelStatusV1 &status);
std::string SerializeTacticalDailySentinelArmResult12004(
    std::string_view request_id, std::string_view step,
    ck3_11906::TacticalDailySentinelArmStatusV1 result,
    const ck3_11906::TacticalDailySentinelStatusV1 &status);
std::string SerializeTacticalDailySentinelCancelResult12004(
    std::string_view request_id, std::string_view step,
    ck3_11906::TacticalDailySentinelCancelStatusV1 result);

} // namespace xar::ck3_12004
