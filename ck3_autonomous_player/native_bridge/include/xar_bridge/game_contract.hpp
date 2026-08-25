#pragma once

#include <cstdint>
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
  std::vector<ArrangeMarriageValidationSample> validation_false_samples;

  friend bool operator==(const ArrangeMarriageQueryDiagnostics &,
                         const ArrangeMarriageQueryDiagnostics &) = default;
};

struct ArmySnapshot {
  std::int32_t army_id = -1;
  std::int32_t owner_character_id = -1;
  bool has_current_province = false;
  std::int32_t current_province_id = -1;
  std::vector<std::int32_t> route_province_ids;
  bool move_target_observable = false;
  std::int32_t move_target_province_id = -1;
  std::int32_t army_state_code = 0;
  std::string army_state = "unknown";
  bool in_combat = false;
  bool retreating = false;
  bool controllable = false;

  friend bool operator==(const ArmySnapshot &, const ArmySnapshot &) = default;
};

enum class ArmyStrengthScopeRole {
  player,
  active_war_ally,
  active_war_enemy,
};

// One generation-checked aggregate over a public CUnit and its exact CArmy /
// CRegiment graph. A row is atomic: when any component ID, native array,
// public-ID identity predicate or checked sum cannot be validated, available
// is false and
// every numeric aggregate must remain uninterpretable. The base-power raw
// value is CK3's AI metric, not a combat prediction or win probability.
struct ArmyStrengthSnapshot {
  bool available = false;
  std::int32_t army_id = -1;
  bool native_carmy_id_observable = false;
  std::int32_t native_carmy_id = -1;
  ArmyStrengthScopeRole scope_role = ArmyStrengthScopeRole::player;
  std::vector<std::int32_t> war_ids;
  std::int32_t regiment_count = 0;
  std::int32_t current_soldiers = 0;
  std::int32_t maximum_soldiers = 0;
  std::int64_t ai_base_power_raw = 0;
  std::int64_t ai_base_power_scale = 100'000;
  std::string unavailable_reason;

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

  friend bool operator==(const CombatCommanderSnapshot &,
                         const CombatCommanderSnapshot &) = default;
};

struct CombatKnightSnapshot {
  bool eligible = false;
  std::int32_t character_id = -1;
  std::int32_t source_regiment_id = -1;
  std::int32_t army_id = -1;
  bool participant_army_membership_verified = false;
  std::int32_t prowess = 0;
  std::int64_t knight_effectiveness_raw = 0;
  std::int64_t effective_damage_raw = 0;
  std::int64_t effective_toughness_raw = 0;
  std::int64_t scale = 100'000;

  friend bool operator==(const CombatKnightSnapshot &,
                         const CombatKnightSnapshot &) = default;
};

struct CombatKnightsSnapshot {
  bool available = false;
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
  std::int32_t base_advantage = 0;
  std::int32_t resolved_advantage = 0;
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

  friend bool operator==(const CombatSimulationInputsRequest &,
                         const CombatSimulationInputsRequest &) = default;
};

struct CombatHypotheticalScenarioSnapshot {
  std::int32_t attacker_entry_province_id = -1;
  std::vector<std::int32_t> attacker_army_ids;
  std::vector<std::int32_t> defender_army_ids;
  std::string attacker_side;
  std::string defender_side;

  friend bool operator==(const CombatHypotheticalScenarioSnapshot &,
                         const CombatHypotheticalScenarioSnapshot &) = default;
};

// One paused projection of an explicit hypothetical contact scenario. The
// adapter revalidates both public ArmyID partitions against one current active
// war and derives crossing only from the caller-supplied final-edge origin;
// native storage handles never cross this contract.
struct CombatSimulationInputsSnapshot {
  std::int32_t target_province_id = -1;
  CombatHypotheticalScenarioSnapshot scenario;
  std::vector<CombatArmyInputsSnapshot> armies;
  CombatCandidateProvinceSnapshot target_province;
  std::vector<OngoingCombatInputsSnapshot> ongoing_combats;
  std::vector<CombatCounterResolutionSnapshot> counter_resolutions;
  bool input_observation_ready = false;
  bool monte_carlo_ready = false;
  std::vector<std::string> missing_required_domains;

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

// Narrow, complete claim-CB terms projection. This intentionally does not
// widen WarTerminationOptionsSnapshot: gold, prestige, truce and prisoner
// effects require separately versioned readers once their native ABIs are
// closed. The rows preserve the CWar target-title order.
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

struct PreviewMoveArmyResult {
  PreviewMoveArmyStatus status = PreviewMoveArmyStatus::unavailable;
  std::int32_t army_id = -1;
  std::int32_t origin_province_id = -1;
  std::int32_t target_province_id = -1;
  std::vector<std::int32_t> route_province_ids;

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
enum class ReadWarTerminationTermsResult {
  available,
  unsupported_casus_belli,
  requires_paused,
  no_played_character,
  war_not_found,
  player_not_participant,
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
