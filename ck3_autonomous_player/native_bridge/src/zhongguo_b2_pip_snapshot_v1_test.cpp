#include "xar_bridge/zhongguo_b2_pip_snapshot_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>

namespace {

using xar::ck3_11906::ZhongguoB2PipRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{91, 730'301, true, true,
                                       true, true, 100};
  bool main_thread = true;
  std::unordered_set<std::int32_t> characters{100, 200, 300};
  std::unordered_map<std::string, ZhongguoB2PipRawVariableV1> variables;
  std::size_t reads = 0;
  std::size_t captures = 0;
  bool drift_frame = false;
  bool drift_subject_rows = false;
  bool drift_owner_rows = false;
};

ZhongguoB2PipRawVariableV1 Number(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoB2PipRawVariableV1 Q100000(std::int64_t value) {
  return {true, 1, value};
}

ZhongguoB2PipRawVariableV1 Character(std::int32_t value) {
  return {true, 4, value};
}

std::string Key(std::int32_t character_id, std::string_view name) {
  return std::to_string(character_id) + ":" + std::string(name);
}

bool Capture(void *opaque, xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.captures;
  output = fixture.frame;
  if (fixture.drift_frame && fixture.captures > 1) ++output.date_raw;
  return true;
}

bool IsMain(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool ValidateCharacter(void *opaque, std::int32_t character_id) noexcept {
  return static_cast<Fixture *>(opaque)->characters.contains(character_id);
}

bool ReadVariable(void *opaque, std::int32_t character_id,
                  std::string_view key,
                  ZhongguoB2PipRawVariableV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto &subject =
      xar::ck3_11906::kZhongguoB2PipSubjectVariableAllowlist;
  const auto &owner =
      xar::ck3_11906::kZhongguoB2PipOwnerVariableAllowlist;
  const bool subject_read =
      character_id == fixture.frame.played_character_id &&
      std::find(subject.begin(), subject.end(), key) != subject.end();
  const bool owner_read = character_id == 200 &&
                          std::find(owner.begin(), owner.end(), key) !=
                              owner.end();
  if (!subject_read && !owner_read) return false;
  ++fixture.reads;
  const auto found = fixture.variables.find(Key(character_id, key));
  output = found == fixture.variables.end()
               ? ZhongguoB2PipRawVariableV1{}
               : found->second;
  if (subject_read && fixture.drift_subject_rows &&
      fixture.reads > subject.size() + owner.size() &&
      key == "zg361_b2_pip_state") {
    output = Number(2);
  }
  if (owner_read && fixture.drift_owner_rows &&
      fixture.reads > 2 * subject.size() + owner.size() &&
      key == "zg361_b2_pip_capacity_used") {
    output = Number(2);
  }
  return true;
}

xar::ck3_11906::ZhongguoB2PipNativeEnvironmentV1 Environment() {
  xar::ck3_11906::ZhongguoB2PipNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoB2PipAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoB2PipAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  return access;
}

xar::ck3_11906::ZhongguoB2PipSnapshotRequestV1 Request(
    std::int32_t owner = 200) {
  return {91, owner, "b2-pip:91"};
}

void Set(Fixture &fixture, std::string_view name,
         ZhongguoB2PipRawVariableV1 value,
         std::int32_t character_id = 100) {
  fixture.variables[Key(character_id, name)] = value;
}

void PopulateGate(Fixture &fixture, std::int64_t count = 3,
                  std::int64_t status = 1) {
  Set(fixture, "zg361_b2_pip_gate_owner", Character(200));
  Set(fixture, "zg361_b2_pip_gate_subject", Character(100));
  Set(fixture, "zg361_b2_pip_gate_cycle", Number(7));
  Set(fixture, "zg361_b2_pip_gate_case", Number(903));
  Set(fixture, "zg361_b2_pip_gate_threshold", Number(3));
  Set(fixture, "zg361_b2_pip_gate_component_count", Number(count));
  Set(fixture, "zg361_b2_pip_gate_evidence_complete", Number(1));
  Set(fixture, "zg361_b2_pip_gate_status", Number(status));
  Set(fixture, "zg361_result_case_serial", Number(903));
  Set(fixture, "zg361_result_grade", Number(1));
  Set(fixture, "zg361_result_absolute_grade", Number(count ? 1 : 2));
  Set(fixture, "zg361_result_kpi_frozen", Q100000(count ? -1 : 1));
  Set(fixture, "zg361_result_evidence_governance", Q100000(count ? -1 : 1));
  Set(fixture, "zg361_result_evidence_capability", Q100000(1));
  Set(fixture, "zg361_result_evidence_growth", Q100000(1));
  Set(fixture, "zg361_result_evidence_superior", Q100000(1));
  Set(fixture, "zg361_result_evidence_values", Q100000(1));
  Set(fixture, "zg361_result_evidence_collaboration", Q100000(1));
  Set(fixture, "zg361_result_evidence_jingcha", Q100000(1));
  Set(fixture, "zg361_result_evidence_organization", Q100000(1));
  Set(fixture, "zg361_result_treasury_paid", Number(50));
  Set(fixture, "zg361_result_gold_paid", Number(25));
}

void PopulatePending(Fixture &fixture) {
  PopulateGate(fixture);
  Set(fixture, "zg361_b2_pip_owner", Character(200));
  Set(fixture, "zg361_b2_pip_subject", Character(100));
  Set(fixture, "zg361_b2_pip_cycle", Number(7));
  Set(fixture, "zg361_b2_pip_case", Number(903));
  Set(fixture, "zg361_b2_pip_state", Number(1));
  Set(fixture, "zg361_b2_pip_task_kind", Number(2));
  Set(fixture, "zg361_b2_pip_task_controllable", Number(1));
  Set(fixture, "zg361_b2_pip_policy_route", Number(1));
  Set(fixture, "zg361_b2_m015_receipt_serial", Number(903));
  Set(fixture, "zg361_b2_pip_subject_response", Number(0));
  Set(fixture, "zg361_b2_pip_subject_response_case", Number(0));
  Set(fixture, "zg361_b2_pip_goal_revision_used", Number(0));
  Set(fixture, "zg361_b2_pip_refusal_receipt", Number(0));
  Set(fixture, "zg361_b2_pip_support_reserved", Number(0));
  Set(fixture, "zg361_b2_pip_support_absent", Number(0));
  Set(fixture, "zg361_b2_pip_support_budget_allocated", Number(0));
  Set(fixture, "zg361_b2_pip_support_budget_spent", Number(0));
}

void PopulateAccepted(Fixture &fixture) {
  PopulatePending(fixture);
  Set(fixture, "zg361_b2_pip_state", Number(2));
  Set(fixture, "zg361_b2_pip_subject_response", Number(1));
  Set(fixture, "zg361_b2_pip_subject_response_case", Number(903));
  Set(fixture, "zg361_b2_pip_subject_response_author", Character(100));
  Set(fixture, "zg361_b2_pip_support_reserved", Number(1));
  Set(fixture, "zg361_b2_pip_support_absent", Number(0));
  Set(fixture, "zg361_b2_pip_support_hours", Number(12));
  Set(fixture, "zg361_b2_pip_support_attention", Number(1));
  Set(fixture, "zg361_b2_pip_support_mentor", Character(300));
  Set(fixture, "zg361_b2_pip_support_budget_owner", Character(200));
  Set(fixture, "zg361_b2_pip_support_budget_allocated", Number(25));
  Set(fixture, "zg361_b2_pip_support_budget_spent", Number(25));
  Set(fixture, "zg361_b2_m016_receipt_serial", Number(903));
  Set(fixture, "zg361_b2_pip_capacity_used", Number(1), 200);
}

void PopulateTerminal(Fixture &fixture, bool graduated) {
  PopulateAccepted(fixture);
  Set(fixture, "zg361_b2_pip_state", Number(graduated ? 3 : 4));
  Set(fixture, "zg361_b2_pip_support_reserved", Number(0));
  Set(fixture, "zg361_b2_pip_support_released", Number(1));
  Set(fixture, "zg361_b2_pip_capacity_used", Number(0), 200);
  Set(fixture, "zg361_b2_pip_midpoint_receipt", Number(903));
  Set(fixture, "zg361_b2_pip_midpoint_resource_delivery_valid", Number(1));
  Set(fixture, "zg361_b2_pip_midpoint_progress_status", Number(0));
  Set(fixture, "zg361_b2_pip_midpoint_progress_red_code", Number(1));
  Set(fixture, "zg361_b2_pip_midpoint_state", Number(2));
  Set(fixture, "zg361_b2_pip_outcome_code", Number(graduated ? 1 : 2));
  Set(fixture, "zg361_b2_pip_settlement_receipt", Number(903));
  Set(fixture, "zg361_b2_pip_outcome_result_cycle", Number(8));
  Set(fixture, "zg361_b2_pip_outcome_result_case", Number(904));
  Set(fixture, "zg361_b2_pip_outcome_result_grade", Number(2));
  Set(fixture, "zg361_b2_pip_stability_days_observed", Number(365));
  Set(fixture, "zg361_b2_pip_independent_review_status", Number(0));
  Set(fixture, "zg361_b2_pip_independent_review_red_code", Number(2));
  Set(fixture, "zg361_b2_pip_graduation_receipt",
      Number(graduated ? 903 : 0));
  Set(fixture, "zg361_b2_pip_failure_receipt",
      Number(graduated ? 0 : 903));
  Set(fixture, "zg361_b2_pip_performance_evidence_status", Number(1));
  Set(fixture, "zg361_b2_pip_performance_evidence_owner", Character(200));
  Set(fixture, "zg361_b2_pip_performance_evidence_subject", Character(100));
  Set(fixture, "zg361_b2_pip_performance_evidence_source_cycle", Number(7));
  Set(fixture, "zg361_b2_pip_performance_evidence_source_case", Number(903));
  Set(fixture, "zg361_b2_pip_performance_evidence_due_cycle", Number(8));
  Set(fixture, "zg361_b2_pip_performance_evidence_delta",
      Number(graduated ? 10 : -10));
}

void PopulateRefused(Fixture &fixture) {
  PopulatePending(fixture);
  Set(fixture, "zg361_b2_pip_state", Number(5));
  Set(fixture, "zg361_b2_pip_subject_response", Number(3));
  Set(fixture, "zg361_b2_pip_subject_response_case", Number(903));
  Set(fixture, "zg361_b2_pip_subject_response_author", Character(100));
  Set(fixture, "zg361_b2_pip_refusal_receipt", Number(903));
  Set(fixture, "zg361_b2_pip_performance_evidence_status", Number(1));
  Set(fixture, "zg361_b2_pip_performance_evidence_owner", Character(200));
  Set(fixture, "zg361_b2_pip_performance_evidence_subject", Character(100));
  Set(fixture, "zg361_b2_pip_performance_evidence_source_cycle", Number(7));
  Set(fixture, "zg361_b2_pip_performance_evidence_source_case", Number(903));
  Set(fixture, "zg361_b2_pip_performance_evidence_due_cycle", Number(8));
  Set(fixture, "zg361_b2_pip_performance_evidence_delta", Number(-15));
}

bool Read(Fixture &fixture, xar::game::ZhongguoB2PipSnapshotV1 &output,
          xar::ck3_11906::ZhongguoB2PipSnapshotRequestV1 request =
              Request()) {
  return xar::ck3_11906::ReadZhongguoB2PipSnapshotV1(
             Environment(), Access(fixture), request, output) ==
         xar::game::ReadZhongguoB2PipSnapshotResultV1::available;
}

bool TestPendingAndAllowlist() {
  Fixture fixture;
  PopulatePending(fixture);
  xar::game::ZhongguoB2PipSnapshotV1 output{};
  if (!Read(fixture, output) || !output.readiness.ready ||
      !output.readiness.gate_evidence_ready ||
      !output.readiness.pip_identity_ready ||
      !output.readiness.response_ready || output.readiness.support_ready ||
      !output.readiness.budget_ledger_ready ||
      *output.budget_ledger.treasury_penalty_paid.value != 50 ||
      *output.budget_ledger.personal_gold_penalty_paid.value != 25 ||
      fixture.reads !=
          2 * (xar::ck3_11906::
                   kZhongguoB2PipSubjectVariableAllowlist.size() +
               xar::ck3_11906::
                   kZhongguoB2PipOwnerVariableAllowlist.size())) {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoB2PipSnapshotV1(output);
  return json.find("\"case_kind\":\"zhongguo.b2.pip\"") !=
             std::string::npos &&
         json.find("\"due_date_raw\":{\"status\":\"unavailable\","
                   "\"value\":null,\"unavailable_reason\":"
                   "\"product_not_persisted\"") != std::string::npos &&
         json.find("\"pip_modifier_present\":{\"status\":"
                   "\"unavailable\"") != std::string::npos;
}

bool TestAcceptedSupportAndOwnerScope() {
  Fixture fixture;
  PopulateAccepted(fixture);
  xar::game::ZhongguoB2PipSnapshotV1 output{};
  return Read(fixture, output) && output.readiness.response_ready &&
         output.readiness.support_ready &&
         *output.support.owner_capacity_used.value == 1 &&
         *output.support.mentor_character_id.value == 300 &&
         *output.support.treasury_budget_spent.value == 25;
}

bool TestStaleSupportFlagsRejectPackageReadiness() {
  Fixture fixture;
  PopulateAccepted(fixture);
  Set(fixture, "zg361_b2_pip_support_released", Number(1));
  xar::game::ZhongguoB2PipSnapshotV1 output{};
  return Read(fixture, output) && !output.readiness.support_ready;
}

bool TestGateOnlyAndBindingFailures() {
  Fixture gate_only;
  PopulateGate(gate_only, 0, 2);
  xar::game::ZhongguoB2PipSnapshotV1 output{};
  if (!Read(gate_only, output) || !output.readiness.ready ||
      output.readiness.pip_identity_ready ||
      !output.readiness.gate_evidence_ready) {
    return false;
  }
  Fixture wrong_owner;
  PopulatePending(wrong_owner);
  if (Read(wrong_owner, output, Request(201)) ||
      output.unavailable_reason != "owner_filter_mismatch") {
    return false;
  }
  Fixture self_bound;
  PopulatePending(self_bound);
  Set(self_bound, "zg361_b2_pip_gate_owner", Character(100));
  Set(self_bound, "zg361_b2_pip_owner", Character(100));
  if (Read(self_bound, output, Request(100)) ||
      output.unavailable_reason != "not_received_self") {
    return false;
  }
  Fixture cross_case;
  PopulatePending(cross_case);
  Set(cross_case, "zg361_b2_pip_case", Number(904));
  if (Read(cross_case, output) ||
      output.unavailable_reason != "case_inconsistent") {
    return false;
  }
  Fixture partial_pip;
  PopulateGate(partial_pip);
  Set(partial_pip, "zg361_b2_pip_task_kind", Number(2));
  if (Read(partial_pip, output) ||
      output.unavailable_reason != "case_inconsistent") {
    return false;
  }
  Fixture mismatched_result;
  PopulatePending(mismatched_result);
  Set(mismatched_result, "zg361_result_case_serial", Number(904));
  if (!Read(mismatched_result, output) ||
      output.readiness.gate_evidence_ready ||
      output.readiness.budget_ledger_ready ||
      output.gate.result_grade.unavailable_reason !=
          "case_binding_mismatch") {
    return false;
  }
  Fixture absent;
  return !Read(absent, output) &&
         output.unavailable_reason == "case_not_found";
}

bool TestTerminalRefusalAndConsumedEvidence() {
  xar::game::ZhongguoB2PipSnapshotV1 output{};
  Fixture graduated;
  PopulateTerminal(graduated, true);
  if (!Read(graduated, output) || !output.readiness.midpoint_ready ||
      !output.readiness.outcome_ready ||
      !output.readiness.next_cycle_evidence_ready ||
      *output.outcome.graduation_receipt_serial.value != 903 ||
      *output.next_cycle_evidence.delta.value != 10) {
    return false;
  }

  Fixture failed;
  PopulateTerminal(failed, false);
  if (!Read(failed, output) || !output.readiness.outcome_ready ||
      *output.outcome.failure_receipt_serial.value != 903 ||
      *output.next_cycle_evidence.delta.value != -10) {
    return false;
  }
  Set(failed, "zg361_b2_pip_performance_evidence_status", Number(2));
  Set(failed, "zg361_b2_pip_performance_evidence_consumed_cycle", Number(8));
  Set(failed, "zg361_b2_pip_performance_evidence_consumed_case", Number(903));
  if (!Read(failed, output) ||
      !output.readiness.next_cycle_evidence_ready ||
      *output.next_cycle_evidence.consumed_cycle_serial.value != 8) {
    return false;
  }

  Fixture refused;
  PopulateRefused(refused);
  return Read(refused, output) && output.readiness.response_ready &&
         !output.readiness.outcome_ready &&
         output.readiness.next_cycle_evidence_ready &&
         *output.response.refusal_receipt_serial.value == 903;
}

bool TestFrameAndAllowlistDriftFailClosed() {
  xar::game::ZhongguoB2PipSnapshotV1 output{};
  Fixture frame_drift;
  PopulatePending(frame_drift);
  frame_drift.drift_frame = true;
  if (Read(frame_drift, output) ||
      output.unavailable_reason != "state_changed") {
    return false;
  }

  Fixture subject_drift;
  PopulatePending(subject_drift);
  subject_drift.drift_subject_rows = true;
  if (Read(subject_drift, output) ||
      output.unavailable_reason != "state_changed") {
    return false;
  }

  Fixture owner_drift;
  PopulateAccepted(owner_drift);
  owner_drift.drift_owner_rows = true;
  return !Read(owner_drift, output) &&
         output.unavailable_reason == "state_changed";
}

} // namespace

int main() {
  if (!TestPendingAndAllowlist() || !TestAcceptedSupportAndOwnerScope() ||
      !TestStaleSupportFlagsRejectPackageReadiness() ||
      !TestGateOnlyAndBindingFailures() ||
      !TestTerminalRefusalAndConsumedEvidence() ||
      !TestFrameAndAllowlistDriftFailClosed()) {
    std::cerr << "zhongguo B2 PIP snapshot fixture failed\n";
    return 1;
  }
  return 0;
}
