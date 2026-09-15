#pragma once

#include "xar_bridge/council_application_main_v1.hpp"

namespace xar::bridge {

// Bind as CouncilApplicationMainConfigurationV1::evaluate_action_gates with
// action_gate_context pointing at the owning CouncilApplicationMainContextV1.
// This callback never advertises a worker command by itself.
bool EvaluateCouncilAssignCouncillorProductionGatesV1(
    void *context, const game::CouncilAssignCouncillorFrameV1 &frame,
    std::int32_t candidate_character_id,
    game::CouncilAssignCouncillorFinalLegalityV1 &output) noexcept;

} // namespace xar::bridge
