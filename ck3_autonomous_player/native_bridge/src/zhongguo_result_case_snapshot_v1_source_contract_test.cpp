#include <array>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <string_view>

namespace {

std::string ReadFile(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool Contains(std::string_view value, std::string_view token) {
  return value.find(token) != std::string_view::npos;
}

std::size_t Count(std::string_view value, std::string_view token) {
  std::size_t count = 0;
  std::size_t cursor = 0;
  while ((cursor = value.find(token, cursor)) != std::string_view::npos) {
    ++count;
    cursor += token.size();
  }
  return count;
}

bool HasAll(std::string_view value,
            std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (!Contains(value, token)) return false;
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 12) {
    std::cerr << "expected eleven source-contract paths\n";
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
  const auto effects = ReadFile(argv[10]);
  const auto events = ReadFile(argv[11]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      mailbox.empty() || adapter.empty() || game_adapter.empty() ||
      bridge.empty() || abi.empty() || fixture.empty() || effects.empty() ||
      events.empty()) {
    std::cerr << "source-contract input is missing\n";
    return 1;
  }

  constexpr std::array<std::string_view, 13> allowlist{
      "zg361_result_case_owner",
      "zg361_result_cycle_serial",
      "zg361_result_case_serial",
      "zg361_result_case_state",
      "zg361_result_grade",
      "zg361_result_absolute_grade",
      "zg361_result_kpi_frozen",
      "zg361_result_rank_frozen",
      "zg361_result_cohort_n_frozen",
      "zg361_result_delivery_method",
      "zg361_result_objection_recorded",
      "zg361_result_settlement_posted_serial",
      "zg361_result_appeal_open",
  };
  for (const auto key : allowlist) {
    if (Count(header, key) != 1 || Count(fixture, key) != 1 ||
        !Contains(abi, key) || !Contains(effects, key)) {
      std::cerr << "allowlist identity mismatch: " << key << '\n';
      return 1;
    }
  }
  const auto require_tokens = [](std::string_view source,
                                 std::initializer_list<std::string_view> tokens,
                                 std::string_view label) {
    if (HasAll(source, tokens)) return true;
    std::cerr << "result-case source contract token mismatch: " << label
              << '\n';
    return false;
  };
  if (!require_tokens(
          header,
          {"std::array<std::string_view, 13>",
           "zhongguo.result.received-self",
           "game.command.query-zhongguo-result-case-snapshot-v1",
           "kpi_frozen_q100000"},
          "header") ||
      !require_tokens(
          reader,
          {"before.played_character_id", "first != second",
           "actual_owner == before.played_character_id",
           "actual_owner != request.owner_character_id", "DecodeQ100000",
           "objection_recorded, true"},
          "reader") ||
      !require_tokens(serializer,
                      {"player_subject_binding_ready", "owner_binding_ready",
                       "case_inconsistent", "not_received_self"},
                      "serializer") ||
      !require_tokens(
          mailbox,
          {"HasExactControlFields", "subject_character_id", "case_kind",
           "variable_name",
           "ExecuteZhongguoResultCaseSnapshotMailboxQueryV1"},
          "mailbox") ||
      !require_tokens(adapter,
                      {"std::array<std::string_view, 70>",
                       "kZhongguoResultCaseSnapshotV1Capability"},
                      "adapter") ||
      !require_tokens(game_adapter,
                      {"ParseZhongguoResultCaseSnapshotV1Step",
                       "kZhongguoResultCaseSnapshotV1Capability"},
                      "game_adapter") ||
      !require_tokens(
          bridge,
          {"permitted_executor_quindenary",
           "ZhongguoResultCaseSnapshotResultFrame",
           "zhongguo_result_case_snapshot_query_sequence",
           "zhongguo_result_case_snapshot"},
          "bridge") ||
      !require_tokens(
          abi,
          {"paused_played_character_only", "zg361_notice_prompt_owner",
           "compare_manager_case_serial_to_result_case_serial\": false",
           "production_live_acceptance"},
          "abi") ||
      !require_tokens(
          fixture,
          {"\"allowlist_count\": 13",
           "\"mailbox_fixed_slot\": \"permitted_executor_quindenary\"",
           "\"readiness\": \"static_and_fixture_ready_not_live\""},
          "fixture") ||
      !require_tokens(events,
                      {"zg361.50 =", "scope:zg361_notice_prompt_owner",
                       "save_scope_as = zg361_reviewing_superior"},
                      "events")) {
    return 1;
  }
  const std::string combined = header + reader + serializer + mailbox + abi +
                               fixture;
  if (Contains(combined, "zg361_b1_") ||
      Count(fixture, "zg361_result_") != allowlist.size()) {
    std::cerr << "result-case source contract escaped its fixed allowlist\n";
    return 1;
  }
  return 0;
}
