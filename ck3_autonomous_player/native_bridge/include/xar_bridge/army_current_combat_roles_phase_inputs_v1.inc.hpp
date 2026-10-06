#pragma once
// Included inside xar::game after the post-admission and current31 DTOs.
struct ArmyCurrentCombatRawReferenceV1 {
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  friend bool operator==(const ArmyCurrentCombatRawReferenceV1 &, const ArmyCurrentCombatRawReferenceV1 &) = default;
};
struct ArmyCurrentCombatRawRosterV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  std::optional<std::string> data_identity;
  std::optional<std::uint32_t> capacity_raw_u32;
  std::optional<std::int32_t> count_raw_i32;
  std::vector<ArmyCurrentCombatRawReferenceV1> references;
  bool references_ready = false;
  friend bool operator==(const ArmyCurrentCombatRawRosterV1 &, const ArmyCurrentCombatRawRosterV1 &) = default;
};
struct ArmyCurrentCombatManagerInputsV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  std::optional<std::string> game_state_identity, domain_identity, manager_identity, secondary_vtable_identity;
  std::optional<bool> secondary_vtable_matched;
  ArmyCurrentCombatRawRosterV1 roster{};
  bool manager_inputs_ready = false;
  friend bool operator==(const ArmyCurrentCombatManagerInputsV1 &, const ArmyCurrentCombatManagerInputsV1 &) = default;
};
struct ArmyCurrentCombatSideInputsV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  std::optional<std::string> parent_identity;
  std::optional<bool> parent_matches_selected_combat;
  ArmyCurrentCombatRawRosterV1 armies{};
  std::vector<std::int32_t> matching_army_indices;
  bool matching_membership_ready = false;
  std::optional<std::uint32_t> primary_70_raw_u32, commander_74_raw_u32;
  std::optional<bool> owner_matches_primary;
  bool side_inputs_ready = false;
  friend bool operator==(const ArmyCurrentCombatSideInputsV1 &, const ArmyCurrentCombatSideInputsV1 &) = default;
};
struct ArmyCurrentCombatRolesPhaseOccurrenceV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 original_army_resolution{};
  bool same_query_army_selection_matched = false;
  std::optional<std::uint32_t> actual_army_10_raw_u32, army_128_raw_u32;
  ArmyFlag31SelectionV1 combat_resolution{};
  std::optional<std::uint32_t> selected_combat_magic_0c_raw_u32, selected_combat_full_id_08_raw_u32;
  std::optional<bool> source_active_combat;
  bool active_combat_inputs_ready = false;
  std::vector<std::int32_t> manager_match_indices;
  bool combat_manager_membership_ready = false;
  std::optional<std::uint32_t> army_124_raw_u32, unit_owner_174_raw_u32;
  ArmyFlag31SelectionV1 unit_resolution{}, character_resolution{};
  std::optional<std::uint32_t> selected_character_18_raw_u32;
  bool owner_inputs_ready = false;
  ArmyCurrentCombatSideInputsV1 attacker_side{}, defender_side{};
  std::optional<std::int32_t> phase_6b0_raw_i32, day_6b4_raw_i32, forced_winner_700_raw_i32;
  std::optional<std::uint8_t> finalized_704_raw_u8, processing_705_raw_u8;
  bool phase_inputs_ready = false, threshold_required = false;
  std::optional<std::int32_t> maneuver_threshold_raw_i32;
  bool threshold_inputs_ready = false, current_combat_roles_phase_inputs_ready = false;
  friend bool operator==(const ArmyCurrentCombatRolesPhaseOccurrenceV1 &, const ArmyCurrentCombatRolesPhaseOccurrenceV1 &) = default;
};
struct ArmyCurrentCombatRolesPhaseInputsV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  std::int32_t schema_version = 1;
  std::string source = "native_current_army_combat_roles_phase_inputs";
  std::string stage = "observed_current_army_combat_roles_phase_inputs";
  std::optional<bool> original_army_manager_loaded;
  std::optional<std::string> original_army_manager_identity;
  ArmyDailyAssaultRawReferencesV1 original_roster{};
  ArmyCurrentCombatManagerInputsV1 combat_manager{};
  std::vector<ArmyCurrentCombatRolesPhaseOccurrenceV1> occurrences;
  bool raw_roster_references_ready = false, original_army_selections_ready = false;
  bool current_combat_roles_phase_inputs_ready = false, actual_manager_invocation_observed = false;
  bool future_phase_transition_ready = false, full_callback_ready = false, full_battle_ready = false;
  std::uint32_t native_calls_executed = 0, native_writes_executed = 0;
  friend bool operator==(const ArmyCurrentCombatRolesPhaseInputsV1 &, const ArmyCurrentCombatRolesPhaseInputsV1 &) = default;
};
