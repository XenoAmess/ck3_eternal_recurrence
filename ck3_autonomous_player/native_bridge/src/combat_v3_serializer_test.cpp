#include "xar_bridge/combat_v3.hpp"

#include <algorithm>
#include <array>
#include <iostream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

constexpr std::array<std::string_view, 56> kTraits{
    "ambitious", "athletic", "berserker", "brave", "calm",
    "cautious_leader", "compassionate", "content", "craven",
    "desert_warrior", "disfigured", "education_martial_1",
    "education_martial_2", "education_martial_3", "education_martial_4",
    "education_martial_5", "education_martial_prowess_1",
    "education_martial_prowess_2", "education_martial_prowess_3",
    "education_martial_prowess_4", "flexible_leader", "forest_fighter",
    "giant", "holy_warrior", "impatient", "incapable", "intellect_good_1",
    "intellect_good_2", "intellect_good_3", "jungle_stalker", "lazy",
    "lifestyle_blademaster", "maimed", "nomadic_philosophy", "one_eyed",
    "one_legged", "open_terrain_expert", "patient", "physique_good",
    "reckless", "rough_terrain_expert", "sadistic", "scholar",
    "shieldmaiden", "shrewd", "strong", "temperate", "winter_soldier",
    "wrathful", "zealous", "aggressive_attacker", "wounded_1",
    "wounded_2", "wounded_3", "fragile_bones", "tourney_participant"};
constexpr std::array<std::string_view, 12> kInnovations{
    "innovation_quilted_armor", "innovation_sarawit",
    "innovation_legionnaires", "innovation_arched_saddle",
    "innovation_valets", "innovation_tiefutu",
    "innovation_advanced_bowmaking", "innovation_repeating_crossbow",
    "innovation_war_camels", "innovation_elephantry",
    "innovation_gunpowder", "innovation_fire_medicine"};
constexpr std::array<std::string_view, 14> kTraditions{
    "tradition_fp1_coastal_warriors", "tradition_hird",
    "tradition_futuwaa", "tradition_druzhina", "tradition_khadga_puja",
    "tradition_garuda_warriors", "tradition_himalayan_settlers",
    "tradition_mubarizuns", "tradition_burman_royal_army",
    "tradition_mountaineer_ruralism", "tradition_caucasian_wolves",
    "tradition_roman_legacy", "tradition_ep3_audacious_cadets",
    "tradition_ep3_imperial_tagmata"};
constexpr std::array<std::string_view, 10> kCultureParameters{
    "knights_slightly_more_prone_to_injury", "blademaster_traits_more_common",
    "unlock_zhanmadao", "unlock_burenjia", "unlock_maa_cataphract_archers",
    "unlock_maa_black_armor_cavalry", "unlock_maa_horse_archers",
    "unlock_maa_mangudai", "unlock_emishi_horse_archers_units",
    "unlock_mounted_samurai_units"};
constexpr std::array<std::string_view, 6> kAccoladeParameters{
    "accolade_defends_family_low", "accolade_defends_family_medium",
    "accolade_defends_family_high",
    "accolade_increase_hostile_knight_death_low",
    "accolade_increase_hostile_knight_death_medium",
    "accolade_increase_hostile_knight_death_high"};
constexpr std::array<std::string_view, 13> kAttributeUnlocks{
    "skirmisher", "archer", "crossbowmen", "pike", "vanguard", "outrider",
    "lancer", "camelry", "elephantry", "horse_archer", "gunpowder",
    "fanatic", "valiant"};
constexpr std::array<std::string_view, 11> kMaaCounts{
    "skirmishers_raw", "pikemen_raw", "heavy_infantry_raw",
    "light_cavalry_raw", "heavy_cavalry_raw", "camel_cavalry_raw",
    "elephant_cavalry_raw", "archer_cavalry_raw", "gunpowder_raw",
    "crossbow_family_raw", "non_crossbow_archers_raw"};

template <std::size_t Size>
std::vector<xar::ck3_11906::NamedBoolV3>
FalseNamed(const std::array<std::string_view, Size> &keys) {
  std::vector<xar::ck3_11906::NamedBoolV3> output;
  output.reserve(keys.size());
  for (const auto key : keys) {
    output.push_back({std::string(key), false});
  }
  return output;
}

xar::ck3_11906::CombatPhaseCharacterV3 Character(
    std::int32_t id, std::int32_t army_id, std::int32_t regiment_id,
    std::string role, std::vector<std::string> phase_roles,
    std::int32_t ordinal) {
  using namespace xar::ck3_11906;
  CombatPhaseCharacterV3 row{};
  row.character_id = id;
  row.source_army_id = army_id;
  row.source_regiment_id = regiment_id;
  row.encounter_role = std::move(role);
  row.phase_roles = std::move(phase_roles);
  row.alive = true;
  row.is_ai = true;
  row.martial = 10 + ordinal;
  row.learning = 11 + ordinal;
  row.prowess = 12 + ordinal;
  row.traits_or_groups = FalseNamed(kTraits);
  row.house = {true, 100 + ordinal};
  row.liege = {true, 20'000 + ordinal};
  row.liege_house = row.house;
  row.employer = {true, 30'000 + ordinal};
  row.dynasty = {true, 40'000 + ordinal};
  row.culture = {true, 50'000 + ordinal};
  row.faith = {true, 60'000 + ordinal};
  row.religion = {true, 70'000 + ordinal};
  row.innovations = FalseNamed(kInnovations);
  row.traditions = FalseNamed(kTraditions);
  row.culture_parameters = FalseNamed(kCultureParameters);
  row.accolade = {false, -1};
  row.accolade_parameters = FalseNamed(kAccoladeParameters);
  row.attribute_unlock_variables = FalseNamed(kAttributeUnlocks);
  row.hold_court_8050_knight = {false, -1};
  row.employer_hold_court_8050_promise = {false, -1};
  row.can_be_acclaimed = true;
  return row;
}

xar::ck3_11906::CombatPhaseArmyV3 Army(
    std::int32_t id, std::int32_t native_id, std::string role,
    std::string_view selected_family, std::int64_t regiment_count_raw) {
  using namespace xar::ck3_11906;
  CombatPhaseArmyV3 row{};
  row.army_id = id;
  row.native_carmy_id = native_id;
  row.encounter_role = std::move(role);
  row.maa_regiment_count_raw = regiment_count_raw;
  for (const auto key : kMaaCounts) {
    row.maa_counts_raw.push_back(
        {std::string(key), key == selected_family ? 100'000 : 0});
  }
  return row;
}

xar::ck3_11906::CombatPhaseInputsV3 Fixture() {
  using namespace xar::ck3_11906;
  CombatPhaseInputsV3 fixture{};
  fixture.available = true;
  fixture.characters.push_back(Character(
      16'777'218, 16'777'217, 16'777'217, "attacker",
      {"commander", "knight"}, 0));
  fixture.characters.push_back(Character(
      16'777'219, 16'777'218, 16'777'219, "defender", {"knight"}, 1));
  fixture.armies.push_back(Army(16'777'217, 33'554'449, "attacker",
                                "non_crossbow_archers_raw", 100'000));
  fixture.armies.push_back(Army(16'777'218, 33'554'450, "defender",
                                "heavy_cavalry_raw", 200'000));

  CombatPhaseSideV3 attacker{};
  attacker.side_index = 0;
  attacker.encounter_role = "attacker";
  attacker.ordered_army_ids = {16'777'217};
  attacker.ordered_character_ids = {16'777'218};
  attacker.ordered_commander_ids = {16'777'218};
  attacker.ordered_knight_ids = {16'777'218};
  attacker.primary_participant_character_id = 16'777'218;
  attacker.primary_source_army_id = 16'777'217;
  attacker.commander_character_id = 16'777'218;
  attacker.side_strength_raw = 432'000;
  attacker.side_army_size_raw = 100'000'000;
  attacker.participants.push_back({16'777'217, 16'777'218, 60'000});
  attacker.candidate_source_proof.source_vector_equivalence = true;
  attacker.candidate_source_proof.sequence_sha256 =
      "BED2F60F06753A1E834BAEED9D1926E4B574DD833E74E39B997CFB1EC4CDCF8B";
  attacker.candidate_source_proof.ordered_sources = {
      {"commander", 16'777'217, -1, 16'777'218},
      {"knight", 16'777'217, 16'777'217, 16'777'218},
  };
  fixture.sides.push_back(attacker);

  CombatPhaseSideV3 defender{};
  defender.side_index = 1;
  defender.encounter_role = "defender";
  defender.ordered_army_ids = {16'777'218};
  defender.ordered_character_ids = {16'777'219};
  defender.ordered_knight_ids = {16'777'219};
  defender.primary_participant_character_id = 16'777'219;
  defender.primary_source_army_id = 16'777'218;
  defender.commander_character_id = -1;
  defender.side_strength_raw = 288'000;
  defender.side_army_size_raw = 80'000'000;
  defender.participants.push_back({16'777'218, 16'777'219, 60'001});
  defender.candidate_source_proof.source_vector_equivalence = true;
  defender.candidate_source_proof.sequence_sha256 =
      "DC94F02BFE75DB393A6E90847C27D39FE980948E4A2BABDE8CAC61E29C9E145F";
  defender.candidate_source_proof.ordered_sources = {
      {"knight", 16'777'218, 16'777'219, 16'777'219},
  };
  fixture.sides.push_back(defender);
  fixture.faith_hostility.push_back(
      {16'777'218, 1, 16'777'219, 60'001, 60'000, 3});
  fixture.faith_hostility.push_back(
      {16'777'219, 0, 16'777'218, 60'000, 60'001, 3});

  auto &advantage = fixture.advantage_model;
  advantage.available = true;
  advantage.observation_origin = "native_exact_build_production";
  xar::game::CombatAdvantageSideInputV3TestOnly attacker_input{};
  attacker_input.side = "attacker";
  attacker_input.primary_army_id = 16'777'217;
  attacker_input.ordered_army_ids = {16'777'217};
  attacker_input.supply.selected_key = "supply_state_supplied_advantage";
  attacker_input.supply.selected_effect_identity =
      "loaded_combat_rule_database:+0xF38";
  attacker_input.supply.eligible_soldiers_total = 1'000;
  attacker_input.supply.eligible_soldiers_supplied = 1'000;
  attacker_input.owner_character_id = 16'777'218;
  advantage.side_inputs.push_back(attacker_input);
  xar::game::CombatAdvantageSideInputV3TestOnly defender_input{};
  defender_input.side = "defender";
  defender_input.primary_army_id = 16'777'218;
  defender_input.ordered_army_ids = {16'777'218};
  defender_input.supply.selected_key =
      "supply_state_running_low_advantage";
  defender_input.supply.selected_effect_identity =
      "loaded_combat_rule_database:+0xF48";
  defender_input.supply.selected_effect_points = -10;
  defender_input.supply.eligible_soldiers_total = 800;
  defender_input.supply.eligible_soldiers_running_low = 800;
  defender_input.owner_character_id = 16'777'219;
  defender_input.owner_debt_selector_raw = 1;
  advantage.side_inputs.push_back(defender_input);

  std::int64_t accumulator = 0;
  std::int32_t append_order = 0;
  const auto add_source = [&advantage, &accumulator, &append_order](
                              std::string stage, std::string side,
                              bool selected, bool applied, std::string key,
                              std::int32_t points, std::string skip_reason) {
    xar::game::CombatAdvantageConstructorSourceV3TestOnly row{};
    row.stage_order =
        static_cast<std::int32_t>(advantage.constructor_sources.size());
    row.stage = std::move(stage);
    row.side = std::move(side);
    row.selected = selected;
    row.applied = applied;
    row.source_key = std::move(key);
    row.effect_advantage_points = points;
    row.accumulator_before_raw = accumulator;
    if (applied) {
      row.append_order = append_order++;
      row.signed_contribution_raw =
          static_cast<std::int64_t>(points) * 100'000 *
          (row.side == "defender" ? -1 : 1);
      accumulator = std::clamp<std::int64_t>(
          accumulator + row.signed_contribution_raw, -10'000'000, 10'000'000);
    } else {
      row.skip_reason = std::move(skip_reason);
    }
    row.accumulator_after_raw = accumulator;
    advantage.constructor_sources.push_back(std::move(row));
  };
  add_source("attacker_adjacency", "attacker", true, true,
             "attacker_river", -10, {});
  add_source("defender_adjacency", "defender", true, true,
             "defender_river", 10, {});
  add_source("attacker_terrain", "attacker", true, true,
             "terrain:hills:attacker", 2, {});
  add_source("defender_terrain", "defender", true, true,
             "terrain:hills:defender", 3, {});
  add_source("supply_0", "attacker", true, false,
             "supply_state_supplied_advantage", 0,
             "zero_effect_not_appended");
  add_source("supply_1", "defender", true, true,
             "supply_state_running_low_advantage", -10, {});
  add_source("holding_defender_1", "defender", true, true,
             "holding_defender_advantage", 5, {});
  add_source("recently_disembarked_0", "attacker", false, false, {}, 0,
             "primary_army_not_recently_disembarked");
  add_source("recently_disembarked_1", "defender", false, false, {}, 0,
             "primary_army_not_recently_disembarked");
  add_source("debt_0_owner", "attacker", true, true,
             "combat_debt_level_0", -5, {});
  add_source("debt_0_treasury", "attacker", false, false, {}, 0,
             "treasury_debt_gate_false");
  add_source("debt_1_owner", "defender", true, true,
             "combat_debt_level_1", -10, {});
  add_source("debt_1_treasury", "defender", false, false, {}, 0,
             "treasury_debt_gate_false");
  add_source("unreformed_faith_0", "attacker", false, false, {}, 0,
             "target_faith_not_unreformed");
  add_source("unreformed_faith_1", "defender", true, true,
             "unreformed_faith_province", 5, {});
  advantage.base_static_accumulator_raw = accumulator;

  xar::game::CombatResolvedDynamicSideV3TestOnly attacker_dynamic{};
  attacker_dynamic.side = "attacker";
  attacker_dynamic.battle_commander_selected = true;
  attacker_dynamic.battle_commander_character_id = 16'777'218;
  attacker_dynamic.target_conditionals_residual_raw = 1'200'000;
  attacker_dynamic.commander_dynamic_raw = 500'000;
  attacker_dynamic.side_dynamic_raw = 300'000;
  attacker_dynamic.side_total_raw = 2'000'000;
  attacker_dynamic.contribution_to_resolved_raw = 2'000'000;
  advantage.resolved_dynamic.sides.push_back(attacker_dynamic);
  xar::game::CombatResolvedDynamicSideV3TestOnly defender_dynamic{};
  defender_dynamic.side = "defender";
  defender_dynamic.target_conditionals_residual_raw = 750'000;
  defender_dynamic.side_dynamic_raw = 250'000;
  defender_dynamic.side_total_raw = 1'000'000;
  defender_dynamic.contribution_to_resolved_raw = -1'000'000;
  advantage.resolved_dynamic.sides.push_back(defender_dynamic);
  advantage.resolved_dynamic.side_0_dynamic_raw = 2'000'000;
  advantage.resolved_dynamic.side_1_dynamic_raw = 1'000'000;
  advantage.resolved_dynamic.resolved_advantage_at_zero_roll_raw =
      accumulator + 1'000'000;
  advantage.resolved_dynamic.original_total_helper_raw =
      advantage.resolved_dynamic.resolved_advantage_at_zero_roll_raw;
  advantage.resolved_dynamic.original_total_helper_match = true;
  return fixture;
}

} // namespace

int main(int argc, char **argv) {
  const auto available =
      xar::ck3_11906::SerializeCombatPhaseInputsV3(Fixture());
  if (argc == 2 && std::string(argv[1]) == "--print") {
    std::cout << available;
    return 0;
  }
  if (argc == 2 && std::string(argv[1]) == "--print-unavailable") {
    xar::ck3_11906::CombatPhaseInputsV3 unavailable{};
    unavailable.unavailable_reason =
        "native_phase_identity_revalidation_failed";
    std::cout <<
        xar::ck3_11906::SerializeCombatPhaseInputsV3(unavailable);
    return 0;
  }
  if (available.find("\"native_leaf_exact\":81") ==
          std::string::npos ||
      available.find("\"offline_exact\":51") == std::string::npos ||
      available.find("native_exact_build_production") ==
          std::string::npos ||
      available.find("test_only") != std::string::npos ||
      available.find("\"commander_character_id\":null") ==
          std::string::npos ||
      available.find(
          "\"source_vector_equivalence\":true,\"sequence_sha256\":\""
          "BED2F60F06753A1E834BAEED9D1926E4B574DD833E74E39B997CFB1EC4CDCF8B"
          "\"") == std::string::npos ||
      available.find(
          "\"role\":\"commander\",\"source_army_id\":16777217,"
          "\"source_regiment_id\":null,\"character_id\":16777218") ==
          std::string::npos ||
      available.find("\"stage_order\":14") == std::string::npos ||
      available.find("\"original_total_helper_match\":true") ==
          std::string::npos) {
    return 1;
  }

  auto nullable_fixture = Fixture();
  nullable_fixture.characters.front().phase_roles = {"commander"};
  nullable_fixture.characters.front().source_regiment_id = -1;
  const auto nullable =
      xar::ck3_11906::SerializeCombatPhaseInputsV3(nullable_fixture);
  if (nullable.find("\"source_regiment_id\":null") ==
      std::string::npos) {
    return 1;
  }

  xar::ck3_11906::CombatPhaseInputsV3 unavailable{};
  unavailable.unavailable_reason = "fixture_failure";
  const auto failed =
      xar::ck3_11906::SerializeCombatPhaseInputsV3(unavailable);
  if (failed.find("\"status\":\"unavailable\"") ==
          std::string::npos ||
      failed.find("\"raw\":null") == std::string::npos ||
      failed.find("\"advantage_model\":null") == std::string::npos) {
    return 1;
  }
  return 0;
}
