#include "xar_bridge/zhongguo_workforce_owner_snapshot_v1_mailbox.hpp"

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
  void Number(int id, std::string key, std::int64_t value) {
    variables[{id, std::move(key)}] = {true, 1, value * 100'000};
  }
  void Character(int id, std::string key, int value) {
    variables[{id, std::move(key)}] = {true, 4, value};
  }
};

bool Capture(void *opaque, xar::game::ZhongguoCaseFrameV1 &out) noexcept {
  out = static_cast<Fixture *>(opaque)->frame;
  return true;
}
bool MainThread(void *) noexcept { return true; }
bool ValidateCharacter(void *, std::int32_t id) noexcept { return id == 100 || id == 200; }
bool ReadVariable(void *opaque, std::int32_t id, std::string_view key, Raw &out) noexcept {
  const auto &values = static_cast<Fixture *>(opaque)->variables;
  const auto it = values.find({id, std::string(key)});
  out = it == values.end() ? Raw{} : it->second;
  return true;
}

void Populate(Fixture &f, int status) {
  f.variables.clear();
  f.Character(200, "zg361_p2c_subject", 100);
  f.Number(200, "zg361_p2c_cycle", 7);
  f.Number(200, "zg361_p2c_case_serial", 14);
  f.Number(200, "zg361_p2c_stage_11_status", status == 5 ? 5 : status == 7 ? 3 : 2);
  f.Character(100, "zg361_case_al_owner", 200);
  f.Character(100, "zg361_case_al_subject", 100);
  f.Number(100, "zg361_case_al_cycle_serial", 7);
  f.Number(100, "zg361_case_al_case_serial", 214);
  f.Number(100, "zg361_case_al_state", status == 5 ? 4 : 8);
  f.Number(100, "zg361_case_al_active", status == 5 ? 1 : 0);
  f.Number(100, "zg361_case_al_revision", status == 5 ? 18 : 20);
  f.Number(100, "zg361_we_portfolio_cycle", 7);
  f.Number(100, "zg361_we_portfolio_closed", status == 5 ? 0 : 1);
  f.Number(100, "zg361_we_portfolio_status", status);
  if (status != 5) f.Number(100, "zg361_we_final_conservation_ok", 1);
  if (status == 6) f.Number(100, "zg361_we_portfolio_terminal_success", 1);
  if (status == 8) {
    f.Number(100, "zg361_we_portfolio_terminal_history_accruing", 1);
    f.Number(100, "zg361_we_portfolio_history_cycle_count", 2);
    f.Number(100, "zg361_we_portfolio_terminal_owned_operations", 39);
    f.Number(100, "zg361_we_portfolio_terminal_skipped_charter", 1);
    f.Number(100, "zg361_we_portfolio_terminal_success", 0);
  }
  if (status == 7) {
    f.Number(100, "zg361_we_portfolio_terminal_na", 1);
    f.Number(100, "zg361_we_portfolio_terminal_reason", 360362);
    f.Number(100, "zg361_we_portfolio_terminal_owned_operations", 38);
    f.Number(100, "zg361_we_portfolio_terminal_skipped_manager_only", 2);
    f.Number(100, "zg361_we_portfolio_terminal_success", 0);
    return; // No manager-only M360 source or receipt on the N/A branch.
  }
  f.Number(200, "zg361_p2c_m360_source_status", status == 5 ? 1 : 2);
  f.Character(200, "zg361_p2c_m360_source_owner", 200);
  f.Character(200, "zg361_p2c_m360_source_subject", 100);
  f.Number(200, "zg361_p2c_m360_source_p2c_cycle", 7);
  f.Number(200, "zg361_p2c_m360_source_p2c_case", 14);
  f.Number(200, "zg361_p2c_m360_source_al_cycle", 7);
  f.Number(200, "zg361_p2c_m360_source_al_case", 214);
  if (status == 5) return;
  f.Character(100, "zg361_we_m360_receipt_owner", 200);
  f.Character(100, "zg361_we_m360_receipt_subject", 100);
  f.Number(100, "zg361_we_m360_receipt_cycle", 7);
  f.Number(100, "zg361_we_m360_receipt_case", 214);
  f.Number(100, "zg361_we_m360_receipt_state", 4);
  f.Number(100, "zg361_we_m360_receipt_choice", 1);
}

xar::game::ZhongguoWorkforceOwnerSnapshotV1 Read(Fixture &f) {
  ZhongguoWorkforceOwnerNativeEnvironmentV1 env{};
  env.exact_build_admitted = true;
  env.offline_fixture_function_overrides = true;
  ZhongguoWorkforceOwnerAccessV1 access{};
  access.context = &f;
  access.capture_frame = &Capture;
  access.is_main_thread = &MainThread;
  access.validate_character = &ValidateCharacter;
  access.read_allowlisted_variable = &ReadVariable;
  xar::game::ZhongguoWorkforceOwnerSnapshotV1 out{};
  const auto original = f.variables;
  assert(ReadZhongguoWorkforceOwnerSnapshotV1(env, access, {41, "workforce-owner-fixture"}, out) ==
         xar::game::ReadZhongguoWorkforceOwnerResultV1::available);
  assert(f.variables == original && f.frame.played_character_id == 200);
  assert(out.player_character_id == 200 && out.subject_character_id == 100);
  return out;
}
} // namespace

int main(int argc, char **argv) {
  using namespace xar::ck3_11906;
  Fixture f;
  Populate(f, 5);
  auto out = Read(f);
  assert(out.readiness.ready && !out.terminal && out.terminal_kind == "none");
  assert(!out.m360_receipt.choice.available && !out.portfolio.final_conservation_ok.available);
  Populate(f, 6);
  out = Read(f);
  assert(out.readiness.ready && out.terminal && out.terminal_kind == "success");
  Populate(f, 7);
  out = Read(f);
  assert(out.readiness.ready && out.terminal && out.terminal_kind == "not_applicable");
  assert(!out.source.owner_character_id.available && !out.m360_receipt.choice.available);
  Populate(f, 8);
  out = Read(f);
  assert(out.readiness.ready && out.terminal && out.terminal_kind == "history_accruing");
  const auto serialized = SerializeZhongguoWorkforceOwnerSnapshotV1(out);
  if (argc == 2 && std::string_view(argv[1]) == "--json") std::cout << serialized << '\n';
  // Missing the product-required charter skip cannot be labeled a terminal.
  f.variables.erase({100, "zg361_we_portfolio_terminal_skipped_charter"});
  out = Read(f);
  assert(out.readiness.ready && !out.terminal);
  ZhongguoWorkforceOwnerRequestV1 request{};
  std::int32_t owner = -1;
  assert(ParseZhongguoWorkforceOwnerSnapshotRequestV1(
      R"({"type":"execute_step","protocol_version":1,"request_id":"workforce-test","step":"query-zhongguo-workforce-owner-snapshot-v1","expected_revision":41,"owner_character_id":200,"request_nonce":"workforce-owner-fixture"})",
      request, owner));
  assert(owner == 200 && request.expected_snapshot_revision == 41);
  return 0;
}
