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
void *expected_owner = nullptr;
void *expected_province = nullptr;
bool admission = true, fleet = false;
std::int32_t predicate_calls = 0;
std::int32_t Count(void *, std::uint8_t) { return 0; }
std::int32_t Maximum(void *) { return 0; }
bool Fleet(void *) { return fleet; }
bool Admission(void *owner, void *province) {
  Check(owner == expected_owner && province == expected_province,
        "predicate receives actual owner and current Province, never commander");
  ++predicate_calls;
  return admission;
}
void Emit(const std::filesystem::path &directory, const char *name,
          const game::ArmyStrengthSnapshot &row) {
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
      [](std::string &out, std::string_view text) { out += '"'; out += text; out += '"'; });
  std::filesystem::create_directories(directory);
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  Check(static_cast<bool>(output), "new land resupply wire output");
  output << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  constexpr std::int32_t unit_id = 0x01000001, army_id = 0x02000001;
  constexpr std::int32_t owner_id = 0x03000001, commander_id = 0x03000002;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x208> army{};
  std::array<std::byte, 0x30> owner{}, commander{};
  std::array<std::byte, 0x860> province{};
  std::array<std::byte, 0x150> data{};
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x30> units{}, armies{}, characters{}, regiments{};
  std::array<std::byte, 0x30> unit_slots{}, army_slots{}, character_slots{};
  std::array<void *, 2> province_slots{nullptr, province.data()};
  Put(unit, 0x10, unit_id); Put(unit, 0x20, static_cast<void *>(province.data()));
  Put(unit, 0x174, owner_id); Put(unit, 0x178, army_id);
  Put(army, 0x10, army_id); Put(army, 0x14, std::uint32_t{0x41726D79});
  Put(army, 0x120, commander_id); Put(army, 0x124, unit_id);
  Put(owner, 0x18, owner_id); Put(commander, 0x18, commander_id);
  Put(province, 0x10, std::int32_t{1});
  Put(data, 0x140, static_cast<void *>(province_slots.data())); Put(data, 0x14C, std::int32_t{2});
  Put(state, 0xA0, static_cast<void *>(data.data()));
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(character_slots, 0x18, static_cast<void *>(owner.data()));
  Put(character_slots, 0x28, static_cast<void *>(commander.data()));
  const auto storage = [&](auto &header, auto &slots, std::int32_t capacity) {
    Put(header, 0x20, static_cast<void *>(slots.data())); Put(header, 0x2C, capacity);
  };
  storage(units, unit_slots, 2); storage(armies, army_slots, 2); storage(characters, character_slots, 3);
  void *unit_storage = units.data(), *army_storage = armies.data();
  void *regiment_storage = regiments.data();
  void *character_storage = characters.data(), *state_pointer = state.data();
  std::int64_t loaded_gain = 2345678;
  expected_owner = owner.data(); expected_province = province.data();
  ArmyBindings bindings{};
  bindings.enabled = true; bindings.game_state_slot = &state_pointer;
  bindings.unit_storage_slot = &unit_storage; bindings.internal_army_storage_slot = &army_storage;
  bindings.regiment_storage_slot = &regiment_storage;
  bindings.get_army_current_soldiers = Count; bindings.get_army_maximum_soldiers = Maximum;
  auto &native = bindings.current_land_resupply_bindings;
  native.enabled = true; native.is_resupply_eligible = Admission;
  native.is_army_fleet_supply_active = Fleet; native.character_storage_slot = &character_storage;
  native.loaded_gain_raw = &loaded_gain;
  const std::array<ArmyStrengthScope, 1> scope{{{unit_id, game::ArmyStrengthScopeRole::player, {}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto read = [&]() {
    Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "parent strength remains available");
    Check(rows.size() == 1 && rows[0].current_land_resupply_v1.has_value(), "new query family attached");
    return rows[0];
  };
  auto row = read();
  Check(row.current_land_resupply_v1->current_observation_ready &&
        row.current_land_resupply_v1->owner_character_id == owner_id &&
        row.current_land_resupply_v1->native_resupply_eligible == true &&
        row.current_land_resupply_v1->loaded_gain_raw == loaded_gain,
        "land admission and actual nondefault loaded gain are observed");
  Check(read() == row, "stable two captures include this new DTO");
  Emit(directory, "land-eligible-loaded-gain", row);
  admission = false; loaded_gain = 0; row = read();
  Check(row.current_land_resupply_v1->current_observation_ready &&
        row.current_land_resupply_v1->native_resupply_eligible == false &&
        row.current_land_resupply_v1->loaded_gain_raw == 0,
        "native false and loaded zero stay available");
  Emit(directory, "land-ineligible-zero", row);
  Put(owner, 0x18, std::int32_t{0x04000001}); loaded_gain = -17;
  const auto calls_before = predicate_calls; row = read();
  Check(!row.current_land_resupply_v1->current_observation_ready &&
        !row.current_land_resupply_v1->native_resupply_eligible &&
        row.current_land_resupply_v1->loaded_gain_raw == -17 && predicate_calls == calls_before,
        "unresolved owner is distinct from native false; actual gain remains observed");
  Emit(directory, "owner-unresolved", row);
  Put(owner, 0x18, owner_id); fleet = true; row = read();
  Check(row.current_land_resupply_v1->status == "not_land" &&
        row.current_land_resupply_v1->native_land_branch_applicable == false &&
        !row.current_land_resupply_v1->native_resupply_eligible && predicate_calls == calls_before,
        "fleet branch does not invoke land admission");
  Emit(directory, "fleet-branch", row);
  native.enabled = false;
  Check(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
        !rows[0].current_land_resupply_v1, "older producer omits the additive family");
  Check(!BindArmyImage(0x140000000, kExecutableSha256).current_land_resupply_bindings.enabled,
        "legacy .2 binder never installs the .3 predicate or slot");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire directory required"); Cases(argv[1]);
    std::cout << "PASS: current land resupply observer and four new production wires\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n'; return 1;
  }
}
