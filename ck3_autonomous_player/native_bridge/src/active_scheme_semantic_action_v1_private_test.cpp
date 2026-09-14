#include "xar_bridge/active_scheme_semantic_action_v1_private.hpp"

#include <algorithm>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string>

namespace {

using AckStatus =
    xar::bridge::ActiveSchemeSemanticActionV1PrivateAckStatus;
using Failure = xar::bridge::ActiveSchemeSemanticActionV1PrivateFailure;
using PreviewStatus =
    xar::bridge::ActiveSchemeSemanticActionV1PrivatePreviewStatus;
using ReceiptStatus =
    xar::bridge::ActiveSchemeSemanticActionV1PrivateReceiptStatus;
using TargetKind = xar::bridge::ActiveSchemeStateV1PrivateTargetKind;

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error(
        "active scheme semantic action fixture failed at line " +
        std::to_string(location.line()));
  }
}

template <std::size_t Size>
void SetKey(std::array<char, Size> &target, std::string_view value) {
  target.fill('\0');
  Require(value.size() < target.size());
  std::copy(value.begin(), value.end(), target.begin());
}

struct Fixture {
  xar::bridge::ActiveSchemeStateV1PrivateObservation observation{};
  xar::bridge::ActiveSchemeSemanticActionV1PrivatePrecondition precondition{};
  xar::bridge::ActiveSchemeSemanticActionV1PrivateCommand submitted_command{};
  int observation_captures = 0;
  int precondition_captures = 0;
  int submits = 0;
  bool pre_submit_observation_drift = false;
  bool pre_submit_precondition_drift = false;
  bool submit_result = true;
  bool advance_epoch_on_submit = true;
  int matching_rows_on_submit = 1;
  std::int64_t submitted_row_target_delta = 0;

  Fixture() {
    observation.status =
        xar::bridge::ActiveSchemeStateV1PrivateStatus::available;
    observation.unavailable_reason =
        xar::bridge::ActiveSchemeStateV1PrivateFailure::none;
    observation.capture_epoch = 17;
    observation.date_raw = 53'175'816;
    observation.played_character_id = 0x0100002A;
    observation.container_generation = 71;

    precondition.available = true;
    precondition.paused = true;
    precondition.capture_epoch = observation.capture_epoch;
    precondition.date_raw = observation.date_raw;
    precondition.actor_character_id = observation.played_character_id;
    precondition.target_kind = TargetKind::character;
    precondition.target_id = 0x01000039;
    precondition.interaction_key = "sway_interaction";
    precondition.scheme_type_key = "sway";
    precondition.shown_evaluated = true;
    precondition.shown = true;
    precondition.validity_evaluated = true;
    precondition.valid = true;
    precondition.can_start_scheme_evaluated = true;
    precondition.can_start_scheme = true;
    precondition.success_chance.status =
        PreviewStatus::explicitly_unavailable;
    precondition.maximum_success_chance.status =
        PreviewStatus::explicitly_unavailable;
    precondition.secrecy.status = PreviewStatus::explicitly_unavailable;
  }

  void MakeMurder() {
    precondition.interaction_key = "start_murder_interaction";
    precondition.scheme_type_key = "murder";
    precondition.starter_options_evaluated = true;
    precondition.starter_options_exclusive = true;
    precondition.starter_option_count = 4;
    precondition.selected_starter_package = "agent_focus_secrecy";
    precondition.success_chance = {PreviewStatus::available, 63};
    precondition.maximum_success_chance = {PreviewStatus::available, 95};
    precondition.secrecy = {PreviewStatus::available, 72};
  }

  void AddMatchingRow(std::uint64_t instance_id,
                      std::uint32_t generation,
                      std::int64_t target_delta = 0) {
    Require(observation.row_count < observation.rows.size());
    auto &row = observation.rows[observation.row_count++];
    row.scheme_instance_id = instance_id;
    row.scheme_instance_generation = generation;
    row.owner_character_id = observation.played_character_id;
    SetKey(row.scheme_type_key, precondition.scheme_type_key);
    SetKey(row.category_key,
           precondition.scheme_type_key == "murder" ? "hostile" :
                                                       "personal");
    row.target_kind = precondition.target_kind;
    row.target_id = precondition.target_id + target_delta;
    row.is_basic = precondition.scheme_type_key == "sway";
    row.is_secret = precondition.scheme_type_key == "murder";
    row.progress = {xar::bridge::ActiveSchemeStateV1PrivateValueStatus::available,
                    0};
    row.progress_goal = {
        xar::bridge::ActiveSchemeStateV1PrivateValueStatus::available, 10};
  }
};

bool CaptureObservation(
    void *context,
    xar::bridge::ActiveSchemeStateV1PrivateObservation &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.observation;
  ++fixture.observation_captures;
  if (fixture.pre_submit_observation_drift &&
      fixture.observation_captures == 2) {
    ++output.container_generation;
  }
  return true;
}

bool CapturePrecondition(
    void *context,
    xar::bridge::ActiveSchemeSemanticActionV1PrivatePrecondition
        &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.precondition;
  ++fixture.precondition_captures;
  if (fixture.pre_submit_precondition_drift &&
      fixture.precondition_captures == 2) {
    output.shown = false;
  }
  return true;
}

bool Submit(
    void *context,
    const xar::bridge::ActiveSchemeSemanticActionV1PrivateCommand
        &command) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.submits;
  fixture.submitted_command = command;
  if (!fixture.submit_result) return false;
  if (fixture.advance_epoch_on_submit) {
    ++fixture.observation.capture_epoch;
    ++fixture.observation.container_generation;
    ++fixture.observation.date_raw;
  }
  for (int index = 0; index < fixture.matching_rows_on_submit; ++index) {
    fixture.AddMatchingRow(0x0000000200000042ULL +
                               static_cast<std::uint64_t>(index),
                           8 + static_cast<std::uint32_t>(index),
                           fixture.submitted_row_target_delta);
  }
  return true;
}

xar::bridge::ActiveSchemeSemanticActionV1PrivateAccess Access(
    Fixture &fixture) {
  return {&fixture, CaptureObservation, CapturePrecondition, Submit};
}

xar::bridge::ActiveSchemeSemanticActionV1PrivateEnvironment Environment() {
  return {0, true,
          xar::bridge::
              kActiveSchemeSemanticActionV1PrivateExecutableSha256,
          false, true};
}

xar::bridge::ActiveSchemeSemanticActionV1PrivateRequest Request(
    const Fixture &fixture) {
  return {"scheme-action-fixture-1",
          fixture.precondition.interaction_key,
          fixture.precondition.actor_character_id,
          fixture.precondition.target_kind,
          fixture.precondition.target_id,
          fixture.observation.capture_epoch,
          fixture.observation.container_generation,
          fixture.observation.date_raw,
          fixture.precondition.selected_starter_package};
}

xar::bridge::ActiveSchemeSemanticActionV1PrivateAck Execute(
    Fixture &fixture) {
  auto request = Request(fixture);
  xar::bridge::ActiveSchemeSemanticActionV1PrivateAck ack{};
  xar::bridge::ExecuteActiveSchemeSemanticActionV1Private(
      Environment(), Access(fixture), request, ack);
  return ack;
}

void TestSwaySingleSubmitAndFreshReceipt() {
  Fixture fixture;
  const auto ack = Execute(fixture);
  Require(ack.status == AckStatus::submitted_verification_pending);
  Require(ack.failure == Failure::none);
  Require(ack.submit_attempted && ack.submit_call_count == 1);
  Require(ack.verification_pending && fixture.submits == 1);
  Require(fixture.observation_captures == 2);
  Require(fixture.precondition_captures == 2);
  Require(fixture.submitted_command.interaction_key == "sway_interaction");
  Require(fixture.submitted_command.scheme_type_key == "sway");
  Require(fixture.submitted_command.selected_starter_package.empty());

  xar::bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
  Require(xar::bridge::VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
              Access(fixture), ack, receipt) == ReceiptStatus::applied);
  Require(receipt.failure == Failure::none);
  Require(receipt.postcondition_verified);
  Require(receipt.post_capture_epoch > ack.pre_capture_epoch);
  Require(receipt.scheme_instance_id == 0x0000000200000042ULL);
  Require(receipt.scheme_instance_generation == 8);
  Require(fixture.observation_captures == 3);
  Require(fixture.submits == 1);
}

void TestMurderPreconditionAndReceipt() {
  Fixture fixture;
  fixture.MakeMurder();
  const auto ack = Execute(fixture);
  Require(ack.status == AckStatus::submitted_verification_pending);
  Require(fixture.submits == 1);
  Require(fixture.submitted_command.interaction_key ==
          "start_murder_interaction");
  Require(fixture.submitted_command.scheme_type_key == "murder");
  Require(fixture.submitted_command.selected_starter_package ==
          "agent_focus_secrecy");
  xar::bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
  Require(xar::bridge::VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
              Access(fixture), ack, receipt) == ReceiptStatus::applied);
  Require(receipt.postcondition_verified);
  Require(fixture.submits == 1);
}

void TestTypedPreSubmitFailuresNeverSubmit() {
  {
    Fixture fixture;
    auto environment = Environment();
    environment.admitted_executable_sha256 = "wrong";
    auto request = Request(fixture);
    xar::bridge::ActiveSchemeSemanticActionV1PrivateAck ack{};
    xar::bridge::ExecuteActiveSchemeSemanticActionV1Private(
        environment, Access(fixture), request, ack);
    Require(ack.failure == Failure::exact_build_mismatch);
    Require(fixture.submits == 0);
  }
  {
    Fixture fixture;
    fixture.precondition.shown = false;
    const auto ack = Execute(fixture);
    Require(ack.failure == Failure::interaction_not_shown);
    Require(fixture.submits == 0);
  }
  {
    Fixture fixture;
    fixture.precondition.can_start_scheme = false;
    fixture.precondition.native_reason_key = "scheme_interaction_tt_warning";
    const auto ack = Execute(fixture);
    Require(ack.failure == Failure::can_start_scheme_denied);
    Require(ack.native_reason_key == "scheme_interaction_tt_warning");
    Require(fixture.submits == 0);
  }
  {
    Fixture fixture;
    fixture.MakeMurder();
    fixture.precondition.selected_starter_package = "not_a_package";
    const auto ack = Execute(fixture);
    Require(ack.failure == Failure::starter_package_invalid);
    Require(fixture.submits == 0);
  }
  {
    Fixture fixture;
    fixture.precondition.secrecy.status = PreviewStatus::unresolved;
    const auto ack = Execute(fixture);
    Require(ack.failure == Failure::preview_unresolved);
    Require(fixture.submits == 0);
  }
  {
    Fixture fixture;
    fixture.AddMatchingRow(0x0000000200000099ULL, 2);
    const auto ack = Execute(fixture);
    Require(ack.failure == Failure::matching_scheme_already_active);
    Require(fixture.submits == 0);
  }
  {
    Fixture fixture;
    fixture.pre_submit_observation_drift = true;
    const auto ack = Execute(fixture);
    Require(ack.failure == Failure::state_changed_before_submit);
    Require(fixture.submits == 0);
  }
  {
    Fixture fixture;
    fixture.pre_submit_precondition_drift = true;
    const auto ack = Execute(fixture);
    Require(ack.failure == Failure::state_changed_before_submit);
    Require(fixture.submits == 0);
  }
}

void TestSubmitRejectionIsTypedAndNotRetried() {
  Fixture fixture;
  fixture.submit_result = false;
  const auto ack = Execute(fixture);
  Require(ack.status == AckStatus::rejected_before_submit);
  Require(ack.failure == Failure::submit_rejected);
  Require(ack.submit_attempted && ack.submit_call_count == 1);
  Require(fixture.submits == 1);

  xar::bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
  Require(xar::bridge::VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
              Access(fixture), ack, receipt) == ReceiptStatus::rejected);
  Require(receipt.failure == Failure::submit_rejected);
  Require(fixture.submits == 1);
}

void TestAckNeverSubstitutesForFreshPostcondition() {
  Fixture fixture;
  fixture.advance_epoch_on_submit = false;
  fixture.matching_rows_on_submit = 0;
  const auto ack = Execute(fixture);
  Require(ack.status == AckStatus::submitted_verification_pending);
  xar::bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
  Require(xar::bridge::VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
              Access(fixture), ack, receipt) == ReceiptStatus::red);
  Require(receipt.failure == Failure::post_observation_not_fresh);
  Require(!receipt.postcondition_verified);
  Require(fixture.submits == 1);
}

void TestFreshPostconditionFailuresStayTypedRed() {
  {
    Fixture fixture;
    fixture.matching_rows_on_submit = 0;
    const auto ack = Execute(fixture);
    xar::bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
    Require(xar::bridge::VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
                Access(fixture), ack, receipt) == ReceiptStatus::red);
    Require(receipt.failure == Failure::postcondition_missing);
  }
  {
    Fixture fixture;
    fixture.submitted_row_target_delta = 1;
    const auto ack = Execute(fixture);
    xar::bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
    Require(xar::bridge::VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
                Access(fixture), ack, receipt) == ReceiptStatus::red);
    Require(receipt.failure == Failure::postcondition_missing);
  }
  {
    Fixture fixture;
    fixture.matching_rows_on_submit = 2;
    const auto ack = Execute(fixture);
    xar::bridge::ActiveSchemeSemanticActionV1PrivateReceipt receipt{};
    Require(xar::bridge::VerifyActiveSchemeSemanticActionReceiptV1PrivateFresh(
                Access(fixture), ack, receipt) == ReceiptStatus::red);
    Require(receipt.failure == Failure::postcondition_ambiguous);
  }
}

void TestFailureNamesRemainTyped() {
  Require(xar::bridge::ActiveSchemeSemanticActionV1PrivateFailureName(
              Failure::can_start_scheme_denied) ==
          "can_start_scheme_denied");
  Require(xar::bridge::ActiveSchemeSemanticActionV1PrivateFailureName(
              Failure::post_observation_not_fresh) ==
          "post_observation_not_fresh");
  Require(xar::bridge::ActiveSchemeSemanticActionV1PrivateFailureName(
              Failure::postcondition_ambiguous) ==
          "postcondition_ambiguous");
}

} // namespace

int main() {
  try {
    TestSwaySingleSubmitAndFreshReceipt();
    TestMurderPreconditionAndReceipt();
    TestTypedPreSubmitFailuresNeverSubmit();
    TestSubmitRejectionIsTypedAndNotRetried();
    TestAckNeverSubstitutesForFreshPostcondition();
    TestFreshPostconditionFailuresStayTypedRed();
    TestFailureNamesRemainTyped();
    std::cout << "active scheme semantic action private fixtures: GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
