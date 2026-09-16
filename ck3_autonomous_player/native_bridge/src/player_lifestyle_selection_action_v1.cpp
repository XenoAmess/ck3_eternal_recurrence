#include "xar_bridge/player_lifestyle_selection_action_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

using AckStatus = game::PlayerLifestyleSelectionActionAckStatusV1;
using FailureClass = game::PlayerLifestyleSelectionActionFailureClassV1;
using Kind = game::PlayerLifestyleSelectionKindV1;
using ReceiptStatus = game::PlayerLifestyleSelectionActionReceiptStatusV1;
using StableKey = game::PlayerLifestyleWindowStableKeyV1;

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ValidRequestToken(std::string_view value, std::size_t maximum) noexcept {
  if (value.empty() || value.size() > maximum) return false;
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

bool ValidStableKey(const StableKey &value) noexcept {
  const auto view = PlayerLifestyleWindowStableKeyViewV1(value);
  if (view.empty()) return false;
  for (const char character : view) {
    if (!((character >= 'a' && character <= 'z') ||
          (character >= '0' && character <= '9') || character == '_')) {
      return false;
    }
  }
  return true;
}

bool ValidRequest(
    const game::PlayerLifestyleSelectionActionRequestV1 &request) noexcept {
  return ValidRequestToken(request.request_id, 64) &&
      (request.kind == Kind::focus || request.kind == Kind::perk) &&
      request.target_key.size() <
          game::kPlayerLifestyleWindowStableKeyCapacityV1 &&
      ValidRequestToken(request.target_key,
                        game::kPlayerLifestyleWindowStableKeyCapacityV1 - 1) &&
      ValidRequestToken(
          request.expected_snapshot_id,
          game::kPlayerLifestyleWindowSnapshotIdCapacityV1 - 1) &&
      ValidRequestToken(
          request.expected_episode_run_id,
          game::kPlayerLifestyleSelectionEpisodeRunIdCapacityV1 - 1) &&
      request.expected_public_revision != 0 &&
      request.expected_native_revision != 0 &&
      request.expected_proof_epoch != 0 &&
      request.expected_player_character_id != 0xFFFFFFFFU;
}

AckStatus Reject(
    const game::PlayerLifestyleSelectionActionRequestV1 &request,
    FailureClass failure_class, std::string_view reason,
    game::PlayerLifestyleSelectionActionAckV1 &ack) {
  ack = {};
  ack.request_id.assign(request.request_id);
  ack.kind = request.kind;
  (void)AssignPlayerLifestyleWindowStableKeyV1(request.target_key,
                                               ack.target_key);
  ack.failure_class = failure_class;
  ack.rejection_reason.assign(reason);
  return AckStatus::rejected_before_submit;
}

bool CandidateSnapshotBoundToRequest(
    const game::PlayerLifestyleWindowCandidatesV1 &candidates,
    const game::PlayerLifestyleSelectionStateObservationV1 &state,
    const game::PlayerLifestyleSelectionActionRequestV1 &request) noexcept {
  const bool requested_collection_ready =
      request.kind == Kind::perk
      ? candidates.readiness.perk_candidates_ready &&
          candidates.perk_status !=
              game::PlayerLifestyleWindowCollectionStatusV1::unavailable
      : candidates.readiness.focus_candidates_ready &&
          candidates.focus_status !=
              game::PlayerLifestyleWindowCollectionStatusV1::unavailable;
  return candidates.status ==
          game::PlayerLifestyleWindowCandidatesStatusV1::available &&
      candidates.unavailable_reason ==
          game::PlayerLifestyleWindowCandidatesFailureV1::none &&
      FixedString(candidates.snapshot_id) == request.expected_snapshot_id &&
      candidates.public_revision == request.expected_public_revision &&
      candidates.native_revision == request.expected_native_revision &&
      candidates.proof_epoch == request.expected_proof_epoch &&
      candidates.date_raw == request.expected_date_raw &&
      candidates.player_character_id ==
          request.expected_player_character_id &&
      candidates.readiness.bound_player_ready &&
      candidates.readiness.containers_ready &&
      requested_collection_ready &&
      candidates.readiness.final_legality_ready &&
      candidates.readiness.same_frame_ready && state.available &&
      state.paused &&
      FixedString(state.snapshot_id) == FixedString(candidates.snapshot_id) &&
      FixedString(state.episode_run_id) ==
          request.expected_episode_run_id &&
      state.public_revision == candidates.public_revision &&
      state.native_revision == candidates.native_revision &&
      state.proof_epoch == candidates.proof_epoch &&
      state.date_raw == candidates.date_raw &&
      state.player_character_id == candidates.player_character_id;
}

const game::PlayerLifestyleWindowFocusCandidateV1 *FindFocusCandidate(
    const game::PlayerLifestyleWindowCandidatesV1 &candidates,
    std::string_view target) noexcept {
  if (candidates.focus_status !=
          game::PlayerLifestyleWindowCollectionStatusV1::available ||
      candidates.focus_count == 0 ||
      candidates.focus_count > game::kPlayerLifestyleWindowMaximumFocusesV1) {
    return nullptr;
  }
  const game::PlayerLifestyleWindowFocusCandidateV1 *match = nullptr;
  for (std::uint32_t index = 0; index < candidates.focus_count; ++index) {
    const auto &candidate = candidates.focuses[index];
    if (!ValidStableKey(candidate.key) ||
        !ValidStableKey(candidate.lifestyle_key)) {
      return nullptr;
    }
    if (PlayerLifestyleWindowStableKeyViewV1(candidate.key) == target) {
      if (match != nullptr) return nullptr;
      match = &candidate;
    }
  }
  return match;
}

const game::PlayerLifestyleWindowPerkCandidateV1 *FindPerkCandidate(
    const game::PlayerLifestyleWindowCandidatesV1 &candidates,
    std::string_view target) noexcept {
  if (candidates.perk_status !=
          game::PlayerLifestyleWindowCollectionStatusV1::available ||
      candidates.perk_count == 0 ||
      candidates.perk_count > game::kPlayerLifestyleWindowMaximumPerksV1) {
    return nullptr;
  }
  const game::PlayerLifestyleWindowPerkCandidateV1 *match = nullptr;
  for (std::uint32_t index = 0; index < candidates.perk_count; ++index) {
    const auto &candidate = candidates.perks[index];
    if (!ValidStableKey(candidate.key) ||
        !ValidStableKey(candidate.lifestyle_key)) {
      return nullptr;
    }
    if (PlayerLifestyleWindowStableKeyViewV1(candidate.key) == target) {
      if (match != nullptr) return nullptr;
      match = &candidate;
    }
  }
  return match;
}

bool ContainsOwnedPerk(
    const game::PlayerLifestyleSelectionStateObservationV1 &state,
    const StableKey &target) noexcept {
  for (std::uint32_t index = 0; index < state.owned_perk_count; ++index) {
    if (state.owned_perk_keys[index] == target) return true;
  }
  return false;
}

bool CompleteStateObservation(
    const game::PlayerLifestyleSelectionStateObservationV1 &state,
    const StableKey &target_lifestyle,
    const game::PlayerLifestyleSelectionProgressRowV1 *&target_progress)
    noexcept {
  target_progress = nullptr;
  if (!state.available || !state.paused || !state.current_focus_known ||
      !state.owned_perks_fully_materialized ||
      state.owned_perk_count >
          game::kPlayerLifestyleWindowMaximumPerksV1 ||
      !state.lifestyle_progress_fully_materialized ||
      state.lifestyle_progress_count == 0 ||
      state.lifestyle_progress_count >
          game::kPlayerLifestyleSelectionMaximumProgressRowsV1) {
    return false;
  }
  if (state.has_current_focus) {
    if (!ValidStableKey(state.current_focus_key)) return false;
  } else if (state.current_focus_key.size != 0) {
    return false;
  }
  for (std::uint32_t index = 0; index < state.owned_perk_count; ++index) {
    if (!ValidStableKey(state.owned_perk_keys[index])) return false;
    for (std::uint32_t previous = 0; previous < index; ++previous) {
      if (state.owned_perk_keys[previous] == state.owned_perk_keys[index]) {
        return false;
      }
    }
  }
  for (std::uint32_t index = 0; index < state.lifestyle_progress_count;
       ++index) {
    const auto &row = state.lifestyle_progress[index];
    if (!ValidStableKey(row.lifestyle_key) || row.experience_raw < 0 ||
        row.perk_points < 0) {
      return false;
    }
    for (std::uint32_t previous = 0; previous < index; ++previous) {
      if (state.lifestyle_progress[previous].lifestyle_key ==
          row.lifestyle_key) {
        return false;
      }
    }
    if (row.lifestyle_key == target_lifestyle) target_progress = &row;
  }
  return target_progress != nullptr;
}

bool EquivalentCandidates(
    const game::PlayerLifestyleWindowCandidatesV1 &left,
    const game::PlayerLifestyleWindowCandidatesV1 &right) noexcept {
  return left.status == right.status &&
      left.unavailable_reason == right.unavailable_reason &&
      left.snapshot_id == right.snapshot_id &&
      left.public_revision == right.public_revision &&
      left.native_revision == right.native_revision &&
      left.proof_epoch == right.proof_epoch && left.date_raw == right.date_raw &&
      left.player_character_id == right.player_character_id &&
      left.focus_status == right.focus_status &&
      left.focus_count == right.focus_count && left.focuses == right.focuses &&
      left.perk_status == right.perk_status &&
      left.perk_count == right.perk_count && left.perks == right.perks &&
      left.readiness == right.readiness;
}

bool EquivalentPrecondition(
    const game::PlayerLifestyleSelectionPreconditionV1 &left,
    const game::PlayerLifestyleSelectionPreconditionV1 &right) noexcept {
  return EquivalentCandidates(left.candidates, right.candidates) &&
      left.state == right.state;
}

bool EnvironmentReady(
    const PlayerLifestyleSelectionActionEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted || environment.module_base == 0 ||
      environment.admitted_executable_sha256 !=
          kPlayerLifestyleSelectionActionExecutableSha256V1) {
    return false;
  }
  return environment.offline_fixture_command ||
      environment.command_abi_certified;
}

void CopyPreconditionToAck(
    const game::PlayerLifestyleSelectionActionRequestV1 &request,
    const game::PlayerLifestyleSelectionPreconditionV1 &precondition,
    const StableKey &target, const StableKey &target_lifestyle,
    const game::PlayerLifestyleSelectionProgressRowV1 &progress,
    game::PlayerLifestyleSelectionActionAckV1 &ack) {
  ack = {};
  ack.status = AckStatus::submitted_verification_pending;
  ack.verification_pending = true;
  ack.request_id.assign(request.request_id);
  ack.kind = request.kind;
  ack.target_key = target;
  ack.target_lifestyle_key = target_lifestyle;
  ack.snapshot_id = precondition.state.snapshot_id;
  ack.episode_run_id = precondition.state.episode_run_id;
  ack.pre_public_revision = precondition.state.public_revision;
  ack.pre_native_revision = precondition.state.native_revision;
  ack.pre_proof_epoch = precondition.state.proof_epoch;
  ack.pre_date_raw = precondition.state.date_raw;
  ack.player_character_id = precondition.state.player_character_id;
  ack.pre_has_current_focus = precondition.state.has_current_focus;
  ack.pre_current_focus_key = precondition.state.current_focus_key;
  ack.pre_owned_perk_count = precondition.state.owned_perk_count;
  ack.pre_target_perk_owned =
      ContainsOwnedPerk(precondition.state, target);
  ack.pre_target_lifestyle_experience_raw = progress.experience_raw;
  ack.pre_target_lifestyle_perk_points = progress.perk_points;
  ack.failure_class = FailureClass::none;
}

ReceiptStatus FailReceipt(
    std::string_view reason,
    game::PlayerLifestyleSelectionActionReceiptV1 &receipt) {
  receipt.status = ReceiptStatus::postcondition_failed;
  receipt.reason.assign(reason);
  receipt.target_state_changed = false;
  receipt.postcondition_verified = false;
  return receipt.status;
}

} // namespace

PlayerLifestyleSelectionActionEnvironmentV1
BindPlayerLifestyleSelectionActionEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256) noexcept {
  // LIFE6 is the semantic core only. Production command dispatch stays
  // unavailable until a later exact-build command adapter certifies its ABI.
  return {exact_build_admitted, admitted_executable_sha256, module_base,
          false, false};
}

AckStatus ExecutePlayerLifestyleSelectionActionV1(
    const PlayerLifestyleSelectionActionEnvironmentV1 &environment,
    const PlayerLifestyleSelectionActionAccessV1 &access,
    const game::PlayerLifestyleSelectionActionRequestV1 &request,
    game::PlayerLifestyleSelectionActionAckV1 &ack) noexcept {
  try {
    if (!ValidRequest(request)) {
      return Reject(request, FailureClass::request_contract,
                    "invalid_request", ack);
    }
    if (!EnvironmentReady(environment)) {
      return Reject(request, FailureClass::exact_build_binding,
                    "exact_command_adapter_unavailable", ack);
    }
    if (access.capture_precondition == nullptr ||
        access.is_main_thread == nullptr || access.submit_native == nullptr ||
        !access.is_main_thread(access.context)) {
      return Reject(request, FailureClass::snapshot_binding,
                    "application_main_precondition_unavailable", ack);
    }

    auto first =
        std::make_unique<game::PlayerLifestyleSelectionPreconditionV1>();
    if (!access.capture_precondition(access.context, *first) ||
        !CandidateSnapshotBoundToRequest(first->candidates, first->state,
                                         request)) {
      return Reject(request, FailureClass::snapshot_binding,
                    "paused_snapshot_mismatch", ack);
    }

    StableKey target{};
    if (!AssignPlayerLifestyleWindowStableKeyV1(request.target_key, target)) {
      return Reject(request, FailureClass::request_contract,
                    "invalid_target_key", ack);
    }
    StableKey target_lifestyle{};
    bool final_can_select = false;
    if (request.kind == Kind::focus) {
      const auto *candidate =
          FindFocusCandidate(first->candidates, request.target_key);
      if (candidate != nullptr) {
        target_lifestyle = candidate->lifestyle_key;
        final_can_select = candidate->can_select;
      }
    } else {
      const auto *candidate =
          FindPerkCandidate(first->candidates, request.target_key);
      if (candidate != nullptr) {
        target_lifestyle = candidate->lifestyle_key;
        // can_select_ignore_cost is explanatory and never authorizes submit.
        final_can_select = candidate->can_select;
      }
    }
    if (!final_can_select || !ValidStableKey(target_lifestyle)) {
      return Reject(request, FailureClass::final_legality,
                    "target_not_finally_selectable", ack);
    }

    const game::PlayerLifestyleSelectionProgressRowV1 *progress = nullptr;
    if (!CompleteStateObservation(first->state, target_lifestyle, progress)) {
      return Reject(request, FailureClass::state_observation,
                    "complete_pre_state_unavailable", ack);
    }
    const bool target_owned = ContainsOwnedPerk(first->state, target);
    if ((request.kind == Kind::focus && first->state.has_current_focus &&
         first->state.current_focus_key == target) ||
        (request.kind == Kind::perk && target_owned)) {
      return Reject(request, FailureClass::final_legality,
                    "target_already_applied", ack);
    }

    // Re-capture all semantic inputs immediately before dispatch. Only a
    // byte-equivalent paused observation may authorize the one submit call.
    auto second =
        std::make_unique<game::PlayerLifestyleSelectionPreconditionV1>();
    if (!access.capture_precondition(access.context, *second) ||
        !EquivalentPrecondition(*first, *second)) {
      return Reject(request, FailureClass::snapshot_binding,
                    "state_changed_before_submit", ack);
    }
    if (!access.submit_native(access.context, request.kind, target)) {
      return Reject(request, FailureClass::native_command_dispatch,
                    "native_command_submit_failed", ack);
    }

    CopyPreconditionToAck(request, *first, target, target_lifestyle, *progress,
                          ack);
    return ack.status;
  } catch (...) {
    return Reject(request, FailureClass::native_command_dispatch,
                  "action_executor_exception", ack);
  }
}

ReceiptStatus VerifyPlayerLifestyleSelectionActionReceiptV1(
    const PlayerLifestyleSelectionActionAccessV1 &access,
    const game::PlayerLifestyleSelectionActionAckV1 &ack,
    game::PlayerLifestyleSelectionActionReceiptV1 &receipt) noexcept {
  try {
    receipt = {};
    receipt.request_id = ack.request_id;
    receipt.kind = ack.kind;
    receipt.target_key = ack.target_key;
    if (ack.status == AckStatus::rejected_before_submit) {
      receipt.status = ReceiptStatus::rejected;
      receipt.reason = ack.rejection_reason;
      return receipt.status;
    }
    if (ack.status != AckStatus::submitted_verification_pending ||
        !ack.verification_pending ||
        (ack.kind != Kind::focus && ack.kind != Kind::perk) ||
        !ValidStableKey(ack.target_key) ||
        !ValidStableKey(ack.target_lifestyle_key) ||
        FixedString(ack.episode_run_id).empty()) {
      return FailReceipt("invalid_pending_ack", receipt);
    }
    if (access.capture_receipt_state == nullptr ||
        access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      return FailReceipt("receipt_state_reader_unavailable", receipt);
    }

    // The receipt owns this fresh read. A pending ACK is never upgraded from
    // data carried by the submit path.
    auto post =
        std::make_unique<game::PlayerLifestyleSelectionStateObservationV1>();
    if (!access.capture_receipt_state(access.context, *post)) {
      return FailReceipt("receipt_state_read_failed", receipt);
    }
    receipt.post_public_revision = post->public_revision;
    receipt.post_snapshot_id = post->snapshot_id;
    receipt.episode_run_id = post->episode_run_id;
    receipt.post_native_revision = post->native_revision;
    receipt.post_proof_epoch = post->proof_epoch;
    receipt.post_date_raw = post->date_raw;
    receipt.player_character_id = post->player_character_id;

    if (!post->available || !post->paused ||
        FixedString(post->episode_run_id) !=
            FixedString(ack.episode_run_id) ||
        post->player_character_id != ack.player_character_id) {
      return FailReceipt("post_episode_or_player_mismatch", receipt);
    }
    if (FixedString(post->snapshot_id).empty() ||
        FixedString(post->snapshot_id) == FixedString(ack.snapshot_id)) {
      return FailReceipt("no_new_native_snapshot_frame", receipt);
    }
    if (post->public_revision <= ack.pre_public_revision ||
        post->native_revision < ack.pre_native_revision ||
        post->proof_epoch < ack.pre_proof_epoch ||
        post->date_raw < ack.pre_date_raw) {
      return FailReceipt("no_new_paused_observation", receipt);
    }

    const game::PlayerLifestyleSelectionProgressRowV1 *progress = nullptr;
    if (!CompleteStateObservation(*post, ack.target_lifestyle_key, progress)) {
      return FailReceipt("complete_post_state_unavailable", receipt);
    }
    receipt.post_has_current_focus = post->has_current_focus;
    receipt.post_current_focus_key = post->current_focus_key;
    receipt.post_owned_perk_count = post->owned_perk_count;
    receipt.post_target_perk_owned = ContainsOwnedPerk(*post, ack.target_key);
    receipt.post_target_lifestyle_experience_raw = progress->experience_raw;
    receipt.post_target_lifestyle_perk_points = progress->perk_points;
    receipt.current_focus_reread = true;
    receipt.owned_perks_reread = true;
    receipt.experience_reread = true;
    receipt.perk_points_reread = true;

    if (ack.kind == Kind::focus) {
      if ((ack.pre_has_current_focus &&
           ack.pre_current_focus_key == ack.target_key) ||
          !post->has_current_focus ||
          post->current_focus_key != ack.target_key) {
        return FailReceipt("target_focus_change_not_observed", receipt);
      }
    } else if (ack.pre_target_perk_owned ||
               !receipt.post_target_perk_owned) {
      return FailReceipt("target_perk_change_not_observed", receipt);
    }

    receipt.status = ReceiptStatus::applied;
    receipt.reason.clear();
    receipt.target_state_changed = true;
    receipt.postcondition_verified = true;
    return receipt.status;
  } catch (...) {
    receipt = {};
    receipt.request_id = ack.request_id;
    receipt.kind = ack.kind;
    receipt.target_key = ack.target_key;
    return FailReceipt("receipt_verifier_exception", receipt);
  }
}

std::string_view PlayerLifestyleSelectionActionFailureClassKeyV1(
    FailureClass value) noexcept {
  switch (value) {
  case FailureClass::none: return "none";
  case FailureClass::request_contract: return "request_contract";
  case FailureClass::exact_build_binding: return "exact_build_binding";
  case FailureClass::snapshot_binding: return "snapshot_binding";
  case FailureClass::final_legality: return "final_legality";
  case FailureClass::state_observation: return "state_observation";
  case FailureClass::native_command_dispatch:
    return "native_command_dispatch";
  }
  return "native_command_dispatch";
}

} // namespace xar::ck3_11906
