#include "xar_bridge/realm_law_governance_snapshot_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <cassert>
#include <iostream>
#include <memory>
#include <string_view>
#include <type_traits>

namespace {

namespace bridge = xar::bridge;
using Capture = bridge::RealmLawGovernanceCaptureV1;
using Candidate = bridge::RealmLawGovernanceCandidateV1;
using Failure = bridge::RealmLawGovernanceSnapshotV1Failure;
using Group = bridge::RealmLawGovernanceGroupV1;
using Presence = bridge::RealmLawGovernancePresenceV1;
using Snapshot = bridge::RealmLawGovernanceSnapshotV1;

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

bridge::RealmLawGovernanceSuccessionShapeV1 Partition(
    std::int64_t primary_share = 0) {
  bridge::RealmLawGovernanceSuccessionShapeV1 output{};
  output.presence = Presence::present;
  output.order_of_succession = Key("inheritance");
  output.title_division = OptionalKey("partition");
  output.traversal_order = OptionalKey("children");
  output.rank = OptionalKey("oldest");
  if (primary_share == 0) {
    output.primary_heir_minimum_share.presence = Presence::absent;
  } else {
    output.primary_heir_minimum_share.presence = Presence::present;
    output.primary_heir_minimum_share.value_raw = primary_share;
  }
  return output;
}

bridge::RealmLawGovernanceSuccessionShapeV1 SingleHeir() {
  auto output = Partition();
  output.title_division = OptionalKey("single_heir");
  return output;
}

Candidate Law(std::string_view key, bool active, bool can_have,
              bool can_pass, bool can_enact, std::string_view blocked_reason,
              bridge::RealmLawGovernanceSuccessionShapeV1 succession) {
  Candidate output{};
  output.law_key = Key(key);
  output.is_active = active;
  output.evaluation_complete = true;
  output.can_have = can_have;
  output.can_pass = can_pass;
  output.can_enact = can_enact;
  output.blocked_reason = can_enact ? NoReason() : Reason(blocked_reason);
  output.costs_complete = true;
  output.cost_count = 1;
  output.costs[0] = {Key("prestige"), 10'000'000};
  output.succession = succession;
  return output;
}

Group CrownAuthority() {
  Group output{};
  output.group_key = Key("crown_authority");
  output.active_law_key = Key("crown_authority_2");
  output.can_change_evaluated = true;
  output.can_change = true;
  output.candidates_complete = true;
  output.candidate_count = 3;
  output.candidates[0] = Law("crown_authority_3", false, true, false,
                             false, "cooldown_active", NoSuccession());
  output.candidates[1] = Law("crown_authority_1", false, true, true,
                             true, "", NoSuccession());
  output.candidates[2] = Law("crown_authority_2", true, true, true,
                             false, "already_enacted", NoSuccession());
  return output;
}

Group Succession() {
  Group output{};
  output.group_key = Key("succession_order_laws");
  output.active_law_key = Key("partition_succession_law");
  output.can_change_evaluated = true;
  output.can_change = true;
  output.candidates_complete = true;
  output.candidate_count = 3;
  output.candidates[0] = Law("single_heir_succession_law", false, false,
                             false, false, "innovation_unavailable",
                             SingleHeir());
  output.candidates[1] = Law("partition_succession_law", true, true, true,
                             false, "already_enacted", Partition());
  output.candidates[2] = Law("high_partition_succession_law", false, true,
                             true, true, "",
                             Partition(bridge::
                                 kRealmLawGovernanceFixedPointOneV1 / 2));
  return output;
}

std::unique_ptr<Capture> StableCapture() {
  auto capture = std::make_unique<Capture>();
  capture->exact_build_admitted = true;
  const auto hash = bridge::kRealmLawGovernanceSnapshotV1ExecutableSha256;
  std::copy(hash.begin(), hash.end(),
            capture->admitted_executable_sha256.begin());
  capture->source_adapter_bound = true;
  capture->application_main_thread = true;
  auto &frame = capture->frame_before;
  frame.public_revision = 901;
  frame.native_revision = 19'006;
  frame.proof_epoch = 33;
  frame.date_raw = 56'000'000;
  frame.paused = true;
  frame.map_ready = true;
  frame.played_character_id = 32'904;
  frame.played_character_alive = true;
  frame.played_character_identity_round_trip = true;
  capture->frame_after = frame;

  auto &sample = capture->first_sample;
  sample.source_read_complete = true;
  sample.played_character_id = frame.played_character_id;
  sample.played_character_identity_round_trip = true;
  sample.groups_complete = true;
  sample.group_count = 2;
  // Input order is deliberately not lexical; publication is deterministic.
  sample.groups[0] = Succession();
  sample.groups[1] = CrownAuthority();
  sample.title_baseline_complete = true;
  auto &baseline = sample.title_baseline;
  baseline.primary_title_presence = Presence::present;
  baseline.primary_title_id = 101;
  baseline.primary_title_successor_count = 2;
  baseline.primary_title_successor_character_ids[0] = 301;
  baseline.primary_title_successor_character_ids[1] = 201;
  baseline.held_title_count = 2;
  baseline.held_titles[0].title_id = 102;
  baseline.held_titles[0].successor_count = 1;
  baseline.held_titles[0].successor_character_ids[0] = 401;
  baseline.held_titles[1].title_id = 101;
  baseline.held_titles[1].primary = true;
  baseline.held_titles[1].successor_count = 2;
  baseline.held_titles[1].successor_character_ids[0] = 301;
  baseline.held_titles[1].successor_character_ids[1] = 201;
  capture->second_sample = sample;
  return capture;
}

void ExpectFailure(const Capture &capture, Failure expected) {
  auto output = std::make_unique<Snapshot>();
  assert(!bridge::ObserveRealmLawGovernanceSnapshotV1(capture, *output));
  assert(output->status ==
         bridge::RealmLawGovernanceSnapshotV1Status::unavailable);
  assert(output->unavailable_reason == expected);
  assert(output->group_count == 0);
  assert(output->played_character_id == -1);
  assert(!output->readiness.same_frame_ready);
  assert(bridge::RealmLawGovernanceSnapshotV1FailureName(expected) !=
         "unknown");
}

void TestAvailablePointerFreeSnapshot() {
  static_assert(std::is_trivially_copyable_v<
                bridge::RealmLawGovernanceSourceSampleV1>);
  static_assert(std::is_trivially_copyable_v<
                bridge::RealmLawGovernanceSnapshotV1>);
  static_assert(!std::is_pointer_v<decltype(Capture::first_sample)>);
  static_assert(!std::is_pointer_v<decltype(Snapshot::groups)>);

  auto capture = StableCapture();
  auto output = std::make_unique<Snapshot>();
  assert(bridge::ObserveRealmLawGovernanceSnapshotV1(*capture, *output));
  assert(output->status ==
         bridge::RealmLawGovernanceSnapshotV1Status::available);
  assert(output->unavailable_reason == Failure::none);
  assert(output->played_character_id == 32'904);
  assert(output->group_count == 2);
  assert(bridge::RealmLawGovernanceKeyViewV1(
             output->groups[0].group_key) == "crown_authority");
  assert(bridge::RealmLawGovernanceKeyViewV1(
             output->groups[0].candidates[0].law_key) ==
         "crown_authority_1");
  assert(output->groups[0].candidates[0].can_enact);
  assert(output->groups[1].candidates[0].law_key ==
         Key("high_partition_succession_law"));
  assert(output->groups[1].candidates[0].
             succession.primary_heir_minimum_share.value_raw == 50'000);
  assert(output->title_baseline.held_titles[0].title_id == 101);
  assert(output->title_baseline.held_titles[0].
             successor_character_ids[0] == 201);
  assert(output->readiness.groups_ready);
  assert(output->readiness.engine_final_legality_ready);
  assert(output->readiness.engine_final_costs_ready);
  assert(output->readiness.succession_shapes_ready);
  assert(output->readiness.title_successor_baseline_ready);
  assert(output->readiness.same_frame_ready);
}

void TestTypedFailureDoesNotPublishEmptyState() {
  auto capture = StableCapture();
  capture->source_adapter_bound = false;
  ExpectFailure(*capture, Failure::source_adapter_unavailable);

  capture = StableCapture();
  capture->first_sample.source_read_complete = false;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::source_sample_incomplete);
}

void TestDoubleSampleDriftFailsClosed() {
  auto capture = StableCapture();
  ++capture->second_sample.groups[0].candidates[0].costs[0].amount_raw;
  ExpectFailure(*capture, Failure::source_sample_drift);
}

void TestPausedSameFrameGate() {
  auto capture = StableCapture();
  capture->frame_before.paused = false;
  capture->frame_after = capture->frame_before;
  ExpectFailure(*capture, Failure::not_paused);

  capture = StableCapture();
  ++capture->frame_after.proof_epoch;
  ExpectFailure(*capture, Failure::frame_drift);
}

void TestGroupAndActiveLawInvariants() {
  auto capture = StableCapture();
  capture->first_sample.groups[1].group_key = Key("succession_order_laws");
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::duplicate_group_key);

  capture = StableCapture();
  capture->first_sample.groups[0].candidates[1].is_active = false;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::active_law_mismatch);
}

void TestCandidateLegalityReasonAndCosts() {
  auto capture = StableCapture();
  capture->first_sample.groups[0].candidates[0].can_enact = true;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::candidate_legality_invariant_failed);

  capture = StableCapture();
  capture->first_sample.groups[0].candidates[0].blocked_reason = NoReason();
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::candidate_reason_invariant_failed);

  capture = StableCapture();
  capture->first_sample.groups[0].candidates[0].costs_complete = false;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::cost_collection_incomplete);

  capture = StableCapture();
  capture->first_sample.groups[0].candidates[0].costs[0].amount_raw = -1;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::cost_value_invalid);
}

void TestSuccessionShapeInvariant() {
  auto capture = StableCapture();
  capture->first_sample.groups[0].candidates[0].
      succession.primary_heir_minimum_share.presence = Presence::unknown;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::succession_shape_invalid);

  capture = StableCapture();
  capture->first_sample.groups[0].candidates[0].
      succession.primary_heir_minimum_share.value_raw = 100'001;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::succession_shape_invalid);
}

void TestTitleSuccessorBaselineInvariant() {
  auto capture = StableCapture();
  capture->first_sample.title_baseline.held_titles[1].primary = false;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::title_baseline_invalid);

  capture = StableCapture();
  capture->first_sample.title_baseline.held_titles[1].
      successor_character_ids[1] = 301;
  capture->first_sample.title_baseline.
      primary_title_successor_character_ids[1] = 301;
  capture->second_sample = capture->first_sample;
  ExpectFailure(*capture, Failure::duplicate_successor_identity);
}

void TestBuildThreadIdentityAndVocabulary() {
  auto capture = StableCapture();
  capture->admitted_executable_sha256[0] = '0';
  ExpectFailure(*capture, Failure::exact_build_mismatch);

  capture = StableCapture();
  capture->application_main_thread = false;
  ExpectFailure(*capture, Failure::application_main_thread_required);

  capture = StableCapture();
  capture->second_sample.played_character_id = 0;
  ExpectFailure(*capture, Failure::player_identity_mismatch);

  bridge::RealmLawGovernanceKeyV1 key{};
  assert(bridge::AssignRealmLawGovernanceKeyV1(
      "succession_order_laws", key));
  assert(bridge::RealmLawGovernanceKeyViewV1(key) ==
         "succession_order_laws");
  assert(!bridge::AssignRealmLawGovernanceKeyV1("Faith-Law", key));
  assert(bridge::RealmLawGovernanceSnapshotV1FailureName(
             Failure::source_sample_drift) == "source_sample_drift");
}

} // namespace

int main() {
  TestAvailablePointerFreeSnapshot();
  TestTypedFailureDoesNotPublishEmptyState();
  TestDoubleSampleDriftFailsClosed();
  TestPausedSameFrameGate();
  TestGroupAndActiveLawInvariants();
  TestCandidateLegalityReasonAndCosts();
  TestSuccessionShapeInvariant();
  TestTitleSuccessorBaselineInvariant();
  TestBuildThreadIdentityAndVocabulary();
  std::cout << "realm_law_governance_snapshot_v1_test: 9/9 GREEN\n";
  return 0;
}
