#include "xar_bridge/current_first_heir_relationship_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <algorithm>

namespace xar::ck3_11906 {

bool ValidateCurrentFirstHeirRawRelationshipV1(
    std::int32_t raw_betrothed_character_id,
    std::int32_t raw_primary_spouse_character_id,
    const std::vector<std::int32_t> &raw_spouse_character_ids,
    const MarriageHeirRelationshipV1 &filtered) noexcept {
  const auto scalar_matches = [](std::int32_t raw, std::int32_t observed) {
    return (raw == -1 || raw == 0) ? observed == -1
                                   : raw > 0 && observed == raw;
  };
  if (!scalar_matches(raw_betrothed_character_id,
                      filtered.betrothed_character_id) ||
      !scalar_matches(raw_primary_spouse_character_id,
                      filtered.primary_spouse_character_id) ||
      raw_spouse_character_ids != filtered.spouse_character_ids)
    return false;
  return std::all_of(raw_spouse_character_ids.begin(),
                     raw_spouse_character_ids.end(),
                     [](std::int32_t id) { return id > 0; });
}

bool ValidateCurrentFirstHeirBilateralRelationshipV1(
    std::int32_t heir_character_id,
    const MarriageHeirRelationshipV1 &heir,
    const std::vector<CurrentFirstHeirPartnerRelationshipV1> &partners) noexcept {
  if (heir_character_id <= 0 || heir.betrothed_character_id == 0 ||
      heir.primary_spouse_character_id == 0)
    return false;
  std::vector<std::int32_t> expected = heir.spouse_character_ids;
  for (const auto id : expected) {
    if (id <= 0 || id == heir_character_id ||
        std::count(expected.begin(), expected.end(), id) != 1)
      return false;
  }
  const auto add = [&](std::int32_t id) {
    if (id > 0 && std::find(expected.begin(), expected.end(), id) == expected.end())
      expected.push_back(id);
  };
  add(heir.primary_spouse_character_id);
  add(heir.betrothed_character_id);
  if (heir.betrothed_character_id > 0 &&
      (heir.betrothed_character_id == heir.primary_spouse_character_id ||
       std::find(heir.spouse_character_ids.begin(), heir.spouse_character_ids.end(),
                 heir.betrothed_character_id) != heir.spouse_character_ids.end()))
    return false;
  if (expected.size() != partners.size()) return false;
  for (const auto &partner : partners) {
    if (partner.character_id <= 0 || partner.character_id == heir_character_id ||
        std::find(expected.begin(), expected.end(), partner.character_id) ==
            expected.end())
      return false;
    if (std::count_if(partners.begin(), partners.end(), [&](const auto &row) {
          return row.character_id == partner.character_id;
        }) != 1)
      return false;
    if (partner.character_id == heir.betrothed_character_id) {
      if (partner.relationship.betrothed_character_id != heir_character_id)
        return false;
    } else if (partner.relationship.primary_spouse_character_id !=
                   heir_character_id &&
               std::find(partner.relationship.spouse_character_ids.begin(),
                         partner.relationship.spouse_character_ids.end(),
                         heir_character_id) ==
                   partner.relationship.spouse_character_ids.end()) {
      return false;
    }
  }
  return true;
}

} // namespace xar::ck3_11906
#endif
