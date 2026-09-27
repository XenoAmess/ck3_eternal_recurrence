#pragma once

#include "xar_bridge/ck3_11906.hpp"

#include <cstdint>
#include <vector>

namespace xar::ck3_11906 {
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)

struct CurrentFirstHeirPartnerRelationshipV1 {
  std::int32_t character_id = -1;
  MarriageHeirRelationshipV1 relationship{};

  friend bool operator==(const CurrentFirstHeirPartnerRelationshipV1 &,
                         const CurrentFirstHeirPartnerRelationshipV1 &) = default;
};

// The shared relationship reader filters unresolved raw IDs. This check is
// required before an empty filtered result can be reported as a real empty
// family relation in the private current-heir query.
bool ValidateCurrentFirstHeirRawRelationshipV1(
    std::int32_t raw_betrothed_character_id,
    std::int32_t raw_primary_spouse_character_id,
    const std::vector<std::int32_t> &raw_spouse_character_ids,
    const MarriageHeirRelationshipV1 &filtered) noexcept;

// Pure reciprocity check used by the exact-build native reader. The peer list
// must cover every observed heir partner, including a primary spouse that is
// absent from the spouse array.
bool ValidateCurrentFirstHeirBilateralRelationshipV1(
    std::int32_t heir_character_id,
    const MarriageHeirRelationshipV1 &heir,
    const std::vector<CurrentFirstHeirPartnerRelationshipV1> &partners) noexcept;

#endif
} // namespace xar::ck3_11906
