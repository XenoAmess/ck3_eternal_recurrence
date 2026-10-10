#pragma once

#include "xar_bridge/conception_sample_passive_12004.hpp"
#include <sstream>
#include <string>

namespace xar::ck3_12004 {
inline void AppendConceptionSampleObservations12004(
    std::string &output, const ConceptionSampleObservations12004 &observations) {
  std::ostringstream stream;
  stream << std::boolalpha
      << "{\"source\":\"natural_E46530_original_entry_return\","
         "\"build\":\"1.20.0.4\",\"source_pin\":\"" << kConceptionSampleSourcePin12004
      << "\",\"observer_installed\":" << observations.observer_installed
      << ",\"oldest_available_sequence\":" << observations.oldest_available_sequence
      << ",\"latest_sequence\":" << observations.latest_sequence
      << ",\"overwritten_events\":" << observations.overwritten_events
      << ",\"event_count\":" << observations.events.size() << ",\"events\":[";
  const auto write_event = [&stream](const PersonInstalledTransferEvent12004 &event) {
    stream << "{\"clock_identity\":" << event.clock_identity
        << ",\"sequence\":" << event.sequence << ",\"thread_id\":";
    if (event.thread_id) stream << *event.thread_id;
    else stream << "null";
    stream << '}';
  };
  const auto write_state = [&stream](const std::optional<std::array<std::uint32_t,2>> &state) {
    if (state) stream << '[' << (*state)[0] << ',' << (*state)[1] << ']';
    else stream << "null";
  };
  bool first = true;
  for (const auto &event : observations.events) {
    if (!first) stream << ',';
    first = false;
    stream << "{\"journal_sequence\":" << event.journal_sequence
        << ",\"source_pin\":\"" << event.source_pin
        << "\",\"parent\":{\"clock_identity\":" << event.parent.clock_identity
        << ",\"parent_scope_id\":" << event.parent.parent_scope_id
        << ",\"process_clock\":" << event.parent.process_clock
        << ",\"thread_id\":" << event.parent.thread_id
        << ",\"first_character\":" << event.parent.first_character
        << ",\"second_character\":" << event.parent.second_character
        << ",\"first_full_id\":" << event.parent.first_full_id
        << ",\"second_full_id\":" << event.parent.second_full_id
        << ",\"sample_receiver\":" << event.parent.sample_receiver << '}'
        << ",\"caller_return_rva\":" << event.caller_return_rva
        << ",\"receiver\":" << event.receiver
        << ",\"original_lower\":" << event.original_lower
        << ",\"original_upper\":" << event.original_upper
        << ",\"original_returned\":" << event.original_returned
        << ",\"returned_rax_signed64\":" << event.returned_rax
        << ",\"state_before_2dword\":";
    write_state(event.state_before);
    stream << ",\"state_after_2dword\":";
    write_state(event.state_after);
    stream << ",\"state_transition_matches_source\":";
    if (event.state_transition_matches_source) stream << *event.state_transition_matches_source;
    else stream << "null";
    stream << ",\"before_event\":";
    write_event(event.before_event);
    stream << ",\"returned_event\":";
    write_event(event.returned_event);
    stream << ",\"threshold_at_sample_signed64\":";
    if (event.threshold_at_sample) stream << *event.threshold_at_sample;
    else stream << "null";
    stream << ",\"threshold_capture_ready\":" << event.threshold_capture_ready
        << ",\"comparison_at_sample_passed\":";
    if (event.comparison_at_sample_passed) stream << *event.comparison_at_sample_passed;
    else stream << "null";
    stream << ",\"parent_extent_and_generation_unchanged\":"
        << event.parent_extent_and_generation_unchanged
        << ",\"event_clock_and_thread_match\":" << event.event_clock_and_thread_match
        << ",\"sample_within_source_range\":" << event.sample_within_source_range
        << ",\"causal_sample_ready\":" << event.causal_sample_ready
        << ",\"capture_failure_flags\":" << event.capture_failure_flags
        << ",\"native_class_name\":null,\"loaded_scalar_reconstruction\":null}";
  }
  stream << "]}";
  output += stream.str();
}
} // namespace xar::ck3_12004
