#include "knight_effectiveness_context_memory.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace knight_context_wire {
std::string SerializeKnights(const xar::game::CombatKnightsSnapshot &);
}

namespace {
using namespace combat_fixture;
constexpr std::int32_t kSelectedId = 0x0300000D;
constexpr std::int32_t kScale = 100000;
Memory<0x220> selected_character{};
Memory<0x360> selected_landed{};
Memory<0x90> selected_model{};
void *selected_context = nullptr;
bool model_missing = false;
bool callback_contract_valid = true;
std::int32_t missing_modifier = -1;
std::size_t context_calls = 0;
std::size_t scalar_calls = 0;
std::vector<std::int32_t> queried_keys;
constexpr std::array<std::int64_t, 9> kModifiers{
    -150000, 0, 200000, -300000, 400000, 500000, -600000, 700000, -800000};
constexpr std::array<std::size_t, 6> kSkillOffsets{0xEC, 0xD8, 0xE4, 0xE8, 0xDC, 0xE0};

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

void *SelectedContext(void *knight) {
  ++context_calls;
  callback_contract_valid = callback_contract_valid && knight == Character(knight_char);
  return selected_context;
}

void *SelectedModel(void *character) {
  if (character == selected_context) return model_missing ? nullptr : selected_model.data();
  return Aggregator(character);
}

std::int64_t *SelectedModifier(void *model, std::int64_t *out, std::int32_t key) {
  if (key < 0xC1 || key > 0xC9) return Modifier(model, out, key);
  queried_keys.push_back(key);
  callback_contract_valid = callback_contract_valid &&
      model == selected_model.data() + 0x68;
  if (key == missing_modifier || !callback_contract_valid) return nullptr;
  *out = kModifiers[static_cast<std::size_t>(key - 0xC1)];
  return out;
}

std::int64_t *NativeScalar(std::int64_t *out, void *context, std::uint64_t mode) {
  ++scalar_calls;
  callback_contract_valid = callback_contract_valid && context == selected_context && mode == 0;
  if (!callback_contract_valid) return nullptr;
  // A callable leaf fixture, independent of the diagnostic raw-table reads.
  *out = 125000;
  return out;
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

void Configure(bool self, bool missing_model = false, std::int32_t missing_key = -1) {
  selected_character.fill(std::byte{});
  selected_landed.fill(std::byte{});
  selected_model.fill(std::byte{});
  Put(selected_character.data(), 0x1C, std::uint32_t{0x43686172});
  Register(3, kSelectedId, selected_character.data(), 0x18);
  selected_context = self ? Character(knight_char) : selected_character.data();
  Put(selected_context, 0x1C0, self ? nullptr : selected_landed.data());
  const std::array<std::int32_t, 6> skills = self
      ? std::array<std::int32_t, 6>{25, -2, 3, -4, 5, -6}
      : std::array<std::int32_t, 6>{-7, 11, -13, 0, 17, -19};
  for (std::size_t i = 0; i < skills.size(); ++i) Put(selected_context, kSkillOffsets[i], skills[i]);
  Put(selected_landed.data(), 0x350, std::int64_t{-1234567890123});
  Put(selected_landed.data(), 0x358, std::int64_t{9876543210123});
  model_missing = missing_model;
  missing_modifier = missing_key;
  callback_contract_valid = true;
  context_calls = scalar_calls = 0;
  queried_keys.clear();
}

std::string RunCase(xar::ck3_12002::CombatBindings bindings, bool self,
                    bool missing_model = false, std::int32_t missing_key = -1) {
  Configure(self, missing_model, missing_key);
  bindings.get_knight_effectiveness_context = SelectedContext;
  bindings.get_character_modifier_aggregator = SelectedModel;
  bindings.read_character_modifier = SelectedModifier;
  bindings.read_knight_effectiveness = NativeScalar;
  const auto characters_before = characters;
  const auto regiments_before = regiments;
  const auto selected_before = selected_character;
  const auto landed_before = selected_landed;
  const auto model_before = selected_model;
  xar::game::CombatSimulationInputsSnapshot output{};
  const xar::game::CombatSimulationInputsRequest request{1, 2, {enemy}, {player}};
  Require(xar::ck3_12002::ReadCombatSimulationInputs(bindings, Scope(), request, output) ==
              xar::game::ReadCombatSimulationInputsResult::available,
          "production combat reader must preserve available result");
  Require(characters == characters_before && regiments == regiments_before &&
              selected_character == selected_before && selected_landed == landed_before &&
              selected_model == model_before,
          "production combat reader changed fixture memory");
  Require(callback_contract_valid && context_calls == 1 && scalar_calls == 1,
          "native context/scalar callback arguments differed");
  const auto army = std::find_if(output.armies.begin(), output.armies.end(),
      [](const auto &row) { return row.army_id == player; });
  Require(army != output.armies.end() && army->knights.available && army->knights.members.size() == 1,
          "production native knight output missing");
  const auto &knight = army->knights.members.front();
  Require(knight.character_id == knight_char && knight.prowess == 25 && knight.eligible &&
              knight.knight_effectiveness_raw == 125000 && knight.effective_damage_raw == 312500000 &&
              knight.effective_toughness_raw == 31250000,
          "diagnostic read must retain original knight identity and scalar/stat values");
  Require(knight.effectiveness_context.has_value(), "production DTO lacks effectiveness context");
  const auto &context = *knight.effectiveness_context;
  const auto expected_id = self ? knight_char : kSelectedId;
  Require(context.character_id == expected_id, "selected Character full ID was lost or replaced by knight ID");
  const bool available = !missing_model && missing_key == -1;
  Require(context.available == available, "diagnostic availability differs");
  if (available) {
    const std::array<std::int64_t, 9> expected_operands = self
        ? std::array<std::int64_t, 9>{kScale, 0, 0, 2500000, -200000, 300000, -400000, 500000, -600000}
        : std::array<std::int64_t, 9>{kScale, -1234567890123, 9876543210123,
                                     -700000, 1100000, -1300000, 0, 1700000, -1900000};
    Require(context.modifier_raw == kModifiers && context.operand_raw == expected_operands &&
                context.unavailable_reason.empty(),
            "signed C1..C9 modifier/operand mapping differs");
    Require(queried_keys == std::vector<std::int32_t>{0xC1, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9},
            "raw diagnostics must read all ordered C1..C9 keys, including zero operands");
  } else {
    Require(context.unavailable_reason == "effectiveness_context_modifiers_unavailable",
            "missing modifier/model diagnostic reason differs");
    Require(missing_model ? queried_keys.empty() :
                queried_keys == std::vector<std::int32_t>{0xC1, 0xC2, 0xC3, 0xC4, 0xC5},
            "missing diagnostic did not stop at the expected callable leaf");
  }
  const auto wire = knight_context_wire::SerializeKnights(army->knights);
  std::string expected = "\"effectiveness_context\":{\"schema\":\"ck3_12003_knight_effectiveness_context_v1\",\"status\":\"";
  expected += available ? "available" : "unavailable";
  expected += "\",\"character_id\":" + std::to_string(expected_id) +
      ",\"modifier_indices\":[193,194,195,196,197,198,199,200,201],\"modifier_raw\":";
  if (available) {
    expected += "[-150000,0,200000,-300000,400000,500000,-600000,700000,-800000],\"operand_raw\":";
    expected += self ? "[100000,0,0,2500000,-200000,300000,-400000,500000,-600000]"
                     : "[100000,-1234567890123,9876543210123,-700000,1100000,-1300000,0,1700000,-1900000]";
    expected += ",\"scale\":100000,\"unavailable_reason\":null}";
  } else {
    expected += "null,\"operand_raw\":null,\"scale\":100000,\"unavailable_reason\":\"effectiveness_context_modifiers_unavailable\"}";
  }
  Require(wire.find(expected) != std::string::npos, "literal production context JSON bytes differ");
  Require(wire.find("\"knight_effectiveness_raw\":125000,") != std::string::npos &&
              wire.find("\"effective_damage_raw\":312500000,\"effective_toughness_raw\":31250000") != std::string::npos &&
              wire.starts_with("{\"status\":\"available\",\"members\":["),
          "literal production serializer discarded available scalar/stats");
  return wire;
}

void WriteCase(const std::filesystem::path &directory, std::string_view name, const std::string &wire) {
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << wire << '\n';
  Require(out.good(), "fixture JSON output failed");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "one output directory is required");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    auto bindings = Setup();
    WriteCase(directory, "selected_character", RunCase(bindings, false));
    WriteCase(directory, "self_character", RunCase(bindings, true));
    WriteCase(directory, "missing_key", RunCase(bindings, false, false, 0xC5));
    WriteCase(directory, "missing_model", RunCase(bindings, false, true));
    std::cout << "4 new native effectiveness-context reader/wire cases; synthetic memory and callable leaves only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
