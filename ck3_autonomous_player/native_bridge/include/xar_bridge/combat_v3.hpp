#pragma once

#include "xar_bridge/combat_v3_test_only.hpp"
#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_11906 {

struct Bindings;

inline constexpr std::string_view kCombatPhaseInputsV3Capability =
    "game.command.query-combat-simulation-inputs-v3-N";
inline constexpr std::string_view kCombatPhaseInputsV3StepPrefix =
    "query-combat-simulation-inputs-v3-";
inline constexpr std::int32_t kCombatPhaseNativeLeafRefCount = 81;
inline constexpr std::int32_t kCombatPhaseOfflineRefCount = 51;

} // namespace xar::ck3_11906

namespace xar::game {

struct NamedBoolV3 {
  std::string key;
  bool value = false;
};

struct NamedSignedV3 {
  std::string key;
  std::int64_t value = 0;
};

struct OptionalFullIdV3 {
  bool present = false;
  std::int32_t value = -1;
};

struct CombatPhaseCharacterV3 {
  std::int32_t character_id = -1;
  std::int32_t source_army_id = -1;
  std::int32_t source_regiment_id = -1;
  std::string encounter_role;
  std::vector<std::string> phase_roles;

  bool alive = false;
  bool is_ai = true;
  std::int32_t martial = 0;
  std::int32_t learning = 0;
  std::int32_t prowess = 0;

  // Exact stable-key membership. The list is a fixed contract set and is
  // serialized in source-key order; missing keys never mean false.
  std::vector<NamedBoolV3> traits_or_groups;
  std::int64_t wounded_rank_raw = 0;
  std::int64_t fragile_bones_rank_raw = 0;
  std::int64_t fragile_bones_xp_raw = 0;
  std::int64_t lifestyle_blademaster_xp_raw = 0;
  std::int64_t tourney_bow_xp_raw = 0;
  std::int64_t tourney_foot_xp_raw = 0;
  std::int64_t tourney_horse_xp_raw = 0;

  OptionalFullIdV3 house;
  OptionalFullIdV3 liege;
  OptionalFullIdV3 liege_house;
  OptionalFullIdV3 employer;
  OptionalFullIdV3 dynasty;
  bool warfare_legacy_3 = false;
  bool stalwart_leader = false;

  OptionalFullIdV3 culture;
  OptionalFullIdV3 faith;
  OptionalFullIdV3 religion;
  bool heritage_north_germanic = false;
  bool knights_slightly_more_prone_to_injury = false;
  bool death_is_glory = false;
  bool tenet_warmonger = false;
  bool germanic_religion = false;
  bool blademaster_traits_more_common = false;
  std::vector<NamedBoolV3> innovations;
  std::vector<NamedBoolV3> traditions;
  std::vector<NamedBoolV3> culture_parameters;

  bool is_acclaimed = false;
  bool can_be_acclaimed = false;
  OptionalFullIdV3 accolade;
  bool accolade_has_men_at_arms_category = false;
  std::vector<NamedBoolV3> accolade_parameters;

  bool conqueror_variable_present = false;
  std::vector<NamedBoolV3> attribute_unlock_variables;
  OptionalFullIdV3 hold_court_8050_knight;
  OptionalFullIdV3 employer_hold_court_8050_promise;
  std::int64_t liege_accolade_progress_raw = 0;
  bool ai_extreme_conqueror_modifier = false;
  bool garuda_court_position = false;
  bool government_is_nomadic = false;
};

struct CombatPhaseArmyV3 {
  std::int32_t army_id = -1;
  std::int32_t native_carmy_id = -1;
  std::string encounter_role;
  std::int64_t maa_regiment_count_raw = 0;
  std::vector<NamedSignedV3> maa_counts_raw;
};

struct CombatPhaseParticipantFaithV3 {
  std::int32_t source_army_id = -1;
  std::int32_t owner_character_id = -1;
  std::int32_t faith_id = -1;
};

struct CombatPhaseCandidateSourceRowV3 {
  std::string role;
  std::int32_t source_army_id = -1;
  // Commander rows use the legal null sentinel; knight rows always carry the
  // generation-valid CRegimentID read from the native CCombatSide source row.
  std::int32_t source_regiment_id = -1;
  std::int32_t character_id = -1;

  friend bool operator==(const CombatPhaseCandidateSourceRowV3 &,
                         const CombatPhaseCandidateSourceRowV3 &) = default;
};

struct CombatPhaseCandidateSourceProofV3 {
  std::string policy =
      "ccombat_side_commanders_then_knights_native_source_equivalence_v1";
  bool source_vector_equivalence = false;
  std::string sequence_sha256;
  std::vector<CombatPhaseCandidateSourceRowV3> ordered_sources;
};

struct CombatPhaseSideV3 {
  std::int32_t side_index = -1;
  std::string encounter_role;
  std::vector<std::int32_t> ordered_army_ids;
  std::vector<std::int32_t> ordered_character_ids;
  std::vector<std::int32_t> ordered_commander_ids;
  std::vector<std::int32_t> ordered_knight_ids;
  std::int32_t primary_participant_character_id = -1;
  std::int32_t primary_source_army_id = -1;
  std::int32_t commander_character_id = -1;
  std::int32_t side_strength_raw = 0;
  std::int64_t side_army_size_raw = 0;
  std::vector<CombatPhaseParticipantFaithV3> participants;
  CombatPhaseCandidateSourceProofV3 candidate_source_proof;
};

struct CombatPhaseFaithHostilityV3 {
  std::int32_t root_character_id = -1;
  std::int32_t enemy_side_index = -1;
  std::int32_t enemy_owner_character_id = -1;
  std::int32_t enemy_faith_id = -1;
  std::int32_t root_faith_id = -1;
  std::int32_t hostility_level_raw = 0;
};

struct CombatPhaseInputsV3 {
  bool available = false;
  std::vector<CombatPhaseCharacterV3> characters;
  std::vector<CombatPhaseArmyV3> armies;
  std::vector<CombatPhaseSideV3> sides;
  std::vector<CombatPhaseFaithHostilityV3> faith_hostility;
  bool easy_difficulty = false;
  bool very_easy_difficulty = false;
  CombatAdvantageModelV3TestOnly advantage_model;
  std::string unavailable_reason;
};

enum class ReadCombatSimulationInputsV3Result {
  available,
  requires_paused,
  no_played_character,
  invalid_arguments,
  target_province_not_found,
  army_not_in_scope,
  invalid_encounter,
  base_inputs_unavailable,
  phase_inputs_unavailable,
  unavailable,
};

struct CombatSimulationInputsV3Snapshot {
  CombatSimulationInputsSnapshot base_inputs;
  CombatPhaseInputsV3 phase_event_inputs;
};

} // namespace xar::game

namespace xar::ck3_11906 {

using game::CombatPhaseArmyV3;
using game::CombatPhaseCandidateSourceProofV3;
using game::CombatPhaseCandidateSourceRowV3;
using game::CombatPhaseCharacterV3;
using game::CombatPhaseFaithHostilityV3;
using game::CombatPhaseInputsV3;
using game::CombatPhaseParticipantFaithV3;
using game::CombatPhaseSideV3;
using game::CombatSimulationInputsV3Snapshot;
using game::NamedBoolV3;
using game::NamedSignedV3;
using game::OptionalFullIdV3;
using game::ReadCombatSimulationInputsV3Result;

ReadCombatSimulationInputsV3Result ReadCombatSimulationInputsV3(
    const Bindings &bindings,
    const game::CombatSimulationInputsRequest &request,
    CombatSimulationInputsV3Snapshot &output) noexcept;

// Serializes the production phase fragment only. bridge.cpp composes it with
// the existing v2 base serializer in one command_result frame.
std::string SerializeCombatPhaseInputsV3(const CombatPhaseInputsV3 &inputs);

} // namespace xar::ck3_11906
