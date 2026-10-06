#pragma once

#include "xar_bridge/ck3_12003_fixed_chunk0_preparation.hpp"
#include <string>

namespace xar::game {
template<class JsonString>
inline void AppendFixedChunk0PreparationStatusV1(
    std::string &out, FixedChunk0PreparationInputStatusV1 value,
    std::string_view reason, JsonString append_json_string) {
  out += "\"status\":\"";
  out += FixedChunk0PreparationInputStatusNameV1(value);
  out += "\",\"ready\":";
  out += value == FixedChunk0PreparationInputStatusV1::available ? "true" : "false";
  out += ",\"unavailable_reason\":";
  if (reason.empty()) out += "null";
  else append_json_string(out, reason);
}

template<class Number, class JsonString>
inline void AppendFixedChunk0PreparationPersistentInputV1(
    std::string &out, const FixedChunk0PreparationPersistentInputV1 &row,
    Number number, JsonString append_json_string) {
  const auto integer = [&](std::string_view key, const auto &value) {
    out += ",\""; out += key; out += "\":";
    out += value ? number(*value) : "null";
  };
  out += "{\"persistent_regiment_id\":" + number(row.persistent_regiment_id);
  out += ",\"fixed_chunk_index\":0,";
  AppendFixedChunk0PreparationStatusV1(out, row.status, row.unavailable_reason, append_json_string);
  integer("containing_guard_138_raw", row.containing_guard_138_raw);
  integer("containing_definition_magic_38", row.containing_definition_magic_38);
  out += ",\"native_fixed_chunk0_can_replenish\":";
  out += row.native_fixed_chunk0_can_replenish
      ? (*row.native_fixed_chunk0_can_replenish ? "true" : "false") : "null";
  integer("fresh_fraction_raw", row.fresh_fraction_raw);
  out += ",\"fraction_scale\":100000}";
}

template<class Number, class JsonString>
inline void AppendFixedChunk0PreparationInputsV1(
    std::string &out, const FixedChunk0PreparationInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  const auto status = [&](FixedChunk0PreparationInputStatusV1 value,
                          std::string_view reason) {
    AppendFixedChunk0PreparationStatusV1(out, value, reason, append_json_string);
  };
  out += "{\"source\":\"native_scoped_fixed_chunk0_preparation_inputs\",";
  out += "\"entry_kind\":\"current_frozen_context_preparation\",";
  status(inputs.status, inputs.unavailable_reason);
  out += ",\"subject_army_id\":" + number(inputs.subject_army_id);
  out += ",\"subject_carmy_id\":" + number(inputs.subject_carmy_id);
  out += ",\"referenced_persistent_ids_complete\":";
  out += inputs.referenced_persistent_ids_complete ? "true" : "false";
  out += ",\"persistent_regiments\":[";
  bool first = true;
  for (const auto &row : inputs.persistent_regiments) {
    if (!first) out += ',';
    first = false;
    AppendFixedChunk0PreparationPersistentInputV1(out, row, number, append_json_string);
  }
  out += "]}";
}
} // namespace xar::game
