#include "xar_bridge/projected_contact_scope_v1_serializer.hpp"
#include "xar_bridge/public_unit_id.hpp"

namespace xar::game {
namespace {

bool ParsePositiveProvince(std::string_view text,
                          std::int32_t &output) noexcept {
  return ParsePublicCUnitIdV1(text, output) && output > 0;
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char byte : value) {
    if (byte == '"' || byte == '\\') {
      out += '\\';
      out += static_cast<char>(byte);
    } else if (byte < 0x20) {
      out += "\\u00";
      out += hex[byte >> 4];
      out += hex[byte & 15];
    } else {
      out += static_cast<char>(byte);
    }
  }
  return out + '"';
}

const char *Bool(bool value) noexcept { return value ? "true" : "false"; }

std::string Int32Array(const std::vector<std::int32_t> &values) {
  std::string out = "[";
  for (const auto value : values) {
    if (out.size() != 1) out += ',';
    out += std::to_string(value);
  }
  return out + ']';
}

std::string_view StatusName(ProjectedContactScopeStatus status) noexcept {
  switch (status) {
  case ProjectedContactScopeStatus::available: return "available";
  case ProjectedContactScopeStatus::requires_paused: return "requires_paused";
  case ProjectedContactScopeStatus::subject_army_not_found:
    return "subject_army_not_found";
  case ProjectedContactScopeStatus::subject_army_not_controllable:
    return "subject_army_not_controllable";
  case ProjectedContactScopeStatus::subject_in_combat: return "subject_in_combat";
  case ProjectedContactScopeStatus::subject_not_contact_eligible:
    return "subject_not_contact_eligible";
  case ProjectedContactScopeStatus::target_province_not_found:
    return "target_province_not_found";
  case ProjectedContactScopeStatus::incoming_entry_province_not_found:
    return "incoming_entry_province_not_found";
  case ProjectedContactScopeStatus::invalid_entry_target_adjacency:
    return "invalid_entry_target_adjacency";
  case ProjectedContactScopeStatus::relation_unavailable:
    return "relation_unavailable";
  case ProjectedContactScopeStatus::state_changed: return "state_changed";
  case ProjectedContactScopeStatus::unavailable: return "unavailable";
  }
  return "unavailable";
}

} // namespace

bool ParseProjectedContactScopeV1Step(
    std::string_view step, ProjectedContactScopeRequest &output) noexcept {
  output = {};
  if (!step.starts_with(kProjectedContactScopeV1StepPrefix)) return false;
  const auto body = step.substr(kProjectedContactScopeV1StepPrefix.size());
  const auto to = body.find("-to-");
  if (to == std::string_view::npos) return false;
  const auto from = body.find("-from-", to + 4);
  if (from == std::string_view::npos) return false;
  ProjectedContactScopeRequest parsed{};
  if (!ParsePublicCUnitIdV1(body.substr(0, to), parsed.subject_army_id) ||
      !ParsePositiveProvince(body.substr(to + 4, from - to - 4),
                             parsed.target_province_id) ||
      !ParsePositiveProvince(body.substr(from + 6),
                             parsed.incoming_entry_province_id)) return false;
  output = parsed;
  return true;
}

std::string SerializeProjectedContactScopeV1Snapshot(
    const ProjectedContactScopeSnapshot &scope) {
  const bool has_current_combat = scope.transition_kind == "join_existing";
  const auto selected_combat =
      has_current_combat && scope.selected_current_combat_id >= 0
          ? std::to_string(scope.selected_current_combat_id) : "null";
  const auto selected_index =
      has_current_combat && scope.selected_current_combat_array_index >= 0
          ? std::to_string(scope.selected_current_combat_array_index) : "null";
  const auto initiator_is_defender =
      scope.transition_kind == "create_new" &&
              scope.projected_initiator_is_defender_observable
          ? Bool(scope.projected_initiator_is_defender) : "null";
  return "{\"status\":" + Quote(StatusName(scope.status)) +
      ",\"scope_kind\":" + Quote(scope.scope_kind) +
      ",\"snapshot_revision\":" + std::to_string(scope.snapshot_revision) +
      ",\"date_raw\":" + std::to_string(scope.date_raw) +
      ",\"subject_army_id\":" + std::to_string(scope.subject_army_id) +
      ",\"subject_native_carmy_id\":" + std::to_string(scope.subject_native_carmy_id) +
      ",\"subject_owner_character_id\":" + std::to_string(scope.subject_owner_character_id) +
      ",\"subject_current_province_id\":" + std::to_string(scope.subject_current_province_id) +
      ",\"target_province_id\":" + std::to_string(scope.target_province_id) +
      ",\"incoming_entry_province_id\":" + std::to_string(scope.incoming_entry_province_id) +
      ",\"observed_target_public_cunit_ids\":" + Int32Array(scope.observed_target_public_cunit_ids) +
      ",\"observed_target_combat_ids\":" + Int32Array(scope.observed_target_combat_ids) +
      ",\"transition_kind\":" + Quote(scope.transition_kind) +
      ",\"selected_current_combat_id\":" + selected_combat +
      ",\"selected_current_combat_array_index\":" + selected_index +
      ",\"projected_subject_side\":" + Quote(scope.projected_subject_side) +
      ",\"projected_initiator_is_defender_observable\":" +
          Bool(scope.projected_initiator_is_defender_observable) +
      ",\"projected_initiator_is_defender\":" + initiator_is_defender +
      ",\"incoming_adjacency_kind_raw\":" + std::to_string(scope.incoming_adjacency_kind_raw) +
      ",\"projected_attacker_army_ids\":" + Int32Array(scope.projected_attacker_army_ids) +
      ",\"projected_defender_army_ids\":" + Int32Array(scope.projected_defender_army_ids) +
      ",\"contact_projection_inputs_complete\":" +
          Bool(scope.contact_projection_inputs_complete) + "}";
}

} // namespace xar::game
