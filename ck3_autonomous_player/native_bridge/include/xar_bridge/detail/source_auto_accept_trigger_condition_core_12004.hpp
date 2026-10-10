#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"

namespace xar::ck3_12004::detail {
template <typename T, typename Raw>
std::optional<T> CopyAutoAcceptTriggerField12004(const PrisonerQuoteReadOnlyAccess12004 &access,
    Raw &out, std::uintptr_t receiver, std::size_t offset, const char *field) {
  out.any_native_field_read_attempted = true;
  auto value = ReadPrisonerQuoteSource12004<T>(access, receiver, offset);
  if (!value) out.missing_fields.emplace_back(field);
  return value;
}

// Both caller families use this exact copied-field algorithm. Their wrappers
// supply separate frame admission and retain their original typed frames.
template <typename Raw>
void CopyAutoAcceptTriggerFields12004(const PrisonerQuoteReadOnlyAccess12004 &access,
    Raw &out, const char *frame_unavailable) {
  if (!out.query_frame_ready) {
    out.unavailable_reason = frame_unavailable; return;
  }
  if (!out.trigger_identity) {
    out.unavailable_reason = "selected_trigger_pointer_unavailable"; return;
  }
  const auto trigger = *out.trigger_identity;
  if (trigger == 0) {
    out.unavailable_reason = "null_trigger_scalar_branch_owned_by_quote_parent"; return;
  }
  out.trigger_vtable = CopyAutoAcceptTriggerField12004<std::uintptr_t>(access, out, trigger, 0, "trigger.vtable");
  out.support_report_identity38 = CopyAutoAcceptTriggerField12004<std::uintptr_t>(access, out, trigger, 0x38, "trigger.support38");
  if (out.trigger_vtable && *out.trigger_vtable != 0) {
    out.root_kind_getter_slot58 = CopyAutoAcceptTriggerField12004<std::uintptr_t>(access, out, *out.trigger_vtable, 0x58, "trigger.slot58");
    out.root_mask_getter_slot60 = CopyAutoAcceptTriggerField12004<std::uintptr_t>(access, out, *out.trigger_vtable, 0x60, "trigger.slot60");
    out.evaluator_slotc8 = CopyAutoAcceptTriggerField12004<std::uintptr_t>(access, out, *out.trigger_vtable, 0xC8, "trigger.slotc8");
  }
  out.all_attempted_native_reads_complete = out.any_native_field_read_attempted && out.missing_fields.empty();
  if (!out.all_attempted_native_reads_complete) out.unavailable_reason = "trigger_readonly_copy_partial";
  else if (out.trigger_vtable && *out.trigger_vtable == 0) out.unavailable_reason = "trigger_vtable_is_null";
  else out.unavailable_reason = "trigger_virtual_outputs_source_unavailable";
}

template <typename Condition, typename Raw, typename Gate>
Condition EvaluateAutoAcceptTriggerConditions12004(const Raw &raw, const Gate &gate,
    bool frame_ready, bool helper_matches_query, const char *frame_unavailable) {
  Condition out{};
  out.frame = raw.frame; out.trigger_identity = raw.trigger_identity;
  if (!raw.query_frame_ready || !frame_ready) {
    out.unavailable_reason = frame_unavailable; return out;
  }
  if (!raw.parent_alias_shape_matches || !*raw.parent_alias_shape_matches) {
    out.unavailable_reason = "parent_alias_shape_unavailable_or_mismatched"; return out;
  }
  if (!raw.trigger_identity || *raw.trigger_identity == 0) {
    out.unavailable_reason = "selected_trigger_unavailable_or_scalar_parent_branch"; return out;
  }
  if (!raw.aliases.primary_scope_root_word) {
    out.unavailable_reason = "root_scope_kind_copy_unavailable"; return out;
  }
  out.root_validator_bypassed = *raw.aliases.primary_scope_root_word == std::uint16_t{0};
  if (*out.root_validator_bypassed) out.root_scope_source_valid = true;
  out.helper_matches_query = helper_matches_query;
  if (!out.helper_matches_query) {
    out.unavailable_reason = "helper_frame_or_trigger_or_root_mismatched"; return out;
  }
  if (gate.conditional_result_ready && gate.conditional_allows) {
    out.helper_conditional_allows = gate.conditional_allows;
    if (out.root_scope_source_valid && *out.root_scope_source_valid)
      out.conditional_reaches_virtual_c8 = gate.conditional_allows;
  }
  if (gate.qualified_ready && gate.getter_output_source_ready && gate.returned_byte) {
    out.helper_qualified_allows = *gate.returned_byte != std::uint8_t{0};
    if (out.root_scope_source_valid && *out.root_scope_source_valid && !*out.helper_qualified_allows) {
      out.source_projected_returned_raw_u8 = std::uint8_t{0};
      out.accepted = false; out.source_value_ready = true;
      return out;
    }
  }
  if (!out.root_scope_source_valid) out.unavailable_reason = "root_validator_output_source_unavailable";
  else if (!out.helper_qualified_allows) out.unavailable_reason = "root_scope_getter_outputs_source_unavailable";
  else out.unavailable_reason = "final_virtual_c8_output_source_unavailable";
  // A permitted helper path has no final returned byte: +C8 is not qualified.
  return out;
}
} // namespace xar::ck3_12004::detail
