#include "xar_bridge/realm_law_native_shared_glue_v1.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <type_traits>

namespace xar::bridge {
namespace {

using AbiFailure =
    ck3_11906::private_law::RealmLawMutationAbiFailureV1;
using Failure = RealmLawNativeSharedGlueFailureV1;
using RuntimeProof = RealmLawNativeRuntimeProofV1;
using State = RealmLawNativeSharedGlueStateV1;
using Submission = RealmLawEnactSubmissionV1;
using Target = RealmLawNativeEnactTargetLeaseV1;

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

void SetFailure(State &state, Failure failure, const char *evidence,
                AbiFailure abi_failure = AbiFailure::none) noexcept {
  if (state.failure == Failure::none || !state.prepared) {
    state.failure = failure;
    state.abi_failure = abi_failure;
    state.failed_evidence = evidence;
  }
}

bool SourceOperationsComplete(
    const RealmLawNativeBinderOperationsV1 &operations) noexcept {
  return operations.read_runtime_proof != nullptr &&
      operations.capture_frame != nullptr &&
      operations.resolve_player != nullptr &&
      operations.resolve_container != nullptr &&
      operations.read_group != nullptr &&
      operations.read_candidate != nullptr &&
      operations.read_title_baseline != nullptr &&
      operations.read_resources != nullptr;
}

bool SourceProofMatchesConfiguration(
    const RuntimeProof &proof,
    const RealmLawNativeSharedGlueConfigurationV1 &configuration) noexcept {
  return proof.exact_build_admitted &&
      FixedView(proof.executable_sha256) ==
          kRealmLawNativeSharedGlueV1ExecutableSha256 &&
      proof.module_base == configuration.module_base &&
      proof.signatures_complete &&
      FixedView(proof.signature_manifest_sha256) ==
          configuration.expected_source_signature_manifest_sha256 &&
      proof.signature_generation != 0 && proof.connection_generation != 0 &&
      proof.proof_epoch != 0 && proof.current_thread_id != 0 &&
      proof.current_thread_id == proof.application_main_thread_id &&
      proof.paused;
}

bool SourceProofMatchesState(const RuntimeProof &proof,
                             const State &state) noexcept {
  return state.prepared && proof.exact_build_admitted &&
      FixedView(proof.executable_sha256) ==
          kRealmLawNativeSharedGlueV1ExecutableSha256 &&
      proof.module_base == state.module_base && proof.signatures_complete &&
      FixedView(proof.signature_manifest_sha256) ==
          FixedView(state.source_signature_manifest_sha256) &&
      proof.signature_generation == state.source_signature_generation &&
      proof.connection_generation == state.connection_generation &&
      proof.proof_epoch != 0 &&
      proof.application_main_thread_id == state.application_main_thread_id &&
      proof.current_thread_id == state.application_main_thread_id &&
      proof.paused;
}

bool VerifyMutationAbi(State &state) noexcept {
  const auto proof =
      ck3_11906::private_law::VerifyRealmLawEnactMutationAbiV1(
          state.mutation_abi_reader, state.module_base);
  if (!proof.verified) {
    SetFailure(state, Failure::mutation_abi_rejected, proof.failed_evidence,
               proof.failure);
    return false;
  }
  return true;
}

bool ReadVerifiedRuntimeProof(State &state, RuntimeProof &output) noexcept {
  output = {};
  RuntimeProof source{};
  if (state.failure != Failure::none ||
      !state.source_operations.read_runtime_proof(
          state.source_context, source)) {
    SetFailure(state, Failure::runtime_proof_unavailable,
               "read_runtime_proof");
    return false;
  }
  if (!SourceProofMatchesState(source, state)) {
    SetFailure(state, Failure::runtime_proof_mismatch,
               "source_runtime_proof");
    return false;
  }
  output = source;
  if (!AssignRealmLawNativeDigestV1(
          kRealmLawNativeSharedGlueV1MutationManifestSha256,
          output.signature_manifest_sha256)) {
    SetFailure(state, Failure::mutation_abi_rejected,
               "mutation_manifest_digest");
    return false;
  }
  return true;
}

bool ReadRuntimeProofThunk(void *context, RuntimeProof &output) noexcept {
  return ReadVerifiedRuntimeProof(*static_cast<State *>(context), output);
}

bool CaptureFrameThunk(void *context,
                       RealmLawGovernanceFrameV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.failure == Failure::none &&
      state.source_operations.capture_frame(state.source_context, output)) {
    return true;
  }
  SetFailure(state, Failure::source_callback_failed, "capture_frame");
  return false;
}

bool ResolvePlayerThunk(
    void *context, std::int32_t expected_character_id,
    RealmLawGovernanceSourcePlayerLeaseV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.failure == Failure::none &&
      state.source_operations.resolve_player(
          state.source_context, expected_character_id, output)) {
    return true;
  }
  SetFailure(state, Failure::source_callback_failed, "resolve_player");
  return false;
}

bool ResolveContainerThunk(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    RealmLawGovernanceSourceContainerLeaseV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.failure == Failure::none &&
      state.source_operations.resolve_container(state.source_context, player,
                                                output)) {
    return true;
  }
  SetFailure(state, Failure::source_callback_failed, "resolve_container");
  return false;
}

bool ReadGroupThunk(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    const RealmLawGovernanceSourceContainerLeaseV1 &container,
    std::size_t group_index,
    RealmLawGovernanceSourceGroupLeaseV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.failure == Failure::none &&
      state.source_operations.read_group(state.source_context, player,
                                         container, group_index, output)) {
    return true;
  }
  SetFailure(state, Failure::source_callback_failed, "read_group");
  return false;
}

bool ReadCandidateThunk(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    const RealmLawGovernanceSourceContainerLeaseV1 &container,
    const RealmLawGovernanceSourceGroupLeaseV1 &group,
    std::size_t candidate_index,
    RealmLawGovernanceCandidateV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.failure == Failure::none &&
      state.source_operations.read_candidate(
          state.source_context, player, container, group, candidate_index,
          output)) {
    return true;
  }
  SetFailure(state, Failure::source_callback_failed, "read_candidate");
  return false;
}

bool ReadTitleBaselineThunk(
    void *context, const RealmLawGovernanceSourcePlayerLeaseV1 &player,
    RealmLawGovernanceTitleBaselineV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.failure == Failure::none &&
      state.source_operations.read_title_baseline(state.source_context,
                                                  player, output)) {
    return true;
  }
  SetFailure(state, Failure::source_callback_failed,
             "read_title_baseline");
  return false;
}

bool ReadResourcesThunk(
    void *context, const RealmLawGovernanceSnapshotV1 &snapshot,
    RealmLawNativeResourceSampleV1 &output) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.failure == Failure::none &&
      state.source_operations.read_resources(state.source_context, snapshot,
                                             output)) {
    return true;
  }
  SetFailure(state, Failure::source_callback_failed, "read_resources");
  return false;
}

bool ValidSubmission(const Submission &submission) noexcept {
  return submission.player_character_id != -1 &&
      submission.public_revision != 0 && submission.native_revision != 0 &&
      submission.proof_epoch != 0 &&
      !RealmLawGovernanceKeyViewV1(submission.group_key).empty() &&
      !RealmLawGovernanceKeyViewV1(submission.requested_law_key).empty() &&
      submission.charge_count <= submission.charges.size();
}

bool ValidTarget(const Target &target, const Submission &submission,
                 const RuntimeProof &proof) noexcept {
  return target.actor_identity_round_trip && target.actor_address != 0 &&
      target.actor_character_id == submission.player_character_id &&
      target.group_identity_round_trip && target.group_identity != 0 &&
      target.group_generation != 0 &&
      target.group_key == submission.group_key &&
      target.law_identity_round_trip && target.law_address != 0 &&
      target.law_identity != 0 && target.law_generation != 0 &&
      target.law_key == submission.requested_law_key &&
      target.connection_generation == proof.connection_generation &&
      target.proof_epoch == proof.proof_epoch &&
      target.proof_epoch == submission.proof_epoch;
}

struct alignas(std::uintptr_t) AddLawCommandV1 {
  std::array<unsigned char, kRealmLawNativeAddLawCommandSizeV1> bytes{};
};

static_assert(sizeof(AddLawCommandV1) == kRealmLawNativeAddLawCommandSizeV1);

template <typename Value>
void Store(AddLawCommandV1 &command, std::size_t offset,
           Value value) noexcept {
  static_assert(std::is_trivially_copyable_v<Value>);
  std::memcpy(command.bytes.data() + offset, &value, sizeof(value));
}

AddLawCommandV1 BuildCommand(const State &state,
                             const Target &target) noexcept {
  AddLawCommandV1 command{};
  Store(command, 0x00,
        state.module_base +
            ck3_11906::private_law::kAddLawCommandPrimaryVtableRvaV1);
  Store(command, 0x18,
        state.module_base +
            ck3_11906::private_law::kAddLawCommandSecondaryVtableRvaV1);
  Store(command, 0x20, target.actor_character_id);
  Store(command, 0x28, target.law_address);
  return command;
}

#if defined(_MSC_VER)
using ValidateNativeCommand = bool(__fastcall *)(void *, void *);
using SubmitNativeCommand = bool(__fastcall *)(void *, void *,
                                               std::uint32_t);
#else
using ValidateNativeCommand = bool (*)(void *, void *);
using SubmitNativeCommand = bool (*)(void *, void *, std::uint32_t);
#endif

bool ValidateCommand(State &state, AddLawCommandV1 &command) noexcept {
  ++state.final_legality_calls;
  if (state.offline_fixture) {
    return state.offline_calls.validate_command(
        state.offline_call_context, command.bytes.data(),
        command.bytes.size());
  }
  const auto validate = reinterpret_cast<ValidateNativeCommand>(
      state.module_base +
      ck3_11906::private_law::kAddLawCommandValidatorRvaV1);
  return validate(command.bytes.data(), nullptr);
}

bool QueueCommand(State &state, AddLawCommandV1 &command) noexcept {
  ++state.native_queue_calls;
  const auto manager =
      state.module_base +
      ck3_11906::private_law::kCommandManagerRvaV1;
  if (state.offline_fixture) {
    return state.offline_calls.submit_command(
        state.offline_call_context, manager, command.bytes.data(),
        command.bytes.size(), kRealmLawNativeSubmitFlagsV1);
  }
  const auto submit = reinterpret_cast<SubmitNativeCommand>(
      state.module_base + kRealmLawNativeSubmitCommandRvaV1);
  return submit(reinterpret_cast<void *>(manager), command.bytes.data(),
                kRealmLawNativeSubmitFlagsV1);
}

RealmLawNativeSubmitDispositionV1 SubmitEnactThunk(
    void *context, const Submission &submission) noexcept {
  auto &state = *static_cast<State *>(context);
  if (state.failure != Failure::none || !state.prepared) {
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  if (!state.native_submit_enabled) {
    SetFailure(state, Failure::native_submit_disabled,
               "native_submit_enabled");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  if (!ValidSubmission(submission)) {
    SetFailure(state, Failure::submission_contract_invalid, "submission");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }

  RuntimeProof before{};
  if (!ReadVerifiedRuntimeProof(state, before) ||
      before.proof_epoch != submission.proof_epoch) {
    SetFailure(state, Failure::runtime_proof_mismatch,
               "submission_proof_epoch");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }

  Target first{};
  ++state.target_resolve_calls;
  if (!state.resolve_target(state.target_context, submission, first)) {
    SetFailure(state, Failure::target_unavailable, "target_first");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  RuntimeProof after_first{};
  if (!ReadVerifiedRuntimeProof(state, after_first) ||
      after_first != before) {
    SetFailure(state, Failure::runtime_proof_mismatch,
               "proof_after_target_first");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }

  Target second{};
  ++state.target_resolve_calls;
  if (!state.resolve_target(state.target_context, submission, second)) {
    SetFailure(state, Failure::target_unavailable, "target_second");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  RuntimeProof after_second{};
  if (!ReadVerifiedRuntimeProof(state, after_second) ||
      after_second != before) {
    SetFailure(state, Failure::runtime_proof_mismatch,
               "proof_after_target_second");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  if (!ValidTarget(first, submission, before) ||
      !ValidTarget(second, submission, before)) {
    SetFailure(state, Failure::target_identity_invalid, "target_identity");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  if (first != second) {
    SetFailure(state, Failure::target_sample_drift, "target_double_sample");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }

  auto command = BuildCommand(state, second);
  if (!ValidateCommand(state, command)) {
    SetFailure(state, Failure::final_legality_denied,
               "CAddLawCommand.validator");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  RuntimeProof before_queue{};
  if (!ReadVerifiedRuntimeProof(state, before_queue) ||
      before_queue != before) {
    SetFailure(state, Failure::runtime_proof_mismatch,
               "proof_after_final_legality");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  if (!QueueCommand(state, command)) {
    SetFailure(state, Failure::native_queue_rejected,
               "submit_command_queue");
    return RealmLawNativeSubmitDispositionV1::not_submitted;
  }
  return RealmLawNativeSubmitDispositionV1::submitted;
}

RealmLawNativeBinderOperationsV1 MakeOperations() noexcept {
  RealmLawNativeBinderOperationsV1 operations{};
  operations.read_runtime_proof = &ReadRuntimeProofThunk;
  operations.capture_frame = &CaptureFrameThunk;
  operations.resolve_player = &ResolvePlayerThunk;
  operations.resolve_container = &ResolveContainerThunk;
  operations.read_group = &ReadGroupThunk;
  operations.read_candidate = &ReadCandidateThunk;
  operations.read_title_baseline = &ReadTitleBaselineThunk;
  operations.read_resources = &ReadResourcesThunk;
  operations.submit_enact = &SubmitEnactThunk;
  return operations;
}

} // namespace

bool PrepareRealmLawNativeSharedGlueV1(
    const RealmLawNativeSharedGlueConfigurationV1 &configuration,
    RealmLawNativeSharedGlueStateV1 &state) noexcept {
  if (state.prepared) {
    SetFailure(state, Failure::already_prepared, "state.prepared");
    return false;
  }
  state = {};
  if (!configuration.enabled) {
    SetFailure(state, Failure::configuration_disabled, "configuration.enabled");
    return false;
  }
  if (configuration.admitted_executable_sha256 !=
      kRealmLawNativeSharedGlueV1ExecutableSha256) {
    SetFailure(state, Failure::exact_build_mismatch,
               "admitted_executable_sha256");
    return false;
  }
  constexpr auto maximum_rva =
      ck3_11906::private_law::kCommandManagerRvaV1;
  if (configuration.module_base == 0 ||
      (configuration.module_base & 0xFFFU) != 0 ||
      configuration.module_base >
          (std::numeric_limits<std::uintptr_t>::max)() - maximum_rva) {
    SetFailure(state, Failure::module_base_invalid, "module_base");
    return false;
  }
  if (!ValidDigest(configuration.expected_source_signature_manifest_sha256)) {
    SetFailure(state, Failure::source_signature_invalid,
               "source_signature_manifest_sha256");
    return false;
  }
  if (!SourceOperationsComplete(configuration.source_operations)) {
    SetFailure(state, Failure::source_operations_incomplete,
               "source_operations");
    return false;
  }
  if (configuration.source_operations.submit_enact != nullptr) {
    SetFailure(state, Failure::source_submit_override_forbidden,
               "source_operations.submit_enact");
    return false;
  }
  if (configuration.resolve_target == nullptr) {
    SetFailure(state, Failure::target_resolver_unavailable,
               "resolve_target");
    return false;
  }
  const bool any_offline_call =
      configuration.offline_calls.validate_command != nullptr ||
      configuration.offline_calls.submit_command != nullptr;
  const bool complete_offline_calls =
      configuration.offline_calls.validate_command != nullptr &&
      configuration.offline_calls.submit_command != nullptr;
  if ((!configuration.offline_fixture && any_offline_call) ||
      (configuration.offline_fixture && !complete_offline_calls)) {
    SetFailure(state, Failure::offline_call_contract_invalid,
               "offline_calls");
    return false;
  }

  RuntimeProof first{};
  RuntimeProof second{};
  if (!configuration.source_operations.read_runtime_proof(
          configuration.source_context, first) ||
      !configuration.source_operations.read_runtime_proof(
          configuration.source_context, second)) {
    SetFailure(state, Failure::runtime_proof_unavailable,
               "prepare_runtime_proof");
    return false;
  }
  if (first != second ||
      !SourceProofMatchesConfiguration(first, configuration)) {
    SetFailure(state, Failure::runtime_proof_mismatch,
               "prepare_runtime_proof");
    return false;
  }

  state.offline_fixture = configuration.offline_fixture;
  state.native_submit_enabled = configuration.native_submit_enabled;
  state.module_base = configuration.module_base;
  state.mutation_abi_reader = configuration.mutation_abi_reader;
  state.source_context = configuration.source_context;
  state.source_operations = configuration.source_operations;
  state.target_context = configuration.target_context;
  state.resolve_target = configuration.resolve_target;
  state.offline_call_context = configuration.offline_call_context;
  state.offline_calls = configuration.offline_calls;
  if (!AssignRealmLawNativeDigestV1(
          configuration.expected_source_signature_manifest_sha256,
          state.source_signature_manifest_sha256)) {
    SetFailure(state, Failure::source_signature_invalid,
               "source_signature_manifest_sha256");
    return false;
  }
  state.source_signature_generation = first.signature_generation;
  state.connection_generation = first.connection_generation;
  state.application_main_thread_id = first.application_main_thread_id;
  state.prepared = true;
  state.failure = Failure::none;
  state.abi_failure = AbiFailure::none;
  state.failed_evidence = "";
  if (!VerifyMutationAbi(state)) {
    state.prepared = false;
    return false;
  }
  // A second complete proof makes preparation itself a stable sample.
  if (!VerifyMutationAbi(state)) {
    state.prepared = false;
    return false;
  }
  return true;
}

RealmLawNativeBinderEnvironmentV1 MakeRealmLawNativeSharedGlueEnvironmentV1(
    RealmLawNativeSharedGlueStateV1 &state) noexcept {
  RealmLawNativeBinderEnvironmentV1 environment{};
  if (!state.prepared || state.failure != Failure::none) return environment;
  environment.binding_enabled = true;
  environment.offline_fixture = state.offline_fixture;
  environment.module_base = state.module_base;
  environment.admitted_executable_sha256 =
      kRealmLawNativeSharedGlueV1ExecutableSha256;
  environment.expected_signature_manifest_sha256 =
      kRealmLawNativeSharedGlueV1MutationManifestSha256;
  environment.native_context = &state;
  environment.operations = MakeOperations();
  return environment;
}

std::string_view RealmLawNativeSharedGlueFailureNameV1(
    RealmLawNativeSharedGlueFailureV1 failure) noexcept {
  switch (failure) {
  case Failure::none: return "none";
  case Failure::already_prepared: return "already_prepared";
  case Failure::configuration_disabled: return "configuration_disabled";
  case Failure::exact_build_mismatch: return "exact_build_mismatch";
  case Failure::module_base_invalid: return "module_base_invalid";
  case Failure::source_signature_invalid: return "source_signature_invalid";
  case Failure::source_operations_incomplete:
    return "source_operations_incomplete";
  case Failure::source_submit_override_forbidden:
    return "source_submit_override_forbidden";
  case Failure::target_resolver_unavailable:
    return "target_resolver_unavailable";
  case Failure::offline_call_contract_invalid:
    return "offline_call_contract_invalid";
  case Failure::runtime_proof_unavailable:
    return "runtime_proof_unavailable";
  case Failure::runtime_proof_mismatch: return "runtime_proof_mismatch";
  case Failure::mutation_abi_rejected: return "mutation_abi_rejected";
  case Failure::source_callback_failed: return "source_callback_failed";
  case Failure::native_submit_disabled: return "native_submit_disabled";
  case Failure::submission_contract_invalid:
    return "submission_contract_invalid";
  case Failure::target_unavailable: return "target_unavailable";
  case Failure::target_identity_invalid: return "target_identity_invalid";
  case Failure::target_sample_drift: return "target_sample_drift";
  case Failure::final_legality_denied: return "final_legality_denied";
  case Failure::native_queue_rejected: return "native_queue_rejected";
  }
  return "unknown";
}

} // namespace xar::bridge
