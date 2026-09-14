#include "xar_bridge/steward_develop_county_action_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using AckStatus = game::StewardDevelopCountyActionAckStatusV1;
using FailureClass = game::StewardDevelopCountyActionFailureClassV1;
using ReceiptStatus = game::StewardDevelopCountyActionReceiptStatusV1;

bool Positive(std::int32_t value) noexcept { return value > 0; }

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

AckStatus Reject(const game::StewardDevelopCountyActionRequestV1 &request,
                 FailureClass failure_class, std::string_view reason,
                 std::string_view native_reason_key,
                 game::StewardDevelopCountyActionAckV1 &ack) {
  ack = {};
  ack.request_id = request.request_id;
  ack.councillor_character_id = request.councillor_character_id;
  ack.task_key = request.task_key;
  ack.target_county_title_id = request.target_county_title_id;
  ack.failure_class = failure_class;
  ack.rejection_reason.assign(reason);
  ack.native_reason_key.assign(native_reason_key);
  return AckStatus::rejected_before_submit;
}

void CopyPostObservation(
    const game::StewardDevelopCountyTaskObservationV1 &post,
    game::StewardDevelopCountyActionReceiptV1 &receipt) {
  receipt.post_snapshot_revision = post.snapshot_revision;
  receipt.post_native_snapshot_revision = post.native_snapshot_revision;
  receipt.post_observed_date_raw = post.observed_date_raw;
  receipt.councillor_character_id = post.steward_character_id;
  receipt.active_task_key = post.active_task_key;
  receipt.target_county_title_id = post.active_target_county_title_id;
  receipt.target_province_id = post.active_target_province_id;
  if (post.progress_available) {
    receipt.progress_kind = post.progress_kind;
    receipt.progress_current_raw = post.progress_current_raw;
    receipt.progress_max_raw = post.progress_max_raw;
    receipt.progress_frozen = post.progress_frozen;
  }
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

std::string OptionalInt64(const std::optional<std::int64_t> &value) {
  return value ? std::to_string(*value) : "null";
}

std::string OptionalBool(const std::optional<bool> &value) {
  if (!value) return "null";
  return *value ? "true" : "false";
}

} // namespace

StewardDevelopCountyActionNativeEnvironmentV1
BindStewardDevelopCountyActionNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  // The command ABI is intentionally not enabled by address alone.  A later
  // exact-build capture must certify the factory, validator and submit seam.
  return {module_base, exact_build_admitted, false, false};
}

AckStatus ExecuteStewardDevelopCountyActionV1(
    const StewardDevelopCountyActionNativeEnvironmentV1 &environment,
    const StewardDevelopCountyActionAccessV1 &access,
    const game::StewardDevelopCountyActionRequestV1 &request,
    game::StewardDevelopCountyActionAckV1 &ack) noexcept {
  try {
    if (!ValidRequestId(request.request_id) ||
        !Positive(request.councillor_character_id) ||
        request.task_key != kStewardDevelopCountyActionV1TaskKey ||
        !Positive(request.target_county_title_id) ||
        request.expected_revision == 0) {
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
    game::StewardDevelopCountyTaskObservationV1 first{};
    if (!access.capture_observation(access.context, first) ||
        !first.available || !first.paused) {
      return Reject(request, FailureClass::snapshot_binding,
                    "paused_observation_unavailable", {}, ack);
    }
    if (first.snapshot_revision != request.expected_revision) {
      return Reject(request, FailureClass::snapshot_binding,
                    "stale_snapshot", {}, ack);
    }
    if (first.player_character_id <= 0 ||
        first.steward_character_id != request.councillor_character_id) {
      return Reject(request, FailureClass::councillor_binding,
                    "steward_identity_changed", {}, ack);
    }
    if (!first.target_candidate_present || !first.target_native_legal ||
        first.target_county_title_id != request.target_county_title_id ||
        !Positive(first.target_capital_province_id)) {
      return Reject(request, FailureClass::task_or_target_legality,
                    "candidate_not_from_bound_query", {}, ack);
    }
    const bool already_active =
        first.has_active_task &&
        first.active_task_key == kStewardDevelopCountyActionV1TaskKey &&
        first.active_target_county_title_id == request.target_county_title_id;
    if (already_active) {
      return Reject(request, FailureClass::task_or_target_legality,
                    "already_active_at_target", {}, ack);
    }
    if (first.has_active_task && !request.replace_existing_task) {
      return Reject(request, FailureClass::task_or_target_legality,
                    "replacement_not_authorized", {}, ack);
    }

    // Production remains strictly unavailable until all three native command
    // seams have been exact-build certified.  Offline fixtures must also opt
    // in explicitly; a zero module base alone cannot enable dispatch.
    const bool production_certified =
        environment.module_base != 0 && environment.command_abi_certified;
    const bool offline_certified =
        environment.module_base == 0 && environment.offline_fixture_command;
    if ((!production_certified && !offline_certified) ||
        access.validate_native == nullptr || access.submit_native == nullptr) {
      return Reject(request, FailureClass::native_command_dispatch,
                    "native_command_abi_not_certified", {}, ack);
    }

    bool native_valid = false;
    std::string native_reason_key;
    if (!access.validate_native(access.context,
                                request.councillor_character_id,
                                first.target_capital_province_id,
                                native_valid, native_reason_key)) {
      return Reject(request, FailureClass::native_command_dispatch,
                    "native_validator_unavailable", native_reason_key, ack);
    }
    if (!native_valid) {
      return Reject(request, FailureClass::task_or_target_legality,
                    "native_validation_failed", native_reason_key, ack);
    }

    // Re-read through the same observer immediately before submit.  This is a
    // binding check, not the postcondition receipt observation.
    game::StewardDevelopCountyTaskObservationV1 second{};
    if (!access.capture_observation(access.context, second) ||
        first != second) {
      return Reject(request, FailureClass::snapshot_binding,
                    "state_changed_before_submit", {}, ack);
    }
    if (!access.submit_native(access.context,
                              request.councillor_character_id,
                              first.target_capital_province_id)) {
      return Reject(request, FailureClass::native_command_dispatch,
                    "native_command_submit_failed", {}, ack);
    }

    ack = {};
    ack.status = AckStatus::submitted_verification_pending;
    ack.verification_pending = true;
    ack.request_id = request.request_id;
    ack.pre_snapshot_revision = first.snapshot_revision;
    ack.pre_native_snapshot_revision = first.native_snapshot_revision;
    ack.councillor_character_id = request.councillor_character_id;
    ack.task_key.assign(kStewardDevelopCountyActionV1TaskKey);
    ack.target_county_title_id = request.target_county_title_id;
    ack.submitted_target_province_id = first.target_capital_province_id;
    ack.replaced_existing_task = first.has_active_task;
    ack.failure_class = FailureClass::none;
    return ack.status;
  } catch (...) {
    return Reject(request, FailureClass::native_command_dispatch,
                  "action_executor_exception", {}, ack);
  }
}

ReceiptStatus VerifyStewardDevelopCountyActionReceiptV1(
    const game::StewardDevelopCountyActionAckV1 &ack,
    const game::StewardDevelopCountyTaskObservationV1 &post,
  game::StewardDevelopCountyActionReceiptV1 &receipt) noexcept {
  receipt = {};
  receipt.request_id = ack.request_id;
  if (ack.status == AckStatus::rejected_before_submit) {
    receipt.status = ReceiptStatus::rejected;
    receipt.reason = ack.rejection_reason;
    return receipt.status;
  }
  CopyPostObservation(post, receipt);
  const auto fail = [&](std::string_view reason) noexcept {
    receipt.status = ReceiptStatus::postcondition_failed;
    receipt.reason.assign(reason);
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
  if (post.steward_character_id != ack.councillor_character_id) {
    return fail("player_or_steward_changed");
  }
  if (!post.has_active_task ||
      post.active_task_key != kStewardDevelopCountyActionV1TaskKey ||
      post.active_task_type != "county" ||
      post.active_target_county_title_id != ack.target_county_title_id ||
      post.active_target_province_id != ack.submitted_target_province_id) {
    return fail("wrong_task_or_target_observed");
  }
  if (!post.progress_available || post.progress_kind != "value") {
    return fail("progress_binding_unavailable");
  }
  receipt.status = ReceiptStatus::applied;
  receipt.reason.clear();
  receipt.postcondition_verified = true;
  return receipt.status;
}

std::string_view StewardDevelopCountyActionFailureClassKeyV1(
    FailureClass value) noexcept {
  switch (value) {
  case FailureClass::none: return "none";
  case FailureClass::request_contract: return "request_contract";
  case FailureClass::snapshot_binding: return "snapshot_binding";
  case FailureClass::councillor_binding: return "councillor_binding";
  case FailureClass::task_or_target_legality:
    return "task_or_target_legality";
  case FailureClass::native_command_dispatch:
    return "native_command_dispatch";
  }
  return "native_command_dispatch";
}

std::string SerializeStewardDevelopCountyActionAckV1(
    const game::StewardDevelopCountyActionAckV1 &ack) {
  const auto status = ack.status == AckStatus::submitted_verification_pending
                          ? "submitted_verification_pending"
                          : "rejected_before_submit";
  return "{\"schema_version\":1,\"contract_stage\":" +
         Quote(kStewardDevelopCountyActionV1ContractStage) +
         ",\"status\":" + Quote(status) +
         ",\"verification_pending\":" +
         (ack.verification_pending ? "true" : "false") +
         ",\"request_id\":" + Quote(ack.request_id) +
         ",\"pre_snapshot_revision\":" +
         std::to_string(ack.pre_snapshot_revision) +
         ",\"pre_native_snapshot_revision\":" +
         std::to_string(ack.pre_native_snapshot_revision) +
         ",\"councillor_character_id\":" +
         std::to_string(ack.councillor_character_id) +
         ",\"task_key\":" + Quote(ack.task_key) +
         ",\"target_county_title_id\":" +
         std::to_string(ack.target_county_title_id) +
         ",\"submitted_target_province_id\":" +
         std::to_string(ack.submitted_target_province_id) +
         ",\"replaced_existing_task\":" +
         (ack.replaced_existing_task ? "true" : "false") +
         ",\"failure_class\":" +
         Quote(StewardDevelopCountyActionFailureClassKeyV1(
             ack.failure_class)) +
         ",\"rejection_reason\":" +
         (ack.rejection_reason.empty() ? "null" : Quote(ack.rejection_reason)) +
         ",\"native_reason_key\":" +
         (ack.native_reason_key.empty() ? "null" : Quote(ack.native_reason_key)) +
         ",\"exact_build\":{\"game_version\":" +
         Quote(kStewardDevelopCountyActionV1GameVersion) +
         ",\"executable_sha256\":" +
         Quote(kStewardDevelopCountyActionV1ExecutableSha256) +
         ",\"backend_id\":" + Quote(kStewardDevelopCountyActionV1BackendId) +
         "}}";
}

std::string SerializeStewardDevelopCountyActionReceiptV1(
    const game::StewardDevelopCountyActionReceiptV1 &receipt) {
  std::string_view status = "postcondition_failed";
  if (receipt.status == ReceiptStatus::applied) status = "applied";
  if (receipt.status == ReceiptStatus::rejected) status = "rejected";
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
         ",\"councillor_character_id\":" +
         std::to_string(receipt.councillor_character_id) +
         ",\"active_task_key\":" + Quote(receipt.active_task_key) +
         ",\"target_county_title_id\":" +
         OptionalInt32(receipt.target_county_title_id) +
         ",\"target_province_id\":" +
         OptionalInt32(receipt.target_province_id) +
         ",\"progress_kind\":" + Quote(receipt.progress_kind) +
         ",\"progress_current_raw\":" +
         OptionalInt64(receipt.progress_current_raw) +
         ",\"progress_max_raw\":" +
         OptionalInt64(receipt.progress_max_raw) +
         ",\"progress_frozen\":" +
         OptionalBool(receipt.progress_frozen) +
         ",\"postcondition_verified\":" +
         (receipt.postcondition_verified ? "true" : "false") + "}";
}

} // namespace xar::ck3_11906
