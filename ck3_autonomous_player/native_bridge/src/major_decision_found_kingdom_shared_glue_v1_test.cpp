#include "xar_bridge/major_decision_found_kingdom_shared_glue_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace bridge = xar::bridge;
namespace native = xar::ck3_11906;

namespace {

int failures = 0;

#define CHECK(value)                                                           \
  do {                                                                         \
    if (!(value)) {                                                            \
      std::cerr << __FILE__ << ':' << __LINE__ << ": CHECK failed: "          \
                << #value << '\n';                                             \
      ++failures;                                                              \
    }                                                                          \
  } while (false)

constexpr std::uintptr_t kDatabase = 0x70000000;
constexpr std::uintptr_t kDefinition = 0x70001000;
constexpr std::uintptr_t kPlayer = 0x70002000;
constexpr std::uint32_t kDecisionHash = 0xA11CE123;
constexpr std::uint64_t kFnvOffset = 14695981039346656037ULL;
constexpr std::uint64_t kFnvPrime = 1099511628211ULL;

struct Region {
  std::uintptr_t begin = 0;
  std::size_t size = 0;
};

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> image{};
  std::vector<Region> command_regions{};
  std::vector<bridge::MajorDecisionFoundKingdomActionPreconditionV1>
      observations{};
  std::size_t capture_index = 0;
  bridge::MajorDecisionFoundKingdomActionPostconditionV1 postcondition{};
  bool postcondition_available = true;
  int construct_calls = 0;
  int validate_calls = 0;
  int clone_calls = 0;
  int stack_destroy_calls = 0;
  int heap_destroy_calls = 0;
  int queue_calls = 0;
};

std::uint64_t HashValue(std::uint64_t hash, std::uint64_t value) {
  for (int byte = 0; byte != 8; ++byte) {
    hash ^= value & 0xFFU;
    hash *= kFnvPrime;
    value >>= 8;
  }
  return hash;
}

template <typename T>
void MapValue(Fixture &fixture, std::uintptr_t address, const T &value) {
  const auto *bytes = reinterpret_cast<const std::uint8_t *>(&value);
  for (std::size_t index = 0; index != sizeof(value); ++index) {
    fixture.image[address + index] = bytes[index];
  }
}

void MapBytes(Fixture &fixture, std::uintptr_t address,
              const std::uint8_t *bytes, std::size_t size) {
  for (std::size_t index = 0; index != size; ++index) {
    fixture.image[address + index] = bytes[index];
  }
}

Fixture MakeFixture() {
  Fixture fixture{};
  for (const auto &signature :
       bridge::kMajorDecisionFoundKingdomNativeSignaturesV1) {
    MapBytes(fixture, signature.rva, signature.bytes.data(), signature.size);
  }
  for (const auto &slot : bridge::kMajorDecisionFoundKingdomNativeSlotsV1) {
    MapValue(fixture, slot.slot_rva, slot.function_rva);
  }
  for (const auto &signature :
       bridge::kMajorDecisionFoundKingdomNativeSubmitSignaturesV1) {
    MapBytes(fixture, signature.rva, signature.bytes.data(), signature.size);
  }
  for (const auto &slot :
       bridge::kMajorDecisionFoundKingdomNativeSubmitSlotsV1) {
    MapValue(fixture, slot.slot_rva, slot.function_rva);
  }
  constexpr char rtti[] = ".?AVCExecuteDecisionCommand@@";
  MapBytes(fixture,
           bridge::kMajorDecisionFoundKingdomExecuteCommandTypeDescriptorRvaV1 +
               0x10,
           reinterpret_cast<const std::uint8_t *>(rtti), sizeof(rtti));
  MapValue(fixture,
           bridge::kMajorDecisionFoundKingdomDecisionDatabaseSlotRvaV1,
           kDatabase);
  const std::uintptr_t database_vtable =
      bridge::kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1;
  const std::uintptr_t definition_vtable =
      bridge::kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1;
  MapValue(fixture, kDatabase, database_vtable);
  MapValue(fixture, kDefinition, definition_vtable);
  const std::int32_t character_id = 0x0100002A;
  MapValue(fixture, kPlayer + 0x18, character_id);
  return fixture;
}

bool InRegion(const Fixture &fixture, std::uintptr_t address,
              std::size_t size) {
  for (const auto &region : fixture.command_regions) {
    if (address >= region.begin && size <= region.size &&
        address - region.begin <= region.size - size) {
      return true;
    }
  }
  return false;
}

bool Read(void *context, const void *address, void *output,
          std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto start = reinterpret_cast<std::uintptr_t>(address);
  if (output == nullptr || size == 0) return false;
  if (InRegion(fixture, start, size)) {
    std::memcpy(output, address, size);
    return true;
  }
  auto *destination = static_cast<std::uint8_t *>(output);
  for (std::size_t index = 0; index != size; ++index) {
    const auto found = fixture.image.find(start + index);
    if (found == fixture.image.end()) return false;
    destination[index] = found->second;
  }
  return true;
}

std::uintptr_t ResolvePlayer(void *, std::uintptr_t module_base,
                             std::int32_t character_id) noexcept {
  return module_base == 0 && character_id == 0x0100002A ? kPlayer : 0;
}

bool HashName(void *, std::uintptr_t module_base, std::string_view name,
              std::uint32_t &output) noexcept {
  output = kDecisionHash;
  return module_base == 0 &&
         name == bridge::kMajorDecisionFoundKingdomDecisionIdV1;
}

std::uintptr_t LookupDefinition(void *, std::uintptr_t module_base,
                                std::uintptr_t database,
                                std::uint32_t hash) noexcept {
  return module_base == 0 && database == kDatabase && hash == kDecisionHash
             ? kDefinition
             : 0;
}

void WriteCommand(void *command, std::int32_t character_id,
                  std::uintptr_t definition) {
  std::memset(command, 0,
              bridge::kMajorDecisionFoundKingdomExecuteCommandSizeV1);
  const std::uintptr_t primary =
      bridge::kMajorDecisionFoundKingdomExecuteCommandPrimaryVtableRvaV1;
  const std::uintptr_t secondary =
      bridge::kMajorDecisionFoundKingdomExecuteCommandSecondaryVtableRvaV1;
  std::memcpy(command, &primary, sizeof(primary));
  std::memcpy(static_cast<std::byte *>(command) +
                  bridge::kMajorDecisionFoundKingdomExecuteCommandSecondaryOffsetV1,
              &secondary, sizeof(secondary));
  std::memcpy(static_cast<std::byte *>(command) +
                  bridge::kMajorDecisionFoundKingdomExecuteCommandCharacterIdOffsetV1,
              &character_id, sizeof(character_id));
  std::memcpy(static_cast<std::byte *>(command) +
                  bridge::kMajorDecisionFoundKingdomExecuteCommandDefinitionOffsetV1,
              &definition, sizeof(definition));
}

bool Construct(void *context, std::uintptr_t module_base, void *command,
               std::int32_t character_id, std::uintptr_t definition,
               void **owned_decision_context) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.construct_calls;
  if (module_base != 0 || command == nullptr ||
      owned_decision_context == nullptr || *owned_decision_context != nullptr) {
    return false;
  }
  WriteCommand(command, character_id, definition);
  fixture.command_regions.push_back(
      {reinterpret_cast<std::uintptr_t>(command),
       bridge::kMajorDecisionFoundKingdomExecuteCommandSizeV1});
  return true;
}

bool Validate(void *context, std::uintptr_t module_base,
              void *command) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.validate_calls;
  return module_base == 0 && command != nullptr;
}

bool Clone(void *context, std::uintptr_t module_base, void *command,
           void **owned_clone) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.clone_calls;
  if (module_base != 0 || command == nullptr || owned_clone == nullptr ||
      *owned_clone != nullptr) {
    return false;
  }
  auto *clone = new std::byte[
      bridge::kMajorDecisionFoundKingdomExecuteCommandSizeV1];
  std::memcpy(clone, command,
              bridge::kMajorDecisionFoundKingdomExecuteCommandSizeV1);
  fixture.command_regions.push_back(
      {reinterpret_cast<std::uintptr_t>(clone),
       bridge::kMajorDecisionFoundKingdomExecuteCommandSizeV1});
  *owned_clone = clone;
  return true;
}

bool Destroy(void *context, std::uintptr_t module_base, void *command,
             std::uint32_t flags) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (module_base != 0 || command == nullptr || (flags != 0 && flags != 1)) {
    return false;
  }
  if (flags == 0) {
    ++fixture.stack_destroy_calls;
  } else {
    ++fixture.heap_destroy_calls;
    delete[] static_cast<std::byte *>(command);
  }
  return true;
}

bool Queue(void *context, std::uintptr_t module_base, void **owned_command,
           std::uint32_t flags) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.queue_calls;
  if (module_base != 0 || owned_command == nullptr ||
      *owned_command == nullptr ||
      flags != bridge::kMajorDecisionFoundKingdomCommandQueueFlagsV1) {
    return false;
  }
  delete[] static_cast<std::byte *>(*owned_command);
  *owned_command = nullptr;
  return true;
}

bridge::MajorDecisionFoundKingdomNativeSubmitOperationsV1 Operations() {
  return {&Read,    &ResolvePlayer, &HashName, &LookupDefinition, &Construct,
          &Validate, &Clone,         &Destroy,  &Queue};
}

bridge::MajorDecisionFoundKingdomActionBindingV1 Binding() {
  bridge::MajorDecisionFoundKingdomActionBindingV1 output{};
  output.snapshot_revision = 100;
  output.native_revision = 70;
  output.proof_epoch = 40;
  output.date_raw = 1092;
  output.played_character_id = 0x0100002A;
  output.decision_database_identity = kDatabase;
  auto database_generation = HashValue(kFnvOffset, kDatabase);
  database_generation = HashValue(
      database_generation,
      bridge::kMajorDecisionFoundKingdomDecisionDatabaseVtableRvaV1);
  output.decision_database_generation = database_generation;
  output.decision_definition_identity = kDefinition;
  auto definition_generation = HashValue(kFnvOffset, database_generation);
  definition_generation = HashValue(definition_generation, kDefinition);
  definition_generation = HashValue(
      definition_generation,
      bridge::kMajorDecisionFoundKingdomDecisionDefinitionVtableRvaV1);
  output.decision_definition_generation = definition_generation;
  output.primary_title_id = 0x02000031;
  output.primary_title_identity = 0x71001;
  output.primary_title_generation = 13;
  output.world_identity = 0xA11001;
  output.world_generation = 14;
  output.world_revision = 60;
  return output;
}

bridge::MajorDecisionTypedBoolV1 Known(bool value) {
  return {bridge::MajorDecisionFieldStateV1::known, value,
          bridge::MajorDecisionUnknownReasonV1::none};
}

bridge::MajorDecisionEvaluatedCostV1 Cost() {
  bridge::MajorDecisionEvaluatedCostV1 output{};
  output.state = bridge::MajorDecisionFieldStateV1::known;
  output.source = bridge::MajorDecisionCostSourceV1::native_evaluated_cost;
  output.gold_q100000 = 30'000'000;
  output.treasury_q100000 = 10'000'000;
  output.prestige_q100000 = 50'000'000;
  output.piety_q100000 = 20'000'000;
  output.unknown_reason = bridge::MajorDecisionUnknownReasonV1::none;
  return output;
}

bridge::MajorDecisionFoundKingdomActionPreconditionV1 Precondition(
    bool eligible = true) {
  bridge::MajorDecisionFoundKingdomActionPreconditionV1 output{};
  output.available = true;
  output.application_main_thread = true;
  output.paused = true;
  output.map_ready = true;
  output.played_character_alive = true;
  output.played_character_identity_round_trip = true;
  output.decision_database_identity_round_trip = true;
  output.decision_definition_identity_round_trip = true;
  output.decision_source_block_sha256_round_trip = true;
  output.decision_id.assign(
      bridge::kMajorDecisionFoundKingdomDecisionIdV1);
  output.binding = Binding();
  output.is_shown = Known(eligible);
  output.is_valid = Known(eligible);
  output.is_valid_showing_failures_only = Known(eligible);
  output.evaluated_cost = Cost();
  output.is_affordable = Known(true);
  output.can_take = Known(eligible);
  output.effect_preview.state = bridge::MajorDecisionFieldStateV1::unknown;
  output.effect_preview.unknown_reason =
      bridge::MajorDecisionUnknownReasonV1::effect_preview_not_provided;
  output.effect_preview.executable = false;
  return output;
}

bool Capture(void *context,
             bridge::MajorDecisionFoundKingdomActionPreconditionV1 &output)
    noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (fixture.capture_index >= fixture.observations.size()) return false;
  output = fixture.observations[fixture.capture_index++];
  return true;
}

bool CapturePost(
    void *context,
    bridge::MajorDecisionFoundKingdomActionPostconditionV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (!fixture.postcondition_available) return false;
  output = fixture.postcondition;
  return true;
}

bridge::MajorDecisionFoundKingdomActionPostconditionV1 Postcondition() {
  const auto binding = Binding();
  bridge::MajorDecisionFoundKingdomActionPostconditionV1 output{};
  output.available = true;
  output.application_main_thread = true;
  output.paused = true;
  output.map_ready = true;
  output.snapshot_revision = binding.snapshot_revision + 1;
  output.native_revision = binding.native_revision + 1;
  output.proof_epoch = binding.proof_epoch;
  output.date_raw = binding.date_raw;
  output.played_character_id = binding.played_character_id;
  output.played_character_identity_round_trip = true;
  output.decision_database_identity = binding.decision_database_identity;
  output.decision_database_generation = binding.decision_database_generation;
  output.decision_database_identity_round_trip = true;
  output.decision_state_observed = true;
  output.decision_definition_present = true;
  output.decision_definition_identity = binding.decision_definition_identity;
  output.decision_definition_generation =
      binding.decision_definition_generation;
  output.decision_definition_identity_round_trip = true;
  output.decision_can_take_known = true;
  output.decision_can_take = false;
  output.primary_title_observed = true;
  output.primary_title_id = 0x03000044;
  output.primary_title_identity = 0x72001;
  output.primary_title_generation = 15;
  output.primary_title_tier =
      bridge::MajorDecisionFoundKingdomTitleTierV1::kingdom;
  output.primary_title_holder_character_id = binding.played_character_id;
  output.primary_title_identity_round_trip = true;
  output.primary_title_holder_identity_round_trip = true;
  output.player_primary_title_round_trip = true;
  output.dynamic_custom_kingdom_observed = true;
  output.world_outcome_observed = true;
  output.world_identity = binding.world_identity;
  output.world_generation = binding.world_generation;
  output.world_revision = binding.world_revision + 1;
  output.world_identity_round_trip = true;
  output.new_title_registered = true;
  output.title_world_index_round_trip = true;
  return output;
}

bridge::MajorDecisionFoundKingdomNativeSubmitEnvironmentV1 Environment(
    Fixture &fixture) {
  bridge::MajorDecisionFoundKingdomNativeSubmitEnvironmentV1 output{};
  output.binding_enabled = true;
  output.exact_build_admitted = true;
  output.admitted_game_version =
      bridge::kMajorDecisionFoundKingdomNativeSubmitGameVersionV1;
  output.admitted_executable_sha256 =
      bridge::kMajorDecisionFoundKingdomExecutableSha256V1;
  output.offline_fixture = true;
  output.operation_context = &fixture;
  output.operations = Operations();
  return output;
}

void PrepareMailbox(native::MainThreadQueryMailboxV1 &mailbox) {
  mailbox.state.store(native::MainThreadQueryMailboxStateV1::idle);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.executor_submission_enabled = true;
  mailbox.permitted_executor_sextrigintary =
      &bridge::ExecuteMajorDecisionFoundKingdomSharedMailboxV1;
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      native::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
}

native::MainThreadExecutionStampV1 Stamp() {
  native::MainThreadExecutionStampV1 output{};
  output.pump_epoch = 10;
  output.thread_id = GetCurrentThreadId();
  output.tls_initialized_flag_address = 0x1000;
  output.tls_initialized = 1;
  output.tls_context = 0x2000;
  output.tls_main_thread_marker = 1;
  output.jomini_state = 0x3000;
  output.game_state = 0x4000;
  output.date_raw = static_cast<std::int32_t>(Binding().date_raw);
  output.paused = true;
  return output;
}

void ExecuteAndComplete(native::MainThreadQueryMailboxV1 &mailbox,
                        bridge::MajorDecisionFoundKingdomSharedContextV1
                            &context,
                        bool expected_executor_result = true) {
  CHECK(mailbox.state.load() ==
        native::MainThreadQueryMailboxStateV1::queued);
  mailbox.state.store(native::MainThreadQueryMailboxStateV1::executing);
  const bool result = bridge::ExecuteMajorDecisionFoundKingdomSharedMailboxV1(
      &context, Stamp());
  CHECK(result == expected_executor_result);
  mailbox.executor_succeeded = result;
  mailbox.completed_sequence.store(context.ticket.sequence);
  mailbox.state.store(result
                          ? native::MainThreadQueryMailboxStateV1::completed
                          : native::MainThreadQueryMailboxStateV1::executor_failed);
}

bool Configure(Fixture &fixture, native::MainThreadQueryMailboxV1 &mailbox,
               bridge::MajorDecisionFoundKingdomSharedStateV1 &state,
               bridge::MajorDecisionFoundKingdomSharedContextV1 &context) {
  PrepareMailbox(mailbox);
  bridge::MajorDecisionFoundKingdomActionAccessV1 access{};
  access.context = &fixture;
  access.capture_precondition = &Capture;
  return bridge::ConfigureMajorDecisionFoundKingdomSharedGlueV1(
      mailbox, Environment(fixture), state, access, &fixture, &CapturePost,
      context);
}

void Reclaim(bridge::MajorDecisionFoundKingdomSharedContextV1 &context) {
  CHECK(bridge::ReclaimMajorDecisionFoundKingdomSharedV1(context) ==
        native::MainThreadQueryReclaimResultV1::reclaimed);
}

void TestSubmitAndFreshReceipt() {
  auto fixture = MakeFixture();
  const auto precondition = Precondition();
  fixture.observations = {precondition, precondition, precondition};
  fixture.postcondition = Postcondition();
  native::MainThreadQueryMailboxV1 mailbox{};
  bridge::MajorDecisionFoundKingdomSharedStateV1 state{};
  bridge::MajorDecisionFoundKingdomSharedContextV1 context{};
  CHECK(Configure(fixture, mailbox, state, context));
  CHECK(bridge::PrepareMajorDecisionFoundKingdomSubmitV1(
      context, "decision7-happy"));
  CHECK(bridge::TryQueueMajorDecisionFoundKingdomSharedV1(context) ==
        native::MainThreadQuerySubmitResultV1::submitted);
  ExecuteAndComplete(mailbox, context);
  CHECK(context.concrete_candidate_generated);
  CHECK(context.concrete_request.decision_id ==
        bridge::kMajorDecisionFoundKingdomDecisionIdV1);
  CHECK(context.completion == bridge::MajorDecisionFoundKingdomSharedCompletionV1::
                                  submitted_verification_pending);
  CHECK(state.has_pending_ack);
  CHECK(state.action.verification_pending);
  CHECK(state.pending_ack.verification_pending);
  CHECK(!state.pending_ack.effect_preview_available);
  CHECK(!state.pending_ack.exact_benefit_claimed);
  CHECK(fixture.capture_index == 3);
  CHECK(fixture.queue_calls == 1);
  Reclaim(context);

  CHECK(bridge::PrepareMajorDecisionFoundKingdomReceiptV1(context));
  CHECK(bridge::TryQueueMajorDecisionFoundKingdomSharedV1(context) ==
        native::MainThreadQuerySubmitResultV1::submitted);
  ExecuteAndComplete(mailbox, context);
  CHECK(context.completion ==
        bridge::MajorDecisionFoundKingdomSharedCompletionV1::receipt_applied);
  CHECK(context.receipt.postcondition_verified);
  CHECK(context.receipt.new_kingdom_title_verified);
  CHECK(context.receipt.world_outcome_verified);
  CHECK(!context.receipt.effect_preview_available);
  CHECK(!context.receipt.exact_benefit_claimed);
  CHECK(!state.has_pending_ack);
  CHECK(!state.action.verification_pending);
  CHECK(fixture.queue_calls == 1);
  Reclaim(context);
}

void TestEligibilityStaysTypedRed() {
  auto fixture = MakeFixture();
  const auto ineligible = Precondition(false);
  fixture.observations = {ineligible, ineligible};
  fixture.postcondition = Postcondition();
  native::MainThreadQueryMailboxV1 mailbox{};
  bridge::MajorDecisionFoundKingdomSharedStateV1 state{};
  bridge::MajorDecisionFoundKingdomSharedContextV1 context{};
  CHECK(Configure(fixture, mailbox, state, context));
  CHECK(bridge::PrepareMajorDecisionFoundKingdomSubmitV1(
      context, "decision7-ineligible"));
  CHECK(bridge::TryQueueMajorDecisionFoundKingdomSharedV1(context) ==
        native::MainThreadQuerySubmitResultV1::submitted);
  ExecuteAndComplete(mailbox, context);
  CHECK(context.concrete_candidate_generated);
  CHECK(context.completion ==
        bridge::MajorDecisionFoundKingdomSharedCompletionV1::action_red);
  CHECK(context.failure ==
        bridge::MajorDecisionFoundKingdomSharedFailureV1::action_rejected);
  CHECK(context.action_failure_class ==
        bridge::MajorDecisionFoundKingdomActionFailureClassV1::eligibility);
  CHECK(fixture.queue_calls == 0);
  CHECK(!state.has_pending_ack);
  Reclaim(context);
}

void TestPendingSubmitAndStaleReceiptStayRed() {
  auto fixture = MakeFixture();
  const auto precondition = Precondition();
  fixture.observations = {precondition, precondition, precondition,
                          precondition};
  fixture.postcondition = Postcondition();
  native::MainThreadQueryMailboxV1 mailbox{};
  bridge::MajorDecisionFoundKingdomSharedStateV1 state{};
  bridge::MajorDecisionFoundKingdomSharedContextV1 context{};
  CHECK(Configure(fixture, mailbox, state, context));
  CHECK(bridge::PrepareMajorDecisionFoundKingdomSubmitV1(
      context, "decision7-first"));
  CHECK(bridge::TryQueueMajorDecisionFoundKingdomSharedV1(context) ==
        native::MainThreadQuerySubmitResultV1::submitted);
  ExecuteAndComplete(mailbox, context);
  Reclaim(context);
  CHECK(fixture.queue_calls == 1);

  CHECK(bridge::PrepareMajorDecisionFoundKingdomSubmitV1(
      context, "decision7-duplicate"));
  CHECK(bridge::TryQueueMajorDecisionFoundKingdomSharedV1(context) ==
        native::MainThreadQuerySubmitResultV1::submitted);
  ExecuteAndComplete(mailbox, context);
  CHECK(context.completion ==
        bridge::MajorDecisionFoundKingdomSharedCompletionV1::action_red);
  CHECK(context.action_failure_class ==
        bridge::MajorDecisionFoundKingdomActionFailureClassV1::pending_action);
  CHECK(state.pending_ack.request_id == "decision7-first");
  CHECK(fixture.queue_calls == 1);
  CHECK(state.has_pending_ack);
  Reclaim(context);

  fixture.postcondition.snapshot_revision = Binding().snapshot_revision;
  CHECK(bridge::PrepareMajorDecisionFoundKingdomReceiptV1(context));
  CHECK(bridge::TryQueueMajorDecisionFoundKingdomSharedV1(context) ==
        native::MainThreadQuerySubmitResultV1::submitted);
  ExecuteAndComplete(mailbox, context);
  CHECK(context.completion ==
        bridge::MajorDecisionFoundKingdomSharedCompletionV1::receipt_red);
  CHECK(context.failure ==
        bridge::MajorDecisionFoundKingdomSharedFailureV1::receipt_rejected);
  CHECK(state.has_pending_ack);
  CHECK(state.action.verification_pending);
  CHECK(fixture.queue_calls == 1);
  Reclaim(context);
}

void TestMailboxIdentityFailureIsInfrastructureRed() {
  auto fixture = MakeFixture();
  const auto precondition = Precondition();
  fixture.observations = {precondition, precondition, precondition};
  fixture.postcondition = Postcondition();
  native::MainThreadQueryMailboxV1 mailbox{};
  bridge::MajorDecisionFoundKingdomSharedStateV1 state{};
  bridge::MajorDecisionFoundKingdomSharedContextV1 context{};
  CHECK(Configure(fixture, mailbox, state, context));
  CHECK(bridge::PrepareMajorDecisionFoundKingdomSubmitV1(
      context, "decision7-mailbox-red"));
  CHECK(bridge::TryQueueMajorDecisionFoundKingdomSharedV1(context) ==
        native::MainThreadQuerySubmitResultV1::submitted);
  mailbox.executor_context = nullptr;
  ExecuteAndComplete(mailbox, context, false);
  CHECK(context.completion ==
        bridge::MajorDecisionFoundKingdomSharedCompletionV1::infrastructure_red);
  CHECK(context.failure ==
        bridge::MajorDecisionFoundKingdomSharedFailureV1::mailbox_identity);
  CHECK(fixture.queue_calls == 0);
  Reclaim(context);
}

void TestFailedReconfigurationDisablesPreviousBinding() {
  auto fixture = MakeFixture();
  fixture.observations = {Precondition()};
  fixture.postcondition = Postcondition();
  native::MainThreadQueryMailboxV1 mailbox{};
  bridge::MajorDecisionFoundKingdomSharedStateV1 state{};
  bridge::MajorDecisionFoundKingdomSharedContextV1 context{};
  CHECK(Configure(fixture, mailbox, state, context));

  auto invalid_environment = Environment(fixture);
  invalid_environment.exact_build_admitted = false;
  bridge::MajorDecisionFoundKingdomActionAccessV1 access{};
  access.context = &fixture;
  access.capture_precondition = &Capture;
  CHECK(!bridge::ConfigureMajorDecisionFoundKingdomSharedGlueV1(
      mailbox, invalid_environment, state, access, &fixture, &CapturePost,
      context));
  CHECK(!context.configured);
  CHECK(context.completion ==
        bridge::MajorDecisionFoundKingdomSharedCompletionV1::infrastructure_red);
  CHECK(context.failure ==
        bridge::MajorDecisionFoundKingdomSharedFailureV1::not_configured);
  CHECK(!bridge::PrepareMajorDecisionFoundKingdomSubmitV1(
      context, "decision7-invalid-reconfigure"));
}

} // namespace

int main() {
  TestSubmitAndFreshReceipt();
  TestEligibilityStaysTypedRed();
  TestPendingSubmitAndStaleReceiptStayRed();
  TestMailboxIdentityFailureIsInfrastructureRed();
  TestFailedReconfigurationDisablesPreviousBinding();
  if (failures != 0) {
    std::cerr << failures << " shared-glue checks failed\n";
    return 1;
  }
  std::cout << "major decision found-kingdom shared glue: GREEN\n";
  return 0;
}
