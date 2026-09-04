#include "xar_bridge/zhongguo_career_hc_workforce_postcondition_v1.hpp"

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

bool AppendBoolean(std::string &output,
                   const game::ZhongguoTypedBooleanV1 &field) {
  return AppendTyped(output, field,
                     [](std::string &target, bool value) {
                       target += value ? "true" : "false";
                       return true;
                     });
}

bool AppendIdentity(
    std::string &output,
    const game::ZhongguoCareerHcWorkforceIdentityV1 &value) {
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

bool AppendReceipt(std::string &output,
                   const game::ZhongguoCareerHcWorkforceReceiptV1 &value,
                   bool provider_observed) {
  output += "{\"owner_character_id\":";
  if (!AppendInteger(output, value.identity.owner_character_id)) return false;
  output += ",\"subject_character_id\":";
  if (!AppendInteger(output, value.identity.subject_character_id)) return false;
  output += ",\"cycle_serial\":";
  if (!AppendInteger(output, value.identity.cycle_serial)) return false;
  output += ",\"case_serial\":";
  if (!AppendInteger(output, value.identity.case_serial)) return false;
  output += ",\"state\":";
  if (!AppendInteger(output, value.state)) return false;
  output += ",\"choice\":";
  if (!AppendInteger(output, value.choice)) return false;
  output += ",\"provider_observed\":";
  output += provider_observed ? "true}" : "false}";
  return true;
}

bool AppendPartition(std::string &output,
                     const game::ZhongguoCareerHcPartitionV1 &value,
                     bool provider_observed) {
  output += "{\"authorized\":";
  if (!AppendInteger(output, value.authorized)) return false;
  output += ",\"available\":";
  if (!AppendInteger(output, value.available)) return false;
  output += ",\"reserved\":";
  if (!AppendInteger(output, value.reserved)) return false;
  output += ",\"occupied\":";
  if (!AppendInteger(output, value.occupied)) return false;
  output += ",\"frozen\":";
  if (!AppendInteger(output, value.frozen)) return false;
  output += ",\"reclaimed\":";
  if (!AppendInteger(output, value.reclaimed)) return false;
  output += ",\"conserved\":";
  if (!AppendBoolean(output, value.conserved)) return false;
  output += ",\"provider_observed\":";
  output += provider_observed ? "true}" : "false}";
  return true;
}

void AppendReadiness(
    std::string &output,
    const game::ZhongguoCareerHcWorkforcePostconditionReadinessV1 &value) {
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
  flag("m360_identity_ready", value.m360_identity_ready);
  flag("m360_route_b_receipt_ready", value.m360_route_b_receipt_ready);
  flag("career_hc_partition_ready", value.career_hc_partition_ready);
  flag("career_hc_conservation_ready", value.career_hc_conservation_ready);
  flag("route_b_manager_cost_zero_ready",
       value.route_b_manager_cost_zero_ready);
  flag("same_frame_ready", value.same_frame_ready);
  flag("ready", value.ready);
  output.push_back('}');
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.19.0.6\",\"executable_sha256\":\"";
  output += kZhongguoCaseSnapshotV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kZhongguoCareerHcWorkforcePostconditionV1BackendId;
  output += "\",\"consumer_id\":\"";
  output += kZhongguoCareerHcWorkforcePostconditionV1ConsumerId;
  output += "\",\"allowlist_id\":\"";
  output += kZhongguoCareerHcWorkforcePostconditionV1AllowlistId;
  output +=
      "\",\"variable_context_for_scope_rva\":\"0x3329A40\","
      "\"variable_identifier_table_rva\":\"0x3B971A0\","
      "\"variable_identifier_lookup_rva\":\"0x3B97020\","
      "\"variable_identifier_name_rva\":\"0x3B97090\","
      "\"character_storage_slot_rva\":\"0x570C130\","
      "\"character_fallback_slot_rva\":\"0x570C138\"}";
}

} // namespace

std::string SerializeZhongguoCareerHcWorkforcePostconditionV1(
    const game::ZhongguoCareerHcWorkforcePostconditionV1 &snapshot) {
  if (snapshot.case_kind !=
          kZhongguoCareerHcWorkforcePostconditionV1CaseKind ||
      snapshot.request_nonce.empty() || snapshot.snapshot_revision == 0 ||
      snapshot.requested_owner_character_id <= 0 ||
      snapshot.subject_character_id <= 0) {
    return {};
  }
  std::string output;
  output.reserve(4'000);
  output += "{\"schema_version\":1,\"status\":\"";
  output += snapshot.status ==
                    game::ZhongguoCareerHcWorkforcePostconditionStatusV1::available
                ? "available"
                : "unavailable";
  output += "\",\"capability\":\"";
  output += kZhongguoCareerHcWorkforcePostconditionV1Capability;
  output += "\",\"case_kind\":";
  AppendJsonString(output, snapshot.case_kind);
  output += ",\"source_backend_id\":\"native-headless\",\"request_nonce\":";
  AppendJsonString(output, snapshot.request_nonce);
  output += ",\"snapshot_revision\":";
  if (!AppendNumber(output, snapshot.snapshot_revision)) return {};
  output += ",\"date_raw\":";
  if (!AppendNumber(output, snapshot.date_raw)) return {};
  output += ",\"paused\":";
  output += snapshot.paused ? "true" : "false";
  output += ",\"player_character_id\":";
  if (!AppendNumber(output, snapshot.player_character_id)) return {};
  output += ",\"subject_character_id\":";
  if (!AppendNumber(output, snapshot.subject_character_id)) return {};
  output += ",\"requested_owner_character_id\":";
  if (!AppendNumber(output, snapshot.requested_owner_character_id)) return {};
  output += ",\"m360_identity\":";
  if (!AppendIdentity(output, snapshot.m360_identity)) return {};
  output += ",\"m360_receipt\":";
  if (!AppendReceipt(output, snapshot.m360_receipt,
                     snapshot.readiness.m360_route_b_receipt_ready)) return {};
  output += ",\"career_hc_partition\":";
  if (!AppendPartition(output, snapshot.career_hc_partition,
                       snapshot.readiness.career_hc_partition_ready)) return {};
  output += ",\"route_b_cost\":{\"manager_cost_total\":";
  if (!AppendInteger(output, snapshot.route_b_cost.manager_cost_total)) return {};
  output += ",\"provider_observed\":";
  output += snapshot.readiness.route_b_manager_cost_zero_ready ? "true}" : "false}";
  output += ",\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"provenance\":";
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
