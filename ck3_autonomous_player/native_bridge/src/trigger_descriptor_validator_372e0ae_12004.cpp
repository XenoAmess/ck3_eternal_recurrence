#include "xar_bridge/trigger_descriptor_validator_372e0ae_12004.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {
std::optional<std::uintptr_t> Add(std::uintptr_t base, std::size_t offset) noexcept {
  if (!base || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return {};
  return base + offset;
}

bool BoundTarget(const LifestyleTriggerFrontierInputs12004 &inputs,
                 std::uintptr_t target, std::uintptr_t &rva) noexcept {
  if (!target || !inputs.module_image_size || !*inputs.module_image_size ||
      target < inputs.read_frame.module_base)
    return false;
  rva = target - inputs.read_frame.module_base;
  return rva < *inputs.module_image_size;
}

LifestyleTriggerLaneSource12004 CopiedDescriptor(
    const LifestyleTriggerFrontierInputs12004 &inputs) noexcept {
  LifestyleTriggerLaneSource12004 out{};
  out.lane = "descriptor_al";
  out.call_rva = kTriggerDescriptorValidatorCallerRva12004;
  out.return_rva = kTriggerDescriptorValidatorReturnRva12004;
  if (!inputs.descriptor_provider) {
    out.unavailable_reason = "same_query_descriptor_provider_not_copied";
    return out;
  }
  const auto &provider = *inputs.descriptor_provider;
  // Copied raw facts remain available independently of admission/output.
  out.target.target_identity = provider.descriptor_validator_pointer10;
  if (provider.selected_descriptor_identity)
    out.target.slot_identity = Add(*provider.selected_descriptor_identity, 0x10);
  out.target.copied = provider.descriptor_validator_pointer_copied;
  std::uintptr_t rva = 0;
  const bool bounded = out.target.target_identity &&
      BoundTarget(inputs, *out.target.target_identity, rva);
  if (bounded && provider.frame == inputs.read_frame) out.target.target_rva = rva;
  if (!SourceReadFrameReady12004(inputs.read_frame) ||
      provider.frame != inputs.read_frame || !provider.query_frame_ready) {
    out.unavailable_reason = "descriptor_provider_source_frame_mismatch_or_unavailable";
    return out;
  }
  if (!inputs.source_context_root_word || !inputs.context_is_source_projection ||
      provider.caller_copied_root_kind_raw_u16 != inputs.source_context_root_word) {
    out.unavailable_reason = "same_reached_source_projection_kind_not_copied_or_mismatched";
    return out;
  }
  const auto kind = *inputs.source_context_root_word;
  if (kind == 0) {
    out.unavailable_reason = "native_zero_kind_bypasses_descriptor_call_no_al_output";
    return out;
  }
  if (!provider.count_raw_i32 || !provider.descriptor_selection_inputs_copied ||
      !provider.selected_descriptor_identity ||
      (provider.copied_fields_unchanged && !*provider.copied_fields_unchanged)) {
    out.unavailable_reason = "descriptor_selection_copy_unavailable_or_changed";
    return out;
  }
  const bool use_table = *provider.count_raw_i32 > static_cast<std::int32_t>(kind);
  const auto expected_descriptor = use_table && provider.table_data_identity
      ? Add(*provider.table_data_identity, static_cast<std::size_t>(kind) *
          kTriggerScopeDescriptorStride3795A6012004)
      : (!use_table ? Add(inputs.read_frame.module_base,
                         kTriggerScopeFallbackRva3795A6012004) : std::nullopt);
  if (!expected_descriptor || expected_descriptor != provider.selected_descriptor_identity ||
      (provider.selected_source_fallback && *provider.selected_source_fallback != !use_table)) {
    out.unavailable_reason = "copied_descriptor_does_not_match_literal_count_kind_branch";
    return out;
  }
  if (!provider.descriptor_validator_pointer_copied || !out.target.slot_identity || !bounded) {
    out.unavailable_reason = "copied_descriptor_direct_target_null_unbounded_or_unavailable";
    return out;
  }
  out.raw_target_ready = true;
  out.unavailable_reason = "concrete_readonly_target_body_or_matching_natural_al_witness_unavailable";
  return out;
}

bool NaturalEventsMatch(const LifestyleTriggerNaturalWitness12004 &w) noexcept {
  const auto &call = w.call_event;
  const auto &returned = w.return_event;
  const auto &cursor = w.query_cursor;
  return call.clock_identity && call.clock_identity == returned.clock_identity &&
      call.clock_identity == cursor.clock_identity && cursor.sequence &&
      call.sequence > cursor.sequence && returned.sequence > call.sequence &&
      call.thread_id && *call.thread_id && call.thread_id == returned.thread_id &&
      call.thread_id == cursor.thread_id;
}
} // namespace

LifestyleTriggerLaneSource12004 ReadLifestyleDescriptorFrontier12004(
    const SourceLeafReadOnlyAccess12004 &access,
    const LifestyleTriggerFrontierInputs12004 &inputs) noexcept {
  // This revision has no concrete target body profile. Access is reserved for
  // its source-proved operands; neither raw capture nor projection is replayed.
  (void)access;
  return CopiedDescriptor(inputs);
}

LifestyleTriggerLaneSource12004 QualifyLifestyleDescriptorNaturalWitness12004(
    const LifestyleTriggerFrontierInputs12004 &inputs,
    const LifestyleTriggerNaturalWitness12004 &witness) noexcept {
  auto out = CopiedDescriptor(inputs);
  out.natural_witness = witness;
  if (!out.raw_target_ready) return out;
  if (witness.read_frame != inputs.read_frame ||
      !inputs.selected_perk_identity || !inputs.receiver_identity ||
      Add(inputs.selected_perk_identity, 0x80) != inputs.receiver_identity ||
      witness.selected_perk_identity != inputs.selected_perk_identity ||
      witness.receiver_identity != *inputs.receiver_identity ||
      witness.call_rva != out.call_rva || witness.return_rva != out.return_rva ||
      witness.target_identity != *out.target.target_identity || !witness.original_rcx ||
      !inputs.descriptor_provider->selected_descriptor_identity ||
      witness.original_rdx != *inputs.descriptor_provider->selected_descriptor_identity ||
      witness.original_root_word != inputs.source_context_root_word ||
      (*inputs.source_context_root_word == 4 &&
       (!inputs.source_context_full_id_payload ||
        witness.original_full_id_payload != inputs.source_context_full_id_payload))) {
    out.unavailable_reason = "actual_natural_descriptor_call_frame_or_operands_mismatch";
    return out;
  }
  if (!NaturalEventsMatch(witness) || !witness.original_call_observed ||
      !witness.original_return_observed || witness.original_matching_call_count != 1 ||
      !witness.returned_raw_u8 || witness.returned_raw_u16 ||
      witness.returned_qword0 || witness.returned_qword1) {
    out.unavailable_reason = "actual_original_once_al_or_process_clock_thread_cursor_unavailable";
    return out;
  }
  out.returned_raw_u8 = witness.returned_raw_u8;
  out.source_value_ready = true;
  out.result_source = "natural_original_once";
  out.unavailable_reason.clear();
  return out;
}

} // namespace xar::ck3_12004
