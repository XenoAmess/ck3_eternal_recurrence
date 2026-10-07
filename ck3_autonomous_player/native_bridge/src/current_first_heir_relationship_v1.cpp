#include "xar_bridge/current_first_heir_relationship_v1.hpp"

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include <algorithm>

namespace xar::ck3_11906 {
namespace {
void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}
std::string_view CurrentFirstHeirRelationshipFailureKeyV1(
    CurrentFirstHeirRelationshipFailureV1 failure) {
  using Failure = CurrentFirstHeirRelationshipFailureV1;
  switch (failure) {
  case Failure::none: return "none";
  case Failure::frame_changed: return "frame_changed";
  case Failure::heir_unavailable: return "heir_unavailable";
  case Failure::relationship_unavailable: return "relationship_unavailable";
  case Failure::partner_unavailable: return "partner_unavailable";
  case Failure::bilateral_inconsistent: return "bilateral_inconsistent";
  }
  return "unknown";
}

template <typename T>
void AppendOptionalNumber(std::string &json, const std::optional<T> &value) {
  json += value.has_value() ? std::to_string(*value) : "null";
}

void AppendOptionalBoolean(std::string &json, const std::optional<bool> &value) {
  json += value.has_value() ? (*value ? "true" : "false") : "null";
}

void AppendDescendantLineage(
    std::string &json, const CurrentFirstHeirDescendantLineageV1 &lineage) {
  json += "{\"status\":";
  AppendJsonString(json, lineage.available ? "available" : "unavailable");
  json += ",\"unavailable_reason\":";
  if (lineage.available) json += "null";
  else AppendJsonString(json, lineage.unavailable_reason);
  json += ",\"house_id_raw\":";
  json += lineage.available ? std::to_string(lineage.house_id_raw) : "null";
  json += ",\"dynasty_id_raw\":";
  json += lineage.available ? std::to_string(lineage.dynasty_id_raw) : "null";
  json += '}';
}

std::string CurrentFirstHeirDescendantsJsonV1(
    const CurrentFirstHeirDescendantsReadV1 &read,
    std::uint64_t native_revision) {
  using Status = CurrentFirstHeirDescendantsStatusV1;
  std::string json = "{\"status\":";
  AppendJsonString(json, read.status == Status::available ? "available" :
      read.status == Status::partial ? "partial" : "unavailable");
  json += ",\"unavailable_reason\":";
  if (read.status == Status::available) json += "null";
  else AppendJsonString(json, read.unavailable_reason);
  json += ",\"native_revision\":" + std::to_string(native_revision);
  json += ",\"played_character_id\":";
  json += read.played_character_id > 0
      ? std::to_string(read.played_character_id) : "null";
  json += ",\"heir_character_id\":";
  json += read.heir_character_id > 0
      ? std::to_string(read.heir_character_id) : "null";
  json += ",\"date_raw\":";
  AppendOptionalNumber(json, read.date_raw);
  json += ",\"family_present\":";
  AppendOptionalBoolean(json, read.family_present);
  json += ",\"native_child_count_raw\":";
  AppendOptionalNumber(json, read.native_child_count_raw);
  json += ",\"data_pointer_present\":";
  AppendOptionalBoolean(json, read.data_pointer_present);
  json += ",\"roster_complete\":";
  json += read.roster_complete ? "true" : "false";
  json += ",\"played_lineage\":";
  AppendDescendantLineage(json, read.played_lineage);
  json += ",\"heir_lineage\":";
  AppendDescendantLineage(json, read.heir_lineage);
  json += ",\"rows\":[";
  for (std::size_t index = 0; index < read.rows.size(); ++index) {
    if (index != 0) json += ',';
    const auto &row = read.rows[index];
    json += "{\"occurrence_index\":" + std::to_string(row.occurrence_index);
    json += ",\"raw_character_id\":" + std::to_string(row.raw_character_id);
    json += ",\"generation_valid\":";
    json += row.generation_valid ? "true" : "false";
    json += ",\"alive\":";
    AppendOptionalBoolean(json, row.alive);
    json += ",\"parent_family_present\":";
    AppendOptionalBoolean(json, row.parent_family_present);
    json += ",\"parent_0_character_id_raw\":";
    AppendOptionalNumber(json, row.parent_0_character_id_raw);
    json += ",\"parent_4_character_id_raw\":";
    AppendOptionalNumber(json, row.parent_4_character_id_raw);
    json += ",\"child_of_heir\":";
    AppendOptionalBoolean(json, row.child_of_heir);
    json += ",\"lineage\":";
    AppendDescendantLineage(json, row.lineage);
    json += '}';
  }
  json += "]}";
  return json;
}
} // namespace

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
  boolean("matrilineal_option_selected", read.matrilineal_option_selected.has_value(),
          read.matrilineal_option_selected.value_or(false));
  json += ",\"native_child_house_preview\":{\"status\":";
  AppendJsonString(json, not_applicable ? "not_applicable" :
      read.native_child_house_preview_available ? "available" : "unavailable");
  json += ",\"reason\":";
  AppendJsonString(json, not_applicable ? read.unavailable_reason :
                   read.native_child_house_preview_reason);
  id("subject_character_id", read.heir_character_id);
  id("candidate_character_id", read.partner_character_id);
  json += ",\"requested_matrilineal_option\":false";
  if (read.native_child_house_preview_available) {
    boolean("selected_matrilineal_option", true,
            read.matrilineal_option_selected.value_or(false));
    boolean("effective_matrilineal_if_accepted", true,
            read.effective_matrilineal_if_accepted);
    boolean("complete_can_send", true, read.complete_can_send);
    id("native_selected_parent_character_id", read.native_selected_parent_character_id);
    number("house_id", read.native_preview_lineage.house_id >= 0,
           read.native_preview_lineage.house_id);
    number("dynasty_id", read.native_preview_lineage.dynasty_id >= 0,
           read.native_preview_lineage.dynasty_id);
  }
  json += '}';
  json += ",\"predicted_outcome_if_accepted\":";
  json += !read.outcome_available ? "null" :
      read.adult.predicted_outcome == bridge::MarriagePredictedOutcomeV1::marriage
          ? "\"marriage\"" : "\"betrothal\"";
  json += '}';
  return json;
}

std::string CurrentFirstHeirRelationshipResultJsonV1(
    std::string_view request_id, std::uint64_t native_revision,
    std::int32_t heir_character_id,
    const CurrentFirstHeirRelationshipReadV1 &read,
    std::string_view override_unavailable_reason) {
  const bool available = override_unavailable_reason.empty() &&
      read.failure == CurrentFirstHeirRelationshipFailureV1::none;
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, "query-current-first-heir-relationship-v1-private");
  result += ",\"accepted\":true,\"private_build\":true,"
            "\"read_only\":true,\"advertised\":false,\"status\":";
  AppendJsonString(result, available ? "available" : "unavailable");
  result += ",\"native_revision\":" + std::to_string(native_revision);
  result += ",\"subject_source\":\"public_campaign_root_primary_first_heir\","
            "\"heir_character_id\":" + std::to_string(heir_character_id);
  result += ",\"unavailable_reason\":";
  if (available) {
    result += "null";
  } else {
    AppendJsonString(result, override_unavailable_reason.empty()
        ? CurrentFirstHeirRelationshipFailureKeyV1(read.failure)
        : override_unavailable_reason);
  }
  result += ",\"bilateral_verified\":";
  result += available ? "true" : "false";
  result += ",\"betrothed_character_id\":";
  result += available && read.relationship.betrothed_character_id > 0
      ? std::to_string(read.relationship.betrothed_character_id) : "null";
  result += ",\"primary_spouse_character_id\":";
  result += available && read.relationship.primary_spouse_character_id > 0
      ? std::to_string(read.relationship.primary_spouse_character_id) : "null";
  result += ",\"spouse_character_ids\":";
  if (!available) {
    result += "null";
  } else {
    result += '[';
    for (std::size_t index = 0; index < read.relationship.spouse_character_ids.size(); ++index) {
      if (index != 0) result += ',';
      result += std::to_string(read.relationship.spouse_character_ids[index]);
    }
    result += ']';
  }
  result += ",\"betrothal_actionability\":";
  result += CurrentFirstHeirBetrothalActionabilityJsonV1(read.betrothal_actionability);
  if (read.descendants.has_value()) {
    result += ",\"current_first_heir_descendants_v1\":";
    result += CurrentFirstHeirDescendantsJsonV1(*read.descendants, native_revision);
  }
  result += "}}";
  return result;
}

} // namespace xar::ck3_11906
#endif
