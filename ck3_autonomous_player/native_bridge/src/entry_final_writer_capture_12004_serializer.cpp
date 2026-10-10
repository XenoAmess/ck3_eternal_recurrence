#include "xar_bridge/entry_final_writer_capture_12004.hpp"
#include "xar_bridge/entry_final_getter_capture_12004.hpp"

#include <iomanip>
#include <sstream>

namespace xar::ck3_12004 {
namespace {
void Quote(std::ostream &out, std::string_view value) {
  out << '"';
  for (const unsigned char c : value) {
    switch (c) {
    case '"': out << "\\\""; break;
    case '\\': out << "\\\\"; break;
    case '\n': out << "\\n"; break;
    case '\r': out << "\\r"; break;
    case '\t': out << "\\t"; break;
    default:
      if (c < 0x20)
        out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
            << static_cast<unsigned>(c) << std::dec;
      else out << static_cast<char>(c);
    }
  }
  out << '"';
}
void Hex(std::ostream &out, std::uint64_t value, int width = 16) {
  out << "\"0x" << std::hex << std::setw(width) << std::setfill('0') << value
      << std::dec << '"';
}
template <class T> void OptionalHex(std::ostream &out, const std::optional<T> &value,
                                    int width = 16) {
  if (value) Hex(out, static_cast<std::uint64_t>(*value), width);
  else out << "null";
}
template <class T> void OptionalNumber(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}
void OptionalBool(std::ostream &out, const std::optional<bool> &value) {
  if (value) out << (*value ? "true" : "false");
  else out << "null";
}
void RawImage(std::ostream &out, const std::optional<EntryFinalCacheImage12004> &image) {
  if (!image) { out << "null"; return; }
  out << '"' << std::hex << std::setfill('0');
  for (const auto byte : *image) out << std::setw(2) << static_cast<unsigned>(byte);
  out << std::dec << '"';
}
void Event(std::ostream &out, const PersonInstalledTransferEvent12004 &event) {
  out << "{\"clock_identity\":"; Hex(out, event.clock_identity);
  out << ",\"sequence\":" << event.sequence << ",\"thread_id\":";
  OptionalNumber(out, event.thread_id); out << '}';
}
void Side(std::ostream &out, const EntryFinalSideIdentity12004 &side) {
  out << "{\"occurrence\":"; Event(out, side.occurrence);
  out << ",\"side_identity\":"; Hex(out, side.side_identity);
  out << ",\"province_identity\":"; Hex(out, side.province_identity);
  out << ",\"caller_return_rva\":"; Hex(out, side.caller_return_rva);
  out << ",\"caller_return_slot\":"; Hex(out, side.caller_return_slot);
  out << ",\"source_side_index\":"; OptionalNumber(out, side.source_side_index);
  out << '}';
}
void Slot(std::ostream &out, const EntryFinalSidePhysicalSlot12004 &slot) {
  out << "{\"bucket\":\""
      << (slot.bucket == EntryFinalSideBucket12004::levy ? "levy" : "men_at_arms")
      << "\",\"bucket_index\":" << slot.bucket_index
      << ",\"traversal_ordinal\":" << slot.traversal_ordinal;
  out << ",\"entry_identity\":"; Hex(out, slot.entry_identity);
  out << ",\"writer_return_rva\":"; Hex(out, slot.writer_return_rva);
  out << ",\"raw_before_hex\":"; RawImage(out, slot.raw_before); out << '}';
}
void Scope(std::ostream &out, const EntryFinalWriterActiveScope12004 &scope) {
  out << "{\"parent_identity\":";
  if (scope.parent_identity) Side(out, *scope.parent_identity); else out << "null";
  out << ",\"side_writer\":";
  if (scope.side_writer) {
    out << "{\"side\":"; Side(out, scope.side_writer->side);
    out << ",\"slot\":"; Slot(out, scope.side_writer->slot);
    out << ",\"begin_event\":"; Event(out, scope.side_writer->begin_event); out << '}';
  } else out << "null";
  out << ",\"image_base\":"; Hex(out, scope.image_base);
  out << ",\"entry_identity\":"; Hex(out, scope.entry_identity);
  out << ",\"province_identity\":"; Hex(out, scope.province_identity);
  out << ",\"writer_return_rva\":"; OptionalHex(out, scope.writer_return_rva);
  out << ",\"begin_event\":"; Event(out, scope.begin_event); out << '}';
}
void Fields(std::ostream &out, const EntryFinalSixCacheRaw12004 &fields) {
  out << "{\"max_size_bits\":"; OptionalHex(out, fields.max_size_bits, 8);
  out << ",\"siege_bits\":"; OptionalHex(out, fields.siege_bits);
  out << ",\"damage_bits\":"; OptionalHex(out, fields.damage_bits);
  out << ",\"toughness_bits\":"; OptionalHex(out, fields.toughness_bits);
  out << ",\"pursuit_bits\":"; OptionalHex(out, fields.pursuit_bits);
  out << ",\"screen_bits\":"; OptionalHex(out, fields.screen_bits); out << '}';
}
} // namespace

std::string SerializeEntryFinalWriterCapture12004(const EntryFinalWriterCaptureRecord12004 &record) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":\"xar.ck3.entry-final-writer-capture-12004-v1\",\"writer_scope\":";
  Scope(out, record.writer_scope);
  out << ",\"caller_return_address\":"; Hex(out, record.caller_return_address);
  out << ",\"exact_build_bound\":" << record.exact_build_bound
      << ",\"original_called\":" << record.original_called
      << ",\"original_returned\":" << record.original_returned;
  out << ",\"completed_event\":"; Event(out, record.completed_event);
  out << ",\"original_return_bits\":"; OptionalHex(out, record.original_return_bits);
  out << ",\"entry_before_raw_hex\":"; RawImage(out, record.entry_before);
  out << ",\"entry_after_raw_hex\":"; RawImage(out, record.entry_after);
  out << ",\"requested_regiment_id_before\":"; OptionalHex(out, record.requested_regiment_id_before, 8);
  out << ",\"requested_regiment_id_after\":"; OptionalHex(out, record.requested_regiment_id_after, 8);
  out << ",\"final_province_id\":"; OptionalNumber(out, record.final_province_id);
  out << ",\"copied_fallback_source_identity\":"; OptionalHex(out, record.copied_fallback_source_identity);
  out << ",\"actual_resolved_regiment_full_id\":"; OptionalHex(out, record.actual_resolved_regiment_full_id, 8);
  out << ",\"resolved_identity_matches_copied_fallback\":"; OptionalBool(out, record.resolved_identity_matches_copied_fallback);
  out << ",\"resolved_full_id_matches_requested\":"; OptionalBool(out, record.resolved_full_id_matches_requested);
  out << ",\"returned_record\":";
  if (record.returned_record) out << EntryFinalGetterReturnedRecordJson12004(*record.returned_record);
  else out << "null";
  out << ",\"child_records_accepted\":" << record.child_records_accepted
      << ",\"child_records_rejected\":" << record.child_records_rejected;
  out << ",\"entry_cache_after\":"; Fields(out, record.entry_cache_after);
  out << ",\"returned_fields_match_entry_after\":[";
  for (std::size_t i = 0; i < record.returned_fields_match_entry_after.size(); ++i) {
    if (i != 0) out << ',';
    OptionalBool(out, record.returned_fields_match_entry_after[i]);
  }
  out << "]";
  out << ",\"all_returned_fields_match_entry_after\":"; OptionalBool(out, record.all_returned_fields_match_entry_after);
  out << ",\"original_return_matches_returned_screen\":"; OptionalBool(out, record.original_return_matches_returned_screen);
  out << ",\"requested_handle_preserved\":"; OptionalBool(out, record.requested_handle_preserved);
  out << ",\"parent_identity_matches_completion_scope\":"; OptionalBool(out, record.parent_identity_matches_completion_scope);
  out << ",\"writer_event_order_proven\":"; OptionalBool(out, record.writer_event_order_proven);
  out << ",\"getter_completed_before_writer_return\":"; OptionalBool(out, record.getter_completed_before_writer_return);
  out << ",\"entry_images_copy_complete\":" << record.entry_images_copy_complete
      << ",\"returned_fields_copy_complete\":" << record.returned_fields_copy_complete
      << ",\"entry_cache_after_copy_complete\":" << record.entry_cache_after_copy_complete
      << ",\"side_slot_associated\":" << record.side_slot_associated
      << ",\"six_cache_writeback_observed\":" << record.six_cache_writeback_observed
      << ",\"side_slot_six_cache_writeback_observed\":" << record.side_slot_six_cache_writeback_observed;
  out << ",\"reason\":"; Quote(out, record.reason); out << '}';
  return out.str();
}

} // namespace xar::ck3_12004
