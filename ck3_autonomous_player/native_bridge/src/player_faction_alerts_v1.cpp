#include "xar_bridge/player_faction_alerts_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <limits>
#include <string_view>
#include <unordered_set>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kMaximumRows = 16'384;
constexpr std::int32_t kFixedPointScale = 100'000;
using Failure = game::PlayerFactionAlertsFailureReasonV1;
using Result = game::ReadPlayerFactionAlertsResultV1;

bool PositiveIdentity(std::int32_t value) noexcept { return value > 0; }

bool StableKey(std::string_view value) noexcept {
  if (value.empty()) {
    return false;
  }
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
    if (!PositiveIdentity(value) || !seen.insert(value).second) {
      return false;
    }
  }
  return true;
}

Failure ValidateSample(const PlayerFactionAlertsSourceSampleV1 &sample,
                       std::int32_t expected_player) noexcept {
  if (!PositiveIdentity(sample.player_character_id) ||
      sample.player_character_id != expected_player ||
      !sample.player_identity_round_trip || sample.targeting_faction_count < 0 ||
      static_cast<std::size_t>(sample.targeting_faction_count) !=
          sample.targeting_factions.size() ||
      sample.targeting_factions.size() > kMaximumRows ||
      sample.county_exposures.size() > kMaximumRows) {
    return Failure::schema_invariant_failed;
  }
  std::unordered_set<std::int32_t> faction_ids;
  for (const auto &source : sample.targeting_factions) {
    const auto &row = source.row;
    if (!PositiveIdentity(row.faction_id) ||
        !PositiveIdentity(row.target_character_id) ||
        row.target_character_id != expected_player ||
        !source.faction_identity_round_trip ||
        !source.target_identity_round_trip ||
        (row.leader_character_id.has_value() &&
         (!PositiveIdentity(row.leader_character_id.value()) ||
          !source.leader_identity_round_trip)) ||
        (!row.leader_character_id.has_value() && row.leader_is_human) ||
        (row.special_character_id.has_value() &&
         (!PositiveIdentity(row.special_character_id.value()) ||
          !source.special_character_identity_round_trip)) ||
        (row.special_title_id.has_value() &&
         (!PositiveIdentity(row.special_title_id.value()) ||
          !source.special_title_identity_round_trip)) ||
        (row.faction_war_id.has_value() &&
         (!PositiveIdentity(row.faction_war_id.value()) ||
          !source.war_identity_round_trip)) ||
        (!row.faction_at_war && row.faction_war_id.has_value()) ||
        !source.member_identities_round_trip ||
        !StableKey(row.faction_type_key) ||
        !ValidFixedPoint(row.power, true) ||
        !ValidFixedPoint(row.power_threshold, true) ||
        !ValidFixedPoint(row.discontent, true) ||
        !ValidFixedPoint(row.discontent_per_month, false) ||
        (row.months_until_max_discontent.has_value() &&
         row.months_until_max_discontent.value() < 0) ||
        !PositiveUnique(row.character_member_ids) ||
        !PositiveUnique(row.county_member_title_ids)) {
      return Failure::identity_round_trip_failed;
    }
    if (!faction_ids.insert(row.faction_id).second) {
      return Failure::identity_drift;
    }
  }
  std::unordered_set<std::int32_t> county_ids;
  for (const auto &source : sample.county_exposures) {
    const auto &row = source.row;
    if (!PositiveIdentity(row.county_title_id) ||
        !PositiveIdentity(row.faction_id) ||
        !PositiveIdentity(row.target_character_id) ||
        !source.county_identity_round_trip ||
        !source.faction_identity_round_trip ||
        !source.target_identity_round_trip ||
        row.faction_type_key != "populist_faction" ||
        row.target_character_id == expected_player ||
        !ValidFixedPoint(row.power, true) ||
        !ValidFixedPoint(row.power_threshold, true) ||
        row.power.raw <= row.power_threshold.raw) {
      return Failure::schema_invariant_failed;
    }
    if (!county_ids.insert(row.county_title_id).second) {
      return Failure::identity_drift;
    }
  }
  return Failure::none;
}

void DeriveStockDanger(game::PlayerTargetingFactionV1 &row) {
  row.dangerous_by_stock_rule = false;
  if (row.leader_is_human) {
    row.dangerous_by_stock_rule = true;
    row.danger_reason = "human_faction_leader";
    return;
  }
  if (row.faction_type_key == "peasant_faction") {
    if (row.months_until_max_discontent.has_value() &&
        row.months_until_max_discontent.value() <= 12) {
      row.dangerous_by_stock_rule = true;
      row.danger_reason = "peasant_ultimatum_within_12_months";
    } else {
      row.danger_reason = "peasant_ultimatum_not_within_12_months";
    }
    return;
  }
  if (row.discontent_per_month.raw > 0) {
    row.dangerous_by_stock_rule = true;
    row.danger_reason = "non_peasant_discontent_increasing";
  } else {
    row.danger_reason = "non_peasant_discontent_not_increasing";
  }
}

void MaterializeFull(const PlayerFactionAlertsSourceSampleV1 &sample,
                     const game::PlayerFactionAlertsFrameV1 &frame,
                     game::PlayerFactionAlertsV1 &output) {
  output.status = game::PlayerFactionAlertsStatusV1::available;
  output.snapshot_revision = frame.snapshot_revision;
  output.date_raw = frame.date_raw;
  output.player_character_id = sample.player_character_id;
  output.targeting_faction_count = sample.targeting_faction_count;
  output.targeting_factions.clear();
  output.targeting_factions.reserve(sample.targeting_factions.size());
  for (const auto &source : sample.targeting_factions) {
    auto row = source.row;
    std::sort(row.character_member_ids.begin(), row.character_member_ids.end());
    std::sort(row.county_member_title_ids.begin(),
              row.county_member_title_ids.end());
    DeriveStockDanger(row);
    output.targeting_factions.push_back(std::move(row));
  }
  std::sort(output.targeting_factions.begin(),
            output.targeting_factions.end(),
            [](const auto &left, const auto &right) {
              return left.faction_id < right.faction_id;
            });
  output.county_exposures.clear();
  output.county_exposures.reserve(sample.county_exposures.size());
  for (const auto &source : sample.county_exposures) {
    auto row = source.row;
    row.dangerous_by_stock_rule = true;
    row.danger_reason =
        "player_county_in_powerful_liege_targeting_populist_faction";
    output.county_exposures.push_back(std::move(row));
  }
  std::sort(output.county_exposures.begin(), output.county_exposures.end(),
            [](const auto &left, const auto &right) {
              return left.county_title_id < right.county_title_id;
            });

  auto &planner = output.planner_projection;
  planner.status = game::PlayerFactionPlannerProjectionStatusV1::available;
  planner.present = !output.targeting_factions.empty() ||
                    !output.county_exposures.empty();
  planner.dangerous = !output.county_exposures.empty();
  for (const auto &row : output.targeting_factions) {
    if (row.faction_at_war) {
      planner.war_handoff_faction_ids.push_back(row.faction_id);
    } else if (row.dangerous_by_stock_rule) {
      planner.dangerous_faction_ids.push_back(row.faction_id);
      planner.dangerous = true;
    } else {
      planner.watch_faction_ids.push_back(row.faction_id);
    }
  }
  for (const auto &row : output.county_exposures) {
    planner.exposed_county_title_ids.push_back(row.county_title_id);
  }
  planner.exact_ultimatum_timing_ready = false;
  output.readiness = {true, true, true, true, true, true, true, false};
  output.component_unavailable_reasons = {};
  output.unavailable_reason = Failure::none;
}

void MaterializeCountOnly(std::int32_t player_character_id,
                          std::int32_t targeting_faction_count,
                          const game::PlayerFactionAlertsFrameV1 &frame,
                          game::PlayerFactionAlertsV1 &output) {
  output.status = game::PlayerFactionAlertsStatusV1::available;
  output.snapshot_revision = frame.snapshot_revision;
  output.date_raw = frame.date_raw;
  output.player_character_id = player_character_id;
  output.targeting_faction_count = targeting_faction_count;
  output.targeting_factions.clear();
  output.county_exposures.clear();
  output.planner_projection = {};
  const bool empty_targeting_set = targeting_faction_count == 0;
  output.readiness = {true, true, empty_targeting_set, false,
                      empty_targeting_set, true, false, false};
  if (!empty_targeting_set) {
    output.component_unavailable_reasons.targeting_rows =
        kPlayerFactionAlertsV1TargetingRowsUnavailableReason;
  }
  output.component_unavailable_reasons.county_exposure =
      kPlayerFactionAlertsV1CountyExposureUnavailableReason;
  output.unavailable_reason = Failure::none;
}

} // namespace

PlayerFactionAlertsNativeEnvironmentV1
BindPlayerFactionAlertsNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return {module_base, exact_build_admitted, false};
}

game::ReadPlayerFactionAlertsResultV1 ReadPlayerFactionAlertsV1(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access,
    const PlayerFactionAlertsRequestV1 &request,
    game::PlayerFactionAlertsV1 &output) noexcept {
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  const auto fail = [&](Failure reason) noexcept {
    output.status = game::PlayerFactionAlertsStatusV1::unavailable;
    output.player_character_id.reset();
    output.targeting_faction_count.reset();
    output.targeting_factions.clear();
    output.county_exposures.clear();
    output.planner_projection = {};
    output.readiness = {};
    output.component_unavailable_reasons = {};
    output.unavailable_reason = reason;
    return Result::unavailable;
  };
  try {
    if (request.expected_snapshot_revision == 0) {
      return fail(Failure::invalid_request);
    }
    if (!environment.exact_build_admitted) {
      return fail(Failure::exact_build_not_admitted);
    }
    if (access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      return fail(Failure::application_main_thread_required);
    }
    if (access.capture_frame == nullptr) {
      return fail(Failure::frame_capture_failed);
    }
    game::PlayerFactionAlertsFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      return fail(Failure::frame_capture_failed);
    }
    output.date_raw = before.date_raw;
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      return fail(Failure::snapshot_revision_mismatch);
    }
    if (!before.paused || !before.map_ready ||
        !before.has_played_character || !before.played_character_alive ||
        !PositiveIdentity(before.played_character_id)) {
      return fail(Failure::paused_player_unavailable);
    }

    if (environment.offline_fixture_source) {
      if (environment.module_base != 0 ||
          access.read_offline_fixture_source == nullptr) {
        return fail(Failure::offline_fixture_source_not_authorized);
      }
      PlayerFactionAlertsSourceSampleV1 first{};
      PlayerFactionAlertsSourceSampleV1 second{};
      if (!access.read_offline_fixture_source(access.context, first) ||
          !access.read_offline_fixture_source(access.context, second)) {
        return fail(Failure::fixture_source_failed);
      }
      const auto first_failure =
          ValidateSample(first, before.played_character_id);
      const auto second_failure =
          ValidateSample(second, before.played_character_id);
      if (first_failure != Failure::none) {
        return fail(first_failure);
      }
      if (second_failure != Failure::none) {
        return fail(second_failure);
      }
      if (first != second) {
        const bool identity_changed =
            first.player_character_id != second.player_character_id ||
            first.targeting_faction_count != second.targeting_faction_count ||
            first.targeting_factions.size() !=
                second.targeting_factions.size() ||
            first.county_exposures.size() != second.county_exposures.size();
        return fail(identity_changed ? Failure::identity_drift
                                     : Failure::native_sample_drift);
      }
      game::PlayerFactionAlertsFrameV1 after{};
      if (!access.capture_frame(access.context, after) || after != before) {
        return fail(Failure::same_frame_drift);
      }
      MaterializeFull(first, before, output);
      return Result::available;
    }

    if (environment.module_base == 0 ||
        access.read_targeting_faction_count == nullptr) {
      return fail(Failure::native_reader_not_frozen);
    }
    std::int32_t first_count = 0;
    std::int32_t second_count = 0;
    if (!access.read_targeting_faction_count(
            access.context, before.played_character_id, first_count) ||
        first_count < 0 ||
        !access.read_targeting_faction_count(
            access.context, before.played_character_id, second_count) ||
        second_count < 0) {
      return fail(Failure::targeting_count_unavailable);
    }
    if (first_count != second_count) {
      return fail(Failure::native_sample_drift);
    }
    game::PlayerFactionAlertsFrameV1 after{};
    if (!access.capture_frame(access.context, after) || after != before) {
      return fail(Failure::same_frame_drift);
    }
    MaterializeCountOnly(before.played_character_id, first_count, before,
                         output);
    return Result::available;
  } catch (...) {
    return fail(Failure::reader_exception);
  }
}

std::string_view PlayerFactionAlertsFailureReasonKeyV1(
    game::PlayerFactionAlertsFailureReasonV1 reason) noexcept {
  using enum game::PlayerFactionAlertsFailureReasonV1;
  switch (reason) {
  case none:
    return {};
  case invalid_request:
    return "state_changed";
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
  case snapshot_revision_mismatch:
  case targeting_count_unavailable:
  case identity_round_trip_failed:
  case identity_drift:
  case same_frame_drift:
  case native_sample_drift:
  case schema_invariant_failed:
    return "state_changed";
  }
  return "reader_not_implemented";
}

} // namespace xar::ck3_11906
