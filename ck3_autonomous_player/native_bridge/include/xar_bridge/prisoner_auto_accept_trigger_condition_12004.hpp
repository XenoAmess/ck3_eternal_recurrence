#pragma once

#include "xar_bridge/prisoner_quote_readonly_source_12004.hpp"

#define XAR_HAS_PRISONER_AUTO_ACCEPT_TRIGGER_CONDITION_12004 1

namespace xar::ck3_12004 {
inline constexpr std::uintptr_t kPrisonerAutoAcceptTriggerWrapperRva12004 = 0x372E000;
inline constexpr std::uintptr_t kPrisonerAutoAcceptTriggerWrapperEndRva12004 = 0x372E42E;
inline constexpr std::uintptr_t kPrisonerAutoAcceptTriggerParentCallRva12004 = 0x372DF78;

struct PrisonerTriggerRootScopeGateResult12004;

// Copied query fields. They do not claim a natural evaluator entry or invoke
// any scope validator, trigger getter, evaluator, logger, or instrumentation.
struct PrisonerAutoAcceptTriggerRaw12004 {
  PrisonerQuoteSourceFrame12004 frame;
  PrisonerQuoteInternalAliases12004 aliases;
  std::optional<std::uintptr_t> trigger_identity;
  std::optional<std::uintptr_t> trigger_vtable;
  std::optional<std::uintptr_t> root_kind_getter_slot58;
  std::optional<std::uintptr_t> root_mask_getter_slot60;
  std::optional<std::uintptr_t> evaluator_slotc8;
  std::optional<std::uintptr_t> support_report_identity38;
  std::optional<bool> parent_alias_shape_matches;
  bool query_frame_ready = false;
  bool any_native_field_read_attempted = false;
  bool all_attempted_native_reads_complete = false;
  bool actual_trigger_evaluation_observed = false;
  std::vector<std::string> missing_fields;
  std::string unavailable_reason;
};

struct PrisonerAutoAcceptTriggerCondition12004 {
  PrisonerQuoteSourceFrame12004 frame;
  std::optional<std::uintptr_t> trigger_identity;
  std::optional<bool> root_validator_bypassed;
  std::optional<bool> root_scope_source_valid;
  bool helper_matches_query = false;
  std::optional<bool> helper_conditional_allows;
  std::optional<bool> helper_qualified_allows;
  std::optional<bool> conditional_reaches_virtual_c8;
  // The closed wrapper preserves the raw returned byte. The final +C8
  // producer is unknown, so there is no interface accepting an invented value.
  std::optional<std::uint8_t> source_projected_returned_raw_u8;
  std::optional<bool> accepted;
  bool source_value_ready = false;
  bool final_virtual_evaluator_source_ready = false;
  bool native_callback_executed = false;
  bool actual_trigger_evaluation_observed = false;
  std::string unavailable_reason;
};

PrisonerAutoAcceptTriggerRaw12004 ReadPrisonerAutoAcceptTriggerCondition12004(
    const PrisonerQuoteReadOnlyAccess12004 &, const PrisonerQuoteSourceFrame12004 &,
    const PrisonerQuoteInternalAliases12004 &, std::optional<std::uintptr_t> trigger_identity);

PrisonerAutoAcceptTriggerCondition12004 EvaluatePrisonerAutoAcceptTriggerCondition12004(
    const PrisonerAutoAcceptTriggerRaw12004 &, const PrisonerTriggerRootScopeGateResult12004 &);
} // namespace xar::ck3_12004
