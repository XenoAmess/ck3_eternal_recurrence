#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

using xar::ck3_11906::ZhongguoRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{41, 730'001, true, true,
                                       true, true, 100};
  bool main_thread = true;
  bool drift_frame = false;
  bool drift_rows = false;
  std::uint32_t captures = 0;
  std::uint32_t variable_reads = 0;
  std::unordered_set<std::int32_t> characters{100, 200};
  std::unordered_map<std::string, ZhongguoRawVariableV1> variables;
  std::vector<std::string> requested_keys;
};

ZhongguoRawVariableV1 Number(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoRawVariableV1 Character(std::int32_t value) {
  return {true, 4, value};
}

bool Capture(void *opaque, xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = fixture.frame;
  ++fixture.captures;
  if (fixture.drift_frame && fixture.captures > 1) {
    ++output.date_raw;
  }
  return true;
}

bool IsMain(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool ValidateCharacter(void *opaque, std::int32_t character_id) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  return fixture.characters.contains(character_id);
}

bool ReadVariable(void *opaque, std::int32_t character_id,
                  std::string_view key,
                  ZhongguoRawVariableV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (character_id != 200 ||
      std::find(xar::ck3_11906::
                    kZhongguoCaseSnapshotV1VariableAllowlist.begin(),
                xar::ck3_11906::
                    kZhongguoCaseSnapshotV1VariableAllowlist.end(),
                key) == xar::ck3_11906::
                            kZhongguoCaseSnapshotV1VariableAllowlist.end()) {
    return false;
  }
  try {
    fixture.requested_keys.emplace_back(key);
  } catch (...) {
    return false;
  }
  ++fixture.variable_reads;
  const auto found = fixture.variables.find(std::string(key));
  output = found == fixture.variables.end() ? ZhongguoRawVariableV1{}
                                             : found->second;
  if (fixture.drift_rows &&
      fixture.variable_reads >
          xar::ck3_11906::kZhongguoCaseSnapshotV1VariableAllowlist.size() &&
      key == "zg361_b1_case_revision") {
    output = Number(99);
  }
  return true;
}

xar::ck3_11906::ZhongguoCaseNativeEnvironmentV1 Environment() {
  xar::ck3_11906::ZhongguoCaseNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoCaseAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoCaseAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  return access;
}

xar::ck3_11906::ZhongguoCaseSnapshotRequestV1 Request(
    std::int32_t owner = 100) {
  xar::ck3_11906::ZhongguoCaseSnapshotRequestV1 request{};
  request.expected_snapshot_revision = 41;
  request.subject_character_id = 200;
  request.owner_character_id = owner;
  request.case_kind = xar::ck3_11906::kZhongguoCaseSnapshotV1CaseKind;
  request.request_nonce = "case-fixture:41";
  return request;
}

void PopulateCase(Fixture &fixture, std::int32_t owner = 100) {
  fixture.variables["zg361_b1_case_owner"] = Character(owner);
  fixture.variables["zg361_b1_case_subject"] = Character(200);
  fixture.variables["zg361_b1_cycle_serial"] = Number(7);
  fixture.variables["zg361_b1_case_serial"] = Number(19);
  fixture.variables["zg361_b1_case_state"] = Number(1);
  fixture.variables["zg361_b1_case_active"] = Number(1);
  fixture.variables["zg361_b1_case_revision"] = Number(2);
  fixture.variables["zg361_b1_case_timeline_serial"] = Number(3);
  fixture.variables["zg361_b1_case_feedback_revision"] = Number(4);
  fixture.variables["zg361_b1_case_last_operation"] = Number(39);
  fixture.variables["zg361_b1_case_last_choice"] = Number(1);
}

void PopulateReceipt(Fixture &fixture) {
  fixture.variables["zg361_b1_roster_lock_receipt_owner"] = Character(100);
  fixture.variables["zg361_b1_roster_lock_receipt_subject"] = Character(200);
  fixture.variables["zg361_b1_roster_lock_receipt_cycle"] = Number(7);
  fixture.variables["zg361_b1_roster_lock_receipt_case"] = Number(19);
  fixture.variables["zg361_b1_roster_lock_receipt_state"] = Number(1);
  fixture.variables["zg361_b1_roster_lock_receipt_choice"] = Number(1);
}

void PopulatePendingDeadline(Fixture &fixture) {
  fixture.variables["zg361_b1_pending_deadline_owner"] = Character(100);
  fixture.variables["zg361_b1_pending_deadline_subject"] = Character(200);
  fixture.variables["zg361_b1_pending_deadline_ticket_cycle"] = Number(7);
  fixture.variables["zg361_b1_pending_deadline_ticket_case"] = Number(19);
  fixture.variables["zg361_b1_pending_deadline_ticket_state"] = Number(7);
  fixture.variables["zg361_b1_pending_deadline_days"] = Number(30);
  fixture.variables["zg361_b1_pending_deadline_pending"] = Number(1);
  fixture.variables["zg361_b1_pending_deadline_expired"] = Number(0);
  // The exact-build kind/payload for a script-variable date is deliberately
  // not frozen. A present opaque value must remain typed unavailable.
  fixture.variables["zg361_b1_pending_open_date"] = {true, 9, 730'001};
}

bool AllUnavailable(const xar::game::ZhongguoCaseIdentityV1 &value) {
  return !value.owner_character_id.available &&
         !value.subject_character_id.available &&
         !value.cycle_serial.available && !value.case_serial.available &&
         !value.state.available && !value.active.available &&
         !value.revision.available && !value.timeline_serial.available &&
         !value.feedback_revision.available;
}

bool ReceiptAllUnavailable(const xar::game::ZhongguoCaseReceiptV1 &value) {
  return !value.key.available && !value.owner_character_id.available &&
         !value.subject_character_id.available &&
         !value.cycle_serial.available && !value.case_serial.available &&
         !value.state.available && !value.choice.available;
}

bool DeadlineAllUnavailable(const xar::game::ZhongguoCaseDeadlineV1 &value) {
  return !value.target_character_id.available &&
         !value.owner_character_id.available &&
         !value.cycle_serial.available && !value.case_serial.available &&
         !value.expected_state.available && !value.days.available &&
         !value.pending.available && !value.expired.available &&
         !value.open_date_raw.available && !value.due_date_raw.available &&
         !value.on_due_operation.available;
}

bool Read(Fixture &fixture, xar::game::ZhongguoCaseSnapshotV1 &output,
          xar::ck3_11906::ZhongguoCaseSnapshotRequestV1 request = Request()) {
  return xar::ck3_11906::ReadZhongguoCaseSnapshotV1(
             Environment(), Access(fixture), request, output) ==
         xar::game::ReadZhongguoCaseSnapshotResultV1::available;
}

bool TestHappyAndNotScheduled() {
  Fixture fixture;
  PopulateCase(fixture);
  PopulateReceipt(fixture);
  PopulatePendingDeadline(fixture);
  fixture.variables["zg361_b1_pending_deadline_days"] = Number(0);
  fixture.variables["zg361_b1_pending_deadline_pending"] = Number(0);
  fixture.variables["zg361_b1_pending_deadline_expired"] = Number(1);
  fixture.variables["zg361_b1_pending_deadline_ticket_cycle"] = Number(6);
  fixture.variables["zg361_b1_pending_deadline_ticket_case"] = Number(18);
  fixture.variables.erase("zg361_b1_pending_open_date");
  xar::game::ZhongguoCaseSnapshotV1 output{};
  if (!Read(fixture, output) ||
      output.status !=
          xar::game::ZhongguoCaseSnapshotStatusV1::available ||
      !output.readiness.ready || !output.readiness.player_binding_ready ||
      output.receipt.status !=
          xar::game::ZhongguoReceiptStatusV1::recorded ||
      output.deadline.status !=
          xar::game::ZhongguoDeadlineStatusV1::not_scheduled ||
      !output.readiness.deadline_identity_ready ||
      !output.readiness.deadline_due_date_ready ||
      fixture.variable_reads !=
          2 * xar::ck3_11906::
                  kZhongguoCaseSnapshotV1VariableAllowlist.size() ||
      std::find(fixture.requested_keys.begin(), fixture.requested_keys.end(),
                "zg361_b1_pending_deadline_due_date") !=
          fixture.requested_keys.end()) {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoCaseSnapshotV1(output);
  return json.find("\"status\":\"available\"") != std::string::npos &&
         json.find("\"case_kind\":\"zhongguo.b1.performance\"") !=
             std::string::npos &&
         json.find("\"open_date_raw\"") != std::string::npos &&
         json.find("\"deadline_due_date_ready\":true") !=
             std::string::npos;
}

bool TestPendingDateIsTypedUnavailable() {
  Fixture fixture;
  PopulateCase(fixture);
  PopulateReceipt(fixture);
  PopulatePendingDeadline(fixture);
  xar::game::ZhongguoCaseSnapshotV1 output{};
  if (!Read(fixture, output) ||
      output.deadline.status !=
          xar::game::ZhongguoDeadlineStatusV1::pending ||
      !output.readiness.deadline_identity_ready ||
      output.readiness.deadline_due_date_ready || output.readiness.ready ||
      output.deadline.open_date_raw.available ||
      output.deadline.open_date_raw.unavailable_reason !=
          "value_type_mismatch" ||
      output.deadline.due_date_raw.available ||
      output.deadline.due_date_raw.unavailable_reason !=
          "due_date_not_persisted_by_product") {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoCaseSnapshotV1(output);
  return !json.empty() &&
         json.find("due_date_not_persisted_by_product") !=
             std::string::npos;
}

bool TestExpiredDateIsTypedUnavailable() {
  Fixture fixture;
  PopulateCase(fixture);
  PopulateReceipt(fixture);
  PopulatePendingDeadline(fixture);
  fixture.variables["zg361_b1_pending_deadline_pending"] = Number(0);
  fixture.variables["zg361_b1_pending_deadline_expired"] = Number(1);
  xar::game::ZhongguoCaseSnapshotV1 output{};
  return Read(fixture, output) &&
         output.deadline.status ==
             xar::game::ZhongguoDeadlineStatusV1::expired &&
         output.readiness.deadline_identity_ready &&
         !output.readiness.deadline_due_date_ready &&
         !output.deadline.open_date_raw.available &&
         output.deadline.open_date_raw.unavailable_reason ==
             "value_type_mismatch" &&
         !output.deadline.due_date_raw.available &&
         output.deadline.due_date_raw.unavailable_reason ==
             "due_date_not_persisted_by_product" &&
         !xar::ck3_11906::SerializeZhongguoCaseSnapshotV1(output).empty();
}

bool TestPlayerAndOwnerBindingUnavailable() {
  Fixture ai_owned;
  ai_owned.characters.insert(300);
  PopulateCase(ai_owned, 300);
  PopulateReceipt(ai_owned);
  xar::game::ZhongguoCaseSnapshotV1 output{};
  if (Read(ai_owned, output, Request(300)) ||
      output.unavailable_reason != "player_binding_mismatch" ||
      !AllUnavailable(output.case_identity) ||
      xar::ck3_11906::SerializeZhongguoCaseSnapshotV1(output).empty()) {
    return false;
  }

  Fixture owner_filter;
  PopulateCase(owner_filter);
  PopulateReceipt(owner_filter);
  if (Read(owner_filter, output, Request(300)) ||
      output.unavailable_reason != "owner_filter_mismatch" ||
      !AllUnavailable(output.case_identity)) {
    return false;
  }
  return true;
}

bool TestMalformedGroupsAreWiped() {
  Fixture partial_case;
  PopulateCase(partial_case);
  PopulateReceipt(partial_case);
  partial_case.variables.erase("zg361_b1_case_revision");
  xar::game::ZhongguoCaseSnapshotV1 output{};
  if (Read(partial_case, output) ||
      output.unavailable_reason != "case_not_found" ||
      !AllUnavailable(output.case_identity)) {
    return false;
  }

  Fixture zero_revision;
  PopulateCase(zero_revision);
  PopulateReceipt(zero_revision);
  zero_revision.variables["zg361_b1_case_revision"] = Number(0);
  if (Read(zero_revision, output) ||
      output.unavailable_reason != "case_not_found" ||
      !AllUnavailable(output.case_identity)) {
    return false;
  }

  Fixture receipt;
  PopulateCase(receipt);
  PopulateReceipt(receipt);
  receipt.variables["zg361_b1_roster_lock_receipt_choice"] = Number(2);
  if (!Read(receipt, output) ||
      output.receipt.status !=
          xar::game::ZhongguoReceiptStatusV1::unavailable ||
      !ReceiptAllUnavailable(output.receipt) ||
      output.readiness.receipt_ready) {
    return false;
  }

  Fixture zero_receipt_state;
  PopulateCase(zero_receipt_state);
  PopulateReceipt(zero_receipt_state);
  zero_receipt_state.variables["zg361_b1_roster_lock_receipt_state"] =
      Number(0);
  if (!Read(zero_receipt_state, output) ||
      output.receipt.status !=
          xar::game::ZhongguoReceiptStatusV1::unavailable ||
      !ReceiptAllUnavailable(output.receipt) ||
      output.readiness.receipt_ready || output.readiness.operation_ready) {
    return false;
  }

  Fixture invalid_policy_choice;
  PopulateCase(invalid_policy_choice);
  PopulateReceipt(invalid_policy_choice);
  invalid_policy_choice.variables["zg361_b1_case_last_choice"] = Number(2);
  if (!Read(invalid_policy_choice, output) ||
      output.readiness.policy_ready || output.policy.policy_id.available ||
      !output.policy.choice.available || *output.policy.choice.value != 2 ||
      output.receipt.status !=
          xar::game::ZhongguoReceiptStatusV1::unavailable ||
      !ReceiptAllUnavailable(output.receipt) ||
      xar::ck3_11906::SerializeZhongguoCaseSnapshotV1(output).empty()) {
    return false;
  }

  Fixture deadline;
  PopulateCase(deadline);
  PopulateReceipt(deadline);
  PopulatePendingDeadline(deadline);
  deadline.variables["zg361_b1_pending_deadline_ticket_case"] = Number(20);
  if (!Read(deadline, output) ||
      output.deadline.status !=
          xar::game::ZhongguoDeadlineStatusV1::unavailable ||
      !DeadlineAllUnavailable(output.deadline) ||
      output.readiness.deadline_identity_ready) {
    return false;
  }
  return true;
}

bool TestNotRecordedAndDrift() {
  Fixture not_recorded;
  PopulateCase(not_recorded);
  PopulateReceipt(not_recorded);
  not_recorded.variables["zg361_b1_roster_lock_receipt_cycle"] = Number(6);
  not_recorded.variables["zg361_b1_roster_lock_receipt_case"] = Number(18);
  not_recorded.variables["zg361_b1_case_last_operation"] = Number(0);
  not_recorded.variables["zg361_b1_case_last_choice"] = Number(0);
  xar::game::ZhongguoCaseSnapshotV1 output{};
  if (!Read(not_recorded, output) ||
      output.receipt.status !=
          xar::game::ZhongguoReceiptStatusV1::not_recorded ||
      !ReceiptAllUnavailable(output.receipt) ||
      !output.readiness.receipt_ready) {
    return false;
  }

  Fixture drift;
  PopulateCase(drift);
  PopulateReceipt(drift);
  drift.drift_rows = true;
  if (Read(drift, output) || output.unavailable_reason != "state_changed" ||
      !AllUnavailable(output.case_identity)) {
    return false;
  }
  return true;
}

bool TestDirectCallAndInvalidEnvelope() {
  Fixture fixture;
  PopulateCase(fixture);
  PopulateReceipt(fixture);
  fixture.main_thread = false;
  xar::game::ZhongguoCaseSnapshotV1 output{};
  if (Read(fixture, output) ||
      output.unavailable_reason != "requires_application_main" ||
      !xar::ck3_11906::SerializeZhongguoCaseSnapshotV1(output).empty()) {
    return false;
  }
  fixture.main_thread = true;
  fixture.frame.paused = false;
  if (Read(fixture, output) || output.unavailable_reason != "requires_paused" ||
      !xar::ck3_11906::SerializeZhongguoCaseSnapshotV1(output).empty()) {
    return false;
  }
  return true;
}

} // namespace

int main() {
  const bool ok = TestHappyAndNotScheduled() &&
                  TestPendingDateIsTypedUnavailable() &&
                  TestExpiredDateIsTypedUnavailable() &&
                  TestPlayerAndOwnerBindingUnavailable() &&
                  TestMalformedGroupsAreWiped() &&
                  TestNotRecordedAndDrift() &&
                  TestDirectCallAndInvalidEnvelope();
  if (!ok) {
    std::cerr << "zhongguo case snapshot fixture failed\n";
    return 1;
  }
  return 0;
}
