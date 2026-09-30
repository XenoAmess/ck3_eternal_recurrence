#include "xar_bridge/ck3_12002_combat.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <vector>

namespace {
using namespace xar;
template <typename T> void Put(void *p, std::size_t o, T v) {
  std::memcpy(static_cast<std::byte *>(p) + o, &v, sizeof(v));
}
template <typename T> T Get(const void *p, std::size_t o) {
  T v{}; std::memcpy(&v, static_cast<const std::byte *>(p) + o, sizeof(v)); return v;
}
template <std::size_t N> using Memory = std::array<std::byte, N>;
constexpr std::int32_t enemy = 0x01000001, player = 0x01000002;
constexpr std::int32_t enemy_army = 0x01000003, player_army = 0x01000004;
constexpr std::int32_t enemy_owner = 0x01000005, player_owner = 0x01000006;
constexpr std::int32_t enemy_reg = 0x01000007, player_reg = 0x01000008;
constexpr std::int32_t knight_reg = 0x01000009, knight_char = 0x0100000A;
constexpr std::int32_t commander = 0x0100000B;
constexpr std::int32_t combat_id = 0x0100000C;
Memory<0x100> gs{};
Memory<0x160> gd{};
Memory<0xF10> rules{};
std::array<Memory<0x190>, 2> units{};
std::array<Memory<0x140>, 2> armies{};
std::array<Memory<0x160>, 3> regiments{};
std::array<Memory<0x220>, 4> characters{};
Memory<0x108> knight_link{};
std::array<Memory<0xA00>, 3> types{};
std::array<Memory<0xB0>, 2> provinces{};
Memory<0x90> map_node{};
Memory<0x790> terrain{};
Memory<0x718> live_combat{};
std::array<void *, 4> province_index{};
std::array<Memory<0x30>, 4> stores{};
std::array<std::array<Memory<0x10>, 16>, 4> slots{};
std::array<void *, 4> store_ptrs{};
std::array<std::uintptr_t, 2> identity_vtable{};
std::array<std::uintptr_t, 1> database_vtable{};
std::array<std::int32_t, 1> enemy_reg_ids{enemy_reg};
std::array<std::int32_t, 2> player_reg_ids{player_reg, knight_reg};
std::array<Memory<0x10>, 2> counter_targets{};
Memory<0x30> adjacency{};
std::int32_t minimum_roll = 0, maximum_roll = 10, damage = 50, toughness = 10, minimum_width = 100;
std::int64_t width_ratio = 100000;
void *gs_ptr = gs.data();

void Key(void *p, const char *s) {
  const auto n = std::strlen(s);
  std::memcpy(static_cast<std::byte *>(p) + 0x18, s, n);
  Put(p, 0x28, n); Put(p, 0x30, std::size_t{15});
}
void Register(std::size_t store, std::int32_t id, void *p, std::size_t id_offset) {
  Put(p, id_offset, id);
  Put(slots[store][static_cast<std::uint32_t>(id) & 0xFFFFFF].data(), 8, p);
}
void *Character(std::int32_t id) {
  return Get<void *>(slots[3][static_cast<std::uint32_t>(id) & 0xFFFFFF].data(), 8);
}
void *Commander(void *army) { return Character(Get<std::int32_t>(army, 0x120)); }
std::int32_t Advantage(void *, std::int32_t context, bool include_roll) {
  return context == -1 && !include_roll ? 7 : -1000;
}
void *Terrain(void *) { return terrain.data(); }
bool Special(void *r) { return Get<std::int32_t>(r, 0x148) != -1; }
void *Stats(void *r, void *out, void *province) {
  if (province != provinces[0].data()) return nullptr;
  Put(out, 8, std::int32_t{100}); Put(out, 0x10, std::int64_t{0});
  const auto is_knight = Special(r);
  Put(out, 0x18, is_knight ? std::int64_t{15000000} : std::int64_t{1000000});
  Put(out, 0x20, is_knight ? std::int64_t{3000000} : std::int64_t{1000000});
  Put(out, 0x28, std::int64_t{0}); Put(out, 0x30, std::int64_t{0}); return out;
}
void *Aggregator(void *c) { return c; }
std::int64_t *Modifier(void *, std::int64_t *out, std::int32_t index) {
  switch (index) {
  case 0x113: case 0x114: *out = 0; break;
  case 0x115: *out = 100000; break;
  case 0x116: *out = 200000; break;
  case 0x200: *out = 300000; break;
  case 0x201: *out = 400000; break;
  default: return nullptr;
  }
  return out;
}
void *Rules() { return rules.data(); }
std::int64_t *Chunk(const void *entry, std::int64_t *out) {
  *out = Get<std::int64_t>(entry, 0x18) / 100; return out;
}
std::int64_t *Scale(std::int64_t *out, void *, void *) { *out = 100000; return out; }
void Counter(void *, void *, void *out_header, std::int64_t scale) {
  if (scale != 100000) return;
  auto *v = Get<std::int64_t *>(out_header, 0);
  v[0] = 100000; v[1] = 50000;
}
void *KnightContext(void *c) { return c; }
std::int64_t *Effectiveness(std::int64_t *out, void *, std::uint64_t mode) {
  if (mode != 0) return nullptr;
  *out = 100000; return out;
}
bool Holding(void *owner, void *province) {
  return owner == Character(player_owner) && province == provinces[0].data();
}
ck3_12002::CombatBindings Setup() {
  // Removed legacy validity entries are deliberately null. Identity reads
  // must use the new native inline predicates, not the former virtual slots.
  identity_vtable[1] = 0;
  database_vtable[0] = 0;
  for (std::size_t i = 0; i != stores.size(); ++i) {
    store_ptrs[i] = stores[i].data();
    Put(stores[i].data(), 0x20, slots[i].data()); Put(stores[i].data(), 0x2C, std::int32_t{16});
  }
  Register(0, enemy, units[0].data(), 0x10); Register(0, player, units[1].data(), 0x10);
  Register(1, enemy_army, armies[0].data(), 0x10); Register(1, player_army, armies[1].data(), 0x10);
  Register(2, enemy_reg, regiments[0].data(), 0x10); Register(2, player_reg, regiments[1].data(), 0x10);
  Register(2, knight_reg, regiments[2].data(), 0x10);
  for (std::size_t i = 0; i != characters.size(); ++i) {
    Put(characters[i].data(), 0x10, identity_vtable.data());
    Put(characters[i].data(), 0x1C, std::uint32_t{0x43686172});
  }
  Register(3, enemy_owner, characters[0].data(), 0x18); Register(3, player_owner, characters[1].data(), 0x18);
  Register(3, knight_char, characters[2].data(), 0x18); Register(3, commander, characters[3].data(), 0x18);
  Put(units[0].data(), 0x174, enemy_owner); Put(units[1].data(), 0x174, player_owner);
  Put(units[0].data(), 0x178, enemy_army); Put(units[1].data(), 0x178, player_army);
  Put(armies[0].data(), 0x124, enemy); Put(armies[1].data(), 0x124, player);
  Put(armies[0].data(), 0x120, commander); Put(armies[1].data(), 0x120, std::int32_t{-1});
  Put(armies[0].data(), 0x128, std::int32_t{-1}); Put(armies[1].data(), 0x128, std::int32_t{-1});
  Put(armies[0].data(), 0x38, enemy_reg_ids.data()); Put(armies[0].data(), 0x40, std::int32_t{1}); Put(armies[0].data(), 0x44, std::int32_t{1});
  Put(armies[1].data(), 0x38, player_reg_ids.data()); Put(armies[1].data(), 0x40, std::int32_t{2}); Put(armies[1].data(), 0x44, std::int32_t{2});
  for (std::size_t i = 0; i != regiments.size(); ++i) {
    Put(regiments[i].data(), 8, identity_vtable.data()); Put(regiments[i].data(), 0x18, types[i].data());
    Put(regiments[i].data(), 0x14, std::uint32_t{0x41725267});
    // CArmyRegiment carries its type at +18. CRegiment is a different
    // class whose +118 type offset must not leak into this reader.
    Put(regiments[i].data(), 0x118, static_cast<void *>(nullptr));
    Put(regiments[i].data(), 0x38, std::int32_t{i == 2 ? 1 : 100}); Put(regiments[i].data(), 0x3C, std::int32_t{i == 2 ? 1 : 100});
    Put(regiments[i].data(), 0x140, i == 0 ? enemy_army : player_army); Put(regiments[i].data(), 0x148, i == 2 ? knight_char : -1);
    Put(types[i].data(), 0, database_vtable.data()); Key(types[i].data(), i == 2 ? "knight" : "archers");
    Put(types[i].data(), 0x38, std::uint32_t{0x4744624F});
    Put(types[i].data(), 0x260, std::int32_t{i == 2 ? -1 : 1}); Put(types[i].data(), 0x98A, std::uint8_t{1});
    // Legacy locations are deliberately invalid decoys.
    Put(types[i].data(), 0x270, std::int32_t{999}); Put(types[i].data(), 0x2C4, std::int32_t{99999});
  }
  Put(characters[2].data(), 0xEC, std::int32_t{3}); Put(characters[2].data(), 0xE8, std::int32_t{999});
  Put(characters[2].data(), 0x1B8, knight_link.data()); Put(knight_link.data(), 0xF8, knight_reg);
  Put(rules.data(), 0xEFC, std::int32_t{2}); Put(rules.data(), 0xF04, std::int32_t{99999});
  Put(terrain.data(), 0, database_vtable.data()); Key(terrain.data(), "hills");
  // The old +58 is a live-observed decoy in 1.20. Actual combat width reads +60.
  Put(terrain.data(), 0x58, std::int64_t{4291601254});
  Put(terrain.data(), 0x60, std::int64_t{80000});
  Put(terrain.data(), 0x776, std::uint16_t{0x200}); Put(terrain.data(), 0x778, std::uint16_t{0x201});
  Put(terrain.data(), 0x76E, std::uint16_t{999}); Put(terrain.data(), 0x770, std::uint16_t{999});
  Put(provinces[0].data(), 0x10, std::int32_t{1}); Put(provinces[1].data(), 0x10, std::int32_t{2});
  province_index[1] = provinces[0].data(); province_index[2] = provinces[1].data();
  Put(gs.data(), 0xA0, gd.data()); Put(gd.data(), 0x140, province_index.data()); Put(gd.data(), 0x14C, std::int32_t{4});
  Put(provinces[1].data(), 8, map_node.data()); Put(map_node.data(), 0x50, adjacency.data()); Put(map_node.data(), 0x5C, std::int32_t{1});
  Put(adjacency.data(), 0, std::int32_t{2}); Put(adjacency.data(), 4, std::int32_t{1});
  Put(units[0].data(), 0x20, provinces[1].data()); Put(units[1].data(), 0x20, provinces[0].data());
  ck3_12002::CombatBindings b{}; b.enabled = true; b.game_state_slot = &gs_ptr;
  b.army_storage_slot = &store_ptrs[0]; b.army_internal_storage_slot = &store_ptrs[1]; b.regiment_storage_slot = &store_ptrs[2]; b.character_storage_slot = &store_ptrs[3];
  // No live combat is present initially; an empty exact storage is legitimate.
  static Memory<0x30> combat_store{}; static std::array<Memory<0x10>, 16> combat_slots{};
  static void *combat_store_ptr = combat_store.data();
  Put(combat_store.data(), 0x20, combat_slots.data()); Put(combat_store.data(), 0x2C, std::int32_t{16});
  Put(live_combat.data(), 8, combat_id); Put(combat_slots[12].data(), 8, live_combat.data());
  b.combat_storage_slot = &combat_store_ptr;
  b.get_army_commander = Commander; b.get_commander_advantage = Advantage; b.get_province_terrain = Terrain; b.evaluate_regiment_stats_at_province = Stats;
  b.is_special_combat_regiment = Special; b.get_character_modifier_aggregator = Aggregator; b.read_character_modifier = Modifier; b.get_combat_rules = Rules;
  b.read_counter_current_chunk = Chunk; b.resolve_counter_classes = Counter; b.get_counter_context_scale = Scale; b.get_knight_effectiveness_context = KnightContext; b.read_knight_effectiveness = Effectiveness; b.is_holding_defender = Holding;
  b.commander_min_roll = &minimum_roll; b.commander_max_roll = &maximum_roll; b.knight_damage_per_prowess = &damage; b.knight_toughness_per_prowess = &toughness;
  b.minimum_combat_width = &minimum_width; b.base_combat_width_ratio = &width_ratio; return b;
}
int Fail(const char *s) { std::cerr << s << '\n'; return 1; }
} // namespace

int main() {
  const auto bound = ck3_12002::BindCombatImage(0x140000000, ck3_12002::kExecutableSha256);
  if (!bound.enabled || reinterpret_cast<std::uintptr_t>(bound.read_counter_current_chunk) != 0x142657970 ||
      ck3_12002::BindCombatImage(0x140000000, "old-build").enabled) return Fail("exact image binding");
  auto b = Setup();
  game::Snapshot scope{}; scope.paused = true; scope.has_played_character = true; scope.played_character_alive = true;
  game::ArmySnapshot player_row{}; player_row.army_id = player;
  game::ArmySnapshot enemy_row{}; enemy_row.army_id = enemy;
  scope.player_armies.push_back(player_row);
  game::ActiveWarSnapshot war{}; war.war_id = 0x1000020; war.allied_armies.push_back(player_row); war.enemy_armies.push_back(enemy_row); scope.active_wars.push_back(war);
  game::CombatSimulationInputsRequest request{1, 2, {enemy}, {player}};
  game::CombatSimulationInputsSnapshot out{};
  const auto read = [&] { return ck3_12002::ReadCombatSimulationInputs(b, scope, request, out); };
  if (read() != game::ReadCombatSimulationInputsResult::available || !out.input_observation_ready || out.monte_carlo_ready || out.armies.size() != 2) return Fail("rich combat inputs unavailable");
  if (out.armies[0].regiments.size() != 1 ||
      out.armies[0].regiments[0].maa_type.status != game::CombatObservationStatus::available ||
      out.armies[0].regiments[0].maa_type.key != "archers")
    return Fail("CArmyRegiment type identity uses +18 rather than CRegiment +118");
  if (out.armies[0].commander.battle_context.effective_min_roll != 4 || out.armies[0].commander.battle_context.effective_max_roll != 16 ||
      out.armies[1].knights.members.size() != 1 || out.armies[1].knights.members[0].prowess != 3 ||
      out.armies[1].knights.members[0].effective_damage_raw != 15000000 || out.target_province.crossing.kind != "river" ||
      !out.target_province.defender_context.holding_defender || out.counter_resolutions[0].damage_retention_by_class_raw[1] != 50000 ||
      out.target_province.terrain.combat_width_multiplier_raw != 80000 ||
      out.target_province.precontact_width.final != 100) return Fail("new fields / modifiers / knight linkage");
  scope.paused = false;
  if (read() != game::ReadCombatSimulationInputsResult::requires_paused || out != game::CombatSimulationInputsSnapshot{}) return Fail("paused scope required");
  scope.paused = true;
  Put(regiments[1].data(), 0x10, std::int32_t{0x02000008});
  if (read() != game::ReadCombatSimulationInputsResult::partial || out.input_observation_ready) return Fail("stale full generation was accepted");
  Put(regiments[1].data(), 0x10, player_reg);
  Put(armies[0].data(), 0x128, combat_id); Put(live_combat.data(), 0x6B8, provinces[0].data()); Put(live_combat.data(), 0x6B0, std::int32_t{1});
  Put(live_combat.data(), 0x6B4, std::int32_t{4}); Put(live_combat.data(), 0x6C0, std::int32_t{200}); Put(live_combat.data(), 0x6C4, std::int32_t{160});
  if (read() != game::ReadCombatSimulationInputsResult::available || out.ongoing_combats.size() != 1 || out.ongoing_combats[0].phase_day != 4) return Fail("live combat memory fixture");
  request.defender_army_ids = {enemy};
  if (read() != game::ReadCombatSimulationInputsResult::invalid_arguments || out != game::CombatSimulationInputsSnapshot{}) return Fail("duplicate army partitions");
  std::cout << "CK3 1.20.0.2 combat input fixture GREEN\n";
  return 0;
}
