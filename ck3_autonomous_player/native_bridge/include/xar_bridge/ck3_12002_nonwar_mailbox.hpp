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
  ck3_11906::MainThreadQueryExecutorV1 prisoner_collection = nullptr;
  ck3_11906::MainThreadQueryExecutorV1 prisoner_ransom = nullptr;
};

// This is the production registration seam used before mailbox installation.
// It is pure and can be tested without loading, attaching or querying CK3.
void RegisterNonwarMailboxExecutorsV1(
    ck3_11906::MainThreadQueryInstallEnvironmentV1 &,
    const NonwarMailboxExecutorsV1 &) noexcept;

} // namespace xar::ck3_12002
