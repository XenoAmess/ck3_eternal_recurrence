#pragma once

#include "xar_bridge/army_late_context_copy12004.hpp"
#include "xar_bridge/army_late_context_copy12004_serializer.hpp"
#include <cstdint>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

namespace xar::game {
inline constexpr std::size_t kArmyActualCompiledEffectJournalCapacityV1 = 256;
enum class ArmyCompiledEffectSourceV1 : std::uint32_t { positive_1e0, flag30 };
inline const char *ArmyCompiledEffectSourceNameV1(ArmyCompiledEffectSourceV1 source) noexcept {
  return source == ArmyCompiledEffectSourceV1::positive_1e0 ? "positive_1e0" : "flag30";
}
struct ArmyActualCompiledEffectObservationV1 {
  std::uint64_t sequence = 0, entry_sequence = 0;
  std::uint64_t caller_return_rva = 0, callsite_rva = 0;
  std::uint32_t thread_id = 0, receiver_owner_offset = 0, capture_failure_flags = 0;
  std::int32_t native_carmy_id = -1;
  ArmyCompiledEffectSourceV1 source = ArmyCompiledEffectSourceV1::positive_1e0;
  std::uintptr_t incoming_receiver_address = 0, incoming_context_address = 0;
  std::optional<std::uint64_t> receiver_vptr_raw_u64;
  std::optional<std::uint32_t> negative_seed_receiver_key_2c_raw_u32;
  std::optional<std::uint8_t> effect_flag_raw_u8;
  ck3_12004::ArmyLateContextCopy12004 before{}, after{};
  std::uint64_t original_rax_raw_u64 = 0;
  bool original_returned = false, same_root_after = false;
};
struct ArmyActualCompiledEffectObservationsV1 {
  bool observer_installed = false, current_session_guard = false;
  std::uint64_t oldest_available_sequence = 0, latest_sequence = 0;
  std::uint64_t overwritten_events = 0, unattributed_capture_failures = 0;
  std::vector<ArmyActualCompiledEffectObservationV1> events;
};
// All values are owned copies of natural entry/return observations. A query only
// joins the full CArmy generation ID; it does not execute a compiled effect.
inline void AppendArmyActualCompiledEffectObservationsV1(
    std::string &output, const ArmyActualCompiledEffectObservationsV1 &observations) {
  std::ostringstream stream;
  stream << std::boolalpha
      << "{\"source\":\"native_natural_compiled_effect_entry_return\","
         "\"membership_basis\":\"current_full_carmy_id_join\","
         "\"observer_installed\":" << observations.observer_installed
      << ",\"current_session_guard\":" << observations.current_session_guard
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
        << ",\"entry_sequence\":" << event.entry_sequence
        << ",\"thread_id\":" << event.thread_id
        << ",\"native_carmy_id\":" << event.native_carmy_id
        << ",\"caller_return_rva\":" << event.caller_return_rva
        << ",\"callsite_rva\":" << event.callsite_rva
        << ",\"source_kind\":\"" << ArmyCompiledEffectSourceNameV1(event.source)
        << "\",\"receiver_owner_offset\":" << event.receiver_owner_offset
        << ",\"incoming_receiver_address_raw\":" << event.incoming_receiver_address
        << ",\"incoming_context_address_raw\":" << event.incoming_context_address
        << ",\"receiver_vptr_raw_u64\":";
    if (event.receiver_vptr_raw_u64) stream << *event.receiver_vptr_raw_u64;
    else stream << "null";
    stream << ",\"negative_seed_receiver_key_2c_raw_u32\":";
    if (event.negative_seed_receiver_key_2c_raw_u32)
      stream << *event.negative_seed_receiver_key_2c_raw_u32;
    else stream << "null";
    stream << ",\"effect_flag_raw_u8\":";
    if (event.effect_flag_raw_u8) stream << static_cast<unsigned>(*event.effect_flag_raw_u8);
    else stream << "null";
    stream << ",\"original_returned\":" << event.original_returned
        << ",\"original_rax_raw_u64\":" << event.original_rax_raw_u64
        << ",\"same_root_after\":" << event.same_root_after
        << ",\"capture_failure_flags\":" << event.capture_failure_flags
        << ",\"before_context\":" << ck3_12004::SerializeActualArmyLateContextCopy12004(event.before, {})
        << ",\"after_context\":" << ck3_12004::SerializeActualArmyLateContextCopy12004(event.after, {})
        << ",\"rng_fallback_observed\":false,\"derived_seed_raw_u32\":null,"
           "\"selected_effects_observed\":false,\"complete_effects_observed\":false,"
           "\"date_at_invocation\":null,\"frame_at_invocation\":null}";
  }
  stream << "]}";
  output += stream.str();
}
} // namespace xar::game
