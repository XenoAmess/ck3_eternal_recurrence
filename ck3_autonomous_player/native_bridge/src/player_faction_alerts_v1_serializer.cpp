#include "xar_bridge/player_faction_alerts_v1.hpp"

#include <algorithm>
#include <charconv>
#include <cstdint>
#include <limits>
#include <string>
#include <string_view>
#include <unordered_set>

namespace xar::ck3_11906 {
namespace {

constexpr std::int32_t kFixedPointScale = 100'000;

void AppendJsonString(std::string &output, std::string_view value) {
  output.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20) {
        constexpr char hex[] = "0123456789ABCDEF";
        output += "\\u00";
        output.push_back(hex[(character >> 4U) & 0x0FU]);
        output.push_back(hex[character & 0x0FU]);
      } else {
        output.push_back(static_cast<char>(character));
      }
    }
  }
  output.push_back('"');
}

template <typename Integer>
std::string Number(Integer value) {
  char buffer[64]{};
  const auto result = std::to_chars(buffer, buffer + sizeof(buffer), value);
  return result.ec == std::errc{} ? std::string(buffer, result.ptr)
                                  : std::string{};
}

bool StableKey(std::string_view value) noexcept {
  if (value.empty()) return false;
  for (const char character : value) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

bool ValidFixedPoint(const game::PlayerFactionFixedPointV1 &value,
                     bool nonnegative) noexcept {
  return value.scale == kFixedPointScale && (!nonnegative || value.raw >= 0);
}

bool PositiveUnique(const std::vector<std::int32_t> &values) {
  std::unordered_set<std::int32_t> seen;
  for (const auto value : values) {
    if (value <= 0 || !seen.insert(value).second) return false;
  }
  return true;
}

bool StrictlyIncreasing(const std::vector<std::int32_t> &values) {
  return PositiveUnique(values) &&
         std::is_sorted(values.begin(), values.end()) &&
         std::adjacent_find(values.begin(), values.end()) == values.end();
}

bool ValidCountyObservationStatus(std::string_view status) noexcept {
  return status == "available" || status == "unavailable" ||
         status == "unsupported_build";
}

bool ValidCountyObservations(const game::PlayerTargetingFactionV1 &row) {
  std::int32_t previous_title_id = 0;
  for (const auto &county : row.county_member_observations) {
    if (county.county_title_id <= previous_title_id ||
        !std::binary_search(row.county_member_title_ids.begin(),
                            row.county_member_title_ids.end(),
                            county.county_title_id) ||
        (county.capital_province_id.has_value() &&
         county.capital_province_id.value() <= 0) ||
        (county.holder_character_id.has_value() &&
         county.holder_character_id.value() <= 0) ||
        !ValidCountyObservationStatus(county.opinion_status) ||
        !ValidCountyObservationStatus(county.native_final_status)) {
      return false;
    }
    previous_title_id = county.county_title_id;
  }
  return true;
}

bool ValidTargetingRow(const game::PlayerTargetingFactionV1 &row,
                       std::int32_t player_character_id) {
  if (row.faction_id <= 0 || row.target_character_id != player_character_id ||
      !StableKey(row.faction_type_key) ||
      (row.leader_character_id.has_value() &&
       row.leader_character_id.value() <= 0) ||
      (!row.leader_character_id.has_value() && row.leader_is_human) ||
      (row.special_character_id.has_value() &&
       row.special_character_id.value() <= 0) ||
      (row.special_title_id.has_value() &&
       row.special_title_id.value() <= 0) ||
      (row.faction_war_id.has_value() && row.faction_war_id.value() <= 0) ||
      (!row.faction_at_war && row.faction_war_id.has_value()) ||
      !ValidFixedPoint(row.power, true) ||
      !ValidFixedPoint(row.power_threshold, true) ||
      !ValidFixedPoint(row.discontent, true) ||
      !ValidFixedPoint(row.discontent_per_month, false) ||
      (row.months_until_max_discontent.has_value() &&
       row.months_until_max_discontent.value() < 0) ||
      !StrictlyIncreasing(row.character_member_ids) ||
      !StrictlyIncreasing(row.county_member_title_ids) ||
      !ValidCountyObservations(row) ||
      !StableKey(row.danger_reason)) {
    return false;
  }
  bool expected_dangerous = false;
  std::string_view expected_reason;
  if (row.leader_is_human) {
    expected_dangerous = true;
    expected_reason = "human_faction_leader";
  } else if (row.faction_type_key == "peasant_faction") {
    expected_dangerous = row.months_until_max_discontent.has_value() &&
                         row.months_until_max_discontent.value() <= 12;
    expected_reason = expected_dangerous
                          ? "peasant_ultimatum_within_12_months"
                          : "peasant_ultimatum_not_within_12_months";
  } else {
    expected_dangerous = row.discontent_per_month.raw > 0;
    expected_reason = expected_dangerous
                          ? "non_peasant_discontent_increasing"
                          : "non_peasant_discontent_not_increasing";
  }
  return row.dangerous_by_stock_rule == expected_dangerous &&
         row.danger_reason == expected_reason;
}

bool ValidCountyExposure(const game::PlayerFactionCountyExposureV1 &row,
                         std::int32_t player_character_id) {
  return row.county_title_id > 0 && row.faction_id > 0 &&
         row.target_character_id > 0 &&
         row.target_character_id != player_character_id &&
         row.faction_type_key == "populist_faction" &&
         ValidFixedPoint(row.power, true) &&
         ValidFixedPoint(row.power_threshold, true) &&
         row.power.raw > row.power_threshold.raw &&
         row.dangerous_by_stock_rule &&
         row.danger_reason ==
             "player_county_in_powerful_liege_targeting_populist_faction";
}

std::string_view WireUnavailableReason(
    game::PlayerFactionAlertsFailureReasonV1 reason) noexcept {
  using enum game::PlayerFactionAlertsFailureReasonV1;
  switch (reason) {
  case exact_build_not_admitted:
    return "unsupported_build";
  case native_reader_not_frozen:
  case offline_fixture_source_not_authorized:
  case fixture_source_failed:
  case reader_exception:
    return "reader_not_implemented";
  case application_main_thread_required:
    return "requires_application_main";
  case frame_capture_failed:
  case paused_player_unavailable:
    return "requires_paused";
  case invalid_request:
  case snapshot_revision_mismatch:
  case targeting_count_unavailable:
  case identity_round_trip_failed:
  case identity_drift:
  case same_frame_drift:
  case native_sample_drift:
  case schema_invariant_failed:
    return "state_changed";
  case none:
    break;
  }
  return {};
}

bool ValidAvailable(const game::PlayerFactionAlertsV1 &value) {
  if (value.snapshot_revision == 0 || !value.date_raw.has_value() ||
      !value.player_character_id.has_value() ||
      value.player_character_id.value() <= 0 ||
      !value.targeting_faction_count.has_value() ||
      value.targeting_faction_count.value() < 0 ||
      value.unavailable_reason !=
          game::PlayerFactionAlertsFailureReasonV1::none ||
      !value.readiness.identity_ready ||
      !value.readiness.targeting_count_ready ||
      !value.readiness.same_frame_ready ||
      value.readiness.exact_ultimatum_timing_ready ||
      value.planner_projection.exact_ultimatum_timing_ready) {
    return false;
  }
  if (value.readiness.targeting_rows_ready) {
    if (!value.readiness.stock_dangerous_predicate_ready ||
        value.component_unavailable_reasons.targeting_rows.has_value() ||
        static_cast<std::size_t>(value.targeting_faction_count.value()) !=
            value.targeting_factions.size()) {
      return false;
    }
  } else if (!value.targeting_factions.empty() ||
             value.readiness.stock_dangerous_predicate_ready ||
             value.component_unavailable_reasons.targeting_rows !=
                 kPlayerFactionAlertsV1TargetingRowsUnavailableReason) {
    return false;
  }
  if (value.readiness.county_exposure_ready) {
    if (value.component_unavailable_reasons.county_exposure.has_value()) {
      return false;
    }
  } else if (!value.county_exposures.empty() ||
             value.component_unavailable_reasons.county_exposure !=
                 kPlayerFactionAlertsV1CountyExposureUnavailableReason) {
    return false;
  }
  const bool expected_alert_ready =
      value.readiness.targeting_rows_ready &&
      value.readiness.county_exposure_ready &&
      value.readiness.stock_dangerous_predicate_ready;
  if (value.readiness.alert_ready != expected_alert_ready) return false;

  std::unordered_set<std::int32_t> faction_ids;
  std::int32_t previous_faction_id = 0;
  std::vector<std::int32_t> expected_dangerous;
  std::vector<std::int32_t> expected_watch;
  std::vector<std::int32_t> expected_war_handoff;
  for (const auto &row : value.targeting_factions) {
    if (!ValidTargetingRow(row, value.player_character_id.value()) ||
        !faction_ids.insert(row.faction_id).second ||
        row.faction_id <= previous_faction_id) return false;
    previous_faction_id = row.faction_id;
    if (row.faction_at_war) expected_war_handoff.push_back(row.faction_id);
    else if (row.dangerous_by_stock_rule)
      expected_dangerous.push_back(row.faction_id);
    else expected_watch.push_back(row.faction_id);
  }
  std::unordered_set<std::int32_t> county_ids;
  std::int32_t previous_county_id = 0;
  std::vector<std::int32_t> expected_exposed_counties;
  for (const auto &row : value.county_exposures) {
    if (!ValidCountyExposure(row, value.player_character_id.value()) ||
        !county_ids.insert(row.county_title_id).second ||
        row.county_title_id <= previous_county_id) return false;
    previous_county_id = row.county_title_id;
    expected_exposed_counties.push_back(row.county_title_id);
  }

  const auto &planner = value.planner_projection;
  if (expected_alert_ready) {
    if (planner.status !=
            game::PlayerFactionPlannerProjectionStatusV1::available ||
        planner.present != (!value.targeting_factions.empty() ||
                            !value.county_exposures.empty()) ||
        planner.dangerous != (!expected_dangerous.empty() ||
                              !expected_exposed_counties.empty()) ||
        planner.dangerous_faction_ids != expected_dangerous ||
        planner.watch_faction_ids != expected_watch ||
        planner.war_handoff_faction_ids != expected_war_handoff ||
        planner.exposed_county_title_ids != expected_exposed_counties ||
        !StrictlyIncreasing(planner.dangerous_faction_ids) ||
        !StrictlyIncreasing(planner.watch_faction_ids) ||
        !StrictlyIncreasing(planner.war_handoff_faction_ids) ||
        !StrictlyIncreasing(planner.exposed_county_title_ids)) {
      return false;
    }
  } else if (planner.status !=
                 game::PlayerFactionPlannerProjectionStatusV1::unavailable ||
             planner.present.has_value() || planner.dangerous.has_value() ||
             !planner.dangerous_faction_ids.empty() ||
             !planner.watch_faction_ids.empty() ||
             !planner.war_handoff_faction_ids.empty() ||
             !planner.exposed_county_title_ids.empty()) {
    return false;
  }
  return true;
}

bool ValidUnavailable(const game::PlayerFactionAlertsV1 &value) {
  return value.snapshot_revision > 0 &&
         !WireUnavailableReason(value.unavailable_reason).empty() &&
         !value.player_character_id.has_value() &&
         !value.targeting_faction_count.has_value() &&
         value.targeting_factions.empty() && value.county_exposures.empty() &&
         value.planner_projection.status ==
             game::PlayerFactionPlannerProjectionStatusV1::unavailable &&
         !value.planner_projection.present.has_value() &&
         !value.planner_projection.dangerous.has_value() &&
         value.planner_projection.dangerous_faction_ids.empty() &&
         value.planner_projection.watch_faction_ids.empty() &&
         value.planner_projection.war_handoff_faction_ids.empty() &&
         value.planner_projection.exposed_county_title_ids.empty() &&
         !value.readiness.identity_ready &&
         !value.readiness.targeting_count_ready &&
         !value.readiness.targeting_rows_ready &&
         !value.readiness.county_exposure_ready &&
         !value.readiness.stock_dangerous_predicate_ready &&
         !value.readiness.same_frame_ready && !value.readiness.alert_ready &&
         !value.readiness.exact_ultimatum_timing_ready &&
         !value.component_unavailable_reasons.targeting_rows.has_value() &&
         !value.component_unavailable_reasons.county_exposure.has_value();
}

void AppendOptionalInt32(std::string &output,
                         const std::optional<std::int32_t> &value) {
  output += value.has_value() ? Number(value.value()) : "null";
}

void AppendOptionalBool(std::string &output,
                        const std::optional<bool> &value) {
  output += value.has_value() ? (value.value() ? "true" : "false") : "null";
}

void AppendOptionalString(std::string &output,
                          const std::optional<std::string> &value) {
  if (value.has_value()) AppendJsonString(output, value.value());
  else output += "null";
}

void AppendInt32Array(std::string &output,
                      const std::vector<std::int32_t> &values) {
  output.push_back('[');
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) output.push_back(',');
    output += Number(values[index]);
  }
  output.push_back(']');
}

void AppendFixedPoint(std::string &output,
                      const game::PlayerFactionFixedPointV1 &value) {
  output += "{\"raw\":" + Number(value.raw) + ",\"scale\":" +
            Number(value.scale) + "}";
}

template <typename Integer>
void AppendOptionalScaledInteger(std::string &output,
                                 const std::optional<Integer> &value,
                                 std::int32_t scale) {
  if (value.has_value()) {
    output += "{\"raw\":" + Number(value.value()) + ",\"scale\":" +
              Number(scale) + "}";
  } else {
    output += "null";
  }
}

void AppendCountyMemberObservation(
    std::string &output,
    const game::PlayerFactionCountyMemberObservationV1 &county) {
  output += "{\"county_title_id\":" + Number(county.county_title_id) +
            ",\"capital_province_id\":";
  AppendOptionalInt32(output, county.capital_province_id);
  output += ",\"holder_character_id\":";
  AppendOptionalInt32(output, county.holder_character_id);
  output += ",\"county_opinion\":";
  AppendOptionalScaledInteger(output, county.county_opinion, 1);
  output += ",\"native_county_join_score\":";
  AppendOptionalScaledInteger(output, county.native_county_join_score_raw,
                              kFixedPointScale);
  output += ",\"can_add_county\":";
  AppendOptionalBool(output, county.can_add_county);
  output += ",\"removal_queued\":";
  AppendOptionalBool(output, county.removal_queued);
  output += ",\"native_leave_score_threshold\":";
  AppendOptionalScaledInteger(output, county.native_leave_score_threshold, 1);
  output += ",\"opinion_status\":";
  AppendJsonString(output, county.opinion_status);
  output += ",\"native_final_status\":";
  AppendJsonString(output, county.native_final_status);
  output += ",\"county_culture_id\":";
  AppendOptionalInt32(output, county.county_culture_id);
  output += ",\"target_culture_id\":";
  AppendOptionalInt32(output, county.target_culture_id);
  output += ",\"same_culture_as_target\":";
  AppendOptionalBool(output, county.same_culture_as_target);
  output += ",\"culture_relation_status\":";
  AppendJsonString(output, county.culture_relation_status);
  output.push_back('}');
}

void AppendSurrenderTitle(std::string &output,
                          const game::FactionSurrenderTitleV1 &title) {
  output += "{\"title_id\":" + Number(title.title_id) +
            ",\"tier_raw\":" + Number(title.tier_raw) +
            ",\"de_jure_parent_title_id\":";
  AppendOptionalInt32(output, title.de_jure_parent_title_id);
  output += ",\"duchy_title_id\":";
  AppendOptionalInt32(output, title.duchy_title_id);
  output += ",\"kingdom_title_id\":";
  AppendOptionalInt32(output, title.kingdom_title_id);
  output += ",\"holder_character_id\":";
  AppendOptionalInt32(output, title.holder_character_id);
  output += ",\"top_liege_character_id\":";
  AppendOptionalInt32(output, title.top_liege_character_id);
  output.push_back('}');
}

void AppendSurrenderTitles(std::string &output,
                           const std::vector<game::FactionSurrenderTitleV1> &titles) {
  output.push_back('[');
  for (std::size_t index = 0; index < titles.size(); ++index) {
    if (index) output.push_back(',');
    AppendSurrenderTitle(output, titles[index]);
  }
  output.push_back(']');
}

void AppendSurrenderImpact(std::string &output,
                          const game::FactionSurrenderImpactV1 &impact) {
  output += "{\"status\":";
  AppendJsonString(output, impact.status);
  output += ",\"unavailable_reason\":";
  AppendOptionalString(output, impact.unavailable_reason);
  output += ",\"government_allows_state_faith\":";
  AppendOptionalBool(output, impact.government_allows_state_faith);
  output += ",\"leader_at_war_with_target\":";
  AppendOptionalBool(output, impact.leader_at_war_with_target);
  output += ",\"ordinary_branch_title_sets_ready\":";
  output += impact.ordinary_branch_title_sets_ready ? "true" : "false";
  output += ",\"county_loss_complete\":";
  output += impact.county_loss_complete ? "true" : "false";
  output += ",\"kingdom_outcome_complete\":";
  output += impact.kingdom_outcome_complete ? "true" : "false";
  output += ",\"player_subrealm_county_title_ids\":";
  AppendInt32Array(output, impact.player_subrealm_county_title_ids);
  output += ",\"member_counties\":";
  AppendSurrenderTitles(output, impact.member_counties);
  output += ",\"seized_counties\":";
  AppendSurrenderTitles(output, impact.seized_counties);
  output += ",\"seized_duchies\":";
  AppendSurrenderTitles(output, impact.seized_duchies);
  output += ",\"player_direct_title_loss_ids\":";
  AppendInt32Array(output, impact.player_direct_title_loss_ids);
  output += ",\"player_remaining_direct_county_title_ids\":";
  AppendInt32Array(output, impact.player_remaining_direct_county_title_ids);
  output += ",\"kingdoms\":[";
  for (std::size_t index = 0; index < impact.kingdoms.size(); ++index) {
    if (index) output.push_back(',');
    const auto &kingdom = impact.kingdoms[index];
    output += "{\"title\":";
    AppendSurrenderTitle(output, kingdom.title);
    output += ",\"de_jure_county_title_ids\":";
    AppendInt32Array(output, kingdom.de_jure_county_title_ids);
    output += ",\"seized_county_title_ids\":";
    AppendInt32Array(output, kingdom.seized_county_title_ids);
    output += ",\"strict_majority_from_seized_counties\":";
    output += kingdom.strict_majority_from_seized_counties ? "true" : "false";
    output.push_back('}');
  }
  output += "],\"unresolved_branches\":[";
  for (std::size_t index = 0; index < impact.unresolved_branches.size(); ++index) {
    if (index) output.push_back(',');
    AppendJsonString(output, impact.unresolved_branches[index]);
  }
  output += "]}";
}

void AppendTargetingRow(std::string &output,
                        const game::PlayerTargetingFactionV1 &row) {
  output += "{\"faction_id\":" + Number(row.faction_id) +
            ",\"faction_type_key\":";
  AppendJsonString(output, row.faction_type_key);
  output += ",\"target_character_id\":" + Number(row.target_character_id) +
            ",\"leader_character_id\":";
  AppendOptionalInt32(output, row.leader_character_id);
  output += ",\"leader_is_human\":";
  output += row.leader_is_human ? "true" : "false";
  output += ",\"special_character_id\":";
  AppendOptionalInt32(output, row.special_character_id);
  output += ",\"special_title_id\":";
  AppendOptionalInt32(output, row.special_title_id);
  output += ",\"faction_at_war\":";
  output += row.faction_at_war ? "true" : "false";
  output += ",\"faction_war_id\":";
  AppendOptionalInt32(output, row.faction_war_id);
  output += ",\"power\":";
  AppendFixedPoint(output, row.power);
  output += ",\"power_threshold\":";
  AppendFixedPoint(output, row.power_threshold);
  output += ",\"discontent\":";
  AppendFixedPoint(output, row.discontent);
  output += ",\"discontent_per_month\":";
  AppendFixedPoint(output, row.discontent_per_month);
  output += ",\"months_until_max_discontent\":";
  AppendOptionalInt32(output, row.months_until_max_discontent);
  output += ",\"character_member_ids\":";
  AppendInt32Array(output, row.character_member_ids);
  output += ",\"county_member_title_ids\":";
  AppendInt32Array(output, row.county_member_title_ids);
  // Legacy providers do not claim an empty current material query.
  if (!row.county_member_observations.empty()) {
    output += ",\"county_member_observations\":[";
    for (std::size_t index = 0;
         index < row.county_member_observations.size(); ++index) {
      if (index != 0) output.push_back(',');
      AppendCountyMemberObservation(output, row.county_member_observations[index]);
    }
    output.push_back(']');
  }
  if (row.surrender_impact) {
    output += ",\"surrender_impact\":";
    AppendSurrenderImpact(output, *row.surrender_impact);
  }
  output += ",\"dangerous_by_stock_rule\":";
  output += row.dangerous_by_stock_rule ? "true" : "false";
  output += ",\"danger_reason\":";
  AppendJsonString(output, row.danger_reason);
  output.push_back('}');
}

void AppendCountyExposure(std::string &output,
                          const game::PlayerFactionCountyExposureV1 &row) {
  output += "{\"county_title_id\":" + Number(row.county_title_id) +
            ",\"faction_id\":" + Number(row.faction_id) +
            ",\"faction_type_key\":";
  AppendJsonString(output, row.faction_type_key);
  output += ",\"target_character_id\":" + Number(row.target_character_id) +
            ",\"power\":";
  AppendFixedPoint(output, row.power);
  output += ",\"power_threshold\":";
  AppendFixedPoint(output, row.power_threshold);
  output += ",\"dangerous_by_stock_rule\":";
  output += row.dangerous_by_stock_rule ? "true" : "false";
  output += ",\"danger_reason\":";
  AppendJsonString(output, row.danger_reason);
  output.push_back('}');
}

void AppendProvenance(std::string &output, std::string_view game_version,
                      std::string_view executable_sha256,
                      std::string_view backend_id) {
  output += "{\"game_version\":";
  AppendJsonString(output, game_version);
  output += ",\"executable_sha256\":";
  AppendJsonString(output, executable_sha256);
  output += ",\"backend_id\":";
  AppendJsonString(output, backend_id);
  output.push_back('}');
}

} // namespace

std::string SerializePlayerFactionAlertsV1(
    const game::PlayerFactionAlertsV1 &value) {
  return SerializePlayerFactionAlertsWithProvenanceV1(
      value, kPlayerFactionAlertsV1GameVersion,
      kPlayerFactionAlertsV1ExecutableSha256, kPlayerFactionAlertsV1BackendId);
}

std::string SerializePlayerFactionAlertsWithProvenanceV1(
    const game::PlayerFactionAlertsV1 &value, std::string_view game_version,
    std::string_view executable_sha256, std::string_view backend_id) {
  const bool available =
      value.status == game::PlayerFactionAlertsStatusV1::available;
  if ((available && !ValidAvailable(value)) ||
      (!available && !ValidUnavailable(value))) return {};

  std::string output;
  output.reserve(8'192 + value.targeting_factions.size() * 1'024 +
                 value.county_exposures.size() * 512);
  output += "{\"schema_version\":1,\"status\":";
  AppendJsonString(output, available ? "available" : "unavailable");
  output += ",\"snapshot_revision\":" + Number(value.snapshot_revision) +
            ",\"date_raw\":";
  AppendOptionalInt32(output, value.date_raw);
  output += ",\"player_character_id\":";
  AppendOptionalInt32(output, value.player_character_id);
  output += ",\"targeting_faction_count\":";
  AppendOptionalInt32(output, value.targeting_faction_count);
  output += ",\"targeting_factions\":[";
  for (std::size_t index = 0; index < value.targeting_factions.size(); ++index) {
    if (index != 0) output.push_back(',');
    AppendTargetingRow(output, value.targeting_factions[index]);
  }
  output += "],\"county_exposures\":[";
  for (std::size_t index = 0; index < value.county_exposures.size(); ++index) {
    if (index != 0) output.push_back(',');
    AppendCountyExposure(output, value.county_exposures[index]);
  }
  const auto &planner = value.planner_projection;
  output += "],\"planner_projection\":{\"status\":";
  AppendJsonString(
      output,
      planner.status == game::PlayerFactionPlannerProjectionStatusV1::available
          ? "available" : "unavailable");
  output += ",\"present\":";
  AppendOptionalBool(output, planner.present);
  output += ",\"dangerous\":";
  AppendOptionalBool(output, planner.dangerous);
  output += ",\"dangerous_faction_ids\":";
  AppendInt32Array(output, planner.dangerous_faction_ids);
  output += ",\"watch_faction_ids\":";
  AppendInt32Array(output, planner.watch_faction_ids);
  output += ",\"war_handoff_faction_ids\":";
  AppendInt32Array(output, planner.war_handoff_faction_ids);
  output += ",\"exposed_county_title_ids\":";
  AppendInt32Array(output, planner.exposed_county_title_ids);
  output += ",\"exact_ultimatum_timing_ready\":false},\"readiness\":{";
  output += "\"identity_ready\":";
  output += value.readiness.identity_ready ? "true" : "false";
  output += ",\"targeting_count_ready\":";
  output += value.readiness.targeting_count_ready ? "true" : "false";
  output += ",\"targeting_rows_ready\":";
  output += value.readiness.targeting_rows_ready ? "true" : "false";
  output += ",\"county_exposure_ready\":";
  output += value.readiness.county_exposure_ready ? "true" : "false";
  output += ",\"stock_dangerous_predicate_ready\":";
  output += value.readiness.stock_dangerous_predicate_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += value.readiness.same_frame_ready ? "true" : "false";
  output += ",\"alert_ready\":";
  output += value.readiness.alert_ready ? "true" : "false";
  output += ",\"exact_ultimatum_timing_ready\":false}";
  output += ",\"component_unavailable_reasons\":{";
  output += "\"targeting_rows\":";
  AppendOptionalString(output,
                       value.component_unavailable_reasons.targeting_rows);
  output += ",\"county_exposure\":";
  AppendOptionalString(output,
                       value.component_unavailable_reasons.county_exposure);
  output += "},\"unavailable_reason\":";
  if (available) output += "null";
  else AppendJsonString(output, WireUnavailableReason(value.unavailable_reason));
  output += ",\"provenance\":";
  AppendProvenance(output, game_version, executable_sha256, backend_id);
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
