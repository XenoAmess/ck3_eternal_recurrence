#include "xar_bridge/zhongguo_manager_governance_snapshot_v1.hpp"

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
      "case_unavailable", "variable_absent", "value_type_mismatch",
      "value_out_of_range", "not_applicable", "lifecycle_not_reached",
      "receipt_not_recorded"};
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool ValidTopReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 14> reasons{
      "unsupported_build",
      "requires_application_main",
      "requires_paused",
      "map_not_ready",
      "case_not_found",
      "case_inconsistent",
      "ai_manager_owner_not_player",
      "bounded_ai_manager_dependency_unavailable",
      "subject_not_bounded_ai_manager",
      "owner_filter_mismatch",
      "variable_identifier_unavailable",
      "variable_context_unavailable",
      "state_changed",
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

bool AppendString(std::string &output,
                  const game::ZhongguoTypedStringV1 &field) {
  return AppendTyped(output, field,
                     [](std::string &target, const std::string &value) {
                       AppendJsonString(target, value);
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
        (index == 0 && !alpha && !digit)) return false;
  }
  return true;
}

bool AppendBinding(std::string &output,
                   const game::ZhongguoManagerSubjectBindingV1 &value) {
  output += "{\"kind\":\"";
  switch (value.kind) {
  case game::ZhongguoManagerSubjectBindingKindV1::unavailable:
    output += "unavailable";
    break;
  case game::ZhongguoManagerSubjectBindingKindV1::played_character:
    output += "played_character";
    break;
  case game::ZhongguoManagerSubjectBindingKindV1::bounded_ai_direct_manager:
    output += "bounded_ai_direct_manager";
    break;
  default: return false;
  }
  output += "\",\"manager_character_id\":";
  if (!AppendInteger(output, value.manager_character_id)) return false;
  output += ",\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"bounded_ai_manager_dependency\":";
  if (!AppendString(output, value.bounded_ai_manager_dependency)) return false;
  output.push_back('}');
  return true;
}

bool AppendFCase(std::string &output,
                 const game::ZhongguoManagerFCaseV1 &value) {
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

bool AppendTeam(std::string &output,
                const game::ZhongguoManagerTeamSnapshotV1 &value) {
  output += "{\"status\":";
  if (!AppendInteger(output, value.status)) return false;
  output += ",\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"subject_character_id\":";
  if (!AppendInteger(output, value.subject_character_id)) return false;
  output += ",\"cycle_serial\":";
  if (!AppendInteger(output, value.cycle_serial)) return false;
  output += ",\"case_serial\":";
  if (!AppendInteger(output, value.case_serial)) return false;
  output += ",\"revision\":";
  if (!AppendInteger(output, value.revision)) return false;
  output += ",\"source_cycle\":";
  if (!AppendInteger(output, value.source_cycle)) return false;
  output += ",\"cohort_n\":";
  if (!AppendInteger(output, value.cohort_n)) return false;
  output += ",\"aggregates\":{\"targets\":";
  if (!AppendInteger(output, value.targets)) return false;
  output += ",\"jingcha\":";
  if (!AppendInteger(output, value.jingcha)) return false;
  output += ",\"calibration\":";
  if (!AppendInteger(output, value.calibration)) return false;
  output += ",\"pip_success\":";
  if (!AppendInteger(output, value.pip_success)) return false;
  output += ",\"appeal_overturn\":";
  if (!AppendInteger(output, value.appeal_overturn)) return false;
  output += ",\"retention\":";
  if (!AppendInteger(output, value.retention)) return false;
  output += ",\"hc_efficiency\":";
  if (!AppendInteger(output, value.hc_efficiency)) return false;
  output += "}}";
  return true;
}

bool AppendReceipt(std::string &output,
                   const game::ZhongguoManagerReceiptV1 &value) {
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

bool AppendDistributionSnapshot(
    std::string &output,
    const game::ZhongguoManagerDistributionSnapshotV1 &value) {
  output += "{\"available\":";
  if (!AppendBoolean(output, value.available)) return false;
  output += ",\"mode\":";
  if (!AppendInteger(output, value.mode)) return false;
  output += ",\"rule_source\":";
  if (!AppendInteger(output, value.rule_source)) return false;
  output += ",\"top_slots\":";
  if (!AppendInteger(output, value.top_slots)) return false;
  output += ",\"middle_slots\":";
  if (!AppendInteger(output, value.middle_slots)) return false;
  output += ",\"bottom_slots\":";
  if (!AppendInteger(output, value.bottom_slots)) return false;
  output += ",\"conserved_slots\":";
  if (!AppendInteger(output, value.conserved_slots)) return false;
  output.push_back('}');
  return true;
}

bool AppendNextPolicy(std::string &output,
                      const game::ZhongguoManagerNextCyclePolicyV1 &value) {
  output += "{\"status\":";
  if (!AppendInteger(output, value.status)) return false;
  output += ",\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"subject_character_id\":";
  if (!AppendInteger(output, value.subject_character_id)) return false;
  output += ",\"source_reviewer_character_id\":";
  if (!AppendInteger(output, value.source_reviewer_character_id)) return false;
  output += ",\"source_cycle\":";
  if (!AppendInteger(output, value.source_cycle)) return false;
  output += ",\"source_case\":";
  if (!AppendInteger(output, value.source_case)) return false;
  output += ",\"source_revision\":";
  if (!AppendInteger(output, value.source_revision)) return false;
  output += ",\"input_revision\":";
  if (!AppendInteger(output, value.input_revision)) return false;
  output += ",\"mode\":";
  if (!AppendInteger(output, value.mode)) return false;
  output += ",\"rule_source\":";
  if (!AppendInteger(output, value.rule_source)) return false;
  output += ",\"due_cycle\":";
  if (!AppendInteger(output, value.due_cycle)) return false;
  output.push_back('}');
  return true;
}

bool AppendEffective(
    std::string &output,
    const game::ZhongguoManagerEffectiveDistributionV1 &value) {
  output += "{\"mode\":";
  if (!AppendInteger(output, value.mode)) return false;
  output += ",\"cycle\":";
  if (!AppendInteger(output, value.cycle)) return false;
  output += ",\"source_cycle\":";
  if (!AppendInteger(output, value.source_cycle)) return false;
  output += ",\"source_case\":";
  if (!AppendInteger(output, value.source_case)) return false;
  output += ",\"input_revision\":";
  if (!AppendInteger(output, value.input_revision)) return false;
  output += ",\"settled_cycle\":";
  if (!AppendInteger(output, value.settled_cycle)) return false;
  output += ",\"settlement_receipt\":";
  if (!AppendInteger(output, value.settlement_receipt)) return false;
  output += ",\"actual_cohort_n\":";
  if (!AppendInteger(output, value.actual_cohort_n)) return false;
  output += ",\"actual_bottom_slots\":";
  if (!AppendInteger(output, value.actual_bottom_slots)) return false;
  output.push_back('}');
  return true;
}

bool AppendScore(std::string &output,
                 const game::ZhongguoManagerScoreV1 &value) {
  output += "{\"sum\":";
  if (!AppendInteger(output, value.sum)) return false;
  output += ",\"mode\":";
  if (!AppendInteger(output, value.mode)) return false;
  output.push_back('}');
  return true;
}

bool AppendComponent8(std::string &output,
                      const game::ZhongguoManagerComponent8V1 &value) {
  output += "{\"status\":";
  if (!AppendInteger(output, value.status)) return false;
  output += ",\"owner_character_id\":";
  if (!AppendInteger(output, value.owner_character_id)) return false;
  output += ",\"subject_character_id\":";
  if (!AppendInteger(output, value.subject_character_id)) return false;
  output += ",\"source_cycle\":";
  if (!AppendInteger(output, value.source_cycle)) return false;
  output += ",\"source_case\":";
  if (!AppendInteger(output, value.source_case)) return false;
  output += ",\"source_revision\":";
  if (!AppendInteger(output, value.source_revision)) return false;
  output += ",\"input_revision\":";
  if (!AppendInteger(output, value.input_revision)) return false;
  output += ",\"component\":";
  if (!AppendInteger(output, value.component)) return false;
  output += ",\"value\":";
  if (!AppendInteger(output, value.value)) return false;
  output += ",\"due_cycle\":";
  if (!AppendInteger(output, value.due_cycle)) return false;
  output += ",\"settled_by_owner_character_id\":";
  if (!AppendInteger(output, value.settled_by_owner_character_id)) return false;
  output += ",\"settled_cycle\":";
  if (!AppendInteger(output, value.settled_cycle)) return false;
  output += ",\"settled_value\":";
  if (!AppendInteger(output, value.settled_value)) return false;
  output += ",\"settlement_receipt\":";
  if (!AppendInteger(output, value.settlement_receipt)) return false;
  output.push_back('}');
  return true;
}

void AppendReadiness(
    std::string &output,
    const game::ZhongguoManagerGovernanceReadinessV1 &value) {
#define XAR_APPEND_READY(name)                                                   \
  output += "\"" #name "\":";                                               \
  output += value.name ? "true" : "false"
  output.push_back('{');
  XAR_APPEND_READY(subject_binding_ready);
  output.push_back(','); XAR_APPEND_READY(bounded_ai_dependency_ready);
  output.push_back(','); XAR_APPEND_READY(case_identity_ready);
  output.push_back(','); XAR_APPEND_READY(team_snapshot_ready);
  output.push_back(','); XAR_APPEND_READY(f035_receipt_ready);
  output.push_back(','); XAR_APPEND_READY(distribution_snapshot_ready);
  output.push_back(','); XAR_APPEND_READY(distribution_conservation_ready);
  output.push_back(','); XAR_APPEND_READY(next_cycle_policy_ready);
  output.push_back(','); XAR_APPEND_READY(effective_distribution_ready);
  output.push_back(','); XAR_APPEND_READY(distribution_settlement_ready);
  output.push_back(','); XAR_APPEND_READY(actual_bottom_slots_ready);
  output.push_back(','); XAR_APPEND_READY(distribution_lifecycle_ready);
  output.push_back(','); XAR_APPEND_READY(f032_receipt_ready);
  output.push_back(','); XAR_APPEND_READY(manager_score_ready);
  output.push_back(','); XAR_APPEND_READY(component8_token_ready);
  output.push_back(','); XAR_APPEND_READY(component8_settlement_ready);
  output.push_back(','); XAR_APPEND_READY(component8_lifecycle_ready);
  output.push_back(','); XAR_APPEND_READY(same_frame_ready);
  output.push_back(','); XAR_APPEND_READY(ready);
  output.push_back('}');
#undef XAR_APPEND_READY
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.19.0.6\",\"executable_sha256\":\"";
  output += kZhongguoCaseSnapshotV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kZhongguoManagerGovernanceSnapshotV1BackendId;
  output += "\",\"consumer_id\":\"";
  output += kZhongguoManagerGovernanceSnapshotV1ConsumerId;
  output += "\",\"allowlist_id\":\"";
  output += kZhongguoManagerGovernanceSnapshotV1AllowlistId;
  output +=
      "\",\"variable_context_for_scope_rva\":\"0x3329A40\","
      "\"variable_identifier_table_rva\":\"0x3B971A0\","
      "\"variable_identifier_lookup_rva\":\"0x3B97020\","
      "\"variable_identifier_name_rva\":\"0x3B97090\","
      "\"character_storage_slot_rva\":\"0x570C130\"}";
}

bool ComponentGate(
    const game::ZhongguoManagerGovernanceReadinessV1 &value) noexcept {
  return value.subject_binding_ready && value.case_identity_ready &&
         value.team_snapshot_ready && value.f035_receipt_ready &&
         value.distribution_lifecycle_ready && value.f032_receipt_ready &&
         value.component8_lifecycle_ready && value.same_frame_ready;
}

bool ValidEnvelope(
    const game::ZhongguoManagerGovernanceSnapshotV1 &snapshot) noexcept {
  if (snapshot.case_kind != kZhongguoManagerGovernanceSnapshotV1CaseKind ||
      !ValidNonce(snapshot.request_nonce) || snapshot.snapshot_revision == 0 ||
      snapshot.subject_character_id <= 0 ||
      snapshot.requested_owner_character_id <= 0 ||
      snapshot.readiness.ready != ComponentGate(snapshot.readiness)) {
    return false;
  }
  const bool available =
      snapshot.status ==
      game::ZhongguoManagerGovernanceSnapshotStatusV1::available;
  if (available) {
    return snapshot.unavailable_reason.empty() && snapshot.paused &&
           snapshot.player_character_id > 0 &&
           snapshot.readiness.subject_binding_ready &&
           snapshot.readiness.case_identity_ready;
  }
  return ValidTopReason(snapshot.unavailable_reason) &&
         !snapshot.readiness.ready;
}

} // namespace

std::string SerializeZhongguoManagerGovernanceSnapshotV1(
    const game::ZhongguoManagerGovernanceSnapshotV1 &snapshot) {
  if (!ValidEnvelope(snapshot)) return {};
  std::string output;
  output.reserve(10'000);
  output += "{\"schema_version\":1,\"status\":\"";
  output += snapshot.status ==
                    game::ZhongguoManagerGovernanceSnapshotStatusV1::available
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
  output += ",\"subject_binding\":";
  if (!AppendBinding(output, snapshot.subject_binding)) return {};
  output += ",\"f_case\":";
  if (!AppendFCase(output, snapshot.f_case)) return {};
  output += ",\"team_snapshot\":";
  if (!AppendTeam(output, snapshot.team_snapshot)) return {};
  output += ",\"f035\":{\"receipt\":";
  if (!AppendReceipt(output, snapshot.f035_receipt)) return {};
  output += ",\"snapshot\":";
  if (!AppendDistributionSnapshot(output, snapshot.distribution_snapshot))
    return {};
  output += ",\"next_cycle_policy\":";
  if (!AppendNextPolicy(output, snapshot.next_cycle_policy)) return {};
  output += ",\"effective\":";
  if (!AppendEffective(output, snapshot.effective_distribution)) return {};
  output += "},\"f032\":{\"receipt\":";
  if (!AppendReceipt(output, snapshot.f032_receipt)) return {};
  output += ",\"manager_score\":";
  if (!AppendScore(output, snapshot.manager_score)) return {};
  output += ",\"component8\":";
  if (!AppendComponent8(output, snapshot.component8)) return {};
  output += "},\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"unavailable_reason\":";
  if (snapshot.status ==
      game::ZhongguoManagerGovernanceSnapshotStatusV1::available) {
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
