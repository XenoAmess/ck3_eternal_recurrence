#include "xar_bridge/zhongguo_ai_owned_case_snapshot_v1.hpp"

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

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

bool ContainsAll(std::string_view value,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (!Contains(value, token)) return false;
  }
  return true;
}

bool ConstantsMatch() {
  using namespace xar::ck3_11906;
  return kZhongguoAiOwnedCaseSnapshotV1Capability ==
             "game.command.query-zhongguo-ai-owned-case-snapshot-v1" &&
         kZhongguoAiOwnedCaseSnapshotV1Step ==
             "query-zhongguo-ai-owned-case-snapshot-v1" &&
         kZhongguoAiOwnedCaseSnapshotV1CaseKind ==
             "zhongguo.b1.performance" &&
         kZhongguoAiOwnedCaseSnapshotV1VariableAllowlist.size() == 17 &&
         kZhongguoAiCasePrimaryTitleRva == 0x25F3350 &&
         kZhongguoAiCaseImmediateLiegeRva == 0x2613480 &&
         kZhongguoAiCaseGovernmentRva == 0x26165B0 &&
         kZhongguoAiCaseIsHumanPlayerRva == 0x28BCEB0;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 12 || !ConstantsMatch()) return 1;
  const auto header = ReadFile(argv[1]);
  const auto reader = ReadFile(argv[2]);
  const auto serializer = ReadFile(argv[3]);
  const auto mailbox = ReadFile(argv[4]);
  const auto adapter = ReadFile(argv[5]);
  const auto game_adapter = ReadFile(argv[6]);
  const auto bridge = ReadFile(argv[7]);
  const auto abi = ReadFile(argv[8]);
  const auto fixture = ReadFile(argv[9]);
  const auto documentation = ReadFile(argv[10]);
  const auto product = ReadFile(argv[11]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      mailbox.empty() || adapter.empty() || game_adapter.empty() ||
      bridge.empty() || abi.empty() || fixture.empty() ||
      documentation.empty() || product.empty()) {
    return 1;
  }

  const bool ok =
      ContainsAll(
          header,
          {"std::array<std::string_view, 17>",
           "zg361_b1_roster_lock_receipt_choice",
           "ZhongguoAiOwnerEligibilityV1",
           "ZhongguoAiOwnedCaseRouteV1",
           "authorized_ai_background"}) &&
      ContainsAll(
          reader,
          {"request.owner_character_id == before.played_character_id",
           "owner_is_played_character", "owner_not_ai",
           "owner_not_celestial", "owner_not_landed_duke_plus",
           "subject_not_direct_subject", "celestial_government",
           "first_eligibility != second_eligibility",
           "first_rows != second_rows", "case_not_found",
           "stage_inconsistent", "mechanism_039", "roster_lock",
           "receipt_not_recorded", "receipt_inconsistent"}) &&
      ContainsAll(
          serializer,
          {"owner_eligibility", "visible_event_allowed",
           "owner_eligibility_ready", "primary_title_rva",
           "immediate_liege_rva", "government_rva",
           "is_human_player_rva"}) &&
      ContainsAll(
          mailbox,
          {"ParseZhongguoAiOwnedCaseSnapshotRequestV1",
           "HasOnlyAllowlistedRequestFields",
           "ExecuteZhongguoAiOwnedCaseSnapshotMailboxQueryV1",
           "typed_available", "typed_unavailable"}) &&
      ContainsAll(
          adapter,
          {"constexpr std::size_t kCapabilityCount = 76",
           "kZhongguoAiOwnedCaseSnapshotV1Capability"}) &&
      ContainsAll(
          game_adapter,
          {"ParseZhongguoAiOwnedCaseSnapshotV1Step",
           "kZhongguoAiOwnedCaseSnapshotV1Capability"}) &&
      ContainsAll(
          bridge,
          {"permitted_executor_vigintary",
           "ExecuteZhongguoAiOwnedCaseSnapshotMailboxQueryV1",
           "ZhongguoAiOwnedCaseSnapshotResultFrame",
           "zhongguo_ai_owned_case_snapshot_query_sequence",
           "zhongguo_ai_owned_case_snapshot"}) &&
      ContainsAll(
          abi,
          {"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
           "\"allowlist_count\": 17", "\"mailbox_fixed_slot\"",
           "permitted_executor_vigintary",
           "\"evidence_level\": \"static_fixture_only\"",
           "\"live_artifact\": null"}) &&
      ContainsAll(
          fixture,
          {"\"allowlist_count\": 17", "unknown_field",
           "authorized_ai_duchy_recorded_roster_lock_receipt",
           "authorized_ai_hegemony_published_not_recorded_receipt",
           "player_owner_rejected_before_variable_read",
           "stage_active_mismatch_available_but_not_ready",
           "production_live_claim"}) &&
      ContainsAll(
          documentation,
          {"static-ready / fixture-ready / live-unverified",
           "authorized_ai_background", "语义投影", "不得宣称",
           "0x2613480", "0x26165B0"}) &&
      ContainsAll(
          product,
          {"zg361_b1_case_owner", "zg361_b1_case_subject",
           "zg361_b1_case_state", "zg361_b1_case_active",
           "zg361_b1_roster_lock_receipt_owner",
           "zg361_b1_roster_lock_receipt_choice"});
  if (!ok) {
    std::cerr << "ZhongGuo AI-owned case source contract failed\n";
    return 1;
  }
  return 0;
}
