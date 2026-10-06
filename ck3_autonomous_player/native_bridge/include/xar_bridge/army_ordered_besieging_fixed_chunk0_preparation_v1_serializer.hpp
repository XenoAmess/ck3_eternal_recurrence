#pragma once
#include "xar_bridge/army_ordered_besieging_fixed_chunk0_preparation_v1.hpp"
#include "xar_bridge/army_fixed_chunk0_preparation_v1_serializer.hpp"

namespace xar::game {
template<class Number, class JsonString>
inline void AppendOrderedBesiegingFixedChunk0PreparationInputsV1(
    std::string &out, const ArmyOrderedBesiegingFixedChunk0PreparationInputsV1 &inputs,
    Number number, JsonString append_json_string) {
  out += "{\"source\":\"native_ordered_besieging_fixed_chunk0_preparation_inputs\",";
  out += "\"entry_kind\":\"current_frozen_context_preparation\",";
  out += "\"scope_kind\":\"actual_ordered_besieging_target_physical_union\",";
  AppendFixedChunk0PreparationStatusV1(out, inputs.status, inputs.unavailable_reason, append_json_string);
  out += ",\"source_scope_status\":\"";
  out += FixedChunk0PreparationInputStatusNameV1(inputs.source_scope_status);
  out += "\",\"subject_army_id\":" + number(inputs.subject_army_id);
  out += ",\"subject_carmy_id\":" + number(inputs.subject_carmy_id);
  out += ",\"province_id\":" + number(inputs.province_id);
  out += ",\"target_persistent_ids_complete\":";
  out += inputs.target_persistent_ids_complete ? "true" : "false";
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
