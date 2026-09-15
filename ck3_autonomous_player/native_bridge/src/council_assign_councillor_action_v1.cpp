#include "xar_bridge/council_assign_councillor_action_v1.hpp"

#include <algorithm>

namespace xar::ck3_11906 {
namespace {

using AckStatus = game::CouncilAssignCouncillorAckStatusV1;
using Failure = game::CouncilAssignCouncillorFailureV1;
using Frame = game::CouncilAssignCouncillorFrameV1;
using ReceiptStatus = game::CouncilAssignCouncillorReceiptStatusV1;
using Route = game::CouncilAssignCouncillorRouteV1;

template <std::size_t Size>
std::string_view FixedString(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ValidToken(std::string_view value, std::size_t capacity) noexcept {
  if (value.empty() || value.size() > capacity) return false;
  return std::all_of(value.begin(), value.end(), [](char character) {
    const bool alpha = (character >= 'a' && character <= 'z') ||
        (character >= 'A' && character <= 'Z');
    const bool digit = character >= '0' && character <= '9';
    return alpha || digit || character == '-' || character == '_' ||
        character == '.' || character == ':';
  });
}

bool ValidRequest(
    const game::CouncilAssignCouncillorActionRequestV1 &request) noexcept {
  if (!ValidToken(request.request_id,
                  kCouncilAssignCouncillorRequestIdCapacityV1) ||
      !ValidToken(request.expected_snapshot_id,
                  kCouncilAssignCouncillorSnapshotIdCapacityV1) ||
      request.position_key != kCouncilAssignCouncillorPositionKeyV1 ||
      request.expected_public_revision == 0 ||
      request.expected_native_revision == 0 ||
      request.expected_owner_character_id <= 0 ||
      request.candidate_character_id <= 0) {
    return false;
  }
  if (request.expected_has_incumbent) {
    return request.expected_incumbent_character_id > 0;
  }
  return request.expected_incumbent_character_id == -1;
}

AckStatus Reject(
    const game::CouncilAssignCouncillorActionRequestV1 &request,
    Failure failure, std::string_view native_reason_key,
    game::CouncilAssignCouncillorActionAckV1 &ack) noexcept {
  ack = {};
  ack.status = AckStatus::rejected_before_submit;
  ack.failure = failure;
  ack.request_id = request.request_id;
  ack.position_key = request.position_key;
  ack.candidate_character_id = request.candidate_character_id;
  ack.native_reason_key.assign(native_reason_key);
  return ack.status;
}

Failure BindFrame(
    const Frame &frame,
    const game::CouncilAssignCouncillorActionRequestV1 &request) noexcept {
  if (!frame.available || !frame.map_ready) return Failure::observation_unavailable;
  if (!frame.paused) return Failure::not_paused;
  if (frame.position_key != kCouncilAssignCouncillorPositionKeyV1) {
    return Failure::position_outside_coverage;
  }
  if (frame.snapshot_id != request.expected_snapshot_id ||
      frame.public_revision != request.expected_public_revision ||
      frame.native_revision != request.expected_native_revision ||
      frame.date_raw != request.expected_date_raw ||
      frame.owner_character_id != request.expected_owner_character_id ||
      !frame.owner_identity_round_trip ||
      frame.has_incumbent != request.expected_has_incumbent ||
      frame.incumbent_character_id !=
          request.expected_incumbent_character_id) {
    return Failure::snapshot_binding_mismatch;
  }
  if (frame.active_task_id <= 0 || !frame.active_task_identity_round_trip) {
    return Failure::active_task_identity_unavailable;
  }
  if (frame.has_incumbent &&
      (frame.incumbent_character_id <= 0 ||
       !frame.incumbent_identity_round_trip)) {
    return Failure::incumbent_identity_unavailable;
  }
  if (!frame.has_incumbent &&
      (frame.incumbent_character_id != -1 ||
       frame.incumbent_identity_round_trip)) {
    return Failure::incumbent_identity_unavailable;
  }
  if (frame.has_incumbent &&
      frame.incumbent_character_id == request.candidate_character_id) {
    return Failure::candidate_equals_incumbent;
  }
  return Failure::none;
}

Failure CheckFinalLegality(
    const Frame &frame,
    const game::CouncilAssignCouncillorActionRequestV1 &request,
    const game::CouncilAssignCouncillorFinalLegalityV1 &legality) noexcept {
  if (!legality.available ||
      legality.owner_character_id != frame.owner_character_id ||
      legality.active_task_id != frame.active_task_id ||
      legality.position_key != frame.position_key ||
      legality.candidate_character_id != request.candidate_character_id) {
    return Failure::final_legality_unavailable;
  }
  if (legality.candidate_match_count != 1) {
    return Failure::candidate_not_in_exact_collection;
  }
  if (!legality.candidate_identity_round_trip) {
    return Failure::candidate_identity_mismatch;
  }
  if (legality.candidate_already_councillor) {
    return Failure::candidate_already_councillor;
  }
  if (legality.candidate_is_guest) return Failure::candidate_is_guest;
  if (legality.pending_character_interaction) {
    return Failure::pending_character_interaction;
  }
  if (frame.has_incumbent &&
      (!legality.incumbent_fireability_evaluated ||
       !legality.incumbent_can_be_fired)) {
    return Failure::incumbent_cannot_be_replaced;
  }
  return Failure::none;
}

void CopyPost(const Frame &post,
              game::CouncilAssignCouncillorActionReceiptV1 &receipt) {
  receipt.post_snapshot_id = post.snapshot_id;
  receipt.post_public_revision = post.public_revision;
  receipt.post_native_revision = post.native_revision;
  receipt.post_date_raw = post.date_raw;
  receipt.owner_character_id = post.owner_character_id;
  receipt.position_key = post.position_key;
  receipt.incumbent_character_id = post.incumbent_character_id;
  receipt.incumbent_identity_round_trip = post.incumbent_identity_round_trip;
}

} // namespace

bool PrepareCouncilAssignCouncillorActionRequestV1(
    const game::CouncilCompositionCandidatesPublicV1 &candidates,
    std::int32_t candidate_character_id, std::string_view request_id,
    game::CouncilAssignCouncillorActionRequestV1 &request) noexcept {
  request = {};
  if (candidates.status !=
          game::CouncilCompositionCandidatesPublicStatusV1::available ||
      !candidates.readiness.identity_ready ||
      !candidates.readiness.candidate_collection_ready ||
      !candidates.readiness.incumbent_ready ||
      !candidates.readiness.candidate_legality_ready ||
      !candidates.readiness.main_skill_ready ||
      !candidates.readiness.action_route_ready ||
      !candidates.readiness.same_frame_ready ||
      !candidates.readiness.ready || !candidates.paused ||
      candidates.owner_character_id <= 0 || candidate_character_id <= 0 ||
      candidates.public_revision == 0 || candidates.native_revision == 0 ||
      candidates.candidate_count > candidates.candidates.size() ||
      FixedString(candidates.position_key) !=
          kCouncilAssignCouncillorPositionKeyV1 ||
      !ValidToken(request_id, kCouncilAssignCouncillorRequestIdCapacityV1)) {
    return false;
  }
  const auto snapshot_id = FixedString(candidates.snapshot_id);
  if (!ValidToken(snapshot_id, kCouncilAssignCouncillorSnapshotIdCapacityV1)) {
    return false;
  }
  if ((candidates.vacant && candidates.incumbent_character_id != -1) ||
      (!candidates.vacant && candidates.incumbent_character_id <= 0)) {
    return false;
  }
  const auto expected_route = candidates.vacant
      ? game::CouncilCompositionCandidateActionRouteV1::assign
      : game::CouncilCompositionCandidateActionRouteV1::replace;
  if (candidates.action_route != expected_route) return false;
  const game::CouncilCompositionCandidatePublicRowV1 *matched = nullptr;
  for (std::uint32_t index = 0; index < candidates.candidate_count; ++index) {
    const auto &row = candidates.candidates[index];
    if (row.character_id != candidate_character_id) continue;
    if (matched != nullptr) return false;
    matched = &row;
  }
  if (matched == nullptr || !matched->eligible ||
      matched->action_route != expected_route) {
    return false;
  }
  request.request_id.assign(request_id);
  request.position_key.assign(kCouncilAssignCouncillorPositionKeyV1);
  request.expected_snapshot_id.assign(snapshot_id);
  request.expected_public_revision = candidates.public_revision;
  request.expected_native_revision = candidates.native_revision;
  request.expected_date_raw = candidates.date_raw;
  request.expected_owner_character_id = candidates.owner_character_id;
  request.candidate_character_id = candidate_character_id;
  request.expected_has_incumbent = !candidates.vacant;
  request.expected_incumbent_character_id =
      candidates.incumbent_character_id;
  return true;
}

AckStatus ExecuteCouncilAssignCouncillorActionV1(
    const CouncilAssignCouncillorNativeEnvironmentV1 &environment,
    const CouncilAssignCouncillorActionAccessV1 &access,
    const game::CouncilAssignCouncillorActionRequestV1 &request,
    game::CouncilAssignCouncillorActionAckV1 &ack) noexcept {
  try {
    if (!ValidRequest(request)) {
      return Reject(request, Failure::request_contract_invalid, {}, ack);
    }
    if (!environment.exact_build_admitted ||
        environment.admitted_executable_sha256 !=
            kCouncilAssignCouncillorExecutableSha256V1) {
      return Reject(request, Failure::exact_build_mismatch, {}, ack);
    }
    if (!environment.private_candidate_admitted) {
      return Reject(request, Failure::private_candidate_not_admitted, {}, ack);
    }
    if (environment.current_thread_id == 0 ||
        environment.current_thread_id !=
            environment.application_main_thread_id) {
      return Reject(request, Failure::application_main_thread_required, {},
                    ack);
    }
    const bool production_certified = environment.module_base != 0 &&
        environment.native_command_abi_certified &&
        !environment.offline_fixture;
    const bool offline_certified = environment.module_base == 0 &&
        environment.native_command_abi_certified &&
        environment.offline_fixture;
    if ((!production_certified && !offline_certified) ||
        access.capture_frame == nullptr ||
        access.recheck_final_legality == nullptr ||
        access.invoke_native_helper == nullptr) {
      return Reject(request, Failure::callbacks_unavailable, {}, ack);
    }

    Frame first{};
    if (!access.capture_frame(access.context, first)) {
      return Reject(request, Failure::observation_unavailable, {}, ack);
    }
    auto failure = BindFrame(first, request);
    if (failure != Failure::none) return Reject(request, failure, {}, ack);

    game::CouncilAssignCouncillorFinalLegalityV1 legality{};
    if (!access.recheck_final_legality(
            access.context, first, request.candidate_character_id, legality)) {
      return Reject(request, Failure::final_legality_unavailable, {}, ack);
    }
    failure = CheckFinalLegality(first, request, legality);
    if (failure != Failure::none) {
      return Reject(request, failure, legality.native_reason_key, ack);
    }

    Frame second{};
    if (!access.capture_frame(access.context, second) || second != first) {
      return Reject(request, Failure::state_changed_before_submit, {}, ack);
    }

    game::CouncilAssignCouncillorNativeSubmissionV1 submission{};
    submission.route = first.has_incumbent ? Route::replace_incumbent
                                           : Route::assign_vacant;
    submission.owner_character_id = first.owner_character_id;
    submission.active_task_id = first.active_task_id;
    submission.candidate_character_id = request.candidate_character_id;
    submission.had_incumbent = first.has_incumbent;
    submission.previous_incumbent_character_id =
        first.incumbent_character_id;
    if (!access.invoke_native_helper(access.context, submission)) {
      return Reject(request, Failure::native_helper_not_invoked, {}, ack);
    }

    ack = {};
    ack.status = AckStatus::native_helper_invoked_verification_pending;
    ack.failure = Failure::none;
    ack.request_id = request.request_id;
    ack.pre_snapshot_id = first.snapshot_id;
    ack.pre_public_revision = first.public_revision;
    ack.pre_native_revision = first.native_revision;
    ack.pre_date_raw = first.date_raw;
    ack.owner_character_id = first.owner_character_id;
    ack.position_key = first.position_key;
    ack.active_task_id = first.active_task_id;
    ack.candidate_character_id = request.candidate_character_id;
    ack.had_incumbent = first.has_incumbent;
    ack.previous_incumbent_character_id = first.incumbent_character_id;
    ack.route = submission.route;
    ack.native_helper_invoked = true;
    // 0x1056C00 returns void and discards the generic command manager's AL.
    ack.queue_acceptance_observed = false;
    ack.verification_pending = true;
    return ack.status;
  } catch (...) {
    return Reject(request, Failure::native_helper_not_invoked,
                  "action_executor_exception", ack);
  }
}

ReceiptStatus VerifyCouncilAssignCouncillorActionReceiptV1(
    const game::CouncilAssignCouncillorActionAckV1 &ack, const Frame &post,
    game::CouncilAssignCouncillorActionReceiptV1 &receipt) noexcept {
  receipt = {};
  receipt.request_id = ack.request_id;
  if (ack.status == AckStatus::rejected_before_submit) {
    receipt.status = ReceiptStatus::rejected;
    receipt.rejected_action_failure = ack.failure;
    receipt.reason = "action_rejected";
    return receipt.status;
  }
  CopyPost(post, receipt);
  const auto fail = [&](std::string_view reason) noexcept {
    receipt.status = ReceiptStatus::postcondition_failed;
    receipt.reason.assign(reason);
    return receipt.status;
  };
  if (ack.status != AckStatus::native_helper_invoked_verification_pending ||
      !ack.native_helper_invoked || ack.queue_acceptance_observed ||
      !ack.verification_pending) {
    return fail("invalid_ack");
  }
  if (!post.available || !post.paused || !post.map_ready) {
    return fail("post_observation_unavailable");
  }
  if (post.snapshot_id.empty() || post.snapshot_id == ack.pre_snapshot_id ||
      post.public_revision <= ack.pre_public_revision ||
      post.native_revision <= ack.pre_native_revision ||
      post.date_raw < ack.pre_date_raw) {
    return fail("no_new_paused_frame");
  }
  if (post.owner_character_id != ack.owner_character_id ||
      !post.owner_identity_round_trip ||
      post.position_key != ack.position_key) {
    return fail("owner_or_position_changed");
  }
  if (post.active_task_id != ack.active_task_id ||
      !post.active_task_identity_round_trip) {
    return fail("active_task_changed");
  }
  if (!post.has_incumbent ||
      post.incumbent_character_id != ack.candidate_character_id ||
      !post.incumbent_identity_round_trip) {
    return fail("candidate_not_observed_as_incumbent");
  }
  receipt.status = ReceiptStatus::applied;
  receipt.reason.clear();
  receipt.postcondition_verified = true;
  return receipt.status;
}

std::string_view CouncilAssignCouncillorFailureKeyV1(Failure failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::request_contract_invalid: return "request_contract_invalid";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::private_candidate_not_admitted:
    return "private_candidate_not_admitted";
  case Failure::application_main_thread_required:
    return "application_main_thread_required";
  case Failure::callbacks_unavailable: return "callbacks_unavailable";
  case Failure::observation_unavailable: return "observation_unavailable";
  case Failure::not_paused: return "not_paused";
  case Failure::snapshot_binding_mismatch:
    return "snapshot_binding_mismatch";
  case Failure::position_outside_coverage:
    return "position_outside_coverage";
  case Failure::active_task_identity_unavailable:
    return "active_task_identity_unavailable";
  case Failure::incumbent_identity_unavailable:
    return "incumbent_identity_unavailable";
  case Failure::candidate_equals_incumbent:
    return "candidate_equals_incumbent";
  case Failure::final_legality_unavailable:
    return "final_legality_unavailable";
  case Failure::candidate_not_in_exact_collection:
    return "candidate_not_in_exact_collection";
  case Failure::candidate_identity_mismatch:
    return "candidate_identity_mismatch";
  case Failure::candidate_already_councillor:
    return "candidate_already_councillor";
  case Failure::candidate_is_guest: return "candidate_is_guest";
  case Failure::pending_character_interaction:
    return "pending_character_interaction";
  case Failure::incumbent_cannot_be_replaced:
    return "incumbent_cannot_be_replaced";
  case Failure::state_changed_before_submit:
    return "state_changed_before_submit";
  case Failure::native_helper_not_invoked:
    return "native_helper_not_invoked";
  }
  return "native_helper_not_invoked";
}

std::string_view CouncilAssignCouncillorRouteKeyV1(Route route) noexcept {
  switch (route) {
  case Route::none: return "none";
  case Route::assign_vacant: return "assign_vacant";
  case Route::replace_incumbent: return "replace_incumbent";
  }
  return "none";
}

} // namespace xar::ck3_11906
