#include "activity_feast_stage5_start_private_transport_v1.hpp"

#include <array>
#include <string>

namespace xar::ck3_11906 {
namespace {

void AppendIdentities(std::string &payload,
                      const std::array<bridge::ActivityHostedIdentityV1, 64> &ids,
                      std::uint32_t count) {
  payload += "[";
  for (std::uint32_t index = 0; index < count; ++index) {
    if (index != 0) payload += ",";
    payload += "{\"activity_id\":" + std::to_string(ids[index].activity_id) +
               ",\"host_character_id\":" +
               std::to_string(ids[index].host_character_id) +
               ",\"activity_type_key\":\"";
    payload.append(ids[index].type_key.data(), ids[index].type_key_size);
    payload += "\"";
    if (ids[index].terminal_flags_observed) {
      payload += ",\"terminal_flags_observed\":true,\"native_completed\":";
      payload += ids[index].native_completed ? "true" : "false";
      payload += ",\"native_invalidated\":";
      payload += ids[index].native_invalidated ? "true" : "false";
    }
    payload += "}";
  }
  payload += "]";
}

void AppendBalances(std::string &payload,
                    const bridge::ActivityFeastResourceBalancesV1 &balances) {
  payload += "\"balances\":{";
  for (std::size_t index = 0; index < bridge::kActivityFeastCostKeysV1.size();
       ++index) {
    if (index != 0) payload += ",";
    payload += "\"" + std::string(bridge::kActivityFeastCostKeysV1[index]) +
               "\":{";
    payload += "\"available\":";
    payload += balances.available[index] ? "true" : "false";
    payload += ",\"raw\":";
    payload += balances.available[index]
                   ? std::to_string(balances.raw[index]) : "null";
    payload += "}";
  }
  payload += "}";
}

void AppendOutcomeValues(std::string &payload,
                         const bridge::FeastOutcomeValuesV1 &values) {
  if (!values.prestige_available && !values.stress_available &&
      !values.reveler_available && !values.reveler_xp_available)
    return;
  payload += ",\"outcome_values\":{\"prestige_raw\":";
  payload += values.prestige_available ? std::to_string(values.prestige_raw)
                                      : "null";
  payload += ",\"stress_points\":";
  payload += values.stress_available ? std::to_string(values.stress_points)
                                    : "null";
  payload += ",\"reveler_present\":";
  payload += values.reveler_available
                 ? values.reveler_present ? "true" : "false"
                 : "null";
  payload += ",\"reveler_xp_raw\":";
  payload += values.reveler_xp_available
                 ? std::to_string(values.reveler_xp_raw) : "null";
  payload += "}";
}

#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
void AppendOrdinaryGuestRoute(
    std::string &payload, const bridge::ActivityFeastStage5StartSnapshotV1 &input) {
  const auto &route = input.ordinary_guest;
  const auto &candidate = route.candidate;
  const bool rule_observed =
      route.rule_status == bridge::ActivityFeastGuestRuleStatusV1::observed_active ||
      route.rule_status == bridge::ActivityFeastGuestRuleStatusV1::observed_inactive;
  const bool provenance_observed =
      route.provenance_status == bridge::ActivityGuestRuleProvenanceStatusV1::observed;
  payload += ",\"ordinary_guest_route\":{\"status\":\"";
  payload += bridge::IsActivityFeastOrdinaryGuestRouteObservedV1(input)
                 ? "observed" : "unavailable";
  payload += "\",\"authored_rule_key\":\"" + std::string(route.authored_rule_key) +
             "\",\"candidate_status\":\"";
  payload += bridge::ActivityFeastGuestCandidateStatusKeyV1(candidate.status);
  payload += "\",\"rule_status\":\"";
  payload += bridge::ActivityFeastGuestRuleStatusKeyV1(route.rule_status);
  payload += "\",\"provenance_status\":\"";
  payload += bridge::ActivityGuestRuleProvenanceStatusKeyV1(route.provenance_status);
  payload += "\",\"rule_active\":";
  payload += rule_observed ? route.rule_active ? "true" : "false" : "null";
  payload += ",\"native_key_hash\":";
  payload += rule_observed ? std::to_string(route.native_key_hash) : "null";
  payload += ",\"provenance_key_hash\":";
  payload += provenance_observed ? std::to_string(route.provenance_key_hash) : "null";
  payload += ",\"provenance_refresh_sequence\":";
  payload += provenance_observed ? std::to_string(route.provenance_refresh_sequence) : "null";
  payload += ",\"raw_rule_character_count\":";
  payload += provenance_observed ? std::to_string(route.raw_rule_character_count) : "null";
  payload += ",\"filtered_rule_character_count\":";
  payload += provenance_observed ? std::to_string(route.filtered_rule_character_count) : "null";
  payload += ",\"candidate_membership\":";
  payload += provenance_observed ? route.candidate_membership ? "true" : "false" : "null";
  payload += ",\"candidate\":";
  if (candidate.status == bridge::ActivityFeastGuestCandidateStatusV1::observed) {
    std::string fingerprint = "0x0000000000000000";
    constexpr char hex[] = "0123456789abcdef";
    for (std::size_t index = 0; index < 16; ++index)
      fingerprint[17 - index] = hex[(candidate.source_fingerprint >> (index * 4)) & 15];
    payload += "{\"character_id\":" + std::to_string(candidate.character_id) +
               ",\"planner_join_raw\":" + std::to_string(candidate.planner_join_raw) +
               ",\"travel_days\":" + std::to_string(candidate.travel_days) +
               ",\"arrival_raw\":" + std::to_string(candidate.arrival_raw) +
               ",\"planned_start_raw\":" + std::to_string(candidate.planned_start_raw) +
               ",\"snapshot_revision\":" + std::to_string(candidate.frame.revision) +
               ",\"date_raw\":" + std::to_string(candidate.frame.date_raw) +
               ",\"actor_character_id\":" + std::to_string(candidate.frame.actor_character_id) +
               ",\"normal_refresh_sequence\":" + std::to_string(candidate.normal_refresh_sequence) +
               ",\"source_fingerprint\":\"" + fingerprint + "\",\"native_filtered\":";
    payload += candidate.native_filtered ? "true" : "false";
    payload += "}";
  } else {
    payload += "null";
  }
  payload += ",\"qualified\":";
  payload += bridge::IsActivityFeastOrdinaryGuestRouteQualifiedV1(input) ? "true" : "false";
  payload += "}";
}
#endif

} // namespace

std::string SerializeActivityFeastStage5PrivateV1(
    const ActivityFeastStage5PrivateQueryV1 &query) {
  if (!query.completed || query.frame_changed) return {};
  if (query.mode == ActivityFeastStage5PrivateModeV1::hosted_post) {
    if (!query.post.hosted_identities_observed) return {};
    const auto &post = query.post;
    std::string payload =
        "{\"schema\":\"activity-feast-hosted-post-private-read-v1\",";
    payload += "\"snapshot_revision\":" +
               std::to_string(post.frame.revision) +
               ",\"date_raw\":" + std::to_string(post.frame.date_raw) +
               ",\"actor_character_id\":" +
               std::to_string(post.frame.actor_character_id) + ",";
    AppendBalances(payload, post.balances);
    payload += ",\"hosted_activities\":";
    AppendIdentities(payload, post.hosted, post.hosted_count);
    AppendOutcomeValues(payload, post.outcome_values);
    payload += ",\"read_only\":true,\"advertised\":false}";
    return payload;
  }
  if (!query.inputs.four_costs_observed ||
      !query.inputs.hosted_identities_observed)
    return {};
  const auto &input = query.inputs;
  std::string payload =
      "{\"schema\":\"activity-feast-stage5-start-inputs-private-v1\",";
  payload += "\"snapshot_revision\":" +
             std::to_string(input.frame.revision) +
             ",\"date_raw\":" + std::to_string(input.frame.date_raw) +
             ",\"actor_character_id\":" +
             std::to_string(input.frame.actor_character_id) +
             ",\"activity_key\":\"activity_feast\","
             "\"selected_option_key\":\"feast_type_generic\","
             "\"planning_stage\":5,\"scale\":100000,";
  payload += "\"normal_refresh_sequence\":" +
             std::to_string(input.normal_cost_refresh_sequence) +
             ",\"final_can_start\":" +
             std::string(input.final_can_start ? "true" : "false") +
             ",\"resources\":{";
  for (std::size_t index = 0; index < bridge::kActivityFeastCostKeysV1.size();
       ++index) {
    if (index != 0) payload += ",";
    payload += "\"" + std::string(bridge::kActivityFeastCostKeysV1[index]) +
               "\":{\"resource_index\":" +
               std::to_string(input.cost_resource_indices[index]) +
               ",\"configured_cost_raw\":" +
               std::to_string(input.cost_raw[index]) + "}";
  }
  payload += "},";
  AppendBalances(payload, input.balances);
  payload += ",\"hosted_activities\":";
  AppendIdentities(payload, input.hosted, input.hosted_count);
  AppendOutcomeValues(payload, input.outcome_values);
  payload += ",\"guest_join_status\":\"";
  payload += bridge::ActivityFeastGuestJoinStatusKeyV1(query.guest_status);
  payload += "\",\"selected_nonhost_count\":";
  payload += query.guest_status == bridge::ActivityFeastGuestJoinStatusV1::observed
                 ? std::to_string(query.selected_nonhost_count) : "null";
  payload += ",\"positive_join_count\":";
  payload += query.guest_status == bridge::ActivityFeastGuestJoinStatusV1::observed
                 ? std::to_string(query.positive_join_count) : "null";
  payload += ",\"timely_positive_join_count\":";
  payload += query.guest_status == bridge::ActivityFeastGuestJoinStatusV1::observed
                 ? std::to_string(query.timely_positive_join_count) : "null";
  payload += ",\"arrival_time_observed\":";
  payload += query.guest_status == bridge::ActivityFeastGuestJoinStatusV1::observed &&
                     query.arrival_time_observed ? "true" : "false";
  payload += ",\"native_guest_route_qualified\":";
  payload += query.guest_route_qualified ? "true" : "false";
#if defined(XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_GUEST_RULE_PROVENANCE_PRIVATE_V1)
  AppendOrdinaryGuestRoute(payload, input);
#endif
  payload += ",\"read_only\":";
  payload += query.mode == ActivityFeastStage5PrivateModeV1::start_inputs
                 ? "true" : "false";
  payload += ",\"advertised\":false}";
  return payload;
}

} // namespace xar::ck3_11906
