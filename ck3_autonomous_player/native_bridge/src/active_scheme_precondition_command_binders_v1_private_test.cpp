#define main ActiveSchemeScheme9FixtureMain
#include "active_scheme_paused_live_native_glue_v1_private_test.cpp"
#undef main

#include "active_scheme_precondition_command_binders_v1_private.hpp"

namespace {

constexpr std::size_t kFixtureCharacterCapacity = 64;
constexpr std::array<std::string_view, 4> kScheme10MurderStarters{
    "agent_focus_balance", "agent_focus_success", "agent_focus_speed",
    "agent_focus_secrecy"};

struct Scheme10Fixture {
  Fixture base{};
  std::array<std::uint8_t, 0x40> character_storage{};
  std::array<std::uint8_t, kFixtureCharacterCapacity * 0x10>
      character_slots{};
  std::array<std::uint8_t, 0x20> actor{};
  std::array<std::uint8_t, 0x20> target{};
  std::array<std::uint8_t, 4 * kActiveSchemeDefinitionOptionStride>
      murder_options{};
  std::array<std::uint8_t, 4> selected_options{};
  std::uintptr_t character_storage_slot = 0;
  std::uintptr_t character_fallback_slot = 0x7E000000;
  bool validator_result = true;
  bool corrupt_starter_flag = false;
  bool reject_submit = false;
  bool reject_destroy = false;
  bool partial_command_failure = false;
  int contexts_constructed = 0;
  int contexts_destroyed = 0;
  int commands_constructed = 0;
  int submits = 0;

  Scheme10Fixture() {
    character_storage_slot =
        reinterpret_cast<std::uintptr_t>(character_storage.data());
    const auto slots =
        reinterpret_cast<std::uintptr_t>(character_slots.data());
    const std::int32_t capacity =
        static_cast<std::int32_t>(kFixtureCharacterCapacity);
    Put(character_storage, 0x20, slots);
    Put(character_storage, 0x2C, capacity);
    const auto actor_address = reinterpret_cast<std::uintptr_t>(actor.data());
    const auto target_address =
        reinterpret_cast<std::uintptr_t>(target.data());
    Put(character_slots,
        static_cast<std::size_t>(kActor & 0x00FFFFFFU) * 0x10 + 0x08,
        actor_address);
    Put(character_slots,
        static_cast<std::size_t>(kTarget & 0x00FFFFFFU) * 0x10 + 0x08,
        target_address);
    Put(actor, 0x18, kActor);
    Put(target, 0x18, kTarget);

    const auto option_rows =
        reinterpret_cast<std::uintptr_t>(murder_options.data());
    const std::int32_t option_count = 4;
    const bool exclusive = true;
    Put(base.murder_definition, kActiveSchemeDefinitionOptionsOffset,
        option_rows);
    Put(base.murder_definition,
        kActiveSchemeDefinitionOptionsCountOffset, option_count);
    Put(base.murder_definition,
        kActiveSchemeDefinitionOptionsExclusiveOffset, exclusive);
    for (std::size_t index = 0; index < kScheme10MurderStarters.size(); ++index) {
      const auto identifier = static_cast<std::int32_t>(700 + index);
      Put(murder_options,
          index * kActiveSchemeDefinitionOptionStride +
              kActiveSchemeDefinitionOptionFlagOffset,
          identifier);
    }
  }
};

bool Scheme10Read(void *context, const void *address, void *output,
                  std::size_t size) noexcept {
  auto &fixture = *static_cast<Scheme10Fixture *>(context);
  const auto current = reinterpret_cast<std::uintptr_t>(address);
  for (const auto &signature :
       kActiveSchemePreconditionCommandBindersV1PrivateSignatures) {
    if (current == kModuleBase + signature.rva && size == signature.size) {
      std::memcpy(output, signature.bytes.data(), size);
      return true;
    }
  }
  if (current == kModuleBase + kActiveSchemeCharacterStorageSlotRva &&
      size == sizeof(std::uintptr_t)) {
    std::memcpy(output, &fixture.character_storage_slot, size);
    return true;
  }
  if (current == kModuleBase + kActiveSchemeCharacterFallbackSlotRva &&
      size == sizeof(std::uintptr_t)) {
    std::memcpy(output, &fixture.character_fallback_slot, size);
    return true;
  }
  if (ReadMemory(&fixture.base, address, output, size) ||
      CopyRegion(fixture.character_storage, current, output, size) ||
      CopyRegion(fixture.character_slots, current, output, size) ||
      CopyRegion(fixture.actor, current, output, size) ||
      CopyRegion(fixture.target, current, output, size) ||
      CopyRegion(fixture.murder_options, current, output, size) ||
      CopyRegion(fixture.selected_options, current, output, size)) {
    return true;
  }
  // Binder-owned context/command buffers have ordinary process addresses.
  if (current > 0x1'0000'0000ULL && output != nullptr && size != 0) {
    std::memcpy(output, address, size);
    return true;
  }
  return false;
}

bool Scheme10Write(void *, void *address, const void *input,
                   std::size_t size) noexcept {
  if (address == nullptr || input == nullptr || size == 0) return false;
  std::memcpy(address, input, size);
  return true;
}

bool Scheme10Getter(void *context, std::uintptr_t address,
                    std::uintptr_t &output) noexcept {
  return InvokeGetter(&static_cast<Scheme10Fixture *>(context)->base, address,
                      output);
}

bool Scheme10Hash(void *context, std::uintptr_t address,
                  std::uintptr_t database, std::string_view key,
                  std::int32_t &output) noexcept {
  return InvokeHash(&static_cast<Scheme10Fixture *>(context)->base, address,
                    database, key, output);
}

bool Scheme10Lookup(void *context, std::uintptr_t address,
                    std::uintptr_t database, std::int32_t hash,
                    std::uintptr_t &output) noexcept {
  return InvokeLookup(&static_cast<Scheme10Fixture *>(context)->base, address,
                      database, hash, output);
}

bool Scheme10Identifier(void *context, std::uintptr_t table,
                        std::uintptr_t lookup, std::string_view key,
                        std::int32_t &output) noexcept {
  auto &fixture = *static_cast<Scheme10Fixture *>(context);
  if (table !=
          kModuleBase + kActiveSchemePreconditionGetScriptIdentifierTableRva ||
      lookup !=
          kModuleBase + kActiveSchemePreconditionLookupScriptIdentifierRva) {
    return false;
  }
  const auto found = std::find(kScheme10MurderStarters.begin(),
                               kScheme10MurderStarters.end(), key);
  if (found == kScheme10MurderStarters.end()) return false;
  output = static_cast<std::int32_t>(
      700 + std::distance(kScheme10MurderStarters.begin(), found));
  if (fixture.corrupt_starter_flag && key == "agent_focus_success") ++output;
  return true;
}

bool Scheme10ConstructContext(void *context, std::uintptr_t address,
                              void *storage, std::uintptr_t interaction,
                              std::int32_t actor,
                              std::int32_t target) noexcept {
  auto &fixture = *static_cast<Scheme10Fixture *>(context);
  if (address !=
          kModuleBase +
              kActiveSchemeSemanticActionV1PrivateConstructContextRva ||
      storage == nullptr ||
      (interaction != reinterpret_cast<std::uintptr_t>(
                          fixture.base.sway_definition.data()) &&
       interaction != reinterpret_cast<std::uintptr_t>(
                          fixture.base.murder_definition.data()))) {
    return false;
  }
  ++fixture.contexts_constructed;
  std::memset(storage, 0, kActiveSchemeNativeContextSize);
  const std::uintptr_t context_vtable = kModuleBase + 0x4330000;
  std::memcpy(storage, &context_vtable, sizeof(context_vtable));
  std::memcpy(static_cast<std::byte *>(storage) +
                  kActiveSchemeContextActorOffset,
              &actor, sizeof(actor));
  std::memcpy(static_cast<std::byte *>(storage) +
                  kActiveSchemeContextRecipientOffset,
              &target, sizeof(target));
  if (interaction == reinterpret_cast<std::uintptr_t>(
                         fixture.base.murder_definition.data())) {
    fixture.selected_options.fill(0);
    const auto bytes =
        reinterpret_cast<std::uintptr_t>(fixture.selected_options.data());
    const std::int32_t count = 4;
    std::memcpy(static_cast<std::byte *>(storage) +
                    kActiveSchemeContextSelectedOptionsOffset,
                &bytes, sizeof(bytes));
    std::memcpy(static_cast<std::byte *>(storage) +
                    kActiveSchemeContextSelectedOptionsCountOffset,
                &count, sizeof(count));
  }
  return true;
}

bool Scheme10Refresh(void *, std::uintptr_t address, void *) noexcept {
  return address == kModuleBase + kActiveSchemePreconditionRefreshContextRva;
}

bool Scheme10Finalize(void *, std::uintptr_t address, void *) noexcept {
  return address == kModuleBase + kActiveSchemePreconditionFinalizeContextRva;
}

bool Scheme10Validate(void *context, std::uintptr_t address, void *,
                      bool &output) noexcept {
  if (address !=
      kModuleBase + kActiveSchemeSemanticActionV1PrivateValidateContextRva) {
    return false;
  }
  output = static_cast<Scheme10Fixture *>(context)->validator_result;
  return true;
}

bool Scheme10ConstructCommand(void *context, std::uintptr_t address,
                              void *storage,
                              const void *native_context) noexcept {
  auto &fixture = *static_cast<Scheme10Fixture *>(context);
  if (address !=
          kModuleBase +
              kActiveSchemeSemanticActionV1PrivateConstructCommandRva ||
      storage == nullptr || native_context == nullptr) {
    return false;
  }
  ++fixture.commands_constructed;
  std::memset(storage, 0, kActiveSchemeNativeCommandSize);
  const auto primary =
      kModuleBase + kActiveSchemeSemanticActionV1PrivateCommandPrimaryVtableRva;
  const auto secondary = kModuleBase +
                         kActiveSchemeSemanticActionV1PrivateCommandSecondaryVtableRva;
  std::memcpy(storage, &primary, sizeof(primary));
  std::memcpy(static_cast<std::byte *>(storage) + 0x18, &secondary,
              sizeof(secondary));
  std::memcpy(static_cast<std::byte *>(storage) +
                  kActiveSchemeCopiedCommandContextOffset,
              native_context, kActiveSchemeNativeContextSize);
  return !fixture.partial_command_failure;
}

bool Scheme10Submit(void *context, std::uintptr_t address,
                    std::uintptr_t manager, void *, std::uint32_t channel,
                    bool &accepted) noexcept {
  auto &fixture = *static_cast<Scheme10Fixture *>(context);
  if (address !=
          kModuleBase + kActiveSchemeSemanticActionV1PrivateSubmitCommandRva ||
      manager != kModuleBase + kActiveSchemeCommandManagerRva ||
      channel != kActiveSchemeSemanticActionV1PrivateNativeCommandChannel) {
    return false;
  }
  ++fixture.submits;
  accepted = !fixture.reject_submit;
  if (accepted) fixture.base.ApplyPostcondition();
  return true;
}

bool Scheme10Destroy(void *context, std::uintptr_t address,
                     void *) noexcept {
  if (address !=
      kModuleBase + kActiveSchemeSemanticActionV1PrivateDestroyContextRva) {
    return false;
  }
  auto &fixture = *static_cast<Scheme10Fixture *>(context);
  ++fixture.contexts_destroyed;
  return !fixture.reject_destroy;
}

ActiveSchemePreconditionCommandBindersV1PrivateEnvironment
Scheme10Environment(Scheme10Fixture &fixture) {
  ActiveSchemePreconditionCommandBindersV1PrivateEnvironment environment{};
  environment.binding_enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      kActiveSchemeSemanticActionV1PrivateExecutableSha256;
  environment.admitted_game_version =
      kActiveSchemeSemanticActionV1PrivateNativeCommandGameVersion;
  environment.offline_fixture = true;
  environment.module_base = kModuleBase;
  environment.source_access = SourceAccess(fixture.base);
  environment.operation_context = &fixture;
  environment.operations = {
      &Scheme10Read,          &Scheme10Write,     &Scheme10Getter,
      &Scheme10Hash,          &Scheme10Lookup,    &Scheme10Identifier,
      &Scheme10ConstructContext, &Scheme10Refresh, &Scheme10Finalize,
      &Scheme10Validate,      &Scheme10ConstructCommand,
      &Scheme10Submit,        &Scheme10Destroy};
  return environment;
}

struct Scheme10Bound {
  ActiveSchemePreconditionCommandBindersV1PrivateState state{};
  ActiveSchemePreconditionCommandBindersV1PrivateReadiness readiness{};
};

void BindScheme10(Scheme10Fixture &fixture, Scheme10Bound &bound) {
  Require(BindActiveSchemePreconditionCommandBindersV1Private(
      Scheme10Environment(fixture), bound.state, bound.readiness));
  Require(bound.readiness.exact_build_bound &&
          bound.readiness.stable_identity_route_bound &&
          bound.readiness.native_context_validator_bound &&
          bound.readiness.native_single_submit_release_bound &&
          bound.readiness.native_precondition_bound &&
          bound.readiness.callback_core_ready);
}

void TestScheme10SwayAndMurder() {
  for (const bool murder : {false, true}) {
    Scheme10Fixture fixture{};
    if (murder) fixture.base.MakeMurder();
    Scheme10Bound bound{};
    BindScheme10(fixture, bound);
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution execution{77, 77};
    auto request = Request(fixture.base);

    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    ActiveSchemeStateV1PrivateObservation snapshot{};
    Require(CaptureActiveSchemePreconditionCommandSnapshotV1Private(
        bound.state, execution, snapshot, failure));
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease definition{};
    const bool definition_ok =
        ResolveActiveSchemePreconditionCommandDefinitionV1Private(
            bound.state, execution, request.interaction_key, definition,
            failure);
    if (!definition_ok) {
      std::cerr << "definition red: "
                << ActiveSchemePreconditionCommandBindersV1PrivateFailureName(
                       failure)
                << " frames=" << fixture.base.source_frame_captures
                << " getter=" << fixture.base.getter_calls
                << " hash=" << fixture.base.hash_calls
                << " lookup=" << fixture.base.lookup_calls << '\n';
    }
    Require(definition_ok);
    ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
    Require(CaptureActiveSchemePreconditionCommandPreconditionV1Private(
        bound.state, execution, request, precondition, failure));
    Require(precondition.available && precondition.shown &&
            precondition.valid && precondition.can_start_scheme &&
            precondition.success_chance.status ==
                ActiveSchemeSemanticActionV1PrivatePreviewStatus::
                    explicitly_unavailable);
    Require(precondition.starter_option_count == (murder ? 4U : 0U));

    ActiveSchemeSemanticActionV1PrivateAck ack{};
    Require(ExecuteActiveSchemePreconditionCommandV1Private(
                bound.state, execution, request, ack, failure) ==
            ActiveSchemeSemanticActionV1PrivateAckStatus::
                submitted_verification_pending);
    Require(ack.submit_call_count == 1 && fixture.submits == 1 &&
            fixture.commands_constructed == 1);
    ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
    Require(VerifyActiveSchemePreconditionCommandReceiptV1Private(
                bound.state, execution, ack, receipt, failure) ==
            ActiveSchemeSemanticActionV1PrivateReceiptStatus::applied);
    Require(receipt.postcondition_verified && fixture.submits == 1);
    // Standalone precondition + Scheme5's two captures + submitted context,
    // then copied-command context and the three originals are released.
    Require(fixture.contexts_constructed == 4 &&
            fixture.contexts_destroyed == 5);
  }
}

void TestScheme10TypedRedAndSingleSubmit() {
  {
    Scheme10Fixture fixture{};
    fixture.validator_result = false;
    Scheme10Bound bound{};
    BindScheme10(fixture, bound);
    ActiveSchemeSemanticActionV1PrivateAck ack{};
    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    Require(ExecuteActiveSchemePreconditionCommandV1Private(
                bound.state, {88, 88}, Request(fixture.base), ack, failure) ==
            ActiveSchemeSemanticActionV1PrivateAckStatus::
                rejected_before_submit);
    Require(fixture.submits == 0 &&
            failure ==
                ActiveSchemePreconditionCommandBindersV1PrivateFailure::
                    glue_red);
  }
  {
    Scheme10Fixture fixture{};
    fixture.base.MakeMurder();
    fixture.corrupt_starter_flag = true;
    Scheme10Bound bound{};
    BindScheme10(fixture, bound);
    ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    Require(!CaptureActiveSchemePreconditionCommandPreconditionV1Private(
        bound.state, {89, 89}, Request(fixture.base), precondition, failure));
    Require(failure ==
            ActiveSchemePreconditionCommandBindersV1PrivateFailure::
                native_precondition_red);
    Require(fixture.submits == 0);
  }
  {
    Scheme10Fixture fixture{};
    fixture.reject_destroy = true;
    Scheme10Bound bound{};
    BindScheme10(fixture, bound);
    ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    Require(!CaptureActiveSchemePreconditionCommandPreconditionV1Private(
        bound.state, {89, 89}, Request(fixture.base), precondition, failure));
    Require(failure ==
            ActiveSchemePreconditionCommandBindersV1PrivateFailure::
                native_precondition_red);
  }
  {
    Scheme10Fixture fixture{};
    fixture.partial_command_failure = true;
    Scheme10Bound bound{};
    BindScheme10(fixture, bound);
    ActiveSchemeSemanticActionV1PrivateAck ack{};
    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    Require(ExecuteActiveSchemePreconditionCommandV1Private(
                bound.state, {89, 89}, Request(fixture.base), ack, failure) ==
            ActiveSchemeSemanticActionV1PrivateAckStatus::
                rejected_before_submit);
    Require(fixture.submits == 0 && fixture.contexts_destroyed == 4);
  }
  {
    Scheme10Fixture fixture{};
    Scheme10Bound bound{};
    BindScheme10(fixture, bound);
    ActiveSchemeSemanticActionV1PrivateAck ack{};
    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    const auto request = Request(fixture.base);
    Require(ExecuteActiveSchemePreconditionCommandV1Private(
                bound.state, {90, 90}, request, ack, failure) ==
            ActiveSchemeSemanticActionV1PrivateAckStatus::
                submitted_verification_pending);
    ActiveSchemeSemanticActionV1PrivateAck second{};
    Require(ExecuteActiveSchemePreconditionCommandV1Private(
                bound.state, {90, 90}, request, second, failure) ==
            ActiveSchemeSemanticActionV1PrivateAckStatus::
                rejected_before_submit);
    Require(fixture.submits == 1);
  }
}

void TestScheme10BindingAndOwnershipGates() {
  {
    Scheme10Fixture fixture{};
    auto environment = Scheme10Environment(fixture);
    environment.operations.submit = nullptr;
    Scheme10Bound bound{};
    Require(!BindActiveSchemePreconditionCommandBindersV1Private(
        environment, bound.state, bound.readiness));
    Require(bound.readiness.failure ==
            ActiveSchemePreconditionCommandBindersV1PrivateFailure::
                primitive_callbacks_unavailable);
  }
  {
    Scheme10Fixture fixture{};
    Scheme10Bound bound{};
    BindScheme10(fixture, bound);
    ActiveSchemeStateV1PrivateObservation observation{};
    ActiveSchemePreconditionCommandBindersV1PrivateFailure failure{};
    Require(!CaptureActiveSchemePreconditionCommandSnapshotV1Private(
        bound.state, {90, 91}, observation, failure));
    Require(failure ==
            ActiveSchemePreconditionCommandBindersV1PrivateFailure::
                not_application_main_thread);
    bound.state.operation_active = true;
    Require(!CaptureActiveSchemePreconditionCommandSnapshotV1Private(
        bound.state, {91, 91}, observation, failure));
    Require(failure ==
            ActiveSchemePreconditionCommandBindersV1PrivateFailure::
                reentrant_execution);
  }
}

} // namespace

int main() {
  try {
    TestScheme10SwayAndMurder();
    TestScheme10TypedRedAndSingleSubmit();
    TestScheme10BindingAndOwnershipGates();
    std::cout << "active scheme precondition/command binders: GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
