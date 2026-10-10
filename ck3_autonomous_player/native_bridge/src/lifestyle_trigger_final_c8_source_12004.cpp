#include "xar_bridge/lifestyle_trigger_final_c8_source_12004.hpp"
#include "xar_bridge/lifestyle_trigger_frontier_types_12004.hpp"

namespace xar::ck3_12004 {

LifestyleTriggerLaneSource12004 ReadLifestyleFinalC8Frontier12004(
    const SourceLeafReadOnlyAccess12004 &,
    const LifestyleTriggerFrontierInputs12004 &inputs) noexcept {
  LifestyleTriggerLaneSource12004 out{};
  try {
    out.lane = "final_c8_al";
    out.call_rva = kLifestyleFinalC8CallRva12004;
    out.return_rva = kLifestyleFinalC8ReturnRva12004;
    out.target = inputs.slotc8;

    LifestyleFinalC8CopiedInputs12004 c8{};
    c8.query_frame = inputs.read_frame;
    c8.query_frame.caller_snapshot_confirmed =
        c8.query_frame.caller_snapshot_confirmed && inputs.caller_before_after_confirmed;
    c8.module_image_size = inputs.module_image_size;
    c8.selected_perk_identity = inputs.selected_perk_identity;
    c8.character_full_id = inputs.requested_full_character_id;
    c8.receiver_identity = inputs.receiver_identity;
    c8.vtable_identity = inputs.vtable_identity;
    c8.target_identity = inputs.slotc8.target_identity;
    c8.scope_root_word = inputs.source_context_root_word;
    c8.scope_full_id_payload = inputs.source_context_full_id_payload;
    c8.scope_is_source_projection = inputs.context_is_source_projection;
    c8.class_slot_copied = inputs.slotc8.copied;
    // The frozen common inputs provide no original aliases, scope payload
    // address, clock cursor or return-event plane. Do not infer those from the
    // software source trace or from either existing parent can_select bool.
    const auto raw = BindLifestyleFinalC8RawSource12004(c8);
    const bool slot_matches = raw.slot_identity && inputs.slotc8.slot_identity &&
        *raw.slot_identity == *inputs.slotc8.slot_identity;
    const bool vtable_rva_matches = raw.vtable_rva && inputs.vtable_rva &&
        *raw.vtable_rva == *inputs.vtable_rva;
    const bool target_rva_matches = raw.target_rva && inputs.slotc8.target_rva &&
        *raw.target_rva == *inputs.slotc8.target_rva;
    out.raw_target_ready = raw.raw_target_source_capture_ready && slot_matches &&
        vtable_rva_matches && target_rva_matches;
    out.unavailable_reason = out.raw_target_ready
        ? "final_c8_raw_target_only_original_return_or_closed_target_unavailable"
        : "final_c8_same_query_receiver_slot_image_binding_unavailable";

    // No concrete C8 target body has been supplied by the actual same-query
    // packet yet. Only02 assigns a bounded exact-target source owner after that
    // evidence exists. An earlier source-qualified false guard is not C8's AL.
    // Consequently this adapter supplies raw source-claim readiness, not an AL
    // value, a natural-call witness or overall command legality.
    return out;
  } catch (...) {
    out.raw_target_ready = false;
    out.source_value_ready = false;
    out.returned_raw_u8.reset();
    out.natural_witness.reset();
    out.closed_target_proof.reset();
    out.unavailable_reason = "final_c8_common_input_binding_failed";
    return out;
  }
}

} // namespace xar::ck3_12004
