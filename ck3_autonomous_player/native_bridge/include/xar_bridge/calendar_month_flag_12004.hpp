#pragma once

#include "xar_bridge/army_source_derived_next_daily_supply_frame_v1.hpp"

#include <optional>

namespace xar::ck3_12004 {

// Actual344B source229C540..229C698 closes the day444C4B0 zero test,
// mask2 clear229C676 and final BYTE+C0 store229C68D. The existing clock
// producer supplies this same daily CDate domain, not the phase epoch.
// Root passes the existing next-clock field from the same Strength row that
// already contains the current rawC0/mask2 observer. No new read or write.
// This is a prospective pre-command branch input, not an observed future flag.
std::optional<bool> ProjectNextCalendarMonthFlag12004(
    const game::ArmySourceDerivedNextDailySupplyFrameInputsV1 &clock) noexcept;

} // namespace xar::ck3_12004
