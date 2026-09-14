#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kRealmLawGovernanceSnapshotV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view
    kRealmLawGovernanceSnapshotV1EvidenceRevision =
        "g2_nonreligious_law_contract_succession_native_tree_v1@d2fc0fd";
inline constexpr bool kRealmLawGovernanceSnapshotV1AdvertisedByDefault = false;

inline constexpr std::size_t kRealmLawGovernanceKeyCapacityV1 = 96;
inline constexpr std::size_t kRealmLawGovernanceReasonCapacityV1 = 192;
inline constexpr std::size_t kRealmLawGovernanceSha256CapacityV1 = 65;
inline constexpr std::size_t kRealmLawGovernanceMaximumGroupsV1 = 12;
inline constexpr std::size_t kRealmLawGovernanceMaximumCandidatesV1 = 24;
inline constexpr std::size_t kRealmLawGovernanceMaximumCostsV1 = 6;
inline constexpr std::size_t kRealmLawGovernanceMaximumHeldTitlesV1 = 32;
inline constexpr std::size_t kRealmLawGovernanceMaximumSuccessorsV1 = 16;
inline constexpr std::int64_t kRealmLawGovernanceFixedPointOneV1 = 100'000;

enum class RealmLawGovernanceSnapshotV1Status : std::uint8_t {
  unavailable,
  available,
};

enum class RealmLawGovernanceSnapshotV1Failure : std::uint8_t {
  none,
  exact_build_mismatch,
  source_adapter_unavailable,
  application_main_thread_required,
  not_paused,
  frame_drift,
  played_character_unavailable,
  source_sample_incomplete,
  player_identity_mismatch,
  source_sample_drift,
  group_enumeration_incomplete,
  group_count_invalid,
  group_key_invalid,
  duplicate_group_key,
  active_law_key_invalid,
  candidate_enumeration_incomplete,
  candidate_count_invalid,
  candidate_key_invalid,
  duplicate_candidate_key,
  active_law_mismatch,
  candidate_evaluation_incomplete,
  candidate_legality_invariant_failed,
  candidate_reason_invariant_failed,
  cost_collection_incomplete,
  cost_collection_invalid,
  cost_key_invalid,
  duplicate_cost_key,
  cost_value_invalid,
  succession_shape_invalid,
  title_baseline_incomplete,
  title_baseline_invalid,
  duplicate_title_identity,
  successor_collection_invalid,
  duplicate_successor_identity,
};

enum class RealmLawGovernancePresenceV1 : std::uint8_t {
  unknown,
  absent,
  present,
};

struct RealmLawGovernanceKeyV1 {
  std::uint16_t size = 0;
  std::array<char, kRealmLawGovernanceKeyCapacityV1> bytes{};

  friend bool operator==(const RealmLawGovernanceKeyV1 &,
                         const RealmLawGovernanceKeyV1 &) = default;
};

// The adapter owns the mapping from an engine-final description to this
// opaque copied payload. The core neither localizes nor interprets it.
struct RealmLawGovernanceReasonV1 {
  RealmLawGovernancePresenceV1 presence =
      RealmLawGovernancePresenceV1::unknown;
  std::uint16_t size = 0;
  std::array<char, kRealmLawGovernanceReasonCapacityV1> bytes{};

  friend bool operator==(const RealmLawGovernanceReasonV1 &,
                         const RealmLawGovernanceReasonV1 &) = default;
};

struct RealmLawGovernanceOptionalKeyV1 {
  RealmLawGovernancePresenceV1 presence =
      RealmLawGovernancePresenceV1::unknown;
  RealmLawGovernanceKeyV1 value{};

  friend bool operator==(const RealmLawGovernanceOptionalKeyV1 &,
                         const RealmLawGovernanceOptionalKeyV1 &) = default;
};

struct RealmLawGovernanceOptionalFixedPointV1 {
  RealmLawGovernancePresenceV1 presence =
      RealmLawGovernancePresenceV1::unknown;
  std::int64_t value_raw = 0;

  friend bool operator==(const RealmLawGovernanceOptionalFixedPointV1 &,
                         const RealmLawGovernanceOptionalFixedPointV1 &) =
      default;
};

struct RealmLawGovernanceCurrencyCostV1 {
  RealmLawGovernanceKeyV1 currency_key{};
  // Engine-final fixed-point cost. Zero is a legal observed value.
  std::int64_t amount_raw = 0;

  friend bool operator==(const RealmLawGovernanceCurrencyCostV1 &,
                         const RealmLawGovernanceCurrencyCostV1 &) = default;
};

struct RealmLawGovernanceSuccessionShapeV1 {
  RealmLawGovernancePresenceV1 presence =
      RealmLawGovernancePresenceV1::unknown;
  RealmLawGovernanceKeyV1 order_of_succession{};
  RealmLawGovernanceOptionalKeyV1 title_division{};
  RealmLawGovernanceOptionalKeyV1 traversal_order{};
  RealmLawGovernanceOptionalKeyV1 rank{};
  RealmLawGovernanceOptionalFixedPointV1 primary_heir_minimum_share{};

  friend bool operator==(const RealmLawGovernanceSuccessionShapeV1 &,
                         const RealmLawGovernanceSuccessionShapeV1 &) =
      default;
};

struct RealmLawGovernanceCandidateV1 {
  RealmLawGovernanceKeyV1 law_key{};
  bool is_active = false;
  bool evaluation_complete = false;
  bool can_have = false;
  bool can_pass = false;
  bool can_enact = false;
  RealmLawGovernanceReasonV1 blocked_reason{};
  bool costs_complete = false;
  std::uint32_t cost_count = 0;
  std::array<RealmLawGovernanceCurrencyCostV1,
             kRealmLawGovernanceMaximumCostsV1>
      costs{};
  RealmLawGovernanceSuccessionShapeV1 succession{};

  friend bool operator==(const RealmLawGovernanceCandidateV1 &,
                         const RealmLawGovernanceCandidateV1 &) = default;
};

struct RealmLawGovernanceGroupV1 {
  RealmLawGovernanceKeyV1 group_key{};
  RealmLawGovernanceKeyV1 active_law_key{};
  bool can_change_evaluated = false;
  bool can_change = false;
  bool candidates_complete = false;
  std::uint32_t candidate_count = 0;
  std::array<RealmLawGovernanceCandidateV1,
             kRealmLawGovernanceMaximumCandidatesV1>
      candidates{};

  friend bool operator==(const RealmLawGovernanceGroupV1 &,
                         const RealmLawGovernanceGroupV1 &) = default;
};

struct RealmLawGovernanceHeldTitleSuccessionV1 {
  std::int32_t title_id = -1;
  bool primary = false;
  std::uint32_t successor_count = 0;
  std::array<std::int32_t, kRealmLawGovernanceMaximumSuccessorsV1>
      successor_character_ids{};

  friend bool operator==(const RealmLawGovernanceHeldTitleSuccessionV1 &,
                         const RealmLawGovernanceHeldTitleSuccessionV1 &) =
      default;
};

struct RealmLawGovernanceTitleBaselineV1 {
  RealmLawGovernancePresenceV1 primary_title_presence =
      RealmLawGovernancePresenceV1::unknown;
  std::int32_t primary_title_id = -1;
  std::uint32_t primary_title_successor_count = 0;
  std::array<std::int32_t, kRealmLawGovernanceMaximumSuccessorsV1>
      primary_title_successor_character_ids{};
  std::uint32_t held_title_count = 0;
  std::array<RealmLawGovernanceHeldTitleSuccessionV1,
             kRealmLawGovernanceMaximumHeldTitlesV1>
      held_titles{};

  friend bool operator==(const RealmLawGovernanceTitleBaselineV1 &,
                         const RealmLawGovernanceTitleBaselineV1 &) = default;
};

// This value-only sample is the handoff from a future exact-build adapter.
// It contains copied IDs, fixed strings, booleans and fixed-point values only;
// no native address or borrowed lifetime crosses the handoff.
struct RealmLawGovernanceSourceSampleV1 {
  bool source_read_complete = false;
  std::int32_t played_character_id = -1;
  bool played_character_identity_round_trip = false;
  bool groups_complete = false;
  std::uint32_t group_count = 0;
  std::array<RealmLawGovernanceGroupV1,
             kRealmLawGovernanceMaximumGroupsV1>
      groups{};
  bool title_baseline_complete = false;
  RealmLawGovernanceTitleBaselineV1 title_baseline{};

  friend bool operator==(const RealmLawGovernanceSourceSampleV1 &,
                         const RealmLawGovernanceSourceSampleV1 &) = default;
};

struct RealmLawGovernanceFrameV1 {
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  std::int32_t played_character_id = -1;
  bool played_character_alive = false;
  bool played_character_identity_round_trip = false;

  friend bool operator==(const RealmLawGovernanceFrameV1 &,
                         const RealmLawGovernanceFrameV1 &) = default;
};

// Both samples must be captured from the same paused application-main turn.
// The core publishes neither one unless the complete value copies agree.
struct RealmLawGovernanceCaptureV1 {
  bool exact_build_admitted = false;
  std::array<char, kRealmLawGovernanceSha256CapacityV1>
      admitted_executable_sha256{};
  bool source_adapter_bound = false;
  bool application_main_thread = false;
  RealmLawGovernanceFrameV1 frame_before{};
  RealmLawGovernanceSourceSampleV1 first_sample{};
  RealmLawGovernanceSourceSampleV1 second_sample{};
  RealmLawGovernanceFrameV1 frame_after{};
};

struct RealmLawGovernanceReadinessV1 {
  bool groups_ready = false;
  bool engine_final_legality_ready = false;
  bool engine_final_costs_ready = false;
  bool succession_shapes_ready = false;
  bool title_successor_baseline_ready = false;
  bool same_frame_ready = false;

  friend bool operator==(const RealmLawGovernanceReadinessV1 &,
                         const RealmLawGovernanceReadinessV1 &) = default;
};

struct RealmLawGovernanceSnapshotV1 {
  RealmLawGovernanceSnapshotV1Status status =
      RealmLawGovernanceSnapshotV1Status::unavailable;
  RealmLawGovernanceSnapshotV1Failure unavailable_reason =
      RealmLawGovernanceSnapshotV1Failure::source_adapter_unavailable;
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::uint32_t group_count = 0;
  std::array<RealmLawGovernanceGroupV1,
             kRealmLawGovernanceMaximumGroupsV1>
      groups{};
  RealmLawGovernanceTitleBaselineV1 title_baseline{};
  RealmLawGovernanceReadinessV1 readiness{};
};

bool AssignRealmLawGovernanceKeyV1(
    std::string_view value, RealmLawGovernanceKeyV1 &output) noexcept;

std::string_view RealmLawGovernanceKeyViewV1(
    const RealmLawGovernanceKeyV1 &value) noexcept;

bool AssignRealmLawGovernanceReasonV1(
    std::string_view value, RealmLawGovernanceReasonV1 &output) noexcept;

std::string_view RealmLawGovernanceReasonViewV1(
    const RealmLawGovernanceReasonV1 &value) noexcept;

bool ObserveRealmLawGovernanceSnapshotV1(
    const RealmLawGovernanceCaptureV1 &capture,
    RealmLawGovernanceSnapshotV1 &output) noexcept;

std::string_view RealmLawGovernanceSnapshotV1FailureName(
    RealmLawGovernanceSnapshotV1Failure failure) noexcept;

} // namespace xar::bridge
