#include "xar_bridge/combat_v3_test_only.hpp"

#include <array>
#include <cctype>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <utility>

namespace {

int Fail(const char *message) {
  std::cerr << "FAIL: " << message << '\n';
  return 1;
}

std::string MinifyJsonWhitespace(std::string_view source) {
  std::string result;
  result.reserve(source.size());
  bool in_string = false;
  bool escaped = false;
  for (const char character : source) {
    if (in_string) {
      result += character;
      if (escaped) {
        escaped = false;
      } else if (character == '\\') {
        escaped = true;
      } else if (character == '"') {
        in_string = false;
      }
    } else if (character == '"') {
      in_string = true;
      result += character;
    } else if (!std::isspace(static_cast<unsigned char>(character))) {
      result += character;
    }
  }
  return result;
}

std::string_view EncounterRoleForStage(std::string_view stage) {
  constexpr std::array<std::string_view, 8> defender_stages{
      "defender_adjacency",
      "defender_terrain",
      "supply_1",
      "holding_defender_1",
      "recently_disembarked_1",
      "debt_1_owner",
      "debt_1_treasury",
      "unreformed_faith_1",
  };
  for (const auto candidate : defender_stages) {
    if (stage == candidate) {
      return "defender";
    }
  }
  return "attacker";
}

xar::game::CombatPhaseInputsV3TestOnly Fixture() {
  using namespace xar::game;
  CombatPhaseInputsV3TestOnly fixture{};
  fixture.available = true;

  CombatPhaseCharacterV3TestOnly commander{};
  commander.character_id = 36'108;
  commander.source_army_id = 357;
  commander.encounter_role = "attacker";
  commander.phase_roles = {"commander"};
  commander.state_refs.push_back({
      "root.skills.martial_raw",
      CombatPhaseStateValueKind::signed_int32,
      false,
      12,
      {},
      {},
  });
  fixture.characters.push_back(std::move(commander));

  CombatPhaseArmyV3TestOnly army{};
  army.army_id = 357;
  army.encounter_role = "attacker";
  army.state_refs.push_back({
      "army.maa_regiment_count_raw",
      CombatPhaseStateValueKind::signed_q100000,
      false,
      0,
      {},
      {},
  });
  fixture.armies.push_back(std::move(army));

  fixture.sides.push_back({0, "attacker", {357}, {36'108}, 36'108, 357,
                           "first_inserted_army_owner_with_native_preservation",
                           0, 123'400'000, {}});
  fixture.sides.push_back({1, "defender", {83'886'341}, {}, 29'829,
                           83'886'341,
                           "first_inserted_army_owner_with_native_preservation",
                           0, 259'600'000, {}});
  fixture.global_state_refs.push_back({
      "game_rules.easy_difficulty",
      CombatPhaseStateValueKind::boolean,
      false,
      0,
      {},
      {},
  });

  auto &model = fixture.advantage_model;
  model.available = true;
  model.observation_origin = "independent_synthetic_contract_fixture";
  CombatAdvantageSideInputV3TestOnly attacker{};
  attacker.side = "attacker";
  attacker.primary_army_id = 357;
  attacker.ordered_army_ids = {357};
  attacker.supply = {"supply_state_supplied_advantage", "fixture:db+F38",
                     0, 0, 0, 0, 0};
  attacker.owner_character_id = 36'108;
  CombatAdvantageSideInputV3TestOnly defender{};
  defender.side = "defender";
  defender.primary_army_id = 83'886'341;
  defender.ordered_army_ids = {83'886'341};
  defender.supply = {"supply_state_supplied_advantage", "fixture:db+F38",
                     0, 0, 0, 0, 0};
  defender.owner_character_id = 29'829;
  model.side_inputs = {attacker, defender};

  constexpr std::array<std::string_view, 15> stages{
      "attacker_adjacency",
      "defender_adjacency",
      "attacker_terrain",
      "defender_terrain",
      "supply_0",
      "supply_1",
      "holding_defender_1",
      "recently_disembarked_0",
      "recently_disembarked_1",
      "debt_0_owner",
      "debt_0_treasury",
      "debt_1_owner",
      "debt_1_treasury",
      "unreformed_faith_0",
      "unreformed_faith_1",
  };
  for (std::size_t index = 0; index < stages.size(); ++index) {
    CombatAdvantageConstructorSourceV3TestOnly source{};
    source.stage_order = static_cast<std::int32_t>(index);
    source.stage = stages[index];
    source.side = EncounterRoleForStage(stages[index]);
    source.skip_reason = "not_selected_in_synthetic_fixture";
    model.constructor_sources.push_back(std::move(source));
  }

  CombatResolvedDynamicSideV3TestOnly attacker_dynamic{};
  attacker_dynamic.side = "attacker";
  attacker_dynamic.battle_commander_selected = true;
  attacker_dynamic.battle_commander_character_id = 36'108;
  CombatResolvedDynamicSideV3TestOnly defender_dynamic{};
  defender_dynamic.side = "defender";
  model.resolved_dynamic.sides = {attacker_dynamic, defender_dynamic};
  model.resolved_dynamic.original_total_helper_match = true;
  return fixture;
}

} // namespace

int main(int argc, char **argv) {
  const auto serialized =
      xar::game::SerializeCombatPhaseInputsV3TestOnly(Fixture());
  if (serialized.find("\"combat_id\"") != std::string::npos ||
      serialized.find("query-combat-simulation-inputs-v3") !=
          std::string::npos) {
    return Fail("test-only serializer invented a CombatID or dispatch literal");
  }
  auto unavailable_fixture = Fixture();
  unavailable_fixture.available = false;
  unavailable_fixture.unavailable_reason = "side_strength_helper_mismatch";
  const auto unavailable =
      xar::game::SerializeCombatPhaseInputsV3TestOnly(unavailable_fixture);
  constexpr std::array<std::string_view, 5> unavailable_fragments{
      "\"status\":\"unavailable\"",
      "\"characters\":null",
      "\"armies\":null",
      "\"sides\":null",
      "\"advantage_model\":null",
  };
  for (const auto fragment : unavailable_fragments) {
    if (unavailable.find(fragment) == std::string::npos) {
      return Fail("helper failure did not suppress every advantage value");
    }
  }
  if (argc == 1) {
    std::cout << serialized << '\n';
    return 0;
  }
  if (argc != 2) {
    return Fail("expected zero args or one golden fixture path");
  }
  std::ifstream stream(argv[1], std::ios::binary);
  if (!stream) {
    return Fail("could not open independent serializer golden");
  }
  std::string golden((std::istreambuf_iterator<char>(stream)),
                     std::istreambuf_iterator<char>());
  if (serialized != MinifyJsonWhitespace(golden)) {
    return Fail("v3 test-only serializer drifted from independent golden");
  }
  std::cout << "PASS: v3_test_only_phase_serializer=1 "
               "production_capability=0 dispatch=0 combat_id=0\n";
  return 0;
}
