#include "xar_bridge/person_installed_transfer_capture_12004.hpp"
#include "xar_bridge/person_transfer_postimage_12004_serializer.hpp"

#include <iomanip>
#include <sstream>

namespace xar::ck3_12004 {
namespace {
void Quoted(std::ostringstream &out, std::string_view value) {
  out << '"';
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') out << '\\' << static_cast<char>(ch);
    else if (ch < 0x20) {
      out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
          << static_cast<unsigned>(ch) << std::dec << std::setfill(' ');
    } else out << static_cast<char>(ch);
  }
  out << '"';
}
void Address(std::ostringstream &out, std::uintptr_t value) {
  out << "\"0x" << std::hex << value << std::dec << '"';
}
void Address(std::ostringstream &out, std::optional<std::uintptr_t> value) {
  if (value) Address(out, *value);
  else out << "null";
}
template <class T> void Number(std::ostringstream &out, std::optional<T> value) {
  if (value) out << *value;
  else out << "null";
}
void Boolean(std::ostringstream &out, std::optional<bool> value) {
  if (value) out << (*value ? "true" : "false");
  else out << "null";
}
void Event(std::ostringstream &out, const PersonInstalledTransferEvent12004 &event) {
  out << "{\"clock_identity\":";
  Address(out, event.clock_identity);
  out << ",\"sequence\":" << event.sequence << ",\"thread_id\":";
  Number(out, event.thread_id);
  out << '}';
}
void Preparation(std::ostringstream &out, const PersonInstalledTransferPreparation12004 &p) {
  out << "{\"observed\":" << (p.observed ? "true" : "false")
      << ",\"preparation_capture_complete\":" << (p.preparation_capture_complete ? "true" : "false")
      << ",\"preparation_capture_sequence\":" << p.preparation_capture_sequence
      << ",\"preparation_capture_thread_id\":";
  Number(out, p.preparation_capture_thread_id);
  out << ",\"preparation_completion_thread_id\":";
  Number(out, p.preparation_completion_thread_id);
  out << ",\"preparation_character_identity\":";
  Address(out, p.preparation_character_identity);
  out << ",\"preparation_model_identity\":";
  Address(out, p.preparation_model_identity);
  out << ",\"preparation_context_identity\":";
  Address(out, p.preparation_context_identity);
  out << ",\"preparation_owner_character_identity\":";
  Address(out, p.preparation_owner_character_identity);
  out << ",\"preparation_owner_character_id\":";
  Number(out, p.preparation_owner_character_id);
  out << '}';
}
void Snapshot(std::ostringstream &out, const PersonInstalledTransferSnapshot12004 &s) {
  out << "{\"model_a_owner_identity\":"; Address(out, s.model_a_owner_identity);
  out << ",\"model_a_owner_character_id\":"; Number(out, s.model_a_owner_character_id);
  out << ",\"model_b_owner_identity\":"; Address(out, s.model_b_owner_identity);
  out << ",\"model_b_owner_character_id\":"; Number(out, s.model_b_owner_character_id);
  out << ",\"observed_owner_identity\":"; Address(out, s.observed_owner_identity);
  out << ",\"observed_owner_character_id\":"; Number(out, s.observed_owner_character_id);
  out << ",\"carrier_identity\":"; Address(out, s.carrier_identity);
  out << ",\"installed_model_identity\":"; Address(out, s.installed_model_identity);
  out << ",\"installed_model_owner_identity\":"; Address(out, s.installed_model_owner_identity);
  out << ",\"installed_owner_matches_observed_owner\":"; Boolean(out, s.installed_owner_matches_observed_owner);
  out << ",\"installed_model_is_a\":"; Boolean(out, s.installed_model_is_a);
  out << ",\"installed_model_is_b\":"; Boolean(out, s.installed_model_is_b);
  out << ",\"matching_installed_inline_context_identity\":"; Address(out, s.matching_installed_inline_context_identity);
  out << '}';
}
void Stage(std::ostringstream &out, const PersonInstalledTransferStage12004 &s) {
  out << "{\"observation_stage\":\"actual_paired_transfer_return\",\"observed\":"
      << (s.observed ? "true" : "false") << ",\"original_called\":"
      << (s.original_called ? "true" : "false") << ",\"original_returned\":"
      << (s.original_returned ? "true" : "false") << ",\"reason\":";
  Quoted(out, s.reason);
  out << ",\"model_a_identity\":"; Address(out, s.model_a_identity);
  out << ",\"model_b_identity\":"; Address(out, s.model_b_identity);
  out << ",\"original_return_rva\":"; Address(out, s.original_return_rva);
  out << ",\"before_event\":"; Event(out, s.before_event);
  out << ",\"completed_event\":"; Event(out, s.completed_event);
  out << ",\"preparation\":"; Preparation(out, s.preparation);
  out << ",\"before\":"; Snapshot(out, s.before);
  out << ",\"after\":"; Snapshot(out, s.after);
  out << ",\"preparation_model_is_b\":"; Boolean(out, s.preparation_model_is_b);
  out << ",\"preparation_owner_matches_before\":"; Boolean(out, s.preparation_owner_matches_before);
  out << ",\"preparation_owner_matches_after\":"; Boolean(out, s.preparation_owner_matches_after);
  out << ",\"before_after_owner_generation_equal\":"; Boolean(out, s.before_after_owner_generation_equal);
  out << ",\"event_clock_and_thread_match\":"; Boolean(out, s.event_clock_and_thread_match);
  out << ",\"completion_ordered_after_begin\":"; Boolean(out, s.completion_ordered_after_begin);
  out << ",\"generic_postimages_complete\":false,\"transfer_to_entry_association_proven\":false"
      << ",\"observer_model_write_performed\":false,\"full_person_ready\":false,\"entry_ready\":false}";
}
} // namespace

std::string SerializePersonInstalledTransferCapture12004(
    const PersonInstalledTransferCaptureQuery12004 &query) {
  std::ostringstream out;
  out << "{\"schema\":"; Quoted(out, kPersonInstalledTransferCaptureSchema12004);
  out << ",\"build_version\":\"1.20.0.4\",\"executable_sha256\":";
  Quoted(out, kPersonInstalledTransferCaptureExeSha12004);
  out << ",\"historical_capture\":true,\"configured\":" << (query.configured ? "true" : "false")
      << ",\"installed\":" << (query.installed ? "true" : "false")
      << ",\"install_failure_flags\":" << query.install_failure_flags
      << ",\"request_filtered\":" << (query.request_filtered ? "true" : "false")
      << ",\"snapshot_revision\":";
  Number(out, query.snapshot_revision);
  out << ",\"observed_date_raw\":"; Number(out, query.observed_date_raw);
  out << ",\"requested_receiver_count\":" << query.requested_receiver_count
      << ",\"unresolved_receiver_count\":" << query.unresolved_receiver_count
      << ",\"latest_record_sequence\":" << query.latest_record_sequence
      << ",\"overwritten_records\":" << query.overwritten_records << ",\"records\":[";
  bool first = true;
  for (const auto &record : query.records) {
    if (!first) out << ',';
    first = false;
    out << "{\"record_sequence\":" << record.record_sequence
        << ",\"offline_fixture\":" << (record.offline_fixture ? "true" : "false")
        << ",\"stage\":";
    Stage(out, record.stage);
    out << ",\"physical_postimage\":";
    if (record.physical_postimage)
      out << SerializePersonTransferPhysicalPostimage12004(*record.physical_postimage);
    else out << "null";
    out << '}';
  }
  out << "]}";
  return out.str();
}

} // namespace xar::ck3_12004
