#include "xar_bridge/ck3_12002_world.hpp"

#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_province.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
template <typename T, typename Buffer>
void Put(Buffer &buffer, std::size_t offset, T value) {
  std::memcpy(buffer.data() + offset, &value, sizeof(value));
}
template <typename T>
T Load(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}
bool FixtureContains(const void *side, std::int32_t id) {
  std::vector<std::int32_t> ids;
  if (!xar::ck3_12002::ReadWarParticipantIds(side, ids)) {
    return false;
  }
  for (const auto candidate : ids) {
    if (candidate == id) {
      return true;
    }
  }
  return false;
}
std::int32_t FixtureScore(const void *war, void *) {
  return Load<std::int32_t>(war, 0x2B4);
}

void *fixture_province = nullptr;
void *fixture_raise_province = nullptr;
void *FixtureTitleProvince(void *) { return fixture_province; }
void *FixtureCapital(void *) { return fixture_province; }
void *FixtureRaise(void *, void *capital, std::int32_t range,
                   std::int32_t maximum_range) {
  return capital == fixture_province && range == 0 && maximum_range == -1
             ? fixture_raise_province
             : nullptr;
}
std::int32_t FixtureUnitState(void *) { return 7; }
bool FixtureOccupied(void *) { return false; }
std::int32_t FixtureFort(void *) { return 4; }
std::int32_t FixtureGarrison(void *) { return 800; }
std::int32_t FixtureBesiegers(void *) { return 0; }
std::int64_t *FixtureFixed(void *, std::int64_t *value) { return value; }
std::int32_t FixtureDays(void *) { return 12; }

bool CheckWholeWorld() {
  using namespace xar::ck3_12002;
  constexpr std::int32_t player = 0x02000010;
  constexpr std::int32_t enemy = 0x03000001;
  constexpr std::int32_t war_id = 0x04000000;
  constexpr std::int32_t unit_id = 0x05000000;
  constexpr std::int32_t title_id = 0x06000001;
  std::array<std::byte, 0xA8> state{};
  std::vector<std::byte> data(0x36780);
  std::array<std::byte, 0x30> war_storage{}, unit_storage{}, title_storage{},
      character_storage{}, siege_storage{};
  std::array<std::byte, 0x10> war_slots{}, unit_slots{};
  std::array<std::byte, 0x20> title_slots{}, character_slots{};
  std::array<std::byte, 0x360> war{};
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x120> title{};
  std::array<std::byte, 0x70> definition{};
  std::array<std::byte, 0x1D8> character{};
  std::array<std::byte, 0x860> province{}, raise_province{};
  std::array<std::byte, 0x10> attacker{}, defender{};
  std::array<void *, 1> attack_pointers{attacker.data()},
      defense_pointers{defender.data()};
  std::array<void *, 5> provinces{};
  provinces[3] = province.data();
  provinces[4] = raise_province.data();
  std::array<std::int32_t, 1> titles{title_id};
  std::array<std::byte, 4> route_origin{}, route_target{};
  Put(route_origin, 0, std::int32_t{3});
  Put(route_target, 0, std::int32_t{4});
  std::array<void *, 2> route{route_origin.data(), route_target.data()};
  Put(state, 0xA0, data.data());
  Put(data, kWorldWarManagerOffset + 0x20, war_storage.data());
  Put(data, 0x140, provinces.data());
  Put(data, 0x14C, std::int32_t{5});
  Put(war_storage, 0x20, war_slots.data());
  Put(war_storage, 0x2C, std::int32_t{1});
  Put(war_slots, 8, war.data());
  Put(war, 8, war_id);
  Put(attacker, 8, player);
  Put(defender, 8, enemy);
  Put(war, 0x28, attack_pointers.data());
  Put(war, 0x30, std::int32_t{1});
  Put(war, 0x34, std::int32_t{1});
  Put(war, 0x88, defense_pointers.data());
  Put(war, 0x90, std::int32_t{1});
  Put(war, 0x94, std::int32_t{1});
  Put(war, 0x270, titles.data());
  Put(war, 0x278, std::int32_t{1});
  Put(war, 0x27C, std::int32_t{1});
  Put(war, 0x288, player);
  Put(war, 0x28C, enemy);
  Put(war, 0x2B4, std::int32_t{17});
  Put(unit_storage, 0x20, unit_slots.data());
  Put(unit_storage, 0x2C, std::int32_t{1});
  Put(unit_slots, 8, unit.data());
  Put(unit, 0x10, unit_id);
  Put(unit, 0x20, province.data());
  Put(unit, 0x174, player);
  Put(unit, 0x38, route.data());
  Put(unit, 0x40, std::int32_t{2});
  Put(unit, 0x44, std::int32_t{2});
  Put(province, 0x10, std::int32_t{3});
  Put(province, 0x788, std::int32_t{-1});
  Put(province, 0x85C, std::uint32_t{0x50726F76});
  Put(raise_province, 0x10, std::int32_t{4});
  Put(raise_province, 0x85C, std::uint32_t{0x50726F76});
  Put(title_storage, 0x20, title_slots.data());
  Put(title_storage, 0x2C, std::int32_t{2});
  Put(title_slots, 0x18, title.data());
  Put(title, 0x10, title_id);
  Put(title, 0x48, definition.data());
  Put(definition, 0x64, std::int32_t{2});
  Put(character_storage, 0x20, character_slots.data());
  Put(character_storage, 0x2C, std::int32_t{2});
  Put(character_slots, 0x18, character.data());
  Put(character, 0x18, enemy);
  void *state_pointer = state.data(), *unit_pointer = unit_storage.data(),
       *title_pointer = title_storage.data(),
       *character_pointer = character_storage.data(),
       *siege_pointer = siege_storage.data();
  WorldBindings world{true, &state_pointer, FixtureContains, FixtureScore,
                      &character_pointer, FixtureCapital, FixtureRaise};
  ArmyBindings armies{};
  armies.enabled = true;
  armies.game_state_slot = &state_pointer;
  armies.unit_storage_slot = &unit_pointer;
  armies.get_unit_state = FixtureUnitState;
  ProvinceBindings province_bindings{};
  province_bindings.enabled = true;
  province_bindings.game_state_slot = &state_pointer;
  province_bindings.landed_title_storage_slot = &title_pointer;
  province_bindings.title_province = FixtureTitleProvince;
  province_bindings.is_occupied = FixtureOccupied;
  province_bindings.fort_level = FixtureFort;
  province_bindings.garrison_size = FixtureGarrison;
  province_bindings.besieging_strength = FixtureBesiegers;
  province_bindings.siege_storage_slot = &siege_pointer;
  province_bindings.siege_progress = FixtureFixed;
  province_bindings.siege_total_work = FixtureFixed;
  province_bindings.siege_days_left = FixtureDays;
  fixture_province = province.data();
  fixture_raise_province = raise_province.data();
  CoreSnapshotPrefix prefix{};
  prefix.map_ready = true;
  prefix.has_played_character = true;
  prefix.played_character_id = player;
  prefix.clock.paused = true;
  xar::game::Snapshot snapshot{};
  if (ReadWorldSnapshot(world, armies, province_bindings, prefix, snapshot) !=
          WorldReadResult::available ||
      snapshot.player_armies.size() != 1 ||
      snapshot.player_armies[0].army_id != unit_id ||
      !snapshot.player_armies[0].controllable ||
      snapshot.player_armies[0].route_province_ids !=
          std::vector<std::int32_t>{3, 4} ||
      snapshot.active_wars.size() != 1 ||
      snapshot.active_wars[0].enemy_primary_default_raise_province_id != 4 ||
      snapshot.active_wars[0].war_objective_province_ids !=
          std::vector<std::int32_t>{3} ||
      snapshot.active_wars[0].objective_province_states.size() != 1) {
    return false;
  }
  const auto &objective = snapshot.active_wars[0].objective_province_states[0];
  if (!objective.occupation_observable || objective.is_occupied ||
      !objective.fort_level_observable || objective.fort_level != 4 ||
      !objective.garrison_size_observable || objective.garrison_size != 800 ||
      !objective.siege_observable || objective.has_active_siege) {
    return false;
  }
  prefix.map_ready = false;
  return ReadWorldSnapshot(world, armies, province_bindings, prefix, snapshot) ==
             WorldReadResult::available &&
         snapshot.player_armies.empty() && snapshot.active_wars.empty();
}

bool CheckWarGraph() {
  using namespace xar::ck3_12002;
  constexpr std::int32_t war_id = 0x05000002;
  constexpr std::int32_t player = 0x02000010;
  constexpr std::int32_t enemy = 0x03000011;
  constexpr std::int32_t ally = 0x04000012;
  std::array<std::byte, 0xA8> state{};
  std::vector<std::byte> data(0x36780);
  std::array<std::byte, 0x30> storage{};
  std::array<std::byte, 0x80> slots{};
  std::array<std::byte, 0x360> war{};
  std::array<std::byte, 0x10> player_row{}, enemy_row{}, ally_row{};
  std::array<void *, 2> attackers{player_row.data(), ally_row.data()};
  std::array<void *, 1> defenders{enemy_row.data()};
  std::array<std::int32_t, 2> titles{0x02000005, 0x03000006};
  Put(state, 0xA0, data.data());
  Put(data, kWorldWarManagerOffset + 0x20, storage.data());
  Put(storage, 0x20, slots.data());
  Put(storage, 0x2C, std::int32_t{8});
  Put(slots, 2 * 0x10 + 8, war.data());
  Put(war, 8, war_id);
  Put(player_row, 8, player);
  Put(enemy_row, 8, enemy);
  Put(ally_row, 8, ally);
  Put(war, 0x20 + 8, attackers.data());
  Put(war, 0x20 + 0x10, std::int32_t{2});
  Put(war, 0x20 + 0x14, std::int32_t{2});
  Put(war, 0x80 + 8, defenders.data());
  Put(war, 0x80 + 0x10, std::int32_t{1});
  Put(war, 0x80 + 0x14, std::int32_t{1});
  Put(war, 0x270, titles.data());
  Put(war, 0x278, std::int32_t{2});
  Put(war, 0x27C, std::int32_t{2});
  Put(war, 0x288, player);
  Put(war, 0x28C, enemy);
  Put(war, 0x2B4, std::int32_t{42});
  // This independent state byte must not be mistaken for the ended flag.
  war[0x35C] = std::byte{1};
  void *state_pointer = state.data();
  WorldBindings bindings{true, &state_pointer, FixtureContains, FixtureScore};
  std::vector<xar::game::ArmySnapshot> armies(4);
  armies[0].army_id = 10;
  armies[0].owner_character_id = player;
  armies[1].army_id = 11;
  armies[1].owner_character_id = ally;
  armies[2].army_id = 12;
  armies[2].owner_character_id = enemy;
  armies[3].army_id = 13;
  armies[3].owner_character_id = 123;
  std::vector<xar::game::ActiveWarSnapshot> rows;
  if (ResolveWar(bindings, war_id) != war.data() ||
      ResolveWar(bindings, 0x04000002) != nullptr ||
      ReadActiveWars(bindings, player, armies, rows) !=
          WorldReadResult::available ||
      rows.size() != 1 || rows[0].war_id != war_id ||
      !rows[0].player_is_primary_war_leader ||
      rows[0].player_side != xar::game::PlayerWarSide::attacker ||
      rows[0].primary_opponent_character_id != enemy ||
      rows[0].player_relative_war_score != 42 ||
      rows[0].targeted_title_ids.size() != 2 ||
      rows[0].allied_armies.size() != 2 || rows[0].enemy_armies.size() != 1) {
    return false;
  }
  if (ReadActiveWars(bindings, enemy, armies, rows) !=
          WorldReadResult::available ||
      rows.size() != 1 ||
      rows[0].player_side != xar::game::PlayerWarSide::defender ||
      rows[0].player_relative_war_score != -42 ||
      rows[0].primary_opponent_character_id != player ||
      rows[0].allied_armies.size() != 1 || rows[0].enemy_armies.size() != 2) {
    return false;
  }
  war[0x358] = std::byte{1};
  if (ResolveWar(bindings, war_id) != nullptr ||
      ReadActiveWars(bindings, player, armies, rows) !=
          WorldReadResult::available ||
      !rows.empty()) {
    return false;
  }
  war[0x358] = std::byte{0};
  Put(war, 0x20 + 0x14, std::int32_t{3});
  if (ReadActiveWars(bindings, player, armies, rows) !=
          WorldReadResult::partial ||
      !rows.empty()) {
    return false;
  }
  Put(war, 0x20 + 0x14, std::int32_t{2});
  Put(war, 0x27C, std::int32_t{3});
  if (ReadActiveWars(bindings, player, armies, rows) !=
          WorldReadResult::partial ||
      !rows.empty()) {
    return false;
  }
  bindings.get_war_score = nullptr;
  if (ReadActiveWars(bindings, player, armies, rows) !=
      WorldReadResult::unavailable) {
    return false;
  }
  state_pointer = nullptr;
  return ResolveWar(bindings, war_id) == nullptr;
}
} // namespace

int main() {
  using namespace xar::ck3_12002;
  constexpr std::uintptr_t base = 0x140000000;
  const auto valid = BindWorldImage(base, kExecutableSha256);
  if (!valid.enabled ||
      reinterpret_cast<std::uintptr_t>(valid.game_state_slot) !=
          base + kGameStateSlotRva ||
      reinterpret_cast<std::uintptr_t>(valid.get_war_score) !=
          base + kWorldGetWarScoreRva ||
      BindWorldImage(base, "old-build").enabled || !CheckWarGraph() ||
      !CheckWholeWorld()) {
    std::cerr << "CK3 1.20.0.2 world fixture FAILED\n";
    return 1;
  }
  std::cout << "CK3 1.20.0.2 world fixture PASSED\n";
  return 0;
}
