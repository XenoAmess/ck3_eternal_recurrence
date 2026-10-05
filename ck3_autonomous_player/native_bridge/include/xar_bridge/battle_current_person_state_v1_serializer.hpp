#pragma once

#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <string>
#include <string_view>

namespace xar::bridge {
namespace battle_current_person_state_v1_detail {

inline void AppendString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output += '\\';
      output += static_cast<char>(character);
    } else if (character < 0x20U) {
      output += "\\u00";
      output += hex[(character >> 4U) & 0x0FU];
      output += hex[character & 0x0FU];
    } else {
      output += static_cast<char>(character);
    }
  }
  output += '"';
}

inline void AppendReason(std::string &output, bool observed,
                         std::string_view reason, std::string_view fallback) {
  if (observed) output += "null";
  else AppendString(output, reason.empty() ? fallback : reason);
}

inline std::string_view TraitStatusName(
    xar::game::BattleCurrentPersonInjuryTraitsStatusV1 status) {
  switch (status) {
  case xar::game::BattleCurrentPersonInjuryTraitsStatusV1::available:
    return "available";
  case xar::game::BattleCurrentPersonInjuryTraitsStatusV1::partial:
    return "partial";
  case xar::game::BattleCurrentPersonInjuryTraitsStatusV1::unavailable:
    return "unavailable";
  }
  return "unavailable";
}

inline std::string_view DeathRecordStatusName(
    xar::game::BattleCurrentPersonDeathRecordStatusV1 status) {
  switch (status) {
  case xar::game::BattleCurrentPersonDeathRecordStatusV1::none:
    return "none";
  case xar::game::BattleCurrentPersonDeathRecordStatusV1::available:
    return "available";
  case xar::game::BattleCurrentPersonDeathRecordStatusV1::unavailable:
    return "unavailable";
  }
  return "unavailable";
}


template <typename T>
inline void AppendRawNumber(std::string &out, const std::optional<T> &value) {
  out += value ? std::to_string(*value) : "null";
}
template <typename T>
inline void AppendRawVector(std::string &out,
                            const std::optional<std::vector<T>> &values) {
  if (!values) { out += "null"; return; }
  out += '[';
  for (std::size_t i = 0; i < values->size(); ++i) {
    if (i) out += ',';
    out += std::to_string((*values)[i]);
  }
  out += ']';
}
inline void AppendRawProperties(std::string &out,
    const xar::game::BattleCurrentPersonRawPropertiesSnapshotV1 &p) {
  out += "{\"count\":";
  AppendRawNumber(out, p.count);
  out += ",\"keys_u16\":";
  AppendRawVector(out, p.keys_u16);
  out += ",\"values_q64\":";
  AppendRawVector(out, p.values_q64);
  out += '}';
}
inline std::string SerializeRawNumericInputs(
    const xar::game::BattleCurrentPersonRawNumericInputsSnapshotV1 &p) {
  std::string out = "{\"status\":";
  AppendString(out, p.status);
  out += ",\"raw_numeric_inputs_ready\":";
  out += p.raw_numeric_inputs_ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  out += ",\"scratch_present\":";
  out += p.scratch_present ? (*p.scratch_present ? "true" : "false") : "null";
  out += ",\"context_source\":";
  AppendString(out, p.context_source);
  const auto append_array = [&out](const auto &values) {
    out += '[';
    for (std::size_t i = 0; i < values.size(); ++i) {
      if (i) out += ',';
      AppendRawNumber(out, values[i]);
    }
    out += ']';
  };
  out += ",\"base_points\":"; append_array(p.base_points);
  out += ",\"caps\":"; append_array(p.caps);
  out += ",\"prowess_adjustment\":"; AppendRawNumber(out, p.prowess_adjustment);
  out += ",\"category_counts\":"; append_array(p.category_counts);
  out += ",\"scratch_factor_numerator\":";
  AppendRawNumber(out, p.scratch_factor_numerator);
  out += ",\"scratch_factor_denominator\":";
  AppendRawNumber(out, p.scratch_factor_denominator);
  out += ",\"context\":";
  if (!p.context) out += "null";
  else {
    const auto &c = *p.context;
    out += "{\"aggregate_properties\":";
    if (c.aggregate_properties) AppendRawProperties(out, *c.aggregate_properties);
    else out += "null";
    out += ",\"weighted_count\":"; AppendRawNumber(out, c.weighted_count);
    out += ",\"weighted_rows\":";
    if (!c.weighted_rows) out += "null";
    else {
      out += '[';
      for (std::size_t i = 0; i < c.weighted_rows->size(); ++i) {
        if (i) out += ',';
        const auto &row = (*c.weighted_rows)[i];
        out += "{\"native_index\":" + std::to_string(row.native_index);
        out += ",\"weight_q64\":"; AppendRawNumber(out, row.weight_q64);
        out += ",\"properties\":";
        if (row.properties) AppendRawProperties(out, *row.properties);
        else out += "null";
        out += '}';
      }
      out += ']';
    }
    out += '}';
  }
  out += ",\"unavailable_reason\":";
  AppendReason(out, p.raw_numeric_inputs_ready, p.unavailable_reason,
               "raw_numeric_input_reads_unavailable");
  out += '}';
  return out;
}

inline std::string SerializeContextBranchInputs(
    const xar::game::BattleCurrentPersonContextBranchInputsSnapshotV1 &p) {
  std::string out = "{\"status\":";
  AppendString(out, p.status);
  out += ",\"ready\":";
  out += p.ready ? "true" : "false";
  out += ",\"character_id\":" + std::to_string(p.character_id);
  out += ",\"flag14\":";
  out += p.flag14 ? (*p.flag14 ? "true" : "false") : "null";
  out += ",\"selected_index\":";
  AppendRawNumber(out, p.selected_index);
  out += ",\"selected_property_block\":";
  if (p.selected_property_block) AppendRawProperties(out, *p.selected_property_block);
  else out += "null";
  out += ",\"group_counts\":[";
  for (std::size_t i = 0; i < p.group_counts.size(); ++i) {
    if (i) out += ',';
    AppendRawNumber(out, p.group_counts[i]);
  }
  out += "],\"group_property_blocks\":[";
  for (std::size_t i = 0; i < p.group_property_blocks.size(); ++i) {
    if (i) out += ',';
    if (p.group_property_blocks[i]) AppendRawProperties(out, *p.group_property_blocks[i]);
    else out += "null";
  }
  out += "],\"unavailable_reason\":";
  AppendReason(out, p.ready, p.unavailable_reason, "context_branch_inputs_unavailable");
  out += '}';
  return out;
}

inline void AppendCurrentPriorPropertyBlock(
    std::string &out,
    const std::optional<xar::game::BattleCurrentPersonPriorPropertyBlockSnapshotV1> &block) {
  if (!block) { out += "null"; return; }
  out += "{\"rows\":[";
  for (std::size_t i = 0; i < block->rows.size(); ++i) {
    if (i) out += ',';
    const auto &row = block->rows[i];
    out += "{\"key\":" + std::to_string(row.key)
        + ",\"value_raw\":" + std::to_string(row.value_raw) + '}';
  }
  out += "]}";
}
inline void AppendCurrentPriorPropertyBlocks(
    std::string &out,
    const std::optional<std::vector<std::optional<
        xar::game::BattleCurrentPersonPriorPropertyBlockSnapshotV1>>> &blocks) {
  if (!blocks) { out += "null"; return; }
  out += '[';
  for (std::size_t i = 0; i < blocks->size(); ++i) {
    if (i) out += ',';
    AppendCurrentPriorPropertyBlock(out, (*blocks)[i]);
  }
  out += ']';
}
inline std::string SerializeCurrentPriorContextInputs(
    const xar::game::BattleCurrentPersonPriorContextInputsSnapshotV1 &p) {
  std::string out = "{\"available\":";
  out += p.available ? "true" : "false";
  out += ",\"reason\":";
  AppendReason(out, p.available, p.reason, "current_prior_context_input_reads_unavailable");
  out += ",\"character_full_id\":" + std::to_string(p.character_full_id)
      + ",\"base_property_block\":";
  AppendCurrentPriorPropertyBlock(out, p.base_property_block);
  out += ",\"common_property_blocks\":";
  AppendCurrentPriorPropertyBlocks(out, p.common_property_blocks);
  out += ",\"selector\":{\"available\":";
  out += p.selector.available ? "true" : "false";
  out += ",\"uses_18f8_source\":";
  out += p.selector.uses_18f8_source ? (*p.selector.uses_18f8_source ? "true" : "false") : "null";
  out += ",\"selected_header_offset\":";
  AppendRawNumber(out, p.selector.selected_header_offset);
  out += "},\"selected_property_blocks\":";
  AppendCurrentPriorPropertyBlocks(out, p.selected_property_blocks);
  out += '}';
  return out;
}

}  // namespace battle_current_person_state_v1_detail

// Insert inside xar::bridge, after the existing detail namespace closes and
// before SerializeBattleCurrentPersonStateV1. Reuses its JSON/property helpers.
namespace battle_current_person_state_v1_detail {
inline void AppendTaskPositionBool(std::string &out, const std::optional<bool> &value) {
  out += value ? (*value ? "true" : "false") : "null";
}
inline void AppendTaskPositionProperties(std::string &out,
    const std::optional<game::BattleCurrentPersonRawPropertiesSnapshotV1> &value) {
  if (value) AppendRawProperties(out, *value);
  else out += "null";
}
inline void AppendTaskPositionContext(std::string &out,
    const std::optional<game::BattleCurrentPersonRawContextSnapshotV1> &value) {
  if (!value) { out += "null"; return; }
  out += "{\"aggregate_properties\":";
  AppendTaskPositionProperties(out, value->aggregate_properties);
  out += ",\"weighted_count\":"; AppendRawNumber(out, value->weighted_count);
  out += ",\"weighted_rows\":";
  if (!value->weighted_rows) out += "null";
  else {
    out += '[';
    for (std::size_t i = 0; i < value->weighted_rows->size(); ++i) {
      if (i) out += ',';
      const auto &row = (*value->weighted_rows)[i];
      out += "{\"native_index\":" + std::to_string(row.native_index);
      out += ",\"weight_q64\":"; AppendRawNumber(out, row.weight_q64);
      out += ",\"properties\":"; AppendTaskPositionProperties(out, row.properties);
      out += '}';
    }
    out += ']';
  }
  out += '}';
}
template <typename Row>
inline void AppendTaskPositionModifierMetadata(std::string &out, const Row &row) {
  out += ",\"contributor_kind\":"; AppendString(out, row.contributor_kind);
  out += ",\"scope_root_character_id_raw\":"; AppendRawNumber(out, row.scope_root_character_id_raw);
  out += ",\"scope_saved_character_id_raw\":"; AppendRawNumber(out, row.scope_saved_character_id_raw);
  out += ",\"declaration_scale_q64\":"; AppendRawNumber(out, row.declaration_scale_q64);
  out += ",\"modifier_flags_raw\":"; AppendRawNumber(out, row.modifier_flags_raw);
  out += ",\"source_provenance\":"; AppendString(out, row.source_provenance);
}
inline void AppendTaskPositionDeclaration(std::string &out,
    const game::BattleCurrentPersonTaskPositionDeclarationSnapshotV1 &row) {
  out += "{\"native_index\":" + std::to_string(row.native_index);
  AppendTaskPositionModifierMetadata(out, row);
  out += ",\"declared_properties\":"; AppendTaskPositionProperties(out, row.declared_properties);
  out += '}';
}
inline void AppendTaskPositionEvaluatedRow(std::string &out,
    const game::BattleCurrentPersonTaskPositionEvaluatedRowSnapshotV1 &row) {
  out += "{\"task_native_index\":" + std::to_string(row.task_native_index);
  out += ",\"declaration_native_index\":" + std::to_string(row.declaration_native_index);
  AppendTaskPositionModifierMetadata(out, row);
  out += ",\"properties\":"; AppendTaskPositionProperties(out, row.properties);
  out += '}';
}
template <typename Row, typename Append>
inline void AppendTaskPositionRows(std::string &out,
    const std::optional<std::vector<Row>> &rows, Append append) {
  if (!rows) { out += "null"; return; }
  out += '[';
  for (std::size_t i = 0; i < rows->size(); ++i) {
    if (i) out += ',';
    append(out, (*rows)[i]);
  }
  out += ']';
}
inline void AppendTaskPositionTask(std::string &out,
    const game::BattleCurrentPersonTaskPositionTaskSnapshotV1 &task) {
  out += "{\"native_index\":" + std::to_string(task.native_index);
  out += ",\"task_id_raw\":" + std::to_string(task.task_id_raw);
  out += ",\"resolved_task_id_raw\":"; AppendRawNumber(out, task.resolved_task_id_raw);
  out += ",\"used_native_default\":"; AppendTaskPositionBool(out, task.used_native_default);
  out += ",\"frozen_raw\":"; AppendRawNumber(out, task.frozen_raw);
  out += ",\"incumbent_character_id_raw\":"; AppendRawNumber(out, task.incumbent_character_id_raw);
  out += ",\"owner_character_id_raw\":"; AppendRawNumber(out, task.owner_character_id_raw);
  out += ",\"task_type_present\":"; AppendTaskPositionBool(out, task.task_type_present);
  out += ",\"original_position_type_present\":"; AppendTaskPositionBool(out, task.original_position_type_present);
  out += ",\"native_gate_allowed\":"; AppendTaskPositionBool(out, task.native_gate_allowed);
  out += ",\"terminal_task_type_present\":"; AppendTaskPositionBool(out, task.terminal_task_type_present);
  out += ",\"declarations\":"; AppendTaskPositionRows(out, task.declarations, AppendTaskPositionDeclaration);
  out += ",\"owner_aggregate_properties_ready\":";
  out += task.owner_aggregate_properties_ready ? "true" : "false";
  out += ",\"owner_aggregate_properties\":"; AppendTaskPositionProperties(out, task.owner_aggregate_properties);
  out += '}';
}
inline void AppendTaskPositionBranch(std::string &out,
    const game::BattleCurrentPersonTaskPositionBranchSnapshotV1 &branch) {
  out += "{\"status\":"; AppendString(out, branch.status);
  out += ",\"complete_no_contribution\":"; AppendTaskPositionBool(out, branch.complete_no_contribution);
  out += ",\"vectors_ready\":"; out += branch.vectors_ready ? "true" : "false";
  out += ",\"evaluated_rows\":"; AppendTaskPositionRows(out, branch.evaluated_rows, AppendTaskPositionEvaluatedRow);
  out += ",\"prefix_before\":"; AppendTaskPositionContext(out, branch.prefix_before);
  out += ",\"prefix_source\":"; AppendString(out, branch.prefix_source);
  out += ",\"aggregate_properties_after\":"; AppendTaskPositionProperties(out, branch.aggregate_properties_after);
  out += ",\"aggregate_source\":"; AppendString(out, branch.aggregate_source);
  out += ",\"unavailable_reason\":";
  AppendReason(out, branch.vectors_ready, branch.unavailable_reason, "task_position_vector_inputs_unobserved");
  out += '}';
}
}  // namespace battle_current_person_state_v1_detail

inline std::string SerializeCurrentContextTaskPositionInputsV1(
    const game::BattleCurrentPersonTaskPositionInputsSnapshotV1 &inputs) {
  using namespace battle_current_person_state_v1_detail;
  std::string out = "{\"schema_version\":1,\"status\":"; AppendString(out, inputs.status);
  out += ",\"character_id\":" + std::to_string(inputs.character_id);
  out += ",\"raw_task_inputs_ready\":"; out += inputs.raw_task_inputs_ready ? "true" : "false";
  out += ",\"branch_vectors_ready\":"; out += inputs.branch_vectors_ready ? "true" : "false";
  out += ",\"owner_council_present\":"; AppendTaskPositionBool(out, inputs.owner_council_present);
  out += ",\"ordered_owned_tasks\":"; AppendTaskPositionRows(out, inputs.ordered_owned_tasks, AppendTaskPositionTask);
  out += ",\"councillor_task_link_present\":"; AppendTaskPositionBool(out, inputs.councillor_task_link_present);
  out += ",\"councillor_task\":";
  if (inputs.councillor_task) AppendTaskPositionTask(out, *inputs.councillor_task);
  else out += "null";
  out += ",\"owned_passive\":"; AppendTaskPositionBranch(out, inputs.owned_passive);
  out += ",\"councillor_position_task\":"; AppendTaskPositionBranch(out, inputs.councillor_position_task);
  out += ",\"unavailable_reason\":";
  AppendReason(out, inputs.status == "available", inputs.unavailable_reason, "task_position_inputs_unobserved");
  out += '}';
  return out;
}


// A current-character read; it does not project historical injury causality.
// The enclosing serializer controls optional presence and current-only scope.
inline std::string SerializeBattleCurrentPersonStateV1(
    const xar::game::BattleCurrentPersonStateSnapshotV1 &state) {
  using namespace battle_current_person_state_v1_detail;
  const auto &prowess = state.effective_prowess;
  const auto &injury = state.injury_traits;
  std::string output = "{\"scope\":\"current_character\","
                       "\"effective_prowess\":{\"status\":";
  AppendString(output, prowess.available ? "available" : "unavailable");
  output += ",\"points\":";
  output += prowess.available && prowess.points.has_value()
                ? std::to_string(*prowess.points) : "null";
  output += ",\"unavailable_reason\":";
  AppendReason(output, prowess.available, prowess.unavailable_reason,
               "effective_prowess_unavailable");
  output += "},\"injury_traits\":{\"status\":";
  AppendString(output, TraitStatusName(injury.status));
  output += ",\"flags\":{";
  constexpr std::string_view keys[] = {
      "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
      "one_eyed", "disfigured", "incapable"};
  for (std::size_t index = 0; index < injury.flags.size(); ++index) {
    if (index != 0) output += ',';
    AppendString(output, keys[index]);
    output += ':';
    output += injury.flags[index].has_value()
                  ? (*injury.flags[index] ? "true" : "false") : "null";
  }
  output += "},\"wounded_rank\":";
  output += injury.wounded_rank.has_value()
                ? std::to_string(*injury.wounded_rank) : "null";
  output += ",\"wounded_rank_unavailable_reason\":";
  AppendReason(output, injury.wounded_rank.has_value(),
               injury.wounded_rank_unavailable_reason, "wounded_rank_unavailable");
  output += ",\"unavailable_reason\":";
  AppendReason(output,
               injury.status == xar::game::BattleCurrentPersonInjuryTraitsStatusV1::available,
               injury.unavailable_reason, "injury_trait_reads_unavailable");
  const auto &death = state.death_record;
  output += "},\"death_record\":{\"status\":";
  AppendString(output, DeathRecordStatusName(death.status));
  output += ",\"reason_key\":";
  if (death.status == xar::game::BattleCurrentPersonDeathRecordStatusV1::available &&
      death.reason_key.has_value())
    AppendString(output, *death.reason_key);
  else
    output += "null";
  output += ",\"unavailable_reason\":";
  AppendReason(output,
               death.status != xar::game::BattleCurrentPersonDeathRecordStatusV1::unavailable,
               death.unavailable_reason, "death_record_unavailable");
  output += '}';
  if (state.raw_numeric_inputs) {
    output += ",\"raw_numeric_inputs\":";
    output += SerializeRawNumericInputs(*state.raw_numeric_inputs);
  }
  if (state.current_context_task_position_inputs) {
    output += ",\"current_context_task_position_inputs\":";
    output += SerializeCurrentContextTaskPositionInputsV1(*state.current_context_task_position_inputs);
  }
  if (state.context_branch_inputs) {
    output += ",\"context_branch_inputs\":";
    output += SerializeContextBranchInputs(*state.context_branch_inputs);
  }
  if (state.current_prior_context_inputs) {
    output += ",\"current_prior_context_inputs\":";
    output += SerializeCurrentPriorContextInputs(*state.current_prior_context_inputs);
  }
  if (state.current_context_source_inputs) {
    output += ",\"current_context_source_inputs\":";
    output += SerializeBattleCurrentPersonContextSourceInputsV1(
        *state.current_context_source_inputs);
  }
  output += '}';
  return output;
}

}  // namespace xar::bridge
