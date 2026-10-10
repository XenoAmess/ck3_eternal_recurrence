#pragma once

#include "xar_bridge/army_battle_casualty_observations_v1.hpp"

#include <charconv>
#include <optional>
#include <string>
#include <string_view>

namespace xar::game {
namespace army_battle_casualty_json_v1 {

template <typename Integer>
inline void Number(std::string &output, Integer value) {
  char buffer[32]{};
  const auto converted = std::to_chars(buffer, buffer + sizeof(buffer), value);
  output.append(buffer, converted.ptr);
}

template <typename Integer>
inline void OptionalNumber(std::string &output,
                           const std::optional<Integer> &value) {
  if (value) Number(output, *value);
  else output += "null";
}

inline void Key(std::string &output, std::string_view key) {
  output += ",\"";
  output += key;
  output += "\":";
}

template <typename Integer>
inline void Field(std::string &output, std::string_view key, Integer value) {
  Key(output, key);
  Number(output, value);
}

template <typename Integer>
inline void OptionalField(std::string &output, std::string_view key,
                          const std::optional<Integer> &value) {
  Key(output, key);
  OptionalNumber(output, value);
}

inline void BooleanField(std::string &output, std::string_view key, bool value) {
  Key(output, key);
  output += value ? "true" : "false";
}

inline void Owner(std::string &output,
                  const ArmyBattleCasualtyOwnerResolutionV1 &owner) {
  output += "{\"reference_demanded\":";
  output += owner.reference_demanded ? "true" : "false";
  OptionalField(output, "requested_full_id", owner.requested_full_id);
  OptionalField(output, "resolved_full_id", owner.resolved_full_id);
  Key(output, "used_fallback");
  output += owner.used_fallback
      ? (*owner.used_fallback ? "true" : "false") : "null";
  BooleanField(output, "read_complete", owner.read_complete);
  output += '}';
}

} // namespace army_battle_casualty_json_v1

// Appends completed owned observations only. Native reads belong to the journal.
inline void AppendArmyBattleCasualtyObservationsV1(
    std::string &output, const ArmyBattleCasualtyObservationsV1 &observations) {
  using namespace army_battle_casualty_json_v1;
  output += "{\"status\":\"available\","
            "\"source\":\"native_battle_casualty_application_entry_return\","
            "\"membership_basis\":\"membership_at_query\",\"observer_installed\":";
  output += observations.observer_installed ? "true" : "false";
  Field(output, "oldest_available_sequence", observations.oldest_available_sequence);
  Field(output, "latest_sequence", observations.latest_sequence);
  Field(output, "overwritten_events", observations.overwritten_events);
  Field(output, "event_count", observations.events.size());
  output += ",\"events\":[";
  bool first = true;
  for (const auto &event : observations.events) {
    if (!first) output += ',';
    first = false;
    output += "{\"sequence\":";
    Number(output, event.sequence);
    Field(output, "entry_identity", event.entry_identity);
    OptionalField(output, "entry_army_regiment_id", event.entry_army_regiment_id);
    Field(output, "soft_request_raw", event.soft_request_raw);
    Field(output, "hard_request_raw", event.hard_request_raw);
    output += ",\"raw_scale\":100000,\"soldiers_scale\":1";
    OptionalField(output, "observed_date_raw", event.observed_date_raw);
    OptionalField(output, "before_fighting_raw", event.before_fighting_raw);
    OptionalField(output, "before_soft_raw", event.before_soft_raw);
    OptionalField(output, "after_fighting_raw", event.after_fighting_raw);
    OptionalField(output, "after_soft_raw", event.after_soft_raw);
    BooleanField(output, "same_entry_after", event.same_entry_after);
    Field(output, "nested_writer_event_count", event.nested_writer_event_count);
    OptionalField(output, "writer_sequence", event.writer_sequence);
    OptionalField(output, "writer_army_regiment_id", event.writer_army_regiment_id);
    OptionalField(output, "writer_request_raw", event.writer_request_raw);
    BooleanField(output, "entry_writer_association_proven", event.entry_writer_association_proven);
    BooleanField(output, "physical_capture_complete", event.physical_capture_complete);
    OptionalField(output, "actual_physical_soldier_debit", event.actual_physical_soldier_debit);
    Key(output, "owner_army"); Owner(output, event.owner_army);
    Key(output, "owner_unit"); Owner(output, event.owner_unit);
    OptionalField(output, "owner_character_id", event.owner_character_id);
    Field(output, "original_return_identity", event.original_return_identity);
    OptionalField(output, "owner_hard_ledger_after_raw", event.owner_hard_ledger_after_raw);
    output += '}';
  }
  output += "]}";
}

} // namespace xar::game
