#include "xar_bridge/active_scheme_interaction_definition_resolver_v1_private.hpp"

#include <algorithm>
#include <array>
#include <bit>
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
constexpr std::uintptr_t kFallback = 0x7F000000;
constexpr auto kSwayHash =
    std::bit_cast<std::int32_t>(kActiveSchemeSwayInteractionStableHash);
constexpr auto kMurderHash =
    std::bit_cast<std::int32_t>(kActiveSchemeMurderInteractionStableHash);

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "scheme definition resolver fixture failed at line " +
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

template <std::size_t Size>
void Put(std::array<std::uint8_t, Size> &memory, std::size_t offset,
         const void *value, std::size_t value_size) {
  Require(offset <= memory.size() && value_size <= memory.size() - offset);
  std::memcpy(memory.data() + offset, value, value_size);
}

template <typename T, std::size_t Size>
void Put(std::array<std::uint8_t, Size> &memory, std::size_t offset,
         const T &value) {
  Put(memory, offset, &value, sizeof(value));
}

template <std::size_t Size>
bool CopyRegion(const std::array<std::uint8_t, Size> &memory,
                std::uintptr_t address, void *output, std::size_t size) {
  const auto base = reinterpret_cast<std::uintptr_t>(memory.data());
  if (address < base || address - base > memory.size() ||
      size > memory.size() - (address - base)) {
    return false;
  }
  std::memcpy(output, memory.data() + (address - base), size);
  return true;
}

struct Fixture {
  ActiveSchemeStateV1PrivateObservation observation{};
  ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
  std::array<std::uint8_t, 0x78> database{};
  std::array<std::uintptr_t, 2> rows{};
  std::array<std::uint8_t, 0x2A88> sway_definition{};
  std::array<std::uint8_t, 0x2A88> murder_definition{};
  std::array<char, 32> sway_key{};
  std::array<char, 40> murder_key{};
  std::uintptr_t database_slot = 0;
  std::uintptr_t fallback_slot = kFallback;
  int observation_captures = 0;
  int precondition_captures = 0;
  int frame_captures = 0;
  int getter_calls = 0;
  int hash_calls = 0;
  int lookup_calls = 0;
  int character_resolves = 0;
  int route_resolves = 0;
  int native_submits = 0;
  int contexts_released = 0;
  int commands_released = 0;
  bool corrupt_resolver_signature = false;
  bool corrupt_resolver_vtable = false;
  bool corrupt_rtti = false;
  bool getter_mismatch = false;
  bool return_fallback = false;
  bool return_other_definition = false;
  bool frame_drift = false;
  bool ordinal_drift = false;

  Fixture() {
    observation.status = ActiveSchemeStateV1PrivateStatus::available;
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
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::explicitly_unavailable;
    precondition.maximum_success_chance.status =
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::explicitly_unavailable;
    precondition.secrecy.status =
        ActiveSchemeSemanticActionV1PrivatePreviewStatus::explicitly_unavailable;

    SetKey(sway_key, "sway_interaction");
    SetKey(murder_key, "start_murder_interaction");
    InitializeDefinition(sway_definition, 14, kSwayHash, sway_key.data(), 16);
    InitializeDefinition(murder_definition, 27, kMurderHash,
                         murder_key.data(), 24);
    rows = {reinterpret_cast<std::uintptr_t>(sway_definition.data()),
            reinterpret_cast<std::uintptr_t>(murder_definition.data())};
    const auto rows_address = reinterpret_cast<std::uintptr_t>(rows.data());
    const std::int32_t count = 2;
    Put(database, kActiveSchemeInteractionDatabaseRowsOffset, rows_address);
    Put(database, kActiveSchemeInteractionDatabaseCountOffset, count);
    database_slot = reinterpret_cast<std::uintptr_t>(database.data());
  }

  void InitializeDefinition(std::array<std::uint8_t, 0x2A88> &definition,
                            std::int32_t ordinal, std::int32_t hash,
                            const char *key, std::size_t key_size) {
    const auto primary =
        kModuleBase + kActiveSchemeInteractionDefinitionPrimaryVtableRva;
    const auto secondary =
        kModuleBase + kActiveSchemeInteractionDefinitionSecondaryVtableRva;
    Put(definition, 0, primary);
    Put(definition,
        kActiveSchemeInteractionDefinitionSecondarySubobjectOffset,
        secondary);
    Put(definition, kActiveSchemeInteractionDefinitionRuntimeOrdinalOffset,
        ordinal);
    Put(definition, kActiveSchemeInteractionDefinitionStableHashOffset, hash);
    const auto key_pointer = reinterpret_cast<std::uintptr_t>(key);
    Put(definition, kActiveSchemeInteractionDefinitionCanonicalKeyOffset,
        key_pointer);
    Put(definition,
        kActiveSchemeInteractionDefinitionCanonicalKeyOffset + 0x10,
        key_size);
    Put(definition,
        kActiveSchemeInteractionDefinitionCanonicalKeyOffset + 0x18,
        key_size);
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
           precondition.scheme_type_key == "murder" ? "hostile" : "personal");
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
  for (const auto &signature :
       kActiveSchemeSemanticActionV1PrivateNativeCommandSignatures) {
    if (current == kModuleBase + signature.rva && size == signature.size) {
      std::memcpy(output, signature.bytes.data(), size);
      return true;
    }
  }
  for (std::size_t index = 0;
       index < kActiveSchemeInteractionDefinitionResolverV1PrivateSignatures.size();
       ++index) {
    const auto &signature =
        kActiveSchemeInteractionDefinitionResolverV1PrivateSignatures[index];
    if (current == kModuleBase + signature.rva && size == signature.size) {
      std::memcpy(output, signature.bytes.data(), size);
      if (fixture.corrupt_resolver_signature && index == 0) {
        static_cast<std::uint8_t *>(output)[0] ^= 1U;
      }
      return true;
    }
  }
  for (std::size_t index = 0;
       index < kActiveSchemeInteractionDefinitionResolverV1PrivateImagePointerSlots.size();
       ++index) {
    const auto &slot =
        kActiveSchemeInteractionDefinitionResolverV1PrivateImagePointerSlots[index];
    if (current == kModuleBase + slot.slot_rva && size == sizeof(std::uintptr_t)) {
      auto value = kModuleBase + slot.target_rva;
      if (fixture.corrupt_resolver_vtable && index == 0) ++value;
      std::memcpy(output, &value, size);
      return true;
    }
  }
  constexpr std::string_view rtti = ".?AVCCharacterInteraction@@";
  if (current == kModuleBase + kActiveSchemeInteractionDefinitionRttiRva + 0x10 &&
      size == rtti.size() + 1) {
    std::memcpy(output, rtti.data(), rtti.size());
    static_cast<char *>(output)[rtti.size()] = '\0';
    if (fixture.corrupt_rtti) static_cast<char *>(output)[0] = '!';
    return true;
  }
  if (current == kModuleBase + kActiveSchemeInteractionDatabaseSingletonSlotRva &&
      size == sizeof(std::uintptr_t)) {
    std::memcpy(output, &fixture.database_slot, size);
    return true;
  }
  if (current == kModuleBase + kActiveSchemeInteractionLookupFallbackSlotRva &&
      size == sizeof(std::uintptr_t)) {
    std::memcpy(output, &fixture.fallback_slot, size);
    return true;
  }
  if (CopyRegion(fixture.database, current, output, size) ||
      CopyRegion(fixture.sway_definition, current, output, size) ||
      CopyRegion(fixture.murder_definition, current, output, size)) {
    return true;
  }
  const auto rows_base = reinterpret_cast<std::uintptr_t>(fixture.rows.data());
  if (current >= rows_base && current - rows_base <= sizeof(fixture.rows) &&
      size <= sizeof(fixture.rows) - (current - rows_base)) {
    std::memcpy(output,
                reinterpret_cast<const void *>(rows_base + current - rows_base),
                size);
    return true;
  }
  const auto copy_key = [&](const auto &key) noexcept {
    const auto base = reinterpret_cast<std::uintptr_t>(key.data());
    if (current < base || current - base > key.size() ||
        size > key.size() - (current - base)) return false;
    std::memcpy(output, key.data() + (current - base), size);
    return true;
  };
  return copy_key(fixture.sway_key) || copy_key(fixture.murder_key);
}

bool CaptureFrame(
    void *context,
    ActiveSchemeInteractionDefinitionResolverV1PrivateFrame &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_captures;
  output = {true, true, kProofEpoch,
            fixture.precondition.date_raw +
                (fixture.frame_drift && fixture.frame_captures % 2 == 0 ? 1 : 0)};
  return true;
}

bool InvokeGetter(void *context, std::uintptr_t address,
                  std::uintptr_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.getter_calls;
  if (address != kModuleBase +
                     kActiveSchemeInteractionDefinitionDatabaseGetterRva) {
    return false;
  }
  output = fixture.database_slot + (fixture.getter_mismatch ? 1U : 0U);
  return true;
}

bool InvokeHash(void *context, std::uintptr_t address, std::uintptr_t database,
                std::string_view key, std::int32_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.hash_calls;
  if (address != kModuleBase + kActiveSchemeInteractionStableKeyHashRva ||
      database != fixture.database_slot) return false;
  if (key == "sway_interaction") output = kSwayHash;
  else if (key == "start_murder_interaction") output = kMurderHash;
  else return false;
  return true;
}

bool InvokeLookup(void *context, std::uintptr_t address,
                  std::uintptr_t database, std::int32_t hash,
                  std::uintptr_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.lookup_calls;
  if (address != kModuleBase +
                     kActiveSchemeInteractionLoadedLookupReferenceRva ||
      database != fixture.database_slot) return false;
  if (fixture.ordinal_drift && fixture.lookup_calls == 2) {
    const std::int32_t drifted = 15;
    Put(fixture.sway_definition,
        kActiveSchemeInteractionDefinitionRuntimeOrdinalOffset, drifted);
  }
  if (fixture.return_fallback) {
    output = fixture.fallback_slot;
  } else if (fixture.return_other_definition) {
    output = reinterpret_cast<std::uintptr_t>(fixture.murder_definition.data());
  } else if (hash == kSwayHash) {
    output = reinterpret_cast<std::uintptr_t>(fixture.sway_definition.data());
  } else if (hash == kMurderHash) {
    output = reinterpret_cast<std::uintptr_t>(fixture.murder_definition.data());
  } else {
    output = fixture.fallback_slot;
  }
  return true;
}

bool ResolveCharacter(
    void *context, std::uint32_t full_id,
    ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.character_resolves;
  output = {true, 0x20000000U + full_id, full_id,
            full_id & 0x00FFFFFFU, full_id >> 24U, kProofEpoch};
  return true;
}

bool ResolveRoute(
    void *context,
    ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.route_resolves;
  output = {true, 0x41000000U, 14,
            kModuleBase + kActiveSchemeSemanticActionV1PrivateSubmitCommandRva,
            kProofEpoch};
  return true;
}

bool ConstructContext(
    void *, const ActiveSchemeSemanticActionV1PrivateCommand &command,
    const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &actor,
    const ActiveSchemeSemanticActionV1PrivateNativeCharacterLease &target,
    const ActiveSchemeSemanticActionV1PrivateNativeInteractionLease &interaction,
    ActiveSchemeSemanticActionV1PrivateNativeContextLease &output) noexcept {
  output = {};
  output.identity_round_trip = true;
  output.native_address = 0x51000000U;
  output.generation = 21;
  output.proof_epoch = kProofEpoch;
  output.actor_full_id = actor.observed_full_id;
  output.target_full_id = target.observed_full_id;
  output.interaction_stable_key_hash = interaction.stable_key_hash;
  output.interaction_generation = interaction.definition_generation;
  if (command.interaction_key == "start_murder_interaction") {
    output.starter_options_exclusive = true;
    output.starter_option_count = 4;
    output.selected_starter_package = command.selected_starter_package;
  }
  return true;
}

bool ValidateContext(
    void *, const ActiveSchemeSemanticActionV1PrivateNativeContextLease &context,
    ActiveSchemeSemanticActionV1PrivateNativeValidationProof &output) noexcept {
  output = {true, true,
            kModuleBase + kActiveSchemeSemanticActionV1PrivateValidateContextRva,
            context.native_address, context.generation, kProofEpoch};
  return true;
}

bool ConstructCommand(
    void *, const ActiveSchemeSemanticActionV1PrivateNativeContextLease &context,
    ActiveSchemeSemanticActionV1PrivateNativeCommandLease &output) noexcept {
  output = {};
  output.identity_round_trip = true;
  output.native_address = 0x61000000U;
  output.generation = 31;
  output.proof_epoch = kProofEpoch;
  output.constructor_address =
      kModuleBase + kActiveSchemeSemanticActionV1PrivateConstructCommandRva;
  output.primary_vtable =
      kModuleBase + kActiveSchemeSemanticActionV1PrivateCommandPrimaryVtableRva;
  output.secondary_vtable =
      kModuleBase + kActiveSchemeSemanticActionV1PrivateCommandSecondaryVtableRva;
  output.copied_context_address = output.native_address + 0x20;
  output.copied_context_generation = context.generation;
  output.actor_full_id = context.actor_full_id;
  output.target_full_id = context.target_full_id;
  output.interaction_stable_key_hash = context.interaction_stable_key_hash;
  return true;
}

bool SubmitNative(
    void *context,
    const ActiveSchemeSemanticActionV1PrivateNativeSubmitRouteLease &,
    const ActiveSchemeSemanticActionV1PrivateNativeCommandLease &,
    std::uint32_t channel) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.native_submits;
  if (channel != kActiveSchemeSemanticActionV1PrivateNativeCommandChannel)
    return false;
  fixture.ApplyPostcondition();
  return true;
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

ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment CommandBinding(
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
  binding.operations = {&ReadMemory,       &ResolveCharacter, nullptr,
                        &ResolveRoute,     &ConstructContext, &ValidateContext,
                        &ConstructCommand, &SubmitNative,     &ReleaseContext,
                        &ReleaseCommand};
  binding.proof_gate.evidence_revision =
      kActiveSchemeSemanticActionV1PrivateNativeCommandEvidenceRevision;
  binding.proof_gate.full_character_identity_generation_proven = true;
  binding.proof_gate.starter_package_encoding_proven = true;
  binding.proof_gate.command_copy_lifetime_proven = true;
  return binding;
}

ActiveSchemeInteractionDefinitionResolverV1PrivateEnvironment ResolverBinding(
    Fixture &fixture) {
  return {true,
          true,
          kActiveSchemeInteractionDefinitionResolverV1PrivateExecutableSha256,
          kActiveSchemeInteractionDefinitionResolverV1PrivateGameVersion,
          kActiveSchemeInteractionDefinitionResolverV1PrivateEvidenceRevision,
          kModuleBase,
          &fixture,
          &CaptureFrame,
          &InvokeGetter,
          &InvokeHash,
          &InvokeLookup};
}

ActiveSchemeSemanticActionV1PrivateAccess UpstreamAccess(Fixture &fixture) {
  return {&fixture, &CaptureObservation, &CapturePrecondition, nullptr};
}

ActiveSchemeSemanticActionV1PrivateRequest Request(const Fixture &fixture) {
  return {"scheme7-fixture-1",
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
  ActiveSchemeInteractionDefinitionResolverV1PrivateState resolver_state{};
  ActiveSchemeSemanticActionV1PrivateNativeCommandState command_state{};
  ActiveSchemeSemanticActionV1PrivateAccess access{};
  ActiveSchemeSemanticActionV1PrivateEnvironment action_environment{};
};

void Bind(Fixture &fixture, BoundFixture &bound) {
  auto command = CommandBinding(fixture);
  Require(BindActiveSchemeInteractionDefinitionResolverV1Private(
      ResolverBinding(fixture), bound.resolver_state, command));
  bound.access = UpstreamAccess(fixture);
  Require(BindActiveSchemeSemanticActionV1PrivateNativeCommand(
      command, bound.command_state, bound.access, bound.action_environment));
}

ActiveSchemeSemanticActionV1PrivateAck Execute(Fixture &fixture,
                                               BoundFixture &bound) {
  ActiveSchemeSemanticActionV1PrivateAck ack{};
  ExecuteActiveSchemeSemanticActionV1Private(
      bound.action_environment, bound.access, Request(fixture), ack);
  return ack;
}

void TestSwayAndMurderEndToEnd() {
  for (const bool murder : {false, true}) {
    Fixture fixture{};
    if (murder) fixture.MakeMurder();
    BoundFixture bound{};
    Bind(fixture, bound);
    const auto ack = Execute(fixture, bound);
    Require(ack.status == ActiveSchemeSemanticActionV1PrivateAckStatus::
                              submitted_verification_pending);
    Require(ack.verification_pending && ack.submit_call_count == 1);
    Require(fixture.native_submits == 1);
    Require(fixture.getter_calls == 4 && fixture.hash_calls == 4 &&
            fixture.lookup_calls == 4 && fixture.frame_captures == 4);
    Require(fixture.contexts_released == 1 && fixture.commands_released == 1);
    ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
    Require(VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
                bound.access, ack, receipt) ==
            ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied);
    Require(receipt.postcondition_verified && fixture.native_submits == 1);
  }
}

void TestExactImageBindingGates() {
  for (const int mode : {0, 1, 2}) {
    Fixture fixture{};
    fixture.corrupt_resolver_signature = mode == 0;
    fixture.corrupt_resolver_vtable = mode == 1;
    fixture.corrupt_rtti = mode == 2;
    auto command = CommandBinding(fixture);
    ActiveSchemeInteractionDefinitionResolverV1PrivateState state{};
    Require(!BindActiveSchemeInteractionDefinitionResolverV1Private(
        ResolverBinding(fixture), state, command));
  }
}

void RequireTypedRedWithoutNativeSubmit(Fixture &fixture) {
  BoundFixture bound{};
  Bind(fixture, bound);
  const auto ack = Execute(fixture, bound);
  Require(ack.status ==
          ActiveSchemeSemanticActionV1PrivateAckStatus::rejected_before_submit);
  Require(ack.failure ==
          ActiveSchemeSemanticActionV1PrivateFailure::submit_rejected);
  Require(ack.submit_attempted && ack.submit_call_count == 1);
  Require(fixture.native_submits == 0);
}

void TestLifecycleAndCollisionGates() {
  {
    Fixture fixture{};
    fixture.getter_mismatch = true;
    RequireTypedRedWithoutNativeSubmit(fixture);
  }
  {
    Fixture fixture{};
    fixture.return_fallback = true;
    RequireTypedRedWithoutNativeSubmit(fixture);
  }
  {
    Fixture fixture{};
    fixture.return_other_definition = true;
    RequireTypedRedWithoutNativeSubmit(fixture);
  }
  {
    Fixture fixture{};
    fixture.frame_drift = true;
    RequireTypedRedWithoutNativeSubmit(fixture);
  }
  {
    Fixture fixture{};
    fixture.ordinal_drift = true;
    RequireTypedRedWithoutNativeSubmit(fixture);
  }
  {
    Fixture fixture{};
    SetKey(fixture.murder_key, "sway_interaction");
    fixture.InitializeDefinition(fixture.murder_definition, 27, kSwayHash,
                                 fixture.murder_key.data(), 16);
    RequireTypedRedWithoutNativeSubmit(fixture);
  }
}

void TestUnknownKeyFailsClosed() {
  Fixture fixture{};
  auto command = CommandBinding(fixture);
  ActiveSchemeInteractionDefinitionResolverV1PrivateState state{};
  Require(BindActiveSchemeInteractionDefinitionResolverV1Private(
      ResolverBinding(fixture), state, command));
  ActiveSchemeSemanticActionV1PrivateNativeInteractionLease lease{};
  Require(!command.operations.resolve_interaction(command.operation_context,
                                                  "invented_interaction",
                                                  lease));
  Require(lease.native_address == 0 && fixture.lookup_calls == 0);
}

} // namespace

int main() {
  try {
    TestSwayAndMurderEndToEnd();
    TestExactImageBindingGates();
    TestLifecycleAndCollisionGates();
    TestUnknownKeyFailsClosed();
    std::cout << "active scheme private definition resolver: GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
