#pragma once

#include "xar_bridge/council_assign_councillor_action_v1.hpp"

#include <cstdint>

namespace xar::ck3_11906 {

// The exact 1.19.0.6 CanConfirm chain reads only the full incumbent and task
// identities at confirmation+0x160/+0x164. A false native result is a legal
// denial; a false return from this adapter means the evaluation did not run.
using CouncilReplacementCanConfirmOverrideV1 = bool (*)(
    void *context, const void *confirmation) noexcept;

bool EvaluateCouncilReplacementFireabilityV1(
    const CouncilAssignCouncillorNativeEnvironmentV1 &environment,
    std::int32_t incumbent_character_id, std::int32_t active_task_id,
    bool &can_be_fired,
    CouncilReplacementCanConfirmOverrideV1 fixture_override = nullptr,
    void *fixture_context = nullptr) noexcept;

} // namespace xar::ck3_11906
