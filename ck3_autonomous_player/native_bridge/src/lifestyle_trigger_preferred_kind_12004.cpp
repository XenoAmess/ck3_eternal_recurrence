#include "xar_bridge/lifestyle_trigger_preferred_kind_12004.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {
bool SameEvent(const PersonInstalledTransferEvent12004 &a,
    const PersonInstalledTransferEvent12004 &b) noexcept {
  return a.clock_identity == b.clock_identity && a.sequence == b.sequence && a.thread_id == b.thread_id;
}
bool OrderedSameClock(const PersonInstalledTransferEvent12004 &query,
    const PersonInstalledTransferEvent12004 &before, const PersonInstalledTransferEvent12004 &after) noexcept {
  return query.clock_identity != 0 && query.sequence != 0 && query.thread_id && before.thread_id && after.thread_id &&
      query.clock_identity == before.clock_identity && query.clock_identity == after.clock_identity &&
      query.thread_id == before.thread_id && query.thread_id == after.thread_id &&
      query.sequence < before.sequence && before.sequence < after.sequence;
}
bool SourceDigest(const std::string &value) noexcept {
  if (value.size() != 64) return false;
  for (const auto c : value) if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'))) return false;
  return true;
}
SourceTriggerPreferredKindResult12004 Empty(const SourceTriggerPreferredKindRaw12004 &raw) {
  SourceTriggerPreferredKindResult12004 out{}; out.raw = raw;
  out.unavailable_reason = raw.raw_source_ready ? "preferred_kind_output_unavailable" : raw.unavailable_reason;
  return out;
}
} // namespace

SourceTriggerPreferredKindRaw12004 BindSourceTriggerPreferredKindCopiedInputs12004(
    const SourceTriggerPreferredKindCopiedInputs12004 &copied) {
  SourceTriggerPreferredKindRaw12004 out{}; out.frame = copied.frame;
  out.selected_perk_identity = copied.selected_perk_identity; out.selected_perk_key = copied.selected_perk_key;
  out.command_identity = copied.command_identity; out.requested_full_character_id = copied.requested_full_character_id;
  out.selected_character_identity = copied.selected_character_identity; out.selected_character_full_id = copied.selected_character_full_id;
  out.source_context_full_id_payload = copied.source_context_full_id_payload;
  out.context_is_source_projection = copied.context_is_source_projection;
  out.selection_source_qualified = copied.selection_source_qualified; out.source_kind = copied.source_kind;
  out.validate_scope_entry_event = copied.validate_scope_entry_event;
  out.trigger_receiver = copied.trigger_receiver; out.trigger_vptr = copied.trigger_vptr;
  out.slot58_address = copied.slot58_address; out.slot58_target_va = copied.slot58_target_va;
  out.slot58_target_rva = copied.slot58_target_rva; out.module_extent_bytes = copied.module_extent_bytes;
  out.root_kind_raw_u16 = copied.root_kind_raw_u16;
  const auto &frame = out.frame;
  const auto perk = out.selected_perk_identity;
  const auto maximum = (std::numeric_limits<std::uintptr_t>::max)();
  if (!SourceReadFrameReady12004(frame.read_frame) || frame.producer_rva != 0x372B4C0 ||
      frame.read_frame.caller_domain != "stock_perk_legality_12004" || !out.selection_source_qualified || out.selected_perk_key.empty() ||
      out.source_kind != SourceTriggerPreferredKindSource12004::perk_allow_trigger_80 ||
      !perk || perk > maximum - 0x80 || frame.receiver_identity != perk + 0x80 ||
      out.trigger_receiver != perk + 0x80 || !out.command_identity ||
      !out.selected_character_identity || !*out.selected_character_identity ||
      out.selected_character_full_id != out.requested_full_character_id) {
    out.unavailable_reason = "preferred_kind_selection_or_source_frame_unavailable"; return out;
  }
  if (out.root_kind_raw_u16 != frame.primary_scope_root_word ||
      (out.source_context_full_id_payload && *out.source_context_full_id_payload != out.requested_full_character_id)) {
    out.unavailable_reason = "preferred_kind_source_scope_word_mismatch_or_partial"; return out;
  }
  if (!out.trigger_vptr || !*out.trigger_vptr || *out.trigger_vptr > maximum - 0x58) {
    out.unavailable_reason = "preferred_kind_trigger_vptr_unavailable"; return out;
  }
  if (out.slot58_address != *out.trigger_vptr + 0x58) {
    out.unavailable_reason = "preferred_kind_slot58_address_mismatch"; return out;
  }
  if (!out.slot58_target_va || !*out.slot58_target_va || *out.slot58_target_va < frame.read_frame.module_base ||
      !out.module_extent_bytes || !*out.module_extent_bytes || *out.module_extent_bytes > maximum - frame.read_frame.module_base ||
      *out.slot58_target_va - frame.read_frame.module_base >= *out.module_extent_bytes ||
      *out.slot58_target_va - frame.read_frame.module_base > (std::numeric_limits<std::uint32_t>::max)()) {
    out.unavailable_reason = "preferred_kind_slot58_target_not_image_relative"; return out;
  }
  const auto derived_rva = static_cast<std::uint32_t>(*out.slot58_target_va - frame.read_frame.module_base);
  if (out.slot58_target_rva && *out.slot58_target_rva != derived_rva) {
    out.unavailable_reason = "preferred_kind_slot58_rva_mismatch"; return out;
  }
  // Bounded copied target arithmetic is not a class claim or body qualification.
  out.slot58_target_rva = derived_rva;
  out.raw_source_ready = true;
  out.unavailable_reason = "preferred_kind_specific_target_or_natural_return_unavailable";
  return out;
}

SourceTriggerPreferredKindRaw12004 BindLifestyleRootKindFrontierInputs12004(
    const LifestyleTriggerFrontierInputs12004 &input) {
  SourceTriggerPreferredKindCopiedInputs12004 copied{};
  copied.frame.read_frame = input.read_frame; copied.frame.producer_rva = 0x372B4C0;
  copied.frame.receiver_identity = input.receiver_identity.value_or(0);
  // No native stack/root-scope address exists in this before-Validate plane.
  copied.frame.primary_scope_root_word = input.source_context_root_word;
  copied.source_kind = SourceTriggerPreferredKindSource12004::perk_allow_trigger_80;
  copied.selected_perk_identity = input.selected_perk_identity; copied.selected_perk_key = input.target_key;
  copied.command_identity = input.command_identity; copied.requested_full_character_id = input.requested_full_character_id;
  copied.selected_character_identity = input.selected_character_identity; copied.selected_character_full_id = input.selected_character_full_id;
  copied.source_context_full_id_payload = input.source_context_full_id_payload; copied.context_is_source_projection = input.context_is_source_projection;
  copied.trigger_receiver = input.receiver_identity; copied.trigger_vptr = input.vtable_identity;
  copied.slot58_address = input.slot58.slot_identity; copied.slot58_target_va = input.slot58.target_identity;
  if (input.slot58.target_rva && *input.slot58.target_rva <= (std::numeric_limits<std::uint32_t>::max)())
    copied.slot58_target_rva = static_cast<std::uint32_t>(*input.slot58.target_rva);
  copied.module_extent_bytes = input.module_image_size;
  copied.root_kind_raw_u16 = input.source_context_root_word;
  copied.selection_source_qualified = input.caller_before_after_confirmed &&
      input.mailbox_before_accepted.value_or(false) && input.slot58.copied;
  auto raw = BindSourceTriggerPreferredKindCopiedInputs12004(copied);
  if (input.slot58.target_rva && *input.slot58.target_rva > (std::numeric_limits<std::uint32_t>::max)()) {
    raw.raw_source_ready = false; raw.unavailable_reason = "preferred_kind_slot58_rva_not_u32";
  }
  return raw;
}

LifestyleTriggerLaneSource12004 ReadLifestyleRootKindFrontier12004(
    const SourceLeafReadOnlyAccess12004 &, const LifestyleTriggerFrontierInputs12004 &input) noexcept {
  LifestyleTriggerLaneSource12004 lane{};
  try {
    lane.lane = "root_kind_ax"; lane.call_rva = 0x372B4D3; lane.return_rva = 0x372B4D6;
    lane.target = input.slot58;
    const auto raw = BindLifestyleRootKindFrontierInputs12004(input);
    lane.raw_target_ready = raw.raw_source_ready;
    // No real same-query target body or natural output record is held yet.
    // A concrete claimed target implementation will join here after Root
    // closes its reached source. The copied target is never invoked.
    lane.unavailable_reason = raw.unavailable_reason;
  } catch (...) {
    lane.raw_target_ready = false; lane.source_value_ready = false;
  }
  return lane;
}

SourceTriggerPreferredKindResult12004 QualifySourceTriggerPreferredKindNaturalReturn12004(
    const SourceTriggerPreferredKindRaw12004 &raw, const SourceTriggerPreferredKindNaturalReturn12004 &w) {
  auto out = Empty(raw);
  out.natural_return_provenance = w;
  if (!raw.raw_source_ready) return out;
  if (w.frame != raw.frame || w.source_kind != raw.source_kind ||
      w.selected_perk_identity != raw.selected_perk_identity || w.selected_perk_key != raw.selected_perk_key ||
      w.command_identity != raw.command_identity || w.requested_full_character_id != raw.requested_full_character_id ||
      w.selected_character_identity != raw.selected_character_identity || w.selected_character_full_id != raw.selected_character_full_id ||
      w.source_context_full_id_payload != raw.source_context_full_id_payload ||
      w.trigger_receiver != raw.trigger_receiver || w.trigger_vptr != raw.trigger_vptr ||
      w.slot58_target_va != raw.slot58_target_va || w.actual_call_rva != 0x372B4D3 || w.actual_return_rva != 0x372B4D6) {
    out.unavailable_reason = "preferred_kind_native_return_identity_mismatch"; return out;
  }
  if (!raw.validate_scope_entry_event || !SameEvent(*raw.validate_scope_entry_event, w.validate_scope_entry_event) ||
      !OrderedSameClock(w.validate_scope_entry_event, w.before_original_event, w.returned_event)) {
    out.unavailable_reason = "preferred_kind_native_return_clock_thread_or_scope_unavailable"; return out;
  }
  if (!w.actual_validate_scope_observed || !w.actual_slot58_original_once_observed ||
      !w.original_returned || !w.live_observer_binding_verified || !w.returned_rax_bits) {
    out.unavailable_reason = "preferred_kind_actual_original_once_return_unavailable"; return out;
  }
  out.preferred_kind_ax_u16 = static_cast<std::uint16_t>(*w.returned_rax_bits & 0xFFFFu);
  out.preferred_kind_source_ready = true; out.actual_native_original_observed = true;
  out.caller_root_word_source_ready = w.root_after_return_observed && w.root_after_return_scope_identity != 0 &&
      (!raw.frame.primary_scope_identity || w.root_after_return_scope_identity == raw.frame.primary_scope_identity) &&
      w.root_after_return_raw_u16.has_value();
  if (out.caller_root_word_source_ready) out.caller_root_word_raw_u16 = w.root_after_return_raw_u16;
  out.basis = SourceTriggerPreferredKindBasis12004::natural_original_return;
  out.unavailable_reason.clear(); return out;
}

SourceTriggerPreferredKindResult12004 ReadSourceTriggerPreferredKindClosedTarget12004(
    const SourceLeafReadOnlyAccess12004 &access, const SourceTriggerPreferredKindRaw12004 &raw,
    const SourceTriggerPreferredKindClosedTarget12004 &target) {
  auto out = Empty(raw);
  if (!raw.raw_source_ready) return out;
  if (!target.exact_target_source_closed || !target.native_invocation_free || !target.read_pure ||
      !raw.slot58_target_rva || target.actual_target_rva != *raw.slot58_target_rva ||
      target.source_kind != raw.source_kind || !SourceDigest(target.complete_source_sha256)) {
    out.unavailable_reason = "preferred_kind_specific_target_source_not_qualified"; return out;
  }
  const auto value = target.read_pure(access, raw);
  if (!value.reached_readonly_source_ready || !value.preferred_kind_ax_u16) {
    out.unavailable_reason = "preferred_kind_specific_target_read_partial"; return out;
  }
  out.preferred_kind_ax_u16 = value.preferred_kind_ax_u16; out.preferred_kind_source_ready = true;
  out.caller_root_word_source_ready = raw.root_kind_raw_u16.has_value();
  out.caller_root_word_raw_u16 = raw.root_kind_raw_u16;
  out.basis = SourceTriggerPreferredKindBasis12004::specific_target_pure_read;
  out.specific_target_source_sha256 = target.complete_source_sha256;
  out.unavailable_reason.clear(); return out;
}

SourceTriggerPreferredKindGate12004 ProjectSourceTriggerPreferredKindGate12004(
    const SourceTriggerPreferredKindResult12004 &value) {
  SourceTriggerPreferredKindGate12004 out{}; out.frame = value.raw.frame;
  out.root_kind_raw_u16 = value.caller_root_word_raw_u16; out.preferred_kind_ax_u16 = value.preferred_kind_ax_u16;
  out.preferred_kind_source_ready = value.preferred_kind_source_ready;
  if (!value.raw.raw_source_ready || !value.preferred_kind_source_ready || !value.caller_root_word_source_ready ||
      value.basis == SourceTriggerPreferredKindBasis12004::unavailable ||
      !out.root_kind_raw_u16 || !out.preferred_kind_ax_u16) {
    out.unavailable_reason = value.unavailable_reason.empty() ? "preferred_kind_qualified_value_unavailable" : value.unavailable_reason;
    return out;
  }
  out.preferred_kind_matches_root = *out.preferred_kind_ax_u16 != 0 && *out.preferred_kind_ax_u16 == *out.root_kind_raw_u16;
  if (*out.preferred_kind_matches_root) {
    out.qualified_ready = true; out.returned_byte = std::uint8_t{1}; out.source_branch = "preferred_kind_match";
  } else {
    out.source_branch = "requires_independent_slot60_mask";
    out.unavailable_reason = "preferred_kind_no_shortcut_mask_lane_required";
  }
  return out;
}
} // namespace xar::ck3_12004
