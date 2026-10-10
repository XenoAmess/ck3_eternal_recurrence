#include "xar_bridge/compiled_expression_variant_3755500_provider_metadata_12004.hpp"

#include <limits>

namespace xar::ck3_12004::piety_price_raw_inputs {

std::optional<CompiledExpressionVariant3755500ProviderMetadata12004>
ProjectCompiledExpressionVariant3755500ProviderMetadata12004(
    const CompiledExpressionVariant3755500Readonly12004 &source) {
  if (!source.list_count_before_raw_i32 || *source.list_count_before_raw_i32 <= 0)
    return std::nullopt;

  CompiledExpressionVariant3755500ProviderMetadata12004 out{};
  out.module_base = source.module_base;
  out.expression_list_identity = source.expression_list_identity;
  out.unchanged_snapshot_revision = source.unchanged_snapshot_revision;
  out.copied_parent_pack = source.copied_pack;
  out.list_count_before_raw_i32 = source.list_count_before_raw_i32;
  out.list_count_after_raw_i32 = source.list_count_after_raw_i32;
  out.list_data_identity = source.list_data_identity;
  out.first_row_identity = source.first_row_identity;
  out.provider_receiver_identity = source.provider_receiver_identity;
  out.provider_vtable = source.provider_vtable;
  out.type_mask_slot30_raw_va = source.type_mask_slot30;
  out.value_slot20_raw_va = source.value_producer_slot20;
  if (source.module_base != 0 && out.value_slot20_raw_va &&
      *out.value_slot20_raw_va >= source.module_base) {
    const auto relative = *out.value_slot20_raw_va - source.module_base;
    if (relative <= (std::numeric_limits<std::uint32_t>::max)())
      out.value_slot20_module_relative_rva_candidate = static_cast<std::uint32_t>(relative);
  }
  out.original_named_tuple_identity = source.named_tuple_identity;
  out.embedded_tuple_first_qword = source.embedded_tuple_first_qword;
  out.selected_tuple_identity = source.selected_tuple_identity;
  out.selected_tuple_before_raw = source.selected_tuple_before_raw;
  out.selected_tuple_after_raw = source.selected_tuple_after_raw;
  if (source.embedded_tuple_first_qword)
    out.original_named_tuple_selected_as_numeric_input = *source.embedded_tuple_first_qword == 0;
  out.primary_scope_before_identity = source.primary_scope_before_identity;
  out.primary_scope_after_identity = source.primary_scope_after_identity;
  out.incoming_root_before_raw = source.incoming_root_before_raw;
  out.incoming_root_after_raw = source.incoming_root_after_raw;
  out.source_operand_bookends_equal = source.copied_operand_bookends_equal;
  out.source_operand_unavailable_reason = source.unavailable_reason;

  if (!source.copied_operand_bookends_equal) {
    out.unavailable_reason = source.unavailable_reason.empty()
        ? "compiled_positive_provider_source_operand_bookends_unavailable"
        : source.unavailable_reason;
  } else if (!out.provider_receiver_identity || *out.provider_receiver_identity == 0) {
    out.unavailable_reason = "compiled_positive_provider_receiver_unavailable";
  } else if (!out.provider_vtable || *out.provider_vtable == 0) {
    out.unavailable_reason = "compiled_positive_provider_vtable_unavailable";
  } else if (!out.value_slot20_raw_va || *out.value_slot20_raw_va == 0) {
    out.unavailable_reason = "compiled_positive_provider_value_slot20_unavailable";
  } else if (!out.type_mask_slot30_raw_va || *out.type_mask_slot30_raw_va == 0) {
    out.unavailable_reason = "compiled_positive_provider_type_mask_slot30_unavailable";
  } else if (!out.selected_tuple_identity || *out.selected_tuple_identity == 0 ||
             !out.selected_tuple_before_raw || !out.selected_tuple_after_raw) {
    out.unavailable_reason = "compiled_positive_provider_selected_tuple_unavailable";
  } else {
    out.unavailable_reason = "compiled_positive_provider_type_mask_and_returned_value_unclosed";
  }
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
