#include "xar_bridge/realm_law_enact_action_v1.hpp"

#include <algorithm>
#include <memory>

namespace xar::bridge {
namespace {

using AckStatus = RealmLawEnactActionAckStatusV1;
using ActionFailure = RealmLawEnactActionFailureV1;
using Observation = RealmLawEnactActionObservationV1;
using Presence = RealmLawGovernancePresenceV1;
using ReceiptFailure = RealmLawEnactActionReceiptFailureV1;
using ReceiptStatus = RealmLawEnactActionReceiptStatusV1;

struct StableCandidateV1 {
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
  std::int32_t player_character_id = -1;
  RealmLawGovernanceKeyV1 group_key{};
  RealmLawGovernanceKeyV1 active_law_key{};
  bool authority_evaluated = false;
  bool authority_allows_change = false;
  RealmLawGovernanceCandidateV1 candidate{};
  RealmLawGovernanceTitleBaselineV1 title_successors{};
  std::uint32_t resource_count = 0;
  std::array<RealmLawEnactResourceBalanceV1,
             kRealmLawEnactMaximumResourcesV1>
      resources{};

  friend bool operator==(const StableCandidateV1 &,
                         const StableCandidateV1 &) = default;
};

bool ValidKey(const RealmLawGovernanceKeyV1 &key) noexcept {
  const auto view = RealmLawGovernanceKeyViewV1(key);
  return !view.empty() && view.size() == key.size;
}

bool ValidRequestId(std::string_view value) noexcept {
  if (value.empty() || value.size() > kRealmLawEnactRequestIdCapacityV1) {
    return false;
  }
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

bool CompleteReadiness(const RealmLawGovernanceReadinessV1 &value) noexcept {
  return value.groups_ready && value.engine_final_legality_ready &&
      value.engine_final_costs_ready && value.succession_shapes_ready &&
      value.title_successor_baseline_ready && value.same_frame_ready;
}

bool ValidRequest(const RealmLawEnactActionRequestV1 &request) noexcept {
  if (!ValidRequestId(request.request_id) || !ValidKey(request.group_key) ||
      !ValidKey(request.law_key) || request.expected_public_revision == 0 ||
      request.expected_native_revision == 0 ||
      request.expected_player_character_id <= 0 ||
      request.budget_count > request.budgets.size()) {
    return false;
  }
  for (std::uint32_t index = 0; index < request.budget_count; ++index) {
    const auto &budget = request.budgets[index];
    if (!ValidKey(budget.currency_key) || budget.maximum_spend_raw < 0) {
      return false;
    }
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (request.budgets[prior].currency_key == budget.currency_key) {
        return false;
      }
    }
  }
  return true;
}

const RealmLawGovernanceGroupV1 *FindGroup(
    const RealmLawGovernanceSnapshotV1 &snapshot,
    const RealmLawGovernanceKeyV1 &group_key) noexcept {
  for (std::uint32_t index = 0; index < snapshot.group_count; ++index) {
    if (snapshot.groups[index].group_key == group_key) {
      return &snapshot.groups[index];
    }
  }
  return nullptr;
}

const RealmLawGovernanceCandidateV1 *FindCandidate(
    const RealmLawGovernanceGroupV1 &group,
    const RealmLawGovernanceKeyV1 &law_key) noexcept {
  for (std::uint32_t index = 0; index < group.candidate_count; ++index) {
    if (group.candidates[index].law_key == law_key) {
      return &group.candidates[index];
    }
  }
  return nullptr;
}

bool NormalizeResources(
    const Observation &observation,
    std::uint32_t &count,
    std::array<RealmLawEnactResourceBalanceV1,
               kRealmLawEnactMaximumResourcesV1> &resources) noexcept {
  count = 0;
  resources = {};
  if (!observation.resources_complete ||
      observation.resource_count > observation.resources.size()) {
    return false;
  }
  count = observation.resource_count;
  for (std::uint32_t index = 0; index < count; ++index) {
    const auto &resource = observation.resources[index];
    if (!ValidKey(resource.currency_key) || resource.amount_raw < 0) {
      return false;
    }
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (observation.resources[prior].currency_key ==
          resource.currency_key) {
        return false;
      }
    }
    resources[index] = resource;
  }
  std::sort(resources.begin(), resources.begin() + count,
            [](const auto &left, const auto &right) {
              return RealmLawGovernanceKeyViewV1(left.currency_key) <
                  RealmLawGovernanceKeyViewV1(right.currency_key);
            });
  return true;
}

ActionFailure ExtractStableCandidate(
    const Observation &observation,
    const RealmLawEnactActionRequestV1 &request,
    StableCandidateV1 &output) noexcept {
  output = {};
  if (!observation.available) return ActionFailure::observation_unavailable;
  if (!observation.paused) return ActionFailure::not_paused;
  const auto &snapshot = observation.law_snapshot;
  if (snapshot.status != RealmLawGovernanceSnapshotV1Status::available ||
      snapshot.unavailable_reason != RealmLawGovernanceSnapshotV1Failure::none ||
      !CompleteReadiness(snapshot.readiness)) {
    return ActionFailure::snapshot_unavailable;
  }
  if (snapshot.public_revision != request.expected_public_revision ||
      snapshot.native_revision != request.expected_native_revision ||
      snapshot.proof_epoch != request.expected_proof_epoch ||
      snapshot.date_raw != request.expected_date_raw ||
      snapshot.played_character_id != request.expected_player_character_id) {
    return ActionFailure::stale_snapshot;
  }
  const auto *group = FindGroup(snapshot, request.group_key);
  if (group == nullptr) return ActionFailure::candidate_not_found;
  const auto *candidate = FindCandidate(*group, request.law_key);
  if (candidate == nullptr) return ActionFailure::candidate_not_found;

  output.public_revision = snapshot.public_revision;
  output.native_revision = snapshot.native_revision;
  output.proof_epoch = snapshot.proof_epoch;
  output.date_raw = snapshot.date_raw;
  output.player_character_id = snapshot.played_character_id;
  output.group_key = group->group_key;
  output.active_law_key = group->active_law_key;
  output.authority_evaluated = group->can_change_evaluated;
  output.authority_allows_change = group->can_change;
  output.candidate = *candidate;
  output.title_successors = snapshot.title_baseline;
  if (!NormalizeResources(observation, output.resource_count,
                          output.resources)) {
    return ActionFailure::resource_observation_invalid;
  }
  if (!output.authority_evaluated || !output.authority_allows_change) {
    return ActionFailure::authority_denied;
  }
  if (candidate->is_active || !candidate->evaluation_complete ||
      !candidate->can_have || !candidate->can_pass ||
      !candidate->can_enact || !candidate->costs_complete ||
      candidate->blocked_reason.presence != Presence::absent) {
    return ActionFailure::final_legality_denied;
  }
  return ActionFailure::none;
}

const RealmLawEnactBudgetV1 *FindBudget(
    const RealmLawEnactActionRequestV1 &request,
    const RealmLawGovernanceKeyV1 &currency_key) noexcept {
  for (std::uint32_t index = 0; index < request.budget_count; ++index) {
    if (request.budgets[index].currency_key == currency_key) {
      return &request.budgets[index];
    }
  }
  return nullptr;
}

const RealmLawEnactResourceBalanceV1 *FindResource(
    const StableCandidateV1 &state,
    const RealmLawGovernanceKeyV1 &currency_key) noexcept {
  for (std::uint32_t index = 0; index < state.resource_count; ++index) {
    if (state.resources[index].currency_key == currency_key) {
      return &state.resources[index];
    }
  }
  return nullptr;
}

ActionFailure PrepareCharges(
    const RealmLawEnactActionRequestV1 &request,
    const StableCandidateV1 &state, std::uint32_t &charge_count,
    std::array<RealmLawEnactChargeV1, kRealmLawEnactMaximumResourcesV1>
        &charges) noexcept {
  charge_count = 0;
  charges = {};
  if (state.candidate.cost_count != request.budget_count ||
      state.candidate.cost_count > charges.size()) {
    return ActionFailure::budget_not_authorized;
  }
  charge_count = state.candidate.cost_count;
  for (std::uint32_t index = 0; index < charge_count; ++index) {
    const auto &cost = state.candidate.costs[index];
    const auto *budget = FindBudget(request, cost.currency_key);
    if (budget == nullptr || budget->maximum_spend_raw < cost.amount_raw) {
      return ActionFailure::budget_not_authorized;
    }
    const auto *resource = FindResource(state, cost.currency_key);
    if (resource == nullptr || resource->amount_raw < cost.amount_raw) {
      return ActionFailure::insufficient_resources;
    }
    charges[index].currency_key = cost.currency_key;
    charges[index].cost_raw = cost.amount_raw;
    charges[index].pre_balance_raw = resource->amount_raw;
  }
  return ActionFailure::none;
}

AckStatus Reject(const RealmLawEnactActionRequestV1 &request,
                 ActionFailure failure,
                 const RealmLawGovernanceReasonV1 *blocked_reason,
                 RealmLawEnactActionAckV1 &ack) {
  ack = {};
  ack.status = AckStatus::rejected_before_submit;
  ack.failure = failure;
  ack.request_id = request.request_id;
  ack.group_key = request.group_key;
  ack.requested_law_key = request.law_key;
  if (blocked_reason != nullptr) ack.blocked_reason = *blocked_reason;
  return ack.status;
}

void PopulateReceiptFrame(const Observation &post,
                          RealmLawEnactActionReceiptV1 &receipt) noexcept {
  receipt.post_public_revision = post.law_snapshot.public_revision;
  receipt.post_native_revision = post.law_snapshot.native_revision;
  receipt.post_proof_epoch = post.law_snapshot.proof_epoch;
  receipt.post_date_raw = post.law_snapshot.date_raw;
  receipt.post_title_successors = post.law_snapshot.title_baseline;
}

bool NewerThanAck(const RealmLawEnactActionAckV1 &ack,
                  const RealmLawGovernanceSnapshotV1 &post) noexcept {
  if (post.public_revision < ack.pre_public_revision ||
      post.native_revision < ack.pre_native_revision ||
      post.proof_epoch < ack.pre_proof_epoch ||
      post.date_raw < ack.pre_date_raw) {
    return false;
  }
  return post.public_revision > ack.pre_public_revision ||
      post.native_revision > ack.pre_native_revision ||
      post.proof_epoch > ack.pre_proof_epoch ||
      post.date_raw > ack.pre_date_raw;
}

} // namespace

AckStatus ExecuteRealmLawEnactActionV1(
    const RealmLawEnactActionAccessV1 &access,
    const RealmLawEnactActionRequestV1 &request,
    RealmLawEnactActionAckV1 &ack) noexcept {
  try {
    if (!ValidRequest(request)) {
      return Reject(request, ActionFailure::request_contract_invalid, nullptr,
                    ack);
    }
    if (!access.exact_build_admitted ||
        access.admitted_executable_sha256 !=
            kRealmLawGovernanceSnapshotV1ExecutableSha256) {
      return Reject(request, ActionFailure::exact_build_mismatch, nullptr, ack);
    }
    if (access.current_thread_id == 0 ||
        access.current_thread_id != access.application_main_thread_id) {
      return Reject(request, ActionFailure::application_main_thread_required,
                    nullptr, ack);
    }
    if (access.capture_observation == nullptr || access.submit == nullptr) {
      return Reject(request, ActionFailure::callbacks_unavailable, nullptr,
                    ack);
    }

    const auto first = std::make_unique<Observation>();
    const auto second = std::make_unique<Observation>();
    if (!first || !second) {
      return Reject(request, ActionFailure::working_storage_unavailable,
                    nullptr, ack);
    }
    if (!access.capture_observation(access.context, *first)) {
      return Reject(request, ActionFailure::observation_unavailable, nullptr,
                    ack);
    }
    StableCandidateV1 first_state{};
    auto failure = ExtractStableCandidate(*first, request, first_state);
    if (failure != ActionFailure::none) {
      const auto *reason = failure == ActionFailure::final_legality_denied
          ? &first_state.candidate.blocked_reason
          : nullptr;
      return Reject(request, failure, reason, ack);
    }

    std::uint32_t charge_count = 0;
    std::array<RealmLawEnactChargeV1, kRealmLawEnactMaximumResourcesV1>
        charges{};
    failure = PrepareCharges(request, first_state, charge_count, charges);
    if (failure != ActionFailure::none) {
      return Reject(request, failure, nullptr, ack);
    }

    if (!access.capture_observation(access.context, *second)) {
      return Reject(request, ActionFailure::state_changed_before_submit,
                    nullptr, ack);
    }
    StableCandidateV1 second_state{};
    if (ExtractStableCandidate(*second, request, second_state) !=
            ActionFailure::none ||
        first_state != second_state) {
      return Reject(request, ActionFailure::state_changed_before_submit,
                    nullptr, ack);
    }

    RealmLawEnactSubmissionV1 submission{};
    submission.player_character_id = first_state.player_character_id;
    submission.group_key = first_state.group_key;
    submission.previous_effective_law_key = first_state.active_law_key;
    submission.requested_law_key = first_state.candidate.law_key;
    submission.public_revision = first_state.public_revision;
    submission.native_revision = first_state.native_revision;
    submission.proof_epoch = first_state.proof_epoch;
    submission.charge_count = charge_count;
    submission.charges = charges;
    if (!access.submit(access.context, submission)) {
      return Reject(request, ActionFailure::native_submit_rejected, nullptr,
                    ack);
    }

    ack = {};
    ack.status = AckStatus::submitted_verification_pending;
    ack.verification_pending = true;
    ack.failure = ActionFailure::none;
    ack.request_id = request.request_id;
    ack.pre_public_revision = first_state.public_revision;
    ack.pre_native_revision = first_state.native_revision;
    ack.pre_proof_epoch = first_state.proof_epoch;
    ack.pre_date_raw = first_state.date_raw;
    ack.player_character_id = first_state.player_character_id;
    ack.group_key = first_state.group_key;
    ack.previous_effective_law_key = first_state.active_law_key;
    ack.requested_law_key = first_state.candidate.law_key;
    ack.charge_count = charge_count;
    ack.charges = charges;
    ack.expected_succession = first_state.candidate.succession;
    ack.pre_title_successors = first_state.title_successors;
    ack.blocked_reason.presence = Presence::absent;
    return ack.status;
  } catch (...) {
    return Reject(request, ActionFailure::working_storage_unavailable, nullptr,
                  ack);
  }
}

ReceiptStatus VerifyRealmLawEnactActionReceiptV1(
    const RealmLawEnactActionAckV1 &ack,
    const RealmLawEnactActionObservationV1 &post_observation,
    RealmLawEnactActionReceiptV1 &receipt) noexcept {
  receipt = {};
  receipt.request_id = ack.request_id;
  if (ack.status == AckStatus::rejected_before_submit) {
    receipt.status = ReceiptStatus::rejected;
    receipt.failure = ReceiptFailure::action_rejected;
    receipt.rejected_action_failure = ack.failure;
    return receipt.status;
  }
  const auto fail = [&](ReceiptFailure failure) noexcept {
    receipt.status = ReceiptStatus::failed;
    receipt.failure = failure;
    return receipt.status;
  };
  if (ack.status != AckStatus::submitted_verification_pending ||
      !ack.verification_pending || ack.failure != ActionFailure::none ||
      !ValidRequestId(ack.request_id) || !ValidKey(ack.group_key) ||
      !ValidKey(ack.requested_law_key) || ack.player_character_id <= 0 ||
      ack.charge_count > ack.charges.size()) {
    return fail(ReceiptFailure::invalid_ack);
  }
  if (!post_observation.available ||
      post_observation.law_snapshot.status !=
          RealmLawGovernanceSnapshotV1Status::available ||
      post_observation.law_snapshot.unavailable_reason !=
          RealmLawGovernanceSnapshotV1Failure::none ||
      !CompleteReadiness(post_observation.law_snapshot.readiness)) {
    return fail(ReceiptFailure::post_observation_unavailable);
  }
  PopulateReceiptFrame(post_observation, receipt);
  if (!post_observation.paused ||
      !NewerThanAck(ack, post_observation.law_snapshot)) {
    return fail(ReceiptFailure::no_new_paused_snapshot);
  }
  if (post_observation.law_snapshot.played_character_id !=
      ack.player_character_id) {
    return fail(ReceiptFailure::player_identity_changed);
  }
  const auto *group = FindGroup(post_observation.law_snapshot, ack.group_key);
  if (group == nullptr) {
    return fail(ReceiptFailure::group_or_candidate_unavailable);
  }
  receipt.effective_law_key = group->active_law_key;
  const auto *candidate = FindCandidate(*group, ack.requested_law_key);
  if (candidate == nullptr) {
    return fail(ReceiptFailure::group_or_candidate_unavailable);
  }
  receipt.observed_succession = candidate->succession;
  if (group->active_law_key != ack.requested_law_key ||
      !candidate->is_active) {
    return fail(ReceiptFailure::effective_law_not_enacted);
  }
  receipt.effective_law_verified = true;

  std::uint32_t resource_count = 0;
  std::array<RealmLawEnactResourceBalanceV1,
             kRealmLawEnactMaximumResourcesV1>
      resources{};
  if (!NormalizeResources(post_observation, resource_count, resources)) {
    return fail(ReceiptFailure::resource_recheck_failed);
  }
  receipt.charge_count = ack.charge_count;
  receipt.charges = ack.charges;
  for (std::uint32_t charge_index = 0; charge_index < ack.charge_count;
       ++charge_index) {
    const auto &expected = ack.charges[charge_index];
    const RealmLawEnactResourceBalanceV1 *post_resource = nullptr;
    for (std::uint32_t index = 0; index < resource_count; ++index) {
      if (resources[index].currency_key == expected.currency_key) {
        post_resource = &resources[index];
        break;
      }
    }
    if (post_resource == nullptr || expected.cost_raw < 0 ||
        expected.pre_balance_raw < expected.cost_raw ||
        post_resource->amount_raw !=
            expected.pre_balance_raw - expected.cost_raw) {
      return fail(ReceiptFailure::resource_recheck_failed);
    }
    receipt.charges[charge_index].post_balance_raw =
        post_resource->amount_raw;
  }
  receipt.resources_verified = true;
  if (candidate->succession != ack.expected_succession) {
    return fail(ReceiptFailure::succession_shape_changed);
  }
  receipt.succession_verified = true;
  receipt.status = ReceiptStatus::enacted;
  receipt.failure = ReceiptFailure::none;
  return receipt.status;
}

std::string_view RealmLawEnactActionFailureNameV1(
    ActionFailure failure) noexcept {
  switch (failure) {
  case ActionFailure::none: return "none";
  case ActionFailure::request_contract_invalid:
    return "request_contract_invalid";
  case ActionFailure::exact_build_mismatch: return "exact_build_mismatch";
  case ActionFailure::application_main_thread_required:
    return "application_main_thread_required";
  case ActionFailure::callbacks_unavailable: return "callbacks_unavailable";
  case ActionFailure::observation_unavailable:
    return "observation_unavailable";
  case ActionFailure::not_paused: return "not_paused";
  case ActionFailure::snapshot_unavailable: return "snapshot_unavailable";
  case ActionFailure::stale_snapshot: return "stale_snapshot";
  case ActionFailure::candidate_not_found: return "candidate_not_found";
  case ActionFailure::authority_denied: return "authority_denied";
  case ActionFailure::final_legality_denied:
    return "final_legality_denied";
  case ActionFailure::resource_observation_invalid:
    return "resource_observation_invalid";
  case ActionFailure::budget_not_authorized:
    return "budget_not_authorized";
  case ActionFailure::insufficient_resources:
    return "insufficient_resources";
  case ActionFailure::state_changed_before_submit:
    return "state_changed_before_submit";
  case ActionFailure::working_storage_unavailable:
    return "working_storage_unavailable";
  case ActionFailure::native_submit_rejected:
    return "native_submit_rejected";
  }
  return "unknown";
}

std::string_view RealmLawEnactActionReceiptFailureNameV1(
    ReceiptFailure failure) noexcept {
  switch (failure) {
  case ReceiptFailure::none: return "none";
  case ReceiptFailure::action_rejected: return "action_rejected";
  case ReceiptFailure::invalid_ack: return "invalid_ack";
  case ReceiptFailure::post_observation_unavailable:
    return "post_observation_unavailable";
  case ReceiptFailure::no_new_paused_snapshot:
    return "no_new_paused_snapshot";
  case ReceiptFailure::player_identity_changed:
    return "player_identity_changed";
  case ReceiptFailure::group_or_candidate_unavailable:
    return "group_or_candidate_unavailable";
  case ReceiptFailure::effective_law_not_enacted:
    return "effective_law_not_enacted";
  case ReceiptFailure::resource_recheck_failed:
    return "resource_recheck_failed";
  case ReceiptFailure::succession_shape_changed:
    return "succession_shape_changed";
  }
  return "unknown";
}

} // namespace xar::bridge
