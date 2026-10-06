#pragma once
// Included inside xar::game after the existing roster, pending and dated DTOs.
struct ArmyPreDateCharacterPredicateV1 {
  bool demanded = false;
  bool observable = false;
  std::optional<bool> verdict;
  std::string unavailable_reason = "not_demanded";
  friend bool operator==(const ArmyPreDateCharacterPredicateV1 &, const ArmyPreDateCharacterPredicateV1 &) = default;
};
struct ArmyPreDateCharacterOccurrenceV1 {
  std::string status = "unavailable";
  bool ready = false;
  std::string unavailable_reason = "not_demanded";
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> original_request_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 army_resolution{};
  std::optional<bool> earlier_skip;
  std::string earlier_skip_source = "unavailable";
  std::optional<std::uint32_t> army_character_120_raw_u32;
  ArmyDailyAssaultOperandResolutionV1 character_resolution{};
  std::optional<std::uint32_t> army_unit_124_raw_u32;
  ArmyDailyAssaultOperandResolutionV1 unit_resolution{};
  std::optional<std::uint32_t> unit_owner_174_raw_u32;
  std::optional<std::uint32_t> character_magic_1c_raw_u32;
  std::optional<std::uint32_t> character_full_id_18_raw_u32;
  std::optional<bool> character_death_1d0_present;
  std::optional<bool> character_state_1c8_present, character_state_1c0_present, character_state_1b8_present;
  ArmyPreDateCharacterPredicateV1 membership{}, basic_rule{}, availability{};
  std::optional<std::uint32_t> failure_append_army_10_raw_u32;
  friend bool operator==(const ArmyPreDateCharacterOccurrenceV1 &, const ArmyPreDateCharacterOccurrenceV1 &) = default;
};
struct ArmyCurrentPreDateCharacterPrefixInputsV1 {
  std::int32_t schema_version = 1;
  std::string source = "native_current_pre_date_character_prefix_inputs";
  std::string stage = "observed_current_conditional_2a99f72_character_prefix";
  std::string status = "unavailable";
  bool ready = false;
  std::string unavailable_reason = "not_demanded";
  bool manager_loaded = false;
  std::optional<std::string> manager_identity;
  ArmyDailyAssaultRawReferencesV1 original_roster{};
  ArmyPreDateDatedIdListV1 initial_80{};
  std::vector<ArmyPreDateCharacterOccurrenceV1> occurrences;
  friend bool operator==(const ArmyCurrentPreDateCharacterPrefixInputsV1 &, const ArmyCurrentPreDateCharacterPrefixInputsV1 &) = default;
};
