#pragma once
// Included inside xar::game after the existing post-admission refresh DTO.
struct ArmyCondition30UnitResolutionV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::optional<std::uint32_t> requested_full_id_u32, registry_capacity_u32, registry_index_u32;
  std::optional<std::uint32_t> indexed_full_id_u32;
  std::optional<bool> registry_loaded, used_fallback;
  std::optional<std::string> indexed_identity, selection, object_identity;
  bool selected_object_ready = false;
  friend bool operator==(const ArmyCondition30UnitResolutionV1 &, const ArmyCondition30UnitResolutionV1 &) = default;
};
struct ArmyCondition30OccurrenceV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 original_army_resolution{};
  bool same_query_army_selection_matched = false;
  std::optional<std::uint8_t> actual_army_30_raw_u8, army_1d4_raw_u8;
  std::optional<std::uint32_t> army_124_raw_u32, unit_owner_174_raw_u32;
  ArmyCondition30UnitResolutionV1 unit_resolution{};
  std::optional<std::string> condition_owner_identity, inline_condition_identity;
  std::optional<std::uint32_t> root_kind, root_subtype;
  std::optional<std::uint64_t> root_payload_u64;
  std::optional<std::string> root_construction;
  std::optional<bool> native_current_condition_passed;
  std::optional<std::uint8_t> derived_current_30_raw_u8;
  bool current_condition_30_inputs_ready = false;
  friend bool operator==(const ArmyCondition30OccurrenceV1 &, const ArmyCondition30OccurrenceV1 &) = default;
};
struct ArmyCurrentCondition30InputsV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t schema_version = 1;
  std::string source = "native_current_army_condition30_inputs";
  std::string stage = "observed_current_army_condition30_inputs";
  std::optional<bool> manager_loaded;
  std::optional<std::string> manager_identity;
  ArmyDailyAssaultRawReferencesV1 original_roster{};
  std::vector<ArmyCondition30OccurrenceV1> occurrences;
  bool raw_roster_references_ready = false, original_army_selections_ready = false;
  bool current_condition_30_inputs_ready = false;
  bool actual_refresh_execution_ready = false, actual_next_occurrence_ready = false;
  bool full_callback_ready = false, full_daily_assault_ready = false, full_monthly_ready = false;
  friend bool operator==(const ArmyCurrentCondition30InputsV1 &, const ArmyCurrentCondition30InputsV1 &) = default;
};
