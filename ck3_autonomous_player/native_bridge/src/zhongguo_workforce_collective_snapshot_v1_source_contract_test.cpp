#include "xar_bridge/zhongguo_workforce_collective_snapshot_v1.hpp"

#include <cstdint>
#include <fstream>
#include <initializer_list>
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

bool RequireTokens(std::string_view source,
                   std::initializer_list<std::string_view> tokens,
                   std::string_view label) {
  if (HasAll(source, tokens)) return true;
  std::cerr << "Workforce source-contract token mismatch: " << label << '\n';
  return false;
}

} // namespace

int main(int argc, char **argv) {
  using namespace xar::ck3_11906;

  static_assert(kZhongguoWorkforceSubjectVariableAllowlist.size() == 144);
  static_assert(kZhongguoWorkforceOwnerVariableAllowlist.size() == 31);
  static_assert(kZhongguoVariableContextForScopeRva == 0x3329A40);
  static_assert(kZhongguoVariableIdentifierTableRva == 0x3B971A0);
  static_assert(kZhongguoVariableIdentifierLookupRva == 0x3B97020);
  static_assert(kZhongguoVariableIdentifierNameRva == 0x3B97090);
  static_assert(kZhongguoCharacterStorageSlotRva == 0x570C130);
  static_assert(kZhongguoCharacterFallbackSlotRva == 0x570C138);
  static_assert(kZhongguoWorkforceCollectiveSnapshotV1Capability ==
                "game.command.query-zhongguo-workforce-collective-snapshot-v1");
  static_assert(kZhongguoWorkforceCollectiveSnapshotV1Step ==
                "query-zhongguo-workforce-collective-snapshot-v1");
  static_assert(kZhongguoWorkforceCollectiveSnapshotV1CaseKind ==
                "zhongguo.workforce-collective");

  if (argc != 8) {
    std::cerr << "expected seven source-contract paths\n";
    return 1;
  }
  const auto header = ReadFile(argv[1]);
  const auto reader = ReadFile(argv[2]);
  const auto serializer = ReadFile(argv[3]);
  const auto mailbox = ReadFile(argv[4]);
  const auto abi = ReadFile(argv[5]);
  const auto fixture = ReadFile(argv[6]);
  const auto documentation = ReadFile(argv[7]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      mailbox.empty() || abi.empty() || fixture.empty() ||
      documentation.empty()) {
    std::cerr << "Workforce source-contract input is missing\n";
    return 1;
  }

  const auto verify_allowlist = [&](const auto &allowlist,
                                    std::string_view label) {
    for (const auto key : allowlist) {
      const std::string quoted = "\"" + std::string(key) + "\"";
      if (Count(header, quoted) != 1 || Count(abi, quoted) != 1 ||
          Count(fixture, quoted) != 1) {
        std::cerr << label << " allowlist identity mismatch: " << key << '\n';
        return false;
      }
    }
    return true;
  };
  if (!verify_allowlist(kZhongguoWorkforceSubjectVariableAllowlist,
                        "subject") ||
      !verify_allowlist(kZhongguoWorkforceOwnerVariableAllowlist, "owner") ||
      Count(header, "\"zg361_") != 175 ||
      Count(abi, "\"zg361_") != 175 ||
      Count(fixture, "\"zg361_") != 175) {
    std::cerr << "Workforce fixed allowlist cardinality mismatch\n";
    return 1;
  }

  if (!RequireTokens(
          header,
          {"kZhongguoWorkforceSubjectVariableAllowlist",
           "kZhongguoWorkforceOwnerVariableAllowlist",
           "game.command.query-zhongguo-workforce-collective-snapshot-v1",
           "query-zhongguo-workforce-collective-snapshot-v1",
           "zhongguo.workforce-collective",
           "expected_snapshot_revision", "owner_character_id",
           "request_nonce"},
          "header") ||
      !RequireTokens(
          reader,
          {"EnvironmentIsExact", "kZhongguoVariableContextForScopeRva",
           "kZhongguoVariableIdentifierTableRva",
           "kZhongguoVariableIdentifierLookupRva",
           "kZhongguoVariableIdentifierNameRva",
           "kZhongguoCharacterStorageSlotRva",
           "kZhongguoCharacterFallbackSlotRva",
           "before.played_character_id", "ReadAllowlistedRows",
           "subject_first != subject_second",
           "owner_first != owner_second", "owner_filter_mismatch",
           "ReceiptFieldsPresent", "ReceiptFieldsAbsent", "ReceiptMatches",
           "Integer(value.cohort_count) == 3", "quota >= 1 && quota <= 6",
           "FrozenEvidenceMatchesHistory", "collective_inconsistent",
           "history_inconsistent", "state_changed"},
          "reader") ||
      !RequireTokens(
          serializer,
          {"effective_count", "route_c_debt", "charter_gate",
           "subject_allowlist_count", "owner_allowlist_count",
           "0x3329A40", "0x3B971A0", "0x3B97020", "0x3B97090",
           "0x570C130",
           "paused_received_self_al_case_plus_owner_rolling_three_cycle"},
          "serializer") ||
      !RequireTokens(
          mailbox,
          {"HasExactControlFields", "expected_revision",
           "owner_character_id", "request_nonce",
           "ExecuteZhongguoWorkforceCollectiveSnapshotMailboxQueryV1",
           "result.subject_character_id",
           "result.requested_owner_character_id"},
          "mailbox") ||
      !RequireTokens(
          abi,
          {"\"status\": \"static_and_fixture_ready_not_live\"",
           "\"subject_allowlist_count\": 144",
           "\"owner_allowlist_count\": 31",
           "paused_played_character_only", "permitted_executor_novemdenary",
           "subject_allowlist_first", "owner_allowlist_first",
           "subject_rows_first_second_equal", "owner_rows_first_second_equal",
           "0x3329A40", "0x3B971A0", "0x3B97020", "0x3B97090",
           "0x570C130", "0x570C138",
           "arbitrary_character_variable_reader",
           "write_or_action_provider", "production_live_acceptance"},
          "ABI") ||
      !RequireTokens(
          fixture,
          {"\"readiness\": \"static_and_fixture_ready_not_live\"",
           "\"subject_allowlist_count\": 144",
           "\"owner_allowlist_count\": 31",
           "\"mailbox_fixed_slot\": \"permitted_executor_novemdenary\"",
           "paused_played_character_is_only_subject",
           "request_has_no_subject_variable_name_or_action",
           "prepared_m361_evidence_slots_mirror_owner_history_slots",
           "provider_is_read_only", "OCR"},
          "fixture") ||
      !RequireTokens(
          documentation,
          {"static-ready + fixture-ready", "not-live",
           "game.command.query-zhongguo-workforce-collective-snapshot-v1",
           "request_nonce", "expected_revision", "owner_character_id",
           "permitted_executor_novemdenary", "route_a_exception",
           "route_b_forced", "route_c_debt", "effective_count=0",
           "owner_filter_mismatch", "production-live primitive", "OCR"},
          "documentation")) {
    return 1;
  }

  const std::string combined = header + reader + serializer + mailbox + abi +
                               fixture + documentation;
  if (Contains(combined, "third_party_subject_query\": true") ||
      Contains(combined, "arbitrary_character_variable_reader\": true") ||
      Contains(combined, "write_or_action_provider\": true") ||
      Contains(combined, "game.command.execute-zhongguo-workforce") ||
      Contains(combined, "production-live acceptance complete") ||
      Contains(combined, "production_live_acceptance\": true")) {
    std::cerr << "Workforce source contract escaped its read-only boundary\n";
    return 1;
  }
  return 0;
}
