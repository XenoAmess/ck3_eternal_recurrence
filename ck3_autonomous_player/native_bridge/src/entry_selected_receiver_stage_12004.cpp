#include "xar_bridge/entry_selected_receiver_stage_12004.hpp"

#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_knight_stat_consumption.hpp"
#include "xar_bridge/ck3_12004_person_six_stage_capture.hpp"

namespace xar::ck3_12004 {
namespace {
template <class T>
std::optional<bool> Equal(const std::optional<T> &left,
                          const std::optional<T> &right) noexcept {
  if (left && right) return *left == *right;
  return std::nullopt;
}
std::optional<bool> SameObject(const std::optional<std::uintptr_t> &left,
                              const std::optional<std::uintptr_t> &right) noexcept {
  if (left && right) return *left != 0 && *right != 0 && *left == *right;
  return std::nullopt;
}
bool Positive(const std::optional<bool> &value) noexcept {
  return value.has_value() && *value;
}
} // namespace

EntrySelectedReceiverStage12004 ObserveEntrySelectedReceiverStage12004(
    const PersonSixStageCapture12004DTO &capture,
    const KnightConsumedContext12004 &consumed,
    const EntrySelectedReceiverCall12004 &call) noexcept {
  EntrySelectedReceiverStage12004 out;
  out.property_key = consumed.property_key;
  out.consumed_return_rva = consumed.caller_return_rva;
  if (consumed.property_key >= 0xC1 && consumed.property_key <= 0xC9) {
    const auto index = static_cast<std::size_t>(consumed.property_key - 0xC1);
    out.exact_consumed_callsite =
        consumed.caller_return_rva == kKnightStatContextReturns12004[index];
  }
  out.exact_capture_build = capture.build_version == "1.20.0.4" &&
      capture.executable_sha256 == kExecutableSha256;
  out.linked_character_id = call.linked_character_id;
  out.linked_character_identity = call.linked_character_identity;
  out.selected_character_id = consumed.selected_character_id;
  out.selected_character_identity = consumed.selected_character_identity;
  out.getter_context_identity = consumed.context_identity;
  out.consumption_thread_id = call.consumption_thread_id;
  out.preparation_capture_observed = capture.capture_observed;
  out.preparation_capture_complete = capture.capture_complete;
  out.preparation_raw_counts_ready = capture.raw_counts_ready;
  if (!capture.capture_observed) return out;

  out.preparation_stage = capture.capture_complete
      ? "paused_same_thread_six_stage_completion" : "open_native_six_stage_capture";
  out.preparation_capture_sequence = capture.capture_sequence;
  out.preparation_source_return_rva = capture.source_return_rva;
  out.preparation_capture_thread_id = capture.capture_thread_id;
  if (capture.capture_complete)
    out.preparation_completion_thread_id = capture.query_thread_id;
  out.preparation_character_identity = capture.character_identity;
  out.preparation_model_identity = capture.preparation_model.model_identity;
  out.preparation_context_identity = capture.context_identity;
  out.preparation_owner_character_identity = capture.preparation_model.owner_character_identity;
  out.preparation_owner_character_id = capture.preparation_model.owner_character_id;
  for (std::size_t index = 0; index < capture.stages.size(); ++index) {
    if (capture.stages[index].observed)
      out.preparation_stage_observed_mask |= static_cast<std::uint8_t>(1U << index);
  }
  if (capture.capture_sequence != 0 && consumed.preparation_capture_sequence)
    out.capture_sequence_matches_record =
        capture.capture_sequence == *consumed.preparation_capture_sequence;
  if (capture.source_return_rva)
    out.exact_preparation_source_return =
        *capture.source_return_rva == kPersonSixStageReturnRva12004;
  out.selected_matches_capture_identity = SameObject(
      consumed.selected_character_identity, capture.character_identity);
  out.selected_matches_capture_id = Equal(consumed.selected_character_id, capture.character_id);
  out.selected_matches_model_owner_identity = SameObject(
      consumed.selected_character_identity, capture.preparation_model.owner_character_identity);
  out.selected_matches_model_owner_id = Equal(
      consumed.selected_character_id, capture.preparation_model.owner_character_id);
  out.getter_matches_capture_context = SameObject(consumed.context_identity, capture.context_identity);
  if (capture.preparation_model.model_identity) {
    const auto model = *capture.preparation_model.model_identity;
    out.getter_matches_preparation_model_inline = model != 0 && consumed.context_identity
        ? std::optional<bool>(*consumed.context_identity == model + 0x10)
        : std::nullopt;
  }
  if (capture.capture_complete && capture.capture_thread_id && capture.query_thread_id &&
      call.consumption_thread_id != 0) {
    out.completion_on_consumption_thread =
        *capture.capture_thread_id == *capture.query_thread_id &&
        *capture.query_thread_id == call.consumption_thread_id;
  }
  if (capture.capture_complete && capture.post_six_aggregate.observed &&
      capture.post_six_aggregate.pc.ready && consumed.consumed_pc.ready) {
    out.completed_post_pc_matches_consumed =
        capture.post_six_aggregate.pc == consumed.consumed_pc;
  }

  out.completed_preparation_lineage_proven =
      out.exact_consumed_callsite && out.exact_capture_build &&
      capture.configured && capture.historical_capture && capture.capture_complete &&
      capture.raw_counts_ready && out.preparation_stage_observed_mask == 0x3F &&
      capture.preparation_model.observed && capture.preparation_model.ready &&
      Positive(out.capture_sequence_matches_record) &&
      Positive(out.exact_preparation_source_return) &&
      Positive(out.selected_matches_capture_identity) && Positive(out.selected_matches_capture_id) &&
      Positive(out.selected_matches_model_owner_identity) && Positive(out.selected_matches_model_owner_id) &&
      Positive(out.getter_matches_capture_context) && Positive(out.getter_matches_preparation_model_inline) &&
      Positive(out.completion_on_consumption_thread) && Positive(out.completed_post_pc_matches_consumed);

  if (out.completed_preparation_lineage_proven) out.reason = {};
  else if (!out.exact_consumed_callsite) out.reason = "actual_ci_return_unmatched";
  else if (!out.exact_capture_build) out.reason = "preparation_capture_build_unmatched";
  else if (!capture.capture_complete) out.reason = "preparation_capture_open_at_consumption";
  else if (!capture.raw_counts_ready || out.preparation_stage_observed_mask != 0x3F)
    out.reason = "preparation_six_stage_incomplete";
  else if (!Positive(out.capture_sequence_matches_record)) out.reason = "preparation_sequence_unmatched_or_missing";
  else if (!Positive(out.exact_preparation_source_return)) out.reason = "preparation_source_unmatched_or_missing";
  else if (!Positive(out.completion_on_consumption_thread)) out.reason = "preparation_completion_thread_unmatched_or_missing";
  else if (!Positive(out.selected_matches_capture_identity) || !Positive(out.selected_matches_capture_id) ||
      !Positive(out.selected_matches_model_owner_identity) || !Positive(out.selected_matches_model_owner_id))
    out.reason = "selected_preparation_owner_unmatched_or_missing";
  else if (!Positive(out.getter_matches_capture_context) || !Positive(out.getter_matches_preparation_model_inline))
    out.reason = "consumed_preparation_receiver_unmatched_or_missing";
  else if (!Positive(out.completed_post_pc_matches_consumed)) out.reason = "completed_preparation_pc_unmatched_or_missing";
  else out.reason = "preparation_capture_not_admitted";
  return out;
}

} // namespace xar::ck3_12004
