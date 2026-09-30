#include "xar_bridge/ck3_12002_phase_advantage.hpp"
#include "xar_bridge/ck3_12002_phase.hpp"

#include <array>
#include <algorithm>
#include <cstring>
#include <iostream>
#include <string>

namespace advantage_fixture {
using namespace xar::ck3_12002;
template<class T, std::size_t N> void Store(std::array<std::byte, N> &data,
    std::size_t offset, T value) {
  std::memcpy(data.data() + offset, &value, sizeof(value));
}
struct Effect {
  std::array<std::byte, 0x60> bytes{};
  std::string key;
  Effect(std::string name, std::int32_t points) : key(std::move(name)) {
    Store(bytes, 0x18, key.data());
    Store(bytes, 0x28, key.size());
    Store(bytes, 0x30, std::max<std::size_t>(key.size(), 16));
    Store(bytes, 0x38, std::uint32_t{0x4744624F});
    Store(bytes, 0x40, points);
  }
  void *ptr() { return bytes.data(); }
};
struct Fixture {
  std::array<std::byte, 0x1100> rules{};
  std::array<std::byte, 0x90> terrain{}, aggregator{};
  std::array<std::byte, 0x880> province{};
  std::array<std::array<std::byte, 0x210>, 2> armies{}, owners{};
  std::array<std::array<std::byte, 0x180>, 2> regiments{}, supply_units{};
  std::array<std::byte, 0x60> regiment_store{}, unit_store{}, government{};
  std::array<std::byte, 0x350> treasury{};
  std::array<std::byte, 0x200> realms{};
  std::array<std::byte, 0x30> regiment_slots{}, unit_slots{};
  std::array<std::int32_t, 3> thresholds{50, 20, 0};
  const std::int32_t *threshold_data = thresholds.data();
  std::int32_t threshold_count = 3, realm_id = 0x01000001;
  void *regiment_storage = regiment_store.data(), *unit_storage = unit_store.data();
  Effect attacker_cross{"attacker_river", 1}, defender_cross{"defender_river", 2};
  Effect attacker_terrain{"hills_attacker", 4}, defender_terrain{"hills_defender", 3};
  Effect supplied{"supply_state_supplied_advantage", 0};
  Effect low{"supply_state_running_low_advantage", -5};
  Effect starving{"supply_state_starving_advantage", -10};
  Effect holding{"holding_defender_advantage", 5};
  Effect gathering{"gathering_army_advantage", -4};
  Effect owner_debt{"combat_debt_level_0", -2};
  Effect treasury_debt{"treasury_combat_debt_level_0", -3};
  Effect no_income{"combat_debt_level_no_income", -7};
  std::array<void *, 1> debt_rows{}, treasury_rows{};
  bool ignore_crossing = false, fail_native_supply = false;
  xar::game::CombatSimulationInputsSnapshot base;
  Fixture() {
    Store(rules, 0xF70 + 2 * 8, attacker_cross.ptr());
    Store(rules, 0xFA0 + 2 * 8, defender_cross.ptr());
    Store(rules, 0xF00, gathering.ptr());
    Store(rules, 0xF10, holding.ptr());
    Store(rules, 0xF20, supplied.ptr());
    Store(rules, 0xF30, low.ptr());
    Store(rules, 0xF40, starving.ptr());
    Store(rules, 0xF60, no_income.ptr());
    debt_rows[0] = owner_debt.ptr(); treasury_rows[0] = treasury_debt.ptr();
    Store(rules, 0xFD0, debt_rows.data()); Store(rules, 0xFDC, std::int32_t{1});
    Store(rules, 0x1078, treasury_rows.data()); Store(rules, 0x1084, std::int32_t{1});
    Store(terrain, 0x18, static_cast<const char *>("hills"));
    Store(terrain, 0x28, std::size_t{5}); Store(terrain, 0x30, std::size_t{16});
    Store(terrain, 0x40, no_income.ptr()); // old-layout decoy must be ignored.
    Store(terrain, 0x48, attacker_terrain.ptr());
    Store(terrain, 0x50, defender_terrain.ptr());
    Store(regiment_store, 0x20, regiment_slots.data());
    Store(regiment_store, 0x2C, std::uint32_t{3});
    Store(unit_store, 0x20, unit_slots.data()); Store(unit_store, 0x2C, std::uint32_t{3});
    Store(government, 0x40, std::uint32_t{1U << 29U});
    Store(treasury, 0x10, realm_id); Store(treasury, 0x14, std::uint32_t{0x4C616E64});
    Store(treasury, 0x318, std::int64_t{-1});
    Store(realms, 0x1E0, &realm_id); Store(realms, 0x1EC, std::int32_t{1});
    for (std::size_t index = 0; index < 2; ++index) {
      const auto id = static_cast<std::int32_t>(0x01000001 + index);
      Store(armies[index], 0x10, id);
      Store(armies[index], 0x180, std::int64_t{index == 0 ? 80 * 100'000 : 0});
      Store(armies[index], 0x5C, std::int32_t{index == 0 ? 1 : 0});
      Store(owners[index], 0x18, id);
      Store(regiments[index], 0x10, id);
      Store(regiments[index], 0x14, std::uint32_t{0x41725267});
      Store(regiments[index], 0x140, id);
      Store(regiments[index], 0x14C, std::int32_t{0});
      Store(regiments[index], 0x38, std::int32_t{100});
      Store(regiment_slots, (index + 1) * 16 + 8, regiments[index].data());
      Store(supply_units[index], 0x10, id);
      Store(unit_slots, (index + 1) * 16 + 8, supply_units[index].data());
      xar::game::CombatArmyInputsSnapshot army;
      army.available = army.regiments_observable = true;
      army.owner.status = xar::game::CombatObservationStatus::available;
      army.army_id = army.native_carmy_id = army.owner.character_id = id;
      xar::game::CombatRegimentSnapshot regiment;
      regiment.regiment_id = id; regiment.identity_valid = true; regiment.current_soldiers = 100;
      army.regiments.push_back(regiment); base.armies.push_back(army);
    }
    Store(owners[1], 0x1B0, treasury.data()); Store(owners[1], 0x1C0, realms.data());
    base.scenario.attacker_army_ids = {0x01000001};
    base.scenario.defender_army_ids = {0x01000002};
    base.target_province_id = base.target_province.province_id = 5;
    base.target_province.available = base.target_province.terrain.available = true;
    base.target_province.terrain.key = "hills";
    base.target_province.crossing.available = true; base.target_province.crossing.kind = "river";
    base.target_province.defender_context.available = true;
    base.target_province.defender_context.holding_defender = true;
    base.target_province.defender_context.holding_defender_status = xar::game::CombatObservationStatus::available;
  }
};
Fixture *fixture = nullptr;
void *Rules() { return fixture->rules.data(); }
void *Terrain(void *) { return fixture->terrain.data(); }
void *Aggregator(void *) { return fixture->aggregator.data(); }
void *Government(void *) { return fixture->government.data(); }
bool Flag(void *ptr, std::int32_t id) {
  return ptr == fixture->aggregator.data() + 0x68 && id == 0x1A4 && fixture->ignore_crossing;
}
bool Holding(void *, void *) { return true; }
bool HasHolding(void *) { return true; }
std::int64_t *ProvinceModifier(std::int64_t *out, void *, std::int32_t id,
    std::int32_t, void *) { *out = id == 0x1EB ? 50'000 : -99; return out; }
std::int64_t *Modifier(std::int64_t *out, void *, std::int32_t id, void *,
    std::int64_t, std::int32_t) { *out = id == 0x1D6 ? 200'000 : -99; return out; }
void *Supply(const AdvantageNativeIdArray *array) {
  if (fixture->fail_native_supply) return fixture->holding.ptr();
  const auto index = array->data[0] == 0x01000001 ? 0U : 1U;
  std::int64_t value = 0;
  std::memcpy(&value, fixture->armies[index].data() + 0x180, sizeof(value));
  return value >= 50 * 100'000 ? fixture->supplied.ptr()
      : value >= 20 * 100'000 ? fixture->low.ptr() : fixture->starving.ptr();
}
std::int32_t Debt(void *owner, std::int32_t mode) {
  return mode == 3 || owner == fixture->owners[0].data() ? 0 : 1;
}
void *Treasury(const std::int32_t *id) { return *id == fixture->realm_id ? fixture->treasury.data() : nullptr; }
void *Army(void *, std::int32_t id) { return id == 0x01000001 ? fixture->armies[0].data() : fixture->armies[1].data(); }
void *Character(void *, std::int32_t id) { return id == 0x01000001 ? fixture->owners[0].data() : fixture->owners[1].data(); }
void *Province(void *, std::int32_t) { return fixture->province.data(); }
} // namespace

#include <cassert>
#include <cstdlib>
namespace assembled_fixture {
namespace af = advantage_fixture;
using namespace xar;
using namespace xar::ck3_12002;
template<class T> T Read(const void *p, std::size_t offset) {
  T value{}; std::memcpy(&value, static_cast<const std::byte *>(p) + offset, sizeof(value)); return value;
}
template<class T> void Write(void *p, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
}
struct Counters {
  std::array<std::uintptr_t, 3> table{};
  void *allocator = nullptr;
  int constructed = 0, destroyed = 0, population_allocated = 0, released = 0;
  int ledger_allocated = 0, resolved = 0;
  bool corrupt_total = false;
} counters;
void Release(void *, void *p, std::size_t alignment) {
  assert(alignment == 8); ++counters.released; std::free(p);
}
void *Allocate(void *, std::size_t bytes, std::size_t alignment) {
  assert(alignment == 8 && bytes > 0 && bytes % sizeof(AdvantageLedgerEntry) == 0);
  ++counters.ledger_allocated; return std::calloc(1, bytes);
}
void *Construct(void *side, void *shell) {
  assert(Read<std::uint32_t>(shell, 0x0C) == 0x436F6D62);
  ++counters.constructed; Write(side, 0x340, std::uint32_t{0x436F5369});
  Write(side, 8, std::int32_t{-1}); Write(side, 0x70, std::int32_t{-1});
  Write(side, 0xB8, shell); Write(side, 0x10, std::calloc(8, 4));
  Write(side, 0x18, std::int32_t{8}); Write(side, 0x40, std::calloc(8, 0x60));
  Write(side, 0x48, std::int32_t{8});
  Write(side, 0x50, &counters.allocator); Write(side, 0x88, &counters.allocator); return side;
}
void Populate(void *side, void *army) {
  const auto id = Read<std::int32_t>(army, 0x10);
  Write(Read<void *>(side, 0x10), 0, id); Write(side, 0x1C, std::int32_t{1});
  Write(side, 0x70, id); Write(side, 0xA8, std::int64_t{100'000'000});
  auto local = Read<void *>(side, 0xC8);
  Write(local, 0x38, std::calloc(1, 0x50)); ++counters.population_allocated;
  Write(local, 0x40, std::int32_t{1}); Write(local, 0x44, std::int32_t{1});
}
void *Commander(void *side) {
  return af::Character(nullptr, Read<std::int32_t>(Read<void *>(side, 0x10), 0));
}
void Refresh(void *) {}
std::int32_t Strength(void *side) {
  return Read<std::int32_t>(Read<void *>(side, 0x10), 0) == 0x01000001 ? 100 : 101;
}
void Destroy(void *side) {
  ++counters.destroyed; assert(Read<std::uint32_t>(side, 0x340) == 0x436F5369);
  auto ledger = Read<void *>(side, 0x78);
  if (ledger) Release(nullptr, ledger, 8);
  std::free(Read<void *>(side, 0x10)); std::free(Read<void *>(side, 0x40));
}
std::int64_t *Dynamic(void *shell, std::int64_t *out, std::int32_t side, void *) {
  assert(Read<std::int32_t>(shell, 0x6D0) == 0 && Read<std::int32_t>(shell, 0x6D4) == 0);
  auto object = static_cast<std::byte *>(shell) + (side == 0 ? 0x20 : 0x368);
  assert(Read<std::uint8_t>(object, 0x344) == (side == 0 ? 0 : 1));
  *out = side == 0 ? 2'000'000 : 500'000; return out;
}
void Resolve(void *shell) {
  ++counters.resolved;
  assert(Read<std::int64_t>(shell, 0x6C8) == 150'000);
  std::int64_t summed = 0;
  for (std::size_t side = 0; side < 2; ++side) {
    auto object = static_cast<std::byte *>(shell) + (side == 0 ? 0x20 : 0x368);
    auto rows = Read<AdvantageLedgerEntry *>(object, 0x78);
    auto count = Read<std::int32_t>(object, 0x84);
    assert(rows && count > 0 && count == Read<std::int32_t>(object, 0x80));
    for (int i = 0; i < count; ++i) {
      assert(rows[i].effect); summed += (side == 0 ? 1 : -1) * rows[i].contribution_raw;
    }
    if (side == 1) {
      assert(count > 3 && rows[3].effect == af::fixture->holding.ptr());
      assert(rows[3].contribution_raw == 1'250'000);
      assert(rows[3].contribution_raw != 250'000); // A scale is not a contribution.
    }
  }
  assert(summed == 150'000);
  std::int64_t left{}, right{}; Dynamic(shell, &left, 0, nullptr); Dynamic(shell, &right, 1, nullptr);
  Write(shell, 0x710, Read<std::int64_t>(shell, 0x6C8) + left - right + (counters.corrupt_total ? 1 : 0));
}
std::int32_t Relation(void *, std::int32_t side) { return side == 0 ? 4 : 7; }
std::int64_t *CommanderDynamic(void *, std::int64_t *out, void *commander,
                              std::int32_t side, std::int32_t relation, void *) {
  assert(relation == (side == 0 ? 4 : 7) && commander == af::fixture->owners[side].data());
  *out = side == 0 ? 1'000'000 : 200'000; return out;
}
std::int64_t *SideModifier(void *, std::int64_t *out, void *aggregator,
                          std::int32_t side, std::int32_t relation, void *) {
  assert(aggregator && relation == (side == 0 ? 4 : 7));
  *out = side == 0 ? 400'000 : 100'000; return out;
}
bool Gathering(void *, std::int32_t id, bool &out) { out = id == 0x01000002; return true; }
int Run() {
  af::Fixture f; af::fixture = &f;
  counters.table[1] = reinterpret_cast<std::uintptr_t>(&Allocate);
  counters.table[2] = reinterpret_cast<std::uintptr_t>(&Release); counters.allocator = counters.table.data();
  auto &base = f.base; base.input_observation_ready = true;
  for (std::size_t i = 0; i < base.armies.size(); ++i) {
    auto &army = base.armies[i]; army.native_carmy_id_observable = true;
    army.commander.status = game::CombatObservationStatus::available;
    army.commander.character_id = army.owner.character_id; army.knights.available = true;
    army.encounter_role = i == 0 ? "attacker" : "defender";
    af::Store(f.armies[i], 0x120, army.commander.character_id);
    af::Store(f.armies[i], 0x124, army.army_id);
    af::Store(f.armies[i], 0x1D0, std::int32_t{i == 0 ? 0 : 1});
  }
  AdvantageBindings advantage;
  advantage.enabled = true; advantage.get_rules = af::Rules; advantage.get_terrain = af::Terrain;
  advantage.select_supply = af::Supply; advantage.select_debt = af::Debt;
  advantage.resolve_treasury = af::Treasury; advantage.get_government = af::Government;
  advantage.get_modifier_aggregator = af::Aggregator; advantage.has_modifier_flag = af::Flag;
  advantage.is_holding_defender = af::Holding; advantage.province_has_holding = af::HasHolding;
  advantage.read_province_modifier = af::ProvinceModifier; advantage.read_modifier_value = af::Modifier;
  advantage.regiment_storage_slot = &f.regiment_storage;
  advantage.supply_unit_storage_slot = &f.unit_storage;
  advantage.supply_thresholds = &f.threshold_data; advantage.supply_threshold_count = &f.threshold_count;
  PhaseBindings bindings{true, Construct, Populate, Commander, Refresh, Strength,
                        Destroy, Resolve, Dynamic, af::HasHolding};
  bindings.advantage = advantage; bindings.commander_dynamic = CommanderDynamic;
  bindings.side_modifier = SideModifier; bindings.relation_kind = Relation;
  PhaseEnvironment env{nullptr, af::Army, af::Character, af::Province, Gathering};
  game::Snapshot scope; scope.paused = scope.has_played_character = scope.played_character_alive = true;
  NativeCombatPhase output;
  assert(ReadNativeCombatPhase(bindings, env, scope, base, output) == ReadNativeCombatPhaseResult::available);
  assert(output.nonreligious_constructor_ready && output.nonreligious_advantage_model.constructor_sources.size() == 15);
  assert(output.nonreligious_advantage_model.base_static_accumulator_raw == 150'000);
  assert(output.dynamic_advantage_at_zero_roll_raw == 1'500'000);
  const auto &dynamic = output.nonreligious_advantage_model.resolved_dynamic;
  assert(dynamic.original_total_helper_match && dynamic.original_total_helper_raw == 1'650'000 && dynamic.sides.size() == 2);
  assert(dynamic.sides[0].commander_dynamic_raw == 1'000'000 && dynamic.sides[0].side_dynamic_raw == 400'000 &&
         dynamic.sides[0].target_conditionals_residual_raw == 600'000 && dynamic.sides[0].primary_army_gathering_raw == 0);
  assert(dynamic.sides[1].target_conditionals_residual_raw == 200'000 && dynamic.sides[1].primary_army_gathering_raw == 1);
  assert(counters.constructed == 2 && counters.destroyed == 2 && counters.ledger_allocated == 2 &&
         counters.population_allocated == 2 && counters.released == 4 && counters.resolved == 1);
  counters.corrupt_total = true;
  assert(ReadNativeCombatPhase(bindings, env, scope, base, output) == ReadNativeCombatPhaseResult::native_phase_unavailable);
  assert(!output.available && output.unavailable_reason == "phase_dynamic_resolution_mismatch");
  assert(counters.constructed == counters.destroyed && counters.released == counters.ledger_allocated + counters.population_allocated);
  std::cout << "PASS phase assembled constructor ledger, native total/dynamic decomposition and cleanup\n";
  return 0;
}
}
int main() { return assembled_fixture::Run(); }
