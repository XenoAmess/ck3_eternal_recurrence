#include "xar_bridge/conception_pair_passive_12004.hpp"
#include "xar_bridge/conception_sample_passive_12004_serializer.hpp"
#include <sstream>

namespace xar::ck3_12004 {
namespace {
template <typename T> void Number(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << *value; else out << "null";
}
void Byte(std::ostringstream &out, const std::optional<std::uint8_t> &value) {
  if (value) out << static_cast<unsigned>(*value); else out << "null";
}
template <typename T> void Raw64(std::ostringstream &out, const std::optional<T> &value) {
  if (value) out << '"' << *value << '"'; else out << "null";
}
void Boolean(std::ostringstream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false"); else out << "null";
}
void Clock(std::ostringstream &out, const PersonInstalledTransferEvent12004 &event) {
  out << "{\"clock_identity\":" << event.clock_identity
      << ",\"sequence\":" << event.sequence << ",\"thread_id\":";
  Number(out, event.thread_id);
  out << '}';
}
void State(std::ostringstream &out, const std::optional<std::array<std::uint32_t, 2>> &state) {
  if (state) out << '[' << (*state)[0] << ',' << (*state)[1] << ']';
  else out << "null";
}
void Character(std::ostringstream &out, const ConceptionPairCharacterFacts12004 &facts) {
  out << "{\"character\":" << facts.character << ",\"full_id\":";
  Number(out, facts.full_id);
  out << ",\"magic\":"; Number(out, facts.magic);
  out << ",\"native_sex_1a1\":"; Byte(out, facts.native_sex_1a1);
  out << ",\"extended_pointer\":"; Number(out, facts.extended_pointer);
  out << ",\"extended_288_raw\":"; Raw64(out, facts.extended_288_raw);
  out << ",\"extended_288_blocks\":"; Boolean(out, facts.extended_288_blocks);
  out << ",\"pending_3e8_raw\":"; Byte(out, facts.pending_3e8_raw);
  out << ",\"pending_3f0_raw\":"; Number(out, facts.pending_3f0_raw);
  out << '}';
}
void Source(std::ostringstream &out, const ConceptionPairSourceCopies12004 &source) {
  out << "{\"scalar_5c69ec8_raw\":"; Raw64(out, source.scalar_5c69ec8_raw);
  out << ",\"lower_5c69f00_raw\":"; Raw64(out, source.lower_5c69f00_raw);
  out << ",\"upper_5c69f10_raw\":"; Raw64(out, source.upper_5c69f10_raw);
  out << ",\"actual_original_consumed_values\":false}";
}
}

std::string SerializeConceptionPairPassiveJournal12004(
    const ConceptionPairPassiveJournal12004 &journal) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":\"xar.ck3.conception-pair-passive-12004.v1\","
      "\"source\":\"natural_2929B40_original_once\",\"build_version\":\"1.20.0.4\","
      "\"source_pin\":\"" << kConceptionPairPassiveSourcePin12004
      << "\",\"image_base\":" << journal.image_base
      << ",\"observer_installed\":" << journal.observer_installed
      << ",\"current_session_guard\":" << journal.current_session_guard
      << ",\"clock_identity\":" << journal.clock_identity
      << ",\"oldest_available_sequence\":" << journal.oldest_available_sequence
      << ",\"latest_sequence\":" << journal.latest_sequence
      << ",\"overwritten_events\":" << journal.overwritten_events
      << ",\"unattributed_identity_events\":" << journal.unattributed_identity_events
      << ",\"event_count\":" << journal.events.size() << ",\"events\":[";
  bool first = true;
  for (const auto &event : journal.events) {
    if (!first) out << ',';
    first = false;
    out << "{\"journal_sequence\":" << event.journal_sequence
        << ",\"source_pin\":\"" << event.source_pin
        << "\",\"caller_return_pc\":" << event.caller_return_pc
        << ",\"caller_return_rva\":";
    Number(out, event.caller_return_rva);
    out << ",\"process_id\":" << event.process_id << ",\"thread_id\":" << event.thread_id
        << ",\"before_event\":"; Clock(out, event.before_event);
    out << ",\"completed_event\":"; Clock(out, event.completed_event);
    out << ",\"first_character\":" << event.first_character
        << ",\"second_character\":" << event.second_character
        << ",\"sample_receiver\":" << event.sample_receiver
        << ",\"original_r9_modifier\":\"" << event.original_r9_modifier
        << "\",\"first_before\":"; Character(out, event.first_before);
    out << ",\"second_before\":"; Character(out, event.second_before);
    out << ",\"first_after\":"; Character(out, event.first_after);
    out << ",\"second_after\":"; Character(out, event.second_after);
    out << ",\"sample_state_before_2dword\":"; State(out, event.sample_state_before);
    out << ",\"sample_state_after_2dword\":"; State(out, event.sample_state_after);
    out << ",\"source_before\":"; Source(out, event.source_before);
    out << ",\"source_after\":"; Source(out, event.source_after);
    out << ",\"original_called_once\":" << event.original_called_once
        << ",\"original_returned\":" << event.original_returned
        << ",\"original_rax_bits\":"; Raw64(out, event.original_rax_bits);
    out << ",\"original_al\":"; Byte(out, event.original_al);
    out << ",\"generation_unchanged\":"; Boolean(out, event.generation_unchanged);
    out << ",\"first_post_pending_matches_write_pattern\":";
    Boolean(out, event.first_post_pending_matches_write_pattern);
    out << ",\"event_clock_and_thread_match\":" << event.event_clock_and_thread_match
        << ",\"duplicate_provider_returns\":" << event.duplicate_provider_returns
        << ",\"duplicate_sample_returns\":" << event.duplicate_sample_returns
        << ",\"fixture_origin\":" << event.fixture_origin << ",\"provider\":";
    if (event.provider) out << SerializeConceptionPairProviderObservation12004(*event.provider);
    else out << "null";
    out << ",\"sample\":";
    if (event.sample) {
      ConceptionSampleObservations12004 sample;
      sample.events.push_back(*event.sample);
      sample.oldest_available_sequence = event.sample->journal_sequence;
      sample.latest_sequence = event.sample->journal_sequence;
      std::string wire;
      AppendConceptionSampleObservations12004(wire, sample);
      out << wire;
    } else out << "null";
    out << '}';
  }
  out << "]}";
  return out.str();
}
} // namespace xar::ck3_12004
