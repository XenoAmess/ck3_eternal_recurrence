#include "xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1.hpp"

#include <cstddef>
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

bool RequireTokens(std::string_view source,
                   std::initializer_list<std::string_view> tokens,
                   std::string_view label) {
  for (const auto token : tokens) {
    if (!Contains(source, token)) {
      std::cerr << "Workforce normal-exit source-contract token mismatch: "
                << label << " -> " << token << '\n';
      return false;
    }
  }
  return true;
}

} // namespace

int main(int argc, char **argv) {
  using namespace xar::ck3_11906;

  static_assert(kZhongguoWorkforceNormalExitVariableAllowlist.size() == 94);
  static_assert(kZhongguoVariableContextForScopeRva == 0x3329A40);
  static_assert(kZhongguoVariableIdentifierTableRva == 0x3B971A0);
  static_assert(kZhongguoVariableIdentifierLookupRva == 0x3B97020);
  static_assert(kZhongguoVariableIdentifierNameRva == 0x3B97090);
  static_assert(kZhongguoCharacterStorageSlotRva == 0x570C130);
  static_assert(kZhongguoCharacterFallbackSlotRva == 0x570C138);
  static_assert(
      kZhongguoWorkforceNormalExitSnapshotV1Capability ==
      "game.command.query-zhongguo-workforce-normal-exit-snapshot-v1");
  static_assert(kZhongguoWorkforceNormalExitSnapshotV1Step ==
                "query-zhongguo-workforce-normal-exit-snapshot-v1");
  static_assert(kZhongguoWorkforceNormalExitSnapshotV1CaseKind ==
                "zhongguo.workforce.normal-exit.received-self");

  if (argc != 13) {
    std::cerr << "expected twelve Workforce normal-exit source-contract paths\n";
    return 1;
  }
  const auto header = ReadFile(argv[1]);
  const auto reader = ReadFile(argv[2]);
  const auto serializer = ReadFile(argv[3]);
  const auto mailbox = ReadFile(argv[4]);
  const auto adapter = ReadFile(argv[5]);
  const auto bridge = ReadFile(argv[6]);
  const auto abi = ReadFile(argv[7]);
  const auto fixture = ReadFile(argv[8]);
  const auto documentation = ReadFile(argv[9]);
  const auto normal_exit_product = ReadFile(argv[10]);
  const auto rehire_product = ReadFile(argv[11]);
  const auto b2_product = ReadFile(argv[12]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      mailbox.empty() || adapter.empty() || bridge.empty() || abi.empty() ||
      fixture.empty() || documentation.empty() || normal_exit_product.empty() ||
      rehire_product.empty() || b2_product.empty()) {
    std::cerr << "Workforce normal-exit source-contract input is missing\n";
    return 1;
  }

  // The header is the sole canonical name ledger.  Each key must be unique
  // there and must also be emitted or consumed by its owning product source.
  for (std::size_t index = 0;
       index < kZhongguoWorkforceNormalExitVariableAllowlist.size(); ++index) {
    const auto key = kZhongguoWorkforceNormalExitVariableAllowlist[index];
    for (std::size_t earlier = 0; earlier < index; ++earlier) {
      if (key == kZhongguoWorkforceNormalExitVariableAllowlist[earlier]) {
        std::cerr << "duplicate Workforce normal-exit allowlist key: " << key
                  << '\n';
        return 1;
      }
    }
    const std::string quoted = "\"" + std::string(key) + "\"";
    if (Count(header, quoted) != 1) {
      std::cerr << "non-canonical Workforce normal-exit header key: " << key
                << '\n';
      return 1;
    }
    const std::string_view expected_product =
        index < 16 ? std::string_view{b2_product}
                   : index < 68 ? std::string_view{normal_exit_product}
                                : std::string_view{rehire_product};
    if (!Contains(expected_product, key)) {
      std::cerr << "Workforce normal-exit key has no owning product source: "
                << key << '\n';
      return 1;
    }
  }
  if (Count(header, "\"zg361_") != 94) {
    std::cerr << "Workforce normal-exit fixed allowlist cardinality drifted\n";
    return 1;
  }

  if (!RequireTokens(
          header,
          {"kZhongguoWorkforceNormalExitVariableAllowlist",
           "game.command.query-zhongguo-workforce-normal-exit-snapshot-v1",
           "query-zhongguo-workforce-normal-exit-snapshot-v1",
           "zhongguo.workforce.normal-exit.received-self",
           "expected_snapshot_revision", "owner_character_id",
           "request_nonce", "current_hc_matches_stage_ready"},
          "header") ||
      !RequireTokens(
          reader,
          {"EnvironmentIsExact", "ReadAllowlistedRows",
           "before.played_character_id", "first != second",
           "SourceCanonical", "PendingCanonical", "ReceiptCanonical",
           "RehireCanonical", "PartitionConserved", "MigrationValid",
           "WorkflowPendingAbsent", "ReceiptTouched", "RehireTouched",
           "ZhongguoWorkforceNormalExitLifecycleV1::pre",
           "ZhongguoWorkforceNormalExitLifecycleV1::migrating",
           "ZhongguoWorkforceNormalExitLifecycleV1::sealed",
           "ZhongguoWorkforceNormalExitLifecycleV1::rehire_captured",
           "ready.current_hc_matches_stage_ready =",
           "ready.ready = ready.player_subject_binding_ready &&",
           "ready.owner_binding_ready &&", "ready.lifecycle_ready &&",
           "ready.same_frame_ready", "case_not_found",
           "case_inconsistent", "not_received_self",
           "owner_filter_mismatch", "state_changed"},
          "reader") ||
      !RequireTokens(
          serializer,
          {"return \"pre\"", "return \"migrating\"", "return \"sealed\"",
           "return \"rehire_captured\"", "sealed_receipt_ready",
           "rehire_capture_ready", "current_hc_matches_stage_ready",
           "subject_allowlist_count", "owner_allowlist_count",
           "paused_received_self_workforce_normal_exit_lifecycle"},
          "serializer") ||
      !RequireTokens(
          mailbox,
          {"HasExactControlFields", "expected_revision",
           "owner_character_id", "request_nonce",
           "ParseZhongguoWorkforceNormalExitSnapshotRequestV1",
           "ExecuteZhongguoWorkforceNormalExitSnapshotMailboxQueryV1",
           "result.subject_character_id",
           "result.requested_owner_character_id", "typed_available",
           "typed_unavailable"},
          "mailbox") ||
      !RequireTokens(
          adapter,
          {"zhongguo_workforce_normal_exit_snapshot_v1.hpp",
           "kZhongguoWorkforceNormalExitSnapshotV1Capability"},
          "adapter") ||
      !RequireTokens(
          bridge,
          {"zhongguo_workforce_normal_exit_snapshot_v1_mailbox.hpp",
           "permitted_executor_unvigintary",
           "ExecuteZhongguoWorkforceNormalExitSnapshotMailboxQueryV1",
           "ZhongguoWorkforceNormalExitSnapshotResultFrame",
           "zhongguo_workforce_normal_exit_snapshot_query_sequence",
           "zhongguo_workforce_normal_exit_snapshot"},
          "bridge") ||
      !RequireTokens(
          abi,
          {"\"total_count\": 94", "\"owner_scope_count\": 0",
           "\"name\": \"m075_source\"", "\"count\": 16",
           "\"name\": \"normal_exit_workflow\"", "\"count\": 14",
           "\"name\": \"live_hc\"", "\"count\": 8",
           "\"name\": \"sealed_receipt\"", "\"count\": 30",
           "\"name\": \"rehire_capture\"", "\"count\": 26",
           "immutable_receipt", "current_match", "independent_readiness",
           "played_character_only", "not_live"},
          "ABI") ||
      !RequireTokens(
          fixture,
          {"\"allowlist_count\": 94", "\"m075_source\": 16",
           "\"normal_exit_workflow\": 14", "\"live_hc\": 8",
           "\"sealed_receipt\": 30", "\"rehire_capture\": 26",
           "\"owner_scope_reads\": 0", "paused_played_character_only",
           "highest_complete_stage_wins", "partial_higher_stage",
           "immutable_receipt_independent_of_later_live_hc",
           "live_match_is_independent_readiness", "not_live"},
          "fixture") ||
      !RequireTokens(
          documentation,
          {"static-ready + fixture-ready", "not-live", "MCP-first",
           "game.command.query-zhongguo-workforce-normal-exit-snapshot-v1",
           "request_nonce", "expected_revision", "owner_character_id",
           "played_character_id", "owner_scope_reads=0",
           "permitted_executor_unvigintary", "m075_source",
           "normal_exit_workflow", "live_hc", "sealed_receipt",
           "rehire_capture", "pre", "migrating", "sealed",
           "rehire_captured", "current_hc_matches_stage_ready", "OCR",
           "evidence_status=static_fixture_only_not_live"},
          "documentation") ||
      !RequireTokens(
          normal_exit_product,
          {"zg361_workforce_normal_exit_fact_audit_hc_then_finalize_receipt_effect",
           "pending_hc_occupied_before subtract = 1",
           "pending_hc_frozen_before add = 1",
           "receipt_hc_ledger_settled value = 1",
           "receipt_hc_destination_frozen value = 1",
           "receipt_hc_conservation_verified value = 1",
           "receipt_formal_hc_active_before value = 1",
           "receipt_formal_hc_active_after value = 0"},
          "normal-exit product") ||
      !RequireTokens(
          rehire_product,
          {"zg361_workforce_rehire_fact_exit_receipt_id value = var:zg361_workforce_normal_exit_fact_receipt_id",
           "zg361_workforce_rehire_fact_exit_receipt_hash value = var:zg361_workforce_normal_exit_fact_receipt_hash",
           "zg361_workforce_rehire_fact_exit_hc_authorized_before value = var:zg361_workforce_normal_exit_fact_receipt_hc_authorized_before",
           "zg361_workforce_rehire_fact_exit_hc_authorized_after value = var:zg361_workforce_normal_exit_fact_receipt_hc_authorized_after",
           "zg361_workforce_rehire_fact_exit_formal_hc_case value = var:zg361_workforce_normal_exit_fact_receipt_formal_hc_case",
           "zg361_workforce_rehire_fact_normal_exit_verified value = 1"},
          "rehire product") ||
      !RequireTokens(
          b2_product,
          {"zg361_b2_m075_open_business_object_effect",
           "zg361_b2_m075_consume_business_object_effect",
           "zg361_b2_m075_object_owner",
           "zg361_b2_m075_object_subject",
           "zg361_b2_m075_object_active value = 0",
           "zg361_b2_m075_object_consumed value = 1",
           "zg361_b2_m075_consumer_receipt_case"},
          "B2 product")) {
    return 1;
  }

  if (Count(reader,
            "ReadAllowlistedRows(environment, access, before.played_character_id") !=
          2 ||
      Contains(header, "WorkforceNormalExitOwnerVariableAllowlist") ||
      Contains(reader,
               "ReadAllowlistedRows(environment, access, request.owner_character_id") ||
      Contains(abi, "\"owner_scope_count\": 1") ||
      Contains(fixture, "\"owner_scope_reads\": 1")) {
    std::cerr << "Workforce normal-exit source contract escaped player scope\n";
    return 1;
  }

  const std::string combined = abi + fixture + documentation;
  if (Contains(combined, "\"production_live_acceptance\": true") ||
      Contains(combined, "\"mcp_query_live\": true") ||
      Contains(combined, "\"ck3_loader_live\": true") ||
      Contains(combined, "\"live_artifact\": {") ||
      Contains(combined, "production-live acceptance complete") ||
      Contains(documentation, "evidence_status=production_live") ||
      Contains(documentation, "live_acceptance_complete=true")) {
    std::cerr << "Workforce normal-exit source contract made a live claim\n";
    return 1;
  }
  return 0;
}
