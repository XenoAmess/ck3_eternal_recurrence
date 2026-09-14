#include "xar_bridge/steward_develop_county_candidates_v1.hpp"

#include <cstdint>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

using Failure = xar::game::StewardDevelopCountyFailureReasonV1;
using Result = xar::game::ReadStewardDevelopCountyCandidatesResultV1;

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "steward develop county core fixture failed at line " +
        std::to_string(location.line()));
  }
}

struct Fixture {
  xar::game::StewardDevelopCountyCandidatesFrameV1 frame{
      77, 53'175'816, true, true, true, true, 0x0100002A};
  xar::ck3_11906::StewardDevelopCountyCandidatesSourceSampleV1 sample;
  int source_reads = 0;
  bool drift_identity = false;
  bool drift_value = false;
  bool drift_frame = false;

  Fixture() {
    sample.player_character_id = frame.played_character_id;
    sample.steward_character_id = 0x02000011;
    sample.player_identity_round_trip = true;
    sample.steward_identity_round_trip = true;
    sample.shown = true;
    sample.valid = true;
    sample.steward_increase_development_value_raw = 9'000'000;
    sample.current_gold_raw = 15'000'000;
    sample.has_active_improve_development_directive = true;
    xar::ck3_11906::StewardDevelopCountyCandidateSourceRowV1 row;
    row.candidate.county_title_id = 0x0300000A;
    row.candidate.capital_province_id = 921;
    row.candidate.holder_character_id = frame.played_character_id;
    row.candidate.is_player_capital = true;
    row.candidate.directly_held_by_player = true;
    row.candidate.native_legal = true;
    row.candidate.development_level_raw = 12'000'000;
    row.candidate.development_progress_raw = 35'000;
    row.candidate.monthly_development_rate_raw = 8'250;
    row.candidate.max_development_level_raw = 100'000'000;
    row.candidate.terrain_key = "plains";
    row.candidate.same_culture_as_player = true;
    row.candidate.cultural_acceptance_threshold_passed = true;
    row.county_title_identity_round_trip = true;
    row.capital_province_identity_round_trip = true;
    row.holder_character_identity_round_trip = true;
    sample.candidates.push_back(row);
  }
};

bool MainThread(void *) noexcept { return true; }

bool CaptureFrame(
    void *context,
    xar::game::StewardDevelopCountyCandidatesFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.frame;
  if (fixture.drift_frame && fixture.source_reads >= 2) {
    ++output.snapshot_revision;
  }
  return true;
}

bool ReadSource(
    void *context,
    xar::ck3_11906::StewardDevelopCountyCandidatesSourceSampleV1
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.sample;
  ++fixture.source_reads;
  if (fixture.source_reads == 2 && fixture.drift_identity) {
    ++output.candidates.front().candidate.county_title_id;
  }
  if (fixture.source_reads == 2 && fixture.drift_value) {
    ++output.candidates.front().candidate.monthly_development_rate_raw;
  }
  return true;
}

xar::ck3_11906::StewardDevelopCountyCandidatesAccessV1 Access(Fixture &f) {
  return {&f, CaptureFrame, MainThread, ReadSource};
}

xar::ck3_11906::StewardDevelopCountyCandidatesNativeEnvironmentV1
FixtureEnvironment() {
  return {0, true, true};
}

void TestProductionStrictUnavailable() {
  using namespace xar::ck3_11906;
  Fixture fixture;
  auto environment =
      BindStewardDevelopCountyCandidatesNativeEnvironmentV1(0x140000000, true);
  xar::game::StewardDevelopCountyCandidatesV1 output;
  Require(ReadStewardDevelopCountyCandidatesV1(
             environment, Access(fixture), {fixture.frame.snapshot_revision},
             output) == Result::unavailable);
  Require(output.unavailable_reason == Failure::native_reader_not_frozen);
  Require(fixture.source_reads == 0);

  environment.offline_fixture_source = true;
  Require(ReadStewardDevelopCountyCandidatesV1(
             environment, Access(fixture), {fixture.frame.snapshot_revision},
             output) == Result::unavailable);
  Require(output.unavailable_reason ==
         Failure::offline_fixture_source_not_authorized);
  Require(fixture.source_reads == 0);
}

void TestOfflineFixtureHappyPath() {
  using namespace xar::ck3_11906;
  Fixture fixture;
  xar::game::StewardDevelopCountyCandidatesV1 output;
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(fixture),
             {fixture.frame.snapshot_revision}, output) == Result::available);
  Require(fixture.source_reads == 2);
  Require(output.status ==
         xar::game::StewardDevelopCountyCandidatesStatusV1::available);
  Require(output.readiness.ready && output.same_frame_stable);
  Require(output.player_character_id == fixture.frame.played_character_id);
  Require(output.steward_character_id == fixture.sample.steward_character_id);
  Require(output.task_key == "task_develop_county");
  Require(output.target_selection_mode == "engine_random_unscored");
  Require(output.candidates.size() == 1);
  Require(output.candidates.front().capital_province_id == 921);
  Require(output.candidates.front().monthly_development_rate_raw == 8'250);
}

void TestDriftRejection() {
  using namespace xar::ck3_11906;
  for (int mode = 0; mode != 3; ++mode) {
    Fixture fixture;
    fixture.drift_identity = mode == 0;
    fixture.drift_value = mode == 1;
    fixture.drift_frame = mode == 2;
    xar::game::StewardDevelopCountyCandidatesV1 output;
    Require(ReadStewardDevelopCountyCandidatesV1(
               FixtureEnvironment(), Access(fixture),
               {fixture.frame.snapshot_revision}, output) ==
           Result::unavailable);
    const auto expected =
        mode == 0 ? Failure::identity_drift
                  : mode == 1 ? Failure::native_sample_drift
                              : Failure::same_frame_drift;
    Require(output.unavailable_reason == expected);
    Require(output.candidates.empty() && !output.readiness.ready);
  }
}

void TestIdentityAndSchemaRejection() {
  using namespace xar::ck3_11906;
  Fixture fixture;
  fixture.sample.candidates.front().holder_character_identity_round_trip =
      false;
  xar::game::StewardDevelopCountyCandidatesV1 output;
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(fixture),
             {fixture.frame.snapshot_revision}, output) ==
         Result::unavailable);
  Require(output.unavailable_reason == Failure::identity_round_trip_failed);

  Fixture signed_rates;
  signed_rates.sample.candidates.front().candidate.development_progress_raw =
      -1;
  signed_rates.sample.candidates.front().candidate.monthly_development_rate_raw =
      -500;
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(signed_rates),
             {signed_rates.frame.snapshot_revision}, output) ==
          Result::available);

  Fixture invalid_key;
  invalid_key.sample.candidates.front().candidate.terrain_key = "Bad-Key";
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(invalid_key),
             {invalid_key.frame.snapshot_revision}, output) ==
          Result::unavailable);
  Require(output.unavailable_reason == Failure::schema_invariant_failed);

  Fixture invalid;
  invalid.sample.valid = false;
  invalid.sample.task_failure_reason = "native_fixture_invalid";
  // Invalid tasks do not publish a candidate domain.
  invalid.sample.candidates.clear();
  Require(ReadStewardDevelopCountyCandidatesV1(
             FixtureEnvironment(), Access(invalid),
             {invalid.frame.snapshot_revision}, output) == Result::available);
  Require(output.valid == false && output.candidates.empty());
}

} // namespace

int main() {
  try {
    using namespace xar::ck3_11906;
    static_assert(kStewardDevelopCountyCandidatesV1ExecutableSha256.size() ==
                  64);
    Require(StewardDevelopCountyFailureReasonKeyV1(
               Failure::native_reader_not_frozen) ==
           "native_reader_not_frozen");
    TestProductionStrictUnavailable();
    TestOfflineFixtureHappyPath();
    TestDriftRejection();
    TestIdentityAndSchemaRejection();
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
