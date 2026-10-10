#pragma once

#include "xar_bridge/prisoner_auto_accept_trigger_condition_12004.hpp"
#include "xar_bridge/source_read_leaf_frame_12004.hpp"
#include "xar_bridge/trigger_scope_table_provider_3795a60_12004.hpp"

namespace xar::ck3_12004 {
struct SourceTriggerRootScopeGateResult12004;

struct SourceAutoAcceptTriggerRaw12004 {
  SourceLeafFrame12004 frame;
  PrisonerQuoteInternalAliases12004 aliases;
  std::optional<std::uintptr_t> trigger_identity;
  std::optional<std::uintptr_t> trigger_vtable;
  std::optional<std::uintptr_t> root_kind_getter_slot58, root_mask_getter_slot60, evaluator_slotc8;
  std::optional<std::uintptr_t> support_report_identity38;
  std::optional<bool> parent_alias_shape_matches, source_leaf_scope_word_matches;
  TriggerScopeTableProviderRaw3795A6012004 scope_table_provider;
  bool query_frame_ready = false;
  bool any_native_field_read_attempted = false;
  bool all_attempted_native_reads_complete = false;
  bool actual_trigger_evaluation_observed = false;
  std::vector<std::string> missing_fields;
  std::string unavailable_reason;
};

struct SourceAutoAcceptTriggerCondition12004 {
  SourceLeafFrame12004 frame;
  std::optional<std::uintptr_t> trigger_identity;
  std::optional<bool> root_validator_bypassed, root_scope_source_valid;
  bool helper_matches_query = false;
  bool scope_table_matches_query = false;
  std::optional<bool> helper_conditional_allows, helper_qualified_allows, conditional_reaches_virtual_c8;
  std::optional<std::uint8_t> source_projected_returned_raw_u8;
  std::optional<bool> accepted;
  bool source_value_ready = false;
  bool final_virtual_evaluator_source_ready = false;
  bool native_callback_executed = false;
  bool actual_trigger_evaluation_observed = false;
  std::string unavailable_reason;
};

// Only the caller-owned generic snapshot is supplied. No prisoner role Frame
// is constructed, and the producer must be the literal372E000 wrapper.
SourceAutoAcceptTriggerRaw12004 ReadPrisonerAutoAcceptTriggerCondition12004(
    const SourceLeafReadOnlyAccess12004 &, const SourceLeafFrame12004 &,
    const PrisonerQuoteInternalAliases12004 &);
SourceAutoAcceptTriggerCondition12004 EvaluatePrisonerAutoAcceptTriggerCondition12004(
    const SourceAutoAcceptTriggerRaw12004 &, const SourceTriggerRootScopeGateResult12004 &);

// Only16's new M5 compound owns execution of these generic-frame boundaries.
void RunSourceAutoAcceptTriggerConditionGenericFocus12004();
} // namespace xar::ck3_12004
