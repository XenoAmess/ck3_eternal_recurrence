#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar;
using namespace xar::ck3_12002;
template<class T, class Bytes> void Put(Bytes &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
void Check(bool value, const char *message) { if (!value) throw std::runtime_error(message); }
void *expected_owner = nullptr, *expected_commander = nullptr, *expected_province = nullptr;
std::array<std::byte, 0xD8> aggregator{};
bool condition = true, fleet = false;
std::int64_t component = -600000, modifier = 100000;
std::int32_t component_calls = 0, modifier_calls = 0;
std::int32_t Count(void *, std::uint8_t) { return 0; }
std::int32_t Maximum(void *) { return 0; }
bool Fleet(void *) { return fleet; }
bool Eligible(void *) { return true; }
bool SameSide(void *, void *, void *) { return false; }
bool Admission(void *owner, void *province) {
  Check(owner == expected_owner && province == expected_province, "resupply uses actual owner");
  return true;
}
std::int32_t Limit(void *province, void *owner, void *commander, void *detail) {
  Check(province == expected_province && owner == expected_owner &&
        commander == expected_commander && detail == nullptr, "native limit context");
  return 100;
}
std::int32_t Usage(void *province, void *owner, std::int32_t mode, std::int64_t *detail) {
  Check(province == expected_province && owner == expected_owner && mode == 0 &&
        detail == nullptr, "native current Province usage context");
  return 80;
}
bool Condition(void *province) {
  Check(province == expected_province, "Province condition receiver"); return condition;
}
std::int64_t *Component(std::int64_t *out, void *receiver, std::int32_t ordinal,
                        void *detail, std::int64_t multiplier, std::int32_t mode) {
  Check(receiver == static_cast<std::byte *>(expected_province) + 0x30 &&
        ordinal == 0x1AB && detail == nullptr && multiplier == 100000 && mode == 0,
        "Province+30 exact six argument modifier ABI");
  ++component_calls; *out = component; return out;
}
void *Aggregator(void *character) {
  Check(character == expected_commander, "native commander or fallback, not owner");
  return aggregator.data();
}
std::int64_t *Modifier(void *receiver, std::int64_t *out, std::int32_t ordinal) {
  Check(receiver == aggregator.data() + 0x68 && ordinal == 0x1A9,
        "generic sparse subtable and fixed1A9, not monthly dynamic ordinal");
  ++modifier_calls; *out = modifier; return out;
}
void Emit(const std::filesystem::path &directory, const char *name,
          const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
          if (i != 0) out += ','; out += std::to_string(values[i]);
        }
        out += ']';
      }, [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::filesystem::create_directories(directory);
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  Check(static_cast<bool>(output), "new rate wire output"); output << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  constexpr std::int32_t unit_id = 0x01000001, army_id = 0x02000001;
  constexpr std::int32_t owner_id = 0x03000001, commander_id = 0x03000002;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x208> army{};
  std::array<std::byte, 0x30> owner{}, commander{}, fallback{};
  std::array<std::byte, 0x864> province{};
  std::array<std::byte, 0x150> data{};
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x30> units{}, armies{}, characters{}, regiments{};
  std::array<std::byte, 0x30> unit_slots{}, army_slots{}, character_slots{};
  std::array<void *, 2> province_slots{nullptr, province.data()};
  Put(unit, 0x10, unit_id); Put(unit, 0x20, static_cast<void *>(province.data()));
  Put(unit, 0x174, owner_id); Put(unit, 0x178, army_id);
  Put(army, 0x10, army_id); Put(army, 0x14, std::uint32_t{0x41726D79});
  Put(army, 0x120, commander_id); Put(army, 0x124, unit_id);
  Put(owner, 0x18, owner_id); Put(commander, 0x18, commander_id); Put(fallback, 0x18, std::int32_t{-1});
  Put(province, 0x10, std::int32_t{1}); Put(province, 0x85C, std::uint32_t{0x50726F76});
  Put(data, 0x140, static_cast<void *>(province_slots.data())); Put(data, 0x14C, std::int32_t{2});
  Put(state, 0xA0, static_cast<void *>(data.data()));
  Put(unit_slots, 0x18, static_cast<void *>(unit.data())); Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(character_slots, 0x18, static_cast<void *>(owner.data())); Put(character_slots, 0x28, static_cast<void *>(commander.data()));
  const auto storage = [&](auto &header, auto &slots, std::int32_t capacity) {
    Put(header, 0x20, static_cast<void *>(slots.data())); Put(header, 0x2C, capacity);
  };
  storage(units, unit_slots, 2); storage(armies, army_slots, 2); storage(characters, character_slots, 3);
  void *unit_storage = units.data(), *army_storage = armies.data(), *regiment_storage = regiments.data();
  void *character_storage = characters.data(), *state_pointer = state.data(), *fallback_pointer = fallback.data();
  expected_owner = owner.data(); expected_commander = commander.data(); expected_province = province.data();
  std::int64_t loaded_gain = 2345678, slope = 10000, min_loss = 200000, max_loss = 5000000, floor = 300000;
  ArmyBindings bindings{};
  bindings.enabled = true; bindings.game_state_slot = &state_pointer;
  bindings.unit_storage_slot = &unit_storage; bindings.internal_army_storage_slot = &army_storage;
  bindings.regiment_storage_slot = &regiment_storage;
  bindings.get_army_current_soldiers = Count; bindings.get_army_maximum_soldiers = Maximum;
  bindings.monthly_loss_budget_bindings.character_storage_slot = &character_storage;
  bindings.province_supply_character_fallback_slot = &fallback_pointer;
  bindings.get_province_supply_limit = Limit; bindings.get_province_supply_usage = Usage;
  bindings.is_regiment_supply_loss_eligible = Eligible;
  bindings.current_province_supply_contributor_bindings = {true, SameSide};
  auto &resupply = bindings.current_land_resupply_bindings;
  resupply.enabled = true; resupply.is_resupply_eligible = Admission;
  resupply.is_army_fleet_supply_active = Fleet; resupply.character_storage_slot = &character_storage;
  resupply.loaded_gain_raw = &loaded_gain;
  auto &native = bindings.current_land_supply_rate_bindings;
  native.enabled = true; native.province_component_condition = Condition;
  native.read_province_component = Component; native.character_storage_slot = &character_storage;
  native.character_fallback_slot = &fallback_pointer;
  native.get_character_modifier_aggregator = Aggregator; native.read_character_modifier = Modifier;
  native.loaded_excess_slope_raw = &slope; native.loaded_min_loss_raw = &min_loss;
  native.loaded_max_loss_raw = &max_loss; native.loaded_divisor_floor_raw = &floor;
  const std::array<ArmyStrengthScope, 1> scope{{{unit_id, game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read = [&]() {
    Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "parent Strength query remains available");
    Check(rows.size() == 1 && rows[0].current_land_supply_rate_inputs_v1.has_value(), "new rate family attached");
    return rows[0];
  };
  auto row = read();
  Check(row.current_land_supply_rate_inputs_v1->current_observation_ready &&
        row.current_land_supply_rate_inputs_v1->province_component_raw == -600000 &&
        row.current_land_supply_rate_inputs_v1->commander_modifier_1a9_raw == 100000 &&
        row.current_land_supply_rate_inputs_v1->loaded_divisor_floor_raw == 300000,
        "actual raw operands captured through production query");
  Check(read() == row, "stable capture equality includes new rate DTO");
  Emit(directory, "land-rate-negative-component-floor", row);
  condition = false; modifier = 0; loaded_gain = 0;
  slope = 0; min_loss = 0; max_loss = 0; floor = 0;
  Put(army, 0x120, std::int32_t{-1}); expected_commander = fallback.data();
  const auto component_before = component_calls; row = read();
  Check(row.current_land_supply_rate_inputs_v1->current_observation_ready &&
        row.current_land_supply_rate_inputs_v1->commander_used_native_fallback == true &&
        row.current_land_supply_rate_inputs_v1->commander_resolved_full_id == -1 &&
        row.current_land_supply_rate_inputs_v1->province_component_raw == 0 &&
        row.current_land_supply_rate_inputs_v1->loaded_divisor_floor_raw == 0 && component_calls == component_before,
        "native fallback, absent component and legitimate loaded/modifier zero");
  Emit(directory, "fallback-absent-component-zero", row);
  condition = true; modifier = -100000; max_loss = 5000000;
  Put(army, 0x120, commander_id); expected_commander = commander.data(); row = read();
  Emit(directory, "zero-divisor", row);
  fleet = true; const auto modifier_before = modifier_calls; row = read();
  Check(row.current_land_supply_rate_inputs_v1->status == "not_land" &&
        !row.current_land_supply_rate_inputs_v1->province_component_raw && modifier_calls == modifier_before,
        "fleet branch does not read land component/modifier");
  Emit(directory, "fleet-branch", row);
  fleet = false; native.loaded_divisor_floor_raw = nullptr; row = read();
  Check(!row.current_land_supply_rate_inputs_v1->current_observation_ready &&
        row.current_land_resupply_v1->current_observation_ready,
        "missing raw slot does not invalidate independent current gain observation");
  Emit(directory, "missing-loaded-slot", row);
  native.enabled = false;
  Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
        !rows[0].current_land_supply_rate_inputs_v1, "legacy producer omits new rate family");
  Check(!BindArmyImage(0x140000000, kExecutableSha256).current_land_supply_rate_bindings.enabled,
        "legacy .2 binder does not install these .3 operands");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire directory required"); Cases(argv[1]);
    std::cout << "PASS: current full land rate observer and five new production wires\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n'; return 1;
  }
}
