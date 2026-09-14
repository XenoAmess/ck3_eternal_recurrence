#include "xar_bridge/player_prisoner_management_action_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {
namespace {

using AckStatus = PlayerPrisonerActionAckStatusV1;
using Action = PlayerPrisonerActionKindV1;
using Failure = PlayerPrisonerActionFailureClassV1;
using FieldState = PlayerPrisonerFieldStateV1;
using NativeSource = PlayerPrisonerNativeReasonSourceV1;
using PreviewSource = PlayerPrisonerPreviewSourceV1;
using ReceiptStatus = PlayerPrisonerActionReceiptStatusV1;

bool ValidRequestToken(std::string_view value) noexcept {
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

bool ValidAction(Action action) noexcept {
  return action == Action::ransom ||
      action == Action::release_unconditional ||
      action == Action::punish_execute;
}

bool ValidRequest(const PlayerPrisonerActionRequestV1 &request) noexcept {
  return ValidRequestToken(request.request_id) && ValidAction(request.action) &&
      request.expected_player_character_id > 0 &&
      request.prisoner_character_id > 0 &&
      request.prisoner_character_id != request.expected_player_character_id &&
      request.expected_public_revision != 0 &&
      request.expected_native_revision != 0 &&
      request.expected_proof_epoch != 0 && request.expected_date_raw > 0;
}

bool EnvironmentReady(
    const PlayerPrisonerActionEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.admitted_executable_sha256 !=
          kPlayerPrisonerManagementActionV1ExecutableSha256) {
    return false;
  }
  const bool production = environment.module_base != 0 &&
      environment.command_abi_certified &&
      !environment.offline_fixture_command;
  const bool fixture = environment.module_base == 0 &&
      !environment.command_abi_certified &&
      environment.offline_fixture_command;
  return production || fixture;
}

bool EquivalentSnapshot(const PlayerPrisonerManagementSnapshotV1 &left,
                        const PlayerPrisonerManagementSnapshotV1 &right)
    noexcept {
  if (left.status != right.status ||
      left.unavailable_reason != right.unavailable_reason ||
      left.public_revision != right.public_revision ||
      left.native_revision != right.native_revision ||
      left.proof_epoch != right.proof_epoch || left.date_raw != right.date_raw ||
      left.played_character_id != right.played_character_id ||
      left.total_prisoner_count != right.total_prisoner_count ||
      left.prisoner_count != right.prisoner_count ||
      left.religious_details_exposed != right.religious_details_exposed ||
      left.readiness != right.readiness ||
      left.prisoner_count > kPlayerPrisonerMaximumRowsV1) {
    return false;
  }
  return std::equal(left.prisoners.begin(),
                    left.prisoners.begin() + left.prisoner_count,
                    right.prisoners.begin());
}

bool SnapshotBoundToRequest(
    const PlayerPrisonerManagementSnapshotV1 &snapshot,
    const PlayerPrisonerActionRequestV1 &request) noexcept {
  if (snapshot.status != PlayerPrisonerSnapshotStatusV1::available ||
      snapshot.unavailable_reason != PlayerPrisonerSnapshotFailureV1::none ||
      snapshot.public_revision != request.expected_public_revision ||
      snapshot.native_revision != request.expected_native_revision ||
      snapshot.proof_epoch != request.expected_proof_epoch ||
      snapshot.date_raw != request.expected_date_raw ||
      snapshot.played_character_id !=
          request.expected_player_character_id ||
      snapshot.total_prisoner_count != snapshot.prisoner_count ||
      snapshot.prisoner_count > kPlayerPrisonerMaximumRowsV1 ||
      snapshot.religious_details_exposed ||
      !snapshot.readiness.collection_ready ||
      !snapshot.readiness.same_frame_ready) {
    return false;
  }
  switch (request.action) {
  case Action::ransom:
    return snapshot.readiness.ransom_previews_ready &&
        snapshot.readiness.ransom_candidate_available;
  case Action::release_unconditional:
    return snapshot.readiness.release_previews_ready;
  case Action::punish_execute:
    return snapshot.readiness.crime_reasons_ready &&
        snapshot.readiness.punishment_legality_ready;
  case Action::unknown:
    return false;
  }
  return false;
}

const PlayerPrisonerRowV1 *FindUniquePrisoner(
    const PlayerPrisonerManagementSnapshotV1 &snapshot,
    std::int32_t prisoner_character_id) noexcept {
  const PlayerPrisonerRowV1 *match = nullptr;
  for (std::uint32_t index = 0; index < snapshot.prisoner_count; ++index) {
    if (snapshot.prisoners[index].prisoner_character_id ==
        prisoner_character_id) {
      if (match != nullptr) return nullptr;
      match = &snapshot.prisoners[index];
    }
  }
  return match;
}

bool PreviewCanSend(
    const PlayerPrisonerInteractionPreviewV1 &preview) noexcept {
  return preview.state == FieldState::known &&
      preview.source ==
          PreviewSource::native_finalized_character_interaction &&
      preview.shown && preview.valid && preview.can_send;
}

bool OpaqueFinalKnown(
    const PlayerPrisonerOpaqueFinalBoolV1 &value) noexcept {
  return value.state == FieldState::known &&
      value.source == NativeSource::native_opaque_final;
}

bool KnownKey(const PlayerPrisonerTypedKeyV1 &key) noexcept {
  return key.state == FieldState::known &&
      !PlayerPrisonerKeyViewV1(key.value).empty();
}

bool FillSubmission(const PlayerPrisonerActionRequestV1 &request,
                    const PlayerPrisonerManagementSnapshotV1 &snapshot,
                    const PlayerPrisonerRowV1 &row,
                    PlayerPrisonerActionSubmissionV1 &submission) noexcept {
  submission = {};
  submission.action = request.action;
  submission.player_character_id = snapshot.played_character_id;
  submission.prisoner_character_id = row.prisoner_character_id;
  submission.pre_public_revision = snapshot.public_revision;
  submission.pre_native_revision = snapshot.native_revision;
  submission.pre_proof_epoch = snapshot.proof_epoch;
  submission.pre_date_raw = snapshot.date_raw;
  switch (request.action) {
  case Action::ransom:
    if (!PreviewCanSend(row.ransom.interaction) ||
        row.ransom.payer_character_id <= 0 ||
        !KnownKey(row.ransom.selected_option_key) ||
        !KnownKey(row.ransom.resource_key) ||
        row.ransom.resource_amount_raw < 0 ||
        (row.ransom.acceptance_required &&
         (!OpaqueFinalKnown(row.ransom.would_accept_now) ||
          !row.ransom.would_accept_now.value))) {
      return false;
    }
    submission.payer_character_id = row.ransom.payer_character_id;
    submission.selected_option_key = row.ransom.selected_option_key;
    submission.resource_key = row.ransom.resource_key;
    submission.resource_amount_raw = row.ransom.resource_amount_raw;
    return true;
  case Action::release_unconditional:
    return PreviewCanSend(row.release_unconditional);
  case Action::punish_execute:
    // has_execute_reason can contain faith-derived logic, but it remains one
    // opaque engine-final result. Can Send is the actual authorization gate.
    return OpaqueFinalKnown(row.has_execute_reason) &&
        PreviewCanSend(row.execute);
  case Action::unknown:
    return false;
  }
  return false;
}

AckStatus Reject(const PlayerPrisonerActionRequestV1 &request,
                 Failure failure, std::string_view reason,
                 PlayerPrisonerActionAckV1 &ack) {
  ack = {};
  ack.request_id.assign(request.request_id);
  ack.action = request.action;
  ack.player_character_id = request.expected_player_character_id;
  ack.prisoner_character_id = request.prisoner_character_id;
  ack.failure_class = failure;
  ack.rejection_reason.assign(reason);
  return ack.status;
}

void FillAck(const PlayerPrisonerActionRequestV1 &request,
             const PlayerPrisonerManagementSnapshotV1 &snapshot,
             const PlayerPrisonerRowV1 &row,
             const PlayerPrisonerActionSubmissionV1 &submission,
             PlayerPrisonerActionAckV1 &ack) {
  ack = {};
  ack.status = AckStatus::submitted_verification_pending;
  ack.verification_pending = true;
  ack.request_id.assign(request.request_id);
  ack.action = request.action;
  ack.player_character_id = snapshot.played_character_id;
  ack.prisoner_character_id = row.prisoner_character_id;
  ack.pre_custody = row.custody;
  ack.payer_character_id = submission.payer_character_id;
  ack.selected_option_key = submission.selected_option_key;
  ack.resource_key = submission.resource_key;
  ack.resource_amount_raw = submission.resource_amount_raw;
  ack.native_execute_reason_known =
      OpaqueFinalKnown(row.has_execute_reason);
  ack.native_execute_reason =
      ack.native_execute_reason_known && row.has_execute_reason.value;
  ack.pre_public_revision = snapshot.public_revision;
  ack.pre_native_revision = snapshot.native_revision;
  ack.pre_proof_epoch = snapshot.proof_epoch;
  ack.pre_date_raw = snapshot.date_raw;
}

ReceiptStatus FailReceipt(
    std::string_view reason,
    PlayerPrisonerActionReceiptV1 &receipt) noexcept {
  receipt.status = ReceiptStatus::postcondition_failed;
  receipt.reason.assign(reason);
  receipt.target_state_changed = false;
  receipt.postcondition_verified = false;
  return receipt.status;
}

} // namespace

PlayerPrisonerActionEnvironmentV1 BindPlayerPrisonerActionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  // PRISONER4 is the semantic core. A later exact-build command adapter must
  // explicitly certify the production command ABI.
  return {exact_build_admitted, admitted_executable_sha256, module_base,
          false, false};
}

AckStatus ExecutePlayerPrisonerActionV1(
    const PlayerPrisonerActionEnvironmentV1 &environment,
    const PlayerPrisonerActionAccessV1 &access,
    const PlayerPrisonerActionRequestV1 &request,
    PlayerPrisonerActionAckV1 &ack) noexcept {
  try {
    if (!ValidRequest(request)) {
      return Reject(request, Failure::request_contract, "invalid_request",
                    ack);
    }
    if (!EnvironmentReady(environment)) {
      return Reject(request, Failure::exact_build_binding,
                    "exact_command_adapter_unavailable", ack);
    }
    if (access.capture_snapshot == nullptr ||
        access.is_application_main_thread == nullptr ||
        access.submit_native == nullptr ||
        !access.is_application_main_thread(access.context)) {
      return Reject(request, Failure::snapshot_binding,
                    "application_main_snapshot_unavailable", ack);
    }

    PlayerPrisonerManagementSnapshotV1 first{};
    if (!access.capture_snapshot(access.context, first) ||
        !SnapshotBoundToRequest(first, request)) {
      return Reject(request, Failure::snapshot_binding,
                    "paused_snapshot_mismatch", ack);
    }
    const auto *first_row =
        FindUniquePrisoner(first, request.prisoner_character_id);
    if (first_row == nullptr || !first_row->prisoner_identity_round_trip ||
        !first_row->prisoner_alive ||
        first_row->jailer_character_id != first.played_character_id) {
      return Reject(request, Failure::prisoner_binding,
                    "prisoner_full_identity_not_bound", ack);
    }

    PlayerPrisonerActionSubmissionV1 submission{};
    if (!FillSubmission(request, first, *first_row, submission)) {
      return Reject(request, Failure::final_legality,
                    "native_final_action_not_sendable", ack);
    }

    // Re-read the complete value-owned PRISONER3 snapshot in the same paused
    // turn. Only exact equality can authorize the one native submit call.
    PlayerPrisonerManagementSnapshotV1 second{};
    if (!access.capture_snapshot(access.context, second) ||
        !EquivalentSnapshot(first, second)) {
      return Reject(request, Failure::snapshot_binding,
                    "state_changed_before_submit", ack);
    }
    if (!access.submit_native(access.context, submission)) {
      return Reject(request, Failure::native_command_dispatch,
                    "native_command_submit_failed", ack);
    }

    FillAck(request, first, *first_row, submission, ack);
    return ack.status;
  } catch (...) {
    return Reject(request, Failure::native_command_dispatch,
                  "action_executor_exception", ack);
  }
}

ReceiptStatus VerifyPlayerPrisonerActionReceiptV1(
    const PlayerPrisonerActionAccessV1 &access,
    const PlayerPrisonerActionAckV1 &ack,
    PlayerPrisonerActionReceiptV1 &receipt) noexcept {
  receipt = {};
  receipt.request_id = ack.request_id;
  receipt.action = ack.action;
  receipt.player_character_id = ack.player_character_id;
  receipt.prisoner_character_id = ack.prisoner_character_id;
  if (ack.status == AckStatus::rejected_before_submit) {
    receipt.status = ReceiptStatus::rejected;
    receipt.reason = ack.rejection_reason;
    return receipt.status;
  }
  if (ack.status != AckStatus::submitted_verification_pending ||
      !ack.verification_pending || !ValidAction(ack.action) ||
      ack.player_character_id <= 0 || ack.prisoner_character_id <= 0) {
    return FailReceipt("invalid_pending_ack", receipt);
  }
  if (access.capture_snapshot == nullptr ||
      access.is_application_main_thread == nullptr ||
      !access.is_application_main_thread(access.context)) {
    return FailReceipt("receipt_snapshot_unavailable", receipt);
  }

  PlayerPrisonerManagementSnapshotV1 post{};
  if (!access.capture_snapshot(access.context, post)) {
    return FailReceipt("receipt_snapshot_read_failed", receipt);
  }
  receipt.post_public_revision = post.public_revision;
  receipt.post_native_revision = post.native_revision;
  receipt.post_proof_epoch = post.proof_epoch;
  receipt.post_date_raw = post.date_raw;
  receipt.complete_prisoner_collection_reread =
      post.status == PlayerPrisonerSnapshotStatusV1::available &&
      post.unavailable_reason == PlayerPrisonerSnapshotFailureV1::none &&
      post.total_prisoner_count == post.prisoner_count &&
      post.prisoner_count <= kPlayerPrisonerMaximumRowsV1 &&
      post.readiness.collection_ready && post.readiness.same_frame_ready;
  if (!receipt.complete_prisoner_collection_reread ||
      post.religious_details_exposed ||
      post.played_character_id != ack.player_character_id) {
    return FailReceipt("post_snapshot_or_player_mismatch", receipt);
  }
  if (post.public_revision <= ack.pre_public_revision ||
      post.native_revision <= ack.pre_native_revision ||
      post.proof_epoch <= ack.pre_proof_epoch ||
      post.date_raw < ack.pre_date_raw) {
    return FailReceipt("no_fresh_paused_receipt", receipt);
  }

  const auto *target = FindUniquePrisoner(post, ack.prisoner_character_id);
  receipt.target_still_imprisoned = target != nullptr;
  if (target != nullptr) {
    receipt.post_custody = target->custody;
    return FailReceipt("target_still_in_player_prisoner_collection", receipt);
  }
  receipt.status = ReceiptStatus::applied;
  receipt.target_state_changed = true;
  receipt.postcondition_verified = true;
  receipt.reason.clear();
  return receipt.status;
}

std::string_view PlayerPrisonerActionFailureClassNameV1(
    Failure failure) noexcept {
  switch (failure) {
  case Failure::none:
    return "none";
  case Failure::request_contract:
    return "request_contract";
  case Failure::exact_build_binding:
    return "exact_build_binding";
  case Failure::snapshot_binding:
    return "snapshot_binding";
  case Failure::prisoner_binding:
    return "prisoner_binding";
  case Failure::final_legality:
    return "final_legality";
  case Failure::native_command_dispatch:
    return "native_command_dispatch";
  case Failure::state_observation:
    return "state_observation";
  }
  return "state_observation";
}

} // namespace xar::bridge
