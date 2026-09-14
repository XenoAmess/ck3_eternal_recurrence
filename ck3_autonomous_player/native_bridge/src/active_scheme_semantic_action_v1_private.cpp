#include "xar_bridge/active_scheme_semantic_action_v1_private.hpp"

#include <algorithm>
#include <string_view>

namespace xar::bridge {
namespace {

using AckStatus = ActiveSchemeSemanticActionV1PrivateAckStatus;
using Failure = ActiveSchemeSemanticActionV1PrivateFailure;
using PreviewStatus = ActiveSchemeSemanticActionV1PrivatePreviewStatus;
using ReceiptStatus = ActiveSchemeSemanticActionV1PrivateReceiptStatus;
using TargetKind = ActiveSchemeStateV1PrivateTargetKind;

struct InteractionSpec {
  std::string_view scheme_type_key;
  bool murder_starter_required = false;
};

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

bool ResolveInteraction(std::string_view interaction_key,
                        InteractionSpec &spec) noexcept {
  if (interaction_key == "sway_interaction") {
    spec = {"sway", false};
    return true;
  }
  if (interaction_key == "start_murder_interaction") {
    spec = {"murder", true};
    return true;
  }
  return false;
}

bool ValidMurderStarter(std::string_view key) noexcept {
  return key == "agent_focus_balance" || key == "agent_focus_success" ||
         key == "agent_focus_speed" || key == "agent_focus_secrecy";
}

template <std::size_t Size>
bool KeyEquals(const std::array<char, Size> &key,
               std::string_view expected) noexcept {
  if (expected.size() >= key.size()) return false;
  return std::equal(expected.begin(), expected.end(), key.begin()) &&
         key[expected.size()] == '\0';
}

template <typename T>
bool SameValue(const ActiveSchemeStateV1PrivateValue<T> &left,
               const ActiveSchemeStateV1PrivateValue<T> &right) noexcept {
  return left.status == right.status && left.value == right.value;
}

bool SameRow(const ActiveSchemeStateV1PrivateRow &left,
             const ActiveSchemeStateV1PrivateRow &right) noexcept {
  return left.scheme_instance_id == right.scheme_instance_id &&
         left.scheme_instance_generation == right.scheme_instance_generation &&
         left.owner_character_id == right.owner_character_id &&
         left.scheme_type_key == right.scheme_type_key &&
         left.category_key == right.category_key &&
         left.target_kind == right.target_kind &&
         left.target_id == right.target_id && left.is_basic == right.is_basic &&
         left.is_secret == right.is_secret &&
         left.is_exposed == right.is_exposed &&
         left.is_frozen == right.is_frozen &&
         SameValue(left.progress, right.progress) &&
         SameValue(left.progress_goal, right.progress_goal) &&
         SameValue(left.success_chance, right.success_chance) &&
         SameValue(left.maximum_success_chance,
                   right.maximum_success_chance) &&
         SameValue(left.secrecy, right.secrecy) &&
         SameValue(left.opportunity_charges, right.opportunity_charges) &&
         SameValue(left.breaches, right.breaches) &&
         SameValue(left.maximum_breaches, right.maximum_breaches) &&
         SameValue(left.phases_remaining_until_opportunity,
                   right.phases_remaining_until_opportunity);
}

bool SameObservation(const ActiveSchemeStateV1PrivateObservation &left,
                     const ActiveSchemeStateV1PrivateObservation &right) noexcept {
  if (left.status != right.status ||
      left.unavailable_reason != right.unavailable_reason ||
      left.capture_epoch != right.capture_epoch ||
      left.date_raw != right.date_raw ||
      left.played_character_id != right.played_character_id ||
      left.container_generation != right.container_generation ||
      left.row_count != right.row_count) {
    return false;
  }
  for (std::size_t index = 0; index < left.row_count; ++index) {
    if (!SameRow(left.rows[index], right.rows[index])) return false;
  }
  return true;
}

bool MatchesScheme(const ActiveSchemeStateV1PrivateRow &row,
                   std::int64_t actor_character_id,
                   std::string_view scheme_type_key, TargetKind target_kind,
                   std::int64_t target_id) noexcept {
  return row.owner_character_id == actor_character_id &&
         KeyEquals(row.scheme_type_key, scheme_type_key) &&
         row.target_kind == target_kind && row.target_id == target_id;
}

bool HasMatchingScheme(const ActiveSchemeStateV1PrivateObservation &observation,
                       std::int64_t actor_character_id,
                       std::string_view scheme_type_key,
                       TargetKind target_kind,
                       std::int64_t target_id) noexcept {
  for (std::size_t index = 0; index < observation.row_count; ++index) {
    if (MatchesScheme(observation.rows[index], actor_character_id,
                      scheme_type_key, target_kind, target_id)) {
      return true;
    }
  }
  return false;
}

bool PreviewStatusResolved(PreviewStatus status) noexcept {
  return status == PreviewStatus::available ||
         status == PreviewStatus::explicitly_unavailable;
}

bool PreviewValueInRange(
    const ActiveSchemeSemanticActionV1PrivatePreviewValue &value) noexcept {
  return value.status != PreviewStatus::available ||
         (value.value >= 0 && value.value <= 100);
}

AckStatus Reject(const ActiveSchemeSemanticActionV1PrivateRequest &request,
                 Failure failure, std::string_view reason,
                 std::string_view native_reason_key,
                 ActiveSchemeSemanticActionV1PrivateAck &ack) {
  ack = {};
  ack.status = AckStatus::rejected_before_submit;
  ack.failure = failure;
  ack.reason.assign(reason);
  ack.native_reason_key.assign(native_reason_key);
  ack.request_id = request.request_id;
  ack.interaction_key = request.interaction_key;
  ack.actor_character_id = request.actor_character_id;
  ack.target_kind = request.target_kind;
  ack.target_id = request.target_id;
  return ack.status;
}

ReceiptStatus Red(Failure failure, std::string_view reason,
                  ActiveSchemeSemanticActionV1PrivateReceipt &receipt) {
  receipt.status = ReceiptStatus::red;
  receipt.failure = failure;
  receipt.reason.assign(reason);
  receipt.postcondition_verified = false;
  return receipt.status;
}

bool IsPriorIdentity(const ActiveSchemeSemanticActionV1PrivateAck &ack,
                     const ActiveSchemeStateV1PrivateRow &row) noexcept {
  for (std::size_t index = 0; index < ack.prior_identity_count; ++index) {
    if (ack.prior_identities[index].instance_id == row.scheme_instance_id &&
        ack.prior_identities[index].generation ==
            row.scheme_instance_generation) {
      return true;
    }
  }
  return false;
}

} // namespace

AckStatus ExecuteActiveSchemeSemanticActionV1Private(
    const ActiveSchemeSemanticActionV1PrivateEnvironment &environment,
    const ActiveSchemeSemanticActionV1PrivateAccess &access,
    const ActiveSchemeSemanticActionV1PrivateRequest &request,
    ActiveSchemeSemanticActionV1PrivateAck &ack) noexcept {
  try {
    if (!ValidRequestId(request.request_id) ||
        request.actor_character_id <= 0 || request.target_id <= 0 ||
        request.target_kind != TargetKind::character ||
        request.expected_capture_epoch == 0 ||
        request.expected_container_generation == 0 ||
        request.expected_date_raw <= 0) {
      return Reject(request, Failure::request_contract, "invalid_request", {},
                    ack);
    }

    InteractionSpec spec{};
    if (!ResolveInteraction(request.interaction_key, spec)) {
      return Reject(request, Failure::interaction_not_allowed,
                    "interaction_not_allowlisted", {}, ack);
    }
    if (!environment.exact_build_admitted ||
        environment.admitted_executable_sha256 !=
            kActiveSchemeSemanticActionV1PrivateExecutableSha256) {
      return Reject(request, Failure::exact_build_mismatch,
                    "exact_build_mismatch", {}, ack);
    }
    const bool production_route =
        environment.module_base != 0 &&
        environment.character_interaction_route_bound;
    const bool fixture_route =
        environment.module_base == 0 && environment.offline_fixture;
    if ((!production_route && !fixture_route) || access.submit == nullptr) {
      return Reject(request, Failure::action_route_unavailable,
                    "character_interaction_route_unavailable", {}, ack);
    }
    if (access.capture_observation == nullptr) {
      return Reject(request, Failure::observation_unavailable,
                    "active_scheme_observation_callback_unavailable", {},
                    ack);
    }
    if (access.capture_precondition == nullptr) {
      return Reject(request, Failure::precondition_unavailable,
                    "interaction_precondition_callback_unavailable", {},
                    ack);
    }

    ActiveSchemeStateV1PrivateObservation first_observation{};
    if (!access.capture_observation(access.context, first_observation) ||
        first_observation.status !=
            ActiveSchemeStateV1PrivateStatus::available) {
      return Reject(request, Failure::observation_unavailable,
                    "active_scheme_observation_unavailable", {}, ack);
    }
    if (first_observation.capture_epoch != request.expected_capture_epoch ||
        first_observation.container_generation !=
            request.expected_container_generation ||
        first_observation.date_raw != request.expected_date_raw) {
      return Reject(request, Failure::snapshot_mismatch,
                    "active_scheme_snapshot_mismatch", {}, ack);
    }
    if (first_observation.played_character_id !=
        request.actor_character_id) {
      return Reject(request, Failure::actor_or_target_mismatch,
                    "played_character_mismatch", {}, ack);
    }
    if (HasMatchingScheme(first_observation, request.actor_character_id,
                          spec.scheme_type_key, request.target_kind,
                          request.target_id)) {
      return Reject(request, Failure::matching_scheme_already_active,
                    "matching_scheme_already_active", {}, ack);
    }

    ActiveSchemeSemanticActionV1PrivatePrecondition first_precondition{};
    if (!access.capture_precondition(access.context, first_precondition) ||
        !first_precondition.available || !first_precondition.paused) {
      return Reject(request, Failure::precondition_unavailable,
                    "paused_interaction_precondition_unavailable", {}, ack);
    }
    if (first_precondition.capture_epoch != first_observation.capture_epoch ||
        first_precondition.date_raw != first_observation.date_raw) {
      return Reject(request, Failure::snapshot_mismatch,
                    "precondition_not_from_active_scheme_frame", {}, ack);
    }
    if (first_precondition.actor_character_id !=
            request.actor_character_id ||
        first_precondition.target_kind != request.target_kind ||
        first_precondition.target_id != request.target_id ||
        first_precondition.interaction_key != request.interaction_key ||
        first_precondition.scheme_type_key != spec.scheme_type_key) {
      return Reject(request, Failure::actor_or_target_mismatch,
                    "precondition_identity_mismatch", {}, ack);
    }
    if (!first_precondition.shown_evaluated) {
      return Reject(request, Failure::precondition_unavailable,
                    "is_shown_unavailable", {}, ack);
    }
    if (!first_precondition.shown) {
      return Reject(request, Failure::interaction_not_shown,
                    "interaction_not_shown", first_precondition.native_reason_key,
                    ack);
    }
    if (!first_precondition.validity_evaluated) {
      return Reject(request, Failure::precondition_unavailable,
                    "validity_unavailable", {}, ack);
    }
    if (!first_precondition.valid) {
      return Reject(request, Failure::interaction_not_valid,
                    "interaction_not_valid",
                    first_precondition.native_reason_key, ack);
    }
    if (!first_precondition.can_start_scheme_evaluated) {
      return Reject(request, Failure::precondition_unavailable,
                    "can_start_scheme_unavailable", {}, ack);
    }
    if (!first_precondition.can_start_scheme) {
      return Reject(request, Failure::can_start_scheme_denied,
                    "can_start_scheme_denied",
                    first_precondition.native_reason_key, ack);
    }
    if (spec.murder_starter_required) {
      if (!first_precondition.starter_options_evaluated ||
          !first_precondition.starter_options_exclusive ||
          first_precondition.starter_option_count != 4 ||
          request.selected_starter_package !=
              first_precondition.selected_starter_package ||
          !ValidMurderStarter(request.selected_starter_package)) {
        return Reject(request, Failure::starter_package_invalid,
                      "murder_starter_package_invalid", {}, ack);
      }
    } else if (!request.selected_starter_package.empty() ||
               !first_precondition.selected_starter_package.empty()) {
      return Reject(request, Failure::starter_package_invalid,
                    "starter_package_not_applicable", {}, ack);
    }

    const auto &success = first_precondition.success_chance;
    const auto &maximum = first_precondition.maximum_success_chance;
    const auto &secrecy = first_precondition.secrecy;
    if (!PreviewStatusResolved(success.status) ||
        !PreviewStatusResolved(maximum.status) ||
        !PreviewStatusResolved(secrecy.status)) {
      return Reject(request, Failure::preview_unresolved,
                    "scheme_preview_unresolved", {}, ack);
    }
    if (success.status != maximum.status || !PreviewValueInRange(success) ||
        !PreviewValueInRange(maximum) || !PreviewValueInRange(secrecy) ||
        (success.status == PreviewStatus::available &&
         success.value > maximum.value)) {
      return Reject(request, Failure::preview_invalid,
                    "scheme_preview_invalid", {}, ack);
    }

    // Both sources are re-evaluated immediately before the only submit call.
    ActiveSchemeStateV1PrivateObservation second_observation{};
    ActiveSchemeSemanticActionV1PrivatePrecondition second_precondition{};
    if (!access.capture_observation(access.context, second_observation) ||
        !access.capture_precondition(access.context, second_precondition) ||
        !SameObservation(first_observation, second_observation) ||
        first_precondition != second_precondition) {
      return Reject(request, Failure::state_changed_before_submit,
                    "state_changed_before_submit", {}, ack);
    }

    ActiveSchemeSemanticActionV1PrivateCommand command{};
    command.request_id = request.request_id;
    command.interaction_key = request.interaction_key;
    command.scheme_type_key.assign(spec.scheme_type_key);
    command.actor_character_id = request.actor_character_id;
    command.target_kind = request.target_kind;
    command.target_id = request.target_id;
    command.selected_starter_package = request.selected_starter_package;

    const bool submitted = access.submit(access.context, command);
    if (!submitted) {
      Reject(request, Failure::submit_rejected, "submit_rejected", {}, ack);
      ack.submit_attempted = true;
      ack.submit_call_count = 1;
      return ack.status;
    }

    ack = {};
    ack.status = AckStatus::submitted_verification_pending;
    ack.failure = Failure::none;
    ack.request_id = request.request_id;
    ack.interaction_key = request.interaction_key;
    ack.scheme_type_key.assign(spec.scheme_type_key);
    ack.actor_character_id = request.actor_character_id;
    ack.target_kind = request.target_kind;
    ack.target_id = request.target_id;
    ack.pre_capture_epoch = first_observation.capture_epoch;
    ack.pre_container_generation = first_observation.container_generation;
    ack.pre_date_raw = first_observation.date_raw;
    ack.submit_attempted = true;
    ack.submit_call_count = 1;
    ack.verification_pending = true;
    ack.prior_identity_count = first_observation.row_count;
    for (std::size_t index = 0; index < first_observation.row_count; ++index) {
      ack.prior_identities[index] = {
          first_observation.rows[index].scheme_instance_id,
          first_observation.rows[index].scheme_instance_generation};
    }
    return ack.status;
  } catch (...) {
    return Reject(request, Failure::submit_rejected,
                  "action_executor_exception", {}, ack);
  }
}

ReceiptStatus VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
    const ActiveSchemeSemanticActionV1PrivateAccess &access,
    const ActiveSchemeSemanticActionV1PrivateAck &ack,
    ActiveSchemeSemanticActionV1PrivateReceipt &receipt) noexcept {
  receipt = {};
  receipt.request_id = ack.request_id;
  if (ack.status == AckStatus::rejected_before_submit) {
    receipt.status = ReceiptStatus::rejected;
    receipt.failure = ack.failure;
    receipt.reason = ack.reason;
    return receipt.status;
  }
  if (ack.status != AckStatus::submitted_verification_pending ||
      !ack.verification_pending || !ack.submit_attempted ||
      ack.submit_call_count != 1 || ack.pre_capture_epoch == 0 ||
      ack.prior_identity_count > ack.prior_identities.size()) {
    return Red(Failure::request_contract, "invalid_submit_ack", receipt);
  }
  if (access.capture_observation == nullptr) {
    return Red(Failure::post_observation_unavailable,
               "post_observation_callback_unavailable", receipt);
  }

  try {
    ActiveSchemeStateV1PrivateObservation post{};
    if (!access.capture_observation(access.context, post) ||
        post.status != ActiveSchemeStateV1PrivateStatus::available) {
      return Red(Failure::post_observation_unavailable,
                 "post_observation_unavailable", receipt);
    }
    receipt.post_capture_epoch = post.capture_epoch;
    receipt.post_container_generation = post.container_generation;
    receipt.post_date_raw = post.date_raw;
    if (post.capture_epoch <= ack.pre_capture_epoch) {
      return Red(Failure::post_observation_not_fresh,
                 "post_observation_not_fresh", receipt);
    }
    if (post.played_character_id != ack.actor_character_id) {
      return Red(Failure::post_actor_changed, "post_actor_changed", receipt);
    }

    const ActiveSchemeStateV1PrivateRow *match = nullptr;
    std::size_t match_count = 0;
    for (std::size_t index = 0; index < post.row_count; ++index) {
      const auto &row = post.rows[index];
      if (!MatchesScheme(row, ack.actor_character_id, ack.scheme_type_key,
                         ack.target_kind, ack.target_id) ||
          IsPriorIdentity(ack, row)) {
        continue;
      }
      match = &row;
      ++match_count;
    }
    if (match_count == 0) {
      return Red(Failure::postcondition_missing,
                 "new_matching_scheme_not_observed", receipt);
    }
    if (match_count != 1 || match == nullptr) {
      return Red(Failure::postcondition_ambiguous,
                 "multiple_new_matching_schemes_observed", receipt);
    }
    receipt.status = ReceiptStatus::applied;
    receipt.failure = Failure::none;
    receipt.reason.clear();
    receipt.scheme_instance_id = match->scheme_instance_id;
    receipt.scheme_instance_generation = match->scheme_instance_generation;
    receipt.postcondition_verified = true;
    return receipt.status;
  } catch (...) {
    return Red(Failure::post_observation_unavailable,
               "receipt_verifier_exception", receipt);
  }
}

std::string_view ActiveSchemeSemanticActionV1PrivateFailureName(
    Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::request_contract: return "request_contract";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::action_route_unavailable: return "action_route_unavailable";
  case Failure::observation_unavailable: return "observation_unavailable";
  case Failure::snapshot_mismatch: return "snapshot_mismatch";
  case Failure::actor_or_target_mismatch:
    return "actor_or_target_mismatch";
  case Failure::interaction_not_allowed: return "interaction_not_allowed";
  case Failure::matching_scheme_already_active:
    return "matching_scheme_already_active";
  case Failure::precondition_unavailable:
    return "precondition_unavailable";
  case Failure::interaction_not_shown: return "interaction_not_shown";
  case Failure::interaction_not_valid: return "interaction_not_valid";
  case Failure::can_start_scheme_denied: return "can_start_scheme_denied";
  case Failure::starter_package_invalid: return "starter_package_invalid";
  case Failure::preview_unresolved: return "preview_unresolved";
  case Failure::preview_invalid: return "preview_invalid";
  case Failure::state_changed_before_submit:
    return "state_changed_before_submit";
  case Failure::submit_rejected: return "submit_rejected";
  case Failure::post_observation_unavailable:
    return "post_observation_unavailable";
  case Failure::post_observation_not_fresh:
    return "post_observation_not_fresh";
  case Failure::post_actor_changed: return "post_actor_changed";
  case Failure::postcondition_missing: return "postcondition_missing";
  case Failure::postcondition_ambiguous: return "postcondition_ambiguous";
  }
  return "unknown";
}

} // namespace xar::bridge
