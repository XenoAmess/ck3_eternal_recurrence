#include "xar_bridge/entry_final_side_capture_12004.hpp"

#include <iomanip>
#include <sstream>

namespace xar::ck3_12004 {
namespace {
void Quoted(std::ostream &out, std::string_view value) {
  out << '"';
  for (const auto c : value) {
    if (c == '"' || c == '\\') out << '\\' << c;
    else if (c == '\n') out << "\\n";
    else if (c == '\r') out << "\\r";
    else if (c == '\t') out << "\\t";
    else if (static_cast<unsigned char>(c) < 0x20)
      out << "\\u00" << std::hex << std::setw(2) << std::setfill('0')
          << static_cast<unsigned int>(static_cast<unsigned char>(c)) << std::dec;
    else out << c;
  }
  out << '"';
}
void Pointer(std::ostream &out, std::uintptr_t value) {
  out << '"' << "0x" << std::hex << value << std::dec << '"';
}
void U64(std::ostream &out, std::uint64_t value) { out << '"' << value << '"'; }
template <typename T> void OptionalNumber(std::ostream &out, std::optional<T> value) {
  if (value) out << *value; else out << "null";
}
void OptionalPointer(std::ostream &out, std::optional<std::uintptr_t> value) {
  if (value) Pointer(out, *value); else out << "null";
}
void OptionalU64(std::ostream &out, std::optional<std::uint64_t> value) {
  if (value) U64(out, *value); else out << "null";
}
void OptionalBool(std::ostream &out, std::optional<bool> value) {
  if (value) out << (*value ? "true" : "false"); else out << "null";
}
void Event(std::ostream &out, const PersonInstalledTransferEvent12004 &value) {
  out << "{\"clock_identity\":"; Pointer(out, value.clock_identity);
  out << ",\"sequence\":"; U64(out, value.sequence);
  out << ",\"thread_id\":"; OptionalNumber(out, value.thread_id);
  out << '}';
}
void Identity(std::ostream &out, const EntryFinalSideIdentity12004 &value) {
  out << "{\"occurrence\":"; Event(out, value.occurrence);
  out << ",\"side_identity\":"; Pointer(out, value.side_identity);
  out << ",\"province_identity\":"; Pointer(out, value.province_identity);
  out << ",\"caller_return_rva\":"; U64(out, value.caller_return_rva);
  out << ",\"caller_return_slot\":"; Pointer(out, value.caller_return_slot);
  out << ",\"source_side_index\":"; OptionalNumber(out, value.source_side_index);
  out << '}';
}
void Header(std::ostream &out, const EntryFinalSideBucketHeader12004 &value) {
  out << "{\"data_identity\":"; OptionalPointer(out, value.data_identity);
  out << ",\"count_i32\":"; OptionalNumber(out, value.count_i32);
  out << '}';
}
void Slot(std::ostream &out, const EntryFinalSidePhysicalSlot12004 &value) {
  out << "{\"bucket_id\":";
  Quoted(out, value.bucket == EntryFinalSideBucket12004::levy ? "levy" : "men_at_arms");
  out << ",\"bucket_index\":"; U64(out, value.bucket_index);
  out << ",\"traversal_ordinal\":"; U64(out, value.traversal_ordinal);
  out << ",\"entry_identity\":"; Pointer(out, value.entry_identity);
  out << ",\"writer_return_rva\":"; U64(out, value.writer_return_rva);
  out << ",\"raw_before\":";
  if (!value.raw_before) out << "null";
  else {
    out << '"';
    for (const auto byte : *value.raw_before)
      out << std::hex << std::setw(2) << std::setfill('0')
          << static_cast<unsigned int>(byte);
    out << std::dec << '"';
  }
  out << '}';
}
void Preceding(std::ostream &out, const EntryPrecedingRecord12004 &value) {
  out << "{\"record_sequence\":"; U64(out, value.record_sequence);
  out << ",\"install_epoch\":"; U64(out, value.install_epoch);
  out << ",\"offline_fixture\":" << (value.offline_fixture ? "true" : "false");
  out << ",\"original_returned\":" << (value.original_returned ? "true" : "false");
  out << ",\"identity_stable\":" << (value.identity_stable ? "true" : "false");
  out << ",\"combat_identity\":"; Pointer(out, value.combat_identity);
  out << ",\"combat_full_id_before\":"; OptionalNumber(out, value.combat_full_id_before);
  out << ",\"combat_full_id_after\":"; OptionalNumber(out, value.combat_full_id_after);
  out << ",\"caller_return_rva\":"; U64(out, value.caller_return_rva);
  out << ",\"caller_return_slot\":"; Pointer(out, value.caller_return_slot);
  out << ",\"original_begin\":"; Event(out, value.original_begin);
  out << ",\"original_completion\":"; Event(out, value.original_completion);
  out << ",\"raw_return_bits\":"; U64(out, value.raw_return_bits);
  out << ",\"outer_invocation\":"; OptionalU64(out, value.outer_invocation);
  out << '}';
}
void Record(std::ostream &out, const EntryFinalSideCaptureRecord12004 &value) {
  out << "{\"record_sequence\":"; U64(out, value.record_sequence);
  out << ",\"install_epoch\":"; U64(out, value.install_epoch);
  out << ",\"offline_fixture\":" << (value.offline_fixture ? "true" : "false");
  out << ",\"identity\":"; Identity(out, value.scope.identity);
  out << ",\"levy_header\":"; Header(out, value.scope.levy_header);
  out << ",\"maa_header\":"; Header(out, value.scope.maa_header);
  out << ",\"physical_copy_complete\":" << (value.scope.copy_complete ? "true" : "false");
  out << ",\"physical_copy_reason\":"; Quoted(out, value.scope.reason);
  out << ",\"physical_slots\":[";
  for (std::size_t i = 0; i != value.scope.physical_slots.size(); ++i) {
    if (i) out << ',';
    Slot(out, value.scope.physical_slots[i]);
  }
  out << "],\"preceding\":";
  if (value.preceding) Preceding(out, *value.preceding); else out << "null";
  out << ",\"original_called\":" << (value.original_called ? "true" : "false");
  out << ",\"original_returned\":" << (value.original_returned ? "true" : "false");
  out << ",\"raw_return_bits\":"; U64(out, value.raw_return_bits);
  out << ",\"completed_event\":"; Event(out, value.completed_event);
  out << ",\"writer_retention_complete\":" << (value.writer_retention_complete ? "true" : "false");
  out << ",\"writer_occurrences_cover_copied_slots\":";
  OptionalBool(out, value.writer_occurrences_cover_copied_slots);
  out << ",\"writer_records\":[";
  for (std::size_t i = 0; i != value.writer_records.size(); ++i) {
    if (i) out << ',';
    out << SerializeEntryFinalWriterCapture12004(value.writer_records[i]);
  }
  out << "],\"outer_invocation\":"; OptionalU64(out, value.outer_invocation);
  out << '}';
}
} // namespace

std::string SerializeEntryFinalSideCapture12004(
    const EntryFinalSideCaptureQuery12004 &query) {
  std::ostringstream out;
  out << "{\"schema\":\"entry_final_side_capture_12004\",\"version\":1";
  out << ",\"source_rva\":"; U64(out, kEntryFinalSideRva12004);
  out << ",\"configured\":" << (query.configured ? "true" : "false");
  out << ",\"installed\":" << (query.installed ? "true" : "false");
  out << ",\"request_filtered\":" << (query.request_filtered ? "true" : "false");
  out << ",\"install_failure_flags\":" << query.install_failure_flags;
  out << ",\"latest_record_sequence\":"; U64(out, query.latest_record_sequence);
  out << ",\"overwritten_records\":"; U64(out, query.overwritten_records);
  out << ",\"capture_retention_failures\":"; U64(out, query.capture_retention_failures);
  out << ",\"records\":[";
  for (std::size_t i = 0; i != query.records.size(); ++i) {
    if (i) out << ',';
    Record(out, query.records[i]);
  }
  out << "]}";
  return out.str();
}
} // namespace xar::ck3_12004
