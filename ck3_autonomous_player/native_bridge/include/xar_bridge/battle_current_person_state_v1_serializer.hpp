#pragma once

#include "xar_bridge/game_contract.hpp"

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

}  // namespace battle_current_person_state_v1_detail

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
  output += '}';
  return output;
}

}  // namespace xar::bridge
