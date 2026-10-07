#pragma once

#include "xar_bridge/game_contract.hpp"

namespace xar::bridge {
// The Root-run fixture definition projects production bridge.cpp's literal
// AppendCombatSimulationInputs. No bridge DLL export or parallel serializer.
std::string SerializeCombatSimulationInputsV2(
    const game::CombatSimulationInputsSnapshot &snapshot);
} // namespace xar::bridge
