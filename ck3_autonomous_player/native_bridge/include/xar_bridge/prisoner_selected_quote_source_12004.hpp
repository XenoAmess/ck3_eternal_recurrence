#pragma once
#include "xar_bridge/prisoner_recipient_score_3761780_12004.hpp"
#include "xar_bridge/prisoner_answer_helpers_12004.hpp"
#include "xar_bridge/prisoner_answer_predicate_3148bb0_12004.hpp"
#include "xar_bridge/prisoner_answer_control_inputs_12004.hpp"
#include "xar_bridge/prisoner_mode0_scalar_307c340_12004.hpp"
#include "xar_bridge/negotiated_reply_reporter_null_path_12004.hpp"
#include "xar_bridge/prisoner_cost_lane_9d7060_readonly_12004.hpp"
#include "xar_bridge/prisoner_auto_accept_trigger_condition_12004.hpp"
#include "xar_bridge/prisoner_trigger_root_scope_gate_12004.hpp"
#include <array>
#include <bit>

namespace xar::ck3_12004 {
struct PrisonerQuoteCostSource12004 {
  std::uintptr_t cost_block_identity = 0;
  std::array<std::int64_t, 10> original_output_q64{};
  std::array<PrisonerCostLane9D7060Readonly12004, 10> lanes{};
  std::optional<std::uint8_t> clamp_nonnegative_raw_u8, round_raw_u8;
  std::optional<std::array<std::int64_t, 10>> projected_q64, native_final_q64;
  bool original_output_copied = false, numeric_source_ready = false, native_getter_called = false;
  std::string unavailable_reason;
};
struct PrisonerQuoteSourceSample12004 {
  PrisonerQuoteSourceFrame12004 frame;
  PrisonerQuoteInternalAliases12004 caller_aliases;
  std::optional<PrisonerQuoteRecipientScoreSource12004> recipient_score;
  PrisonerAnswerHelperRaw12004 answer_raw;
  PrisonerAnswerPredicate3148BB0Raw12004 answer_predicate_raw;
  std::optional<PrisonerAnswerControlPackage12004> answer_control_raw;
  std::optional<PrisonerMode0ScalarInputs12004> mode0_scalar_raw;
  PrisonerAnswerHelperResult12004 initial_gate, mode0, mode1;
  std::optional<std::uint8_t> source_answer_raw_u8, native_answer_raw_u8;
  bool answer_source_ready = false, answer_effects_source_ready = false;
  std::optional<PrisonerQuoteCostSource12004> actor_on_send_costs;
  std::optional<std::uintptr_t> auto_accept_trigger_identity;
  std::optional<std::uint8_t> auto_accept_scalar_raw_u8;
  std::optional<PrisonerAutoAcceptTriggerRaw12004> auto_accept_trigger_raw;
  std::optional<PrisonerAutoAcceptTriggerCondition12004> auto_accept_condition;
  std::optional<bool> source_auto_accept, native_auto_accept;
  std::array<std::optional<std::uint8_t>, 4> answer_lookup_raw_u8{};
  bool copied_at_existing_query_call = false;
};
struct PrisonerSelectedQuoteSource12004 {
  std::uint32_t source_ordinal = 0;
  std::string quote_kind;
  std::vector<PrisonerQuoteSourceSample12004> samples;
  bool selected_query_completed = false;
  std::string unavailable_reason = "not_evaluated";
};
PrisonerQuoteSourceSample12004 CopyPrisonerQuoteSourceSample12004(
    const PrisonerQuoteReadOnlyAccess12004 &, PrisonerQuoteSourceFrame12004,
    std::uintptr_t owned_context, bool ordinary_ransom);
void CopyPrisonerQuoteRecipientScoreSource12004(const PrisonerQuoteReadOnlyAccess12004 &,
    PrisonerQuoteSourceSample12004 &);
void CopyPrisonerQuoteCostSource12004(const PrisonerQuoteReadOnlyAccess12004 &,
    PrisonerQuoteSourceSample12004 &, std::uintptr_t cost_block, const std::int64_t *original_output);
void CopyPrisonerQuoteAutoAcceptSource12004(const PrisonerQuoteReadOnlyAccess12004 &,
    PrisonerQuoteSourceSample12004 &);
void FinishPrisonerQuoteSourceSample12004(PrisonerQuoteSourceSample12004 &, bool same_frame);
void ProjectPrisonerQuoteAnswerParent12004(PrisonerQuoteSourceSample12004 &,
    const std::optional<PrisonerAnswerByteChild12004> &expression_372df10 = {},
    const PrisonerAnswerModeChildren12004 &mode0_children = {},
    const PrisonerAnswerModeChildren12004 &mode1_children = {});
// Exact 310CEC0 tail: wrapped QWORD addition, optional signed clamp, integer
// nearest-unit transform (including EDX's signed32 narrowing). No float math.
std::int64_t PrisonerQuoteCostRound310D07012004(std::int64_t) noexcept;
void ProjectPrisonerQuoteCosts12004(PrisonerQuoteCostSource12004 &);
std::string SerializePrisonerSelectedQuoteSource12004(const PrisonerSelectedQuoteSource12004 &);
bool AppendPrisonerSelectedQuoteSource12004(std::string &command_result,
    const PrisonerSelectedQuoteSource12004 &);
} // namespace xar::ck3_12004
