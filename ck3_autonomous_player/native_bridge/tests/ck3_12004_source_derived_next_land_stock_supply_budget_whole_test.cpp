#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_future_daily_supply_schedule.hpp"
#include "xar_bridge/ck3_12004_source_derived_next_daily_supply_frame.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <bit>
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
#include <utility>
#include <vector>

namespace {
using namespace xar;
namespace current = ck3_12004;
constexpr std::int32_t kUnit = 0x01000001;
constexpr std::int32_t kArmy = 0x02000001;
constexpr std::int32_t kRegiment = 0x03000001;
constexpr std::int32_t kFleet = 0x04000001;
constexpr std::int32_t kCurrentDate = 53288448;
// Independent synthetic stored D; source-derived future D must not be D+1.
constexpr std::int32_t kCurrentD = 12;
constexpr std::int64_t kCurrentDateStorage = (std::int64_t{7} << 32) | kCurrentDate;
constexpr std::int64_t kPreviousDateStorage = 21528124856LL;
constexpr std::int64_t kAnchorDateStorage = 38707994064LL;
constexpr std::int64_t kExpectedNextDateStorage = 304845178016701976LL;
constexpr std::int32_t kCommander = 0x05000001;
struct SceneSpec {
  std::string_view stem;
  std::int32_t native_usage;
  std::int64_t stock, fixed_modifier, divisor_floor, observed_rate;
};
constexpr std::array<SceneSpec, 3> kScenes{{
    {"01-land-over-limit-loss", 101, 100000000, 0, 100000, -100000},
    {"02-land-under-limit-gain-cap", 99, 199000000, 0, 100000, 2000000},
    {"03-land-zero-divisor-cap", 101, 100000000, -100000, 0, 4294967295LL}}};
constexpr std::uintptr_t kFixtureImageBase = 0x140000000ULL;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <class T, std::size_t N>
void Store(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Check(offset <= N && sizeof(T) <= N - offset, "fixture-owned object store out of range");
  std::memcpy(object.data() + offset, &value, sizeof value);
}

// The native manager secondary is embedded at GameData+2A548; not an indirect
// pointer slot. Large input storage and its before-copy are directly heap-owned.
struct Inputs {
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x2A9B0> game_data{};
  std::array<std::byte, 0x30> unit_storage{}, army_storage{}, regiment_storage{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{}, regiment_slots{};
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x200> army{};
  std::array<std::byte, 0x180> regiment{};
  std::array<std::byte, 0x900> province{};
  std::array<std::byte, 0xC0> province_definition{};
  std::array<std::byte, 0x780> terrain{};
  std::array<std::byte, 0x30> character_storage{};
  std::array<std::byte, 16 * 29830> character_slots{};
  std::array<std::byte, 0x400> owner{}, commander{};
  std::array<std::byte, 0x100> modifier_aggregator{};
  std::array<std::uint16_t, 2> modifier_keys{0x1A9, 0x1B0};
  std::array<std::int64_t, 2> modifier_values{};
  std::array<std::int32_t, 1> province_unit_ids{kUnit};
  std::int64_t loaded_gain = 2000000, loaded_excess_slope = 100000;
  std::int64_t loaded_min_loss = 100000, loaded_max_loss = 500000;
  std::int64_t loaded_divisor_floor = 100000, fixed_modifier_1a9 = 0;
  std::int32_t native_usage = 0;
  std::array<std::byte, 0x30> fleet_storage{}, fleet_slots{};
  std::array<std::byte, 0x28> fleet{};
  std::array<std::byte, 0x20> invalid_character{};
  std::array<std::int32_t, 3> supply_levels{2000, 1000, 0};
  std::array<std::int64_t, 3> supply_fractions{0, 12500, 25000};
  std::int32_t supply_level_count = 3, supply_fraction_count = 3;
  std::int32_t fleet_date_sentinel = -1;
  std::int64_t siege_rate = 0, raid_rate = 0;
  std::array<void *, 2> provinces{};
  std::array<std::int32_t, 2> regiment_ids{kRegiment, kRegiment};
  std::array<const void *, 1> next_phase_pointers{};
  std::array<std::uint8_t, 365> calendar_days{}, calendar_months{};
  std::int32_t loaded_grace_days = 2;
  friend bool operator==(const Inputs &, const Inputs &) = default;
};
struct Counters {
  std::size_t current_soldiers = 0, maximum_soldiers = 0;
  std::size_t supply_capacity = 0, attrition_fraction = 0, monthly_supply = 0;
  std::size_t combat = 0, gathering = 0, fleet_active = 0;
  std::size_t siege_active = 0, supply_budget = 0, whole_budget = 0;
  std::size_t province_limit = 0, province_usage = 0, regiment_eligible = 0;
  std::size_t resupply = 0, province_condition = 0, province_component = 0;
  std::size_t modifier_aggregator = 0, modifier_reads = 0, shares_war_side = 0;
  std::vector<std::int32_t> modifier_ordinals;
  std::array<std::size_t, 4> soldier_flags{};
  bool abi_matches = true;
  std::vector<std::string> abi_failures;
  std::vector<std::string> events;
};
std::string PointerText(const void *value) {
  return std::to_string(reinterpret_cast<std::uintptr_t>(value));
}
void RecordAbi(Counters &calls, bool matches, std::string arguments) {
  calls.abi_matches &= matches;
  if (!matches) calls.abi_failures.push_back(std::move(arguments));
}
struct Fixture;
Fixture *active = nullptr;
std::int32_t CurrentSoldiers(void *, std::uint8_t);
std::int32_t MaximumSoldiers(void *);
std::int64_t *SupplyCapacity(std::int64_t *, void *, void *);
std::int64_t *Attrition(void *, std::int64_t *, void *);
std::int64_t *MonthlySupply(void *, std::int64_t *, void *, void *);
bool InCombat(void *);
bool Gathering(void *);
bool FleetActive(void *);
bool SiegeActive(void *);
std::int32_t SupplyLossBudget(void *);
std::int32_t WholeLossBudget(std::int64_t, void *);
std::int32_t ProvinceLimit(void *, void *, void *, void *);
std::int32_t ProvinceUsage(void *, void *, std::int32_t, std::int64_t *);
bool RegimentEligible(void *);
bool SharesWarSide(void *, void *, void *);
bool ResupplyEligible(void *, void *);
bool ProvinceCondition(void *);
std::int64_t *ProvinceComponent(std::int64_t *, void *, std::int32_t, void *,
                               std::int64_t, std::int32_t);
void *ModifierAggregator(void *);
std::int64_t *ReadModifier(void *, std::int64_t *, std::int32_t);

struct Fixture {
  Inputs input{};
  SceneSpec scene;
  void *game_slot = input.game_state.data();
  void *unit_slot = input.unit_storage.data();
  void *army_slot = input.army_storage.data();
  void *regiment_slot = input.regiment_storage.data();
  void *fleet_slot = input.fleet_storage.data();
  void *character_slot = input.character_storage.data();
  void *character_fallback = input.invalid_character.data();
  const std::int32_t *levels_slot = input.supply_levels.data();
  const std::int64_t *fractions_slot = input.supply_fractions.data();
  current::ArmyBindings bindings{};
  Counters calls{};
  explicit Fixture(SceneSpec value) : scene(value) {
    input.native_usage = scene.native_usage;
    input.loaded_divisor_floor = scene.divisor_floor;
    input.fixed_modifier_1a9 = scene.fixed_modifier;
    input.modifier_values = {scene.fixed_modifier, 0};
    Store(input.modifier_aggregator, 0x68, static_cast<void *>(input.modifier_keys.data()));
    Store(input.modifier_aggregator, 0x74, std::int32_t{2});
    Store(input.modifier_aggregator, 0xD0, static_cast<void *>(input.modifier_values.data()));
    Store(input.game_state, 0x08, kCurrentDateStorage);
    Store(input.game_state, 0x9C, kCurrentD);
    Store(input.game_state, 0xA0, static_cast<void *>(input.game_data.data()));
    input.provinces = {nullptr, input.province.data()};
    Store(input.game_data, 0x140, static_cast<void *>(input.provinces.data()));
    Store(input.game_data, 0x14C, std::int32_t{2});
    Store(input.province, 0x10, std::int32_t{1});
    Store(input.province, 0x20, static_cast<void *>(input.province_definition.data()));
    Store(input.province, 0x740, static_cast<void *>(input.province_unit_ids.data()));
    Store(input.province, 0x74C, std::int32_t{1});
    Store(input.province, 0x85C, std::uint32_t{0x50726F76});
    Store(input.province_definition, 0xB8, static_cast<void *>(input.terrain.data()));
    Store(input.terrain, 0x38, std::uint32_t{0x4744624F});
    Store(input.terrain, 0x770, std::uint16_t{0x1B0});
    Store(input.character_storage, 0x20, static_cast<void *>(input.character_slots.data()));
    Store(input.character_storage, 0x2C, std::int32_t{29830});
    Store(input.character_slots, 16 * 29829 + 8, static_cast<void *>(input.owner.data()));
    Store(input.character_slots, 16 + 8, static_cast<void *>(input.commander.data()));
    Store(input.owner, 0x18, std::int32_t{29829});
    Store(input.owner, 0x1C, std::uint32_t{0x43686172});
    Store(input.commander, 0x18, kCommander);
    Store(input.commander, 0x1C, std::uint32_t{0x43686172});
    Store(input.unit_storage, 0x20, static_cast<void *>(input.unit_slots.data()));
    Store(input.unit_storage, 0x2C, std::int32_t{2});
    Store(input.army_storage, 0x20, static_cast<void *>(input.army_slots.data()));
    Store(input.army_storage, 0x2C, std::int32_t{2});
    Store(input.regiment_storage, 0x20, static_cast<void *>(input.regiment_slots.data()));
    Store(input.regiment_storage, 0x2C, std::int32_t{2});
    Store(input.unit_slots, 0x18, static_cast<void *>(input.unit.data()));
    Store(input.army_slots, 0x18, static_cast<void *>(input.army.data()));
    Store(input.regiment_slots, 0x18, static_cast<void *>(input.regiment.data()));
    Store(input.unit, 0x10, kUnit);
    Store(input.unit, 0x170, std::int32_t{1});
    Store(input.unit, 0x174, std::int32_t{29829});
    Store(input.unit, 0x178, kArmy);
    Store(input.unit, 0x20, static_cast<void *>(input.province.data()));
    Store(input.army, 0x10, kArmy);
    Store(input.army, 0x14, std::uint32_t{0x41726D79});
    Store(input.army, 0x120, kCommander);
    Store(input.army, 0x124, kUnit);
    Store(input.army, 0x38, static_cast<void *>(input.regiment_ids.data()));
    Store(input.army, 0x40, std::int32_t{2});
    Store(input.army, 0x44, std::int32_t{2});
    Store(input.army, 0x180, scene.stock);
    Store(input.army, 0x22, std::uint8_t{0});
    Store(input.army, 0x5C, std::int32_t{0});
    Store(input.army, 0x188, kPreviousDateStorage);
    Store(input.army, 0x190, kAnchorDateStorage);
    Store(input.army, 0x12C, kFleet);
    Store(input.army, 0x1E8, std::int32_t{-1});
    Store(input.fleet_storage, 0x20, static_cast<void *>(input.fleet_slots.data()));
    Store(input.fleet_storage, 0x2C, std::int32_t{2});
    Store(input.fleet_slots, 0x18, static_cast<void *>(input.fleet.data()));
    Store(input.fleet, 0x10, kFleet);
    Store(input.fleet, 0x20, std::int32_t{53288472});
    Store(input.invalid_character, 0x18, std::int32_t{-1});
    Store(input.regiment, 0x10, kRegiment);
    Store(input.regiment, 0x14, std::uint32_t{0x41725267});
    Store(input.regiment, 0x38, std::int32_t{50});
    Store(input.regiment, 0x3C, std::int32_t{100});
    Store(input.regiment, 0x40, std::int64_t{25000000});
    // A fresh one-entry scene: current phase12 is empty, next phase13 contains
    // exactly one original CArmy pointer. Every other phase is readable empty.
    input.next_phase_pointers = {input.army.data()};
    constexpr auto next_header = std::size_t{0x2A548 + 0x190 + 24 * 13};
    Store(input.game_data, next_header, static_cast<const void *>(input.next_phase_pointers.data()));
    Store(input.game_data, next_header + 0x08, std::int32_t{1});
    Store(input.game_data, next_header + 0x0C, std::int32_t{1});
    // Synthetic loaded table bytes, read by the production full-CDate builder.
    // D395353 => year1083/remainder58; no future DTO value is fixture-assigned.
    input.calendar_days[58] = 19;
    input.calendar_months[58] = 7;
    bindings.enabled = true;
    bindings.game_state_slot = &game_slot;
    bindings.unit_storage_slot = &unit_slot;
    bindings.internal_army_storage_slot = &army_slot;
    bindings.regiment_storage_slot = &regiment_slot;
    bindings.get_army_current_soldiers = CurrentSoldiers;
    bindings.get_army_maximum_soldiers = MaximumSoldiers;
    bindings.get_army_supply_capacity = SupplyCapacity;
    bindings.get_army_attrition_fraction = Attrition;
    bindings.get_army_monthly_supply_change = MonthlySupply;
    bindings.future_daily_supply_schedule_bindings =
        current::BindFutureDailySupplySchedule12004(kFixtureImageBase, current::kExecutableSha256);
    bindings.source_derived_next_daily_supply_frame_bindings =
        current::BindSourceDerivedNextDailySupplyFrame12004(kFixtureImageBase, current::kExecutableSha256);
    bindings.source_derived_next_daily_supply_frame_bindings.calendar_day_table =
        input.calendar_days.data();
    bindings.source_derived_next_daily_supply_frame_bindings.calendar_month_table =
        input.calendar_months.data();
    bindings.timing_bindings = {true, &input.loaded_grace_days};
    bindings.monthly_loss_budget_bindings.enabled = true;
    auto &budget = bindings.monthly_loss_budget_bindings;
    budget.is_unit_in_combat = InCombat;
    budget.is_unit_gathering = Gathering;
    budget.is_army_fleet_supply_active = FleetActive;
    budget.fleet_storage_slot = &fleet_slot;
    budget.fleet_date_sentinel = &input.fleet_date_sentinel;
    budget.supply_state_levels_slot = &levels_slot;
    budget.supply_state_levels_count = &input.supply_level_count;
    budget.supply_state_fractions_slot = &fractions_slot;
    budget.supply_state_fractions_count = &input.supply_fraction_count;
    budget.character_storage_slot = &character_slot;
    budget.character_fallback_slot = &character_fallback;
    budget.get_character_modifier_aggregator = ModifierAggregator;
    budget.read_character_modifier = ReadModifier;
    bindings.province_supply_character_fallback_slot = &character_fallback;
    bindings.get_province_supply_limit = ProvinceLimit;
    bindings.get_province_supply_usage = ProvinceUsage;
    bindings.is_regiment_supply_loss_eligible = RegimentEligible;
    bindings.current_province_supply_contributor_bindings = {true, SharesWarSide};
    auto &resupply = bindings.current_land_resupply_bindings;
    resupply.enabled = true;
    resupply.is_resupply_eligible = ResupplyEligible;
    resupply.is_army_fleet_supply_active = FleetActive;
    resupply.character_storage_slot = &character_slot;
    resupply.loaded_gain_raw = &input.loaded_gain;
    auto &land = bindings.current_land_supply_rate_bindings;
    land.enabled = true;
    land.province_component_condition = ProvinceCondition;
    land.read_province_component = ProvinceComponent;
    land.character_storage_slot = &character_slot;
    land.character_fallback_slot = &character_fallback;
    land.get_character_modifier_aggregator = ModifierAggregator;
    land.read_character_modifier = ReadModifier;
    land.loaded_excess_slope_raw = &input.loaded_excess_slope;
    land.loaded_min_loss_raw = &input.loaded_min_loss;
    land.loaded_max_loss_raw = &input.loaded_max_loss;
    land.loaded_divisor_floor_raw = &input.loaded_divisor_floor;
    bindings.current_fleet_supply_tick_bindings.enabled = true;
    // Same-capture LAND inverse supplies bare Fleetfalse; the real Fleet
    // collector publishes not_fleet/ready with legitimate null rate payload.
    bindings.loss_application_inputs_enabled = true;
    bindings.siege_loss_rate_raw = &input.siege_rate;
    bindings.raid_loss_rate_raw = &input.raid_rate;
    bindings.get_army_whole_loss_budget = WholeLossBudget;
    bindings.get_army_supply_loss_budget = SupplyLossBudget;
    bindings.is_army_siege_active = SiegeActive;
    bindings.monthly_caller_effect_bindings.enabled = true;

  }
};
std::int32_t CurrentSoldiers(void *receiver, std::uint8_t flags) {
  auto &f = *active;
  ++f.calls.current_soldiers;
  f.calls.events.emplace_back("army_current_soldiers_flags_" + std::to_string(flags));
  RecordAbi(f.calls, receiver == f.input.army.data() + 0x38 && flags < 4,
      "CurrentSoldiers receiver=" + PointerText(receiver) + " expected=" +
      PointerText(f.input.army.data() + 0x38) + " flags=" + std::to_string(flags));
  if (flags >= 4) return -1;
  ++f.calls.soldier_flags[flags];
  return flags == 0 || flags == 2 ? 100 : 0;
}
std::int32_t MaximumSoldiers(void *receiver) {
  auto &f = *active;
  ++f.calls.maximum_soldiers;
  f.calls.events.emplace_back("army_maximum_soldiers");
  RecordAbi(f.calls, receiver == f.input.army.data(),
      "MaximumSoldiers receiver=" + PointerText(receiver) + " expected=" + PointerText(f.input.army.data()));
  return 200;
}
std::int64_t *SupplyCapacity(std::int64_t *out, void *receiver, void *details) {
  auto &f = *active;
  ++f.calls.supply_capacity;
  f.calls.events.emplace_back("army_supply_capacity");
  RecordAbi(f.calls, out && receiver == f.input.army.data() && details == nullptr,
      "SupplyCapacity out=" + PointerText(out) + " receiver=" + PointerText(receiver) +
      " expected=" + PointerText(f.input.army.data()) + " details=" + PointerText(details));
  *out = 200000000;
  return out;
}
std::int64_t *Attrition(void *receiver, std::int64_t *out, void *details) {
  auto &f = *active;
  ++f.calls.attrition_fraction;
  f.calls.events.emplace_back("army_attrition_fraction");
  RecordAbi(f.calls, out && receiver == f.input.army.data() && details == nullptr,
      "Attrition out=" + PointerText(out) + " receiver=" + PointerText(receiver) +
      " expected=" + PointerText(f.input.army.data()) + " details=" + PointerText(details));
  *out = 0;
  return out;
}
std::int64_t *MonthlySupply(void *receiver, std::int64_t *out, void *province, void *details) {
  auto &f = *active;
  ++f.calls.monthly_supply;
  f.calls.events.emplace_back("army_monthly_supply_change");
  RecordAbi(f.calls, out && receiver == f.input.army.data() &&
      province == f.input.province.data() && details == nullptr,
      "MonthlySupply out=" + PointerText(out) + " receiver=" + PointerText(receiver) +
      " expected_army=" + PointerText(f.input.army.data()) + " province=" + PointerText(province) +
      " expected_province=" + PointerText(f.input.province.data()) + " details=" + PointerText(details));
  // Direct current LAND rate has no date/grace gate. Preserve the source-
  // consistent observed current total separately from the prospective program.
  *out = f.scene.observed_rate;
  return out;
}
bool InCombat(void *receiver) {
  auto &f = *active;
  ++f.calls.combat;
  f.calls.events.emplace_back("unit_in_combat");
  RecordAbi(f.calls, receiver == f.input.unit.data(),
      "InCombat receiver=" + PointerText(receiver) + " expected=" + PointerText(f.input.unit.data()));
  return false;
}
bool Gathering(void *receiver) {
  auto &f = *active;
  ++f.calls.gathering;
  f.calls.events.emplace_back("unit_gathering");
  RecordAbi(f.calls, receiver == f.input.unit.data(),
      "Gathering receiver=" + PointerText(receiver) + " expected=" + PointerText(f.input.unit.data()));
  return false;
}
bool FleetActive(void *receiver) {
  auto &f = *active;
  ++f.calls.fleet_active;
  f.calls.events.emplace_back("army_fleet_active");
  RecordAbi(f.calls, receiver == f.input.army.data(),
      "FleetActive receiver=" + PointerText(receiver) + " expected=" + PointerText(f.input.army.data()));
  return false;
}
std::int32_t ProvinceLimit(void *province, void *owner, void *commander, void *details) {
  auto &f = *active;
  ++f.calls.province_limit;
  f.calls.events.emplace_back("current_province_native_limit");
  RecordAbi(f.calls, province == f.input.province.data() &&
      owner == f.input.owner.data() && commander == f.input.commander.data() &&
      details == nullptr,
      "ProvinceLimit province=" + PointerText(province) + " expected_province=" + PointerText(f.input.province.data()) +
      " owner=" + PointerText(owner) + " expected_owner=" + PointerText(f.input.owner.data()) +
      " commander=" + PointerText(commander) + " expected_commander=" + PointerText(f.input.commander.data()) +
      " details=" + PointerText(details));
  return 100;
}
std::int32_t ProvinceUsage(void *province, void *owner, std::int32_t mode,
                          std::int64_t *details) {
  auto &f = *active;
  ++f.calls.province_usage;
  f.calls.events.emplace_back("current_province_native_usage");
  RecordAbi(f.calls, province == f.input.province.data() &&
      owner == f.input.owner.data() && mode == 0 && details == nullptr,
      "ProvinceUsage province=" + PointerText(province) + " expected_province=" + PointerText(f.input.province.data()) +
      " owner=" + PointerText(owner) + " expected_owner=" + PointerText(f.input.owner.data()) +
      " mode=" + std::to_string(mode) + " details=" + PointerText(details));
  return f.input.native_usage;
}
bool RegimentEligible(void *regiment) {
  auto &f = *active;
  ++f.calls.regiment_eligible;
  f.calls.events.emplace_back("province_contributor_regiment_eligible");
  RecordAbi(f.calls, regiment == f.input.regiment.data(),
      "RegimentEligible receiver=" + PointerText(regiment) + " expected=" + PointerText(f.input.regiment.data()));
  return true;
}
bool SharesWarSide(void *left, void *right, void *details) {
  auto &f = *active;
  ++f.calls.shares_war_side;
  RecordAbi(f.calls, left == f.input.owner.data() && right == f.input.owner.data() && details == nullptr,
      "SharesWarSide left=" + PointerText(left) + " right=" + PointerText(right) +
      " expected_owner=" + PointerText(f.input.owner.data()) + " details=" + PointerText(details));
  return true;
}
bool ResupplyEligible(void *owner, void *province) {
  auto &f = *active;
  ++f.calls.resupply;
  f.calls.events.emplace_back("current_owner_province_resupply");
  RecordAbi(f.calls, owner == f.input.owner.data() && province == f.input.province.data(),
      "ResupplyEligible owner=" + PointerText(owner) + " expected_owner=" + PointerText(f.input.owner.data()) +
      " province=" + PointerText(province) + " expected_province=" + PointerText(f.input.province.data()));
  return true;
}
bool ProvinceCondition(void *province) {
  auto &f = *active;
  ++f.calls.province_condition;
  f.calls.events.emplace_back("current_province_component_condition");
  RecordAbi(f.calls, province == f.input.province.data(),
      "ProvinceCondition receiver=" + PointerText(province) + " expected=" + PointerText(f.input.province.data()));
  return true;
}
std::int64_t *ProvinceComponent(std::int64_t *out, void *receiver,
    std::int32_t ordinal, void *details, std::int64_t multiplier, std::int32_t mode) {
  auto &f = *active;
  ++f.calls.province_component;
  f.calls.events.emplace_back("current_province_component_427");
  RecordAbi(f.calls, out != nullptr && receiver == f.input.province.data() + 0x30 &&
      ordinal == 0x1AB && details == nullptr && multiplier == 100000 && mode == 0,
      "ProvinceComponent out=" + PointerText(out) + " receiver=" + PointerText(receiver) +
      " expected=" + PointerText(f.input.province.data() + 0x30) + " ordinal=" + std::to_string(ordinal) +
      " details=" + PointerText(details) + " multiplier=" + std::to_string(multiplier) + " mode=" + std::to_string(mode));
  if (out == nullptr) return nullptr;
  *out = 0;
  return out;
}
void *ModifierAggregator(void *commander) {
  auto &f = *active;
  ++f.calls.modifier_aggregator;
  f.calls.events.emplace_back("valid_commander_modifier_aggregator");
  RecordAbi(f.calls, commander == f.input.commander.data(),
      "ModifierAggregator receiver=" + PointerText(commander) + " expected=" + PointerText(f.input.commander.data()));
  return f.input.modifier_aggregator.data();
}
std::int64_t *ReadModifier(void *receiver, std::int64_t *out, std::int32_t ordinal) {
  auto &f = *active;
  ++f.calls.modifier_reads;
  f.calls.modifier_ordinals.push_back(ordinal);
  f.calls.events.emplace_back("valid_commander_modifier_" + std::to_string(ordinal));
  RecordAbi(f.calls, out != nullptr &&
      receiver == f.input.modifier_aggregator.data() + 0x68 &&
      (ordinal == 0x1B0 || ordinal == 0x1A9),
      "ReadModifier out=" + PointerText(out) + " receiver=" + PointerText(receiver) +
      " expected=" + PointerText(f.input.modifier_aggregator.data() + 0x68) + " ordinal=" + std::to_string(ordinal));
  if (out == nullptr) return nullptr;
  *out = f.input.modifier_values[ordinal == 0x1A9 ? 0 : 1];
  return out;
}
bool SiegeActive(void *receiver) {
  auto &f = *active;
  ++f.calls.siege_active;
  f.calls.events.emplace_back("army_siege_active");
  RecordAbi(f.calls, receiver == f.input.army.data(),
      "SiegeActive receiver=" + PointerText(receiver) + " expected=" + PointerText(f.input.army.data()));
  return false;
}
std::int32_t SupplyLossBudget(void *receiver) {
  auto &f = *active;
  ++f.calls.supply_budget;
  f.calls.events.emplace_back("army_current_supply_loss_budget");
  RecordAbi(f.calls, receiver == f.input.army.data(),
      "SupplyLossBudget receiver=" + PointerText(receiver) + " expected=" + PointerText(f.input.army.data()));
  // All three ORIGINAL stocks select state1/fraction12500/eligible100.
  // This current direct getter12 is independent of updater grace rejection.
  return 12;
}
std::int32_t WholeLossBudget(std::int64_t rate, void *receiver) {
  auto &f = *active;
  ++f.calls.whole_budget;
  f.calls.events.emplace_back("army_whole_loss_budget");
  RecordAbi(f.calls, receiver == f.input.army.data() && rate == 0,
      "WholeLossBudget receiver=" + PointerText(receiver) + " expected=" +
      PointerText(f.input.army.data()) + " rate=" + std::to_string(rate));
  return 0;
}
void AppendString(std::string &out, std::string_view value) {
  out += '"';
  for (const char c : value) {
    if (c == '"' || c == '\\') out += '\\';
    out += c;
  }
  out += '"';
}
void AppendIds(std::string &out, const std::vector<std::int32_t> &ids) {
  out += '[';
  for (std::size_t i = 0; i < ids.size(); ++i) {
    if (i) out += ',';
    out += std::to_string(ids[i]);
  }
  out += ']';
}
std::string CallbackDiagnostics(const Fixture &f) {
  const auto &calls = f.calls;
  const std::pair<const char *, std::size_t> counters[]{
      {"current_soldiers", calls.current_soldiers}, {"maximum_soldiers", calls.maximum_soldiers},
      {"supply_capacity", calls.supply_capacity}, {"attrition_fraction", calls.attrition_fraction},
      {"monthly_supply", calls.monthly_supply}, {"combat", calls.combat},
      {"gathering", calls.gathering}, {"fleet_active", calls.fleet_active},
      {"siege_active", calls.siege_active}, {"supply_budget", calls.supply_budget},
      {"whole_budget", calls.whole_budget}, {"province_limit", calls.province_limit},
      {"province_usage", calls.province_usage}, {"regiment_eligible", calls.regiment_eligible},
      {"resupply", calls.resupply}, {"province_condition", calls.province_condition},
      {"province_component", calls.province_component}, {"modifier_aggregator", calls.modifier_aggregator},
      {"modifier_reads", calls.modifier_reads}, {"shares_war_side", calls.shares_war_side}};
  std::string out = "{\"scene\":";
  AppendString(out, f.scene.stem);
  for (const auto &[name, value] : counters) {
    out += ',';
    AppendString(out, name);
    out += ':';
    out += std::to_string(value);
  }
  out += ",\"abi_matches\":";
  out += calls.abi_matches ? "true" : "false";
  out += ",\"soldier_flags\":[";
  for (std::size_t i = 0; i < calls.soldier_flags.size(); ++i) {
    if (i) out += ',';
    out += std::to_string(calls.soldier_flags[i]);
  }
  out += "],\"modifier_ordinals\":";
  AppendIds(out, calls.modifier_ordinals);
  out += ",\"abi_failures\":[";
  for (std::size_t i = 0; i < calls.abi_failures.size(); ++i) {
    if (i) out += ',';
    AppendString(out, calls.abi_failures[i]);
  }
  out += "],\"events\":[";
  for (std::size_t i = 0; i < calls.events.size(); ++i) {
    if (i) out += ',';
    AppendString(out, calls.events[i]);
  }
  out += "]}";
  return out;
}
void Write(const std::filesystem::path &path, std::string_view text) {
  std::ofstream file(path, std::ios::binary);
  file << text << '\n';
  Check(static_cast<bool>(file), "new whole fixture artifact write failed");
}
void AssertScene(const Fixture &f, const Inputs &before, const game::ArmyStrengthSnapshot &row) {
  Check(row.available && row.army_id == kUnit && row.native_carmy_id_observable &&
      row.native_carmy_id == kArmy, "whole reader identity changed");
  Check(row.regiment_count == 2 && row.regiment_strengths && row.regiment_strengths->size() == 2 &&
      (*row.regiment_strengths)[0].army_regiment_id == kRegiment &&
      (*row.regiment_strengths)[1].army_regiment_id == kRegiment &&
      row.current_soldiers == 100 && row.maximum_soldiers == 200,
      "original whole duplicate roster/totals changed");
  Check(row.current_supply_raw == f.scene.stock && row.current_supply_capacity_raw == 200000000 &&
      row.current_supply_change_monthly_raw == f.scene.observed_rate &&
      row.current_attrition_fraction_raw == 0, "original current held-stock/scalars changed");
  Check(row.monthly_loss_budget_inputs_v1.has_value(), "real monthly operand collector omitted");
  const auto &budget = *row.monthly_loss_budget_inputs_v1;
  Check(budget.available && budget.unavailable_reason.empty() &&
      budget.unit_native_170_raw == 1 && budget.native_unit_in_combat == false &&
      budget.native_unit_gathering == false && budget.army_gathering_count_raw == 0 &&
      budget.native_fleet_supply_loss_suppressed == false &&
      budget.loaded_supply_state_levels == std::vector<std::int32_t>({2000, 1000, 0}) &&
      budget.loaded_supply_state_fractions_raw == std::vector<std::int64_t>({0, 12500, 25000}) &&
      budget.commander_valid == true && budget.commander_supply_modifier_id == 0x1B0 &&
      budget.commander_supply_modifier_raw == 0,
      "current suppression or original held-stock component operands changed");
  Check(row.loss_application_inputs_v1.has_value(), "actual native integer-budget getters omitted");
  const auto &loss = *row.loss_application_inputs_v1;
  Check(loss.available && loss.whole_soldiers == 100 && loss.supply_eligible_soldiers == 100 &&
      loss.current_supply_loss_budget == 12 && loss.definition_le_zero_soldiers == 0 &&
      loss.definition_le_zero_supply_eligible_soldiers == 0 &&
      loss.raid_association_id == -1 && !loss.raid_active && !loss.siege_active &&
      loss.siege_loss_budget == 0 && loss.raid_loss_budget == 0,
      "current native getter12 or independent eligible-current100 changed");
  Check(row.current_fleet_supply_tick_inputs_v1.has_value(), "real bare Fleet witness omitted");
  const auto &fleet = *row.current_fleet_supply_tick_inputs_v1;
  Check(fleet.ready && fleet.status == "not_fleet" &&
      fleet.native_fleet_branch_applicable == false && !fleet.unavailable_reason &&
      !fleet.current_native_date_low32 && !fleet.fleet_day_raw &&
      !fleet.loaded_fleet_day_sentinel_raw, "LAND bare predicate/date-null contract changed");
  Check(row.current_land_resupply_v1.has_value(), "real current LAND resupply omitted");
  const auto &gain = *row.current_land_resupply_v1;
  Check(gain.status == "available" && gain.current_observation_ready &&
      gain.province_id == 1 && gain.owner_character_id == 29829 &&
      gain.native_land_branch_applicable == true && gain.native_resupply_eligible == true &&
      gain.loaded_gain_raw == 2000000, "current native LAND gain inputs changed");
  Check(row.current_land_supply_rate_inputs_v1.has_value(), "real full LAND raw collector omitted");
  const auto &land = *row.current_land_supply_rate_inputs_v1;
  Check(land.status == "available" && land.current_observation_ready &&
      land.subject_army_id == kUnit && land.subject_carmy_id == kArmy &&
      land.province_id == 1 && land.owner_character_id == 29829 &&
      land.native_land_branch_applicable == true &&
      land.native_province_component_applicable == true && land.province_component_raw == 0 &&
      land.loaded_excess_slope_raw == 100000 && land.loaded_min_loss_raw == 100000 &&
      land.loaded_max_loss_raw == 500000 && land.loaded_divisor_floor_raw == f.scene.divisor_floor &&
      land.commander_raw_full_id == kCommander && land.commander_resolved_full_id == kCommander &&
      land.commander_used_native_fallback == false &&
      land.commander_modifier_1a9_raw == f.scene.fixed_modifier,
      "original full LAND operand/type/commander witnesses changed");
  Check(row.current_province_supply_contributors_v1.has_value(), "original nativeusage omitted");
  const auto &province = *row.current_province_supply_contributors_v1;
  Check(province.current_usage_ready && province.native_supply_usage_soldiers == f.scene.native_usage &&
      province.native_supply_limit_soldiers == 100 && province.subject_army_id == kUnit &&
      province.subject_carmy_id == kArmy && province.province_id == 1 &&
      province.owner_character_id == 29829 && province.native_province_unit_count == 1 &&
      province.occurrences.size() == 1 && province.occurrences[0].included == true,
      "ORIGINAL native Province usage/context changed");
  Check(row.future_daily_supply_schedule_inputs_v1.has_value(), "real all30 collector omitted");
  const auto &schedule = *row.future_daily_supply_schedule_inputs_v1;
  Check(schedule.status == "available" && schedule.ready &&
      schedule.current_date_storage_raw64 == kCurrentDateStorage &&
      schedule.current_date_raw_i32 == kCurrentDate &&
      schedule.native_day_index_raw_i32 == kCurrentD &&
      schedule.phases[13].matching_positions == std::vector<std::int32_t>({0}) &&
      schedule.phases[13].subject_occurrence_count_i32 == 1,
      "current captured schedule/date changed");
  Check(row.source_derived_next_daily_supply_frame_inputs_v1.has_value(),
      "production same-row next global-date RHS omitted");
  const auto &next = *row.source_derived_next_daily_supply_frame_inputs_v1;
  Check(next.ready && next.current_date_storage_raw64 == kCurrentDateStorage &&
      next.current_date_raw_i32 == kCurrentDate &&
      next.source_derived_next_date_raw_i32 == 53288472 &&
      next.source_derived_next_native_day_index_raw_i32 == 395353 &&
      next.source_derived_full_cdate64_ready &&
      next.source_derived_next_date_storage_raw64 == kExpectedNextDateStorage,
      "existing source next global-date builder changed");
  // Current total and ORIGINAL input fields remain independent native observations.
  // The fixture never assigns the prospective rate/stock/budget to a DTO.
  Check(f.calls.abi_matches && f.calls.current_soldiers == 5 &&
      f.calls.soldier_flags == std::array<std::size_t, 4>{1, 1, 2, 1} &&
      f.calls.maximum_soldiers == 1 && f.calls.supply_capacity == 1 &&
      f.calls.attrition_fraction == 1 && f.calls.monthly_supply == 1 &&
      f.calls.combat == 2 && f.calls.gathering == 2 && f.calls.fleet_active == 3 &&
      f.calls.siege_active == 1 && f.calls.supply_budget == 1 && f.calls.whole_budget == 0 &&
      f.calls.province_limit == 1 && f.calls.province_usage == 1 &&
      f.calls.regiment_eligible == 4 && f.calls.shares_war_side == 0 &&
      f.calls.resupply == 1 && f.calls.province_condition == 1 && f.calls.province_component == 1 &&
      // MonthlyBudgetInputs samples the validated commander twice; the
      // current LAND collector then reads its independent fixed1A9 operand.
      f.calls.modifier_aggregator == 3 && f.calls.modifier_reads == 3 &&
      f.calls.modifier_ordinals == std::vector<std::int32_t>({0x1B0, 0x1B0, 0x1A9}) &&
      f.calls.events == std::vector<std::string>({
          // Base regiment_strengths reads eligibility per original occurrence;
          // the later Province contributor independently reads both again.
          "province_contributor_regiment_eligible", "province_contributor_regiment_eligible",
          "army_current_soldiers_flags_0", "army_maximum_soldiers", "army_supply_capacity",
          "army_attrition_fraction", "army_monthly_supply_change", "army_siege_active",
          "army_current_soldiers_flags_1", "army_current_soldiers_flags_2",
          "army_current_soldiers_flags_3", "army_current_supply_loss_budget",
          "unit_in_combat", "unit_gathering", "army_fleet_active",
          "valid_commander_modifier_aggregator", "valid_commander_modifier_432",
          "unit_in_combat", "unit_gathering", "army_fleet_active",
          "valid_commander_modifier_aggregator", "valid_commander_modifier_432",
          "current_province_native_limit", "current_province_native_usage",
          "army_current_soldiers_flags_2", "province_contributor_regiment_eligible",
          "province_contributor_regiment_eligible", "army_fleet_active",
          "current_owner_province_resupply", "current_province_component_condition",
          "current_province_component_427", "valid_commander_modifier_aggregator",
          "valid_commander_modifier_425"}),
      ("whole LAND callback ABI/count/order changed: " + CallbackDiagnostics(f)).c_str());
  Check(f.input == before, "readonly whole reader changed original held-stock/input memory");
}

std::string SerializeWhole(const Fixture &f, const game::ArmyStrengthSnapshot &row) {
  std::string wire =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendString(wire, f.scene.stem);
  wire += ",\"ok\":true,"
      "\"result\":{\"step\":\"query-army-strengths-v1\",\"accepted\":true,"
      "\"status\":\"available\",\"query_sequence\":1,\"army_strengths\":[";
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); }, AppendIds, AppendString);
  wire += "]}}";
  return game::Render12004BuildIdentity(std::move(wire), game::Ck3_12004AdapterDescriptor());
}
std::string Context(const Fixture &f, const game::ArmyStrengthSnapshot &row) {
  const auto &next = *row.source_derived_next_daily_supply_frame_inputs_v1;
  std::string out =
      "{\"schema\":\"xar.source-derived-next-land-stock-supply-budget-native-context.v1\","
      "\"scene\":";
  AppendString(out, f.scene.stem);
  out += ",\"producer\":\"ReadArmyStrengthsForScope12004 -> AppendArmyStrengthV1 -> Render12004BuildIdentity\","
      "\"synthetic_context\":{\"actor_character_id\":29829,"
      "\"public_revision\":1,\"native_revision\":1,\"snapshot_id\":\"native:1\","
      "\"date_raw\":53288448,\"paused\":true,\"map_ready\":true,"
      "\"bridge_host_pid\":1200401,\"current_province_id\":1,\"scope_role\":\"player\","
      "\"scope_army_ids\":[16777217],\"war_ids\":[],"
      "\"transport_connection_id\":\"source-derived-next-land-stock-supply-budget-12004\","
      "\"episode_id\":\"source-derived-next-land-stock-supply-budget-12004\"},"
      "\"heartbeat_published\":false,\"native_inputs\":{\"current_date_storage_raw64\":30118059520,"
      "\"current_global_date_low32\":53288448,\"current_native_day_index_raw_i32\":12,"
      "\"source_derived_next_date_raw_i32\":53288472,"
      "\"source_derived_next_native_day_index_raw_i32\":395353,"
      "\"source_derived_next_date_storage_raw64\":";
  out += std::to_string(*next.source_derived_next_date_storage_raw64);
  out += ",\"source_derived_full_cdate64_ready\":true,\"original_native_usage_soldiers\":";
  out += std::to_string(f.scene.native_usage);
  out += ",\"native_supply_limit_soldiers\":100,\"held_current_stock_raw\":";
  out += std::to_string(f.scene.stock);
  out += ",\"current_observed_rate_raw\":";
  out += std::to_string(f.scene.observed_rate);
  out += ",\"held_capacity_raw\":200000000,\"native_current_supply_loss_budget\":12,"
      "\"loaded_supply_state_levels\":[2000,1000,0],"
      "\"loaded_supply_state_fractions_raw\":[0,12500,25000],"
      "\"commander_valid\":true,\"commander_raw_full_id\":83886081,"
      "\"commander_resolved_full_id\":83886081,\"commander_used_native_fallback\":false,"
      "\"commander_supply_modifier_id\":432,\"commander_supply_modifier_raw\":0,"
      "\"commander_modifier_1a9_raw\":";
  out += std::to_string(f.scene.fixed_modifier);
  out += ",\"loaded_divisor_floor_raw\":";
  out += std::to_string(f.scene.divisor_floor);
  out += ",\"loaded_excess_slope_raw\":100000,\"loaded_min_loss_raw\":100000,"
      "\"loaded_max_loss_raw\":500000,\"province_component_raw\":0,"
      "\"native_land_branch_applicable\":true,\"native_resupply_eligible\":true,"
      "\"loaded_gain_raw\":2000000,\"native_fleet_branch_applicable\":false,"
      "\"current_fleet_family_status\":\"not_fleet\",\"current_fleet_family_ready\":true,"
      "\"observed_army_byte_22_raw\":0,\"observed_last_supply_date_storage_raw64\":21528124856,"
      "\"observed_grace_anchor_date_storage_raw64\":38707994064,"
      "\"grace_anchor_date_raw\":53288400,\"loaded_grace_days\":2},"
      "\"callbacks\":{\"army_current_soldiers\":";
  out += std::to_string(f.calls.current_soldiers);
  out += ",\"army_current_soldiers_by_flags\":[1,1,2,1],"
      "\"army_maximum_soldiers\":1,\"army_supply_capacity\":1,"
      "\"army_attrition_fraction\":1,\"army_monthly_supply_change\":1,"
      "\"unit_in_combat\":2,\"unit_gathering\":2,\"army_fleet_active\":3,"
      "\"army_siege_active\":1,\"army_current_supply_loss_budget\":1,"
      "\"army_whole_loss_budget\":0,\"province_limit\":1,\"province_usage\":1,"
      "\"regiment_supply_eligible\":4,\"shares_current_war_side\":0,"
      "\"resupply_eligible\":1,\"province_component_condition\":1,\"province_component\":1,"
      "\"character_modifier_aggregator\":3,\"character_modifier_reads\":3,"
      "\"character_modifier_ordinals\":[432,432,425],\"native_updater\":0,"
      "\"native_daily_date_writer\":0,\"abi_matches\":";
  out += f.calls.abi_matches ? "true" : "false";
  out += ",\"ordered_events\":[";
  for (std::size_t i = 0; i < f.calls.events.size(); ++i) {
    if (i) out += ',';
    AppendString(out, f.calls.events[i]);
  }
  out += "]},\"all_fixture_input_bytes_unchanged\":true,\"assertions_passed\":true,"
      "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
      "\"native_post_updater_stock_observed\":false,\"conditional_single_add_clamp_selected\":true,"
      "\"actual_future_rate_getter_observed\":false,\"actual_future_capacity_getter_observed\":false,"
      "\"earlier_unit_stage_reconstructed\":false,\"future_stock_or_strength_ready\":false,"
      "\"full_daily_supply_transition_ready\":false,\"full_monthly_ready\":false,"
      "\"synthetic_calendar_tables\":true,\"G2_context_is_metadata_only\":true,"
      "\"G2_actual_stored_D_claimed\":false}";
  return out;
}

} // namespace

int main(int argc, char **argv) {
  std::filesystem::path output;
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir",
        "usage: xar_ck3_12004_source_derived_next_land_stock_supply_budget_whole_test --wire-dir <fresh-dir>");
    output = argv[2];
    std::filesystem::create_directories(output);
    for (const auto scene : kScenes) {
      auto fixture = std::make_unique<Fixture>(scene);
      Check(fixture->bindings.future_daily_supply_schedule_bindings.enabled &&
          fixture->bindings.source_derived_next_daily_supply_frame_bindings.enabled,
          "readonly actual4 date binders disabled");
      auto before = std::make_unique<Inputs>(fixture->input);
      active = fixture.get();
      const std::array<current::ArmyStrengthScope, 1> scope{
          current::ArmyStrengthScope{kUnit, game::ArmyStrengthScopeRole::player, {}}};
      std::vector<game::ArmyStrengthSnapshot> rows;
      const auto result = current::ReadArmyStrengthsForScope12004(fixture->bindings, scope, rows);
      Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 1,
          "real whole Strength producer did not return one available row");
      AssertScene(*fixture, *before, rows.front());
      Write(output / (std::string(scene.stem) + ".json"), SerializeWhole(*fixture, rows.front()));
      Write(output / (std::string(scene.stem) + "-native-context.json"), Context(*fixture, rows.front()));
      active = nullptr;
    }
    Write(output / "PRODUCER-RECEIPT.json",
        "{\"schema\":\"xar.source-derived-next-land-stock-supply-budget-producer-receipt.v1\","
        "\"status\":\"PASS\",\"scene_count\":3,\"whole_reader_calls\":3,"
        "\"whole_serializer_calls\":3,\"fixture_owned_objects_and_callbacks\":true,"
        "\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false,"
        "\"old_GREEN_replayed\":false,\"all_fixture_input_bytes_unchanged\":true}");
    active = nullptr;
    std::cout << "three source-derived next LAND stock and supply budget whole scenes emitted\n";
    return 0;
  } catch (const std::exception &error) {
    active = nullptr;
    if (!output.empty()) {
      std::string receipt =
          "{\"schema\":\"xar.source-derived-next-land-stock-supply-budget-producer-receipt.v1\","
          "\"status\":\"FAIL\",\"scene_count\":3,\"error\":";
      AppendString(receipt, error.what());
      receipt += ",\"native_EXE_callback_invoked\":false,\"actual_future_stage_observed\":false}";
      std::ofstream file(output / "PRODUCER-RECEIPT.json", std::ios::binary);
      file << receipt << '\n';
    }
    std::cerr << error.what() << '\n';
    return 1;
  }
}
