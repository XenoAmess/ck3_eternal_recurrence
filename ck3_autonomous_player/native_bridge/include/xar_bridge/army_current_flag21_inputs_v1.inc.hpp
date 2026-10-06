#pragma once
// Included inside xar::game after the post-admission refresh DTO.
struct ArmyFlag21SelectionV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::optional<bool> registry_loaded, used_fallback;
  std::optional<std::uint32_t> requested_full_id_u32, registry_capacity_u32, registry_index_u32, indexed_full_id_u32;
  std::optional<std::string> indexed_identity, selection, object_identity;
  bool selected_object_ready = false;
  friend bool operator==(const ArmyFlag21SelectionV1 &, const ArmyFlag21SelectionV1 &) = default;
};
struct ArmyFlag21OccurrenceV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 original_army_resolution{};
  bool same_query_army_selection_matched = false;
  std::optional<std::uint8_t> actual_army_21_raw_u8, army_1ec_raw_u8;
  std::optional<std::int64_t> army_1f0_raw_i64;
  std::optional<std::uint32_t> army_124_raw_u32, unit_owner_174_raw_u32;
  ArmyFlag21SelectionV1 unit_resolution{}, character_resolution{};
  std::optional<bool> owner_character_carrier_1c0_present;
  std::optional<std::string> owner_character_carrier_identity, header_selection, header_identity;
  std::optional<std::int32_t> header_0c_raw_i32;
  bool owner_header_inputs_ready = false, native_shared_tail_returned = false;
  std::optional<std::uint8_t> native_shared_tail_21_raw_u8, derived_current_21_raw_u8;
  bool current_flag21_inputs_ready = false;
  friend bool operator==(const ArmyFlag21OccurrenceV1 &, const ArmyFlag21OccurrenceV1 &) = default;
};
struct ArmyCurrentFlag21InputsV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t schema_version = 1;
  std::string source = "native_current_army_flag21_inputs";
  std::string stage = "observed_current_army_flag21_inputs";
  std::optional<bool> manager_loaded;
  std::optional<std::string> manager_identity;
  ArmyDailyAssaultRawReferencesV1 original_roster{};
  std::vector<ArmyFlag21OccurrenceV1> occurrences;
  bool raw_roster_references_ready = false, original_army_selections_ready = false, current_flag21_inputs_ready = false;
  bool actual_refresh_execution_ready = false, actual_next_occurrence_ready = false;
  bool full_callback_ready = false, full_daily_assault_ready = false, full_monthly_ready = false;
  friend bool operator==(const ArmyCurrentFlag21InputsV1 &, const ArmyCurrentFlag21InputsV1 &) = default;
};
