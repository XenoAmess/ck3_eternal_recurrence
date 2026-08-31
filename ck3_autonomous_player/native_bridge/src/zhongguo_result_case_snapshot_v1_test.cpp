#include "xar_bridge/zhongguo_result_case_snapshot_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

using xar::ck3_11906::ZhongguoResultRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{81, 730'101, true, true,
                                       true, true, 100};
  bool main_thread = true;
  bool drift_rows = false;
  std::uint32_t captures = 0;
  std::uint32_t variable_reads = 0;
  std::unordered_set<std::int32_t> characters{100, 200};
  std::unordered_map<std::string, ZhongguoResultRawVariableV1> variables;
  std::vector<std::string> requested_keys;
};

ZhongguoResultRawVariableV1 Number(std::int64_t value) {
  return {true, 1, value * 100'000};
}

ZhongguoResultRawVariableV1 Q100000(std::int64_t value) {
  return {true, 1, value};
}

ZhongguoResultRawVariableV1 Character(std::int32_t value) {
  return {true, 4, value};
}

bool Capture(void *opaque, xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  output = fixture.frame;
  ++fixture.captures;
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
                  ZhongguoResultRawVariableV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto &allowlist =
      xar::ck3_11906::kZhongguoResultCaseSnapshotV1VariableAllowlist;
  if (character_id != fixture.frame.played_character_id ||
      std::find(allowlist.begin(), allowlist.end(), key) == allowlist.end()) {
    return false;
  }
  try {
    fixture.requested_keys.emplace_back(key);
  } catch (...) {
    return false;
  }
  ++fixture.variable_reads;
  const auto found = fixture.variables.find(std::string(key));
  output = found == fixture.variables.end()
               ? ZhongguoResultRawVariableV1{}
               : found->second;
  if (fixture.drift_rows && fixture.variable_reads > allowlist.size() &&
      key == "zg361_result_case_state") {
    output = Number(2);
  }
  return true;
}

xar::ck3_11906::ZhongguoResultNativeEnvironmentV1 Environment() {
  xar::ck3_11906::ZhongguoResultNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  return environment;
}

xar::ck3_11906::ZhongguoResultAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::ZhongguoResultAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &IsMain;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  return access;
}

xar::ck3_11906::ZhongguoResultCaseSnapshotRequestV1 Request(
    std::int32_t owner = 200) {
  return {81, owner, "received-self:81"};
}

void PopulateOpen(Fixture &fixture, std::int32_t owner = 200) {
  fixture.variables["zg361_result_case_owner"] = Character(owner);
  fixture.variables["zg361_result_cycle_serial"] = Number(7);
  fixture.variables["zg361_result_case_serial"] = Number(903);
  fixture.variables["zg361_result_case_state"] = Number(1);
  fixture.variables["zg361_result_grade"] = Number(1);
  fixture.variables["zg361_result_absolute_grade"] = Number(2);
  fixture.variables["zg361_result_kpi_frozen"] = Q100000(7'654'321);
  fixture.variables["zg361_result_rank_frozen"] = Number(4);
  fixture.variables["zg361_result_cohort_n_frozen"] = Number(17);
  fixture.variables["zg361_result_delivery_method"] = Number(0);
  fixture.variables["zg361_result_settlement_posted_serial"] = Number(0);
  fixture.variables["zg361_result_appeal_open"] = Number(0);
  // Objection is deliberately absent: product initialization removes it.
}

bool AllSemanticsUnavailable(
    const xar::game::ZhongguoResultCaseSnapshotV1 &value) {
  return !value.case_identity.owner_character_id.available &&
         !value.case_identity.subject_character_id.available &&
         !value.case_identity.cycle_serial.available &&
         !value.case_identity.case_serial.available &&
         !value.case_identity.state.available &&
         !value.case_identity.grade.available &&
         !value.notice.absolute_grade.available &&
         !value.notice.kpi_frozen_q100000.available &&
         !value.notice.rank_frozen.available &&
         !value.notice.cohort_n_frozen.available &&
         !value.delivery.method.available &&
         !value.delivery.objection_recorded.available &&
         !value.delivery.settlement_posted_serial.available &&
         !value.delivery.appeal_open.available;
}

bool Read(Fixture &fixture,
          xar::game::ZhongguoResultCaseSnapshotV1 &output,
          xar::ck3_11906::ZhongguoResultCaseSnapshotRequestV1 request =
              Request()) {
  return xar::ck3_11906::ReadZhongguoResultCaseSnapshotV1(
             Environment(), Access(fixture), request, output) ==
         xar::game::ReadZhongguoResultCaseSnapshotResultV1::available;
}

bool TestOpenAndAllowlist() {
  Fixture fixture;
  PopulateOpen(fixture);
  xar::game::ZhongguoResultCaseSnapshotV1 output{};
  if (!Read(fixture, output) || !output.readiness.ready ||
      output.subject_character_id != 100 ||
      !output.case_identity.subject_character_id.available ||
      *output.case_identity.subject_character_id.value != 100 ||
      *output.case_identity.owner_character_id.value != 200 ||
      *output.notice.kpi_frozen_q100000.value != 7'654'321 ||
      !output.delivery.objection_recorded.available ||
      *output.delivery.objection_recorded.value ||
      fixture.variable_reads !=
          2 * xar::ck3_11906::
                  kZhongguoResultCaseSnapshotV1VariableAllowlist.size()) {
    return false;
  }
  for (const auto &key : fixture.requested_keys) {
    if (key.starts_with("zg361_b1_")) return false;
  }
  const auto json =
      xar::ck3_11906::SerializeZhongguoResultCaseSnapshotV1(output);
  return json.find("\"case_kind\":\"zhongguo.result.received-self\"") !=
             std::string::npos &&
         json.find("\"kpi_frozen_q100000\":{\"status\":\"available\","
                   "\"value\":7654321") != std::string::npos;
}

bool TestDeliveryMatrix() {
  xar::game::ZhongguoResultCaseSnapshotV1 output{};

  Fixture signed_a;
  PopulateOpen(signed_a);
  signed_a.variables["zg361_result_case_state"] = Number(3);
  signed_a.variables["zg361_result_delivery_method"] = Number(1);
  signed_a.variables["zg361_result_settlement_posted_serial"] = Number(903);
  signed_a.variables["zg361_result_appeal_open"] = Number(1);
  if (!Read(signed_a, output) || !output.readiness.delivery_state_ready) {
    return false;
  }

  Fixture signed_b;
  PopulateOpen(signed_b);
  signed_b.variables["zg361_result_case_state"] = Number(3);
  signed_b.variables["zg361_result_delivery_method"] = Number(2);
  signed_b.variables["zg361_result_objection_recorded"] = Number(1);
  signed_b.variables["zg361_result_settlement_posted_serial"] = Number(903);
  signed_b.variables["zg361_result_appeal_open"] = Number(1);
  if (!Read(signed_b, output) || !output.readiness.delivery_state_ready) {
    return false;
  }

  Fixture refused_c;
  PopulateOpen(refused_c);
  refused_c.variables["zg361_result_case_state"] = Number(2);
  refused_c.variables["zg361_result_delivery_method"] = Number(3);
  if (!Read(refused_c, output) || !output.readiness.delivery_state_ready) {
    return false;
  }

  signed_a.variables["zg361_result_settlement_posted_serial"] = Number(902);
  return Read(signed_a, output) &&
         !output.readiness.delivery_state_ready && !output.readiness.ready;
}

bool TestBindingAndCoreNegatives() {
  xar::game::ZhongguoResultCaseSnapshotV1 output{};
  Fixture wrong_owner;
  PopulateOpen(wrong_owner);
  if (Read(wrong_owner, output, Request(201)) ||
      output.unavailable_reason != "owner_filter_mismatch" ||
      !AllSemanticsUnavailable(output)) {
    return false;
  }

  Fixture self_owned;
  PopulateOpen(self_owned, 100);
  if (Read(self_owned, output, Request(100)) ||
      output.unavailable_reason != "not_received_self" ||
      !AllSemanticsUnavailable(output)) {
    return false;
  }

  Fixture wrong_kind;
  PopulateOpen(wrong_kind);
  wrong_kind.variables["zg361_result_case_owner"] = Number(200);
  if (Read(wrong_kind, output) ||
      output.unavailable_reason != "case_inconsistent" ||
      !AllSemanticsUnavailable(output)) {
    return false;
  }

  Fixture partial;
  PopulateOpen(partial);
  partial.variables.erase("zg361_result_case_state");
  if (Read(partial, output) ||
      output.unavailable_reason != "case_inconsistent" ||
      !AllSemanticsUnavailable(output)) {
    return false;
  }

  Fixture absent;
  if (Read(absent, output) || output.unavailable_reason != "case_not_found" ||
      !AllSemanticsUnavailable(output)) {
    return false;
  }
  return true;
}

bool TestReadinessAndDrift() {
  xar::game::ZhongguoResultCaseSnapshotV1 output{};
  Fixture rank;
  PopulateOpen(rank);
  rank.variables["zg361_result_rank_frozen"] = Number(18);
  if (!Read(rank, output) || output.readiness.notice_facts_ready ||
      output.readiness.ready) {
    return false;
  }

  Fixture drift;
  PopulateOpen(drift);
  drift.drift_rows = true;
  if (Read(drift, output) || output.unavailable_reason != "state_changed" ||
      !AllSemanticsUnavailable(output)) {
    return false;
  }

  Fixture direct;
  PopulateOpen(direct);
  direct.main_thread = false;
  return !Read(direct, output) &&
         output.unavailable_reason == "requires_application_main";
}

} // namespace

int main() {
  const bool ok = TestOpenAndAllowlist() && TestDeliveryMatrix() &&
                  TestBindingAndCoreNegatives() && TestReadinessAndDrift();
  if (!ok) {
    std::cerr << "zhongguo received-self result snapshot fixture failed\n";
    return 1;
  }
  return 0;
}
