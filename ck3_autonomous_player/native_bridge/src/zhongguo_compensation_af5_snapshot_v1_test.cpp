#include "xar_bridge/zhongguo_compensation_af5_snapshot_v1_mailbox.hpp"

#include <cassert>
#include <iostream>
#include <map>
#include <string>
#include <utility>

namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &, game::Snapshot &) noexcept { return false; }
} // namespace xar::ck3_11906

namespace {
using namespace xar::ck3_11906;
using Raw = ZhongguoRawVariableV1;
struct Fixture {
  xar::game::ZhongguoCaseFrameV1 frame{41, 1066123, true, true, true, true, 200};
  std::map<std::pair<std::int32_t, std::string>, Raw> variables;
};

Raw Number(std::int64_t value) { return {true, 1, value * 100'000}; }
Raw Character(std::int64_t value) { return {true, 4, value}; }
bool Capture(void *opaque, xar::game::ZhongguoCaseFrameV1 &out) noexcept {
  out = static_cast<Fixture *>(opaque)->frame;
  return true;
}
bool MainThread(void *) noexcept { return true; }
bool ValidateCharacter(void *, std::int32_t id) noexcept {
  return id == 100 || id == 200;
}
bool ReadVariable(void *opaque, std::int32_t id, std::string_view key,
                  Raw &out) noexcept {
  const auto &values = static_cast<Fixture *>(opaque)->variables;
  const auto it = values.find({id, std::string(key)});
  out = it == values.end() ? Raw{} : it->second;
  return true;
}

void Populate(Fixture &f, bool closed) {
  auto set = [&](int id, std::string key, Raw value) {
    f.variables[{id, std::move(key)}] = value;
  };
  set(200, "zg361_comp_portfolio_domain", Number(closed ? 4 : 3));
  set(200, "zg361_comp_portfolio_stage", Number(5));
  set(200, "zg361_comp_portfolio_visible_pending", Number(closed ? 0 : 1));
  set(200, "zg361_comp_portfolio_subject", Character(100));
  set(200, "zg361_comp_portfolio_result_owner", Character(200));
  set(200, "zg361_comp_portfolio_result_subject", Character(100));
  set(200, "zg361_comp_portfolio_result_cycle", Number(7));
  set(200, "zg361_comp_portfolio_result_case", Number(14));
  set(100, "zg361_case_af_owner", Character(200));
  set(100, "zg361_case_af_subject", Character(100));
  set(100, "zg361_case_af_cycle_serial", Number(7));
  set(100, "zg361_case_af_case_serial", Number(214));
  set(100, "zg361_case_af_revision", Number(closed ? 20 : 18));
  set(100, "zg361_comp_result_case", Number(14));
  set(100, "zg361_case_af_state", Number(closed ? 6 : 5));
  set(100, "zg361_case_af_active", Number(closed ? 0 : 1));
  set(100, "zg361_comp_af_last_operation", Number(closed ? 300 : 298));
  set(100, "zg361_comp_af_last_route", Number(closed ? 3 : 1));
  set(100, "zg361_comp_af_repurchase_resolved", Number(closed ? 1 : 0));
  set(100, "zg361_comp_af_unit_conserved", Number(1));
  if (!closed) return;
  for (int operation : {299, 300}) {
    const auto prefix = "zg361_comp_m" + std::to_string(operation);
    set(100, prefix + "_receipt_owner", Character(200));
    set(100, prefix + "_receipt_subject", Character(100));
    set(100, prefix + "_receipt_cycle", Number(7));
    set(100, prefix + "_receipt_case", Number(214));
    set(100, prefix + "_receipt_state", Number(5));
    set(100, prefix + "_receipt_active", Number(1));
    set(100, prefix + "_consumed", Number(1));
    set(100, prefix + "_receipt_route", Number(3));
  }
}

xar::game::ZhongguoCompensationAf5SnapshotV1 Read(Fixture &f) {
  ZhongguoCompensationAf5NativeEnvironmentV1 env{};
  env.exact_build_admitted = true;
  env.offline_fixture_function_overrides = true;
  ZhongguoCompensationAf5AccessV1 access{};
  access.context = &f;
  access.capture_frame = &Capture;
  access.is_main_thread = &MainThread;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  xar::game::ZhongguoCompensationAf5SnapshotV1 out{};
  const auto original = f.variables;
  assert(ReadZhongguoCompensationAf5SnapshotV1(env, access, {41, "af5-fixture"}, out) ==
         xar::game::ReadZhongguoCompensationAf5ResultV1::available);
  assert(f.variables == original);
  return out;
}
} // namespace

int main(int argc, char **argv) {
  using namespace xar::ck3_11906;
  Fixture f;
  Populate(f, false);
  auto out = Read(f);
  assert(out.readiness.ready && !out.terminal);
  assert(!out.m299.active.available && !out.m300.active.available);
  assert(out.af_case.identity.case_serial.value == 214);
  assert(out.portfolio.result_identity.case_serial.value == 14);
  Populate(f, true);
  out = Read(f);
  assert(out.readiness.ready && out.terminal);
  assert(out.portfolio.domain.value == 4);
  // Next-day cursor cleanup and a cold restore retain the result subject.
  f.variables.erase({200, "zg361_comp_portfolio_domain"});
  f.variables.erase({200, "zg361_comp_portfolio_stage"});
  f.variables.erase({200, "zg361_comp_portfolio_subject"});
  f.variables[{200, "zg361_comp_portfolio_completed_cycle"}] = Number(7);
  out = Read(f);
  assert(out.readiness.ready && out.terminal);
  assert(!out.portfolio.domain.available && !out.portfolio.stage.available);
  const auto serialized = SerializeZhongguoCompensationAf5SnapshotV1(out);
  assert(serialized.find("\"terminal\":true") != std::string::npos);
  assert(serialized.find("\"result_case_serial\":{\"status\":\"available\",\"value\":14") !=
         std::string::npos);
  if (argc == 2 && std::string_view(argv[1]) == "--json")
    std::cout << serialized << '\n';
  // A receipt from another AF case is readable but cannot prove this terminal.
  f.variables[{100, "zg361_comp_m300_receipt_case"}] = Number(215);
  out = Read(f);
  assert(out.readiness.ready && !out.terminal);
  ZhongguoCompensationAf5RequestV1 request{};
  std::int32_t owner = -1;
  assert(ParseZhongguoCompensationAf5SnapshotRequestV1(
      R"({"type":"execute_step","protocol_version":1,"request_id":"af5-test","step":"query-zhongguo-compensation-af5-snapshot-v1","expected_revision":41,"owner_character_id":200,"request_nonce":"af5-fixture"})",
      request, owner));
  assert(owner == 200 && request.expected_snapshot_revision == 41);
  assert(ParseZhongguoCompensationAf5SnapshotV1Step(kZhongguoCompensationAf5SnapshotV1Step));
  return 0;
}
