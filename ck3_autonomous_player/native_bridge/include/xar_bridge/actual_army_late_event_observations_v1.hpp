#pragma once

#include "xar_bridge/army_late_context_copy12004.hpp"
#include "xar_bridge/army_late_context_copy12004_serializer.hpp"
#include <cstdint>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace xar::game {
inline constexpr std::size_t kArmyActualLateEventJournalCapacityV1 = 256;
enum class ArmyLateEventSourceV1 : std::uint32_t { positive_1e0, flag21, flag30 };
inline const char *ArmyLateEventSourceNameV1(ArmyLateEventSourceV1 source) noexcept {
  switch (source) {
  case ArmyLateEventSourceV1::positive_1e0: return "positive_1e0";
  case ArmyLateEventSourceV1::flag21: return "flag21";
  default: return "flag30";
  }
}
struct ArmyLateEventDefinitionV1 {
  std::uintptr_t definition_address = 0;
  std::optional<bool> actual_loaded_table_slot_equal;
  bool row_copy_complete = false;
  std::int32_t row_index_raw = 0;
  std::uintptr_t trigger_address = 0, primary_effect_address = 0;
  std::uintptr_t recursive_definition_address = 0, alternate_effect_address = 0;
};
struct ArmyActualLateEventObservationV1 {
  std::uint64_t sequence = 0, caller_return_rva = 0;
  std::int32_t native_carmy_id = -1;
  ArmyLateEventSourceV1 source = ArmyLateEventSourceV1::positive_1e0;
  std::uint32_t definition_table_offset = 0, capture_failure_flags = 0;
  std::uintptr_t effect_callback_address = 0, event_callback_address = 0;
  ck3_12004::ArmyLateContextCopy12004 before{}, after{};
  ck3_12004::ArmyLateContextSourceRoles12004 before_roles{}, after_roles{};
  ArmyLateEventDefinitionV1 definition{};
  bool original_returned = false, same_root_after = false;
};
struct ArmyActualLateEventObservationsV1 {
  bool observer_installed = false;
  std::uint64_t oldest_available_sequence = 0, latest_sequence = 0;
  std::uint64_t overwritten_events = 0, unattributed_capture_failures = 0;
  std::vector<ArmyActualLateEventObservationV1> events;
};
// Owned journal only; current query cannot call the event dispatcher, mutate a
// scope, regenerate a seed, execute a trigger, or infer historical effects.
inline void AppendArmyActualLateEventObservationsV1(
    std::string &output, const ArmyActualLateEventObservationsV1 &observations) {
  std::ostringstream stream;
  stream << std::boolalpha
      << "{\"source\":\"native_natural_late_event_dispatch_entry_return\","
         "\"membership_basis\":\"current_full_carmy_id_join\","
         "\"observer_installed\":" << observations.observer_installed
      << ",\"oldest_available_sequence\":" << observations.oldest_available_sequence
      << ",\"latest_sequence\":" << observations.latest_sequence
      << ",\"overwritten_events\":" << observations.overwritten_events
      << ",\"unattributed_capture_failures\":" << observations.unattributed_capture_failures
      << ",\"event_count\":" << observations.events.size() << ",\"events\":[";
  bool first = true;
  for (const auto &event : observations.events) {
    if (!first) stream << ',';
    first = false;
    stream << "{\"sequence\":" << event.sequence
        << ",\"native_carmy_id\":" << event.native_carmy_id
        << ",\"caller_return_rva\":" << event.caller_return_rva
        << ",\"source_kind\":\"" << ArmyLateEventSourceNameV1(event.source)
        << "\",\"definition_table_offset\":" << event.definition_table_offset
        << ",\"original_returned\":" << event.original_returned
        << ",\"same_root_after\":" << event.same_root_after
        << ",\"capture_failure_flags\":" << event.capture_failure_flags
        << ",\"before_context\":" << ck3_12004::SerializeActualArmyLateContextCopy12004(event.before, event.before_roles)
        << ",\"after_context\":" << ck3_12004::SerializeActualArmyLateContextCopy12004(event.after, event.after_roles)
        << ",\"definition_input\":{\"address_raw\":" << event.definition.definition_address
        << ",\"actual_loaded_table_slot_equal\":";
    if (event.definition.actual_loaded_table_slot_equal) stream << *event.definition.actual_loaded_table_slot_equal;
    else stream << "null";
    stream << ",\"row_copy_complete\":" << event.definition.row_copy_complete << ",\"row_index_raw\":";
    if (event.definition.row_copy_complete) stream << event.definition.row_index_raw;
    else stream << "null";
    stream << ",\"trigger_address_raw\":" << event.definition.trigger_address
        << ",\"primary_effect_address_raw\":" << event.definition.primary_effect_address
        << ",\"recursive_definition_address_raw\":" << event.definition.recursive_definition_address
        << ",\"alternate_effect_address_raw\":" << event.definition.alternate_effect_address
        << "},\"effect_callback_address_raw\":" << event.effect_callback_address
        << ",\"event_callback_address_raw\":" << event.event_callback_address
        << ",\"trigger_result_observed\":false,\"selected_effects_observed\":false,"
           "\"complete_effects_observed\":false,\"date_at_invocation\":null,"
           "\"late_parent_predicate_pc\":null}";
  }
  stream << "]}";
  output += stream.str();
}
} // namespace xar::game
