#pragma once

#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <cstddef>
#include <span>
#include <string>

namespace xar::game {

// This is a transport view over completed query values. It does not change
// ArmyStrengthSnapshot or sample / mutate a native object.
inline bool HaveSharedArmyManagerInputsV1(
    std::span<const ArmyStrengthSnapshot> rows) {
  if (rows.size() < 2) return false;
  const auto &first = rows.front();
  if (!first.current_daily_assault_roster_admission_v1 &&
      !first.current_pre_date_pending_update_inputs_v1 &&
      !first.current_post_admission_refresh_inputs_v1 &&
      !first.current_selected_title_holder_owner_relation_v1 &&
      !first.current_army_combat_roles_phase_inputs_v1 &&
      !first.current_army_flag31_inputs_v1) return false;
  for (const auto &row : rows.subspan(1)) {
    if (row.current_daily_assault_roster_admission_v1 !=
            first.current_daily_assault_roster_admission_v1 ||
        row.current_pre_date_pending_update_inputs_v1 !=
            first.current_pre_date_pending_update_inputs_v1 ||
        row.current_post_admission_refresh_inputs_v1 !=
            first.current_post_admission_refresh_inputs_v1 ||
        row.current_selected_title_holder_owner_relation_v1 !=
            first.current_selected_title_holder_owner_relation_v1 ||
        row.current_army_combat_roles_phase_inputs_v1 !=
            first.current_army_combat_roles_phase_inputs_v1 ||
        row.current_army_flag31_inputs_v1 !=
            first.current_army_flag31_inputs_v1) return false;
  }
  return true;
}

template <class Number, class Int32Array, class JsonString>
inline void AppendArmyManagerInputsSharedV1(
    std::string &out, std::span<const ArmyStrengthSnapshot> rows,
    Number number, Int32Array append_int32_array,
    JsonString append_json_string) {
  out += "{\"schema_version\":1,\"army_ids\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) out += ',';
    out += number(rows[index].army_id);
  }
  out += "],\"fields\":{";
  const auto &source = rows.front();
  bool first = true;
  const auto key = [&](const char *name) {
    if (!first) out += ',';
    first = false;
    append_json_string(out, name);
    out += ':';
  };
  if (source.current_daily_assault_roster_admission_v1) {
    key("current_daily_assault_roster_admission_v1");
    AppendArmyCurrentDailyAssaultRosterAdmissionV1(
        out, *source.current_daily_assault_roster_admission_v1,
        number, append_json_string);
  }
  if (source.current_pre_date_pending_update_inputs_v1) {
    key("current_pre_date_pending_update_inputs_v1");
    AppendArmyCurrentPreDatePendingUpdateInputsV1(
        out, *source.current_pre_date_pending_update_inputs_v1,
        number, append_json_string);
  }
  if (source.current_post_admission_refresh_inputs_v1) {
    key("current_post_admission_refresh_inputs_v1");
    AppendArmyCurrentPostAdmissionRefreshInputsV1(
        out, *source.current_post_admission_refresh_inputs_v1,
        number, append_json_string);
  }
  if (source.current_selected_title_holder_owner_relation_v1) {
    key("current_selected_title_holder_owner_relation_v1");
    AppendArmyCurrentSelectedTitleHolderOwnerRelationV1(
        out, *source.current_selected_title_holder_owner_relation_v1,
        number, append_json_string);
  }
  if (source.current_army_combat_roles_phase_inputs_v1) {
    key("current_army_combat_roles_phase_inputs_v1");
    AppendArmyCurrentCombatRolesPhaseInputsV1(
        out, *source.current_army_combat_roles_phase_inputs_v1,
        number, append_int32_array, append_json_string);
  }
  if (source.current_army_flag31_inputs_v1) {
    key("current_army_flag31_inputs_v1");
    AppendArmyCurrentFlag31InputsV1(
        out, *source.current_army_flag31_inputs_v1,
        number, append_int32_array, append_json_string);
  }
  out += "}}";
}

// Append only result members; the caller retains its command envelope and
// existing row writer (including any Bridge-only row extensions).
template <class Number, class Int32Array, class JsonString, class RowWriter>
inline void AppendArmyStrengthsQueryMembersV1(
    std::string &out, std::span<const ArmyStrengthSnapshot> rows,
    Number number, Int32Array append_int32_array,
    JsonString append_json_string, RowWriter append_row) {
  const bool shared = HaveSharedArmyManagerInputsV1(rows);
  const auto mode = shared ? ArmyStrengthManagerInputsModeV1::query_shared
                          : ArmyStrengthManagerInputsModeV1::inline_values;
  out += ",\"army_strengths\":[";
  for (std::size_t index = 0; index < rows.size(); ++index) {
    if (index != 0) out += ',';
    append_row(out, rows[index], mode);
  }
  out += ']';
  if (shared) {
    out += ",\"army_manager_inputs_shared_v1\":";
    AppendArmyManagerInputsSharedV1(
        out, rows, number, append_int32_array, append_json_string);
  }
}

} // namespace xar::game
