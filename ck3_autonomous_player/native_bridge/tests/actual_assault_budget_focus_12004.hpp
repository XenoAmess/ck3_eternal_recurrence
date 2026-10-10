#pragma once
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <cstdint>

namespace xar::ck3_12004::focus {
inline constexpr std::uintptr_t kActualBudgetFocusRawReturn12004 = 0xA1B2C3D400000007ULL;
// Prepare outside the natural phase. Run is called by37's fake original only
// inside real37 TLS under the real33 shared phase clock; this file owns no main.
void PrepareActualAssaultBudgetFocus12004(
    std::uintptr_t raw_return_bits = kActualBudgetFocusRawReturn12004);
std::uintptr_t RunActualAssaultBudgetFocus12004(void *selected_siege);
void VerifyActualAssaultBudgetFocus12004(
    const ArmyNaturalPhaseEvent12004 &parent_entry_event, bool expected_group_bound = true);
void RunExcludedActualAssaultBudgetFocus12004(void *selected_siege);
} // namespace xar::ck3_12004::focus
