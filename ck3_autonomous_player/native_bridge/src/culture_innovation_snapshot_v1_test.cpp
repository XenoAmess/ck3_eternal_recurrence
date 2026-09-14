#include "xar_bridge/culture_innovation_snapshot_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string_view>

namespace {

namespace game = xar::game;
namespace ck3 = xar::ck3_11906;

template <std::size_t Size>
void Fixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < Size);
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

game::CultureInnovationStableKeyV1 Key(std::string_view value) {
  game::CultureInnovationStableKeyV1 output{};
  assert(ck3::AssignCultureInnovationStableKeyV1(value, output));
  return output;
}

struct Fixture {
  ck3::CultureInnovationSnapshotFrameV1 before{};
  ck3::CultureInnovationSnapshotFrameV1 after{};
  ck3::CultureInnovationSourceSampleV1 first{};
  ck3::CultureInnovationSourceSampleV1 second{};
  bool main_thread = true;
  bool fail_frame = false;
  bool fail_source = false;
  std::uint32_t frame_calls = 0;
  std::uint32_t source_calls = 0;
};

bool Capture(void *context,
             ck3::CultureInnovationSnapshotFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_calls;
  if (fixture.fail_frame) return false;
  output = fixture.frame_calls == 1 ? fixture.before : fixture.after;
  return true;
}

bool IsMain(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool ReadSource(void *context, std::uintptr_t played_character,
                ck3::CultureInnovationSourceSampleV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.source_calls;
  if (fixture.fail_source ||
      played_character != fixture.before.played_character) {
    return false;
  }
  output = fixture.source_calls == 1 ? fixture.first : fixture.second;
  return true;
}

ck3::CultureInnovationSnapshotEnvironmentV1 Environment() {
  ck3::CultureInnovationSnapshotEnvironmentV1 output{};
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      ck3::kCultureInnovationSnapshotExecutableSha256V1;
  output.offline_fixture = true;
  return output;
}

ck3::CultureInnovationSnapshotAccessV1 Access(Fixture &fixture) {
  ck3::CultureInnovationSnapshotAccessV1 output{};
  output.context = &fixture;
  output.capture_frame = &Capture;
  output.is_main_thread = &IsMain;
  output.read_source = &ReadSource;
  return output;
}

ck3::CultureInnovationSnapshotRequestV1 Request() {
  // Signed zero is deliberately used as a legal CharacterID.
  return {"culture2-fixture-001", 801, 9801, 55'000'000, 0};
}

game::CultureInnovationRowV1 Innovation(
    std::string_view key, std::string_view era, std::string_view group,
    std::string_view skill, std::int64_t progress_raw, bool is_active,
    bool can_gain_progress, bool can_be_fascination, bool is_fascination,
    bool has_spread_marker) {
  game::CultureInnovationRowV1 output{};
  output.key = Key(key);
  output.era_key = Key(era);
  output.group_key = Key(group);
  output.skill_key = Key(skill);
  output.progress_raw = progress_raw;
  output.is_active = is_active;
  output.can_gain_progress = can_gain_progress;
  output.can_be_fascination = can_be_fascination;
  output.is_fascination = is_fascination;
  output.has_spread_marker = has_spread_marker;
  return output;
}

std::unique_ptr<Fixture> Base() {
  auto fixture = std::make_unique<Fixture>();
  auto &frame = fixture->before;
  Fixed(frame.snapshot_id, "culture2-fixture-001");
  frame.public_revision = 801;
  frame.native_revision = 9801;
  frame.proof_epoch = 77;
  frame.date_raw = 55'000'000;
  frame.paused = true;
  frame.map_ready = true;
  frame.has_played_character = true;
  frame.played_character_alive = true;
  frame.played_character_id = 0;
  frame.played_character = 0x1234;
  frame.played_character_identity_round_trip = true;
  fixture->after = frame;

  auto &sample = fixture->first;
  sample.player_character_id = 0;
  sample.player_identity_round_trip = true;
  sample.state.culture_id = 0;
  sample.state.culture_head_presence =
      game::CultureInnovationPresenceV1::present;
  sample.state.culture_head_character_id = 0;
  sample.state.is_player_culture_head = true;
  sample.state.fascination_presence =
      game::CultureInnovationPresenceV1::present;
  sample.state.current_fascination_key = Key("innovation_motte");

  // Native order is intentionally unstable-looking. The observer publishes
  // stable key order without changing meaning.
  sample.state.era_count = 2;
  sample.state.eras[0] = {Key("culture_era_high_medieval"), 150'000};
  sample.state.eras[1] = {Key("culture_era_tribal"), 0};
  sample.state.innovation_count = 3;
  sample.state.innovations[0] = Innovation(
      "innovation_primogeniture", "culture_era_high_medieval",
      "culture_group_civic", "learning", 0, false, true, true, false,
      false);
  sample.state.innovations[1] = Innovation(
      "innovation_motte", "culture_era_tribal", "culture_group_military",
      "martial", 2'500'000, false, true, true, true, true);
  sample.state.innovations[2] = Innovation(
      "innovation_gavelkind", "culture_era_tribal", "culture_group_civic",
      "stewardship", ck3::kCultureInnovationCompleteFixedPointV1, true,
      false, false, false, false);
  fixture->second = sample;
  return fixture;
}

game::CultureInnovationSnapshotV1 ReadAvailable(Fixture &fixture) {
  game::CultureInnovationSnapshotV1 output{};
  const auto result = ck3::ReadCultureInnovationSnapshotV1(
      Environment(), Access(fixture), Request(), output);
  assert(result == game::ReadCultureInnovationSnapshotResultV1::available);
  assert(output.status == game::CultureInnovationSnapshotStatusV1::available);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::none);
  assert(output.readiness.culture_identity_ready);
  assert(output.readiness.culture_head_ready);
  assert(output.readiness.fascination_ready);
  assert(output.readiness.era_collection_ready);
  assert(output.readiness.innovation_collection_ready);
  assert(output.readiness.same_frame_ready);
  assert(fixture.frame_calls == 2);
  assert(fixture.source_calls == 2);
  return output;
}

void TestAvailableSnapshotAndLegalZero() {
  auto fixture = Base();
  const auto output = ReadAvailable(*fixture);
  assert(output.player_character_id == 0);
  assert(output.state.culture_id == 0);
  assert(output.state.culture_head_character_id == 0);
  assert(output.state.is_player_culture_head);
  assert(std::string_view(output.game_build.data()) == "1.19.0.6");
  assert(std::string_view(output.executable_sha256.data()) ==
         ck3::kCultureInnovationSnapshotExecutableSha256V1);
  assert(ck3::CultureInnovationStableKeyViewV1(output.state.eras[0].key) ==
         "culture_era_high_medieval");
  assert(ck3::CultureInnovationStableKeyViewV1(output.state.eras[1].key) ==
         "culture_era_tribal");
  assert(output.state.eras[1].progress_raw == 0);
  assert(ck3::CultureInnovationStableKeyViewV1(
             output.state.innovations[0].key) ==
         "innovation_gavelkind");
  assert(ck3::CultureInnovationStableKeyViewV1(
             output.state.innovations[2].key) ==
         "innovation_primogeniture");
  assert(output.state.innovations[2].progress_raw == 0);
  assert(!output.state.innovations[2].is_active);
}

void TestObservedAbsentHeadAndFascination() {
  auto fixture = Base();
  auto &state = fixture->first.state;
  state.culture_head_presence = game::CultureInnovationPresenceV1::absent;
  state.culture_head_character_id = -1;
  state.is_player_culture_head = false;
  state.fascination_presence = game::CultureInnovationPresenceV1::absent;
  state.current_fascination_key = {};
  state.innovations[1].is_fascination = false;
  fixture->second = fixture->first;
  const auto output = ReadAvailable(*fixture);
  assert(output.state.culture_head_presence ==
         game::CultureInnovationPresenceV1::absent);
  assert(output.state.fascination_presence ==
         game::CultureInnovationPresenceV1::absent);
}

void TestStorageNoiseIsCanonicalized() {
  auto fixture = Base();
  fixture->before.snapshot_id[40] = 'x';
  fixture->after.snapshot_id[41] = 'y';
  fixture->first.state.current_fascination_key.bytes[80] = 'x';
  fixture->second.state.current_fascination_key.bytes[81] = 'y';
  fixture->first.state.eras[0].key.bytes[80] = 'x';
  fixture->second.state.eras[0].key.bytes[81] = 'y';
  fixture->first.state.innovations[0].group_key.bytes[80] = 'x';
  fixture->second.state.innovations[0].group_key.bytes[81] = 'y';
  fixture->first.state.eras[fixture->first.state.era_count].progress_raw = 1;
  fixture->second.state.eras[fixture->second.state.era_count].progress_raw = 2;
  fixture->first.state
      .innovations[fixture->first.state.innovation_count]
      .progress_raw = 1;
  fixture->second.state
      .innovations[fixture->second.state.innovation_count]
      .progress_raw = 2;

  const auto output = ReadAvailable(*fixture);
  assert(output.snapshot_id[40] == '\0');
  assert(output.snapshot_id[41] == '\0');
  assert(output.state.current_fascination_key.bytes[80] == '\0');
  assert(output.state.eras[0].key.bytes[80] == '\0');
  assert(output.state.eras[output.state.era_count] ==
         game::CultureInnovationEraV1{});
  assert(output.state.innovations[output.state.innovation_count] ==
         game::CultureInnovationRowV1{});
}

void TestTypedUnavailableIsNotLegalZero() {
  auto fixture = Base();
  fixture->fail_source = true;
  game::CultureInnovationSnapshotV1 output{};
  assert(ck3::ReadCultureInnovationSnapshotV1(
             Environment(), Access(*fixture), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.status ==
         game::CultureInnovationSnapshotStatusV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::native_source_read_failed);
  assert(output.player_character_id == -1);
  assert(output.state.culture_id == -1);
  assert(output.state.fascination_presence ==
         game::CultureInnovationPresenceV1::unknown);
  assert(output.state.era_count == 0);
  assert(output.state.innovation_count == 0);
  assert(!output.readiness.culture_identity_ready);
  assert(!output.readiness.same_frame_ready);
}

void TestSourceAndFrameDriftFailClosed() {
  auto sample_drift = Base();
  ++sample_drift->second.state.innovations[0].progress_raw;
  game::CultureInnovationSnapshotV1 output{};
  assert(ck3::ReadCultureInnovationSnapshotV1(
             Environment(), Access(*sample_drift), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::native_sample_drift);

  auto frame_drift = Base();
  ++frame_drift->after.proof_epoch;
  assert(ck3::ReadCultureInnovationSnapshotV1(
             Environment(), Access(*frame_drift), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::revision_drift);
}

void TestFascinationInvariantFailsClosed() {
  auto fixture = Base();
  fixture->first.state.current_fascination_key =
      Key("innovation_primogeniture");
  fixture->second = fixture->first;
  game::CultureInnovationSnapshotV1 output{};
  assert(ck3::ReadCultureInnovationSnapshotV1(
             Environment(), Access(*fixture), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::
             fascination_invariant_failed);
}

void TestCollectionAndProgressInvariantsFailClosed() {
  auto duplicate = Base();
  duplicate->first.state.innovations[2].key =
      duplicate->first.state.innovations[0].key;
  duplicate->second = duplicate->first;
  game::CultureInnovationSnapshotV1 output{};
  assert(ck3::ReadCultureInnovationSnapshotV1(
             Environment(), Access(*duplicate), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::duplicate_stable_key);

  auto bad_progress = Base();
  bad_progress->first.state.innovations[0].progress_raw =
      ck3::kCultureInnovationCompleteFixedPointV1 + 1;
  bad_progress->second = bad_progress->first;
  assert(ck3::ReadCultureInnovationSnapshotV1(
             Environment(), Access(*bad_progress), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::progress_invalid);

  auto bad_era = Base();
  bad_era->first.state.innovations[0].era_key =
      Key("culture_era_late_medieval");
  bad_era->second = bad_era->first;
  assert(ck3::ReadCultureInnovationSnapshotV1(
             Environment(), Access(*bad_era), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::
             innovation_collection_invalid);
}

void TestExactBuildThreadAndBindingGuards() {
  auto fixture = Base();
  game::CultureInnovationSnapshotV1 output{};
  auto wrong_build = Environment();
  wrong_build.admitted_executable_sha256 = "WRONG";
  assert(ck3::ReadCultureInnovationSnapshotV1(
             wrong_build, Access(*fixture), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::
             exact_build_not_admitted);

  fixture = Base();
  fixture->main_thread = false;
  assert(ck3::ReadCultureInnovationSnapshotV1(
             Environment(), Access(*fixture), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::
             application_main_thread_required);

  fixture = Base();
  auto production_without_module = Environment();
  production_without_module.offline_fixture = false;
  assert(ck3::ReadCultureInnovationSnapshotV1(
             production_without_module, Access(*fixture), Request(), output) ==
         game::ReadCultureInnovationSnapshotResultV1::unavailable);
  assert(output.unavailable_reason ==
         game::CultureInnovationSnapshotFailureV1::
             native_bindings_unavailable);
}

void TestStableKeyAndFailureVocabulary() {
  game::CultureInnovationStableKeyV1 output{};
  assert(ck3::AssignCultureInnovationStableKeyV1("innovation_motte", output));
  assert(ck3::CultureInnovationStableKeyViewV1(output) ==
         "innovation_motte");
  assert(!ck3::AssignCultureInnovationStableKeyV1("Innovation-Motte", output));
  assert(output.size == 0);
  assert(ck3::CultureInnovationSnapshotFailureKeyV1(
             game::CultureInnovationSnapshotFailureV1::progress_invalid) ==
         "progress_invalid");
}

} // namespace

int main() {
  TestAvailableSnapshotAndLegalZero();
  TestObservedAbsentHeadAndFascination();
  TestStorageNoiseIsCanonicalized();
  TestTypedUnavailableIsNotLegalZero();
  TestSourceAndFrameDriftFailClosed();
  TestFascinationInvariantFailsClosed();
  TestCollectionAndProgressInvariantsFailClosed();
  TestExactBuildThreadAndBindingGuards();
  TestStableKeyAndFailureVocabulary();
  std::cout << "culture_innovation_snapshot_v1_test: 9/9 GREEN\n";
  return 0;
}
