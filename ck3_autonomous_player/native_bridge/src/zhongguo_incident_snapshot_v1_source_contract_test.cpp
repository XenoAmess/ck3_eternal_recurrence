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

  constexpr std::array<std::string_view, 10> common{
      "zg361_ip_probe_owner",
      "zg361_ip_probe_subject",
      "zg361_ip_probe_cycle",
      "zg361_ip_probe_serial",
      "zg361_ip_probe_result",
      "zg361_ip_probe_source_kind",
      "zg361_ip_probe_consequence_kind",
      "zg361_ip_probe_subject_gold",
      "zg361_ip_probe_manager_treasury",
      "zg361_ip_probe_capital_control",
  };
  constexpr std::array<std::string_view, 40> profile_suffixes{
      "final_applicable",
      "final_kpi_staged",
      "final_na_owner",
      "final_na_subject",
      "final_na_cycle",
      "final_na_reason",
      "final_na_probe_serial",
      "final_na_receipt",
      "final_owner",
      "final_subject",
      "final_cycle",
      "final_case",
      "final_state",
      "final_revision",
      "final_incident_serial",
      "final_source_kind",
      "final_consequence_kind",
      "final_score",
      "kpi_pending",
      "kpi_consumed",
      "kpi_owner",
      "kpi_subject",
      "kpi_origin_cycle",
      "kpi_case",
      "kpi_state",
      "kpi_score",
      "kpi_due_cycle",
      "kpi_due_offset",
      "kpi_incident_serial",
      "kpi_source_kind",
      "kpi_consequence_kind",
      "kpi_receipt_serial",
      "kpi_consumed_owner",
      "kpi_consumed_subject",
      "kpi_consumed_origin_cycle",
      "kpi_consumed_due_cycle",
      "kpi_consumed_cycle",
      "kpi_consumed_case",
      "kpi_consumed_score",
      "kpi_consumed_incident_serial",
  };
  for (const auto key : common) {
    const std::string quoted = "\"" + std::string(key) + "\"";
    if (Count(header, quoted) != 3 || !Contains(abi, quoted) ||
        !Contains(fixture, quoted) || !Contains(producer, key)) {
      std::cerr << "common allowlist identity mismatch: " << key << '\n';
      return 1;
    }
  }
  for (const std::string_view profile : {"x", "y", "z"}) {
    for (const auto suffix : profile_suffixes) {
      const std::string key =
          "zg361_ip_" + std::string(profile) + "_" + std::string(suffix);
      const std::string quoted = "\"" + key + "\"";
      if (Count(header, quoted) != 1 || !Contains(producer, key)) {
        std::cerr << "profile allowlist identity mismatch: " << key << '\n';
        return 1;
      }
    }
  }
  if (Count(header, "std::array<std::string_view, 50>") != 3) {
    std::cerr << "profile allowlist cardinality declaration mismatch\n";
    return 1;
  }

  const auto require_tokens = [](std::string_view source,
                                 std::initializer_list<std::string_view> tokens,
                                 std::string_view label) {
    if (HasAll(source, tokens)) return true;
    std::cerr << "Incident source contract token mismatch: " << label << '\n';
    return false;
  };
  if (!require_tokens(
          header,
          {"std::array<std::string_view, 50>",
           "zhongguo.incident.subject-self",
           "game.command.query-zhongguo-incident-snapshot-v1",
           "manager_treasury_q100000"},
          "header") ||
      !require_tokens(
          reader,
          {"before.played_character_id", "Allowlist(request.profile)",
           "RawRows first", "RawRows second", "first != second",
           "actual_owner != request.owner_character_id", "DecodeQ100000",
           "rows[probe_manager_treasury]", "ComponentGate"},
          "reader") ||
      !require_tokens(
          serializer,
          {"manager_treasury_q100000",
           "zg361_ip_probe_manager_treasury", "resource_snapshot_ready",
           "same_frame_ready"},
          "serializer") ||
      !require_tokens(
          mailbox,
          {"HasExactControlFields", "expected_revision",
           "owner_character_id", "profile", "request_nonce",
           "ExecuteZhongguoIncidentSnapshotMailboxQueryV1"},
          "mailbox") ||
      !require_tokens(
          adapter,
          {"std::array<std::string_view, 72>",
           "kZhongguoIncidentSnapshotV1Capability"},
          "adapter") ||
      !require_tokens(
          game_adapter,
          {"ParseZhongguoIncidentSnapshotV1Step",
           "kZhongguoIncidentSnapshotV1Capability"},
          "game_adapter") ||
      !require_tokens(
          bridge,
          {"permitted_executor_septendenary",
           "ZhongguoIncidentSnapshotResultFrame",
           "zhongguo_incident_snapshot_query_sequence",
           "zhongguo_incident_snapshot"},
          "bridge") ||
      !require_tokens(
          abi,
          {"paused_played_character_only",
           "two_complete_profile_allowlist_reads",
           "manager_treasury_missing",
           "production_live_acceptance",
           "permitted_executor_septendenary"},
          "abi") ||
      !require_tokens(
          fixture,
          {"\"allowlist_count_per_profile\": 50",
           "\"mailbox_fixed_slot\": \"permitted_executor_septendenary\"",
           "\"integration_status\": \"shared_protocol_static_ready\"",
           "manager_treasury_uses_exact_mod_variable"},
          "fixture") ||
      !require_tokens(
          producer,
          {"zg361_ip_capture_real_incident_effect",
           "zg361_ip_probe_manager_treasury", "root.treasury",
           "government_has_flag = government_has_treasury"},
          "producer") ||
      !require_tokens(
          documentation,
          {"50-key", "permitted_executor_septendenary", "static-ready",
           "production-live"},
          "documentation")) {
    return 1;
  }

  const std::string combined = header + reader + serializer + mailbox + abi +
                               fixture + documentation;
  if (Contains(combined, "third_party_subject_query\": true") ||
      Contains(combined, "arbitrary_character_variable_reader\": true") ||
      Contains(combined, "production-live acceptance complete")) {
    std::cerr << "Incident source contract escaped its strict boundary\n";
    return 1;
  }
  return 0;
}
