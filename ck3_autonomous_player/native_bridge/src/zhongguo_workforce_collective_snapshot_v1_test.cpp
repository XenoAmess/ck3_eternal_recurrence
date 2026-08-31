#include "xar_bridge/zhongguo_workforce_collective_snapshot_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>

namespace {

using xar::ck3_11906::ZhongguoWorkforceRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{91, 730'301, true, true,
                                       true, true, 100};
  bool main_thread = true;
  std::unordered_set<std::int32_t> characters{100, 200, 201, 202, 203, 300};
  std::unordered_map<std::string, ZhongguoWorkforceRawVariableV1> variables;
  std::size_t reads = 0;
  std::size_t owner_read_attempts = 0;
  std::size_t captures = 0;
  bool reject_unbound_owner_scope = false;
  bool drift_frame = false;
  bool drift_subject_rows = false;
  bool drift_owner_rows = false;
};

ZhongguoWorkforceRawVariableV1 Number(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoWorkforceRawVariableV1 Character(std::int32_t value) {
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
                  ZhongguoWorkforceRawVariableV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto &subject =
      xar::ck3_11906::kZhongguoWorkforceSubjectVariableAllowlist;
  const auto &owner =
      xar::ck3_11906::kZhongguoWorkforceOwnerVariableAllowlist;
  const bool subject_read =
      character_id == fixture.frame.played_character_id &&
      std::find(subject.begin(), subject.end(), key) != subject.end();
  const bool owner_key =
      std::find(owner.begin(), owner.end(), key) != owner.end();
  const bool owner_read =
      character_id != fixture.frame.played_character_id &&
      owner_key;
  if (owner_read) {
    ++fixture.owner_read_attempts;
    if (fixture.reject_unbound_owner_scope && character_id != 200) {
      return false;
    }
  }
  if (!subject_read && !owner_read) return false;
  ++fixture.reads;
  const auto found = fixture.variables.find(Key(character_id, key));
  output = found == fixture.variables.end()
               ? ZhongguoWorkforceRawVariableV1{}
               : found->second;
  const auto pass_width = subject.size() + owner.size();
  if (subject_read && fixture.drift_subject_rows &&
      fixture.reads > pass_width && key == "zg361_case_al_revision") {
    output = Number(2);
  }
  if (owner_read && fixture.drift_owner_rows &&
      fixture.reads > pass_width + subject.size() &&
      key == "zg361_we_completed_cycle_ledger_count") {
    output = Number(2);
  }
  return true;
}

xar::ck3_11906::ZhongguoWorkforceNativeEnvironmentV1 Environment() {
  xar::ck3_11906::ZhongguoWorkforceNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoWorkforceAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoWorkforceAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  return access;
}

xar::ck3_11906::ZhongguoWorkforceCollectiveSnapshotRequestV1 Request(
    std::int32_t owner = 200) {
  return {91, owner, "workforce:91"};
}

void Set(Fixture &fixture, std::string_view name,
         ZhongguoWorkforceRawVariableV1 value,
         std::int32_t character_id = 100) {
  fixture.variables[Key(character_id, name)] = value;
}

void PopulateCase(Fixture &fixture) {
  Set(fixture, "zg361_case_al_owner", Character(200));
  Set(fixture, "zg361_case_al_subject", Character(100));
  Set(fixture, "zg361_case_al_cycle_serial", Number(7));
  Set(fixture, "zg361_case_al_case_serial", Number(903));
  Set(fixture, "zg361_case_al_state", Number(8));
  Set(fixture, "zg361_case_al_active", Number(0));
  Set(fixture, "zg361_case_al_revision", Number(1));
}

void PopulateReceipt(Fixture &fixture, std::int64_t choice) {
  Set(fixture, "zg361_we_m360_receipt_owner", Character(200));
  Set(fixture, "zg361_we_m360_receipt_subject", Character(100));
  Set(fixture, "zg361_we_m360_receipt_cycle", Number(7));
  Set(fixture, "zg361_we_m360_receipt_case", Number(903));
  Set(fixture, "zg361_we_m360_receipt_state", Number(4));
  Set(fixture, "zg361_we_m360_receipt_choice", Number(choice));
}

std::string CohortKey(std::size_t slot, std::string_view suffix) {
  return "zg361_we_al_external_collective_" + std::to_string(slot) + "_" +
         std::string(suffix);
}

void PopulateCollective(Fixture &fixture, std::int64_t route) {
  PopulateReceipt(fixture, route);
  Set(fixture, "zg361_we_al_external_collective_submission_active", Number(0));
  Set(fixture, "zg361_we_al_external_collective_submission_sealed", Number(1));
  Set(fixture, "zg361_we_al_external_collective_submission_consumed", Number(1));
  Set(fixture, "zg361_we_al_external_collective_submission_owner", Character(200));
  Set(fixture, "zg361_we_al_external_collective_submission_subject", Character(100));
  Set(fixture, "zg361_we_al_external_collective_submission_cycle", Number(7));
  Set(fixture, "zg361_we_al_external_collective_submission_case", Number(903));
  Set(fixture, "zg361_we_al_external_collective_submission_state", Number(4));
  Set(fixture, "zg361_we_al_external_collective_case", Number(903));
  Set(fixture, "zg361_we_al_external_collective_submitted_cycle", Number(7));
  Set(fixture, "zg361_we_al_external_collective_cohort_count", Number(3));
  Set(fixture, "zg361_we_al_external_collective_settlement_id", Number(701));
  Set(fixture, "zg361_we_al_external_collective_settlement_hash", Number(702));
  Set(fixture, "zg361_we_al_external_collective_settled", Number(1));
  Set(fixture, "zg361_we_al_external_collective_route", Number(route));
  Set(fixture, "zg361_we_al_external_collective_total_members", Number(12));
  Set(fixture, "zg361_we_al_external_collective_total_quota", Number(3));
  Set(fixture, "zg361_we_al_external_collective_forced_count",
      Number(route == 2 ? 3 : 0));
  Set(fixture, "zg361_we_al_external_collective_exception_count",
      Number(route == 1 ? 3 : 0));
  Set(fixture, "zg361_we_al_external_collective_manager_cost_total",
      Number(route == 1 ? 3 : 0));
  for (std::size_t slot = 1; slot <= 3; ++slot) {
    Set(fixture, CohortKey(slot, "cohort_id"), Number(slot));
    Set(fixture, CohortKey(slot, "manager"),
        Character(static_cast<std::int32_t>(200 + slot)));
    Set(fixture, CohortKey(slot, "member_count"), Number(4));
    Set(fixture, CohortKey(slot, "member_hash"), Number(1000 + slot));
    Set(fixture, CohortKey(slot, "quota"), Number(1));
    Set(fixture, CohortKey(slot, "forced_count"),
        Number(route == 2 ? 1 : 0));
    Set(fixture, CohortKey(slot, "exception_count"),
        Number(route == 1 ? 1 : 0));
    Set(fixture, CohortKey(slot, "manager_cost"),
        Number(route == 1 ? 1 : 0));
    Set(fixture, CohortKey(slot, "partition_verified"), Number(1));
    Set(fixture, CohortKey(slot, "approval_verified"),
        Number(route == 1 ? 1 : 0));
    Set(fixture, CohortKey(slot, "b1_cycle"), Number(7));
    Set(fixture, CohortKey(slot, "b1_case"), Number(800 + slot));
    Set(fixture, CohortKey(slot, "b1_source_id"), Number(900 + slot));
    Set(fixture, CohortKey(slot, "b1_source_hash"), Number(1000 + slot));
    Set(fixture, CohortKey(slot, "mg_cycle"), Number(7));
    Set(fixture, CohortKey(slot, "mg_case"), Number(1100 + slot));
    Set(fixture, CohortKey(slot, "mg_snapshot_source_serial"),
        Number(1200 + slot));
    Set(fixture, CohortKey(slot, "mg_snapshot_revision"), Number(1));
  }
}

std::string HistoryKey(std::size_t slot, std::string_view field) {
  return "zg361_we_completed_cycle_ledger_" + std::string(field) + "_" +
         std::to_string(slot);
}

void PopulateHistory(Fixture &fixture, std::int64_t count) {
  Set(fixture, "zg361_we_completed_cycle_ledger_count", Number(count), 200);
  for (std::size_t slot = 1; slot <= static_cast<std::size_t>(count); ++slot) {
    Set(fixture, HistoryKey(slot, "owner"), Character(200), 200);
    Set(fixture, HistoryKey(slot, "subject"), Character(100), 200);
    Set(fixture, HistoryKey(slot, "cycle"), Number(4 + slot), 200);
    Set(fixture, HistoryKey(slot, "case"), Number(900 + slot), 200);
    Set(fixture, HistoryKey(slot, "m357_receipt_id"), Number(1000 + slot), 200);
    Set(fixture, HistoryKey(slot, "m357_receipt_hash"), Number(2000 + slot), 200);
    Set(fixture, HistoryKey(slot, "m358_receipt_id"), Number(3000 + slot), 200);
    Set(fixture, HistoryKey(slot, "m358_receipt_hash"), Number(4000 + slot), 200);
    Set(fixture, HistoryKey(slot, "m359_receipt_id"), Number(5000 + slot), 200);
    Set(fixture, HistoryKey(slot, "m359_receipt_hash"), Number(6000 + slot), 200);
  }
}

void PopulateCharterGate(Fixture &fixture, bool consumed,
                         bool deferred = false) {
  Set(fixture, "zg361_we_m361_evidence_count", Number(3));
  Set(fixture, "zg361_we_m361_evidence_ready",
      Number(!consumed && !deferred ? 1 : 0));
  Set(fixture, "zg361_we_m361_evidence_consumed", Number(consumed ? 1 : 0));
  Set(fixture, "zg361_we_m361_evidence_owner", Character(200));
  Set(fixture, "zg361_we_m361_evidence_subject", Character(100));
  Set(fixture, "zg361_we_m361_evidence_cycle", Number(7));
  Set(fixture, "zg361_we_m361_evidence_case", Number(903));
  Set(fixture, "zg361_we_m361_evidence_state", Number(5));
  Set(fixture, "zg361_we_m361_prepared_report_id", Number(7001));
  Set(fixture, "zg361_we_m361_prepared_charter_id", Number(7002));
  Set(fixture, "zg361_we_m361_prepared_previous_charter_id", Number(0));
  Set(fixture, "zg361_we_m361_prepared_previous_version", Number(0));
  Set(fixture, "zg361_we_m361_prepared_adopted_cycle", Number(7));
  Set(fixture, "zg361_we_m361_prepared_effective_cycle", Number(8));
  for (std::size_t slot = 1; slot <= 3; ++slot) {
    Set(fixture, "zg361_we_m361_evidence_owner_" + std::to_string(slot),
        Character(200));
    Set(fixture, "zg361_we_m361_evidence_subject_" + std::to_string(slot),
        Character(100));
    Set(fixture, "zg361_we_m361_evidence_cycle_" + std::to_string(slot),
        Number(4 + slot));
    Set(fixture, "zg361_we_m361_evidence_case_" + std::to_string(slot),
        Number(900 + slot));
    Set(fixture,
        "zg361_we_m361_evidence_m357_receipt_id_" + std::to_string(slot),
        Number(1000 + slot));
    Set(fixture,
        "zg361_we_m361_evidence_m357_receipt_hash_" + std::to_string(slot),
        Number(2000 + slot));
    Set(fixture,
        "zg361_we_m361_evidence_m358_receipt_id_" + std::to_string(slot),
        Number(3000 + slot));
    Set(fixture,
        "zg361_we_m361_evidence_m358_receipt_hash_" + std::to_string(slot),
        Number(4000 + slot));
    Set(fixture,
        "zg361_we_m361_evidence_m359_receipt_id_" + std::to_string(slot),
        Number(5000 + slot));
    Set(fixture,
        "zg361_we_m361_evidence_m359_receipt_hash_" + std::to_string(slot),
        Number(6000 + slot));
  }
}

void PopulateDebt(Fixture &fixture) {
  PopulateReceipt(fixture, 3);
  Set(fixture, "zg361_we_m360_debt_owner", Character(200));
  Set(fixture, "zg361_we_m360_debt_subject", Character(100));
  Set(fixture, "zg361_we_m360_debt_cycle", Number(7));
  Set(fixture, "zg361_we_m360_debt_case", Number(903));
  Set(fixture, "zg361_we_m360_debt_state", Number(4));
  Set(fixture, "zg361_we_m360_debt_open", Number(1));
  Set(fixture, "zg361_we_m360_debt_consumed", Number(0));
  Set(fixture, "zg361_we_m360_debt_due_cycle", Number(8));
}

bool Read(Fixture &fixture,
          xar::game::ZhongguoWorkforceCollectiveSnapshotV1 &output,
          xar::ck3_11906::ZhongguoWorkforceCollectiveSnapshotRequestV1 request =
              Request()) {
  return xar::ck3_11906::ReadZhongguoWorkforceCollectiveSnapshotV1(
             Environment(), Access(fixture), request, output) ==
         xar::game::ReadZhongguoWorkforceCollectiveSnapshotResultV1::available;
}

bool TestNotReachedAndAllowlist() {
  Fixture fixture;
  PopulateCase(fixture);
  xar::game::ZhongguoWorkforceCollectiveSnapshotV1 output{};
  return Read(fixture, output) && output.readiness.ready &&
         output.collective.phase ==
             xar::game::ZhongguoWorkforceCollectivePhaseV1::not_reached &&
         output.history.status ==
             xar::game::ZhongguoWorkforceHistoryStatusV1::empty &&
         output.charter_gate.status ==
             xar::game::ZhongguoWorkforceCharterGateStatusV1::not_eligible &&
         fixture.reads ==
             2 * (xar::ck3_11906::
                      kZhongguoWorkforceSubjectVariableAllowlist.size() +
                  xar::ck3_11906::
                      kZhongguoWorkforceOwnerVariableAllowlist.size());
}

bool TestRouteAThreeCycleAndSerializer() {
  Fixture fixture;
  PopulateCase(fixture);
  PopulateCollective(fixture, 1);
  PopulateHistory(fixture, 3);
  PopulateCharterGate(fixture, false);
  xar::game::ZhongguoWorkforceCollectiveSnapshotV1 output{};
  if (!Read(fixture, output) || !output.readiness.ready ||
      !output.readiness.three_cycle_ready ||
      output.collective.phase !=
          xar::game::ZhongguoWorkforceCollectivePhaseV1::route_a_exception ||
      output.history.status !=
          xar::game::ZhongguoWorkforceHistoryStatusV1::three_cycle ||
      output.charter_gate.status !=
          xar::game::ZhongguoWorkforceCharterGateStatusV1::ready ||
      *output.collective.exception_count.value != 3 ||
      *output.collective.manager_cost_total.value != 3) {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoWorkforceCollectiveSnapshotV1(output);
  return json.find("\"case_kind\":\"zhongguo.workforce-collective\"") !=
             std::string::npos &&
         json.find("\"phase\":\"route_a_exception\"") !=
             std::string::npos &&
         json.find("\"status\":\"three_cycle\"") !=
             std::string::npos &&
         json.find("\"status\":\"ready\"") != std::string::npos;
}

bool TestRouteBAndRouteC() {
  Fixture route_b;
  PopulateCase(route_b);
  PopulateCollective(route_b, 2);
  PopulateHistory(route_b, 1);
  xar::game::ZhongguoWorkforceCollectiveSnapshotV1 output_b{};
  if (!Read(route_b, output_b) ||
      output_b.collective.phase !=
          xar::game::ZhongguoWorkforceCollectivePhaseV1::route_b_forced ||
      *output_b.collective.forced_count.value != 3 ||
      *output_b.collective.exception_count.value != 0 ||
      output_b.history.status !=
          xar::game::ZhongguoWorkforceHistoryStatusV1::partial) {
    return false;
  }

  Fixture route_c;
  PopulateCase(route_c);
  PopulateDebt(route_c);
  PopulateHistory(route_c, 2);
  xar::game::ZhongguoWorkforceCollectiveSnapshotV1 output_c{};
  return Read(route_c, output_c) && output_c.readiness.ready &&
         output_c.collective.phase ==
             xar::game::ZhongguoWorkforceCollectivePhaseV1::route_c_debt &&
         *output_c.route_c_debt.due_cycle_serial.value == 8;
}

bool TestCharterLifecycleAndFrozenEvidence() {
  Fixture consumed;
  PopulateCase(consumed);
  PopulateHistory(consumed, 3);
  PopulateCharterGate(consumed, true);
  xar::game::ZhongguoWorkforceCollectiveSnapshotV1 output{};
  if (!Read(consumed, output) ||
      output.charter_gate.status !=
          xar::game::ZhongguoWorkforceCharterGateStatusV1::consumed) {
    return false;
  }

  Fixture deferred;
  PopulateCase(deferred);
  PopulateHistory(deferred, 3);
  PopulateCharterGate(deferred, false, true);
  if (!Read(deferred, output) ||
      output.charter_gate.status !=
          xar::game::ZhongguoWorkforceCharterGateStatusV1::awaiting_gate) {
    return false;
  }

  Fixture mismatch;
  PopulateCase(mismatch);
  PopulateHistory(mismatch, 3);
  PopulateCharterGate(mismatch, false);
  Set(mismatch, "zg361_we_m361_evidence_cycle_2", Number(99));
  return !Read(mismatch, output) &&
         output.unavailable_reason == "history_inconsistent";
}

bool TestFailClosedCases() {
  Fixture wrong_owner;
  PopulateCase(wrong_owner);
  wrong_owner.reject_unbound_owner_scope = true;
  xar::game::ZhongguoWorkforceCollectiveSnapshotV1 output{};
  if (Read(wrong_owner, output, Request(300)) ||
      output.unavailable_reason != "owner_filter_mismatch" ||
      wrong_owner.owner_read_attempts != 0 ||
      wrong_owner.reads !=
          xar::ck3_11906::
              kZhongguoWorkforceSubjectVariableAllowlist.size()) {
    return false;
  }

  Fixture history_order;
  PopulateCase(history_order);
  PopulateHistory(history_order, 2);
  Set(history_order, HistoryKey(2, "cycle"), Number(5), 200);
  if (Read(history_order, output) ||
      output.unavailable_reason != "history_inconsistent") {
    return false;
  }

  Fixture raw_drift;
  PopulateCase(raw_drift);
  raw_drift.drift_subject_rows = true;
  if (Read(raw_drift, output) || output.unavailable_reason != "state_changed") {
    return false;
  }

  Fixture frame_drift;
  PopulateCase(frame_drift);
  frame_drift.drift_frame = true;
  return !Read(frame_drift, output) &&
         output.unavailable_reason == "state_changed";
}

} // namespace

int main() {
  if (!TestNotReachedAndAllowlist()) {
    std::cerr << "Workforce not-reached/allowlist fixture failed\n";
    return 1;
  }
  if (!TestRouteAThreeCycleAndSerializer()) {
    std::cerr << "Workforce route-A/three-cycle fixture failed\n";
    return 1;
  }
  if (!TestRouteBAndRouteC()) {
    std::cerr << "Workforce route-B/route-C fixture failed\n";
    return 1;
  }
  if (!TestCharterLifecycleAndFrozenEvidence()) {
    std::cerr << "Workforce charter lifecycle/frozen evidence fixture failed\n";
    return 1;
  }
  if (!TestFailClosedCases()) {
    std::cerr << "Workforce fail-closed fixture failed\n";
    return 1;
  }
  return 0;
}
