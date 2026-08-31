#include "xar_bridge/zhongguo_ai_owned_case_snapshot_v1.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <unordered_map>
#include <unordered_set>

namespace {

using xar::ck3_11906::ZhongguoAiOwnerEligibilityObservationV1;
using xar::ck3_11906::ZhongguoRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{41, 53147016, true, true, true,
                                       true, 100};
  std::unordered_set<std::int32_t> characters{100, 200, 300};
  std::unordered_map<std::string, ZhongguoRawVariableV1> variables;
  ZhongguoAiOwnerEligibilityObservationV1 eligibility{
      300, true, true, 900, 3, "duchy", "celestial_government", 300};
  std::size_t variable_reads = 0;
  std::size_t eligibility_reads = 0;
  bool drift_rows = false;
  bool drift_eligibility = false;
  bool main_thread = true;
};

ZhongguoRawVariableV1 Number(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoRawVariableV1 Character(std::int32_t value) {
  return {true, 4, value};
}

bool CaptureFrame(void *context,
                  xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}

bool IsMainThread(void *context) noexcept {
  return static_cast<Fixture *>(context)->main_thread;
}

bool ValidateCharacter(void *context, std::int32_t value) noexcept {
  return static_cast<Fixture *>(context)->characters.contains(value);
}

bool ReadVariable(void *context, std::int32_t subject,
                  std::string_view key,
                  ZhongguoRawVariableV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (subject != 200) return false;
  ++fixture.variable_reads;
  const auto found = fixture.variables.find(std::string(key));
  output = found == fixture.variables.end() ? ZhongguoRawVariableV1{}
                                             : found->second;
  if (fixture.drift_rows &&
      fixture.variable_reads >
          xar::ck3_11906::
              kZhongguoAiOwnedCaseSnapshotV1VariableAllowlist.size() &&
      key == "zg361_b1_case_revision") {
    output = Number(9);
  }
  return true;
}

bool ObserveEligibility(
    void *context, std::int32_t owner, std::int32_t subject,
    ZhongguoAiOwnerEligibilityObservationV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (owner != 300 || subject != 200) return false;
  ++fixture.eligibility_reads;
  output = fixture.eligibility;
  if (fixture.drift_eligibility && fixture.eligibility_reads > 1) {
    output.primary_title_tier_raw = 4;
    output.primary_title_tier_key = "kingdom";
  }
  return true;
}

xar::ck3_11906::ZhongguoAiOwnedCaseNativeEnvironmentV1 Environment() {
  xar::ck3_11906::ZhongguoAiOwnedCaseNativeEnvironmentV1 environment{};
  environment.variables.exact_build_admitted = true;
  environment.variables.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoAiOwnedCaseAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoAiOwnedCaseAccessV1 access{};
  access.variables.context = &fixture;
  access.variables.capture_frame = &CaptureFrame;
  access.variables.is_main_thread = &IsMainThread;
  access.variables.validate_character = &ValidateCharacter;
  access.variables.read_allowlisted_variable = &ReadVariable;
  access.observe_owner_eligibility = &ObserveEligibility;
  return access;
}

xar::ck3_11906::ZhongguoAiOwnedCaseSnapshotRequestV1 Request(
    std::int32_t owner = 300) {
  return {41, owner, 200, "ai-case-fixture:41"};
}

void PopulateCase(Fixture &fixture, std::int64_t state = 7,
                  std::int64_t active = 1) {
  fixture.variables["zg361_b1_case_owner"] = Character(300);
  fixture.variables["zg361_b1_case_subject"] = Character(200);
  fixture.variables["zg361_b1_cycle_serial"] = Number(7);
  fixture.variables["zg361_b1_case_serial"] = Number(19);
  fixture.variables["zg361_b1_case_state"] = Number(state);
  fixture.variables["zg361_b1_case_active"] = Number(active);
  fixture.variables["zg361_b1_case_revision"] = Number(2);
  fixture.variables["zg361_b1_case_timeline_serial"] = Number(3);
  fixture.variables["zg361_b1_case_feedback_revision"] = Number(4);
  fixture.variables["zg361_b1_case_last_operation"] = Number(39);
  fixture.variables["zg361_b1_case_last_choice"] = Number(1);
}

void PopulateReceipt(Fixture &fixture) {
  fixture.variables["zg361_b1_roster_lock_receipt_owner"] = Character(300);
  fixture.variables["zg361_b1_roster_lock_receipt_subject"] = Character(200);
  fixture.variables["zg361_b1_roster_lock_receipt_cycle"] = Number(7);
  fixture.variables["zg361_b1_roster_lock_receipt_case"] = Number(19);
  fixture.variables["zg361_b1_roster_lock_receipt_state"] = Number(7);
  fixture.variables["zg361_b1_roster_lock_receipt_choice"] = Number(1);
}

bool Read(Fixture &fixture,
          xar::game::ZhongguoAiOwnedCaseSnapshotV1 &output,
          xar::ck3_11906::ZhongguoAiOwnedCaseSnapshotRequestV1 request =
              Request()) {
  return xar::ck3_11906::ReadZhongguoAiOwnedCaseSnapshotV1(
             Environment(), Access(fixture), request, output) ==
         xar::game::ReadZhongguoAiOwnedCaseSnapshotResultV1::available;
}

bool TestAuthorizedAiDukeAndRecordedReceipt() {
  Fixture fixture;
  PopulateCase(fixture);
  PopulateReceipt(fixture);
  xar::game::ZhongguoAiOwnedCaseSnapshotV1 output{};
  if (!Read(fixture, output) || !output.readiness.ready ||
      output.status !=
          xar::game::ZhongguoAiOwnedCaseSnapshotStatusV1::available ||
      !output.owner_eligibility.authorized.available ||
      !*output.owner_eligibility.authorized.value ||
      !output.stage.key.available ||
      *output.stage.key.value != "calibration_open" ||
      !output.route.kind.available ||
      *output.route.kind.value != "authorized_ai_background" ||
      !output.route.visible_event_allowed.available ||
      *output.route.visible_event_allowed.value ||
      output.receipt.status != xar::game::ZhongguoReceiptStatusV1::recorded ||
      fixture.variable_reads !=
          2 * xar::ck3_11906::
                  kZhongguoAiOwnedCaseSnapshotV1VariableAllowlist.size() ||
      fixture.eligibility_reads != 2) {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoAiOwnedCaseSnapshotV1(output);
  return json.find("\"status\":\"available\"") != std::string::npos &&
         json.find("\"government_key\":{\"status\":\"available\",\"value\":\"celestial_government\"") !=
             std::string::npos &&
         json.find("\"primary_title_rva\":\"0x25F3350\"") !=
             std::string::npos;
}

bool TestHegemonyAndNotRecordedAreReady() {
  Fixture fixture;
  fixture.eligibility.primary_title_id = 901;
  fixture.eligibility.primary_title_tier_raw = 6;
  fixture.eligibility.primary_title_tier_key = "hegemony";
  PopulateCase(fixture, 8, 0);
  fixture.variables["zg361_b1_case_last_operation"] = Number(0);
  fixture.variables["zg361_b1_case_last_choice"] = Number(0);
  PopulateReceipt(fixture); // stale tuple must not fabricate a receipt.
  xar::game::ZhongguoAiOwnedCaseSnapshotV1 output{};
  return Read(fixture, output) && output.readiness.ready &&
         output.stage.key.available &&
         *output.stage.key.value == "published" &&
         output.receipt.status ==
             xar::game::ZhongguoReceiptStatusV1::not_recorded &&
         !output.receipt.owner_character_id.available &&
         !xar::ck3_11906::SerializeZhongguoAiOwnedCaseSnapshotV1(output)
              .empty();
}

bool TestPlayerOwnerRejectedBeforeVariableRead() {
  Fixture fixture;
  PopulateCase(fixture);
  PopulateReceipt(fixture);
  xar::game::ZhongguoAiOwnedCaseSnapshotV1 output{};
  return !Read(fixture, output, Request(100)) &&
         output.unavailable_reason == "owner_is_played_character" &&
         fixture.variable_reads == 0 && fixture.eligibility_reads == 0 &&
         !xar::ck3_11906::SerializeZhongguoAiOwnedCaseSnapshotV1(output)
              .empty();
}

bool RejectedWith(Fixture fixture, std::string_view expected) {
  PopulateCase(fixture);
  PopulateReceipt(fixture);
  xar::game::ZhongguoAiOwnedCaseSnapshotV1 output{};
  return !Read(fixture, output) && output.unavailable_reason == expected &&
         fixture.variable_reads == 0 && fixture.eligibility_reads == 1 &&
         !xar::ck3_11906::SerializeZhongguoAiOwnedCaseSnapshotV1(output)
              .empty();
}

bool TestEligibilityRejectionMatrix() {
  Fixture dead;
  dead.eligibility.owner_alive = false;
  if (!RejectedWith(dead, "owner_not_alive")) return false;
  Fixture human;
  human.eligibility.owner_is_ai = false;
  if (!RejectedWith(human, "owner_not_ai")) return false;
  Fixture wrong_government;
  wrong_government.eligibility.government_key = "feudal_government";
  if (!RejectedWith(wrong_government, "owner_not_celestial")) return false;
  Fixture count;
  count.eligibility.primary_title_tier_raw = 2;
  count.eligibility.primary_title_tier_key = "county";
  if (!RejectedWith(count, "owner_not_landed_duke_plus")) return false;
  Fixture other_liege;
  other_liege.characters.insert(301);
  other_liege.eligibility.subject_immediate_liege_character_id = 301;
  return RejectedWith(other_liege, "subject_not_direct_subject");
}

bool TestClosedStageMatrix() {
  constexpr std::string_view stage_keys[] = {
      "targets_open", "midcycle_open", "evidence_open", "facts_frozen",
      "shadow_open", "quota_ready", "calibration_open", "published",
  };
  for (std::int64_t state = 1; state <= 8; ++state) {
    Fixture fixture;
    PopulateCase(fixture, state, state == 8 ? 0 : 1);
    fixture.variables["zg361_b1_case_last_operation"] = Number(0);
    fixture.variables["zg361_b1_case_last_choice"] = Number(0);
    xar::game::ZhongguoAiOwnedCaseSnapshotV1 output{};
    if (!Read(fixture, output) || !output.readiness.ready ||
        !output.stage.state.available ||
        *output.stage.state.value != state || !output.stage.key.available ||
        *output.stage.key.value != stage_keys[state - 1] ||
        !output.stage.active.available ||
        *output.stage.active.value != (state != 8)) {
      return false;
    }
  }
  return true;
}

bool TestMalformedAndDrift() {
  Fixture inconsistent_stage;
  PopulateCase(inconsistent_stage, 8, 1);
  PopulateReceipt(inconsistent_stage);
  xar::game::ZhongguoAiOwnedCaseSnapshotV1 output{};
  if (!Read(inconsistent_stage, output) || output.readiness.stage_ready ||
      output.readiness.ready || output.stage.key.available ||
      xar::ck3_11906::SerializeZhongguoAiOwnedCaseSnapshotV1(output).empty()) {
    return false;
  }

  Fixture row_drift;
  PopulateCase(row_drift);
  PopulateReceipt(row_drift);
  row_drift.drift_rows = true;
  if (Read(row_drift, output) || output.unavailable_reason != "state_changed") {
    return false;
  }

  Fixture eligibility_drift;
  PopulateCase(eligibility_drift);
  PopulateReceipt(eligibility_drift);
  eligibility_drift.drift_eligibility = true;
  return !Read(eligibility_drift, output) &&
         output.unavailable_reason == "state_changed";
}

bool TestRequiresApplicationMain() {
  Fixture fixture;
  PopulateCase(fixture);
  fixture.main_thread = false;
  xar::game::ZhongguoAiOwnedCaseSnapshotV1 output{};
  return !Read(fixture, output) &&
         output.unavailable_reason == "requires_application_main";
}

} // namespace

int main() {
  const bool ok = TestAuthorizedAiDukeAndRecordedReceipt() &&
                  TestHegemonyAndNotRecordedAreReady() &&
                  TestPlayerOwnerRejectedBeforeVariableRead() &&
                  TestEligibilityRejectionMatrix() &&
                  TestClosedStageMatrix() &&
                  TestMalformedAndDrift() &&
                  TestRequiresApplicationMain();
  if (!ok) {
    std::cerr << "zhongguo AI-owned case snapshot fixture failed\n";
    return 1;
  }
  return 0;
}
