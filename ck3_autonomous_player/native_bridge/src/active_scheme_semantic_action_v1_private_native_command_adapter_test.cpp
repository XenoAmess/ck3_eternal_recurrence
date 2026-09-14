#include "xar_bridge/active_scheme_semantic_action_v1_private_native_command_adapter.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string>

namespace {

using namespace xar::bridge;

constexpr std::uintptr_t kModuleBase = 0x10000000;
constexpr std::uint32_t kActor = 0x0100002A;
constexpr std::uint32_t kTarget = 0x01000039;
constexpr std::uint64_t kProofEpoch = 900;
constexpr std::int32_t kSwayHash = 0x22334455;
constexpr std::int32_t kMurderHash = 0x33445566;

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "scheme native command adapter fixture failed at line " +
        std::to_string(location.line()));
  }
}

template <std::size_t Size>
void SetKey(std::array<char, Size> &output, std::string_view value) noexcept {
  output.fill('\0');
  if (value.size() < output.size()) {
    std::copy(value.begin(), value.end(), output.begin());
  }
}

struct Fixture {
  ActiveSchemeStateV1PrivateObservation observation{};
  ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
  int observation_captures = 0;
  int precondition_captures = 0;
  int character_resolves = 0;
  int interaction_resolves = 0;
  int route_resolves = 0;
  int contexts_constructed = 0;
  int validations = 0;
  int commands_constructed = 0;
  int native_submits = 0;
  int contexts_released = 0;
  int commands_released = 0;
  bool corrupt_signature = false;
  bool invalid_character_generation = false;
  bool drift_character_second_pass = false;
  bool drift_interaction_second_pass = false;
  bool drift_route_second_pass = false;
  bool validation_result = true;
  bool corrupt_command_vtable = false;
  bool native_submit_result = true;

  Fixture() {
    observation.status = ActiveSchemeStateV1PrivateStatus::available;
    observation.unavailable_reason = ActiveSchemeStateV1PrivateFailure::none;
    observation.capture_epoch = 17;
    observation.date_raw = 53'175'816;
    observation.played_character_id = kActor;
    observation.container_generation = 71;

    precondition.available = true;
    precondition.paused = true;
    precondition.capture_epoch = observation.capture_epoch;
    precondition.date_raw = observation.date_raw;
    precondition.actor_character_id = kActor;
    precondition.target_kind = ActiveSchemeStateV1PrivateTargetKind::character;
    precondition.target_id = kTarget;
    precondition.interaction_key = "sway_interaction";
    precondition.scheme_type_key = "sway";
    precondition.shown_evaluated = true;
    precondition.shown = true;
    precondition.validity_evaluated = true;
    precondition.valid = true;
    precondition.can_start_scheme_evaluated = true;
    precondition.can_start_scheme = true;
    precondition.success_chance.status =
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::
            explicitly_unavailable;
    precondition.maximum_success_chance.status =
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::
            explicitly_unavailable;
    precondition.secrecy.status =
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::
            explicitly_unavailable;
  }

  void MakeMurder() {
    precondition.interaction_key = "start_murder_interaction";
    precondition.scheme_type_key = "murder";
    precondition.starter_options_evaluated = true;
    precondition.starter_options_exclusive = true;
    precondition.starter_option_count = 4;
    precondition.selected_starter_package = "agent_focus_speed";
    precondition.success_chance = {
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::available, 61};
    precondition.maximum_success_chance = {
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::available, 95};
    precondition.secrecy = {
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::available, 73};
  }

  std::int32_t InteractionHash() const noexcept {
    return precondition.interaction_key == "sway_interaction" ? kSwayHash
                                                               : kMurderHash;
  }

  void ApplyPostcondition() noexcept {
    ++observation.capture_epoch;
    ++observation.container_generation;
    ++observation.date_raw;
    auto &row = observation.rows[observation.row_count++];
    row.scheme_instance_id = 0x0000000200000042ULL;
    row.scheme_instance_generation = 8;
    row.owner_character_id = kActor;
    SetKey(row.scheme_type_key, precondition.scheme_type_key);
    SetKey(row.category_key,
           precondition.scheme_type_key == "murder" ? "hostile" :
                                                       "personal");
    row.target_kind = ActiveSchemeStateV1PrivateTargetKind::character;
    row.target_id = kTarget;
    row.is_basic = precondition.scheme_type_key == "sway";
    row.is_secret = precondition.scheme_type_key == "murder";
    row.progress = {ActiveSchemeStateV1PrivateValueStatus::available, 0};
    row.progress_goal = {ActiveSchemeStateV1PrivateValueStatus::available, 10};
  }
};

bool CaptureObservation(void *context,
                        ActiveSchemeStateV1PrivateObservation &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.observation_captures;
  output = fixture.observation;
  return true;
}

bool CapturePrecondition(
    void *context,
    ActiveSchemeSemanticActionV1PrivatePrecondition &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.precondition_captures;
  output = fixture.precondition;
  return true;
}

bool ReadMemory(void *context, const void *address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto current = reinterpret_cast<std::uintptr_t>(address);
  for (std::size_t index = 0;
       index <
       kActiveSchemeSemanticActionV1PrivateNativeCommandSignatures.size();
       ++index) {
    const auto &signature =
        kActiveSchemeSemanticActionV1PrivateNativeCommandSignatures[index];
    if (current == kModuleBase + signature.rva && size == signature.size) {
      std::memcpy(output, signature.bytes.data(), size);
      if (fixture.corrupt_signature && index == 0) {
        static_cast<std::uint8_t *>(output)[0] ^= 0x01U;
      }
      return true;
    }
  }
  return false;
}

bool ResolveCharacter(
    void *context, std::uint32_t full_id,
    ActiveSchemeSemanticActionV1PrivateNativeCharacterLease
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.character_resolves;
  output = {};
  output.identity_round_trip = true;
  output.native_address = 0x20000000U + full_id;
  output.observed_full_id = full_id;
  output.slot_index = full_id & 0x00FFFFFFU;
  output.generation = full_id >> 24U;
  output.proof_epoch = kProofEpoch;
  if (fixture.invalid_character_generation) ++output.generation;
  if (fixture.drift_character_second_pass &&
      fixture.character_resolves == 3) {
    ++output.native_address;
  }
  return true;
}

bool ResolveInteraction(
    void *context, std::string_view interaction_key,
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.interaction_resolves;
  output = {};
  output.identity_round_trip = true;
  output.native_address = interaction_key == "sway_interaction" ? 0x31000000U
                                                                  : 0x32000000U;
  output.interaction_key.assign(interaction_key);
  output.scheme_type_key = interaction_key == "sway_interaction" ? "sway"
                                                                  : "murder";
  output.stable_key_hash = fixture.InteractionHash();
  output.definition_generation = 12;
  output.proof_epoch = kProofEpoch;
  if (fixture.drift_interaction_second_pass &&
      fixture.interaction_resolves == 2) {
    ++output.definition_generation;
  }
  return true;
}

bool ResolveSubmitRoute(
    void *context,
    ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.route_resolves;
  output = {};
  output.identity_round_trip = true;
  output.command_manager_address = 0x41000000U;
  output.command_manager_generation = 14;
  output.submitter_address =
      kModuleBase + kActiveSchemeSemanticActionV1PrivateSubmitCommandRva;
  output.proof_epoch = kProofEpoch;
  if (fixture.drift_route_second_pass && fixture.route_resolves == 2) {
    ++output.command_manager_generation;
  }
  return true;
}

bool ConstructContext(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateCommand &semantic_command,
    const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &actor,
    const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &target,
    const ActiveSchemeSemanticActionV1PrivateNativeInteractionLease
        &interaction,
    ActiveSchemeSemanticActionV1PrivateNativeContextLease &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.contexts_constructed;
  output = {};
  output.identity_round_trip = true;
  output.native_address = 0x51000000U;
  output.generation = 21;
  output.proof_epoch = kProofEpoch;
  output.actor_full_id = actor.observed_full_id;
  output.target_full_id = target.observed_full_id;
  output.interaction_stable_key_hash = interaction.stable_key_hash;
  output.interaction_generation = interaction.definition_generation;
  if (semantic_command.interaction_key == "start_murder_interaction") {
    output.starter_options_exclusive = true;
    output.starter_option_count = 4;
    output.selected_starter_package =
        semantic_command.selected_starter_package;
  }
  return true;
}

bool ValidateContext(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease
        &native_context,
    ActiveSchemeSemanticActionV1PrivateNativeValidationProof
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.validations;
  output = {};
  output.evaluated = true;
  output.valid = fixture.validation_result;
  output.validator_address =
      kModuleBase + kActiveSchemeSemanticActionV1PrivateValidateContextRva;
  output.context_address = native_context.native_address;
  output.context_generation = native_context.generation;
  output.proof_epoch = kProofEpoch;
  return true;
}

bool ConstructCommand(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease
        &native_context,
    ActiveSchemeSemanticActionV1PrivateNativeCommandLease &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.commands_constructed;
  output = {};
  output.identity_round_trip = true;
  output.native_address = 0x61000000U;
  output.generation = 31;
  output.proof_epoch = kProofEpoch;
  output.constructor_address =
      kModuleBase + kActiveSchemeSemanticActionV1PrivateConstructCommandRva;
  output.primary_vtable = kModuleBase +
                          kActiveSchemeSemanticActionV1PrivateCommandPrimaryVtableRva;
  output.secondary_vtable =
      kModuleBase +
      kActiveSchemeSemanticActionV1PrivateCommandSecondaryVtableRva;
  if (fixture.corrupt_command_vtable) ++output.secondary_vtable;
  output.copied_context_address = output.native_address + 0x20;
  output.copied_context_generation = native_context.generation;
  output.actor_full_id = native_context.actor_full_id;
  output.target_full_id = native_context.target_full_id;
  output.interaction_stable_key_hash =
      native_context.interaction_stable_key_hash;
  return true;
}

bool SubmitNative(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease &,
    const ActiveSchemeSemanticActionV1PrivateNativeCommandLease &,
    std::uint32_t channel_flags) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.native_submits;
  if (channel_flags !=
      kActiveSchemeSemanticActionV1PrivateNativeCommandChannel) {
    return false;
  }
  if (fixture.native_submit_result) fixture.ApplyPostcondition();
  return fixture.native_submit_result;
}

void ReleaseContext(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeContextLease &) noexcept {
  ++static_cast<Fixture *>(context)->contexts_released;
}

void ReleaseCommand(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeCommandLease &) noexcept {
  ++static_cast<Fixture *>(context)->commands_released;
}

ActiveSchemeSemanticActionV1PrivateNativeCommandOperations Operations() {
  return {&ReadMemory,        &ResolveCharacter, &ResolveInteraction,
          &ResolveSubmitRoute, &ConstructContext, &ValidateContext,
          &ConstructCommand, &SubmitNative,      &ReleaseContext,
          &ReleaseCommand};
}

ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment Binding(
    Fixture &fixture) {
  ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment binding{};
  binding.binding_enabled = true;
  binding.exact_build_admitted = true;
  binding.admitted_executable_sha256 =
      kActiveSchemeSemanticActionV1PrivateExecutableSha256;
  binding.admitted_game_version =
      kActiveSchemeSemanticActionV1PrivateNativeCommandGameVersion;
  binding.offline_fixture = true;
  binding.module_base = kModuleBase;
  binding.operation_context = &fixture;
  binding.operations = Operations();
  binding.proof_gate.evidence_revision =
      kActiveSchemeSemanticActionV1PrivateNativeCommandEvidenceRevision;
  binding.proof_gate.stable_interaction_key_lookup_proven = true;
  binding.proof_gate.full_character_identity_generation_proven = true;
  binding.proof_gate.starter_package_encoding_proven = true;
  binding.proof_gate.command_copy_lifetime_proven = true;
  return binding;
}

ActiveSchemeSemanticActionV1PrivateAccess UpstreamAccess(Fixture &fixture) {
  return {&fixture, &CaptureObservation, &CapturePrecondition, nullptr};
}

ActiveSchemeSemanticActionV1PrivateRequest Request(const Fixture &fixture) {
  return {"scheme6-fixture-1",
          fixture.precondition.interaction_key,
          fixture.precondition.actor_character_id,
          fixture.precondition.target_kind,
          fixture.precondition.target_id,
          fixture.observation.capture_epoch,
          fixture.observation.container_generation,
          fixture.observation.date_raw,
          fixture.precondition.selected_starter_package};
}

struct BoundFixture {
  ActiveSchemeSemanticActionV1PrivateNativeCommandState state{};
  ActiveSchemeSemanticActionV1PrivateAccess access{};
  ActiveSchemeSemanticActionV1PrivateEnvironment action_environment{};
};

void Bind(Fixture &fixture, BoundFixture &bound) {
  bound.access = UpstreamAccess(fixture);
  Require(BindActiveSchemeSemanticActionV1PrivateNativeCommand(
      Binding(fixture), bound.state, bound.access,
      bound.action_environment));
}

ActiveSchemeSemanticActionV1PrivateAck Execute(Fixture &fixture,
                                               BoundFixture &bound) {
  ActiveSchemeSemanticActionV1PrivateAck ack{};
  const auto request = Request(fixture);
  ExecuteActiveSchemeSemanticActionV1Private(
      bound.action_environment, bound.access, request, ack);
  return ack;
}

void TestSwayAndMurderStayPendingUntilFreshReceipt() {
  for (const bool murder : {false, true}) {
    Fixture fixture{};
    if (murder) fixture.MakeMurder();
    BoundFixture bound{};
    Bind(fixture, bound);
    const auto ack = Execute(fixture, bound);
    Require(ack.status ==
            ActiveSchemeSemanticActionV1PrivateAckStatus::
                submitted_verification_pending);
    Require(ack.verification_pending);
    Require(ack.submit_call_count == 1 && fixture.native_submits == 1);
    Require(fixture.character_resolves == 4);
    Require(fixture.interaction_resolves == 2);
    Require(fixture.route_resolves == 2);
    Require(fixture.contexts_constructed == 1 && fixture.validations == 1 &&
            fixture.commands_constructed == 1);
    Require(fixture.contexts_released == 1 && fixture.commands_released == 1);

    ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
    Require(VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
                bound.access, ack, receipt) ==
            ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied);
    Require(receipt.postcondition_verified);
    Require(fixture.native_submits == 1);
  }
}

void TestExactImageAndProofBindingGates() {
  {
    Fixture fixture{};
    fixture.corrupt_signature = true;
    auto binding = Binding(fixture);
    auto access = UpstreamAccess(fixture);
    ActiveSchemeSemanticActionV1PrivateNativeCommandState state{};
    ActiveSchemeSemanticActionV1PrivateEnvironment environment{};
    Require(!BindActiveSchemeSemanticActionV1PrivateNativeCommand(
        binding, state, access, environment));
  }
  {
    Fixture fixture{};
    auto binding = Binding(fixture);
    binding.admitted_game_version = "1.19.0.5";
    auto access = UpstreamAccess(fixture);
    ActiveSchemeSemanticActionV1PrivateNativeCommandState state{};
    ActiveSchemeSemanticActionV1PrivateEnvironment environment{};
    Require(!BindActiveSchemeSemanticActionV1PrivateNativeCommand(
        binding, state, access, environment));
  }
  {
    Fixture fixture{};
    auto binding = Binding(fixture);
    binding.proof_gate.starter_package_encoding_proven = false;
    auto access = UpstreamAccess(fixture);
    ActiveSchemeSemanticActionV1PrivateNativeCommandState state{};
    ActiveSchemeSemanticActionV1PrivateEnvironment environment{};
    Require(!BindActiveSchemeSemanticActionV1PrivateNativeCommand(
        binding, state, access, environment));
  }
  {
    Fixture fixture{};
    auto binding = Binding(fixture);
    binding.operations.resolve_interaction = nullptr;
    auto access = UpstreamAccess(fixture);
    ActiveSchemeSemanticActionV1PrivateNativeCommandState state{};
    ActiveSchemeSemanticActionV1PrivateEnvironment environment{};
    Require(!BindActiveSchemeSemanticActionV1PrivateNativeCommand(
        binding, state, access, environment));
  }
}

void RequireRejectedWithoutNativeSubmit(Fixture &fixture) {
  BoundFixture bound{};
  Bind(fixture, bound);
  const auto ack = Execute(fixture, bound);
  Require(ack.status ==
          ActiveSchemeSemanticActionV1PrivateAckStatus::
              rejected_before_submit);
  Require(ack.failure ==
          ActiveSchemeSemanticActionV1PrivateFailure::submit_rejected);
  Require(ack.submit_attempted && ack.submit_call_count == 1);
  Require(fixture.native_submits == 0);
}

void TestIdentityGenerationAndProofGates() {
  {
    Fixture fixture{};
    fixture.invalid_character_generation = true;
    RequireRejectedWithoutNativeSubmit(fixture);
    Require(fixture.contexts_constructed == 0);
  }
  {
    Fixture fixture{};
    fixture.drift_character_second_pass = true;
    RequireRejectedWithoutNativeSubmit(fixture);
    Require(fixture.contexts_released == 1);
  }
  {
    Fixture fixture{};
    fixture.drift_interaction_second_pass = true;
    RequireRejectedWithoutNativeSubmit(fixture);
    Require(fixture.contexts_released == 1);
  }
  {
    Fixture fixture{};
    fixture.drift_route_second_pass = true;
    RequireRejectedWithoutNativeSubmit(fixture);
    Require(fixture.contexts_released == 1);
  }
  {
    Fixture fixture{};
    fixture.validation_result = false;
    RequireRejectedWithoutNativeSubmit(fixture);
    Require(fixture.commands_constructed == 0);
    Require(fixture.contexts_released == 1);
  }
  {
    Fixture fixture{};
    fixture.corrupt_command_vtable = true;
    RequireRejectedWithoutNativeSubmit(fixture);
    Require(fixture.commands_released == 1);
    Require(fixture.contexts_released == 1);
  }
}

void TestNativeSubmitFailureIsCalledOnceAndNotRetried() {
  Fixture fixture{};
  fixture.native_submit_result = false;
  BoundFixture bound{};
  Bind(fixture, bound);
  const auto ack = Execute(fixture, bound);
  Require(ack.status ==
          ActiveSchemeSemanticActionV1PrivateAckStatus::
              rejected_before_submit);
  Require(ack.failure ==
          ActiveSchemeSemanticActionV1PrivateFailure::submit_rejected);
  Require(ack.submit_call_count == 1);
  Require(fixture.native_submits == 1);
  Require(fixture.commands_released == 1 && fixture.contexts_released == 1);

  ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
  Require(VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
              bound.access, ack, receipt) ==
          ActiveSchemeSemanticActionV1PrivateReceiptStatus::rejected);
  Require(fixture.native_submits == 1);
}

} // namespace

int main() {
  try {
    TestSwayAndMurderStayPendingUntilFreshReceipt();
    TestExactImageAndProofBindingGates();
    TestIdentityGenerationAndProofGates();
    TestNativeSubmitFailureIsCalledOnceAndNotRetried();
    std::cout << "active scheme private native command adapter: GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
