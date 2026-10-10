#pragma once

#include "xar_bridge/prisoner_recipient_score_3761780_12004.hpp"

#include <cstring>

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kPrisonerMode0ScalarHelperRva12004 = 0x307C340;
inline constexpr std::uintptr_t kPrisonerMode0ScalarParentCallRva12004 = 0x307BEE9;
inline constexpr std::uintptr_t kPrisonerMode0ScoreCallRva12004 = 0x307C3A4;

enum class PrisonerMode0ScalarBranch12004 : std::uint8_t {
  unavailable, invalid_2e8_constant, equal_ids_constant, score_block_18c8,
};

struct PrisonerMode0ScalarInputs12004 {
  PrisonerQuoteSourceFrame12004 frame;
  PrisonerMode0ScalarBranch12004 branch = PrisonerMode0ScalarBranch12004::unavailable;
  std::optional<std::uint32_t> context_2e8_raw_u32, context_2d8_raw_u32;
  std::optional<std::uintptr_t> context_definition;
  std::uintptr_t clone_source_identity = 0, score_block_identity = 0;
  // Actual307C382 and307C38D overwrite these two cloned-scope members.
  std::uint16_t cloned_scope_root_word = 4;
  std::optional<std::uint64_t> cloned_scope_payload_u64;
  std::optional<std::uint8_t> score_evaluation_flag_raw_u8;
  PrisonerRecipientScoreInputs12004 raw_score;
  bool raw_branch_complete = false;
  std::string unavailable_reason;
};

inline PrisonerMode0ScalarInputs12004 ReadPrisonerMode0ScalarInputs12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerQuoteSourceFrame12004 &frame,
    const PrisonerQuoteInternalAliases12004 &score_aliases = {}) {
  PrisonerMode0ScalarInputs12004 out{};
  out.frame = frame;
  if (!PrisonerQuoteSourceFrameReady12004(frame)) {
    out.unavailable_reason = "mode0_existing_query_frame_unbound"; return out;
  }
  out.context_2e8_raw_u32 = ReadPrisonerQuoteSource12004<std::uint32_t>(
      access, frame.interaction_context_identity, 0x2E8);
  if (!out.context_2e8_raw_u32) {
    out.unavailable_reason = "mode0_context_2e8_unavailable"; return out;
  }
  if (*out.context_2e8_raw_u32 == 0xFFFFFFFFu) {
    out.branch = PrisonerMode0ScalarBranch12004::invalid_2e8_constant;
    out.raw_branch_complete = true;
    return out;
  }
  out.context_2d8_raw_u32 = ReadPrisonerQuoteSource12004<std::uint32_t>(
      access, frame.interaction_context_identity, 0x2D8);
  if (!out.context_2d8_raw_u32) {
    out.unavailable_reason = "mode0_context_2d8_unavailable"; return out;
  }
  if (*out.context_2d8_raw_u32 == *out.context_2e8_raw_u32) {
    out.branch = PrisonerMode0ScalarBranch12004::equal_ids_constant;
    out.raw_branch_complete = true;
    return out;
  }
  out.context_definition = ReadPrisonerQuoteSource12004<std::uintptr_t>(
      access, frame.interaction_context_identity);
  if (!out.context_definition || *out.context_definition != frame.definition_identity ||
      frame.interaction_context_identity > (std::numeric_limits<std::uintptr_t>::max)() - 8 ||
      frame.definition_identity > (std::numeric_limits<std::uintptr_t>::max)() - 0x18C8) {
    out.unavailable_reason = "mode0_owned_definition_or_address_unavailable"; return out;
  }
  out.clone_source_identity = frame.interaction_context_identity + 8;
  if (out.clone_source_identity != frame.original_scope_identity) {
    out.unavailable_reason = "mode0_original_scope_binding_mismatch"; return out;
  }
  out.score_block_identity = frame.definition_identity + 0x18C8;
  out.cloned_scope_payload_u64 = static_cast<std::uint64_t>(*out.context_2e8_raw_u32);
  out.score_evaluation_flag_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(
      access, frame.module_base, 0x5D1DADC);
  out.raw_score = ReadPrisonerRecipientScoreInputs12004(
      access, frame, out.score_block_identity, score_aliases);
  out.branch = PrisonerMode0ScalarBranch12004::score_block_18c8;
  out.raw_branch_complete = true;
  return out;
}

// The same actual3761780 body is reached through the held241B3761680
// wrapper. Its source virtual receives the existing qword output pointer.
// Every post value replaces that output; this caller adds no row values.
inline PrisonerRecipientScoreProjection12004 ProjectPrisonerMode0Score12004(
    const PrisonerMode0ScalarInputs12004 &input,
    const std::vector<PrisonerRecipientScoreModifierTransition12004> &transitions = {}) {
  PrisonerRecipientScoreProjection12004 out{};
  const auto fail = [&](const char *reason) {
    out.returned_q64.reset(); out.numeric_source_ready = false;
    out.unavailable_reason = reason; return out;
  };
  const auto &score = input.raw_score;
  if (!PrisonerQuoteSourceFrameReady12004(input.frame) || score.frame != input.frame ||
      input.branch != PrisonerMode0ScalarBranch12004::score_block_18c8 ||
      !input.raw_branch_complete || !input.context_definition ||
      !input.context_2e8_raw_u32 || *input.context_2e8_raw_u32 == 0xFFFFFFFFu ||
      !input.context_2d8_raw_u32 || *input.context_2d8_raw_u32 == *input.context_2e8_raw_u32 ||
      *input.context_definition != input.frame.definition_identity ||
      input.frame.definition_identity > (std::numeric_limits<std::uintptr_t>::max)() - 0x18C8 ||
      input.score_block_identity != input.frame.definition_identity + 0x18C8 ||
      score.score_block_identity != input.score_block_identity)
    return fail("mode0_score_owned_18c8_binding_mismatch");
  if (!score.raw_inputs_complete || !score.base_q64 || !score.modifier_count_raw_i32 ||
      *score.modifier_count_raw_i32 < 0 ||
      score.ordered_modifier_occurrences.size() != static_cast<std::size_t>(*score.modifier_count_raw_i32))
    return fail("mode0_score_raw_inputs_incomplete");
  if (transitions.size() != score.ordered_modifier_occurrences.size())
    return fail("mode0_score_modifier_post_output_unavailable");
  auto value = *score.base_q64;
  for (std::size_t index = 0; index < score.ordered_modifier_occurrences.size(); ++index) {
    const auto &row = score.ordered_modifier_occurrences[index];
    const auto &post = transitions[index];
    if (!row.raw_receiver_ready || !post.source_result_ready || post.frame != input.frame ||
        post.internal_aliases != score.internal_aliases ||
        post.native_occurrence_index != static_cast<std::int32_t>(index) ||
        post.receiver_identity != row.stored_receiver_identity ||
        post.vtable_identity != row.vtable_identity ||
        post.slot30_target_identity != row.slot30_target_identity ||
        post.actual_callsite_rva != kPrisonerRecipientScoreModifierCallRva12004 ||
        !post.incoming_q64 || *post.incoming_q64 != value || !post.returned_q64)
      return fail("mode0_score_modifier_transition_binding_mismatch");
    value = *post.returned_q64;
    ++out.applied_transition_count;
  }
  out.returned_q64 = value;
  out.numeric_source_ready = true;
  return out;
}

// Supplied by independently source-closed children in the same query.
// This packet never invokes the scope clone/score/cleanup.
// A scope address alone and a computed pre-cleanup score are not a final out.
struct PrisonerMode0ScalarPostWitness12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uintptr_t actual_helper_rva = 0, actual_parent_callsite_rva = 0;
  std::uintptr_t context_identity = 0, definition_identity = 0, score_block_identity = 0;
  std::uintptr_t clone_source_identity = 0;
  std::optional<std::uintptr_t> physical_cloned_scope_identity;
  std::optional<std::uint16_t> cloned_scope_root_word;
  std::optional<std::uint64_t> cloned_scope_payload_u64, final_qword_bits;
  PrisonerQuoteInternalAliases12004 score_internal_aliases;
  bool source_equivalent_clone_shape_ready = false;
  bool native_clone_observed = false;
  bool complete_reached_post_effects_source_ready = false;
};

struct PrisonerMode0ScalarProjection12004 {
  PrisonerMode0ScalarBranch12004 branch = PrisonerMode0ScalarBranch12004::unavailable;
  std::optional<std::int64_t> projected_score_q64;
  std::optional<std::uint64_t> returned_qword_bits;
  bool projected_score_source_ready = false;
  bool numeric_source_ready = false, reached_effects_source_ready = false;
  bool actual_native_output_observed = false;
  std::string unavailable_reason;
};

inline PrisonerMode0ScalarProjection12004 ProjectPrisonerMode0Scalar12004(
    const PrisonerMode0ScalarInputs12004 &input,
    const std::vector<PrisonerRecipientScoreModifierTransition12004> &transitions = {},
    const std::optional<PrisonerMode0ScalarPostWitness12004> &post = {}) {
  PrisonerMode0ScalarProjection12004 out{};
  out.branch = input.branch;
  if (!PrisonerQuoteSourceFrameReady12004(input.frame) || !input.raw_branch_complete) {
    out.unavailable_reason = "mode0_branch_or_query_frame_unavailable"; return out;
  }
  if (input.branch == PrisonerMode0ScalarBranch12004::invalid_2e8_constant ||
      input.branch == PrisonerMode0ScalarBranch12004::equal_ids_constant) {
    if (!input.context_2e8_raw_u32 ||
        (input.branch == PrisonerMode0ScalarBranch12004::invalid_2e8_constant &&
         *input.context_2e8_raw_u32 != 0xFFFFFFFFu) ||
        (input.branch == PrisonerMode0ScalarBranch12004::equal_ids_constant &&
         (*input.context_2e8_raw_u32 == 0xFFFFFFFFu || !input.context_2d8_raw_u32 ||
          *input.context_2d8_raw_u32 != *input.context_2e8_raw_u32))) {
      out.unavailable_reason = "mode0_constant_branch_raw_condition_mismatch"; return out;
    }
    // The actual constant branch has no scope/scoring/cleanup CALL.
    out.returned_qword_bits = std::uint64_t{10000000};
    out.numeric_source_ready = true;
    out.reached_effects_source_ready = true;
    return out;
  }
  const auto score = ProjectPrisonerMode0Score12004(input, transitions);
  out.projected_score_q64 = score.returned_q64;
  out.projected_score_source_ready = score.numeric_source_ready;
  if (!score.numeric_source_ready || !score.returned_q64) {
    out.unavailable_reason = score.unavailable_reason; return out;
  }
  if (!post || post->frame != input.frame ||
      post->actual_helper_rva != kPrisonerMode0ScalarHelperRva12004 ||
      post->actual_parent_callsite_rva != kPrisonerMode0ScalarParentCallRva12004 ||
      post->context_identity != input.frame.interaction_context_identity ||
      post->definition_identity != input.frame.definition_identity ||
      post->score_block_identity != input.score_block_identity ||
      post->clone_source_identity != input.clone_source_identity ||
      !post->cloned_scope_root_word ||
      *post->cloned_scope_root_word != 4 ||
      post->cloned_scope_payload_u64 != input.cloned_scope_payload_u64 ||
      post->score_internal_aliases != input.raw_score.internal_aliases ||
      post->score_internal_aliases.secondary_scope != std::uintptr_t{0} ||
      post->score_internal_aliases.primary_scope_root_word != std::uint16_t{4} ||
      !input.score_evaluation_flag_raw_u8 ||
      post->score_internal_aliases.evaluation_flag_raw_u8 != input.score_evaluation_flag_raw_u8 ||
      !post->final_qword_bits || !post->complete_reached_post_effects_source_ready) {
    out.unavailable_reason = "mode0_same_frame_final_out_witness_unavailable"; return out;
  }
  if (post->physical_cloned_scope_identity) {
    if (*post->physical_cloned_scope_identity == 0 ||
        post->score_internal_aliases.primary_scope != post->physical_cloned_scope_identity ||
        post->score_internal_aliases.tertiary_scope != post->physical_cloned_scope_identity) {
      out.unavailable_reason = "mode0_physical_clone_alias_mismatch"; return out;
    }
  } else if (!post->source_equivalent_clone_shape_ready || post->native_clone_observed ||
             post->score_internal_aliases.primary_scope.has_value() ||
             post->score_internal_aliases.tertiary_scope.has_value()) {
    // Source-defined copied shapes carry root/payload, with no invented
    // physical clone address or alias back to the original context scope.
    out.unavailable_reason = "mode0_copied_clone_shape_binding_mismatch"; return out;
  }
  std::uint64_t score_bits = 0;
  std::memcpy(&score_bits, &*score.returned_q64, sizeof(score_bits));
  if (*post->final_qword_bits != score_bits) {
    out.unavailable_reason = "mode0_final_out_differs_from_score_source"; return out;
  }
  out.returned_qword_bits = post->final_qword_bits;
  out.numeric_source_ready = true;
  out.reached_effects_source_ready = post->complete_reached_post_effects_source_ready;
  return out;
}
} // namespace xar::ck3_12004
