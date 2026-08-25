#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

inline constexpr std::string_view kCombatPhaseManifestSha256 =
    "91EDCEEDC634C5ACDCFAC8B02F53FE74C4E7A2E1768AAFC12CD0D976E874F2AC";
inline constexpr std::string_view kCombatPhaseRequiredRefsSha256 =
    "2B5E8445EFD14DC65D8BA4046242BBC37A0226C2BCD971D805D9A6F0064A1DD0";
inline constexpr std::int32_t kCombatPhaseRequiredRefCount = 132;

enum class CombatPhaseStateValueKind {
  boolean,
  signed_int32,
  signed_int64,
  signed_q100000,
  full_id,
  full_id_array,
  string,
  not_applicable,
};

struct CombatPhaseStateRefV3TestOnly {
  std::string path;
  CombatPhaseStateValueKind value_kind =
      CombatPhaseStateValueKind::not_applicable;
  bool boolean_value = false;
  std::int64_t signed_value = 0;
  std::vector<std::int32_t> id_values;
  std::string string_value;
};

struct CombatPhaseCharacterV3TestOnly {
  std::int32_t character_id = -1;
  std::int32_t source_army_id = -1;
  std::int32_t source_regiment_id = -1;
  std::string encounter_role;
  std::vector<std::string> phase_roles;
  std::vector<CombatPhaseStateRefV3TestOnly> state_refs;
};

struct CombatPhaseArmyV3TestOnly {
  std::int32_t army_id = -1;
  std::string encounter_role;
  std::vector<CombatPhaseStateRefV3TestOnly> state_refs;
};

struct CombatPhaseSideV3TestOnly {
  std::int32_t side_index = -1;
  std::string encounter_role;
  std::vector<std::int32_t> ordered_army_ids;
  std::vector<std::int32_t> ordered_character_ids;
  std::int32_t primary_participant_character_id = -1;
  std::int32_t primary_source_army_id = -1;
  std::string primary_selection_policy =
      "first_inserted_army_owner_with_native_preservation";
  std::int32_t side_strength_raw = 0;
  std::int64_t side_army_size_raw = 0;
  std::vector<CombatPhaseStateRefV3TestOnly> state_refs;
};

struct CombatAdvantageSupplyInputV3TestOnly {
  std::string selected_key;
  std::string selected_effect_identity;
  std::int32_t selected_effect_points = 0;
  std::int64_t eligible_soldiers_total = 0;
  std::int64_t eligible_soldiers_supplied = 0;
  std::int64_t eligible_soldiers_running_low = 0;
  std::int64_t eligible_soldiers_starving = 0;
};

struct CombatAdvantageSideInputV3TestOnly {
  std::string side;
  std::int32_t primary_army_id = -1;
  std::vector<std::int32_t> ordered_army_ids;
  CombatAdvantageSupplyInputV3TestOnly supply;
  std::int32_t primary_army_gathering_raw = 0;
  std::int32_t owner_character_id = -1;
  std::int32_t owner_debt_selector_raw = 0;
  bool treasury_debt_selector_observable = false;
  std::int32_t treasury_debt_selector_raw = 0;
};

struct CombatAdvantageConstructorSourceV3TestOnly {
  std::int32_t stage_order = -1;
  std::int32_t append_order = -1;
  std::string stage;
  std::string side;
  bool selected = false;
  bool applied = false;
  std::string source_key;
  std::int32_t effect_advantage_points = 0;
  std::int64_t scale_raw = 100'000;
  std::int64_t signed_contribution_raw = 0;
  std::int64_t accumulator_before_raw = 0;
  std::int64_t accumulator_after_raw = 0;
  std::string skip_reason;
};

struct CombatResolvedDynamicSideV3TestOnly {
  std::string side;
  bool battle_commander_selected = false;
  std::int32_t battle_commander_character_id = -1;
  std::int32_t primary_army_gathering_raw = 0;
  std::int32_t relation_kind_raw = 0;
  std::int32_t roll_points = 0;
  std::int64_t roll_raw = 0;
  std::int64_t target_conditionals_residual_raw = 0;
  std::int64_t commander_dynamic_raw = 0;
  std::int64_t side_dynamic_raw = 0;
  std::int64_t side_total_raw = 0;
  std::int64_t contribution_to_resolved_raw = 0;
};

struct CombatResolvedDynamicV3TestOnly {
  std::vector<CombatResolvedDynamicSideV3TestOnly> sides;
  std::int64_t side_0_dynamic_raw = 0;
  std::int64_t side_1_dynamic_raw = 0;
  std::int64_t resolved_advantage_at_zero_roll_raw = 0;
  std::int64_t original_total_helper_raw = 0;
  bool original_total_helper_match = false;
};

struct CombatAdvantageModelV3TestOnly {
  bool available = false;
  std::string observation_origin = "native_exact_build_test_only";
  std::vector<CombatAdvantageSideInputV3TestOnly> side_inputs;
  std::vector<CombatAdvantageConstructorSourceV3TestOnly> constructor_sources;
  std::int64_t base_static_accumulator_raw = 0;
  CombatResolvedDynamicV3TestOnly resolved_dynamic;
  std::string unavailable_reason;
};

struct CombatPhaseInputsV3TestOnly {
  bool available = false;
  std::vector<CombatPhaseCharacterV3TestOnly> characters;
  std::vector<CombatPhaseArmyV3TestOnly> armies;
  std::vector<CombatPhaseSideV3TestOnly> sides;
  std::vector<CombatPhaseStateRefV3TestOnly> global_state_refs;
  CombatAdvantageModelV3TestOnly advantage_model;
  std::string unavailable_reason;
};

// Serializes only the v3 phase-event fragment. Production bridge composition,
// capability advertisement and step dispatch remain deliberately absent.
std::string SerializeCombatPhaseInputsV3TestOnly(
    const CombatPhaseInputsV3TestOnly &inputs);

} // namespace xar::game
