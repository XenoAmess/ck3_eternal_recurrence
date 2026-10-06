#pragma once

#include "xar_bridge/phase_rite_parameters_v1.hpp"
#include <string_view>

namespace xar::game {
inline void AppendPhaseRiteStringV1(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const auto c : value) {
    const auto byte = static_cast<unsigned char>(c);
    if (c == '\\' || c == '"') { out += '\\'; out += c; }
    else if (byte < 32) {
      out += "\\u00"; out += hex[byte >> 4]; out += hex[byte & 15];
    } else out += c;
  }
  out += '"';
}
inline void AppendPhaseRiteParametersV1(std::string &out, const PhaseRiteParametersV1 &value) {
  out += "{\"status\":\"";
  out += value.status == PhaseRiteParameterStatusV1::available ? "available" :
         value.status == PhaseRiteParameterStatusV1::absent ? "absent" : "unavailable";
  out += "\",\"source_character_id\":" + std::to_string(value.source_character_id);
  out += ",\"raw_adopted_rite_id\":" + std::to_string(value.raw_adopted_rite_id);
  out += ",\"rite_id\":" + (value.rite_id ? std::to_string(*value.rite_id) : "null");
  out += ",\"faith_id\":" + (value.faith_id ? std::to_string(*value.faith_id) : "null");
  out += ",\"boolean_parameters_complete\":";
  out += value.boolean_parameters_complete ? "true" : "false";
  out += ",\"boolean_parameter_keys\":[";
  for (std::size_t i = 0; i < value.boolean_parameter_keys.size(); ++i) {
    if (i) out += ',';
    AppendPhaseRiteStringV1(out, value.boolean_parameter_keys[i]);
  }
  out += "],\"unavailable_reason\":";
  if (value.status == PhaseRiteParameterStatusV1::unavailable)
    AppendPhaseRiteStringV1(out, value.unavailable_reason);
  else out += "null";
  out += '}';
}
} // namespace xar::game
