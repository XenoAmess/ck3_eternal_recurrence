#pragma once
// Included inside xar::game after the post-admission refresh DTOs.
struct ArmySelectedHolderOperandSelectionV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::optional<bool> registry_loaded, used_fallback;
  std::optional<std::uint32_t> requested_full_id_u32, registry_capacity_u32, registry_index_u32;
  std::optional<std::uint32_t> indexed_full_id_u32;
  std::optional<std::string> indexed_identity, object_identity;
  std::string selection = "not_demanded";
  bool selected_object_ready = false;
  friend bool operator==(const ArmySelectedHolderOperandSelectionV1 &, const ArmySelectedHolderOperandSelectionV1 &) = default;
};
struct ArmySelectedHolderUnitSelectionV1 {
  std::int32_t native_index = 0;
  std::string purpose;
  std::optional<std::uint32_t> army_124_raw_u32;
  ArmySelectedHolderOperandSelectionV1 unit_resolution{};
  std::optional<bool> province_used_fallback;
  std::optional<std::string> province_identity;
  std::optional<std::uint32_t> province_magic_85c_raw_u32;
  friend bool operator==(const ArmySelectedHolderUnitSelectionV1 &, const ArmySelectedHolderUnitSelectionV1 &) = default;
};
struct ArmySelectedTitleHolderOwnerRelationOccurrenceV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 original_army_resolution{};
  bool same_query_army_selection_matched = false;
  std::vector<ArmySelectedHolderUnitSelectionV1> unit_selections;
  std::optional<std::uint32_t> province_title_738_raw_u32, title_holder_128_raw_u32;
  ArmySelectedHolderOperandSelectionV1 title_resolution{}, parent_title_resolution{};
  std::optional<std::uint32_t> title_definition_64_raw_u32, parent_title_e8_raw_u32, parent_holder_128_raw_u32;
  std::optional<std::uint32_t> holder_requested_full_id_u32, holder_character_full_id_u32;
  ArmySelectedHolderOperandSelectionV1 holder_character_resolution{};
  std::optional<std::uint32_t> selected_unit_owner_174_raw_u32;
  std::optional<bool> holder_owner_equal;
  bool native_relation_demanded = false, native_relation_returned = false;
  std::optional<bool> native_holder_owner_relation;
  std::optional<std::uint8_t> derived_current_shared_tail_raw_u8;
  bool current_shared_tail_inputs_ready = false;
  friend bool operator==(const ArmySelectedTitleHolderOwnerRelationOccurrenceV1 &, const ArmySelectedTitleHolderOwnerRelationOccurrenceV1 &) = default;
};
struct ArmyCurrentSelectedTitleHolderOwnerRelationV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t schema_version = 1;
  std::string source = "native_selected_title_holder_owner_relation_28b2820";
  std::string stage = "observed_current_selected_title_holder_owner_relation_inputs";
  std::string context_basis = "same_query_selected_title_holder_and_unit_owner";
  std::optional<bool> manager_loaded;
  std::optional<std::string> manager_identity;
  ArmyDailyAssaultRawReferencesV1 original_roster{};
  std::vector<ArmySelectedTitleHolderOwnerRelationOccurrenceV1> occurrences;
  bool raw_roster_references_ready = false, original_army_selections_ready = false;
  bool current_shared_tail_inputs_ready = false;
  bool actual_refresh_execution_ready = false, actual_next_occurrence_ready = false;
  bool changed_selection_context_ready = false, changed_relationship_context_ready = false;
  bool full_callback_ready = false, full_daily_assault_ready = false, full_monthly_ready = false;
  friend bool operator==(const ArmyCurrentSelectedTitleHolderOwnerRelationV1 &, const ArmyCurrentSelectedTitleHolderOwnerRelationV1 &) = default;
};
