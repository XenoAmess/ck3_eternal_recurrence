#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class StewardDevelopCountyCandidatesStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class StewardDevelopCountyFailureReasonV1 : std::uint32_t {
  none = 0,
  invalid_request,
  exact_build_not_admitted,
  native_reader_not_frozen,
  offline_fixture_source_not_authorized,
  application_main_thread_required,
  frame_capture_failed,
  snapshot_revision_mismatch,
  paused_player_unavailable,
  fixture_source_failed,
  task_not_shown,
  task_invalid,
  candidate_invalid,
  identity_round_trip_failed,
  identity_drift,
  same_frame_drift,
  native_sample_drift,
  schema_invariant_failed,
  reader_exception,
};

struct StewardDevelopCountyCandidateV1 {
  std::int32_t county_title_id = -1;
  std::int32_t capital_province_id = -1;
  std::int32_t holder_character_id = -1;
  bool is_player_capital = false;
  bool directly_held_by_player = false;
  bool native_legal = false;
  std::int64_t development_level_raw = 0;
  std::int64_t development_progress_raw = 0;
  std::int64_t monthly_development_rate_raw = 0;
  std::int64_t max_development_level_raw = 0;
  std::string terrain_key;
  bool same_culture_as_player = false;
  bool cultural_acceptance_threshold_passed = false;

  friend bool operator==(const StewardDevelopCountyCandidateV1 &,
                         const StewardDevelopCountyCandidateV1 &) = default;
};

struct StewardDevelopCountyCandidatesReadinessV1 {
  bool ready = false;

  friend bool operator==(const StewardDevelopCountyCandidatesReadinessV1 &,
                         const StewardDevelopCountyCandidatesReadinessV1 &) =
      default;
};

struct StewardDevelopCountyCandidatesV1 {
  StewardDevelopCountyCandidatesStatusV1 status =
      StewardDevelopCountyCandidatesStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::optional<std::int32_t> observed_date_raw;
  std::optional<std::int32_t> player_character_id;
  std::optional<std::int32_t> steward_character_id;
  std::string task_key = "task_develop_county";
  std::optional<bool> shown;
  std::optional<bool> valid;
  std::optional<std::string> task_failure_reason;
  std::optional<std::int64_t> steward_increase_development_value_raw;
  std::optional<std::int64_t> current_gold_raw;
  std::optional<bool> no_ai_increase_development;
  std::optional<bool> has_active_improve_development_directive;
  std::string target_selection_mode = "engine_random_unscored";
  std::vector<StewardDevelopCountyCandidateV1> candidates;
  bool same_frame_stable = false;
  StewardDevelopCountyCandidatesReadinessV1 readiness;
  StewardDevelopCountyFailureReasonV1 unavailable_reason =
      StewardDevelopCountyFailureReasonV1::none;

  friend bool operator==(const StewardDevelopCountyCandidatesV1 &,
                         const StewardDevelopCountyCandidatesV1 &) = default;
};

struct StewardDevelopCountyCandidatesFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::int32_t played_character_id = -1;

  friend bool operator==(const StewardDevelopCountyCandidatesFrameV1 &,
                         const StewardDevelopCountyCandidatesFrameV1 &) =
      default;
};

enum class ReadStewardDevelopCountyCandidatesResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kStewardDevelopCountyCandidatesV1Capability =
    "game.command.query-steward-develop-county-candidates-v1";
inline constexpr std::string_view kStewardDevelopCountyCandidatesV1Step =
    "query-steward-develop-county-candidates-v1";
inline constexpr std::string_view kStewardDevelopCountyCandidatesV1GameVersion =
    "1.19.0.6";
inline constexpr std::string_view
    kStewardDevelopCountyCandidatesV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kStewardDevelopCountyCandidatesV1BackendId =
    "ck3-1.19.0.6-native-steward-develop-county-candidates-v1";
inline constexpr std::string_view
    kStewardDevelopCountyCandidatesV1ContractStage =
        "exact_build_contract_fixture_pending_live_reader";
inline constexpr std::string_view kStewardDevelopCountyCandidatesV1TaskKey =
    "task_develop_county";
inline constexpr std::string_view
    kStewardDevelopCountyCandidatesV1TargetSelectionMode =
        "engine_random_unscored";
inline constexpr std::string_view kStewardDevelopCountyCandidatesV1ReaderMode =
    "contract_fixture_pending_live_reader";
inline constexpr std::string_view
    kStewardDevelopCountyCandidatesV1NextReverseEngineeringEntry =
        "task_develop_county_native_candidate_enumerator_and_final_legality_call";

// ABI-independent test source. It is rejected unless the environment is
// explicitly offline and has no production module binding.
struct StewardDevelopCountyCandidateSourceRowV1 {
  game::StewardDevelopCountyCandidateV1 candidate;
  bool county_title_identity_round_trip = false;
  bool capital_province_identity_round_trip = false;
  bool holder_character_identity_round_trip = false;

  friend bool operator==(const StewardDevelopCountyCandidateSourceRowV1 &,
                         const StewardDevelopCountyCandidateSourceRowV1 &) =
      default;
};

struct StewardDevelopCountyCandidatesSourceSampleV1 {
  std::int32_t player_character_id = -1;
  std::int32_t steward_character_id = -1;
  bool player_identity_round_trip = false;
  bool steward_identity_round_trip = false;
  bool shown = false;
  bool valid = false;
  std::optional<std::string> task_failure_reason;
  std::int64_t steward_increase_development_value_raw = 0;
  std::int64_t current_gold_raw = 0;
  bool no_ai_increase_development = false;
  bool has_active_improve_development_directive = false;
  std::vector<StewardDevelopCountyCandidateSourceRowV1> candidates;

  friend bool operator==(
      const StewardDevelopCountyCandidatesSourceSampleV1 &,
      const StewardDevelopCountyCandidatesSourceSampleV1 &) = default;
};

struct StewardDevelopCountyCandidatesNativeEnvironmentV1 {
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  bool offline_fixture_source = false;
};

using CaptureStewardDevelopCountyCandidatesFrameV1 = bool (*)(
    void *context,
    game::StewardDevelopCountyCandidatesFrameV1 &output) noexcept;
using IsStewardDevelopCountyCandidatesMainThreadV1 = bool (*)(
    void *context) noexcept;
using ReadStewardDevelopCountyCandidatesFixtureSourceV1 = bool (*)(
    void *context,
    StewardDevelopCountyCandidatesSourceSampleV1 &output) noexcept;

struct StewardDevelopCountyCandidatesAccessV1 {
  void *context = nullptr;
  CaptureStewardDevelopCountyCandidatesFrameV1 capture_frame = nullptr;
  IsStewardDevelopCountyCandidatesMainThreadV1 is_main_thread = nullptr;
  ReadStewardDevelopCountyCandidatesFixtureSourceV1
      read_offline_fixture_source = nullptr;
};

struct StewardDevelopCountyCandidatesRequestV1 {
  std::uint64_t expected_snapshot_revision = 0;
};

StewardDevelopCountyCandidatesNativeEnvironmentV1
BindStewardDevelopCountyCandidatesNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept;

game::ReadStewardDevelopCountyCandidatesResultV1
ReadStewardDevelopCountyCandidatesV1(
    const StewardDevelopCountyCandidatesNativeEnvironmentV1 &environment,
    const StewardDevelopCountyCandidatesAccessV1 &access,
    const StewardDevelopCountyCandidatesRequestV1 &request,
    game::StewardDevelopCountyCandidatesV1 &output) noexcept;

std::string_view StewardDevelopCountyFailureReasonKeyV1(
    game::StewardDevelopCountyFailureReasonV1 reason) noexcept;

std::string SerializeStewardDevelopCountyCandidatesV1(
    const game::StewardDevelopCountyCandidatesV1 &snapshot);

} // namespace xar::ck3_11906
