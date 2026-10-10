#include "xar_bridge/army_observed_phase_query_12004.hpp"
#include <ostream>
#include <set>

// This is an offline compound readout. Subjects come from actual captured
// roster/resolution fields. They are owned readout keys; they do not claim that
// a current ArmyStrength query resolved a current CArmy object.
void EmitArmyNaturalOwnedJournalsPacket12004(std::ostream &stream) {
  using namespace xar::ck3_12004;
  std::set<std::uint32_t> subjects;
  const auto admit = [&](std::uint32_t full_id) {
    if (full_id != UINT32_MAX) subjects.insert(full_id);
  };
  for (const auto &record : ReadArmyNaturalPhaseJournal12004())
    for (auto id : record.scope.original_army_roster.ordered_full_ids) admit(id);
  for (const auto &event : ReadArmyRegularCoreJournal12004().events) {
    for (const auto &row : event.entry.army_refresh_occurrences)
      if (row.resolved_full_id) admit(static_cast<std::uint32_t>(*row.resolved_full_id));
  }
  for (const auto &event : ReadArmyGatheringDueNaturalJournal12004()) {
    for (const auto *frame : {&event.entry, &event.returned}) {
      for (const auto *armies : {&frame->queued_armies, &frame->roster_armies})
        for (const auto &army : *armies)
          if (army.receiver.resolution_complete && army.receiver.selected_full_id)
            admit(*army.receiver.selected_full_id);
    }
  }
  for (const auto &event : ReadArmyActualMonthfirstCleanupJournal12004().events)
    for (auto id : event.phase.original_army_roster.ordered_full_ids) admit(id);

  std::string packet = "{\"schema\":\"army_owned_natural_journal_readout_12004/1\","
      "\"synthetic_offline_fixture\":true,"
      "\"subject_basis\":\"captured_roster_and_resolved_full_ID_owned_readout_keys\","
      "\"current_ArmyStrength_availability\":null,\"current_game_load_epoch\":null,\"subjects\":[";
  bool first = true;
  const auto number = [](auto value) { return std::to_string(value); };
  const auto string = [](std::string &out, std::string_view value) {
    army_actual_monthfirst_cleanup_json_detail::String(out, value);
  };
  for (auto full_id : subjects) {
    if (!first) packet += ',';
    first = false;
    packet += "{\"captured_subject_full_carmy_id_u32\":" + std::to_string(full_id);
    // The two admission booleans select a known captured full-ID readout key.
    // The enclosing packet explicitly leaves current-query availability unknown.
    xar::game::AppendArmyObservedPhaseQuery12004(packet, true, true,
        static_cast<std::int32_t>(full_id), number, string);
    packet += '}';
  }
  packet += "]}";
  stream << packet;
}
