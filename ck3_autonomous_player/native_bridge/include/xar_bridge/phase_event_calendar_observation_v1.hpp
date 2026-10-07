#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
// Conditional arithmetic on the V2 roster; no native candidate admission,
// event selection, dispatch, or committed effect is represented here.
struct PhaseEventCalendarOccurrenceV1 {
  std::uint32_t occurrence_index = 0;
  std::uint32_t character_id = 0;
  std::int32_t source_public_cunit_id = -1;
  std::optional<std::int32_t> source_native_carmy_id;
  std::optional<std::int32_t> source_regiment_id;
  std::string encounter_role;
  std::string phase_role;
  std::optional<bool> current_calendar_predicate;
  std::optional<bool> next_day_calendar_predicate;
  std::optional<std::uint32_t> current_remainder_raw;
  std::optional<std::uint32_t> next_remainder_raw;
  friend bool operator==(const PhaseEventCalendarOccurrenceV1 &,
                         const PhaseEventCalendarOccurrenceV1 &) = default;
};

struct PhaseEventCalendarObservationV1 {
  std::string status = "unavailable";
  std::optional<std::uint32_t> date_low32;
  std::optional<std::uint32_t> next_date_low32;
  std::optional<std::int32_t> day_index;
  std::optional<std::int32_t> next_day_index;
  std::optional<std::uint32_t> loaded_interval_days_raw;
  bool loaded_interval_source_closed = false;
  bool calendar_predicate_source_closed = false;
  std::string source_ck3_sha256 =
      "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
  std::string unavailable_reason = "actual4_calendar_operands_unavailable";
  std::vector<PhaseEventCalendarOccurrenceV1> occurrences;
  friend bool operator==(const PhaseEventCalendarObservationV1 &,
                         const PhaseEventCalendarObservationV1 &) = default;
};
} // namespace xar::game
