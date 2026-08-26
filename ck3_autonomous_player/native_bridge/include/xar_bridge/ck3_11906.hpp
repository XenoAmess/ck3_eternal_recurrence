#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace xar::ck3_11906 {

inline constexpr char kExecutableSha256[] =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr char kCheckpointSaveName[] = "xar_checkpoint";

using SubmitCommand = bool (*)(void *manager, void *command,
                               std::uint32_t channel_flags);
using GetLocalPlayer = void *(*)(void *jomini_state);
using GetCurrentEvent = void *(*)(void *event_manager);
using IsPendingCharacterInteractionForCharacter = bool (*)(
    void *pending_interaction, void *character);
using ValidateReplyCharacterInteractionCommand = bool (*)(void *command);
using ContainsWarParticipant = bool (*)(void *participant_container,
                                        std::int32_t character_id);
using GetWarScore = std::int32_t (*)(void *war, void *war_score_context);
using GetWarScoreComponent = std::int32_t (*)(void *war,
                                              void *war_score_context);
using GetWarScoreSideComponent = std::int32_t (*)(
    void *war, bool side, void *war_score_context);
using GetWarScoreOccupationComponent = std::uint64_t (*)(
    void *war, bool side, void *war_score_context);
using GetWarScoreTickingComponent = std::int32_t (*)(
    void *war, bool side, void *war_score_context, bool mode);
using IsNativeComponentAlive = bool (*)(void *component);
using ReadSiegeFixedPoint = std::int64_t *(*)(void *siege,
                                              std::int64_t *output);
using GetSiegeDaysLeft = std::int32_t (*)(void *siege);
using ReadAssaultDailyProgress = std::int64_t *(*)(
    void *siege, std::int64_t *output, std::int32_t eligible_besiegers);
using GetAssaultDailyCasualties = std::int32_t (*)(void *siege);
using ValidateAssaultCommand = bool (*)(
    std::int32_t command_kind, std::int32_t played_character_id,
    std::int32_t siege_id, void *error_output);
using IsProvinceOccupied = bool (*)(void *province);
using GetProvinceInt32 = std::int32_t (*)(void *province);
using ResolveDefaultRaiseProvince = void *(*)(void *character);
using GetUnitState = std::int32_t (*)(void *unit);
using GetArmyCurrentSoldiers = std::int32_t (*)(
    const void *regiment_id_array, std::uint8_t flags);
using GetArmyMaximumSoldiers = std::int32_t (*)(void *army);
using GetArmyCommander = void *(*)(void *army);
using GetCommanderAdvantage = std::int32_t (*)(void *character,
                                               std::int32_t context,
                                               bool include_roll);
using GetProvinceTerrain = void *(*)(void *province);
using EvaluateRegimentStatsAtProvince = void *(*)(
    void *regiment, void *output, void *province);
using IsSpecialCombatRegiment = bool (*)(void *regiment);
using GetCharacterModifierAggregator = void *(*)(void *character);
using ReadCharacterModifier = std::int64_t *(*)(
    void *aggregator, std::int64_t *output, std::int32_t modifier_index);
using GetCombatRules = void *(*)();
using GetCombatSideStrength = std::int32_t (*)(void *combat_side);
using GetCombatRegimentStrength = std::int32_t (*)(void *combat_regiment);
using ReadCounterCurrentChunk = std::int64_t *(*)(
    const void *side_maa_entry, std::int64_t *output);
using ResolveCounterClasses = void (*)(
    void *countered_entries, void *countering_entries,
    void *output_by_counter_class, std::int64_t context_scale);
using GetCounterContextScale = std::int64_t *(*)(
    std::int64_t *output, void *countered_modifier_aggregator,
    void *countering_modifier_aggregator);
using GetKnightEffectivenessContext = void *(*)(void *character);
using ReadKnightEffectiveness = std::int64_t *(*)(
    std::int64_t *output, void *effectiveness_context,
    std::uint64_t mode);
using IsHoldingDefender = bool (*)(void *defender_owner,
                                   void *target_province);
using ConstructRaiseTroopsCommand = void *(*)(void *command,
                                              std::int32_t character_id,
                                              const void *raise_entry);
using ValidateRaiseTroopsCommand = bool (*)(void *command,
                                            void *validation_context);
using DestroyNativeCommand = void *(*)(void *command,
                                       std::int32_t delete_flags);
using GetArmyMoveMode = std::int32_t (*)(void *army, void *province,
                                        std::int32_t direct_target);
using CanCharacterUseCommandKind = bool (*)(void *character,
                                            std::int32_t command_kind);
using CanArmyUseMoveMode = bool (*)(void *army, std::int32_t move_mode);
using CanMoveArmy = bool (*)(std::int32_t command_kind, void *army,
                             std::int32_t move_mode);
using CanOrderCombatRetreat = bool (*)(void *combat, void *selected_army,
                                       void *error_sink);
using GetCombatRetreatRuleState = void *(*)();
using ResolveMoveOrigin = void *(*)(void *origin_context);
using ConstructMovePathContext = void *(*)(void *path_context, void *army);
using ConstructArmyMovePath = void *(*)(void *path_storage);
using BuildArmyMoveRoute = bool (*)(void *path_context, void *origin_province,
                                    void *target_province,
                                    std::int32_t route_kind,
                                    void *path_storage);
using ReadRouteTravelDuration = std::int64_t *(*)(
    void *unit, std::int64_t *output, const void *path_storage,
    void *origin_province);
using ReadRouteEdgeDuration = std::int64_t *(*)(
    void *unit, std::int64_t *output, std::int32_t route_index);
using ReadUnitRouteSpeed = std::int64_t *(*)(void *unit,
                                             std::int64_t *output);
using ValidateDisbandArmyCommand = bool (*)(
    std::int32_t command_kind, std::int32_t command_target_id,
    void *error_output);
using ValidateSplitArmyHalfCommand = bool (*)(
    std::int32_t command_kind, std::int32_t source_army_id,
    std::int32_t played_character_id, void *error_output);
using CreateMergeArmiesCommand = void *(*)();
using ValidateMergeArmiesCommand = bool (*)(void *command,
                                             void *error_output);
using GetCasusBelliTypeDatabase = void *(*)();
using GetCharacterInteractionDatabase = void *(*)();
using HashStableKey = std::int32_t (*)(void *context,
                                      const char *data,
                                      std::uint32_t size);
using LookupSchemeType = void *(*)(void *database, std::int32_t key_hash);
using EvaluateCasusBelli = bool (*)(void *casus_belli_type,
                                    void *attacker_character,
                                    void *defender_character,
                                    void *output_configurations,
                                    bool include_blocked,
                                    bool unknown_flag,
                                    void *evaluation_context);
using DestroyValidCasusBelliConfiguration = void (*)(void *configuration);
using ConstructCharacterInteractionContext = void *(*)(
    void *context, void *interaction, std::int32_t actor_character_id,
    std::int32_t recipient_character_id, void *extra_context,
    bool initialize_special_data);
using RedirectCharacterInteractionRoles = void (*)(
    void *interaction, std::int32_t *actor_character_id,
    std::int32_t *recipient_character_id,
    std::int32_t *secondary_actor_character_id,
    std::int32_t *secondary_recipient_character_id,
    std::int32_t *intermediary_character_id);
using ConstructCharacterInteractionContextAllRoles = void *(*)(
    void *context, void *interaction, std::int32_t actor_character_id,
    std::int32_t recipient_character_id,
    std::int32_t secondary_actor_character_id,
    std::int32_t secondary_recipient_character_id,
    std::int32_t intermediary_character_id, void *extra_context);
using CopyNativeIntArray = void (*)(void *destination, const void *source);
using AppendNativeIntArrayRange = void (*)(void *destination,
                                           std::int32_t insertion_index,
                                           const std::int32_t *begin,
                                           const std::int32_t *end);
using RefreshCharacterInteractionContext = void (*)(void *context,
                                                     bool refresh);
using FinalizeCharacterInteractionContext = void (*)(void *context);
using ValidateCharacterInteractionContext = bool (*)(void *context,
                                                      void *error_output);
using ReadCharacterInteractionAnswerScore = std::int64_t *(*)(
    void *context, std::int64_t *output);
using EvaluateCharacterInteractionTrigger = bool (*)(
    void *trigger, const void *event_target_scope);
using ConstructSendCharacterInteractionCommand = void *(*)(
    void *command, const void *context);
using DestroyCharacterInteractionContext = void (*)(void *context);
using DefaultConstructCharacterInteractionContext = void *(*)(void *context);
using ConstructWarResolutionInteractionContext = void (*)(void *context,
                                                           void *war,
                                                           bool attacker_victory);
using ConstructSpecialCharacterInteractionContext = void *(*)(
    void *context, std::uint8_t special_index,
    std::int32_t actor_character_id,
    std::int32_t recipient_character_id);
using ReadCharacterClaim = void *(*)(void *output, void *claimant,
                                     void *title);
using ConstructWarEffectContext = void *(*)(void *context);
using PopulateWarEffectContext = void (*)(void *context, void *war,
                                          bool unknown_flag);
using ConstructEffectPreviewCollector = void *(*)(void *collector);
using DestroyEffectPreviewCollector = void (*)(void *collector);
using TraverseLoadedEffect = void (*)(void *loaded_effect,
                                      void *effect_context,
                                      void *collector);
using DestroyEffectContextSubobject = void (*)(void *subobject);
using EvaluateTruceDurationDays = std::int32_t (*)(
    void *script_value, void *effect_context, void *evaluation_context);
using GetCharacterPrimaryTitle = void *(*)(void *character);
using ReadMonthlyGoldIncome = std::int64_t *(*)(
    std::int64_t *output, void *character, void *optional_breakdown,
    void *evaluation_context);
using EvaluateCharacterInteractionAnswer = std::uint8_t (*)(
    void *context, std::uint8_t answer_mode, std::uint8_t flag,
    void *error_sink_a, void *error_sink_b);
using GetGlobalVariableContainer = void *(*)();
using GetScriptIdentifierTable = void *(*)();
using LookupScriptIdentifierId = std::int32_t *(*)(
    void *table, std::int32_t *output, const void *string_view);
using IsEventTargetValid = bool (*)(const void *event_target);
using ResolveEventTargetObject = void *(*)(const void *event_target);
using IsCharacterHostile = bool (*)(void *left_character,
                                    void *right_character, bool mode);
using ArmyContactPredicate = bool (*)(void *army);
using ReadProvinceHolderCharacterId = std::int32_t *(*)(
    void *province, std::int32_t *output);
using CharacterRelationPredicate = bool (*)(void *left_character,
                                             void *right_character);
using CharacterProvincePredicate = bool (*)(void *character,
                                             void *province);

// Absolute addresses resolved only after the main executable matches the
// pinned 1.19.0.6 SHA-256. Tests may supply a small in-memory fixture instead.
struct Bindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **jomini_state_slot = nullptr;
  void *command_manager = nullptr;
  std::uintptr_t pause_primary_vtable = 0;
  std::uintptr_t pause_secondary_vtable = 0;
  std::uintptr_t set_speed_primary_vtable = 0;
  std::uintptr_t set_speed_secondary_vtable = 0;
  std::uintptr_t select_event_option_primary_vtable = 0;
  std::uintptr_t select_event_option_secondary_vtable = 0;
  std::uintptr_t ingame_interface_idler_vtable = 0;
  std::uintptr_t event_window_primary_vtable = 0;
  std::uintptr_t scheme_type_primary_vtable = 0;
  std::uintptr_t auto_save_primary_vtable = 0;
  std::uintptr_t auto_save_secondary_vtable = 0;
  std::uintptr_t reply_character_interaction_primary_vtable = 0;
  std::uintptr_t reply_character_interaction_secondary_vtable = 0;
  std::uintptr_t raise_troops_primary_vtable = 0;
  std::uintptr_t raise_troops_secondary_vtable = 0;
  std::uintptr_t move_army_primary_vtable = 0;
  std::uintptr_t move_army_secondary_vtable = 0;
  std::uintptr_t disband_army_primary_vtable = 0;
  std::uintptr_t disband_army_secondary_vtable = 0;
  std::uintptr_t split_army_half_primary_vtable = 0;
  std::uintptr_t split_army_half_secondary_vtable = 0;
  std::uintptr_t merge_armies_primary_vtable = 0;
  std::uintptr_t merge_armies_secondary_vtable = 0;
  std::uintptr_t start_assault_primary_vtable = 0;
  std::uintptr_t start_assault_secondary_vtable = 0;
  std::uintptr_t stop_assault_primary_vtable = 0;
  std::uintptr_t stop_assault_secondary_vtable = 0;
  std::uintptr_t send_character_interaction_primary_vtable = 0;
  std::uintptr_t send_character_interaction_secondary_vtable = 0;
  std::uintptr_t war_declaration_vtable = 0;
  std::uintptr_t character_claim_vtable = 0;
  std::uintptr_t effect_preview_collector_vtable = 0;
  std::uintptr_t jomini_effect_vtable = 0;
  std::uintptr_t jomini_scripted_effect_vtable = 0;
  std::uintptr_t jomini_scripted_effect_template_vtable = 0;
  std::uintptr_t hidden_effect_vtable = 0;
  std::uintptr_t jomini_context_effect_vtable = 0;
  std::uintptr_t prestige_effect_vtable = 0;
  std::uintptr_t prestige_experience_effect_vtable = 0;
  std::uintptr_t piety_effect_vtable = 0;
  std::uintptr_t piety_experience_effect_vtable = 0;
  std::uintptr_t legitimacy_effect_vtable = 0;
  std::uintptr_t stress_impact_effect_vtable = 0;
  std::uintptr_t add_from_contribution_attackers_effect_vtable = 0;
  std::uintptr_t add_from_contribution_defenders_effect_vtable = 0;
  std::uintptr_t gold_transfer_effect_vtable = 0;
  std::uintptr_t truce_effect_vtable = 0;
  std::uintptr_t ai_unit_stack_vtable = 0;
  std::uintptr_t ai_subunit_stack_vtable = 0;
  std::uintptr_t ai_war_coordinator_vtable = 0;
  const std::int32_t *cb_prestige_factor_identifier_id = nullptr;
  void **pending_character_interaction_storage_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **army_storage_slot = nullptr;
  void **army_internal_storage_slot = nullptr;
  void **regiment_storage_slot = nullptr;
  void **combat_storage_slot = nullptr;
  void **battle_result_storage_slot = nullptr;
  void **battle_result_fallback_slot = nullptr;
  void **ai_war_coordinator_storage_slot = nullptr;
  void **ai_war_coordinator_fallback_slot = nullptr;
  void **siege_storage_slot = nullptr;
  void **contact_game_mode_slot = nullptr;
  void **trait_database_slot = nullptr;
  void **scheme_type_database_slot = nullptr;
  void **scheme_type_fallback_slot = nullptr;
  GetGlobalVariableContainer *global_variable_container_accessor_slot =
      nullptr;
  void *valid_casus_belli_configuration_scratch = nullptr;
  std::size_t event_manager_offset = 0;
  std::size_t player_character_manager_offset = 0;
  std::size_t war_manager_offset = 0;
  std::size_t landed_title_manager_offset = 0;
  std::size_t arrange_marriage_interaction_offset = 0;
  std::size_t declare_war_interaction_offset = 0;
  SubmitCommand submit_command = nullptr;
  GetLocalPlayer get_local_player = nullptr;
  GetCurrentEvent get_current_event = nullptr;
  IsPendingCharacterInteractionForCharacter
      is_pending_character_interaction_for_character = nullptr;
  ValidateReplyCharacterInteractionCommand
      validate_reply_character_interaction_command = nullptr;
  ContainsWarParticipant contains_war_participant = nullptr;
  GetWarScore get_war_score = nullptr;
  GetWarScoreComponent get_imprisonment_war_score = nullptr;
  GetWarScoreComponent get_battle_war_score_base = nullptr;
  GetWarScoreSideComponent get_battle_war_score_side = nullptr;
  GetWarScoreOccupationComponent get_occupation_war_score_side = nullptr;
  GetWarScoreTickingComponent get_ticking_war_score_side = nullptr;
  IsNativeComponentAlive is_native_component_alive = nullptr;
  ReadSiegeFixedPoint get_siege_progress = nullptr;
  ReadSiegeFixedPoint get_siege_total_work = nullptr;
  GetSiegeDaysLeft get_siege_days_left = nullptr;
  ReadAssaultDailyProgress read_assault_daily_progress = nullptr;
  GetAssaultDailyCasualties get_assault_daily_casualties = nullptr;
  ValidateAssaultCommand validate_start_assault_command = nullptr;
  ValidateAssaultCommand validate_stop_assault_command = nullptr;
  DestroyNativeCommand destroy_assault_command = nullptr;
  IsProvinceOccupied is_province_occupied = nullptr;
  GetProvinceInt32 get_province_fort_level = nullptr;
  GetProvinceInt32 get_province_garrison_size = nullptr;
  GetProvinceInt32 get_province_besieging_strength = nullptr;
  ResolveDefaultRaiseProvince resolve_default_raise_province = nullptr;
  GetUnitState get_unit_state = nullptr;
  GetArmyCurrentSoldiers get_army_current_soldiers = nullptr;
  GetArmyMaximumSoldiers get_army_maximum_soldiers = nullptr;
  GetArmyCommander get_army_commander = nullptr;
  GetCommanderAdvantage get_commander_advantage = nullptr;
  GetProvinceTerrain get_province_terrain = nullptr;
  EvaluateRegimentStatsAtProvince evaluate_regiment_stats_at_province =
      nullptr;
  IsSpecialCombatRegiment is_special_combat_regiment = nullptr;
  GetCharacterModifierAggregator get_character_modifier_aggregator = nullptr;
  ReadCharacterModifier read_character_modifier = nullptr;
  GetCombatRules get_combat_rules = nullptr;
  GetCombatSideStrength get_combat_side_strength = nullptr;
  GetCombatRegimentStrength get_combat_regiment_strength = nullptr;
  ReadCounterCurrentChunk read_counter_current_chunk = nullptr;
  ResolveCounterClasses resolve_counter_classes = nullptr;
  GetCounterContextScale get_counter_context_scale = nullptr;
  GetKnightEffectivenessContext get_knight_effectiveness_context = nullptr;
  ReadKnightEffectiveness read_knight_effectiveness = nullptr;
  IsHoldingDefender is_holding_defender = nullptr;
  const std::int32_t *commander_min_roll = nullptr;
  const std::int32_t *commander_max_roll = nullptr;
  const std::int32_t *knight_damage_per_prowess = nullptr;
  const std::int32_t *knight_toughness_per_prowess = nullptr;
  const std::int32_t *minimum_combat_width = nullptr;
  const std::int64_t *base_combat_width_ratio = nullptr;
  ConstructRaiseTroopsCommand construct_raise_troops_command = nullptr;
  ValidateRaiseTroopsCommand validate_raise_troops_command = nullptr;
  DestroyNativeCommand destroy_raise_troops_command = nullptr;
  GetArmyMoveMode get_army_move_mode = nullptr;
  CanCharacterUseCommandKind can_character_use_command_kind = nullptr;
  CanArmyUseMoveMode can_army_use_move_mode = nullptr;
  CanMoveArmy can_move_army = nullptr;
  CanOrderCombatRetreat can_order_combat_retreat = nullptr;
  GetCombatRetreatRuleState get_combat_retreat_rule_state = nullptr;
  const std::int32_t *minimum_days_before_manual_retreat = nullptr;
  ResolveMoveOrigin resolve_move_origin = nullptr;
  ConstructMovePathContext construct_move_path_context = nullptr;
  ConstructArmyMovePath construct_army_move_path = nullptr;
  BuildArmyMoveRoute build_army_move_route = nullptr;
  ReadUnitRouteSpeed read_unit_land_route_speed = nullptr;
  ReadUnitRouteSpeed read_unit_naval_route_speed = nullptr;
  ReadUnitRouteSpeed read_unit_current_edge_speed = nullptr;
  ReadRouteTravelDuration read_route_travel_duration = nullptr;
  ReadRouteEdgeDuration read_route_edge_duration = nullptr;
  DestroyNativeCommand destroy_move_army_command = nullptr;
  ValidateDisbandArmyCommand validate_disband_army_command = nullptr;
  ValidateSplitArmyHalfCommand validate_split_army_half_command = nullptr;
  DestroyNativeCommand destroy_split_army_half_command = nullptr;
  CreateMergeArmiesCommand create_merge_armies_command = nullptr;
  ValidateMergeArmiesCommand validate_merge_armies_command = nullptr;
  DestroyNativeCommand destroy_merge_armies_command = nullptr;
  GetCasusBelliTypeDatabase get_casus_belli_type_database = nullptr;
  GetCharacterInteractionDatabase get_character_interaction_database =
      nullptr;
  HashStableKey hash_stable_key = nullptr;
  LookupSchemeType lookup_scheme_type = nullptr;
  EvaluateCasusBelli evaluate_casus_belli = nullptr;
  DestroyValidCasusBelliConfiguration
      destroy_valid_casus_belli_configuration = nullptr;
  ConstructCharacterInteractionContext
      construct_character_interaction_context = nullptr;
  RedirectCharacterInteractionRoles redirect_character_interaction_roles =
      nullptr;
  ConstructCharacterInteractionContextAllRoles
      construct_character_interaction_context_all_roles = nullptr;
  CopyNativeIntArray copy_native_int_array = nullptr;
  AppendNativeIntArrayRange append_native_int_array_range = nullptr;
  RefreshCharacterInteractionContext
      refresh_character_interaction_context = nullptr;
  FinalizeCharacterInteractionContext
      finalize_character_interaction_context = nullptr;
  ValidateCharacterInteractionContext
      validate_character_interaction_context = nullptr;
  ReadCharacterInteractionAnswerScore
      read_character_interaction_answer_score = nullptr;
  EvaluateCharacterInteractionTrigger
      evaluate_character_interaction_trigger = nullptr;
  ConstructSendCharacterInteractionCommand
      construct_send_character_interaction_command = nullptr;
  DestroyCharacterInteractionContext
      destroy_character_interaction_context = nullptr;
  DefaultConstructCharacterInteractionContext
      default_construct_character_interaction_context = nullptr;
  ConstructWarResolutionInteractionContext
      construct_war_resolution_interaction_context = nullptr;
  ConstructSpecialCharacterInteractionContext
      construct_special_character_interaction_context = nullptr;
  ReadCharacterClaim read_character_claim = nullptr;
  ConstructWarEffectContext construct_war_effect_context = nullptr;
  PopulateWarEffectContext populate_war_effect_context = nullptr;
  ConstructEffectPreviewCollector construct_effect_preview_collector =
      nullptr;
  DestroyEffectPreviewCollector destroy_effect_preview_collector = nullptr;
  TraverseLoadedEffect traverse_loaded_effect = nullptr;
  DestroyEffectContextSubobject destroy_effect_context_118 = nullptr;
  DestroyEffectContextSubobject destroy_effect_context_array_row = nullptr;
  EvaluateTruceDurationDays evaluate_truce_duration_days = nullptr;
  GetCharacterPrimaryTitle get_character_primary_title = nullptr;
  ReadMonthlyGoldIncome read_monthly_gold_income = nullptr;
  EvaluateCharacterInteractionAnswer evaluate_character_interaction_answer =
      nullptr;
  GetScriptIdentifierTable get_script_identifier_table = nullptr;
  LookupScriptIdentifierId lookup_script_identifier_id = nullptr;
  IsEventTargetValid is_event_target_valid = nullptr;
  ResolveEventTargetObject resolve_event_target_object = nullptr;
  IsCharacterHostile is_character_hostile = nullptr;
  ArmyContactPredicate is_army_empty_for_contact = nullptr;
  ArmyContactPredicate is_army_in_combat = nullptr;
  ReadProvinceHolderCharacterId read_province_holder_character_id = nullptr;
  CharacterRelationPredicate classify_contact_defender_by_holder = nullptr;
  CharacterProvincePredicate classify_contact_defender_fallback = nullptr;
};

using game::ActiveWarSnapshot;
using game::ArrangeMarriageChoice;
using game::ArrangeMarriageQueryDiagnostics;
using game::ArrangeMarriageValidationSample;
using game::ArmySnapshot;
using game::ArmyStrengthSnapshot;
using game::ArmyStrengthScopeRole;
using game::CombatArmyInputsSnapshot;
using game::CombatCandidateProvinceSnapshot;
using game::CombatCommanderContextSnapshot;
using game::CombatCommanderSnapshot;
using game::CombatEffectiveStatsSnapshot;
using game::CombatMaaTypeSnapshot;
using game::CombatObservationStatus;
using game::CombatRegimentSnapshot;
using game::CombatSimulationInputsRequest;
using game::CombatSimulationInputsSnapshot;
using game::OngoingCombatInputsSnapshot;
using game::DeclarableWarSnapshot;
using game::FixedPointValue;
using game::OneLifeSettlementSnapshot;
using game::PlayerWarSide;
using game::Snapshot;
using game::WarObjectiveProvinceState;
using game::WarTerminationOptionsSnapshot;
using game::WarTerminationTermsSnapshot;
using game::WarTerminationExitTermsSnapshot;
using game::PauseSubmitResult;
using game::ResumeSubmitResult;

// The generic registry hashes the process image once and passes an exact-match
// decision into the selected version adapter. False returns disabled bindings.
Bindings BindCurrentProcess(bool executable_matches) noexcept;

bool ReadSnapshot(const Bindings &bindings, Snapshot &output) noexcept;

// Reuses the exact-build generation-bearing active-CWar resolver for the
// pending-interaction read-only mailbox. The caller supplies the already
// captured application-main game_state; no command or effect is executed.
bool ResolvePendingCharacterInteractionActiveWarV1(
    const Bindings &bindings, void *game_state, std::int32_t war_id,
    void *&output) noexcept;

using game::ReadArmyStrengthsResult;

// Paused, read-only aggregate for every public CUnit currently published by
// the same snapshot as a player, active-war ally or active-war enemy. The
// adapter generation-resolves CUnit -> CArmy -> every CRegiment, validates the
// public-ID identity predicate, checked-sums all fields and never queues a
// command. That predicate is not combat activity or participation eligibility.
ReadArmyStrengthsResult ReadArmyStrengths(
    const Bindings &bindings,
    std::vector<ArmyStrengthSnapshot> &output) noexcept;

using game::ReadCombatSimulationInputsResult;

// Paused object-graph projection for one explicit hypothetical contact. The
// request supplies target/final-edge ProvinceIDs and two non-empty ArmyID
// partitions. The adapter revalidates one active-war coalition split in the
// same snapshot; it never depends on current routes, exports storage handles,
// applies combat transitions, advances date, or consumes CK3 RNG.
ReadCombatSimulationInputsResult ReadCombatSimulationInputs(
    const Bindings &bindings,
    const game::CombatSimulationInputsRequest &request,
    CombatSimulationInputsSnapshot &output) noexcept;

// pause-map is an idempotent action: it reports already_paused without adding
// a command, otherwise it submits the same 0x28-byte CPauseGameCommand shape
// used by CK3's own UI through the engine's locked command queue path.
PauseSubmitResult SubmitPauseMap(const Bindings &bindings) noexcept;

// resume-map is the inverse idempotent operation.  It is required for a
// freshly loaded headless map because changing the speed does not clear
// Jomini's paused bit.
ResumeSubmitResult SubmitResumeMap(const Bindings &bindings) noexcept;

// Fixed public speeds 1..5 deliberately map to separate advertised gameplay
// steps.  CK3's native CSetGameSpeedCommand payload is zero based (0..4).
bool SubmitSetSpeed(const Bindings &bindings, std::int32_t speed) noexcept;

using game::SelectEventOptionResult;

// Selects a zero-based native option on the same current local-player event
// returned in Snapshot. The public select-event-option-1..N step is translated
// to this zero-based payload at the protocol boundary. CK3's executor performs
// the same 0 <= index < option_count check before dispatching the effect.
SelectEventOptionResult
SubmitSelectEventOption(const Bindings &bindings,
                        std::int32_t option_index) noexcept;

using game::SaveCheckpointResult;
using game::SaveCheckpointStatus;

// Queues CK3's own CAutoSaveCommand with the fixed short save name
// `xar_checkpoint`. The result confirms queue submission, not asynchronous
// disk completion; the caller can correlate date_raw and the save name with
// the produced save file.
SaveCheckpointResult SubmitSaveCheckpoint(const Bindings &bindings) noexcept;

using game::PendingInteractionReply;
using game::ReplyPendingInteractionResult;
using game::AcknowledgePendingInteractionResult;

// Replies to the first locally addressed and natively actionable CK3 character
// interaction exposed by Snapshot. CPendingCharacterInteraction's component ID
// is the int32 payload consumed by CReplyCharacterInteractionCommand;
// accept/reject are native enum values 0/1.
ReplyPendingInteractionResult SubmitReplyToPendingInteraction(
    const Bindings &bindings, PendingInteractionReply reply) noexcept;

// Acknowledges one exact generation-bearing auto-accept notification. This is
// deliberately a fixed enum-4 action rather than a generic reply surface. It
// fresh-reads the paused snapshot, re-resolves the complete pending ID and
// played Character, re-runs the exact local-route predicate, revalidates
// +0x5C6, and never treats the enum-4 validator's early true as legality.
AcknowledgePendingInteractionResult SubmitAcknowledgePendingInteraction(
    const Bindings &bindings, std::int32_t pending_interaction_id) noexcept;

using game::RaiseTroopsResult;

// Raises the played character's troops at CK3's own default rally province.
// The native constructor owns an internal allocation, so the bridge validates,
// queues (which clones synchronously), and destroys the stack command in the
// same order as the original UI path.
RaiseTroopsResult SubmitRaiseTroopsDefault(const Bindings &bindings) noexcept;

using game::MoveArmyResult;

MoveArmyResult SubmitMoveArmy(const Bindings &bindings,
                              std::int32_t army_id,
                              std::int32_t province_id) noexcept;

using game::PreviewMoveArmyResult;
using game::PreviewMoveArmyStatus;
using game::RouteContactHorizonRequest;
using game::RouteContactHorizonSnapshot;
using game::RouteContactHorizonStatus;
using game::ActualContactScopeRequest;
using game::ActualContactScopeSnapshot;
using game::ActualContactScopeStatus;
using game::BattleControlRequest;
using game::BattleControlSnapshot;
using game::BattleControlSnapshotStatus;
using game::BattleTransitionRequest;
using game::BattleTransitionSnapshot;
using game::BattleTransitionSnapshotStatus;
using game::BattleTerminalTransitionRequestV1;
using game::BattleTerminalTransitionSnapshotV1;
using game::BattleTerminalTransitionStatusV1;
using game::BattleTerminalAiMembershipStatusV1;
using game::BattleReinforcementAssignmentRequest;
using game::BattleReinforcementAssignmentSnapshot;
using game::BattleReinforcementAssignmentStatus;

// Runs CK3's own route planner into a temporary MovePath and copies its
// resolved ProvinceIDs before destroying that path. This never applies the
// planned route and never queues a command.
PreviewMoveArmyResult PreviewMoveArmy(const Bindings &bindings,
                                      std::int32_t army_id,
                                      std::int32_t province_id) noexcept;

// Main-thread-only exact-build reader.  Production calls this exclusively
// through RouteContactHorizonMailboxContextV1; the direct entry point exists
// for the deterministic native fixture.  It builds CK3-owned MovePath state,
// copies only atomic public IDs/dates, and never queues a command.
RouteContactHorizonStatus ReadRouteContactHorizon(
    const Bindings &bindings, const RouteContactHorizonRequest &request,
    RouteContactHorizonSnapshot &output) noexcept;

// Main-thread-only mirror of 0x2208320/0x2209450.  It reads the current
// Province stored arrays twice and never calls any join/create mutator.
ActualContactScopeStatus ReadActualContactScope(
    const Bindings &bindings, const ActualContactScopeRequest &request,
    ActualContactScopeSnapshot &output) noexcept;

// Main-thread-only, paused exact-build projection of the live CCombat reached
// through one controllable public CUnit.  The implementation samples the
// complete retained-entry graph twice and calls only the two read-only native
// strength leaves; it never refreshes, advances, finalizes or mutates combat.
BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const Bindings &bindings, const BattleControlRequest &request,
    BattleControlSnapshot &output) noexcept;

// Main-thread-only, paused lifecycle query addressed directly by one positive
// full-generation CombatID. It samples the retained CCombat projection twice,
// calls no native function, and has no selected-Army or retreat-legality gate.
BattleTransitionSnapshotStatus ReadBattleTransitionSnapshot(
    const Bindings &bindings, const BattleTransitionRequest &request,
    BattleTransitionSnapshot &output) noexcept;

// Main-thread-only, paused composition of the passive terminal journal with
// the current full-generation Combat/Province/CUnit graph. It samples the
// complete semantic frame twice and never calls a finalizer, row writer,
// contact resolver, AI lifecycle function or combat constructor.
BattleTerminalTransitionStatusV1 ReadBattleTerminalTransitionV1(
    const Bindings &bindings, const Snapshot &same_frame_world,
    const BattleTerminalTransitionRequestV1 &request,
    BattleTerminalTransitionSnapshotV1 &output) noexcept;

// Main-thread-only, paused exact-build projection of one AI-managed CUnit's
// stored help signal, assignment target, committed route/ETA and present-time
// compatible combats. It never runs an AI update, contact resolver or combat
// mutator.
BattleReinforcementAssignmentStatus ReadBattleReinforcementAssignmentV1(
    const Bindings &bindings, const Snapshot &same_frame_world,
    const BattleReinforcementAssignmentRequest &request,
    BattleReinforcementAssignmentSnapshot &output) noexcept;

using game::DisbandArmyResult;

DisbandArmyResult SubmitDisbandArmy(const Bindings &bindings,
                                    std::int32_t army_id) noexcept;

using game::SplitArmyHalfResult;

// Resolves the public generation-bearing CUnit ID to its internal CArmyID,
// passes the current played CharacterID through CK3's complete Split Half
// validator, queues the 0x30-byte player command, then destroys the stack
// object after the queue wrapper has synchronously cloned it. Submission is
// not a claim that the next snapshot already contains the sibling CUnit.
SplitArmyHalfResult SubmitSplitArmyHalf(const Bindings &bindings,
                                        std::int32_t army_id) noexcept;

using game::MergeArmiesResult;

// Uses the original heap constructor and native range-copy helper to build a
// one-source CMergeUnitsCommand. Both IDs are public generation-bearing CUnit
// IDs; CK3's complete validator owns province/combat/movement/siege gates.
// Submission preserves destination identity but is not an immediate outcome
// claim: a later paused snapshot must prove that the source disappeared.
MergeArmiesResult SubmitMergeArmies(const Bindings &bindings,
                                    std::int32_t destination_army_id,
                                    std::int32_t source_army_id) noexcept;

using game::StartAssaultResult;
using game::StopAssaultResult;

// These commands contain only player kind, full-generation played
// CharacterID and full-generation SiegeID. Queue acceptance is a typed ACK;
// applied/complete remains a later paused-snapshot postcondition.
StartAssaultResult SubmitStartAssault(const Bindings &bindings,
                                      std::int32_t siege_id) noexcept;
StopAssaultResult SubmitStopAssault(const Bindings &bindings,
                                    std::int32_t siege_id) noexcept;

using game::ReadDeclarableWarsResult;

// Runs CK3's own CB evaluator against one explicit target. This is the cheap
// path for a planner that already knows a CharacterID. The global overload is
// intentionally separate because scanning every live Character is a much
// heavier strategic query and should not run on every heartbeat snapshot.
ReadDeclarableWarsResult ReadDeclarableWarsForTarget(
    const Bindings &bindings, std::int32_t target_character_id,
    std::vector<DeclarableWarSnapshot> &output) noexcept;

bool ReadDeclarableWars(
    const Bindings &bindings,
    std::vector<DeclarableWarSnapshot> &output) noexcept;

using game::DeclareWarResult;

// Re-runs native enumeration and requires an exact match of every choice
// field before constructing CSendCharacterInteractionCommand. Queue cloning
// is synchronous; both the copied command context and the original temporary
// context are destroyed after submission in CK3's native order.
DeclareWarResult SubmitDeclareWar(
    const Bindings &bindings,
    const DeclarableWarSnapshot &declaration) noexcept;

using game::ReadArrangeMarriageChoicesResult;

// Explicit strategic query; it is intentionally not part of the heartbeat
// snapshot. Every returned candidate has passed CK3's own arrange-marriage
// context refresh/finalize/validation chain for the currently played
// Character. Minors naturally produce a betrothal through the same native
// interaction.
ReadArrangeMarriageChoicesResult ReadArrangeMarriageChoices(
    const Bindings &bindings,
    std::vector<ArrangeMarriageChoice> &output,
    ArrangeMarriageQueryDiagnostics &diagnostics) noexcept;

using game::ArrangeMarriageResult;

// Rebuilds the context from both exact CharacterID handles and validates it
// again before sending CSendCharacterInteractionCommand. This first slice is
// deliberately the useful direct path (played Character <-> candidate), not
// the wider four-role courtier matchmaking surface.
ArrangeMarriageResult SubmitArrangeMarriage(
    const Bindings &bindings,
    const ArrangeMarriageChoice &choice) noexcept;

using game::EnforceDemandsResult;

// Builds the same victory interaction context as WarOverviewWindow's victory
// tab for one live CWar led by the played character, then sends the common
// native character-interaction command. The visual confirmation wrapper is
// intentionally not part of the gameplay command and is not needed in
// headless mode.
EnforceDemandsResult SubmitEnforceDemands(const Bindings &bindings,
                                          std::int32_t war_id) noexcept;

using game::ReadWarTerminationOptionsResult;

// Rebuilds all currently proven WarOverview result contexts for one exact
// WarID while paused, validates them through CK3's common interaction
// validator, then destroys every temporary context without queuing a command.
ReadWarTerminationOptionsResult ReadWarTerminationOptions(
    const Bindings &bindings, std::int32_t war_id,
    WarTerminationOptionsSnapshot &output) noexcept;

using game::ReadWarTerminationTermsResult;

// Reads the complete claim_cb claimant/target/claim-disposition slice without
// constructing or submitting a character-interaction command. Non-claim CBs
// return a typed unsupported result with only CB identity populated.
ReadWarTerminationTermsResult ReadWarTerminationTerms(
    const Bindings &bindings, std::int32_t war_id,
    WarTerminationTermsSnapshot &output) noexcept;

using game::ReadWarTerminationExitTermsResult;

// Complete claim_cb white-peace/attacker-defeat terms from the original
// loaded-effect dry-preview path. The query never queues a command or applies
// an effect and publishes only after same-frame before/after identity and
// resource checks match.
ReadWarTerminationExitTermsResult ReadWarTerminationExitTerms(
    const Bindings &bindings, std::int32_t war_id,
    WarTerminationExitTermsSnapshot &output) noexcept;

#if defined(XAR_CK3_WAR_EXIT_TERMS_OFFLINE_RE_TEST)
// Offline-only entry point for the exact-build loaded-effect fixtures.  The
// production entry point remains disabled until the native visitor/scope ABI
// that crashed at CK3 RVA 0x334C668 is closed and revalidated live.
ReadWarTerminationExitTermsResult
ReadWarTerminationExitTermsForOfflineReFixture(
    const Bindings &bindings, std::int32_t war_id,
    WarTerminationExitTermsSnapshot &output) noexcept;
#endif

// Error-only stage name from the immediately preceding exit-terms read on the
// current bridge thread.  Successful reads clear it.
std::string_view LastWarTerminationExitTermsUnavailableReason() noexcept;

using game::SurrenderWarResult;
using game::OfferWhitePeaceResult;

// Sends the played war leader's defeat result for one exact WarID. The native
// boolean is the absolute outcome (`true` attacker victory, `false` attacker
// defeat), so the submitted value depends on the player's physical war side.
// Queue submission is a typed ACK, not proof that the war already ended or
// that any still-unobserved terms were applied.
SurrenderWarResult SubmitSurrenderWar(const Bindings &bindings,
                                      std::int32_t war_id) noexcept;

// Builds the native special-interaction index 3 white-peace context for the
// played primary war leader, validates it, and submits only a typed queue ACK.
OfferWhitePeaceResult SubmitOfferWhitePeace(const Bindings &bindings,
                                            std::int32_t war_id) noexcept;

} // namespace xar::ck3_11906
