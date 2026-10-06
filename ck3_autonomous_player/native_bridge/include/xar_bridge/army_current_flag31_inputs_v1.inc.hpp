#pragma once
#include "xar_bridge/army_current_rule24_source_pins_v1.inc.hpp"
// Included inside xar::game after the post-admission refresh DTO.
struct ArmyFlag31SelectionV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::optional<bool> registry_loaded, used_fallback;
  std::optional<std::uint32_t> requested_full_id_u32, registry_capacity_u32, registry_index_u32, indexed_full_id_u32;
  std::optional<std::string> indexed_identity, selection, object_identity;
  bool selected_object_ready = false;
  friend bool operator==(const ArmyFlag31SelectionV1 &, const ArmyFlag31SelectionV1 &) = default;
};
struct ArmyFlag31OccurrenceV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t native_index = 0;
  std::optional<std::uint32_t> raw_full_id_u32;
  ArmyDailyAssaultOperandResolutionV1 original_army_resolution{};
  bool same_query_army_selection_matched = false;
  std::optional<std::uint8_t> actual_army_31_raw_u8, army_1d4_raw_u8;
  std::optional<std::uint32_t> army_128_raw_u32;
  ArmyFlag31SelectionV1 combat_resolution{};
  std::optional<std::uint32_t> selected_combat_magic_0c_raw_u32, selected_combat_full_id_08_raw_u32;
  std::optional<bool> source_active_combat;
  bool active_combat_inputs_ready = false;
  std::optional<std::uint32_t> army_124_raw_u32, unit_owner_174_raw_u32;
  ArmyFlag31SelectionV1 unit_resolution{}, character_resolution{};
  std::optional<std::uint32_t> selected_character_18_raw_u32;
  std::int32_t rule_selector_i32 = 24;
  std::uint32_t rule_inline_offset_u32 = 0x1380;
  std::optional<std::string> rule_provider_identity, rule_array_identity, inline_rule_identity;
  std::optional<std::int32_t> root_kind, root_subtype;
  std::optional<std::uint64_t> root_payload_u64;
  std::string root_construction = "not_demanded";
  bool native_rule_evaluation_returned = false;
  std::optional<bool> native_current_rule24_passed;
  std::optional<std::uint8_t> derived_current_31_raw_u8;
  bool current_flag31_inputs_ready = false;
  std::optional<ArmyCurrentRule24SourcePinsV1> rule24_source_pins_v1;
  friend bool operator==(const ArmyFlag31OccurrenceV1 &, const ArmyFlag31OccurrenceV1 &) = default;
};
struct ArmyCurrentFlag31InputsV1 {
  std::string status = "unavailable", unavailable_reason = "not_demanded";
  bool ready = false;
  std::int32_t schema_version = 1;
  std::string source = "native_current_army_flag31_inputs";
  std::string stage = "observed_current_army_flag31_inputs";
  std::optional<bool> manager_loaded;
  std::optional<std::string> manager_identity;
  ArmyDailyAssaultRawReferencesV1 original_roster{};
  std::vector<ArmyFlag31OccurrenceV1> occurrences;
  bool raw_roster_references_ready = false, original_army_selections_ready = false, current_flag31_inputs_ready = false;
  bool actual_refresh_execution_ready = false, actual_next_occurrence_ready = false;
  bool full_callback_ready = false, full_daily_assault_ready = false, full_monthly_ready = false;
  friend bool operator==(const ArmyCurrentFlag31InputsV1 &, const ArmyCurrentFlag31InputsV1 &) = default;
};
