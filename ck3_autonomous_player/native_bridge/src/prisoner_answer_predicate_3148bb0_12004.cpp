#include "xar_bridge/prisoner_answer_predicate_3148bb0_12004.hpp"

namespace xar::ck3_12004 {

PrisonerAnswerPredicate3148BB0Raw12004 ReadPrisonerAnswerPredicate3148BB0Raw12004(
    const PrisonerQuoteReadOnlyAccess12004 &access,
    const PrisonerAnswerHelperRaw12004 &parent) {
  PrisonerAnswerPredicate3148BB0Raw12004 out{};
  out.frame = parent.frame;
  if (!parent.frame_ready || !parent.context_definition ||
      *parent.context_definition != parent.frame.definition_identity)
    return out;
  out.definition_identity = *parent.context_definition;
  out.second_argument_identity = parent.frame.interaction_context_identity + 8;
  out.input_source_ready = true;
  out.definition_2290_expression = ReadPrisonerQuoteSource12004<std::uintptr_t>(
      access, out.definition_identity, 0x2290); // MOV3148BD1.
  if (out.definition_2290_expression && *out.definition_2290_expression == 0)
    out.definition_2718_raw_u8 = ReadPrisonerQuoteSource12004<std::uint8_t>(
        access, out.definition_identity, 0x2718); // MOVZX3148BDD.
  return out;
}

PrisonerAnswerPredicate3148BB0Result12004 ProjectPrisonerAnswerPredicate3148BB012004(
    const PrisonerAnswerPredicate3148BB0Raw12004 &raw,
    const std::optional<PrisonerAnswerByteChild12004> &expression) {
  PrisonerAnswerPredicate3148BB0Result12004 out{};
  auto &child = out.byte_child;
  child.frame = raw.frame;
  child.actual_callee_rva = kPrisonerAnswerPredicateRva12004;
  child.receiver_identity = raw.definition_identity;
  child.second_argument_identity = raw.second_argument_identity;
  if (!raw.input_source_ready) {
    out.unavailable.push_back("predicate_3148bb0_parent_input_unavailable");
    return out;
  }
  if (!raw.definition_2290_expression) {
    out.unavailable.push_back("predicate_3148bb0_expression_pointer_unread");
    return out;
  }
  if (*raw.definition_2290_expression == 0) {
    out.branch = "null_expression_definition_raw_byte";
    child.raw_al = raw.definition_2718_raw_u8;
    child.reached_effects_source_ready = child.raw_al.has_value();
    if (!child.raw_al)
      out.unavailable.push_back("predicate_3148bb0_definition_2718_unread");
    return out;
  }
  // CALL3148BE9 receives RCX=definition+2290's expression pointer. RDX still
  // carries the actual second argument. With R8=null, TEST3148BFA always leaves
  // the diagnostic tree; MOVZX3148D9F returns the child's saved raw AL.
  out.branch = "expression_raw_al_null_diagnostic_output";
  if (!expression || expression->frame != raw.frame ||
      expression->actual_callee_rva != kPrisonerAnswerExpressionPredicateRva12004 ||
      expression->receiver_identity != *raw.definition_2290_expression ||
      expression->second_argument_identity != raw.second_argument_identity ||
      !expression->raw_al) {
    out.unavailable.push_back("predicate_372df10_same_input_result_unavailable");
    return out;
  }
  child.raw_al = expression->raw_al;
  child.reached_effects_source_ready = expression->reached_effects_source_ready;
  if (!child.reached_effects_source_ready)
    out.unavailable.push_back("predicate_372df10_reached_effects_unclosed");
  return out;
}
} // namespace xar::ck3_12004
