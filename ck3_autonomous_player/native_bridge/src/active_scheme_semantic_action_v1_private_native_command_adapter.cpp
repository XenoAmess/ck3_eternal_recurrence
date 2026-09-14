#include "xar_bridge/active_scheme_semantic_action_v1_private_native_command_adapter.hpp"

#include <algorithm>
#include <limits>

namespace xar::bridge {
namespace {

using CharacterLease =
    ActiveSchemeSemanticActionV1PrivateNativeCharacterLease;
using CommandLease = ActiveSchemeSemanticActionV1PrivateNativeCommandLease;
using ContextLease = ActiveSchemeSemanticActionV1PrivateNativeContextLease;
using InteractionLease =
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease;
using Operations =
    ActiveSchemeSemanticActionV1PrivateNativeCommandOperations;
using RouteLease =
    ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease;
using State = ActiveSchemeSemanticActionV1PrivateNativeCommandState;
using ValidationProof =
    ActiveSchemeSemanticActionV1PrivateNativeValidationProof;

constexpr std::uint32_t kIdentitySlotMask = 0x00FFFFFFU;
constexpr unsigned kIdentityGenerationShift = 24U;

struct InteractionSpec {
  std::string_view scheme_type_key;
  bool murder_starter_required = false;
};

bool ResolveInteractionSpec(std::string_view interaction_key,
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

bool Complete(const Operations &operations) noexcept {
  return operations.read_memory != nullptr &&
         operations.resolve_character != nullptr &&
         operations.resolve_interaction != nullptr &&
         operations.resolve_submit_route != nullptr &&
         operations.construct_context != nullptr &&
         operations.validate_context != nullptr &&
         operations.construct_command != nullptr &&
         operations.submit != nullptr &&
         operations.release_context != nullptr &&
         operations.release_command != nullptr;
}

bool CheckedAddress(std::uintptr_t base, std::uintptr_t rva,
                    std::uintptr_t &output) noexcept {
  if (base == 0 ||
      rva > (std::numeric_limits<std::uintptr_t>::max)() - base) {
    output = 0;
    return false;
  }
  output = base + rva;
  return true;
}

bool VerifyExactImage(
    const ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment
        &binding) noexcept {
  std::array<std::uint8_t, 40> observed{};
  for (const auto &signature :
       kActiveSchemeSemanticActionV1PrivateNativeCommandSignatures) {
    std::uintptr_t address = 0;
    observed.fill(0);
    if (!CheckedAddress(binding.module_base, signature.rva, address) ||
        !binding.operations.read_memory(
            binding.operation_context,
            reinterpret_cast<const void *>(address), observed.data(),
            signature.size) ||
        !std::equal(observed.begin(), observed.begin() + signature.size,
                    signature.bytes.begin())) {
      return false;
    }
  }
  return true;
}

bool FullCharacterId(std::int64_t value, std::uint32_t &output) noexcept {
  if (value <= 0 ||
      static_cast<std::uint64_t>(value) >
          (std::numeric_limits<std::uint32_t>::max)()) {
    output = 0;
    return false;
  }
  output = static_cast<std::uint32_t>(value);
  return (output >> kIdentityGenerationShift) != 0;
}

bool ValidCharacterLease(const CharacterLease &lease, std::uint32_t full_id,
                         std::uint64_t expected_proof_epoch) noexcept {
  return lease.identity_round_trip && lease.native_address != 0 &&
         lease.observed_full_id == full_id &&
         lease.slot_index == (full_id & kIdentitySlotMask) &&
         lease.generation == (full_id >> kIdentityGenerationShift) &&
         lease.generation != 0 && lease.proof_epoch != 0 &&
         (expected_proof_epoch == 0 ||
          lease.proof_epoch == expected_proof_epoch);
}

bool ValidInteractionLease(const InteractionLease &lease,
                           const ActiveSchemeSemanticActionV1PrivateCommand
                               &command,
                           const InteractionSpec &spec,
                           std::uint64_t expected_proof_epoch) noexcept {
  return lease.identity_round_trip && lease.native_address != 0 &&
         lease.interaction_key == command.interaction_key &&
         lease.scheme_type_key == spec.scheme_type_key &&
         lease.stable_key_hash != 0 && lease.definition_generation != 0 &&
         lease.proof_epoch != 0 &&
         (expected_proof_epoch == 0 ||
          lease.proof_epoch == expected_proof_epoch);
}

bool ValidRouteLease(const State &state, const RouteLease &lease,
                     std::uint64_t expected_proof_epoch) noexcept {
  std::uintptr_t expected_submitter = 0;
  return CheckedAddress(
             state.module_base,
             kActiveSchemeSemanticActionV1PrivateSubmitCommandRva,
             expected_submitter) &&
         lease.identity_round_trip && lease.command_manager_address != 0 &&
         lease.command_manager_generation != 0 &&
         lease.submitter_address == expected_submitter &&
         lease.proof_epoch != 0 &&
         (expected_proof_epoch == 0 ||
          lease.proof_epoch == expected_proof_epoch);
}

bool ValidContextLease(const ContextLease &context,
                       const ActiveSchemeSemanticActionV1PrivateCommand
                           &command,
                       const InteractionSpec &spec,
                       const CharacterLease &actor,
                       const CharacterLease &target,
                       const InteractionLease &interaction,
                       std::uint64_t proof_epoch) noexcept {
  if (!context.identity_round_trip || context.native_address == 0 ||
      context.generation == 0 || context.proof_epoch != proof_epoch ||
      context.actor_full_id != actor.observed_full_id ||
      context.target_full_id != target.observed_full_id ||
      context.interaction_stable_key_hash != interaction.stable_key_hash ||
      context.interaction_generation != interaction.definition_generation) {
    return false;
  }
  if (spec.murder_starter_required) {
    return context.starter_options_exclusive &&
           context.starter_option_count == 4 &&
           context.selected_starter_package ==
               command.selected_starter_package &&
           ValidMurderStarter(command.selected_starter_package);
  }
  return !context.starter_options_exclusive &&
         context.starter_option_count == 0 &&
         context.selected_starter_package.empty() &&
         command.selected_starter_package.empty();
}

bool ValidValidationProof(const State &state,
                          const ValidationProof &proof,
                          const ContextLease &context,
                          std::uint64_t proof_epoch) noexcept {
  std::uintptr_t expected_validator = 0;
  return CheckedAddress(
             state.module_base,
             kActiveSchemeSemanticActionV1PrivateValidateContextRva,
             expected_validator) &&
         proof.evaluated && proof.valid &&
         proof.validator_address == expected_validator &&
         proof.context_address == context.native_address &&
         proof.context_generation == context.generation &&
         proof.proof_epoch == proof_epoch;
}

bool ValidCommandLease(const State &state, const CommandLease &native_command,
                       const ContextLease &context,
                       const CharacterLease &actor,
                       const CharacterLease &target,
                       const InteractionLease &interaction,
                       std::uint64_t proof_epoch) noexcept {
  std::uintptr_t expected_constructor = 0;
  std::uintptr_t expected_primary_vtable = 0;
  std::uintptr_t expected_secondary_vtable = 0;
  return CheckedAddress(
             state.module_base,
             kActiveSchemeSemanticActionV1PrivateConstructCommandRva,
             expected_constructor) &&
         CheckedAddress(
             state.module_base,
             kActiveSchemeSemanticActionV1PrivateCommandPrimaryVtableRva,
             expected_primary_vtable) &&
         CheckedAddress(
             state.module_base,
             kActiveSchemeSemanticActionV1PrivateCommandSecondaryVtableRva,
             expected_secondary_vtable) &&
         native_command.identity_round_trip &&
         native_command.native_address != 0 && native_command.generation != 0 &&
         native_command.proof_epoch == proof_epoch &&
         native_command.constructor_address == expected_constructor &&
         native_command.primary_vtable == expected_primary_vtable &&
         native_command.secondary_vtable == expected_secondary_vtable &&
         native_command.copied_context_address != 0 &&
         native_command.copied_context_address != context.native_address &&
         native_command.copied_context_generation == context.generation &&
         native_command.actor_full_id == actor.observed_full_id &&
         native_command.target_full_id == target.observed_full_id &&
         native_command.interaction_stable_key_hash ==
             interaction.stable_key_hash;
}

bool CaptureObservationThunk(
    void *context,
    ActiveSchemeStateV1PrivateObservation &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_capture_observation != nullptr &&
         state.upstream_capture_observation(state.upstream_context, output);
}

bool CapturePreconditionThunk(
    void *context,
    ActiveSchemeSemanticActionV1PrivatePrecondition &output) noexcept {
  auto &state = *static_cast<State *>(context);
  return state.attached && state.upstream_capture_precondition != nullptr &&
         state.upstream_capture_precondition(state.upstream_context, output);
}

bool SubmitThunk(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateCommand &command) noexcept {
  auto &state = *static_cast<State *>(context);
  if (!state.attached || !Complete(state.operations)) return false;

  InteractionSpec spec{};
  std::uint32_t actor_full_id = 0;
  std::uint32_t target_full_id = 0;
  if (!ResolveInteractionSpec(command.interaction_key, spec) ||
      command.scheme_type_key != spec.scheme_type_key ||
      !FullCharacterId(command.actor_character_id, actor_full_id) ||
      command.target_kind != ActiveSchemeStateV1PrivateTargetKind::character ||
      !FullCharacterId(command.target_id, target_full_id) ||
      actor_full_id == target_full_id ||
      (spec.murder_starter_required
           ? !ValidMurderStarter(command.selected_starter_package)
           : !command.selected_starter_package.empty())) {
    return false;
  }

  const auto &operations = state.operations;
  CharacterLease actor{};
  CharacterLease target{};
  InteractionLease interaction{};
  RouteLease route{};
  if (!operations.resolve_character(state.operation_context, actor_full_id,
                                    actor) ||
      !ValidCharacterLease(actor, actor_full_id, 0) ||
      !operations.resolve_character(state.operation_context, target_full_id,
                                    target) ||
      !ValidCharacterLease(target, target_full_id, actor.proof_epoch) ||
      !operations.resolve_interaction(state.operation_context,
                                      command.interaction_key,
                                      interaction) ||
      !ValidInteractionLease(interaction, command, spec,
                             actor.proof_epoch) ||
      !operations.resolve_submit_route(state.operation_context, route) ||
      !ValidRouteLease(state, route, actor.proof_epoch)) {
    return false;
  }
  const auto proof_epoch = actor.proof_epoch;

  ContextLease native_context{};
  if (!operations.construct_context(
          state.operation_context, command, actor, target, interaction,
          native_context)) {
    if (native_context.native_address != 0) {
      operations.release_context(state.operation_context, native_context);
    }
    return false;
  }
  const auto release_context = [&]() noexcept {
    operations.release_context(state.operation_context, native_context);
  };
  if (!ValidContextLease(native_context, command, spec, actor, target,
                         interaction, proof_epoch)) {
    release_context();
    return false;
  }

  ValidationProof validation{};
  if (!operations.validate_context(state.operation_context, native_context,
                                   validation) ||
      !ValidValidationProof(state, validation, native_context, proof_epoch)) {
    release_context();
    return false;
  }

  // Re-resolve every external identity and the command manager immediately
  // before constructing/submitting the command. Nothing is cached in state.
  CharacterLease actor_second{};
  CharacterLease target_second{};
  InteractionLease interaction_second{};
  RouteLease route_second{};
  if (!operations.resolve_character(state.operation_context, actor_full_id,
                                    actor_second) ||
      !operations.resolve_character(state.operation_context, target_full_id,
                                    target_second) ||
      !operations.resolve_interaction(state.operation_context,
                                      command.interaction_key,
                                      interaction_second) ||
      !operations.resolve_submit_route(state.operation_context,
                                       route_second) ||
      !ValidCharacterLease(actor_second, actor_full_id, proof_epoch) ||
      !ValidCharacterLease(target_second, target_full_id, proof_epoch) ||
      !ValidInteractionLease(interaction_second, command, spec, proof_epoch) ||
      !ValidRouteLease(state, route_second, proof_epoch) ||
      actor_second != actor || target_second != target ||
      interaction_second != interaction || route_second != route) {
    release_context();
    return false;
  }

  CommandLease native_command{};
  if (!operations.construct_command(state.operation_context, native_context,
                                    native_command)) {
    if (native_command.native_address != 0) {
      operations.release_command(state.operation_context, native_command);
    }
    release_context();
    return false;
  }
  if (!ValidCommandLease(state, native_command, native_context, actor,
                         target, interaction, proof_epoch)) {
    operations.release_command(state.operation_context, native_command);
    release_context();
    return false;
  }

  // This is the only native submit call in the transaction. No validation or
  // receipt check may submit again; Scheme5 keeps a true result pending until
  // its own fresh active-scheme observation verifies the postcondition.
  const bool submitted = operations.submit(
      state.operation_context, route, native_command,
      kActiveSchemeSemanticActionV1PrivateNativeCommandChannel);
  operations.release_command(state.operation_context, native_command);
  release_context();
  return submitted;
}

} // namespace

bool BindActiveSchemeSemanticActionV1PrivateNativeCommand(
    const ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment &binding,
    ActiveSchemeSemanticActionV1PrivateNativeCommandState &state,
    ActiveSchemeSemanticActionV1PrivateAccess &access,
    ActiveSchemeSemanticActionV1PrivateEnvironment
        &action_environment) noexcept {
  const auto &gate = binding.proof_gate;
  if (!binding.binding_enabled || !binding.exact_build_admitted ||
      binding.admitted_executable_sha256 !=
          kActiveSchemeSemanticActionV1PrivateExecutableSha256 ||
      binding.admitted_game_version !=
          kActiveSchemeSemanticActionV1PrivateNativeCommandGameVersion ||
      binding.module_base == 0 || !Complete(binding.operations) ||
      gate.evidence_revision !=
          kActiveSchemeSemanticActionV1PrivateNativeCommandEvidenceRevision ||
      !gate.stable_interaction_key_lookup_proven ||
      !gate.full_character_identity_generation_proven ||
      !gate.starter_package_encoding_proven ||
      !gate.command_copy_lifetime_proven || state.attached ||
      access.context == &state || access.capture_observation == nullptr ||
      access.capture_precondition == nullptr || access.submit != nullptr ||
      action_environment.character_interaction_route_bound ||
      action_environment.offline_fixture ||
      !VerifyExactImage(binding)) {
    return false;
  }

  state = {};
  state.offline_fixture = binding.offline_fixture;
  state.module_base = binding.module_base;
  state.operation_context = binding.operation_context;
  state.operations = binding.operations;
  state.upstream_context = access.context;
  state.upstream_capture_observation = access.capture_observation;
  state.upstream_capture_precondition = access.capture_precondition;
  state.attached = true;

  access.context = &state;
  access.capture_observation = &CaptureObservationThunk;
  access.capture_precondition = &CapturePreconditionThunk;
  access.submit = &SubmitThunk;

  action_environment = {};
  action_environment.module_base = binding.offline_fixture
                                       ? 0
                                       : binding.module_base;
  action_environment.exact_build_admitted = true;
  action_environment.admitted_executable_sha256 =
      kActiveSchemeSemanticActionV1PrivateExecutableSha256;
  action_environment.character_interaction_route_bound =
      !binding.offline_fixture;
  action_environment.offline_fixture = binding.offline_fixture;
  return true;
}

} // namespace xar::bridge
