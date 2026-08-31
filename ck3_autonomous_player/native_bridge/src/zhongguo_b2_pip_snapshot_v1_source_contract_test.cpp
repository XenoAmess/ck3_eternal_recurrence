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
  const auto producer = ReadFile(argv[10]);
  const auto documentation = ReadFile(argv[11]);
  if (header.empty() || reader.empty() || serializer.empty() ||
      mailbox.empty() || adapter.empty() || game_adapter.empty() ||
      bridge.empty() || abi.empty() || fixture.empty() || producer.empty() ||
      documentation.empty()) {
    std::cerr << "source-contract input is missing\n";
    return 1;
  }

  constexpr std::array<std::string_view, 73> subject_allowlist{
      "zg361_b2_pip_gate_owner",
      "zg361_b2_pip_gate_subject",
      "zg361_b2_pip_gate_cycle",
      "zg361_b2_pip_gate_case",
      "zg361_b2_pip_gate_threshold",
      "zg361_b2_pip_gate_component_count",
      "zg361_b2_pip_gate_evidence_complete",
      "zg361_b2_pip_gate_status",
      "zg361_result_case_serial",
      "zg361_result_grade",
      "zg361_result_absolute_grade",
      "zg361_result_kpi_frozen",
      "zg361_result_evidence_governance",
      "zg361_result_evidence_capability",
      "zg361_result_evidence_growth",
      "zg361_result_evidence_superior",
      "zg361_result_evidence_values",
      "zg361_result_evidence_collaboration",
      "zg361_result_evidence_jingcha",
      "zg361_result_evidence_organization",
      "zg361_b2_pip_owner",
      "zg361_b2_pip_subject",
      "zg361_b2_pip_cycle",
      "zg361_b2_pip_case",
      "zg361_b2_pip_state",
      "zg361_b2_pip_task_kind",
      "zg361_b2_pip_task_controllable",
      "zg361_b2_pip_policy_route",
      "zg361_b2_m015_receipt_serial",
      "zg361_b2_pip_subject_response",
      "zg361_b2_pip_subject_response_case",
      "zg361_b2_pip_subject_response_author",
      "zg361_b2_pip_goal_revision_used",
      "zg361_b2_pip_refusal_receipt",
      "zg361_b2_pip_support_reserved",
      "zg361_b2_pip_support_absent",
      "zg361_b2_pip_support_hours",
      "zg361_b2_pip_support_attention",
      "zg361_b2_pip_support_mentor",
      "zg361_b2_pip_support_budget_owner",
      "zg361_b2_pip_support_budget_allocated",
      "zg361_b2_pip_support_budget_spent",
      "zg361_b2_m016_receipt_serial",
      "zg361_b2_pip_support_released",
      "zg361_b2_pip_support_withheld",
      "zg361_b2_pip_support_atomic_shortfall",
      "zg361_result_treasury_paid",
      "zg361_result_gold_paid",
      "zg361_b2_pip_midpoint_receipt",
      "zg361_b2_pip_midpoint_resource_delivery_valid",
      "zg361_b2_pip_midpoint_progress_status",
      "zg361_b2_pip_midpoint_progress_red_code",
      "zg361_b2_pip_midpoint_state",
      "zg361_b2_pip_outcome_code",
      "zg361_b2_pip_settlement_receipt",
      "zg361_b2_pip_outcome_result_cycle",
      "zg361_b2_pip_outcome_result_case",
      "zg361_b2_pip_outcome_result_grade",
      "zg361_b2_pip_stability_days_observed",
      "zg361_b2_pip_independent_review_status",
      "zg361_b2_pip_independent_review_red_code",
      "zg361_b2_pip_graduation_receipt",
      "zg361_b2_pip_failure_receipt",
      "zg361_b2_pip_no_support_liability",
      "zg361_b2_pip_performance_evidence_status",
      "zg361_b2_pip_performance_evidence_owner",
      "zg361_b2_pip_performance_evidence_subject",
      "zg361_b2_pip_performance_evidence_source_cycle",
      "zg361_b2_pip_performance_evidence_source_case",
      "zg361_b2_pip_performance_evidence_due_cycle",
      "zg361_b2_pip_performance_evidence_delta",
      "zg361_b2_pip_performance_evidence_consumed_cycle",
      "zg361_b2_pip_performance_evidence_consumed_case",
  };
  constexpr std::string_view owner_key = "zg361_b2_pip_capacity_used";
  for (const auto key : subject_allowlist) {
    const std::string quoted = "\"" + std::string(key) + "\"";
    if (Count(header, quoted) != 1 || Count(abi, quoted) != 1 ||
        Count(fixture, quoted) != 1 || !Contains(producer, key)) {
      std::cerr << "subject allowlist identity mismatch: " << key << '\n';
      return 1;
    }
  }
  const std::string quoted_owner = "\"" + std::string(owner_key) + "\"";
  if (Count(header, quoted_owner) != 1 || Count(abi, quoted_owner) != 1 ||
      Count(fixture, quoted_owner) != 1 || !Contains(producer, owner_key) ||
      Count(header, "\"zg361_") != subject_allowlist.size() + 1 ||
      Count(abi, "\"zg361_") != subject_allowlist.size() + 1 ||
      Count(fixture, "\"zg361_") != subject_allowlist.size() + 1) {
    std::cerr << "owner or fixed allowlist cardinality mismatch\n";
    return 1;
  }

  const auto require_tokens = [](std::string_view source,
                                 std::initializer_list<std::string_view> tokens,
                                 std::string_view label) {
    if (HasAll(source, tokens)) return true;
    std::cerr << "B2 PIP source contract token mismatch: " << label << '\n';
    return false;
  };
  if (!require_tokens(
          header,
          {"std::array<std::string_view, 73>",
           "std::array<std::string_view, 1>", "zhongguo.b2.pip",
           "game.command.query-zhongguo-b2-pip-snapshot-v1",
           "pip_modifier_present"},
          "header") ||
      !require_tokens(
          reader,
          {"before.played_character_id", "SubjectRows first",
           "SubjectRows second", "OwnerRows owner_first",
           "OwnerRows owner_second", "first != second",
           "owner_first != owner_second", "BoundOwnerFromRows",
           "actual_owner == requested_owner", "not_received_self",
           "IntegerEquals(p.cycle_serial, *g.cycle_serial.value)",
           "IntegerEquals(p.case_serial, *g.case_serial.value)",
           "DecodeQ100000",
           "case_binding_mismatch", "MarkUnobservableTickets",
           "product_not_persisted", "native_observation_unavailable",
           "ComponentGate"},
          "reader") ||
      !require_tokens(
          serializer,
          {"d180_ticket", "d365_ticket", "pip_modifier_present",
           "next_cycle_evidence_ready", "owner_binding_ready",
           "same_frame_ready"},
          "serializer") ||
      !require_tokens(
          mailbox,
          {"HasExactControlFields", "expected_revision",
           "owner_character_id", "request_nonce",
           "result.subject_character_id",
           "result.requested_owner_character_id",
           "ExecuteZhongguoB2PipSnapshotMailboxQueryV1"},
          "mailbox") ||
      !require_tokens(
          adapter,
          {"std::array<std::string_view, 70>",
           "kZhongguoB2PipSnapshotV1Capability"},
          "adapter") ||
      !require_tokens(
          game_adapter,
          {"ParseZhongguoB2PipSnapshotV1Step",
           "kZhongguoB2PipSnapshotV1Capability"},
          "game_adapter") ||
      !require_tokens(
          bridge,
          {"permitted_executor_sexdenary",
           "ZhongguoB2PipSnapshotResultFrame",
           "zhongguo_b2_pip_snapshot_query_sequence",
           "zhongguo_b2_pip_snapshot"},
          "bridge") ||
      !require_tokens(
          abi,
          {"paused_played_character_only", "two_complete_subject_allowlist_reads",
           "two_complete_owner_allowlist_reads",
           "product_not_persisted", "production_live_acceptance",
           "arbitrary_character_variable_reader"},
          "abi") ||
      !require_tokens(
          fixture,
          {"\"subject_allowlist_count\": 73",
           "\"owner_allowlist_count\": 1",
           "\"mailbox_fixed_slot\": \"permitted_executor_sexdenary\"",
           "\"readiness\": \"static_and_fixture_ready_not_live\"",
           "terminal_graduated", "terminal_failed", "refused",
           "next_cycle_evidence_consumed", "frame_drift",
           "subject_row_drift", "owner_row_drift"},
          "fixture") ||
      !require_tokens(
          producer,
          {"zg361_b2_m015_open_pip_effect",
           "zg361_b2_publish_pip_performance_evidence_effect",
           "zg361_b2_consume_pip_performance_evidence_effect",
           "zg361_b2_pip_graduation_receipt",
           "zg361_b2_pip_failure_receipt",
           "zg361_b2_pip_refusal_receipt"},
          "producer") ||
      !require_tokens(
          documentation,
          {"73-key allowlist", "D+180", "D+365",
           "product_not_persisted", "native_observation_unavailable",
           "production-live"},
          "documentation")) {
    return 1;
  }

  const std::string combined = header + reader + serializer + mailbox + abi +
                               fixture + documentation;
  if (Contains(combined, "third_party_subject_query\": true") ||
      Contains(combined, "arbitrary_character_variable_reader\": true") ||
      Contains(combined, "production-live acceptance complete")) {
    std::cerr << "B2 PIP source contract escaped its strict boundary\n";
    return 1;
  }
  return 0;
}
