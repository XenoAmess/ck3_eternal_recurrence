#include "xar_bridge/major_decision_found_kingdom_native_submit_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

namespace bridge = xar::bridge;

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
  int construct_calls = 0;
  int validate_calls = 0;
  int clone_calls = 0;
  int stack_destroy_calls = 0;
  int heap_destroy_calls = 0;
  int queue_calls = 0;
  bool validate_result = true;
  bool clone_result = true;
  bool corrupt_clone = false;
  bool queue_result = true;
  bool queue_consumes = true;
  std::uint32_t queue_flags = 0;
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
  if (module_base != 0 || command == nullptr || owned_decision_context == nullptr ||
      *owned_decision_context != nullptr) {
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
  return module_base == 0 && command != nullptr && fixture.validate_result;
}

bool Clone(void *context, std::uintptr_t module_base, void *command,
           void **owned_clone) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.clone_calls;
  if (module_base != 0 || command == nullptr || owned_clone == nullptr ||
      *owned_clone != nullptr || !fixture.clone_result) {
    return false;
  }
  auto *clone = new std::byte[
      bridge::kMajorDecisionFoundKingdomExecuteCommandSizeV1];
  std::memcpy(clone, command,
              bridge::kMajorDecisionFoundKingdomExecuteCommandSizeV1);
  if (fixture.corrupt_clone) {
    const std::uintptr_t invalid = 0;
    std::memcpy(clone, &invalid, sizeof(invalid));
  }
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
  fixture.queue_flags = flags;
  if (module_base != 0 || owned_command == nullptr ||
      *owned_command == nullptr) {
    return false;
  }
  if (fixture.queue_consumes) {
    delete[] static_cast<std::byte *>(*owned_command);
    *owned_command = nullptr;
  }
  return fixture.queue_result;
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
  output.prestige_q100000 = 50'000'000;
  output.piety_q100000 = 20'000'000;
  output.unknown_reason = bridge::MajorDecisionUnknownReasonV1::none;
  return output;
}

bridge::MajorDecisionFoundKingdomActionPreconditionV1 Precondition() {
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
  output.is_shown = Known(true);
  output.is_valid = Known(true);
  output.is_valid_showing_failures_only = Known(true);
  output.evaluated_cost = Cost();
  output.is_affordable = Known(true);
  output.can_take = Known(true);
  output.effect_preview.state = bridge::MajorDecisionFieldStateV1::unknown;
  output.effect_preview.unknown_reason =
      bridge::MajorDecisionUnknownReasonV1::effect_preview_not_provided;
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

bridge::MajorDecisionFoundKingdomNativeSubmitEnvironmentV1
Environment(Fixture &fixture) {
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

bridge::MajorDecisionFoundKingdomActionRequestV1 Request() {
  bridge::MajorDecisionFoundKingdomActionRequestV1 output{};
  output.request_id = "decision6-fixture";
  output.decision_id.assign(
      bridge::kMajorDecisionFoundKingdomDecisionIdV1);
  output.expected_binding = Binding();
  output.expected_evaluated_cost = Cost();
  return output;
}

void RunSubmit(Fixture &fixture,
               bridge::MajorDecisionFoundKingdomActionAckV1 &ack) {
  const auto precondition = Precondition();
  fixture.observations = {precondition, precondition};
  bridge::MajorDecisionFoundKingdomActionEnvironmentV1 action_environment{};
  action_environment.action_enabled = true;
  bridge::MajorDecisionFoundKingdomActionAccessV1 action_access{
      &fixture, &Capture, nullptr};
  bridge::MajorDecisionFoundKingdomNativeSubmitStateV1 native_state{};
  auto environment = Environment(fixture);
  CHECK(bridge::BindMajorDecisionFoundKingdomNativeSubmitV1(
      environment, native_state, action_environment, action_access));
  CHECK(native_state.attached);
  CHECK(action_environment.offline_fixture_submit);
  CHECK(!action_environment.submit_abi_certified);
  bridge::MajorDecisionFoundKingdomActionStateV1 action_state{};
  const auto request = Request();
  bridge::ExecuteMajorDecisionFoundKingdomActionCoreV1(
      action_environment, action_access, request, action_state, ack);
}

void TestHappyNativeLifecycle() {
  auto fixture = MakeFixture();
  bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
  RunSubmit(fixture, ack);
  CHECK(ack.status ==
        bridge::MajorDecisionFoundKingdomActionAckStatusV1::
            submitted_verification_pending);
  CHECK(fixture.capture_index == 2);
  CHECK(fixture.construct_calls == 1);
  CHECK(fixture.validate_calls == 1);
  CHECK(fixture.clone_calls == 1);
  CHECK(fixture.stack_destroy_calls == 1);
  CHECK(fixture.heap_destroy_calls == 0);
  CHECK(fixture.queue_calls == 1);
  CHECK(fixture.queue_flags ==
        bridge::kMajorDecisionFoundKingdomCommandQueueFlagsV1);
  CHECK(!ack.effect_preview_available);
  CHECK(!ack.exact_benefit_claimed);
}

void TestLifecycleFailures() {
  {
    auto fixture = MakeFixture();
    fixture.validate_result = false;
    bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
    RunSubmit(fixture, ack);
    CHECK(ack.status ==
          bridge::MajorDecisionFoundKingdomActionAckStatusV1::
              rejected_before_submit);
    CHECK(fixture.stack_destroy_calls == 1);
    CHECK(fixture.clone_calls == 0);
    CHECK(fixture.queue_calls == 0);
  }
  {
    auto fixture = MakeFixture();
    fixture.clone_result = false;
    bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
    RunSubmit(fixture, ack);
    CHECK(ack.status ==
          bridge::MajorDecisionFoundKingdomActionAckStatusV1::
              rejected_before_submit);
    CHECK(fixture.stack_destroy_calls == 1);
    CHECK(fixture.heap_destroy_calls == 0);
    CHECK(fixture.queue_calls == 0);
  }
  {
    auto fixture = MakeFixture();
    fixture.corrupt_clone = true;
    bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
    RunSubmit(fixture, ack);
    CHECK(ack.status ==
          bridge::MajorDecisionFoundKingdomActionAckStatusV1::
              rejected_before_submit);
    CHECK(fixture.stack_destroy_calls == 1);
    CHECK(fixture.heap_destroy_calls == 1);
    CHECK(fixture.queue_calls == 0);
  }
  {
    auto fixture = MakeFixture();
    fixture.queue_result = false;
    fixture.queue_consumes = false;
    bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
    RunSubmit(fixture, ack);
    CHECK(ack.status ==
          bridge::MajorDecisionFoundKingdomActionAckStatusV1::
              rejected_before_submit);
    CHECK(fixture.stack_destroy_calls == 1);
    CHECK(fixture.heap_destroy_calls == 1);
    CHECK(fixture.queue_calls == 1);
  }
  {
    auto fixture = MakeFixture();
    fixture.queue_result = false;
    fixture.queue_consumes = true;
    bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
    RunSubmit(fixture, ack);
    CHECK(ack.status ==
          bridge::MajorDecisionFoundKingdomActionAckStatusV1::
              rejected_before_submit);
    CHECK(fixture.stack_destroy_calls == 1);
    CHECK(fixture.heap_destroy_calls == 0);
    CHECK(fixture.queue_calls == 1);
  }
}

void TestIdentityDriftStopsBeforeConstruction() {
  auto fixture = MakeFixture();
  const std::uintptr_t drifted = kDefinition + 0x100;
  MapValue(fixture,
           bridge::kMajorDecisionFoundKingdomDecisionDatabaseSlotRvaV1,
           drifted);
  bridge::MajorDecisionFoundKingdomActionAckV1 ack{};
  RunSubmit(fixture, ack);
  CHECK(ack.status ==
        bridge::MajorDecisionFoundKingdomActionAckStatusV1::
            rejected_before_submit);
  CHECK(fixture.construct_calls == 0);
  CHECK(fixture.queue_calls == 0);
}

void TestAdmissionGates() {
  const auto run = [](auto mutate) {
    auto fixture = MakeFixture();
    bridge::MajorDecisionFoundKingdomActionEnvironmentV1 action_environment{};
    bridge::MajorDecisionFoundKingdomActionAccessV1 action_access{
        &fixture, &Capture, nullptr};
    bridge::MajorDecisionFoundKingdomNativeSubmitStateV1 state{};
    auto environment = Environment(fixture);
    mutate(fixture, environment);
    CHECK(!bridge::BindMajorDecisionFoundKingdomNativeSubmitV1(
        environment, state, action_environment, action_access));
    CHECK(!state.attached);
    CHECK(action_access.context == &fixture);
    CHECK(action_access.submit == nullptr);
  };

  run([](auto &fixture, auto &) {
    fixture.image[bridge::
                      kMajorDecisionFoundKingdomExecuteCommandConstructorRvaV1] ^=
        0xFF;
  });
  run([](auto &fixture, auto &) {
    const std::uintptr_t invalid = 0;
    MapValue(fixture,
             bridge::kMajorDecisionFoundKingdomExecuteCommandPrimaryVtableRvaV1 +
                 0x40,
             invalid);
  });
  run([](auto &fixture, auto &) {
    fixture.image[bridge::
                      kMajorDecisionFoundKingdomExecuteCommandTypeDescriptorRvaV1 +
                  0x10] = '?';
  });
  run([](auto &, auto &environment) {
    environment.admitted_executable_sha256 = "wrong";
  });

  auto fixture = MakeFixture();
  auto production = Environment(fixture);
  production.offline_fixture = false;
  production.module_base = 1;
  bridge::MajorDecisionFoundKingdomActionEnvironmentV1 action_environment{};
  bridge::MajorDecisionFoundKingdomActionAccessV1 action_access{
      &fixture, &Capture, nullptr};
  bridge::MajorDecisionFoundKingdomNativeSubmitStateV1 state{};
  CHECK(!bridge::BindMajorDecisionFoundKingdomNativeSubmitV1(
      production, state, action_environment, action_access));
}

} // namespace

int main() {
  TestHappyNativeLifecycle();
  TestLifecycleFailures();
  TestIdentityDriftStopsBeforeConstruction();
  TestAdmissionGates();
  if (failures != 0) {
    std::cerr << failures << " native submit test failure(s)\n";
    return 1;
  }
  return 0;
}
