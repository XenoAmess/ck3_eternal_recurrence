#include "xar_bridge/zhongguo_result_case_snapshot_v1.hpp"

#include <algorithm>
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
    case '\b': output += "\\b"; break;
    case '\f': output += "\\f"; break;
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
  if (converted.ec != std::errc{}) {
    return false;
  }
  output.append(buffer.data(), converted.ptr);
  return true;
}

bool ValidFieldReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 4> reasons{
      "case_unavailable", "variable_absent", "value_type_mismatch",
      "value_out_of_range"};
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool ValidTopReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 12> reasons{
      "unsupported_build", "requires_application_main", "requires_paused",
      "map_not_ready", "case_not_found", "case_inconsistent",
      "owner_filter_mismatch", "not_received_self",
      "variable_identifier_unavailable", "variable_context_unavailable",
      "state_changed", "internal_error"};
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

template <typename Value>
bool ValidTyped(const game::ZhongguoTypedValueV1<Value> &field) noexcept {
  return field.available
             ? field.value.has_value() && field.unavailable_reason.empty()
             : !field.value.has_value() &&
                   ValidFieldReason(field.unavailable_reason);
}

template <typename Value, typename AppendValue>
bool AppendTyped(std::string &output,
                 const game::ZhongguoTypedValueV1<Value> &field,
                 AppendValue append_value) {
  if (!ValidTyped(field)) {
    return false;
  }
  output += "{\"status\":\"";
  output += field.available ? "available" : "unavailable";
  output += "\",\"value\":";
  if (field.available) {
    if (!append_value(output, *field.value)) {
      return false;
    }
  } else {
    output += "null";
  }
  output += ",\"unavailable_reason\":";
  if (field.available) {
    output += "null";
  } else {
    AppendJsonString(output, field.unavailable_reason);
  }
  output.push_back('}');
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
  return AppendTyped(output, field, [](std::string &target, bool value) {
    target += value ? "true" : "false";
    return true;
  });
}

bool ComponentGate(
    const game::ZhongguoResultCaseReadinessV1 &value) noexcept {
  return value.player_subject_binding_ready && value.owner_binding_ready &&
         value.case_identity_ready && value.notice_facts_ready &&
         value.delivery_state_ready && value.same_frame_ready;
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t index = 0; index < value.size(); ++index) {
    const char character = value[index];
    const bool alpha = (character >= 'a' && character <= 'z') ||
                       (character >= 'A' && character <= 'Z');
    const bool digit = character >= '0' && character <= '9';
    const bool punctuation = character == '.' || character == '_' ||
                             character == ':' || character == '-';
    if ((!alpha && !digit && !punctuation) ||
        (index == 0 && !alpha && !digit)) return false;
  }
  return true;
}

bool ValidEnvelope(
    const game::ZhongguoResultCaseSnapshotV1 &snapshot) noexcept {
  if (snapshot.case_kind != kZhongguoResultCaseSnapshotV1CaseKind ||
      !ValidNonce(snapshot.request_nonce) ||
      snapshot.snapshot_revision == 0 || !snapshot.paused ||
      snapshot.player_character_id <= 0 ||
      snapshot.subject_character_id != snapshot.player_character_id ||
      snapshot.requested_owner_character_id <= 0 ||
      snapshot.readiness.ready != ComponentGate(snapshot.readiness)) {
    return false;
  }
  const bool available =
      snapshot.status == game::ZhongguoResultCaseSnapshotStatusV1::available;
  return available
             ? snapshot.unavailable_reason.empty() &&
                   snapshot.readiness.player_subject_binding_ready &&
                   snapshot.readiness.owner_binding_ready &&
                   snapshot.readiness.case_identity_ready
             : ValidTopReason(snapshot.unavailable_reason) &&
                   !snapshot.readiness.ready;
}

bool AppendCase(std::string &output,
                const game::ZhongguoResultCaseIdentityV1 &value) {
  output += "{\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"subject_character_id\":";
  if (!AppendInteger(output, value.subject_character_id)) return false;
  output += ",\"cycle_serial\":";
  if (!AppendInteger(output, value.cycle_serial)) return false;
  output += ",\"case_serial\":";
  if (!AppendInteger(output, value.case_serial)) return false;
  output += ",\"state\":";
  if (!AppendInteger(output, value.state)) return false;
  output += ",\"grade\":";
  if (!AppendInteger(output, value.grade)) return false;
  output.push_back('}');
  return true;
}

bool AppendNotice(std::string &output,
                  const game::ZhongguoResultNoticeV1 &value) {
  output += "{\"absolute_grade\":";
  if (!AppendInteger(output, value.absolute_grade)) return false;
  output += ",\"kpi_frozen_q100000\":";
  if (!AppendInteger(output, value.kpi_frozen_q100000)) return false;
  output += ",\"rank_frozen\":";
  if (!AppendInteger(output, value.rank_frozen)) return false;
  output += ",\"cohort_n_frozen\":";
  if (!AppendInteger(output, value.cohort_n_frozen)) return false;
  output.push_back('}');
  return true;
}

bool AppendDelivery(std::string &output,
                    const game::ZhongguoResultDeliveryV1 &value) {
  output += "{\"method\":";
  if (!AppendInteger(output, value.method)) return false;
  output += ",\"objection_recorded\":";
  if (!AppendBoolean(output, value.objection_recorded)) return false;
  output += ",\"settlement_posted_serial\":";
  if (!AppendInteger(output, value.settlement_posted_serial)) return false;
  output += ",\"appeal_open\":";
  if (!AppendBoolean(output, value.appeal_open)) return false;
  output.push_back('}');
  return true;
}

void AppendReadiness(std::string &output,
                     const game::ZhongguoResultCaseReadinessV1 &value) {
  output += "{\"player_subject_binding_ready\":";
  output += value.player_subject_binding_ready ? "true" : "false";
  output += ",\"owner_binding_ready\":";
  output += value.owner_binding_ready ? "true" : "false";
  output += ",\"case_identity_ready\":";
  output += value.case_identity_ready ? "true" : "false";
  output += ",\"notice_facts_ready\":";
  output += value.notice_facts_ready ? "true" : "false";
  output += ",\"delivery_state_ready\":";
  output += value.delivery_state_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += value.same_frame_ready ? "true" : "false";
  output += ",\"ready\":";
  output += value.ready ? "true" : "false";
  output.push_back('}');
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.19.0.6\",\"executable_sha256\":\"";
  output += kZhongguoCaseSnapshotV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kZhongguoResultCaseSnapshotV1BackendId;
  output += "\",\"consumer_id\":\"";
  output += kZhongguoResultCaseSnapshotV1ConsumerId;
  output += "\",\"allowlist_id\":\"";
  output += kZhongguoResultCaseSnapshotV1AllowlistId;
  output +=
      "\",\"variable_context_for_scope_rva\":\"0x3329A40\","
      "\"variable_identifier_table_rva\":\"0x3B971A0\","
      "\"variable_identifier_lookup_rva\":\"0x3B97020\","
      "\"variable_identifier_name_rva\":\"0x3B97090\","
      "\"character_storage_slot_rva\":\"0x570C130\"}";
}

} // namespace

std::string SerializeZhongguoResultCaseSnapshotV1(
    const game::ZhongguoResultCaseSnapshotV1 &snapshot) {
  if (!ValidEnvelope(snapshot)) {
    return {};
  }
  std::string output;
  output.reserve(3'000);
  output += "{\"schema_version\":1,\"status\":\"";
  output += snapshot.status ==
                    game::ZhongguoResultCaseSnapshotStatusV1::available
                ? "available"
                : "unavailable";
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
  output += ",\"subject_character_id\":";
  if (!AppendNumber(output, snapshot.subject_character_id)) return {};
  output += ",\"requested_owner_character_id\":";
  if (!AppendNumber(output, snapshot.requested_owner_character_id)) return {};
  output += ",\"case\":";
  if (!AppendCase(output, snapshot.case_identity)) return {};
  output += ",\"notice\":";
  if (!AppendNotice(output, snapshot.notice)) return {};
  output += ",\"delivery\":";
  if (!AppendDelivery(output, snapshot.delivery)) return {};
  output += ",\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"unavailable_reason\":";
  if (snapshot.status ==
      game::ZhongguoResultCaseSnapshotStatusV1::available) {
    output += "null";
  } else {
    AppendJsonString(output, snapshot.unavailable_reason);
  }
  output += ",\"provenance\":";
  AppendProvenance(output);
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
