#pragma once
// Included inside xar::game after the existing post-admission refresh DTO.
struct ArmyFlag20OccurrenceV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 original_army_resolution{};
  bool same_query_army_selection_matched = false;
  std::optional<std::uint8_t> actual_army_20_raw_u8, army_1d4_raw_u8;
  bool native_getter_returned = false;
  std::optional<std::uint8_t> native_getter_20_raw_u8, derived_current_20_raw_u8;
  bool current_flag20_inputs_ready = false;
  friend bool operator==(const ArmyFlag20OccurrenceV1 &, const ArmyFlag20OccurrenceV1 &) = default;
};
struct ArmyCurrentFlag20InputsV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t schema_version = 1;
  std::string source = "native_current_army_flag20_inputs";
  std::string stage = "observed_current_army_flag20_inputs";
  std::optional<bool> manager_loaded;
  std::optional<std::string> manager_identity;
  ArmyDailyAssaultRawReferencesV1 original_roster{};
  std::vector<ArmyFlag20OccurrenceV1> occurrences;
  bool raw_roster_references_ready = false, original_army_selections_ready = false;
  bool current_flag20_inputs_ready = false;
  bool actual_refresh_execution_ready = false, actual_next_occurrence_ready = false;
  bool full_callback_ready = false, full_daily_assault_ready = false, full_monthly_ready = false;
  friend bool operator==(const ArmyCurrentFlag20InputsV1 &, const ArmyCurrentFlag20InputsV1 &) = default;
};
