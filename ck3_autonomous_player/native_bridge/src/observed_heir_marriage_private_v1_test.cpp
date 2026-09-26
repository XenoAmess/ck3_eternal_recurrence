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
  return EXIT_SUCCESS;
}
