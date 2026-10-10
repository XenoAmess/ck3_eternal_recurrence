#include "xar_bridge/person_transfer_postimage_12004_serializer.hpp"

#include <iomanip>
#include <sstream>

namespace xar::ck3_12004 {
namespace {
void Quoted(std::ostringstream &out, std::string_view value) {
  out << '"';
  for (const unsigned char ch : value) {
    if (ch == '"' || ch == '\\') out << '\\' << static_cast<char>(ch);
    else if (ch < 0x20)
      out << "\\u" << std::hex << std::setw(4) << std::setfill('0')
          << static_cast<unsigned>(ch) << std::dec << std::setfill(' ');
    else out << static_cast<char>(ch);
  }
  out << '"';
}
void Address(std::ostringstream &out, std::uintptr_t value) {
  out << "\"0x" << std::hex << value << std::dec << '"';
}
void Raw64(std::ostringstream &out, std::uint64_t value) {
  out << "\"0x" << std::hex << std::setw(16) << std::setfill('0')
      << value << std::dec << std::setfill(' ') << '"';
}
struct Object {
  std::ostringstream &out;
  bool first = true;
  explicit Object(std::ostringstream &stream) : out(stream) { out << '{'; }
  ~Object() { out << '}'; }
  template<class Write> void Field(std::string_view key, Write write) {
    if (!first) out << ',';
    first = false;
    Quoted(out, key); out << ':'; write();
  }
  void Text(std::string_view key, std::string_view value) {
    Field(key, [&] { Quoted(out, value); });
  }
  void Bool(std::string_view key, bool value) {
    Field(key, [&] { out << (value ? "true" : "false"); });
  }
  void Bool(std::string_view key, std::optional<bool> value) {
    Field(key, [&] { if (value) out << (*value ? "true" : "false"); else out << "null"; });
  }
  template<class T> void Number(std::string_view key, T value) {
    Field(key, [&] { out << value; });
  }
  template<class T> void Number(std::string_view key, std::optional<T> value) {
    Field(key, [&] { if (value) out << *value; else out << "null"; });
  }
  void Pointer(std::string_view key, std::uintptr_t value) {
    Field(key, [&] { Address(out, value); });
  }
  void Pointer(std::string_view key, std::optional<std::uintptr_t> value) {
    Field(key, [&] { if (value) Address(out, *value); else out << "null"; });
  }
};
template<class T, class Write>
void Array(std::ostringstream &out, const std::optional<std::vector<T>> &values,
           Write write) {
  if (!values) { out << "null"; return; }
  out << '[';
  bool first = true;
  for (const auto &value : *values) {
    if (!first) out << ',';
    first = false;
    write(value);
  }
  out << ']';
}
void Event(std::ostringstream &out, const PersonInstalledTransferEvent12004 &event) {
  Object object(out);
  object.Pointer("clock_identity", event.clock_identity);
  object.Number("sequence", event.sequence);
  object.Number("thread_id", event.thread_id);
}
void Scope(std::ostringstream &out, const PersonTransferSnapshotScope12004 &scope) {
  Object object(out);
  object.Field("occurrence", [&] { Event(out, scope.occurrence); });
  object.Field("event", [&] { Event(out, scope.event); });
  object.Text("phase", scope.phase == PersonTransferSnapshotPhase12004::before_original
      ? "before_original" : "after_original");
  object.Text("side", scope.side == PersonTransferSnapshotSide12004::a ? "a" : "b");
  object.Pointer("model_identity", scope.model_identity);
  object.Pointer("original_return_rva", scope.original_return_rva);
}
template<class T> void Header(Object &object, const T &raw) {
  object.Pointer("data_identity", raw.data_identity);
  object.Number("capacity_i32", raw.capacity_i32);
  object.Number("count_i32", raw.count_i32);
}
void Rows(std::ostringstream &out, const PersonTransferBlock10Snapshot12004 &raw) {
  Object object(out);
  object.Text("source", raw.source);
  object.Bool("configured", raw.configured);
  object.Bool("rows_ready", raw.rows_ready);
  object.Bool("descriptor_ready", raw.descriptor_ready);
  object.Text("reason", raw.reason);
  object.Pointer("model_identity", raw.model_identity);
  object.Pointer("block_identity", raw.block_identity);
  object.Number("row_copy_budget", raw.row_copy_budget);
  Header(object, raw);
  object.Field("rows", [&] {
    Array(out, raw.rows, [&](const auto &row) {
      out << '"';
      for (const auto byte : row)
        out << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned>(byte);
      out << std::dec << std::setfill(' ') << '"';
    });
  });
}
void Keys(std::ostringstream &out, const PersonTransferKeysSnapshot12004 &copy) {
  Object object(out);
  object.Field("scope", [&] { Scope(out, copy.scope); });
  object.Number("maximum_payload_bytes", copy.maximum_payload_bytes);
  object.Bool("payload_budget_exceeded", copy.payload_budget_exceeded);
  object.Bool("descriptor_copy_complete", copy.descriptor_copy_complete);
  object.Bool("payload_copy_complete", copy.payload_copy_complete);
  object.Bool("declared_operand_copy_complete", copy.declared_operand_copy_complete);
  object.Field("raw", [&] {
    Object raw(out);
    raw.Pointer("storage_identity", copy.raw.storage_identity);
    Header(raw, copy.raw);
    raw.Field("keys_u16", [&] {
      Array(out, copy.raw.keys_u16, [&](const auto key) { out << key; });
    });
    raw.Bool("header_ready", copy.raw.header_ready);
    raw.Bool("key_elements_ready", copy.raw.key_elements_ready);
    raw.Text("reason", copy.raw.reason);
  });
}
void Values(std::ostringstream &out, const PersonTransferValuesSnapshot12004 &copy) {
  Object object(out);
  object.Field("scope", [&] { Scope(out, copy.scope); });
  object.Number("maximum_payload_bytes", copy.maximum_payload_bytes);
  object.Bool("descriptor_copy_complete", copy.descriptor_copy_complete);
  object.Bool("payload_copy_complete", copy.payload_copy_complete);
  object.Bool("declared_operand_copy_complete", copy.declared_operand_copy_complete);
  object.Text("reason", copy.reason);
  object.Field("values_q64_raw_bits", [&] {
    Array(out, copy.values_q64_raw_bits, [&](const auto bits) { Raw64(out, bits); });
  });
  object.Field("raw", [&] {
    Object raw(out);
    raw.Pointer("model_identity", copy.raw.model_identity);
    raw.Pointer("block_identity", copy.raw.block_identity);
    raw.Pointer("allocator_receiver_identity", copy.raw.allocator_receiver_identity);
    Header(raw, copy.raw);
    raw.Field("values_q64", [&] {
      Array(out, copy.raw.values_q64, [&](const auto value) { out << value; });
    });
    raw.Text("values_reason", copy.raw.values_reason);
  });
}
void Tail(std::ostringstream &out, const PersonTransferBlock248SnapshotCapture12004 &copy) {
  Object object(out);
  object.Field("scope", [&] { Scope(out, copy.scope); });
  object.Bool("descriptor_copy_complete", copy.descriptor_copy_complete);
  object.Bool("payload_copy_complete", copy.payload_copy_complete);
  object.Bool("declared_operand_copy_complete", copy.declared_operand_copy_complete);
  object.Field("raw", [&] {
    Object raw(out);
    raw.Pointer("model_identity", copy.raw.model_identity);
    raw.Pointer("block_identity", copy.raw.block_identity);
    Header(raw, copy.raw);
    raw.Pointer("allocator_identity", copy.raw.allocator_identity);
    raw.Pointer("allocator_dispatch_vtable_identity", copy.raw.allocator_dispatch_vtable_identity);
    raw.Field("ordered_payload_raw64", [&] {
      Array(out, copy.raw.ordered_payload_raw64, [&](const auto bits) { Raw64(out, bits); });
    });
    raw.Bool("payload_ready", copy.raw.payload_ready);
    raw.Text("reason", copy.raw.reason);
  });
}
void Model(std::ostringstream &out, const PersonTransferModelPhysicalSnapshot12004 &copy) {
  Object object(out);
  object.Field("scope", [&] { Scope(out, copy.scope); });
  object.Field("block10_rows", [&] { Rows(out, copy.block10_rows); });
  object.Field("block78_keys", [&] { Keys(out, copy.block78_keys); });
  object.Field("blocke0_values", [&] { Values(out, copy.blocke0_values); });
  object.Field("block248_raw64", [&] { Tail(out, copy.block248_raw64); });
  object.Bool("four_descriptors_copy_complete", copy.four_descriptors_copy_complete);
  object.Bool("four_payloads_copy_complete", copy.four_payloads_copy_complete);
  object.Bool("four_operands_copy_complete", copy.four_operands_copy_complete);
  object.Text("reason", copy.reason);
}
void Pair(std::ostringstream &out, const PersonTransferPhysicalPair12004 &copy) {
  Object object(out);
  object.Bool("configured", copy.configured);
  object.Text("phase", copy.phase == PersonTransferSnapshotPhase12004::before_original
      ? "before_original" : "after_original");
  object.Field("a", [&] { Model(out, copy.a); });
  object.Field("b", [&] { Model(out, copy.b); });
}
void BlockComparison(std::ostringstream &out, const PersonTransferPhysicalBlockComparison12004 &copy) {
  Object object(out);
  object.Bool("four_descriptors_copy_complete", copy.four_descriptors_copy_complete);
  object.Bool("four_payloads_copy_complete", copy.four_payloads_copy_complete);
  object.Bool("four_operands_copy_complete", copy.four_operands_copy_complete);
  object.Bool("a_descriptor_equals_b_before", copy.a_descriptor_equals_b_before);
  object.Bool("b_descriptor_equals_a_before", copy.b_descriptor_equals_a_before);
  object.Bool("descriptor_cross_equal", copy.descriptor_cross_equal);
  object.Bool("a_payload_equals_b_before", copy.a_payload_equals_b_before);
  object.Bool("b_payload_equals_a_before", copy.b_payload_equals_a_before);
  object.Bool("payload_cross_equal", copy.payload_cross_equal);
}
void Comparison(std::ostringstream &out, const PersonTransferPhysicalComparison12004 &copy) {
  Object object(out);
  object.Bool("original_transfer_returned", copy.original_transfer_returned);
  object.Bool("model_pair_matches_transfer", copy.model_pair_matches_transfer);
  object.Bool("snapshot_scopes_match_transfer", copy.snapshot_scopes_match_transfer);
  object.Bool("same_clock_and_thread", copy.same_clock_and_thread);
  object.Bool("completion_after_begin", copy.completion_after_begin);
  object.Bool("same_original_observation_ready", copy.same_original_observation_ready);
  object.Field("block10_rows", [&] { BlockComparison(out, copy.block10_rows); });
  object.Field("block78_keys", [&] { BlockComparison(out, copy.block78_keys); });
  object.Field("blocke0_values", [&] { BlockComparison(out, copy.blocke0_values); });
  object.Field("block248_raw64", [&] { BlockComparison(out, copy.block248_raw64); });
  object.Bool("four_block_operand_copies_complete", copy.four_block_operand_copies_complete);
  object.Bool("four_block_payload_comparison_ready", copy.four_block_payload_comparison_ready);
  object.Bool("four_block_payloads_cross_equal", copy.four_block_payloads_cross_equal);
  object.Bool("four_block_payload_exchange_observed", copy.four_block_payload_exchange_observed);
  object.Bool("preparation_descriptor_matches_before_b", copy.preparation_descriptor_matches_before_b);
  object.Bool("preparation_threads_match_original", copy.preparation_threads_match_original);
  object.Bool("b_before_pc_key_value_counts_equal", copy.b_before_pc_key_value_counts_equal);
  object.Bool("a_after_pc_key_value_counts_equal", copy.a_after_pc_key_value_counts_equal);
  object.Text("reason", copy.reason);
}
} // namespace

std::string SerializePersonTransferPhysicalPostimage12004(
    const PersonTransferPhysicalPostimage12004 &copy) {
  std::ostringstream out;
  {
    Object object(out);
    object.Text("schema", kPersonTransferPhysicalPostimageSchema12004);
    object.Field("before", [&] { Pair(out, copy.before); });
    object.Field("after", [&] { Pair(out, copy.after); });
    object.Field("comparison", [&] { Comparison(out, copy.comparison); });
    object.Bool("all_native_delegate_postimages_ready", false);
    object.Bool("retained_preparation_numeric_payload_compared", false);
    object.Bool("actual_Ci_numeric_payload_compared", false);
    object.Bool("full_person_ready", false);
    object.Bool("entry_ready", false);
  }
  return out.str();
}

} // namespace xar::ck3_12004
