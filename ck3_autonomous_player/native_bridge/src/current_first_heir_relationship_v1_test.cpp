#include "xar_bridge/current_first_heir_relationship_v1.hpp"

#include <cstdlib>

int main() {
  using namespace xar::ck3_11906;
  MarriageHeirRelationshipV1 heir{};
  std::vector<CurrentFirstHeirPartnerRelationshipV1> peers;
  if (!ValidateCurrentFirstHeirBilateralRelationshipV1(38822, heir, peers))
    return EXIT_FAILURE;
  heir.betrothed_character_id = 38710;
  peers.push_back({38710, {38822, -1, {}}});
  if (!ValidateCurrentFirstHeirBilateralRelationshipV1(38822, heir, peers))
    return EXIT_FAILURE;
  peers[0].relationship.betrothed_character_id = -1;
  if (ValidateCurrentFirstHeirBilateralRelationshipV1(38822, heir, peers))
    return EXIT_FAILURE;
  heir.betrothed_character_id = -1;
  heir.primary_spouse_character_id = 38710;
  peers[0].relationship.primary_spouse_character_id = 38822;
  if (!ValidateCurrentFirstHeirBilateralRelationshipV1(38822, heir, peers))
    return EXIT_FAILURE;
  heir.spouse_character_ids = {38710, 38710};
  if (ValidateCurrentFirstHeirBilateralRelationshipV1(38822, heir, peers))
    return EXIT_FAILURE;
  heir.spouse_character_ids = {38710};
  if (!ValidateCurrentFirstHeirBilateralRelationshipV1(38822, heir, peers))
    return EXIT_FAILURE;
  heir.betrothed_character_id = 38710;
  if (ValidateCurrentFirstHeirBilateralRelationshipV1(38822, heir, peers))
    return EXIT_FAILURE;
  heir.betrothed_character_id = -1;
  peers.clear();
  if (ValidateCurrentFirstHeirBilateralRelationshipV1(38822, heir, peers))
    return EXIT_FAILURE;
  return EXIT_SUCCESS;
}
