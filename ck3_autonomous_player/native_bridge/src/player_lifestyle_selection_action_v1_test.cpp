#include "xar_bridge/player_lifestyle_selection_action_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <source_location>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

namespace ck3 = xar::ck3_11906;
namespace game = xar::game;

using AckStatus = game::PlayerLifestyleSelectionActionAckStatusV1;
using FailureClass = game::PlayerLifestyleSelectionActionFailureClassV1;
using Kind = game::PlayerLifestyleSelectionKindV1;
using ReceiptStatus = game::PlayerLifestyleSelectionActionReceiptStatusV1;
using StableKey = game::PlayerLifestyleWindowStableKeyV1;

constexpr std::uintptr_t kModule = 0x0000000140000000ULL;
constexpr std::uint32_t kPlayer = 0xF100002A;
constexpr std::string_view kSnapshot = "native:711";
constexpr std::string_view kPostSnapshot = "native:712";
constexpr std::string_view kEpisode = "native-29829-ee172aa720db";

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "lifestyle selection action fixture failed at line " +
        std::to_string(location.line()));
  }
}

StableKey Key(std::string_view value) {
  StableKey output{};
  Require(ck3::AssignPlayerLifestyleWindowStableKeyV1(value, output));
  return output;
}

template <std::size_t Size>
void Fixed(std::array<char, Size> &output, std::string_view value) {
  Require(value.size() < output.size());
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

struct Fixture {
  game::PlayerLifestyleSelectionPreconditionV1 precondition{};
  game::PlayerLifestyleSelectionStateObservationV1 receipt_state{};
  int precondition_captures = 0;
  int receipt_captures = 0;
  int submits = 0;
  bool main_thread = true;
  bool capture_precondition_result = true;
  bool capture_receipt_result = true;
  bool submit_result = true;
  bool drift_second_precondition = false;
  Kind submitted_kind = Kind::unknown;
  StableKey submitted_key{};
};

game::PlayerLifestyleSelectionStateObservationV1 State() {
  game::PlayerLifestyleSelectionStateObservationV1 output{};
  output.available = true;
  output.paused = true;
  Fixed(output.snapshot_id, kSnapshot);
  Fixed(output.episode_run_id, kEpisode);
  output.public_revision = 711;
  output.native_revision = 9'021;
  output.proof_epoch = 31;
  output.date_raw = 54'335'000;
  output.player_character_id = kPlayer;
  output.current_focus_known = true;
  output.has_current_focus = true;
  output.current_focus_key = Key("learning_medicine_focus");
  output.owned_perks_fully_materialized = true;
  output.owned_perk_count = 1;
  output.owned_perk_keys[0] = Key("architect_perk");
  output.lifestyle_progress_fully_materialized = true;
  output.lifestyle_progress_count = 2;
  output.lifestyle_progress[0] =
      {Key("stewardship_lifestyle"), 37'500, 2};
  output.lifestyle_progress[1] =
      {Key("learning_lifestyle"), 12'250, 0};
  return output;
}

game::PlayerLifestyleWindowCandidatesV1 Candidates() {
  game::PlayerLifestyleWindowCandidatesV1 output{};
  output.status = game::PlayerLifestyleWindowCandidatesStatusV1::available;
  output.unavailable_reason =
      game::PlayerLifestyleWindowCandidatesFailureV1::none;
  Fixed(output.snapshot_id, kSnapshot);
  output.public_revision = 711;
  output.native_revision = 9'021;
  output.proof_epoch = 31;
  output.date_raw = 54'335'000;
  output.player_character_id = kPlayer;
  output.focus_status =
      game::PlayerLifestyleWindowCollectionStatusV1::available;
  output.focus_count = 2;
  output.focuses[0] = {Key("learning_medicine_focus"),
                       Key("learning_lifestyle"), false};
  output.focuses[1] = {Key("stewardship_wealth_focus"),
                       Key("stewardship_lifestyle"), true};
  output.perk_status =
      game::PlayerLifestyleWindowCollectionStatusV1::available;
  output.perk_count = 2;
  output.perks[0] = {Key("architect_perk"),
                     Key("stewardship_lifestyle"), false, true};
  output.perks[1] = {Key("tax_man_perk"),
                     Key("stewardship_lifestyle"), true, true};
  output.readiness = {true, true, true, true, true, true, true};
  return output;
}

std::unique_ptr<Fixture> Base() {
  auto fixture = std::make_unique<Fixture>();
  fixture->precondition.candidates = Candidates();
  fixture->precondition.state = State();
  fixture->receipt_state = State();
  Fixed(fixture->receipt_state.snapshot_id, kPostSnapshot);
  ++fixture->receipt_state.public_revision;
  ++fixture->receipt_state.native_revision;
  ++fixture->receipt_state.proof_epoch;
  return fixture;
}

bool CapturePrecondition(
    void *context,
    game::PlayerLifestyleSelectionPreconditionV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.precondition_captures;
  if (!fixture.capture_precondition_result) return false;
  output = fixture.precondition;
  if (fixture.drift_second_precondition &&
      fixture.precondition_captures == 2) {
    ++output.candidates.native_revision;
    ++output.state.native_revision;
  }
  return true;
}

bool CaptureReceipt(
    void *context,
    game::PlayerLifestyleSelectionStateObservationV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.receipt_captures;
  if (!fixture.capture_receipt_result) return false;
  output = fixture.receipt_state;
  return true;
}

bool IsMainThread(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool Submit(void *context, Kind kind, const StableKey &target) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.submits;
  fixture.submitted_kind = kind;
  fixture.submitted_key = target;
  return fixture.submit_result;
}

ck3::PlayerLifestyleSelectionActionAccessV1 Access(Fixture &fixture) {
  return {&fixture, &CapturePrecondition, &CaptureReceipt, &IsMainThread,
          &Submit};
}

ck3::PlayerLifestyleSelectionActionEnvironmentV1 FixtureEnvironment() {
  return {true, ck3::kPlayerLifestyleSelectionActionExecutableSha256V1,
          kModule, false, true};
}

game::PlayerLifestyleSelectionActionRequestV1 Request(
    Kind kind, std::string_view target) {
  return {"life6-selection-request-1", kind, target, kSnapshot, kEpisode,
          711, 9'021, 31, 54'335'000, kPlayer};
}

game::PlayerLifestyleSelectionActionAckV1 SubmitExpected(
    Fixture &fixture, Kind kind, std::string_view target) {
  game::PlayerLifestyleSelectionActionAckV1 ack{};
  Require(ck3::ExecutePlayerLifestyleSelectionActionV1(
              FixtureEnvironment(), Access(fixture), Request(kind, target),
              ack) == AckStatus::submitted_verification_pending);
  Require(ack.status == AckStatus::submitted_verification_pending);
  Require(ack.verification_pending);
  Require(ack.failure_class == FailureClass::none);
  Require(fixture.precondition_captures == 2);
  Require(fixture.submits == 1);
  Require(fixture.submitted_kind == kind);
  Require(ck3::PlayerLifestyleWindowStableKeyViewV1(
              fixture.submitted_key) == target);
  return ack;
}

void TestFocusAckIsPendingAndReceiptRereadsState() {
  auto fixture = Base();
  const auto ack = SubmitExpected(
      *fixture, Kind::focus, "stewardship_wealth_focus");
  Require(ack.pre_has_current_focus);
  Require(ck3::PlayerLifestyleWindowStableKeyViewV1(
              ack.pre_current_focus_key) == "learning_medicine_focus");
  Require(ack.pre_target_lifestyle_experience_raw == 37'500);
  Require(ack.pre_target_lifestyle_perk_points == 2);

  fixture->receipt_state.current_focus_key =
      Key("stewardship_wealth_focus");
  game::PlayerLifestyleSelectionActionReceiptV1 receipt{};
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*fixture), ack, receipt) == ReceiptStatus::applied);
  Require(fixture->receipt_captures == 1);
  Require(receipt.current_focus_reread && receipt.owned_perks_reread &&
          receipt.experience_reread && receipt.perk_points_reread);
  Require(receipt.target_state_changed && receipt.postcondition_verified);
  Require(std::string_view(receipt.post_snapshot_id.data()) == kPostSnapshot);
  Require(std::string_view(receipt.episode_run_id.data()) == kEpisode);
  Require(receipt.post_target_lifestyle_experience_raw == 37'500);
  Require(receipt.post_target_lifestyle_perk_points == 2);
}

void TestPerkSubmitAcceptsWindowIndependentPartialCollection() {
  auto fixture = Base();
  auto &candidates = fixture->precondition.candidates;
  candidates.focus_status =
      game::PlayerLifestyleWindowCollectionStatusV1::unavailable;
  candidates.focus_count = 0;
  candidates.readiness.owner_path_ready = false;
  candidates.readiness.focus_candidates_ready = false;
  const auto ack = SubmitExpected(*fixture, Kind::perk, "tax_man_perk");
  Require(ack.kind == Kind::perk && fixture->submits == 1);
}

void TestPerkReceiptRequiresNewOwnedMembership() {
  auto fixture = Base();
  const auto ack = SubmitExpected(*fixture, Kind::perk, "tax_man_perk");
  Require(!ack.pre_target_perk_owned);
  fixture->receipt_state.owned_perk_count = 2;
  fixture->receipt_state.owned_perk_keys[1] = Key("tax_man_perk");
  fixture->receipt_state.lifestyle_progress[0].perk_points = 1;

  game::PlayerLifestyleSelectionActionReceiptV1 receipt{};
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*fixture), ack, receipt) == ReceiptStatus::applied);
  Require(receipt.post_target_perk_owned);
  Require(receipt.post_owned_perk_count == 2);
  Require(receipt.post_target_lifestyle_perk_points == 1);
  Require(receipt.target_state_changed && receipt.postcondition_verified);
}

void TestOnlyFinalCanSelectTargetCanSubmit() {
  {
    auto fixture = Base();
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    ck3::ExecutePlayerLifestyleSelectionActionV1(
        FixtureEnvironment(), Access(*fixture),
        Request(Kind::perk, "architect_perk"), ack);
    Require(ack.failure_class == FailureClass::final_legality);
    Require(ack.rejection_reason == "target_not_finally_selectable");
    // can_select_ignore_cost=true did not authorize the action.
    Require(fixture->submits == 0);
  }
  {
    auto fixture = Base();
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    ck3::ExecutePlayerLifestyleSelectionActionV1(
        FixtureEnvironment(), Access(*fixture),
        Request(Kind::focus, "missing_focus"), ack);
    Require(ack.failure_class == FailureClass::final_legality);
    Require(fixture->submits == 0);
  }
  {
    auto fixture = Base();
    auto request = Request(Kind::focus, "stewardship_wealth_focus");
    ++request.expected_native_revision;
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    ck3::ExecutePlayerLifestyleSelectionActionV1(
        FixtureEnvironment(), Access(*fixture), request, ack);
    Require(ack.failure_class == FailureClass::snapshot_binding);
    Require(fixture->submits == 0);
  }
}

void TestIncompleteStateAndPreSubmitDriftNeverSubmit() {
  {
    auto fixture = Base();
    fixture->precondition.state.current_focus_known = false;
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    ck3::ExecutePlayerLifestyleSelectionActionV1(
        FixtureEnvironment(), Access(*fixture),
        Request(Kind::focus, "stewardship_wealth_focus"), ack);
    Require(ack.failure_class == FailureClass::state_observation);
    Require(fixture->submits == 0);
  }
  {
    auto fixture = Base();
    fixture->precondition.state.lifestyle_progress_count = 1;
    fixture->precondition.state.lifestyle_progress[0] =
        {Key("learning_lifestyle"), 12'250, 0};
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    ck3::ExecutePlayerLifestyleSelectionActionV1(
        FixtureEnvironment(), Access(*fixture),
        Request(Kind::perk, "tax_man_perk"), ack);
    Require(ack.failure_class == FailureClass::state_observation);
    Require(fixture->submits == 0);
  }
  {
    auto fixture = Base();
    fixture->drift_second_precondition = true;
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    ck3::ExecutePlayerLifestyleSelectionActionV1(
        FixtureEnvironment(), Access(*fixture),
        Request(Kind::focus, "stewardship_wealth_focus"), ack);
    Require(ack.failure_class == FailureClass::snapshot_binding);
    Require(ack.rejection_reason == "state_changed_before_submit");
    Require(fixture->precondition_captures == 2 && fixture->submits == 0);
  }
}

void TestCommandBindingAndSubmitAreFailClosedAndSingleShot() {
  {
    auto fixture = Base();
    const auto production =
        ck3::BindPlayerLifestyleSelectionActionEnvironmentV1(
            kModule, true,
            ck3::kPlayerLifestyleSelectionActionExecutableSha256V1);
    Require(!production.command_abi_certified &&
            !production.offline_fixture_command);
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    ck3::ExecutePlayerLifestyleSelectionActionV1(
        production, Access(*fixture),
        Request(Kind::focus, "stewardship_wealth_focus"), ack);
    Require(ack.failure_class == FailureClass::exact_build_binding);
    Require(fixture->precondition_captures == 0 && fixture->submits == 0);
  }
  {
    auto fixture = Base();
    fixture->submit_result = false;
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    Require(ck3::ExecutePlayerLifestyleSelectionActionV1(
                FixtureEnvironment(), Access(*fixture),
                Request(Kind::perk, "tax_man_perk"), ack) ==
            AckStatus::rejected_before_submit);
    Require(ack.failure_class == FailureClass::native_command_dispatch);
    Require(ack.rejection_reason == "native_command_submit_failed");
    Require(!ack.verification_pending);
    Require(fixture->submits == 1);
  }
  {
    auto fixture = Base();
    fixture->main_thread = false;
    game::PlayerLifestyleSelectionActionAckV1 ack{};
    ck3::ExecutePlayerLifestyleSelectionActionV1(
        FixtureEnvironment(), Access(*fixture),
        Request(Kind::perk, "tax_man_perk"), ack);
    Require(ack.failure_class == FailureClass::snapshot_binding);
    Require(fixture->precondition_captures == 0 && fixture->submits == 0);
  }
}

void TestReceiptFailuresAreExplicit() {
  auto fixture = Base();
  const auto ack = SubmitExpected(
      *fixture, Kind::focus, "stewardship_wealth_focus");
  game::PlayerLifestyleSelectionActionReceiptV1 receipt{};

  fixture->receipt_state.native_revision = ack.pre_native_revision;
  fixture->receipt_state.public_revision = ack.pre_public_revision;
  fixture->receipt_state.proof_epoch = ack.pre_proof_epoch;
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*fixture), ack, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "no_new_paused_observation");

  ++fixture->receipt_state.native_revision;
  ++fixture->receipt_state.public_revision;
  ++fixture->receipt_state.proof_epoch;
  fixture->receipt_state.owned_perks_fully_materialized = false;
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*fixture), ack, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "complete_post_state_unavailable");

  fixture->receipt_state.owned_perks_fully_materialized = true;
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*fixture), ack, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "target_focus_change_not_observed");
  Require(receipt.current_focus_reread && receipt.owned_perks_reread &&
          receipt.experience_reread && receipt.perk_points_reread);

  auto perk_fixture = Base();
  const auto perk_ack = SubmitExpected(
      *perk_fixture, Kind::perk, "tax_man_perk");
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*perk_fixture), perk_ack, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "target_perk_change_not_observed");

  game::PlayerLifestyleSelectionActionAckV1 rejected{};
  rejected.status = AckStatus::rejected_before_submit;
  rejected.rejection_reason = "invalid_request";
  const auto captures_before = perk_fixture->receipt_captures;
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*perk_fixture), rejected, receipt) ==
          ReceiptStatus::rejected);
  Require(receipt.reason == "invalid_request");
  Require(perk_fixture->receipt_captures == captures_before);
}

void TestDistinctNativeFrameAndEpisodeAreRequired() {
  auto fixture = Base();
  const auto ack = SubmitExpected(
      *fixture, Kind::focus, "stewardship_wealth_focus");
  fixture->receipt_state.current_focus_key =
      Key("stewardship_wealth_focus");
  game::PlayerLifestyleSelectionActionReceiptV1 receipt{};

  Fixed(fixture->receipt_state.snapshot_id, kSnapshot);
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*fixture), ack, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "no_new_native_snapshot_frame");
  Fixed(fixture->receipt_state.snapshot_id, kPostSnapshot);
  Fixed(fixture->receipt_state.episode_run_id,
        "native-29829-other-campaign");
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*fixture), ack, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "post_episode_or_player_mismatch");
  Fixed(fixture->receipt_state.episode_run_id, kEpisode);
  Require(ck3::VerifyPlayerLifestyleSelectionActionReceiptV1(
              Access(*fixture), ack, receipt) == ReceiptStatus::applied);
  Require(fixture->submits == 1);
}

} // namespace

int main() {
  try {
    static_assert(
        ck3::kPlayerLifestyleSelectionActionExecutableSha256V1.size() == 64);
    Require(ck3::PlayerLifestyleSelectionActionFailureClassKeyV1(
                FailureClass::final_legality) == "final_legality");
    TestFocusAckIsPendingAndReceiptRereadsState();
    TestPerkSubmitAcceptsWindowIndependentPartialCollection();
    TestPerkReceiptRequiresNewOwnedMembership();
    TestOnlyFinalCanSelectTargetCanSubmit();
    TestIncompleteStateAndPreSubmitDriftNeverSubmit();
    TestCommandBindingAndSubmitAreFailClosedAndSingleShot();
    TestReceiptFailuresAreExplicit();
    TestDistinctNativeFrameAndEpisodeAreRequired();
    std::cout << "player_lifestyle_selection_action_v1_test: 8/8 GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
