#pragma once

#include "xar_bridge/phase_warmonger_core_v1.hpp"
#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"

namespace xar::game {
inline void AppendPhaseWarmongerCoreV1(std::string &out, const PhaseWarmongerCoreV1 &value) {
  out += "{\"status\":\"";
  out += value.available ? "available" : "unavailable";
  out += "\",\"source_character_id\":" + std::to_string(value.source_character_id);
  out += ",\"raw_adopted_rite_id\":" + std::to_string(value.raw_adopted_rite_id);
  out += ",\"rite_id\":" + (value.rite_id ? std::to_string(*value.rite_id) : "null");
  out += ",\"rite_resolution\":";
  AppendPhaseRiteStringV1(out, value.rite_resolution);
  out += ",\"requested_tenet_key\":\"tenet_warmonger\",\"target_tenet_key\":";
  if (value.target_tenet_key) AppendPhaseRiteStringV1(out, *value.target_tenet_key);
  else out += "null";
  out += ",\"warmonger_core_membership\":";
  if (value.warmonger_core_membership) out += *value.warmonger_core_membership ? "true" : "false";
  else out += "null";
  out += ",\"unavailable_reason\":";
  if (value.available) out += "null";
  else AppendPhaseRiteStringV1(out, value.unavailable_reason);
  out += '}';
}
} // namespace xar::game
