#include "xar_bridge/steward_develop_county_action_v1.hpp"

#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string>

namespace {

using AckStatus = xar::game::StewardDevelopCountyActionAckStatusV1;
using FailureClass = xar::game::StewardDevelopCountyActionFailureClassV1;
using ReceiptStatus = xar::game::StewardDevelopCountyActionReceiptStatusV1;

void Require(
    bool condition,
    const std::source_location location = std::source_location::current()) {
  if (!condition) {
    throw std::runtime_error("steward develop county action fixture failed at line " +
                             std::to_string(location.line()));
  }
}

struct Fixture {
  xar::game::StewardDevelopCountyTaskObservationV1 observation;
  int captures = 0;
  int validations = 0;
  int submits = 0;
  bool native_valid = true;
  bool submit_result = true;
  bool drift = false;

  Fixture() {
    observation.available = true;
    observation.paused = true;
    observation.snapshot_revision = 17;
    observation.native_snapshot_revision = 71;
    observation.observed_date_raw = 53'175'816;
    observation.player_character_id = 0x0100002A;
    observation.steward_character_id = 0x02000011;
    observation.target_candidate_present = true;
    observation.target_county_title_id = 0x0300000A;
    observation.target_capital_province_id = 921;
    observation.target_native_legal = true;
    observation.has_active_task = true;
    observation.active_task_key = "task_collect_taxes";
    observation.active_task_type = "county";
    observation.active_target_county_title_id = 0x0300000B;
    observation.active_target_province_id = 922;
    observation.progress_available = true;
    observation.progress_kind = "value";
    observation.progress_current_raw = 1'000;
    observation.progress_max_raw = 10'000;
  }
};

bool Capture(void *context,
             xar::game::StewardDevelopCountyTaskObservationV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  output = fixture.observation;
  if (++fixture.captures == 2 && fixture.drift) {
    ++output.snapshot_revision;
  }
  return true;
}

bool Validate(void *context, std::int32_t, std::int32_t, bool &valid,
              std::string &native_reason_key) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.validations;
  valid = fixture.native_valid;
  if (!valid) native_reason_key = "COUNCIL_NOT_VALID_TASK";
  return true;
}

bool Submit(void *context, std::int32_t, std::int32_t) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  ++fixture.submits;
  return fixture.submit_result;
}

xar::game::StewardDevelopCountyActionRequestV1 Request() {
  return {"devact-fixture-1", 0x02000011, "task_develop_county",
          0x0300000A, 17, true};
}

xar::ck3_11906::StewardDevelopCountyActionAccessV1 Access(Fixture &fixture) {
  return {&fixture, Capture, Validate, Submit};
}

xar::ck3_11906::StewardDevelopCountyActionNativeEnvironmentV1
FixtureEnvironment() {
  return {0, true, false, true};
}

void TestProductionFailsClosedWithoutCommandAbi() {
  Fixture fixture;
  auto environment =
      xar::ck3_11906::BindStewardDevelopCountyActionNativeEnvironmentV1(
          0x140000000, true);
  xar::game::StewardDevelopCountyActionAckV1 ack;
  Require(xar::ck3_11906::ExecuteStewardDevelopCountyActionV1(
              environment, Access(fixture), Request(), ack) ==
          AckStatus::rejected_before_submit);
  Require(ack.failure_class == FailureClass::native_command_dispatch);
  Require(ack.rejection_reason == "native_command_abi_not_certified");
  Require(!ack.verification_pending && fixture.submits == 0);
}

void TestFiveFailureClasses() {
  using namespace xar::ck3_11906;
  {
    Fixture fixture;
    auto request = Request();
    request.task_key = "task_collect_taxes";
    xar::game::StewardDevelopCountyActionAckV1 ack;
    ExecuteStewardDevelopCountyActionV1(FixtureEnvironment(), Access(fixture),
                                        request, ack);
    Require(ack.failure_class == FailureClass::request_contract);
  }
  {
    Fixture fixture;
    auto request = Request();
    ++request.expected_revision;
    xar::game::StewardDevelopCountyActionAckV1 ack;
    ExecuteStewardDevelopCountyActionV1(FixtureEnvironment(), Access(fixture),
                                        request, ack);
    Require(ack.failure_class == FailureClass::snapshot_binding);
  }
  {
    Fixture fixture;
    auto request = Request();
    ++request.councillor_character_id;
    xar::game::StewardDevelopCountyActionAckV1 ack;
    ExecuteStewardDevelopCountyActionV1(FixtureEnvironment(), Access(fixture),
                                        request, ack);
    Require(ack.failure_class == FailureClass::councillor_binding);
  }
  {
    Fixture fixture;
    auto request = Request();
    request.replace_existing_task = false;
    xar::game::StewardDevelopCountyActionAckV1 ack;
    ExecuteStewardDevelopCountyActionV1(FixtureEnvironment(), Access(fixture),
                                        request, ack);
    Require(ack.failure_class == FailureClass::task_or_target_legality);
  }
  {
    Fixture fixture;
    auto environment = FixtureEnvironment();
    environment.offline_fixture_command = false;
    xar::game::StewardDevelopCountyActionAckV1 ack;
    ExecuteStewardDevelopCountyActionV1(environment, Access(fixture), Request(),
                                        ack);
    Require(ack.failure_class == FailureClass::native_command_dispatch);
  }
}

void TestNativeFailureAndDriftDoNotSubmit() {
  using namespace xar::ck3_11906;
  Fixture invalid;
  invalid.native_valid = false;
  xar::game::StewardDevelopCountyActionAckV1 ack;
  ExecuteStewardDevelopCountyActionV1(FixtureEnvironment(), Access(invalid),
                                      Request(), ack);
  Require(ack.failure_class == FailureClass::task_or_target_legality);
  Require(ack.rejection_reason == "native_validation_failed");
  Require(ack.native_reason_key == "COUNCIL_NOT_VALID_TASK");
  Require(invalid.submits == 0);

  Fixture drift;
  drift.drift = true;
  ExecuteStewardDevelopCountyActionV1(FixtureEnvironment(), Access(drift),
                                      Request(), ack);
  Require(ack.failure_class == FailureClass::snapshot_binding);
  Require(ack.rejection_reason == "state_changed_before_submit");
  Require(drift.submits == 0);
}

xar::game::StewardDevelopCountyActionAckV1 SubmittedAck(Fixture &fixture) {
  xar::game::StewardDevelopCountyActionAckV1 ack;
  Require(xar::ck3_11906::ExecuteStewardDevelopCountyActionV1(
              FixtureEnvironment(), Access(fixture), Request(), ack) ==
          AckStatus::submitted_verification_pending);
  Require(ack.verification_pending);
  Require(fixture.submits == 1);
  return ack;
}

void TestAckAndIndependentReceipt() {
  using namespace xar::ck3_11906;
  Fixture fixture;
  const auto ack = SubmittedAck(fixture);
  Require(ack.pre_snapshot_revision == 17);
  Require(ack.submitted_target_province_id == 921);
  const auto ack_json = SerializeStewardDevelopCountyActionAckV1(ack);
  Require(ack_json.find("submitted_verification_pending") !=
          std::string::npos);
  Require(ack_json.find("\"applied\"") == std::string::npos);
  Require(ack_json.find("\"success\"") == std::string::npos);

  auto post = fixture.observation;
  ++post.snapshot_revision;
  ++post.native_snapshot_revision;
  post.has_active_task = true;
  post.active_task_key = "task_develop_county";
  post.active_task_type = "county";
  post.active_target_county_title_id = Request().target_county_title_id;
  post.active_target_province_id = 921;
  post.progress_available = true;
  post.progress_kind = "value";
  xar::game::StewardDevelopCountyActionReceiptV1 receipt;
  Require(VerifyStewardDevelopCountyActionReceiptV1(ack, post, receipt) ==
          ReceiptStatus::applied);
  Require(receipt.postcondition_verified);
  Require(receipt.progress_current_raw == 1'000);

  auto stale = post;
  stale.snapshot_revision = ack.pre_snapshot_revision;
  Require(VerifyStewardDevelopCountyActionReceiptV1(ack, stale, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "no_new_paused_observation");

  auto wrong = post;
  wrong.active_target_province_id = 999;
  Require(VerifyStewardDevelopCountyActionReceiptV1(ack, wrong, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "wrong_task_or_target_observed");

  auto no_progress = post;
  no_progress.progress_available = false;
  Require(VerifyStewardDevelopCountyActionReceiptV1(
              ack, no_progress, receipt) ==
          ReceiptStatus::postcondition_failed);
  Require(receipt.reason == "progress_binding_unavailable");

  auto rejected_request = Request();
  rejected_request.task_key = "task_collect_taxes";
  xar::game::StewardDevelopCountyActionAckV1 rejected_ack;
  ExecuteStewardDevelopCountyActionV1(FixtureEnvironment(), Access(fixture),
                                      rejected_request, rejected_ack);
  Require(VerifyStewardDevelopCountyActionReceiptV1(
              rejected_ack, post, receipt) == ReceiptStatus::rejected);
  Require(receipt.post_snapshot_revision == 0);
  Require(receipt.councillor_character_id == -1);
  Require(!receipt.target_county_title_id.has_value());
}

} // namespace

int main() {
  try {
    using namespace xar::ck3_11906;
    static_assert(kStewardDevelopCountyActionV1ExecutableSha256.size() == 64);
    Require(StewardDevelopCountyActionFailureClassKeyV1(
                FailureClass::task_or_target_legality) ==
            "task_or_target_legality");
    TestProductionFailsClosedWithoutCommandAbi();
    TestFiveFailureClasses();
    TestNativeFailureAndDriftDoNotSubmit();
    TestAckAndIndependentReceipt();
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
