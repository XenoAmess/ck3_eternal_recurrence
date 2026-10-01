#pragma once

#include "xar_bridge/ck3_12002_family.hpp"

#include <span>
#include <string>
#include <string_view>

namespace xar::ck3_12002 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

inline constexpr std::string_view kFamilyAllianceProjectionWireStepV1 =
    "query-first-heir-candidate-alliance-projection-v1-private";
inline constexpr std::string_view kFamilyChildValueWireStepV1 =
    "query-player-child-marriage-value-v1-private";

struct FamilyAllianceWireRowV1 {
  game::ArrangeMarriageFamilyCandidateV1 observed{};
  ck3_11906::MarriageCandidateAlliancePrivateReadV1 read{};
};

// Pure wire rendering extracted from the existing bridge serializer. Callers
// supply actual provider rows; version identity remains the adapter envelope.
std::string SerializeFamilyAllianceFrameV1(std::string_view request_id,
    std::uint64_t revision, std::uint64_t legality_query_sequence,
    std::span<const FamilyAllianceWireRowV1> rows,
    std::string_view step = kFamilyAllianceProjectionWireStepV1);

#endif
} // namespace xar::ck3_12002
