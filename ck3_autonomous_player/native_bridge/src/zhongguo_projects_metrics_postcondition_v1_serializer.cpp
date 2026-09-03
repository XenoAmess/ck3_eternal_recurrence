#include "xar_bridge/zhongguo_projects_metrics_postcondition_v1.hpp"

#include <array>
#include <charconv>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {
namespace {

void AppendJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output.push_back('"');
  for (const unsigned char character : value) {
    switch (character) {
    case '"': output += "\\\""; break;
    case '\\': output += "\\\\"; break;
    case '\n': output += "\\n"; break;
    case '\r': output += "\\r"; break;
    case '\t': output += "\\t"; break;
    default:
      if (character < 0x20U) {
        output += "\\u00";
        output.push_back(hex[(character >> 4U) & 0x0FU]);
        output.push_back(hex[character & 0x0FU]);
      } else {
        output.push_back(static_cast<char>(character));
      }
      break;
    }
  }
  output.push_back('"');
}

template <typename Value>
bool AppendNumber(std::string &output, Value value) {
  std::array<char, 32> buffer{};
  const auto converted =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (converted.ec != std::errc{}) return false;
  output.append(buffer.data(), converted.ptr);
  return true;
}

template <typename Value, typename Writer>
bool AppendTyped(std::string &output,
                 const game::ZhongguoTypedValueV1<Value> &field,
                 Writer writer) {
  if (field.available != field.value.has_value()) return false;
  if (field.available != field.unavailable_reason.empty()) return false;
  output += field.available ? "{\"status\":\"available\",\"value\":"
                            : "{\"status\":\"unavailable\",\"value\":null";
  if (field.available && !writer(output, *field.value)) return false;
  output += ",\"unavailable_reason\":";
  if (field.available) {
    output += "null}";
  } else {
    AppendJsonString(output, field.unavailable_reason);
    output.push_back('}');
  }
  return true;
}

bool AppendInteger(std::string &output,
                   const game::ZhongguoTypedIntegerV1 &field) {
  return AppendTyped(output, field,
                     [](std::string &target, std::int64_t value) {
                       return AppendNumber(target, value);
                     });
}

bool AppendString(std::string &output,
                  const game::ZhongguoTypedStringV1 &field) {
  return AppendTyped(output, field,
                     [](std::string &target, const std::string &value) {
                       AppendJsonString(target, value);
                       return true;
                     });
}

bool AppendIdentity(std::string &output,
                    const game::ZhongguoProjectsMetricsIdentityV1 &value) {
  output += "{\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"subject_character_id\":";
  if (!AppendInteger(output, value.subject_character_id)) return false;
  output += ",\"cycle_serial\":";
  if (!AppendInteger(output, value.cycle_serial)) return false;
  output += ",\"case_serial\":";
  if (!AppendInteger(output, value.case_serial)) return false;
  output.push_back('}');
  return true;
}

bool AppendContribution(std::string &output,
                        const game::ZhongguoProjectsContributionV1 &value) {
  output += "{\"identity\":";
  if (!AppendIdentity(output, value.identity)) return false;
  output += ",\"receipt_id\":";
  if (!AppendInteger(output, value.receipt_id)) return false;
  output += ",\"receipt_revision\":";
  if (!AppendInteger(output, value.receipt_revision)) return false;
  output += ",\"value\":";
  if (!AppendInteger(output, value.value)) return false;
  output += ",\"provider_observed\":true}";
  return true;
}

bool AppendMetrics(std::string &output,
                   const game::ZhongguoProjectsMetricsResultV1 &value) {
  output += "{\"identity\":";
  if (!AppendIdentity(output, value.identity)) return false;
  output += ",\"source_contribution_receipt_id\":";
  if (!AppendInteger(output, value.source_contribution_receipt_id)) return false;
  output += ",\"source_contribution_receipt_revision\":";
  if (!AppendInteger(output, value.source_contribution_receipt_revision)) {
    return false;
  }
  output += ",\"metrics_revision\":";
  if (!AppendInteger(output, value.metrics_revision)) return false;
  output += ",\"dictionary_key\":";
  if (!AppendString(output, value.dictionary_key)) return false;
  output += ",\"provider_observed\":true}";
  return true;
}

void AppendReadiness(
    std::string &output,
    const game::ZhongguoProjectsMetricsPostconditionReadinessV1 &value) {
  const auto flag = [&output](std::string_view name, bool enabled,
                              bool first = false) {
    if (!first) output.push_back(',');
    AppendJsonString(output, name);
    output.push_back(':');
    output += enabled ? "true" : "false";
  };
  output.push_back('{');
  flag("player_subject_binding_ready", value.player_subject_binding_ready,
       true);
  flag("owner_binding_ready", value.owner_binding_ready);
  flag("source_identity_ready", value.source_identity_ready);
  flag("result_identity_ready", value.result_identity_ready);
  flag("contribution_ready", value.contribution_ready);
  flag("metrics_ready", value.metrics_ready);
  flag("same_project_case_identity", value.same_project_case_identity);
  flag("receipt_lineage_ready", value.receipt_lineage_ready);
  flag("result_operation_committed", value.result_operation_committed);
  flag("same_frame_ready", value.same_frame_ready);
  flag("ready", value.ready);
  output.push_back('}');
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.19.0.6\",\"executable_sha256\":\"";
  output += kZhongguoCaseSnapshotV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kZhongguoProjectsMetricsPostconditionV1BackendId;
  output += "\",\"consumer_id\":\"";
  output += kZhongguoProjectsMetricsPostconditionV1ConsumerId;
  output += "\",\"allowlist_id\":\"";
  output += kZhongguoProjectsMetricsPostconditionV1AllowlistId;
  output +=
      "\",\"variable_context_for_scope_rva\":\"0x3329A40\","
      "\"variable_identifier_table_rva\":\"0x3B971A0\","
      "\"variable_identifier_lookup_rva\":\"0x3B97020\","
      "\"variable_identifier_name_rva\":\"0x3B97090\","
      "\"character_storage_slot_rva\":\"0x570C130\","
      "\"character_fallback_slot_rva\":\"0x570C138\"}";
}

} // namespace

std::string SerializeZhongguoProjectsMetricsPostconditionV1(
    const game::ZhongguoProjectsMetricsPostconditionV1 &snapshot) {
  if (snapshot.case_kind != kZhongguoProjectsMetricsPostconditionV1CaseKind ||
      snapshot.request_nonce.empty() || snapshot.snapshot_revision == 0 ||
      snapshot.requested_owner_character_id <= 0) {
    return {};
  }
  std::string output;
  output.reserve(5'000);
  output += "{\"schema_version\":1,\"status\":\"";
  output += snapshot.status ==
                    game::ZhongguoProjectsMetricsPostconditionStatusV1::available
                ? "available"
                : "unavailable";
  output += "\",\"capability\":\"";
  output += kZhongguoProjectsMetricsPostconditionV1Capability;
  output += "\",\"case_kind\":";
  AppendJsonString(output, snapshot.case_kind);
  output += ",\"request_nonce\":";
  AppendJsonString(output, snapshot.request_nonce);
  output += ",\"snapshot_revision\":";
  if (!AppendNumber(output, snapshot.snapshot_revision)) return {};
  output += ",\"date_raw\":";
  if (!AppendNumber(output, snapshot.date_raw)) return {};
  output += ",\"paused\":";
  output += snapshot.paused ? "true" : "false";
  output += ",\"player_character_id\":";
  if (!AppendNumber(output, snapshot.player_character_id)) return {};
  output += ",\"requested_owner_character_id\":";
  if (!AppendNumber(output, snapshot.requested_owner_character_id)) return {};
  output += ",\"source_identity\":";
  if (!AppendIdentity(output, snapshot.source_identity)) return {};
  output += ",\"result_identity\":";
  if (!AppendIdentity(output, snapshot.result_identity)) return {};
  output += ",\"projects_metrics\":{\"source_identity\":";
  if (!AppendIdentity(output, snapshot.source_identity)) return {};
  output += ",\"result_identity\":";
  if (!AppendIdentity(output, snapshot.result_identity)) return {};
  output += ",\"contribution\":";
  if (!AppendContribution(output, snapshot.contribution)) return {};
  output += ",\"metrics_result\":";
  if (!AppendMetrics(output, snapshot.metrics_result)) return {};
  output += "},\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"source_backend_id\":\"native-headless\",\"provenance\":";
  AppendProvenance(output);
  output += ",\"unavailable_reason\":";
  if (snapshot.unavailable_reason.empty()) {
    output += "null";
  } else {
    AppendJsonString(output, snapshot.unavailable_reason);
  }
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
