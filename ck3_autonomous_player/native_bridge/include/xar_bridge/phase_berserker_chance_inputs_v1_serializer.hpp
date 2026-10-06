#pragma once

#include "xar_bridge/phase_berserker_chance_inputs_v1.hpp"
#include "xar_bridge/phase_berserker_validity_inputs_v1_serializer.hpp"

namespace xar::game {
inline void AppendPhaseBerserkerChanceBoolV1(std::string &out, const PhaseBerserkerChanceBoolV1 &value) {
  out += "{\"status\":\"";
  out += value.value ? "available" : "unavailable";
  out += "\",\"value\":"; AppendBerserkerOptionalBool(out, value.value);
  out += ",\"unavailable_reason\":";
  AppendBerserkerReason(out, value.value.has_value(), value.unavailable_reason); out += '}';
}
inline void AppendPhaseBerserkerChancePerkV1(std::string &out, const PhaseBerserkerChancePerkV1 &value) {
  out += "{\"definition_key\":";
  if (value.definition_key) AppendPhaseRiteStringV1(out, *value.definition_key); else out += "null";
  out += ",\"presence\":"; AppendPhaseBerserkerChanceBoolV1(out, value.presence); out += '}';
}
inline void AppendPhaseBerserkerChanceInputsV1(std::string &out, const PhaseBerserkerChanceInputsV1 &value) {
  out += "{\"source_character_id\":" + std::to_string(value.source_character_id) + ",\"is_ai\":";
  AppendPhaseBerserkerChanceBoolV1(out, value.is_ai);
  out += ",\"stalwart\":"; AppendPhaseBerserkerChancePerkV1(out, value.stalwart);
  const auto &dynasty = value.dynasty;
  out += ",\"dynasty\":{\"raw_house_id\":" + std::to_string(dynasty.raw_house_id) + ",\"house_id\":";
  AppendBerserkerOptionalRef(out, dynasty.house_id);
  out += ",\"raw_dynasty_id\":"; AppendBerserkerOptionalRef(out, dynasty.raw_dynasty_id);
  out += ",\"dynasty_id\":"; AppendBerserkerOptionalRef(out, dynasty.dynasty_id);
  out += ",\"house_resolution\":"; AppendPhaseRiteStringV1(out, dynasty.house_resolution);
  out += ",\"dynasty_resolution\":"; AppendPhaseRiteStringV1(out, dynasty.dynasty_resolution);
  out += ",\"warfare_legacy_3\":"; AppendPhaseBerserkerChancePerkV1(out, dynasty.warfare_legacy_3);
  const auto &acclaimed = value.acclaimed;
  out += "},\"acclaimed\":{\"raw_accolade_id\":"; AppendBerserkerOptionalRef(out, acclaimed.raw_accolade_id);
  out += ",\"accolade_id\":"; AppendBerserkerOptionalRef(out, acclaimed.accolade_id);
  out += ",\"resolution\":"; AppendPhaseRiteStringV1(out, acclaimed.resolution);
  out += ",\"is_acclaimed\":"; AppendPhaseBerserkerChanceBoolV1(out, acclaimed.is_acclaimed);
  out += "},\"traits\":{";
  for (std::size_t index = 0; index < value.traits.size(); ++index) {
    if (index) out += ',';
    AppendPhaseRiteStringV1(out, std::string(kPhaseBerserkerChanceTraitKeysV1[index])); out += ':';
    AppendPhaseBerserkerChanceBoolV1(out, value.traits[index]);
  }
  out += "}}";
}
} // namespace xar::game
