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

std::string CurrentFirstHeirBetrothalActionabilityJsonV1(
    const CurrentFirstHeirBetrothalActionabilityReadV1 &read) {
  const bool available = read.unavailable_reason.empty();
  const bool not_applicable =
      read.unavailable_reason == "current_heir_has_no_betrothal";
  std::string json = "{\"status\":\"";
  json += available ? "available" : not_applicable ? "not_applicable" : "unavailable";
  json += "\",\"unavailable_reason\":";
  json += available ? "null" : "\"" + std::string(read.unavailable_reason) + "\"";
  const auto id = [&](std::string_view key, std::int32_t value) {
    json += ",\"" + std::string(key) + "\":";
    json += value > 0 ? std::to_string(value) : "null";
  };
  id("actor_character_id", read.actor_character_id);
  id("heir_character_id", read.heir_character_id);
  id("partner_character_id", read.partner_character_id);
  id("recipient_character_id", read.recipient_character_id);
  id("intermediary_character_id", read.intermediary_character_id);
  const auto boolean = [&](std::string_view key, bool known, bool value) {
    json += ",\"" + std::string(key) + "\":";
    json += known ? (value ? "true" : "false") : "null";
  };
  const auto number = [&](std::string_view key, bool known, std::int64_t value) {
    json += ",\"" + std::string(key) + "\":";
    json += known ? std::to_string(value) : "null";
  };
  boolean("adult_readback_available", true, read.adult_readback_available);
  boolean("heir_is_adult", read.adult_readback_available, read.adult.subject_is_adult);
  boolean("partner_is_adult", read.adult_readback_available, read.adult.candidate_is_adult);
  number("heir_adult_measure_raw", read.adult_readback_available, read.adult.subject_adult_measure_raw);
  number("partner_adult_measure_raw", read.adult_readback_available, read.adult.candidate_adult_measure_raw);
  number("heir_adult_threshold_raw", read.adult_readback_available, read.adult.subject_adult_threshold_raw);
  number("partner_adult_threshold_raw", read.adult_readback_available, read.adult.candidate_adult_threshold_raw);
  boolean("ready_to_marry_betrothed", read.has_betrothal && read.adult_readback_available,
          read.adult.subject_is_adult && read.adult.candidate_is_adult);
  boolean("final_legality_sampled", true, read.final_legality_sampled);
  boolean("complete_can_send", read.final_legality_sampled, read.complete_can_send);
  boolean("recipient_acceptance_ready", true, read.recipient_acceptance_ready);
  number("recipient_ai_accept_raw", read.recipient_acceptance_ready, read.recipient_ai_accept_raw);
  number("recipient_answer_status_raw", read.recipient_acceptance_ready, read.recipient_answer_status_raw);
  json += ",\"generic_costs\":";
  if (!read.generic_costs_available) {
    json += "null";
  } else {
    constexpr std::array<std::string_view, 10> keys{
        "gold_raw", "prestige_raw", "piety_raw", "renown_raw", "influence_raw",
        "herd_raw", "treasury_raw", "treasury_or_gold_raw", "merit_raw", "barter_goods_raw"};
    json += "{\"raw_scale\":100000,\"payer_role\":\"actor\",\"application_timing\":\"on_send\"";
    for (std::size_t index = 0; index < keys.size(); ++index) {
      json += ",\"" + std::string(keys[index]) + "\":" + std::to_string(read.generic_cost_raw[index]);
    }
    json += '}';
  }
  boolean("effective_matrilineal_if_accepted", read.lineality_available,
          read.effective_matrilineal_if_accepted);
  json += ",\"predicted_outcome_if_accepted\":";
  json += !read.outcome_available ? "null" :
      read.adult.predicted_outcome == bridge::MarriagePredictedOutcomeV1::marriage
          ? "\"marriage\"" : "\"betrothal\"";
  json += '}';
  return json;
}

} // namespace xar::ck3_11906
#endif
