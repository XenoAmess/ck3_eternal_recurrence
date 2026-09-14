#include "xar_bridge/military_preparation_summary_v1.hpp"
#include "xar_bridge/military_preparation_summary_v1_serializer.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

using xar::bridge::MilitaryPreparationFrameIdentityV1;
using xar::bridge::MilitaryPreparationSummaryEnvironmentV1;
using xar::bridge::MilitaryPreparationSummaryResultV1;
using xar::bridge::MilitaryPreparationSummaryStatusV1;

struct Fixture {
  std::array<MilitaryPreparationFrameIdentityV1, 2> frames{};
  std::array<std::array<std::int64_t, 10>, 2> values{};
  std::array<std::uintptr_t, 10> definitions{};
  std::size_t frame_reads = 0;
  std::size_t begin_calls = 0;
  std::size_t end_calls = 0;
  std::size_t resolve_calls = 0;
  std::size_t validate_calls = 0;
  std::size_t evaluate_calls = 0;
  std::size_t evaluate_failure_at = static_cast<std::size_t>(-1);
  bool frame_readable = true;
  bool begin_ok = true;
  bool end_ok = true;
  std::uint64_t session_marker = 0xC0DEC0DEULL;
};

bool ReadFrame(void *context,
               MilitaryPreparationFrameIdentityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (!fixture.frame_readable || fixture.frame_reads >= fixture.frames.size()) {
    return false;
  }
  output = fixture.frames[fixture.frame_reads++];
  return true;
}

bool BeginSession(void *context, std::int32_t played_character_id,
                  void *&session) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.begin_calls;
  if (!fixture.begin_ok || played_character_id != 0x12345678) {
    return false;
  }
  session = &fixture.session_marker;
  return true;
}

bool EndSession(void *context, void *session) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.end_calls;
  return session == &fixture.session_marker && fixture.end_ok;
}

bool ResolveDefinition(void *context, std::string_view key,
                       const void *&definition) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto index = fixture.resolve_calls % fixture.definitions.size();
  if (key != xar::bridge::kMilitaryPreparationSummaryDefinitionKeysV1[index]) {
    return false;
  }
  definition = &fixture.definitions[index];
  ++fixture.resolve_calls;
  return true;
}

bool DefinitionIsValid(void *context, const void *definition) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto index = fixture.validate_calls % fixture.definitions.size();
  ++fixture.validate_calls;
  return definition == &fixture.definitions[index];
}

bool EvaluateFixed(void *context, const void *definition, void *session,
                   std::int64_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  const auto call = fixture.evaluate_calls++;
  const auto pass = call / fixture.definitions.size();
  const auto index = call % fixture.definitions.size();
  if (call == fixture.evaluate_failure_at || pass >= fixture.values.size() ||
      definition != &fixture.definitions[index] ||
      session != &fixture.session_marker) {
    return false;
  }
  output = fixture.values[pass][index];
  return true;
}

Fixture AvailableFixture() {
  Fixture fixture{};
  fixture.frames[0] = {42, 12345, 0x12345678, 9001, true};
  fixture.frames[1] = fixture.frames[0];
  fixture.values[0] = {100000000, 120000000, 500000, 700000, 18000,
                       15000,     40000,     60000,  40000,  10000};
  fixture.values[1] = fixture.values[0];
  for (std::size_t index = 0; index < fixture.definitions.size(); ++index) {
    fixture.definitions[index] = 0x1000 + index;
  }
  return fixture;
}

MilitaryPreparationSummaryEnvironmentV1 Environment(Fixture &fixture) {
  MilitaryPreparationSummaryEnvironmentV1 environment{};
  environment.observer_enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      xar::bridge::kMilitaryPreparationSummaryExecutableSha256V1;
  environment.current_thread_id = 77;
  environment.application_main_thread_id = 77;
  environment.offline_fixture = true;
  environment.callback_context = &fixture;
  environment.read_frame = &ReadFrame;
  environment.begin_session = &BeginSession;
  environment.end_session = &EndSession;
  environment.resolve_definition = &ResolveDefinition;
  environment.definition_is_valid = &DefinitionIsValid;
  environment.evaluate_fixed = &EvaluateFixed;
  return environment;
}

void AssertNoStateCallbacks(const Fixture &fixture) {
  assert(fixture.frame_reads == 0);
  assert(fixture.begin_calls == 0);
  assert(fixture.end_calls == 0);
  assert(fixture.resolve_calls == 0);
  assert(fixture.validate_calls == 0);
  assert(fixture.evaluate_calls == 0);
}

void AssertNoPublishedValues(const MilitaryPreparationSummaryResultV1 &result) {
  assert(!result.observation_ready);
  assert(result.values.current_military_strength_raw == 0);
  assert(result.values.max_military_strength_raw == 0);
  assert(result.values.number_of_knights_raw == 0);
  assert(result.values.max_number_of_knights_raw == 0);
  assert(result.values.maa_gold_expense_relative_raw == 0);
  assert(result.frame.snapshot_revision == 0);
}

void TestAdmissionFailuresDoNotReadState() {
  static_assert(!xar::bridge::kMilitaryPreparationSummaryEnabledByDefaultV1);
  Fixture fixture = AvailableFixture();
  auto environment = Environment(fixture);
  MilitaryPreparationSummaryResultV1 result{};

  environment.observer_enabled = false;
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(environment, 42,
                                                        result));
  assert(result.status == MilitaryPreparationSummaryStatusV1::disabled);
  AssertNoStateCallbacks(fixture);

  environment.observer_enabled = true;
  environment.admitted_executable_sha256 = "wrong-build";
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(environment, 42,
                                                        result));
  AssertNoStateCallbacks(fixture);

  environment.admitted_executable_sha256 =
      xar::bridge::kMilitaryPreparationSummaryExecutableSha256V1;
  environment.evaluate_fixed = nullptr;
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(environment, 42,
                                                        result));
  AssertNoStateCallbacks(fixture);

  environment.evaluate_fixed = &EvaluateFixed;
  environment.current_thread_id = 78;
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(environment, 42,
                                                        result));
  AssertNoStateCallbacks(fixture);
}

void TestAvailableTwoPassCaptureMatchesFixture(const char *fixture_path) {
  Fixture fixture = AvailableFixture();
  const auto environment = Environment(fixture);
  MilitaryPreparationSummaryResultV1 result{};
  assert(xar::bridge::ReadMilitaryPreparationSummaryV1(environment, 42,
                                                       result));
  assert(result.status == MilitaryPreparationSummaryStatusV1::available);
  assert(result.observation_ready);
  assert(result.offline_fixture);
  assert(result.failure_flags == 0);
  assert(result.frame == fixture.frames[0]);
  assert(result.values.current_military_strength_raw == 100000000);
  assert(result.values.maa_gold_chance_below_ideal_raw == 10000);
  assert(fixture.frame_reads == 2);
  assert(fixture.begin_calls == 1);
  assert(fixture.end_calls == 1);
  assert(fixture.resolve_calls == 20);
  assert(fixture.validate_calls == 20);
  assert(fixture.evaluate_calls == 20);

  std::ifstream input(fixture_path, std::ios::binary);
  assert(input);
  std::string expected{std::istreambuf_iterator<char>(input),
                       std::istreambuf_iterator<char>()};
  while (!expected.empty() &&
         (expected.back() == '\n' || expected.back() == '\r')) {
    expected.pop_back();
  }
  assert(xar::bridge::SerializeMilitaryPreparationSummaryV1(result) ==
         expected);
}

void TestRuntimeFailureStopsAndPublishesNoPartialState() {
  Fixture fixture = AvailableFixture();
  fixture.evaluate_failure_at = 3;
  MilitaryPreparationSummaryResultV1 result{};
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(
      Environment(fixture), 42, result));
  assert(result.failure_flags ==
         xar::bridge::military_preparation_summary_failure_evaluation);
  assert(fixture.frame_reads == 1);
  assert(fixture.evaluate_calls == 4);
  assert(fixture.end_calls == 1);
  AssertNoPublishedValues(result);
}

void TestUnstableValueAndFrameAreRejected() {
  Fixture unstable = AvailableFixture();
  unstable.values[1][5] += 1;
  MilitaryPreparationSummaryResultV1 result{};
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(
      Environment(unstable), 42, result));
  assert(result.failure_flags ==
         xar::bridge::military_preparation_summary_failure_unstable_values);
  assert(unstable.frame_reads == 1);
  assert(unstable.end_calls == 1);
  AssertNoPublishedValues(result);

  Fixture changed = AvailableFixture();
  changed.frames[1].gameplay_rng_fingerprint += 1;
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(
      Environment(changed), 42, result));
  assert(result.failure_flags ==
         xar::bridge::military_preparation_summary_failure_frame_changed);
  assert(changed.frame_reads == 2);
  assert(changed.end_calls == 1);
  AssertNoPublishedValues(result);
}

void TestTeardownFailureRejectsCompletedRead() {
  Fixture fixture = AvailableFixture();
  fixture.end_ok = false;
  MilitaryPreparationSummaryResultV1 result{};
  assert(!xar::bridge::ReadMilitaryPreparationSummaryV1(
      Environment(fixture), 42, result));
  assert(result.failure_flags ==
         xar::bridge::military_preparation_summary_failure_teardown);
  AssertNoPublishedValues(result);
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 2);
  TestAdmissionFailuresDoNotReadState();
  TestAvailableTwoPassCaptureMatchesFixture(argv[1]);
  TestRuntimeFailureStopsAndPublishesNoPartialState();
  TestUnstableValueAndFrameAreRejected();
  TestTeardownFailureRejectsCompletedRead();
  return 0;
}
