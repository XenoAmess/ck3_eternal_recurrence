#include "xar_bridge/army_natural_phase_json_12004.hpp"
#include <ostream>
namespace xar::ck3_12004 {
namespace {
template<class T> void Optional(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value; else out << "null";
}
void Optional(std::ostream &out, const std::optional<std::uint8_t> &value) {
  if (value) out << static_cast<unsigned>(*value); else out << "null";
}
void Optional(std::ostream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false"); else out << "null";
}
const char *Phase(ArmyNaturalPhaseKind12004 phase) noexcept {
  if (phase == ArmyNaturalPhaseKind12004::pre_date) return "pre_date";
  if (phase == ArmyNaturalPhaseKind12004::post_date) return "post_date";
  return "unknown";
}
const char *Boundary(ArmyNaturalRosterBoundary12004 boundary) noexcept {
  if (boundary == ArmyNaturalRosterBoundary12004::parent_entry) return "parent_entry";
  if (boundary == ArmyNaturalRosterBoundary12004::pre_date_prefix_return) return "pre_date_prefix_return";
  return "unavailable";
}
void Roster(std::ostream &out, const ArmyNaturalPhaseRoster12004 &r) {
  out << "{\"boundary\":\"" << Boundary(r.boundary) << "\",\"capture_rva\":" << r.capture_rva;
  out << ",\"capture_event\":"; AppendArmyNaturalPhaseEvent12004(out, r.capture_event);
  out << ",\"begin_identity\":"; Optional(out, r.begin_identity);
  out << ",\"end_identity\":"; Optional(out, r.end_identity);
  out << ",\"count\":"; Optional(out, r.count);
  out << ",\"complete\":" << (r.complete ? "true" : "false") << ",\"ordered_full_ids\":[";
  bool first = true;
  for (auto id : r.ordered_full_ids) { if (!first) out << ','; first = false; out << id; }
  out << "]}";
}
} // namespace
void AppendArmyNaturalPhaseEvent12004(std::ostream &out, const ArmyNaturalPhaseEvent12004 &event) {
  out << "{\"clock_identity\":" << event.clock_identity << ",\"sequence\":" << event.sequence;
  out << ",\"thread_id\":"; Optional(out, event.thread_id); out << '}';
}
void AppendArmyNaturalPhaseScope12004(std::ostream &out, const ArmyNaturalPhaseScope12004 &s) {
  out << "{\"observed\":" << (s.observed ? "true" : "false") << ",\"phase\":\"" << Phase(s.phase);
  out << "\",\"actual_entry_rva\":" << s.actual_entry_rva << ",\"caller_return_rva\":" << s.caller_return_rva;
  out << ",\"primary_manager_identity\":" << s.primary_manager_identity;
  out << ",\"secondary_manager_identity\":" << s.secondary_manager_identity;
  out << ",\"game_state_identity\":" << s.game_state_identity;
  out << ",\"session_identity\":"; Optional(out, s.session_identity);
  out << ",\"entry_event\":"; AppendArmyNaturalPhaseEvent12004(out, s.entry_event);
  out << ",\"date_raw\":"; Optional(out, s.date_raw);
  out << ",\"prefix_date_raw\":"; Optional(out, s.prefix_date_raw);
  out << ",\"absolute_day_raw\":"; Optional(out, s.absolute_day_raw);
  out << ",\"entry_c0_raw\":"; Optional(out, s.entry_c0_raw);
  out << ",\"saved_c0_raw\":"; Optional(out, s.saved_c0_raw);
  out << ",\"saved_mask02_admitted\":"; Optional(out, s.saved_mask02_admitted);
  out << ",\"saved_c0_observed_rva\":" << s.saved_c0_observed_rva;
  out << ",\"saved_c0_event\":"; AppendArmyNaturalPhaseEvent12004(out, s.saved_c0_event);
  out << ",\"original_army_roster\":"; Roster(out, s.original_army_roster);
  out << '}';
}
void AppendArmyNaturalPhaseRecord12004(std::ostream &out, const ArmyNaturalPhaseRecord12004 &r) {
  out << "{\"scope\":"; AppendArmyNaturalPhaseScope12004(out, r.scope);
  out << ",\"original_called\":" << (r.original_called ? "true" : "false");
  out << ",\"original_returned\":" << (r.original_returned ? "true" : "false");
  out << ",\"raw_return_bits\":" << r.raw_return_bits << ",\"returned_event\":";
  AppendArmyNaturalPhaseEvent12004(out, r.returned_event);
  out << ",\"returned_date_raw\":"; Optional(out, r.returned_date_raw);
  out << ",\"returned_absolute_day_raw\":"; Optional(out, r.returned_absolute_day_raw);
  out << ",\"returned_c0_raw\":"; Optional(out, r.returned_c0_raw);
  out << ",\"same_clock_thread_order\":"; Optional(out, r.same_clock_thread_order);
  out << '}';
}
void AppendArmyNaturalPhaseJournal12004(std::ostream &out,
    const std::vector<ArmyNaturalPhaseRecord12004> &records) {
  out << '['; bool first = true;
  for (const auto &record : records) {
    if (!first) out << ','; first = false; AppendArmyNaturalPhaseRecord12004(out, record);
  }
  out << ']';
}
void AppendArmyNaturalPhaseJournalStatus12004(std::ostream &out,
    const ArmyNaturalPhaseJournalStatus12004 &s) {
  out << "{\"read_complete\":" << (s.read_complete ? "true" : "false")
      << ",\"capacity\":" << s.capacity << ",\"retained_records\":" << s.retained_records
      << ",\"appended_records\":" << s.appended_records << ",\"overwritten_records\":" << s.overwritten_records
      << ",\"failed_appends\":" << s.failed_appends << ",\"clear_operations\":" << s.clear_operations << '}';
}
} // namespace xar::ck3_12004
