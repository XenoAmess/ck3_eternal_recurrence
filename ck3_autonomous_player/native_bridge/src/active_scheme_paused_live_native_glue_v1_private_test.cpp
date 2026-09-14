#include "active_scheme_paused_live_native_glue_v1_private.hpp"

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
  int source_frame_captures = 0;
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
  bool source_paused = true;
  bool stale_postcondition = false;

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
    if (precondition.scheme_type_key == "murder") {
      row.success_chance = {
          ActiveSchemeStateV1PrivateValueStatus::available, 61};
      row.maximum_success_chance = {
          ActiveSchemeStateV1PrivateValueStatus::available, 95};
      row.secrecy = {ActiveSchemeStateV1PrivateValueStatus::available, 73};
      row.opportunity_charges = {
          ActiveSchemeStateV1PrivateValueStatus::available, 2};
      row.breaches = {ActiveSchemeStateV1PrivateValueStatus::available, 0};
      row.maximum_breaches = {
          ActiveSchemeStateV1PrivateValueStatus::available, 5};
      row.phases_remaining_until_opportunity = {
          ActiveSchemeStateV1PrivateValueStatus::available, 1};
    }
  }
};

bool CaptureSourceFrame(
    void *context, ActiveSchemeStateV1PrivateSourceFrame &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.source_frame_captures;
  output = {fixture.observation.capture_epoch, fixture.observation.date_raw,
            fixture.observation.played_character_id, fixture.source_paused};
  return true;
}

bool ResolveSourceRoot(
    void *, std::int64_t,
    ActiveSchemeStateV1PrivateSourceRoot &output) noexcept {
  output = {true, 0x71000000U, 0x71000000U, 41};
  return true;
}

bool ResolveSourceContainer(
    void *context, const ActiveSchemeStateV1PrivateSourceRoot &,
    std::int64_t played_character_id,
    ActiveSchemeStateV1PrivateSourceContainer &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  output = {true,
            0x72000000U,
            0x72000000U,
            fixture.observation.container_generation,
            played_character_id,
            fixture.observation.row_count};
  return true;
}

bool ReadSourceRow(
    void *context, const ActiveSchemeStateV1PrivateSourceRoot &,
    const ActiveSchemeStateV1PrivateSourceContainer &, std::size_t index,
    ActiveSchemeStateV1PrivateCapturedRow &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  if (index >= fixture.observation.row_count) return false;
  const auto &row = fixture.observation.rows[index];
  output = {};
  output.scheme_identity_round_trip = true;
  output.scheme_instance_id = row.scheme_instance_id;
  output.scheme_instance_generation = row.scheme_instance_generation;
  output.owner_character_id = row.owner_character_id;
  output.scheme_type_key = row.scheme_type_key;
  output.category_key = row.category_key;
  output.target_identity_round_trip = true;
  output.target_kind = row.target_kind;
  output.target_id = row.target_id;
  output.definition_flags_verified = true;
  output.is_basic = row.is_basic;
  output.is_secret = row.is_secret;
  output.is_exposed = row.is_exposed;
  output.is_frozen = row.is_frozen;
  output.progress = row.progress;
  output.progress_goal = row.progress_goal;
  output.success_chance = row.success_chance;
  output.maximum_success_chance = row.maximum_success_chance;
  output.secrecy = row.secrecy;
  output.opportunity_charges = row.opportunity_charges;
  output.breaches = row.breaches;
  output.maximum_breaches = row.maximum_breaches;
  output.phases_remaining_until_opportunity =
      row.phases_remaining_until_opportunity;
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

bool CaptureDefinitionFrame(
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
  if (fixture.stale_postcondition) --fixture.observation.capture_epoch;
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
          &CaptureDefinitionFrame,
          &InvokeGetter,
          &InvokeHash,
          &InvokeLookup};
}

ActiveSchemeStateV1PrivateSourceAccess SourceAccess(Fixture &fixture) {
  return {true,
          kActiveSchemeStateV1PrivateObserverExecutableSha256,
          0,
          0,
          &fixture,
          &CaptureSourceFrame,
          &ResolveSourceRoot,
          &ResolveSourceContainer,
          &ReadSourceRow};
}

ActiveSchemePausedLiveNativeGlueV1PrivateEnvironment GlueEnvironment(
    Fixture &fixture) {
  return {true,
          SourceAccess(fixture),
          &fixture,
          &CapturePrecondition,
          CommandBinding(fixture),
          ResolverBinding(fixture)};
}

ActiveSchemeSemanticActionV1PrivateRequest Request(const Fixture &fixture) {
  return {"scheme9-fixture-1",
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
  ActiveSchemePausedLiveNativeGlueV1PrivateState state{};
  ActiveSchemePausedLiveNativeGlueV1PrivateReadiness readiness{};
};

void Bind(Fixture &fixture, BoundFixture &bound) {
  Require(BindActiveSchemePausedLiveNativeGlueV1Private(
      GlueEnvironment(fixture), bound.state, bound.readiness));
  Require(bound.readiness.candidate_core_ready &&
          bound.readiness.failure ==
              ActiveSchemePausedLiveNativeGlueV1PrivateFailure::none);
}

ActiveSchemeSemanticActionV1PrivateAck Execute(Fixture &fixture,
                                               BoundFixture &bound) {
  ActiveSchemeSemanticActionV1PrivateAck ack{};
  ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure{};
  ExecuteActiveSchemePausedLiveNativeGlueV1Private(
      bound.state, {42, 42}, Request(fixture), ack, failure);
  Require((ack.status == ActiveSchemeSemanticActionV1PrivateAckStatus::
                             submitted_verification_pending) ==
          (failure == ActiveSchemePausedLiveNativeGlueV1PrivateFailure::none));
  return ack;
}

void TestSwayAndMurderEndToEnd() {
  for (const bool murder : {false, true}) {
    Fixture fixture{};
    if (murder) fixture.MakeMurder();
    BoundFixture bound{};
    Bind(fixture, bound);
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure{};
    ActiveSchemeStateV1PrivateObservation snapshot{};
    Require(CaptureActiveSchemePausedLiveSnapshotV1Private(
        bound.state, {42, 42}, snapshot, failure));
    Require(snapshot.status == ActiveSchemeStateV1PrivateStatus::available &&
            snapshot.capture_epoch == fixture.observation.capture_epoch);
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease definition{};
    Require(ResolveActiveSchemePausedLiveDefinitionV1Private(
        bound.state, {42, 42}, fixture.precondition.interaction_key,
        definition, failure));
    Require(definition.interaction_key ==
            fixture.precondition.interaction_key);
    ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
    Require(CaptureActiveSchemePausedLivePreconditionV1Private(
        bound.state, {42, 42}, precondition, failure));
    Require(precondition == fixture.precondition);
    const auto ack = Execute(fixture, bound);
    Require(ack.status == ActiveSchemeSemanticActionV1PrivateAckStatus::
                              submitted_verification_pending);
    Require(ack.verification_pending && ack.submit_call_count == 1);
    Require(fixture.native_submits == 1);
    Require(fixture.getter_calls == 6 && fixture.hash_calls == 6 &&
            fixture.lookup_calls == 6 && fixture.frame_captures == 6);
    Require(fixture.contexts_released == 1 && fixture.commands_released == 1);
    ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
    Require(VerifyActiveSchemePausedLiveNativeGlueReceiptV1Private(
                bound.state, {42, 42}, ack, receipt, failure) ==
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
    ActiveSchemePausedLiveNativeGlueV1PrivateState state{};
    ActiveSchemePausedLiveNativeGlueV1PrivateReadiness readiness{};
    Require(!BindActiveSchemePausedLiveNativeGlueV1Private(
        GlueEnvironment(fixture), state, readiness));
    Require(readiness.failure ==
            ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                definition_binding_rejected);
  }
  {
    Fixture fixture{};
    auto environment = GlueEnvironment(fixture);
    environment.capture_precondition = nullptr;
    ActiveSchemePausedLiveNativeGlueV1PrivateState state{};
    ActiveSchemePausedLiveNativeGlueV1PrivateReadiness readiness{};
    Require(!BindActiveSchemePausedLiveNativeGlueV1Private(
        environment, state, readiness));
    Require(readiness.failure ==
            ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                precondition_access_unavailable);
  }
  {
    Fixture fixture{};
    auto environment = GlueEnvironment(fixture);
    environment.source_access.read_row = nullptr;
    ActiveSchemePausedLiveNativeGlueV1PrivateState state{};
    ActiveSchemePausedLiveNativeGlueV1PrivateReadiness readiness{};
    Require(!BindActiveSchemePausedLiveNativeGlueV1Private(
        environment, state, readiness));
    Require(readiness.failure ==
            ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                source_access_unavailable);
  }
}

void TestExecutionOwnershipGates() {
  Fixture fixture{};
  BoundFixture bound{};
  Bind(fixture, bound);
  ActiveSchemeStateV1PrivateObservation observation{};
  ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure{};
  Require(!CaptureActiveSchemePausedLiveSnapshotV1Private(
      bound.state, {41, 42}, observation, failure));
  Require(failure == ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                         not_application_main_thread);
  bound.state.execution_active = true;
  Require(!CaptureActiveSchemePausedLiveSnapshotV1Private(
      bound.state, {42, 42}, observation, failure));
  Require(failure == ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                         reentrant_execution);
  bound.state.execution_active = false;
  Require(fixture.native_submits == 0);
}

void TestStageTypedRed() {
  {
    Fixture fixture{};
    BoundFixture bound{};
    Bind(fixture, bound);
    fixture.source_paused = false;
    ActiveSchemeStateV1PrivateObservation observation{};
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure{};
    Require(!CaptureActiveSchemePausedLiveSnapshotV1Private(
        bound.state, {42, 42}, observation, failure));
    Require(failure == ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                           observation_red);
    Require(bound.state.last_source_failure ==
            ActiveSchemeStateV1PrivateSourceFailure::not_paused);
  }
  {
    Fixture fixture{};
    BoundFixture bound{};
    Bind(fixture, bound);
    fixture.return_fallback = true;
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease definition{};
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure{};
    Require(!ResolveActiveSchemePausedLiveDefinitionV1Private(
        bound.state, {42, 42}, "sway_interaction", definition, failure));
    Require(failure == ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                           definition_red);
  }
  {
    Fixture fixture{};
    BoundFixture bound{};
    Bind(fixture, bound);
    fixture.precondition.available = false;
    ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure{};
    Require(!CaptureActiveSchemePausedLivePreconditionV1Private(
        bound.state, {42, 42}, precondition, failure));
    Require(failure == ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                           precondition_red);
  }
  {
    Fixture fixture{};
    BoundFixture bound{};
    Bind(fixture, bound);
    fixture.stale_postcondition = true;
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure{};
    ActiveSchemeSemanticActionV1PrivateAck ack{};
    Require(ExecuteActiveSchemePausedLiveNativeGlueV1Private(
                bound.state, {42, 42}, Request(fixture), ack, failure) ==
            ActiveSchemeSemanticActionV1PrivateAckStatus::
                submitted_verification_pending);
    ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
    Require(VerifyActiveSchemePausedLiveNativeGlueReceiptV1Private(
                bound.state, {42, 42}, ack, receipt, failure) ==
            ActiveSchemeSemanticActionV1PrivateReceiptStatus::red);
    Require(failure == ActiveSchemePausedLiveNativeGlueV1PrivateFailure::
                           receipt_red);
    Require(receipt.failure == ActiveSchemeSemanticActionV1PrivateFailure::
                                   post_observation_not_fresh);
    Require(fixture.native_submits == 1);
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
    TestExecutionOwnershipGates();
    TestStageTypedRed();
    TestLifecycleAndCollisionGates();
    TestUnknownKeyFailsClosed();
    std::cout << "active scheme paused-live native glue: GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
