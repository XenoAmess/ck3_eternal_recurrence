#include "knight_effectiveness_context_memory.hpp"
#include "xar_bridge/phase_rite_parameters_v1_serializer.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace phase_rite_wire {
std::string SerializeCommander(const xar::game::CombatCommanderSnapshot &);
std::string SerializeKnights(const xar::game::CombatKnightsSnapshot &);
}
namespace {
using namespace combat_fixture;
Memory<0x800> adopted_rite{}, main_rite{};
Memory<0xA0> faith{};
std::array<Memory<0x20>, 4> native_keys{};
std::array<std::int32_t, 3> tokens{1, 2, 3};
std::array<std::int32_t, 1> unrelated_tokens{4};
bool fail_key = false;
constexpr std::uint32_t adopted_id = 0x0100000DU;
constexpr std::uint32_t main_id = 0x0100000EU;
constexpr std::uint32_t faith_id = 0x0100000FU;

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
void CString(void *out, const char *key) {
  const auto length = std::strlen(key);
  if (length < 16U) std::memcpy(out, key, length);
  else Put(out, 0, key);
  Put(out, 0x10, static_cast<std::uint64_t>(length));
  Put(out, 0x18, length < 16U ? std::uint64_t{15} : static_cast<std::uint64_t>(length));
}
void *Rite(void *) { return adopted_rite.data(); }
void *Faith(void *) { return faith.data(); }
bool Contains(const void *collection, const std::int32_t *token) {
  const auto *data = Get<const std::int32_t *>(collection, 0);
  const auto count = Get<std::int32_t>(collection, 0xC);
  return data && std::find(data, data + count, *token) != data + count;
}
const void *TokenKey(std::int32_t token) {
  if (fail_key || token < 1 || token > 4) return nullptr;
  return native_keys[static_cast<std::size_t>(token - 1)].data();
}
xar::game::Snapshot Scope() {
  xar::game::Snapshot scope{};
  scope.paused = true;
  scope.has_played_character = true;
  scope.played_character_alive = true;
  xar::game::ArmySnapshot own{}, opposing{};
  own.army_id = player; opposing.army_id = enemy;
  scope.player_armies.push_back(own);
  xar::game::ActiveWarSnapshot war{};
  war.war_id = 0x01000020;
  war.allied_armies.push_back(own); war.enemy_armies.push_back(opposing);
  scope.active_wars.push_back(war);
  return scope;
}

void RunCase(const std::filesystem::path &directory, const char *name,
             bool known_false, bool zero_ref, bool absent, bool failed) {
  auto bindings = Setup();
  adopted_rite = {}; main_rite = {}; faith = {}; native_keys = {};
  CString(native_keys[0].data(), "death_is_glory");
  CString(native_keys[1].data(), "killing_bestows_heads");
  CString(native_keys[2].data(), "decapitation_steals_prestige_as_piety");
  CString(native_keys[3].data(), "unrelated_key");
  const std::uint32_t actual_rite_id = zero_ref ? 0U : adopted_id;
  const std::uint32_t actual_faith_id = zero_ref ? 0U : faith_id;
  Put(adopted_rite.data(), 8, actual_rite_id);
  Put(adopted_rite.data(), 0x4B8, actual_faith_id);
  Put(adopted_rite.data(), 0x7B8, known_false ? unrelated_tokens.data() : tokens.data());
  Put(adopted_rite.data(), 0x7C4, known_false ? std::int32_t{1} : std::int32_t{3});
  // An independent main Rite intentionally has opposite Boolean contents.
  // No main-Rite getter is provided to this candidate provider.
  Put(main_rite.data(), 8, main_id);
  Put(main_rite.data(), 0x7B8, known_false ? tokens.data() : unrelated_tokens.data());
  Put(main_rite.data(), 0x7C4, known_false ? std::int32_t{3} : std::int32_t{1});
  Put(faith.data(), 8, actual_faith_id); Put(faith.data(), 0x98, main_id);
  Put(Character(commander), 0xB4, absent ? 0xFFFFFFFFU : actual_rite_id);
  Put(Character(knight_char), 0xB4, absent ? 0xFFFFFFFFU : actual_rite_id);
  fail_key = failed;
  bindings.phase_rite_parameters = {true, Rite, Faith, Faith, {true, Contains, TokenKey}};
  const auto source_rite_before = adopted_rite;
  const auto source_faith_before = faith;
  const auto source_characters_before = characters;
  xar::game::CombatSimulationInputsSnapshot output{};
  const xar::game::CombatSimulationInputsRequest request{1, 2, {enemy}, {player}};
  Require(xar::ck3_12002::ReadCombatSimulationInputs(bindings, Scope(), request, output) ==
              xar::game::ReadCombatSimulationInputsResult::available && output.input_observation_ready,
          "optional candidate Rite leaf changed base query readiness");
  Require(adopted_rite == source_rite_before && faith == source_faith_before && characters == source_characters_before,
          "candidate helper changed source memory");
  const auto enemy_row = std::find_if(output.armies.begin(), output.armies.end(),
      [](const auto &row) { return row.army_id == enemy; });
  const auto player_row = std::find_if(output.armies.begin(), output.armies.end(),
      [](const auto &row) { return row.army_id == player; });
  Require(enemy_row != output.armies.end() && player_row != output.armies.end() &&
              player_row->knights.members.size() == 1U,
          "real production V2 commander/knight occurrences missing");
  const auto &commander_leaf = enemy_row->commander.phase_rite_parameters_v1;
  const auto &knight_leaf = player_row->knights.members.front().phase_rite_parameters_v1;
  Require(commander_leaf && knight_leaf && commander_leaf->source_character_id == static_cast<std::uint32_t>(commander) &&
              knight_leaf->source_character_id == static_cast<std::uint32_t>(knight_char),
          "production collector did not attach source identities");
  using Status = xar::game::PhaseRiteParameterStatusV1;
  for (const auto *leaf : {&*commander_leaf, &*knight_leaf}) {
    if (absent) {
      Require(leaf->status == Status::absent && leaf->raw_adopted_rite_id == 0xFFFFFFFFU &&
                  !leaf->rite_id && !leaf->faith_id && !leaf->boolean_parameters_complete &&
                  leaf->boolean_parameter_keys.empty() && leaf->unavailable_reason.empty(),
              "observed absent adopted Rite was not distinct");
    } else if (failed) {
      Require(leaf->status == Status::unavailable && leaf->rite_id == actual_rite_id &&
                  leaf->faith_id == actual_faith_id && !leaf->boolean_parameters_complete &&
                  leaf->boolean_parameter_keys.empty() && leaf->unavailable_reason == "parameter_key_unavailable",
              "failed actual key read became a known false or lost source identity");
    } else {
      const std::vector<std::string> expected = known_false ? std::vector<std::string>{"unrelated_key"} :
          std::vector<std::string>{"death_is_glory", "killing_bestows_heads", "decapitation_steals_prestige_as_piety"};
      Require(leaf->status == Status::available && leaf->raw_adopted_rite_id == actual_rite_id &&
                  leaf->rite_id == actual_rite_id && leaf->faith_id == actual_faith_id &&
                  leaf->boolean_parameters_complete && leaf->boolean_parameter_keys == expected,
              "actual adopted set/ref0 differs or main Rite replaced it");
    }
  }
  std::string wire = "{\"schema\":\"ck3_12003_phase_rite_parameters_fixture_v1\",\"case\":";
  xar::game::AppendPhaseRiteStringV1(wire, name);
  wire += ",\"base_input_observation_ready\":true,\"main_rite_id\":" + std::to_string(main_id);
  wire += ",\"commander_public_army_id\":" + std::to_string(enemy);
  wire += ",\"commander_native_carmy_id\":" + std::to_string(enemy_army);
  wire += ",\"knight_public_army_id\":" + std::to_string(player);
  wire += ",\"knight_native_carmy_id\":" + std::to_string(player_army);
  wire += ",\"knight_regiment_id\":" + std::to_string(knight_reg);
  wire += ",\"commander\":" + phase_rite_wire::SerializeCommander(enemy_row->commander);
  wire += ",\"knights\":" + phase_rite_wire::SerializeKnights(player_row->knights) + '}';
  std::ofstream file(directory / (std::string(name) + ".json"), std::ios::binary);
  file << wire << '\n';
  Require(file.good(), "candidate Rite wire write failed");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Require(argc == 2, "one wire output directory required");
    Require(!xar::ck3_12003::phase_rite::BindImage(0x1000, xar::ck3_12002::kExecutableSha256).enabled,
            "legacy build unexpectedly enabled candidate provider");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    RunCase(directory, "complete_true", false, false, false, false);
    RunCase(directory, "known_false_main_different", true, false, false, false);
    RunCase(directory, "zero_reference", false, true, false, false);
    RunCase(directory, "absent_rite", false, false, true, false);
    RunCase(directory, "unavailable_key", false, false, false, true);
    std::cout << "5 NEW actual collector/serializer candidate Rite cases; synthetic source only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
