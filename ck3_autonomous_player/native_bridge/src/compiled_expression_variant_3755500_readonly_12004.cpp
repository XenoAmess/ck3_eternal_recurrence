#include "xar_bridge/compiled_expression_variant_3755500_readonly_12004.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12004::piety_price_raw_inputs {
namespace {

template <class Value>
std::optional<Value> ReadOperand(const PietyPriceNumericAccess12004 &access,
                                std::uintptr_t object, std::size_t offset = 0) {
  Value value{};
  if (!ReadPietyPriceNumericField12004(access, object, offset, value)) return {};
  return value;
}

std::optional<std::uintptr_t> ReadPrimaryAlias(
    const PietyPriceNumericAccess12004 &access,
    const CompiledExpressionVariantPack3755500Readonly12004 &pack) {
  if (pack.physical_pack_identity)
    return ReadOperand<std::uintptr_t>(access, *pack.physical_pack_identity);
  return pack.primary_scope_identity;
}

bool RecopyReachedRootAndCount(const PietyPriceNumericAccess12004 &access,
                             CompiledExpressionVariant3755500Readonly12004 &out) {
  out.list_count_after_raw_i32 = ReadOperand<std::int32_t>(
      access, out.expression_list_identity, 0xC);
  if (!out.list_count_after_raw_i32 ||
      out.list_count_after_raw_i32 != out.list_count_before_raw_i32) {
    out.unavailable_reason = "compiled_variant_count_changed_or_unavailable";
    return false;
  }
  if (*out.list_count_before_raw_i32 == 0) {
    out.copied_operand_bookends_equal = true;
    return true;
  }
  out.primary_scope_after_identity = ReadPrimaryAlias(access, out.copied_pack);
  if (!out.primary_scope_after_identity ||
      out.primary_scope_after_identity != out.primary_scope_before_identity) {
    out.unavailable_reason = "compiled_variant_primary_alias_changed_or_unavailable";
    return false;
  }
  out.incoming_root_after_raw = ReadOperand<std::array<std::uint8_t, 16>>(
      access, *out.primary_scope_after_identity);
  if (!out.incoming_root_after_raw || out.incoming_root_after_raw != out.incoming_root_before_raw) {
    out.unavailable_reason = "compiled_variant_primary_root_changed_or_unavailable";
    return false;
  }
  if (out.selected_tuple_before_raw && out.selected_tuple_identity) {
    out.selected_tuple_after_raw = ReadOperand<std::array<std::uint8_t, 32>>(
        access, *out.selected_tuple_identity);
    if (!out.selected_tuple_after_raw || out.selected_tuple_after_raw != out.selected_tuple_before_raw) {
      out.unavailable_reason = "compiled_variant_selected_tuple_changed_or_unavailable";
      return false;
    }
  }
  out.copied_operand_bookends_equal = true;
  return true;
}

} // namespace

CompiledExpressionVariant3755500Readonly12004
ReadCompiledExpressionVariant3755500Readonly12004(
    const PietyPriceNumericAccess12004 &access,
    const CompiledExpressionVariant3755500Inputs12004 &inputs) {
  CompiledExpressionVariant3755500Readonly12004 out{};
  out.module_base = access.module_base;
  out.expression_list_identity = inputs.expression_list_identity;
  out.copied_pack = inputs.copied_pack;
  out.named_tuple_identity = inputs.named_tuple_identity;
  out.unchanged_snapshot_revision = inputs.unchanged_snapshot_revision;
  if (!access.exact_12004_bound || !access.guarded_read) {
    out.unavailable_reason = "compiled_variant_exact_read_access_unavailable";
    return out;
  }
  out.list_count_before_raw_i32 = ReadOperand<std::int32_t>(
      access, inputs.expression_list_identity, 0xC);
  if (!out.list_count_before_raw_i32) {
    out.unavailable_reason = "compiled_variant_count_unavailable";
    return out;
  }
  // Actual375553B/3D write DWORD0 and QWORD0 before any R8 or R9 read.
  if (*out.list_count_before_raw_i32 == 0) {
    if (RecopyReachedRootAndCount(access, out)) {
      out.variant_tag_raw_u16 = std::uint16_t{0};
      out.variant_payload_raw_q64 = std::int64_t{0};
      out.source_result_ready = true;
    }
    return out;
  }

  // Actual3755546..554C copy the primary root16. The physical pack alias is
  // read only when it is supplied; a source-defined copied shape stays owned.
  out.primary_scope_before_identity = ReadPrimaryAlias(access, inputs.copied_pack);
  out.physical_primary_alias_copied = inputs.copied_pack.physical_pack_identity.has_value() &&
      out.primary_scope_before_identity.has_value();
  if (!out.primary_scope_before_identity || *out.primary_scope_before_identity == 0) {
    out.unavailable_reason = "compiled_variant_primary_alias_unavailable";
    return out;
  }
  if (inputs.copied_pack.primary_scope_identity &&
      out.primary_scope_before_identity != inputs.copied_pack.primary_scope_identity) {
    out.unavailable_reason = "compiled_variant_copied_primary_alias_mismatch";
    return out;
  }
  out.incoming_root_before_raw = ReadOperand<std::array<std::uint8_t, 16>>(
      access, *out.primary_scope_before_identity);
  if (!out.incoming_root_before_raw) {
    out.unavailable_reason = "compiled_variant_primary_root_unavailable";
    return out;
  }
  std::uint16_t tag{};
  std::memcpy(&tag, out.incoming_root_before_raw->data(), sizeof(tag));
  out.incoming_root_tag_raw_u16 = tag;
  // Actual skip argument is DWORD0; the signed <=0 loop guard then returns
  // the initial root16 for a negative count, with no tuple/other-alias demand.
  if (*out.list_count_before_raw_i32 < 0) {
    if (RecopyReachedRootAndCount(access, out)) {
      std::int64_t payload{};
      std::memcpy(&payload, out.incoming_root_before_raw->data() + 8, sizeof(payload));
      out.variant_tag_raw_u16 = tag;
      out.variant_payload_raw_q64 = payload;
      out.source_result_ready = true;
    }
    return out;
  }

  // Positive count reaches two actual virtual methods. Their identities and
  // current operands are witnesses; reading them never supplies their result.
  out.list_data_identity = ReadOperand<std::uintptr_t>(access, inputs.expression_list_identity);
  if (out.list_data_identity && *out.list_data_identity != 0) {
    out.first_row_identity = *out.list_data_identity;
    out.provider_receiver_identity = ReadOperand<std::uintptr_t>(access, *out.first_row_identity);
    if (out.provider_receiver_identity && *out.provider_receiver_identity != 0) {
      out.provider_vtable = ReadOperand<std::uintptr_t>(access, *out.provider_receiver_identity);
      if (out.provider_vtable && *out.provider_vtable != 0) {
        out.type_mask_slot30 = ReadOperand<std::uintptr_t>(access, *out.provider_vtable, 0x30);
        out.value_producer_slot20 = ReadOperand<std::uintptr_t>(access, *out.provider_vtable, 0x20);
      }
    }
  }
  // 37555D5..55E7: choose inline list+70 if its first QWORD is nonzero,
  // otherwise original R9, then copy32B into the real value-producer context.
  out.embedded_tuple_first_qword = ReadOperand<std::uintptr_t>(
      access, inputs.expression_list_identity, 0x70);
  if (out.embedded_tuple_first_qword) {
    if (*out.embedded_tuple_first_qword == 0) {
      out.named_tuple_numeric_input_demanded = true;
      out.selected_tuple_identity = inputs.named_tuple_identity;
    } else if (inputs.expression_list_identity <=
               (std::numeric_limits<std::uintptr_t>::max)() - 0x70) {
      out.selected_tuple_identity = inputs.expression_list_identity + 0x70;
    }
    if (out.selected_tuple_identity && *out.selected_tuple_identity != 0)
      out.selected_tuple_before_raw = ReadOperand<std::array<std::uint8_t, 32>>(
          access, *out.selected_tuple_identity);
  }
  if (!RecopyReachedRootAndCount(access, out)) return out;
  out.unavailable_reason = "compiled_variant_dynamic_type_mask_and_value_producer_unclosed";
  return out;
}

} // namespace xar::ck3_12004::piety_price_raw_inputs
