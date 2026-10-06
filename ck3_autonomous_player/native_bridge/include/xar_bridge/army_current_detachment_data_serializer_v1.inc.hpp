// Included INSIDE xar::game after daily_assault_table_json_detail.
namespace current_detachment_data_json_detail {
using daily_assault_table_json_detail::Writer;
using daily_assault_table_json_detail::Resolution;
template <class Number, class JsonString, class Rows, class Append>
inline void Array(std::string &out, const Rows &rows, Number number, JsonString string, Append append) {
  out += '[';
  for (std::size_t i = 0; i < rows.size(); ++i) {
    if (i) out += ',';
    append(out, rows[i], number, string);
  }
  out += ']';
}
template <class Number, class JsonString>
inline void DataOccurrence(std::string &out, const ArmyDetachmentDataOccurrenceV1 &p, Number n, JsonString s) {
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Text("record_identity", p.record_identity);
  w.Integer("raw_regi_full_id_u32", p.raw_regi_full_id_u32);
  w.Integer("data_ordinal_raw_i32", p.data_ordinal_raw_i32);
  w.Text("held_fallback_regi_identity", p.held_fallback_regi_identity);
  w.Key("resolution"); Resolution(out, p.resolution, n, s);
  w.Integer("magic_14_raw_u32", p.magic_14_raw_u32); w.Boolean("identity_valid", p.identity_valid);
  w.Boolean("physical_chunk_present", p.physical_chunk_present);
  w.Integer("physical_chunk_index", p.physical_chunk_index); out += '}';
}
template <class Number, class JsonString>
inline void Chunk(std::string &out, const ArmyDetachmentPhysicalChunkV1 &p, Number n, JsonString s) {
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Text("chunk_identity", p.chunk_identity);
  w.Integer("maximum_00_raw_i32", p.maximum_00_raw_i32); w.Integer("current_04_raw_i32", p.current_04_raw_i32);
  w.Integer("owner_08_raw_u32", p.owner_08_raw_u32); w.Integer("ordinal_0c_raw_i32", p.ordinal_0c_raw_i32);
  w.Integer("association_10_raw_u32", p.association_10_raw_u32); w.Integer("flag_14_raw_u8", p.flag_14_raw_u8);
  w.Integer("date_1c_raw64", p.date_1c_raw64); out += '}';
}
template <class Number, class JsonString>
inline void Association(std::string &out, const ArmyDetachmentAssociationInputV1 &p, Number n, JsonString s) {
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Integer("requested_full_id_u32", p.requested_full_id_u32);
  w.Key("arrg_resolution"); Resolution(out, p.arrg_resolution, n, s);
  w.Integer("army_full_id_140_u32", p.army_full_id_140_u32);
  w.Key("army_resolution"); Resolution(out, p.army_resolution, n, s);
  w.Integer("unit_full_id_124_u32", p.unit_full_id_124_u32);
  w.Key("unit_resolution"); Resolution(out, p.unit_resolution, n, s);
  w.Integer("character_full_id_174_u32", p.character_full_id_174_u32);
  w.Key("character_resolution"); Resolution(out, p.character_resolution, n, s);
  w.Text("context_pointer_identity", p.context_pointer_identity);
  w.Integer("context_count_0c_raw_u32", p.context_count_0c_raw_u32); out += '}';
}
template <class Number, class JsonString>
inline void Owner(std::string &out, const ArmyDetachmentOwnerInputV1 &p, Number n, JsonString s) {
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Integer("requested_full_id_u32", p.requested_full_id_u32);
  w.Key("resolution"); Resolution(out, p.resolution, n, s);
  w.Integer("state_138_raw_i32", p.state_138_raw_i32);
  w.Text("definition_identity", p.definition_identity); w.Integer("definition_magic_38_raw_u32", p.definition_magic_38_raw_u32);
  w.Text("origin_identity", p.origin_identity); w.Integer("origin_magic_85c_raw_u32", p.origin_magic_85c_raw_u32); out += '}';
}
template <class Number, class JsonString>
inline void Date(std::string &out, const ArmyDetachmentDateInputV1 &p, Number n, JsonString s) {
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Text("basis", p.basis); w.Integer("association_full_id_u32", p.association_full_id_u32);
  w.Integer("owner_full_id_u32", p.owner_full_id_u32); w.Text("unit_identity", p.unit_identity);
  w.Text("source_origin_identity", p.source_origin_identity); w.Integer("source_origin_magic_85c_raw_u32", p.source_origin_magic_85c_raw_u32);
  w.Text("capital_origin_identity", p.capital_origin_identity); w.Integer("capital_origin_magic_85c_raw_u32", p.capital_origin_magic_85c_raw_u32);
  w.Integer("output_date_raw64", p.output_date_raw64); out += '}';
}
template <class Number, class JsonString>
inline void PendingRecord(std::string &out, const ArmyDetachmentPendingRecordV1 &p, Number n, JsonString s) {
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Text("record_identity", p.record_identity);
  w.Text("vtable_identity", p.vtable_identity); w.Text("slot0_target_identity", p.slot0_target_identity);
  w.Integer("owner_08_raw_u32", p.owner_08_raw_u32); w.Integer("ordinal_0c_raw_i32", p.ordinal_0c_raw_i32); out += '}';
}
template <class Number, class JsonString>
inline void Pending(std::string &out, const ArmyDetachmentPendingInputsV1 &p, Number n, JsonString s) {
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Text("header_identity", p.header_identity); w.Text("buffer_identity", p.buffer_identity);
  w.Integer("capacity_08_raw_i32", p.capacity_08_raw_i32); w.Integer("count_0c_raw_i32", p.count_0c_raw_i32);
  w.Text("allocator_identity", p.allocator_identity); w.Key("records");
  Array(out, p.records, n, s, [](auto &o, const auto &r, auto a, auto b) { PendingRecord(o, r, a, b); }); out += '}';
}
template <class Number, class JsonString>
inline void Incoming(std::string &out, const ArmyCurrentDetachmentIncomingV1 &p, Number n, JsonString s) {
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Integer("native_index", p.native_index); w.Text("arrg_identity", p.arrg_identity);
  w.Integer("arrg_full_id_u32", p.arrg_full_id_u32); w.Integer("army_full_id_140_u32", p.army_full_id_140_u32);
  w.Key("army_resolution"); Resolution(out, p.army_resolution, n, s);
  w.Integer("unit_full_id_124_u32", p.unit_full_id_124_u32);
  w.Key("unit_resolution"); Resolution(out, p.unit_resolution, n, s);
  w.Text("passed_province_identity", p.passed_province_identity); w.Text("data_pointer_identity", p.data_pointer_identity);
  w.Integer("data_count_raw_i32", p.data_count_raw_i32); w.Text("captured_cursor_identity", p.captured_cursor_identity);
  w.Text("captured_end_identity", p.captured_end_identity); w.Boolean("data_ready", p.data_ready);
  w.Integer("character_full_id_148_u32", p.character_full_id_148_u32);
  w.Key("character_resolution"); Resolution(out, p.character_resolution, n, s);
  w.Boolean("character_pointer_1b8_present", p.character_pointer_1b8_present);
  w.Text("character_pointer_1b8_identity", p.character_pointer_1b8_identity);
  w.Key("data_occurrences"); Array(out, p.data_occurrences, n, s, [](auto &o, const auto &r, auto a, auto b) { DataOccurrence(o, r, a, b); });
  w.Key("physical_chunks"); Array(out, p.physical_chunks, n, s, [](auto &o, const auto &r, auto a, auto b) { Chunk(o, r, a, b); });
  w.Key("association_inputs"); Array(out, p.association_inputs, n, s, [](auto &o, const auto &r, auto a, auto b) { Association(o, r, a, b); });
  w.Key("owner_inputs"); Array(out, p.owner_inputs, n, s, [](auto &o, const auto &r, auto a, auto b) { Owner(o, r, a, b); });
  w.Key("date_inputs"); Array(out, p.date_inputs, n, s, [](auto &o, const auto &r, auto a, auto b) { Date(o, r, a, b); });
  w.Key("pending"); Pending(out, p.pending, n, s); out += '}';
}
} // namespace current_detachment_data_json_detail
template <class Number, class JsonString>
inline void AppendArmyCurrentDetachmentDataInputsV1(std::string &out,
    const ArmyCurrentDetachmentDataInputsV1 &p, Number n, JsonString s) {
  using namespace current_detachment_data_json_detail;
  out += '{'; Writer<Number, JsonString> w{out, n, s}; w.Status(p);
  w.Integer("schema_version", p.schema_version); w.Text("source", p.source); w.Text("stage", p.stage);
  w.Boolean("selection_ready", p.selection_ready); w.Boolean("roster_ready", p.roster_ready);
  w.Integer("current_date_storage_raw64", p.current_date_storage_raw64);
  w.Text("primary_receiver_identity", p.primary_receiver_identity);
  w.Text("canonical_pending_vtable_identity", p.canonical_pending_vtable_identity);
  w.Text("ready_pending_callback_identity", p.ready_pending_callback_identity);
  w.Key("candidate_occurrences");
  Array(out, p.candidate_occurrences, n, s, [](auto &o, const auto &r, auto a, auto b) {
    o += '{'; Writer<decltype(a), decltype(b)> c{o, a, b}; c.Status(r);
    c.Integer("native_index", r.native_index); c.Integer("raw_full_id_u32", r.raw_full_id_u32);
    c.Key("resolution"); Resolution(o, r.resolution, a, b);
    c.Integer("magic_14_raw_u32", r.magic_14_raw_u32); c.Boolean("incoming_valid", r.incoming_valid);
    c.Integer("incoming_index", r.incoming_index); o += '}';
  });
  w.Key("incoming"); Array(out, p.incoming, n, s, [](auto &o, const auto &r, auto a, auto b) { Incoming(o, r, a, b); }); out += '}';
}
