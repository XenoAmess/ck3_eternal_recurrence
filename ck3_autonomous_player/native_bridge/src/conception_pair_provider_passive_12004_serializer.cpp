#include "xar_bridge/conception_pair_provider_passive_12004.hpp"
#include <sstream>

namespace xar::ck3_12004 {
namespace {
template<typename T> void Optional(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << *value; else out << "null";
}
void Event(std::ostringstream &out, const PersonInstalledTransferEvent12004 &event) {
  out << "{\"clock_identity\":" << event.clock_identity
      << ",\"sequence\":" << event.sequence << ",\"thread_id\":";
  Optional(out,event.thread_id); out << '}';
}
} // namespace

std::string SerializeConceptionPairProviderObservation12004(
    const ConceptionPairProviderObservation12004 &r) {
  std::ostringstream out;
  out << std::boolalpha << "{\"source\":\"natural_original_pair_provider_first_qword\""
      << ",\"source_pin\":\"" << r.source_pin << "\",\"journal_sequence\":" << r.journal_sequence
      << ",\"parent\":{\"active\":" << r.parent.active
      << ",\"clock_identity\":" << r.parent.clock_identity
      << ",\"parent_scope_id\":" << r.parent.parent_scope_id
      << ",\"process_clock\":" << r.parent.process_clock
      << ",\"thread_id\":" << r.parent.thread_id
      << ",\"first_character\":" << r.parent.first_character
      << ",\"second_character\":" << r.parent.second_character
      << ",\"first_full_id\":" << r.parent.first_full_id
      << ",\"second_full_id\":" << r.parent.second_full_id
      << ",\"sample_receiver\":" << r.parent.sample_receiver << '}'
      << ",\"before_event\":"; Event(out,r.before_event);
  out << ",\"returned_event\":"; Event(out,r.returned_event);
  out << ",\"process_id\":" << r.process_id << ",\"thread_id\":" << r.thread_id
      << ",\"caller_return_pc\":" << r.caller_return_pc
      << ",\"caller_return_rva\":" << r.caller_return_rva
      << ",\"output_pointer\":" << r.output_pointer
      << ",\"first_character\":" << r.first_character
      << ",\"second_character\":" << r.second_character
      << ",\"mode\":" << r.mode << ",\"fifth_argument\":" << r.fifth_argument
      << ",\"output_before\":"; Optional(out,r.output_before);
  out << ",\"output_after\":"; Optional(out,r.output_after);
  out << ",\"first_full_id_before\":"; Optional(out,r.first_full_id_before);
  out << ",\"second_full_id_before\":"; Optional(out,r.second_full_id_before);
  out << ",\"first_full_id_after\":"; Optional(out,r.first_full_id_after);
  out << ",\"second_full_id_after\":"; Optional(out,r.second_full_id_after);
  out << ",\"native_return_bits\":" << r.native_return_bits
      << ",\"original_returned\":" << r.original_returned
      << ",\"native_return_matches_output\":" << r.native_return_matches_output
      << ",\"parent_extent_unchanged\":" << r.parent_extent_unchanged
      << ",\"event_clock_and_thread_match\":" << r.event_clock_and_thread_match
      << ",\"actual_caller_input_ready\":" << r.actual_caller_input_ready
      << ",\"capture_failure_flags\":" << r.capture_failure_flags << '}';
  return out.str();
}
} // namespace xar::ck3_12004
