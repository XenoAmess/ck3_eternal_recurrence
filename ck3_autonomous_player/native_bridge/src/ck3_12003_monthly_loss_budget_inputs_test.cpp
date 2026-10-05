#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
template <class T, class Bytes> void Put(Bytes &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
void *expected_unit = nullptr, *expected_army = nullptr;
void *expected_character = nullptr, *expected_context = nullptr;
bool in_combat = false, gathering = false, fleet_active = false;
bool unstable = false;
int combat_calls = 0, modifier_calls = 0;
std::uint16_t expected_modifier = 513;
std::int64_t modifier_raw = -25'000;
bool Combat(void *unit) {
  Check(unit == expected_unit, "combat gets actual Unit");
  ++combat_calls;
  return unstable ? (combat_calls % 2 != 0) : in_combat;
}
bool Gathering(void *unit) {
  Check(unit == expected_unit, "gathering gets actual Unit"); return gathering;
}
bool Fleet(void *army) {
  Check(army == expected_army, "fleet leaf gets actual Army"); return fleet_active;
}
bool Siege(void *army) {
  Check(army == expected_army, "siege gets actual Army"); return true;
}
bool Eligible(void *) { return true; }
std::int32_t PublicState(void *) { return 3; }
std::int32_t Current(void *, std::uint8_t) { return 12; }
std::int32_t Maximum(void *) { return 12; }
std::int32_t SupplyBudget(void *) { return 0; }
std::int32_t WholeBudget(std::int64_t rate, void *army) {
  Check(army == expected_army, "budget receives Army and rate VALUE");
  if (rate < 0) rate = 0;
  if (rate > 100'000) rate = 100'000;
  return static_cast<std::int32_t>(12 * rate / 100'000);
}
std::int64_t *Capacity(std::int64_t *out, void *army, void *details) {
  Check(army == expected_army && details == nullptr, "capacity actual receiver");
  *out = 2'000'000; return out;
}
std::int64_t *Change(void *army, std::int64_t *out, void *, void *details) {
  Check(army == expected_army && details == nullptr, "change readonly null breakdown");
  *out = -100'000; return out;
}
void *Context(void *character) {
  Check(character == expected_character, "actual resolved commander context");
  return expected_context;
}
std::int64_t *Modifier(void *container, std::int64_t *out, std::int32_t ordinal) {
  Check(container == static_cast<std::byte *>(expected_context) + 0x68 &&
        ordinal == expected_modifier, "actual current province selects dynamic ordinal");
  ++modifier_calls;
  *out = modifier_raw; return out;
}

std::string Wire(const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
          if (i != 0) out += ',';
          out += std::to_string(values[i]);
        }
        out += ']';
      },
      [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  return wire;
}
void Emit(const std::filesystem::path &directory, const char *label,
          const game::ArmyStrengthSnapshot &row) {
  std::filesystem::create_directories(directory);
  std::ofstream file(directory / (std::string(label) + ".json"), std::ios::binary);
  Check(static_cast<bool>(file), "wire artifact output");
  file << Wire(row) << '\n';
}

void Cases(const std::filesystem::path &directory) {
  constexpr std::int32_t unit_id = 0x01000001, army_id = 0x02000001;
  constexpr std::int32_t commander_id = 0x03000001, fleet_id = 0x04000001;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x200> army{};
  std::array<std::byte, 0x50> r1{}, r2{}, fleet{}, character{}, invalid_character{};
  std::array<std::byte, 0x80> context{};
  std::array<std::byte, 0x30> province{};
  std::array<std::byte, 0xC0> province_type{};
  std::array<std::byte, 0x780> definition{};
  std::array<std::byte, 0xB0> state{};
  std::vector<std::byte> game_data(0x2B000);
  std::array<std::byte, 0x30> units{}, armies{}, regiments{}, characters{}, fleets{};
  std::array<std::byte, 0x30> unit_slots{}, army_slots{}, regiment_slots{}, character_slots{}, fleet_slots{};
  std::array<std::int32_t, 2> ids{0x06000002, 0x05000001};
  std::array<void *, 2> provinces{nullptr, province.data()};
  std::array<std::int32_t, 3> levels{20, 10, 0};
  std::array<std::int64_t, 3> fractions{0, 0, 50'000};
  const std::int32_t *level_pointer = levels.data();
  const std::int64_t *fraction_pointer = fractions.data();
  std::int32_t level_count = 3, fraction_count = 3, sentinel = -1, grace = 1;
  std::int64_t siege_rate = 16'666, raid_rate = 16'666;
  Put(unit, 0x10, unit_id); Put(unit, 0x178, army_id);
  Put(unit, 0x170, std::int32_t{0}); Put(unit, 0x20, static_cast<void *>(province.data()));
  Put(army, 0x10, army_id); Put(army, 0x124, unit_id);
  Put(army, 0x120, commander_id); Put(army, 0x12C, fleet_id);
  Put(army, 0x38, static_cast<void *>(ids.data()));
  Put(army, 0x40, std::int32_t{2}); Put(army, 0x44, std::int32_t{2});
  Put(army, 0x180, std::int64_t{1'050'000}); Put(army, 0x1E8, std::int32_t{42});
  Put(r1, 0x10, ids[1]); Put(r2, 0x10, ids[0]);
  for (auto *row : {&r1, &r2}) Put(*row, 0x14, std::uint32_t{0x41725267});
  Put(r1, 0x38, std::int32_t{9}); Put(r1, 0x3C, std::int32_t{9});
  Put(r2, 0x38, std::int32_t{3}); Put(r2, 0x3C, std::int32_t{3});
  Put(character, 0x18, commander_id); Put(character, 0x1C, std::uint32_t{0x43686172});
  Put(invalid_character, 0x18, std::int32_t{-1});
  Put(fleet, 0x10, fleet_id); Put(fleet, 0x14, std::uint32_t{0x466C6574});
  Put(fleet, 0x20, std::int32_t{241});
  Put(province, 0x10, std::int32_t{1});
  Put(province, 0x20, static_cast<void *>(province_type.data()));
  Put(province_type, 0xB8, static_cast<void *>(definition.data()));
  Put(definition, 0x770, expected_modifier);
  Put(state, 8, std::int32_t{240}); Put(state, 0x9C, std::int32_t{10});
  Put(state, 0xA0, static_cast<void *>(game_data.data()));
  Put(game_data, 0x140, static_cast<void *>(provinces.data()));
  Put(game_data, 0x14C, std::int32_t{2});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(regiment_slots, 0x18, static_cast<void *>(r1.data()));
  Put(regiment_slots, 0x28, static_cast<void *>(r2.data()));
  Put(character_slots, 0x18, static_cast<void *>(character.data()));
  Put(fleet_slots, 0x18, static_cast<void *>(fleet.data()));
  for (auto *storage : {&units, &armies, &regiments, &characters, &fleets})
    Put(*storage, 0x2C, std::int32_t{3});
  Put(units, 0x20, static_cast<void *>(unit_slots.data()));
  Put(armies, 0x20, static_cast<void *>(army_slots.data()));
  Put(regiments, 0x20, static_cast<void *>(regiment_slots.data()));
  Put(characters, 0x20, static_cast<void *>(character_slots.data()));
  Put(fleets, 0x20, static_cast<void *>(fleet_slots.data()));
  void *units_pointer = units.data(), *armies_pointer = armies.data();
  void *regiments_pointer = regiments.data(), *characters_pointer = characters.data();
  void *fleets_pointer = fleets.data(), *state_pointer = state.data();
  void *fallback_character = invalid_character.data();
  expected_unit = unit.data(); expected_army = army.data();
  expected_character = character.data(); expected_context = context.data();
  ArmyBindings bindings{};
  bindings.enabled = true; bindings.game_state_slot = &state_pointer;
  bindings.unit_storage_slot = &units_pointer;
  bindings.internal_army_storage_slot = &armies_pointer;
  bindings.regiment_storage_slot = &regiments_pointer;
  bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
  bindings.get_unit_state = PublicState;
  bindings.is_regiment_supply_loss_eligible = Eligible;
  bindings.get_army_supply_capacity = Capacity; bindings.get_army_monthly_supply_change = Change;
  bindings.loss_application_inputs_enabled = true;
  bindings.siege_loss_rate_raw = &siege_rate; bindings.raid_loss_rate_raw = &raid_rate;
  bindings.get_army_whole_loss_budget = WholeBudget;
  bindings.get_army_supply_loss_budget = SupplyBudget; bindings.is_army_siege_active = Siege;
  bindings.timing_bindings = {true, &grace};
  auto &monthly = bindings.monthly_loss_budget_bindings;
  monthly.enabled = true; monthly.is_unit_in_combat = Combat;
  monthly.is_unit_gathering = Gathering; monthly.is_army_fleet_supply_active = Fleet;
  monthly.fleet_storage_slot = &fleets_pointer; monthly.fleet_date_sentinel = &sentinel;
  monthly.supply_state_levels_slot = &level_pointer; monthly.supply_state_levels_count = &level_count;
  monthly.supply_state_fractions_slot = &fraction_pointer;
  monthly.supply_state_fractions_count = &fraction_count;
  monthly.character_storage_slot = &characters_pointer;
  monthly.character_fallback_slot = &fallback_character;
  monthly.get_character_modifier_aggregator = Context; monthly.read_character_modifier = Modifier;
  const std::array<ArmyStrengthScope, 1> scope{{{unit_id, game::ArmyStrengthScopeRole::player, {42}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read = [&]() -> game::ArmyStrengthSnapshot {
    Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "unchanged parent production strength remains available");
    return rows[0];
  };
  const auto army_before = army;
  const auto unit_before = unit;
  const auto character_before = character;
  auto row = read();
  const auto &initial = *row.monthly_loss_budget_inputs_v1;
  Check(initial.available && initial.unit_native_170_raw == 0 &&
        bindings.get_unit_state(unit.data()) == 3 &&
        initial.native_unit_in_combat == false && initial.native_unit_gathering == false &&
        initial.native_fleet_supply_loss_suppressed == false && initial.commander_valid == true,
        "legal zero and false are observed, independent of public unit state");
  Check(*initial.loaded_supply_state_levels == std::vector<std::int32_t>{20, 10, 0} &&
        *initial.loaded_supply_state_fractions_raw == std::vector<std::int64_t>{0, 0, 50'000} &&
        initial.commander_supply_modifier_id == 513 && initial.commander_supply_modifier_raw == -25'000 &&
        modifier_calls == 2 && combat_calls == 2, "ordered loaded vectors and actual ordinal are stably sampled twice");
  Check(army == army_before && unit == unit_before && character == character_before,
        "provider invokes no updater and preserves fixture receivers");
  Check(Wire(row).find("\"native_unit_in_combat\":false") != std::string::npos,
        "production serializer publishes actual false");
  Emit(directory, "admitted-commander", row);
  fleet_active = true;
  row = read();
  Check(row.monthly_loss_budget_inputs_v1->native_fleet_supply_loss_suppressed == true,
        "strict future Fleet date suppresses supply loss");
  Emit(directory, "fleet-future", row);
  Put(fleet, 0x20, std::int32_t{240});
  Check(read().monthly_loss_budget_inputs_v1->native_fleet_supply_loss_suppressed == false,
        "equal Fleet date does not suppress");
  sentinel = 241; Put(fleet, 0x20, std::int32_t{241});
  Check(read().monthly_loss_budget_inputs_v1->native_fleet_supply_loss_suppressed == false,
        "sentinel future date does not suppress");
  Put(army, 0x120, std::int32_t{-1});
  row = read();
  Check(row.monthly_loss_budget_inputs_v1->available &&
        row.monthly_loss_budget_inputs_v1->commander_valid == false &&
        !row.monthly_loss_budget_inputs_v1->commander_supply_modifier_raw.has_value() &&
        !row.monthly_loss_budget_inputs_v1->commander_supply_modifier_id.has_value(),
        "invalid commander is a known branch, with absent modifier operands");
  Emit(directory, "invalid-commander", row);
  Put(unit, 0x170, std::int32_t{3});
  in_combat = true; gathering = true;
  row = read();
  Check(row.monthly_loss_budget_inputs_v1->unit_native_170_raw == 3 &&
        row.monthly_loss_budget_inputs_v1->native_unit_in_combat == true &&
        row.monthly_loss_budget_inputs_v1->native_unit_gathering == true,
        "admission publishes direct native170 and actual booleans");
  Emit(directory, "admission-rejected", row);
  level_count = 0; fraction_count = 0;
  row = read();
  Check(row.monthly_loss_budget_inputs_v1->available &&
        row.monthly_loss_budget_inputs_v1->loaded_supply_state_levels->empty() &&
        row.monthly_loss_budget_inputs_v1->loaded_supply_state_fractions_raw->empty(),
        "observed nonpositive native vector counts are legal empty arrays");
  Emit(directory, "empty-tables", row);
  monthly.is_unit_in_combat = nullptr;
  row = read();
  Check(!row.monthly_loss_budget_inputs_v1->available &&
        !row.monthly_loss_budget_inputs_v1->native_unit_in_combat.has_value() &&
        row.monthly_loss_budget_inputs_v1->unit_native_170_raw == 3,
        "missing leaf stays null while independent operands survive");
  Emit(directory, "partial-inputs", row);
  monthly.is_unit_in_combat = Combat;
  unstable = true; combat_calls = 0;
  row = read();
  Check(!row.monthly_loss_budget_inputs_v1->available &&
        row.monthly_loss_budget_inputs_v1->unavailable_reason == "monthly_loss_budget_inputs_changed_during_read" &&
        !row.monthly_loss_budget_inputs_v1->unit_native_170_raw.has_value(),
        "changed double sample does not publish a mixed operand frame");
  Emit(directory, "changed-inputs", row);
  unstable = false;
  monthly.enabled = false;
  Check(!read().monthly_loss_budget_inputs_v1.has_value(), "older binder leaves additive block absent");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire output directory required");
    Cases(argv[1]);
    std::cout << "PASS: production monthly budget input reader and wire; seven retained frames\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n'; return 1;
  }
}
