#pragma once

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kMajorDecisionFoundKingdomObserverKeyV1 =
        "major_decision_found_kingdom_observer_v1";
inline constexpr std::string_view kMajorDecisionFoundKingdomSchemaV1 =
    "xar.ck3.private.major_decision_found_kingdom_observer/v1";
inline constexpr std::string_view kMajorDecisionFoundKingdomGameVersionV1 =
    "1.19.0.6";
inline constexpr std::string_view
    kMajorDecisionFoundKingdomExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kMajorDecisionFoundKingdomDecisionIdV1 =
    "found_kingdom_decision";
inline constexpr std::string_view
    kMajorDecisionFoundKingdomDecisionBlockSha256V1 =
        "4AA72233FD9266CD36C18DF10E9DBFC21B967003201F61B575C687FAA380C7DF";
inline constexpr std::string_view
    kMajorDecisionFoundKingdomEffectBlockSha256V1 =
        "11944754762E1683CD11512658CBA527D69AE70E4E8AED90B43F80C2ACC8F4AF";
inline constexpr std::string_view
    kMajorDecisionFoundKingdomEvidenceRevisionV1 =
        "major-decision-found-kingdom-1.19.0.6-source-freeze-v1@a33bf13a";
inline constexpr bool kMajorDecisionFoundKingdomAdvertisedByDefaultV1 = false;
inline constexpr std::int64_t kMajorDecisionFixedPointOneV1 = 100'000;
inline constexpr std::size_t kMajorDecisionSha256CapacityV1 = 65;

enum class MajorDecisionFoundKingdomStatusV1 : std::uint8_t {
  unavailable = 0,
  available = 1,
};

enum class MajorDecisionFoundKingdomFailureV1 : std::uint8_t {
  none = 0,
  observer_disabled,
  exact_build_not_admitted,
  application_main_thread_required,
  not_paused,
  map_not_ready,
  played_character_unavailable,
  played_character_identity_mismatch,
  frame_drift,
  source_sample_incomplete,
  source_sample_drift,
  decision_definition_identity_mismatch,
  eligibility_source_invalid,
  typed_field_invalid,
  evaluated_cost_source_invalid,
  evaluated_cost_invalid,
  can_take_invariant_failed,
};

enum class MajorDecisionFieldStateV1 : std::uint8_t {
  unknown = 0,
  known = 1,
};

enum class MajorDecisionUnknownReasonV1 : std::uint8_t {
  none = 0,
  not_observed,
  decision_database_unavailable,
  decision_definition_missing,
  decision_evaluator_unavailable,
  evaluated_cost_evaluator_unavailable,
  affordability_evaluator_unavailable,
  can_take_evaluator_unavailable,
  effect_preview_not_provided,
};

enum class MajorDecisionEligibilitySourceV1 : std::uint8_t {
  unknown = 0,
  native_decision_evaluator,
};

enum class MajorDecisionCostSourceV1 : std::uint8_t {
  unknown = 0,
  native_evaluated_cost,
};

struct MajorDecisionTypedBoolV1 {
  MajorDecisionFieldStateV1 state = MajorDecisionFieldStateV1::unknown;
  bool value = false;
  MajorDecisionUnknownReasonV1 unknown_reason =
      MajorDecisionUnknownReasonV1::not_observed;

  friend bool operator==(const MajorDecisionTypedBoolV1 &,
                         const MajorDecisionTypedBoolV1 &) = default;
};

struct MajorDecisionEvaluatedCostV1 {
  MajorDecisionFieldStateV1 state = MajorDecisionFieldStateV1::unknown;
  MajorDecisionCostSourceV1 source = MajorDecisionCostSourceV1::unknown;
  std::int64_t gold_q100000 = 0;
  std::int64_t treasury_q100000 = 0;
  std::int64_t prestige_q100000 = 0;
  std::int64_t piety_q100000 = 0;
  MajorDecisionUnknownReasonV1 unknown_reason =
      MajorDecisionUnknownReasonV1::not_observed;

  friend bool operator==(const MajorDecisionEvaluatedCostV1 &,
                         const MajorDecisionEvaluatedCostV1 &) = default;
};

struct MajorDecisionEffectPreviewBoundaryV1 {
  MajorDecisionFieldStateV1 state = MajorDecisionFieldStateV1::unknown;
  MajorDecisionUnknownReasonV1 unknown_reason =
      MajorDecisionUnknownReasonV1::effect_preview_not_provided;
  bool executable = false;

  friend bool operator==(const MajorDecisionEffectPreviewBoundaryV1 &,
                         const MajorDecisionEffectPreviewBoundaryV1 &) =
      default;
};

struct MajorDecisionFoundKingdomFrameV1 {
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  std::int32_t played_character_id = -1;
  bool application_main_thread = false;
  bool paused = false;
  bool map_ready = false;
  bool played_character_alive = false;
  bool played_character_identity_round_trip = false;

  friend bool operator==(const MajorDecisionFoundKingdomFrameV1 &,
                         const MajorDecisionFoundKingdomFrameV1 &) = default;
};

// A future exact-build adapter hands this value-only sample to the semantic
// core. No engine pointer, callback, command object, or effect object is stored.
struct MajorDecisionFoundKingdomSourceSampleV1 {
  bool source_read_complete = false;
  std::int32_t played_character_id = -1;
  bool decision_definition_identity_round_trip = false;
  MajorDecisionEligibilitySourceV1 eligibility_source =
      MajorDecisionEligibilitySourceV1::unknown;
  MajorDecisionTypedBoolV1 is_shown{};
  MajorDecisionTypedBoolV1 is_valid{};
  MajorDecisionTypedBoolV1 is_valid_showing_failures_only{};
  MajorDecisionEvaluatedCostV1 evaluated_cost{};
  MajorDecisionTypedBoolV1 is_affordable{};
  MajorDecisionTypedBoolV1 can_take{};

  friend bool operator==(const MajorDecisionFoundKingdomSourceSampleV1 &,
                         const MajorDecisionFoundKingdomSourceSampleV1 &) =
      default;
};

struct MajorDecisionFoundKingdomCaptureV1 {
  bool observer_enabled = false;
  bool exact_build_admitted = false;
  std::array<char, kMajorDecisionSha256CapacityV1>
      admitted_executable_sha256{};
  MajorDecisionFoundKingdomFrameV1 frame_before{};
  MajorDecisionFoundKingdomSourceSampleV1 first_sample{};
  MajorDecisionFoundKingdomSourceSampleV1 second_sample{};
  MajorDecisionFoundKingdomFrameV1 frame_after{};
};

struct MajorDecisionFoundKingdomReadinessV1 {
  bool same_frame_ready = false;
  bool eligibility_ready = false;
  bool evaluated_cost_ready = false;
  bool affordability_ready = false;
  bool can_take_ready = false;
  bool semantic_observation_ready = false;
  bool effect_preview_ready = false;
  bool action_ready = false;
  bool raw_pointer_fields_persisted = false;
};

struct MajorDecisionFoundKingdomSnapshotV1 {
  MajorDecisionFoundKingdomStatusV1 status =
      MajorDecisionFoundKingdomStatusV1::unavailable;
  MajorDecisionFoundKingdomFailureV1 unavailable_reason =
      MajorDecisionFoundKingdomFailureV1::observer_disabled;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  std::int32_t played_character_id = -1;
  MajorDecisionEligibilitySourceV1 eligibility_source =
      MajorDecisionEligibilitySourceV1::unknown;
  MajorDecisionTypedBoolV1 is_shown{};
  MajorDecisionTypedBoolV1 is_valid{};
  MajorDecisionTypedBoolV1 is_valid_showing_failures_only{};
  MajorDecisionEvaluatedCostV1 evaluated_cost{};
  MajorDecisionTypedBoolV1 is_affordable{};
  MajorDecisionTypedBoolV1 can_take{};
  MajorDecisionEffectPreviewBoundaryV1 effect_preview{};
  MajorDecisionFoundKingdomReadinessV1 readiness{};
};

bool ObserveMajorDecisionFoundKingdomV1(
    const MajorDecisionFoundKingdomCaptureV1 &capture,
    MajorDecisionFoundKingdomSnapshotV1 &output) noexcept;

std::string SerializeMajorDecisionFoundKingdomV1(
    const MajorDecisionFoundKingdomSnapshotV1 &snapshot);

std::string_view MajorDecisionFoundKingdomFailureKeyV1(
    MajorDecisionFoundKingdomFailureV1 failure) noexcept;

std::string_view MajorDecisionUnknownReasonKeyV1(
    MajorDecisionUnknownReasonV1 reason) noexcept;

} // namespace xar::bridge
