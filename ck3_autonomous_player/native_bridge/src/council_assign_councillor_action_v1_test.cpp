#include "xar_bridge/council_assign_councillor_action_v1.hpp"

#include <algorithm>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string>

namespace {

using AckStatus = xar::game::CouncilAssignCouncillorAckStatusV1;
using Failure = xar::game::CouncilAssignCouncillorFailureV1;
using ReceiptStatus = xar::game::CouncilAssignCouncillorReceiptStatusV1;
using Route = xar::game::CouncilAssignCouncillorRouteV1;

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "council assign councillor action fixture failed at line " +
        std::to_string(location.line()));
  }
}

template <std::size_t Size>
void SetFixed(std::array<char, Size> &target, std::string_view value) {
  target.fill('\0');
  Require(value.size() < target.size());
  std::copy(value.begin(), value.end(), target.begin());
}

struct Fixture {
  xar::game::CouncilAssignCouncillorFrameV1 frame{};
  xar::game::CouncilAssignCouncillorFinalLegalityV1 legality{};
  int capture_count = 0;
  int legality_count = 0;
  int invocation_count = 0;
  bool capture_result = true;
  bool legality_result = true;
  bool invocation_result = true;
  bool drift = false;
  xar::game::CouncilAssignCouncillorNativeSubmissionV1 submission{};

  explicit Fixture(bool occupied = false) {
    frame.available = true;
    frame.paused = true;
    frame.map_ready = true;
    frame.snapshot_id = "council-frame-700";
    frame.public_revision = 70;
    frame.native_revision = 700;
    frame.date_raw = 53'175'816;
    frame.owner_character_id = 0x01007485;
    frame.owner_identity_round_trip = true;
    frame.position_key = "councillor_steward";
    frame.active_task_id = 0x02001BF7;
    frame.active_task_identity_round_trip = true;
    frame.has_incumbent = occupied;
    frame.incumbent_character_id = occupied ? 0x01001234 : -1;
    frame.incumbent_identity_round_trip = occupied;

    legality.available = true;
    legality.owner_character_id = frame.owner_character_id;
    legality.active_task_id = frame.active_task_id;
    legality.position_key = frame.position_key;
    legality.candidate_character_id = 0x01005678;
    legality.candidate_match_count = 1;
    legality.candidate_identity_round_trip = true;
    legality.incumbent_fireability_evaluated = occupied;
    legality.incumbent_can_be_fired = occupied;
  }
};

bool Capture(
    void *context,
    xar::game::CouncilAssignCouncillorFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.frame;
  if (++fixture.capture_count == 2 && fixture.drift) {
    ++output.native_revision;
  }
  return fixture.capture_result;
}

bool Recheck(
    void *context, const xar::game::CouncilAssignCouncillorFrameV1 &,
    std::int32_t,
    xar::game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.legality_count;
  output = fixture.legality;
  return fixture.legality_result;
}

bool Invoke(
    void *context,
    const xar::game::CouncilAssignCouncillorNativeSubmissionV1
        &submission) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.invocation_count;
  fixture.submission = submission;
  return fixture.invocation_result;
}

xar::game::CouncilAssignCouncillorActionRequestV1 Request(
    const Fixture &fixture) {
  return {
      "council22-fixture-1",
      fixture.frame.position_key,
      fixture.frame.snapshot_id,
      fixture.frame.public_revision,
      fixture.frame.native_revision,
      fixture.frame.date_raw,
      fixture.frame.owner_character_id,
      fixture.legality.candidate_character_id,
      fixture.frame.has_incumbent,
      fixture.frame.incumbent_character_id,
  };
}

xar::game::CouncilCompositionCandidatesPublicV1 PublicCandidates(
    const Fixture &fixture) {
  xar::game::CouncilCompositionCandidatesPublicV1 value{};
  value.status =
      xar::game::CouncilCompositionCandidatesPublicStatusV1::available;
  SetFixed(value.snapshot_id, fixture.frame.snapshot_id);
  value.public_revision = fixture.frame.public_revision;
  value.native_revision = fixture.frame.native_revision;
  value.date_raw = fixture.frame.date_raw;
  value.paused = true;
  value.owner_character_id = fixture.frame.owner_character_id;
  SetFixed(value.position_key, fixture.frame.position_key);
  value.incumbent_character_id = fixture.frame.incumbent_character_id;
  value.vacant = !fixture.frame.has_incumbent;
  value.action_route = value.vacant
      ? xar::game::CouncilCompositionCandidateActionRouteV1::assign
      : xar::game::CouncilCompositionCandidateActionRouteV1::replace;
  value.candidate_collection_complete = true;
  value.candidate_count = 1;
  value.candidates[0].character_id = fixture.legality.candidate_character_id;
  value.candidates[0].eligible = true;
  value.candidates[0].action_route = value.action_route;
  SetFixed(value.candidates[0].main_skill.key, "stewardship");
  value.candidates[0].main_skill.value = 16;
  value.readiness.identity_ready = true;
  value.readiness.candidate_collection_ready = true;
  value.readiness.incumbent_ready = true;
  value.readiness.candidate_legality_ready = true;
  value.readiness.main_skill_ready = true;
  value.readiness.action_route_ready = true;
  value.readiness.same_frame_ready = true;
  value.readiness.ready = true;
  return value;
}

xar::ck3_11906::CouncilAssignCouncillorNativeEnvironmentV1 Environment() {
  return {
      true,
      xar::ck3_11906::kCouncilAssignCouncillorExecutableSha256V1,
      0,
      true,
      true,
      true,
      19,
      19,
  };
}

xar::ck3_11906::CouncilAssignCouncillorActionAccessV1 Access(
    Fixture &fixture) {
  return {&fixture, Capture, Recheck, Invoke};
}

xar::game::CouncilAssignCouncillorActionAckV1 Execute(Fixture &fixture) {
  xar::game::CouncilAssignCouncillorActionAckV1 ack{};
  Require(xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
              Environment(), Access(fixture), Request(fixture), ack) ==
          AckStatus::native_helper_invoked_verification_pending);
  return ack;
}

void TestPrivateAndExactBuildGates() {
  Fixture fixture;
  auto environment = Environment();
  auto request = Request(fixture);
  xar::game::CouncilAssignCouncillorActionAckV1 ack{};
  environment.private_candidate_admitted = false;
  xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
      environment, Access(fixture), request, ack);
  Require(ack.failure == Failure::private_candidate_not_admitted);
  Require(fixture.capture_count == 0 && fixture.invocation_count == 0);

  environment = Environment();
  environment.admitted_executable_sha256 = "wrong";
  xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
      environment, Access(fixture), request, ack);
  Require(ack.failure == Failure::exact_build_mismatch);
  Require(fixture.invocation_count == 0);
}

void TestCouncil19TypedRequestPreparation() {
  Fixture fixture(true);
  auto candidates = PublicCandidates(fixture);
  xar::game::CouncilAssignCouncillorActionRequestV1 request{};
  Require(xar::ck3_11906::PrepareCouncilAssignCouncillorActionRequestV1(
      candidates, fixture.legality.candidate_character_id,
      "council22-from-public", request));
  Require(request.expected_snapshot_id == fixture.frame.snapshot_id);
  Require(request.expected_public_revision == fixture.frame.public_revision);
  Require(request.expected_native_revision == fixture.frame.native_revision);
  Require(request.expected_has_incumbent);
  Require(request.expected_incumbent_character_id ==
          fixture.frame.incumbent_character_id);

  candidates.candidates[0].eligible = false;
  Require(!xar::ck3_11906::PrepareCouncilAssignCouncillorActionRequestV1(
      candidates, fixture.legality.candidate_character_id,
      "council22-ineligible", request));
  candidates = PublicCandidates(fixture);
  candidates.readiness.same_frame_ready = false;
  Require(!xar::ck3_11906::PrepareCouncilAssignCouncillorActionRequestV1(
      candidates, fixture.legality.candidate_character_id,
      "council22-stale", request));
}

void TestAssignAndReplaceRoutes() {
  Fixture vacant;
  const auto assign_ack = Execute(vacant);
  Require(assign_ack.route == Route::assign_vacant);
  Require(assign_ack.native_helper_invoked);
  Require(!assign_ack.queue_acceptance_observed);
  Require(assign_ack.verification_pending);
  Require(vacant.invocation_count == 1);
  Require(vacant.submission.active_task_id == vacant.frame.active_task_id);
  Require(vacant.submission.candidate_character_id ==
          vacant.legality.candidate_character_id);

  Fixture occupied(true);
  const auto replace_ack = Execute(occupied);
  Require(replace_ack.route == Route::replace_incumbent);
  Require(replace_ack.had_incumbent);
  Require(occupied.submission.previous_incumbent_character_id ==
          occupied.frame.incumbent_character_id);
  Require(occupied.invocation_count == 1);
}

void TestBindingAndLegalityFailuresNeverInvoke() {
  {
    Fixture fixture;
    auto request = Request(fixture);
    ++request.expected_native_revision;
    xar::game::CouncilAssignCouncillorActionAckV1 ack{};
    xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
        Environment(), Access(fixture), request, ack);
    Require(ack.failure == Failure::snapshot_binding_mismatch);
    Require(fixture.legality_count == 0 && fixture.invocation_count == 0);
  }
  {
    Fixture fixture;
    fixture.legality.candidate_match_count = 0;
    xar::game::CouncilAssignCouncillorActionAckV1 ack{};
    xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
        Environment(), Access(fixture), Request(fixture), ack);
    Require(ack.failure == Failure::candidate_not_in_exact_collection);
    Require(fixture.invocation_count == 0);
  }
  {
    Fixture fixture;
    fixture.legality.candidate_identity_round_trip = false;
    xar::game::CouncilAssignCouncillorActionAckV1 ack{};
    xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
        Environment(), Access(fixture), Request(fixture), ack);
    Require(ack.failure == Failure::candidate_identity_mismatch);
    Require(fixture.invocation_count == 0);
  }
  {
    Fixture fixture;
    fixture.legality.candidate_already_councillor = true;
    xar::game::CouncilAssignCouncillorActionAckV1 ack{};
    xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
        Environment(), Access(fixture), Request(fixture), ack);
    Require(ack.failure == Failure::candidate_already_councillor);
    Require(fixture.invocation_count == 0);
  }
  {
    Fixture fixture;
    fixture.legality.candidate_is_guest = true;
    xar::game::CouncilAssignCouncillorActionAckV1 ack{};
    xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
        Environment(), Access(fixture), Request(fixture), ack);
    Require(ack.failure == Failure::candidate_is_guest);
    Require(fixture.invocation_count == 0);
  }
  {
    Fixture fixture;
    fixture.legality.pending_character_interaction = true;
    xar::game::CouncilAssignCouncillorActionAckV1 ack{};
    xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
        Environment(), Access(fixture), Request(fixture), ack);
    Require(ack.failure == Failure::pending_character_interaction);
    Require(fixture.invocation_count == 0);
  }
  {
    Fixture fixture(true);
    fixture.legality.incumbent_can_be_fired = false;
    fixture.legality.native_reason_key = "CANNOT_FIRE_COUNCILLOR";
    xar::game::CouncilAssignCouncillorActionAckV1 ack{};
    xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
        Environment(), Access(fixture), Request(fixture), ack);
    Require(ack.failure == Failure::incumbent_cannot_be_replaced);
    Require(ack.native_reason_key == "CANNOT_FIRE_COUNCILLOR");
    Require(fixture.invocation_count == 0);
  }
  {
    Fixture fixture;
    fixture.drift = true;
    xar::game::CouncilAssignCouncillorActionAckV1 ack{};
    xar::ck3_11906::ExecuteCouncilAssignCouncillorActionV1(
        Environment(), Access(fixture), Request(fixture), ack);
    Require(ack.failure == Failure::state_changed_before_submit);
    Require(fixture.invocation_count == 0);
  }
}

void TestReceiptRequiresNewIndependentIncumbentObservation() {
  Fixture fixture(true);
  const auto ack = Execute(fixture);
  auto post = fixture.frame;
  post.snapshot_id = "council-frame-701";
  ++post.public_revision;
  ++post.native_revision;
  post.incumbent_character_id = ack.candidate_character_id;
  post.incumbent_identity_round_trip = true;
  xar::game::CouncilAssignCouncillorActionReceiptV1 receipt{};
  Require(xar::ck3_11906::VerifyCouncilAssignCouncillorActionReceiptV1(
              ack, post, receipt) == ReceiptStatus::applied);
  Require(receipt.postcondition_verified);

  auto stale = post;
  stale.snapshot_id = ack.pre_snapshot_id;
  Require(xar::ck3_11906::VerifyCouncilAssignCouncillorActionReceiptV1(
              ack, stale, receipt) == ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "no_new_paused_frame");

  auto wrong = post;
  wrong.incumbent_character_id = fixture.frame.incumbent_character_id;
  Require(xar::ck3_11906::VerifyCouncilAssignCouncillorActionReceiptV1(
              ack, wrong, receipt) == ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "candidate_not_observed_as_incumbent");

  auto wrong_owner = post;
  ++wrong_owner.owner_character_id;
  Require(xar::ck3_11906::VerifyCouncilAssignCouncillorActionReceiptV1(
              ack, wrong_owner, receipt) == ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "owner_or_position_changed");
}

} // namespace

int main() {
  try {
    using namespace xar::ck3_11906;
    static_assert(!kCouncilAssignCouncillorAdvertisedByDefaultV1);
    static_assert(kCouncilAssignCouncillorExecutableSha256V1.size() == 64);
    Require(kCouncilAssignCouncillorActionTargetCapabilityV1 ==
            "game.action.assign-councillor-v1");
    Require(CouncilAssignCouncillorRouteKeyV1(Route::replace_incumbent) ==
            "replace_incumbent");
    TestPrivateAndExactBuildGates();
    TestCouncil19TypedRequestPreparation();
    TestAssignAndReplaceRoutes();
    TestBindingAndLegalityFailuresNeverInvoke();
    TestReceiptRequiresNewIndependentIncumbentObservation();
    std::cout << "council_assign_councillor_action_v1_test: GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
