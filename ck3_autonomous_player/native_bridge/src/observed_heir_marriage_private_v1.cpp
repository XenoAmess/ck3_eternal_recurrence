#include "xar_bridge/observed_heir_marriage_private_v1.hpp"

namespace xar::bridge {

bool PrepareObservedHeirMarriageSubmissionV1(
    std::int32_t played_character_id, std::int32_t heir_character_id,
    const game::ArrangeMarriageFamilyCandidateV1 &cached,
    const game::ArrangeMarriageFamilyCandidateV1 &fresh,
    const MarriageProposalBilateralRelationshipV1 &before,
    std::uint64_t native_revision, MarriageProposalSubmissionV1 &submission,
    ObservedHeirMarriagePendingV1 &pending) noexcept {
  submission = {};
  pending = {};
  if (native_revision == 0 || played_character_id <= 0 ||
      heir_character_id <= 0 || heir_character_id == played_character_id ||
      cached != fresh || cached.played_character_id != played_character_id ||
      cached.subject_character_id != heir_character_id ||
      cached.candidate_character_id <= 0 ||
      cached.candidate_character_id == played_character_id ||
      cached.candidate_character_id == heir_character_id ||
      cached.recipient_matchmaker_character_id <= 0 ||
      cached.intermediary_character_id != -1 || !cached.complete_can_send ||
      !cached.recipient_answer_allows_send ||
      cached.recipient_answer_status_raw > 1 ||
      before.subject_character_id !=
          static_cast<std::uint32_t>(heir_character_id) ||
      before.candidate_character_id !=
          static_cast<std::uint32_t>(cached.candidate_character_id) ||
      !before.subject_identity_round_trip ||
      !before.candidate_identity_round_trip || !before.subject_alive ||
      !before.candidate_alive || before.subject_has_candidate_as_spouse ||
      before.candidate_has_subject_as_spouse ||
      before.subject_has_candidate_as_betrothed ||
      before.candidate_has_subject_as_betrothed) {
    return false;
  }
  submission.subject_character_id =
      static_cast<std::uint32_t>(heir_character_id);
  submission.candidate_character_id =
      static_cast<std::uint32_t>(cached.candidate_character_id);
  submission.rankless_observed_heir = true;
  submission.native_rank = 0;
  submission.roles.actor_character_id =
      static_cast<std::uint32_t>(played_character_id);
  submission.roles.recipient_character_id = static_cast<std::uint32_t>(
      cached.recipient_matchmaker_character_id);
  submission.roles.secondary_actor_character_id =
      static_cast<std::uint32_t>(heir_character_id);
  submission.roles.secondary_recipient_character_id =
      static_cast<std::uint32_t>(cached.candidate_character_id);
  submission.roles.intermediary_character_id = 0; // native -1 sentinel
  submission.recipient_ai_accept_raw = cached.recipient_ai_accept_raw;
  submission.recipient_answer_status_raw =
      cached.recipient_answer_status_raw;
  submission.predicted_outcome = MarriagePredictedOutcomeV1::unavailable;
  pending.pre_native_revision = native_revision;
  pending.played_character_id = played_character_id;
  pending.heir_character_id = heir_character_id;
  pending.candidate_character_id = cached.candidate_character_id;
  pending.recipient_character_id =
      cached.recipient_matchmaker_character_id;
  return true;
}

#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
bool PrepareCurrentFirstHeirBetrothalFulfillmentSubmissionV1(
    std::int32_t played_character_id, std::int32_t heir_character_id,
    const ck3_11906::CurrentFirstHeirBetrothalActionabilityReadV1 &cached,
    const ck3_11906::CurrentFirstHeirBetrothalActionabilityReadV1 &fresh,
    const MarriageProposalBilateralRelationshipV1 &before,
    std::uint64_t native_revision, MarriageProposalSubmissionV1 &submission,
    ObservedHeirMarriagePendingV1 &pending) noexcept {
  submission = {};
  pending = {};
  if (native_revision == 0 || played_character_id <= 0 ||
      heir_character_id <= 0 || played_character_id == heir_character_id ||
      cached != fresh || !cached.has_betrothal || !cached.unavailable_reason.empty() ||
      cached.actor_character_id != played_character_id ||
      cached.heir_character_id != heir_character_id ||
      cached.partner_character_id <= 0 || cached.partner_character_id == heir_character_id ||
      cached.partner_character_id == played_character_id ||
      cached.recipient_character_id <= 0 || cached.intermediary_character_id == 0 ||
      cached.intermediary_character_id < -1 ||
      !cached.adult_readback_available || !cached.adult.subject_is_adult ||
      !cached.adult.candidate_is_adult || !cached.final_legality_sampled ||
      !cached.complete_can_send || !cached.recipient_acceptance_ready ||
      cached.recipient_answer_status_raw > 1 || !cached.generic_costs_available ||
      !cached.outcome_available || !cached.lineality_available ||
      cached.adult.predicted_outcome != MarriagePredictedOutcomeV1::marriage ||
      before.subject_character_id != static_cast<std::uint32_t>(heir_character_id) ||
      before.candidate_character_id != static_cast<std::uint32_t>(cached.partner_character_id) ||
      !before.subject_identity_round_trip || !before.candidate_identity_round_trip ||
      !before.subject_alive || !before.candidate_alive ||
      before.subject_has_candidate_as_spouse || before.candidate_has_subject_as_spouse ||
      !before.subject_has_candidate_as_betrothed || !before.candidate_has_subject_as_betrothed)
    return false;
  submission.subject_character_id = static_cast<std::uint32_t>(heir_character_id);
  submission.candidate_character_id = static_cast<std::uint32_t>(cached.partner_character_id);
  submission.rankless_observed_heir = true;
  submission.roles.actor_character_id = static_cast<std::uint32_t>(played_character_id);
  submission.roles.recipient_character_id = static_cast<std::uint32_t>(cached.recipient_character_id);
  submission.roles.secondary_actor_character_id = submission.subject_character_id;
  submission.roles.secondary_recipient_character_id = submission.candidate_character_id;
  submission.roles.intermediary_character_id = cached.intermediary_character_id == -1
      ? 0 : static_cast<std::uint32_t>(cached.intermediary_character_id);
  submission.recipient_ai_accept_raw = cached.recipient_ai_accept_raw;
  submission.recipient_answer_status_raw = cached.recipient_answer_status_raw;
  submission.predicted_outcome = MarriagePredictedOutcomeV1::marriage;
  submission.fulfill_existing_betrothal = true;
  submission.expected_effective_matrilineal = cached.effective_matrilineal_if_accepted;
  pending.pre_native_revision = native_revision;
  pending.played_character_id = played_character_id;
  pending.heir_character_id = heir_character_id;
  pending.candidate_character_id = cached.partner_character_id;
  pending.recipient_character_id = cached.recipient_character_id;
  pending.matrilineal_option_selected = cached.effective_matrilineal_if_accepted;
  pending.fulfill_existing_betrothal = true;
  return true;
}
#endif

ObservedHeirMarriageMaterialStatusV1 ReadObservedHeirMarriageMaterialStatusV1(
    const ObservedHeirMarriagePendingV1 &pending,
    const MarriageProposalBilateralRelationshipV1 &after,
    std::uint64_t after_native_revision,
    MarriageProposalNativeResolutionV1 resolution,
    bool cold_recovery) noexcept {
  if ((!cold_recovery && (pending.pre_native_revision == 0 ||
                         after_native_revision <= pending.pre_native_revision)) ||
      after_native_revision == 0 ||
      pending.heir_character_id <= 0 || pending.candidate_character_id <= 0 ||
      after.subject_character_id !=
          static_cast<std::uint32_t>(pending.heir_character_id) ||
      after.candidate_character_id !=
          static_cast<std::uint32_t>(pending.candidate_character_id) ||
      !after.subject_identity_round_trip ||
      !after.candidate_identity_round_trip || !after.subject_alive ||
      !after.candidate_alive) {
    return ObservedHeirMarriageMaterialStatusV1::inconsistent;
  }
  const bool mutual_spouse = after.subject_has_candidate_as_spouse &&
                             after.candidate_has_subject_as_spouse;
  const bool mutual_betrothed =
      after.subject_has_candidate_as_betrothed &&
      after.candidate_has_subject_as_betrothed;
  if (after.subject_has_candidate_as_spouse !=
          after.candidate_has_subject_as_spouse ||
      after.subject_has_candidate_as_betrothed !=
          after.candidate_has_subject_as_betrothed ||
      (mutual_spouse && mutual_betrothed)) {
    return ObservedHeirMarriageMaterialStatusV1::inconsistent;
  }
  if (mutual_spouse) return ObservedHeirMarriageMaterialStatusV1::marriage;
  if (mutual_betrothed && !pending.fulfill_existing_betrothal)
    return ObservedHeirMarriageMaterialStatusV1::betrothal;
  if (!cold_recovery) {
    if (resolution == MarriageProposalNativeResolutionV1::accepted)
      return ObservedHeirMarriageMaterialStatusV1::accepted_pending;
    if (resolution == MarriageProposalNativeResolutionV1::refused)
      return ObservedHeirMarriageMaterialStatusV1::refused;
    if (resolution == MarriageProposalNativeResolutionV1::invalidated)
      return ObservedHeirMarriageMaterialStatusV1::invalidated;
  }
  return ObservedHeirMarriageMaterialStatusV1::pending;
}

} // namespace xar::bridge
