#include "xar_bridge/marriage_matchmaking_observer_v1.hpp"

#include <algorithm>
#include <cassert>
#include <cstring>
#include <iostream>
#include <string_view>

namespace {

namespace bridge = xar::bridge;

struct Fixture {
  bridge::MarriageMatchmakingFrameV1 before{};
  bridge::MarriageMatchmakingFrameV1 after{};
  bridge::MarriageNativeSourceResultV1 source_result =
      bridge::MarriageNativeSourceResultV1::available;
  bridge::MarriageNativeEvaluationResultV1 evaluation_result =
      bridge::MarriageNativeEvaluationResultV1::available;
  std::array<bridge::MarriageMatchmakingRankedRowV1,
             bridge::kMarriageMatchmakingMaximumCandidatesV1>
      rows{};
  std::uint32_t row_count = 0;
  std::uint32_t frame_calls = 0;
  std::uint32_t source_calls = 0;
  std::uint32_t evaluation_calls = 0;
  bool main_thread = true;
  bool drift_second_source = false;
  bool duplicate_candidate = false;
  bool invalid_roles = false;
  bool saw_exact_entry_points = false;
};

void CopySnapshotId(bridge::MarriageMatchmakingFrameV1 &frame,
                    std::string_view value) {
  assert(value.size() < frame.snapshot_id.size());
  std::memcpy(frame.snapshot_id.data(), value.data(), value.size());
}

Fixture BaseFixture() {
  Fixture fixture{};
  CopySnapshotId(fixture.before, "marriage2-fixture-001");
  fixture.before.public_revision = 712;
  fixture.before.native_revision = 9177;
  fixture.before.proof_epoch = 23;
  fixture.before.date_raw = 54'654'000;
  fixture.before.paused = true;
  fixture.before.map_ready = true;
  fixture.before.has_played_character = true;
  fixture.before.played_character_alive = true;
  fixture.before.played_character_id = 32904;
  fixture.before.played_character_identity_round_trip = true;
  fixture.after = fixture.before;
  fixture.rows[0] = {41002, 187'500};
  fixture.rows[1] = {41003, 25'000};
  fixture.row_count = 2;
  return fixture;
}

bridge::MarriageMatchmakingObserverRequestV1 Request() {
  bridge::MarriageMatchmakingObserverRequestV1 request{};
  request.expected_snapshot_id = "marriage2-fixture-001";
  request.expected_public_revision = 712;
  request.expected_native_revision = 9177;
  request.expected_date_raw = 54'654'000;
  request.subject_character_id = 32904;
  request.matchmaker_character_id = 32904;
  request.limit = 8;
  return request;
}

bridge::MarriageMatchmakingObserverEnvironmentV1 Environment() {
  bridge::MarriageMatchmakingObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      bridge::kMarriageMatchmakingObserverExecutableSha256V1;
  environment.module_base = 0x140000000ULL;
  environment.offline_fixture = true;
  environment.native = bridge::BindMarriageMatchmakingNativeEntryPointsV1(
      environment.module_base);
  return environment;
}

bool Capture(void *context,
             bridge::MarriageMatchmakingFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.frame_calls++ == 0 ? fixture.before : fixture.after;
  return true;
}

bool IsMainThread(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool ExactEntryPoints(
    const bridge::MarriageMatchmakingNativeEntryPointsV1 &native) {
  return native == bridge::BindMarriageMatchmakingNativeEntryPointsV1(
                       0x140000000ULL) &&
      native.enumerate_candidates == 0x141890470ULL &&
      native.score_filter_candidates == 0x141890D90ULL &&
      native.complete_can_send == 0x142C43F00ULL &&
      native.recipient_ai_accept == 0x142C44320ULL &&
      native.outer_answer == 0x142C43B40ULL;
}

bridge::MarriageNativeSourceResultV1 ReadRanked(
    void *context,
    const bridge::MarriageMatchmakingNativeEntryPointsV1 &native,
    std::uint32_t subject_character_id, std::uint32_t limit,
    std::array<bridge::MarriageMatchmakingRankedRowV1,
               bridge::kMarriageMatchmakingMaximumCandidatesV1> &output,
    std::uint32_t &output_count) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  fixture.saw_exact_entry_points = ExactEntryPoints(native);
  if (fixture.source_result !=
      bridge::MarriageNativeSourceResultV1::available) {
    return fixture.source_result;
  }
  if (subject_character_id != 32904 || limit != 8) {
    return bridge::MarriageNativeSourceResultV1::failed;
  }
  output = fixture.rows;
  output_count = fixture.row_count;
  if (fixture.duplicate_candidate && output_count > 1) {
    output[1].candidate_character_id = output[0].candidate_character_id;
  }
  if (fixture.drift_second_source && fixture.source_calls == 1 &&
      output_count != 0) {
    ++output[0].native_candidate_score;
  }
  ++fixture.source_calls;
  return bridge::MarriageNativeSourceResultV1::available;
}

bridge::MarriageNativeEvaluationResultV1 Evaluate(
    void *context,
    const bridge::MarriageMatchmakingNativeEntryPointsV1 &native,
    std::uint32_t subject_character_id,
    std::uint32_t matchmaker_character_id,
    std::uint32_t candidate_character_id,
    bridge::MarriageMatchmakingPairEvaluationV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  fixture.saw_exact_entry_points =
      fixture.saw_exact_entry_points && ExactEntryPoints(native);
  ++fixture.evaluation_calls;
  if (fixture.evaluation_result !=
      bridge::MarriageNativeEvaluationResultV1::available) {
    return fixture.evaluation_result;
  }
  output = {};
  output.roles.actor_character_id = matchmaker_character_id;
  output.roles.recipient_character_id = candidate_character_id;
  output.roles.secondary_actor_character_id = subject_character_id;
  output.roles.secondary_recipient_character_id = candidate_character_id;
  output.roles.intermediary_character_id = 0;
  if (fixture.invalid_roles) {
    output.roles.secondary_recipient_character_id = 99999;
  }
  output.complete_can_send = candidate_character_id == 41002;
  output.complete_can_send_status_raw =
      output.complete_can_send ? 1 : -17;
  output.recipient_ai_accept_raw =
      candidate_character_id == 41002 ? 350'000 : -125'000;
  output.recipient_answer_status_raw =
      candidate_character_id == 41002 ? 2 : 1;
  output.recipient_answer_allows_send = candidate_character_id == 41002;
  output.predicted_outcome =
      candidate_character_id == 41002
          ? bridge::MarriagePredictedOutcomeV1::marriage
          : bridge::MarriagePredictedOutcomeV1::betrothal;
  return bridge::MarriageNativeEvaluationResultV1::available;
}

bridge::MarriageMatchmakingObserverAccessV1 Access(Fixture &fixture) {
  bridge::MarriageMatchmakingObserverAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMainThread;
  access.read_ranked_candidates = &ReadRanked;
  access.evaluate_candidate = &Evaluate;
  return access;
}

void TestNormalObservation() {
  auto fixture = BaseFixture();
  bridge::MarriageMatchmakingObservationV1 output{};
  assert(bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(fixture), Request(), output));
  assert(fixture.frame_calls == 2 && fixture.source_calls == 2 &&
         fixture.evaluation_calls == 4 && fixture.saw_exact_entry_points);
  assert(output.status ==
         bridge::MarriageMatchmakingObserverStatusV1::available);
  assert(output.subject_character_id == 32904 &&
         output.matchmaker_character_id == 32904);
  assert(output.candidate_count == 2);
  assert(output.candidates[0].rank == 1 &&
         output.candidates[0].candidate_character_id == 41002 &&
         output.candidates[0].native_candidate_score == 187'500);
  assert(output.candidates[0].evaluation.complete_can_send);
  assert(output.candidates[0].evaluation.recipient_ai_accept_raw == 350'000);
  assert(output.candidates[0].evaluation.recipient_answer_allows_send);
  assert(output.candidates[0].evaluation.predicted_outcome ==
         bridge::MarriagePredictedOutcomeV1::marriage);
  assert(!output.candidates[1].evaluation.complete_can_send);
  assert(output.candidates[1].evaluation.predicted_outcome ==
         bridge::MarriagePredictedOutcomeV1::betrothal);
  assert(output.readiness.ranked_candidates_ready &&
         output.readiness.pair_character_ids_ready &&
         output.readiness.native_score_ready &&
         output.readiness.complete_can_send_ready &&
         output.readiness.recipient_ai_accept_ready &&
         output.readiness.recipient_answer_ready &&
         output.readiness.predicted_outcome_ready &&
         output.readiness.same_frame_ready);

  const auto json = bridge::SerializeMarriageMatchmakingObservationV1(output);
  assert(json.find("\"private_build\":true,\"advertised\":false") !=
         std::string::npos);
  assert(json.find("\"subject_character_id\":32904") !=
         std::string::npos);
  assert(json.find("\"rank\":1,\"subject_character_id\":32904,"
                   "\"matchmaker_character_id\":32904") !=
         std::string::npos);
  assert(json.find("\"candidate_character_id\":41002") !=
         std::string::npos);
  assert(json.find("\"native_candidate_score\":187500") !=
         std::string::npos);
  assert(json.find("\"recipient_ai_accept_scale\":100000") !=
         std::string::npos);
  assert(json.find("\"religion_projection\":"
                   "\"native_final_results_only\"") != std::string::npos);
  assert(json.find("faith") == std::string::npos);
  assert(json.find("doctrine") == std::string::npos);
  assert(json.find("tenet") == std::string::npos);
  assert(json.find("fervor") == std::string::npos);
}

void TestExactCandidateFilterPreservesNativeRank() {
  auto fixture = BaseFixture();
  auto request = Request();
  request.candidate_character_id = 41003;
  bridge::MarriageMatchmakingObservationV1 output{};
  assert(bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(fixture), request, output));
  assert(output.candidate_count == 1);
  assert(output.candidates[0].rank == 2);
  assert(output.candidates[0].candidate_character_id == 41003);
  assert(output.candidates[0].native_candidate_score == 25'000);
}

void TestRankedSourceUnavailableIsNotEmptySuccess() {
  auto fixture = BaseFixture();
  fixture.source_result =
      bridge::MarriageNativeSourceResultV1::ranked_source_unavailable;
  bridge::MarriageMatchmakingObservationV1 output{};
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(fixture), Request(), output));
  assert(output.status ==
         bridge::MarriageMatchmakingObserverStatusV1::unavailable);
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::
             ranked_source_unavailable);
  assert(output.candidate_count == 0);
  assert(bridge::SerializeMarriageMatchmakingObservationV1(output) ==
         "{\"private_build\":true,\"advertised\":false,"
         "\"status\":\"unavailable\","
         "\"unavailable_reason\":\"ranked_source_unavailable\"}");
}

void TestSampleAndFrameDriftFailAtomically() {
  auto sample_drift = BaseFixture();
  sample_drift.drift_second_source = true;
  bridge::MarriageMatchmakingObservationV1 output{};
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(sample_drift), Request(), output));
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::native_sample_drift);
  assert(output.candidate_count == 0);

  auto frame_drift = BaseFixture();
  ++frame_drift.after.proof_epoch;
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(frame_drift), Request(), output));
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::revision_drift);
  assert(output.candidate_count == 0);
}

void TestCandidateAndPairValidation() {
  auto duplicate = BaseFixture();
  duplicate.duplicate_candidate = true;
  bridge::MarriageMatchmakingObservationV1 output{};
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(duplicate), Request(), output));
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::
             candidate_collection_invalid);

  auto invalid_roles = BaseFixture();
  invalid_roles.invalid_roles = true;
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(invalid_roles), Request(), output));
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::pair_roles_invalid);

  auto failed_evaluation = BaseFixture();
  failed_evaluation.evaluation_result =
      bridge::MarriageNativeEvaluationResultV1::failed;
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(failed_evaluation), Request(), output));
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::
             pair_evaluation_failed);
}

void TestAdmissionAndThreadGuards() {
  auto fixture = BaseFixture();
  bridge::MarriageMatchmakingObservationV1 output{};
  auto environment = Environment();
  environment.admitted_executable_sha256 = "wrong";
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      environment, Access(fixture), Request(), output));
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::
             exact_build_not_admitted);

  fixture = BaseFixture();
  environment = Environment();
  environment.native.outer_answer = 0;
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      environment, Access(fixture), Request(), output));
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::
             native_entry_points_unavailable);

  fixture = BaseFixture();
  fixture.main_thread = false;
  assert(!bridge::ReadMarriageMatchmakingObserverV1(
      Environment(), Access(fixture), Request(), output));
  assert(output.unavailable_reason ==
         bridge::MarriageMatchmakingObserverFailureV1::
             application_main_thread_required);
}

void TestNativeLayoutAndBindingConstants() {
  static_assert(bridge::kMarriageNativeRankedRowStrideV1 == 16);
  static_assert(bridge::kMarriageNativeRankedRowCharacterIdOffsetV1 == 8);
  static_assert(bridge::kMarriageNativeRankedRowScoreOffsetV1 == 12);
  static_assert(bridge::kMarriageMatchmakingMaximumCandidatesV1 == 8);
  static_assert(bridge::kMarriageAiAcceptFixedPointScaleV1 == 100000);
  const auto native = bridge::BindMarriageMatchmakingNativeEntryPointsV1(
      0x140000000ULL);
  assert(ExactEntryPoints(native));
  assert(native.candidate_gate_and_score == 0x141890F40ULL);
  assert(native.outcome_dispatch == 0x142282DE0ULL);
  assert(bridge::BindMarriageMatchmakingNativeEntryPointsV1(0) ==
         bridge::MarriageMatchmakingNativeEntryPointsV1{});
}

} // namespace

int main() {
  TestNativeLayoutAndBindingConstants();
  TestNormalObservation();
  TestExactCandidateFilterPreservesNativeRank();
  TestRankedSourceUnavailableIsNotEmptySuccess();
  TestSampleAndFrameDriftFailAtomically();
  TestCandidateAndPairValidation();
  TestAdmissionAndThreadGuards();
  std::cout << "GREEN: marriage-matchmaking-observer-v1 private fixture\n";
  return 0;
}
