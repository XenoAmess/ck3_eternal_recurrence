#include "xar_bridge/ck3_12002_phase_advantage.hpp"
#include "xar_bridge/ck3_12002_phase.hpp"

#include <array>
#include <algorithm>
#include <cstring>
#include <iostream>
#include <string>

namespace {
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
bool Check(bool condition, const char *message) {
  if (!condition) std::cerr << "FAIL " << message << '\n';
  return condition;
}
} // namespace

int main() {
  Fixture f; fixture = &f;
  AdvantageBindings b;
  b.enabled = true; b.get_rules = Rules; b.get_terrain = Terrain;
  b.select_supply = Supply; b.select_debt = Debt; b.resolve_treasury = Treasury;
  b.get_government = Government; b.get_modifier_aggregator = Aggregator;
  b.has_modifier_flag = Flag; b.is_holding_defender = Holding; b.province_has_holding = HasHolding;
  b.read_province_modifier = ProvinceModifier; b.read_modifier_value = Modifier;
  b.regiment_storage_slot = &f.regiment_storage; b.supply_unit_storage_slot = &f.unit_storage;
  b.supply_thresholds = &f.threshold_data; b.supply_threshold_count = &f.threshold_count;
  PhaseEnvironment env; env.resolve_internal_army = Army; env.resolve_character = Character; env.resolve_province = Province;
  const std::array<void *, 2> commanders{f.owners[0].data(), f.owners[1].data()};
  NonReligiousAdvantagePlan plan;
  if (!Check(BuildNonReligiousAdvantagePlan(b, env, f.base, commanders, plan), "baseline build") ||
      !Check(plan.nonreligious_available && !plan.model.available, "partial religion boundary") ||
      !Check(plan.model.constructor_sources.size() == 15, "all constructor stages retained") ||
      !Check(plan.model.base_static_accumulator_raw == 150'000, "signed constructor aggregate") ||
      !Check(plan.ledgers[0][0].contribution_raw == 100'000, "ledger stores effect contribution") ||
      !Check(plan.ledgers[1][3].contribution_raw == 1'250'000, "holding native ledger scale product") ||
      !Check(plan.model.constructor_sources[13].skip_reason == "religion_domain_deferred_by_owner", "religion omitted explicitly")) return 1;
  f.ignore_crossing = true;
  if (!Check(BuildNonReligiousAdvantagePlan(b, env, f.base, commanders, plan) &&
      plan.model.base_static_accumulator_raw == 350'000 &&
      !plan.model.constructor_sources[1].applied, "native crossing flag mapping")) return 1;
  Store(f.treasury, 0x318, std::int64_t{0});
  if (!Check(BuildNonReligiousAdvantagePlan(b, env, f.base, commanders, plan) &&
      !plan.model.side_inputs[1].treasury_debt_selector_observable, "treasury debt zero gate")) return 1;
  f.fail_native_supply = true;
  if (!Check(!BuildNonReligiousAdvantagePlan(b, env, f.base, commanders, plan), "native supply cross-check disagreement")) return 1;
  f.fail_native_supply = false;
  Store(f.regiments[0], 0x10, std::int32_t{0x02000001});
  if (!Check(!BuildNonReligiousAdvantagePlan(b, env, f.base, commanders, plan), "same-slot stale regiment generation")) return 1;
  CombatBindings combat; combat.enabled = true;
  if (!Check(!BindAdvantageImage(0x140000000, "old-build", combat).enabled,
      "exact hash selection")) return 1;
  const auto selected = BindAdvantageImage(0x140000000, kExecutableSha256, combat);
  if (!Check(selected.enabled && reinterpret_cast<std::uintptr_t>(selected.get_rules) ==
      0x1408FC3E0 && reinterpret_cast<std::uintptr_t>(selected.supply_unit_storage_slot) ==
      0x145D1EB68, "phase DB distinct from Maa DB")) return 1;
  std::cout << "PASS CK3 1.20.0.2 nonreligious constructor sources, ledger contributions, native gates and exact build\n";
  return 0;
}
