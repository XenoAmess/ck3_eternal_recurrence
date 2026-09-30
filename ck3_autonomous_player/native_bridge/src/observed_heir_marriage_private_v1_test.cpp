#include "xar_bridge/observed_heir_marriage_private_v1.hpp"

#include <cstdlib>

int main() {
  using namespace xar::bridge;
  xar::game::ArrangeMarriageFamilyCandidateV1 row{};
  row.played_character_id = 101;
  row.subject_character_id = 202;
  row.candidate_character_id = 303;
  row.recipient_matchmaker_character_id = 404;
  row.intermediary_character_id = -1;
  row.recipient_ai_accept_raw = 3'600'000'000LL;
  row.recipient_answer_status_raw = 0; // exact-build native acceptance
  row.complete_can_send = true;
  row.recipient_answer_allows_send = true;
  MarriageProposalBilateralRelationshipV1 before{};
  before.subject_character_id = 202;
  before.candidate_character_id = 303;
  before.subject_identity_round_trip = true;
  before.candidate_identity_round_trip = true;
  before.subject_alive = true;
  before.candidate_alive = true;
  MarriageProposalSubmissionV1 submission{};
  ObservedHeirMarriagePendingV1 pending{};
  if (!PrepareObservedHeirMarriageSubmissionV1(
          101, 202, row, row, before, 7, submission, pending) ||
      !submission.rankless_observed_heir || submission.native_rank != 0 ||
      submission.predicted_outcome != MarriagePredictedOutcomeV1::unavailable ||
      submission.roles.actor_character_id != 101 ||
      submission.roles.recipient_character_id != 404 ||
      submission.roles.secondary_actor_character_id != 202 ||
      submission.roles.secondary_recipient_character_id != 303 ||
      submission.roles.intermediary_character_id != 0 ||
      submission.recipient_ai_accept_raw != 3'600'000'000LL ||
      submission.recipient_answer_status_raw != 0) {
    return EXIT_FAILURE;
  }
  auto changed = row;
  changed.recipient_answer_status_raw = 2;
  changed.recipient_answer_allows_send = false;
  if (PrepareObservedHeirMarriageSubmissionV1(
          101, 202, row, changed, before, 7, submission, pending)) {
    return EXIT_FAILURE;
  }
  changed = row;
  changed.intermediary_character_id = 505;
  if (PrepareObservedHeirMarriageSubmissionV1(
          101, 202, changed, changed, before, 7, submission, pending)) {
    return EXIT_FAILURE;
  }
  auto existing = before;
  existing.subject_has_candidate_as_spouse = true;
  existing.candidate_has_subject_as_spouse = true;
  if (PrepareObservedHeirMarriageSubmissionV1(
          101, 202, row, row, existing, 7, submission, pending) ||
      !PrepareObservedHeirMarriageSubmissionV1(
          101, 202, row, row, before, 7, submission, pending)) {
    return EXIT_FAILURE;
  }
  if (ReadObservedHeirMarriageMaterialStatusV1(pending, before, 8) !=
          ObservedHeirMarriageMaterialStatusV1::pending ||
      ReadObservedHeirMarriageMaterialStatusV1(pending, before, 7) !=
          ObservedHeirMarriageMaterialStatusV1::inconsistent) {
    return EXIT_FAILURE;
  }
  auto after = before;
  after.subject_has_candidate_as_spouse = true;
  if (ReadObservedHeirMarriageMaterialStatusV1(pending, after, 8) !=
      ObservedHeirMarriageMaterialStatusV1::inconsistent) {
    return EXIT_FAILURE;
  }
  after.candidate_has_subject_as_spouse = true;
  if (ReadObservedHeirMarriageMaterialStatusV1(pending, after, 8) !=
      ObservedHeirMarriageMaterialStatusV1::marriage) {
    return EXIT_FAILURE;
  }
  after = before;
  after.subject_has_candidate_as_betrothed = true;
  after.candidate_has_subject_as_betrothed = true;
  if (ReadObservedHeirMarriageMaterialStatusV1(pending, after, 8) !=
      ObservedHeirMarriageMaterialStatusV1::betrothal) {
    return EXIT_FAILURE;
  }
  if (ReadObservedHeirMarriageMaterialStatusV1(
          pending, before, 8, MarriageProposalNativeResolutionV1::refused) !=
          ObservedHeirMarriageMaterialStatusV1::refused ||
      ReadObservedHeirMarriageMaterialStatusV1(
          pending, before, 8, MarriageProposalNativeResolutionV1::accepted) !=
          ObservedHeirMarriageMaterialStatusV1::accepted_pending ||
      ReadObservedHeirMarriageMaterialStatusV1(
          pending, before, 1, MarriageProposalNativeResolutionV1::pending,
          true) != ObservedHeirMarriageMaterialStatusV1::pending ||
      ReadObservedHeirMarriageMaterialStatusV1(
          pending, after, 1, MarriageProposalNativeResolutionV1::pending,
          true) != ObservedHeirMarriageMaterialStatusV1::betrothal) {
    return EXIT_FAILURE;
  }
  // The old new-proposal path remains unable to reuse an existing betrothal.
  if (PrepareObservedHeirMarriageSubmissionV1(
          101, 202, row, row, after, 7, submission, pending))
    return EXIT_FAILURE;
#if defined(XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1)
  xar::ck3_11906::CurrentFirstHeirBetrothalActionabilityReadV1 actual{};
  actual.has_betrothal = true;
  actual.unavailable_reason = {};
  actual.actor_character_id = 101;
  actual.heir_character_id = 202;
  actual.partner_character_id = 303;
  actual.recipient_character_id = 404;
  actual.adult_readback_available = true;
  actual.adult.subject_is_adult = true;
  actual.adult.candidate_is_adult = true;
  actual.adult.subject_adult_measure_raw = 19;
  actual.adult.candidate_adult_measure_raw = 21;
  actual.adult.subject_adult_threshold_raw = 19;
  actual.adult.candidate_adult_threshold_raw = 20;
  actual.adult.predicted_outcome = MarriagePredictedOutcomeV1::marriage;
  actual.final_legality_sampled = true;
  actual.complete_can_send = true;
  actual.recipient_acceptance_ready = true;
  actual.recipient_answer_status_raw = 0;
  actual.recipient_ai_accept_raw = 3'600'000'000LL;
  actual.generic_costs_available = true;
  actual.generic_cost_raw[0] = 123456;
  actual.generic_cost_raw[9] = -456789;
  actual.outcome_available = true;
  actual.lineality_available = true;
  actual.effective_matrilineal_if_accepted = true;
  auto existing_betrothal = before;
  existing_betrothal.subject_has_candidate_as_betrothed = true;
  existing_betrothal.candidate_has_subject_as_betrothed = true;
  auto prepare = [&](const auto &cached, const auto &fresh,
                     const auto &baseline) {
    return PrepareCurrentFirstHeirBetrothalFulfillmentSubmissionV1(
        101, 202, cached, fresh, baseline, 7, submission, pending);
  };
  if (!prepare(actual, actual, existing_betrothal) ||
      !submission.fulfill_existing_betrothal || !pending.fulfill_existing_betrothal ||
      !submission.expected_effective_matrilineal || !pending.matrilineal_option_selected ||
      submission.request_matrilineal_option || submission.require_matrilineal_option_off ||
      submission.recipient_ai_accept_raw != 3'600'000'000LL ||
      submission.predicted_outcome != MarriagePredictedOutcomeV1::marriage)
    return EXIT_FAILURE;
  auto changed_actual = actual;
  changed_actual.generic_cost_raw[9] += 1;
  if (prepare(actual, changed_actual, existing_betrothal)) return EXIT_FAILURE;
  changed_actual = actual;
  changed_actual.adult.candidate_is_adult = false;
  if (prepare(changed_actual, changed_actual, existing_betrothal)) return EXIT_FAILURE;
  changed_actual = actual;
  changed_actual.complete_can_send = false;
  if (prepare(changed_actual, changed_actual, existing_betrothal)) return EXIT_FAILURE;
  changed_actual = actual;
  changed_actual.recipient_answer_status_raw = 2;
  if (prepare(changed_actual, changed_actual, existing_betrothal)) return EXIT_FAILURE;
  changed_actual = actual;
  changed_actual.adult.predicted_outcome = MarriagePredictedOutcomeV1::betrothal;
  if (prepare(changed_actual, changed_actual, existing_betrothal) ||
      prepare(actual, actual, before)) return EXIT_FAILURE;
  changed_actual = actual;
  changed_actual.partner_character_id = 505;
  if (prepare(changed_actual, changed_actual, existing_betrothal)) return EXIT_FAILURE;
  changed_actual = actual;
  changed_actual.intermediary_character_id = 505;
  if (!prepare(changed_actual, changed_actual, existing_betrothal) ||
      submission.roles.intermediary_character_id != 505) return EXIT_FAILURE;
  if (!prepare(actual, actual, existing_betrothal)) return EXIT_FAILURE;
  // Existing betrothal does not prove a fulfillment effect in either PID.
  if (ReadObservedHeirMarriageMaterialStatusV1(pending, existing_betrothal, 8) !=
          ObservedHeirMarriageMaterialStatusV1::pending ||
      ReadObservedHeirMarriageMaterialStatusV1(pending, existing_betrothal, 1,
          MarriageProposalNativeResolutionV1::accepted, true) !=
          ObservedHeirMarriageMaterialStatusV1::pending ||
      ReadObservedHeirMarriageMaterialStatusV1(pending, existing_betrothal, 8,
          MarriageProposalNativeResolutionV1::accepted) !=
          ObservedHeirMarriageMaterialStatusV1::accepted_pending ||
      ReadObservedHeirMarriageMaterialStatusV1(pending, existing_betrothal, 8,
          MarriageProposalNativeResolutionV1::refused) !=
          ObservedHeirMarriageMaterialStatusV1::refused ||
      ReadObservedHeirMarriageMaterialStatusV1(pending, existing_betrothal, 8,
          MarriageProposalNativeResolutionV1::invalidated) !=
          ObservedHeirMarriageMaterialStatusV1::invalidated)
    return EXIT_FAILURE;
  auto married = before;
  married.subject_has_candidate_as_spouse = true;
  married.candidate_has_subject_as_spouse = true;
  if (ReadObservedHeirMarriageMaterialStatusV1(pending, married, 8) !=
          ObservedHeirMarriageMaterialStatusV1::marriage ||
      ReadObservedHeirMarriageMaterialStatusV1(pending, married, 1,
          MarriageProposalNativeResolutionV1::pending, true) !=
          ObservedHeirMarriageMaterialStatusV1::marriage)
    return EXIT_FAILURE;
#endif
  return EXIT_SUCCESS;
}
