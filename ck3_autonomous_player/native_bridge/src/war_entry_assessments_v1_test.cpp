#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace {

constexpr std::int32_t kActorId = 29'829;
constexpr std::int32_t kTarget1Id = 12'345;
constexpr std::int32_t kTarget2Id = 67'890;
constexpr std::int32_t kEffective2Id = 67'891;

template <typename Storage, typename Value>
void Write(Storage &storage, std::size_t offset, const Value &value) {
  if (offset + sizeof(value) > storage.size()) {
    std::abort();
  }
  std::memcpy(storage.data() + offset, &value, sizeof(value));
}

template <typename Storage>
void *Address(Storage &storage) {
  return static_cast<void *>(storage.data());
}

struct Fixture {
  std::array<std::byte, 0x1D0> actor{};
  std::array<std::byte, 0x1D0> target1{};
  std::array<std::byte, 0x1D0> target2{};
  std::array<std::byte, 0x1D0> effective2{};
  std::array<std::byte, 0x1D0> fallback{};
  std::array<std::byte, 0x320> actor_power{};
  std::array<std::byte, 0x320> target1_power{};
  std::array<std::byte, 0x320> target2_power{};
  std::array<std::byte, 0x320> effective2_power{};
  std::array<std::byte, 0x280> actor_ai_extension{};
  std::array<std::byte, 0x30> ai_context{};
  std::array<std::byte, 1> ai_context_map{};
  std::array<std::byte, 0x30> fallback_ai_context{};
  std::array<std::byte, 1> fallback_ai_context_map{};
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x30> character_store{};
  std::vector<std::byte> character_slots;

  void *game_state_slot = nullptr;
  void *character_store_slot = nullptr;
  void *character_fallback_slot = nullptr;
  void *actor_state_dependency_slot = nullptr;
  xar::game::WarEntryAssessmentFrameV1 frame{};

  std::int64_t actor_power_base = 1'200'000;
  std::int64_t actor_network = 300'000;
  std::int64_t target1_network = 100'000;
  std::int64_t target2_network = 500'000;
  std::int64_t target1_final = 1'050'000;
  std::int64_t target2_final = 2'400'000;
  bool bad_second_ratio = false;
  bool mutate_second_frame = false;
  bool mutate_network_configuration = false;
  bool drift_repeated_target_network = false;
  bool drift_repeated_native_output = false;
  bool drift_repeated_actor_base_state = false;
  bool drift_repeated_actor_flags_state = false;
  bool drift_actor_state_dependency_between_samples = false;
  bool drift_actor_state_dependency_during_builder = false;
  bool negative_actor_state_builder_power = false;
  bool mutate_actor_state_in_assessment = false;
  bool report_main_thread = true;
  std::int32_t capture_count = 0;
  std::int32_t effective_resolver_calls = 0;
  std::int32_t network_calls = 0;
  std::int32_t actor_state_builder_calls = 0;
  std::int32_t assessment_calls = 0;
  const xar::ck3_11906::NativeWarEntryActorStateV1 *last_actor_state =
      nullptr;
  std::vector<std::array<std::int32_t, 3>> observed_filters;

  Fixture() : character_slots(70'000U * 0x10U) {
    const auto initialize_character =
        [](auto &character, std::int32_t id, auto &power,
           std::int64_t power_raw) {
          Write(character, 0x18, id);
          void *power_pointer = Address(power);
          Write(character, 0x1B8, power_pointer);
          void *death_marker = nullptr;
          Write(character, 0x1C8, death_marker);
          Write(power, 0x308, power_raw);
        };
    initialize_character(actor, kActorId, actor_power, 1'200'000);
    initialize_character(target1, kTarget1Id, target1_power, 900'000);
    initialize_character(target2, kTarget2Id, target2_power, 1'800'000);
    initialize_character(effective2, kEffective2Id, effective2_power,
                         2'000'000);
    const std::int32_t fallback_id = -1;
    Write(fallback, 0x18, fallback_id);

    const auto put_character = [this](std::int32_t id, void *character) {
      const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
      Write(character_slots, static_cast<std::size_t>(index) * 0x10 + 0x08,
            character);
    };
    put_character(kActorId, Address(actor));
    put_character(kTarget1Id, Address(target1));
    put_character(kTarget2Id, Address(target2));
    put_character(kEffective2Id, Address(effective2));

    void *slots = Address(character_slots);
    const std::int32_t capacity = 70'000;
    Write(character_store, 0x20, slots);
    Write(character_store, 0x2C, capacity);
    character_store_slot = Address(character_store);
    character_fallback_slot = Address(fallback);

    void *actor_extension_pointer = Address(actor_ai_extension);
    Write(actor, 0x1A8, actor_extension_pointer);
    void *ai_context_pointer = Address(ai_context);
    Write(actor_ai_extension, 0x278, ai_context_pointer);
    Write(ai_context, 0x08, actor_power_base);
    const std::uint8_t actor_context_flags = 0x05;
    Write(ai_context, 0x16, actor_context_flags);
    void *actor_pointer = Address(actor);
    Write(ai_context, 0x18, actor_pointer);
    void *ai_context_map_pointer = Address(ai_context_map);
    Write(ai_context, 0x20, ai_context_map_pointer);

    const std::int64_t fallback_power = actor_power_base;
    Write(fallback_ai_context, 0x08, fallback_power);
    const std::uint8_t fallback_flags = 0x05;
    Write(fallback_ai_context, 0x16, fallback_flags);
    void *fallback_character_pointer = Address(fallback);
    Write(fallback_ai_context, 0x18, fallback_character_pointer);
    void *fallback_map_pointer = Address(fallback_ai_context_map);
    Write(fallback_ai_context, 0x20, fallback_map_pointer);
    actor_state_dependency_slot = Address(game_state);
    game_state_slot = Address(game_state);

    frame.snapshot_revision = 74;
    frame.date_raw = 53'175'816;
    frame.paused = true;
    frame.map_ready = true;
    frame.actor_alive = true;
    frame.actor_character_id = kActorId;
    // Multiple declarable CB rows may share one target. The query contract
    // deduplicates its request, not the discovery snapshot.
    frame.declarable_target_character_ids = {kTarget1Id, kTarget2Id,
                                              kTarget1Id};
  }

  xar::ck3_11906::WarEntryNativeEnvironmentV1 Environment() {
    xar::ck3_11906::WarEntryNativeEnvironmentV1 output{};
    output.game_state_slot = &game_state_slot;
    output.character_storage_slot = &character_store_slot;
    output.character_fallback_slot = &character_fallback_slot;
    output.actor_state_dependency_slot = &actor_state_dependency_slot;
    output.offline_fixture_function_overrides = true;
    return output;
  }

  xar::ck3_11906::WarEntryAssessmentAccessV1 Access();

  xar::ck3_11906::WarEntryAssessmentsV1Request Request(
      std::vector<std::int32_t> targets = {kTarget2Id}) const {
    return {74, std::move(targets)};
  }
};

thread_local Fixture *g_fixture = nullptr;

bool CaptureFrame(void *context,
                  xar::game::WarEntryAssessmentFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.capture_count;
  output = fixture.frame;
  if (fixture.mutate_second_frame && fixture.capture_count > 1) {
    ++output.snapshot_revision;
  }
  if (fixture.drift_actor_state_dependency_between_samples &&
      fixture.capture_count == 2) {
    fixture.actor_state_dependency_slot = Address(fixture.fallback);
  }
  return true;
}

bool IsMainThread(void *context) noexcept {
  return static_cast<Fixture *>(context)->report_main_thread;
}

#if defined(_MSC_VER)
#define TEST_FASTCALL __fastcall
#else
#define TEST_FASTCALL
#endif

void *TEST_FASTCALL FakeEffectiveTarget(void *actor, void *target,
                                        std::uint32_t unused_home,
                                        bool alternate_mode) {
  auto &fixture = *g_fixture;
  ++fixture.effective_resolver_calls;
  if (actor != Address(fixture.actor) || unused_home != 0 || alternate_mode) {
    return nullptr;
  }
  if (target == Address(fixture.target1)) {
    return Address(fixture.target1);
  }
  if (target == Address(fixture.target2)) {
    return Address(fixture.effective2);
  }
  return nullptr;
}

void TEST_FASTCALL FakeNetworkCollector(
    void *root,
    xar::ck3_11906::NativeWarEntryNetworkConfigurationV1 *configuration) {
  auto &fixture = *g_fixture;
  ++fixture.network_calls;
  if (configuration == nullptr || configuration->root_character == nullptr ||
      configuration->filter_a == nullptr ||
      configuration->filter_b == nullptr ||
      configuration->filter_c == nullptr ||
      configuration->accumulator == nullptr ||
      *configuration->root_character != root) {
    return;
  }
  const std::array filters{*configuration->filter_a,
                           *configuration->filter_b,
                           *configuration->filter_c};
  fixture.observed_filters.push_back(filters);
  if (root == Address(fixture.actor) &&
      filters == std::array<std::int32_t, 3>{1, 1, 1}) {
    *configuration->accumulator += fixture.actor_network;
  } else if (root == Address(fixture.target1) &&
             filters == std::array<std::int32_t, 3>{0, 0, 0}) {
    *configuration->accumulator +=
        fixture.target1_network +
        (fixture.drift_repeated_target_network && fixture.network_calls > 2
             ? 1
             : 0);
  } else if (root == Address(fixture.effective2) &&
             filters == std::array<std::int32_t, 3>{0, 0, 0}) {
    *configuration->accumulator +=
        fixture.target2_network +
        (fixture.drift_repeated_target_network && fixture.network_calls > 2
             ? 1
             : 0);
  }
  if (fixture.mutate_network_configuration) {
    *configuration->filter_a = 9;
  }
}

void TEST_FASTCALL FakeActorStateBuilder(
    void *actor,
    xar::ck3_11906::NativeWarEntryActorStateV1 *output) {
  auto &fixture = *g_fixture;
  ++fixture.actor_state_builder_calls;
  if (actor != Address(fixture.actor) || output == nullptr) {
    return;
  }
  output->power_base_raw =
      (fixture.negative_actor_state_builder_power ? -1
                                                  : fixture.actor_power_base) +
      (fixture.drift_repeated_actor_base_state &&
               fixture.actor_state_builder_calls > 1
           ? 1
           : 0);
  output->native_state_08_raw = 2;
  output->native_state_0c_raw = 0x1234;
  output->native_flags_raw =
      static_cast<std::uint8_t>(0x05U ^
                                (fixture.drift_repeated_actor_flags_state &&
                                         fixture.actor_state_builder_calls > 1
                                     ? 0x10U
                                     : 0U));
  // +0x0F is intentionally left untouched, exactly like 0x18784D0. The
  // reader must have zero-initialized the complete caller-owned State16.
  fixture.last_actor_state = output;
  if (fixture.drift_actor_state_dependency_during_builder) {
    fixture.actor_state_dependency_slot = Address(fixture.fallback);
  }
}

void TEST_FASTCALL FakeAssessment(
    void *actor,
    const xar::ck3_11906::NativeWarEntryActorStateV1 *actor_state,
    void *effective_target,
    xar::ck3_11906::NativeWarEntryAssessmentOutputV1 *output,
    const std::int64_t *distance_override,
    std::int32_t include_network_mode) {
  auto &fixture = *g_fixture;
  ++fixture.assessment_calls;
  std::int64_t observed_power = -1;
  std::uint8_t observed_flags = 0;
  void *observed_map = nullptr;
  if (actor_state != nullptr) {
    observed_power = actor_state->power_base_raw;
    observed_flags = actor_state->native_flags_raw;
  }
  void *extension = nullptr;
  std::memcpy(&extension, fixture.actor.data() + 0x1A8,
              sizeof(extension));
  const std::byte *context = fixture.fallback_ai_context.data();
  if (extension != nullptr) {
    void *resolved_context = nullptr;
    std::memcpy(&resolved_context,
                static_cast<const std::byte *>(extension) + 0x278,
                sizeof(resolved_context));
    context = static_cast<const std::byte *>(resolved_context);
  }
  if (context != nullptr) {
    std::memcpy(&observed_map, context + 0x20, sizeof(observed_map));
  }
  const auto expected_flags = static_cast<std::uint8_t>(
      0x05U ^ (fixture.drift_repeated_actor_flags_state &&
                       fixture.actor_state_builder_calls > 1
                   ? 0x10U
                   : 0U));
  if (actor != Address(fixture.actor) ||
      actor_state == nullptr || actor_state != fixture.last_actor_state ||
      observed_power != fixture.actor_power_base +
                            (fixture.drift_repeated_actor_base_state &&
                                     fixture.actor_state_builder_calls > 1
                                 ? 1
                                 : 0) ||
      observed_flags != expected_flags || actor_state->native_state_08_raw != 2 ||
      actor_state->native_state_0c_raw != 0x1234 ||
      actor_state->native_state_0f_raw != 0 ||
      output == nullptr ||
      distance_override != nullptr || include_network_mode != 1) {
    if (output != nullptr) {
      output->distance_raw = -1;
    }
    return;
  }
  const auto actor_total = observed_power + fixture.actor_network;
  if (effective_target == Address(fixture.target1)) {
    output->distance_raw = 4'200'000;
    output->target_power_total_raw = fixture.target1_final;
    output->actual_power_ratio_raw =
        actor_total <= 0
            ? fixture.target1_final
            : fixture.target1_final * 100'000 / actor_total;
    output->target_ai_context_actor_entry_raw = -12;
    output->actor_ai_context_target_entry_raw = observed_map == nullptr ? 0 : 7;
    output->native_flags_raw = 137;
  } else if (effective_target == Address(fixture.effective2)) {
    output->distance_raw = 8'000'000;
    output->target_power_total_raw = fixture.target2_final;
    output->actual_power_ratio_raw =
        actor_total <= 0
            ? fixture.target2_final
            : fixture.target2_final * 100'000 / actor_total;
    if (fixture.bad_second_ratio) {
      ++output->actual_power_ratio_raw;
    }
    output->target_ai_context_actor_entry_raw = -3;
    output->actor_ai_context_target_entry_raw =
        observed_map == nullptr ? 0 : 22;
    output->native_flags_raw = 99;
  } else {
    output->distance_raw = -1;
  }
  if (fixture.drift_repeated_native_output &&
      fixture.assessment_calls > 1 && output->distance_raw >= 0) {
    output->native_flags_raw ^= 1U;
  }
  if (fixture.mutate_actor_state_in_assessment && actor_state != nullptr) {
    ++const_cast<xar::ck3_11906::NativeWarEntryActorStateV1 *>(actor_state)
          ->native_state_08_raw;
  }
}

#undef TEST_FASTCALL

xar::ck3_11906::WarEntryAssessmentAccessV1 Fixture::Access() {
  return {this, CaptureFrame, IsMainThread, nullptr};
}

void BindFixtureFunctions(
    Fixture &fixture,
    xar::ck3_11906::WarEntryNativeEnvironmentV1 &environment) {
  g_fixture = &fixture;
  environment.actor_state_builder = FakeActorStateBuilder;
  environment.assessment = FakeAssessment;
  environment.network_collector = FakeNetworkCollector;
  environment.effective_target_resolver = FakeEffectiveTarget;
}

std::string ReadFile(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  std::string output{std::istreambuf_iterator<char>(stream),
                     std::istreambuf_iterator<char>()};
  while (!output.empty() &&
         (output.back() == '\r' || output.back() == '\n')) {
    output.pop_back();
  }
  return output;
}

bool TestLiteralContract() {
  using namespace xar::ck3_11906;
  const std::vector<std::int32_t> expected{kTarget1Id};
  const auto literal = EncodeWarEntryAssessmentsV1Step(expected);
  std::vector<std::int32_t> parsed;
  if (literal != "query-war-entry-assessments-v1-1-12345" ||
      !ParseWarEntryAssessmentsV1Step(literal, parsed) || parsed != expected) {
    return false;
  }
  constexpr std::array<std::string_view, 13> rejected{
      "query-war-entry-assessments-v1-0-12345",
      "query-war-entry-assessments-v1-1-0",
      "query-war-entry-assessments-v1-1--1",
      "query-war-entry-assessments-v1-01-12345",
      "query-war-entry-assessments-v1-1-012345",
      "query-war-entry-assessments-v1-2-12345",
      "query-war-entry-assessments-v1-1-12345-67890",
      "query-war-entry-assessments-v1-2-12345-12345",
      "query-war-entry-assessments-v1-2-12345-67890",
      "query-war-entry-assessments-v1-1-2147483648",
      "query-war-entry-assessments-v1-1-12345-",
      "query-war-entry-assessments-v1-x-12345",
      "query-war-entry-assessments-v1-65-1",
  };
  for (const auto value : rejected) {
    parsed = {1};
    if (ParseWarEntryAssessmentsV1Step(value, parsed) || !parsed.empty()) {
      return false;
    }
  }
  return EncodeWarEntryAssessmentsV1Step({kTarget1Id, kTarget2Id}).empty() &&
         EncodeWarEntryAssessmentsV1Step({kTarget1Id, kTarget1Id}).empty() &&
         kWarEntryAssessmentsV1CapabilityAdvertised;
}

bool TestExactBinder() {
  using namespace xar::ck3_11906;
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto environment = BindWarEntryNativeEnvironmentV1(base);
  return environment.module_base == base &&
         reinterpret_cast<std::uintptr_t>(environment.game_state_slot) ==
             base + kWarEntryGameStateSlotRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.character_storage_slot) ==
             base + kWarEntryCharacterStorageSlotRva &&
         reinterpret_cast<std::uintptr_t>(
              environment.character_fallback_slot) ==
              base + kWarEntryCharacterFallbackSlotRva &&
          reinterpret_cast<std::uintptr_t>(
              environment.actor_state_dependency_slot) ==
              base + kWarEntryActorStateDependencySlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.actor_state_builder) ==
             base + kWarEntryActorStateBuilderRva &&
         reinterpret_cast<std::uintptr_t>(environment.assessment) ==
             base + kWarEntryAssessmentRva &&
         reinterpret_cast<std::uintptr_t>(environment.network_collector) ==
             base + kWarEntryNetworkCollectorRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.effective_target_resolver) ==
             base + kWarEntryEffectiveTargetResolverRva &&
         !environment.offline_fixture_function_overrides;
}

bool TestHappyPath(const char *golden_path) {
  using namespace xar::ck3_11906;
  Fixture fixture;
  auto environment = fixture.Environment();
  BindFixtureFunctions(fixture, environment);
  auto access = fixture.Access();
  xar::game::WarEntryAssessmentsV1 output{};
  const auto read_result = ReadWarEntryAssessmentsV1(
      environment, access, fixture.Request(), output);
  if (read_result !=
          xar::game::ReadWarEntryAssessmentsV1Result::available ||
      !output.available || output.assessments.size() != 1 ||
      output.assessments[0].target_adjustment_delta_raw != -100'000 ||
      fixture.capture_count != 3 || fixture.effective_resolver_calls != 3 ||
      fixture.network_calls != 4 || fixture.actor_state_builder_calls != 2 ||
      fixture.assessment_calls != 2 ||
      fixture.observed_filters !=
          std::vector<std::array<std::int32_t, 3>>{
              {0, 0, 0}, {1, 1, 1}, {0, 0, 0}, {1, 1, 1}}) {
    std::cerr << "happy-path reader mismatch: result="
              << static_cast<int>(read_result)
              << " available=" << output.available
              << " rows=" << output.assessments.size()
              << " capture=" << fixture.capture_count
              << " resolver=" << fixture.effective_resolver_calls
              << " network=" << fixture.network_calls
              << " builder=" << fixture.actor_state_builder_calls
              << " assessment=" << fixture.assessment_calls
              << " filters=" << fixture.observed_filters.size()
              << " stage=" << output.unavailable_stage << '\n';
    return false;
  }
  const auto serialized = SerializeWarEntryAssessmentsV1(output);
  const auto golden = ReadFile(golden_path);
  if (serialized.empty() || serialized != golden) {
    std::cerr << "happy-path golden mismatch\nactual: " << serialized
              << "\nexpected: " << golden << '\n';
    return false;
  }
  return true;
}

bool TestAtomicFailures() {
  using namespace xar::ck3_11906;
  {
    Fixture fixture;
    fixture.report_main_thread = false;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage != "main_thread_required" ||
        fixture.capture_count != 0 || fixture.network_calls != 0 ||
        fixture.assessment_calls != 0) {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.bad_second_ratio = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.available || !output.assessments.empty() ||
        !output.requested_target_character_ids.empty() ||
        output.unavailable_stage != "native_ratio_cross_check" ||
        !SerializeWarEntryAssessmentsV1(output).empty()) {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.actor_state_dependency_slot = nullptr;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage != "actor_state_builder_dependency" ||
        fixture.actor_state_builder_calls != 0 ||
        fixture.assessment_calls != 0) {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.drift_actor_state_dependency_during_builder = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage !=
            "actor_state_builder_dependency_drift" ||
        fixture.actor_state_builder_calls != 1 ||
        fixture.assessment_calls != 0) {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.negative_actor_state_builder_power = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage != "actor_state_builder_domain" ||
        fixture.actor_state_builder_calls != 1 ||
        fixture.assessment_calls != 0) {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.mutate_second_frame = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage != "same_frame_stamp") {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.frame.declarable_target_character_ids = {kTarget1Id};
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage != "target_not_declarable") {
      return false;
    }
  }
  {
    Fixture fixture;
    void *no_extension = nullptr;
    Write(fixture.actor, 0x1A8, no_extension);
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::available ||
        !output.available || output.assessments.size() != 1 ||
        output.assessments.front().actor_power_base_raw !=
            fixture.actor_power_base ||
        output.assessments.front().actor_ai_context_target_entry_raw != 22) {
      return false;
    }
  }
  {
    Fixture fixture;
    void *no_map = nullptr;
    Write(fixture.ai_context, 0x20, no_map);
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::available ||
        !output.available || output.assessments.size() != 1 ||
        output.assessments.front().actor_ai_context_target_entry_raw != 0) {
      return false;
    }
  }
  {
    Fixture fixture;
    void *wrong_actor = Address(fixture.target1);
    Write(fixture.ai_context, 0x18, wrong_actor);
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::available ||
        !output.available || output.assessments.size() != 1 ||
        output.assessments.front().actor_ai_context_target_entry_raw != 22) {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.mutate_network_configuration = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage != "target_network_collector") {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.drift_repeated_target_network = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.available || !output.assessments.empty() ||
        output.unavailable_stage != "same_frame_native_sample") {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.drift_repeated_actor_base_state = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.available || !output.assessments.empty() ||
        output.unavailable_stage != "same_frame_actor_state_builder") {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.drift_repeated_actor_flags_state = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.available || !output.assessments.empty() ||
        output.unavailable_stage != "same_frame_actor_state_builder") {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.drift_actor_state_dependency_between_samples = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.available || !output.assessments.empty() ||
        output.unavailable_stage !=
            "same_frame_actor_state_builder_dependency") {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.mutate_actor_state_in_assessment = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.available || !output.assessments.empty() ||
        output.unavailable_stage != "actor_state_builder_mutated") {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.drift_repeated_native_output = true;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access, fixture.Request(),
                                  output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.available || !output.assessments.empty() ||
        output.unavailable_stage != "same_frame_native_sample") {
      return false;
    }
  }
  return true;
}

bool TestNativeNonpositiveActorBranchAndOverflow() {
  using namespace xar::ck3_11906;
  {
    Fixture fixture;
    fixture.actor_power_base = 0;
    fixture.actor_network = 0;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    const auto request = fixture.Request({kTarget1Id});
    if (ReadWarEntryAssessmentsV1(environment, access, request, output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::available ||
        output.assessments.front().actor_power_total_raw != 0 ||
        output.assessments.front().actual_power_ratio_raw !=
            fixture.target1_final) {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.actor_network = -1;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access,
                                  fixture.Request({kTarget1Id}), output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage != "network_contribution_domain") {
      return false;
    }
  }
  {
    Fixture fixture;
    fixture.actor_power_base = std::numeric_limits<std::int64_t>::max();
    fixture.actor_network = 1;
    auto environment = fixture.Environment();
    BindFixtureFunctions(fixture, environment);
    auto access = fixture.Access();
    xar::game::WarEntryAssessmentsV1 output{};
    if (ReadWarEntryAssessmentsV1(environment, access,
                                  fixture.Request({kTarget1Id}), output) !=
            xar::game::ReadWarEntryAssessmentsV1Result::unavailable ||
        output.unavailable_stage != "network_checked_sum") {
      return false;
    }
  }
  return true;
}

bool TestSerializerRejectsPartial() {
  xar::game::WarEntryAssessmentsV1 partial{};
  partial.available = true;
  partial.snapshot_revision = 74;
  partial.date_raw = 53'175'816;
  partial.actor_character_id = kActorId;
  partial.requested_target_character_ids = {kTarget1Id};
  partial.readiness = {true, true, true, true, true, true, true, true};
  return xar::ck3_11906::SerializeWarEntryAssessmentsV1(partial).empty();
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    return 1;
  }
  if (!TestLiteralContract()) {
    return 2;
  }
  if (!TestExactBinder()) {
    return 3;
  }
  if (!TestHappyPath(argv[1])) {
    return 4;
  }
  if (!TestAtomicFailures()) {
    return 5;
  }
  if (!TestNativeNonpositiveActorBranchAndOverflow()) {
    return 6;
  }
  if (!TestSerializerRejectsPartial()) {
    return 7;
  }
  return 0;
}
