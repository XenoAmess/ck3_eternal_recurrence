#include "xar_bridge/zhongguo_b1_cycle_snapshot_v1.hpp"
#include "xar_bridge/zhongguo_b1_cycle_snapshot_v1_mailbox.hpp"

#include <cstdint>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &) noexcept { return false; }

} // namespace xar::ck3_11906

namespace {

using xar::ck3_11906::ZhongguoRawVariableV1;

struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{77, 123456, true, true, true, true,
                                       100};
  std::unordered_map<std::string, ZhongguoRawVariableV1> variables;
  int reads = 0;
  bool mutate_second = false;
};

ZhongguoRawVariableV1 Number(std::int64_t value) {
  return {true, 1, value * 100'000};
}

bool Capture(void *opaque, xar::game::ZhongguoCaseFrameV1 &out) noexcept {
  out = static_cast<Fixture *>(opaque)->frame;
  return true;
}

bool Main(void *) noexcept { return true; }
bool Character(void *, std::int32_t id) noexcept { return id == 100; }

bool Variable(void *opaque, std::int32_t id, std::string_view key,
              ZhongguoRawVariableV1 &out) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (id != 100) return false;
  ++fixture.reads;
  const auto found = fixture.variables.find(std::string(key));
  out = found == fixture.variables.end() ? ZhongguoRawVariableV1{} : found->second;
  if (fixture.mutate_second && fixture.reads > 38 && key ==
      "zg361_b1_manager_cycle_serial")
    out = Number(8);
  return true;
}

Fixture Complete() {
  Fixture fixture;
  for (auto key : xar::ck3_11906::kZhongguoB1CycleSnapshotV1VariableAllowlist)
    fixture.variables[std::string(key)] = Number(0);
  fixture.variables["zg361_b1_manager_cycle_serial"] = Number(7);
  fixture.variables["zg361_b1_manager_case_serial"] = Number(19);
  fixture.variables["zg361_b1_cycle_state"] = Number(6);
  fixture.variables["zg361_b1_cycle_open_year"] = Number(1088);
  fixture.variables["zg361_b1_cycle_runtime_schema"] = Number(2);
  fixture.variables["zg361_b1_subject_n"] = Number(8);
  fixture.variables["zg361_b1_roster_audit_version"] = Number(1);
  fixture.variables["zg361_b1_processing_n"] = Number(8);
  fixture.variables["zg361_b1_quota_rebuild_generation"] = Number(1);
  fixture.variables["zg361_b1_quota_built_serial"] = Number(19);
  fixture.variables["zg361_b1_quota_book_version"] = Number(1);
  fixture.variables["zg361_pending_375_n"] = Number(2);
  fixture.variables["zg361_pending_35_n"] = Number(5);
  fixture.variables["zg361_pending_325_n"] = Number(1);
  fixture.variables["zg361_b1_quota_recount_top"] = Number(2);
  fixture.variables["zg361_b1_quota_recount_middle"] = Number(5);
  fixture.variables["zg361_b1_quota_recount_bottom"] = Number(1);
  return fixture;
}

bool Check(bool value, const char *message) {
  if (!value) std::cerr << message << '\n';
  return value;
}

} // namespace

int main() {
  xar::ck3_11906::ZhongguoB1CycleSnapshotRequestV1 parsed{};
  bool ok = Check(
      xar::ck3_11906::ParseZhongguoB1CycleSnapshotRequestV1(
          R"({"request_nonce":"portable-1","expected_revision":77})",
          parsed) &&
          parsed.request_nonce == "portable-1" &&
          parsed.expected_snapshot_revision == 77,
      "portable request did not parse");
  ok &= Check(
      !xar::ck3_11906::ParseZhongguoB1CycleSnapshotRequestV1(
          R"({"request_nonce":"portable-1","expected_revision":77,"manager_character_id":100})",
          parsed) &&
          !xar::ck3_11906::ParseZhongguoB1CycleSnapshotRequestV1(
              R"({"request_nonce":"portable-1","expected_revision":77,"variable_name":"anything"})",
              parsed),
      "request accepted caller identity or arbitrary variable name");
  auto environment =
      xar::ck3_11906::BindZhongguoB1CycleNativeEnvironmentV1(0, true);
  environment.offline_fixture_function_overrides = true;
  xar::ck3_11906::ZhongguoB1CycleAccessV1 access{};
  auto fixture = Complete();
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &Main;
  access.validate_character = &Character;
  access.read_allowlisted_variable = &Variable;
  xar::ck3_11906::ZhongguoB1CycleSnapshotRequestV1 request{77, "portable-1"};
  xar::game::ZhongguoB1CycleSnapshotV1 result{};
  const auto read = xar::ck3_11906::ReadZhongguoB1CycleSnapshotV1(
      environment, access, request, result);
  ok &= Check(
      read == xar::game::ReadZhongguoB1CycleSnapshotResultV1::available,
      "complete fixture unavailable");
  ok &= Check(result.manager_character_id == 100 && result.readiness.ready,
              "played manager was not bound");
  ok &= Check(result.cycle.active.value == true &&
                  result.quota.rebuild_generation.value == 1,
              "projection lost cycle facts");
  const auto json =
      xar::ck3_11906::SerializeZhongguoB1CycleSnapshotV1(result);
  ok &= Check(json.find("\"manager_character_id\":100") != std::string::npos &&
                  json.find("\"rebuild_generation\"") != std::string::npos &&
                  json.find("variable_name") == std::string::npos,
              "serialized projection is not closed");

  fixture = Complete();
  fixture.variables.erase("zg361_b1_quota_recount_top");
  result = {};
  const auto partial = xar::ck3_11906::ReadZhongguoB1CycleSnapshotV1(
      environment, access, request, result);
  ok &= Check(
      partial == xar::game::ReadZhongguoB1CycleSnapshotResultV1::available &&
          !result.quota.recount_top.available &&
          result.quota.recount_top.unavailable_reason == "variable_absent" &&
          !result.readiness.quota_ready &&
          !xar::ck3_11906::SerializeZhongguoB1CycleSnapshotV1(result).empty(),
      "partial lifecycle data was not preserved as typed unavailable");

  fixture = Complete();
  fixture.variables.erase("zg361_b1_manager_cycle_serial");
  fixture.variables.erase("zg361_b1_manager_case_serial");
  fixture.variables.erase("zg361_b1_cycle_state");
  result = {};
  const auto missing = xar::ck3_11906::ReadZhongguoB1CycleSnapshotV1(
      environment, access, request, result);
  ok &= Check(
      missing == xar::game::ReadZhongguoB1CycleSnapshotResultV1::unavailable &&
          result.unavailable_reason == "cycle_not_found" &&
          !result.cycle.cycle_serial.available &&
          !xar::ck3_11906::SerializeZhongguoB1CycleSnapshotV1(result).empty(),
      "missing cycle did not produce a typed unavailable snapshot");

  fixture = Complete();
  fixture.mutate_second = true;
  result = {};
  const auto changed = xar::ck3_11906::ReadZhongguoB1CycleSnapshotV1(
      environment, access, request, result);
  ok &= Check(
      changed == xar::game::ReadZhongguoB1CycleSnapshotResultV1::unavailable &&
          result.unavailable_reason == "state_changed",
      "same-frame double read did not reject mutation");

  return ok ? 0 : 1;
}
