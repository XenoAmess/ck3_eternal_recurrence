#include "xar_bridge/realm_law_native_binder_v1.hpp"

#include <algorithm>
#include <cstring>
#include <memory>
#include <new>
#include <type_traits>

namespace xar::bridge {
namespace {

using ActionObservation = RealmLawEnactActionObservationV1;
using RuntimeProof = RealmLawNativeRuntimeProofV1;
using SourceAccess = RealmLawGovernanceSourceAccessV1;
using State = RealmLawNativeBinderStateV1;

template <std::size_t Size>
std::string_view FixedView(const std::array<char, Size> &value) noexcept {
  const auto end = std::find(value.begin(), value.end(), '\0');
  if (end == value.end()) return {};
  return {value.data(), static_cast<std::size_t>(end - value.begin())};
}

bool ValidDigest(std::string_view value) noexcept {
  if (value.size() != 64) return false;
  for (const char character : value) {
    const bool digit = character >= '0' && character <= '9';
    const bool lower = character >= 'a' && character <= 'f';
    const bool upper = character >= 'A' && character <= 'F';
    if (!digit && !lower && !upper) return false;
  }
  return true;
}

bool CompleteOperations(
    const RealmLawNativeBinderOperationsV1 &operations) noexcept {
  return operations.read_runtime_proof != nullptr &&
      operations.capture_frame != nullptr &&
      operations.resolve_player != nullptr &&
      operations.resolve_container != nullptr &&
      operations.read_group != nullptr &&
      operations.read_candidate != nullptr &&
      operations.read_title_baseline != nullptr &&
      operations.read_resources != nullptr &&
      operations.submit_enact != nullptr;
}

bool ProofMatchesEnvironment(
    const RuntimeProof &proof,
    const RealmLawNativeBinderEnvironmentV1 &environment,
    std::string_view expected_signature_manifest) noexcept {
  return proof.exact_build_admitted &&
      FixedView(proof.executable_sha256) ==
          kRealmLawNativeBinderV1ExecutableSha256 &&
      proof.module_base == environment.module_base &&
      proof.signatures_complete &&
      FixedView(proof.signature_manifest_sha256) ==
          expected_signature_manifest &&
      proof.signature_generation != 0 && proof.connection_generation != 0 &&
      proof.proof_epoch != 0 && proof.current_thread_id != 0 &&
      proof.current_thread_id == proof.application_main_thread_id &&
      proof.paused;
}

bool ProofMatchesState(const RuntimeProof &proof,
                       const State &state) noexcept {
  return state.attached && proof.exact_build_admitted &&
      FixedView(proof.executable_sha256) ==
          FixedView(state.executable_sha256) &&
      proof.module_base == state.module_base && proof.signatures_complete &&
      FixedView(proof.signature_manifest_sha256) ==
          FixedView(state.signature_manifest_sha256) &&
      proof.signature_generation == state.signature_generation &&
      proof.connection_generation == state.connection_generation &&
      proof.proof_epoch != 0 &&
      proof.application_main_thread_id == state.application_main_thread_id &&
      proof.current_thread_id == state.application_main_thread_id &&
      proof.paused;
}

void MarkIntegrityFailure(State &state) noexcept {
  state.integrity_failed = true;
}

bool ReadPinnedProof(State &state, RuntimeProof &output) noexcept {
  output = {};
  if (!state.attached || state.integrity_failed ||
      state.operations.read_runtime_proof == nullptr ||
      !state.operations.read_runtime_proof(state.native_context, output) ||
      !ProofMatchesState(output, state)) {
    MarkIntegrityFailure(state);
    return false;
  }
  return true;
}

bool SamePinnedProofAfterCall(State &state,
                              const RuntimeProof &before) noexcept {
  RuntimeProof after{};
  if (!ReadPinnedProof(state, after) || after != before) {
    MarkIntegrityFailure(state);
    return false;
  }
  return true;
}

bool FrameMatchesProof(const RealmLawGovernanceFrameV1 &frame,
                       const RuntimeProof &proof) noexcept {
  return frame.paused == proof.paused &&
      frame.proof_epoch == proof.proof_epoch;
}

bool CaptureFrameThunk(void *context,
                       RealmLawGovernanceFrameV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  RuntimeProof before{};
  if (!ReadPinnedProof(state, before)) return false;
  const bool closing = state.source_transaction_open;
  if (closing &&
      before.proof_epoch != state.source_transaction_proof_epoch) {
    MarkIntegrityFailure(state);
    return false;
  }
  if (!state.operations.capture_frame(state.native_context, output) ||
      !SamePinnedProofAfterCall(state, before) ||
      !FrameMatchesProof(output, before)) {
    return false;
  }
  if (closing) {
    state.source_transaction_open = false;
    state.source_transaction_proof_epoch = 0;
  } else {
    state.source_transaction_open = true;
    state.source_transaction_proof_epoch = before.proof_epoch;
  }
  return true;
}

bool BeginSourceCall(State &state, RuntimeProof &before) noexcept {
  if (!state.source_transaction_open || !ReadPinnedProof(state, before) ||
      before.proof_epoch != state.source_transaction_proof_epoch) {
    MarkIntegrityFailure(state);
    return false;
  }
  return true;
}

bool ResolvePlayerThunk(
    void *context, std::int32_t expected_character_id,
    RealmLawGovernanceSourcePlayerLeaseV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  RuntimeProof before{};
  return BeginSourceCall(state, before) &&
      state.operations.resolve_player(state.native_context,
                                      expected_character_id, output) &&
      SamePinnedProofAfterCall(state, before);
}

bool ResolveContainerThunk(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    RealmLawGovernanceSourceContainerLeaseV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  RuntimeProof before{};
  return BeginSourceCall(state, before) &&
      state.operations.resolve_container(state.native_context, player,
                                         output) &&
      SamePinnedProofAfterCall(state, before);
}

bool ReadGroupThunk(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    const RealmLawGovernanceSourceContainerLeaseV1 &container,
    std::size_t group_index,
    RealmLawGovernanceSourceGroupLeaseV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  RuntimeProof before{};
  return BeginSourceCall(state, before) &&
      state.operations.read_group(state.native_context, player, container,
                                  group_index, output) &&
      SamePinnedProofAfterCall(state, before);
}

bool ReadCandidateThunk(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    const RealmLawGovernanceSourceContainerLeaseV1 &container,
    const RealmLawGovernanceSourceGroupLeaseV1 &group,
    std::size_t candidate_index,
    RealmLawGovernanceCandidateV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  RuntimeProof before{};
  return BeginSourceCall(state, before) &&
      state.operations.read_candidate(state.native_context, player, container,
                                      group, candidate_index, output) &&
      SamePinnedProofAfterCall(state, before);
}

bool ReadTitleBaselineThunk(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    RealmLawGovernanceTitleBaselineV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  RuntimeProof before{};
  return BeginSourceCall(state, before) &&
      state.operations.read_title_baseline(state.native_context, player,
                                           output) &&
      SamePinnedProofAfterCall(state, before);
}

bool ValidResourceSample(
    const RealmLawNativeResourceSampleV1 &sample,
    const RealmLawGovernanceSnapshotV1 &snapshot,
    const RuntimeProof &proof) noexcept {
  if (!sample.complete || sample.public_revision != snapshot.public_revision ||
      sample.native_revision != snapshot.native_revision ||
      sample.connection_generation != proof.connection_generation ||
      sample.proof_epoch != snapshot.proof_epoch ||
      sample.proof_epoch != proof.proof_epoch ||
      sample.date_raw != snapshot.date_raw ||
      sample.player_character_id != snapshot.played_character_id ||
      sample.resource_count > sample.resources.size()) {
    return false;
  }
  for (std::uint32_t index = 0; index < sample.resource_count; ++index) {
    const auto &resource = sample.resources[index];
    const auto key = RealmLawGovernanceKeyViewV1(resource.currency_key);
    if (key.empty() || key.size() != resource.currency_key.size ||
        resource.amount_raw < 0) {
      return false;
    }
    for (std::uint32_t prior = 0; prior < index; ++prior) {
      if (sample.resources[prior].currency_key == resource.currency_key) {
        return false;
      }
    }
  }
  return true;
}

bool CaptureActionObservationImpl(State &state, ActionObservation &output,
                                  bool record) noexcept {
  static_assert(std::is_trivially_copyable_v<ActionObservation>);
  std::memset(&output, 0, sizeof(output));
  if (!state.attached || state.integrity_failed ||
      state.source_transaction_open) {
    return false;
  }
  const auto source_result =
      std::unique_ptr<RealmLawGovernanceSourceResultV1>(
          new (std::nothrow) RealmLawGovernanceSourceResultV1{});
  if (!source_result) return false;
  auto source_access = MakeRealmLawNativeSourceAccessV1(state);
  if (!ObserveRealmLawGovernanceSourceV1(source_access, *source_result) ||
      state.source_transaction_open || state.integrity_failed) {
    if (state.source_transaction_open) MarkIntegrityFailure(state);
    return false;
  }

  RuntimeProof before{};
  RealmLawNativeResourceSampleV1 resources{};
  if (!ReadPinnedProof(state, before) ||
      before.proof_epoch != source_result->snapshot.proof_epoch ||
      !state.operations.read_resources(state.native_context,
                                       source_result->snapshot, resources) ||
      !SamePinnedProofAfterCall(state, before) ||
      !ValidResourceSample(resources, source_result->snapshot, before)) {
    return false;
  }
  output.available = true;
  output.paused = true;
  output.law_snapshot = source_result->snapshot;
  output.resources_complete = true;
  output.resource_count = resources.resource_count;
  output.resources = resources.resources;
  if (record) {
    state.last_action_observation = output;
    state.last_action_observation_available = true;
    ++state.action_capture_serial;
  }
  return true;
}

bool CaptureActionObservationThunk(void *context,
                                   ActionObservation &output) noexcept {
  return CaptureActionObservationImpl(*static_cast<State *>(context), output,
                                      true);
}

const RealmLawGovernanceGroupV1 *FindGroup(
    const RealmLawGovernanceSnapshotV1 &snapshot,
    const RealmLawGovernanceKeyV1 &key) noexcept {
  for (std::uint32_t index = 0; index < snapshot.group_count; ++index) {
    if (snapshot.groups[index].group_key == key) {
      return &snapshot.groups[index];
    }
  }
  return nullptr;
}

const RealmLawGovernanceCandidateV1 *FindCandidate(
    const RealmLawGovernanceGroupV1 &group,
    const RealmLawGovernanceKeyV1 &key) noexcept {
  for (std::uint32_t index = 0; index < group.candidate_count; ++index) {
    if (group.candidates[index].law_key == key) {
      return &group.candidates[index];
    }
  }
  return nullptr;
}

const RealmLawEnactResourceBalanceV1 *FindResource(
    const ActionObservation &observation,
    const RealmLawGovernanceKeyV1 &key) noexcept {
  for (std::uint32_t index = 0; index < observation.resource_count; ++index) {
    if (observation.resources[index].currency_key == key) {
      return &observation.resources[index];
    }
  }
  return nullptr;
}

bool SameResourceVector(const ActionObservation &left,
                        const ActionObservation &right) noexcept {
  if (!left.resources_complete || !right.resources_complete ||
      left.resource_count != right.resource_count) {
    return false;
  }
  for (std::uint32_t index = 0; index < left.resource_count; ++index) {
    if (left.resources[index] != right.resources[index]) return false;
  }
  return true;
}

bool SubmissionMatchesStableTarget(
    const ActionObservation &previous, const ActionObservation &current,
    const RealmLawEnactSubmissionV1 &submission) noexcept {
  const auto frame_matches = [&](const ActionObservation &observation) {
    const auto &snapshot = observation.law_snapshot;
    return observation.available && observation.paused &&
        snapshot.status == RealmLawGovernanceSnapshotV1Status::available &&
        snapshot.public_revision == submission.public_revision &&
        snapshot.native_revision == submission.native_revision &&
        snapshot.proof_epoch == submission.proof_epoch &&
        snapshot.played_character_id == submission.player_character_id;
  };
  if (!frame_matches(previous) || !frame_matches(current) ||
      !SameResourceVector(previous, current) ||
      previous.law_snapshot.title_baseline !=
          current.law_snapshot.title_baseline) {
    return false;
  }
  const auto *previous_group =
      FindGroup(previous.law_snapshot, submission.group_key);
  const auto *current_group =
      FindGroup(current.law_snapshot, submission.group_key);
  if (previous_group == nullptr || current_group == nullptr ||
      previous_group->active_law_key !=
          submission.previous_effective_law_key ||
      previous_group->active_law_key != current_group->active_law_key ||
      previous_group->can_change_evaluated !=
          current_group->can_change_evaluated ||
      previous_group->can_change != current_group->can_change ||
      !previous_group->can_change_evaluated || !previous_group->can_change) {
    return false;
  }
  const auto *previous_candidate =
      FindCandidate(*previous_group, submission.requested_law_key);
  const auto *current_candidate =
      FindCandidate(*current_group, submission.requested_law_key);
  if (previous_candidate == nullptr || current_candidate == nullptr ||
      *previous_candidate != *current_candidate ||
      previous_candidate->is_active || !previous_candidate->can_enact ||
      previous_candidate->cost_count != submission.charge_count ||
      submission.charge_count > submission.charges.size()) {
    return false;
  }
  for (std::uint32_t index = 0; index < submission.charge_count; ++index) {
    const auto &cost = previous_candidate->costs[index];
    const auto &charge = submission.charges[index];
    if (cost.currency_key != charge.currency_key ||
        cost.amount_raw != charge.cost_raw) {
      return false;
    }
    const auto *previous_resource = FindResource(previous, charge.currency_key);
    const auto *current_resource = FindResource(current, charge.currency_key);
    if (previous_resource == nullptr || current_resource == nullptr ||
        previous_resource->amount_raw != charge.pre_balance_raw ||
        *previous_resource != *current_resource) {
      return false;
    }
  }
  return true;
}

bool SubmitActionThunk(
    void *context, const RealmLawEnactSubmissionV1 &submission) noexcept {
  auto &state = *static_cast<State *>(context);
  if (!state.attached || state.integrity_failed || state.submit_pending ||
      !state.last_action_observation_available ||
      state.action_capture_serial < 2) {
    return false;
  }
  const auto current = std::unique_ptr<ActionObservation>(
      new (std::nothrow) ActionObservation{});
  if (!current || !CaptureActionObservationImpl(state, *current, false) ||
      !SubmissionMatchesStableTarget(state.last_action_observation, *current,
                                     submission)) {
    return false;
  }
  RuntimeProof before{};
  if (!ReadPinnedProof(state, before) ||
      before.proof_epoch != submission.proof_epoch) {
    return false;
  }
  const auto disposition =
      state.operations.submit_enact(state.native_context, submission);
  const bool possibly_submitted =
      disposition == RealmLawNativeSubmitDispositionV1::submitted ||
      disposition ==
          RealmLawNativeSubmitDispositionV1::submitted_outcome_unknown;
  if (possibly_submitted) {
    state.submit_pending = true;
    state.last_submission = submission;
  }
  RuntimeProof after{};
  const bool proof_stable = ReadPinnedProof(state, after) && after == before;
  if (!proof_stable) {
    MarkIntegrityFailure(state);
    if (possibly_submitted) state.post_submit_integrity_failed = true;
  }
  return possibly_submitted;
}

bool AckMatchesLastSubmission(const RealmLawEnactActionAckV1 &ack,
                              const State &state) noexcept {
  if (!state.submit_pending ||
      ack.status !=
          RealmLawEnactActionAckStatusV1::submitted_verification_pending ||
      !ack.verification_pending ||
      ack.failure != RealmLawEnactActionFailureV1::none ||
      ack.player_character_id != state.last_submission.player_character_id ||
      ack.group_key != state.last_submission.group_key ||
      ack.previous_effective_law_key !=
          state.last_submission.previous_effective_law_key ||
      ack.requested_law_key != state.last_submission.requested_law_key ||
      ack.pre_public_revision != state.last_submission.public_revision ||
      ack.pre_native_revision != state.last_submission.native_revision ||
      ack.pre_proof_epoch != state.last_submission.proof_epoch ||
      ack.charge_count != state.last_submission.charge_count) {
    return false;
  }
  for (std::uint32_t index = 0; index < ack.charge_count; ++index) {
    if (ack.charges[index].currency_key !=
            state.last_submission.charges[index].currency_key ||
        ack.charges[index].cost_raw !=
            state.last_submission.charges[index].cost_raw ||
        ack.charges[index].pre_balance_raw !=
            state.last_submission.charges[index].pre_balance_raw) {
      return false;
    }
  }
  return true;
}

} // namespace

bool AssignRealmLawNativeDigestV1(
    std::string_view value,
    std::array<char, kRealmLawNativeBinderV1DigestCapacity> &output) noexcept {
  output = {};
  if (!ValidDigest(value)) return false;
  std::copy(value.begin(), value.end(), output.begin());
  return true;
}

bool BindRealmLawNativeV1(
    const RealmLawNativeBinderEnvironmentV1 &environment,
    RealmLawNativeBinderStateV1 &state) noexcept {
  static_assert(std::is_trivially_copyable_v<State>);
  if (state.attached || !environment.binding_enabled ||
      environment.module_base == 0 ||
      environment.admitted_executable_sha256 !=
          kRealmLawNativeBinderV1ExecutableSha256 ||
      !ValidDigest(environment.expected_signature_manifest_sha256) ||
      !CompleteOperations(environment.operations)) {
    return false;
  }
  RuntimeProof first{};
  RuntimeProof second{};
  if (!environment.operations.read_runtime_proof(environment.native_context,
                                                 first) ||
      !environment.operations.read_runtime_proof(environment.native_context,
                                                 second) ||
      first != second ||
      !ProofMatchesEnvironment(first, environment,
                               environment.expected_signature_manifest_sha256)) {
    return false;
  }
  std::memset(&state, 0, sizeof(state));
  state.attached = true;
  state.offline_fixture = environment.offline_fixture;
  state.module_base = environment.module_base;
  state.executable_sha256 = first.executable_sha256;
  state.signature_manifest_sha256 = first.signature_manifest_sha256;
  state.signature_generation = first.signature_generation;
  state.connection_generation = first.connection_generation;
  state.application_main_thread_id = first.application_main_thread_id;
  state.native_context = environment.native_context;
  state.operations = environment.operations;
  return true;
}

SourceAccess MakeRealmLawNativeSourceAccessV1(State &state) noexcept {
  SourceAccess output{};
  if (!state.attached || state.integrity_failed) return output;
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      kRealmLawNativeBinderV1ExecutableSha256;
  output.current_thread_id = state.application_main_thread_id;
  output.application_main_thread_id = state.application_main_thread_id;
  output.context = &state;
  output.capture_frame = &CaptureFrameThunk;
  output.resolve_player = &ResolvePlayerThunk;
  output.resolve_container = &ResolveContainerThunk;
  output.read_group = &ReadGroupThunk;
  output.read_candidate = &ReadCandidateThunk;
  output.read_title_baseline = &ReadTitleBaselineThunk;
  return output;
}

RealmLawEnactActionAccessV1 MakeRealmLawNativeActionAccessV1(
    State &state) noexcept {
  RealmLawEnactActionAccessV1 output{};
  if (!state.attached || state.integrity_failed) return output;
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      kRealmLawNativeBinderV1ExecutableSha256;
  output.current_thread_id = state.application_main_thread_id;
  output.application_main_thread_id = state.application_main_thread_id;
  output.context = &state;
  output.capture_observation = &CaptureActionObservationThunk;
  output.submit = &SubmitActionThunk;
  return output;
}

RealmLawEnactActionAckStatusV1 ExecuteBoundRealmLawNativeEnactV1(
    State &state, const RealmLawEnactActionRequestV1 &request,
    RealmLawEnactActionAckV1 &ack) noexcept {
  auto access = MakeRealmLawNativeActionAccessV1(state);
  return ExecuteRealmLawEnactActionV1(access, request, ack);
}

RealmLawEnactActionReceiptStatusV1 VerifyBoundRealmLawNativeReceiptV1(
    State &state, const RealmLawEnactActionAckV1 &ack,
    RealmLawEnactActionReceiptV1 &receipt) noexcept {
  if (ack.status ==
      RealmLawEnactActionAckStatusV1::rejected_before_submit) {
    return VerifyRealmLawEnactActionReceiptV1(
        ack, state.last_action_observation, receipt);
  }
  if (!AckMatchesLastSubmission(ack, state)) {
    auto invalid_ack = ack;
    invalid_ack.verification_pending = false;
    return VerifyRealmLawEnactActionReceiptV1(
        invalid_ack, state.last_action_observation, receipt);
  }
  const auto post = std::unique_ptr<ActionObservation>(
      new (std::nothrow) ActionObservation{});
  if (!post || state.post_submit_integrity_failed ||
      !CaptureActionObservationImpl(state, *post, true)) {
    if (post) {
      static_assert(std::is_trivially_copyable_v<ActionObservation>);
      std::memset(post.get(), 0, sizeof(*post));
      const auto status =
          VerifyRealmLawEnactActionReceiptV1(ack, *post, receipt);
      return status;
    }
    return VerifyRealmLawEnactActionReceiptV1(
        ack, state.last_action_observation, receipt);
  }
  const auto status = VerifyRealmLawEnactActionReceiptV1(ack, *post, receipt);
  if (status == RealmLawEnactActionReceiptStatusV1::enacted) {
    state.submit_pending = false;
  }
  return status;
}

} // namespace xar::bridge
