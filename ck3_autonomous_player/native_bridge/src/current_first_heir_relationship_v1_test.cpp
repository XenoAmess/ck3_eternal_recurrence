#include "xar_bridge/current_first_heir_relationship_v1.hpp"

#include <cstdlib>
#include <string>

int main() {
  using namespace xar::ck3_11906;
  MarriageHeirRelationshipV1 heir{};
  if (!ValidateCurrentFirstHeirRawRelationshipV1(-1, -1, {}, heir) ||
      !ValidateCurrentFirstHeirRawRelationshipV1(0, 0, {}, heir) ||
      ValidateCurrentFirstHeirRawRelationshipV1(38710, -1, {}, heir) ||
      ValidateCurrentFirstHeirRawRelationshipV1(-1, 38710, {}, heir) ||
      ValidateCurrentFirstHeirRawRelationshipV1(-1, -1, {38710}, heir))
    return EXIT_FAILURE;
  heir.betrothed_character_id = 38710;
  if (!ValidateCurrentFirstHeirRawRelationshipV1(38710, -1, {}, heir))
    return EXIT_FAILURE;
  heir.betrothed_character_id = -1;
  heir.spouse_character_ids = {38710};
  if (!ValidateCurrentFirstHeirRawRelationshipV1(-1, -1, {38710}, heir) ||
      ValidateCurrentFirstHeirRawRelationshipV1(-1, -1,
                                              {38710, 38711}, heir))
    return EXIT_FAILURE;
  heir.spouse_character_ids.clear();
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
  CurrentFirstHeirBetrothalActionabilityReadV1 actionability{};
  auto json = CurrentFirstHeirBetrothalActionabilityJsonV1(actionability);
  if (json.find("\"heir_is_adult\":null") == std::string::npos ||
      json.find("\"complete_can_send\":null") == std::string::npos ||
      json.find("\"generic_costs\":null") == std::string::npos ||
      json.find("\"ready_to_marry_betrothed\":null") == std::string::npos)
    return EXIT_FAILURE;
  actionability.unavailable_reason = "current_heir_has_no_betrothal";
  json = CurrentFirstHeirBetrothalActionabilityJsonV1(actionability);
  if (json.find("\"status\":\"not_applicable\"") == std::string::npos)
    return EXIT_FAILURE;
  actionability.has_betrothal = true;
  actionability.adult_readback_available = true;
  actionability.adult.subject_is_adult = true;
  actionability.adult.candidate_is_adult = false;
  actionability.adult.subject_adult_measure_raw = 17;
  actionability.adult.candidate_adult_measure_raw = 15;
  actionability.adult.subject_adult_threshold_raw = 16;
  actionability.adult.candidate_adult_threshold_raw = 16;
  actionability.unavailable_reason = "current_betrothal_context_unavailable";
  json = CurrentFirstHeirBetrothalActionabilityJsonV1(actionability);
  if (json.find("\"heir_is_adult\":true") == std::string::npos ||
      json.find("\"partner_is_adult\":false") == std::string::npos ||
      json.find("\"ready_to_marry_betrothed\":false") == std::string::npos ||
      json.find("\"complete_can_send\":null") == std::string::npos)
    return EXIT_FAILURE;
  actionability.unavailable_reason = {};
  actionability.final_legality_sampled = true;
  actionability.complete_can_send = false;
  actionability.recipient_acceptance_ready = true;
  actionability.recipient_answer_status_raw = 2;
  actionability.outcome_available = true;
  actionability.adult.predicted_outcome =
      xar::bridge::MarriagePredictedOutcomeV1::betrothal;
  actionability.lineality_available = true;
  actionability.generic_costs_available = true;
  actionability.generic_cost_raw[0] = 700000;
  actionability.generic_cost_raw[1] = -100000;
  json = CurrentFirstHeirBetrothalActionabilityJsonV1(actionability);
  if (json.find("\"status\":\"available\"") == std::string::npos ||
      json.find("\"complete_can_send\":false") == std::string::npos ||
      json.find("\"gold_raw\":700000") == std::string::npos ||
      json.find("\"prestige_raw\":-100000") == std::string::npos ||
      json.find("\"intermediary_character_id\":null") == std::string::npos)
    return EXIT_FAILURE;
  return EXIT_SUCCESS;
}
