#include "xar_bridge/military_preparation_summary_v1_binding.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>

namespace {

using xar::bridge::MilitaryPreparationFrameIdentityV1;
using xar::bridge::MilitaryPreparationSummaryBindingEnvironmentV1;
using xar::bridge::MilitaryPreparationSummaryBindingOperationsV1;
using xar::bridge::MilitaryPreparationSummaryBindingStateV1;
using xar::bridge::MilitaryPreparationSummaryEnvironmentV1;
using xar::bridge::MilitaryPreparationSummaryResultV1;

struct Fixture {
  std::array<MilitaryPreparationFrameIdentityV1, 2> frames{};
  std::array<std::int64_t, 10> values{};
  std::array<std::uintptr_t, 10> definitions{};
  std::array<const void *, 0x45> fixed_slots{};
  std::array<std::byte, 0xF18> database{};
  std::size_t frame_reads = 0;
  std::size_t construct_calls = 0;
  std::size_t destroy_calls = 0;
  std::size_t construct_support_calls = 0;
  std::size_t destroy_support_calls = 0;
  std::size_t character_calls = 0;
  std::size_t hash_calls = 0;
  std::size_t database_calls = 0;
  std::size_t lookup_calls = 0;
  std::size_t valid_calls = 0;
  std::size_t evaluate_calls = 0;
  std::size_t fail_evaluation_at = static_cast<std::size_t>(-1);
  bool construct_ok = true;
  bool construct_support_ok = true;
  bool destroy_ok = true;
  bool destroy_support_ok = true;
  bool character_ok = true;
};

template <typename Value>
void Store(std::array<std::byte, 0xF18> &target, std::size_t offset,
           const Value &value) {
  std::memcpy(target.data() + offset, &value, sizeof(value));
}

Fixture AvailableFixture() {
  Fixture fixture{};
  fixture.frames[0] = {42, 12345, 0x12345678, 9001, true};
  fixture.frames[1] = fixture.frames[0];
  fixture.values = {100000000, 120000000, 500000, 700000, 18000,
                    15000,     40000,     60000,  40000,  10000};
  for (std::size_t index = 0; index < fixture.definitions.size(); ++index) {
    fixture.definitions[index] = 0xA000 + index;
  }
  for (std::size_t index = 0; index < 5; ++index) {
    const auto slot = xar::bridge::kMilitaryPreparationStockFixedSlotsV1[index];
    fixture.fixed_slots[slot] = &fixture.definitions[index + 5];
  }
  void *const data = fixture.fixed_slots.data();
  const std::int32_t capacity = static_cast<std::int32_t>(
      fixture.fixed_slots.size());
  const std::int32_t count = capacity;
  Store(fixture.database,
        xar::bridge::kMilitaryPreparationRegistryDataOffsetV1, data);
  Store(fixture.database,
        xar::bridge::kMilitaryPreparationRegistryCapacityOffsetV1, capacity);
  Store(fixture.database,
        xar::bridge::kMilitaryPreparationRegistryCountOffsetV1, count);
  return fixture;
}

bool ReadFrame(void *context,
               MilitaryPreparationFrameIdentityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (fixture.frame_reads >= fixture.frames.size()) return false;
  output = fixture.frames[fixture.frame_reads++];
  return true;
}

bool Construct(void *context, std::uintptr_t module, void *storage) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.construct_calls;
  return module == 1 && storage != nullptr && fixture.construct_ok;
}

bool Destroy(void *context, std::uintptr_t module, void *storage) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.destroy_calls;
  return module == 1 && storage != nullptr && fixture.destroy_ok;
}

bool ConstructSupport(void *context, std::uintptr_t module, void *support_118,
                      void *support_2a8, void *internal_context,
                      void *root_scope) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.construct_support_calls;
  return module == 1 && support_118 != nullptr && support_2a8 != nullptr &&
         internal_context != nullptr && root_scope != nullptr &&
         fixture.construct_support_ok;
}

bool DestroySupport(void *context, std::uintptr_t module, void *support_118,
                    void *support_2a8) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.destroy_support_calls;
  return module == 1 && support_118 != nullptr && support_2a8 != nullptr &&
         fixture.destroy_support_ok;
}

void *ResolveCharacter(void *context, std::uintptr_t module,
                       std::int32_t character_id) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.character_calls;
  return module == 1 && fixture.character_ok && character_id == 0x12345678
             ? &fixture
             : nullptr;
}

bool HashName(void *context, std::uintptr_t module, std::string_view key,
              std::uint32_t &hash) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.hash_calls;
  if (module != 1) return false;
  for (std::size_t index = 0;
       index < xar::bridge::kMilitaryPreparationSummaryDefinitionKeysV1.size();
       ++index) {
    if (key ==
        xar::bridge::kMilitaryPreparationSummaryDefinitionKeysV1[index]) {
      hash = static_cast<std::uint32_t>(index);
      return true;
    }
  }
  return false;
}

void *GetDatabase(void *context, std::uintptr_t module) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.database_calls;
  return module == 1 ? fixture.database.data() : nullptr;
}

const void *Lookup(void *context, std::uintptr_t module, void *database,
                   std::uint32_t hash) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.lookup_calls;
  if (module != 1 || database != fixture.database.data() ||
      hash >= fixture.definitions.size()) {
    return nullptr;
  }
  return &fixture.definitions[hash];
}

bool DefinitionIsValid(void *context, const void *definition) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.valid_calls;
  for (const auto &candidate : fixture.definitions) {
    if (definition == &candidate) return true;
  }
  return false;
}

bool Evaluate(void *context, std::uintptr_t module, const void *definition,
              void *internal_context, std::int64_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto call = fixture.evaluate_calls++;
  if (module != 1 || internal_context == nullptr ||
      call == fixture.fail_evaluation_at) {
    return false;
  }
  for (std::size_t index = 0; index < fixture.definitions.size(); ++index) {
    if (definition == &fixture.definitions[index]) {
      output = fixture.values[index];
      return true;
    }
  }
  return false;
}

bool ReadMemory(void *, const void *address, void *output,
                std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
  std::memcpy(output, address, size);
  return true;
}

MilitaryPreparationSummaryBindingOperationsV1 Operations() {
  return {&Construct,
          &Destroy,
          &ConstructSupport,
          &DestroySupport,
          &ResolveCharacter,
          &HashName,
          &GetDatabase,
          &Lookup,
          &DefinitionIsValid,
          &Evaluate,
          &ReadMemory};
}

MilitaryPreparationSummaryEnvironmentV1 Core(Fixture &fixture) {
  MilitaryPreparationSummaryEnvironmentV1 core{};
  core.observer_enabled = true;
  core.exact_build_admitted = true;
  core.admitted_executable_sha256 =
      xar::bridge::kMilitaryPreparationSummaryExecutableSha256V1;
  core.current_thread_id = 77;
  core.application_main_thread_id = 77;
  core.offline_fixture = true;
  core.callback_context = &fixture;
  core.read_frame = &ReadFrame;
  return core;
}

MilitaryPreparationSummaryBindingEnvironmentV1 Binding(Fixture &fixture) {
  fixture.fixed_slots.fill(nullptr);
  for (std::size_t index = 0; index < 5; ++index) {
    const auto slot = xar::bridge::kMilitaryPreparationStockFixedSlotsV1[index];
    fixture.fixed_slots[slot] = &fixture.definitions[index + 5];
  }
  void *const data = fixture.fixed_slots.data();
  Store(fixture.database,
        xar::bridge::kMilitaryPreparationRegistryDataOffsetV1, data);
  MilitaryPreparationSummaryBindingEnvironmentV1 binding{};
  binding.binding_enabled = true;
  binding.exact_build_admitted = true;
  binding.admitted_executable_sha256 =
      xar::bridge::kMilitaryPreparationSummaryExecutableSha256V1;
  binding.offline_fixture = true;
  binding.module_base = 1;
  binding.operation_context = &fixture;
  binding.operations = Operations();
  return binding;
}

void TestDefaultOffAndExactGatesPreserveCore() {
  Fixture fixture = AvailableFixture();
  auto core = Core(fixture);
  const auto original_context = core.callback_context;
  const auto original_reader = core.read_frame;
  MilitaryPreparationSummaryBindingStateV1 state{};
  auto binding = Binding(fixture);

  binding.binding_enabled = false;
  assert(!xar::bridge::BindMilitaryPreparationSummaryV1(binding, state, core));
  assert(core.callback_context == original_context);
  assert(core.read_frame == original_reader);

  binding.binding_enabled = true;
  binding.admitted_executable_sha256 = "wrong";
  assert(!xar::bridge::BindMilitaryPreparationSummaryV1(binding, state, core));
  assert(core.callback_context == original_context);
  assert(fixture.frame_reads == 0);
  assert(fixture.construct_calls == 0);
}

void TestPairedSessionAndTenValues() {
  Fixture fixture = AvailableFixture();
  auto core = Core(fixture);
  MilitaryPreparationSummaryBindingStateV1 state{};
  assert(xar::bridge::BindMilitaryPreparationSummaryV1(
      Binding(fixture), state, core));

  MilitaryPreparationSummaryResultV1 result{};
  assert(xar::bridge::ReadMilitaryPreparationSummaryV1(core, 42, result));
  assert(result.observation_ready);
  assert(result.values.current_military_strength_raw == 100000000);
  assert(result.values.maa_gold_chance_below_ideal_raw == 10000);
  assert(fixture.frame_reads == 2);
  assert(fixture.character_calls == 1);
  assert(fixture.construct_calls == 1);
  assert(fixture.destroy_calls == 1);
  assert(fixture.construct_support_calls == 1);
  assert(fixture.destroy_support_calls == 1);
  assert(fixture.hash_calls == 20);
  assert(fixture.database_calls == 20);
  assert(fixture.lookup_calls == 20);
  assert(fixture.valid_calls == 20);
  assert(fixture.evaluate_calls == 20);
  assert(!state.session_active);
  assert(!state.scope_constructed);
  assert(!state.support_constructed);
}

void TestEvaluationAndTeardownFailurePublishNothing() {
  Fixture evaluation = AvailableFixture();
  evaluation.fail_evaluation_at = 4;
  auto core = Core(evaluation);
  MilitaryPreparationSummaryBindingStateV1 state{};
  assert(xar::bridge::BindMilitaryPreparationSummaryV1(
      Binding(evaluation), state, core));
  MilitaryPreparationSummaryResultV1 result{};
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(core, 42, result));
  assert(evaluation.destroy_calls == 1);
  assert(evaluation.destroy_support_calls == 1);
  assert(!result.observation_ready);
  assert(result.values.current_military_strength_raw == 0);

  Fixture teardown = AvailableFixture();
  teardown.destroy_ok = false;
  core = Core(teardown);
  state = {};
  assert(xar::bridge::BindMilitaryPreparationSummaryV1(
      Binding(teardown), state, core));
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(core, 42, result));
  assert(result.failure_flags ==
         xar::bridge::military_preparation_summary_failure_teardown);
  assert(!result.observation_ready);
  assert(result.values.current_military_strength_raw == 0);
  assert(teardown.destroy_calls == 1);
  assert(teardown.destroy_support_calls == 1);
}

void TestSupportConstructionFailureCleansBothOwners() {
  Fixture fixture = AvailableFixture();
  fixture.construct_support_ok = false;
  auto core = Core(fixture);
  MilitaryPreparationSummaryBindingStateV1 state{};
  assert(xar::bridge::BindMilitaryPreparationSummaryV1(
      Binding(fixture), state, core));
  MilitaryPreparationSummaryResultV1 result{};
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(core, 42, result));
  assert(result.failure_flags ==
         xar::bridge::military_preparation_summary_failure_session);
  assert(fixture.construct_calls == 1);
  assert(fixture.construct_support_calls == 1);
  assert(fixture.destroy_support_calls == 1);
  assert(fixture.destroy_calls == 1);
  assert(!result.observation_ready);
}

void TestStockSlotIdentityMismatchFailsClosed() {
  Fixture fixture = AvailableFixture();
  auto binding = Binding(fixture);
  fixture.fixed_slots[
      xar::bridge::kMilitaryPreparationStockFixedSlotsV1[0]] = nullptr;
  auto core = Core(fixture);
  MilitaryPreparationSummaryBindingStateV1 state{};
  assert(xar::bridge::BindMilitaryPreparationSummaryV1(
      binding, state, core));
  MilitaryPreparationSummaryResultV1 result{};
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(core, 42, result));
  assert(result.failure_flags ==
         xar::bridge::military_preparation_summary_failure_definition);
  assert(fixture.evaluate_calls == 5);
  assert(fixture.destroy_calls == 1);
  assert(fixture.destroy_support_calls == 1);
  assert(!result.observation_ready);
}

void TestProductionRejectsOverrides() {
  Fixture fixture = AvailableFixture();
  auto core = Core(fixture);
  auto binding = Binding(fixture);
  binding.offline_fixture = false;
  MilitaryPreparationSummaryBindingStateV1 state{};
  assert(!xar::bridge::BindMilitaryPreparationSummaryV1(binding, state, core));
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 2);
  std::ifstream fixture_input(argv[1], std::ios::binary);
  assert(fixture_input);
  const std::string fixture_text{std::istreambuf_iterator<char>(fixture_input),
                                 std::istreambuf_iterator<char>()};
  assert(fixture_text.find("\"construct_calls\": 1") != std::string::npos);
  assert(fixture_text.find("\"evaluate_calls\": 20") != std::string::npos);
  assert(fixture_text.find("\"current_military_strength_raw\": 100000000") !=
         std::string::npos);
  assert(fixture_text.find("\"maa_gold_chance_below_ideal_raw\": 10000") !=
         std::string::npos);
  static_assert(!xar::bridge::kMilitaryPreparationSummaryEnabledByDefaultV1);
  TestDefaultOffAndExactGatesPreserveCore();
  TestPairedSessionAndTenValues();
  TestEvaluationAndTeardownFailurePublishNothing();
  TestSupportConstructionFailureCleansBothOwners();
  TestStockSlotIdentityMismatchFailsClosed();
  TestProductionRejectsOverrides();
  return 0;
}
