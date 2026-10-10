#include "xar_bridge/prisoner_answer_predicate_3148bb0_12004.hpp"

#include <cstring>
#include <map>
#include <vector>

namespace xar::ck3_12004::new_cases {
namespace {
constexpr std::uintptr_t kDefinition = 0x10000;
constexpr std::uintptr_t kContext = 0x20000;
constexpr std::uintptr_t kExpression = 0x30000;

struct CopiedQuery {
  std::map<std::uintptr_t, std::vector<unsigned char>> fields;
  std::size_t fallback_byte_reads = 0;
  template <typename T> void Put(std::uintptr_t address, T value) {
    auto &field = fields[address];
    field.resize(sizeof(T));
    std::memcpy(field.data(), &value, sizeof(T));
  }
  static bool Read(void *context, const void *address, void *destination,
                   std::size_t bytes) noexcept {
    auto &query = *static_cast<CopiedQuery *>(context);
    const auto key = reinterpret_cast<std::uintptr_t>(address);
    if (key == kDefinition + 0x2718) ++query.fallback_byte_reads;
    const auto field = query.fields.find(key);
    if (field == query.fields.end() || field->second.size() != bytes) return false;
    std::memcpy(destination, field->second.data(), bytes);
    return true;
  }
};

PrisonerAnswerHelperRaw12004 Parent() {
  PrisonerAnswerHelperRaw12004 parent{};
  auto &frame = parent.frame;
  frame.executable_sha256 = kPrisonerQuoteSourceExecutableSha25612004;
  frame.module_base = 0x140000000;
  frame.native_revision = 87;
  frame.query_sequence = 7;
  frame.proof_epoch = 11;
  frame.date_raw = 53289912;
  frame.jailer_full_id = 0x07000002;
  frame.prisoner_full_id = 0x07000003;
  frame.recipient_full_id = 0x07000004;
  frame.definition_identity = kDefinition;
  frame.interaction_context_identity = kContext;
  frame.original_scope_identity = 0x40000;
  frame.roles_verified_in_owned_context = true;
  frame.same_frame_confirmed = true;
  parent.context_definition = kDefinition;
  parent.context_2d8_raw_u32 = *frame.prisoner_full_id;
  parent.context_2dc_raw_u32 = *frame.recipient_full_id;
  parent.frame_ready = PrisonerQuoteSourceFrameReady12004(frame);
  return parent;
}

PrisonerAnswerPredicate3148BB0Raw12004 ReadRaw(CopiedQuery &query,
    const PrisonerAnswerHelperRaw12004 &parent) {
  PrisonerQuoteReadOnlyAccess12004 access{};
  access.context = &query;
  access.read_memory = CopiedQuery::Read;
  return ReadPrisonerAnswerPredicate3148BB0Raw12004(access, parent);
}

bool LiteralNullBranchFeedsParent(std::uint8_t byte, std::uint8_t parent_al) {
  auto parent = Parent();
  CopiedQuery query;
  query.Put(kDefinition + 0x2290, std::uintptr_t{0});
  query.Put(kDefinition + 0x2718, byte);
  const auto raw = ReadRaw(query, parent);
  const auto predicate = ProjectPrisonerAnswerPredicate3148BB012004(raw, {});
  PrisonerAnswerQueryArguments12004 args{};
  args.argument4_pointer = 0;
  args.argument5_pointer = 0;
  const auto helper = ProjectPrisonerAnswerInitialGate12004(
      parent, args, predicate.byte_child);
  return predicate.byte_child.raw_al == byte &&
      predicate.byte_child.receiver_identity == kDefinition &&
      predicate.byte_child.second_argument_identity == kContext + 8 &&
      predicate.byte_child.frame == parent.frame &&
      predicate.byte_child.reached_effects_source_ready &&
      helper.raw_al == parent_al && helper.reached_effects_source_ready;
}

PrisonerAnswerByteChild12004 Expression(const PrisonerAnswerHelperRaw12004 &parent) {
  PrisonerAnswerByteChild12004 expression{};
  expression.frame = parent.frame;
  expression.actual_callee_rva = kPrisonerAnswerExpressionPredicateRva12004;
  expression.receiver_identity = kExpression;
  expression.second_argument_identity = kContext + 8;
  expression.raw_al = std::uint8_t{7};
  expression.reached_effects_source_ready = true;
  return expression;
}

bool NonnullExpressionKeepsRawChildAndSkipsFallback() {
  const auto parent = Parent();
  CopiedQuery query;
  query.Put(kDefinition + 0x2290, kExpression);
  const auto raw = ReadRaw(query, parent);
  const auto predicate = ProjectPrisonerAnswerPredicate3148BB012004(raw, Expression(parent));
  return predicate.byte_child.raw_al == std::uint8_t{7} &&
      predicate.byte_child.reached_effects_source_ready &&
      query.fallback_byte_reads == 0;
}

bool MissingExpressionResultStaysUnknown() {
  const auto parent = Parent();
  CopiedQuery query;
  query.Put(kDefinition + 0x2290, kExpression);
  const auto predicate = ProjectPrisonerAnswerPredicate3148BB012004(ReadRaw(query, parent), {});
  return !predicate.byte_child.raw_al && !predicate.byte_child.reached_effects_source_ready;
}

bool ChangedFrameIsNotTheSameChild() {
  const auto parent = Parent();
  CopiedQuery query;
  query.Put(kDefinition + 0x2290, kExpression);
  auto expression = Expression(parent);
  ++expression.frame.query_sequence;
  const auto predicate = ProjectPrisonerAnswerPredicate3148BB012004(ReadRaw(query, parent), expression);
  return !predicate.byte_child.raw_al && !predicate.byte_child.reached_effects_source_ready;
}

bool ChildEffectsRemainIndependent() {
  const auto parent = Parent();
  CopiedQuery query;
  query.Put(kDefinition + 0x2290, kExpression);
  auto expression = Expression(parent);
  expression.reached_effects_source_ready = false;
  const auto predicate = ProjectPrisonerAnswerPredicate3148BB012004(ReadRaw(query, parent), expression);
  return predicate.byte_child.raw_al == std::uint8_t{7} &&
      !predicate.byte_child.reached_effects_source_ready;
}

bool UnreadFallbackByteIsNotZero() {
  const auto parent = Parent();
  CopiedQuery query;
  query.Put(kDefinition + 0x2290, std::uintptr_t{0});
  const auto predicate = ProjectPrisonerAnswerPredicate3148BB012004(ReadRaw(query, parent), {});
  return !predicate.byte_child.raw_al && !predicate.byte_child.reached_effects_source_ready;
}
} // namespace

// No main or independent execution; joins the current selected-quote compound.
bool RunPrisonerAnswerPredicate3148BB012004NewCases() {
  return LiteralNullBranchFeedsParent(0, 3) && LiteralNullBranchFeedsParent(9, 0) &&
      NonnullExpressionKeepsRawChildAndSkipsFallback() &&
      MissingExpressionResultStaysUnknown() && ChangedFrameIsNotTheSameChild() &&
      ChildEffectsRemainIndependent() && UnreadFallbackByteIsNotZero();
}
} // namespace xar::ck3_12004::new_cases
