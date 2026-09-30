#pragma once

#include "xar_bridge/game_contract.hpp"
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_11906.hpp"
#endif
#include "xar_bridge/marriage_proposal_native_binder_v1.hpp"

#include <cstdint>

namespace xar::bridge {

// This is an unadvertised, exact-build proposal for the player's observed
// first heir. The human player has no native matchmaking rank; rank zero is
// deliberately not interpreted as a score or preference.
struct ObservedHeirMarriagePendingV1 {
  std::uint64_t pre_native_revision = 0;
  std::int32_t played_character_id = -1;
  std::int32_t heir_character_id = -1;
  std::int32_t candidate_character_id = -1;
  std::int32_t recipient_character_id = -1;
  bool matrilineal_option_selected = false;
  bool fulfill_existing_betrothal = false;
};

enum class ObservedHeirMarriageMaterialStatusV1 : std::uint8_t {
  pending = 0,
  marriage = 1,
  betrothal = 2,
  inconsistent = 3,
  refused = 4,
  invalidated = 5,
  accepted_pending = 6,
};

bool PrepareObservedHeirMarriageSubmissionV1(
    std::int32_t played_character_id, std::int32_t heir_character_id,
    const game::ArrangeMarriageFamilyCandidateV1 &cached,
    const game::ArrangeMarriageFamilyCandidateV1 &fresh,
    const MarriageProposalBilateralRelationshipV1 &before,
    std::uint64_t native_revision, MarriageProposalSubmissionV1 &submission,
    ObservedHeirMarriagePendingV1 &pending) noexcept;

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
// Fixed current pair only; no ranked candidate inventory or option mutation.
bool PrepareCurrentFirstHeirBetrothalFulfillmentSubmissionV1(
    std::int32_t played_character_id, std::int32_t heir_character_id,
    const ck3_11906::CurrentFirstHeirBetrothalActionabilityReadV1 &cached,
    const ck3_11906::CurrentFirstHeirBetrothalActionabilityReadV1 &fresh,
    const MarriageProposalBilateralRelationshipV1 &before,
    std::uint64_t native_revision, MarriageProposalSubmissionV1 &submission,
    ObservedHeirMarriagePendingV1 &pending) noexcept;
#endif

ObservedHeirMarriageMaterialStatusV1 ReadObservedHeirMarriageMaterialStatusV1(
    const ObservedHeirMarriagePendingV1 &pending,
    const MarriageProposalBilateralRelationshipV1 &after,
    std::uint64_t after_native_revision,
    MarriageProposalNativeResolutionV1 resolution =
        MarriageProposalNativeResolutionV1::pending,
    bool cold_recovery = false) noexcept;

} // namespace xar::bridge
