#include "xar_bridge/zhongguo_incident_snapshot_v1.hpp"

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
  constexpr std::array<std::string_view, 9> reasons{
      "snapshot_unavailable", "variable_absent", "value_type_mismatch",
      "value_out_of_range", "not_recorded_by_mod", "terminal_not_selected",
      "not_applicable", "kpi_not_staged", "not_yet_consumed"};
  return std::find(reasons.begin(), reasons.end(), reason) != reasons.end();
}

bool ValidTopReason(std::string_view reason) noexcept {
  constexpr std::array<std::string_view, 12> reasons{
      "unsupported_build", "requires_application_main", "requires_paused",
      "map_not_ready", "incident_not_found", "incident_inconsistent",
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

bool AppendTypedInteger(std::string &output,
                        const game::ZhongguoTypedIntegerV1 &field) {
  if (!ValidTyped(field)) return false;
  output += "{\"status\":\"";
  output += field.available ? "available" : "unavailable";
  output += "\",\"value\":";
  if (field.available) {
    if (!AppendNumber(output, *field.value)) return false;
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

bool AppendNamed(std::string &output, std::string_view name,
                 const game::ZhongguoTypedIntegerV1 &field,
                 bool first = false) {
  if (!first) output.push_back(',');
  AppendJsonString(output, name);
  output.push_back(':');
  return AppendTypedInteger(output, field);
}

bool AppendProbe(std::string &output,
                 const game::ZhongguoIncidentProbeV1 &value) {
  output.push_back('{');
  if (!AppendNamed(output, "owner_character_id", value.owner_character_id,
                   true) ||
      !AppendNamed(output, "subject_character_id",
                   value.subject_character_id) ||
      !AppendNamed(output, "cycle_serial", value.cycle_serial) ||
      !AppendNamed(output, "probe_serial", value.probe_serial) ||
      !AppendNamed(output, "result", value.result) ||
      !AppendNamed(output, "source_kind", value.source_kind) ||
      !AppendNamed(output, "consequence_kind", value.consequence_kind)) {
    return false;
  }
  output.push_back('}');
  return true;
}

bool AppendResources(
    std::string &output,
    const game::ZhongguoIncidentResourceSnapshotV1 &value) {
  output.push_back('{');
  if (!AppendNamed(output, "subject_personal_gold_q100000",
                   value.subject_personal_gold_q100000, true) ||
      !AppendNamed(output, "manager_treasury_q100000",
                   value.manager_treasury_q100000) ||
      !AppendNamed(output, "capital_control_q100000",
                   value.capital_control_q100000)) {
    return false;
  }
  output.push_back('}');
  return true;
}

bool AppendNa(std::string &output,
              const game::ZhongguoIncidentNaTerminalV1 &value) {
  output.push_back('{');
  if (!AppendNamed(output, "owner_character_id", value.owner_character_id,
                   true) ||
      !AppendNamed(output, "subject_character_id",
                   value.subject_character_id) ||
      !AppendNamed(output, "cycle_serial", value.cycle_serial) ||
      !AppendNamed(output, "reason", value.reason) ||
      !AppendNamed(output, "probe_serial", value.probe_serial) ||
      !AppendNamed(output, "receipt_serial", value.receipt_serial) ||
      !AppendNamed(output, "applicable", value.applicable) ||
      !AppendNamed(output, "kpi_staged", value.kpi_staged)) {
    return false;
  }
  output.push_back('}');
  return true;
}

bool AppendIncident(
    std::string &output,
    const game::ZhongguoIncidentPositiveTerminalV1 &value) {
  output.push_back('{');
  if (!AppendNamed(output, "owner_character_id", value.owner_character_id,
                   true) ||
      !AppendNamed(output, "subject_character_id",
                   value.subject_character_id) ||
      !AppendNamed(output, "cycle_serial", value.cycle_serial) ||
      !AppendNamed(output, "case_serial", value.case_serial) ||
      !AppendNamed(output, "state", value.state) ||
      !AppendNamed(output, "revision", value.revision) ||
      !AppendNamed(output, "incident_serial", value.incident_serial) ||
      !AppendNamed(output, "source_kind", value.source_kind) ||
      !AppendNamed(output, "consequence_kind", value.consequence_kind) ||
      !AppendNamed(output, "final_score", value.final_score) ||
      !AppendNamed(output, "applicable", value.applicable) ||
      !AppendNamed(output, "kpi_staged", value.kpi_staged)) {
    return false;
  }
  output.push_back('}');
  return true;
}

std::string_view KpiDispositionName(
    game::ZhongguoIncidentKpiDispositionV1 value) {
  switch (value) {
  case game::ZhongguoIncidentKpiDispositionV1::unavailable:
    return "unavailable";
  case game::ZhongguoIncidentKpiDispositionV1::not_staged:
    return "not_staged";
  case game::ZhongguoIncidentKpiDispositionV1::pending: return "pending";
  case game::ZhongguoIncidentKpiDispositionV1::consumed: return "consumed";
  }
  return {};
}

bool AppendKpi(std::string &output,
               const game::ZhongguoIncidentKpiStateV1 &value) {
  output += "{\"disposition\":";
  const auto disposition = KpiDispositionName(value.disposition);
  if (disposition.empty()) return false;
  AppendJsonString(output, disposition);
  if (!AppendNamed(output, "pending", value.pending) ||
      !AppendNamed(output, "consumed", value.consumed) ||
      !AppendNamed(output, "owner_character_id", value.owner_character_id) ||
      !AppendNamed(output, "subject_character_id",
                   value.subject_character_id) ||
      !AppendNamed(output, "origin_cycle", value.origin_cycle) ||
      !AppendNamed(output, "due_cycle", value.due_cycle) ||
      !AppendNamed(output, "due_offset", value.due_offset) ||
      !AppendNamed(output, "case_serial", value.case_serial) ||
      !AppendNamed(output, "state", value.state) ||
      !AppendNamed(output, "score", value.score) ||
      !AppendNamed(output, "incident_serial", value.incident_serial) ||
      !AppendNamed(output, "source_kind", value.source_kind) ||
      !AppendNamed(output, "consequence_kind", value.consequence_kind) ||
      !AppendNamed(output, "receipt_serial", value.receipt_serial) ||
      !AppendNamed(output, "consumed_owner_character_id",
                   value.consumed_owner_character_id) ||
      !AppendNamed(output, "consumed_subject_character_id",
                   value.consumed_subject_character_id) ||
      !AppendNamed(output, "consumed_origin_cycle",
                   value.consumed_origin_cycle) ||
      !AppendNamed(output, "consumed_due_cycle", value.consumed_due_cycle) ||
      !AppendNamed(output, "consumed_cycle", value.consumed_cycle) ||
      !AppendNamed(output, "consumed_case_serial",
                   value.consumed_case_serial) ||
      !AppendNamed(output, "consumed_score", value.consumed_score) ||
      !AppendNamed(output, "consumed_incident_serial",
                   value.consumed_incident_serial)) {
    return false;
  }
  output.push_back('}');
  return true;
}

void AppendReadiness(std::string &output,
                     const game::ZhongguoIncidentReadinessV1 &value) {
  output += "{\"player_subject_binding_ready\":";
  output += value.player_subject_binding_ready ? "true" : "false";
  output += ",\"owner_binding_ready\":";
  output += value.owner_binding_ready ? "true" : "false";
  output += ",\"profile_binding_ready\":";
  output += value.profile_binding_ready ? "true" : "false";
  output += ",\"probe_ready\":";
  output += value.probe_ready ? "true" : "false";
  output += ",\"terminal_ready\":";
  output += value.terminal_ready ? "true" : "false";
  output += ",\"resource_snapshot_ready\":";
  output += value.resource_snapshot_ready ? "true" : "false";
  output += ",\"kpi_state_ready\":";
  output += value.kpi_state_ready ? "true" : "false";
  output += ",\"same_frame_ready\":";
  output += value.same_frame_ready ? "true" : "false";
  output += ",\"ready\":";
  output += value.ready ? "true" : "false";
  output.push_back('}');
}

bool ComponentGate(const game::ZhongguoIncidentReadinessV1 &value) noexcept {
  return value.player_subject_binding_ready && value.owner_binding_ready &&
         value.profile_binding_ready && value.probe_ready &&
         value.terminal_ready && value.resource_snapshot_ready &&
         value.kpi_state_ready && value.same_frame_ready;
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

bool ValidEnvelope(const game::ZhongguoIncidentSnapshotV1 &snapshot) {
  if (snapshot.case_kind != kZhongguoIncidentSnapshotV1CaseKind ||
      (snapshot.profile != "x" && snapshot.profile != "y" &&
       snapshot.profile != "z") ||
      !ValidNonce(snapshot.request_nonce) || snapshot.snapshot_revision == 0 ||
      !snapshot.paused || snapshot.player_character_id <= 0 ||
      snapshot.subject_character_id != snapshot.player_character_id ||
      snapshot.requested_owner_character_id <= 0 ||
      snapshot.readiness.ready != ComponentGate(snapshot.readiness)) {
    return false;
  }
  const bool available = snapshot.status ==
                         game::ZhongguoIncidentSnapshotStatusV1::available;
  if (!available) {
    return snapshot.terminal_kind ==
               game::ZhongguoIncidentTerminalKindV1::unavailable &&
           ValidTopReason(snapshot.unavailable_reason) &&
           !snapshot.readiness.ready;
  }
  return snapshot.unavailable_reason.empty() &&
         (snapshot.terminal_kind == game::ZhongguoIncidentTerminalKindV1::na ||
          snapshot.terminal_kind ==
              game::ZhongguoIncidentTerminalKindV1::incident);
}

void AppendProvenance(std::string &output) {
  output += "{\"game_version\":\"1.19.0.6\",\"executable_sha256\":\"";
  output += kZhongguoCaseSnapshotV1ExecutableSha256;
  output += "\",\"backend_id\":\"";
  output += kZhongguoIncidentSnapshotV1BackendId;
  output += "\",\"consumer_id\":\"";
  output += kZhongguoIncidentSnapshotV1ConsumerId;
  output += "\",\"allowlist_id\":\"";
  output += kZhongguoIncidentSnapshotV1AllowlistId;
  output +=
      "\",\"variable_context_for_scope_rva\":\"0x3329A40\","
      "\"variable_identifier_table_rva\":\"0x3B971A0\","
      "\"variable_identifier_lookup_rva\":\"0x3B97020\","
      "\"variable_identifier_name_rva\":\"0x3B97090\","
      "\"character_storage_slot_rva\":\"0x570C130\","
      "\"manager_treasury_source\":\"not_recorded_by_mod\"}";
}

} // namespace

std::string SerializeZhongguoIncidentSnapshotV1(
    const game::ZhongguoIncidentSnapshotV1 &snapshot) {
  if (!ValidEnvelope(snapshot)) return {};
  std::string output;
  output.reserve(7'000);
  output += "{\"schema_version\":1,\"status\":\"";
  output += snapshot.status ==
                    game::ZhongguoIncidentSnapshotStatusV1::available
                ? "available"
                : "unavailable";
  output += "\",\"case_kind\":";
  AppendJsonString(output, snapshot.case_kind);
  output += ",\"profile\":";
  AppendJsonString(output, snapshot.profile);
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
  output += ",\"probe\":";
  if (!AppendProbe(output, snapshot.probe)) return {};
  output += ",\"resources\":";
  if (!AppendResources(output, snapshot.resources)) return {};
  output += ",\"terminal\":{\"kind\":\"";
  if (snapshot.terminal_kind ==
      game::ZhongguoIncidentTerminalKindV1::unavailable) {
    output += "unavailable\",\"na\":null,\"incident\":null}";
  } else if (snapshot.terminal_kind ==
             game::ZhongguoIncidentTerminalKindV1::na) {
    output += "na\",\"na\":";
    if (!AppendNa(output, snapshot.na_terminal)) return {};
    output += ",\"incident\":null}";
  } else {
    output += "incident\",\"na\":null,\"incident\":";
    if (!AppendIncident(output, snapshot.incident_terminal)) return {};
    output.push_back('}');
  }
  output += ",\"kpi\":";
  if (!AppendKpi(output, snapshot.kpi)) return {};
  output += ",\"readiness\":";
  AppendReadiness(output, snapshot.readiness);
  output += ",\"unavailable_reason\":";
  if (snapshot.status == game::ZhongguoIncidentSnapshotStatusV1::available) {
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
