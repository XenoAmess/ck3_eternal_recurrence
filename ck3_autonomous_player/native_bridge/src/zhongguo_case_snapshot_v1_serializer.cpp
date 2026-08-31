#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

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
    case '"':
      output += "\\\"";
      break;
    case '\\':
      output += "\\\\";
      break;
    case '\b':
      output += "\\b";
      break;
    case '\f':
      output += "\\f";
      break;
    case '\n':
      output += "\\n";
      break;
    case '\r':
      output += "\\r";
      break;
    case '\t':
      output += "\\t";
      break;
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
  constexpr std::array<std::string_view, 12> reasons{
      "case_unavailable",
      "variable_absent",
      "value_type_mismatch",
      "value_out_of_range",
      "no_operation_recorded",
      "unknown_allowlisted_operation",
      "receipt_not_recorded",
      "receipt_inconsistent",
      "deadline_not_scheduled",
      "deadline_inconsistent",
      "due_date_not_persisted_by_product",
      "not_applicable",
  };
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool ValidTopReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 12> reasons{
      "unsupported_build",
      "requires_application_main",
      "requires_paused",
      "map_not_ready",
      "subject_not_found",
      "case_not_found",
      "owner_filter_mismatch",
      "player_binding_mismatch",
      "variable_identifier_unavailable",
      "variable_context_unavailable",
      "state_changed",
      "internal_error",
  };
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

template <typename Value>
bool ValidTyped(const game::ZhongguoTypedValueV1<Value> &field) noexcept {
  return field.available
             ? field.value.has_value() && field.unavailable_reason.empty()
             : !field.value.has_value() &&
                   ValidFieldReason(field.unavailable_reason);
}

bool ValidTypedString(
    const game::ZhongguoTypedStringV1 &field) noexcept {
  return ValidTyped(field) &&
         (!field.available ||
          (!field.value->empty() && field.value->size() <= 128));
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

bool AppendString(std::string &output,
                  const game::ZhongguoTypedStringV1 &field) {
  if (!ValidTypedString(field)) {
    return false;
  }
  return AppendTyped(output, field,
                     [](std::string &target, const std::string &value) {
                       AppendJsonString(target, value);
                       return true;
                     });
}

bool ComponentGate(const game::ZhongguoCaseReadinessV1 &value) noexcept {
  return value.player_binding_ready && value.case_identity_ready &&
         value.policy_ready && value.operation_ready && value.receipt_ready &&
         value.deadline_identity_ready && value.deadline_due_date_ready &&
         value.same_frame_ready;
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
        (index == 0 && !alpha && !digit)) {
      return false;
    }
  }
  return true;
}

bool ValidEnvelope(const game::ZhongguoCaseSnapshotV1 &snapshot) noexcept {
  if (snapshot.case_kind != kZhongguoCaseSnapshotV1CaseKind ||
      !ValidNonce(snapshot.request_nonce) ||
      snapshot.snapshot_revision == 0 || !snapshot.paused ||
      snapshot.player_character_id <= 0 ||
      snapshot.subject_character_id <= 0 ||
      (snapshot.requested_owner_character_id.has_value() &&
       *snapshot.requested_owner_character_id <= 0) ||
      snapshot.readiness.ready != ComponentGate(snapshot.readiness)) {
    return false;
  }
  const bool available = snapshot.status ==
                         game::ZhongguoCaseSnapshotStatusV1::available;
  return available
             ? snapshot.unavailable_reason.empty() &&
                   snapshot.readiness.case_identity_ready &&
                   snapshot.readiness.player_binding_ready
             : ValidTopReason(snapshot.unavailable_reason) &&
                   !snapshot.readiness.ready;
}

std::string_view ReceiptStatus(
    game::ZhongguoReceiptStatusV1 status) noexcept {
  switch (status) {
  case game::ZhongguoReceiptStatusV1::recorded:
    return "recorded";
  case game::ZhongguoReceiptStatusV1::not_recorded:
    return "not_recorded";
  case game::ZhongguoReceiptStatusV1::unavailable:
    return "unavailable";
  }
  return {};
}

std::string_view DeadlineStatus(
    game::ZhongguoDeadlineStatusV1 status) noexcept {
  switch (status) {
  case game::ZhongguoDeadlineStatusV1::pending:
    return "pending";
  case game::ZhongguoDeadlineStatusV1::expired:
    return "expired";
  case game::ZhongguoDeadlineStatusV1::not_scheduled:
    return "not_scheduled";
  case game::ZhongguoDeadlineStatusV1::unavailable:
    return "unavailable";
  }
  return {};
}

bool AppendCase(std::string &output,
                const game::ZhongguoCaseIdentityV1 &value) {
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
  output += ",\"active\":";
  if (!AppendBoolean(output, value.active)) return false;
  output += ",\"revision\":";
  if (!AppendInteger(output, value.revision)) return false;
  output += ",\"timeline_serial\":";
  if (!AppendInteger(output, value.timeline_serial)) return false;
  output += ",\"feedback_revision\":";
  if (!AppendInteger(output, value.feedback_revision)) return false;
  output.push_back('}');
  return true;
}

bool AppendPolicy(std::string &output,
                  const game::ZhongguoCasePolicyV1 &value) {
  output += "{\"policy_id\":";
  if (!AppendString(output, value.policy_id)) return false;
  output += ",\"choice\":";
  if (!AppendInteger(output, value.choice)) return false;
  output.push_back('}');
  return true;
}

bool AppendOperation(std::string &output,
                     const game::ZhongguoCaseOperationV1 &value) {
  output += "{\"operation_id\":";
  if (!AppendInteger(output, value.operation_id)) return false;
  output += ",\"operation_key\":";
  if (!AppendString(output, value.operation_key)) return false;
  output += ",\"hook\":";
  if (!AppendString(output, value.hook)) return false;
  output += ",\"pre_state\":";
  if (!AppendInteger(output, value.pre_state)) return false;
  output += ",\"post_state\":";
  if (!AppendInteger(output, value.post_state)) return false;
  output.push_back('}');
  return true;
}

bool AppendReceipt(std::string &output,
                   const game::ZhongguoCaseReceiptV1 &value) {
  const auto status = ReceiptStatus(value.status);
  if (status.empty()) return false;
  output += "{\"status\":";
  AppendJsonString(output, status);
  output += ",\"key\":";
  if (!AppendString(output, value.key)) return false;
  output += ",\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"subject_character_id\":";
  if (!AppendInteger(output, value.subject_character_id)) return false;
  output += ",\"cycle_serial\":";
  if (!AppendInteger(output, value.cycle_serial)) return false;
  output += ",\"case_serial\":";
  if (!AppendInteger(output, value.case_serial)) return false;
  output += ",\"state\":";
  if (!AppendInteger(output, value.state)) return false;
  output += ",\"choice\":";
  if (!AppendInteger(output, value.choice)) return false;
  output.push_back('}');
  return true;
}

bool AppendDeadline(std::string &output,
                    const game::ZhongguoCaseDeadlineV1 &value) {
  const auto status = DeadlineStatus(value.status);
  if (status.empty()) return false;
  output += "{\"status\":";
  AppendJsonString(output, status);
  output += ",\"target_character_id\":";
  if (!AppendInteger(output, value.target_character_id)) return false;
  output += ",\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"cycle_serial\":";
  if (!AppendInteger(output, value.cycle_serial)) return false;
  output += ",\"case_serial\":";
  if (!AppendInteger(output, value.case_serial)) return false;
  output += ",\"expected_state\":";
  if (!AppendInteger(output, value.expected_state)) return false;
  output += ",\"days\":";
  if (!AppendInteger(output, value.days)) return false;
  output += ",\"pending\":";
  if (!AppendBoolean(output, value.pending)) return false;
  output += ",\"expired\":";
  if (!AppendBoolean(output, value.expired)) return false;
  output += ",\"open_date_raw\":";
  if (!AppendInteger(output, value.open_date_raw)) return false;
  output += ",\"due_date_raw\":";
  if (!AppendInteger(output, value.due_date_raw)) return false;
  output += ",\"on_due_operation\":";
  if (!AppendString(output, value.on_due_operation)) return false;
  output.push_back('}');
  return true;
}

void AppendReadiness(std::string &output,
                     const game::ZhongguoCaseReadinessV1 &value) {
  output += "{\"player_binding_ready\":";
  output += value.player_binding_ready ? "true" : "false";
  output += ",\"case_identity_ready\":";
  output += value.case_identity_ready ? "true" : "false";
  output += ",\"policy_ready\":";
  output += value.policy_ready ? "true" : "false";
  output += ",\"operation_ready\":";
  output += value.operation_ready ? "true" : "false";
  output += ",\"receipt_ready\":";
  output += value.receipt_ready ? "true" : "false";
  output += ",\"deadline_identity_ready\":";
  output += value.deadline_identity_ready ? "true" : "false";
  output += ",\"deadline_due_date_ready\":";
  output += value.deadline_due_date_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += value.same_frame_ready ? "true" : "false";
  output += ",\"ready\":";
  output += value.ready ? "true" : "false";
  output.push_back('}');
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.19.0.6\",";
  output += "\"executable_sha256\":\"";
  output += kZhongguoCaseSnapshotV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kZhongguoCaseSnapshotV1BackendId;
  output += "\",\"consumer_id\":\"";
  output += kZhongguoCaseSnapshotV1ConsumerId;
  output += "\",\"allowlist_id\":\"";
  output += kZhongguoCaseSnapshotV1AllowlistId;
  output += "\",\"variable_context_for_scope_rva\":\"0x3329A40\",";
  output += "\"variable_identifier_table_rva\":\"0x3B971A0\",";
  output += "\"variable_identifier_lookup_rva\":\"0x3B97020\",";
  output += "\"variable_identifier_name_rva\":\"0x3B97090\",";
  output += "\"character_storage_slot_rva\":\"0x570C130\"}";
}

} // namespace

std::string SerializeZhongguoCaseSnapshotV1(
    const game::ZhongguoCaseSnapshotV1 &snapshot) {
  if (!ValidEnvelope(snapshot)) {
    return {};
  }
  std::string output;
  output.reserve(5'000);
  output += "{\"schema_version\":1,\"status\":\"";
  output += snapshot.status == game::ZhongguoCaseSnapshotStatusV1::available
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
  if (snapshot.requested_owner_character_id.has_value()) {
    if (!AppendNumber(output, *snapshot.requested_owner_character_id)) {
      return {};
    }
  } else {
    output += "null";
  }
  output += ",\"case\":";
  if (!AppendCase(output, snapshot.case_identity)) return {};
  output += ",\"policy\":";
  if (!AppendPolicy(output, snapshot.policy)) return {};
  output += ",\"operation\":";
  if (!AppendOperation(output, snapshot.operation)) return {};
  output += ",\"receipt\":";
  if (!AppendReceipt(output, snapshot.receipt)) return {};
  output += ",\"deadline\":";
  if (!AppendDeadline(output, snapshot.deadline)) return {};
  output += ",\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"unavailable_reason\":";
  if (snapshot.status == game::ZhongguoCaseSnapshotStatusV1::available) {
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
