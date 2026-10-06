// SOURCE_PREPARED only. Root owns the FIRST build and execution.
// Eight new whole Strength-reader/production-serializer scenes; no game calls.
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;
constexpr std::int32_t kUnit = 67108883;
constexpr std::int32_t kArmy = 33554443;
constexpr std::int32_t kProvince = 470;
constexpr std::int32_t kCommander = 29829;
constexpr std::int32_t kOwner = 50331848; // low24=200, Character generation3.
constexpr std::int32_t kRegiment = 100663299; // low24=3, ArRg generation6.
constexpr std::int32_t kFleet = 16777217;
constexpr std::int32_t kFallbackFleet = 33554434;
constexpr std::int32_t kStaleFleetRequest = 50331649;
constexpr std::int32_t kStaleCommanderRequest = 16807045; // generation1, low24=29829.
constexpr std::uint16_t kTerrainOrdinal = 0x301;
constexpr std::uint32_t kTerrainMagic = 0x4744624FU;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}

struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  std::vector<Region> regions;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template <typename T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof value);
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> result;
    for (const auto &region : regions)
      result.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return result;
  }
};

struct Registry {
  Memory &memory;
  void *storage;
  void *table;
  void *fallback = nullptr;
  Registry(Memory &source, std::int32_t capacity)
      : memory(source), storage(source.Allocate(0x30)),
        table(source.Allocate(static_cast<std::size_t>(capacity) * 16)) {
    memory.Put(storage, 0x20, table);
    memory.Put(storage, 0x2C, capacity);
  }
  void Add(std::int32_t full_id, void *object, std::size_t id_offset = 0x10) {
    const auto index = static_cast<std::uint32_t>(full_id) & 0x00FFFFFFU;
    memory.Put(table, static_cast<std::size_t>(index) * 16 + 8, object);
    memory.Put(object, id_offset, full_id);
  }
};

struct Fixture;
Fixture *active = nullptr;

struct Fixture {
  Memory memory;
  Registry units{memory, 20}, armies{memory, 12}, regiments{memory, 4};
  Registry fleets{memory, 3}, characters{memory, 29830};
  void *unit = memory.Allocate(0x180);
  void *army = memory.Allocate(0x210);
  void *regiment = memory.Allocate(0x150);
  void *province = memory.Allocate(0x864);
  void *province_definition = memory.Allocate(0xC0);
  void *terrain = memory.Allocate(0x780);
  void *fleet = memory.Allocate(0x30);
  void *fallback_fleet = memory.Allocate(0x30);
  void *commander = memory.Allocate(0x30);
  void *fallback_commander = memory.Allocate(0x30);
  void *owner = memory.Allocate(0x30);
  void *aggregator = memory.Allocate(0xD8);
  void *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x150);
  void *province_table = memory.Allocate(471 * 8);
  void *regiment_ids = memory.Allocate(4);
  ck3_12002::ArmyBindings bindings{};
  bool fleet_branch = true;
  bool missing_fixed_output = false;
  bool missing_numeric_keys = false;
  std::uint16_t terrain_ordinal = kTerrainOrdinal;
  std::int64_t terrain_modifier = 0;
  std::int64_t fixed_modifier = 0;
  std::int64_t loaded_loss = 500000;
  std::int64_t divisor_floor = 100000;
  std::int64_t max_loss = 1000000;
  std::int32_t sentinel = -1;
  std::int64_t observed_current_rate = 0;
  std::int64_t loaded_gain = 2000000;
  std::int64_t land_component = -600000;
  std::int64_t land_slope = 0;
  std::int64_t land_min_loss = 0;
  void *expected_selected_commander = commander;
  std::size_t fleet_calls = 0;
  std::size_t terrain_calls = 0;
  std::size_t fixed_calls = 0;
  std::size_t current_rate_calls = 0;

  static std::int32_t Current(void *receiver, std::uint8_t flags) {
    Check(active && receiver == static_cast<std::byte *>(active->army) + 0x38 && flags == 0,
          "whole Strength current-soldier getter ABI changed");
    return 160;
  }
  static std::int32_t Maximum(void *receiver) {
    Check(active && receiver == active->army, "whole Strength maximum-soldier receiver changed");
    return 240;
  }
  static bool Fleet(void *receiver) {
    Check(active && receiver == active->army, "fleet predicate requires actual resolved CArmy");
    ++active->fleet_calls;
    return active->fleet_branch;
  }
  static std::int64_t *CurrentRate(void *receiver, std::int64_t *output,
                                 void *province_argument, void *details) {
    Check(active && receiver == active->army && province_argument == active->province && details == nullptr,
          "observed current rate requires actual whole-reader CArmy/Province/null-details ABI");
    ++active->current_rate_calls;
    *output = active->observed_current_rate;
    return output;
  }
  static void *Aggregator(void *receiver) {
    Check(active && receiver == active->expected_selected_commander,
          "modifier aggregator must use selected native commander or supplied fallback");
    return active->aggregator;
  }
  static std::int64_t *Modifier(void *receiver, std::int64_t *output, std::int32_t ordinal) {
    Check(active && receiver == static_cast<std::byte *>(active->aggregator) + 0x68,
          "modifier numeric reader must use aggregator+68");
    if (ordinal == 0x1A9) {
      ++active->fixed_calls;
      if (active->missing_fixed_output) return nullptr;
      *output = active->missing_numeric_keys ? 0 : active->fixed_modifier;
    } else {
      Check(ordinal == active->terrain_ordinal, "terrain reader must use actual terrain+772 ordinal");
      ++active->terrain_calls;
      // Synthetic numeric helper reproduces native absent/FFFF-key numeric0.
      // Returning0 is an observed numeric result; nullptr is a read failure.
      *output = active->missing_numeric_keys ? 0 : active->terrain_modifier;
    }
    return output;
  }
  static bool Resupply(void *owner_argument, void *province_argument) {
    Check(active && owner_argument == active->owner && province_argument == active->province,
          "07 actual land-resupply callback must use resolved owner/current Province");
    return true;
  }
  static bool LandCondition(void *province_argument) {
    Check(active && province_argument == active->province, "07 actual land condition Province receiver");
    return true;
  }
  static std::int64_t *LandComponent(std::int64_t *output, void *receiver,
      std::int32_t ordinal, void *details, std::int64_t multiplier, std::int32_t mode) {
    Check(active && receiver == static_cast<std::byte *>(active->province) + 0x30 &&
              ordinal == 0x1AB && details == nullptr && multiplier == 100000 && mode == 0,
          "07 actual land component six-argument ABI");
    *output = active->land_component;
    return output;
  }

  Fixture() {
    active = this;
    units.Add(kUnit, unit); armies.Add(kArmy, army); regiments.Add(kRegiment, regiment);
    fleets.Add(kFleet, fleet); characters.Add(kCommander, commander, 0x18);
    characters.Add(kOwner, owner, 0x18);
    memory.Put(fallback_fleet, 0x10, kFallbackFleet);
    memory.Put(fallback_commander, 0x18, std::int32_t{-1});
    fleets.fallback = fallback_fleet; characters.fallback = fallback_commander;
    memory.Put(unit, 0x20, province); memory.Put(unit, 0x174, kOwner); memory.Put(unit, 0x178, kArmy);
    memory.Put(army, 0x14, std::uint32_t{0x41726D79});
    memory.Put(army, 0x120, kCommander); memory.Put(army, 0x124, kUnit); memory.Put(army, 0x12C, kFleet);
    memory.Put(army, 0x38, regiment_ids); memory.Put(army, 0x40, std::int32_t{1});
    memory.Put(army, 0x44, std::int32_t{1}); memory.Put(regiment_ids, 0, kRegiment);
    memory.Put(army, 0x180, std::int64_t{9000000});
    memory.Put(regiment, 0x14, std::uint32_t{0x41725267});
    memory.Put(regiment, 0x38, std::int32_t{160}); memory.Put(regiment, 0x3C, std::int32_t{240});
    memory.Put(regiment, 0x40, std::int64_t{300000});
    memory.Put(province, 0x10, kProvince); memory.Put(province, 0x85C, std::uint32_t{0x50726F76});
    memory.Put(province, 0x20, province_definition); memory.Put(province_definition, 0xB8, terrain);
    memory.Put(terrain, 0x38, kTerrainMagic); memory.Put(terrain, 0x772, terrain_ordinal);
    memory.Put(fleet, 0x20, std::int32_t{1024}); memory.Put(fallback_fleet, 0x20, std::int32_t{1024});
    memory.Put(state, 8, std::int32_t{1000}); memory.Put(state, 0xA0, data);
    memory.Put(data, 0x140, province_table); memory.Put(data, 0x14C, std::int32_t{471});
    memory.Put(province_table, static_cast<std::size_t>(kProvince) * 8, province);
    bindings.enabled = true; bindings.game_state_slot = &state;
    bindings.unit_storage_slot = &units.storage; bindings.internal_army_storage_slot = &armies.storage;
    bindings.regiment_storage_slot = &regiments.storage;
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    bindings.get_army_monthly_supply_change = CurrentRate;
    auto &native = bindings.monthly_loss_budget_bindings;
    // Borrow qualified callback/registry slots without enabling the old monthly producer.
    native.is_army_fleet_supply_active = Fleet;
    native.fleet_storage_slot = &fleets.storage; native.fleet_fallback_slot = &fleets.fallback;
    native.fleet_date_sentinel = &sentinel;
    native.character_storage_slot = &characters.storage; native.character_fallback_slot = &characters.fallback;
    native.get_character_modifier_aggregator = Aggregator; native.read_character_modifier = Modifier;
    auto &new_binding = bindings.current_fleet_supply_tick_bindings;
    new_binding.enabled = true; new_binding.loaded_fleet_loss_raw = &loaded_loss;
    new_binding.loaded_divisor_floor_raw = &divisor_floor; new_binding.loaded_max_loss_raw = &max_loss;
  }

  void EnableIndependentLandOutputs() {
    auto &resupply = bindings.current_land_resupply_bindings;
    resupply.enabled = true; resupply.is_resupply_eligible = Resupply;
    resupply.is_army_fleet_supply_active = Fleet;
    resupply.character_storage_slot = &characters.storage; resupply.loaded_gain_raw = &loaded_gain;
    auto &land = bindings.current_land_supply_rate_bindings;
    land.enabled = true; land.province_component_condition = LandCondition;
    land.read_province_component = LandComponent;
    land.character_storage_slot = &characters.storage; land.character_fallback_slot = &characters.fallback;
    land.get_character_modifier_aggregator = Aggregator; land.read_character_modifier = Modifier;
    land.loaded_excess_slope_raw = &land_slope; land.loaded_min_loss_raw = &land_min_loss;
    land.loaded_divisor_floor_raw = &divisor_floor; land.loaded_max_loss_raw = &max_loss;
  }

  game::ArmyStrengthSnapshot Observe() {
    const auto before = memory.Snapshot();
    const std::array<ck3_12002::ArmyStrengthScope, 1> scope{{
        {kUnit, game::ArmyStrengthScopeRole::player, {}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) ==
              game::ReadArmyStrengthsResult::available && rows.size() == 1,
          "FIRST fleet inputs must enter actual whole Strength reader and preserve query availability");
    const auto &row = rows[0];
    Check(row.available && row.army_id == kUnit && row.native_carmy_id_observable &&
              row.native_carmy_id == kArmy && row.current_soldiers == 160 &&
              row.maximum_soldiers == 240 && row.ai_base_power_raw == 300000 && row.regiment_count == 1 &&
              row.current_supply_raw == std::int64_t{9000000} &&
              row.current_supply_change_monthly_raw == observed_current_rate,
          "optional fleet family changed whole-row identity, strength, stored supply or observed current rate");
    Check(row.current_fleet_supply_tick_inputs_v1.has_value(),
          "whole Strength collector hook must attach the new family; direct leaf/transplant forbidden");
    const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Check(leaf.subject_army_id == kUnit && leaf.subject_carmy_id == kArmy && leaf.province_id == kProvince,
          "FIRST fleet collector must use the same captured Unit/CArmy/validated Province");
    Check(before == memory.Snapshot(), "whole Strength observation wrote synthetic game input memory");
    Check(current_rate_calls == 1, "whole reader must retain independently observed current rate once");
    return row;
  }
};

void Available(const game::ArmyCurrentFleetSupplyTickInputsV1 &leaf) {
  Check(leaf.status == "available" && leaf.ready && !leaf.unavailable_reason,
        "complete fleet raw operands must be independently available");
}

void Emit(const std::filesystem::path &directory, const char *name,
          const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  // Actual production whole-row serializer, including all existing families.
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &output, const std::vector<std::int32_t> &values) {
        output += '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
          if (i != 0) output += ',';
          output += std::to_string(values[i]);
        }
        output += ']';
      }, [](std::string &output, std::string_view value) {
        output += '"'; output += value; output += '"';
      });
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  Check(static_cast<bool>(output), "FIRST fleet whole wire open failed");
  output << wire << '\n';
  Check(static_cast<bool>(output), "FIRST fleet whole wire write failed");
}

void Scenes(const std::filesystem::path &directory) {
  {
    Fixture fixture;
    const auto row = fixture.Observe(); const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Available(leaf);
    Check(leaf.current_native_date_low32 == 1000 && leaf.fleet_day_raw == 1024 &&
              leaf.loaded_fleet_day_sentinel_raw == -1 && leaf.terrain_magic_38_raw == kTerrainMagic &&
              leaf.terrain_modifier_772_raw == std::int64_t{0} &&
              leaf.loaded_fleet_loss_raw == std::int64_t{500000} &&
              leaf.commander_modifier_1a9_raw == std::int64_t{0} &&
              leaf.loaded_divisor_floor_raw == std::int64_t{100000} &&
              leaf.loaded_max_loss_raw == std::int64_t{1000000} &&
              fixture.terrain_calls == 1 && fixture.fixed_calls == 1,
          "today-suppressed date must still collect complete downstream payload; observed today0 remains separate");
    Emit(directory, "01-date-opens-next-day", row);
  }
  {
    Fixture fixture; fixture.memory.Put(fixture.fleet, 0x20, std::int32_t{2000});
    fixture.memory.Put(fixture.province_definition, 0xB8, static_cast<void *>(nullptr));
    const auto row = fixture.Observe(); const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Check(!leaf.ready && leaf.status == "unavailable" &&
              leaf.unavailable_reason == "native_fleet_supply_terrain_unavailable" &&
              leaf.current_native_date_low32 == 1000 && leaf.fleet_day_raw == 2000 &&
              !leaf.terrain_magic_38_raw && !leaf.loaded_fleet_loss_raw && fixture.terrain_calls == 0,
          "future date and unavailable downstream raw fields must survive partial optional family");
    Emit(directory, "02-still-future-partial-downstream", row);
  }
  {
    Fixture fixture; fixture.memory.Put(fixture.fleet, 0x20, std::int32_t{-1});
    fixture.terrain_modifier = 1; fixture.bindings.current_fleet_supply_tick_bindings.loaded_fleet_loss_raw = nullptr;
    const auto row = fixture.Observe(); const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Available(leaf);
    Check(leaf.terrain_modifier_772_raw == std::int64_t{1} && !leaf.loaded_fleet_loss_raw &&
              !leaf.commander_modifier_1a9_raw && !leaf.loaded_divisor_floor_raw &&
              !leaf.loaded_max_loss_raw && fixture.terrain_calls == 1 && fixture.fixed_calls == 0,
          "signed positive terrain modifier suppresses without demanding absent base/fixed modifier");
    Emit(directory, "03-positive-terrain772", row);
  }
  {
    Fixture fixture; fixture.memory.Put(fixture.army, 0x12C, kStaleFleetRequest);
    fixture.memory.Put(fixture.army, 0x120, kStaleCommanderRequest);
    fixture.expected_selected_commander = fixture.fallback_commander;
    fixture.terrain_ordinal = 0xFFFF; fixture.memory.Put(fixture.terrain, 0x772, fixture.terrain_ordinal);
    fixture.missing_numeric_keys = true;
    const auto row = fixture.Observe(); const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Available(leaf);
    Check(leaf.fleet_raw_full_id == kStaleFleetRequest && leaf.fleet_resolved_full_id == kFallbackFleet &&
              leaf.fleet_used_native_fallback == true && leaf.fleet_day_raw == 1024 &&
              leaf.commander_raw_full_id == kStaleCommanderRequest && leaf.commander_resolved_full_id == -1 &&
              leaf.commander_used_native_fallback == true && leaf.terrain_modifier_772_id == 0xFFFF &&
              leaf.terrain_modifier_772_raw == std::int64_t{0} &&
              leaf.commander_modifier_1a9_raw == std::int64_t{0} &&
              fixture.terrain_calls == 1 && fixture.fixed_calls == 1,
          "stale full IDs must select actual supplied fallback; numeric absent/FFFF0 is not a read failure or Character gate");
    Emit(directory, "04-native-fallback-absent-numeric-key", row);
  }
  {
    Fixture fixture; fixture.fixed_modifier = -100000; fixture.divisor_floor = 0;
    const auto row = fixture.Observe(); const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Available(leaf);
    Check(leaf.commander_modifier_1a9_raw == std::int64_t{-100000} &&
              leaf.loaded_divisor_floor_raw == std::int64_t{0} &&
              leaf.loaded_fleet_loss_raw == std::int64_t{500000} &&
              leaf.loaded_max_loss_raw == std::int64_t{1000000},
          "Fleet zero-divisor raw inputs must be retained for service's unsigned4294967295 path");
    Emit(directory, "05-fleet-zero-divisor", row);
  }
  {
    Fixture fixture; fixture.missing_fixed_output = true;
    const auto row = fixture.Observe(); const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Check(!leaf.ready && leaf.status == "unavailable" &&
              leaf.unavailable_reason == "native_fleet_supply_fixed_modifier_output_unavailable" &&
              leaf.terrain_modifier_772_raw == std::int64_t{0} &&
              leaf.loaded_fleet_loss_raw == std::int64_t{500000} && !leaf.commander_modifier_1a9_raw &&
              leaf.loaded_divisor_floor_raw == std::int64_t{100000} &&
              leaf.loaded_max_loss_raw == std::int64_t{1000000},
          "needed missing fixed output remains null despite independently observed today0");
    Emit(directory, "06-partial-needed-fixed-modifier", row);
  }
  {
    Fixture fixture; fixture.fleet_branch = false; fixture.observed_current_rate = -600000;
    fixture.EnableIndependentLandOutputs();
    fixture.memory.Put(fixture.province_definition, 0xB8, static_cast<void *>(nullptr));
    fixture.bindings.current_fleet_supply_tick_bindings.loaded_fleet_loss_raw = nullptr;
    const auto row = fixture.Observe(); const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Check(leaf.status == "not_fleet" && leaf.ready && !leaf.unavailable_reason &&
              leaf.native_fleet_branch_applicable == false && !leaf.current_native_date_low32 &&
              !leaf.fleet_raw_full_id && !leaf.fleet_day_raw && !leaf.terrain_magic_38_raw &&
              !leaf.loaded_fleet_loss_raw && !leaf.commander_modifier_1a9_raw,
          "not_fleet must need no Fleet/downstream reads");
    Check(row.current_land_resupply_v1 && row.current_land_supply_rate_inputs_v1 &&
              row.current_land_resupply_v1->current_observation_ready &&
              row.current_land_resupply_v1->native_land_branch_applicable == true &&
              row.current_land_resupply_v1->native_resupply_eligible == true &&
              row.current_land_resupply_v1->loaded_gain_raw == std::int64_t{2000000} &&
              row.current_land_supply_rate_inputs_v1->current_observation_ready &&
              row.current_land_supply_rate_inputs_v1->province_component_raw == std::int64_t{-600000} &&
              row.current_land_supply_rate_inputs_v1->commander_modifier_1a9_raw == std::int64_t{0} &&
              fixture.fleet_calls == 1 && fixture.terrain_calls == 0 && fixture.fixed_calls == 1,
          "new nonfleet family must preserve independently captured production land/resupply operands and reuse known branch");
    Emit(directory, "07-not-fleet", row);
  }
  {
    Fixture fixture; fixture.memory.Put(fixture.state, 8, std::int32_t{2147483640});
    fixture.memory.Put(fixture.fleet, 0x20, std::int32_t{-2147483620});
    const auto row = fixture.Observe(); const auto &leaf = *row.current_fleet_supply_tick_inputs_v1;
    Available(leaf);
    Check(leaf.current_native_date_low32 == 2147483640 && leaf.fleet_day_raw == -2147483620 &&
              leaf.loaded_fleet_day_sentinel_raw == -1 &&
              leaf.loaded_fleet_loss_raw == std::int64_t{500000},
          "raw signed low32 clock/Fleet date must survive whole serializer for conditional low32+24U wrap");
    Emit(directory, "08-signed-clock-wrap", row);
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir", "FIRST fixture requires --wire-dir PATH");
    const std::filesystem::path directory(argv[2]);
    std::filesystem::create_directories(directory);
    Scenes(directory);
    std::cout << "PASS: eight FIRST whole ReadArmyStrengthsForScope + AppendArmyStrengthV1 fleet input wires; synthetic callbacks only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIRST FLEET FIXTURE RED: " << error.what() << '\n';
    return 1;
  }
}
