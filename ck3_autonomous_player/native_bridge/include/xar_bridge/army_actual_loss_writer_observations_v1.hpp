#pragma once

#include <array>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

inline constexpr std::size_t kArmyActualLossWriterMaximumDataRecordsV1 = 64;
inline constexpr std::size_t kArmyActualLossWriterJournalCapacityV1 = 512;

enum class ArmyActualLossWriterCallerV1 : std::uint32_t {
  supply_preferred,
  siege_or_raid_preferred,
  residual_allocator,
  other_writer_caller,
};

inline constexpr std::string_view ArmyActualLossWriterCallerNameV1(
    ArmyActualLossWriterCallerV1 caller) noexcept {
  switch (caller) {
  case ArmyActualLossWriterCallerV1::supply_preferred:
    return "supply_preferred";
  case ArmyActualLossWriterCallerV1::siege_or_raid_preferred:
    return "siege_or_raid_preferred";
  case ArmyActualLossWriterCallerV1::residual_allocator:
    return "residual_allocator";
  default:
    return "other_writer_caller";
  }
}

enum ArmyActualLossWriterCaptureFailureV1 : std::uint32_t {
  army_actual_loss_capture_none = 0,
  army_actual_loss_capture_before = 1U << 0,
  army_actual_loss_capture_after = 1U << 1,
  army_actual_loss_capture_clock = 1U << 2,
  army_actual_loss_capture_data_header = 1U << 3,
  army_actual_loss_capture_data_record = 1U << 4,
  army_actual_loss_capture_physical_before = 1U << 5,
  army_actual_loss_capture_physical_after = 1U << 6,
  army_actual_loss_capture_data_truncated = 1U << 7,
  army_actual_loss_capture_data_changed = 1U << 8,
};

struct ArmyActualLossWriterPhysicalValuesV1 {
  std::optional<std::int32_t> maximum_soldiers;
  std::optional<std::int32_t> current_soldiers;
  std::optional<std::int32_t> state_raw;
};

struct ArmyActualLossWriterPhysicalSlotV1 {
  ArmyActualLossWriterPhysicalValuesV1 before;
  ArmyActualLossWriterPhysicalValuesV1 after;
  bool same_instance_after = false;
};

struct ArmyActualLossWriterDataAliasV1 {
  std::int32_t data_record_index = -1;
  std::optional<std::int32_t> persistent_regiment_id;
  std::optional<std::int32_t> data_chunk_ordinal;
  std::optional<std::int32_t> physical_slot_index;
};

struct ArmyActualLossWriterObservationV1 {
  std::uint64_t sequence = 0;
  std::int32_t army_regiment_id = -1;
  std::int64_t request_raw = 0;
  std::optional<std::uint64_t> caller_return_rva;
  ArmyActualLossWriterCallerV1 caller =
      ArmyActualLossWriterCallerV1::other_writer_caller;
  std::optional<std::int32_t> observed_date_raw;
  std::optional<std::int32_t> before_current_soldiers;
  std::optional<std::int32_t> before_maximum_soldiers;
  std::optional<std::int32_t> after_current_soldiers;
  std::optional<std::int32_t> after_maximum_soldiers;
  bool same_instance_after = false;
  std::uint32_t capture_failure_flags = army_actual_loss_capture_none;
  std::optional<std::int32_t> native_data_record_count;
  std::uint32_t captured_data_record_count = 0;
  std::uint32_t physical_slot_count = 0;
  bool physical_capture_complete = false;
  // Only complete, identity-matched physical reads can populate this value.
  // Signed before-minus-after is retained; cached raised deltas never fill it.
  std::optional<std::int64_t> actual_physical_soldier_debit;
  std::array<ArmyActualLossWriterDataAliasV1,
             kArmyActualLossWriterMaximumDataRecordsV1> data_aliases{};
  std::array<ArmyActualLossWriterPhysicalSlotV1,
             kArmyActualLossWriterMaximumDataRecordsV1> physical_slots{};
};

struct ArmyActualLossWriterObservationsV1 {
  bool observer_installed = false;
  std::uint64_t oldest_available_sequence = 0;
  std::uint64_t latest_sequence = 0;
  std::uint64_t overwritten_events = 0;
  std::uint64_t unattributed_capture_failures = 0;
  std::vector<ArmyActualLossWriterObservationV1> events;
};

namespace army_actual_loss_writer_json_v1 {
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
inline void PhysicalValues(std::string &output,
                           const ArmyActualLossWriterPhysicalValuesV1 &value) {
  output += "{\"current_soldiers\":";
  OptionalNumber(output, value.current_soldiers);
  output += ",\"maximum_soldiers\":";
  OptionalNumber(output, value.maximum_soldiers);
  output += ",\"state_raw\":";
  OptionalNumber(output, value.state_raw);
  output += '}';
}
} // namespace army_actual_loss_writer_json_v1

// Appends only the owned observation object. No native reads occur here.
inline void AppendArmyActualLossWriterObservationsV1(
    std::string &output, const ArmyActualLossWriterObservationsV1 &observations) {
  using namespace army_actual_loss_writer_json_v1;
  output += "{\"status\":\"available\",\"source\":\"native_natural_writer_entry_return\","
            "\"membership_basis\":\"membership_at_query\",\"observer_installed\":";
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
    output += ",\"army_regiment_id\":";
    Number(output, event.army_regiment_id);
    output += ",\"request_raw\":";
    Number(output, event.request_raw);
    output += ",\"request_scale\":100000,\"caller_return_rva\":";
    OptionalNumber(output, event.caller_return_rva);
    output += ",\"caller_kind\":\"";
    output += ArmyActualLossWriterCallerNameV1(event.caller);
    output += "\",\"observed_date_raw\":";
    OptionalNumber(output, event.observed_date_raw);
    output += ",\"before_current_soldiers\":";
    OptionalNumber(output, event.before_current_soldiers);
    output += ",\"before_maximum_soldiers\":";
    OptionalNumber(output, event.before_maximum_soldiers);
    output += ",\"after_current_soldiers\":";
    OptionalNumber(output, event.after_current_soldiers);
    output += ",\"after_maximum_soldiers\":";
    OptionalNumber(output, event.after_maximum_soldiers);
    output += ",\"same_instance_after\":";
    output += event.same_instance_after ? "true" : "false";
    output += ",\"cached_current_delta\":";
    if (event.same_instance_after && event.before_current_soldiers &&
        event.after_current_soldiers)
      Number(output, static_cast<std::int64_t>(*event.after_current_soldiers) -
                         *event.before_current_soldiers);
    else output += "null";
    output += ",\"cached_maximum_delta\":";
    if (event.same_instance_after && event.before_maximum_soldiers &&
        event.after_maximum_soldiers)
      Number(output, static_cast<std::int64_t>(*event.after_maximum_soldiers) -
                         *event.before_maximum_soldiers);
    else output += "null";
    output += ",\"capture_failure_flags\":";
    Number(output, event.capture_failure_flags);
    output += ",\"native_data_record_count\":";
    OptionalNumber(output, event.native_data_record_count);
    output += ",\"captured_data_record_count\":";
    Number(output, event.captured_data_record_count);
    output += ",\"physical_capture_complete\":";
    output += event.physical_capture_complete ? "true" : "false";
    output += ",\"physical_debit_observed\":";
    output += event.actual_physical_soldier_debit ? "true" : "false";
    output += ",\"actual_physical_soldier_debit\":";
    OptionalNumber(output, event.actual_physical_soldier_debit);
    output += ",\"physical_slot_count\":";
    Number(output, event.physical_slot_count);
    output += ",\"data_aliases\":[";
    for (std::uint32_t index = 0; index < event.captured_data_record_count; ++index) {
      if (index != 0) output += ',';
      const auto &alias = event.data_aliases[index];
      output += "{\"data_record_index\":";
      Number(output, alias.data_record_index);
      output += ",\"persistent_regiment_id\":";
      OptionalNumber(output, alias.persistent_regiment_id);
      output += ",\"data_chunk_ordinal\":";
      OptionalNumber(output, alias.data_chunk_ordinal);
      output += ",\"physical_slot_index\":";
      OptionalNumber(output, alias.physical_slot_index);
      output += '}';
    }
    output += "],\"physical_slots\":[";
    for (std::uint32_t index = 0; index < event.physical_slot_count; ++index) {
      if (index != 0) output += ',';
      const auto &slot = event.physical_slots[index];
      output += "{\"physical_slot_index\":";
      Number(output, index);
      output += ",\"before\":";
      PhysicalValues(output, slot.before);
      output += ",\"after\":";
      PhysicalValues(output, slot.after);
      output += ",\"same_instance_after\":";
      output += slot.same_instance_after ? "true" : "false";
      output += '}';
    }
    output += "]}";
  }
  output += "]}";
}

} // namespace xar::game
