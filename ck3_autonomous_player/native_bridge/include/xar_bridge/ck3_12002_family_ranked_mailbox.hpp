#pragma once

#include "xar_bridge/game_adapter.hpp"

#include "xar_bridge/ck3_12002_family_ranked.hpp"
#include "xar_bridge/marriage_candidate_internal_route_v1.hpp"

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

bool ExecuteFamilyRankedMailboxV1(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;

bridge::MarriageCandidateWorkerReadResultV1 ReadFamilyRankedOnApplicationMainV1(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t revision, std::uint32_t limit,
    std::uint32_t candidate_filter,
    bridge::MarriageCandidateInternalQueryV1 &) noexcept;

#endif
} // namespace xar::ck3_12002
