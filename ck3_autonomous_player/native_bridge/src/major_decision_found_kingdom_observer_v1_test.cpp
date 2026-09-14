#include "xar_bridge/major_decision_found_kingdom_observer_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <cassert>
#include <iostream>
#include <string>
#include <type_traits>

namespace {

namespace bridge = xar::bridge;
using Capture = bridge::MajorDecisionFoundKingdomCaptureV1;
using Cost = bridge::MajorDecisionEvaluatedCostV1;
using Failure = bridge::MajorDecisionFoundKingdomFailureV1;
using FieldState = bridge::MajorDecisionFieldStateV1;
using Snapshot = bridge::MajorDecisionFoundKingdomSnapshotV1;
using UnknownReason = bridge::MajorDecisionUnknownReasonV1;

bridge::MajorDecisionTypedBoolV1 Known(bool value) {
  return {FieldState::known, value, UnknownReason::none};
}

bridge::MajorDecisionTypedBoolV1 Unknown(UnknownReason reason) {
  return {FieldState::unknown, false, reason};
}

Cost KnownCost(std::int64_t gold, std::int64_t treasury,
               std::int64_t prestige, std::int64_t piety) {
  return {FieldState::known,
          bridge::MajorDecisionCostSourceV1::native_evaluated_cost,
          gold,
          treasury,
          prestige,
          piety,
          UnknownReason::none};
}

Cost UnknownCost() {
  Cost output{};
  output.unknown_reason =
      UnknownReason::evaluated_cost_evaluator_unavailable;
  return output;
}

Capture BaseCapture() {
  Capture capture{};
  capture.observer_enabled = true;
  capture.exact_build_admitted = true;
  const auto hash = bridge::kMajorDecisionFoundKingdomExecutableSha256V1;
  std::copy(hash.begin(), hash.end(),
            capture.admitted_executable_sha256.begin());

  auto &frame = capture.frame_before;
  frame.snapshot_revision = 1201;
  frame.native_revision = 19006;
  frame.proof_epoch = 77;
  frame.date_raw = 55'000'000;
  frame.played_character_id = 0;
  frame.application_main_thread = true;
  frame.paused = true;
  frame.map_ready = true;
  frame.played_character_alive = true;
  frame.played_character_identity_round_trip = true;
  capture.frame_after = frame;

  auto &sample = capture.first_sample;
  sample.source_read_complete = true;
  sample.played_character_id = frame.played_character_id;
  sample.decision_definition_identity_round_trip = true;
  sample.eligibility_source =
      bridge::MajorDecisionEligibilitySourceV1::native_decision_evaluator;
  sample.is_shown = Known(true);
  sample.is_valid = Known(true);
  sample.is_valid_showing_failures_only = Known(true);
  sample.evaluated_cost = KnownCost(30'000'000, 0, 50'000'000, 20'000'000);
  sample.is_affordable = Known(true);
  sample.can_take = Known(true);
  capture.second_sample = sample;
  return capture;
}

Snapshot ObserveAvailable(const Capture &capture) {
  Snapshot output{};
  assert(bridge::ObserveMajorDecisionFoundKingdomV1(capture, output));
  assert(output.status ==
         bridge::MajorDecisionFoundKingdomStatusV1::available);
  assert(output.unavailable_reason == Failure::none);
  return output;
}

void ExpectFailure(const Capture &capture, Failure expected) {
  Snapshot output{};
  assert(!bridge::ObserveMajorDecisionFoundKingdomV1(capture, output));
  assert(output.status ==
         bridge::MajorDecisionFoundKingdomStatusV1::unavailable);
  assert(output.unavailable_reason == expected);
  assert(output.played_character_id == -1);
  assert(!output.readiness.same_frame_ready);
  assert(!output.readiness.action_ready);
  assert(!output.effect_preview.executable);
  assert(bridge::MajorDecisionFoundKingdomFailureKeyV1(expected) !=
         "unknown");
}

void TestAvailablePlayedCharacterSnapshot() {
  static_assert(std::is_trivially_copyable_v<
                bridge::MajorDecisionFoundKingdomSourceSampleV1>);
  static_assert(std::is_trivially_copyable_v<Snapshot>);

  const auto output = ObserveAvailable(BaseCapture());
  assert(output.played_character_id == 0);
  assert(output.is_shown.value);
  assert(output.is_valid.value);
  assert(output.is_valid_showing_failures_only.value);
  assert(output.evaluated_cost.gold_q100000 == 30'000'000);
  assert(output.evaluated_cost.treasury_q100000 == 0);
  assert(output.evaluated_cost.prestige_q100000 == 50'000'000);
  assert(output.evaluated_cost.piety_q100000 == 20'000'000);
  assert(output.is_affordable.value);
  assert(output.can_take.value);
  assert(output.readiness.same_frame_ready);
  assert(output.readiness.eligibility_ready);
  assert(output.readiness.evaluated_cost_ready);
  assert(output.readiness.affordability_ready);
  assert(output.readiness.can_take_ready);
  assert(output.readiness.semantic_observation_ready);
  assert(!output.readiness.effect_preview_ready);
  assert(!output.readiness.action_ready);
  assert(!output.readiness.raw_pointer_fields_persisted);
  assert(output.effect_preview.state == FieldState::unknown);
  assert(output.effect_preview.unknown_reason ==
         UnknownReason::effect_preview_not_provided);
  assert(!output.effect_preview.executable);
}

void TestSerializerCannotAdvertiseExecution() {
  const auto json =
      bridge::SerializeMajorDecisionFoundKingdomV1(
          ObserveAvailable(BaseCapture()));
  assert(json.find("\"private_build\":true") != std::string::npos);
  assert(json.find("\"advertised\":false") != std::string::npos);
  assert(json.find("\"read_only\":true") != std::string::npos);
  assert(json.find("\"can_take\":{\"state\":\"known\",\"value\":true}") !=
         std::string::npos);
  assert(json.find("\"effect_preview\":{\"state\":\"unavailable\"") !=
         std::string::npos);
  assert(json.find("\"unavailable_reason\":\"effect_preview_not_provided\"") !=
         std::string::npos);
  assert(json.find("\"executable\":false") != std::string::npos);
  assert(json.find("\"action_ready\":false") != std::string::npos);
  assert(json.find(bridge::kMajorDecisionFoundKingdomDecisionBlockSha256V1) !=
         std::string::npos);
  assert(json.find(bridge::kMajorDecisionFoundKingdomEffectBlockSha256V1) !=
         std::string::npos);
}

void TestThreeEligibilityGroupsPreserveKnownFalse() {
  for (int index = 0; index < 3; ++index) {
    auto capture = BaseCapture();
    if (index == 0) capture.first_sample.is_shown = Known(false);
    if (index == 1) capture.first_sample.is_valid = Known(false);
    if (index == 2) {
      capture.first_sample.is_valid_showing_failures_only = Known(false);
    }
    capture.first_sample.can_take = Known(false);
    capture.second_sample = capture.first_sample;
    const auto output = ObserveAvailable(capture);
    assert(output.readiness.eligibility_ready);
    assert(output.readiness.can_take_ready);
    assert(output.readiness.semantic_observation_ready);
    assert(!output.can_take.value);
    assert(!output.readiness.action_ready);
  }
}

void TestTypedUnknownDoesNotBecomeFalseOrZero() {
  auto eligibility = BaseCapture();
  eligibility.first_sample.is_valid =
      Unknown(UnknownReason::decision_evaluator_unavailable);
  eligibility.first_sample.can_take =
      Unknown(UnknownReason::can_take_evaluator_unavailable);
  eligibility.second_sample = eligibility.first_sample;
  const auto eligibility_output = ObserveAvailable(eligibility);
  assert(!eligibility_output.readiness.eligibility_ready);
  assert(!eligibility_output.readiness.can_take_ready);
  assert(!eligibility_output.readiness.semantic_observation_ready);
  assert(eligibility_output.is_valid.state == FieldState::unknown);
  assert(eligibility_output.is_valid.unknown_reason ==
         UnknownReason::decision_evaluator_unavailable);

  auto cost = BaseCapture();
  cost.first_sample.evaluated_cost = UnknownCost();
  cost.first_sample.is_affordable =
      Unknown(UnknownReason::affordability_evaluator_unavailable);
  cost.first_sample.can_take =
      Unknown(UnknownReason::can_take_evaluator_unavailable);
  cost.second_sample = cost.first_sample;
  const auto cost_output = ObserveAvailable(cost);
  assert(cost_output.evaluated_cost.state == FieldState::unknown);
  assert(cost_output.evaluated_cost.gold_q100000 == 0);
  assert(!cost_output.readiness.evaluated_cost_ready);
  assert(!cost_output.readiness.affordability_ready);
  assert(!cost_output.readiness.semantic_observation_ready);
}

void TestCanTakeTrueRequiresEverySemanticInput() {
  auto blocked = BaseCapture();
  blocked.first_sample.is_affordable = Known(false);
  blocked.second_sample = blocked.first_sample;
  ExpectFailure(blocked, Failure::can_take_invariant_failed);

  auto unknown = BaseCapture();
  unknown.first_sample.is_valid =
      Unknown(UnknownReason::decision_evaluator_unavailable);
  unknown.second_sample = unknown.first_sample;
  ExpectFailure(unknown, Failure::can_take_invariant_failed);

  auto missing_cost = BaseCapture();
  missing_cost.first_sample.evaluated_cost = UnknownCost();
  missing_cost.second_sample = missing_cost.first_sample;
  ExpectFailure(missing_cost, Failure::can_take_invariant_failed);
}

void TestEvaluatedCostInvariants() {
  auto negative = BaseCapture();
  negative.first_sample.evaluated_cost.gold_q100000 = -1;
  negative.second_sample = negative.first_sample;
  ExpectFailure(negative, Failure::evaluated_cost_invalid);

  auto stale_unknown = BaseCapture();
  stale_unknown.first_sample.evaluated_cost = UnknownCost();
  stale_unknown.first_sample.evaluated_cost.prestige_q100000 = 1;
  stale_unknown.first_sample.can_take =
      Unknown(UnknownReason::can_take_evaluator_unavailable);
  stale_unknown.second_sample = stale_unknown.first_sample;
  ExpectFailure(stale_unknown, Failure::evaluated_cost_source_invalid);

  auto wrong_source = BaseCapture();
  wrong_source.first_sample.evaluated_cost.source =
      bridge::MajorDecisionCostSourceV1::unknown;
  wrong_source.second_sample = wrong_source.first_sample;
  ExpectFailure(wrong_source, Failure::evaluated_cost_source_invalid);

  auto zero = BaseCapture();
  zero.first_sample.evaluated_cost = KnownCost(0, 0, 0, 0);
  zero.second_sample = zero.first_sample;
  const auto output = ObserveAvailable(zero);
  assert(output.readiness.evaluated_cost_ready);
}

void TestBuildThreadPauseMapAndPlayerGates() {
  auto disabled = BaseCapture();
  disabled.observer_enabled = false;
  ExpectFailure(disabled, Failure::observer_disabled);

  auto build = BaseCapture();
  build.admitted_executable_sha256[0] = '0';
  ExpectFailure(build, Failure::exact_build_not_admitted);

  auto thread = BaseCapture();
  thread.frame_before.application_main_thread = false;
  thread.frame_after = thread.frame_before;
  ExpectFailure(thread, Failure::application_main_thread_required);

  auto pause = BaseCapture();
  pause.frame_before.paused = false;
  pause.frame_after = pause.frame_before;
  ExpectFailure(pause, Failure::not_paused);

  auto map = BaseCapture();
  map.frame_before.map_ready = false;
  map.frame_after = map.frame_before;
  ExpectFailure(map, Failure::map_not_ready);

  auto player = BaseCapture();
  player.frame_before.played_character_alive = false;
  player.frame_after = player.frame_before;
  ExpectFailure(player, Failure::played_character_unavailable);
}

void TestFrameAndSourceDriftFailClosed() {
  auto frame = BaseCapture();
  ++frame.frame_after.proof_epoch;
  ExpectFailure(frame, Failure::frame_drift);

  auto source = BaseCapture();
  source.second_sample.evaluated_cost.piety_q100000 += 1;
  ExpectFailure(source, Failure::source_sample_drift);
}

void TestTypedFailureVocabularyAndSampleIdentity() {
  auto incomplete = BaseCapture();
  incomplete.first_sample.source_read_complete = false;
  incomplete.second_sample = incomplete.first_sample;
  ExpectFailure(incomplete, Failure::source_sample_incomplete);

  auto wrong_player = BaseCapture();
  wrong_player.first_sample.played_character_id = 1;
  wrong_player.second_sample = wrong_player.first_sample;
  ExpectFailure(wrong_player, Failure::played_character_identity_mismatch);

  auto wrong_definition = BaseCapture();
  wrong_definition.first_sample.decision_definition_identity_round_trip = false;
  wrong_definition.second_sample = wrong_definition.first_sample;
  ExpectFailure(wrong_definition,
                Failure::decision_definition_identity_mismatch);

  auto wrong_source = BaseCapture();
  wrong_source.first_sample.eligibility_source =
      bridge::MajorDecisionEligibilitySourceV1::unknown;
  wrong_source.second_sample = wrong_source.first_sample;
  ExpectFailure(wrong_source, Failure::eligibility_source_invalid);

  auto stale_unknown = BaseCapture();
  stale_unknown.first_sample.can_take =
      Unknown(UnknownReason::can_take_evaluator_unavailable);
  stale_unknown.first_sample.can_take.value = true;
  stale_unknown.second_sample = stale_unknown.first_sample;
  ExpectFailure(stale_unknown, Failure::typed_field_invalid);

  assert(bridge::MajorDecisionUnknownReasonKeyV1(
             UnknownReason::effect_preview_not_provided) ==
         "effect_preview_not_provided");
}

} // namespace

int main() {
  TestAvailablePlayedCharacterSnapshot();
  TestSerializerCannotAdvertiseExecution();
  TestThreeEligibilityGroupsPreserveKnownFalse();
  TestTypedUnknownDoesNotBecomeFalseOrZero();
  TestCanTakeTrueRequiresEverySemanticInput();
  TestEvaluatedCostInvariants();
  TestBuildThreadPauseMapAndPlayerGates();
  TestFrameAndSourceDriftFailClosed();
  TestTypedFailureVocabularyAndSampleIdentity();
  std::cout << "major_decision_found_kingdom_observer_v1_test: 9/9 GREEN\n";
  return 0;
}
