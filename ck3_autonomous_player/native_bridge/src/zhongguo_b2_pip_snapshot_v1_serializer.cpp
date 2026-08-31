#include "xar_bridge/zhongguo_b2_pip_snapshot_v1.hpp"

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
  constexpr std::array<std::string_view, 8> reasons{
      "case_unavailable", "variable_absent", "value_type_mismatch",
      "value_out_of_range", "case_binding_mismatch",
      "product_not_persisted", "native_observation_unavailable",
      "not_applicable"};
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool ValidTopReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 12> reasons{
      "unsupported_build", "requires_application_main", "requires_paused",
      "map_not_ready", "case_not_found", "case_inconsistent",
      "owner_filter_mismatch", "not_received_self",
      "variable_identifier_unavailable",
      "variable_context_unavailable", "state_changed", "internal_error"};
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

void AppendMemberPrefix(std::string &output, bool &first,
                        std::string_view name) {
  if (!first) output.push_back(',');
  first = false;
  AppendJsonString(output, name);
  output.push_back(':');
}

bool AppendIntegerMember(std::string &output, bool &first,
                         std::string_view name,
                         const game::ZhongguoTypedIntegerV1 &field) {
  AppendMemberPrefix(output, first, name);
  return AppendInteger(output, field);
}

bool AppendBooleanMember(std::string &output, bool &first,
                         std::string_view name,
                         const game::ZhongguoTypedBooleanV1 &field) {
  AppendMemberPrefix(output, first, name);
  return AppendBoolean(output, field);
}

bool AppendGate(std::string &output, const game::ZhongguoB2PipGateV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendIntegerMember(output, f, "owner_character_id", v.owner_character_id) ||
      !AppendIntegerMember(output, f, "subject_character_id", v.subject_character_id) ||
      !AppendIntegerMember(output, f, "cycle_serial", v.cycle_serial) ||
      !AppendIntegerMember(output, f, "case_serial", v.case_serial) ||
      !AppendIntegerMember(output, f, "threshold", v.threshold) ||
      !AppendIntegerMember(output, f, "negative_component_count", v.negative_component_count) ||
      !AppendBooleanMember(output, f, "evidence_complete", v.evidence_complete) ||
      !AppendIntegerMember(output, f, "status", v.status) ||
      !AppendIntegerMember(output, f, "result_case_serial", v.result_case_serial) ||
      !AppendIntegerMember(output, f, "result_grade", v.result_grade) ||
      !AppendIntegerMember(output, f, "absolute_grade", v.absolute_grade) ||
      !AppendIntegerMember(output, f, "kpi_frozen_q100000", v.kpi_frozen_q100000) ||
      !AppendIntegerMember(output, f, "governance_q100000", v.governance_q100000) ||
      !AppendIntegerMember(output, f, "capability_q100000", v.capability_q100000) ||
      !AppendIntegerMember(output, f, "growth_q100000", v.growth_q100000) ||
      !AppendIntegerMember(output, f, "superior_q100000", v.superior_q100000) ||
      !AppendIntegerMember(output, f, "values_q100000", v.values_q100000) ||
      !AppendIntegerMember(output, f, "collaboration_q100000", v.collaboration_q100000) ||
      !AppendIntegerMember(output, f, "jingcha_q100000", v.jingcha_q100000) ||
      !AppendIntegerMember(output, f, "organization_q100000", v.organization_q100000)) return false;
  output.push_back('}'); return true;
}

bool AppendPip(std::string &output, const game::ZhongguoB2PipIdentityV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendIntegerMember(output, f, "owner_character_id", v.owner_character_id) ||
      !AppendIntegerMember(output, f, "subject_character_id", v.subject_character_id) ||
      !AppendIntegerMember(output, f, "cycle_serial", v.cycle_serial) ||
      !AppendIntegerMember(output, f, "case_serial", v.case_serial) ||
      !AppendIntegerMember(output, f, "state", v.state) ||
      !AppendIntegerMember(output, f, "task_kind", v.task_kind) ||
      !AppendBooleanMember(output, f, "task_controllable", v.task_controllable) ||
      !AppendIntegerMember(output, f, "policy_route", v.policy_route)) return false;
  output.push_back('}'); return true;
}

bool AppendResponse(std::string &output, const game::ZhongguoB2PipResponseV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendIntegerMember(output, f, "subject_response", v.subject_response) ||
      !AppendIntegerMember(output, f, "response_case_serial", v.response_case_serial) ||
      !AppendIntegerMember(output, f, "response_author_character_id", v.response_author_character_id) ||
      !AppendIntegerMember(output, f, "acknowledgement_receipt_serial", v.acknowledgement_receipt_serial) ||
      !AppendBooleanMember(output, f, "goal_revision_used", v.goal_revision_used) ||
      !AppendIntegerMember(output, f, "refusal_receipt_serial", v.refusal_receipt_serial)) return false;
  output.push_back('}'); return true;
}

bool AppendSupport(std::string &output, const game::ZhongguoB2PipSupportV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendBooleanMember(output, f, "capacity_reserved", v.capacity_reserved) ||
      !AppendIntegerMember(output, f, "owner_capacity_used", v.owner_capacity_used) ||
      !AppendBooleanMember(output, f, "support_absent", v.support_absent) ||
      !AppendIntegerMember(output, f, "hours", v.hours) ||
      !AppendIntegerMember(output, f, "attention_units", v.attention_units) ||
      !AppendIntegerMember(output, f, "mentor_character_id", v.mentor_character_id) ||
      !AppendIntegerMember(output, f, "budget_owner_character_id", v.budget_owner_character_id) ||
      !AppendIntegerMember(output, f, "treasury_budget_allocated", v.treasury_budget_allocated) ||
      !AppendIntegerMember(output, f, "treasury_budget_spent", v.treasury_budget_spent) ||
      !AppendIntegerMember(output, f, "support_receipt_serial", v.support_receipt_serial) ||
      !AppendBooleanMember(output, f, "released", v.released) ||
      !AppendBooleanMember(output, f, "withheld", v.withheld) ||
      !AppendBooleanMember(output, f, "atomic_shortfall", v.atomic_shortfall)) return false;
  output.push_back('}'); return true;
}

bool AppendBudget(std::string &output, const game::ZhongguoB2PipBudgetLedgerV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendIntegerMember(output, f, "result_case_serial", v.result_case_serial) ||
      !AppendIntegerMember(output, f, "treasury_penalty_paid", v.treasury_penalty_paid) ||
      !AppendIntegerMember(output, f, "personal_gold_penalty_paid", v.personal_gold_penalty_paid) ||
      !AppendIntegerMember(output, f, "support_treasury_allocated", v.support_treasury_allocated) ||
      !AppendIntegerMember(output, f, "support_treasury_spent", v.support_treasury_spent)) return false;
  output.push_back('}'); return true;
}

bool AppendTicket(std::string &output, const game::ZhongguoB2PipTicketV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendIntegerMember(output, f, "owner_character_id", v.owner_character_id) ||
      !AppendIntegerMember(output, f, "subject_character_id", v.subject_character_id) ||
      !AppendIntegerMember(output, f, "cycle_serial", v.cycle_serial) ||
      !AppendIntegerMember(output, f, "case_serial", v.case_serial) ||
      !AppendIntegerMember(output, f, "expected_state", v.expected_state) ||
      !AppendIntegerMember(output, f, "due_date_raw", v.due_date_raw)) return false;
  output.push_back('}'); return true;
}

bool AppendMidpoint(std::string &output, const game::ZhongguoB2PipMidpointV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendIntegerMember(output, f, "receipt_serial", v.receipt_serial) ||
      !AppendBooleanMember(output, f, "resource_delivery_valid", v.resource_delivery_valid) ||
      !AppendIntegerMember(output, f, "progress_status", v.progress_status) ||
      !AppendIntegerMember(output, f, "progress_red_code", v.progress_red_code) ||
      !AppendIntegerMember(output, f, "state", v.state)) return false;
  output.push_back('}'); return true;
}

bool AppendOutcome(std::string &output, const game::ZhongguoB2PipOutcomeV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendIntegerMember(output, f, "code", v.code) ||
      !AppendIntegerMember(output, f, "settlement_receipt_serial", v.settlement_receipt_serial) ||
      !AppendIntegerMember(output, f, "result_cycle_serial", v.result_cycle_serial) ||
      !AppendIntegerMember(output, f, "result_case_serial", v.result_case_serial) ||
      !AppendIntegerMember(output, f, "result_grade", v.result_grade) ||
      !AppendIntegerMember(output, f, "stability_days_observed", v.stability_days_observed) ||
      !AppendIntegerMember(output, f, "independent_review_status", v.independent_review_status) ||
      !AppendIntegerMember(output, f, "independent_review_red_code", v.independent_review_red_code) ||
      !AppendIntegerMember(output, f, "graduation_receipt_serial", v.graduation_receipt_serial) ||
      !AppendIntegerMember(output, f, "failure_receipt_serial", v.failure_receipt_serial) ||
      !AppendBooleanMember(output, f, "no_support_liability", v.no_support_liability)) return false;
  output.push_back('}'); return true;
}

bool AppendEvidence(std::string &output, const game::ZhongguoB2PipNextCycleEvidenceV1 &v) {
  output.push_back('{'); bool f = true;
  if (!AppendIntegerMember(output, f, "status", v.status) ||
      !AppendIntegerMember(output, f, "owner_character_id", v.owner_character_id) ||
      !AppendIntegerMember(output, f, "subject_character_id", v.subject_character_id) ||
      !AppendIntegerMember(output, f, "source_cycle_serial", v.source_cycle_serial) ||
      !AppendIntegerMember(output, f, "source_case_serial", v.source_case_serial) ||
      !AppendIntegerMember(output, f, "due_cycle_serial", v.due_cycle_serial) ||
      !AppendIntegerMember(output, f, "delta", v.delta) ||
      !AppendIntegerMember(output, f, "consumed_cycle_serial", v.consumed_cycle_serial) ||
      !AppendIntegerMember(output, f, "consumed_case_serial", v.consumed_case_serial)) return false;
  output.push_back('}'); return true;
}

bool ComponentGate(const game::ZhongguoB2PipReadinessV1 &v) noexcept {
  return v.player_subject_binding_ready && v.owner_binding_ready &&
         v.gate_ready && v.same_frame_ready;
}

void AppendReadiness(std::string &o, const game::ZhongguoB2PipReadinessV1 &v) {
  o += "{\"player_subject_binding_ready\":";
  o += v.player_subject_binding_ready ? "true" : "false";
  o += ",\"owner_binding_ready\":"; o += v.owner_binding_ready ? "true" : "false";
  o += ",\"gate_ready\":"; o += v.gate_ready ? "true" : "false";
  o += ",\"gate_evidence_ready\":"; o += v.gate_evidence_ready ? "true" : "false";
  o += ",\"pip_identity_ready\":"; o += v.pip_identity_ready ? "true" : "false";
  o += ",\"response_ready\":"; o += v.response_ready ? "true" : "false";
  o += ",\"support_ready\":"; o += v.support_ready ? "true" : "false";
  o += ",\"budget_ledger_ready\":"; o += v.budget_ledger_ready ? "true" : "false";
  o += ",\"midpoint_ready\":"; o += v.midpoint_ready ? "true" : "false";
  o += ",\"outcome_ready\":"; o += v.outcome_ready ? "true" : "false";
  o += ",\"next_cycle_evidence_ready\":"; o += v.next_cycle_evidence_ready ? "true" : "false";
  o += ",\"d180_ticket_observation_ready\":"; o += v.d180_ticket_observation_ready ? "true" : "false";
  o += ",\"d365_ticket_observation_ready\":"; o += v.d365_ticket_observation_ready ? "true" : "false";
  o += ",\"modifier_observation_ready\":"; o += v.modifier_observation_ready ? "true" : "false";
  o += ",\"same_frame_ready\":"; o += v.same_frame_ready ? "true" : "false";
  o += ",\"ready\":"; o += v.ready ? "true" : "false";
  o.push_back('}');
}

bool ValidNonce(std::string_view value) noexcept {
  if (value.empty() || value.size() > 64) return false;
  for (std::size_t i = 0; i < value.size(); ++i) {
    const char c = value[i];
    const bool alpha = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    const bool digit = c >= '0' && c <= '9';
    const bool punctuation = c == '.' || c == '_' || c == ':' || c == '-';
    if ((!alpha && !digit && !punctuation) ||
        (i == 0 && !alpha && !digit)) return false;
  }
  return true;
}

bool ValidEnvelope(const game::ZhongguoB2PipSnapshotV1 &snapshot) noexcept {
  if (snapshot.case_kind != kZhongguoB2PipSnapshotV1CaseKind ||
      !ValidNonce(snapshot.request_nonce) || snapshot.snapshot_revision == 0 ||
      !snapshot.paused || snapshot.player_character_id <= 0 ||
      snapshot.subject_character_id != snapshot.player_character_id ||
      snapshot.requested_owner_character_id <= 0 ||
      snapshot.readiness.ready != ComponentGate(snapshot.readiness)) {
    return false;
  }
  const bool available = snapshot.status ==
                         game::ZhongguoB2PipSnapshotStatusV1::available;
  return available
             ? snapshot.unavailable_reason.empty() &&
                   snapshot.readiness.player_subject_binding_ready &&
                   snapshot.readiness.owner_binding_ready
             : ValidTopReason(snapshot.unavailable_reason) &&
                   !snapshot.readiness.ready;
}

void AppendProvenance(std::string &output) {
  output +=
      "{\"game_version\":\"1.19.0.6\","
      "\"executable_sha256\":\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\",";
  output += "\"backend_id\":";
  AppendJsonString(output, kZhongguoB2PipSnapshotV1BackendId);
  output += ",\"consumer_id\":";
  AppendJsonString(output, kZhongguoB2PipSnapshotV1ConsumerId);
  output += ",\"allowlist_id\":";
  AppendJsonString(output, kZhongguoB2PipSnapshotV1AllowlistId);
  output +=
      ",\"variable_context_for_scope_rva\":\"0x3329A40\","
      "\"variable_identifier_table_rva\":\"0x3B971A0\","
      "\"variable_identifier_lookup_rva\":\"0x3B97020\","
      "\"variable_identifier_name_rva\":\"0x3B97090\","
      "\"character_storage_slot_rva\":\"0x570C130\"}";
}

} // namespace

std::string SerializeZhongguoB2PipSnapshotV1(
    const game::ZhongguoB2PipSnapshotV1 &snapshot) {
  if (!ValidEnvelope(snapshot)) return {};
  std::string output;
  output.reserve(12'000);
  output += "{\"schema_version\":1,\"status\":\"";
  output += snapshot.status == game::ZhongguoB2PipSnapshotStatusV1::available
                ? "available"
                : "unavailable";
  output += "\",\"case_kind\":"; AppendJsonString(output, snapshot.case_kind);
  output += ",\"request_nonce\":"; AppendJsonString(output, snapshot.request_nonce);
  output += ",\"snapshot_revision\":"; if (!AppendNumber(output, snapshot.snapshot_revision)) return {};
  output += ",\"date_raw\":"; if (!AppendNumber(output, snapshot.date_raw)) return {};
  output += ",\"paused\":"; output += snapshot.paused ? "true" : "false";
  output += ",\"player_character_id\":"; if (!AppendNumber(output, snapshot.player_character_id)) return {};
  output += ",\"subject_character_id\":"; if (!AppendNumber(output, snapshot.subject_character_id)) return {};
  output += ",\"requested_owner_character_id\":"; if (!AppendNumber(output, snapshot.requested_owner_character_id)) return {};
  output += ",\"gate\":"; if (!AppendGate(output, snapshot.gate)) return {};
  output += ",\"pip\":"; if (!AppendPip(output, snapshot.pip)) return {};
  output += ",\"response\":"; if (!AppendResponse(output, snapshot.response)) return {};
  output += ",\"support\":"; if (!AppendSupport(output, snapshot.support)) return {};
  output += ",\"budget_ledger\":"; if (!AppendBudget(output, snapshot.budget_ledger)) return {};
  output += ",\"d180_ticket\":"; if (!AppendTicket(output, snapshot.d180_ticket)) return {};
  output += ",\"d365_ticket\":"; if (!AppendTicket(output, snapshot.d365_ticket)) return {};
  output += ",\"midpoint\":"; if (!AppendMidpoint(output, snapshot.midpoint)) return {};
  output += ",\"outcome\":"; if (!AppendOutcome(output, snapshot.outcome)) return {};
  output += ",\"next_cycle_evidence\":"; if (!AppendEvidence(output, snapshot.next_cycle_evidence)) return {};
  output += ",\"pip_modifier_present\":"; if (!AppendBoolean(output, snapshot.pip_modifier_present)) return {};
  output += ",\"readiness\":"; AppendReadiness(output, snapshot.readiness);
  output += ",\"unavailable_reason\":";
  if (snapshot.status == game::ZhongguoB2PipSnapshotStatusV1::available) {
    output += "null";
  } else {
    AppendJsonString(output, snapshot.unavailable_reason);
  }
  output += ",\"provenance\":"; AppendProvenance(output);
  output.push_back('}');
  return output;
}

} // namespace xar::ck3_11906
