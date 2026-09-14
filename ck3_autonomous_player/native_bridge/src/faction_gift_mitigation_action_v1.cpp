#include "xar_bridge/faction_gift_mitigation_action_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using AckStatus = game::FactionGiftMitigationAckStatusV1;
using FailureClass = game::FactionGiftMitigationFailureClassV1;
using MembershipRole = game::FactionGiftMembershipRoleV1;
using ReceiptStatus = game::FactionGiftMitigationReceiptStatusV1;

bool ValidToken(std::string_view value) noexcept {
  if (value.empty() || value.size() > 96) return false;
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

bool ValidRole(MembershipRole value) noexcept {
  return value == MembershipRole::leader ||
         value == MembershipRole::character_member;
}

bool StrictlyIncreasingNonZero(
    const std::vector<std::uint32_t> &values) noexcept {
  if (values.empty()) return true;
  if (values.front() == 0) return false;
  for (std::size_t index = 1; index < values.size(); ++index) {
    if (values[index] == 0 || values[index - 1] >= values[index]) return false;
  }
  return true;
}

bool Contains(const std::vector<std::uint32_t> &values,
              std::uint32_t value) noexcept {
  return std::binary_search(values.begin(), values.end(), value);
}

bool BoundMembership(
    const game::FactionGiftMitigationObservationV1 &observation,
    const game::FactionGiftMitigationRequestV1 &request) noexcept {
  if (request.membership_role == MembershipRole::leader) {
    return observation.source_faction_leader_character_id ==
           request.recipient_character_id;
  }
  return request.membership_role == MembershipRole::character_member &&
         Contains(observation.source_faction_member_character_ids,
                  request.recipient_character_id);
}

AckStatus Reject(const game::FactionGiftMitigationRequestV1 &request,
                 FailureClass failure_class, std::string_view reason,
                 std::string_view native_reason_key,
                 game::FactionGiftMitigationAckV1 &ack) {
  ack = {};
  ack.request_id = request.request_id;
  ack.player_character_id = request.player_character_id;
  ack.source_faction_id = request.source_faction_id;
  ack.recipient_character_id = request.recipient_character_id;
  ack.membership_role = request.membership_role;
  ack.definition_key = request.expected_definition_key;
  ack.definition_stable_hash = request.expected_definition_stable_hash;
  ack.expected_gold_cost_raw = request.expected_gold_cost_raw;
  ack.gold_scale = request.expected_gold_scale;
  ack.expected_opinion_delta = request.expected_opinion_delta;
  ack.minimum_gold_reserve_raw = request.minimum_gold_reserve_raw;
  ack.failure_class = failure_class;
  ack.rejection_reason.assign(reason);
  ack.native_reason_key.assign(native_reason_key);
  return AckStatus::rejected_before_submit;
}

AckStatus ValidateBoundObservation(
    const game::FactionGiftMitigationObservationV1 &observation,
    const game::FactionGiftMitigationRequestV1 &request,
    game::FactionGiftMitigationAckV1 &ack) {
  if (!observation.available || !observation.paused ||
      !observation.player_resources_query_complete ||
      !observation.source_faction_requery_complete ||
      !observation.recipient_opinion_query_complete) {
    return Reject(request, FailureClass::snapshot_binding,
                  "paused_bound_observation_unavailable", {}, ack);
  }
  if (observation.snapshot_revision != request.expected_revision ||
      observation.native_snapshot_revision !=
          request.expected_native_revision ||
      observation.observed_date_raw != request.expected_date_raw) {
    return Reject(request, FailureClass::snapshot_binding,
                  "stale_snapshot", {}, ack);
  }
  if (observation.player_character_id != request.player_character_id ||
      observation.player_gold_scale != request.expected_gold_scale) {
    return Reject(request, FailureClass::snapshot_binding,
                  "player_or_resource_binding_changed", {}, ack);
  }
  if (observation.queried_source_faction_id != request.source_faction_id ||
      !observation.source_faction_present ||
      !observation.source_faction_targeting_player ||
      observation.source_faction_target_character_id !=
          request.player_character_id ||
      observation.source_faction_at_war ||
      !StrictlyIncreasingNonZero(
          observation.source_faction_member_character_ids)) {
    return Reject(request, FailureClass::faction_binding,
                  "not_a_bound_peacetime_targeting_faction", {}, ack);
  }
  if (!observation.recipient_identity_resolved ||
      observation.recipient_character_id != request.recipient_character_id ||
      !BoundMembership(observation, request) || !observation.recipient_alive ||
      !observation.recipient_is_ai ||
      !observation.recipient_is_direct_landed_vassal ||
      observation.gift_opinion_present) {
    return Reject(request, FailureClass::recipient_binding,
                  "recipient_not_a_real_eligible_row_identity", {}, ack);
  }
  const auto &preview = observation.gift_preview;
  if (!preview.available ||
      preview.definition_key != kFactionGiftMitigationActionV1DefinitionKey ||
      preview.definition_key != request.expected_definition_key ||
      preview.definition_stable_hash == 0 ||
      preview.definition_stable_hash !=
          request.expected_definition_stable_hash ||
      !preview.interaction_legal || !preview.auto_accept ||
      preview.gold_cost_raw <= 0 ||
      preview.gold_cost_raw != request.expected_gold_cost_raw ||
      preview.gold_scale != kFactionGiftMitigationActionV1GoldScale ||
      preview.gold_scale != request.expected_gold_scale ||
      preview.opinion_delta <= 0 ||
      preview.opinion_delta != request.expected_opinion_delta) {
    return Reject(request, FailureClass::gift_preview_legality,
                  "gift_preview_not_exact_or_legal", {}, ack);
  }
  if (observation.player_gold_raw < preview.gold_cost_raw ||
      observation.player_gold_raw - preview.gold_cost_raw <
          request.minimum_gold_reserve_raw) {
    return Reject(request, FailureClass::budget_gate,
                  "minimum_gold_reserve_not_satisfied", {}, ack);
  }
  return AckStatus::submitted_verification_pending;
}

void CopyPostObservation(
    const game::FactionGiftMitigationObservationV1 &post,
    game::FactionGiftMitigationReceiptV1 &receipt) {
  receipt.post_snapshot_revision = post.snapshot_revision;
  receipt.post_native_snapshot_revision = post.native_snapshot_revision;
  receipt.post_observed_date_raw = post.observed_date_raw;
  receipt.player_character_id = post.player_character_id;
  receipt.source_faction_id = post.queried_source_faction_id;
  receipt.recipient_character_id = post.recipient_character_id;
  receipt.post_player_gold_raw = post.player_gold_raw;
  receipt.post_recipient_opinion_of_player =
      post.recipient_opinion_of_player;
  receipt.post_gift_opinion_present = post.gift_opinion_present;
  receipt.post_gift_opinion_modifier_value =
      post.gift_opinion_modifier_value;
  receipt.source_faction_present = post.source_faction_present;
}

std::string Escape(std::string_view value) {
  std::string output;
  output.reserve(value.size() + 8);
  for (const char character : value) {
    if (character == '\\' || character == '"') output.push_back('\\');
    output.push_back(character);
  }
  return output;
}

std::string Quote(std::string_view value) {
  return "\"" + Escape(value) + "\"";
}

std::string OptionalInt32(const std::optional<std::int32_t> &value) {
  return value ? std::to_string(*value) : "null";
}

std::string_view RoleKey(MembershipRole value) noexcept {
  return value == MembershipRole::leader ? "leader" : "character_member";
}

} // namespace

FactionGiftMitigationNativeEnvironmentV1
BindFactionGiftMitigationNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  return {module_base, exact_build_admitted, false, false};
}

AckStatus ExecuteFactionGiftMitigationActionV1(
    const FactionGiftMitigationNativeEnvironmentV1 &environment,
    const FactionGiftMitigationActionAccessV1 &access,
    const game::FactionGiftMitigationRequestV1 &request,
    game::FactionGiftMitigationAckV1 &ack) noexcept {
  try {
    if (!ValidToken(request.request_id) ||
        !ValidToken(request.idempotency_key) ||
        request.expected_revision == 0 ||
        request.expected_native_revision == 0 ||
        request.player_character_id == 0 || request.source_faction_id == 0 ||
        request.recipient_character_id == 0 ||
        request.recipient_character_id == request.player_character_id ||
        !ValidRole(request.membership_role) ||
        request.expected_definition_key !=
            kFactionGiftMitigationActionV1DefinitionKey ||
        request.expected_definition_stable_hash == 0 ||
        request.expected_gold_cost_raw <= 0 ||
        request.expected_gold_scale !=
            kFactionGiftMitigationActionV1GoldScale ||
        request.expected_opinion_delta <= 0 ||
        request.minimum_gold_reserve_raw < 0 ||
        request.minimum_gold_reserve_scale != request.expected_gold_scale) {
      return Reject(request, FailureClass::request_contract,
                    "invalid_request", {}, ack);
    }
    if (!environment.exact_build_admitted) {
      return Reject(request, FailureClass::native_command_dispatch,
                    "unsupported_build", {}, ack);
    }
    if (access.capture_observation == nullptr) {
      return Reject(request, FailureClass::snapshot_binding,
                    "observation_unavailable", {}, ack);
    }

    game::FactionGiftMitigationObservationV1 first{};
    if (!access.capture_observation(access.context, first)) {
      return Reject(request, FailureClass::snapshot_binding,
                    "observation_unavailable", {}, ack);
    }
    if (ValidateBoundObservation(first, request, ack) !=
        AckStatus::submitted_verification_pending) {
      return ack.status;
    }

    const bool production_certified =
        environment.module_base != 0 && environment.command_abi_certified;
    const bool offline_certified =
        environment.module_base == 0 && environment.offline_fixture_command;
    if ((!production_certified && !offline_certified) ||
        access.validate_native == nullptr ||
        access.claim_idempotency_key == nullptr ||
        access.submit_native == nullptr) {
      return Reject(request, FailureClass::native_command_dispatch,
                    "native_command_abi_not_certified", {}, ack);
    }

    bool native_valid = false;
    std::string native_reason_key;
    if (!access.validate_native(
            access.context, request.player_character_id,
            request.recipient_character_id, request.expected_definition_key,
            native_valid, native_reason_key)) {
      return Reject(request, FailureClass::native_command_dispatch,
                    "native_validator_unavailable", native_reason_key, ack);
    }
    if (!native_valid) {
      return Reject(request, FailureClass::gift_preview_legality,
                    "native_validation_failed", native_reason_key, ack);
    }

    game::FactionGiftMitigationObservationV1 second{};
    if (!access.capture_observation(access.context, second) ||
        first != second) {
      return Reject(request, FailureClass::snapshot_binding,
                    "state_changed_before_submit", {}, ack);
    }
    if (!access.claim_idempotency_key(access.context,
                                      request.idempotency_key)) {
      return Reject(request, FailureClass::idempotency,
                    "idempotency_key_already_claimed", {}, ack);
    }
    if (!access.submit_native(access.context, request.player_character_id,
                              request.recipient_character_id,
                              request.expected_definition_stable_hash)) {
      return Reject(request, FailureClass::native_command_dispatch,
                    "native_command_submit_failed", {}, ack);
    }

    ack = {};
    ack.status = AckStatus::submitted_verification_pending;
    ack.verification_pending = true;
    ack.request_id = request.request_id;
    ack.pre_snapshot_revision = first.snapshot_revision;
    ack.pre_native_snapshot_revision = first.native_snapshot_revision;
    ack.pre_observed_date_raw = first.observed_date_raw;
    ack.player_character_id = request.player_character_id;
    ack.source_faction_id = request.source_faction_id;
    ack.recipient_character_id = request.recipient_character_id;
    ack.membership_role = request.membership_role;
    ack.definition_key = request.expected_definition_key;
    ack.definition_stable_hash = request.expected_definition_stable_hash;
    ack.expected_gold_cost_raw = request.expected_gold_cost_raw;
    ack.gold_scale = request.expected_gold_scale;
    ack.expected_opinion_delta = request.expected_opinion_delta;
    ack.pre_player_gold_raw = first.player_gold_raw;
    ack.minimum_gold_reserve_raw = request.minimum_gold_reserve_raw;
    ack.failure_class = FailureClass::none;
    return ack.status;
  } catch (...) {
    return Reject(request, FailureClass::native_command_dispatch,
                  "action_executor_exception", {}, ack);
  }
}

ReceiptStatus VerifyFactionGiftMitigationReceiptV1(
    const game::FactionGiftMitigationAckV1 &ack,
    const game::FactionGiftMitigationObservationV1 &post,
    game::FactionGiftMitigationReceiptV1 &receipt) noexcept {
  receipt = {};
  receipt.request_id = ack.request_id;
  if (ack.status == AckStatus::rejected_before_submit) {
    receipt.status = ReceiptStatus::rejected;
    receipt.reason = ack.rejection_reason;
    return receipt.status;
  }

  CopyPostObservation(post, receipt);
  const auto fail = [&](std::string_view reason) noexcept {
    receipt.status = ReceiptStatus::failed;
    receipt.reason.assign(reason);
    receipt.faction_dissolved = false;
    receipt.recipient_left = false;
    receipt.mitigation_applied = false;
    receipt.threat_resolved = false;
    receipt.postcondition_verified = false;
    return receipt.status;
  };
  if (ack.status != AckStatus::submitted_verification_pending ||
      !ack.verification_pending) {
    return fail("invalid_ack");
  }
  if (!post.available || !post.paused ||
      post.snapshot_revision <= ack.pre_snapshot_revision ||
      post.native_snapshot_revision <= ack.pre_native_snapshot_revision) {
    return fail("no_new_paused_observation");
  }
  if (post.observed_date_raw != ack.pre_observed_date_raw ||
      !post.player_resources_query_complete ||
      post.player_character_id != ack.player_character_id ||
      post.player_gold_scale != ack.gold_scale) {
    return fail("same_date_resource_requery_failed");
  }
  if (ack.pre_player_gold_raw < ack.expected_gold_cost_raw ||
      post.player_gold_raw !=
          ack.pre_player_gold_raw - ack.expected_gold_cost_raw) {
    return fail("gift_gold_delta_not_observed");
  }
  if (!post.recipient_identity_resolved ||
      post.recipient_character_id != ack.recipient_character_id ||
      !post.recipient_alive || !post.recipient_opinion_query_complete ||
      !post.gift_opinion_present ||
      post.gift_opinion_modifier_value != ack.expected_opinion_delta) {
    return fail("recipient_gift_opinion_not_observed");
  }
  if (!post.source_faction_requery_complete ||
      post.queried_source_faction_id != ack.source_faction_id) {
    return fail("same_faction_requery_failed");
  }

  bool recipient_still_present = false;
  if (post.source_faction_present) {
    if (!post.source_faction_metrics_available ||
        post.source_faction_metric_scale == 0 ||
        !StrictlyIncreasingNonZero(
            post.source_faction_member_character_ids)) {
      return fail("same_faction_requery_incomplete");
    }
    recipient_still_present =
        post.source_faction_leader_character_id ==
            ack.recipient_character_id ||
        Contains(post.source_faction_member_character_ids,
                 ack.recipient_character_id);
  }

  receipt.source_faction_present = post.source_faction_present;
  receipt.recipient_still_in_source_faction = recipient_still_present;
  receipt.faction_dissolved = !post.source_faction_present;
  receipt.recipient_left =
      post.source_faction_present && !recipient_still_present;
  receipt.mitigation_applied = true;
  receipt.threat_resolved = !post.source_faction_present ||
                            !recipient_still_present ||
                            !post.source_faction_targeting_player;
  receipt.postcondition_verified = true;
  receipt.reason.clear();
  if (receipt.threat_resolved) {
    receipt.status = ReceiptStatus::left;
  } else {
    receipt.status = ReceiptStatus::mitigated;
  }
  return receipt.status;
}

std::string_view FactionGiftMitigationFailureClassKeyV1(
    FailureClass value) noexcept {
  switch (value) {
  case FailureClass::none: return "none";
  case FailureClass::request_contract: return "request_contract";
  case FailureClass::snapshot_binding: return "snapshot_binding";
  case FailureClass::faction_binding: return "faction_binding";
  case FailureClass::recipient_binding: return "recipient_binding";
  case FailureClass::gift_preview_legality: return "gift_preview_legality";
  case FailureClass::budget_gate: return "budget_gate";
  case FailureClass::idempotency: return "idempotency";
  case FailureClass::native_command_dispatch:
    return "native_command_dispatch";
  }
  return "native_command_dispatch";
}

std::string SerializeFactionGiftMitigationAckV1(
    const game::FactionGiftMitigationAckV1 &ack) {
  const auto status = ack.status == AckStatus::submitted_verification_pending
                          ? "submitted_verification_pending"
                          : "rejected_before_submit";
  return "{\"schema_version\":1,\"contract_stage\":" +
         Quote(kFactionGiftMitigationActionV1ContractStage) +
         ",\"status\":" + Quote(status) +
         ",\"verification_pending\":" +
         (ack.verification_pending ? "true" : "false") +
         ",\"request_id\":" + Quote(ack.request_id) +
         ",\"pre_snapshot_revision\":" +
         std::to_string(ack.pre_snapshot_revision) +
         ",\"pre_native_snapshot_revision\":" +
         std::to_string(ack.pre_native_snapshot_revision) +
         ",\"pre_observed_date_raw\":" +
         std::to_string(ack.pre_observed_date_raw) +
         ",\"player_character_id\":" +
         std::to_string(ack.player_character_id) +
         ",\"source_faction_id\":" +
         std::to_string(ack.source_faction_id) +
         ",\"recipient_character_id\":" +
         std::to_string(ack.recipient_character_id) +
         ",\"membership_role\":" + Quote(RoleKey(ack.membership_role)) +
         ",\"definition_key\":" + Quote(ack.definition_key) +
         ",\"definition_stable_hash\":" +
         std::to_string(ack.definition_stable_hash) +
         ",\"expected_gold_cost_raw\":" +
         std::to_string(ack.expected_gold_cost_raw) +
         ",\"gold_scale\":" + std::to_string(ack.gold_scale) +
         ",\"expected_opinion_delta\":" +
         std::to_string(ack.expected_opinion_delta) +
         ",\"pre_player_gold_raw\":" +
         std::to_string(ack.pre_player_gold_raw) +
         ",\"minimum_gold_reserve_raw\":" +
         std::to_string(ack.minimum_gold_reserve_raw) +
         ",\"failure_class\":" +
         Quote(FactionGiftMitigationFailureClassKeyV1(ack.failure_class)) +
         ",\"rejection_reason\":" +
         (ack.rejection_reason.empty() ? "null" : Quote(ack.rejection_reason)) +
         ",\"native_reason_key\":" +
         (ack.native_reason_key.empty() ? "null" :
                                          Quote(ack.native_reason_key)) +
         ",\"exact_build\":{\"game_version\":" +
         Quote(kFactionGiftMitigationActionV1GameVersion) +
         ",\"executable_sha256\":" +
         Quote(kFactionGiftMitigationActionV1ExecutableSha256) +
         ",\"backend_id\":" + Quote(kFactionGiftMitigationActionV1BackendId) +
         "}}";
}

std::string SerializeFactionGiftMitigationReceiptV1(
    const game::FactionGiftMitigationReceiptV1 &receipt) {
  std::string_view status = "failed";
  if (receipt.status == ReceiptStatus::rejected) status = "rejected";
  if (receipt.status == ReceiptStatus::mitigated) status = "mitigated";
  if (receipt.status == ReceiptStatus::left) status = "left";
  return "{\"schema_version\":1,\"status\":" + Quote(status) +
         ",\"request_id\":" + Quote(receipt.request_id) +
         ",\"reason\":" +
         (receipt.reason.empty() ? "null" : Quote(receipt.reason)) +
         ",\"post_snapshot_revision\":" +
         std::to_string(receipt.post_snapshot_revision) +
         ",\"post_native_snapshot_revision\":" +
         std::to_string(receipt.post_native_snapshot_revision) +
         ",\"post_observed_date_raw\":" +
         std::to_string(receipt.post_observed_date_raw) +
         ",\"player_character_id\":" +
         std::to_string(receipt.player_character_id) +
         ",\"source_faction_id\":" +
         std::to_string(receipt.source_faction_id) +
         ",\"recipient_character_id\":" +
         std::to_string(receipt.recipient_character_id) +
         ",\"post_player_gold_raw\":" +
         std::to_string(receipt.post_player_gold_raw) +
         ",\"post_recipient_opinion_of_player\":" +
         std::to_string(receipt.post_recipient_opinion_of_player) +
         ",\"post_gift_opinion_present\":" +
         (receipt.post_gift_opinion_present ? "true" : "false") +
         ",\"post_gift_opinion_modifier_value\":" +
         OptionalInt32(receipt.post_gift_opinion_modifier_value) +
         ",\"source_faction_present\":" +
         (receipt.source_faction_present ? "true" : "false") +
         ",\"recipient_still_in_source_faction\":" +
         (receipt.recipient_still_in_source_faction ? "true" : "false") +
         ",\"faction_dissolved\":" +
         (receipt.faction_dissolved ? "true" : "false") +
         ",\"recipient_left\":" +
         (receipt.recipient_left ? "true" : "false") +
         ",\"mitigation_applied\":" +
         (receipt.mitigation_applied ? "true" : "false") +
         ",\"threat_resolved\":" +
         (receipt.threat_resolved ? "true" : "false") +
         ",\"postcondition_verified\":" +
         (receipt.postcondition_verified ? "true" : "false") + "}";
}

} // namespace xar::ck3_11906
