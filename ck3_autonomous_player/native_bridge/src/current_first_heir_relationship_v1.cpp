#include "xar_bridge/current_first_heir_relationship_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <algorithm>

namespace xar::ck3_11906 {

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
