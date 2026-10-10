#include "xar_bridge/prisoner_answer_helpers_12004.hpp"

namespace xar::ck3_12004 {
namespace {
bool NullOutputs(const PrisonerAnswerQueryArguments12004 &args) noexcept {
  return args.argument4_pointer && *args.argument4_pointer == 0 &&
      args.argument5_pointer && *args.argument5_pointer == 0;
}
void SetResult(PrisonerAnswerHelperResult12004 &out, std::uint8_t value, const char *branch) {
  out.raw_al = value; out.numeric_source_ready = true; out.branch = branch;
}
bool SameFrame(const PrisonerAnswerHelperRaw12004 &raw,
    const PrisonerQuoteSourceFrame12004 &frame) noexcept {
  return raw.frame_ready && frame == raw.frame;
}
bool ReporterReady(const PrisonerAnswerHelperRaw12004 &raw,
    const std::optional<PrisonerAnswerReporterEffects12004> &value, std::uint32_t callee) noexcept {
  return value && SameFrame(raw, value->frame) && value->actual_callee_rva == callee &&
      value->null_null_output_effects_source_ready;
}
} // namespace

PrisonerAnswerHelperRaw12004 ReadPrisonerAnswerHelperRaw12004(
    const PrisonerQuoteReadOnlyAccess12004 &access, const PrisonerQuoteSourceFrame12004 &frame) {
  PrisonerAnswerHelperRaw12004 out{}; out.frame = frame;
  const auto context = frame.interaction_context_identity;
  out.context_definition = ReadPrisonerQuoteSource12004<std::uintptr_t>(access, context);
  out.context_2d8_raw_u32 = ReadPrisonerQuoteSource12004<std::uint32_t>(access, context, 0x2D8);
  out.context_2dc_raw_u32 = ReadPrisonerQuoteSource12004<std::uint32_t>(access, context, 0x2DC);
  out.context_2e8_raw_u32 = ReadPrisonerQuoteSource12004<std::uint32_t>(access, context, 0x2E8);
  if (out.context_definition && *out.context_definition != 0) {
    out.definition_2725_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, *out.context_definition, 0x2725);
    out.definition_2727_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, *out.context_definition, 0x2727);
    out.definition_2728_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(access, *out.context_definition, 0x2728);
  }
  out.frame_ready = PrisonerQuoteSourceFrameReady12004(frame) && out.context_definition &&
      *out.context_definition == frame.definition_identity;
  return out;
}

PrisonerAnswerHelperResult12004 ProjectPrisonerAnswerInitialGate12004(
    const PrisonerAnswerHelperRaw12004 &raw, const PrisonerAnswerQueryArguments12004 &args,
    const std::optional<PrisonerAnswerByteChild12004> &predicate) {
  PrisonerAnswerHelperResult12004 out{}; out.actual_helper_rva = kPrisonerAnswerInitialHelperRva12004;
  if (!raw.frame_ready) { out.unavailable.push_back("answer_helper_frame_unavailable"); return out; }
  if (!NullOutputs(args)) { out.unavailable.push_back("generic_optional_diagnostic_effects_unclosed"); return out; }
  if (!raw.context_2d8_raw_u32 || !raw.context_2dc_raw_u32) {
    out.unavailable.push_back("initial_context_ids_unavailable"); return out;
  }
  if (*raw.context_2d8_raw_u32 == *raw.context_2dc_raw_u32) {
    SetResult(out, 0, "equal_context_ids"); out.reached_effects_source_ready = true; return out;
  }
  if (!predicate || !SameFrame(raw, predicate->frame) || predicate->actual_callee_rva != 0x3148BB0 ||
      predicate->receiver_identity != raw.frame.definition_identity ||
      raw.frame.interaction_context_identity > (std::numeric_limits<std::uintptr_t>::max)() - 8 ||
      predicate->second_argument_identity != raw.frame.interaction_context_identity + 8 || !predicate->raw_al) {
    out.unavailable.push_back("predicate_3148bb0_same_input_result_unavailable"); return out;
  }
  SetResult(out, *predicate->raw_al == 0 ? 3 : 0,
      *predicate->raw_al == 0 ? "different_ids_predicate_zero" : "different_ids_predicate_nonzero");
  out.reached_effects_source_ready = predicate->reached_effects_source_ready;
  if (!out.reached_effects_source_ready) out.unavailable.push_back("predicate_3148bb0_effects_unclosed");
  return out;
}

PrisonerAnswerHelperResult12004 ProjectPrisonerAnswerModeBranch12004(
    const PrisonerAnswerHelperRaw12004 &raw, const PrisonerAnswerQueryArguments12004 &args,
    std::uint32_t mode, const PrisonerAnswerModeChildren12004 &children) {
  PrisonerAnswerHelperResult12004 out{}; out.actual_helper_rva = kPrisonerAnswerModeHelperRva12004;
  if (!raw.frame_ready) { out.unavailable.push_back("answer_helper_frame_unavailable"); return out; }
  if (!NullOutputs(args)) { out.unavailable.push_back("generic_optional_diagnostic_effects_unclosed"); return out; }
  if (mode > 1) { out.unavailable.push_back("outside_current_parent_modes"); return out; }
  if (!args.argument2_raw_u8 || !args.argument3_raw_u8) {
    out.unavailable.push_back("saved_argument_bytes_unavailable"); return out;
  }
  // The current quote passes argument3=1. A different call path keeps its
  // 307B700 branch unknown until that independent child contract is supplied.
  if (*args.argument3_raw_u8 == 0) {
    out.unavailable.push_back("generic_zero_argument3_child_307b700_unclosed"); return out;
  }
  const auto &id = children.id_2baa6f0;
  if (!raw.context_2d8_raw_u32 || !id || !SameFrame(raw, id->frame) ||
      id->actual_callee_rva != 0x2BAA6F0 || id->full_id_argument != raw.context_2d8_raw_u32 || !id->raw_al) {
    out.unavailable.push_back("id_2baa6f0_same_input_result_unavailable"); return out;
  }
  bool preceding_effects_ready = id->reached_effects_source_ready;
  if (*id->raw_al != 0) {
    const auto &debug = children.debug_a75d00;
    if (!debug || !SameFrame(raw, debug->frame) || debug->actual_callee_rva != 0xA75D00 || !debug->byte0_raw_u8) {
      out.unavailable.push_back("debug_a75d00_byte0_unavailable"); return out;
    }
    preceding_effects_ready = preceding_effects_ready && debug->reached_effects_source_ready;
    if (*debug->byte0_raw_u8 != 0) {
      SetResult(out, 0, "debug_byte0_nonzero");
      out.reached_effects_source_ready = preceding_effects_ready && ReporterReady(raw, children.reporter_307b910, 0x307B910);
      if (!out.reached_effects_source_ready) out.unavailable.push_back("debug_path_child_effects_unclosed");
      return out;
    }
    if (*args.argument2_raw_u8 != 0) {
      if (!debug->byte1_raw_u8) { out.unavailable.push_back("debug_a75d00_byte1_unavailable"); return out; }
      if (*debug->byte1_raw_u8 != 0) {
        SetResult(out, 2, "debug_byte1_nonzero");
        out.reached_effects_source_ready = preceding_effects_ready && ReporterReady(raw, children.reporter_307b910, 0x307B910);
        if (!out.reached_effects_source_ready) out.unavailable.push_back("debug_path_child_effects_unclosed");
        return out;
      }
    }
  }
  const auto &scope = children.scope;
  if (!scope || !SameFrame(raw, scope->frame) || scope->actual_callee_rva != (mode == 0 ? 0x307C340u : 0x307C440u) ||
      scope->context_identity != raw.frame.interaction_context_identity || !scope->returned_qword_bits) {
    out.unavailable.push_back("scope_same_input_qword_unavailable"); return out;
  }
  const auto bits = *scope->returned_qword_bits;
  const bool in_native_range = bits - std::uint64_t{1} <= std::uint64_t{0x98967E};
  bool override = false;
  if (mode == 0) {
    if (!raw.definition_2727_raw_u8) { out.unavailable.push_back("definition_flag2727_unavailable"); return out; }
    override = *raw.definition_2727_raw_u8 != 0 && in_native_range;
  } else {
    if (!raw.definition_2728_raw_u8) { out.unavailable.push_back("definition_flag2728_unavailable"); return out; }
    if (*raw.definition_2728_raw_u8 != 0 && in_native_range) override = true;
    else {
      if (!raw.definition_2725_raw_u8) { out.unavailable.push_back("definition_flag2725_unavailable"); return out; }
      override = *raw.definition_2725_raw_u8 != 0;
    }
  }
  if (override) SetResult(out, 1, mode == 0 ? "mode0_range_flag_override" : "mode1_flag_override");
  else if (bits != 0 && (bits & (std::uint64_t{1} << 63)) == 0) SetResult(out, 0, "signed_scope_positive");
  else SetResult(out, 2, "signed_scope_nonpositive");
  out.reached_effects_source_ready = preceding_effects_ready && scope->reached_effects_source_ready &&
      ReporterReady(raw, children.reporter_307baf0, 0x307BAF0);
  if (!out.reached_effects_source_ready) out.unavailable.push_back("scope_path_child_effects_unclosed");
  return out;
}
} // namespace xar::ck3_12004
