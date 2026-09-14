#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kMarriageMatchmakingObserverPrivateKeyV1 =
    "marriage_matchmaking_observer_v1";
inline constexpr std::string_view kMarriageMatchmakingObserverGameVersionV1 =
    "1.19.0.6";
inline constexpr std::string_view
    kMarriageMatchmakingObserverExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

inline constexpr std::uintptr_t kMarriageCandidateEnumeratorRvaV1 =
    0x1890470;
inline constexpr std::uintptr_t kMarriageCandidateScoreFilterRvaV1 =
    0x1890D90;
inline constexpr std::uintptr_t kMarriageCandidateGateAndScoreRvaV1 =
    0x1890F40;
inline constexpr std::uintptr_t kMarriageCompleteCanSendRvaV1 = 0x2C43F00;
inline constexpr std::uintptr_t kMarriageRecipientAiAcceptRvaV1 = 0x2C44320;
inline constexpr std::uintptr_t kMarriageOuterAnswerRvaV1 = 0x2C43B40;
inline constexpr std::uintptr_t kMarriageOutcomeDispatchRvaV1 = 0x2282DE0;

inline constexpr std::uintptr_t kMarriageProductionEnumerationCallsiteRvaV1 =
    0x18FA4C3;
inline constexpr std::uintptr_t kMarriageProductionScoreCallsiteRvaV1 =
    0x18FAF36;
inline constexpr std::uintptr_t kMarriageProductionAiAcceptCallsiteRvaV1 =
    0x18FA932;
inline constexpr std::uintptr_t kMarriageProductionCanSendCallsiteRvaV1 =
    0x18FAB4C;

inline constexpr std::size_t kMarriageNativeRankedRowStrideV1 = 16;
inline constexpr std::size_t kMarriageNativeRankedRowCharacterIdOffsetV1 = 8;
inline constexpr std::size_t kMarriageNativeRankedRowScoreOffsetV1 = 12;
inline constexpr std::uint32_t kMarriageMatchmakingMaximumCandidatesV1 = 8;
inline constexpr std::size_t kMarriageMatchmakingSnapshotIdCapacityV1 = 48;
inline constexpr std::int32_t kMarriageAiAcceptFixedPointScaleV1 = 100000;

enum class MarriageMatchmakingObserverStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class MarriageMatchmakingObserverFailureV1 : std::uint32_t {
  none = 0,
  invalid_request,
  exact_build_not_admitted,
  native_entry_points_unavailable,
  application_main_thread_required,
  frame_capture_failed,
  snapshot_identity_mismatch,
  revision_drift,
  date_drift,
  not_paused,
  player_unavailable,
  ranked_source_unavailable,
  native_ranked_source_failed,
  native_sample_drift,
  candidate_collection_invalid,
  pair_evaluation_failed,
  pair_roles_invalid,
};

enum class MarriageNativeSourceResultV1 : std::uint32_t {
  failed = 0,
  available = 1,
  ranked_source_unavailable = 2,
};

enum class MarriageNativeEvaluationResultV1 : std::uint32_t {
  failed = 0,
  available = 1,
};

enum class MarriagePredictedOutcomeV1 : std::uint32_t {
  unavailable = 0,
  marriage = 1,
  betrothal = 2,
};

struct MarriageMatchmakingNativeEntryPointsV1 {
  std::uintptr_t enumerate_candidates = 0;
  std::uintptr_t score_filter_candidates = 0;
  std::uintptr_t candidate_gate_and_score = 0;
  std::uintptr_t complete_can_send = 0;
  std::uintptr_t recipient_ai_accept = 0;
  std::uintptr_t outer_answer = 0;
  std::uintptr_t outcome_dispatch = 0;

  friend bool operator==(const MarriageMatchmakingNativeEntryPointsV1 &,
                         const MarriageMatchmakingNativeEntryPointsV1 &) =
      default;
};

struct MarriageMatchmakingFrameV1 {
  std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  bool map_ready = false;
  bool has_played_character = false;
  bool played_character_alive = false;
  std::uint32_t played_character_id = 0;
  bool played_character_identity_round_trip = false;

  friend bool operator==(const MarriageMatchmakingFrameV1 &,
                         const MarriageMatchmakingFrameV1 &) = default;
};

struct MarriageMatchmakingPairRolesV1 {
  std::uint32_t actor_character_id = 0;
  std::uint32_t recipient_character_id = 0;
  std::uint32_t secondary_actor_character_id = 0;
  std::uint32_t secondary_recipient_character_id = 0;
  std::uint32_t intermediary_character_id = 0;

  friend bool operator==(const MarriageMatchmakingPairRolesV1 &,
                         const MarriageMatchmakingPairRolesV1 &) = default;
};

struct MarriageMatchmakingPairEvaluationV1 {
  MarriageMatchmakingPairRolesV1 roles{};
  bool complete_can_send = false;
  std::int32_t complete_can_send_status_raw = 0;
  std::int32_t recipient_ai_accept_raw = 0;
  std::int32_t recipient_answer_status_raw = 0;
  bool recipient_answer_allows_send = false;
  MarriagePredictedOutcomeV1 predicted_outcome =
      MarriagePredictedOutcomeV1::unavailable;

  friend bool operator==(const MarriageMatchmakingPairEvaluationV1 &,
                         const MarriageMatchmakingPairEvaluationV1 &) =
      default;
};

struct MarriageMatchmakingRankedRowV1 {
  std::uint32_t candidate_character_id = 0;
  std::int32_t native_candidate_score = 0;

  friend bool operator==(const MarriageMatchmakingRankedRowV1 &,
                         const MarriageMatchmakingRankedRowV1 &) = default;
};

struct MarriageMatchmakingNativeSampleV1 {
  std::uint32_t subject_character_id = 0;
  std::uint32_t matchmaker_character_id = 0;
  std::uint32_t candidate_count = 0;
  std::array<MarriageMatchmakingRankedRowV1,
             kMarriageMatchmakingMaximumCandidatesV1>
      candidates{};
  std::array<MarriageMatchmakingPairEvaluationV1,
             kMarriageMatchmakingMaximumCandidatesV1>
      evaluations{};

  friend bool operator==(const MarriageMatchmakingNativeSampleV1 &,
                         const MarriageMatchmakingNativeSampleV1 &) =
      default;
};

struct MarriageMatchmakingCandidateV1 {
  std::uint32_t rank = 0;
  std::uint32_t subject_character_id = 0;
  std::uint32_t matchmaker_character_id = 0;
  std::uint32_t candidate_character_id = 0;
  std::int32_t native_candidate_score = 0;
  MarriageMatchmakingPairEvaluationV1 evaluation{};

  friend bool operator==(const MarriageMatchmakingCandidateV1 &,
                         const MarriageMatchmakingCandidateV1 &) = default;
};

struct MarriageMatchmakingObserverReadinessV1 {
  bool ranked_candidates_ready = false;
  bool pair_character_ids_ready = false;
  bool native_score_ready = false;
  bool complete_can_send_ready = false;
  bool recipient_ai_accept_ready = false;
  bool recipient_answer_ready = false;
  bool predicted_outcome_ready = false;
  bool same_frame_ready = false;

  friend bool operator==(const MarriageMatchmakingObserverReadinessV1 &,
                         const MarriageMatchmakingObserverReadinessV1 &) =
      default;
};

struct MarriageMatchmakingObservationV1 {
  MarriageMatchmakingObserverStatusV1 status =
      MarriageMatchmakingObserverStatusV1::unavailable;
  MarriageMatchmakingObserverFailureV1 unavailable_reason =
      MarriageMatchmakingObserverFailureV1::none;
  std::array<char, kMarriageMatchmakingSnapshotIdCapacityV1> snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t subject_character_id = 0;
  std::uint32_t matchmaker_character_id = 0;
  std::uint32_t candidate_count = 0;
  std::array<MarriageMatchmakingCandidateV1,
             kMarriageMatchmakingMaximumCandidatesV1>
      candidates{};
  MarriageMatchmakingObserverReadinessV1 readiness{};
};

struct MarriageMatchmakingObserverEnvironmentV1 {
  bool exact_build_admitted = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  MarriageMatchmakingNativeEntryPointsV1 native{};
};

struct MarriageMatchmakingObserverRequestV1 {
  std::string_view expected_snapshot_id{};
  std::uint64_t expected_public_revision = 0;
  std::uint64_t expected_native_revision = 0;
  std::int32_t expected_date_raw = 0;
  std::uint32_t subject_character_id = 0;
  std::uint32_t matchmaker_character_id = 0;
  std::uint32_t limit = kMarriageMatchmakingMaximumCandidatesV1;
  std::uint32_t candidate_character_id = 0;
};

using CaptureMarriageMatchmakingFrameV1 = bool (*)(
    void *context, MarriageMatchmakingFrameV1 &output) noexcept;
using IsMarriageMatchmakingMainThreadV1 = bool (*)(void *context) noexcept;
using ReadMarriageRankedCandidatesV1 = MarriageNativeSourceResultV1 (*)(
    void *context,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    std::uint32_t subject_character_id, std::uint32_t limit,
    std::array<MarriageMatchmakingRankedRowV1,
               kMarriageMatchmakingMaximumCandidatesV1> &output,
    std::uint32_t &output_count) noexcept;
using EvaluateMarriageCandidateV1 = MarriageNativeEvaluationResultV1 (*)(
    void *context,
    const MarriageMatchmakingNativeEntryPointsV1 &native_entry_points,
    std::uint32_t subject_character_id, std::uint32_t matchmaker_character_id,
    std::uint32_t candidate_character_id,
    MarriageMatchmakingPairEvaluationV1 &output) noexcept;

struct MarriageMatchmakingObserverAccessV1 {
  void *context = nullptr;
  CaptureMarriageMatchmakingFrameV1 capture_frame = nullptr;
  IsMarriageMatchmakingMainThreadV1 is_main_thread = nullptr;
  ReadMarriageRankedCandidatesV1 read_ranked_candidates = nullptr;
  EvaluateMarriageCandidateV1 evaluate_candidate = nullptr;
};

MarriageMatchmakingNativeEntryPointsV1
BindMarriageMatchmakingNativeEntryPointsV1(std::uintptr_t module_base) noexcept;

bool ReadMarriageMatchmakingObserverV1(
    const MarriageMatchmakingObserverEnvironmentV1 &environment,
    const MarriageMatchmakingObserverAccessV1 &access,
    const MarriageMatchmakingObserverRequestV1 &request,
    MarriageMatchmakingObservationV1 &output) noexcept;

std::string_view MarriageMatchmakingObserverFailureKeyV1(
    MarriageMatchmakingObserverFailureV1 failure) noexcept;

std::string_view MarriagePredictedOutcomeKeyV1(
    MarriagePredictedOutcomeV1 outcome) noexcept;

std::string SerializeMarriageMatchmakingObservationV1(
    const MarriageMatchmakingObservationV1 &observation);

} // namespace xar::bridge
