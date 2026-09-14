#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class PlayerFactionAlertsStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class PlayerFactionAlertsFailureReasonV1 : std::uint32_t {
  none = 0,
  invalid_request,
  exact_build_not_admitted,
  native_reader_not_frozen,
  offline_fixture_source_not_authorized,
  application_main_thread_required,
  frame_capture_failed,
  snapshot_revision_mismatch,
  paused_player_unavailable,
  targeting_count_unavailable,
  fixture_source_failed,
  identity_round_trip_failed,
  identity_drift,
  same_frame_drift,
  native_sample_drift,
  schema_invariant_failed,
  reader_exception,
};

struct PlayerFactionFixedPointV1 {
  std::int64_t raw = 0;
  std::int32_t scale = 100'000;

  friend bool operator==(const PlayerFactionFixedPointV1 &,
                         const PlayerFactionFixedPointV1 &) = default;
};

struct PlayerTargetingFactionV1 {
  std::int32_t faction_id = -1;
  std::string faction_type_key;
  std::int32_t target_character_id = -1;
  std::optional<std::int32_t> leader_character_id;
  bool leader_is_human = false;
  std::optional<std::int32_t> special_character_id;
  std::optional<std::int32_t> special_title_id;
  bool faction_at_war = false;
  std::optional<std::int32_t> faction_war_id;
  PlayerFactionFixedPointV1 power;
  PlayerFactionFixedPointV1 power_threshold;
  PlayerFactionFixedPointV1 discontent;
  PlayerFactionFixedPointV1 discontent_per_month;
  std::optional<std::int32_t> months_until_max_discontent;
  std::vector<std::int32_t> character_member_ids;
  std::vector<std::int32_t> county_member_title_ids;
  bool dangerous_by_stock_rule = false;
  std::string danger_reason;

  friend bool operator==(const PlayerTargetingFactionV1 &,
                         const PlayerTargetingFactionV1 &) = default;
};

struct PlayerFactionCountyExposureV1 {
  std::int32_t county_title_id = -1;
  std::int32_t faction_id = -1;
  std::string faction_type_key;
  std::int32_t target_character_id = -1;
  PlayerFactionFixedPointV1 power;
  PlayerFactionFixedPointV1 power_threshold;
  bool dangerous_by_stock_rule = false;
  std::string danger_reason;

  friend bool operator==(const PlayerFactionCountyExposureV1 &,
                         const PlayerFactionCountyExposureV1 &) = default;
};

enum class PlayerFactionPlannerProjectionStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

struct PlayerFactionPlannerProjectionV1 {
  PlayerFactionPlannerProjectionStatusV1 status =
      PlayerFactionPlannerProjectionStatusV1::unavailable;
  std::optional<bool> present;
  std::optional<bool> dangerous;
  std::vector<std::int32_t> dangerous_faction_ids;
  std::vector<std::int32_t> watch_faction_ids;
  std::vector<std::int32_t> war_handoff_faction_ids;
  std::vector<std::int32_t> exposed_county_title_ids;
  bool exact_ultimatum_timing_ready = false;

  friend bool operator==(const PlayerFactionPlannerProjectionV1 &,
                         const PlayerFactionPlannerProjectionV1 &) = default;
};

struct PlayerFactionAlertsReadinessV1 {
  bool identity_ready = false;
  bool targeting_count_ready = false;
  bool targeting_rows_ready = false;
  bool county_exposure_ready = false;
  bool stock_dangerous_predicate_ready = false;
  bool same_frame_ready = false;
  bool alert_ready = false;
  bool exact_ultimatum_timing_ready = false;

  friend bool operator==(const PlayerFactionAlertsReadinessV1 &,
                         const PlayerFactionAlertsReadinessV1 &) = default;
};

struct PlayerFactionAlertsComponentUnavailableReasonsV1 {
  std::optional<std::string> targeting_rows;
  std::optional<std::string> county_exposure;

  friend bool operator==(
      const PlayerFactionAlertsComponentUnavailableReasonsV1 &,
      const PlayerFactionAlertsComponentUnavailableReasonsV1 &) = default;
};

struct PlayerFactionAlertsV1 {
  PlayerFactionAlertsStatusV1 status =
      PlayerFactionAlertsStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::optional<std::int32_t> date_raw;
  std::optional<std::int32_t> player_character_id;
  std::optional<std::int32_t> targeting_faction_count;
  std::vector<PlayerTargetingFactionV1> targeting_factions;
  std::vector<PlayerFactionCountyExposureV1> county_exposures;
  PlayerFactionPlannerProjectionV1 planner_projection;
  PlayerFactionAlertsReadinessV1 readiness;
  PlayerFactionAlertsComponentUnavailableReasonsV1
      component_unavailable_reasons;
  PlayerFactionAlertsFailureReasonV1 unavailable_reason =
      PlayerFactionAlertsFailureReasonV1::none;

  friend bool operator==(const PlayerFactionAlertsV1 &,
                         const PlayerFactionAlertsV1 &) = default;
};

struct PlayerFactionAlertsFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::int32_t played_character_id = -1;

  friend bool operator==(const PlayerFactionAlertsFrameV1 &,
                         const PlayerFactionAlertsFrameV1 &) = default;
};

enum class ReadPlayerFactionAlertsResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kPlayerFactionAlertsV1Capability =
    "game.command.query-player-faction-alerts-v1";
inline constexpr std::string_view kPlayerFactionAlertsV1Step =
    "query-player-faction-alerts-v1";
inline constexpr std::string_view kPlayerFactionAlertsV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view kPlayerFactionAlertsV1ExecutableSha256 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kPlayerFactionAlertsV1BackendId =
    "ck3-1.19.0.6-native-player-faction-alerts-v1";
inline constexpr std::string_view kPlayerFactionAlertsV1ContractStage =
    "targeting_count_live_rows_and_county_fixture_pending_native_readers";
inline constexpr std::string_view kPlayerFactionAlertsV1ReaderMode =
    "campaign_root_targeting_count_with_fixture_only_details";
inline constexpr std::string_view
    kPlayerFactionAlertsV1NextReverseEngineeringEntry =
        "faction_alert_targeting_span_and_sub_realm_county_membership_readers";
inline constexpr std::string_view
    kPlayerFactionAlertsV1TargetingRowsUnavailableReason =
        "targeting_rows_native_reader_not_frozen";
inline constexpr std::string_view
    kPlayerFactionAlertsV1CountyExposureUnavailableReason =
        "county_exposure_native_reader_not_frozen";

struct PlayerTargetingFactionSourceRowV1 {
  game::PlayerTargetingFactionV1 row;
  bool faction_identity_round_trip = false;
  bool target_identity_round_trip = false;
  bool leader_identity_round_trip = false;
  bool special_character_identity_round_trip = false;
  bool special_title_identity_round_trip = false;
  bool war_identity_round_trip = false;
  bool member_identities_round_trip = false;

  friend bool operator==(const PlayerTargetingFactionSourceRowV1 &,
                         const PlayerTargetingFactionSourceRowV1 &) = default;
};

struct PlayerFactionCountyExposureSourceRowV1 {
  game::PlayerFactionCountyExposureV1 row;
  bool county_identity_round_trip = false;
  bool faction_identity_round_trip = false;
  bool target_identity_round_trip = false;

  friend bool operator==(
      const PlayerFactionCountyExposureSourceRowV1 &,
      const PlayerFactionCountyExposureSourceRowV1 &) = default;
};

struct PlayerFactionAlertsSourceSampleV1 {
  std::int32_t player_character_id = -1;
  bool player_identity_round_trip = false;
  std::int32_t targeting_faction_count = -1;
  std::vector<PlayerTargetingFactionSourceRowV1> targeting_factions;
  std::vector<PlayerFactionCountyExposureSourceRowV1> county_exposures;

  friend bool operator==(const PlayerFactionAlertsSourceSampleV1 &,
                         const PlayerFactionAlertsSourceSampleV1 &) = default;
};

struct PlayerFactionAlertsNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_source = false;
};

using CapturePlayerFactionAlertsFrameV1 = bool (*)(
    void *context, game::PlayerFactionAlertsFrameV1 &output) noexcept;
using IsPlayerFactionAlertsMainThreadV1 = bool (*)(void *context) noexcept;
using ReadPlayerTargetingFactionCountV1 = bool (*)(
    void *context, std::int32_t expected_player_character_id,
    std::int32_t &output) noexcept;
using ReadPlayerFactionAlertsFixtureSourceV1 = bool (*)(
    void *context, PlayerFactionAlertsSourceSampleV1 &output) noexcept;

struct PlayerFactionAlertsAccessV1 {
  void *context = nullptr;
  CapturePlayerFactionAlertsFrameV1 capture_frame = nullptr;
  IsPlayerFactionAlertsMainThreadV1 is_main_thread = nullptr;
  ReadPlayerTargetingFactionCountV1 read_targeting_faction_count = nullptr;
  ReadPlayerFactionAlertsFixtureSourceV1 read_offline_fixture_source = nullptr;
};

struct PlayerFactionAlertsRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
};

PlayerFactionAlertsNativeEnvironmentV1
BindPlayerFactionAlertsNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadPlayerFactionAlertsResultV1 ReadPlayerFactionAlertsV1(
    const PlayerFactionAlertsNativeEnvironmentV1 &environment,
    const PlayerFactionAlertsAccessV1 &access,
    const PlayerFactionAlertsRequestV1 &request,
    game::PlayerFactionAlertsV1 &output) noexcept;

std::string_view PlayerFactionAlertsFailureReasonKeyV1(
    game::PlayerFactionAlertsFailureReasonV1 reason) noexcept;

std::string SerializePlayerFactionAlertsV1(
    const game::PlayerFactionAlertsV1 &snapshot);

} // namespace xar::ck3_11906
