#include "calendar_month_flag_12004.hpp"

namespace xar::ck3_12004 {

std::optional<bool> ProjectNextCalendarMonthFlag12004(
    const game::ArmySourceDerivedNextDailySupplyFrameInputsV1 &clock) noexcept {
  if (!clock.ready || !clock.source_derived_full_cdate64_ready ||
      !clock.source_derived_next_calendar_day_u8) {
    return std::nullopt;
  }
  // Actual229C609 signed byte load and229C659 unsigned reload have the
  // same zero predicate, including nonzero high-bit bytes. Do not classify
  // from the packed month, present C0 flag, current date or phase remainder.
  return *clock.source_derived_next_calendar_day_u8 == 0;
}

} // namespace xar::ck3_12004
