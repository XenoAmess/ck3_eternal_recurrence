#include "knight_effectiveness_context_memory.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace initialization_context_wire {
std::string SerializeRegiment(const xar::game::CombatRegimentSnapshot &);
}

namespace {
using namespace combat_fixture;
Memory<0x140> ordinary_regiment{}, fallback_regiment{}, selector{}, fallback_selector{};
Memory<0x220> ordinary_character{}, fallback_character{};
Memory<0xE0> ordinary_context{};
Memory<0x20> first_row{};
std::array<Memory<0x30>, 2> ordinary_stores{};
std::array<std::array<Memory<0x10>, 16>, 2> ordinary_slots{};
std::array<void *, 2> ordinary_store_ptrs{};
void *regiment_fallback = nullptr, *selector_fallback = nullptr, *character_fallback = nullptr;
std::array<std::uint16_t, 2> keys{0xB0, 0x1B3};
std::array<std::int64_t, 2> values{-50001, 50000};
std::array<std::int64_t, 5> bases{100000, 100000, 100000, 4000000001, -100000};
bool missing_context = false;
constexpr std::int32_t selected_character_id = 0x0100000D;
constexpr std::int32_t source_regiment_id = 0x01000001;
constexpr std::int32_t nested_selector_id = 0x01000002;

void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
void *OrdinaryAggregator(void *character) {
  if (character == ordinary_character.data() || character == fallback_character.data())
    return missing_context ? nullptr : ordinary_context.data();
  return character;
}
xar::game::Snapshot Scope() {
  xar::game::Snapshot scope{};
  scope.paused = true; scope.has_played_character = true; scope.played_character_alive = true;
  xar::game::ArmySnapshot own{}; own.army_id = player;
  xar::game::ArmySnapshot opposing{}; opposing.army_id = enemy;
  scope.player_armies.push_back(own);
  xar::game::ActiveWarSnapshot war{}; war.war_id = 0x01000020;
  war.allied_armies.push_back(own); war.enemy_armies.push_back(opposing);
  scope.active_wars.push_back(war); return scope;
}

void RunCase(const std::filesystem::path &directory, int index, const char *name) {
  auto bindings = Setup();
  ordinary_regiment = {}; fallback_regiment = {}; selector = {}; fallback_selector = {};
  ordinary_character = {}; fallback_character = {}; ordinary_context = {}; first_row = {};
  ordinary_stores = {}; ordinary_slots = {};
  missing_context = index == 4;
  bases = {100000, 100000, 100000, 4000000001, -100000};
  if (index == 5) bases.fill(0);
  for (std::size_t i = 0; i != ordinary_stores.size(); ++i) {
    ordinary_store_ptrs[i] = ordinary_stores[i].data();
    Put(ordinary_stores[i].data(), 0x20, ordinary_slots[i].data());
    Put(ordinary_stores[i].data(), 0x2C, std::int32_t{16});
  }
  Put(ordinary_regiment.data(), 0x10, source_regiment_id);
  Put(ordinary_regiment.data(), 0x12C, selected_character_id);
  Put(ordinary_regiment.data(), 0x130, std::int32_t{-1});
  Put(ordinary_slots[0][1].data(), 8, ordinary_regiment.data());
  Put(fallback_regiment.data(), 0x10, std::int32_t{-1});
  Put(fallback_regiment.data(), 0x12C, selected_character_id);
  Put(fallback_regiment.data(), 0x130, std::int32_t{-1});
  Put(selector.data(), 0x10, nested_selector_id);
  Put(selector.data(), 0x128, selected_character_id);
  Put(ordinary_slots[1][2].data(), 8, selector.data());
  Put(fallback_selector.data(), 0x10, std::int32_t{-1});
  Put(fallback_selector.data(), 0x128, selected_character_id);
  Put(ordinary_character.data(), 0x18, selected_character_id);
  Put(fallback_character.data(), 0x18, std::int32_t{-1});
  Put(slots[3][13].data(), 8, ordinary_character.data());
  Put(first_row.data(), 8, source_regiment_id);
  Put(regiments[0].data(), 0x20, first_row.data());
  Put(regiments[0].data(), 0x2C, std::int32_t{1});
  Put(types[0].data(), 0x38, std::uint32_t{0});
  Put(types[0].data(), 0x260, std::int32_t{-1});
  if (index == 1 || index == 2) {
    Put(ordinary_regiment.data(), 0x130, nested_selector_id);
    if (index == 1) Put(ordinary_regiment.data(), 0x12C, std::int32_t{-1});
  }
  if (index == 3) {
    Put(regiments[0].data(), 0x2C, std::int32_t{0});
    Put(regiments[0].data(), 0x20, static_cast<void *>(nullptr));
  }
  Put(ordinary_context.data(), 0x68, keys.data());
  Put(ordinary_context.data(), 0x74, std::int32_t{index == 5 ? 0 : 2});
  Put(ordinary_context.data(), 0xD0, values.data());
  regiment_fallback = fallback_regiment.data(); selector_fallback = fallback_selector.data();
  character_fallback = fallback_character.data();
  bindings.ordinary_stat_inputs_enabled = true;
  bindings.ordinary_regiment_storage_slot = &ordinary_store_ptrs[0];
  bindings.ordinary_regiment_fallback_slot = &regiment_fallback;
  bindings.ordinary_selector_storage_slot = &ordinary_store_ptrs[1];
  bindings.ordinary_selector_fallback_slot = &selector_fallback;
  bindings.ordinary_character_fallback_slot = &character_fallback;
  bindings.get_character_modifier_aggregator = OrdinaryAggregator;
  for (std::size_t i = 0; i != bases.size(); ++i) bindings.ordinary_stat_loaded_bases[i] = &bases[i];
  if (index == 6) bindings.ordinary_stat_loaded_bases[4] = nullptr;
  const auto source_before = regiments;
  const auto context_before = ordinary_context;
  xar::game::CombatSimulationInputsSnapshot output{};
  const xar::game::CombatSimulationInputsRequest request{1, 2, {enemy}, {player}};
  Require(xar::ck3_12002::ReadCombatSimulationInputs(bindings, Scope(), request, output) ==
      xar::game::ReadCombatSimulationInputsResult::available, "optional source changed target query readiness");
  Require(regiments == source_before && ordinary_context == context_before, "observer mutated source memory");
  const auto army = std::find_if(output.armies.begin(), output.armies.end(),
      [](const auto &row) { return row.army_id == enemy; });
  Require(army != output.armies.end() && army->regiments.size() == 1, "Army identity lost");
  const auto &row = army->regiments.front();
  Require(row.ordinary_stat_inputs_v1.has_value() && row.effective_stats.available, "ordinary source missing");
  const auto &source = *row.ordinary_stat_inputs_v1;
  Require(source.available == (index != 4 && index != 6), "source independent readiness differs");
  Require(source.selected_character_full_id == (index == 2 ? -1 : selected_character_id), "actual selected Character identity differs");
  Require(source.character_resolution == (index == 2 ? "native_fallback" : "generation_resolved"), "fallback selection lost");
  if (index == 5) Require(source.aggregate_count == 0 && source.aggregate_values_q64->empty(), "native empty became missing");
  for (const auto &other : output.armies)
    if (other.army_id == player)
      for (const auto &regiment : other.regiments)
        Require(!regiment.ordinary_stat_inputs_v1.has_value(), "MAA/special row acquired ordinary operands");
  const auto wire = initialization_context_wire::SerializeRegiment(row);
  Require(wire.find("\"ordinary_stat_inputs_v1\":") != std::string::npos, "production serializer lost leaf");
  std::ofstream file(directory / (std::string(name) + ".json"), std::ios::binary);
  file << wire << '\n'; Require(file.good(), "new wire write failed");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "one output directory required");
    const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
    constexpr std::uintptr_t base = 0x100000000ULL;
    auto bound = xar::ck3_12002::BindCombatImage(base, xar::ck3_12002::kExecutableSha256);
    Require(!bound.ordinary_stat_inputs_enabled, "unchanged .2 binder enabled new .3 source");
    xar::ck3_12002::EnableOrdinaryRegimentStatInputs12003(bound, base,
        "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6");
    Require(bound.ordinary_stat_inputs_enabled &&
        reinterpret_cast<std::uintptr_t>(bound.ordinary_stat_loaded_bases[0]) == base + 0x5C69BD0 &&
        reinterpret_cast<std::uintptr_t>(bound.ordinary_stat_loaded_bases[3]) == base + 0x5C69BE0 &&
        reinterpret_cast<std::uintptr_t>(bound.ordinary_character_fallback_slot) == base + 0x5C67570,
        "exact .3 ordinary binding differs");
    const std::array<const char *, 7> names{"direct", "nested", "native_character_fallback",
        "empty_first_row_native_fallback", "unavailable_context", "native_empty_zero", "unavailable_base"};
    for (std::size_t i = 0; i != names.size(); ++i) RunCase(directory, static_cast<int>(i), names[i]);
    std::cout << "7 new ordinary source/wire cases; synthetic memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
