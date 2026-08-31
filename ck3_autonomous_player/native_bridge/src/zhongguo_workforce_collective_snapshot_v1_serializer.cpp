#include "xar_bridge/zhongguo_workforce_collective_snapshot_v1.hpp"

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
  if (converted.ec != std::errc{}) return false;
  output.append(buffer.data(), converted.ptr);
  return true;
}

bool ValidFieldReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 7> reasons{
      "case_unavailable",       "variable_absent",
      "value_type_mismatch",    "value_out_of_range",
      "not_applicable",         "lifecycle_not_reached",
      "receipt_not_recorded"};
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool ValidTopReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 13> reasons{
      "unsupported_build",          "requires_application_main",
      "requires_paused",            "map_not_ready",
      "case_not_found",             "case_inconsistent",
      "owner_filter_mismatch",      "variable_identifier_unavailable",
      "variable_context_unavailable", "collective_inconsistent",
      "history_inconsistent",       "state_changed",
      "internal_error"};
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
  if (!ValidTyped(field)) return false;
  output += "{\"status\":\"";
  output += field.available ? "available" : "unavailable";
  output += "\",\"value\":";
  if (field.available) {
    if (!append_value(output, *field.value)) return false;
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

bool AppendCase(std::string &output,
                const game::ZhongguoWorkforceCaseV1 &value) {
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
  output.push_back('}');
  return true;
}

bool AppendReceipt(std::string &output,
                   const game::ZhongguoWorkforceM360ReceiptV1 &value) {
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
  output += ",\"choice\":";
  if (!AppendInteger(output, value.choice)) return false;
  output.push_back('}');
  return true;
}

std::string_view CollectivePhase(
    game::ZhongguoWorkforceCollectivePhaseV1 value) noexcept {
  switch (value) {
  case game::ZhongguoWorkforceCollectivePhaseV1::unavailable:
    return "unavailable";
  case game::ZhongguoWorkforceCollectivePhaseV1::not_reached:
    return "not_reached";
  case game::ZhongguoWorkforceCollectivePhaseV1::route_a_exception:
    return "route_a_exception";
  case game::ZhongguoWorkforceCollectivePhaseV1::route_b_forced:
    return "route_b_forced";
  case game::ZhongguoWorkforceCollectivePhaseV1::route_c_debt:
    return "route_c_debt";
  }
  return {};
}

bool AppendCollective(std::string &output,
                      const game::ZhongguoWorkforceCollectiveV1 &value) {
  const auto phase = CollectivePhase(value.phase);
  if (phase.empty()) return false;
  output += "{\"phase\":";
  AppendJsonString(output, phase);
#define XAR_APPEND_BOOL(name)                                                   \
  output += ",\"" #name "\":";                                             \
  if (!AppendBoolean(output, value.name)) return false
#define XAR_APPEND_INT(name)                                                    \
  output += ",\"" #name "\":";                                             \
  if (!AppendInteger(output, value.name)) return false
  XAR_APPEND_BOOL(submission_active);
  XAR_APPEND_BOOL(submission_sealed);
  XAR_APPEND_BOOL(submission_consumed);
  XAR_APPEND_INT(owner_character_id);
  XAR_APPEND_INT(subject_character_id);
  XAR_APPEND_INT(cycle_serial);
  XAR_APPEND_INT(case_serial);
  XAR_APPEND_INT(state);
  XAR_APPEND_INT(collective_case_serial);
  XAR_APPEND_INT(submitted_cycle_serial);
  XAR_APPEND_INT(cohort_count);
  XAR_APPEND_INT(settlement_id);
  XAR_APPEND_INT(settlement_hash);
  XAR_APPEND_BOOL(settled);
  XAR_APPEND_INT(route);
  XAR_APPEND_INT(total_members);
  XAR_APPEND_INT(total_quota);
  XAR_APPEND_INT(forced_count);
  XAR_APPEND_INT(exception_count);
  XAR_APPEND_INT(manager_cost_total);
#undef XAR_APPEND_BOOL
#undef XAR_APPEND_INT
  output.push_back('}');
  return true;
}

bool AppendCohort(std::string &output,
                  const game::ZhongguoWorkforceCohortV1 &value) {
  output.push_back('{');
#define XAR_APPEND_FIRST_INT(name)                                              \
  output += "\"" #name "\":";                                              \
  if (!AppendInteger(output, value.name)) return false
#define XAR_APPEND_INT(name)                                                    \
  output += ",\"" #name "\":";                                             \
  if (!AppendInteger(output, value.name)) return false
#define XAR_APPEND_BOOL(name)                                                   \
  output += ",\"" #name "\":";                                             \
  if (!AppendBoolean(output, value.name)) return false
  XAR_APPEND_FIRST_INT(cohort_id);
  XAR_APPEND_INT(manager_character_id);
  XAR_APPEND_INT(member_count);
  XAR_APPEND_INT(member_hash);
  XAR_APPEND_INT(quota);
  XAR_APPEND_INT(forced_count);
  XAR_APPEND_INT(exception_count);
  XAR_APPEND_INT(manager_cost);
  XAR_APPEND_BOOL(partition_verified);
  XAR_APPEND_BOOL(approval_verified);
  XAR_APPEND_INT(b1_cycle_serial);
  XAR_APPEND_INT(b1_case_serial);
  XAR_APPEND_INT(b1_source_id);
  XAR_APPEND_INT(b1_source_hash);
  XAR_APPEND_INT(mg_cycle_serial);
  XAR_APPEND_INT(mg_case_serial);
  XAR_APPEND_INT(mg_snapshot_source_serial);
  XAR_APPEND_INT(mg_snapshot_revision);
#undef XAR_APPEND_FIRST_INT
#undef XAR_APPEND_INT
#undef XAR_APPEND_BOOL
  output.push_back('}');
  return true;
}

bool AppendDebt(std::string &output,
                const game::ZhongguoWorkforceDebtV1 &value) {
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
  output += ",\"open\":";
  if (!AppendBoolean(output, value.open)) return false;
  output += ",\"consumed\":";
  if (!AppendBoolean(output, value.consumed)) return false;
  output += ",\"due_cycle_serial\":";
  if (!AppendInteger(output, value.due_cycle_serial)) return false;
  output.push_back('}');
  return true;
}

bool AppendHistorySlot(std::string &output,
                       const game::ZhongguoWorkforceHistorySlotV1 &value) {
  output += "{\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"subject_character_id\":";
  if (!AppendInteger(output, value.subject_character_id)) return false;
  output += ",\"cycle_serial\":";
  if (!AppendInteger(output, value.cycle_serial)) return false;
  output += ",\"case_serial\":";
  if (!AppendInteger(output, value.case_serial)) return false;
  output += ",\"m357_receipt_id\":";
  if (!AppendInteger(output, value.m357_receipt_id)) return false;
  output += ",\"m357_receipt_hash\":";
  if (!AppendInteger(output, value.m357_receipt_hash)) return false;
  output += ",\"m358_receipt_id\":";
  if (!AppendInteger(output, value.m358_receipt_id)) return false;
  output += ",\"m358_receipt_hash\":";
  if (!AppendInteger(output, value.m358_receipt_hash)) return false;
  output += ",\"m359_receipt_id\":";
  if (!AppendInteger(output, value.m359_receipt_id)) return false;
  output += ",\"m359_receipt_hash\":";
  if (!AppendInteger(output, value.m359_receipt_hash)) return false;
  output.push_back('}');
  return true;
}

std::string_view HistoryStatus(
    game::ZhongguoWorkforceHistoryStatusV1 value) noexcept {
  switch (value) {
  case game::ZhongguoWorkforceHistoryStatusV1::unavailable:
    return "unavailable";
  case game::ZhongguoWorkforceHistoryStatusV1::empty: return "empty";
  case game::ZhongguoWorkforceHistoryStatusV1::partial: return "partial";
  case game::ZhongguoWorkforceHistoryStatusV1::three_cycle:
    return "three_cycle";
  }
  return {};
}

bool AppendHistory(std::string &output,
                   const game::ZhongguoWorkforceHistoryV1 &value) {
  const auto status = HistoryStatus(value.status);
  if (status.empty()) return false;
  output += "{\"status\":";
  AppendJsonString(output, status);
  output += ",\"count\":";
  if (!AppendInteger(output, value.count)) return false;
  output += ",\"effective_count\":";
  const auto effective = value.status == game::ZhongguoWorkforceHistoryStatusV1::empty
                             ? 0
                             : (value.count.available && value.count.value
                                    ? *value.count.value
                                    : -1);
  if (!AppendNumber(output, effective)) return false;
  output += ",\"slots\":[";
  for (std::size_t index = 0; index < value.slots.size(); ++index) {
    if (index != 0) output.push_back(',');
    if (!AppendHistorySlot(output, value.slots[index])) return false;
  }
  output += "]}";
  return true;
}

std::string_view CharterStatus(
    game::ZhongguoWorkforceCharterGateStatusV1 value) noexcept {
  switch (value) {
  case game::ZhongguoWorkforceCharterGateStatusV1::unavailable:
    return "unavailable";
  case game::ZhongguoWorkforceCharterGateStatusV1::not_eligible:
    return "not_eligible";
  case game::ZhongguoWorkforceCharterGateStatusV1::awaiting_gate:
    return "awaiting_gate";
  case game::ZhongguoWorkforceCharterGateStatusV1::ready: return "ready";
  case game::ZhongguoWorkforceCharterGateStatusV1::consumed:
    return "consumed";
  }
  return {};
}

bool AppendCharter(std::string &output,
                   const game::ZhongguoWorkforceCharterGateV1 &value) {
  const auto status = CharterStatus(value.status);
  if (status.empty()) return false;
  output += "{\"status\":";
  AppendJsonString(output, status);
#define XAR_APPEND_INT(name)                                                    \
  output += ",\"" #name "\":";                                             \
  if (!AppendInteger(output, value.name)) return false
#define XAR_APPEND_BOOL(name)                                                   \
  output += ",\"" #name "\":";                                             \
  if (!AppendBoolean(output, value.name)) return false
  XAR_APPEND_INT(evidence_count);
  XAR_APPEND_BOOL(evidence_ready);
  XAR_APPEND_BOOL(evidence_consumed);
  XAR_APPEND_INT(owner_character_id);
  XAR_APPEND_INT(subject_character_id);
  XAR_APPEND_INT(cycle_serial);
  XAR_APPEND_INT(case_serial);
  XAR_APPEND_INT(state);
  XAR_APPEND_INT(prepared_report_id);
  XAR_APPEND_INT(prepared_charter_id);
  XAR_APPEND_INT(previous_charter_id);
  XAR_APPEND_INT(previous_version);
  XAR_APPEND_INT(adopted_cycle_serial);
  XAR_APPEND_INT(effective_cycle_serial);
  XAR_APPEND_INT(portfolio_status);
  XAR_APPEND_BOOL(portfolio_closed);
  XAR_APPEND_BOOL(terminal_history_accruing);
  XAR_APPEND_INT(portfolio_history_cycle_count);
  XAR_APPEND_BOOL(terminal_success);
#undef XAR_APPEND_INT
#undef XAR_APPEND_BOOL
  output.push_back('}');
  return true;
}

void AppendReadiness(
    std::string &output,
    const game::ZhongguoWorkforceCollectiveReadinessV1 &value) {
#define XAR_APPEND_READY(name)                                                  \
  output += "\"" #name "\":";                                              \
  output += value.name ? "true" : "false"
  output.push_back('{');
  XAR_APPEND_READY(player_subject_binding_ready);
  output.push_back(','); XAR_APPEND_READY(owner_binding_ready);
  output.push_back(','); XAR_APPEND_READY(case_identity_ready);
  output.push_back(','); XAR_APPEND_READY(m360_receipt_projection_ready);
  output.push_back(','); XAR_APPEND_READY(collective_lifecycle_ready);
  output.push_back(','); XAR_APPEND_READY(cohort_identity_ready);
  output.push_back(','); XAR_APPEND_READY(cohort_conservation_ready);
  output.push_back(','); XAR_APPEND_READY(route_conservation_ready);
  output.push_back(','); XAR_APPEND_READY(history_ledger_ready);
  output.push_back(','); XAR_APPEND_READY(history_order_ready);
  output.push_back(','); XAR_APPEND_READY(three_cycle_ready);
  output.push_back(','); XAR_APPEND_READY(charter_gate_lifecycle_ready);
  output.push_back(','); XAR_APPEND_READY(same_frame_ready);
  output.push_back(','); XAR_APPEND_READY(ready);
  output.push_back('}');
#undef XAR_APPEND_READY
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.19.0.6\",\"executable_sha256\":\"";
  output += kZhongguoCaseSnapshotV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kZhongguoWorkforceCollectiveSnapshotV1BackendId;
  output += "\",\"consumer_id\":\"";
  output += kZhongguoWorkforceCollectiveSnapshotV1ConsumerId;
  output += "\",\"allowlist_id\":\"";
  output += kZhongguoWorkforceCollectiveSnapshotV1AllowlistId;
  output +=
      "\",\"variable_context_for_scope_rva\":\"0x3329A40\","
      "\"variable_identifier_table_rva\":\"0x3B971A0\","
      "\"variable_identifier_lookup_rva\":\"0x3B97020\","
      "\"variable_identifier_name_rva\":\"0x3B97090\","
      "\"character_storage_slot_rva\":\"0x570C130\",";
  output += "\"subject_allowlist_count\":";
  AppendNumber(output, kZhongguoWorkforceSubjectVariableAllowlist.size());
  output += ",\"owner_allowlist_count\":";
  AppendNumber(output, kZhongguoWorkforceOwnerVariableAllowlist.size());
  output +=
      ",\"query_scope\":\"paused_received_self_al_case_plus_owner_rolling_three_cycle\"}";
}

bool ComponentGate(
    const game::ZhongguoWorkforceCollectiveReadinessV1 &value) noexcept {
  return value.player_subject_binding_ready && value.owner_binding_ready &&
         value.case_identity_ready && value.m360_receipt_projection_ready &&
         value.collective_lifecycle_ready && value.cohort_identity_ready &&
         value.cohort_conservation_ready && value.route_conservation_ready &&
         value.history_ledger_ready && value.history_order_ready &&
         value.charter_gate_lifecycle_ready && value.same_frame_ready;
}

bool ValidEnvelope(
    const game::ZhongguoWorkforceCollectiveSnapshotV1 &snapshot) noexcept {
  if (snapshot.case_kind !=
          kZhongguoWorkforceCollectiveSnapshotV1CaseKind ||
      !ValidNonce(snapshot.request_nonce) || snapshot.snapshot_revision == 0 ||
      snapshot.subject_character_id <= 0 ||
      snapshot.requested_owner_character_id <= 0 ||
      snapshot.readiness.ready != ComponentGate(snapshot.readiness)) {
    return false;
  }
  const bool available =
      snapshot.status ==
      game::ZhongguoWorkforceCollectiveSnapshotStatusV1::available;
  if (available) {
    return snapshot.unavailable_reason.empty() && snapshot.paused &&
           snapshot.player_character_id == snapshot.subject_character_id &&
           snapshot.readiness.ready;
  }
  return ValidTopReason(snapshot.unavailable_reason) &&
         !snapshot.readiness.ready;
}

} // namespace

std::string SerializeZhongguoWorkforceCollectiveSnapshotV1(
    const game::ZhongguoWorkforceCollectiveSnapshotV1 &snapshot) {
  if (!ValidEnvelope(snapshot)) return {};
  std::string output;
  output.reserve(18'000);
  output += "{\"schema_version\":1,\"status\":\"";
  output += snapshot.status ==
                    game::ZhongguoWorkforceCollectiveSnapshotStatusV1::available
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
  output += ",\"al_case\":";
  if (!AppendCase(output, snapshot.al_case)) return {};
  output += ",\"m360_receipt\":";
  if (!AppendReceipt(output, snapshot.m360_receipt)) return {};
  output += ",\"collective\":";
  if (!AppendCollective(output, snapshot.collective)) return {};
  output += ",\"cohorts\":[";
  for (std::size_t index = 0; index < snapshot.cohorts.size(); ++index) {
    if (index != 0) output.push_back(',');
    if (!AppendCohort(output, snapshot.cohorts[index])) return {};
  }
  output += "],\"route_c_debt\":";
  if (!AppendDebt(output, snapshot.route_c_debt)) return {};
  output += ",\"history\":";
  if (!AppendHistory(output, snapshot.history)) return {};
  output += ",\"charter_gate\":";
  if (!AppendCharter(output, snapshot.charter_gate)) return {};
  output += ",\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"unavailable_reason\":";
  if (snapshot.status ==
      game::ZhongguoWorkforceCollectiveSnapshotStatusV1::available) {
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
