#include "xar_bridge/zhongguo_manager_governance_snapshot_v1.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>

namespace {

using xar::ck3_11906::ZhongguoBoundedAiManagerAuthorizationV1;
using xar::ck3_11906::ZhongguoManagerGovernanceRawVariableV1;

constexpr std::int64_t kScale = 100'000;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{
      81, 730101, true, true, true, true, 100};
  std::unordered_map<std::string, ZhongguoManagerGovernanceRawVariableV1> rows;
  ZhongguoBoundedAiManagerAuthorizationV1 authorization =
      ZhongguoBoundedAiManagerAuthorizationV1::authorized_direct_manager;
};

ZhongguoManagerGovernanceRawVariableV1 Integer(std::int64_t value) {
  return {true, 1, value * kScale};
}

ZhongguoManagerGovernanceRawVariableV1 Character(std::int32_t value) {
  return {true, 4, value};
}

void Put(Fixture &fixture, std::string_view key,
         ZhongguoManagerGovernanceRawVariableV1 value) {
  fixture.rows.insert_or_assign(std::string(key), value);
}

void PutReceipt(Fixture &fixture, std::string_view prefix,
                std::int64_t choice) {
  Put(fixture, std::string(prefix) + "_owner", Character(100));
  Put(fixture, std::string(prefix) + "_subject", Character(200));
  Put(fixture, std::string(prefix) + "_cycle", Integer(7));
  Put(fixture, std::string(prefix) + "_case", Integer(903));
  Put(fixture, std::string(prefix) + "_state", Integer(1));
  Put(fixture, std::string(prefix) + "_choice", Integer(choice));
}

Fixture ReadyFixture() {
  Fixture fixture;
  Put(fixture, "zg361_case_f_owner", Character(100));
  Put(fixture, "zg361_case_f_subject", Character(200));
  Put(fixture, "zg361_case_f_cycle_serial", Integer(7));
  Put(fixture, "zg361_case_f_case_serial", Integer(903));
  Put(fixture, "zg361_case_f_state", Integer(2));
  Put(fixture, "zg361_case_f_active", Integer(1));
  Put(fixture, "zg361_case_f_revision", Integer(5));

  Put(fixture, "zg361_mg_team_snapshot_status", Integer(1));
  Put(fixture, "zg361_mg_team_snapshot_owner", Character(100));
  Put(fixture, "zg361_mg_team_snapshot_subject", Character(200));
  Put(fixture, "zg361_mg_team_snapshot_cycle", Integer(7));
  Put(fixture, "zg361_mg_team_snapshot_case", Integer(903));
  Put(fixture, "zg361_mg_team_snapshot_revision", Integer(12));
  Put(fixture, "zg361_mg_team_snapshot_source_cycle", Integer(6));
  Put(fixture, "zg361_mg_team_n", Integer(17));
  Put(fixture, "zg361_mg_team_targets", Integer(25));
  Put(fixture, "zg361_mg_team_jingcha", Integer(10));
  Put(fixture, "zg361_mg_team_calibration", Integer(-5));
  Put(fixture, "zg361_mg_team_pip_success", Integer(5));
  Put(fixture, "zg361_mg_team_appeal_overturn", Integer(-5));
  Put(fixture, "zg361_mg_team_retention", Integer(30));
  Put(fixture, "zg361_mg_team_hc_efficiency", Integer(9));

  PutReceipt(fixture, "zg361_mg_m035_receipt", 1);
  Put(fixture, "zg361_mg_distribution_policy_available", Integer(1));
  Put(fixture, "zg361_mg_distribution_mode", Integer(1));
  Put(fixture, "zg361_mg_distribution_rule_source", Integer(2));
  Put(fixture, "zg361_mg_distribution_top_slots", Integer(5));
  Put(fixture, "zg361_mg_distribution_middle_slots", Integer(11));
  Put(fixture, "zg361_mg_distribution_bottom_slots", Integer(1));
  Put(fixture, "zg361_mg_distribution_conserved", Integer(17));
  Put(fixture, "zg361_mg_distribution_policy_status", Integer(2));
  Put(fixture, "zg361_mg_distribution_policy_owner", Character(200));
  Put(fixture, "zg361_mg_distribution_policy_subject", Character(200));
  Put(fixture, "zg361_mg_distribution_policy_source_reviewer",
      Character(100));
  Put(fixture, "zg361_mg_distribution_policy_source_cycle", Integer(7));
  Put(fixture, "zg361_mg_distribution_policy_source_case", Integer(903));
  Put(fixture, "zg361_mg_distribution_policy_source_revision", Integer(3));
  Put(fixture, "zg361_mg_distribution_policy_input_revision", Integer(12));
  Put(fixture, "zg361_mg_distribution_policy_mode", Integer(1));
  Put(fixture, "zg361_mg_distribution_policy_rule_source", Integer(2));
  Put(fixture, "zg361_mg_distribution_policy_due_cycle", Integer(8));
  Put(fixture, "zg361_mg_distribution_effective_mode", Integer(1));
  Put(fixture, "zg361_mg_distribution_effective_cycle", Integer(8));
  Put(fixture, "zg361_mg_distribution_effective_source_cycle", Integer(7));
  Put(fixture, "zg361_mg_distribution_effective_source_case", Integer(903));
  Put(fixture, "zg361_mg_distribution_effective_input_revision", Integer(12));
  Put(fixture, "zg361_mg_distribution_policy_settled_cycle", Integer(8));
  Put(fixture, "zg361_mg_distribution_policy_settlement_receipt",
      Integer(903));
  Put(fixture, "zg361_cohort_n", Integer(23));
  Put(fixture, "zg361_bottom_slots", Integer(2));

  PutReceipt(fixture, "zg361_mg_m032_receipt", 1);
  Put(fixture, "zg361_mg_manager_score", Integer(69));
  Put(fixture, "zg361_mg_manager_score_mode", Integer(1));
  Put(fixture, "zg361_mg_organization_input_status", Integer(2));
  Put(fixture, "zg361_mg_organization_input_owner", Character(100));
  Put(fixture, "zg361_mg_organization_input_subject", Character(200));
  Put(fixture, "zg361_mg_organization_input_source_cycle", Integer(7));
  Put(fixture, "zg361_mg_organization_input_source_case", Integer(903));
  Put(fixture, "zg361_mg_organization_input_source_revision", Integer(4));
  Put(fixture, "zg361_mg_organization_input_revision", Integer(12));
  Put(fixture, "zg361_mg_organization_input_component", Integer(8));
  Put(fixture, "zg361_mg_organization_input_value", Integer(69));
  Put(fixture, "zg361_mg_organization_input_due_cycle", Integer(8));
  Put(fixture, "zg361_mg_organization_settled_by_owner", Character(100));
  Put(fixture, "zg361_mg_organization_settled_cycle", Integer(8));
  Put(fixture, "zg361_mg_organization_settled_value", Integer(69));
  Put(fixture, "zg361_mg_organization_settlement_receipt", Integer(903));
  return fixture;
}

bool Capture(void *context, xar::game::ZhongguoCaseFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}

bool MainThread(void *) noexcept { return true; }

bool Validate(void *, std::int32_t character_id) noexcept {
  return character_id == 100 || character_id == 200;
}

bool ReadVariable(void *context, std::int32_t character_id,
                  std::string_view key,
                  ZhongguoManagerGovernanceRawVariableV1 &output) noexcept {
  output = {};
  if (character_id != 200) return false;
  const auto &rows = static_cast<Fixture *>(context)->rows;
  const auto found = rows.find(std::string(key));
  if (found != rows.end()) output = found->second;
  return true;
}

ZhongguoBoundedAiManagerAuthorizationV1 Authorize(
    void *context, std::int32_t player, std::int32_t subject,
    std::int32_t owner) noexcept {
  if (player != 100 || subject != 200 || owner != 100) {
    return ZhongguoBoundedAiManagerAuthorizationV1::rejected;
  }
  return static_cast<Fixture *>(context)->authorization;
}

xar::ck3_11906::ZhongguoManagerGovernanceAccessV1 Access(
    Fixture &fixture) {
  return {&fixture, &Capture, &MainThread, nullptr, &Validate, &ReadVariable,
          &Authorize};
}

bool ReadyAiManagerFixture() {
  auto fixture = ReadyFixture();
  auto environment =
      xar::ck3_11906::ZhongguoManagerGovernanceNativeEnvironmentV1{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  const xar::ck3_11906::ZhongguoManagerGovernanceSnapshotRequestV1 request{
      81, 200, 100, "manager:81"};
  xar::game::ZhongguoManagerGovernanceSnapshotV1 snapshot{};
  const auto result =
      xar::ck3_11906::ReadZhongguoManagerGovernanceSnapshotV1(
          environment, Access(fixture), request, snapshot);
  const auto json =
      xar::ck3_11906::SerializeZhongguoManagerGovernanceSnapshotV1(snapshot);
  return result == xar::game::ReadZhongguoManagerGovernanceSnapshotResultV1::
                       available &&
         snapshot.readiness.ready &&
         snapshot.readiness.bounded_ai_dependency_ready &&
         snapshot.readiness.actual_bottom_slots_ready &&
         snapshot.readiness.component8_settlement_ready &&
         json.find("\"case_kind\":\"zhongguo.manager-governance\"") !=
             std::string::npos &&
         json.find("\"actual_bottom_slots\":{\"status\":\"available\",\"value\":2") !=
             std::string::npos &&
         json.find("\"component\":{\"status\":\"available\",\"value\":8") !=
             std::string::npos;
}

bool DependencyUnavailableFixture() {
  auto fixture = ReadyFixture();
  fixture.authorization =
      ZhongguoBoundedAiManagerAuthorizationV1::dependency_unavailable;
  auto environment =
      xar::ck3_11906::ZhongguoManagerGovernanceNativeEnvironmentV1{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  const xar::ck3_11906::ZhongguoManagerGovernanceSnapshotRequestV1 request{
      81, 200, 100, "manager:dependency"};
  xar::game::ZhongguoManagerGovernanceSnapshotV1 snapshot{};
  const auto result =
      xar::ck3_11906::ReadZhongguoManagerGovernanceSnapshotV1(
          environment, Access(fixture), request, snapshot);
  return result == xar::game::ReadZhongguoManagerGovernanceSnapshotResultV1::
                       unavailable &&
         snapshot.unavailable_reason ==
             "bounded_ai_manager_dependency_unavailable" &&
         !snapshot.readiness.ready;
}

bool RouteCDoesNotLeakStaleBusinessFixture() {
  auto fixture = ReadyFixture();
  PutReceipt(fixture, "zg361_mg_m035_receipt", 3);
  PutReceipt(fixture, "zg361_mg_m032_receipt", 3);
  auto environment =
      xar::ck3_11906::ZhongguoManagerGovernanceNativeEnvironmentV1{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  const xar::ck3_11906::ZhongguoManagerGovernanceSnapshotRequestV1 request{
      81, 200, 100, "manager:route-c"};
  xar::game::ZhongguoManagerGovernanceSnapshotV1 snapshot{};
  const auto result =
      xar::ck3_11906::ReadZhongguoManagerGovernanceSnapshotV1(
          environment, Access(fixture), request, snapshot);
  return result == xar::game::ReadZhongguoManagerGovernanceSnapshotResultV1::
                       available &&
         snapshot.readiness.ready &&
         !snapshot.distribution_snapshot.mode.available &&
         snapshot.distribution_snapshot.mode.unavailable_reason ==
             "not_applicable" &&
         !snapshot.manager_score.sum.available &&
         snapshot.manager_score.sum.unavailable_reason == "not_applicable";
}

} // namespace

int main() {
  if (!ReadyAiManagerFixture() || !DependencyUnavailableFixture() ||
      !RouteCDoesNotLeakStaleBusinessFixture()) {
    std::cerr << "ZhongGuo manager-governance snapshot fixture failed\n";
    return 1;
  }
  return 0;
}
