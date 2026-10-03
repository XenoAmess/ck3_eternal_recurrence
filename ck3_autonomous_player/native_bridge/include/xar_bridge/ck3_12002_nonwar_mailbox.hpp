#pragma once

#include "xar_bridge/ck3_12002_thread_runtime.hpp"

namespace xar::ck3_12002 {

// Version-owned providers retain the master's public/private slot identities.
// Callback contexts are constructed by their corresponding version-owned wire
// handlers; an old provider is never registered merely because its DTO matches.
struct NonwarMailboxExecutorsV1 {
  ck3_11906::MainThreadQueryExecutorV1 lifestyle = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 construction = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 ranked_marriage = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 alliance_projection = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 relationship = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 marriage_submit = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 council_candidates = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 council = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 faction_gift = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 sway_state = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 sway_action = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 law_final_terms = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 law_action = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_open = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_options = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_can_start = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_gold = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_full_costs = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_destination = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_stage2_confirm = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_start = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_guest = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_guest_rules = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 feast_guest_opinion = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 factions = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 warcash = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 family_obligations = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 prewar = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 government = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 holy_order_loan = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 head_of_faith_gold = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 repentance = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 holy_order_context = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 holy_order_selected_title_terms = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 rite_governance = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 clergy = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 county_conversion_task_action = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_conversion = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_conversion_action = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_doctrines = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 rite_members = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_conversion_choices = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_conversion_inputs = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 sway_completion = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_hostility = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_doctrine_knowledge = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_tenets = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 epidemic_treatment = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 epidemic_recovery = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_conversion_reasons = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 sway_completion_execution = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_reform = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_doctrine_catalogue = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_conversion_outcome = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_numeric_special_parameters = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 sway_completion_termination = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_personal_parameters = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 sway_completion_invalidation_reason = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_draft_groups = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_draft_doctrine_choices = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_draft_tenet_choices = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_draft_resource_costs = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 religion_ai_reform_inputs = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 sway_outcome_opinion = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 prisoner_collection = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 prisoner_ransom = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 steward_develop_county = nullptr;
};

// This is the production registration seam used before mailbox installation.
// It is pure and can be tested without loading, attaching or querying CK3.
void RegisterNonwarMailboxExecutorsV1(
    ck3_11906::MainThreadQueryInstallEnvironmentV1 &,
    const NonwarMailboxExecutorsV1 &) noexcept;

} // namespace xar::ck3_12002
