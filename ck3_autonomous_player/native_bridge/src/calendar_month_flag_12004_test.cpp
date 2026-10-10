#include "calendar_month_flag_12004.hpp"

#include <cstdint>
#include <iostream>
#include <stdexcept>

namespace {
void Require(bool condition, const char *message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}
} // namespace

int main() {
  try {
    // New focused predicate scenes. These caller-owned literal bytes do not
    // rerun the already qualified calendar arithmetic or any native callback.
    xar::game::ArmySourceDerivedNextDailySupplyFrameInputsV1 clock;
    clock.status = "available";
    clock.ready = true;
    clock.source_derived_full_cdate64_ready = true;
    clock.source_derived_next_calendar_day_u8 = std::uint8_t{28};
    clock.source_derived_next_calendar_month_u8 = std::uint8_t{0};
    const auto outside_month_first =
        xar::ck3_12004::ProjectNextCalendarMonthFlag12004(clock);
    Require(outside_month_first && !*outside_month_first,
            "month0 cannot substitute for nonzero DOM");

    clock.source_derived_next_calendar_day_u8 = std::uint8_t{0};
    clock.source_derived_next_calendar_month_u8 = std::uint8_t{7};
    const auto month_first =
        xar::ck3_12004::ProjectNextCalendarMonthFlag12004(clock);
    Require(month_first && *month_first,
            "DOM0 in any month must select source-derived mask2");

    clock.source_derived_next_calendar_day_u8 = std::uint8_t{128};
    const auto unsigned_reload_branch =
        xar::ck3_12004::ProjectNextCalendarMonthFlag12004(clock);
    Require(unsigned_reload_branch && !*unsigned_reload_branch,
            "negative signed-byte branch reloads nonzero unsigned DOM");

    clock.source_derived_next_calendar_day_u8 = std::uint8_t{0};
    clock.source_derived_full_cdate64_ready = false;
    Require(!xar::ck3_12004::ProjectNextCalendarMonthFlag12004(clock),
            "old low32/D clock cannot acquire a month-first predicate");

    clock.source_derived_full_cdate64_ready = true;
    clock.source_derived_next_calendar_day_u8.reset();
    Require(!xar::ck3_12004::ProjectNextCalendarMonthFlag12004(clock),
            "missing DOM remains unknown rather than zero");

    clock.source_derived_next_calendar_day_u8 = std::uint8_t{0};
    clock.ready = false;
    Require(!xar::ck3_12004::ProjectNextCalendarMonthFlag12004(clock),
            "unavailable clock does not derive a future branch input");

    std::cout << "{\"schema\":\"xar-calendar-month-flag-focused-v1\","
                 "\"status\":\"GREEN\",\"checks\":6,"
                 "\"synthetic_literal_input\":true,"
                 "\"calendar_arithmetic_replayed\":false,"
                 "\"actual_future_flag_observed\":false,"
                 "\"native_callbacks\":0,\"game_calls\":0}\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
