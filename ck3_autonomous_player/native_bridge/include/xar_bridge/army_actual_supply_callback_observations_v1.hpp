#pragma once

#include <charconv>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

inline constexpr std::size_t kArmyActualSupplyCallbackJournalCapacityV1 = 512;

struct ArmyActualSupplyCallbackValuesV1 {
  std::optional<std::int64_t> supply_raw;
  std::optional<std::uint64_t> last_supply_update_date_raw64;
  std::optional<std::uint8_t> supply_updated_byte_raw;
};

struct ArmyActualSupplyCallbackObservationV1 {
  std::uint64_t sequence = 0;
  std::int32_t army_id = -1;
  std::int32_t native_carmy_id = -1;
  std::optional<std::uint64_t> passed_date_raw64;
  std::optional<std::uint64_t> caller_return_rva;
  ArmyActualSupplyCallbackValuesV1 before;
  ArmyActualSupplyCallbackValuesV1 after;
  bool same_instance_after = false;
  std::uint32_t capture_failure_flags = 0;
};

struct ArmyActualSupplyCallbackObservationsV1 {
  bool observer_installed = false;
  std::uint64_t oldest_available_sequence = 0;
  std::uint64_t latest_sequence = 0;
  std::uint64_t overwritten_events = 0;
  std::uint64_t unattributed_capture_failures = 0;
  std::vector<ArmyActualSupplyCallbackObservationV1> events;
};

namespace army_actual_supply_callback_json_v1 {
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
inline void Values(std::string &output,
                   const ArmyActualSupplyCallbackValuesV1 &value) {
  output += "{\"supply_raw\":";
  OptionalNumber(output, value.supply_raw);
  output += ",\"last_supply_update_date_raw64\":";
  OptionalNumber(output, value.last_supply_update_date_raw64);
  output += ",\"supply_updated_byte_raw\":";
  OptionalNumber(output, value.supply_updated_byte_raw);
  output += '}';
}
} // namespace army_actual_supply_callback_json_v1

// Serializes only owned snapshots; no native reads occur here.
inline void AppendArmyActualSupplyCallbackObservationsV1(
    std::string &output,
    const ArmyActualSupplyCallbackObservationsV1 &observations) {
  using namespace army_actual_supply_callback_json_v1;
  output += "{\"status\":\"available\","
            "\"source\":\"native_natural_supply_callback_entry_return\","
            "\"identity_basis\":\"public_unit_and_native_carmy_full_ids_at_invocation\","
            "\"observer_installed\":";
  output += observations.observer_installed ? "true" : "false";
  output += ",\"oldest_available_sequence\":";
  Number(output, observations.oldest_available_sequence);
  output += ",\"latest_sequence\":";
  Number(output, observations.latest_sequence);
  output += ",\"overwritten_events\":";
  Number(output, observations.overwritten_events);
  output += ",\"unattributed_capture_failures\":";
  Number(output, observations.unattributed_capture_failures);
  output += ",\"event_count\":";
  Number(output, observations.events.size());
  output += ",\"events\":[";
  bool first = true;
  for (const auto &event : observations.events) {
    if (!first) output += ',';
    first = false;
    output += "{\"sequence\":";
    Number(output, event.sequence);
    output += ",\"army_id\":";
    Number(output, event.army_id);
    output += ",\"native_carmy_id\":";
    Number(output, event.native_carmy_id);
    output += ",\"passed_date_raw64\":";
    OptionalNumber(output, event.passed_date_raw64);
    output += ",\"caller_return_rva\":";
    OptionalNumber(output, event.caller_return_rva);
    output += ",\"before\":";
    Values(output, event.before);
    output += ",\"after\":";
    Values(output, event.after);
    output += ",\"same_instance_after\":";
    output += event.same_instance_after ? "true" : "false";
    output += ",\"capture_failure_flags\":";
    Number(output, event.capture_failure_flags);
    output += '}';
  }
  output += "]}";
}

} // namespace xar::game
