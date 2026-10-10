#pragma once
#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kPrisonerRecipientScoreProducerRva12004 = 0x3761780;
inline constexpr std::uintptr_t kPrisonerRecipientScoreModifierCallRva12004 = 0x37618E0;

struct PrisonerRecipientScoreModifierInput12004 {
  std::int32_t native_occurrence_index = 0;
  std::optional<std::uintptr_t> stored_receiver_identity, vtable_identity, slot30_target_identity;
  bool raw_receiver_ready = false;
};
struct PrisonerRecipientScoreInputs12004 {
  PrisonerQuoteSourceFrame12004 frame{};
  PrisonerQuoteInternalAliases12004 internal_aliases{};
  std::uintptr_t score_block_identity = 0;
  std::optional<std::int64_t> base_q64;
  std::optional<std::uintptr_t> modifiers_data_identity;
  std::optional<std::int32_t> modifier_count_raw_i32;
  std::vector<PrisonerRecipientScoreModifierInput12004> ordered_modifier_occurrences;
  bool raw_inputs_complete = false;
  std::string unavailable_reason;
};
// A child owner qualifies its numerical source before supplying a transition.
// Source-equivalent transitions and native observations remain separate. This
// leaf accepts neither a target address nor an initialized zero as a result.
struct PrisonerRecipientScoreModifierTransition12004 {
  PrisonerQuoteSourceFrame12004 frame{};
  PrisonerQuoteInternalAliases12004 internal_aliases{};
  std::int32_t native_occurrence_index = 0;
  std::uintptr_t receiver_identity = 0, vtable_identity = 0, slot30_target_identity = 0;
  std::uintptr_t actual_callsite_rva = 0;
  std::optional<std::int64_t> incoming_q64, returned_q64;
  bool source_result_ready = false;
  bool actual_native_call_observed = false;
};
struct PrisonerRecipientScoreProjection12004 {
  std::optional<std::int64_t> returned_q64;
  bool numeric_source_ready = false;
  std::string unavailable_reason;
  std::size_t applied_transition_count = 0;
  // Numeric equivalence is independent of executing this native function.
  bool actual_callback_execution_observed = false;
};

inline PrisonerRecipientScoreInputs12004 ReadPrisonerRecipientScoreInputs12004(
    const PrisonerQuoteReadOnlyAccess12004 &access, const PrisonerQuoteSourceFrame12004 &frame,
    std::uintptr_t score_block, const PrisonerQuoteInternalAliases12004 &aliases = {}) {
  PrisonerRecipientScoreInputs12004 out{}; out.frame = frame;
  out.internal_aliases = aliases; out.score_block_identity = score_block;
  out.base_q64 = ReadPrisonerQuoteSource12004<std::int64_t>(access, score_block, 0x28);
  out.modifiers_data_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, score_block, 0x30);
  out.modifier_count_raw_i32 = ReadPrisonerQuoteSource12004<std::int32_t>(access, score_block, 0x3C);
  if (!out.base_q64 || !out.modifiers_data_identity || !out.modifier_count_raw_i32) {
    out.unavailable_reason = "recipient_score_header_unavailable"; return out;
  }
  const auto count = *out.modifier_count_raw_i32;
  if (count < 0 || static_cast<std::size_t>(count) > access.maximum_modifier_occurrences) {
    out.unavailable_reason = "recipient_score_modifier_count_outside_readonly_bound"; return out;
  }
  if (count > 0 && *out.modifiers_data_identity == 0) {
    out.unavailable_reason = "recipient_score_positive_count_null_data"; return out;
  }
  if (static_cast<std::size_t>(count) > ((std::numeric_limits<std::uintptr_t>::max)() - *out.modifiers_data_identity) / 8U) {
    out.unavailable_reason = "recipient_score_modifier_end_overflow"; return out;
  }
  for (std::int32_t index = 0; index < count; ++index) {
    PrisonerRecipientScoreModifierInput12004 row{}; row.native_occurrence_index = index;
    row.stored_receiver_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access,
        *out.modifiers_data_identity, static_cast<std::size_t>(index) * 8U);
    if (row.stored_receiver_identity && *row.stored_receiver_identity != 0) {
      row.vtable_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, *row.stored_receiver_identity);
      if (row.vtable_identity && *row.vtable_identity != 0)
        row.slot30_target_identity = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, *row.vtable_identity, 0x30);
    }
    row.raw_receiver_ready = row.stored_receiver_identity.has_value() && *row.stored_receiver_identity != 0 &&
        row.vtable_identity.has_value() && *row.vtable_identity != 0 &&
        row.slot30_target_identity.has_value() && *row.slot30_target_identity != 0;
    out.ordered_modifier_occurrences.push_back(row);
    if (!row.raw_receiver_ready) {
      out.unavailable_reason = "recipient_score_modifier_receiver_unavailable"; return out;
    }
  }
  out.raw_inputs_complete = true;
  return out;
}

inline PrisonerRecipientScoreProjection12004 ProjectPrisonerRecipientScore12004(
    const PrisonerRecipientScoreInputs12004 &input,
    const std::vector<PrisonerRecipientScoreModifierTransition12004> &transitions = {}) {
  PrisonerRecipientScoreProjection12004 out{};
  const auto fail = [&](const char *reason) { out.returned_q64.reset(); out.numeric_source_ready = false;
    out.unavailable_reason = reason; return out; };
  if (!PrisonerQuoteSourceFrameReady12004(input.frame)) return fail("recipient_score_query_frame_unbound");
  if (input.frame.definition_identity > (std::numeric_limits<std::uintptr_t>::max)() - 0x1918 ||
      input.score_block_identity != input.frame.definition_identity + 0x1918)
    return fail("recipient_score_definition_block_mismatch");
  if (!input.raw_inputs_complete || !input.base_q64 || !input.modifier_count_raw_i32 ||
      *input.modifier_count_raw_i32 < 0 ||
      input.ordered_modifier_occurrences.size() != static_cast<std::size_t>(*input.modifier_count_raw_i32))
    return fail("recipient_score_raw_inputs_incomplete");
  if (transitions.size() != input.ordered_modifier_occurrences.size())
    return fail("recipient_score_modifier_post_output_witness_unavailable");
  auto value = *input.base_q64;
  for (std::size_t index = 0; index < input.ordered_modifier_occurrences.size(); ++index) {
    const auto &row = input.ordered_modifier_occurrences[index]; const auto &transition = transitions[index];
    if (!row.raw_receiver_ready || !transition.source_result_ready || transition.frame != input.frame ||
        transition.internal_aliases != input.internal_aliases ||
        transition.native_occurrence_index != static_cast<std::int32_t>(index) ||
        transition.receiver_identity != row.stored_receiver_identity ||
        transition.vtable_identity != row.vtable_identity || transition.slot30_target_identity != row.slot30_target_identity ||
        transition.actual_callsite_rva != kPrisonerRecipientScoreModifierCallRva12004 ||
        !transition.incoming_q64 || *transition.incoming_q64 != value || !transition.returned_q64)
      return fail("recipient_score_modifier_transition_binding_mismatch");
    // Each virtual receives the same native output pointer. Its supplied post
    // value replaces the previous value; the parent does no generic addition.
    value = *transition.returned_q64; ++out.applied_transition_count;
  }
  out.returned_q64 = value; out.numeric_source_ready = true; return out;
}

struct PrisonerQuoteRecipientScoreSource12004 {
  PrisonerRecipientScoreInputs12004 copied_inputs{};
  PrisonerRecipientScoreProjection12004 projection{};
  bool native_getter_called = false, native_getter_returned_output_pointer = false;
  std::optional<std::int64_t> native_final_output_q64;
  std::optional<bool> projected_value_matches_native_final;
};
inline void FinishPrisonerQuoteRecipientScoreSource12004(PrisonerQuoteRecipientScoreSource12004 &value,
    bool same_frame_confirmed, bool called, bool returned_original_output, std::int64_t final_q64) {
  value.copied_inputs.frame.same_frame_confirmed = same_frame_confirmed;
  value.native_getter_called = called; value.native_getter_returned_output_pointer = returned_original_output;
  if (called && returned_original_output) value.native_final_output_q64 = final_q64;
  value.projection = ProjectPrisonerRecipientScore12004(value.copied_inputs);
  if (value.projection.returned_q64 && value.native_final_output_q64)
    value.projected_value_matches_native_final = *value.projection.returned_q64 == *value.native_final_output_q64;
}
} // namespace xar::ck3_12004
