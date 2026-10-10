#pragma once
#include "xar_bridge/army_actual_assault_budget_observations_v1.hpp"
#include <string>

namespace xar::game {
template<class Number>
inline void AppendActualAssaultBudgetEvent12004(std::string &out,
    const ck3_12004::ArmyNaturalPhaseEvent12004 &value, Number number) {
  out += "{\"clock_identity\":" + number(value.clock_identity);
  out += ",\"sequence\":" + number(value.sequence) + ",\"thread_id\":";
  out += value.thread_id ? number(*value.thread_id) : "null"; out += '}';
}
template<class Number>
inline void AppendActualAssaultBudgetReceiver12004(std::string &out,
    const ck3_12004::ActualAssaultBudgetReceiver12004 &value, Number number) {
  out += "{\"siege_full_id_u32\":";
  out += value.siege_full_id ? number(*value.siege_full_id) : "null";
  out += ",\"province_identity\":";
  out += value.province_identity ? number(*value.province_identity) : "null";
  out += ",\"province_full_id_u32\":";
  out += value.province_full_id ? number(*value.province_full_id) : "null";
  out += ",\"province_magic_raw_u32\":";
  out += value.province_magic ? number(*value.province_magic) : "null";
  out += ",\"breach_level_raw_i32\":";
  out += value.breach_level ? number(*value.breach_level) : "null";
  out += ",\"identity_complete\":"; out += value.identity_complete ? "true" : "false"; out += '}';
}
template<class Number, class JsonString>
inline void AppendArmyActualAssaultBudgetObservationsV1(std::string &out,
    const ck3_12004::ArmyActualAssaultBudgetObservationsV1 &value,
    Number number, JsonString string) {
  out += "{\"schema_version\":1,\"source\":";
  string(out, "native_actual_daily_assault_budget_child");
  out += ",\"stage\":"; string(out, "natural_25205A0_return_under_2A97EB0");
  out += ",\"observer_installed\":"; out += value.observer_installed ? "true" : "false";
  out += ",\"latest_journal_sequence\":" + number(value.latest_journal_sequence);
  out += ",\"overwritten_events\":" + number(value.overwritten_events) + ",\"events\":[";
  bool first = true;
  for (const auto &row : value.events) {
    if (!first) out += ','; first = false;
    out += "{\"journal_sequence\":" + number(row.journal_sequence);
    out += ",\"getter_entry_rva\":" + number(row.getter_entry_rva);
    out += ",\"actual_caller_return_rva\":" + number(row.actual_caller_return_rva);
    out += ",\"observed_thread_id\":" + number(row.observed_thread_id);
    out += ",\"selected_siege_identity\":" + number(row.selected_siege_identity);
    out += ",\"parent\":{\"active\":"; out += row.parent.active ? "true" : "false";
    out += ",\"exact_post_date_parent\":"; out += row.parent.exact_post_date_parent ? "true" : "false";
    out += ",\"actual_entry_rva\":" + number(row.parent.actual_entry_rva);
    out += ",\"caller_return_rva\":";
    out += row.parent.caller_return_rva ? number(*row.parent.caller_return_rva) : "null";
    out += ",\"manager_identity\":" + number(row.parent.manager_identity);
    out += ",\"entry_event\":"; AppendActualAssaultBudgetEvent12004(out, row.parent.entry_event, number);
    out += ",\"phase_entry_event\":"; AppendActualAssaultBudgetEvent12004(out, row.parent.phase_entry_event, number);
    out += ",\"date_raw_u64\":"; out += row.parent.date_raw ? number(*row.parent.date_raw) : "null";
    out += ",\"absolute_day_raw_u32\":"; out += row.parent.absolute_day_raw ? number(*row.parent.absolute_day_raw) : "null";
    out += "},\"entry_event\":"; AppendActualAssaultBudgetEvent12004(out, row.entry_event, number);
    out += ",\"returned_event\":"; AppendActualAssaultBudgetEvent12004(out, row.returned_event, number);
    out += ",\"entry_receiver\":"; AppendActualAssaultBudgetReceiver12004(out, row.entry_receiver, number);
    out += ",\"returned_receiver\":"; AppendActualAssaultBudgetReceiver12004(out, row.returned_receiver, number);
    out += ",\"original_called\":"; out += row.original_called ? "true" : "false";
    out += ",\"original_returned\":"; out += row.original_returned ? "true" : "false";
    out += ",\"raw_return_bits_u64\":" + number(row.raw_return_bits);
    out += ",\"consumed_eax_raw_u32\":" + number(row.consumed_eax_u32);
    out += ",\"native_expected_loss_i32\":" + number(row.native_expected_loss_i32);
    out += ",\"parent_still_active\":"; out += row.parent_still_active ? "true" : "false";
    out += ",\"same_clock_thread_order\":"; out += row.same_clock_thread_order ? "true" : "false";
    out += ",\"receiver_identity_unchanged\":"; out += row.receiver_identity_unchanged ? "true" : "false";
    out += ",\"parent_group_budget_recorded\":"; out += row.parent_group_budget_recorded ? "true" : "false";
    out += ",\"full_besieging_dependencies_captured\":false}";
  }
  out += "]}";
}
} // namespace xar::game
