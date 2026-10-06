#pragma once

#include "xar_bridge/battle_current_finalizer_manager_inputs_v1.hpp"

#include <optional>
#include <string>

namespace xar::bridge {

inline void AppendCurrentFinalizerManagerInputsV1(
    std::string &output,
    const std::optional<game::BattleControlCurrentFinalizerManagerInputsV1>
        &inputs) {
  if (!inputs) {
    output += "null";
    return;
  }

  output += "{\"source_combat_id\":" +
            std::to_string(inputs->source_combat_id);
  output += ",\"combat_manager_row_admitted\":";
  output += inputs->combat_manager_row_admitted ? "true" : "false";
  output += ",\"pending_suppression_sweep_raw\":" +
            std::to_string(
                static_cast<unsigned int>(inputs->pending_suppression_sweep_raw));
  output += ",\"pending_suppression_sweep\":";
  output += inputs->pending_suppression_sweep ? "true" : "false";
  output += '}';
}

} // namespace xar::bridge
