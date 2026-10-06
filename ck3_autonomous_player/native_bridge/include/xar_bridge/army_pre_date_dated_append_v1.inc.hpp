#pragma once
// Included inside xar::game after the existing daily-assault operand DTO.
struct ArmyPreDateDatedIdListV1 {
  bool ready = false;
  std::string unavailable_reason = "not_demanded";
  std::string source = "not_demanded";
  std::optional<std::int32_t> count_raw_i32;
  std::optional<std::vector<std::optional<std::uint32_t>>> ordered_ids_u32;
  friend bool operator==(const ArmyPreDateDatedIdListV1 &, const ArmyPreDateDatedIdListV1 &) = default;
};
struct ArmyPreDateDatedEntryV1 {
  std::int32_t native_index = 0;
  std::optional<std::string> pointer_identity;
  std::optional<bool> pointer_present;
  std::optional<std::int32_t> date_low_raw_i32;
  friend bool operator==(const ArmyPreDateDatedEntryV1 &, const ArmyPreDateDatedEntryV1 &) = default;
};
struct ArmyPreDateDatedOccurrenceV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::string unavailable_reason = "not_demanded";
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> original_request_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 army_resolution;
  std::optional<std::uint32_t> combat_request_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 combat_resolution;
  std::optional<std::uint32_t> combat_magic_0c_raw_u32;
  std::optional<std::int32_t> army_date_count_5c_raw_i32;
  std::optional<std::string> date_array_identity;
  std::optional<bool> date_array_present;
  std::vector<ArmyPreDateDatedEntryV1> date_entries;
  bool date_scan_ready = false;
  friend bool operator==(const ArmyPreDateDatedOccurrenceV1 &, const ArmyPreDateDatedOccurrenceV1 &) = default;
};
struct ArmyPreDateDatedAppendInputsV1 {
  std::int32_t schema_version = 1;
  std::string source = "native_current_pre_date_dated_append_inputs";
  std::string stage = "observed_current_2a9a360_tomorrow_operands";
  std::string status = "unavailable";
  bool ready = false;
  std::string unavailable_reason = "not_demanded";
  bool manager_loaded = false;
  std::optional<std::string> manager_identity;
  std::string clock_source = "unavailable";
  bool clock_ready = false;
  std::optional<std::int32_t> current_date_raw_i32;
  std::optional<std::int32_t> tomorrow_date_low_i32;
  ArmyPreDateDatedIdListV1 source_c8;
  ArmyPreDateDatedIdListV1 initial_158;
  std::vector<ArmyPreDateDatedOccurrenceV1> occurrences;
  friend bool operator==(const ArmyPreDateDatedAppendInputsV1 &, const ArmyPreDateDatedAppendInputsV1 &) = default;
};
