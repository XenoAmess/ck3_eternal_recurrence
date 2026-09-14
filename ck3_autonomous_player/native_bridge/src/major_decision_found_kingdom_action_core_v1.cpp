#include "xar_bridge/major_decision_found_kingdom_action_core_v1.hpp"

#include <limits>
#include <string_view>
#include <type_traits>
#include <utility>

namespace xar::bridge {
namespace {

using AckStatus = MajorDecisionFoundKingdomActionAckStatusV1;
using FailureClass = MajorDecisionFoundKingdomActionFailureClassV1;
using ReceiptStatus = MajorDecisionFoundKingdomActionReceiptStatusV1;

static_assert(std::is_nothrow_move_assignable_v<
              MajorDecisionFoundKingdomActionAckV1>);

bool ValidRequestId(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (const char character : value) {
    const bool alpha = (character >= 'a' && character <= 'z') ||
                       (character >= 'A' && character <= 'Z');
    const bool digit = character >= '0' && character <= '9';
    if (!alpha && !digit && character != '-' && character != '_' &&
        character != '.' && character != ':') {
      return false;
    }
  }
  return true;
}

bool ValidBinding(
    const MajorDecisionFoundKingdomActionBindingV1 &binding) noexcept {
  return binding.snapshot_revision != 0 && binding.native_revision != 0 &&
         binding.proof_epoch != 0 && binding.date_raw > 0 &&
         binding.played_character_id > 0 &&
         binding.decision_database_identity != 0 &&
         binding.decision_database_generation != 0 &&
         binding.decision_definition_identity != 0 &&
         binding.decision_definition_generation != 0 &&
         binding.primary_title_id > 0 &&
         binding.primary_title_identity != 0 &&
         binding.primary_title_generation != 0 &&
         binding.world_identity != 0 && binding.world_generation != 0 &&
         binding.world_revision != 0;
}

bool Known(const MajorDecisionTypedBoolV1 &value) noexcept {
  return value.state == MajorDecisionFieldStateV1::known &&
         value.unknown_reason == MajorDecisionUnknownReasonV1::none;
}

bool ValidCost(const MajorDecisionEvaluatedCostV1 &cost) noexcept {
  return cost.state == MajorDecisionFieldStateV1::known &&
         cost.source == MajorDecisionCostSourceV1::native_evaluated_cost &&
         cost.unknown_reason == MajorDecisionUnknownReasonV1::none &&
         cost.gold_q100000 >= 0 && cost.treasury_q100000 >= 0 &&
         cost.prestige_q100000 >= 0 && cost.piety_q100000 >= 0;
}

bool BasePreconditionValid(
    const MajorDecisionFoundKingdomActionPreconditionV1 &value) noexcept {
  return value.available && value.application_main_thread && value.paused &&
         value.map_ready && value.played_character_alive &&
         value.played_character_identity_round_trip &&
         value.decision_database_identity_round_trip &&
         value.decision_definition_identity_round_trip &&
         value.decision_source_block_sha256_round_trip &&
         value.decision_id == kMajorDecisionFoundKingdomDecisionIdV1 &&
         ValidBinding(value.binding) &&
         value.effect_preview.state == MajorDecisionFieldStateV1::unknown &&
         value.effect_preview.unknown_reason ==
             MajorDecisionUnknownReasonV1::effect_preview_not_provided &&
         !value.effect_preview.executable;
}

AckStatus Reject(const MajorDecisionFoundKingdomActionRequestV1 &request,
                 FailureClass failure, std::string_view reason,
                 MajorDecisionFoundKingdomActionAckV1 &ack) {
  ack = {};
  ack.request_id = request.request_id;
  ack.decision_id = request.decision_id;
  ack.failure_class = failure;
  ack.rejection_reason.assign(reason);
  return ack.status;
}

void CopyPost(
    const MajorDecisionFoundKingdomActionPostconditionV1 &postcondition,
    MajorDecisionFoundKingdomActionReceiptV1 &receipt) noexcept {
  receipt.post_snapshot_revision = postcondition.snapshot_revision;
  receipt.post_native_revision = postcondition.native_revision;
  receipt.post_world_identity = postcondition.world_identity;
  receipt.post_world_generation = postcondition.world_generation;
  receipt.post_world_revision = postcondition.world_revision;
  receipt.post_date_raw = postcondition.date_raw;
  receipt.played_character_id = postcondition.played_character_id;
  receipt.observed_primary_title_id = postcondition.primary_title_id;
  receipt.observed_primary_title_identity =
      postcondition.primary_title_identity;
  receipt.observed_primary_title_generation =
      postcondition.primary_title_generation;
}

ReceiptStatus FailReceipt(std::string_view reason,
                          MajorDecisionFoundKingdomActionReceiptV1 &receipt) {
  receipt.status = ReceiptStatus::postcondition_failed;
  receipt.postcondition_verified = false;
  receipt.reason.assign(reason);
  return receipt.status;
}

} // namespace

AckStatus ExecuteMajorDecisionFoundKingdomActionCoreV1(
    const MajorDecisionFoundKingdomActionEnvironmentV1 &environment,
    const MajorDecisionFoundKingdomActionAccessV1 &access,
    const MajorDecisionFoundKingdomActionRequestV1 &request,
    MajorDecisionFoundKingdomActionStateV1 &state,
    MajorDecisionFoundKingdomActionAckV1 &ack) noexcept {
  try {
    if (!ValidRequestId(request.request_id) ||
        request.decision_id != kMajorDecisionFoundKingdomDecisionIdV1 ||
        !ValidBinding(request.expected_binding) ||
        !ValidCost(request.expected_evaluated_cost)) {
      return Reject(request, FailureClass::request_contract,
                    "invalid_request", ack);
    }
    if (!environment.action_enabled || !environment.exact_build_admitted ||
        environment.admitted_game_version !=
            kMajorDecisionFoundKingdomGameVersionV1 ||
        environment.admitted_executable_sha256 !=
            kMajorDecisionFoundKingdomExecutableSha256V1) {
      return Reject(request, FailureClass::exact_build,
                    "exact_build_not_admitted", ack);
    }
    if (state.verification_pending) {
      return Reject(request, FailureClass::pending_action,
                    "previous_submission_verification_pending", ack);
    }
    if (state.next_submission_sequence == 0 ||
        state.next_submission_sequence ==
            (std::numeric_limits<std::uint64_t>::max)()) {
      return Reject(request, FailureClass::request_contract,
                    "submission_sequence_unavailable", ack);
    }
    const bool production_submit = environment.module_base != 0 &&
                                   environment.submit_abi_certified &&
                                   !environment.offline_fixture_submit;
    const bool fixture_submit = environment.module_base == 0 &&
                                !environment.submit_abi_certified &&
                                environment.offline_fixture_submit;
    if ((!production_submit && !fixture_submit) ||
        access.capture_precondition == nullptr || access.submit == nullptr) {
      return Reject(request, FailureClass::native_submit,
                    "submit_abi_not_certified", ack);
    }

    MajorDecisionFoundKingdomActionPreconditionV1 first{};
    if (!access.capture_precondition(access.context, first) ||
        !BasePreconditionValid(first)) {
      return Reject(request, FailureClass::observation,
                    "paused_precondition_unavailable", ack);
    }
    if (first.binding != request.expected_binding) {
      return Reject(request, FailureClass::identity_binding,
                    "expected_binding_mismatch", ack);
    }
    if (!Known(first.is_shown) || !Known(first.is_valid) ||
        !Known(first.is_valid_showing_failures_only) ||
        !first.is_shown.value || !first.is_valid.value ||
        !first.is_valid_showing_failures_only.value) {
      return Reject(request, FailureClass::eligibility,
                    "decision_not_eligible", ack);
    }
    if (!ValidCost(first.evaluated_cost) ||
        first.evaluated_cost != request.expected_evaluated_cost ||
        !Known(first.is_affordable) || !first.is_affordable.value) {
      return Reject(request, FailureClass::resources,
                    "resources_not_bound_or_affordable", ack);
    }
    if (!Known(first.can_take) || !first.can_take.value) {
      return Reject(request, FailureClass::can_take,
                    "decision_cannot_be_taken", ack);
    }

    MajorDecisionFoundKingdomActionPreconditionV1 second{};
    if (!access.capture_precondition(access.context, second) ||
        first != second) {
      return Reject(request, FailureClass::observation,
                    "precondition_changed_before_submit", ack);
    }

    // Finish all potentially allocating ACK work before crossing the native
    // submit boundary. After a successful submit, only non-throwing moves and
    // scalar state updates remain, so the pending token cannot be lost.
    MajorDecisionFoundKingdomActionAckV1 candidate{};
    candidate.status = AckStatus::submitted_verification_pending;
    candidate.verification_pending = true;
    candidate.effect_preview_available = false;
    candidate.exact_benefit_claimed = false;
    candidate.request_id = request.request_id;
    candidate.decision_id = request.decision_id;
    candidate.submission_sequence = state.next_submission_sequence;
    candidate.pre_binding = first.binding;
    candidate.submitted_evaluated_cost = first.evaluated_cost;
    candidate.failure_class = FailureClass::none;
    std::string pending_request_id = request.request_id;
    std::string pending_decision_id = request.decision_id;

    // This is the only submit call in the function. A repeated Execute while
    // its receipt is pending is rejected above.
    if (!access.submit(access.context, first.binding, first.decision_id)) {
      return Reject(request, FailureClass::native_submit,
                    "native_submit_failed", ack);
    }

    state.verification_pending = true;
    state.pending_submission_sequence = state.next_submission_sequence;
    state.pending_request_id = std::move(pending_request_id);
    state.pending_decision_id = std::move(pending_decision_id);
    state.pending_binding = first.binding;
    state.pending_evaluated_cost = first.evaluated_cost;
    ++state.next_submission_sequence;
    ack = std::move(candidate);
    return ack.status;
  } catch (...) {
    return Reject(request, FailureClass::native_submit,
                  "action_core_exception", ack);
  }
}

ReceiptStatus VerifyMajorDecisionFoundKingdomActionReceiptV1(
    const MajorDecisionFoundKingdomActionAckV1 &ack,
    const MajorDecisionFoundKingdomActionPostconditionV1 &postcondition,
    MajorDecisionFoundKingdomActionStateV1 &state,
    MajorDecisionFoundKingdomActionReceiptV1 &receipt) noexcept {
  try {
    receipt = {};
    receipt.request_id = ack.request_id;
    receipt.submission_sequence = ack.submission_sequence;
    CopyPost(postcondition, receipt);
    if (ack.status == AckStatus::rejected_before_submit) {
      receipt.status = ReceiptStatus::rejected;
      receipt.reason = ack.rejection_reason;
      return receipt.status;
    }
    if (ack.status != AckStatus::submitted_verification_pending ||
        !ack.verification_pending || ack.effect_preview_available ||
        ack.exact_benefit_claimed ||
        ack.decision_id != kMajorDecisionFoundKingdomDecisionIdV1 ||
        !ValidBinding(ack.pre_binding) || ack.submission_sequence == 0 ||
        !state.verification_pending ||
        state.pending_submission_sequence != ack.submission_sequence ||
        state.pending_request_id != ack.request_id ||
        state.pending_decision_id != ack.decision_id ||
        state.pending_binding != ack.pre_binding ||
        state.pending_evaluated_cost != ack.submitted_evaluated_cost) {
      return FailReceipt("invalid_pending_ack", receipt);
    }
    if (!postcondition.available ||
        !postcondition.application_main_thread || !postcondition.paused ||
        !postcondition.map_ready ||
        postcondition.snapshot_revision <= ack.pre_binding.snapshot_revision ||
        postcondition.native_revision <= ack.pre_binding.native_revision ||
        postcondition.world_revision <= ack.pre_binding.world_revision) {
      return FailReceipt("no_fresh_paused_observation", receipt);
    }
    if (postcondition.proof_epoch != ack.pre_binding.proof_epoch ||
        postcondition.date_raw != ack.pre_binding.date_raw) {
      return FailReceipt("proof_or_date_binding_changed", receipt);
    }
    if (!postcondition.played_character_identity_round_trip ||
        postcondition.played_character_id !=
            ack.pre_binding.played_character_id ||
        !postcondition.decision_database_identity_round_trip ||
        postcondition.decision_database_identity !=
            ack.pre_binding.decision_database_identity ||
        postcondition.decision_database_generation !=
            ack.pre_binding.decision_database_generation) {
      return FailReceipt("player_or_database_binding_changed", receipt);
    }
    if (!postcondition.decision_state_observed) {
      return FailReceipt("decision_state_not_observed", receipt);
    }
    if (postcondition.decision_definition_present) {
      if (!postcondition.decision_definition_identity_round_trip ||
          postcondition.decision_definition_identity !=
              ack.pre_binding.decision_definition_identity ||
          postcondition.decision_definition_generation !=
              ack.pre_binding.decision_definition_generation) {
        return FailReceipt("decision_definition_binding_changed", receipt);
      }
      if (!postcondition.decision_can_take_known ||
          postcondition.decision_can_take) {
        return FailReceipt("decision_still_takeable", receipt);
      }
    }
    receipt.decision_no_longer_takeable = true;

    if (!postcondition.primary_title_observed ||
        postcondition.primary_title_id <= 0 ||
        postcondition.primary_title_id == ack.pre_binding.primary_title_id ||
        postcondition.primary_title_identity == 0 ||
        postcondition.primary_title_generation == 0 ||
        postcondition.primary_title_tier !=
            MajorDecisionFoundKingdomTitleTierV1::kingdom ||
        postcondition.primary_title_holder_character_id !=
            ack.pre_binding.played_character_id ||
        !postcondition.primary_title_identity_round_trip ||
        !postcondition.primary_title_holder_identity_round_trip ||
        !postcondition.player_primary_title_round_trip ||
        !postcondition.dynamic_custom_kingdom_observed) {
      return FailReceipt("new_kingdom_title_not_observed", receipt);
    }
    receipt.new_kingdom_title_verified = true;

    if (!postcondition.world_outcome_observed ||
        !postcondition.world_identity_round_trip ||
        postcondition.world_identity != ack.pre_binding.world_identity ||
        postcondition.world_generation != ack.pre_binding.world_generation ||
        !postcondition.new_title_registered ||
        !postcondition.title_world_index_round_trip) {
      return FailReceipt("world_outcome_not_observed", receipt);
    }
    receipt.world_outcome_verified = true;
    receipt.status = ReceiptStatus::applied;
    receipt.postcondition_verified = true;
    receipt.reason.clear();
    state.verification_pending = false;
    state.pending_submission_sequence = 0;
    state.pending_request_id.clear();
    state.pending_decision_id.clear();
    state.pending_binding = {};
    state.pending_evaluated_cost = {};
    return receipt.status;
  } catch (...) {
    return FailReceipt("receipt_verifier_exception", receipt);
  }
}

std::string_view MajorDecisionFoundKingdomActionFailureClassNameV1(
    FailureClass failure) noexcept {
  switch (failure) {
  case FailureClass::none: return "none";
  case FailureClass::request_contract: return "request_contract";
  case FailureClass::exact_build: return "exact_build";
  case FailureClass::pending_action: return "pending_action";
  case FailureClass::observation: return "observation";
  case FailureClass::identity_binding: return "identity_binding";
  case FailureClass::eligibility: return "eligibility";
  case FailureClass::resources: return "resources";
  case FailureClass::can_take: return "can_take";
  case FailureClass::native_submit: return "native_submit";
  }
  return "native_submit";
}

} // namespace xar::bridge
