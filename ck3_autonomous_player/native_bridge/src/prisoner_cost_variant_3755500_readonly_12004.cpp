#include "xar_bridge/prisoner_cost_variant_3755500_readonly_12004.hpp"

#include <cstring>
#include <limits>

namespace xar::ck3_12004 {
namespace {

bool AliasShapeReady(const PrisonerQuoteInternalAliases12004 &aliases) {
  return aliases.primary_scope.has_value() && aliases.secondary_scope.has_value() &&
      aliases.tertiary_scope.has_value() && aliases.support118_identity.has_value() &&
      aliases.evaluation_flag_raw_u8.has_value();
}

bool CountStable(const PrisonerQuoteReadOnlyAccess12004 &access,
                 PrisonerCostVariant3755500Readonly12004 &out) {
  out.list_count_after_raw_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(
      access, out.receiver_identity, 0xC);
  if (!out.list_count_after_raw_i32 ||
      out.list_count_after_raw_i32 != out.list_count_raw_i32) {
    out.source_result_ready = false;
    out.variant_tag_raw_u16.reset();
    out.variant_payload_raw_q64.reset();
    out.numeric_raw_q64.reset();
    out.unavailable_reason = "cost_variant_list_count_changed_or_unavailable";
    return false;
  }
  return true;
}

void SetVariant(PrisonerCostVariant3755500Readonly12004 &out,
                std::uint16_t tag, std::int64_t payload) {
  out.variant_tag_raw_u16 = tag;
  out.variant_payload_raw_q64 = payload;
  if (tag == 1) out.numeric_raw_q64 = payload;
  out.source_result_ready = true;
}

} // namespace

PrisonerCostVariant3755500Readonly12004
ReadPrisonerCostVariant3755500Readonly12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerCostVariant3755500Arguments12004 &arguments) {
  PrisonerCostVariant3755500Readonly12004 out{};
  out.frame = arguments.frame;
  out.receiver_identity = arguments.receiver_identity;
  out.descriptor_identity = arguments.descriptor_identity;
  out.internal_aliases = arguments.internal_aliases;
  out.same_frame_confirmed = PrisonerQuoteSourceFrameReady12004(arguments.frame);
  if (arguments.frame.module_base <=
      (std::numeric_limits<std::uintptr_t>::max)() - 0x3755500)
    out.callback_identity = arguments.frame.module_base + 0x3755500;
  if (!out.same_frame_confirmed || arguments.receiver_identity == 0 ||
      out.callback_identity == 0) {
    out.unavailable_reason = "cost_variant_source_frame_or_receiver_unavailable";
    return out;
  }
  out.list_count_raw_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(
      access, arguments.receiver_identity, 0xC);
  if (!out.list_count_raw_i32) {
    out.unavailable_reason = "cost_variant_list_count_unavailable";
    return out;
  }
  // 375553B/375553D write tag DWORD0 and payload QWORD0, without reading R8.
  if (*out.list_count_raw_i32 == 0) {
    SetVariant(out, 0, 0);
    (void)CountStable(access, out);
    return out;
  }
  // The initial sixteen bytes are loaded from the actual primary-scope
  // pointee before the signed count <=0 test. Fixed skip argument is zero.
  if (!arguments.internal_aliases.primary_scope ||
      *arguments.internal_aliases.primary_scope == 0) {
    out.unavailable_reason = "cost_variant_primary_scope_unavailable";
    return out;
  }
  out.incoming_root_raw = ReadPrisonerQuoteSource12004<std::array<std::uint8_t, 16>>(
      access, *arguments.internal_aliases.primary_scope);
  if (!out.incoming_root_raw) {
    out.unavailable_reason = "cost_variant_primary_root_copy_unavailable";
    return out;
  }
  if (*out.list_count_raw_i32 < 0) {
    std::uint16_t tag = 0;
    std::int64_t payload = 0;
    std::memcpy(&tag, out.incoming_root_raw->data(), sizeof(tag));
    std::memcpy(&payload, out.incoming_root_raw->data() + 8, sizeof(payload));
    SetVariant(out, tag, payload);
    (void)CountStable(access, out);
    return out;
  }
  if (static_cast<std::uint32_t>(*out.list_count_raw_i32) >
      access.maximum_modifier_occurrences) {
    out.unavailable_reason = "cost_variant_occurrence_ceiling";
    (void)CountStable(access, out);
    return out;
  }
  // Capture only the first reached current row. Its two virtual targets are
  // witnesses, and are never invoked or replaced by an assumed literal.
  out.list_data_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(
      access, arguments.receiver_identity);
  if (!out.list_data_identity || *out.list_data_identity == 0) {
    out.unavailable_reason = "cost_variant_list_data_unavailable";
    return out;
  }
  out.first_row_identity = *out.list_data_identity;
  out.expression_receiver_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(
      access, *out.first_row_identity);
  if (out.expression_receiver_identity && *out.expression_receiver_identity != 0) {
    out.expression_vtable = ReadPrisonerQuoteSource12004<std::uintptr_t>(
        access, *out.expression_receiver_identity);
    if (out.expression_vtable && *out.expression_vtable != 0) {
      out.expression_type_mask_slot30 = ReadPrisonerQuoteSource12004<std::uintptr_t>(
          access, *out.expression_vtable, 0x30);
      out.expression_value_slot20 = ReadPrisonerQuoteSource12004<std::uintptr_t>(
          access, *out.expression_vtable, 0x20);
    }
  }
  out.embedded_descriptor_first_qword = ReadPrisonerQuoteSource12004<std::uintptr_t>(
      access, arguments.receiver_identity, 0x70);
  if (out.embedded_descriptor_first_qword) {
    if (*out.embedded_descriptor_first_qword != 0 &&
        arguments.receiver_identity <= (std::numeric_limits<std::uintptr_t>::max)() - 0x70)
      out.selected_descriptor_identity = arguments.receiver_identity + 0x70;
    else if (*out.embedded_descriptor_first_qword == 0)
      out.selected_descriptor_identity = arguments.descriptor_identity;
    if (out.selected_descriptor_identity && *out.selected_descriptor_identity != 0)
      out.selected_descriptor_raw = ReadPrisonerQuoteSource12004<std::array<std::uint8_t, 32>>(
          access, *out.selected_descriptor_identity);
  }
  if (!AliasShapeReady(arguments.internal_aliases))
    out.unavailable_reason = "cost_variant_internal_alias_shape_unavailable";
  else if (!out.expression_receiver_identity || *out.expression_receiver_identity == 0 ||
           !out.expression_vtable || *out.expression_vtable == 0 ||
           !out.expression_type_mask_slot30 || *out.expression_type_mask_slot30 == 0 ||
           !out.expression_value_slot20 || *out.expression_value_slot20 == 0)
    out.unavailable_reason = "cost_variant_dynamic_receiver_or_slots_unavailable";
  else
    out.unavailable_reason = "cost_variant_dynamic_type_mask_and_value_producer_unclosed";
  (void)CountStable(access, out);
  return out;
}

} // namespace xar::ck3_12004
