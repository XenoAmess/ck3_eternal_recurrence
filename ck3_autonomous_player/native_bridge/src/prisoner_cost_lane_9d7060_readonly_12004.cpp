#include "xar_bridge/prisoner_cost_lane_9d7060_readonly_12004.hpp"

namespace xar::ck3_12004 {
namespace {
void ReadFallback(const PrisonerQuoteReadOnlyAccess12004 &access,
                  PrisonerCostLane9D7060Readonly12004 &out) noexcept {
  out.fallback_98_q64 = ReadPrisonerQuoteSource12004<std::int64_t>(
      access, out.lane_identity, 0x98);
  out.raw_temp_q64 = out.fallback_98_q64;
  if (!out.raw_temp_q64) out.unavailable_reason = "cost_lane_constant_98_unavailable";
}

bool BoundResult(const PrisonerCostLane9D7060Arguments12004 &args,
                 const PrisonerCostLaneConditionalResult12004 *result,
                 std::uintptr_t receiver, std::uintptr_t callback,
                 std::uintptr_t callsite, std::string &reason) noexcept {
  if (!result || !result->source_result_ready) {
    reason = "cost_lane_dynamic_source_result_unavailable";
    return false;
  }
  if (!callback || result->frame != args.frame ||
      result->lane_identity != args.lane_identity ||
      result->internal_aliases != args.internal_aliases ||
      result->descriptor_identity != args.descriptor_identity ||
      result->receiver_identity != receiver ||
      result->callback_identity != callback ||
      result->consumer_callsite_rva != callsite) {
    reason = "cost_lane_dynamic_source_argument_mismatch";
    return false;
  }
  return true;
}

void UseNumericResult(const PrisonerCostLaneConditionalResult12004 &result,
                      PrisonerCostLane9D7060Readonly12004 &out) noexcept {
  out.raw_temp_q64 = result.result_q64;
  if (!out.raw_temp_q64) out.unavailable_reason = "cost_lane_dynamic_q64_unavailable";
}
} // namespace

PrisonerCostLane9D7060Readonly12004 ReadPrisonerCostLane9D7060Readonly12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerCostLane9D7060Arguments12004 &args,
    const PrisonerCostLaneConditionalResult12004 *conditional_result) noexcept {
  PrisonerCostLane9D7060Readonly12004 out;
  out.lane_identity = args.lane_identity;
  if (!PrisonerQuoteSourceFrameReady12004(args.frame) || !args.lane_identity ||
      !access.read_memory) {
    out.unavailable_reason = "cost_lane_frame_or_read_binding_unavailable";
    return out;
  }
  out.mode_c0_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(access, args.lane_identity, 0xC0);
  if (!out.mode_c0_i32) { out.unavailable_reason = "cost_lane_mode_c0_unavailable"; return out; }
  if (*out.mode_c0_i32 == 0) {
    out.branch = "fixed_mode_zero";
    ReadFallback(access, out);
    return out;
  }
  out.provider_b8_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, args.lane_identity, 0xB8);
  if (!out.provider_b8_identity) { out.unavailable_reason = "cost_lane_provider_b8_unavailable"; return out; }
  if (*out.provider_b8_identity != 0) {
    out.branch = "virtual_provider";
    if (*out.provider_b8_identity > (std::numeric_limits<std::uintptr_t>::max)() - 8) {
      out.unavailable_reason = "cost_lane_provider_receiver_unavailable"; return out;
    }
    out.provider_receiver_identity = *out.provider_b8_identity + 8;
    out.provider_vtable_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(
        access, *out.provider_receiver_identity);
    if (!out.provider_vtable_identity || !*out.provider_vtable_identity) {
      out.unavailable_reason = "cost_lane_provider_vtable_unavailable"; return out;
    }
    out.provider_slot30_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(
        access, *out.provider_vtable_identity, 0x30);
    if (!out.provider_slot30_identity || !*out.provider_slot30_identity) {
      out.unavailable_reason = "cost_lane_provider_slot30_unavailable"; return out;
    }
    if (BoundResult(args, conditional_result, *out.provider_receiver_identity,
                    *out.provider_slot30_identity, 0x9D7141, out.unavailable_reason))
      UseNumericResult(*conditional_result, out);
    return out;
  }
  // Actual310CF50 supplies null R9, so9D7153 skips the mode2 interpolation.
  out.named_a8_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, args.lane_identity, 0xA8);
  if (!out.named_a8_identity) { out.unavailable_reason = "cost_lane_named_a8_unavailable"; return out; }
  if (*out.named_a8_identity != 0) {
    out.branch = "named";
    out.named = ReadPrisonerNamedFixedReadonly12004(access, *out.named_a8_identity);
    if (out.named->numeric_source_ready && out.named->returned_q64) {
      out.raw_temp_q64 = out.named->returned_q64;
      return out;
    }
    if (out.named->expression_identity && *out.named->expression_identity != 0 &&
        out.named->expression_receiver_identity && out.named->expression_slot30 &&
        *out.named->expression_slot30 != 0) {
      if (BoundResult(args, conditional_result, *out.named->expression_receiver_identity,
                      *out.named->expression_slot30, 0x9D7228, out.unavailable_reason))
        UseNumericResult(*conditional_result, out);
    } else out.unavailable_reason = out.named->unavailable_reason;
    return out;
  }
  out.expression_count_14_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(access, args.lane_identity, 0x14);
  if (!out.expression_count_14_i32) { out.unavailable_reason = "cost_lane_expression_count_14_unavailable"; return out; }
  if (*out.expression_count_14_i32 == 0) {
    out.branch = "fixed_no_expression";
    ReadFallback(access, out);
    return out;
  }
  out.branch = "tagged_expression";
  if (args.lane_identity > (std::numeric_limits<std::uintptr_t>::max)() - 8 ||
      args.frame.module_base > (std::numeric_limits<std::uintptr_t>::max)() - 0x3755500) {
    out.unavailable_reason = "cost_lane_expression_receiver_unavailable"; return out;
  }
  PrisonerCostVariant3755500Arguments12004 variant_arguments;
  variant_arguments.frame = args.frame;
  variant_arguments.receiver_identity = args.lane_identity + 8;
  variant_arguments.internal_aliases = args.internal_aliases;
  variant_arguments.descriptor_identity = args.descriptor_identity;
  out.variant = ReadPrisonerCostVariant3755500Readonly12004(access, variant_arguments);
  if (!out.variant->list_count_raw_i32 ||
      out.variant->list_count_raw_i32 != out.expression_count_14_i32) {
    out.unavailable_reason = "cost_lane_variant_parent_count_changed_or_unavailable";
    return out;
  }
  PrisonerCostLaneConditionalResult12004 raw_variant_result;
  const auto *selected_variant_result = conditional_result;
  if (out.variant->source_result_ready) {
    raw_variant_result.frame = out.variant->frame;
    raw_variant_result.lane_identity = args.lane_identity;
    raw_variant_result.internal_aliases = out.variant->internal_aliases;
    raw_variant_result.descriptor_identity = out.variant->descriptor_identity;
    raw_variant_result.receiver_identity = out.variant->receiver_identity;
    raw_variant_result.callback_identity = out.variant->callback_identity;
    raw_variant_result.consumer_callsite_rva = out.variant->consumer_callsite_rva;
    raw_variant_result.source_result_ready = true;
    raw_variant_result.variant_tag_u16 = out.variant->variant_tag_raw_u16;
    raw_variant_result.result_q64 = out.variant->variant_payload_raw_q64;
    selected_variant_result = &raw_variant_result;
  } else if (out.variant->unavailable_reason !=
             "cost_variant_dynamic_type_mask_and_value_producer_unclosed") {
    // A missing demanded copy/count failure cannot be replaced by another
    // producer packet. A fully copied unclosed dynamic producer may supply
    // its own conditional result after that separate source is closed.
    out.unavailable_reason = out.variant->unavailable_reason;
    return out;
  }
  if (!BoundResult(args, selected_variant_result, args.lane_identity + 8,
                   args.frame.module_base + 0x3755500, 0x9D7252, out.unavailable_reason)) return out;
  out.variant_tag_u16 = selected_variant_result->variant_tag_u16;
  if (!out.variant_tag_u16) { out.unavailable_reason = "cost_lane_variant_tag_unavailable"; return out; }
  if (*out.variant_tag_u16 == 1) UseNumericResult(*selected_variant_result, out);
  else {
    out.branch = "fixed_nonnumeric_tag";
    //9D7267..7274 may report/clean up nonnumeric values when scope20==0;
    //9D7279 always copies the constant98. No effect is executed here.
    ReadFallback(access, out);
  }
  return out;
}
} // namespace xar::ck3_12004
