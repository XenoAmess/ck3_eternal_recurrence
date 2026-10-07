#pragma once

#include "xar_bridge/battle_reinforcement_arrival_admission_12003.hpp"
#include "xar_bridge/battle_context_source_inputs_v1.hpp"
#include "xar_bridge/battle_current_finalizer_manager_inputs_v1.hpp"
#include "xar_bridge/battle_current_warscore_caps_v1.hpp"
#include "xar_bridge/battle_current_own_nested_modifier_dto.hpp"
#include "xar_bridge/knight_current_model_association_v1.hpp"

#include "xar_bridge/ck3_12003_maa_recruitment.hpp"
#include "xar_bridge/owned_regiments.hpp"

#include "xar_bridge/war_occupation_targets_v1.hpp"
#include "xar_bridge/siege_membership_v1.hpp"
#include "xar_bridge/battle_native_owner_recall_inputs_12003.hpp"
#include "xar_bridge/ck3_12003_army_supply_timing.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"
#include "xar_bridge/army_scoped_ordered_refill_inputs_v1.hpp"
#include "xar_bridge/army_current_fleet_supply_tick_inputs_v1.hpp"
#include "xar_bridge/army_captured_target_land_supply_inputs_v1.hpp"
#include "xar_bridge/army_current_daily_supply_dispatch_inputs_v1.hpp"
#include "xar_bridge/army_future_daily_supply_schedule_v1.hpp"
#include "xar_bridge/army_source_derived_next_daily_supply_frame_v1.hpp"
#include "xar_bridge/army_current_unit_new_date_schedule_inputs_v1.hpp"
#include "xar_bridge/army_current_unit_new_date_callback_entry_inputs_v1.hpp"
#include "xar_bridge/army_current_detachment_callback_inputs_v1.hpp"
#include "xar_bridge/army_current_detachment_store_inputs_v1.hpp"
#include "xar_bridge/army_current_character_detachment_inputs_v1.hpp"
#include "xar_bridge/army_current_month_first_refill_call_inputs_v1.hpp"
#include "xar_bridge/ck3_12003_fixed_chunk0_preparation.hpp"
#include "xar_bridge/army_ordered_besieging_refill_inputs_v1.hpp"
#include "xar_bridge/army_ordered_besieging_fixed_chunk0_preparation_v1.hpp"
#include "xar_bridge/phase_rite_parameters_v1.hpp"
#include "xar_bridge/phase_warmonger_core_v1.hpp"
#include "xar_bridge/phase_berserker_validity_inputs_v1.hpp"
#include "xar_bridge/phase_berserker_chance_inputs_v1.hpp"
#include "xar_bridge/player_event_trait_membership_12004.hpp"
#include "xar_bridge/phase_event_calendar_observation_v1.hpp"
#include "xar_bridge/phase_event_role_compatibility_v1.hpp"
#include "xar_bridge/phase_event_commander_side_identity_v1.hpp"

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {

// This file is the version-neutral semantic boundary between the pipe bridge
// and a CK3 executable adapter. Native pointers, RVAs, vtables and object
// layouts must not cross it.

// A generation-bound native declaration choice. The indexes are current
// database/evaluator ordinals, not persistent Casus Belli identifiers. An
// adapter must re-enumerate the full value before submission so a stale choice
// cannot silently become a different war.
struct DeclarableWarSnapshot {
  std::int32_t target_character_id = -1;
  std::int32_t casus_belli_index = -1;
  std::string casus_belli_key;
  std::int32_t configuration_index = -1;
  std::int32_t claimant_character_id = -1;
  std::vector<std::int32_t> target_title_ids;

  friend bool operator==(const DeclarableWarSnapshot &,
                         const DeclarableWarSnapshot &) = default;
};

// One directly sendable, generation-bound marriage choice for the minimal
// headless path. Exact CharacterID handles include the component generation;
// adapters must not resolve them by low-24-bit slot alone.
struct ArrangeMarriageChoice {
  std::int32_t played_character_id = -1;
  std::int32_t candidate_character_id = -1;

  friend bool operator==(const ArrangeMarriageChoice &,
                         const ArrangeMarriageChoice &) = default;
};

// Private read-only evidence for a ruler arranging a marriage for the
// observed primary heir. These rows are not action choices and carry no
// native AI rank when the played Character has no matchmaking Strategy.
struct ArrangeMarriageFamilyCandidateV1 {
  std::int32_t played_character_id = -1;
  std::int32_t subject_character_id = -1;
  std::int32_t candidate_character_id = -1;
  std::int32_t recipient_matchmaker_character_id = -1;
  std::int32_t intermediary_character_id = -1;
  std::int64_t recipient_ai_accept_raw = 0;
  std::uint8_t recipient_answer_status_raw = 0;
  bool complete_can_send = false;
  bool recipient_answer_allows_send = false;
  // Exact private value inputs from the already-enumerated native Character
  // pair. Null means this build did not bind the lineage/age observer.
  std::optional<std::int16_t> heir_adult_measure_raw;
  std::optional<std::int16_t> candidate_adult_measure_raw;
  std::optional<std::int32_t> played_dynasty_id;
  std::optional<std::int32_t> heir_dynasty_id;
  std::optional<std::int32_t> candidate_dynasty_id;
  std::optional<bool> realm_backed_actor_recipient;

  friend bool operator==(const ArrangeMarriageFamilyCandidateV1 &,
                         const ArrangeMarriageFamilyCandidateV1 &) = default;
};

// Bounded, version-neutral evidence from one native marriage enumeration.
// Role IDs are captured after the interaction's redirect script has run, so a
// live empty result can be distinguished from storage traversal or context
// routing failures without requiring the CK3 window to be visible.
struct ArrangeMarriageValidationSample {
  std::int32_t slot_index = -1;
  std::int32_t candidate_character_id = -1;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  std::int32_t secondary_actor_character_id = -1;
  std::int32_t secondary_recipient_character_id = -1;
  std::int32_t intermediary_character_id = -1;

  friend bool operator==(const ArrangeMarriageValidationSample &,
                         const ArrangeMarriageValidationSample &) = default;
};

struct ArrangeMarriageQueryDiagnostics {
  std::int32_t storage_capacity = 0;
  std::int32_t slots_scanned = 0;
  std::int32_t empty_slots = 0;
  std::int32_t live_candidates = 0;
  std::int32_t dead_candidates = 0;
  std::int32_t self_candidates = 0;
  std::int32_t generation_mismatch_candidates = 0;
  std::int32_t contexts_constructed = 0;
  std::int32_t context_construct_failures = 0;
  std::int32_t native_validate_true = 0;
  std::int32_t native_validate_false = 0;
  std::int32_t family_subject_role_mismatches = 0;
  std::vector<ArrangeMarriageValidationSample> validation_false_samples;

  friend bool operator==(const ArrangeMarriageQueryDiagnostics &,
                         const ArrangeMarriageQueryDiagnostics &) = default;
};

enum class ArmyRouteReadStatus {
  not_attempted,
  complete_empty,
  complete_nonempty,
  target_only,
  invalid_header,
  unresolved_entry,
};

struct ArmySnapshot {
  std::int32_t army_id = -1;
  std::int32_t owner_character_id = -1;
  bool has_current_province = false;
  std::int32_t current_province_id = -1;
  std::vector<std::int32_t> route_province_ids;
  ArmyRouteReadStatus route_read_status = ArmyRouteReadStatus::not_attempted;
  std::optional<std::int32_t> route_source_count;
  bool move_target_observable = false;
  std::int32_t move_target_province_id = -1;
  std::int32_t army_state_code = 0;
  std::string army_state = "unknown";
  bool in_combat = false;
  bool retreating = false;
  bool controllable = false;
  // Paused exact-build read for a primary defender's hostile siege at this
  // Army's current Province. Absent when the siege or besieger join is unknown.
  std::optional<std::int32_t> siege_days_left;
  std::optional<std::int32_t> siege_province_holder_character_id;
  std::optional<bool> siege_province_in_player_subrealm;

  friend bool operator==(const ArmySnapshot &, const ArmySnapshot &) = default;
};

enum class ArmyStrengthScopeRole {
  player,
  active_war_ally,
  active_war_enemy,
};

// Read-only observations from the first persistent-regiment data record.
// Each chunk is independently matched back to the actual CArmyRegiment;
// these native predicates and monthly fraction are not a future soldier count.
struct ArmyRegimentReplenishmentChunk {
  std::int32_t persistent_regiment_id = -1;
  std::int32_t chunk_index = 0;
  std::int32_t current_soldiers = 0;
  std::int32_t maximum_soldiers = 0;
  std::int32_t state_raw = 0;
  bool native_can_replenish = false;
  bool native_chunk_can_replenish = false;
  std::int64_t persistent_monthly_replenishment_fraction_raw = 0;

  friend bool operator==(const ArmyRegimentReplenishmentChunk &,
                         const ArmyRegimentReplenishmentChunk &) = default;
};

struct ArmyRegimentReplenishmentSnapshot {
  bool available = false;
  std::int32_t army_regiment_id = -1;
  std::optional<std::int32_t> native_data_record_count;
  std::string unavailable_reason;
  std::vector<ArmyRegimentReplenishmentChunk> chunks;

  friend bool operator==(const ArmyRegimentReplenishmentSnapshot &,
                         const ArmyRegimentReplenishmentSnapshot &) = default;
};

// One generation-checked aggregate over a public CUnit and its exact CArmy /
// CArmyRegiment graph. A row is atomic: when any component ID, native array,
// public-ID identity predicate or checked sum cannot be validated, available
// is false and
// every numeric aggregate must remain uninterpretable. The base-power raw
// value is CK3's AI metric, not a combat prediction or win probability.
enum class ArmyGatheringDaysStatus {
  unavailable,
  not_gathering,
  available,
};

enum class ArmyMovementProgressStatus {
  unavailable,
  not_applicable,
  partial,
  available,
};

// Unrounded native predictions for every committed path prefix. Arrival dates
// are the existing bridge projection; the final prefix is the full remainder.
struct ArmyCommittedRouteTimelineSnapshot {
  ArmyMovementProgressStatus status = ArmyMovementProgressStatus::unavailable;
  std::vector<std::int32_t> committed_route_province_ids;
  std::vector<std::int64_t> native_route_prefix_remaining_days_q100000;
  std::optional<std::int64_t> native_full_route_remaining_days_q100000;
  std::vector<std::int32_t> projected_route_arrival_date_raws;
  std::string unavailable_reason;

  friend bool operator==(const ArmyCommittedRouteTimelineSnapshot &,
                         const ArmyCommittedRouteTimelineSnapshot &) = default;
};

// Independent current CUnit observations. Accumulated movement and cached
// speed are movement-weight operands; normalized progress is Q100000 and is
// not elapsed days. Remaining duration is signed Q100000 days, without a
// guessed arrival tick or an inferred embark phase.
struct ArmyMovementProgressSnapshot {
  ArmyMovementProgressStatus status = ArmyMovementProgressStatus::unavailable;
  std::optional<std::int32_t> unit_state_raw;
  std::optional<std::int64_t> accumulated_movement_weight_raw;
  std::optional<std::int64_t> cached_edge_speed_raw;
  std::optional<std::int64_t> normalized_edge_progress_raw;
  std::optional<std::int64_t> first_route_edge_remaining_duration_raw;
  std::string unavailable_reason;
  std::optional<ArmyCommittedRouteTimelineSnapshot> committed_route_timeline;
  std::optional<std::int64_t> current_edge_movement_rate_raw;
  std::optional<bool> native_army_movement_admission;

  friend bool operator==(const ArmyMovementProgressSnapshot &,
                         const ArmyMovementProgressSnapshot &) = default;
};

enum class ArmyRegimentTypeStatusV1 {
  unavailable,
  absent,
  available,
};

// Complete actual CArmyRegiment membership from the same checked array and
// current/maximum reads used by the aggregate. No persistent-record coverage
// or replenishment cause is inferred from these whole-soldier counts.
struct ArmyRegimentStrengthSnapshot {
  std::int32_t army_regiment_id = -1;
  std::int32_t current_soldiers = 0;
  std::int32_t maximum_soldiers = 0;

  // Additive type metadata belongs to this raised ArRg roster component,
  // not a persistent Regi record or the owner's full MAA inventory.
  ArmyRegimentTypeStatusV1 maa_type_status =
      ArmyRegimentTypeStatusV1::unavailable;
  std::string maa_type_key;
  // Signed native type+0x2A0; legal zero differs from an unread null.
  std::optional<std::int32_t> siege_tier;
  std::string composition_unavailable_reason;
  // Exact .3 2A956D0(ArRg), independent of type/tier and writer admission.
  std::optional<bool> native_supply_loss_eligible;
  std::string supply_loss_eligibility_unavailable_reason =
      "supply_loss_eligibility_not_bound";

  friend bool operator==(const ArmyRegimentStrengthSnapshot &,
                         const ArmyRegimentStrengthSnapshot &) = default;
};

// Same-frame readonly native monthly loss operands and integer budgets.
// The definition<=0 category is deliberately unnamed. These are current-input
// native outputs, not future net troop loss, casualties, or a setter forecast.
struct ArmyLossApplicationInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  // Native CArmy+1E8 is a raiding association, not the active Siege ID.
  std::int32_t raid_association_id = -1;
  bool siege_active = false;
  bool raid_active = false;
  std::int64_t siege_rate_raw = 0;
  std::int64_t raid_rate_raw = 0;
  std::int32_t whole_soldiers = 0;
  std::int32_t definition_le_zero_soldiers = 0;
  std::int32_t supply_eligible_soldiers = 0;
  std::int32_t definition_le_zero_supply_eligible_soldiers = 0;
  std::int32_t current_supply_loss_budget = 0;
  std::int32_t siege_loss_budget = 0;
  std::int32_t raid_loss_budget = 0;

  friend bool operator==(const ArmyLossApplicationInputsV1 &,
                         const ArmyLossApplicationInputsV1 &) = default;
};

// Exact .3 operands of24E4D10 admission and24E4FA0 post-stock component.
// This is a readonly current frame; no updater or loss writer is called.
struct ArmyMonthlyLossBudgetInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  std::optional<std::int32_t> unit_native_170_raw;
  std::optional<bool> native_unit_in_combat;
  std::optional<bool> native_unit_gathering;
  std::optional<std::int32_t> army_gathering_count_raw;
  std::optional<std::vector<std::int32_t>> loaded_supply_state_levels;
  std::optional<std::vector<std::int64_t>> loaded_supply_state_fractions_raw;
  std::optional<bool> native_fleet_supply_loss_suppressed;
  std::optional<bool> commander_valid;
  std::optional<std::uint16_t> commander_supply_modifier_id;
  std::optional<std::int64_t> commander_supply_modifier_raw;

  friend bool operator==(const ArmyMonthlyLossBudgetInputsV1 &,
                         const ArmyMonthlyLossBudgetInputsV1 &) = default;
};

// Ordered current-frame operands for24E3430's counters and deferred ArmyID list.
struct ArmyMonthlyCallerWarCounterRowV1 {
  bool available = false;
  std::string unavailable_reason;
  std::int32_t stored_index = 0;
  std::int32_t war_reference_id = -1;
  std::optional<std::int32_t> resolved_war_id;
  std::optional<bool> used_fallback;
  std::optional<std::int32_t> native_selected_side;
  std::optional<std::int32_t> native_counter_30_raw;
  friend bool operator==(const ArmyMonthlyCallerWarCounterRowV1 &,
                         const ArmyMonthlyCallerWarCounterRowV1 &) = default;
};

struct ArmyMonthlyCallerEffectInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  std::optional<std::uint8_t> army_byte_22_raw;
  std::optional<std::int64_t> current_date_storage_raw64;
  std::optional<std::int32_t> unit_actor_character_id;
  std::optional<std::vector<ArmyMonthlyCallerWarCounterRowV1>> war_counter_rows;
  std::optional<std::vector<std::int32_t>> manager_army_id_list_2a5a8;
  friend bool operator==(const ArmyMonthlyCallerEffectInputsV1 &,
                         const ArmyMonthlyCallerEffectInputsV1 &) = default;
};

struct ArmyDailyQueueInitialResolutionRowV1 {
  bool available = false;
  std::string unavailable_reason;
  std::int32_t stored_index = 0;
  std::int32_t raw_army_reference_id = -1;
  std::optional<std::int32_t> resolved_army_id;
  std::optional<bool> used_fallback;
  std::optional<std::uint32_t> army_magic_14_raw;
  std::optional<bool> native_army_identity_valid;
  friend bool operator==(const ArmyDailyQueueInitialResolutionRowV1 &,
                         const ArmyDailyQueueInitialResolutionRowV1 &) = default;
};

// Initial current frame, before2A9FA10 and any2A978A0 call. These resolutions
// must not substitute for later occurrences after a removal call mutates slots.
struct ArmyDailyQueueInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  std::optional<std::vector<std::int32_t>> manager_army_id_list_2a5a8;
  std::optional<std::vector<ArmyDailyQueueInitialResolutionRowV1>> initial_army_resolution_rows;
  friend bool operator==(const ArmyDailyQueueInputsV1 &,
                         const ArmyDailyQueueInputsV1 &) = default;
};

struct ArmyManagerCleanupIdListV1 {
  std::string manager_offset;
  std::optional<std::vector<std::int32_t>> ordered_army_ids;
  friend bool operator==(const ArmyManagerCleanupIdListV1 &,
                         const ArmyManagerCleanupIdListV1 &) = default;
};

struct ArmyManagerCleanupBucketRowV1 {
  std::int32_t stored_index = 0;
  std::optional<std::int32_t> observed_army_id;
  bool native_same_cleanup_army_pointer = false;
  friend bool operator==(const ArmyManagerCleanupBucketRowV1 &,
                         const ArmyManagerCleanupBucketRowV1 &) = default;
};

// Initial first daily request and the finite2A98200 manager membership stage.
// The bucket's helper-resolved physical Army can differ from the passed Army.
struct ArmyFirstRemovalCleanupInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  std::optional<bool> candidate_found;
  std::optional<std::int32_t> candidate_stored_index;
  std::optional<std::int32_t> argument_army_id;
  std::optional<std::int32_t> cleanup_resolved_army_id;
  std::optional<bool> cleanup_used_fallback;
  std::optional<std::uint32_t> selected_bucket_index;
  std::vector<ArmyManagerCleanupIdListV1> id_lists;
  std::optional<std::vector<ArmyManagerCleanupBucketRowV1>> selected_bucket_rows;
  std::optional<std::vector<std::array<std::uint32_t, 4>>> records_b0;
  friend bool operator==(const ArmyFirstRemovalCleanupInputsV1 &,
                         const ArmyFirstRemovalCleanupInputsV1 &) = default;
};

struct ArmyCurrentHelperDomainCountRecordV1 {
  std::int32_t stored_index = 0;
  std::int32_t count_00_raw = 0;
  std::int32_t count_04_raw = 0;
  std::int32_t state_18_raw = 0;
  friend bool operator==(const ArmyCurrentHelperDomainCountRecordV1 &,
                         const ArmyCurrentHelperDomainCountRecordV1 &) = default;
};

// Ordered source operands for isolated current-frame2C57020 calls. These are
// neither the late2A978A0 entry frame nor observed effects of2A98590.
struct ArmyCurrentHelperDomainRowV1 {
  std::int32_t group_index = 0;
  std::int32_t stored_index = 0;
  std::int32_t record_regiment_reference_id = -1;
  std::int32_t chunk_index = 0;
  std::optional<std::int32_t> record_regiment_resolved_id;
  std::optional<bool> record_regiment_used_fallback;
  std::optional<std::uint32_t> record_regiment_magic_14_raw;
  std::optional<bool> data_record_present;
  std::optional<std::int32_t> data_state_18_raw;
  std::optional<std::int32_t> data_owner_regiment_reference_id;
  std::optional<std::int32_t> receiver_regiment_resolved_id;
  std::optional<bool> receiver_regiment_used_fallback;
  std::optional<std::int32_t> receiver_state_138_raw;
  std::optional<std::int32_t> receiver_title_reference_130_raw;
  std::optional<std::int32_t> receiver_character_reference_12c_raw;
  std::optional<std::int32_t> owner_title_resolved_id;
  std::optional<bool> owner_title_used_fallback;
  std::optional<std::int32_t> owner_title_holder_character_id_128_raw;
  std::optional<std::int32_t> selected_character_reference_id;
  std::optional<std::int32_t> selected_character_resolved_id;
  std::optional<bool> selected_character_used_fallback;
  std::optional<bool> character_domain_child_present;
  std::optional<std::int32_t> domain_reference_id;
  std::optional<std::int32_t> domain_resolved_id;
  std::optional<bool> domain_used_fallback;
  std::optional<std::uint32_t> domain_magic_0c_raw;
  std::optional<bool> domain_data_30_present;
  std::optional<std::uint8_t> domain_flag_17e_raw;
  std::optional<std::int32_t> count_base_128_raw;
  std::optional<std::vector<ArmyCurrentHelperDomainCountRecordV1>> count_records;
  std::optional<std::int32_t> domain_owner_character_reference_id;
  std::optional<std::int32_t> domain_owner_character_resolved_id;
  std::optional<bool> domain_owner_character_used_fallback;
  std::optional<std::uint32_t> domain_owner_character_magic_1c_raw;
  std::optional<std::int64_t> domain_value_48_raw64;
  std::optional<std::int32_t> domain_alias_ordinal;
  friend bool operator==(const ArmyCurrentHelperDomainRowV1 &,
                         const ArmyCurrentHelperDomainRowV1 &) = default;
};

struct ArmyCurrentHelperDomainInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  std::int32_t entry_army_id = -1;
  std::optional<std::int32_t> group_count_5c_raw;
  std::optional<std::vector<ArmyCurrentHelperDomainRowV1>> rows;
  friend bool operator==(const ArmyCurrentHelperDomainInputsV1 &,
                         const ArmyCurrentHelperDomainInputsV1 &) = default;
};

struct ArmyCurrentHelperPointRecordV1 {
  std::int32_t stored_index = 0;
  std::int32_t record_regiment_reference_id = -1;
  std::int32_t chunk_index = 0;
  std::optional<std::int32_t> record_regiment_resolved_id;
  std::optional<bool> record_regiment_used_fallback;
  std::optional<std::uint32_t> record_regiment_magic_14_raw;
  std::optional<bool> data_record_present;
  std::optional<std::int32_t> data_alias_ordinal;
  std::optional<std::uint8_t> data_byte_14_raw;
  std::optional<std::int32_t> data_state_18_raw;
  std::optional<std::int32_t> data_owner_regiment_reference_id;
  std::optional<std::int32_t> receiver_regiment_resolved_id;
  std::optional<bool> receiver_regiment_used_fallback;
  std::optional<std::int32_t> receiver_title_reference_130_raw;
  std::optional<std::int32_t> receiver_character_reference_12c_raw;
  std::optional<std::int32_t> owner_title_resolved_id;
  std::optional<bool> owner_title_used_fallback;
  std::optional<std::int32_t> owner_title_holder_character_id_128_raw;
  std::optional<std::int32_t> selected_character_reference_id;
  std::optional<std::int32_t> selected_character_resolved_id;
  std::optional<bool> selected_character_used_fallback;
  std::optional<bool> character_child_1c0_present;
  std::optional<std::int32_t> membership_alias_ordinal;
  std::optional<std::int32_t> membership_count_2b4_raw;
  std::optional<std::vector<std::int32_t>> ordered_persistent_regiment_ids_2a8;
  friend bool operator==(const ArmyCurrentHelperPointRecordV1 &,
                         const ArmyCurrentHelperPointRecordV1 &) = default;
};

struct ArmyCurrentHelperPointCharacterV1 {
  std::int32_t stored_index = 0;
  std::int32_t character_reference_id = -1;
  std::optional<std::int32_t> character_resolved_id;
  std::optional<bool> character_used_fallback;
  std::optional<bool> character_child_1b8_present;
  std::optional<std::int32_t> child_1b8_alias_ordinal;
  std::optional<std::uint8_t> child_byte_108_raw;
  std::optional<std::int32_t> child_character_reference_fc_raw;
  std::optional<bool> character_child_1c8_present;
  std::optional<bool> character_child_1c0_present;
  friend bool operator==(const ArmyCurrentHelperPointCharacterV1 &,
                         const ArmyCurrentHelperPointCharacterV1 &) = default;
};

struct ArmyCurrentHelperPointGroupV1 {
  std::int32_t group_index = 0;
  std::int32_t record_count_14_raw = 0;
  std::optional<std::vector<ArmyCurrentHelperPointRecordV1>> record_rows;
  std::int32_t character_count_2c_raw = 0;
  std::optional<std::vector<ArmyCurrentHelperPointCharacterV1>> character_rows;
  friend bool operator==(const ArmyCurrentHelperPointGroupV1 &,
                         const ArmyCurrentHelperPointGroupV1 &) = default;
};

struct ArmyCurrentHelperPointStoreInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  std::int32_t entry_army_id = -1;
  std::optional<std::int32_t> helper_resolved_army_id;
  std::optional<bool> helper_used_fallback;
  std::optional<bool> helper_same_current_army_pointer;
  std::optional<std::int32_t> group_count_5c_raw;
  std::optional<std::vector<ArmyCurrentHelperPointGroupV1>> groups;
  friend bool operator==(const ArmyCurrentHelperPointStoreInputsV1 &,
                         const ArmyCurrentHelperPointStoreInputsV1 &) = default;
};

// Current native county-entry budget, independent of a route or applied event.
// The predicate uses the validated current province and the FIRST province of
// the complete stored route. It omits the entry executor's special-call flag;
// even a true condition is not evidence that an entry or soldier write occurred.
struct ArmyCountyEntryInputsV1 {
  bool available = false;
  std::string unavailable_reason;
  std::int32_t whole_soldiers = 0;
  std::int32_t current_loss_budget = 0;
  std::int64_t effective_fraction_raw = 0;
  std::int64_t minimum_multiplier_raw = 0;
  std::int32_t loaded_minimum_soldiers = 0;
  bool condition_available = false;
  std::string condition_unavailable_reason = "county_entry_budget_unavailable";
  std::int32_t actor_character_id = -1;
  std::int32_t source_province_id = -1;
  std::int32_t target_province_id = -1;
  std::int32_t mode = 0;
  bool condition_passes = false;

  friend bool operator==(const ArmyCountyEntryInputsV1 &,
                         const ArmyCountyEntryInputsV1 &) = default;
};

// Independent observation of the existing CUnit -> CArmy resolver. Available
// describes the read of the reference/branch, including a failed CArmy lookup.
enum class ArmyNativeResolutionBranchV1 {
  unavailable,
  reference_absent,
  storage_unavailable,
  index_out_of_range,
  entry_empty,
  full_id_mismatch,
  resolved,
};

constexpr std::string_view ArmyNativeResolutionBranchNameV1(
    ArmyNativeResolutionBranchV1 branch) noexcept {
  switch (branch) {
  case ArmyNativeResolutionBranchV1::reference_absent:
    return "reference_absent";
  case ArmyNativeResolutionBranchV1::storage_unavailable:
    return "storage_unavailable";
  case ArmyNativeResolutionBranchV1::index_out_of_range:
    return "index_out_of_range";
  case ArmyNativeResolutionBranchV1::entry_empty:
    return "entry_empty";
  case ArmyNativeResolutionBranchV1::full_id_mismatch:
    return "full_id_mismatch";
  case ArmyNativeResolutionBranchV1::resolved:
    return "resolved";
  default:
    return "unavailable";
  }
}

struct ArmyNativeResolutionSnapshotV1 {
  bool available = false;
  ArmyNativeResolutionBranchV1 branch =
      ArmyNativeResolutionBranchV1::unavailable;
  std::optional<std::int32_t> raw_reference;
  std::optional<std::int32_t> reference_index;
  std::optional<std::int32_t> storage_capacity;
  std::optional<std::int32_t> entry_full_id;

  friend bool operator==(const ArmyNativeResolutionSnapshotV1 &,
                         const ArmyNativeResolutionSnapshotV1 &) = default;
};

// Exact .3 current Province mode0 supply contributors. DATA supports an
// independent conditional refill calculation; it is not an observed refill.
struct ArmyProvinceSupplyContributorRegimentV1 {
  std::int32_t stored_index = 0;
  std::int32_t army_regiment_id = -1;
  bool available = false;
  std::string unavailable_reason;
  std::optional<std::int32_t> current_soldiers;
  std::optional<std::int32_t> maximum_soldiers;
  std::optional<bool> native_supply_loss_eligible;
  std::optional<ArmyRegimentReplenishmentRecordsSnapshotV1> replenishment_records_v1;
  friend bool operator==(const ArmyProvinceSupplyContributorRegimentV1 &,
                         const ArmyProvinceSupplyContributorRegimentV1 &) = default;
};

struct ArmyProvinceSupplyContributorOccurrenceV1 {
  std::int32_t stored_index = 0;
  std::int32_t army_id = -1;
  bool available = false;
  std::string unavailable_reason;
  std::optional<std::int32_t> owner_character_id;
  std::optional<bool> included;
  std::string inclusion_basis;
  std::optional<std::int32_t> native_carmy_id;
  std::optional<std::int32_t> native_eligible_current_soldiers;
  std::vector<ArmyProvinceSupplyContributorRegimentV1> regiments;
  friend bool operator==(const ArmyProvinceSupplyContributorOccurrenceV1 &,
                         const ArmyProvinceSupplyContributorOccurrenceV1 &) = default;
};

struct ArmyCurrentProvinceSupplyContributorsV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  bool current_usage_ready = false;
  bool contributors_ready = false;
  std::optional<std::int32_t> province_id;
  std::optional<std::int32_t> subject_army_id;
  std::optional<std::int32_t> subject_carmy_id;
  std::optional<std::int32_t> owner_character_id;
  std::optional<std::int32_t> native_province_unit_count;
  std::optional<std::int32_t> native_supply_limit_soldiers;
  std::optional<std::int32_t> native_supply_usage_soldiers;
  std::vector<ArmyProvinceSupplyContributorOccurrenceV1> occurrences;
  friend bool operator==(const ArmyCurrentProvinceSupplyContributorsV1 &,
                         const ArmyCurrentProvinceSupplyContributorsV1 &) = default;
};

struct ArmyCurrentLandResupplyV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  bool current_observation_ready = false;
  std::optional<std::int32_t> province_id;
  std::optional<std::int32_t> owner_character_id;
  std::optional<bool> native_land_branch_applicable;
  std::optional<bool> native_resupply_eligible;
  std::optional<std::int64_t> loaded_gain_raw;
  friend bool operator==(const ArmyCurrentLandResupplyV1 &,
                         const ArmyCurrentLandResupplyV1 &) = default;
};

struct ArmyCurrentLandSupplyRateInputsV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  bool current_observation_ready = false;
  std::optional<std::int32_t> province_id, subject_army_id, subject_carmy_id;
  std::optional<std::int32_t> owner_character_id;
  std::optional<std::int32_t> commander_raw_full_id, commander_resolved_full_id;
  std::optional<bool> native_land_branch_applicable, commander_used_native_fallback;
  std::optional<bool> native_province_component_applicable;
  std::optional<std::int64_t> province_component_raw, commander_modifier_1a9_raw;
  std::optional<std::int64_t> loaded_excess_slope_raw, loaded_min_loss_raw;
  std::optional<std::int64_t> loaded_max_loss_raw, loaded_divisor_floor_raw;
  friend bool operator==(const ArmyCurrentLandSupplyRateInputsV1 &,
                         const ArmyCurrentLandSupplyRateInputsV1 &) = default;
};

struct ArmyProvinceBesiegingRegimentV1 {
  std::int32_t stored_index = 0;
  std::int32_t army_regiment_id = -1;
  bool available = false;
  std::string unavailable_reason;
  std::optional<std::int32_t> current_soldiers;
  std::optional<std::int32_t> maximum_soldiers;
  std::optional<ArmyRegimentReplenishmentRecordsSnapshotV1> replenishment_records_v1;
  friend bool operator==(const ArmyProvinceBesiegingRegimentV1 &,
                         const ArmyProvinceBesiegingRegimentV1 &) = default;
};

struct ArmyProvinceBesiegingOccurrenceV1 {
  std::int32_t stored_index = 0;
  std::int32_t public_unit_id = -1;
  std::optional<std::int32_t> resolved_unit_id;
  std::optional<bool> unit_used_fallback;
  std::optional<std::int32_t> current_province_id;
  std::optional<bool> current_province_used_fallback;
  std::optional<std::int32_t> raw_unit18, raw_unit170, raw_unit44;
  std::optional<std::int32_t> native_carmy_id;
  std::optional<bool> army_used_fallback;
  std::optional<bool> eligible;
  bool available = false;
  std::string unavailable_reason;
  std::optional<std::int32_t> native_whole_current_soldiers;
  std::vector<ArmyProvinceBesiegingRegimentV1> regiments;
  friend bool operator==(const ArmyProvinceBesiegingOccurrenceV1 &,
                         const ArmyProvinceBesiegingOccurrenceV1 &) = default;
};

struct ArmyAssaultBudgetContextV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  std::optional<bool> has_active_siege;
  std::optional<std::int32_t> siege_id;
  std::optional<std::int32_t> breach_level_raw;
  std::optional<std::int32_t> casualty_percentage_count;
  std::optional<std::int64_t> casualty_percentage_raw;
  friend bool operator==(const ArmyAssaultBudgetContextV1 &,
                         const ArmyAssaultBudgetContextV1 &) = default;
};

struct ArmyCurrentProvinceBesiegingContributorsV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  std::int32_t province_id = -1;
  std::optional<std::int32_t> native_province_unit_count;
  std::optional<std::int32_t> native_besieging_strength;
  bool contributors_ready = false;
  std::optional<std::int32_t> native_assault_expected_loss;
  ArmyAssaultBudgetContextV1 assault_context;
  std::vector<ArmyProvinceBesiegingOccurrenceV1> occurrences;
  friend bool operator==(const ArmyCurrentProvinceBesiegingContributorsV1 &,
                         const ArmyCurrentProvinceBesiegingContributorsV1 &) = default;
};

#include "xar_bridge/army_daily_assault_active_table_v1.inc.hpp"
#include "xar_bridge/army_current_assault_removal_reference_v1.inc.hpp"
#include "xar_bridge/army_daily_assault_loss_inputs_v1.inc.hpp"
#include "xar_bridge/army_daily_assault_roster_admission_v1.inc.hpp"
#include "xar_bridge/army_pre_date_dated_append_v1.inc.hpp"
#include "xar_bridge/army_current_post_admission_refresh_v1.inc.hpp"
#include "xar_bridge/army_current_condition30_inputs_v1.inc.hpp"
#include "xar_bridge/army_current_flag20_inputs_v1.inc.hpp"
#include "xar_bridge/army_current_flag21_inputs_v1.inc.hpp"
#include "xar_bridge/army_current_flag31_inputs_v1.inc.hpp"
#include "xar_bridge/army_current_combat_roles_phase_inputs_v1.inc.hpp"
#include "xar_bridge/army_current_candidate_detachment_mapper_v1.inc.hpp"
#include "xar_bridge/army_current_detachment_data_v1.inc.hpp"
#include "xar_bridge/army_pre_date_pending_update_v1.inc.hpp"
#include "xar_bridge/army_pre_date_character_prefix_v1.inc.hpp"
#include "xar_bridge/army_current_selected_title_holder_owner_relation_v1.inc.hpp"

// Exact .3 direct getter returns signed int32 remaining days without a clamp/sentinel.
// Native active/expiry status is independent and not inferred here.
using DisembarkPublishedDays12003 = std::int32_t;
struct ArmyCurrentDisembarkPenaltyV1 {
  bool available = false;
  std::optional<DisembarkPublishedDays12003> remaining_days;
  std::string unavailable_reason = "disembark_getter_not_bound";
  friend bool operator==(const ArmyCurrentDisembarkPenaltyV1 &,
                         const ArmyCurrentDisembarkPenaltyV1 &) = default;
};

struct ArmyStrengthSnapshot {
  bool available = false;
  std::int32_t army_id = -1;
  bool native_carmy_id_observable = false;
  std::int32_t native_carmy_id = -1;
  // Present immediately after CUnit resolves, independently of CArmy health.
  // Unreached numeric operands stay null; reference/index/capacity/ID zero is valid.
  std::optional<ArmyNativeResolutionSnapshotV1> native_army_resolution_v1;
  ArmyStrengthScopeRole scope_role = ArmyStrengthScopeRole::player;
  std::vector<std::int32_t> war_ids;
  std::int32_t regiment_count = 0;
  std::int32_t current_soldiers = 0;
  std::int32_t maximum_soldiers = 0;
  std::int64_t ai_base_power_raw = 0;
  std::int64_t ai_base_power_scale = 100'000;
  // Absent for older producers and unavailable rows; valid zero members use [].
  std::optional<std::vector<ArmyRegimentStrengthSnapshot>> regiment_strengths;
  std::string unavailable_reason;
  // Additive .2/.3 current supply observation, signed Q100000. No value is
  // synthesized for other builds or an unresolved CUnit/CArmy backlink.
  std::optional<std::int64_t> current_supply_raw;
  // Exact .3 premerge role operand 24E0160(flags0)+24E02A0, Q100000.
  // This is a candidate destination weight, not an actual completed merge.
  // Source weight reuses validated 2A95740(flags0) current_soldiers *100000.
  std::optional<std::int64_t> merge_supply_destination_weight_raw;
  // Exact .3 native GUI numeric getters, signed Q100000. Attrition is the
  // current native fraction, not a soldier-loss count or a net future forecast.
  // The .2 adapter leaves the new optional getter bindings unassigned.
  std::optional<std::int64_t> current_supply_capacity_raw;
  std::optional<std::int64_t> current_attrition_fraction_raw;
  // Signed native monthly supply change Q100000, not troop replenishment.
  std::optional<std::int64_t> current_supply_change_monthly_raw;
  // Omitted when the exact-build persistent-regiment binding is unavailable.
  // Only the first native data record is observed, not all persistent records.
  std::optional<std::vector<ArmyRegimentReplenishmentSnapshot>>
      regiment_replenishment;
  // Complete stored persistent DATA records, independently readable per record.
  std::optional<std::vector<ArmyRegimentReplenishmentRecordsSnapshotV1>>
      regiment_replenishment_records_v1;
  // Exact .3 current containing-persistent guard, native physicalchunk0
  // permission and fresh fraction. This is separate from observed cache148.
  std::optional<FixedChunk0PreparationInputsV1> fixed_chunk0_preparation_inputs_v1;
  // Exact .3 CArmy native remaining gathering days. Zero is observable while
  // gathering; not_gathering is an observed absence, with no invented days.
  std::optional<ArmySupplyTimingSnapshot> army_update_clock_v1;
  std::optional<ArmyLossApplicationInputsV1> loss_application_inputs_v1;
  std::optional<ArmyMonthlyLossBudgetInputsV1> monthly_loss_budget_inputs_v1;
  std::optional<ArmyMonthlyCallerEffectInputsV1> monthly_caller_effect_inputs_v1;
  std::optional<ArmyDailyQueueInputsV1> monthly_daily_queue_inputs_v1;
  std::optional<ArmyFirstRemovalCleanupInputsV1> monthly_first_removal_cleanup_inputs_v1;
  std::optional<ArmyCurrentHelperDomainInputsV1> monthly_current_helper_domain_inputs_v1;
  std::optional<ArmyCurrentHelperPointStoreInputsV1> monthly_current_helper_point_store_inputs_v1;
  std::optional<ArmyCurrentProvinceSupplyContributorsV1> current_province_supply_contributors_v1;
  std::optional<ArmyCurrentProvinceBesiegingContributorsV1> current_province_besieging_contributors_v1;
  std::optional<ArmyCurrentLandResupplyV1> current_land_resupply_v1;
  std::optional<ArmyCurrentLandSupplyRateInputsV1> current_land_supply_rate_inputs_v1;
  std::optional<ArmyCurrentFleetSupplyTickInputsV1> current_fleet_supply_tick_inputs_v1;
  std::optional<ArmyScopedOrderedRefillInputsV1> scoped_ordered_refill_inputs_v1;
  std::optional<ArmyOrderedBesiegingRefillInputsV1> ordered_besieging_refill_inputs_v1;
  std::optional<ArmyOrderedBesiegingFixedChunk0PreparationInputsV1> ordered_besieging_fixed_chunk0_preparation_inputs_v1;
  std::optional<ArmyCountyEntryInputsV1> county_entry_inputs_v1;
  std::optional<BattleNativeOwnerRecallInputsV1> native_owner_recall_inputs_v1;
  std::optional<NativeMaaRecruitmentInputsV1> native_maa_recruitment_inputs_v1;
  std::optional<ck3_12003::OwnedRegimentsSnapshotV1> owned_regiments_v1;
  std::optional<std::int32_t> gathering_days_left;
  ArmyGatheringDaysStatus gathering_days_status =
      ArmyGatheringDaysStatus::unavailable;
  std::optional<ArmyMovementProgressSnapshot> current_movement_progress;
  std::optional<ArmyCurrentDailyAssaultTableV1> current_daily_assault_table_v1;
  std::optional<ArmyCurrentDailyAssaultLossInputsV1> current_daily_assault_loss_inputs_v1;
  std::optional<ArmyCurrentDailyAssaultRosterAdmissionV1> current_daily_assault_roster_admission_v1;
  std::optional<ArmyCurrentAssaultRemovalReferenceInputsV1> current_assault_removal_reference_inputs_v1;
  std::optional<ArmyCurrentPreDatePendingUpdateInputsV1> current_pre_date_pending_update_inputs_v1;
  std::optional<ArmyPreDateDatedAppendInputsV1> current_pre_date_dated_append_inputs_v1;
  std::optional<ArmyCurrentPostAdmissionRefreshInputsV1> current_post_admission_refresh_inputs_v1;
  std::optional<ArmyCurrentCondition30InputsV1> current_army_condition30_inputs_v1;
  std::optional<ArmyCurrentFlag20InputsV1> current_army_flag20_inputs_v1;
  std::optional<ArmyCurrentFlag21InputsV1> current_army_flag21_inputs_v1;
  std::optional<ArmyCurrentFlag31InputsV1> current_army_flag31_inputs_v1;
  std::optional<ArmyCurrentCandidateDetachmentMapperInputsV1> current_candidate_detachment_mapper_inputs_v1;
  std::optional<ArmyCurrentDetachmentDataInputsV1> current_detachment_data_inputs_v1;
  std::optional<ArmyFutureDailySupplyScheduleInputsV1> future_daily_supply_schedule_inputs_v1;
  std::optional<ArmyCurrentDetachmentCallbackInputsV1> current_detachment_callback_inputs_v1;
  std::optional<ArmyCurrentDetachmentStoreInputsV1> current_detachment_store_inputs_v1;
  std::optional<ArmyCurrentCharacterDetachmentInputsV1> current_character_detachment_inputs_v1;
  std::optional<ArmyCurrentPreDateCharacterPrefixInputsV1> current_pre_date_character_prefix_inputs_v1;
  std::optional<ArmyCurrentSelectedTitleHolderOwnerRelationV1>
      current_selected_title_holder_owner_relation_v1;
  // Exact .3 current landing input; omitted by old/.2 producers.
  std::optional<ArmyCurrentDisembarkPenaltyV1> current_disembark_penalty_v1;
  std::optional<ArmyCurrentDailySupplyDispatchInputsV1> current_daily_supply_dispatch_inputs_v1;
  std::optional<ArmyCurrentMonthFirstRefillCallInputsV1> current_month_first_refill_call_inputs_v1;
  std::optional<ArmyCurrentCombatRolesPhaseInputsV1> current_army_combat_roles_phase_inputs_v1;
  std::optional<ArmySourceDerivedNextDailySupplyFrameInputsV1>
      source_derived_next_daily_supply_frame_inputs_v1;
  std::optional<ArmyCurrentUnitNewDateScheduleInputsV1>
      current_unit_new_date_schedule_inputs_v1;
  std::optional<ArmyCurrentUnitNewDateCallbackEntryInputsV1>
      current_unit_new_date_callback_entry_inputs_v1;

  friend bool operator==(const ArmyStrengthSnapshot &,
                         const ArmyStrengthSnapshot &) = default;
};

// Three-state native observation used by combat-input subdomains. `absent`
// is a proven empty/null engine state; it must never be serialized as either
// an unavailable read or a made-up zero value.
enum class CombatObservationStatus {
  unavailable,
  absent,
  available,
};

struct CombatMaaTypeSnapshot {
  CombatObservationStatus status = CombatObservationStatus::unavailable;
  std::string key;
  std::string unavailable_reason;

  friend bool operator==(const CombatMaaTypeSnapshot &,
                         const CombatMaaTypeSnapshot &) = default;
};

struct CombatRegimentKindSnapshot {
  CombatObservationStatus status = CombatObservationStatus::unavailable;
  std::string value;
  bool fights_in_main_phase = false;
  std::string unavailable_reason = "regiment_kind_unavailable";

  friend bool operator==(const CombatRegimentKindSnapshot &,
                         const CombatRegimentKindSnapshot &) = default;
};

struct CombatEffectiveStatsSnapshot {
  bool available = false;
  std::int32_t source_target_province_id = -1;
  std::int32_t max_size = 0;
  std::int64_t siege_value_raw = 0;
  std::int64_t damage_raw = 0;
  std::int64_t toughness_raw = 0;
  std::int64_t pursuit_raw = 0;
  std::int64_t screen_raw = 0;
  std::int64_t scale = 100'000;
  std::string unavailable_reason =
      "encounter_effective_aggregation_unavailable";

  friend bool operator==(const CombatEffectiveStatsSnapshot &,
                         const CombatEffectiveStatsSnapshot &) = default;
};

struct CombatCounterTargetSnapshot {
  std::int32_t class_index = -1;
  std::int64_t effectiveness_raw = 0;
  std::int64_t scale = 100'000;

  friend bool operator==(const CombatCounterTargetSnapshot &,
                         const CombatCounterTargetSnapshot &) = default;
};

// Exact per-regiment operands. Combining several requested armies into one
// battle side remains a separate operation because CK3 applies side-owner
// efficiency/resistance before the class-retention helper.
struct CombatCounterSnapshot {
  CombatObservationStatus status = CombatObservationStatus::unavailable;
  std::int32_t class_index = -1;
  std::int64_t current_chunk_raw = 0;
  std::int64_t scale = 100'000;
  std::vector<CombatCounterTargetSnapshot> targets;
  std::string unavailable_reason =
      "regiment_counter_operands_unavailable";

  friend bool operator==(const CombatCounterSnapshot &,
                         const CombatCounterSnapshot &) = default;
};

struct CombatOrdinaryStatInputsSnapshotV1 {
  bool available = false;
  std::optional<std::int32_t> selected_character_full_id;
  std::string character_resolution;
  std::optional<std::int32_t> aggregate_count;
  std::optional<std::vector<std::uint16_t>> aggregate_keys_u16;
  std::optional<std::vector<std::int64_t>> aggregate_values_q64;
  // Getter/cache order: siege, damage, toughness, pursuit, screen.
  std::array<std::optional<std::int64_t>, 5> loaded_bases{};
  std::int64_t scale = 100'000;
  std::string unavailable_reason = "ordinary_stat_inputs_unavailable";
  friend bool operator==(const CombatOrdinaryStatInputsSnapshotV1 &,
                         const CombatOrdinaryStatInputsSnapshotV1 &) = default;
};

struct CombatMaaPropertyBlockV1 {
  std::int32_t count = 0;
  std::vector<std::uint16_t> keys_u16;
  std::vector<std::int64_t> values_q64;
  friend bool operator==(const CombatMaaPropertyBlockV1 &,
                         const CombatMaaPropertyBlockV1 &) = default;
};

struct CombatMaaSixStatsV1 {
  std::int32_t max_size = 0;
  // siege, damage, toughness, pursuit, screen.
  std::array<std::int64_t, 5> values{};
  friend bool operator==(const CombatMaaSixStatsV1 &,
                         const CombatMaaSixStatsV1 &) = default;
};

struct CombatMaaCultureRowV1 {
  std::int32_t definition_index = 0, row_index = 0;
  bool definition_is_gdbo = false, definition_matches_selected_type = false;
  std::int32_t class_filter = -1;
  std::optional<CombatMaaSixStatsV1> stats;
  friend bool operator==(const CombatMaaCultureRowV1 &,
                         const CombatMaaCultureRowV1 &) = default;
};

struct CombatMaaAccoladeBlockV1 {
  std::int32_t linked_index = 0, character_full_id = -1;
  std::int32_t accolade_full_id = -1, row_index = 0, level = 0;
  CombatMaaPropertyBlockV1 properties;
  friend bool operator==(const CombatMaaAccoladeBlockV1 &,
                         const CombatMaaAccoladeBlockV1 &) = default;
};

// Actual operands of26344C0->30C4360. This optional leaf has independent
// readiness and never substitutes the current final tuple for its sources.
struct CombatMaaStatInputsSnapshotV1 {
  bool available = false;
  std::int32_t source_target_province_id = -1;
  std::optional<std::int32_t> source_regiment_full_id, selected_character_full_id;
  std::string character_resolution;
  std::optional<bool> inner_type_is_gdbo, selector_mode, class_row_present;
  std::optional<std::int32_t> selected_type_class, culture_full_id, government_index;
  std::optional<CombatMaaSixStatsV1> type_bases;
  std::optional<CombatMaaPropertyBlockV1> selected_properties, extra_properties;
  std::optional<std::array<std::uint16_t, 6>> class_add_keys_u16, class_mult_keys_u16;
  std::optional<std::array<std::uint16_t, 5>> extra_add_keys_u16, extra_mult_keys_u16;
  std::optional<std::vector<CombatMaaCultureRowV1>> government_rows, global_rows;
  std::optional<std::int32_t> extra_title_full_id, extra_holder_full_id, holder_piety_rank;
  std::optional<std::int32_t> selected_government_byte_4d6;
  // Actual2B9CBC0 return, including its signed nonnegative clamp.
  std::optional<std::int64_t> selector_factor_q64;
  std::optional<std::vector<std::int32_t>> linked_character_full_ids;
  std::optional<std::vector<CombatMaaAccoladeBlockV1>> accolade_blocks;
  std::optional<bool> definition620_present;
  std::array<std::optional<CombatMaaSixStatsV1>, 6> environment_components{};
  std::array<std::optional<std::int64_t>, 5> fallback_ordinary_bases{};
  std::int64_t scale = 100'000;
  std::string unavailable_reason = "maa_stat_inputs_unavailable";
  friend bool operator==(const CombatMaaStatInputsSnapshotV1 &,
                         const CombatMaaStatInputsSnapshotV1 &) = default;
};

struct CombatRegimentSnapshot {
  bool available = false;
  std::int32_t regiment_id = -1;
  // CRegiment+0x08 vslot1 proves only that the public full ID is initialized;
  // it is not a combat-active or participation predicate.
  bool identity_valid = false;
  std::int32_t current_soldiers = 0;
  std::int32_t maximum_soldiers = 0;
  CombatMaaTypeSnapshot maa_type;
  CombatRegimentKindSnapshot kind;
  CombatEffectiveStatsSnapshot effective_stats;
  // Same-query readonly initial-stage evaluation at the Army's current Province.
  // Omitted when current==target; that case reuses effective_stats.
  std::optional<CombatEffectiveStatsSnapshot> initialization_context_stats;
  std::optional<CombatOrdinaryStatInputsSnapshotV1> ordinary_stat_inputs_v1;
  std::optional<CombatMaaStatInputsSnapshotV1> maa_stat_inputs_v1;
  CombatCounterSnapshot counter;
  std::string unavailable_reason;

  friend bool operator==(const CombatRegimentSnapshot &,
                         const CombatRegimentSnapshot &) = default;
};

struct CombatCommanderContextSnapshot {
  bool available = false;
  std::int32_t province_id = -1;
  std::int32_t effective_min_roll = 0;
  std::int32_t effective_max_roll = 0;
  bool base_advantage_observable = false;
  std::int64_t base_advantage_raw = 0;
  std::int64_t scale = 100'000;
  std::string unavailable_reason =
      "battle_commander_roll_bounds_unavailable";

  friend bool operator==(const CombatCommanderContextSnapshot &,
                         const CombatCommanderContextSnapshot &) = default;
};

struct CombatCommanderSnapshot {
  CombatObservationStatus status = CombatObservationStatus::unavailable;
  std::int32_t character_id = -1;
  bool generic_advantage_observable = false;
  std::int32_t generic_advantage_points = 0;
  CombatCommanderContextSnapshot battle_context;
  std::string unavailable_reason;
  std::optional<PhaseRiteParametersV1> phase_rite_parameters_v1;

  friend bool operator==(const CombatCommanderSnapshot &,
                         const CombatCommanderSnapshot &) = default;
};

// Exact .3 final-evaluator inputs. The selected Character can be the knight's
// employer/liege or the knight itself; these are current inputs, not a prestage
// source-construction baseline. Failure is independent of the native scalar.
struct CombatKnightEffectivenessContextSnapshot {
  bool available = false;
  std::optional<std::int32_t> character_id;
  std::array<std::int64_t, 9> modifier_raw{};
  std::array<std::int64_t, 9> operand_raw{};
  std::string unavailable_reason = "effectiveness_context_unavailable";
  std::optional<KnightCurrentModelAssociationV1> current_model_association_v1;

  friend bool operator==(const CombatKnightEffectivenessContextSnapshot &,
                         const CombatKnightEffectivenessContextSnapshot &) = default;
};

struct CombatKnightSnapshot {
  bool eligible = false;
  std::int32_t character_id = -1;
  std::int32_t source_regiment_id = -1;
  std::int32_t army_id = -1;
  bool participant_army_membership_verified = false;
  std::int32_t prowess = 0;
  std::int64_t knight_effectiveness_raw = 0;
  // B6..BE in the native 1.19.0.6 effectiveness reader. Optional diagnostic
  // operands; the direct native effectiveness value remains authoritative.
  bool effectiveness_components_observed = false;
  std::array<std::int64_t, 9> effectiveness_modifier_raw{};
  std::array<std::int64_t, 9> effectiveness_operand_raw{};
  std::int64_t effective_damage_raw = 0;
  std::int64_t effective_toughness_raw = 0;
  std::int64_t scale = 100'000;
  std::optional<CombatKnightEffectivenessContextSnapshot> effectiveness_context;
  std::optional<PhaseRiteParametersV1> phase_rite_parameters_v1;
  std::optional<PhaseWarmongerCoreV1> phase_warmonger_core_v1;
  std::optional<PhaseBerserkerValidityInputsV1> phase_berserker_validity_inputs_v1;
  std::optional<PhaseBerserkerChanceInputsV1> phase_berserker_chance_inputs_v1;

  friend bool operator==(const CombatKnightSnapshot &,
                         const CombatKnightSnapshot &) = default;
};

struct CombatKnightsSnapshot {
  bool available = false;
  // Exact .3 runtime signed DWORD coefficients; these are unscaled integers.
  // Legacy providers retain absence instead of supplying a guessed value.
  std::optional<std::int32_t> loaded_damage_multiplier;
  std::optional<std::int32_t> loaded_toughness_multiplier;
  std::vector<CombatKnightSnapshot> members;
  std::string unavailable_reason = "combat_side_knight_list_unavailable";

  friend bool operator==(const CombatKnightsSnapshot &,
                         const CombatKnightsSnapshot &) = default;
};

struct CombatOwnerSnapshot {
  CombatObservationStatus status = CombatObservationStatus::unavailable;
  std::int32_t character_id = -1;
  std::int64_t counter_efficiency_raw = 0;
  std::int64_t counter_resistance_raw = 0;
  std::int64_t scale = 100'000;
  std::string unavailable_reason = "counter_modifier_owner_unavailable";

  friend bool operator==(const CombatOwnerSnapshot &,
                         const CombatOwnerSnapshot &) = default;
};

struct CombatArmyInputsSnapshot {
  bool available = false;
  std::int32_t army_id = -1;
  bool native_carmy_id_observable = false;
  std::int32_t native_carmy_id = -1;
  std::string encounter_role;
  ArmyStrengthScopeRole scope_role = ArmyStrengthScopeRole::player;
  std::vector<std::int32_t> war_ids;
  bool current_province_observable = false;
  std::int32_t current_province_id = -1;
  CombatOwnerSnapshot owner;
  CombatCommanderSnapshot commander;
  bool regiments_observable = false;
  std::vector<CombatRegimentSnapshot> regiments;
  CombatKnightsSnapshot knights;
  std::string unavailable_reason;

  friend bool operator==(const CombatArmyInputsSnapshot &,
                         const CombatArmyInputsSnapshot &) = default;
};

struct CombatTerrainSnapshot {
  bool available = false;
  std::string key;
  std::int64_t combat_width_multiplier_raw = 0;
  std::int64_t scale = 100'000;
  std::string unavailable_reason;

  friend bool operator==(const CombatTerrainSnapshot &,
                         const CombatTerrainSnapshot &) = default;
};

struct BattleRetainedRuleEffectV1 {
  std::string stage;
  std::int32_t side_index = 0;
  std::uint32_t rules_pointer_offset = 0;
  std::string status = "unavailable";
  std::optional<std::string> key;
  std::optional<std::int32_t> advantage_points;
  std::string unavailable_reason;
  friend bool operator==(const BattleRetainedRuleEffectV1 &,
                         const BattleRetainedRuleEffectV1 &) = default;
};

// Current loaded values selected by retained slots, not historical append rows.
struct BattleRetainedRuleEffectsV1 {
  bool available = false;
  std::vector<BattleRetainedRuleEffectV1> rows;
  std::string unavailable_reason;
  friend bool operator==(const BattleRetainedRuleEffectsV1 &,
                         const BattleRetainedRuleEffectsV1 &) = default;
};

struct BattleCurrentHoldingMultiplierV1 {
  std::string status = "unavailable";
  std::optional<std::int64_t> province_multiplier_raw;
  std::optional<bool> province_has_holding;
  std::optional<std::int64_t> holding_modifier_raw;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentHoldingMultiplierV1 &,
                         const BattleCurrentHoldingMultiplierV1 &) = default;
};
struct BattleCurrentCommanderExclusionV1 {
  std::string status = "unavailable";
  std::int32_t selected_character_id_raw = -1;
  std::optional<bool> used_native_fallback;
  std::optional<bool> defender_adjacency_excluded;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentCommanderExclusionV1 &,
                         const BattleCurrentCommanderExclusionV1 &) = default;
};
struct BattleCurrentRuleContextV1 {
  BattleCurrentHoldingMultiplierV1 holding_multiplier;
  BattleCurrentCommanderExclusionV1 commander_exclusion;
  friend bool operator==(const BattleCurrentRuleContextV1 &,
                         const BattleCurrentRuleContextV1 &) = default;
};

// Retained append rows use a 16-byte native record, unlike participant hard
// casualties. Amounts are stored Q100000 contributions before the side sign.
struct BattleStoredEffectFlagsV1 {
  std::optional<std::uint8_t> flag88_raw;
  std::optional<std::uint8_t> flag89_raw;
  std::string unavailable_reason;
  friend bool operator==(const BattleStoredEffectFlagsV1 &,
                         const BattleStoredEffectFlagsV1 &) = default;
};
struct BattleStoredAdvantageRowV1 {
  std::optional<std::string> effect_key;
  std::string key_unavailable_reason;
  std::int64_t contribution_raw = 0;
  std::optional<BattleStoredEffectFlagsV1> effect_flags_v1;
  friend bool operator==(const BattleStoredAdvantageRowV1 &,
                         const BattleStoredAdvantageRowV1 &) = default;
};
struct BattleStoredAdvantageSideV1 {
  std::int32_t side_index = 0;
  bool available = false;
  std::vector<BattleStoredAdvantageRowV1> rows;
  std::string unavailable_reason;
  friend bool operator==(const BattleStoredAdvantageSideV1 &,
                         const BattleStoredAdvantageSideV1 &) = default;
};
struct BattleStoredAdvantageSourcesV1 {
  std::int64_t base_advantage_raw = 0;
  std::int64_t resolved_advantage_raw = 0;
  std::array<BattleStoredAdvantageSideV1, 2> sides;
  friend bool operator==(const BattleStoredAdvantageSourcesV1 &,
                         const BattleStoredAdvantageSourcesV1 &) = default;
};

// Current direct getter output uses the existing cached aggregate. Stored+710
// is independently observed and need not equal a current getter resolution.
struct BattleCurrentDynamicAdvantageSideV1 {
  std::int32_t side_index = 0;
  std::int32_t current_roll_points = 0;
  std::int32_t selected_character_id_raw = -1;
  std::optional<std::int64_t> side_dynamic_total_raw;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentDynamicAdvantageSideV1 &,
                         const BattleCurrentDynamicAdvantageSideV1 &) = default;
};
struct BattleCurrentDynamicAdvantageV1 {
  std::int64_t base_advantage_raw = 0;
  std::int64_t stored_resolved_advantage_raw = 0;
  std::array<BattleCurrentDynamicAdvantageSideV1, 2> sides;
  friend bool operator==(const BattleCurrentDynamicAdvantageV1 &,
                         const BattleCurrentDynamicAdvantageV1 &) = default;
};

struct BattleCurrentDynamicComponentSideV1 {
  std::int32_t side_index = 0;
  std::int32_t current_roll_points = 0;
  std::int32_t selected_character_id_raw = -1;
  std::optional<std::int32_t> resolved_character_id_raw;
  std::optional<bool> used_native_fallback;
  std::string selection_unavailable_reason;
  std::optional<std::int32_t> relation_kind_raw;
  std::string relation_unavailable_reason;
  std::optional<std::int64_t> commander_dynamic_raw;
  std::string commander_unavailable_reason;
  std::optional<std::int64_t> side_aggregate_dynamic_raw;
  std::string side_aggregate_unavailable_reason;
  friend bool operator==(const BattleCurrentDynamicComponentSideV1 &,
                         const BattleCurrentDynamicComponentSideV1 &) = default;
};
struct BattleCurrentDynamicComponentsV1 {
  std::array<BattleCurrentDynamicComponentSideV1, 2> sides;
  friend bool operator==(const BattleCurrentDynamicComponentsV1 &,
                         const BattleCurrentDynamicComponentsV1 &) = default;
};

// Current actual Combat geography; the outer battle query supplies identity and
// frame. Retained constructor fields do not reconstruct a historical entry.
struct BattleActualGeographyInputsV1 {
  CombatTerrainSnapshot terrain;
  std::optional<std::int32_t> constructor_adjacency_kind_raw;
  std::optional<bool> holding_defender;
  std::optional<BattleRetainedRuleEffectsV1> constructor_rule_effects_v1;
  std::optional<BattleCurrentRuleContextV1> current_rule_context_v1;
  std::optional<BattleStoredAdvantageSourcesV1> stored_advantage_sources_v1;
  std::optional<BattleCurrentDynamicAdvantageV1> current_dynamic_advantage_v1;
  std::optional<BattleCurrentDynamicComponentsV1> current_dynamic_components_v1;
  std::optional<BattleCurrentOwnNestedModifierV1> current_own_nested_modifier_v1;

  friend bool operator==(const BattleActualGeographyInputsV1 &,
                         const BattleActualGeographyInputsV1 &) = default;
};

struct CombatCrossingSnapshot {
  bool available = false;
  std::string kind;
  std::string unavailable_reason = "origin_target_adjacency_unavailable";

  friend bool operator==(const CombatCrossingSnapshot &,
                         const CombatCrossingSnapshot &) = default;
};

struct CombatDefenderContextSnapshot {
  bool available = false;
  std::string defender_side;
  CombatObservationStatus holding_defender_status =
      CombatObservationStatus::unavailable;
  bool holding_defender = false;
  std::string holding_unavailable_reason =
      "holding_defender_predicate_unavailable";
  std::string unavailable_reason = "encounter_side_roles_unavailable";

  friend bool operator==(const CombatDefenderContextSnapshot &,
                         const CombatDefenderContextSnapshot &) = default;
};

struct CombatPrecontactWidthSnapshot {
  bool available = false;
  std::int32_t base = 0;
  std::int32_t final = 0;
  std::string unavailable_reason = "contact_participants_unavailable";

  friend bool operator==(const CombatPrecontactWidthSnapshot &,
                         const CombatPrecontactWidthSnapshot &) = default;
};

struct CombatCandidateProvinceSnapshot {
  bool available = false;
  std::int32_t province_id = -1;
  CombatTerrainSnapshot terrain;
  CombatCrossingSnapshot crossing;
  CombatDefenderContextSnapshot defender_context;
  CombatPrecontactWidthSnapshot precontact_width;
  std::string unavailable_reason;

  friend bool operator==(const CombatCandidateProvinceSnapshot &,
                         const CombatCandidateProvinceSnapshot &) = default;
};

struct OngoingCombatInputsSnapshot {
  bool available = false;
  bool combat_id_observable = false;
  std::int32_t combat_id = -1;
  std::int32_t province_id = -1;
  std::int32_t phase = 0;
  std::int32_t phase_day = 0;
  std::int32_t base_combat_width = 0;
  std::int32_t final_combat_width = 0;
  std::int32_t side_0_roll = 0;
  std::int32_t side_1_roll = 0;
  // CCombat stores both signed advantage values as Q100000 int64 fields.
  std::int64_t base_advantage = 0;
  std::int64_t resolved_advantage = 0;
  std::string orientation =
      "native_side_0_attacker_side_1_defender";
  std::string unavailable_reason;

  friend bool operator==(const OngoingCombatInputsSnapshot &,
                         const OngoingCombatInputsSnapshot &) = default;
};

struct CombatCounterResolutionSnapshot {
  bool available = false;
  std::string countered_side;
  std::string countering_side;
  std::int32_t countered_modifier_owner_character_id = -1;
  std::int32_t countering_modifier_owner_character_id = -1;
  std::int64_t context_scale_raw = 0;
  std::int32_t class_count = 0;
  std::vector<std::int64_t> damage_retention_by_class_raw;
  std::int64_t scale = 100'000;
  std::string unavailable_reason;

  friend bool operator==(const CombatCounterResolutionSnapshot &,
                         const CombatCounterResolutionSnapshot &) = default;
};

struct CombatSimulationInputsRequest {
  std::int32_t target_province_id = -1;
  std::int32_t attacker_entry_province_id = -1;
  std::vector<std::int32_t> attacker_army_ids;
  std::vector<std::int32_t> defender_army_ids;
  // Exact .3 defending-arrival constructor operand; absent keeps explicit entry.
  std::optional<std::int32_t> constructor_adjacency_kind_raw;

  friend bool operator==(const CombatSimulationInputsRequest &,
                         const CombatSimulationInputsRequest &) = default;
};

struct CombatHypotheticalScenarioSnapshot {
  std::int32_t attacker_entry_province_id = -1;
  std::vector<std::int32_t> attacker_army_ids;
  std::vector<std::int32_t> defender_army_ids;
  std::string attacker_side;
  std::string defender_side;
  std::optional<std::int32_t> constructor_adjacency_kind_raw;

  friend bool operator==(const CombatHypotheticalScenarioSnapshot &,
                         const CombatHypotheticalScenarioSnapshot &) = default;
};

// One paused projection of an explicit hypothetical contact scenario. The
// adapter revalidates both public ArmyID partitions against one current active
// war and derives crossing only from the caller-supplied final-edge origin;
// native storage handles never cross this contract.
// Narrow observation of a synthetic nonreligious constructor context. The
// selected commander precedes the static ledger; target residual is arithmetic.
// This DTO does not represent a complete encounter or a real resolved CCombat.
// Operation-defined source rows of the query-owned synthetic side modifier.
// Modifier ordinals and raw bytes are observations, not authored trait names.
struct ContextualAdvantageOppositeEffectSnapshot {
  std::int32_t native_ledger_index = -1;
  std::string effect_key;
  std::uint8_t flag88_raw = 0;
  std::uint8_t flag89_raw = 0;
  std::int64_t contribution_raw = 0;

  friend bool operator==(const ContextualAdvantageOppositeEffectSnapshot &,
                         const ContextualAdvantageOppositeEffectSnapshot &) = default;
};

struct ContextualAdvantageSideModifierSourceSnapshot {
  std::int32_t side_index = -1;
  std::string source_slot;
  std::uint16_t source_modifier_id = 0;
  bool condition_observed = false;
  bool selected = false;
  std::optional<std::int64_t> modifier_raw;
  std::optional<std::int64_t> contribution_raw;
  std::int64_t scale100000 = 100'000;
  std::string skip_reason;
  std::optional<std::int32_t> opposite_side_index;
  std::optional<std::vector<ContextualAdvantageOppositeEffectSnapshot>>
      eligible_opposite_effects;
  std::optional<std::int64_t> opposite_eligible_contribution_sum_raw;

  friend bool operator==(const ContextualAdvantageSideModifierSourceSnapshot &,
                         const ContextualAdvantageSideModifierSourceSnapshot &) = default;
};

// Inputs of the same selected Character's synthetic commander component.
struct ContextualAdvantageCommanderSourceInputsSnapshot {
  std::int32_t selected_commander_character_id = -1;
  std::int32_t effective_martial = 0;
  std::int32_t own_primary_character_id = -1;
  std::int32_t opposing_primary_character_id = -1;
  std::optional<std::uint32_t> province_context_raw32;
  std::int32_t relation_kind_raw = 0;
  std::optional<bool> army_gated_modifier_cache_present;
  std::optional<std::int64_t> army_gated_modifier_cached_raw;
  std::optional<std::int32_t> army_gated_modifier_source_army_id;
  std::optional<std::int32_t> army_gated_modifier_resolved_army_id;
  std::optional<bool> army_gated_modifier_used_null_army;
  std::optional<bool> army_gated_modifier_gate_result;
  bool primary_identity_matches = false;
  std::uint8_t gathering_flag_raw = 0;
  std::optional<bool> gathering_modifier_flag_1a5;
  std::optional<std::int32_t> gathering_rule_effect_points;
  std::optional<std::string> gathering_rule_source_key;

  friend bool operator==(const ContextualAdvantageCommanderSourceInputsSnapshot &,
                         const ContextualAdvantageCommanderSourceInputsSnapshot &) = default;
};

struct ContextualAdvantageCommanderOpposingPrimaryModifierSnapshot {
  std::uint16_t modifier_id = 0;
  std::optional<bool> cache_present;
  std::optional<std::int64_t> modifier_raw;
  std::optional<bool> selected;
  std::optional<bool> predicate_observed;
  std::optional<std::int64_t> contribution_raw;
  std::string skip_reason;

  friend bool operator==(const ContextualAdvantageCommanderOpposingPrimaryModifierSnapshot &,
                         const ContextualAdvantageCommanderOpposingPrimaryModifierSnapshot &) = default;
};

struct ContextualAdvantageCommanderOpposingPrimaryDetailsSnapshot {
  std::optional<std::uint32_t> selected_personal_rite_reference;
  std::optional<std::uint32_t> opposing_primary_personal_rite_reference;
  std::optional<bool> opposing_primary_character_used_fallback;
  std::optional<bool> selected_rite_used_fallback;
  std::optional<bool> opposing_primary_rite_used_fallback;
  std::optional<bool> rite_pair_valid;
  std::optional<std::uint8_t> directed_rite_hostility_level;
  std::optional<std::int32_t> hostility_factor_count;
  std::optional<std::int64_t> hostility_factor_raw;
  std::optional<std::uint32_t> selected_personal_faith_reference;
  std::optional<std::uint32_t> opposing_primary_personal_faith_reference;
  std::optional<bool> selected_faith_used_fallback;
  std::optional<bool> opposing_primary_faith_used_fallback;
  std::optional<std::uint32_t> selected_religion_reference;
  std::optional<std::uint32_t> opposing_primary_religion_reference;
  std::optional<bool> religion_references_equal;
  std::vector<ContextualAdvantageCommanderOpposingPrimaryModifierSnapshot> sources;

  friend bool operator==(const ContextualAdvantageCommanderOpposingPrimaryDetailsSnapshot &,
                         const ContextualAdvantageCommanderOpposingPrimaryDetailsSnapshot &) = default;
};

struct ContextualAdvantageCommanderProvinceDetailsSnapshot {
  std::optional<bool> cache_present;
  std::optional<std::uint32_t> selected_culture_reference;
  std::optional<std::uint32_t> province_culture_reference;
  std::optional<bool> selected_culture_used_fallback;
  std::optional<bool> province_culture_used_fallback;
  std::optional<bool> category1_pillar_equal;

  friend bool operator==(const ContextualAdvantageCommanderProvinceDetailsSnapshot &,
                         const ContextualAdvantageCommanderProvinceDetailsSnapshot &) = default;
};

// Seven native caller stages; local accumulators remain absent after any
// required source contribution is unavailable.
struct ContextualAdvantageCommanderSourceSnapshot {
  std::int32_t side_index = -1;
  std::int32_t stage_order = -1;
  std::string source_kind;
  std::optional<std::uint16_t> modifier_id;
  std::string status;
  std::optional<bool> predicate_observed;
  std::optional<bool> selected;
  std::optional<std::int64_t> modifier_raw;
  std::optional<std::int64_t> contribution_raw;
  std::int64_t scale100000 = 100'000;
  std::optional<std::int64_t> accumulator_before_raw;
  std::optional<std::int64_t> accumulator_after_raw;
  std::string skip_reason;
  std::string source_provenance;
  std::optional<ContextualAdvantageCommanderOpposingPrimaryDetailsSnapshot>
      opposing_primary_details;
  std::optional<ContextualAdvantageCommanderProvinceDetailsSnapshot>
      province_details;

  friend bool operator==(const ContextualAdvantageCommanderSourceSnapshot &,
                         const ContextualAdvantageCommanderSourceSnapshot &) = default;
};

struct ContextualAdvantageSideSnapshot {
  std::int32_t side_index = -1;
  std::vector<std::int32_t> ordered_public_cunit_ids;
  std::int32_t selected_commander_character_id = -1;
  std::int32_t relation_kind_raw = 0;
  std::int64_t commander_dynamic_raw = 0;
  std::int64_t side_dynamic_raw = 0;
  std::int64_t target_conditionals_residual_raw = 0;
  std::int64_t side_total_raw = 0;
  // Absent only when this additive source reader is unavailable. Existing
  // context totals and readiness are independent of this optional leaf.
  std::optional<std::vector<ContextualAdvantageSideModifierSourceSnapshot>>
      side_modifier_sources;
  std::optional<ContextualAdvantageCommanderSourceInputsSnapshot>
      commander_source_inputs;
  std::optional<std::vector<ContextualAdvantageCommanderSourceSnapshot>>
      commander_sources;

  friend bool operator==(const ContextualAdvantageSideSnapshot &,
                         const ContextualAdvantageSideSnapshot &) = default;
};

// An already-read constructor source row, not an actual battle result.
struct ContextualAdvantageConstructorSourceSnapshot {
  std::int32_t stage_order = -1;
  std::int32_t append_order = -1;
  std::string stage;
  std::string side;
  bool selected = false;
  bool applied = false;
  std::string source_key;
  std::int32_t effect_advantage_points = 0;
  std::int64_t scale_raw = 100'000;
  std::int64_t signed_contribution_raw = 0;
  std::int64_t accumulator_before_raw = 0;
  std::int64_t accumulator_after_raw = 0;
  std::string skip_reason;

  friend bool operator==(const ContextualAdvantageConstructorSourceSnapshot &,
                         const ContextualAdvantageConstructorSourceSnapshot &) = default;
};

// Exact constructor-faith source operands, not an actual battle result.
struct ContextualAdvantageReligionSourceSnapshot {
  std::int32_t side_index = -1;
  std::int32_t primary_public_cunit_id = -1;
  std::int32_t owner_character_id = -1;
  std::uint32_t target_rite_id = 0xFFFFFFFFU;
  std::uint32_t target_faith_id = 0xFFFFFFFFU;
  std::uint32_t target_main_rite_id = 0xFFFFFFFFU;
  std::uint32_t owner_rite_id = 0xFFFFFFFFU;
  std::uint32_t owner_faith_id = 0xFFFFFFFFU;
  bool owner_rite_observed = false;
  bool target_faith_unreformed = false;
  std::optional<bool> owner_faith_matches_target;
  bool selected = false;
  bool applied = false;
  std::string source_key;
  std::int32_t effect_advantage_points = 0;
  std::int64_t scale_raw = 100'000;
  std::int64_t signed_contribution_raw = 0;
  std::int64_t accumulator_before_raw = 0;
  std::int64_t accumulator_after_raw = 0;
  std::int32_t append_order = -1;
  std::string skip_reason;

  friend bool operator==(const ContextualAdvantageReligionSourceSnapshot &,
                         const ContextualAdvantageReligionSourceSnapshot &) = default;
};

struct ContextualAdvantageSnapshot {
  bool attempted = false;
  bool available = false;
  std::int32_t target_province_id = -1;
  std::vector<ContextualAdvantageSideSnapshot> sides;
  std::int64_t base_nonreligious_accumulator_raw = 0;
  std::vector<ContextualAdvantageConstructorSourceSnapshot> nonreligious_constructor_sources;
  bool religion_constructor_attempted = false;
  bool religion_constructor_sources_ready = false;
  std::int64_t base_constructor_accumulator_raw = 0;
  std::vector<ContextualAdvantageReligionSourceSnapshot> religion_constructor_sources;
  std::int64_t synthetic_zero_roll_total_raw = 0;
  bool synthetic_helper_total_match = false;
  std::string unavailable_reason;

  friend bool operator==(const ContextualAdvantageSnapshot &,
                         const ContextualAdvantageSnapshot &) = default;
};

struct CombatSimulationInputsSnapshot {
  std::int32_t target_province_id = -1;
  CombatHypotheticalScenarioSnapshot scenario;
  std::vector<CombatArmyInputsSnapshot> armies;
  CombatCandidateProvinceSnapshot target_province;
  std::vector<OngoingCombatInputsSnapshot> ongoing_combats;
  std::vector<CombatCounterResolutionSnapshot> counter_resolutions;
  ContextualAdvantageSnapshot contextual_advantage;
  bool input_observation_ready = false;
  bool monte_carlo_ready = false;
  std::vector<std::string> missing_required_domains;
  std::optional<PhaseEventCalendarObservationV1>
      phase_event_calendar_observation_v1;
  std::optional<PhaseEventRoleCompatibilityV1>
      phase_event_role_compatibility_v1;
  std::optional<PhaseEventCommanderSideIdentityV1>
      phase_event_commander_side_identity_v1;

  friend bool operator==(const CombatSimulationInputsSnapshot &,
                         const CombatSimulationInputsSnapshot &) = default;
};

// Exact, version-neutral representation of a CK3 CFixedPoint. Keeping the raw
// numerator and the statically proven scale avoids losing precision at the
// native -> JSON boundary.
struct FixedPointValue {
  std::int64_t raw = 0;
  std::int64_t scale = 100'000;

  friend bool operator==(const FixedPointValue &,
                         const FixedPointValue &) = default;
};

// Additive state for one exact war-objective Province. Each observable flag
// distinguishes an unavailable/transitioning native subgraph from a real
// zero, empty garrison, unoccupied Province, or Province with no active siege.
// besieging_army_id uses the public CUnit-backed ArmySnapshot ID only after a
// unique exact CArmyID join; zero/ambiguous joins remain -1 and native storage
// handles never cross this contract.
struct WarObjectiveProvinceState {
  std::int32_t province_id = -1;
  bool occupation_observable = false;
  bool is_occupied = false;
  std::int32_t occupying_character_id = -1;
  bool fort_level_observable = false;
  std::int32_t fort_level = 0;
  bool garrison_size_observable = false;
  std::int32_t garrison_size = 0;
  bool besieging_strength_observable = false;
  std::int32_t besieging_strength = 0;
  bool siege_observable = false;
  bool has_active_siege = false;
  std::int32_t siege_id = -1;
  std::int32_t besieging_army_id = -1;
  bool player_army_besieging = false;
  FixedPointValue siege_progress_fraction;
  FixedPointValue siege_current_work;
  FixedPointValue siege_total_work;
  bool siege_days_left_observable = false;
  std::int32_t siege_days_left = 0;
  // Independent nullable current-tick inputs, from one paused alive Siege.
  // Current phase is freshly evaluated; prepared phase is last prepare's cache.
  bool siege_ordinary_daily_progress_observable = false;
  FixedPointValue siege_ordinary_daily_progress;
  // Current eligible Province contribution and highest eligible engine tier.
  bool siege_eligible_regiment_siege_work_observable = false;
  FixedPointValue siege_eligible_regiment_siege_work;
  bool siege_highest_eligible_siege_tier_observable = false;
  std::int32_t siege_highest_eligible_siege_tier = 0;
  bool siege_province_unit_occurrences_observable = false;
  std::vector<SiegeProvinceUnitOccurrenceV1> siege_province_unit_occurrences;
  bool siege_current_phase_length_observable = false;
  FixedPointValue siege_current_phase_length;
  bool siege_prepared_phase_length_observable = false;
  FixedPointValue siege_prepared_phase_length;
  bool siege_phase_counter_observable = false;
  std::int32_t siege_phase_counter = 0;
  bool siege_can_advance_observable = false;
  bool siege_can_advance = false;
  // Current phase-event state: nullable independently of the assault group.
  bool siege_phase_event_breach_level_observable = false;
  std::int32_t siege_phase_event_breach_level = 0;
  bool siege_phase_event_starvation_level_observable = false;
  std::int32_t siege_phase_event_starvation_level = 0;
  bool siege_phase_event_disease_level_observable = false;
  std::int32_t siege_phase_event_disease_level = 0;
  bool siege_phase_event_desertion_count_observable = false;
  std::int32_t siege_phase_event_desertion_count = 0;
  bool siege_phase_event_stalemate_count_observable = false;
  std::int32_t siege_phase_event_stalemate_count = 0;
  // Last prepare's enum cache; sentinel 5 means no due selection.
  bool siege_prepared_selected_phase_event_enum_observable = false;
  std::int32_t siege_prepared_selected_phase_event_enum = 0;
  // Exact-build Assault Fort state. This subdomain is published atomically
  // only from a paused rich-siege read. A false observable flag means every
  // following value is unavailable rather than a real zero/false.
  bool assault_observable = false;
  std::int32_t breach_level = 0;
  bool assault_in_progress = false;
  bool can_start_assault = false;
  bool can_stop_assault = false;
  FixedPointValue assault_daily_progress;
  std::int32_t assault_daily_casualties = 0;

  friend bool operator==(const WarObjectiveProvinceState &,
                         const WarObjectiveProvinceState &) = default;
};

enum class PlayerWarSide {
  attacker,
  defender,
};

struct ActiveWarSnapshot {
  std::int32_t war_id = -1;
  PlayerWarSide player_side = PlayerWarSide::attacker;
  std::int32_t primary_opponent_character_id = -1;
  bool player_is_primary_war_leader = false;
  std::vector<std::int32_t> targeted_title_ids;
  std::vector<std::int32_t> war_objective_province_ids;
  std::vector<WarObjectiveProvinceState> objective_province_states;
  std::int32_t enemy_primary_default_raise_province_id = -1;
  std::int32_t player_relative_war_score = 0;
  std::vector<ArmySnapshot> allied_armies;
  std::vector<ArmySnapshot> enemy_armies;

  friend bool operator==(const ActiveWarSnapshot &,
                         const ActiveWarSnapshot &) = default;
};

// Final recipient decision read from the exact interaction context.  The
// unavailable state is explicit because a context may be absent or may fail
// the native validator; neither case may be reconstructed from ai_acceptance.
struct WarTerminationRecipientResponseSnapshot {
  bool observable = false;
  std::int32_t decision_status_raw = 3;
  bool would_accept_now = false;

  friend bool operator==(const WarTerminationRecipientResponseSnapshot &,
                         const WarTerminationRecipientResponseSnapshot &) =
      default;
};

// One native WarOverview result context built for the currently played
// primary war leader. `native_validator_observable=false` means validation was
// not run because no context could be constructed; it must not be serialized
// as a real validator rejection.
struct WarTerminationOptionSnapshot {
  std::string outcome;
  bool context_constructed = false;
  bool native_validator_observable = false;
  bool native_validator_passed = false;
  bool ai_acceptance_observable = false;
  FixedPointValue ai_acceptance;
  bool auto_accept_observable = false;
  bool auto_accept = false;
  WarTerminationRecipientResponseSnapshot recipient_response;

  friend bool operator==(const WarTerminationOptionSnapshot &,
                         const WarTerminationOptionSnapshot &) = default;
};

// Attacker-relative values returned by the same helpers used by the native
// WarOverview score tooltips. These fields are published atomically; a false
// observable flag means none of the numeric members may be interpreted as a
// real zero.
struct WarScoreBreakdownSnapshot {
  bool observable = false;
  std::int32_t imprisonment = 0;
  std::int32_t battles = 0;
  std::int32_t occupation = 0;
  std::int32_t ticking = 0;

  friend bool operator==(const WarScoreBreakdownSnapshot &,
                         const WarScoreBreakdownSnapshot &) = default;
};

// Atomic, paused projection for one full-generation WarID. Acceptance is read
// from each temporary native context when its exact-build evaluator is
// available. CB-specific terms remain deliberately unavailable: callers must
// not infer titles, gold, prestige, piety, legitimacy, truce or prisoner
// effects from a sendable context or an absolute outcome label.
struct WarTerminationOptionsSnapshot {
  std::int32_t war_id = -1;
  PlayerWarSide player_side = PlayerWarSide::attacker;
  bool player_is_primary_war_leader = false;
  std::int32_t player_relative_war_score = 0;
  bool war_duration_days_observable = false;
  std::int32_t war_duration_days = 0;
  bool absolute_war_scores_observable = false;
  std::int32_t attacker_war_score = 0;
  std::int32_t defender_war_score = 0;
  WarScoreBreakdownSnapshot war_score_breakdown;
  bool active_casus_belli_observable = false;
  bool active_casus_belli_present = false;
  bool active_casus_belli_identity_observable = false;
  std::int32_t active_casus_belli_database_index = -1;
  std::string active_casus_belli_key;
  bool white_peace_permission_observable = false;
  bool cb_allows_white_peace = false;
  WarTerminationOptionSnapshot surrender;
  WarTerminationOptionSnapshot white_peace;
  WarTerminationOptionSnapshot victory;

  friend bool operator==(const WarTerminationOptionsSnapshot &,
                         const WarTerminationOptionsSnapshot &) = default;
};

// Exact-build, paused observation of a player-originated white-peace proposal
// that is still present in CK3's global pending-interaction storage.  `present`
// is a typed result, not an inference from the responder-facing notification
// queue.  A false value is published only after two identical storage scans in
// the same unchanged native snapshot.
struct OutboundWarWhitePeaceStatusSnapshot {
  std::int32_t war_id = -1;
  std::int32_t actor_character_id = -1;
  std::int32_t recipient_character_id = -1;
  bool present = false;
  std::int32_t pending_interaction_id = -1;

  friend bool operator==(const OutboundWarWhitePeaceStatusSnapshot &,
                         const OutboundWarWhitePeaceStatusSnapshot &) =
      default;
};

// Narrow, source-pinned terms projection. The claim_cb branch remains the
// complete claim-disposition slice. The raiktor_claim_cb branch publishes its
// attacker-defeat disposition and authored formulas plus whichever isolated
// dynamic domains were proven in the same paused frame. Missing domains stay
// explicitly unobservable and never make the surrender decision ready. The
// rows preserve the CWar target-title order.
struct WarClaimSnapshot {
  std::int32_t title_id = -1;
  bool present = false;
  bool strong = false;
  bool implicit = false;
  std::string state;

  friend bool operator==(const WarClaimSnapshot &,
                         const WarClaimSnapshot &) = default;
};

struct WarClaimDispositionSnapshot {
  std::string declared_title_disposition;
  std::string claim_disposition;

  friend bool operator==(const WarClaimDispositionSnapshot &,
                         const WarClaimDispositionSnapshot &) = default;
};

struct WarRaiktorCharacterFixedPointSnapshot {
  std::int32_t character_id = -1;
  FixedPointValue value;

  friend bool operator==(const WarRaiktorCharacterFixedPointSnapshot &,
                         const WarRaiktorCharacterFixedPointSnapshot &) =
      default;
};

struct WarRaiktorGoldTransferSnapshot {
  std::int32_t from_character_id = -1;
  std::int32_t to_character_id = -1;
  FixedPointValue value;

  friend bool operator==(const WarRaiktorGoldTransferSnapshot &,
                         const WarRaiktorGoldTransferSnapshot &) = default;
};

struct WarRaiktorPrisonerReleaseSnapshot {
  std::int32_t jailer_character_id = -1;
  std::int32_t prisoner_character_id = -1;
  std::string reason;

  friend bool operator==(const WarRaiktorPrisonerReleaseSnapshot &,
                         const WarRaiktorPrisonerReleaseSnapshot &) = default;
};

struct WarRaiktorWarBoundCompositionSnapshot {
  std::int32_t composition_ordinal = -1;
  std::int32_t current_army_regiment_id = -1;
  std::int32_t raised_carmy_id = -1;
  std::int32_t current_soldiers = -1;

  friend bool operator==(const WarRaiktorWarBoundCompositionSnapshot &,
                         const WarRaiktorWarBoundCompositionSnapshot &) =
      default;
};

struct WarRaiktorWarBoundRegimentSnapshot {
  std::int32_t persistent_regiment_id = -1;
  std::int32_t bound_war_id = -1;
  bool war_keep_on_attacker_victory = false;
  std::int64_t current_soldiers = 0;
  std::vector<WarRaiktorWarBoundCompositionSnapshot> composition_rows;

  friend bool operator==(const WarRaiktorWarBoundRegimentSnapshot &,
                         const WarRaiktorWarBoundRegimentSnapshot &) =
      default;
};

// Read-only generic war-bound current-regiment projection.  The bridge stamps
// its transport revision when serializing the query result; source-specific
// origin, pre soldiers, loss, and postwar cleanup remain unavailable.
struct WarRaiktorWarBoundCurrentSnapshot {
  std::int32_t date_raw = 0;
  std::int32_t war_id = -1;
  std::int32_t active_casus_belli_database_index = -1;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::int32_t owner_character_id = -1;
  std::int64_t observed_current_soldiers = -1;
  std::vector<WarRaiktorWarBoundRegimentSnapshot> regiments;

  friend bool operator==(const WarRaiktorWarBoundCurrentSnapshot &,
                         const WarRaiktorWarBoundCurrentSnapshot &) =
      default;
};

struct WarRaiktorSurrenderTermsSnapshot {
  WarClaimDispositionSnapshot claim_disposition;
  std::int32_t gold_reparations_factor = 0;
  std::string gold_reparations_direction;
  std::string gold_reparations_positive_income_basis;
  std::string gold_reparations_fallback_condition;
  std::string gold_reparations_fallback_basis;
  std::string gold_reparations_defender_culture_multiplier;
  std::int32_t attacker_fame_scale = 0;
  std::string attacker_fame_base;
  std::string attacker_fame_resource;
  std::string attacker_fame_limit_rule;
  std::string truce_direction;
  std::string truce_result;
  // The Raiktor truce pointer observer publishes only the evaluated duration
  // from the authored CAddTruce node.  Persisted expiry remains deliberately
  // unavailable and is represented by the wire's explicit false/null pair.
  bool truce_evaluated_days_observable = false;
  std::int32_t truce_evaluated_days = -1;
  std::string prisoner_release_rule;
  std::string conditional_favor_hook_rule;
  bool gold_observable = false;
  WarRaiktorCharacterFixedPointSnapshot attacker_current_gold;
  WarRaiktorCharacterFixedPointSnapshot defender_current_gold;
  WarRaiktorCharacterFixedPointSnapshot
      attacker_authoritative_monthly_gold_income;
  WarRaiktorCharacterFixedPointSnapshot
      defender_authoritative_monthly_gold_income;
  WarRaiktorGoldTransferSnapshot actual_gold_transfer;
  bool prestige_observable = false;
  WarRaiktorCharacterFixedPointSnapshot attacker_current_prestige;
  FixedPointValue cb_prestige_factor;
  WarRaiktorCharacterFixedPointSnapshot attacker_prestige_delta;
  bool prisoner_release_observable = false;
  std::vector<std::int32_t> attacker_participant_ids;
  std::vector<std::int32_t> defender_participant_ids;
  std::vector<std::int32_t> attacker_release_candidate_ids;
  std::vector<std::int32_t> defender_release_candidate_ids;
  std::vector<WarRaiktorPrisonerReleaseSnapshot> prisoner_release_pairs;
  bool full_participant_scan = false;
  bool primary_and_first_three_successors_scanned = false;
  bool favor_hook_observable = false;
  bool claimant_distinct_from_attacker = false;
  bool original_visible_root_traversed = false;
  bool conditional_favor_hook_applies = false;
  bool generic_war_bound_current_observable = false;
  WarRaiktorWarBoundCurrentSnapshot generic_war_bound_current;
  bool observed_dynamic_terms_same_frame_stable = false;
  FixedPointValue attacker_legitimacy_delta;
  FixedPointValue attacker_influence_delta;
  bool hostages_allowed = false;
  std::vector<std::string> unobserved_dynamic_effects;

  friend bool operator==(const WarRaiktorSurrenderTermsSnapshot &,
                         const WarRaiktorSurrenderTermsSnapshot &) = default;
};

struct WarTerminationTermsSnapshot {
  std::int32_t war_id = -1;
  std::int32_t active_casus_belli_database_index = -1;
  std::string active_casus_belli_key;
  std::int32_t claimant_character_id = -1;
  std::vector<std::int32_t> target_title_ids;
  std::vector<WarClaimSnapshot> claims;
  WarClaimDispositionSnapshot attacker_victory;
  WarClaimDispositionSnapshot white_peace;
  WarClaimDispositionSnapshot attacker_defeat;
  std::optional<WarRaiktorSurrenderTermsSnapshot> raiktor_surrender;

  friend bool operator==(const WarTerminationTermsSnapshot &,
                         const WarTerminationTermsSnapshot &) = default;
};

// Complete, available-only claim_cb exit-decision slice. Unlike the narrow
// v1 claim-disposition reader, this snapshot is published only after both
// white-peace and attacker-defeat loaded effects have been dry-previewed in
// the same paused frame, all primary balances/incomes are observed, and the
// original recipient-answer path has returned a non-unavailable status.
struct WarExitResourceSnapshot {
  std::int32_t character_id = -1;
  std::string resource_kind;
  FixedPointValue value;

  friend bool operator==(const WarExitResourceSnapshot &,
                         const WarExitResourceSnapshot &) = default;
};

struct WarExitCharacterFixedPointSnapshot {
  std::int32_t character_id = -1;
  FixedPointValue value;

  friend bool operator==(const WarExitCharacterFixedPointSnapshot &,
                         const WarExitCharacterFixedPointSnapshot &) =
      default;
};

struct WarExitGoldTransferSnapshot {
  std::int32_t from_character_id = -1;
  std::int32_t to_character_id = -1;
  FixedPointValue value;

  friend bool operator==(const WarExitGoldTransferSnapshot &,
                         const WarExitGoldTransferSnapshot &) = default;
};

struct WarExitTruceSnapshot {
  std::int32_t owner_character_id = -1;
  std::int32_t toward_character_id = -1;
  std::int32_t evaluated_days = 0;
  std::int32_t current_date_raw = 0;
  std::int32_t expiry_date_raw = 0;

  friend bool operator==(const WarExitTruceSnapshot &,
                         const WarExitTruceSnapshot &) = default;
};

struct WarExitPrisonerReleaseSnapshot {
  std::int32_t jailer_character_id = -1;
  std::int32_t prisoner_character_id = -1;
  std::string reason;

  friend bool operator==(const WarExitPrisonerReleaseSnapshot &,
                         const WarExitPrisonerReleaseSnapshot &) = default;
};

struct WarExitRecipientResponseSnapshot {
  bool native_validator_passed = false;
  FixedPointValue acceptance;
  std::int32_t decision_status_raw = 3;
  bool would_accept_now = false;
  bool auto_accept = false;

  friend bool operator==(const WarExitRecipientResponseSnapshot &,
                         const WarExitRecipientResponseSnapshot &) = default;
};

struct WarExitOutcomeSnapshot {
  WarClaimDispositionSnapshot claim_disposition;
  WarExitRecipientResponseSnapshot recipient_response;
  FixedPointValue cb_prestige_factor;
  std::vector<WarExitGoldTransferSnapshot> primary_gold_transfers;
  std::vector<WarExitResourceSnapshot> primary_resource_deltas;
  WarExitTruceSnapshot truce;
  std::vector<WarExitPrisonerReleaseSnapshot> prisoner_releases;
  bool complete = false;

  friend bool operator==(const WarExitOutcomeSnapshot &,
                         const WarExitOutcomeSnapshot &) = default;
};

struct WarTerminationExitTermsSnapshot {
  std::int32_t war_id = -1;
  std::int32_t date_raw = 0;
  std::int32_t active_casus_belli_database_index = -1;
  std::string active_casus_belli_key;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::int32_t claimant_character_id = -1;
  std::vector<std::int32_t> target_title_ids;
  std::vector<WarClaimSnapshot> claims;
  std::vector<WarExitResourceSnapshot> primary_resource_balances;
  std::vector<WarExitCharacterFixedPointSnapshot>
      primary_monthly_gold_income;
  WarExitOutcomeSnapshot white_peace;
  WarExitOutcomeSnapshot attacker_defeat;
  bool same_frame_stable = false;
  bool claim_temporary_lifecycle_verified = false;
  bool exit_terms_ready = false;

  friend bool operator==(const WarTerminationExitTermsSnapshot &,
                         const WarTerminationExitTermsSnapshot &) = default;
};

// Native read-only baseline for a primary defender in an individual county
// de-jure war.  The typed unavailable fields are deliberate: this reader does
// not execute or preview setup_de_jure_cb / resolve_title_and_vassal_change.
// No caller may turn an observed balance or target ID into a surrender delta.
struct DefenderDeJureTargetHolderPrestateV1 {
  std::int32_t title_id = -1;
  std::int32_t holder_character_id = -1;
  std::optional<std::int32_t> holder_immediate_liege_character_id;

  friend bool operator==(const DefenderDeJureTargetHolderPrestateV1 &,
                         const DefenderDeJureTargetHolderPrestateV1 &) = default;
};

struct DefenderDeJureExitTermsV1 {
  std::int32_t war_id = -1;
  std::int32_t date_raw = 0;
  std::int32_t casus_belli_database_index = -1;
  std::string casus_belli_key;
  std::int32_t primary_attacker_character_id = -1;
  std::int32_t primary_defender_character_id = -1;
  std::vector<std::int32_t> target_title_ids;
  std::vector<DefenderDeJureTargetHolderPrestateV1> target_title_holder_prestate;
  std::vector<WarExitResourceSnapshot> primary_resource_balances;
  std::vector<WarExitCharacterFixedPointSnapshot> primary_monthly_gold_income;
  // Partial inputs to the stock truce formula only. These are not a truce
  // duration, expiry, or material exit terms.
  struct TruceInput {
    std::optional<bool> value;
    std::string unavailable_reason = "read_only_input_not_observed";
    friend bool operator==(const TruceInput &, const TruceInput &) = default;
  };
  TruceInput attacker_flexible_truces_perk;
  TruceInput attacker_government_is_nomadic;
  TruceInput defender_government_is_nomadic;
  // Full WarManager storage scan is only a structural candidate for the
  // stock any_character_war border-raid predicate. It is never a formal
  // truce input until that evaluator equivalence is independently proven.
  struct BorderRaidStorageCandidate {
    std::optional<bool> value;
    std::int32_t storage_capacity = 0;
    std::int32_t active_war_count = 0;
    std::int32_t matching_war_count = 0;
    std::string unavailable_reason = "full_war_storage_scan_unavailable_or_drift";
    friend bool operator==(const BorderRaidStorageCandidate &,
                           const BorderRaidStorageCandidate &) = default;
  };
  BorderRaidStorageCandidate border_raid_storage_candidate;
  std::string title_vassal_delta_unavailable_reason =
      "runtime_target_scope_and_de_jure_change_semantics_unproven";
  std::string signed_resource_delta_unavailable_reason =
      "conditional_effects_and_cb_prestige_factor_unread";
  std::string directed_truce_unavailable_reason =
      "attacker_victory_truce_duration_unread";
  bool same_frame_stable = false;
  bool material_complete = false;

  friend bool operator==(const DefenderDeJureExitTermsV1 &,
                         const DefenderDeJureExitTermsV1 &) = default;
};

// One fully published Rogue one-life settlement. Adapters expose this object
// only after the Mod's ready gate is exactly 1 and every required global can
// be decoded without coercion. Integer fields are semantic values after exact
// CFixedPoint division; the two scores retain their lossless raw numerator.
struct OneLifeSettlementSnapshot {
  bool ready = true;
  std::int64_t commit_serial = 0;
  std::int32_t source_character_id = -1;
  FixedPointValue final_score;
  FixedPointValue score_before_reject;
  std::int64_t record_candidate = 0;
  std::int64_t old_record = 0;
  std::int64_t record_delta = 0;
  std::int64_t blessing_count = 0;
  std::int64_t refusal_count = 0;
  std::int64_t contract_progress = 0;
  bool record_written = false;

  friend bool operator==(const OneLifeSettlementSnapshot &,
                         const OneLifeSettlementSnapshot &) = default;
};

struct Snapshot {
  std::int32_t date_raw = 0;
  std::int32_t speed = 0;
  bool paused = false;
  std::int32_t player_id = -1;
  bool map_ready = false;
  bool has_played_character = false;
  std::int32_t played_character_id = -1;
  bool played_character_alive = false;
  std::int32_t played_character_stress_points = -1;
  std::optional<ck3_12004::person_events::PlayerEventTraitMembershipV1>
      played_character_event_trait_membership;
  FixedPointValue played_character_gold;
  FixedPointValue played_character_prestige;
  FixedPointValue played_character_piety;
  std::int32_t played_character_betrothed_id = -1;
  std::int32_t played_character_primary_spouse_id = -1;
  std::vector<std::int32_t> played_character_spouse_ids;
  bool has_active_event = false;
  std::int32_t active_event_instance_id = -1;
  std::int32_t active_event_option_count = 0;
  bool has_pending_character_interaction = false;
  std::int32_t pending_character_interaction_id = -1;
  std::int32_t pending_sender_character_id = -1;
  bool pending_auto_accept_notification = false;
  std::vector<ActiveWarSnapshot> active_wars;
  std::vector<ArmySnapshot> player_armies;
  bool has_one_life_settlement = false;
  OneLifeSettlementSnapshot one_life_settlement;

  friend bool operator==(const Snapshot &, const Snapshot &) = default;
};

enum class PauseSubmitResult { submitted, already_paused, unavailable };
enum class ResumeSubmitResult { submitted, already_running, unavailable };
enum class SetPlayedCharacterResult {
  switched,
  already_played,
  target_not_found,
  target_dead,
  target_controlled,
  requires_paused,
  map_not_ready,
  postcondition_failed,
  unavailable,
};
enum class SelectEventOptionResult {
  submitted,
  no_active_event,
  option_out_of_range,
  unavailable,
};
enum class SaveCheckpointStatus { submitted, map_not_ready, unavailable };

struct SaveCheckpointResult {
  SaveCheckpointStatus status = SaveCheckpointStatus::unavailable;
  std::int32_t date_raw = 0;
};

enum class PendingInteractionReply { accept = 0, reject = 1 };
enum class ReplyPendingInteractionResult {
  submitted,
  no_pending_interaction,
  acknowledgement_required,
  unavailable,
};
enum class AcknowledgePendingInteractionResult {
  submitted,
  no_pending_interaction,
  pending_interaction_mismatch,
  acknowledgement_not_required,
  requires_paused,
  not_for_played_character,
  state_changed,
  queue_rejected,
  unavailable,
};
enum class RaiseTroopsResult {
  submitted,
  no_played_character,
  no_default_province,
  validation_failed,
  unavailable,
};
enum class MoveArmyResult {
  submitted,
  army_not_found,
  army_not_controllable,
  province_not_found,
  move_mode_unavailable,
  character_state_rejected,
  army_state_rejected,
  validation_failed,
  unavailable,
};
enum class HaltArmyResult {
  halt_submitted,
  requires_paused,
  no_played_character,
  army_not_found,
  army_not_controllable,
  validator_rejected,
  submission_failed,
  unavailable,
};
enum class PreviewMoveArmyStatus {
  available,
  requires_paused,
  army_not_found,
  army_not_controllable,
  province_not_found,
  move_mode_unavailable,
  character_state_rejected,
  army_state_rejected,
  validation_failed,
  origin_unavailable,
  route_unavailable,
  unavailable,
};

enum class ArmyProvinceSupplyStatus {
  available,
  partial,
  unavailable,
};

enum class ArmyProvinceSupplyRole { current, target };

struct ArmyProvinceSupplyRow {
  bool available = false;
  ArmyProvinceSupplyRole role = ArmyProvinceSupplyRole::current;
  std::int32_t province_id = -1;
  std::optional<std::int32_t> native_supply_limit_soldiers;
  std::optional<std::int32_t> native_supply_usage_soldiers;
  std::optional<ArmyCapturedTargetLandSupplyInputsV1> captured_target_land_supply_inputs_v1;
  std::string unavailable_reason;

  friend bool operator==(const ArmyProvinceSupplyRow &,
                         const ArmyProvinceSupplyRow &) = default;
};

// Both Provinces are evaluated now with the same actual army owner and current
// commander. Target usage excludes any invented future arrival contribution.
struct ArmyProvinceSupplySnapshot {
  ArmyProvinceSupplyStatus status = ArmyProvinceSupplyStatus::unavailable;
  std::string unavailable_reason;
  std::int32_t army_id = -1;
  std::optional<std::int32_t> native_carmy_id;
  std::optional<std::int32_t> owner_character_id;
  std::optional<std::int32_t> commander_character_id;
  ArmyProvinceSupplyRow current;
  ArmyProvinceSupplyRow target;

  friend bool operator==(const ArmyProvinceSupplySnapshot &,
                         const ArmyProvinceSupplySnapshot &) = default;
};

struct PreviewMoveArmyResult {
  PreviewMoveArmyStatus status = PreviewMoveArmyStatus::unavailable;
  std::int32_t army_id = -1;
  std::int32_t origin_province_id = -1;
  std::int32_t target_province_id = -1;
  std::vector<std::int32_t> route_province_ids;
  // Exact .3 additive observation. Its failure does not alter movement legality.
  std::optional<ArmyProvinceSupplySnapshot> province_supply;

  friend bool operator==(const PreviewMoveArmyResult &,
                         const PreviewMoveArmyResult &) = default;
};

// One atomic, paused projection of the remaining native movement timeline for
// a public full-generation CUnit.  Arrival dates are CK3 raw dates (hours) and
// are parallel to route_province_ids.  A published row is therefore never a
// partial path/timing mixture.
struct RouteTimelineSnapshot {
  bool timeline_observable = false;
  std::int32_t army_id = -1;
  std::int32_t current_province_id = -1;
  std::int32_t effective_origin_province_id = -1;
  std::vector<std::int32_t> route_province_ids;
  std::vector<std::int32_t> arrival_date_raws;

  friend bool operator==(const RouteTimelineSnapshot &,
                         const RouteTimelineSnapshot &) = default;
};

struct RouteContactConflictSnapshot {
  std::string kind;
  std::int32_t hostile_army_id = -1;
  std::int32_t province_id = -1;
  std::int32_t subject_from_province_id = -1;
  std::int32_t subject_to_province_id = -1;
  std::int32_t hostile_from_province_id = -1;
  std::int32_t hostile_to_province_id = -1;
  std::int32_t overlap_start_date_raw = 0;
  std::int32_t overlap_end_date_raw = 0;

  friend bool operator==(const RouteContactConflictSnapshot &,
                         const RouteContactConflictSnapshot &) = default;
};

struct RouteContactHorizonRequest {
  std::int32_t subject_army_id = -1;
  std::int32_t target_province_id = -1;
  std::vector<std::int32_t> hostile_army_ids;

  friend bool operator==(const RouteContactHorizonRequest &,
                         const RouteContactHorizonRequest &) = default;
};

enum class RouteContactHorizonStatus {
  available,
  requires_paused,
  subject_army_not_found,
  subject_army_not_controllable,
  target_province_not_found,
  hostile_scope_mismatch,
  route_unavailable,
  timeline_unavailable,
  state_changed,
  unavailable,
};

// Failure-only provenance for the internal route-contact reader.  These
// fields are deliberately not serialized by the successful horizon wire
// frame; they exist so one paused exact-build replay identifies which native
// timeline failed and at which read-only projection gate.
enum class RouteContactTimelineFailureRole {
  none,
  subject,
  hostile,
};

enum class RouteContactTimelinePathKind {
  none,
  stationary_active,
  committed_active,
  constructed,
  hostile_active,
};

enum class RouteContactTimelineFailureStage {
  none,
  invalid_input,
  active_identity,
  path_header,
  route_speed_read,
  route_origin,
  route_entry,
  route_adjacency,
  land_speed,
  naval_speed,
  current_edge_speed,
  zero_progress_boundary,
  edge_duration_read,
  route_duration_read,
  route_duration_value,
  route_duration_order,
  arrival_date,
  route_mismatch,
  timeline_shape,
};

struct RouteContactTimelineFailureDiagnostic {
  RouteContactTimelineFailureRole role =
      RouteContactTimelineFailureRole::none;
  std::int32_t army_id = -1;
  RouteContactTimelinePathKind path_kind =
      RouteContactTimelinePathKind::none;
  RouteContactTimelineFailureStage stage =
      RouteContactTimelineFailureStage::none;

  friend bool operator==(const RouteContactTimelineFailureDiagnostic &,
                         const RouteContactTimelineFailureDiagnostic &) =
      default;
};

struct RouteContactHorizonSnapshot {
  RouteContactHorizonStatus status = RouteContactHorizonStatus::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t subject_army_id = -1;
  std::int32_t target_province_id = -1;
  std::vector<std::int32_t> hostile_army_ids;
  RouteTimelineSnapshot subject_route;
  std::vector<RouteTimelineSnapshot> hostile_routes;
  std::int32_t horizon_start_date_raw = 0;
  std::int32_t horizon_end_date_raw = 0;
  bool one_day_contact_free = false;
  std::vector<RouteContactConflictSnapshot> conflicts;
  RouteContactTimelineFailureDiagnostic timeline_failure;

  friend bool operator==(const RouteContactHorizonSnapshot &,
                         const RouteContactHorizonSnapshot &) = default;
};

// Exact read-only mirror of either the contact transition CK3 would resolve
// for one public CUnit already committed to its current Province, or the
// active CCombat produced by that transition. Participant-side army IDs are
// public CUnitIDs; native CArmyIDs appear only in explicitly named evidence
// fields used to audit exact-build resolution.
struct ActualContactScopeRequest {
  std::int32_t subject_army_id = -1;
  std::int32_t target_province_id = -1;

  friend bool operator==(const ActualContactScopeRequest &,
                         const ActualContactScopeRequest &) = default;
};

enum class ActualContactScopeStatus {
  available,
  requires_paused,
  subject_army_not_found,
  subject_army_not_controllable,
  target_province_not_found,
  subject_not_at_target,
  entry_rejected,
  relation_unavailable,
  state_changed,
  unavailable,
};

struct ActualContactScopeSnapshot {
  ActualContactScopeStatus status = ActualContactScopeStatus::unavailable;
  std::string scope_kind = "pre_contact_prediction";
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::int32_t subject_army_id = -1;
  std::int32_t subject_native_carmy_id = -1;
  std::int32_t subject_owner_character_id = -1;
  std::int32_t target_province_id = -1;
  std::vector<std::int32_t> province_unit_army_ids;
  std::vector<std::int32_t> province_combat_ids;
  std::string transition_kind = "none";
  std::int32_t selected_combat_id = -1;
  std::int32_t selected_combat_array_index = -1;
  std::string join_side = "none";
  std::int32_t defender_seed_character_id = -1;
  bool initiator_is_defender = false;
  std::int32_t adjacency_kind_raw = 0;
  std::vector<std::int32_t> loser_excluded_native_carmy_ids;
  std::vector<std::int32_t> opponent_army_ids;
  std::vector<std::int32_t> attacker_army_ids;
  std::vector<std::int32_t> defender_army_ids;
  bool actual_contact_scope_ready = false;
  bool combat_v3_participant_scope_ready = false;

  friend bool operator==(const ActualContactScopeSnapshot &,
                         const ActualContactScopeSnapshot &) = default;
};

// Exact, read-only projection of one live CCombat reached through a
// controllable public CUnit.  All arrays preserve CK3's native stored order;
// no native pointer crosses this version-neutral boundary.
struct BattleControlRequest {
  std::int32_t subject_public_cunit_id = -1;

  friend bool operator==(const BattleControlRequest &,
                         const BattleControlRequest &) = default;
};

enum class BattleControlSnapshotStatus {
  available,
  requires_paused,
  subject_cunit_not_found,
  subject_not_controllable,
  subject_not_in_combat,
  subject_retreating,
  state_changed,
  unavailable,
};

struct BattleControlArmyIdentitySnapshot {
  std::int32_t native_carmy_id = -1;
  std::int32_t public_cunit_id = -1;
  std::int32_t owner_character_id = -1;
  std::int32_t combat_backlink_id = -1;

  friend bool operator==(const BattleControlArmyIdentitySnapshot &,
                         const BattleControlArmyIdentitySnapshot &) = default;
};

struct BattleControlRegimentEntrySnapshot {
  std::string bucket;
  std::int32_t bucket_index = -1;
  std::int32_t regiment_id = -1;
  std::int32_t native_carmy_id = -1;
  std::int32_t public_cunit_id = -1;
  std::int32_t owner_character_id = -1;
  // Exact CRegiment+0x148 on retained MAA slots; -1 means no knight.
  // Levy entries do not expose this field on the wire.
  std::int32_t knight_character_id_raw = -1;
  // This is a stored link read, not the original accolade validity/source gate.
  std::string accolade_link_status = "not_sampled";
  std::optional<std::int32_t> accolade_id_raw;
  std::int64_t starting_raw = 0;
  std::int64_t current_fighting_raw = 0;
  std::int64_t soft_casualties_raw = 0;
  bool fights_in_main_phase = false;
  bool hard_casualties_available = false;
  std::int64_t hard_casualties_raw = 0;
  std::int32_t effective_max_size = 0;
  std::int64_t effective_siege_raw = 0;
  std::int64_t effective_damage_raw = 0;
  std::int64_t effective_toughness_raw = 0;
  std::int64_t effective_pursuit_raw = 0;
  std::int64_t effective_screen_raw = 0;
  std::int32_t entry_strength_raw = 0;

  friend bool operator==(const BattleControlRegimentEntrySnapshot &,
                         const BattleControlRegimentEntrySnapshot &) = default;
};

struct BattleControlParticipantHardSnapshot {
  std::int32_t row_index = -1;
  std::int32_t participant_character_id = -1;
  std::int64_t hard_casualties_raw = 0;
  std::optional<std::int32_t> resource_share_weight_signed32;

  friend bool operator==(const BattleControlParticipantHardSnapshot &,
                         const BattleControlParticipantHardSnapshot &) = default;
};

struct BattleControlNextRollBoundsSnapshot {
  bool available = false;
  std::int32_t effective_min_roll = 0;
  std::int32_t effective_max_roll = 0;
  std::string unavailable_reason = "not_sampled";

  friend bool operator==(const BattleControlNextRollBoundsSnapshot &,
                         const BattleControlNextRollBoundsSnapshot &) = default;
};

struct BattleControlSideSnapshot {
  std::int32_t side_index = -1;
  std::string role;
  std::int32_t primary_participant_character_id = -1;
  std::int32_t selected_commander_character_id = -1;
  BattleControlNextRollBoundsSnapshot selected_commander_next_roll_bounds;
  std::int32_t current_roll_points = 0;
  std::vector<BattleControlArmyIdentitySnapshot> ordered_armies;
  std::vector<BattleControlRegimentEntrySnapshot> levy_entries;
  std::vector<BattleControlRegimentEntrySnapshot> men_at_arms_entries;
  std::int64_t stored_current_fighting_raw = 0;
  std::int64_t stored_levy_current_fighting_raw = 0;
  // CCombat side +0xA8, consumed by native terminal loss helper 0x23CDD90.
  std::int64_t stored_terminal_loss_baseline_raw = 0;
  bool stored_current_matches_derived = false;
  bool stored_levy_current_matches_derived = false;
  std::int64_t derived_current_fighting_raw = 0;
  std::int64_t derived_soft_casualties_raw = 0;
  std::int64_t derived_main_fighting_entry_hard_casualties_raw = 0;
  std::int64_t non_main_start_minus_current_minus_soft_raw = 0;
  std::vector<BattleControlParticipantHardSnapshot> participant_hard_ledger;
  std::int64_t participant_hard_total_raw = 0;
  std::int32_t side_strength_raw = 0;
  std::int32_t side_strength_scale = 100'000;

  friend bool operator==(const BattleControlSideSnapshot &,
                         const BattleControlSideSnapshot &) = default;
};

// A same-sample observation of the operands used by the native MAA counter
// resolver. This is not a resumed battle forecast or a next-tick promise.
struct BattleControlCounterEntryV1 {
  std::int32_t bucket_index = -1;
  std::int32_t regiment_id = -1;
  std::int32_t native_carmy_id = -1;
  std::int64_t current_fighting_raw = 0;
  CombatObservationStatus status = CombatObservationStatus::unavailable;
  std::int32_t class_index = -1;
  std::int32_t stack_size_soldiers = 0;
  std::int64_t current_chunk_raw = 0;
  std::vector<CombatCounterTargetSnapshot> targets;

  friend bool operator==(const BattleControlCounterEntryV1 &,
                         const BattleControlCounterEntryV1 &) = default;
};

struct BattleControlCounterSideV1 {
  std::int32_t side_index = -1;
  std::int32_t primary_owner_character_id = -1;
  std::int64_t counter_efficiency_raw = 0;
  std::int64_t counter_resistance_raw = 0;
  std::vector<BattleControlCounterEntryV1> men_at_arms_entries;

  friend bool operator==(const BattleControlCounterSideV1 &,
                         const BattleControlCounterSideV1 &) = default;
};

struct BattleControlCounterContextV1 {
  std::int32_t countered_side_index = -1;
  std::int32_t countering_side_index = -1;
  std::int32_t countered_primary_owner_character_id = -1;
  std::int32_t countering_primary_owner_character_id = -1;
  std::int64_t context_scale_raw = 0;

  friend bool operator==(const BattleControlCounterContextV1 &,
                         const BattleControlCounterContextV1 &) = default;
};

struct BattleControlCounterInputsV1 {
  bool attempted = false;
  bool available = false;
  std::string unavailable_reason = "counter_inputs_not_observed";
  std::int32_t source_combat_id = -1;
  std::int32_t source_target_province_id = -1;
  std::int32_t class_count = 0;
  std::vector<BattleControlCounterSideV1> sides;
  std::vector<BattleControlCounterContextV1> contexts;

  friend bool operator==(const BattleControlCounterInputsV1 &,
                         const BattleControlCounterInputsV1 &) = default;
};

struct ActiveCombatRetreatSideFlagsSnapshot {
  bool disallow_retreat = false;
  bool allow_early_retreat = false;
  bool skip_pursuit = false;

  friend bool operator==(const ActiveCombatRetreatSideFlagsSnapshot &,
                         const ActiveCombatRetreatSideFlagsSnapshot &) =
      default;
};

struct ActiveCombatRetreatLegalitySnapshot {
  std::string status = "unavailable";
  bool native_boolean = false;
  std::int32_t phase_raw = -1;
  std::string phase;
  std::int32_t retreat_elapsed_baseline_date_raw = 0;
  std::int64_t elapsed_whole_days = 0;
  std::int32_t minimum_elapsed_whole_days_exclusive = 0;
  bool landless_gate_allows_retreat = false;
  bool legal_now = false;
  std::vector<std::string> reason_codes_in_native_order;
  std::vector<std::string> native_reason_keys_in_native_order;
  std::optional<std::int64_t> earliest_day_gate_date_raw;

  friend bool operator==(const ActiveCombatRetreatLegalitySnapshot &,
                         const ActiveCombatRetreatLegalitySnapshot &) =
      default;
};

struct BattleControlActualHardSideRow {
  std::int32_t side_index = -1;
  std::string encounter_role;
  std::vector<std::int32_t> ordered_army_ids;
  std::int32_t commander_character_id = -1;
  std::int64_t own_modifier_raw = 0;
  std::int64_t enemy_modifier_raw = 0;

  friend bool operator==(const BattleControlActualHardSideRow &,
                         const BattleControlActualHardSideRow &) = default;
};

struct BattleControlActualHardSides {
  bool attempted = false;
  bool available = false;
  std::int32_t source_combat_id = -1;
  std::int32_t source_target_province_id = -1;
  std::vector<BattleControlActualHardSideRow> sides;
  std::string unavailable_reason;

  friend bool operator==(const BattleControlActualHardSides &,
                         const BattleControlActualHardSides &) = default;
};

struct BattleControlPursuitModifierSideRow {
  std::int32_t side_index = -1;
  std::string encounter_role;
  std::int64_t pursuit_efficiency_raw = 0;
  std::int64_t retreat_losses_raw = 0;

  friend bool operator==(const BattleControlPursuitModifierSideRow &,
                         const BattleControlPursuitModifierSideRow &) = default;
};

struct BattleControlPursuitModifierSides {
  bool attempted = false;
  bool available = false;
  std::int32_t source_combat_id = -1;
  std::int32_t source_target_province_id = -1;
  std::vector<BattleControlPursuitModifierSideRow> sides;
  std::string unavailable_reason;

  friend bool operator==(const BattleControlPursuitModifierSides &,
                         const BattleControlPursuitModifierSides &) = default;
};

// Complete current CArmyRegiment backing census in native side/army order.
// Whole soldiers are distinct from the sampled CCombat fighting-entry buckets.
struct BattleControlFullBackingRegimentV1 {
  std::int32_t regiment_id = -1;
  std::int32_t current_soldiers = 0;

  friend bool operator==(const BattleControlFullBackingRegimentV1 &,
                         const BattleControlFullBackingRegimentV1 &) = default;
};

struct BattleControlFullBackingArmyV1 {
  std::int32_t native_carmy_id = -1;
  std::int32_t public_cunit_id = -1;
  std::int32_t owner_character_id = -1;
  std::vector<BattleControlFullBackingRegimentV1> ordered_regiments;

  friend bool operator==(const BattleControlFullBackingArmyV1 &,
                         const BattleControlFullBackingArmyV1 &) = default;
};

struct BattleControlFullBackingSideV1 {
  std::int32_t side_index = -1;
  std::vector<BattleControlFullBackingArmyV1> ordered_armies;

  friend bool operator==(const BattleControlFullBackingSideV1 &,
                         const BattleControlFullBackingSideV1 &) = default;
};

struct BattleControlFullBackingInputsV1 {
  std::int32_t scale = 1;
  std::int32_t source_combat_id = -1;
  std::int32_t source_target_province_id = -1;
  bool enumeration_complete = true;
  std::array<BattleControlFullBackingSideV1, 2> sides{};

  friend bool operator==(const BattleControlFullBackingInputsV1 &,
                         const BattleControlFullBackingInputsV1 &) = default;
};

// Current operands of the native loss branches. These are not a retained
// outgoing damage result and do not execute a combat-loss operation.
struct BattleControlCurrentLossSideInputsV1 {
  std::int32_t side_index = -1;
  std::int32_t primary_participant_character_id = -1;
  // Signed Q100000 from the actual primary participant's native getter.
  std::optional<std::int64_t> levy_damage_raw;
  std::int64_t outgoing_advantage_factor_raw = 0;
  std::int64_t own_hard_conversion_modifier_raw = 0;
  std::int64_t opposing_hard_conversion_modifier_raw = 0;

  friend bool operator==(const BattleControlCurrentLossSideInputsV1 &,
                         const BattleControlCurrentLossSideInputsV1 &) = default;
};

struct BattleControlCurrentLossInputsV1 {
  std::int32_t scale = 100'000;
  std::int32_t source_combat_id = -1;
  std::int32_t source_target_province_id = -1;
  std::int64_t stored_advantage_damage_factor_raw = 0;
  std::int64_t runtime_damage_scaling_raw = 0;
  // Signed Q100000; unavailable binding differs from legitimate zero.
  std::optional<std::int64_t> runtime_advantage_scaling_raw;
  std::int64_t runtime_main_hard_conversion_raw = 0;
  std::int64_t runtime_pursuit_hard_conversion_raw = 0;
  bool province_has_holding = false;
  std::int64_t province_winter_hard_conversion_modifier_raw = 0;
  std::array<BattleControlCurrentLossSideInputsV1, 2> sides{};

  friend bool operator==(const BattleControlCurrentLossInputsV1 &,
                         const BattleControlCurrentLossInputsV1 &) = default;
};

struct BattleControlCurrentPursuitInputsV1 {
  std::int32_t scale = 100'000;
  std::int32_t source_combat_id = -1;
  std::int32_t pursuit_phase_days = 0;
  std::int64_t base_toughness_multiplier_raw = 0;
  std::int64_t minimum_pursuit_multiplier_raw = 0;
  std::int64_t pursuit_stat_multiplier_raw = 0;
  // Active pursuit and a recorded winner are required for initialized pools.
  std::optional<std::int32_t> losing_side_index;
  std::optional<std::int64_t> initial_loser_levy_soft_raw;
  std::optional<std::int64_t> initial_loser_maa_soft_raw;
  std::optional<bool> losing_side_skip_pursuit;

  friend bool operator==(const BattleControlCurrentPursuitInputsV1 &,
                         const BattleControlCurrentPursuitInputsV1 &) = default;
};

// Current main-phase transition observations; no future dispatch is forecast.
struct BattleControlCurrentPhaseTransitionSideInputsV1 {
  std::int32_t side_index = -1;
  std::int64_t stored_current_fighting_raw = 0;
  bool disallowed = false;
  bool allow_early = false;
  bool skip_pursuit = false;
  std::optional<std::int32_t> first_native_carmy_id;
  std::optional<bool> native_can_retreat;
  std::optional<bool> owner_land_rule_allows;

  friend bool operator==(
      const BattleControlCurrentPhaseTransitionSideInputsV1 &,
      const BattleControlCurrentPhaseTransitionSideInputsV1 &) = default;
};

struct BattleControlCurrentPhaseTransitionInputsV1 {
  std::int32_t forced_winner_raw = -1;
  std::int32_t result_start_date_raw = 0;
  std::int32_t minimum_elapsed_days = 0;
  std::array<BattleControlCurrentPhaseTransitionSideInputsV1, 2> sides{};

  friend bool operator==(const BattleControlCurrentPhaseTransitionInputsV1 &,
                         const BattleControlCurrentPhaseTransitionInputsV1 &) = default;
};

struct BattleControlSnapshot {
  BattleControlSnapshotStatus status =
      BattleControlSnapshotStatus::unavailable;
  // Internal/read-only diagnostic retained when an exact paused query cannot
  // publish a frame.  Available wire frames keep this empty; the mailbox may
  // append it to a typed failure without exposing native pointers.
  std::string diagnostic_reason;
  std::uint64_t snapshot_revision = 0;
  std::int64_t observed_date_raw = 0;
  std::int32_t subject_public_cunit_id = -1;
  std::int32_t subject_native_carmy_id = -1;
  std::int32_t combat_id = -1;
  std::int32_t province_id = -1;
  std::int32_t selected_public_cunit_id = -1;
  std::int32_t selected_native_carmy_id = -1;
  std::int32_t selected_owner_character_id = -1;
  std::int32_t combat_province_id = -1;
  std::int32_t side_index = -1;
  std::string side_scope;
  std::vector<std::int32_t> affected_public_cunit_ids_in_stored_order;
  std::vector<std::int32_t>
      unaffected_same_side_public_cunit_ids_in_stored_order;
  ActiveCombatRetreatSideFlagsSnapshot side_flags;
  ActiveCombatRetreatLegalitySnapshot legality;
  std::string phase;
  std::int32_t phase_raw = -1;
  std::int32_t phase_day = -1;
  std::string winner_side;
  std::int32_t winner_raw = -1;
  std::string forced_winner_side;
  std::int32_t forced_winner_raw = -1;
  bool finalized = false;
  std::int32_t battle_result_id = -1;
  std::int32_t base_combat_width = 0;
  std::int32_t final_combat_width = 0;
  std::int32_t roll_cadence_counter = 0;
  // Null is unobserved; the loaded native interval may be zero.
  std::optional<std::int32_t> roll_cadence_interval;
  std::int64_t base_advantage_raw = 0;
  std::int64_t resolved_advantage_raw = 0;
  BattleControlSideSnapshot attacker;
  BattleControlSideSnapshot defender;
  // Private exact-build observation; a complete current operand census does
  // not remove the active-resume planner's other missing domains.
  BattleControlCounterInputsV1 active_counter_inputs_v1;
  // Private exact-build diagnostic. It does not change battle_control_ready.
  BattleControlActualHardSides actual_hard_casualty_sides;
  // Private exact-build diagnostic; these are full CCombatSide modifiers.
  BattleControlPursuitModifierSides pursuit_modifier_sides;
  // Null is an unobserved leaf; zero remains a native numeric observation.
  std::optional<BattleControlCurrentLossInputsV1> current_loss_inputs_v1;
  // Null means the full native backing census was not resolved; zero is valid.
  // This additive observation does not change battle_control_ready.
  std::optional<BattleControlFullBackingInputsV1> full_backing_inputs_v1;
  // Same-Combat current manager operands; null is unobserved, raw zero is valid.
  std::optional<BattleControlCurrentFinalizerManagerInputsV1>
      current_finalizer_manager_inputs_v1;
  // Runtime pursuit rules are independent nullable observations, not a gate.
  std::optional<BattleControlCurrentPursuitInputsV1> current_pursuit_inputs_v1;
  // Optional current-frame first-Army permission inputs, independent of ready.
  std::optional<BattleControlCurrentPhaseTransitionInputsV1>
      current_phase_transition_inputs_v1;
  // Copied from the existing transition sample; independent of control ready.
  std::optional<BattleActualGeographyInputsV1> actual_geography_v1;
  bool battle_control_ready = false;
  // Current loaded native cap pair; independent of row admission and ready.
  std::optional<BattleControlCurrentWarscoreCapsV1>
      current_warscore_caps_v1;

  friend bool operator==(const BattleControlSnapshot &,
                         const BattleControlSnapshot &) = default;
};

// Private exact-build read of one knight in one retained battle regiment.
// Stored CCombat entry values are deliberately separate from a fresh native
// province evaluation.  This is an observation, not a damage forecast.
struct CurrentBattleKnightRequestV1 {
  std::int32_t subject_public_cunit_id = -1;
  std::int32_t expected_played_character_id = -1;
  std::int32_t expected_war_id = -1;
  std::int32_t expected_native_carmy_id = -1;
  std::int32_t expected_combat_id = -1;
  std::int32_t expected_province_id = -1;
  std::int64_t expected_date_raw = -1;
  std::int32_t character_id = -1;
  std::int32_t regiment_id = -1;

  friend bool operator==(const CurrentBattleKnightRequestV1 &,
                         const CurrentBattleKnightRequestV1 &) = default;
};

struct CurrentBattleKnightSnapshotV1 {
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::int64_t observed_date_raw = -1;
  std::int32_t combat_id = -1;
  std::int32_t province_id = -1;
  std::int32_t subject_public_cunit_id = -1;
  std::int32_t native_carmy_id = -1;
  std::int32_t character_id = -1;
  std::int32_t regiment_id = -1;
  std::int32_t effective_prowess = 0;
  std::int64_t knight_effectiveness_raw = 0;
  std::int64_t fresh_damage_raw = 0;
  std::int64_t fresh_toughness_raw = 0;
  std::int64_t stored_entry_damage_raw = 0;
  std::int64_t stored_entry_toughness_raw = 0;
  std::int64_t scale = 100'000;

  friend bool operator==(const CurrentBattleKnightSnapshotV1 &,
                         const CurrentBattleKnightSnapshotV1 &) = default;
};

// Read-only lifecycle projection addressed by a full-generation CombatID.
// Unlike BattleControlSnapshot this query has no CUnit eligibility dependency,
// so it remains usable after a player movement command marks the selected unit
// as retreating. Arrays preserve the CCombatSide native stored order.
struct BattleTransitionRequest {
  std::int32_t combat_id = -1;

  friend bool operator==(const BattleTransitionRequest &,
                         const BattleTransitionRequest &) = default;
};

enum class BattleTransitionSnapshotStatus {
  available,
  combat_not_found,
  state_changed,
  unavailable,
};

// Present-time casualty operands read by full CombatID. These are independent
// accounting views: main-entry hard losses and owner-ledger hard losses must
// never be added together. Non-main residuals are retained separately.
struct BattleCurrentParticipantHardSnapshotV1 {
  std::int32_t participant_character_id = -1;
  std::int64_t hard_casualties_raw = 0;

  friend bool operator==(const BattleCurrentParticipantHardSnapshotV1 &,
                         const BattleCurrentParticipantHardSnapshotV1 &) = default;
};

struct BattleCurrentSideObservationSnapshotV1 {
  std::int64_t derived_current_fighting_raw = 0;
  std::int64_t derived_soft_casualties_raw = 0;
  std::int64_t derived_main_fighting_entry_hard_casualties_raw = 0;
  std::int64_t non_main_start_minus_current_minus_soft_raw = 0;
  std::int64_t participant_hard_total_raw = 0;
  std::vector<BattleCurrentParticipantHardSnapshotV1> participant_hard_ledger;

  friend bool operator==(const BattleCurrentSideObservationSnapshotV1 &,
                         const BattleCurrentSideObservationSnapshotV1 &) = default;
};

struct BattleCurrentObservationSnapshotV1 {
  bool available = false;
  std::string unavailable_reason;
  std::int64_t scale = 100'000;
  std::int32_t base_combat_width = 0;
  std::int32_t final_combat_width = 0;
  std::int64_t base_advantage_raw = 0;
  std::int64_t resolved_advantage_raw = 0;
  BattleCurrentSideObservationSnapshotV1 attacker;
  BattleCurrentSideObservationSnapshotV1 defender;

  friend bool operator==(const BattleCurrentObservationSnapshotV1 &,
                         const BattleCurrentObservationSnapshotV1 &) = default;
};

struct BattleTransitionSnapshot {
  BattleTransitionSnapshotStatus status =
      BattleTransitionSnapshotStatus::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int64_t observed_date_raw = 0;
  std::int32_t combat_id = -1;
  std::int32_t province_id = -1;
  std::string phase;
  std::int32_t phase_raw = -1;
  std::int32_t phase_day = -1;
  std::string winner_side;
  std::int32_t winner_raw = -1;
  std::string forced_winner_side;
  std::int32_t forced_winner_raw = -1;
  bool finalized = false;
  std::int32_t battle_result_id = -1;
  std::vector<std::int32_t> attacker_public_cunit_ids_in_stored_order;
  std::vector<std::int32_t> defender_public_cunit_ids_in_stored_order;
  bool battle_transition_ready = false;
  // Null on older adapters or absent lifecycle; an unavailable leaf
  // preserves the successfully observed original lifecycle.
  std::optional<BattleCurrentObservationSnapshotV1> current_observation;
  // Current owner recall operands; no scheduler or command-event claim.
  std::optional<BattleNativeOwnerRecallInputsV1> native_owner_recall_inputs_v1;
  // Independent actual geography; terrain failure preserves lifecycle ready.
  std::optional<BattleActualGeographyInputsV1> actual_geography_v1;

  friend bool operator==(const BattleTransitionSnapshot &,
                         const BattleTransitionSnapshot &) = default;
};

// Historical terminal identity and the paused post-terminal world are kept
// separate.  A terminal kind is authoritative only when the passive exact-
// build journal observed FinalizeCombat's second argument; current ResultID
// retention is deliberately not used to infer that historical branch.
struct BattleTerminalTransitionRequestV1 {
  std::int32_t prior_combat_id = -1;
  std::int32_t subject_public_cunit_id = -1;
  std::optional<std::uint64_t> after_terminal_sequence;
  std::vector<std::int32_t> character_ids;

  friend bool operator==(const BattleTerminalTransitionRequestV1 &,
                         const BattleTerminalTransitionRequestV1 &) =
      default;
};

enum class BattleTerminalTransitionStatusV1 {
  available,
  unavailable,
};

enum class BattleTerminalJournalEventStatusV1 {
  not_observed,
  observed,
};

enum class BattleTerminalKindV1 {
  active_not_terminal,
  normal_result,
  no_normal_result,
  unavailable_after_removal,
};

enum class BattleTerminalWarscoreStatusV1 {
  recorded,
  not_recorded_by_native,
  unavailable,
};

enum class BattleTerminalSuccessorStateV1 {
  no_successor,
  residual_new_combat,
  subject_missing,
  subject_retreating,
  subject_assignment_reopened,
  unavailable,
};

enum class BattleTerminalAiMembershipStatusV1 {
  none,
  observed,
  unavailable,
};

struct BattleTerminalJournalSnapshotV1 {
  std::optional<std::uint64_t> requested_after_sequence;
  std::uint64_t oldest_available_sequence = 0;
  std::uint64_t latest_sequence = 0;
  std::optional<std::uint64_t> event_sequence;
  BattleTerminalJournalEventStatusV1 event_status =
      BattleTerminalJournalEventStatusV1::not_observed;

  friend bool operator==(const BattleTerminalJournalSnapshotV1 &,
                         const BattleTerminalJournalSnapshotV1 &) = default;
};

struct BattleTerminalDenominatorParticipantSnapshotV1 {
  std::int32_t character_id = -1;
  std::array<std::int32_t, 8> buckets_native_add_order_int32{};

  friend bool operator==(const BattleTerminalDenominatorParticipantSnapshotV1 &,
                         const BattleTerminalDenominatorParticipantSnapshotV1 &) = default;
};

struct BattleTerminalDenominatorSnapshotV1 {
  std::vector<BattleTerminalDenominatorParticipantSnapshotV1> participants;
  std::int32_t sum_int32 = 0;
  std::int32_t after_minimum_int32 = 1;

  friend bool operator==(const BattleTerminalDenominatorSnapshotV1 &,
                         const BattleTerminalDenominatorSnapshotV1 &) = default;
};

struct BattleTerminalWarscoreSnapshotV1 {
  BattleTerminalWarscoreStatusV1 status =
      BattleTerminalWarscoreStatusV1::unavailable;
  std::optional<std::int32_t> war_id;
  std::optional<std::int32_t> war_battle_row_index;
  std::optional<std::int64_t> value_raw_q100000;
  std::optional<bool> winner_is_war_attacker;
  std::optional<bool> combat_side0_is_war_attacker;
  std::optional<std::int64_t> attacker_relative_delta_raw_q100000;
  std::optional<std::int64_t> selected_cb_battle_scale_raw_q100000;
  std::optional<BattleTerminalDenominatorSnapshotV1> denominator_inputs;

  friend bool operator==(const BattleTerminalWarscoreSnapshotV1 &,
                         const BattleTerminalWarscoreSnapshotV1 &) = default;
};

struct BattleTerminalHardLossInputsSnapshotV1 {
  std::int32_t losing_side_index = -1;
  std::int64_t baseline_raw = 0;
  std::int64_t stored_current_raw = 0;
  std::int64_t levy_soft_raw = 0;
  std::int64_t men_at_arms_soft_raw = 0;
  std::int64_t hard_loss_raw = 0;

  friend bool operator==(const BattleTerminalHardLossInputsSnapshotV1 &,
                         const BattleTerminalHardLossInputsSnapshotV1 &) =
      default;
};

// Native finalizer-entry inputs, in Q100000 troop-count units.
// The cached fighting current is not a finalized survivor total.
struct BattleTerminalSideLossInputsSnapshotV1 {
  std::int32_t side_index = -1;
  std::int64_t baseline_raw_q100000 = 0;
  std::int64_t stored_current_fighting_raw_q100000 = 0;
  std::int64_t levy_soft_raw_q100000 = 0;
  std::int64_t men_at_arms_soft_raw_q100000 = 0;
  std::int64_t hard_loss_raw_q100000 = 0;

  friend bool operator==(const BattleTerminalSideLossInputsSnapshotV1 &,
                         const BattleTerminalSideLossInputsSnapshotV1 &) =
      default;
};

struct BattleTerminalSideFinalResultSnapshotV1 {
  std::int32_t side_index = -1;
  std::int32_t selected_commander_character_id = -1;
  std::int64_t baseline_raw_q100000 = 0;
  std::int64_t survivors_raw_q100000 = 0;
  friend bool operator==(const BattleTerminalSideFinalResultSnapshotV1 &,
                         const BattleTerminalSideFinalResultSnapshotV1 &) = default;
};

struct BattleTerminalCharacterResultRowSnapshotV1 {
  std::int32_t native_row_index = -1;
  std::int32_t left_character_id = -1;
  std::int32_t right_character_id = -1;
  std::optional<std::string> key;
  std::int32_t type_raw = 0;
  bool side0 = false;
  bool target_right = false;
  friend bool operator==(const BattleTerminalCharacterResultRowSnapshotV1 &,
                         const BattleTerminalCharacterResultRowSnapshotV1 &) = default;
};

// Current named-character observations are independent of historical battle rows.
struct BattleCurrentPersonEffectiveProwessSnapshotV1 {
  bool available = false;
  std::optional<std::int32_t> points;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentPersonEffectiveProwessSnapshotV1 &,
                         const BattleCurrentPersonEffectiveProwessSnapshotV1 &) = default;
};
enum class BattleCurrentPersonInjuryTraitsStatusV1 { available, partial, unavailable };
struct BattleCurrentPersonInjuryTraitsSnapshotV1 {
  BattleCurrentPersonInjuryTraitsStatusV1 status =
      BattleCurrentPersonInjuryTraitsStatusV1::unavailable;
  // wounded_1, wounded_2, wounded_3, maimed, one_legged, one_eyed,
  // disfigured, incapable; a failed read remains null, never false.
  std::array<std::optional<bool>, 8> flags{};
  std::optional<std::int32_t> wounded_rank;
  std::string unavailable_reason;
  std::string wounded_rank_unavailable_reason;
  friend bool operator==(const BattleCurrentPersonInjuryTraitsSnapshotV1 &,
                         const BattleCurrentPersonInjuryTraitsSnapshotV1 &) = default;
};
enum class BattleCurrentPersonDeathRecordStatusV1 { none, available, unavailable };
struct BattleCurrentPersonDeathRecordSnapshotV1 {
  BattleCurrentPersonDeathRecordStatusV1 status =
      BattleCurrentPersonDeathRecordStatusV1::unavailable;
  // Actual marker absence is none; a dead record's native null reason is
  // available/null. A copied empty stable key remains an empty string.
  std::optional<std::string> reason_key;
  std::string unavailable_reason;
  std::optional<std::uint64_t> date_object_raw_u64;
  std::optional<std::int32_t> killer_full_character_id_raw;
  std::optional<std::int32_t> artifact_full_id_raw;
  friend bool operator==(const BattleCurrentPersonDeathRecordSnapshotV1 &,
                         const BattleCurrentPersonDeathRecordSnapshotV1 &) = default;
};

// Current .3 raw property operands; observation does not construct future traits.
struct BattleCurrentPersonRawPropertiesSnapshotV1 {
  std::optional<std::int32_t> count;
  std::optional<std::vector<std::uint16_t>> keys_u16;
  std::optional<std::vector<std::int64_t>> values_q64;
  friend bool operator==(const BattleCurrentPersonRawPropertiesSnapshotV1 &,
                         const BattleCurrentPersonRawPropertiesSnapshotV1 &) = default;
};
struct BattleCurrentPersonRawWeightedRowSnapshotV1 {
  std::int32_t native_index = 0;
  std::optional<std::int64_t> weight_q64;
  std::optional<BattleCurrentPersonRawPropertiesSnapshotV1> properties;
  friend bool operator==(const BattleCurrentPersonRawWeightedRowSnapshotV1 &,
                         const BattleCurrentPersonRawWeightedRowSnapshotV1 &) = default;
};
struct BattleCurrentPersonRawContextSnapshotV1 {
  std::optional<BattleCurrentPersonRawPropertiesSnapshotV1> aggregate_properties;
  std::optional<std::int32_t> weighted_count;
  std::optional<std::vector<BattleCurrentPersonRawWeightedRowSnapshotV1>> weighted_rows;
  friend bool operator==(const BattleCurrentPersonRawContextSnapshotV1 &,
                         const BattleCurrentPersonRawContextSnapshotV1 &) = default;
};
// Independent current operands/results of 2948DF0/2948F00; no preparation call.
struct BattleCurrentPersonAuxiliaryScratchInputsSnapshotV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<std::int64_t> base430_q64;
  std::optional<std::int64_t> base438_q64;
  std::optional<std::uint8_t> selector_flag_raw;
  std::optional<std::int16_t> selector_metric_raw;
  std::optional<std::int32_t> selected_low_threshold_raw;
  std::optional<std::int32_t> selected_high_threshold_raw;
  std::optional<std::int64_t> prepared430_q64;
  std::optional<std::int64_t> prepared438_q64;
  std::optional<std::int64_t> copied430_q64;
  std::optional<std::int64_t> copied438_q64;
  std::optional<std::uint8_t> ready440_raw;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentPersonAuxiliaryScratchInputsSnapshotV1 &,
                         const BattleCurrentPersonAuxiliaryScratchInputsSnapshotV1 &) = default;
};
// Inputs of 2949010's independent nine-byte cache; actual scratch258 model.
struct BattleCurrentPersonNineCacheByteInputsSnapshotV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::optional<bool> model_present;
  std::optional<BattleCurrentPersonRawPropertiesSnapshotV1> aggregate_properties;
  std::optional<bool> carrier278_present;
  std::optional<std::uint32_t> carrier278_magic_raw;
  std::optional<bool> linked20_present;
  std::optional<bool> used_native_definition_fallback;
  std::optional<bool> selected_definition_present;
  std::optional<std::uint32_t> selected_definition_magic_raw;
  std::optional<std::vector<std::uint16_t>> selected_definition_keys_u16;
  std::optional<bool> current_cache_present;
  std::optional<std::vector<std::int8_t>> current_cache_bytes;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentPersonNineCacheByteInputsSnapshotV1 &,
                         const BattleCurrentPersonNineCacheByteInputsSnapshotV1 &) = default;
};
struct BattleCurrentPersonRawNumericInputsSnapshotV1 {
  std::string status = "unavailable";
  bool raw_numeric_inputs_ready = false;
  std::int32_t character_id = -1;
  std::optional<bool> scratch_present;
  std::string context_source = "unavailable";
  std::array<std::optional<std::int32_t>, 6> base_points{};
  std::array<std::optional<std::int32_t>, 6> caps{};
  std::optional<std::int32_t> prowess_adjustment;
  std::array<std::optional<std::int32_t>, 4> category_counts{};
  std::optional<std::int32_t> scratch_factor_numerator;
  std::optional<std::int32_t> scratch_factor_denominator;
  std::optional<BattleCurrentPersonRawContextSnapshotV1> context;
  std::optional<BattleCurrentPersonAuxiliaryScratchInputsSnapshotV1> auxiliary_scratch_inputs;
  std::optional<BattleCurrentPersonNineCacheByteInputsSnapshotV1> nine_cache_byte_inputs;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentPersonRawNumericInputsSnapshotV1 &,
                         const BattleCurrentPersonRawNumericInputsSnapshotV1 &) = default;
};

struct BattleCurrentPersonTitleCensusRowSnapshotV1 {
  std::int32_t native_row_index = 0;
  std::int32_t requested_full_title_id_raw_i32 = -1;
  std::string resolution = "unavailable";
  std::optional<std::int32_t> resolved_full_title_id_raw_i32;
  std::optional<std::uint8_t> qualifier_1d8_raw_u8;
  std::optional<std::uint8_t> qualifier_130_raw_u8;
  std::optional<std::int32_t> qualifier_12c_raw_i32;
  std::optional<bool> government_bit14;
  std::optional<std::int32_t> template_tier_raw_i32;
  friend bool operator==(const BattleCurrentPersonTitleCensusRowSnapshotV1 &,
                         const BattleCurrentPersonTitleCensusRowSnapshotV1 &) = default;
};

// Current raw source occurrences, independent of stored/future context values.
struct BattleCurrentPersonTitleCensusInputsSnapshotV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  bool scratch_present = false;
  std::optional<bool> model_present;
  std::optional<bool> model_owner_present;
  std::optional<std::int32_t> model_owner_full_character_id_raw_i32;
  std::optional<bool> model_owner_matches_character;
  std::optional<std::uint32_t> model_magic_raw_u32;
  std::string header_source;
  std::optional<std::int32_t> title_count_raw_i32;
  std::optional<std::vector<BattleCurrentPersonTitleCensusRowSnapshotV1>> title_occurrences;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentPersonTitleCensusInputsSnapshotV1 &,
                         const BattleCurrentPersonTitleCensusInputsSnapshotV1 &) = default;
};

// Readonly operands of the exact .3 291D1D0 preparation branch.
// Current prepared contributions; not a final-context or future-state cache.
struct BattleCurrentPersonContextBranchInputsSnapshotV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::int32_t character_id = -1;
  std::optional<bool> flag14;
  std::optional<std::int32_t> selected_index;
  std::optional<BattleCurrentPersonRawPropertiesSnapshotV1> selected_property_block;
  std::array<std::optional<std::int32_t>, 7> group_counts{};
  std::array<std::optional<BattleCurrentPersonRawPropertiesSnapshotV1>, 7>
      group_property_blocks{};
  std::optional<BattleCurrentPersonTitleCensusInputsSnapshotV1> census_inputs;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentPersonContextBranchInputsSnapshotV1 &,
                         const BattleCurrentPersonContextBranchInputsSnapshotV1 &) = default;
};

// Current .3 provider-prefix operands, not a materialized pre/future context.
struct BattleCurrentPersonPriorPropertyRowSnapshotV1 {
  std::uint16_t key = 0;
  std::int64_t value_raw = 0;
  friend bool operator==(const BattleCurrentPersonPriorPropertyRowSnapshotV1 &,
                         const BattleCurrentPersonPriorPropertyRowSnapshotV1 &) = default;
};
struct BattleCurrentPersonPriorPropertyBlockSnapshotV1 {
  std::vector<BattleCurrentPersonPriorPropertyRowSnapshotV1> rows;
  friend bool operator==(const BattleCurrentPersonPriorPropertyBlockSnapshotV1 &,
                         const BattleCurrentPersonPriorPropertyBlockSnapshotV1 &) = default;
};
struct BattleCurrentPersonPriorSelectorSnapshotV1 {
  bool available = false;
  std::optional<bool> uses_18f8_source;
  std::optional<std::int32_t> selected_header_offset;
  friend bool operator==(const BattleCurrentPersonPriorSelectorSnapshotV1 &,
                         const BattleCurrentPersonPriorSelectorSnapshotV1 &) = default;
};
struct BattleCurrentPersonPriorContextInputsSnapshotV1 {
  bool available = false;
  std::string reason;
  std::int32_t character_full_id = -1;
  std::optional<BattleCurrentPersonPriorPropertyBlockSnapshotV1> base_property_block;
  std::optional<std::vector<std::optional<BattleCurrentPersonPriorPropertyBlockSnapshotV1>>>
      common_property_blocks;
  BattleCurrentPersonPriorSelectorSnapshotV1 selector;
  std::optional<std::vector<std::optional<BattleCurrentPersonPriorPropertyBlockSnapshotV1>>>
      selected_property_blocks;
  friend bool operator==(const BattleCurrentPersonPriorContextInputsSnapshotV1 &,
                         const BattleCurrentPersonPriorContextInputsSnapshotV1 &) = default;
};

// Insert after BattleCurrentPersonRawNumericInputsSnapshotV1, inside xar::game.
// Existing RawProperties/RawContext DTOs are reused without unit conversion.
struct BattleCurrentPersonTaskPositionDeclarationSnapshotV1 {
  std::int32_t native_index = 0;
  std::string contributor_kind;
  std::optional<std::int32_t> scope_root_character_id_raw;
  std::optional<std::int32_t> scope_saved_character_id_raw;
  std::optional<std::int64_t> declaration_scale_q64;
  std::optional<BattleCurrentPersonRawPropertiesSnapshotV1> declared_properties;
  std::optional<std::uint64_t> modifier_flags_raw;
  std::string source_provenance;
  friend bool operator==(const BattleCurrentPersonTaskPositionDeclarationSnapshotV1 &,
                         const BattleCurrentPersonTaskPositionDeclarationSnapshotV1 &) = default;
};

struct BattleCurrentPersonTaskPositionEvaluatedRowSnapshotV1 {
  std::int32_t task_native_index = 0;
  std::string contributor_kind;
  std::int32_t declaration_native_index = 0;
  std::optional<std::int32_t> scope_root_character_id_raw;
  std::optional<std::int32_t> scope_saved_character_id_raw;
  std::optional<std::int64_t> declaration_scale_q64;
  // Actual native evaluated, scaled and finalized values; never source base.
  std::optional<BattleCurrentPersonRawPropertiesSnapshotV1> properties;
  std::optional<std::uint64_t> modifier_flags_raw;
  std::string source_provenance;
  friend bool operator==(const BattleCurrentPersonTaskPositionEvaluatedRowSnapshotV1 &,
                         const BattleCurrentPersonTaskPositionEvaluatedRowSnapshotV1 &) = default;
};

struct BattleCurrentPersonTaskPositionTaskSnapshotV1 {
  std::int32_t native_index = 0;
  std::int32_t task_id_raw = -1;
  std::optional<std::int32_t> resolved_task_id_raw;
  std::optional<bool> used_native_default;
  std::optional<std::uint8_t> frozen_raw;
  std::optional<std::int32_t> incumbent_character_id_raw;
  std::optional<std::int32_t> owner_character_id_raw;
  std::optional<bool> task_type_present;
  std::optional<bool> original_position_type_present;
  std::optional<bool> native_gate_allowed;
  std::optional<bool> terminal_task_type_present;
  std::optional<std::vector<BattleCurrentPersonTaskPositionDeclarationSnapshotV1>> declarations;
  bool owner_aggregate_properties_ready = false;
  // Real 31ABE10 output: merged owner collection, not emitted per-decl rows.
  std::optional<BattleCurrentPersonRawPropertiesSnapshotV1> owner_aggregate_properties;
  friend bool operator==(const BattleCurrentPersonTaskPositionTaskSnapshotV1 &,
                         const BattleCurrentPersonTaskPositionTaskSnapshotV1 &) = default;
};

struct BattleCurrentPersonTaskPositionBranchSnapshotV1 {
  std::string status = "unavailable";
  std::optional<bool> complete_no_contribution;
  bool vectors_ready = false;
  std::optional<std::vector<BattleCurrentPersonTaskPositionEvaluatedRowSnapshotV1>> evaluated_rows;
  std::optional<BattleCurrentPersonRawContextSnapshotV1> prefix_before;
  std::string prefix_source = "unobserved";
  std::optional<BattleCurrentPersonRawPropertiesSnapshotV1> aggregate_properties_after;
  std::string aggregate_source = "unobserved";
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentPersonTaskPositionBranchSnapshotV1 &,
                         const BattleCurrentPersonTaskPositionBranchSnapshotV1 &) = default;
};

struct BattleCurrentPersonTaskPositionInputsSnapshotV1 {
  std::string status = "unavailable";
  std::int32_t character_id = -1;
  bool raw_task_inputs_ready = false;
  bool branch_vectors_ready = false;
  std::optional<bool> owner_council_present;
  std::optional<std::vector<BattleCurrentPersonTaskPositionTaskSnapshotV1>> ordered_owned_tasks;
  std::optional<bool> councillor_task_link_present;
  std::optional<BattleCurrentPersonTaskPositionTaskSnapshotV1> councillor_task;
  BattleCurrentPersonTaskPositionBranchSnapshotV1 owned_passive;
  BattleCurrentPersonTaskPositionBranchSnapshotV1 councillor_position_task;
  std::string unavailable_reason;
  friend bool operator==(const BattleCurrentPersonTaskPositionInputsSnapshotV1 &,
                         const BattleCurrentPersonTaskPositionInputsSnapshotV1 &) = default;
};

// Append only this member to BattleCurrentPersonStateSnapshotV1.
// std::optional<BattleCurrentPersonTaskPositionInputsSnapshotV1>
//     current_context_task_position_inputs;

// Actual stored .3 model descriptors; these are current independent arrays.
// Capacity is raw DWORD bits, never a six-skill cap or an admission policy.
template <typename T> struct BattleCurrentStoredArraySnapshotV1 {
  std::optional<std::uint64_t> data_address;
  std::optional<std::uint32_t> capacity_raw;
  std::optional<std::int32_t> count;
  std::optional<std::vector<T>> items;
  friend bool operator==(const BattleCurrentStoredArraySnapshotV1 &,
                         const BattleCurrentStoredArraySnapshotV1 &) = default;
};
struct BattleCurrentStoredPropertyBlockSnapshotV1 {
  BattleCurrentStoredArraySnapshotV1<std::uint16_t> key_array;
  BattleCurrentStoredArraySnapshotV1<std::int64_t> value_array;
  friend bool operator==(const BattleCurrentStoredPropertyBlockSnapshotV1 &,
                         const BattleCurrentStoredPropertyBlockSnapshotV1 &) = default;
};
struct BattleCurrentStoredWeightedRowSnapshotV1 {
  std::int32_t native_index = 0;
  std::optional<std::int64_t> weight_raw;
  std::optional<BattleCurrentStoredPropertyBlockSnapshotV1> property_block;
  friend bool operator==(const BattleCurrentStoredWeightedRowSnapshotV1 &,
                         const BattleCurrentStoredWeightedRowSnapshotV1 &) = default;
};
struct BattleCurrentStoredContextStateSnapshotV1 {
  bool available = false;
  std::string reason;
  std::int32_t character_full_id = -1;
  std::optional<bool> scratch_present;
  std::optional<std::uint64_t> scratch_address;
  std::optional<bool> model_present;
  std::optional<std::uint64_t> model_address;
  std::optional<std::uint64_t> context_address;
  std::optional<std::uint64_t> owner_address;
  std::optional<std::int32_t> owner_character_full_id;
  std::optional<bool> bound_to_requested_character;
  std::optional<std::uint8_t> pending_raw;
  std::optional<std::int32_t> owned_count_raw;
  std::optional<BattleCurrentStoredArraySnapshotV1<BattleCurrentStoredWeightedRowSnapshotV1>> weighted;
  std::optional<BattleCurrentStoredArraySnapshotV1<std::uint16_t>> key_array;
  std::optional<BattleCurrentStoredArraySnapshotV1<std::int64_t>> value_array;
  // Pure predicate on the current operand, not an observed reset invocation.
  std::optional<bool> weighted_count_nonzero;
  friend bool operator==(const BattleCurrentStoredContextStateSnapshotV1 &,
                         const BattleCurrentStoredContextStateSnapshotV1 &) = default;
};

struct BattleCurrentPersonStateSnapshotV1 {
  BattleCurrentPersonEffectiveProwessSnapshotV1 effective_prowess;
  BattleCurrentPersonInjuryTraitsSnapshotV1 injury_traits;
  BattleCurrentPersonDeathRecordSnapshotV1 death_record;
  std::optional<BattleCurrentPersonRawNumericInputsSnapshotV1> raw_numeric_inputs;
  std::optional<BattleCurrentPersonTaskPositionInputsSnapshotV1> current_context_task_position_inputs;
  std::optional<BattleCurrentPersonContextBranchInputsSnapshotV1> context_branch_inputs;
  std::optional<BattleCurrentPersonPriorContextInputsSnapshotV1> current_prior_context_inputs;
  std::optional<BattleCurrentStoredContextStateSnapshotV1> current_stored_context_state;
  std::optional<BattleCurrentPersonContextSourceInputsSnapshotV1> current_context_source_inputs;
  friend bool operator==(const BattleCurrentPersonStateSnapshotV1 &,
                         const BattleCurrentPersonStateSnapshotV1 &) = default;
};

enum class BattleTerminalCustodyStatusV1 { observed, none, unavailable };
struct BattleTerminalCharacterCustodySnapshotV1 {
  std::int32_t character_id = -1;
  BattleTerminalCustodyStatusV1 status = BattleTerminalCustodyStatusV1::unavailable;
  std::optional<std::int32_t> actual_jailer_character_id;
  std::optional<bool> alive;
  std::optional<BattleCurrentPersonStateSnapshotV1> current_person_state;
  friend bool operator==(const BattleTerminalCharacterCustodySnapshotV1 &,
                         const BattleTerminalCharacterCustodySnapshotV1 &) = default;
};

struct BattleTerminalPriorSnapshotV1 {
  std::int32_t combat_id = -1;
  BattleTerminalKindV1 terminal_kind =
      BattleTerminalKindV1::unavailable_after_removal;
  std::optional<std::int32_t> terminal_date_raw;
  std::optional<bool> suppress_normal_result_envelopes;
  std::optional<std::int32_t> phase_raw;
  std::optional<std::int32_t> phase_day;
  std::optional<std::int32_t> winner_raw;
  std::optional<bool> finalized_before;
  std::optional<BattleTerminalHardLossInputsSnapshotV1> hard_loss_inputs;
  std::optional<std::array<BattleTerminalSideLossInputsSnapshotV1, 2>>
      side_loss_inputs_in_native_order;
  std::optional<std::array<BattleTerminalSideFinalResultSnapshotV1, 2>>
      side_final_results_in_native_order;
  std::optional<std::vector<BattleTerminalCharacterResultRowSnapshotV1>>
      character_result_rows_in_native_order;
  std::optional<std::vector<BattleTerminalCharacterCustodySnapshotV1>>
      character_custody_in_observed_order;
  std::optional<std::uint8_t> daily_guard_raw;
  std::optional<std::int32_t> province_id;
  std::optional<std::int32_t> battle_result_id;
  std::optional<bool> wipe_raw;
  std::optional<std::int32_t>
      attacker_primary_participant_character_id;
  std::optional<std::int32_t>
      defender_primary_participant_character_id;
  std::optional<std::vector<std::int32_t>>
      attacker_public_cunit_ids_in_stored_order;
  std::optional<std::vector<std::int32_t>>
      defender_public_cunit_ids_in_stored_order;
  BattleTerminalWarscoreSnapshotV1 battle_warscore;

  friend bool operator==(const BattleTerminalPriorSnapshotV1 &,
                         const BattleTerminalPriorSnapshotV1 &) = default;
};

struct BattleTerminalRemovalSnapshotV1 {
  bool prior_combat_strictly_resolves = false;
  std::optional<bool> prior_province_strictly_resolves;
  std::optional<bool> prior_province_contains_prior_combat_id;
  std::optional<bool> result_strictly_resolves;
  std::optional<std::int32_t> result_relevant_player_count;

  friend bool operator==(const BattleTerminalRemovalSnapshotV1 &,
                         const BattleTerminalRemovalSnapshotV1 &) = default;
};

struct BattleTerminalSubjectSnapshotV1 {
  bool exists = false;
  std::optional<std::int32_t> current_province_id;
  std::optional<std::int32_t> native_carmy_id;
  std::optional<std::int32_t> combat_backlink_id;
  std::optional<std::int32_t> active_combat_id;
  std::optional<std::int32_t> movement_or_retreat_state_raw;
  std::optional<std::int32_t> move_target_province_id;
  std::optional<std::vector<std::int32_t>>
      route_province_ids_in_stored_order;
  BattleTerminalAiMembershipStatusV1 ai_membership_status =
      BattleTerminalAiMembershipStatusV1::unavailable;
  std::optional<std::int32_t> coordinator_id;
  std::optional<std::int32_t> unit_stack_stored_index;
  std::optional<std::int32_t> subunit_stored_index;
  std::optional<bool> blocked_by_active_combat;

  friend bool operator==(const BattleTerminalSubjectSnapshotV1 &,
                         const BattleTerminalSubjectSnapshotV1 &) = default;
};

struct BattleTerminalSuccessorSnapshotV1 {
  BattleTerminalSuccessorStateV1 state =
      BattleTerminalSuccessorStateV1::unavailable;
  std::vector<std::int32_t> matching_combat_ids_in_native_order;
  std::optional<std::int32_t> selected_successor_combat_id;
  std::vector<std::int32_t>
      participant_overlap_public_cunit_ids_in_prior_order;

  friend bool operator==(const BattleTerminalSuccessorSnapshotV1 &,
                         const BattleTerminalSuccessorSnapshotV1 &) =
      default;
};

// Current native pending storage, independent of selected script requests.
struct BattlePendingDeathQueueRowSnapshotV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  std::int32_t row_index = 0;
  std::optional<bool> victim_pointer_present;
  std::optional<std::int32_t> victim_full_character_id_raw;
  std::optional<bool> victim_death_data_pointer_present;
  std::optional<bool> reason_pointer_present;
  std::optional<std::string> reason_key;
  std::optional<std::uint64_t> date_object_raw_u64;
  std::optional<bool> killer_pointer_present;
  std::optional<std::int32_t> killer_full_character_id_raw;
  std::optional<bool> artifact_pointer_present;
  std::optional<std::int32_t> artifact_full_id_raw;
  friend bool operator==(const BattlePendingDeathQueueRowSnapshotV1 &,
                         const BattlePendingDeathQueueRowSnapshotV1 &) = default;
};
struct BattlePendingDeathQueueSnapshotV1 {
  std::string status = "unavailable";
  std::string unavailable_reason;
  std::optional<bool> source_state_pointer_present;
  std::optional<bool> manager_owner_pointer_present;
  std::optional<std::uint8_t> execution_mode_raw;
  std::optional<bool> data_pointer_present;
  std::optional<std::int32_t> capacity_raw;
  std::optional<std::int32_t> count_raw;
  std::optional<std::vector<BattlePendingDeathQueueRowSnapshotV1>> rows;
  friend bool operator==(const BattlePendingDeathQueueSnapshotV1 &,
                         const BattlePendingDeathQueueSnapshotV1 &) = default;
};

struct BattleTerminalTransitionSnapshotV1 {
  BattleTerminalTransitionStatusV1 status =
      BattleTerminalTransitionStatusV1::unavailable;
  std::string unavailable_reason;
  bool battle_terminal_transition_ready = false;
  std::uint64_t snapshot_revision = 0;
  std::int64_t observed_date_raw = 0;
  std::int32_t prior_combat_id = -1;
  std::int32_t subject_public_cunit_id = -1;
  BattleTerminalJournalSnapshotV1 terminal_journal;
  BattleTerminalPriorSnapshotV1 prior;
  BattleTerminalRemovalSnapshotV1 removal;
  BattleTerminalSubjectSnapshotV1 subject;
  BattleTerminalSuccessorSnapshotV1 successor;
  std::optional<std::vector<BattleTerminalCharacterCustodySnapshotV1>>
      character_observations;
  std::optional<BattlePendingDeathQueueSnapshotV1> pending_death_queue;

  friend bool operator==(const BattleTerminalTransitionSnapshotV1 &,
                         const BattleTerminalTransitionSnapshotV1 &) =
      default;
};

// Exact, read-only projection of one native AI-managed CUnit's saved
// reinforcement request/assignment and its already committed route. Native
// arrays retain stored order; no future CombatID is inferred before contact.
struct BattleReinforcementAssignmentRequest {
  std::int32_t selected_public_cunit_id = -1;

  friend bool operator==(const BattleReinforcementAssignmentRequest &,
                         const BattleReinforcementAssignmentRequest &) =
      default;
};

enum class BattleReinforcementAssignmentStatus {
  available,
  unavailable,
};

struct BattleReinforcementSignalSnapshot {
  bool asking_for_help = false;
  bool assigned_to_help = false;
  bool asking_changed_last_evaluation = false;
  std::optional<std::int64_t> request_power_basis_raw;
  std::uint8_t cross_coordinator_request_valid_raw = 0;
  std::optional<std::int64_t> cross_coordinator_request_power_raw;
  std::optional<std::int64_t>
      first_route_edge_remaining_duration_q100000;

  friend bool operator==(const BattleReinforcementSignalSnapshot &,
                         const BattleReinforcementSignalSnapshot &) =
      default;
};

struct BattleReinforcementAssignmentStateSnapshot {
  std::optional<std::int32_t> assignment_target_province_id;
  std::string target_provenance = "none";
  std::string combat_binding_status = "unbound_until_contact";
  std::optional<std::int32_t> active_combat_id;

  friend bool operator==(
      const BattleReinforcementAssignmentStateSnapshot &,
      const BattleReinforcementAssignmentStateSnapshot &) = default;
};

struct BattleReinforcementRouteSnapshot {
  std::int32_t current_province_id = -1;
  std::optional<std::int32_t> move_target_province_id;
  std::vector<std::int32_t> route_province_ids;
  std::string route_alignment;
  std::optional<std::vector<std::int32_t>> arrival_date_raws;
  std::optional<std::int32_t> assignment_eta_date_raw;

  friend bool operator==(const BattleReinforcementRouteSnapshot &,
                         const BattleReinforcementRouteSnapshot &) =
      default;
};

struct BattleReinforcementParentSubunitSnapshot {
  std::vector<std::int32_t> public_cunit_ids_in_stored_order;
  bool asking_for_help = false;
  bool assigned_to_help = false;
  std::optional<std::int32_t> assignment_target_province_id;

  friend bool operator==(
      const BattleReinforcementParentSubunitSnapshot &,
      const BattleReinforcementParentSubunitSnapshot &) = default;
};

struct BattleReinforcementNativeOrderSnapshot {
  std::vector<std::int32_t>
      support_search_province_ids_in_stored_order;
  std::vector<BattleReinforcementParentSubunitSnapshot>
      parent_subunits_in_stored_order;

  friend bool operator==(const BattleReinforcementNativeOrderSnapshot &,
                         const BattleReinforcementNativeOrderSnapshot &) =
      default;
};

struct BattleReinforcementContactProjectionSnapshot {
  std::string status = "not_applicable";
  std::string temporal_semantics =
      "present_time_only_not_future_binding";
  std::vector<std::int32_t>
      current_target_compatible_combat_ids_in_stored_order;
  std::optional<std::int32_t> contact_if_now_selected_combat_id;
  std::optional<BattleReinforcementArrivalAdmission12003Snapshot> arrival_admission;

  friend bool operator==(
      const BattleReinforcementContactProjectionSnapshot &,
      const BattleReinforcementContactProjectionSnapshot &) = default;
};

struct BattleReinforcementAssignmentSnapshot {
  BattleReinforcementAssignmentStatus status =
      BattleReinforcementAssignmentStatus::unavailable;
  std::string unavailable_reason;
  std::uint64_t snapshot_revision = 0;
  std::int64_t observed_date_raw = 0;
  std::int32_t selected_public_cunit_id = -1;
  std::optional<std::int32_t> selected_native_carmy_id;
  std::optional<std::int32_t> coordinator_id;
  std::optional<std::int32_t> unit_stack_stored_index;
  std::optional<std::int32_t> subunit_stored_index;
  std::optional<BattleReinforcementSignalSnapshot> signal;
  std::optional<BattleReinforcementAssignmentStateSnapshot> assignment;
  std::optional<BattleReinforcementRouteSnapshot> route;
  std::optional<BattleReinforcementNativeOrderSnapshot> native_order;
  std::optional<BattleReinforcementContactProjectionSnapshot>
      contact_projection;
  bool battle_reinforcement_assignment_ready = false;

  friend bool operator==(const BattleReinforcementAssignmentSnapshot &,
                         const BattleReinforcementAssignmentSnapshot &) =
      default;
};
enum class DisbandArmyResult {
  submitted,
  army_not_found,
  army_not_controllable,
  unavailable,
};
enum class SplitArmyHalfResult {
  split_submitted,
  submission_failed,
  no_played_character,
  army_not_found,
  army_not_controllable,
  validator_rejected,
  unavailable,
};
enum class MergeArmiesResult {
  merge_submitted,
  submission_failed,
  no_played_character,
  destination_not_found,
  source_not_found,
  destination_not_controllable,
  source_not_controllable,
  same_army,
  validator_rejected,
  unavailable,
};
enum class StartAssaultResult {
  start_submitted,
  submission_failed,
  no_played_character,
  siege_not_found,
  assault_already_active,
  validator_rejected,
  unavailable,
};
enum class StopAssaultResult {
  stop_submitted,
  submission_failed,
  no_played_character,
  siege_not_found,
  assault_not_active,
  validator_rejected,
  unavailable,
};
enum class ReadDeclarableWarsResult {
  available,
  no_played_character,
  target_not_found,
  unavailable,
};
enum class DeclareWarResult {
  submitted,
  no_played_character,
  target_not_found,
  declaration_unavailable,
  validation_failed,
  unavailable,
};
enum class ReadArrangeMarriageChoicesResult {
  available,
  no_played_character,
  unavailable,
};
enum class ReadArrangeMarriageFamilyCandidatesResultV1 {
  available,
  no_played_character,
  subject_not_found,
  unavailable,
};
enum class ArrangeMarriageResult {
  submitted,
  no_played_character,
  candidate_not_found,
  choice_unavailable,
  unavailable,
};
enum class EnforceDemandsResult {
  submitted,
  no_played_character,
  war_not_found,
  player_not_participant,
  player_not_war_leader,
  validation_failed,
  unavailable,
};
enum class ReadWarTerminationOptionsResult {
  available,
  requires_paused,
  no_played_character,
  war_not_found,
  player_not_participant,
  unavailable,
};
enum class ReadOutboundWarWhitePeaceStatusResult {
  available,
  requires_paused,
  no_played_character,
  war_not_found,
  player_not_participant,
  player_not_war_leader,
  state_changed,
  unavailable,
};
enum class ReadWarTerminationTermsResult {
  available,
  unsupported_casus_belli,
  requires_paused,
  no_played_character,
  war_not_found,
  player_not_participant,
  unavailable,
};
enum class ReadDefenderDeJureExitTermsV1Result {
  available_baseline,
  unsupported_casus_belli,
  requires_paused,
  no_played_character,
  war_not_found,
  player_not_primary_defender,
  unavailable,
};

enum class ReadWarTerminationExitTermsResult {
  available,
  unsupported_casus_belli,
  requires_paused,
  no_played_character,
  war_not_found,
  player_not_participant,
  player_not_primary_attacker,
  unavailable,
};
enum class ReadArmyStrengthsResult {
  available,
  partial,
  requires_paused,
  no_played_character,
  unavailable,
};
// One arbitrary Province is read independently of the war-objective row
// budget. A partial result preserves every field's observable/null semantics.
enum class ReadProvinceLocalSiegeResult {
  available,
  partial,
  requires_paused,
  no_played_character,
  province_not_found,
  state_changed,
  unavailable,
};
enum class ReadCombatSimulationInputsResult {
  available,
  partial,
  requires_paused,
  no_played_character,
  invalid_arguments,
  target_province_not_found,
  army_not_in_scope,
  invalid_encounter,
  unavailable,
};
enum class SurrenderWarResult {
  submitted,
  submission_failed,
  requires_paused,
  no_played_character,
  war_not_found,
  player_not_participant,
  player_not_war_leader,
  context_unavailable,
  validation_failed,
  unavailable,
};
enum class OfferWhitePeaceResult {
  submitted,
  submission_failed,
  requires_paused,
  no_played_character,
  war_not_found,
  player_not_participant,
  player_not_war_leader,
  casus_belli_unavailable,
  white_peace_not_allowed,
  context_unavailable,
  validation_failed,
  unavailable,
};

} // namespace xar::game
