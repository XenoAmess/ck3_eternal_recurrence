#pragma once

#include "xar_bridge/phase_event_calendar_observation_v1.hpp"
#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"

namespace xar::game {
template <class T> inline void AppendPhaseCalendarIntegerV1(
    std::string &out, const std::optional<T> &value) {
  out += value ? std::to_string(*value) : "null";
}
inline void AppendPhaseCalendarBooleanV1(
    std::string &out, const std::optional<bool> &value) {
  out += value ? (*value ? "true" : "false") : "null";
}
inline void AppendPhaseEventCalendarObservationV1(
    std::string &out, const PhaseEventCalendarObservationV1 &value) {
  out += "{\"schema_version\":1,\"scope\":\"v2_roster_character_calendar_condition\",\"status\":";
  AppendPhaseRiteStringV1(out, value.status);
  out += ",\"date_low32\":"; AppendPhaseCalendarIntegerV1(out, value.date_low32);
  out += ",\"next_date_low32\":"; AppendPhaseCalendarIntegerV1(out, value.next_date_low32);
  out += ",\"day_index\":"; AppendPhaseCalendarIntegerV1(out, value.day_index);
  out += ",\"next_day_index\":"; AppendPhaseCalendarIntegerV1(out, value.next_day_index);
  out += ",\"loaded_interval_days_raw\":";
  AppendPhaseCalendarIntegerV1(out, value.loaded_interval_days_raw);
  out += ",\"loaded_interval_source_closed\":";
  out += value.loaded_interval_source_closed ? "true" : "false";
  out += ",\"calendar_predicate_source_closed\":";
  out += value.calendar_predicate_source_closed ? "true" : "false";
  out += ",\"complete_phase_effects_ready\":false,\"source_ck3_sha256\":";
  AppendPhaseRiteStringV1(out, value.source_ck3_sha256);
  out += ",\"unavailable_reason\":";
  if (value.unavailable_reason.empty()) out += "null";
  else AppendPhaseRiteStringV1(out, value.unavailable_reason);
  out += ",\"occurrences\":[";
  for (std::size_t index = 0; index < value.occurrences.size(); ++index) {
    if (index) out += ',';
    const auto &row = value.occurrences[index];
    out += "{\"occurrence_index\":" + std::to_string(row.occurrence_index);
    out += ",\"character_id\":" + std::to_string(row.character_id);
    out += ",\"source_public_cunit_id\":" + std::to_string(row.source_public_cunit_id);
    out += ",\"source_native_carmy_id\":";
    AppendPhaseCalendarIntegerV1(out, row.source_native_carmy_id);
    out += ",\"source_regiment_id\":"; AppendPhaseCalendarIntegerV1(out, row.source_regiment_id);
    out += ",\"encounter_role\":"; AppendPhaseRiteStringV1(out, row.encounter_role);
    out += ",\"phase_role\":"; AppendPhaseRiteStringV1(out, row.phase_role);
    out += ",\"current_calendar_predicate\":";
    AppendPhaseCalendarBooleanV1(out, row.current_calendar_predicate);
    out += ",\"next_day_calendar_predicate\":";
    AppendPhaseCalendarBooleanV1(out, row.next_day_calendar_predicate);
    out += ",\"current_remainder_raw\":"; AppendPhaseCalendarIntegerV1(out, row.current_remainder_raw);
    out += ",\"next_remainder_raw\":"; AppendPhaseCalendarIntegerV1(out, row.next_remainder_raw);
    out += '}';
  }
  out += "]}";
}
} // namespace xar::game
