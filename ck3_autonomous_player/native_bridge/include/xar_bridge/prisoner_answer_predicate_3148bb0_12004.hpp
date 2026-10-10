#pragma once

#include "xar_bridge/prisoner_answer_helpers_12004.hpp"

namespace xar::ck3_12004 {
inline constexpr std::uint32_t kPrisonerAnswerPredicateRva12004 = 0x3148BB0;
inline constexpr std::uint32_t kPrisonerAnswerExpressionPredicateRva12004 = 0x372DF10;

struct PrisonerAnswerPredicate3148BB0Raw12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::uintptr_t definition_identity = 0, second_argument_identity = 0;
  std::optional<std::uintptr_t> definition_2290_expression;
  std::optional<std::uint8_t> definition_2718_raw_u8;
  bool input_source_ready = false;
};

// Current selected-query ABI only: RCX=[context], RDX=context+8, R8=null.
// Reuses the parent's copied actual definition/frame instead of qualifying a
// new frame. It copies only the reached data branch and calls no native code.
PrisonerAnswerPredicate3148BB0Raw12004 ReadPrisonerAnswerPredicate3148BB0Raw12004(
    const PrisonerQuoteReadOnlyAccess12004 &, const PrisonerAnswerHelperRaw12004 &);

struct PrisonerAnswerPredicate3148BB0Result12004 {
  PrisonerAnswerByteChild12004 byte_child;
  std::string branch;
  std::vector<std::string> unavailable;
};

// The nonnull-expression branch requires the independently owned actual
// 372DF10 result with the same frame and literal operands. AL is kept raw.
PrisonerAnswerPredicate3148BB0Result12004 ProjectPrisonerAnswerPredicate3148BB012004(
    const PrisonerAnswerPredicate3148BB0Raw12004 &,
    const std::optional<PrisonerAnswerByteChild12004> &expression_372df10);
} // namespace xar::ck3_12004
