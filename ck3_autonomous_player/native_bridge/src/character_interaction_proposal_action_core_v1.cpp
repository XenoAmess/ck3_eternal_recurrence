#include "xar_bridge/character_interaction_proposal_action_core_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using AckStatus = game::CharacterInteractionProposalActionAckStatusV1;
using AcceptanceKind = game::CharacterInteractionAcceptanceKindV1;
using Failure = game::CharacterInteractionProposalActionFailureV1;
using Postcondition = game::CharacterInteractionProposalPostconditionKindV1;
using ReceiptStatus = game::CharacterInteractionProposalReceiptStatusV1;

struct AllowlistedInteraction {
  std::string_view key;
  Postcondition postcondition;
};

constexpr std::array<AllowlistedInteraction, 11> kFirstAllowlist{{
    {"gift_interaction", Postcondition::gift_opinion_and_payment},
    {"recruit_guest_interaction", Postcondition::recruit_to_court},
    {"invite_to_court_interaction",
     Postcondition::invite_to_court_and_cooldown},
    {"offer_vassalization_interaction",
     Postcondition::ordinary_vassalization},
    {"demand_payment_interaction", Postcondition::demand_payment_and_hook},
    {"educate_child_interaction", Postcondition::educate_child_relation},
    {"offer_ward_interaction", Postcondition::offer_ward_relation},
    {"offer_guardianship_interaction",
     Postcondition::offer_guardianship_relation},
    {"grant_titles_interaction", Postcondition::grant_selected_titles},
    {"grant_vassal_interaction", Postcondition::grant_vassal_transfer},
    {"ransom_interaction", Postcondition::ransom_prisoner_release},
}};

std::string_view FixedString(
    const std::array<char,
                     game::kCharacterInteractionPreviewSnapshotIdCapacityV1>
        &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ValidToken(std::string_view value, std::size_t maximum_size) noexcept {
  if (value.empty() || value.size() > maximum_size) return false;
  for (const char character : value) {
    const bool alpha = (character >= 'a' && character <= 'z') ||
                       (character >= 'A' && character <= 'Z');
    const bool digit = character >= '0' && character <= '9';
    if (!alpha && !digit && character != '-' && character != '_' &&
        character != '.' && character != ':' && character != '/' &&
        character != '|' && character != '=') {
      return false;
    }
  }
  return true;
}

bool ValidCharacterId(std::int32_t value) noexcept { return value != -1; }

Postcondition LookupPostcondition(std::string_view key) noexcept {
  for (const auto &entry : kFirstAllowlist) {
    if (entry.key == key) return entry.postcondition;
  }
  return Postcondition::unavailable;
}

bool AllReadinessReady(
    const game::CharacterInteractionPreviewReadinessV1 &readiness) noexcept {
  return readiness.definition_ready && readiness.actor_ready &&
         readiness.recipient_ready && readiness.finalized_context_ready &&
         readiness.can_send_ready && readiness.costs_ready &&
         readiness.acceptance_ready && readiness.same_frame_ready;
}

bool StableAcceptance(
    const game::CharacterInteractionPreviewAcceptanceV1 &value) noexcept {
  if (!value.intermediary_raw_present && value.intermediary_raw != 0) {
    return false;
  }
  if (!value.recipient_raw_present && value.recipient_raw != 0) return false;
  if (!value.final_status_present && value.final_status_raw != -1) return false;
  if (!value.would_accept_now_present && value.would_accept_now) return false;
  switch (value.kind) {
  case AcceptanceKind::auto_accept:
    return value.auto_accept && !value.intermediary_present &&
           !value.intermediary_raw_present && !value.recipient_raw_present &&
           !value.final_status_present && value.would_accept_now_present &&
           value.would_accept_now;
  case AcceptanceKind::ai_final:
    return value.recipient_is_ai && !value.auto_accept &&
           value.recipient_raw_present && value.final_status_present &&
           value.final_status_raw >= 0 && value.final_status_raw <= 2 &&
           value.would_accept_now_present &&
           value.would_accept_now == (value.final_status_raw != 2) &&
           value.intermediary_present == value.intermediary_raw_present;
  case AcceptanceKind::human_pending:
    return !value.recipient_is_ai && !value.auto_accept &&
           !value.intermediary_present && !value.intermediary_raw_present &&
           !value.recipient_raw_present && !value.final_status_present &&
           !value.would_accept_now_present;
  case AcceptanceKind::unavailable:
    return false;
  }
  return false;
}

bool ActionableAcceptance(
    const game::CharacterInteractionPreviewAcceptanceV1 &value) noexcept {
  if (!StableAcceptance(value)) return false;
  return value.kind == AcceptanceKind::auto_accept ||
         (value.kind == AcceptanceKind::ai_final &&
          value.would_accept_now);
}

bool SamePreview(const game::CharacterInteractionPreviewV1 &left,
                 const game::CharacterInteractionPreviewV1 &right) noexcept {
  return left.status == right.status &&
         left.unavailable_reason == right.unavailable_reason &&
         left.snapshot_id == right.snapshot_id &&
         left.public_revision == right.public_revision &&
         left.native_revision == right.native_revision &&
         left.proof_epoch == right.proof_epoch &&
         left.date_raw == right.date_raw &&
         left.definition == right.definition && left.roles == right.roles &&
         left.can_send == right.can_send && left.costs == right.costs &&
         left.acceptance == right.acceptance &&
         left.readiness == right.readiness;
}

bool SameEnvelope(
    const game::CharacterInteractionProposalPreviewEnvelopeV1 &left,
    const game::CharacterInteractionProposalPreviewEnvelopeV1 &right) noexcept {
  return SamePreview(left.preview, right.preview) &&
         left.payload == right.payload;
}

bool PayloadShapeMatches(
    Postcondition postcondition,
    const game::CharacterInteractionProposalPayloadV1 &payload,
    std::int32_t actor_character_id,
    std::int32_t recipient_character_id) noexcept {
  const bool two_role =
      payload.semantic_subject_character_id == recipient_character_id &&
      payload.semantic_object_character_id == actor_character_id &&
      payload.selected_title_count == 0;
  switch (postcondition) {
  case Postcondition::gift_opinion_and_payment:
  case Postcondition::recruit_to_court:
  case Postcondition::invite_to_court_and_cooldown:
  case Postcondition::demand_payment_and_hook:
    return two_role;
  case Postcondition::ordinary_vassalization:
    return two_role && payload.ordinary_feudal_or_clan_vassalization;
  case Postcondition::educate_child_relation:
  case Postcondition::offer_ward_relation:
  case Postcondition::offer_guardianship_relation:
    return payload.selected_title_count == 0 &&
           ValidCharacterId(payload.semantic_subject_character_id) &&
           ValidCharacterId(payload.semantic_object_character_id) &&
           payload.semantic_subject_character_id !=
               payload.semantic_object_character_id;
  case Postcondition::grant_selected_titles:
    return payload.semantic_subject_character_id == recipient_character_id &&
           payload.semantic_object_character_id == actor_character_id &&
           payload.selected_title_count > 0;
  case Postcondition::grant_vassal_transfer:
    return ValidCharacterId(payload.semantic_subject_character_id) &&
           payload.semantic_object_character_id == recipient_character_id &&
           payload.selected_title_count == 0;
  case Postcondition::ransom_prisoner_release:
    return ValidCharacterId(payload.semantic_subject_character_id) &&
           payload.semantic_object_character_id == actor_character_id &&
           payload.selected_title_count == 0;
  case Postcondition::unavailable:
    return false;
  }
  return false;
}

bool RequestValid(
    const game::CharacterInteractionProposalActionRequestV1 &request) noexcept {
  if (!ValidToken(request.request_id, 64) ||
      !ValidToken(request.expected_snapshot_id,
                  game::kCharacterInteractionPreviewSnapshotIdCapacityV1 - 1) ||
      request.expected_public_revision == 0 ||
      request.expected_native_revision == 0 ||
      request.expected_proof_epoch == 0 ||
      !ValidToken(request.interaction_key, 127) ||
      !ValidCharacterId(request.actor_character_id) ||
      !ValidCharacterId(request.recipient_character_id) ||
      request.actor_character_id == request.recipient_character_id ||
      !ValidCharacterId(request.semantic_subject_character_id) ||
      !ValidCharacterId(request.semantic_object_character_id) ||
      !ValidToken(request.payload_fingerprint, 128)) {
    return false;
  }
  return std::all_of(
      request.budget.maximum_actor_spend_raw.begin(),
      request.budget.maximum_actor_spend_raw.end(),
      [](std::int64_t value) { return value >= 0; });
}

Failure ValidateBoundPreview(
    const game::CharacterInteractionProposalActionRequestV1 &request,
    Postcondition postcondition,
    const game::CharacterInteractionProposalPreviewEnvelopeV1
        &envelope) noexcept {
  const auto &preview = envelope.preview;
  const auto &payload = envelope.payload;
  if (preview.status != game::CharacterInteractionPreviewStatusV1::available ||
      preview.unavailable_reason !=
          game::CharacterInteractionPreviewFailureV1::none ||
      !AllReadinessReady(preview.readiness)) {
    return Failure::proposal_preview_unavailable;
  }
  if (FixedString(preview.snapshot_id) != request.expected_snapshot_id ||
      preview.public_revision != request.expected_public_revision ||
      preview.native_revision != request.expected_native_revision ||
      preview.proof_epoch != request.expected_proof_epoch ||
      preview.date_raw != request.expected_date_raw ||
      preview.definition.canonical_key != request.interaction_key ||
      preview.roles.actor_character_id != request.actor_character_id ||
      preview.roles.recipient_character_id != request.recipient_character_id) {
    return Failure::snapshot_binding_mismatch;
  }
  if (!payload.complete ||
      payload.semantic_subject_character_id !=
          request.semantic_subject_character_id ||
      payload.semantic_object_character_id !=
          request.semantic_object_character_id ||
      payload.selected_title_count != request.selected_title_count ||
      payload.fingerprint != request.payload_fingerprint ||
      !PayloadShapeMatches(postcondition, payload, request.actor_character_id,
                           request.recipient_character_id)) {
    return Failure::proposal_payload_mismatch;
  }
  if (payload.religious_option_selected) {
    return Failure::religious_option_deferred;
  }
  if (!preview.can_send) return Failure::can_send_rejected;
  if (!ActionableAcceptance(preview.acceptance)) {
    return Failure::acceptance_not_actionable;
  }
  for (std::size_t index = 0; index < preview.costs.raw.size(); ++index) {
    if (preview.costs.raw[index] > 0 &&
        preview.costs.raw[index] >
            request.budget.maximum_actor_spend_raw[index]) {
      return Failure::budget_exceeded;
    }
  }
  return Failure::none;
}

std::string_view FailureReason(Failure failure) noexcept {
  return CharacterInteractionProposalActionFailureKeyV1(failure);
}

AckStatus Reject(
    const game::CharacterInteractionProposalActionRequestV1 &request,
    Failure failure, game::CharacterInteractionProposalActionAckV1 &ack) {
  ack = {};
  ack.request_id = request.request_id;
  ack.interaction_key = request.interaction_key;
  ack.actor_character_id = request.actor_character_id;
  ack.recipient_character_id = request.recipient_character_id;
  ack.failure = failure;
  ack.reason.assign(FailureReason(failure));
  return AckStatus::rejected_before_submit;
}

void CopySubmittedAck(
    const game::CharacterInteractionProposalActionRequestV1 &request,
    const game::CharacterInteractionProposalPreviewEnvelopeV1 &envelope,
    Postcondition postcondition,
    game::CharacterInteractionProposalActionAckV1 &ack) {
  const auto &preview = envelope.preview;
  ack = {};
  ack.status = AckStatus::submitted_verification_pending;
  ack.verification_pending = true;
  ack.request_id = request.request_id;
  ack.failure = Failure::none;
  ack.snapshot_id.assign(FixedString(preview.snapshot_id));
  ack.pre_public_revision = preview.public_revision;
  ack.pre_native_revision = preview.native_revision;
  ack.pre_proof_epoch = preview.proof_epoch;
  ack.pre_date_raw = preview.date_raw;
  ack.interaction_key = request.interaction_key;
  ack.actor_character_id = request.actor_character_id;
  ack.recipient_character_id = request.recipient_character_id;
  ack.semantic_subject_character_id =
      envelope.payload.semantic_subject_character_id;
  ack.semantic_object_character_id =
      envelope.payload.semantic_object_character_id;
  ack.selected_title_count = envelope.payload.selected_title_count;
  ack.payload_fingerprint = envelope.payload.fingerprint;
  ack.costs = preview.costs;
  ack.acceptance = preview.acceptance;
  ack.postcondition_kind = postcondition;
}

bool PostBindingMatches(
    const game::CharacterInteractionProposalActionAckV1 &ack,
    const game::CharacterInteractionProposalPostconditionObservationV1
        &post) noexcept {
  return post.interaction_key == ack.interaction_key &&
         post.actor_character_id == ack.actor_character_id &&
         post.recipient_character_id == ack.recipient_character_id &&
         post.semantic_subject_character_id ==
             ack.semantic_subject_character_id &&
         post.semantic_object_character_id ==
             ack.semantic_object_character_id &&
         post.selected_title_count == ack.selected_title_count &&
         post.payload_fingerprint == ack.payload_fingerprint;
}

bool AppliedPostcondition(
    const game::CharacterInteractionProposalActionAckV1 &ack,
    const game::CharacterInteractionProposalPostconditionObservationV1
        &post) noexcept {
  switch (ack.postcondition_kind) {
  case Postcondition::gift_opinion_and_payment:
    return ack.costs.raw[0] > 0 && post.terms_reconciled &&
           post.recipient_has_gift_opinion_toward_actor &&
           post.actor_gold_spent_raw == ack.costs.raw[0];
  case Postcondition::recruit_to_court:
    return post.terms_reconciled &&
           post.recipient_court_owner_character_id == ack.actor_character_id;
  case Postcondition::invite_to_court_and_cooldown:
    return post.terms_reconciled && post.invite_cooldown_present &&
           post.recipient_court_owner_character_id == ack.actor_character_id;
  case Postcondition::ordinary_vassalization:
    return post.obligation_state_matches &&
           post.recipient_immediate_liege_character_id ==
               ack.actor_character_id;
  case Postcondition::demand_payment_and_hook:
    return post.terms_reconciled && post.actor_hook_to_recipient_consumed &&
           post.actor_gold_received_raw > 0;
  case Postcondition::educate_child_relation:
  case Postcondition::offer_ward_relation:
  case Postcondition::offer_guardianship_relation:
    return post.terms_reconciled &&
           post.observed_guardian_character_id ==
               ack.semantic_object_character_id &&
           post.observed_ward_character_id ==
               ack.semantic_subject_character_id &&
           (post.education_relation_present ||
            post.education_travel_pending);
  case Postcondition::grant_selected_titles:
    return ack.selected_title_count > 0 &&
           post.selected_titles_held_by_subject_count ==
               ack.selected_title_count &&
           post.title_transfer_graph_consistent;
  case Postcondition::grant_vassal_transfer:
    return post.title_transfer_graph_consistent &&
           post.transferred_vassal_immediate_liege_character_id ==
               ack.semantic_object_character_id;
  case Postcondition::ransom_prisoner_release:
    return post.terms_reconciled &&
           post.prisoner_imprisoned_by_character_id !=
               ack.semantic_object_character_id;
  case Postcondition::unavailable:
    return false;
  }
  return false;
}

void ClearInFlight(CharacterInteractionProposalActionStateV1 &state) {
  state.submission_in_flight = false;
  state.in_flight_request_id.clear();
}

} // namespace

AckStatus ExecuteCharacterInteractionProposalActionCoreV1(
    const CharacterInteractionProposalActionEnvironmentV1 &environment,
    const CharacterInteractionProposalActionAccessV1 &access,
    CharacterInteractionProposalActionStateV1 &state,
    const game::CharacterInteractionProposalActionRequestV1 &request,
    game::CharacterInteractionProposalActionAckV1 &ack) noexcept {
  try {
    if (!RequestValid(request)) {
      return Reject(request, Failure::invalid_request, ack);
    }
    const auto postcondition = LookupPostcondition(request.interaction_key);
    if (postcondition == Postcondition::unavailable) {
      return Reject(request, Failure::interaction_not_allowlisted, ack);
    }
    if (!environment.exact_build_admitted) {
      return Reject(request, Failure::exact_build_not_admitted, ack);
    }
    if (state.submission_in_flight) {
      return Reject(request, Failure::submission_already_in_flight, ack);
    }
    if (access.capture_preview == nullptr) {
      return Reject(request, Failure::proposal_preview_unavailable, ack);
    }

    game::CharacterInteractionProposalPreviewEnvelopeV1 first{};
    if (!access.capture_preview(access.context, first)) {
      return Reject(request, Failure::proposal_preview_unavailable, ack);
    }
    if (const auto failure =
            ValidateBoundPreview(request, postcondition, first);
        failure != Failure::none) {
      return Reject(request, failure, ack);
    }

    const bool submit_certified =
        environment.submit_abi_certified || environment.offline_fixture_submit;
    if (!submit_certified || access.submit_once == nullptr) {
      return Reject(request, Failure::submit_seam_unavailable, ack);
    }

    game::CharacterInteractionProposalPreviewEnvelopeV1 second{};
    if (!access.capture_preview(access.context, second) ||
        !SameEnvelope(first, second)) {
      return Reject(request, Failure::proposal_changed_before_submit, ack);
    }

    // This is the only submit call in the executor. Its boolean is a transport
    // ACK and never upgrades the semantic receipt to applied.
    if (!access.submit_once(access.context, request, second)) {
      return Reject(request, Failure::submit_not_acknowledged, ack);
    }

    CopySubmittedAck(request, second, postcondition, ack);
    state.submission_in_flight = true;
    state.in_flight_request_id = request.request_id;
    ++state.acknowledged_submission_count;
    return ack.status;
  } catch (...) {
    return Reject(request, Failure::submit_not_acknowledged, ack);
  }
}

ReceiptStatus VerifyCharacterInteractionProposalReceiptV1(
    CharacterInteractionProposalActionStateV1 &state,
    const game::CharacterInteractionProposalActionAckV1 &ack,
    const game::CharacterInteractionProposalPostconditionObservationV1 &post,
    game::CharacterInteractionProposalReceiptV1 &receipt) noexcept {
  try {
    receipt = {};
    receipt.request_id = ack.request_id;
    receipt.interaction_key = ack.interaction_key;
    receipt.postcondition_kind = ack.postcondition_kind;
    if (ack.status == AckStatus::rejected_before_submit) {
      receipt.status = ReceiptStatus::rejected;
      receipt.reason = ack.reason;
      return receipt.status;
    }
    const auto fail = [&](std::string_view reason) {
      receipt.status = ReceiptStatus::postcondition_failed;
      receipt.reason.assign(reason);
      return receipt.status;
    };
    if (ack.status != AckStatus::submitted_verification_pending ||
        !ack.verification_pending || !state.submission_in_flight ||
        state.in_flight_request_id != ack.request_id) {
      return fail("ack_not_current");
    }
    if (!post.available || !post.paused || post.snapshot_id.empty() ||
        post.public_revision <= ack.pre_public_revision ||
        post.native_revision <= ack.pre_native_revision ||
        post.date_raw < ack.pre_date_raw) {
      return fail("new_paused_observation_unavailable");
    }
    receipt.post_public_revision = post.public_revision;
    receipt.post_native_revision = post.native_revision;
    receipt.post_date_raw = post.date_raw;
    if (!PostBindingMatches(ack, post)) {
      return fail("postcondition_binding_mismatch");
    }
    if (AppliedPostcondition(ack, post)) {
      receipt.status = ReceiptStatus::applied;
      receipt.reason.clear();
      receipt.interaction_specific_postcondition_verified = true;
      ClearInFlight(state);
      return receipt.status;
    }
    if (post.matching_pending_proposal) {
      receipt.status = ReceiptStatus::response_pending;
      receipt.reason = "interaction_response_pending";
      return receipt.status;
    }
    receipt.status = ReceiptStatus::postcondition_failed;
    receipt.reason = "interaction_specific_postcondition_failed";
    ClearInFlight(state);
    return receipt.status;
  } catch (...) {
    receipt = {};
    receipt.status = ReceiptStatus::postcondition_failed;
    receipt.request_id = ack.request_id;
    receipt.interaction_key = ack.interaction_key;
    receipt.reason = "receipt_verifier_exception";
    return receipt.status;
  }
}

std::string_view CharacterInteractionProposalActionFailureKeyV1(
    Failure failure) noexcept {
  using enum game::CharacterInteractionProposalActionFailureV1;
  switch (failure) {
  case none: return "none";
  case invalid_request: return "invalid_request";
  case interaction_not_allowlisted: return "interaction_not_allowlisted";
  case exact_build_not_admitted: return "exact_build_not_admitted";
  case proposal_preview_unavailable: return "proposal_preview_unavailable";
  case snapshot_binding_mismatch: return "snapshot_binding_mismatch";
  case proposal_payload_mismatch: return "proposal_payload_mismatch";
  case religious_option_deferred: return "religious_option_deferred";
  case can_send_rejected: return "can_send_rejected";
  case acceptance_not_actionable: return "acceptance_not_actionable";
  case budget_exceeded: return "budget_exceeded";
  case proposal_changed_before_submit:
    return "proposal_changed_before_submit";
  case submission_already_in_flight:
    return "submission_already_in_flight";
  case submit_seam_unavailable: return "submit_seam_unavailable";
  case submit_not_acknowledged: return "submit_not_acknowledged";
  }
  return "submit_not_acknowledged";
}

std::string_view CharacterInteractionProposalPostconditionKeyV1(
    Postcondition kind) noexcept {
  switch (kind) {
  case Postcondition::unavailable: return "unavailable";
  case Postcondition::gift_opinion_and_payment:
    return "gift_opinion_and_payment";
  case Postcondition::recruit_to_court: return "recruit_to_court";
  case Postcondition::invite_to_court_and_cooldown:
    return "invite_to_court_and_cooldown";
  case Postcondition::ordinary_vassalization:
    return "ordinary_vassalization";
  case Postcondition::demand_payment_and_hook:
    return "demand_payment_and_hook";
  case Postcondition::educate_child_relation:
    return "educate_child_relation";
  case Postcondition::offer_ward_relation: return "offer_ward_relation";
  case Postcondition::offer_guardianship_relation:
    return "offer_guardianship_relation";
  case Postcondition::grant_selected_titles:
    return "grant_selected_titles";
  case Postcondition::grant_vassal_transfer:
    return "grant_vassal_transfer";
  case Postcondition::ransom_prisoner_release:
    return "ransom_prisoner_release";
  }
  return "unavailable";
}

} // namespace xar::ck3_11906
