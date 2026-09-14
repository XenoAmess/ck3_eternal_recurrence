#include "xar_bridge/realm_law_governance_source_adapter_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <string>
#include <string_view>

namespace {

namespace bridge = xar::bridge;
using Access = bridge::RealmLawGovernanceSourceAccessV1;
using Candidate = bridge::RealmLawGovernanceCandidateV1;
using Container = bridge::RealmLawGovernanceSourceContainerLeaseV1;
using Failure = bridge::RealmLawGovernanceSourceAdapterFailureV1;
using Frame = bridge::RealmLawGovernanceFrameV1;
using Group = bridge::RealmLawGovernanceSourceGroupLeaseV1;
using Player = bridge::RealmLawGovernanceSourcePlayerLeaseV1;
using Presence = bridge::RealmLawGovernancePresenceV1;
using Result = bridge::RealmLawGovernanceSourceResultV1;

bridge::RealmLawGovernanceKeyV1 Key(std::string_view value) {
  bridge::RealmLawGovernanceKeyV1 output{};
  assert(bridge::AssignRealmLawGovernanceKeyV1(value, output));
  return output;
}

bridge::RealmLawGovernanceReasonV1 Reason(std::string_view value) {
  bridge::RealmLawGovernanceReasonV1 output{};
  assert(bridge::AssignRealmLawGovernanceReasonV1(value, output));
  return output;
}

bridge::RealmLawGovernanceReasonV1 NoReason() {
  bridge::RealmLawGovernanceReasonV1 output{};
  output.presence = Presence::absent;
  return output;
}

bridge::RealmLawGovernanceOptionalKeyV1 OptionalKey(
    std::string_view value) {
  return {Presence::present, Key(value)};
}

bridge::RealmLawGovernanceOptionalKeyV1 NoKey() {
  bridge::RealmLawGovernanceOptionalKeyV1 output{};
  output.presence = Presence::absent;
  return output;
}

bridge::RealmLawGovernanceSuccessionShapeV1 NoSuccession() {
  bridge::RealmLawGovernanceSuccessionShapeV1 output{};
  output.presence = Presence::absent;
  output.title_division = NoKey();
  output.traversal_order = NoKey();
  output.rank = NoKey();
  output.primary_heir_minimum_share.presence = Presence::absent;
  return output;
}

bridge::RealmLawGovernanceSuccessionShapeV1 SuccessionShape(
    std::string_view division, std::int64_t primary_share = 0) {
  bridge::RealmLawGovernanceSuccessionShapeV1 output{};
  output.presence = Presence::present;
  output.order_of_succession = Key("inheritance");
  output.title_division = OptionalKey(division);
  output.traversal_order = OptionalKey("children");
  output.rank = OptionalKey("oldest");
  output.primary_heir_minimum_share.presence =
      primary_share == 0 ? Presence::absent : Presence::present;
  output.primary_heir_minimum_share.value_raw = primary_share;
  return output;
}

Candidate Law(std::string_view key, bool active, bool can_have,
              bool can_pass, bool can_enact, std::string_view reason,
              bridge::RealmLawGovernanceSuccessionShapeV1 succession,
              std::int64_t prestige_cost) {
  Candidate output{};
  output.law_key = Key(key);
  output.is_active = active;
  output.evaluation_complete = true;
  output.can_have = can_have;
  output.can_pass = can_pass;
  output.can_enact = can_enact;
  output.blocked_reason = can_enact ? NoReason() : Reason(reason);
  output.costs_complete = true;
  output.cost_count = 1;
  output.costs[0] = {Key("prestige"), prestige_cost};
  output.succession = succession;
  return output;
}

struct Fixture {
  std::array<Frame, 2> frames{};
  std::array<Player, 2> players{};
  std::array<Container, 2> containers{};
  std::array<std::array<Group, 2>, 2> groups{};
  std::array<std::array<std::array<Candidate, 3>, 2>, 2> candidates{};
  std::array<bridge::RealmLawGovernanceTitleBaselineV1, 2> baselines{};
  std::size_t frame_calls = 0;
  std::size_t player_calls = 0;
  std::size_t container_calls = 0;
  std::size_t group_calls = 0;
  std::size_t candidate_calls = 0;
  std::size_t baseline_calls = 0;
  std::size_t fail_frame_call = 0;
  std::size_t fail_player_call = 0;
  std::size_t fail_container_call = 0;
  std::size_t fail_group_call = 0;
  std::size_t fail_candidate_call = 0;
  std::size_t fail_baseline_call = 0;

  Fixture() {
    Frame frame{};
    frame.public_revision = 901;
    frame.native_revision = 19'006;
    frame.proof_epoch = 33;
    frame.date_raw = 56'000'000;
    frame.paused = true;
    frame.map_ready = true;
    frame.played_character_id = 32'904;
    frame.played_character_alive = true;
    frame.played_character_identity_round_trip = true;
    frames.fill(frame);
    players.fill(Player{true, 0x1000, 32'904});
    containers.fill(Container{true, 0x2000, 71, 4, 32'904, 2});

    Group authority{};
    authority.identity_round_trip = true;
    authority.native_address = 0x3000;
    authority.identity = 81;
    authority.generation = 5;
    authority.group_key = Key("crown_authority");
    authority.active_law_key = Key("crown_authority_2");
    authority.can_change_evaluated = true;
    authority.can_change = true;
    authority.candidate_count = 3;
    Group succession{};
    succession.identity_round_trip = true;
    succession.native_address = 0x4000;
    succession.identity = 82;
    succession.generation = 6;
    succession.group_key = Key("succession_order_laws");
    succession.active_law_key = Key("partition_succession_law");
    succession.can_change_evaluated = true;
    succession.can_change = true;
    succession.candidate_count = 3;
    groups[0] = {authority, succession};
    groups[1] = groups[0];

    candidates[0][0][0] =
        Law("crown_authority_1", false, true, true, true, "",
            NoSuccession(), 10'000'000);
    candidates[0][0][1] =
        Law("crown_authority_2", true, true, true, false,
            "already_enacted", NoSuccession(), 10'000'000);
    candidates[0][0][2] =
        Law("crown_authority_3", false, true, false, false,
            "cooldown_active", NoSuccession(), 10'000'000);
    candidates[0][1][0] =
        Law("partition_succession_law", true, true, true, false,
            "already_enacted", SuccessionShape("partition"), 50'000'000);
    candidates[0][1][1] =
        Law("high_partition_succession_law", false, true, true, true, "",
            SuccessionShape("partition", 50'000), 50'000'000);
    candidates[0][1][2] =
        Law("single_heir_succession_law", false, false, false, false,
            "innovation_unavailable", SuccessionShape("single_heir"),
            50'000'000);
    candidates[1] = candidates[0];

    auto &baseline = baselines[0];
    baseline.primary_title_presence = Presence::present;
    baseline.primary_title_id = 101;
    baseline.primary_title_successor_count = 2;
    baseline.primary_title_successor_character_ids[0] = 201;
    baseline.primary_title_successor_character_ids[1] = 301;
    baseline.held_title_count = 2;
    baseline.held_titles[0].title_id = 101;
    baseline.held_titles[0].primary = true;
    baseline.held_titles[0].successor_count = 2;
    baseline.held_titles[0].successor_character_ids[0] = 201;
    baseline.held_titles[0].successor_character_ids[1] = 301;
    baseline.held_titles[1].title_id = 102;
    baseline.held_titles[1].successor_count = 1;
    baseline.held_titles[1].successor_character_ids[0] = 401;
    baselines[1] = baseline;
  }
};

bool CaptureFrame(void *context, Frame &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.frame_calls;
  if (fixture.frame_calls == fixture.fail_frame_call) return false;
  output = fixture.frames[fixture.frame_calls > 1 ? 1 : 0];
  return true;
}

bool ResolvePlayer(void *context, std::int32_t expected, Player &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.player_calls;
  if (fixture.player_calls == fixture.fail_player_call || expected != 32'904) {
    return false;
  }
  output = fixture.players[fixture.player_calls > 1 ? 1 : 0];
  return true;
}

bool ResolveContainer(void *context, const Player &player,
                      Container &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.container_calls;
  if (fixture.container_calls == fixture.fail_container_call) return false;
  const auto pass = fixture.container_calls > 1 ? 1U : 0U;
  if (player.native_address != fixture.players[pass].native_address) {
    return false;
  }
  output = fixture.containers[pass];
  return true;
}

bool ReadGroup(void *context, const Player &player,
               const Container &container, std::size_t index,
               Group &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.group_calls;
  if (fixture.group_calls == fixture.fail_group_call || index >= 2) {
    return false;
  }
  const auto pass = fixture.group_calls > fixture.containers[0].group_count
      ? 1U
      : 0U;
  if (player.native_address != fixture.players[pass].native_address ||
      container.native_address != fixture.containers[pass].native_address) {
    return false;
  }
  output = fixture.groups[pass][index];
  return true;
}

bool ReadCandidate(void *context, const Player &player,
                   const Container &container, const Group &group,
                   std::size_t index, Candidate &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.candidate_calls;
  if (fixture.candidate_calls == fixture.fail_candidate_call || index >= 3) {
    return false;
  }
  const auto pass = fixture.candidate_calls > 6 ? 1U : 0U;
  if (player.native_address != fixture.players[pass].native_address ||
      container.native_address != fixture.containers[pass].native_address) {
    return false;
  }
  const std::size_t group_index = group.identity == 81 ? 0 : 1;
  output = fixture.candidates[pass][group_index][index];
  return true;
}

bool ReadBaseline(void *context, const Player &player,
                  bridge::RealmLawGovernanceTitleBaselineV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.baseline_calls;
  if (fixture.baseline_calls == fixture.fail_baseline_call) return false;
  const auto pass = fixture.baseline_calls > 1 ? 1U : 0U;
  if (player.native_address != fixture.players[pass].native_address) {
    return false;
  }
  output = fixture.baselines[pass];
  return true;
}

Access MakeAccess(Fixture &fixture) {
  Access output{};
  output.exact_build_admitted = true;
  output.admitted_executable_sha256 =
      bridge::kRealmLawGovernanceSnapshotV1ExecutableSha256;
  output.current_thread_id = 77;
  output.application_main_thread_id = 77;
  output.context = &fixture;
  output.capture_frame = &CaptureFrame;
  output.resolve_player = &ResolvePlayer;
  output.resolve_container = &ResolveContainer;
  output.read_group = &ReadGroup;
  output.read_candidate = &ReadCandidate;
  output.read_title_baseline = &ReadBaseline;
  return output;
}

void ExpectFailure(Access access, Failure expected,
                   bridge::RealmLawGovernanceSnapshotV1Failure core) {
  auto output = std::make_unique<Result>();
  output->snapshot.status =
      bridge::RealmLawGovernanceSnapshotV1Status::available;
  output->snapshot.group_count = 1;
  assert(!bridge::ObserveRealmLawGovernanceSourceV1(access, *output));
  assert(output->failure == expected);
  assert(output->core_failure == core);
  assert(output->snapshot.status ==
         bridge::RealmLawGovernanceSnapshotV1Status::unavailable);
  assert(output->snapshot.group_count == 0);
  assert(bridge::RealmLawGovernanceSourceAdapterFailureNameV1(expected) !=
         "unknown");
}

void TestStableTransactionReResolvesAndPublishes() {
  Fixture fixture{};
  auto result = std::make_unique<Result>();
  assert(bridge::ObserveRealmLawGovernanceSourceV1(MakeAccess(fixture),
                                                   *result));
  assert(result->failure == Failure::none);
  assert(result->core_failure ==
         bridge::RealmLawGovernanceSnapshotV1Failure::none);
  assert(result->snapshot.status ==
         bridge::RealmLawGovernanceSnapshotV1Status::available);
  assert(result->snapshot.group_count == 2);
  assert(result->snapshot.groups[0].group_key == Key("crown_authority"));
  assert(result->snapshot.groups[0].candidates[0].can_enact);
  assert(result->snapshot.groups[0].candidates[2].blocked_reason.presence ==
         Presence::present);
  assert(result->snapshot.groups[1].candidates[0].law_key ==
         Key("high_partition_succession_law"));
  assert(result->snapshot.groups[1].candidates[0].costs[0].amount_raw ==
         50'000'000);
  assert(result->snapshot.groups[1].candidates[0].
             succession.primary_heir_minimum_share.value_raw == 50'000);
  assert(result->snapshot.title_baseline.held_title_count == 2);
  assert(result->snapshot.title_baseline.held_titles[0].
             successor_character_ids[1] == 301);
  assert(fixture.frame_calls == 2);
  assert(fixture.player_calls == 2);
  assert(fixture.container_calls == 2);
  assert(fixture.group_calls == 4);
  assert(fixture.candidate_calls == 12);
  assert(fixture.baseline_calls == 2);
}

void TestAdmissionCallbackAndThreadGates() {
  Fixture fixture{};
  auto access = MakeAccess(fixture);
  access.admitted_executable_sha256 = "wrong";
  ExpectFailure(access, Failure::exact_build_mismatch,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    exact_build_mismatch);
  assert(fixture.frame_calls == 0);

  fixture = {};
  access = MakeAccess(fixture);
  access.read_candidate = nullptr;
  ExpectFailure(access, Failure::callbacks_unavailable,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    source_adapter_unavailable);
  assert(fixture.frame_calls == 0);

  fixture = {};
  access = MakeAccess(fixture);
  access.current_thread_id = 78;
  ExpectFailure(access, Failure::application_main_thread_required,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    application_main_thread_required);
  assert(fixture.frame_calls == 0);
}

void TestPlayerContainerAndGroupAreReResolved() {
  Fixture fixture{};
  fixture.players[1].native_address++;
  ExpectFailure(MakeAccess(fixture), Failure::player_drift,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    player_identity_mismatch);
  assert(fixture.player_calls == 2);
  assert(fixture.container_calls == 2);

  fixture = {};
  fixture.fail_container_call = 1;
  ExpectFailure(MakeAccess(fixture), Failure::container_unavailable,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    source_adapter_unavailable);

  fixture = {};
  fixture.containers[1].generation++;
  ExpectFailure(MakeAccess(fixture), Failure::container_drift,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    source_sample_drift);

  fixture = {};
  fixture.groups[1][0].generation++;
  ExpectFailure(MakeAccess(fixture), Failure::group_drift,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    source_sample_drift);
}

void TestEngineFinalSampleDriftFailsClosed() {
  Fixture fixture{};
  ++fixture.candidates[1][0][0].costs[0].amount_raw;
  ExpectFailure(MakeAccess(fixture), Failure::source_sample_drift,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    source_sample_drift);

  fixture = {};
  fixture.baselines[1].held_titles[1].successor_character_ids[0] = 402;
  ExpectFailure(MakeAccess(fixture), Failure::source_sample_drift,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    source_sample_drift);
}

void TestFrameAndReadFailures() {
  Fixture fixture{};
  fixture.frames[0].paused = false;
  fixture.frames[1].paused = false;
  ExpectFailure(MakeAccess(fixture), Failure::not_paused,
                bridge::RealmLawGovernanceSnapshotV1Failure::not_paused);
  assert(fixture.player_calls == 0);

  fixture = {};
  ++fixture.frames[1].proof_epoch;
  ExpectFailure(MakeAccess(fixture), Failure::frame_drift,
                bridge::RealmLawGovernanceSnapshotV1Failure::frame_drift);

  fixture = {};
  fixture.fail_candidate_call = 1;
  ExpectFailure(MakeAccess(fixture), Failure::candidate_unavailable,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    source_adapter_unavailable);

  fixture = {};
  fixture.fail_baseline_call = 1;
  ExpectFailure(MakeAccess(fixture), Failure::title_baseline_unavailable,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    source_adapter_unavailable);
}

void TestCoreValidatesEngineFinalInputs() {
  Fixture fixture{};
  fixture.candidates[0][0][0].evaluation_complete = false;
  fixture.candidates[1][0][0] = fixture.candidates[0][0][0];
  ExpectFailure(MakeAccess(fixture), Failure::core_rejected,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    candidate_evaluation_incomplete);

  fixture = {};
  fixture.candidates[0][0][2].blocked_reason = NoReason();
  fixture.candidates[1][0][2] = fixture.candidates[0][0][2];
  ExpectFailure(MakeAccess(fixture), Failure::core_rejected,
                bridge::RealmLawGovernanceSnapshotV1Failure::
                    candidate_reason_invariant_failed);
}

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool ContainsAll(std::string_view text,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (text.find(token) == std::string_view::npos) return false;
  }
  return true;
}

void TestMachineReadableFixtures(const char *contract_path,
                                 const char *stable_path) {
  const auto contract = ReadAll(contract_path);
  assert(ContainsAll(
      contract,
      {"realm_law_governance_source_adapter_v1",
       "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
       "resolve_player_each_sample", "resolve_law_container_each_sample",
       "engine_final_legality_and_cost", "no_native_pointer_cache",
       "shared_glue_required", "live_validation_required"}));
  const auto stable = ReadAll(stable_path);
  assert(ContainsAll(stable,
      {"offline-fixture", "crown_authority_2",
       "high_partition_succession_law", "cooldown_active",
       "primary_heir_minimum_share_raw", "held_title_successors"}));
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 3);
  TestStableTransactionReResolvesAndPublishes();
  TestAdmissionCallbackAndThreadGates();
  TestPlayerContainerAndGroupAreReResolved();
  TestEngineFinalSampleDriftFailsClosed();
  TestFrameAndReadFailures();
  TestCoreValidatesEngineFinalInputs();
  TestMachineReadableFixtures(argv[1], argv[2]);
  std::cout << "realm_law_governance_source_adapter_v1_test: 7/7 GREEN\n";
  return 0;
}
