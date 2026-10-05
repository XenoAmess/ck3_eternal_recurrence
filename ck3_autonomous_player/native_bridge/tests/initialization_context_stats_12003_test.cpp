#include "knight_effectiveness_context_memory.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

namespace initialization_context_wire {
std::string SerializeRegiment(const xar::game::CombatRegimentSnapshot &);
}

namespace {
using namespace combat_fixture;
std::array<std::size_t, 2> stat_calls{};
bool fail_initial = false;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

void *ContextStats(void *regiment, void *output, void *province) {
  if (province == provinces[0].data()) {
    ++stat_calls[0];
    return Stats(regiment, output, province);
  }
  if (province != provinces[1].data()) return nullptr;
  ++stat_calls[1];
  if (fail_initial) return nullptr;
  Put(output, 8, std::int32_t{200});
  Put(output, 0x10, std::int64_t{-100000});
  Put(output, 0x18, std::int64_t{2000000});
  Put(output, 0x20, std::int64_t{3000000});
  Put(output, 0x28, std::int64_t{0});
  Put(output, 0x30, std::int64_t{-500000});
  return output;
}

xar::game::Snapshot Scope() {
  xar::game::Snapshot scope{};
  scope.paused = true;
  scope.has_played_character = true;
  scope.played_character_alive = true;
  xar::game::ArmySnapshot own{};
  own.army_id = player;
  xar::game::ArmySnapshot opposing{};
  opposing.army_id = enemy;
  scope.player_armies.push_back(own);
  xar::game::ActiveWarSnapshot war{};
  war.war_id = 0x01000020;
  war.allied_armies.push_back(own);
  war.enemy_armies.push_back(opposing);
  scope.active_wars.push_back(war);
  return scope;
}

void RunCase(const std::filesystem::path &directory, const char *name,
             bool equal, bool failed) {
  auto bindings = Setup();
  bindings.evaluate_regiment_stats_at_province = ContextStats;
  Put(units[0].data(), 0x20, provinces[equal ? 0 : 1].data());
  stat_calls = {};
  fail_initial = failed;
  const auto units_before = units;
  const auto regiments_before = regiments;
  xar::game::CombatSimulationInputsSnapshot output{};
  const xar::game::CombatSimulationInputsRequest request{1, 2, {enemy}, {player}};
  Require(xar::ck3_12002::ReadCombatSimulationInputs(bindings, Scope(), request, output) ==
              xar::game::ReadCombatSimulationInputsResult::available,
          "optional initial leaf changed target-query readiness");
  Require(units == units_before && regiments == regiments_before,
          "reader changed fixture source memory");
  Require(stat_calls[0] == 3 && stat_calls[1] == (equal ? 0U : 1U),
          "current==target duplicated native stat reads or differing current was not read");
  const auto army = std::find_if(output.armies.begin(), output.armies.end(),
      [](const auto &row) { return row.army_id == enemy; });
  Require(army != output.armies.end() && army->available && army->regiments.size() == 1,
          "enclosing Army/Regiment identity missing");
  const auto &regiment = army->regiments.front();
  Require(regiment.regiment_id == enemy_reg && regiment.effective_stats.available &&
              regiment.effective_stats.source_target_province_id == 1 &&
              regiment.effective_stats.damage_raw == 1000000,
          "existing target stats changed");
  const auto wire = initialization_context_wire::SerializeRegiment(regiment);
  if (equal) {
    Require(!regiment.initialization_context_stats.has_value() &&
                wire.find("initialization_context_stats") == std::string::npos,
            "equality must reuse the existing tuple without a duplicate leaf");
  } else {
    Require(regiment.initialization_context_stats.has_value(), "initial leaf missing");
    const auto &initial = *regiment.initialization_context_stats;
    Require(initial.available == !failed, "initial readiness differs");
    if (failed) {
      Require(initial.unavailable_reason == "effective_stats_helper_failed" &&
                  wire.find("\"initialization_context_stats\":{\"status\":\"unavailable\","
                            "\"source_target_province_id\":null,\"max_size\":null") != std::string::npos,
              "independent failed initial input must remain null with its reason");
    } else {
      Require(initial.source_target_province_id == 2 && initial.max_size == 200 &&
                  initial.siege_value_raw == -100000 && initial.damage_raw == 2000000 &&
                  initial.toughness_raw == 3000000 && initial.pursuit_raw == 0 &&
                  initial.screen_raw == -500000,
              "actual-current Province six-stat tuple differs");
      Require(wire.find("\"initialization_context_stats\":{\"status\":\"available\","
                        "\"source_target_province_id\":2,\"max_size\":200,"
                        "\"siege_value_raw\":-100000,\"damage_raw\":2000000,"
                        "\"toughness_raw\":3000000,\"pursuit_raw\":0,"
                        "\"screen_raw\":-500000,\"scale\":100000,"
                        "\"unavailable_reason\":null}") != std::string::npos,
              "production literal initial stats JSON differs");
    }
  }
  std::ofstream file(directory / (std::string(name) + ".json"), std::ios::binary);
  file << wire << '\n';
  Require(file.good(), "regiment wire write failed");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "one output directory is required");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    RunCase(directory, "different_current", false, false);
    RunCase(directory, "equal_current", true, false);
    RunCase(directory, "unavailable_initial", false, true);
    std::cout << "3 new initial-context reader/wire cases; synthetic memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
