#pragma once

#include "xar_bridge/council_composition_steward_candidates_reader_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class CouncilCompositionCandidatesPublicStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class CouncilCompositionCandidatesPublicFailureV1 : std::uint32_t {
  none = 0,
  private_reader_unavailable,
  enrichment_unavailable,
  same_frame_binding_mismatch,
  incumbent_invalid,
  candidate_set_mismatch,
  candidate_eligibility_unready,
  candidate_main_skill_unready,
  schema_invariant_failed,
};

enum class CouncilCompositionCandidateEligibilityReasonV1 : std::uint32_t {
  native_candidate_provider_accepted = 0,
};

enum class CouncilCompositionCandidateActionRouteV1 : std::uint32_t {
  assign = 0,
  replace = 1,
};

struct CouncilCompositionCandidateMainSkillV1 {
  std::array<char, 32> key{};
  std::int32_t value = 0;

  friend bool operator==(const CouncilCompositionCandidateMainSkillV1 &,
                         const CouncilCompositionCandidateMainSkillV1 &) =
      default;
};

struct CouncilCompositionCandidatePublicRowV1 {
  std::int32_t character_id = -1;
  std::uint32_t native_collection_ordinal = 0;
  bool eligible = false;
  CouncilCompositionCandidateEligibilityReasonV1 eligibility_reason =
      CouncilCompositionCandidateEligibilityReasonV1::
          native_candidate_provider_accepted;
  CouncilCompositionCandidateMainSkillV1 main_skill{};
  CouncilCompositionCandidateActionRouteV1 action_route =
      CouncilCompositionCandidateActionRouteV1::assign;

  friend bool operator==(const CouncilCompositionCandidatePublicRowV1 &,
                         const CouncilCompositionCandidatePublicRowV1 &) =
      default;
};

struct CouncilCompositionCandidatesPublicReadinessV1 {
  bool identity_ready = false;
  bool candidate_collection_ready = false;
  bool incumbent_ready = false;
  bool candidate_legality_ready = false;
  bool main_skill_ready = false;
  bool action_route_ready = false;
  bool same_frame_ready = false;
  bool ready = false;

  friend bool operator==(const CouncilCompositionCandidatesPublicReadinessV1 &,
                         const CouncilCompositionCandidatesPublicReadinessV1 &) =
      default;
};

struct CouncilCompositionCandidatesPublicV1 {
  CouncilCompositionCandidatesPublicStatusV1 status =
      CouncilCompositionCandidatesPublicStatusV1::unavailable;
  CouncilCompositionCandidatesPublicFailureV1 unavailable_reason =
      CouncilCompositionCandidatesPublicFailureV1::none;
  CouncilCompositionStewardCandidatesFailureV1 source_unavailable_reason =
      CouncilCompositionStewardCandidatesFailureV1::none;
  std::array<char, kCouncilCompositionStewardSnapshotIdCapacityV1>
      snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  bool paused = false;
  std::int32_t owner_character_id = -1;
  std::array<char, kCouncilCompositionStewardPositionKeyCapacityV1>
      position_key{};
  std::int32_t incumbent_character_id = -1;
  bool vacant = false;
  CouncilCompositionCandidateActionRouteV1 action_route =
      CouncilCompositionCandidateActionRouteV1::assign;
  bool candidate_collection_complete = false;
  std::uint32_t candidate_count = 0;
  std::array<CouncilCompositionCandidatePublicRowV1,
             kCouncilCompositionStewardCandidatesMaximumRowsV1>
      candidates{};
  CouncilCompositionCandidatesPublicReadinessV1 readiness{};
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kCouncilCompositionCandidatesPublicCapabilityV1 =
        "game.query.council-composition-candidates-v1";
inline constexpr std::string_view kCouncilCompositionCandidatesPublicSchemaV1 =
    "xar.ck3.council-composition-candidates/v1";
inline constexpr std::string_view
    kCouncilCompositionCandidatesPublicPositionKeyV1 = "councillor_steward";
inline constexpr std::string_view
    kCouncilCompositionCandidatesPublicMainSkillKeyV1 = "stewardship";
inline constexpr std::string_view
    kCouncilCompositionCandidatesPublicGameVersionV1 = "1.19.0.6";
inline constexpr std::string_view
    kCouncilCompositionCandidatesPublicExecutableSha256V1 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

// The native enrichment producer must sample these fields inside the same
// application-main transaction as the private candidate reader.  This public
// projector never treats a later campaign-root frame as equivalent.
struct CouncilCompositionCandidatePublicEnrichmentRowV1 {
  std::int32_t character_id = -1;
  std::uint32_t native_collection_ordinal = 0;
  bool final_eligible = false;
  game::CouncilCompositionCandidateEligibilityReasonV1 eligibility_reason =
      game::CouncilCompositionCandidateEligibilityReasonV1::
          native_candidate_provider_accepted;
  std::int32_t main_skill = 0;
};

struct CouncilCompositionCandidatesPublicEnrichmentV1 {
  std::array<char, game::kCouncilCompositionStewardSnapshotIdCapacityV1>
      snapshot_id{};
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t owner_character_id = -1;
  std::array<char, game::kCouncilCompositionStewardPositionKeyCapacityV1>
      position_key{};
  std::int32_t incumbent_character_id = -1;
  bool incumbent_ready = false;
  bool same_frame_stable = false;
  std::uint32_t candidate_count = 0;
  std::array<CouncilCompositionCandidatePublicEnrichmentRowV1,
             game::kCouncilCompositionStewardCandidatesMaximumRowsV1>
      candidates{};
};

enum class ProjectCouncilCompositionCandidatesPublicResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

ProjectCouncilCompositionCandidatesPublicResultV1
ProjectCouncilCompositionCandidatesPublicV1(
    const game::CouncilCompositionStewardCandidatesV1 &private_result,
    const CouncilCompositionCandidatesPublicEnrichmentV1 &enrichment,
    game::CouncilCompositionCandidatesPublicV1 &output) noexcept;

std::string_view CouncilCompositionCandidatesPublicFailureKeyV1(
    game::CouncilCompositionCandidatesPublicFailureV1 reason) noexcept;
std::string_view CouncilCompositionCandidateEligibilityReasonKeyV1(
    game::CouncilCompositionCandidateEligibilityReasonV1 reason) noexcept;
std::string_view CouncilCompositionCandidateActionRouteKeyV1(
    game::CouncilCompositionCandidateActionRouteV1 route) noexcept;

std::string SerializeCouncilCompositionCandidatesPublicV1(
    const game::CouncilCompositionCandidatesPublicV1 &value);

} // namespace xar::ck3_11906
