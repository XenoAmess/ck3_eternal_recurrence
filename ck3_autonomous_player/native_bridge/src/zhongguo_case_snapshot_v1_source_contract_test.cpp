#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <fstream>
#include <initializer_list>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>

namespace {

std::string ReadFile(const char *path) {
  std::ifstream stream(path, std::ios::binary);
  std::ostringstream output;
  output << stream.rdbuf();
  return output.str();
}

bool Contains(std::string_view haystack, std::string_view needle) {
  return haystack.find(needle) != std::string_view::npos;
}

bool ContainsAll(std::string_view value,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (!Contains(value, token)) return false;
  }
  return true;
}

bool TestConstants() {
  using namespace xar::ck3_11906;
  return kZhongguoCaseSnapshotV1Capability ==
             "game.command.query-zhongguo-case-snapshot-v1" &&
         kZhongguoCaseSnapshotV1Step ==
             "query-zhongguo-case-snapshot-v1" &&
         kZhongguoCaseSnapshotV1CaseKind ==
             "zhongguo.b1.performance" &&
         kZhongguoVariableContextForScopeRva == 0x3329A40 &&
         kZhongguoVariableIdentifierTableRva == 0x3B971A0 &&
         kZhongguoVariableIdentifierLookupRva == 0x3B97020 &&
         kZhongguoVariableIdentifierNameRva == 0x3B97090 &&
         kZhongguoCharacterStorageSlotRva == 0x570C130 &&
         kZhongguoCharacterFallbackSlotRva == 0x570C138 &&
         kZhongguoCaseSnapshotV1VariableAllowlist.size() == 26;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 11 || !TestConstants()) {
    return 1;
  }
  const auto header = ReadFile(argv[1]);
  const auto reader = ReadFile(argv[2]);
  const auto serializer = ReadFile(argv[3]);
  const auto mailbox = ReadFile(argv[4]);
  const auto adapter = ReadFile(argv[5]);
  const auto game_adapter = ReadFile(argv[6]);
  const auto bridge = ReadFile(argv[7]);
  const auto abi = ReadFile(argv[8]);
  const auto fixture = ReadFile(argv[9]);
  const auto product = ReadFile(argv[10]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      mailbox.empty() || adapter.empty() || game_adapter.empty() ||
      bridge.empty() || abi.empty() || fixture.empty() || product.empty()) {
    return 1;
  }

  const bool ok =
      ContainsAll(header,
                  {"kZhongguoCaseSnapshotV1VariableAllowlist",
                   "std::array<std::string_view, 26>",
                   "zg361_b1_pending_open_date",
                   "ZhongguoTypedIntegerV1 open_date_raw",
                   "ZhongguoTypedIntegerV1 due_date_raw"}) &&
      !Contains(header, "zg361_b1_pending_deadline_due_date") &&
      ContainsAll(reader,
                  {"kFixedScale = 100'000",
                   "raw.kind != 1",
                   "raw.kind != 4",
                   "ReadAllowlistedRows(environment, access",
                   "DecodePersistedDate",
                   "No exact-build evidence currently identifies",
                   "due_date_not_persisted_by_product",
                   "player_binding_mismatch",
                   "MakeReceiptUnavailable",
                   "MakeDeadlineUnavailable",
                   "if (operation_id == 0)",
                   "const bool deadline_reset",
                   "first != second"}) &&
      !Contains(reader, "open_date_raw.value +") &&
      ContainsAll(serializer,
                  {"open_date_raw", "due_date_raw",
                   "player_binding_mismatch",
                   "variable_context_for_scope_rva",
                   "kZhongguoCaseSnapshotV1AllowlistId"}) &&
      ContainsAll(mailbox,
                  {"ParseZhongguoCaseSnapshotRequestV1",
                   "ContainsForbiddenVariableAlias",
                   "ExecuteZhongguoCaseSnapshotMailboxQueryV1",
                   "typed_available", "typed_unavailable"}) &&
      ContainsAll(adapter,
                  {"kZhongguoCaseSnapshotV1Capability",
                   "kBaseCapabilityCount = 78",
                   "std::array<std::string_view, kCapabilityCount>"}) &&
      ContainsAll(game_adapter,
                  {"ParseZhongguoCaseSnapshotV1Step",
                   "kZhongguoCaseSnapshotV1Capability"}) &&
      ContainsAll(bridge,
                  {"permitted_executor_quattuordenary",
                   "ExecuteZhongguoCaseSnapshotMailboxQueryV1",
                   "ZhongguoCaseSnapshotResultFrame",
                   "zhongguo_case_snapshot_query_sequence",
                   "zhongguo_case_snapshot"}) &&
      ContainsAll(abi,
                  {"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
                   "\"fixed_variable_allowlist\"",
                   "\"date_event_target_kind\": null",
                   "\"due_date_variable\": null",
                   "\"readiness\": \"static_fixture_only\""}) &&
      ContainsAll(fixture,
                  {"\"fixed_allowlist_size\": 26",
                   "nonexistent_due_date_key_is_not_looked_up",
                   "pending_deadline_days_numeric_zero",
                   "canonical_request_and_forbidden_variable_aliases",
                   "production_live_claim"}) &&
      ContainsAll(product,
                  {"zg361_b1_pending_open_date",
                   "name = zg361_b1_case_last_operation value = 0",
                   "name = zg361_b1_pending_deadline_days value = 0"}) &&
      !Contains(product, "zg361_b1_pending_deadline_due_date");
  if (!ok) {
    std::cerr << "ZhongGuo case snapshot source contract failed\n";
    return 1;
  }
  return 0;
}
