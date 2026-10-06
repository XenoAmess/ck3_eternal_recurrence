#pragma once

#include "xar_bridge/phase_berserker_validity_inputs_v1.hpp"
#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"

namespace xar::game {
inline void AppendBerserkerOptionalRef(std::string &out, const std::optional<std::uint32_t> &value) {
  out += value ? std::to_string(*value) : "null";
}
inline void AppendBerserkerOptionalBool(std::string &out, const std::optional<bool> &value) {
  out += value ? (*value ? "true" : "false") : "null";
}
inline void AppendBerserkerReason(std::string &out, bool available, const std::string &reason) {
  if (available) out += "null";
  else AppendPhaseRiteStringV1(out, reason);
}
inline void AppendPhaseBerserkerValidityInputsV1(std::string &out, const PhaseBerserkerValidityInputsV1 &value) {
  const auto &culture = value.culture;
  out += "{\"source_character_id\":" + std::to_string(value.source_character_id) + ",\"culture\":{\"status\":\"";
  out += culture.available ? "available" : "unavailable";
  out += "\",\"raw_culture_id\":" + std::to_string(culture.raw_culture_id) + ",\"culture_id\":";
  AppendBerserkerOptionalRef(out, culture.culture_id);
  out += ",\"resolution\":"; AppendPhaseRiteStringV1(out, culture.resolution);
  out += ",\"selected_pillar_keys\":";
  if (culture.selected_pillar_keys) {
    out += '[';
    for (std::size_t i = 0; i < culture.selected_pillar_keys->size(); ++i) {
      if (i) out += ',';
      AppendPhaseRiteStringV1(out, (*culture.selected_pillar_keys)[i]);
    }
    out += ']';
  } else out += "null";
  out += ",\"heritage_north_germanic\":"; AppendBerserkerOptionalBool(out, culture.heritage_north_germanic);
  out += ",\"unavailable_reason\":"; AppendBerserkerReason(out, culture.available, culture.unavailable_reason);
  const auto &religion = value.religion;
  out += "},\"religion\":{\"status\":\"";
  out += religion.available ? "available" : "unavailable";
  out += "\",\"raw_adopted_rite_id\":" + std::to_string(religion.raw_adopted_rite_id) + ",\"rite_id\":";
  AppendBerserkerOptionalRef(out, religion.rite_id);
  out += ",\"raw_faith_id\":"; AppendBerserkerOptionalRef(out, religion.raw_faith_id);
  out += ",\"faith_id\":"; AppendBerserkerOptionalRef(out, religion.faith_id);
  out += ",\"raw_religion_id\":"; AppendBerserkerOptionalRef(out, religion.raw_religion_id);
  out += ",\"religion_id\":"; AppendBerserkerOptionalRef(out, religion.religion_id);
  out += ",\"resolution\":"; AppendPhaseRiteStringV1(out, religion.resolution);
  out += ",\"religion_key\":";
  if (religion.religion_key) AppendPhaseRiteStringV1(out, *religion.religion_key);
  else out += "null";
  out += ",\"germanic\":"; AppendBerserkerOptionalBool(out, religion.germanic);
  out += ",\"unavailable_reason\":"; AppendBerserkerReason(out, religion.available, religion.unavailable_reason);
  out += "},\"traits\":{";
  constexpr std::array<const char *, 3> keys{"craven", "berserker", "calm"};
  for (std::size_t i = 0; i < value.traits.size(); ++i) {
    if (i) out += ',';
    AppendPhaseRiteStringV1(out, keys[i]);
    out += ":{\"status\":\"";
    out += value.traits[i].value ? "available" : "unavailable";
    out += "\",\"value\":"; AppendBerserkerOptionalBool(out, value.traits[i].value);
    out += ",\"unavailable_reason\":";
    AppendBerserkerReason(out, value.traits[i].value.has_value(), value.traits[i].unavailable_reason);
    out += '}';
  }
  out += "}}";
}
} // namespace xar::game
