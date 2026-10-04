#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/public_unit_id.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <charconv>
#include <stdexcept>
#include <string_view>
#include <cstring>
#include <iostream>
#include <limits>

namespace {
template <class T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
template <class T> T Get(const void *bytes, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(bytes) + offset, sizeof value);
  return value;
}
void *unit_one = nullptr;
std::array<void *, 3> reg_objects{};
bool mismatch = false;
std::int32_t unit_one_state = 7;
std::int32_t State(void *unit) { return unit == unit_one ? unit_one_state : 2; }
std::int32_t Current(void *ids_array, std::uint8_t flags) {
  if (flags != 0) return -1;
  const auto count = Get<std::int32_t>(ids_array, 0x0C);
  void *ids = Get<void *>(ids_array, 0);
  std::int32_t sum = 0;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto id = Get<std::int32_t>(ids, static_cast<std::size_t>(i) * 4);
    sum += Get<std::int32_t>(reg_objects[static_cast<std::uint32_t>(id) & 0xFFFFFF], 0x38);
  }
  return sum + (mismatch ? 1 : 0);
}
std::int32_t Maximum(void *army) {
  const auto count = Get<std::int32_t>(army, 0x44);
  void *ids = Get<void *>(army, 0x38);
  std::int32_t sum = 0;
  for (std::int32_t i = 0; i < count; ++i) {
    const auto id = Get<std::int32_t>(ids, static_cast<std::size_t>(i) * 4);
    sum += Get<std::int32_t>(reg_objects[static_cast<std::uint32_t>(id) & 0xFFFFFF], 0x3C);
  }
  return sum;
}
bool Check(bool ok, const char *label) {
  if (!ok) std::cerr << label << '\n';
  return ok;
}
bool Test() {
  using namespace xar;
  using namespace xar::ck3_12002;
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x150> data{};
  std::array<std::byte, 0x30> units{}, armies{}, regiments{};
  std::array<std::byte, 0x30> unit_slots{}, army_slots{}, regiment_slots{};
  std::array<std::byte, 0x180> u1{}, u2{};
  std::array<std::byte, 0x190> army{};
  std::array<std::byte, 0x50> r1{}, r2{};
  std::array<std::byte, 0x18> p1{}, p2{};
  std::array<void *, 3> provinces{nullptr, p1.data(), p2.data()};
  std::array<std::int32_t, 2> route_ids{1, 2};
  std::array<void *, 2> route{&route_ids[0], &route_ids[1]};
  std::array<std::int32_t, 2> regs{0x03000001, 0x04000002};
  Put(state, 0xA0, static_cast<void *>(data.data()));
  Put(data, 0x140, static_cast<void *>(provinces.data()));
  Put(data, 0x14C, std::int32_t{3});
  Put(p1, 0x10, std::int32_t{1}); Put(p2, 0x10, std::int32_t{2});
  Put(units, 0x20, static_cast<void *>(unit_slots.data())); Put(units, 0x2C, std::int32_t{3});
  Put(armies, 0x20, static_cast<void *>(army_slots.data())); Put(armies, 0x2C, std::int32_t{3});
  Put(regiments, 0x20, static_cast<void *>(regiment_slots.data())); Put(regiments, 0x2C, std::int32_t{3});
  Put(unit_slots, 0x18, static_cast<void *>(u1.data())); Put(unit_slots, 0x28, static_cast<void *>(u2.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(regiment_slots, 0x18, static_cast<void *>(r1.data())); Put(regiment_slots, 0x28, static_cast<void *>(r2.data()));
  Put(u1, 0x10, std::int32_t{0x01000001}); Put(u1, 0x174, std::int32_t{7});
  Put(u1, 0x178, std::int32_t{0x02000001}); Put(u1, 0x20, static_cast<void *>(p1.data()));
  Put(u1, 0x38, static_cast<void *>(route.data())); Put(u1, 0x40, std::int32_t{2}); Put(u1, 0x44, std::int32_t{2});
  Put(u2, 0x10, std::int32_t{0x05000002}); Put(u2, 0x174, std::int32_t{8});
  Put(u2, 0x170, std::int32_t{1});
  Put(army, 0x10, std::int32_t{0x02000001}); Put(army, 0x38, static_cast<void *>(regs.data()));
  Put(army, 0x40, std::int32_t{2}); Put(army, 0x44, std::int32_t{2});
  Put(r1, 0x10, regs[0]); Put(r2, 0x10, regs[1]);
  Put(r1, 0x14, std::uint32_t{0x41725267}); Put(r2, 0x14, std::uint32_t{0x41725267});
  Put(r1, 0x38, std::int32_t{600}); Put(r2, 0x38, std::int32_t{300});
  Put(r1, 0x3C, std::int32_t{1000}); Put(r2, 0x3C, std::int32_t{500});
  Put(r1, 0x40, std::int64_t{12345678}); Put(r2, 0x40, std::int64_t{23456789});
  unit_one = u1.data(); reg_objects = {nullptr, r1.data(), r2.data()};
  void *state_ptr = state.data(), *units_ptr = units.data(), *armies_ptr = armies.data(), *regiments_ptr = regiments.data();
  ArmyBindings bindings{true, &state_ptr, &units_ptr, &armies_ptr, &regiments_ptr, State, Current, Maximum};
  if (!Check(ResolveArmyUnit(bindings, 0x01000001) == u1.data() &&
             ResolveInternalArmy(bindings, 0x02000001) == army.data() &&
             ResolveArmyUnit(bindings, 0x02000001) == nullptr &&
             ResolveInternalArmy(bindings, 0x03000001) == nullptr,
             "public full generation resolvers")) return false;
  bool gathering = true;
  if (!Check(ReadArmyGathering(bindings, 0x01000001, gathering) && !gathering,
             "moving state is not gathering")) return false;
  unit_one_state = 5;
  if (!Check(ReadArmyGathering(bindings, 0x01000001, gathering) && gathering,
             "native state code five is gathering")) return false;
  if (!Check(!ReadArmyGathering(bindings, 0x02000001, gathering) && !gathering,
             "gathering rejects stale generation")) return false;
  unit_one_state = 7;
  std::vector<game::ArmySnapshot> rows;
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows, 7) && rows.size() == 2,
             "all units enumeration")) return false;
  if (!Check(rows[0].controllable && !rows[1].controllable && rows[0].army_state == "moving" &&
             rows[1].in_combat && rows[1].retreating && rows[0].route_province_ids == std::vector<std::int32_t>{1, 2} &&
             rows[0].move_target_province_id == 2 && rows[0].current_province_id == 1 &&
             rows[0].route_read_status == game::ArmyRouteReadStatus::complete_nonempty &&
             rows[0].route_source_count == 2 && rows[0].move_target_observable &&
             rows[1].route_read_status == game::ArmyRouteReadStatus::complete_empty &&
             rows[1].route_source_count == 0 && !rows[1].move_target_observable,
             "unit semantics and complete route provenance")) return false;
  // Enemy routes use the same producer and must carry the same provenance.
  Put(u2, 0x38, static_cast<void *>(route.data()));
  Put(u2, 0x40, std::int32_t{2}); Put(u2, 0x44, std::int32_t{2});
  const std::array<std::int32_t, 1> enemy_owner{8};
  if (!Check(ReadArmiesForCharacters(bindings, enemy_owner, rows, 7) &&
             rows.size() == 1 && !rows[0].controllable &&
             rows[0].route_read_status == game::ArmyRouteReadStatus::complete_nonempty &&
             rows[0].route_source_count == 2 &&
             rows[0].route_province_ids == std::vector<std::int32_t>{1, 2} &&
             rows[0].move_target_observable && rows[0].move_target_province_id == 2,
             "enemy route has complete provenance")) return false;
  Put(u2, 0x38, static_cast<void *>(nullptr));
  Put(u2, 0x40, std::int32_t{0}); Put(u2, 0x44, std::int32_t{0});
  const std::array<std::int32_t, 1> owner{8};
  if (!Check(ReadArmiesForCharacters(bindings, owner, rows) && rows.size() == 1 && rows[0].owner_character_id == 8,
             "owner filtering")) return false;
  Put(u2, 0x10, std::int32_t{0x05000001});
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows) && rows.size() == 1,
             "incorrect public slot identity skipped")) return false;
  Put(u2, 0x10, std::int32_t{0x05000002});
  route_ids[1] = 99;
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows) && rows[0].route_province_ids.empty() && !rows[0].move_target_observable &&
             rows[0].move_target_province_id == -1 &&
             rows[0].route_read_status == game::ArmyRouteReadStatus::unresolved_entry &&
             rows[0].route_source_count == 2,
             "invalid route province does not become a target")) return false;
  route_ids[1] = 2;
  route[1] = nullptr;
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows) &&
             rows[0].route_read_status == game::ArmyRouteReadStatus::unresolved_entry &&
             rows[0].route_source_count == 2 && rows[0].route_province_ids.empty() &&
             !rows[0].move_target_observable && rows[0].move_target_province_id == -1,
             "unresolved final entry never publishes partial route")) return false;
  route[1] = &route_ids[1];
  Put(u1, 0x38, static_cast<void *>(nullptr));
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows) &&
             rows[0].route_read_status == game::ArmyRouteReadStatus::unresolved_entry &&
             rows[0].route_source_count == 2 && rows[0].route_province_ids.empty() &&
             !rows[0].move_target_observable,
             "null nonempty route preserves unresolved source count")) return false;
  Put(u1, 0x38, static_cast<void *>(route.data()));
  for (const auto header : std::array<std::array<std::int32_t, 2>, 5>{{
           {{-1, 0}}, {{2, -1}}, {{1, 2}}, {{4097, 4097}}, {{2, 0}}}}) {
    Put(u1, 0x40, header[0]); Put(u1, 0x44, header[1]);
    if (!Check(ReadArmiesForCharacters(bindings, {}, rows) &&
               rows[0].route_province_ids.empty() && !rows[0].move_target_observable &&
               rows[0].move_target_province_id == -1 &&
               (header[1] == 0 && header[0] >= 0
                    ? rows[0].route_read_status == game::ArmyRouteReadStatus::complete_empty &&
                      rows[0].route_source_count == 0
                    : rows[0].route_read_status == game::ArmyRouteReadStatus::invalid_header &&
                      !rows[0].route_source_count.has_value()),
               "invalid or empty header has exact route provenance")) return false;
  }
  Put(u1, 0x40, std::int32_t{2}); Put(u1, 0x44, std::int32_t{2});
  std::array<ArmyStrengthScope, 1> scope{{{0x01000001, game::ArmyStrengthScopeRole::player, {42}}}};
  std::vector<game::ArmyStrengthSnapshot> strength;
  if (!Check(ReadArmyStrengthsForScope(bindings, scope, strength) == game::ReadArmyStrengthsResult::available &&
             strength.size() == 1 && strength[0].available && strength[0].current_soldiers == 900 &&
             strength[0].maximum_soldiers == 1500 && strength[0].ai_base_power_raw == 35802467 && strength[0].native_carmy_id == 0x02000001,
             "generation resolved army strength")) return false;
  if (!Check(strength[0].regiment_strengths.has_value() &&
             strength[0].regiment_strengths->size() == 2 &&
             (*strength[0].regiment_strengths)[0] == game::ArmyRegimentStrengthSnapshot{regs[0], 600, 1000} &&
             (*strength[0].regiment_strengths)[1] == game::ArmyRegimentStrengthSnapshot{regs[1], 300, 500},
             "complete actual full-ID regiment strengths share the native aggregate")) return false;
  Put(r1, 0x10, std::int32_t{0x09000001});
  if (!Check(ReadArmyStrengthsForScope(bindings, scope, strength) == game::ReadArmyStrengthsResult::partial &&
             !strength[0].available && strength[0].unavailable_reason == "regiment_not_found", "stale regiment generation")) return false;
  Put(r1, 0x10, regs[0]); Put(r1, 0x14, std::uint32_t{0});
  ReadArmyStrengthsForScope(bindings, scope, strength);
  if (!Check(strength[0].unavailable_reason == "regiment_identity_invalid", "new inline identity predicate")) return false;
  Put(r1, 0x14, std::uint32_t{0x41725267}); Put(r1, 0x38, std::int32_t{-1});
  ReadArmyStrengthsForScope(bindings, scope, strength);
  if (!Check(strength[0].unavailable_reason == "soldier_value_invalid", "negative soldiers")) return false;
  Put(r1, 0x38, std::numeric_limits<std::int32_t>::max());
  ReadArmyStrengthsForScope(bindings, scope, strength);
  if (!Check(strength[0].unavailable_reason == "aggregate_overflow", "soldier sum overflow")) return false;
  Put(r1, 0x38, std::int32_t{600}); mismatch = true;
  ReadArmyStrengthsForScope(bindings, scope, strength);
  if (!Check(strength[0].unavailable_reason == "native_helper_mismatch", "native getter cross check")) return false;
  mismatch = false;
  game::Snapshot snapshot{};
  if (!Check(ReadArmyStrengths(bindings, snapshot, strength) == game::ReadArmyStrengthsResult::requires_paused, "paused precondition")) return false;
  snapshot.paused = true;
  if (!Check(ReadArmyStrengths(bindings, snapshot, strength) == game::ReadArmyStrengthsResult::no_played_character, "played character precondition")) return false;
  snapshot.has_played_character = true;
  ReadArmiesForCharacters(bindings, {}, rows, 7);
  snapshot.player_armies = {rows[0]};
  game::ActiveWarSnapshot war{}; war.war_id = 42; war.allied_armies = {rows[0]};
  snapshot.active_wars = {war};
  if (!Check(ReadArmyStrengths(bindings, snapshot, strength) == game::ReadArmyStrengthsResult::available &&
             strength.size() == 1 && strength[0].scope_role == game::ArmyStrengthScopeRole::player &&
             strength[0].war_ids == std::vector<std::int32_t>{42}, "scope deduplication and war membership")) return false;
  // A full CUnit handle can be zero when generation and storage slot are zero.
  Put(unit_slots, 0x18, static_cast<void *>(nullptr));
  Put(unit_slots, 0x08, static_cast<void *>(u1.data()));
  Put(u1, 0x10, std::int32_t{0});
  if (!Check(ResolveArmyUnit(bindings, 0) == u1.data() &&
             ResolveArmyUnit(bindings, -1) == nullptr &&
             ResolveArmyUnit(bindings, 0x01000000) == nullptr,
             "zero CUnit resolves only exact slot generation")) return false;
  const std::array<std::int32_t, 1> zero_owner{7};
  if (!Check(ReadArmiesForCharacters(bindings, zero_owner, rows, 7) &&
             rows.size() == 1 && rows[0].army_id == 0 && rows[0].controllable,
             "zero CUnit remains a controllable published army")) return false;
  scope = {{0, game::ArmyStrengthScopeRole::player, {42}}};
  if (!Check(ReadArmyStrengthsForScope(bindings, scope, strength) ==
                 game::ReadArmyStrengthsResult::available &&
             strength.size() == 1 && strength[0].army_id == 0 &&
             strength[0].native_carmy_id == 0x02000001,
             "zero public CUnit strength keeps separate native CArmy")) return false;
  std::int32_t parsed_unit = -1;
  if (!Check(game::ParsePublicCUnitIdV1("0", parsed_unit) && parsed_unit == 0 &&
             game::ParsePublicCUnitIdV1("2147483647", parsed_unit) &&
             !game::ParsePublicCUnitIdV1("-1", parsed_unit) &&
             !game::ParsePublicCUnitIdV1("00", parsed_unit) &&
             !game::ParsePublicCUnitIdV1("2147483648", parsed_unit) &&
             !game::ParsePublicCUnitIdV1("true", parsed_unit),
             "public CUnit canonical bounded parser")) return false;
  // Strength's resolved CArmy handle has its own exact database identity;
  // zero is valid here independently of the public CUnit handle.
  Put(army_slots, 0x18, static_cast<void *>(nullptr));
  Put(army_slots, 0x08, static_cast<void *>(army.data()));
  Put(army, 0x10, std::int32_t{0});
  Put(u1, 0x178, std::int32_t{0});
  if (!Check(ResolveInternalArmy(bindings, 0) == army.data() &&
             ResolveInternalArmy(bindings, -1) == nullptr &&
             ResolveInternalArmy(bindings, 0x01000000) == nullptr,
             "zero CArmy resolves exact generation only")) return false;
  if (!Check(ReadArmyStrengthsForScope(bindings, scope, strength) ==
                 game::ReadArmyStrengthsResult::available &&
             strength.size() == 1 && strength[0].army_id == 0 &&
             strength[0].native_carmy_id_observable &&
             strength[0].native_carmy_id == 0 &&
             strength[0].current_soldiers == 900 &&
             strength[0].maximum_soldiers == 1500,
             "zero CArmy aggregate keeps native helper cross check")) return false;
  Put(r1, 0x14, std::uint32_t{0});
  if (!Check(ReadArmyStrengthsForScope(bindings, scope, strength) ==
                 game::ReadArmyStrengthsResult::partial &&
             strength[0].native_carmy_id_observable &&
             strength[0].native_carmy_id == 0 && !strength[0].available &&
             strength[0].unavailable_reason == "regiment_identity_invalid",
             "resolved zero CArmy keeps unavailable aggregate atomic")) return false;
  Put(r1, 0x14, std::uint32_t{0x41725267});
  Put(u1, 0x178, std::int32_t{0x01000000});
  if (!Check(ReadArmyStrengthsForScope(bindings, scope, strength) ==
                 game::ReadArmyStrengthsResult::partial &&
             !strength[0].native_carmy_id_observable &&
             strength[0].unavailable_reason == "native_carmy_not_found",
             "stale CArmy generation stays unobservable")) return false;
  Put(units, 0x2C, std::int32_t{0}); Put(units, 0x20, static_cast<void *>(nullptr));
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows) && rows.empty(), "empty native unit storage")) return false;
  units_ptr = nullptr;
  if (!Check(!ReadArmiesForCharacters(bindings, {}, rows), "missing storage is unavailable")) return false;
  const auto bound = BindArmyImage(0x140000000, kExecutableSha256);
  if (!Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.unit_storage_slot) == 0x145D1E380,
             "exact image binding")) return false;
  return Check(!BindArmyImage(0x140000000, "old build").enabled, "old build rejected");
}

void Require(bool condition, const char *label) {
  if (!condition) throw std::runtime_error(label);
}

void *supply_fixture_army = nullptr;
std::int64_t supply_fixture_capacity = 0;
std::int64_t supply_fixture_attrition = 0;
std::int32_t supply_fixture_capacity_calls = 0;
std::int32_t supply_fixture_attrition_calls = 0;

std::int64_t *SupplyCapacity(std::int64_t *output, void *army,
                             void *detail) {
  Require(army == supply_fixture_army && output != nullptr && detail == nullptr,
          "native capacity ABI: out, CArmy, null detail");
  ++supply_fixture_capacity_calls;
  *output = supply_fixture_capacity;
  return output;
}

std::int64_t *AttritionFraction(void *army, std::int64_t *output,
                               void *detail) {
  Require(army == supply_fixture_army && output != nullptr && detail == nullptr,
          "native attrition ABI: CArmy, out, null detail");
  ++supply_fixture_attrition_calls;
  *output = supply_fixture_attrition;
  return output;
}

std::string FixtureNumber(std::int64_t value) {
  std::array<char, 32> buffer{};
  const auto result = std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  Require(result.ec == std::errc{}, "numeric serializer");
  return std::string(buffer.data(), result.ptr);
}

void FixtureArray(std::string &output, const std::vector<std::int32_t> &values) {
  output += '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) output += ',';
    output += FixtureNumber(values[index]);
  }
  output += ']';
}

void FixtureString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  output += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output += '\\';
      output += static_cast<char>(character);
    } else if (character < 0x20U) {
      output += "\\u00";
      output += hex[(character >> 4U) & 0x0FU];
      output += hex[character & 0x0FU];
    } else {
      output += static_cast<char>(character);
    }
  }
  output += '"';
}

void EmitSupplyCase(std::string_view name,
                    const xar::game::ArmyStrengthSnapshot &row) {
  std::string wire = "{\"case\":";
  FixtureString(wire, name);
  wire += ",\"army_strengths\":[";
  xar::game::AppendArmyStrengthV1(
      wire, row, FixtureNumber, FixtureArray, FixtureString);
  wire += "]}";
  std::cout << wire << '\n';
}

void SupplyFixture() {
  using namespace xar;
  using namespace xar::ck3_12002;
  constexpr std::int32_t public_id = 0x01000001;
  constexpr std::int32_t native_id = 0x02000001;
  constexpr std::int32_t regiment_id = 0x03000001;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x190> army{};
  std::array<std::byte, 0x50> regiment{};
  std::array<std::byte, 0x30> units{}, armies{}, regiments{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{}, regiment_slots{};
  std::array<std::int32_t, 1> regiment_ids{regiment_id};
  Put(unit, 0x10, public_id);
  Put(unit, 0x178, native_id);
  Put(army, 0x10, native_id);
  Put(army, 0x124, public_id);
  Put(army, 0x38, static_cast<void *>(regiment_ids.data()));
  Put(army, 0x40, std::int32_t{1});
  Put(army, 0x44, std::int32_t{1});
  Put(regiment, 0x10, regiment_id);
  Put(regiment, 0x14, std::uint32_t{0x41725267});
  Put(regiment, 0x38, std::int32_t{900});
  Put(regiment, 0x3C, std::int32_t{1500});
  Put(regiment, 0x40, std::int64_t{35000000});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(regiment_slots, 0x18, static_cast<void *>(regiment.data()));
  Put(units, 0x20, static_cast<void *>(unit_slots.data()));
  Put(units, 0x2C, std::int32_t{2});
  Put(armies, 0x20, static_cast<void *>(army_slots.data()));
  Put(armies, 0x2C, std::int32_t{2});
  Put(regiments, 0x20, static_cast<void *>(regiment_slots.data()));
  Put(regiments, 0x2C, std::int32_t{2});
  void *units_ptr = units.data(), *armies_ptr = armies.data(), *regiments_ptr = regiments.data();
  ArmyBindings bindings{};
  bindings.enabled = true;
  bindings.unit_storage_slot = &units_ptr;
  bindings.internal_army_storage_slot = &armies_ptr;
  bindings.regiment_storage_slot = &regiments_ptr;
  bindings.get_army_current_soldiers = Current;
  bindings.get_army_maximum_soldiers = Maximum;
  bindings.get_army_supply_capacity = SupplyCapacity;
  bindings.get_army_attrition_fraction = AttritionFraction;
  reg_objects = {nullptr, regiment.data(), nullptr};
  supply_fixture_army = army.data();
  std::array<ArmyStrengthScope, 1> scope{{{public_id, game::ArmyStrengthScopeRole::player, {42}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  struct Case { const char *name; std::int64_t supply; std::int64_t capacity; std::int64_t attrition; };
  for (const auto &item : std::array<Case, 3>{{
      {"observed", 5'500'000, 12'500'000, 2'500},
      {"legal_zero", 0, 0, 0},
      {"signed_current_supply", -100'001, 15'000'000, 1'000}}}) {
    Put(army, 0x180, item.supply);
    supply_fixture_capacity = item.capacity;
    supply_fixture_attrition = item.attrition;
    const auto before_capacity = supply_fixture_capacity_calls;
    const auto before_attrition = supply_fixture_attrition_calls;
    Require(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available && rows.size() == 1,
            "genuine production strength reader");
    const auto &row = rows[0];
    Require(row.available && row.current_soldiers == 900 && row.maximum_soldiers == 1500 &&
            row.current_supply_raw == item.supply && row.current_supply_capacity_raw == item.capacity &&
            row.current_attrition_fraction_raw == item.attrition,
            "production result keeps exact raw values including zero");
    Require(supply_fixture_capacity_calls == before_capacity + 1 && supply_fixture_attrition_calls == before_attrition + 1,
            "one call per genuine native getter, correct ABI");
    EmitSupplyCase(item.name, row);
  }
  bindings.get_army_supply_capacity = nullptr;
  bindings.get_army_attrition_fraction = nullptr;
  Require(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "older adapter remains available without new getter bindings");
  Require(rows[0].current_supply_raw == -100'001 && !rows[0].current_supply_capacity_raw.has_value() &&
          !rows[0].current_attrition_fraction_raw.has_value(),
          "unassigned getter is unobserved, not synthesized zero");
  EmitSupplyCase("legacy_getters_unassigned", rows[0]);
  const auto bound12002 = BindArmyImage(0x140000000, kExecutableSha256);
  Require(bound12002.enabled && bound12002.get_army_supply_capacity == nullptr &&
          bound12002.get_army_attrition_fraction == nullptr,
          "genuine .2 binder never installs unproved .3 getters");
  bindings.get_army_supply_capacity = SupplyCapacity;
  bindings.get_army_attrition_fraction = AttritionFraction;
  const auto before_capacity = supply_fixture_capacity_calls;
  const auto before_attrition = supply_fixture_attrition_calls;
  Put(army, 0x124, std::int32_t{0x04000001});
  Require(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
          !rows[0].current_supply_raw.has_value() && !rows[0].current_supply_capacity_raw.has_value() &&
          !rows[0].current_attrition_fraction_raw.has_value(),
          "current supply and new getters share exact CArmy backlink");
  Require(supply_fixture_capacity_calls == before_capacity && supply_fixture_attrition_calls == before_attrition,
          "no getter called on unresolved backlink");
  EmitSupplyCase("backlink_unobserved", rows[0]);
  Put(army, 0x124, public_id);
  Put(army, 0x10, std::int32_t{0x05000001});
  Require(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::partial &&
          !rows[0].available && !rows[0].current_supply_capacity_raw.has_value() &&
          !rows[0].current_attrition_fraction_raw.has_value(),
          "partial production row keeps unobserved values separate");
  EmitSupplyCase("native_carmy_not_found", rows[0]);
}

void *replenishment_fixture_persistent = nullptr;
void *replenishment_fixture_chunk_zero = nullptr;
void *replenishment_fixture_chunk_six = nullptr;
void *replenishment_fixture_province = nullptr;
std::int64_t replenishment_fixture_monthly_fraction = 0;
std::int64_t replenishment_fixture_monthly_supply = 0;
bool replenishment_fixture_regiment_answer = true;
bool replenishment_fixture_chunk_answer = false;
std::int32_t replenishment_fixture_regiment_calls = 0;
std::int32_t replenishment_fixture_chunk_calls = 0;
std::int32_t replenishment_fixture_monthly_calls = 0;
std::int32_t replenishment_fixture_supply_calls = 0;

bool RegimentCanReplenish(void *regiment, void *chunk) {
  Require(regiment == replenishment_fixture_persistent &&
              (chunk == replenishment_fixture_chunk_zero || chunk == replenishment_fixture_chunk_six),
          "262C700 receives persistent CRegiment and exact matching chunk");
  ++replenishment_fixture_regiment_calls;
  return replenishment_fixture_regiment_answer;
}

bool ChunkCanReplenish(void *chunk) {
  Require(chunk == replenishment_fixture_chunk_zero || chunk == replenishment_fixture_chunk_six,
          "2657F10 receives the exact persistent chunk");
  ++replenishment_fixture_chunk_calls;
  return replenishment_fixture_chunk_answer;
}

std::int64_t *RegimentMonthlyFraction(void *regiment, std::int64_t *output) {
  Require(regiment == replenishment_fixture_persistent && output != nullptr,
          "262CAD0 receives CRegiment,out64 and returns out64");
  ++replenishment_fixture_monthly_calls;
  *output = replenishment_fixture_monthly_fraction;
  return output;
}

std::int64_t *ArmyMonthlySupply(void *army, std::int64_t *output, void *province,
                              void *detail) {
  Require(army == supply_fixture_army && output != nullptr &&
              province == replenishment_fixture_province && detail == nullptr,
          "24E51A0 receives CArmy,out64,current validated CProvince,null detail");
  ++replenishment_fixture_supply_calls;
  *output = replenishment_fixture_monthly_supply;
  return output;
}

void ReplenishmentFixture() {
  using namespace xar;
  using namespace xar::ck3_12002;
  constexpr std::int32_t public_id = 0x01000001;
  constexpr std::int32_t native_id = 0x02000001;
  constexpr std::int32_t army_regiment_id = 0x03000001;
  constexpr std::int32_t persistent_id = 0x04000002;
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x150> game_data{};
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x190> army{};
  std::array<std::byte, 0x50> army_regiment{};
  std::array<std::byte, 0x140> persistent{};
  std::array<std::byte, 0x10> first_record{};
  std::array<std::byte, 0x30> units{}, armies{}, army_regiments{}, persistent_regiments{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{}, army_regiment_slots{};
  std::array<std::byte, 0x30> persistent_slots{};
  std::array<std::byte, 0x18> province{}, invalid_province{};
  std::array<void *, 3> provinces{nullptr, nullptr, province.data()};
  std::array<std::int32_t, 1> regiment_ids{army_regiment_id};
  Put(game_state, 0xA0, static_cast<void *>(game_data.data()));
  Put(game_data, 0x140, static_cast<void *>(provinces.data()));
  Put(game_data, 0x14C, std::int32_t{3});
  Put(province, 0x10, std::int32_t{2});
  Put(invalid_province, 0x10, std::int32_t{1});
  Put(unit, 0x10, public_id);
  Put(unit, 0x178, native_id);
  Put(unit, 0x20, static_cast<void *>(province.data()));
  Put(army, 0x10, native_id);
  Put(army, 0x124, public_id);
  Put(army, 0x38, static_cast<void *>(regiment_ids.data()));
  Put(army, 0x40, std::int32_t{1});
  Put(army, 0x44, std::int32_t{1});
  Put(army, 0x180, std::int64_t{10'000'000});
  Put(army_regiment, 0x10, army_regiment_id);
  Put(army_regiment, 0x14, std::uint32_t{0x41725267});
  Put(army_regiment, 0x20, static_cast<void *>(first_record.data()));
  Put(army_regiment, 0x2C, std::int32_t{1});
  Put(army_regiment, 0x38, std::int32_t{600});
  Put(army_regiment, 0x3C, std::int32_t{1000});
  Put(army_regiment, 0x40, std::int64_t{35'000'000});
  Put(first_record, 0x08, persistent_id);
  Put(persistent, 0x10, persistent_id);
  Put(persistent, 0x14, std::uint32_t{0x52656769});
  Put(persistent, 0x128, std::int32_t{1000});
  for (std::int32_t index = 0; index < 7; ++index) {
    const auto offset = 0x18ULL + static_cast<std::size_t>(index) * 0x24;
    Put(persistent, offset + 0x08, persistent_id);
    Put(persistent, offset + 0x10, std::int32_t{-1});
  }
  Put(persistent, 0x18, std::int32_t{1000});
  Put(persistent, 0x1C, std::int32_t{600});
  Put(persistent, 0x28, army_regiment_id);
  Put(persistent, 0x30, std::int32_t{2});
  Put(persistent, 0x100, army_regiment_id);
  Put(persistent, 0x108, std::int32_t{3});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(army_regiment_slots, 0x18, static_cast<void *>(army_regiment.data()));
  Put(persistent_slots, 0x28, static_cast<void *>(persistent.data()));
  Put(units, 0x20, static_cast<void *>(unit_slots.data()));
  Put(units, 0x2C, std::int32_t{2});
  Put(armies, 0x20, static_cast<void *>(army_slots.data()));
  Put(armies, 0x2C, std::int32_t{2});
  Put(army_regiments, 0x20, static_cast<void *>(army_regiment_slots.data()));
  Put(army_regiments, 0x2C, std::int32_t{2});
  Put(persistent_regiments, 0x20, static_cast<void *>(persistent_slots.data()));
  Put(persistent_regiments, 0x2C, std::int32_t{3});
  void *state_ptr = game_state.data(), *units_ptr = units.data(), *armies_ptr = armies.data();
  void *army_regiments_ptr = army_regiments.data(), *persistent_ptr = persistent_regiments.data();
  ArmyBindings bindings{};
  bindings.enabled = true;
  bindings.game_state_slot = &state_ptr;
  bindings.unit_storage_slot = &units_ptr;
  bindings.internal_army_storage_slot = &armies_ptr;
  bindings.regiment_storage_slot = &army_regiments_ptr;
  bindings.get_army_current_soldiers = Current;
  bindings.get_army_maximum_soldiers = Maximum;
  bindings.get_army_supply_capacity = SupplyCapacity;
  bindings.get_army_attrition_fraction = AttritionFraction;
  bindings.persistent_regiment_storage_slot = &persistent_ptr;
  bindings.can_regiment_replenish = RegimentCanReplenish;
  bindings.can_chunk_replenish = ChunkCanReplenish;
  bindings.get_regiment_monthly_replenishment_fraction = RegimentMonthlyFraction;
  bindings.get_army_monthly_supply_change = ArmyMonthlySupply;
  reg_objects = {nullptr, army_regiment.data(), nullptr};
  supply_fixture_army = army.data();
  supply_fixture_capacity = 10'000'000;
  supply_fixture_attrition = 0;
  replenishment_fixture_persistent = persistent.data();
  replenishment_fixture_chunk_zero = persistent.data() + 0x18;
  replenishment_fixture_chunk_six = persistent.data() + 0xF0;
  replenishment_fixture_province = province.data();
  replenishment_fixture_monthly_fraction = 10'000;
  replenishment_fixture_monthly_supply = 2'000'000;
  std::array<ArmyStrengthScope, 1> scope{{{public_id, game::ArmyStrengthScopeRole::player, {42}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  auto read = [&]() -> const game::ArmyStrengthSnapshot & {
    Require(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
                rows.size() == 1 && rows[0].available,
            "new observations must use genuine production Strength reader");
    Require(rows[0].current_supply_raw == 10'000'000 &&
                rows[0].current_supply_capacity_raw == 10'000'000 &&
                rows[0].current_attrition_fraction_raw == 0,
            "first candidate's three source observations remain intact");
    return rows[0];
  };
  auto expect_available = [&](const game::ArmyStrengthSnapshot &row, std::int32_t count) {
    Require(row.regiment_replenishment.has_value() && row.regiment_replenishment->size() == 1,
            "one exact ArmyRegiment scope");
    const auto &item = row.regiment_replenishment->front();
    Require(item.available && item.army_regiment_id == army_regiment_id &&
                item.native_data_record_count == count && item.chunks.size() == 2 &&
                item.chunks[0].chunk_index == 0 && item.chunks[1].chunk_index == 6,
            "native first-record pointer, full identity, count and seven-chunk bounds");
    for (const auto &chunk : item.chunks) {
      Require(chunk.persistent_regiment_id == persistent_id &&
                  chunk.native_can_replenish == replenishment_fixture_regiment_answer &&
                  chunk.native_chunk_can_replenish == replenishment_fixture_chunk_answer &&
                  chunk.persistent_monthly_replenishment_fraction_raw == replenishment_fixture_monthly_fraction,
              "two independent native booleans and whole-persistent monthly fraction");
    }
    Require(item.chunks[0].current_soldiers == 600 && item.chunks[0].maximum_soldiers == 1000 &&
                item.chunks[0].state_raw == 2 && item.chunks[1].current_soldiers == 0 &&
                item.chunks[1].maximum_soldiers == 0 && item.chunks[1].state_raw == 3,
            "real zero is retained separately from unavailable");
  };
  auto expect_unavailable = [&](std::string_view reason, std::int32_t count) {
    const auto before = replenishment_fixture_regiment_calls + replenishment_fixture_chunk_calls +
                        replenishment_fixture_monthly_calls;
    const auto &row = read();
    Require(row.regiment_strengths.has_value() && row.regiment_strengths->size() == 1 &&
                row.regiment_strengths->front() ==
                    game::ArmyRegimentStrengthSnapshot{army_regiment_id, 600, 1000},
            "actual regiment counts remain complete when persistent first-record is absent");
    Require(row.regiment_replenishment.has_value() && row.regiment_replenishment->size() == 1,
            "unavailable subgraph keeps ArmyRegiment identity");
    const auto &item = row.regiment_replenishment->front();
    Require(!item.available && item.native_data_record_count == count &&
                item.unavailable_reason == reason && item.chunks.empty(),
            "unknown join cannot become native false or partial chunk rows");
    Require(before == replenishment_fixture_regiment_calls + replenishment_fixture_chunk_calls +
                          replenishment_fixture_monthly_calls,
            "unresolved native subgraph does not call a getter on another object type");
    EmitSupplyCase(reason, row);
  };
  const auto &observed = read();
  expect_available(observed, 1);
  Require(observed.current_supply_change_monthly_raw == 2'000'000 &&
              replenishment_fixture_regiment_calls == 2 && replenishment_fixture_chunk_calls == 2 &&
              replenishment_fixture_monthly_calls == 1 && replenishment_fixture_supply_calls == 1,
          "new native ABIs each execute once per exact receiver");
  EmitSupplyCase("native_first_record", observed);
  Put(army_regiment, 0x2C, std::int32_t{3});
  const auto &multiple = read();
  expect_available(multiple, 3);
  EmitSupplyCase("multiple_data_records_first_only", multiple);
  Put(army_regiment, 0x2C, std::int32_t{1});
  replenishment_fixture_regiment_answer = false;
  replenishment_fixture_chunk_answer = true;
  replenishment_fixture_monthly_fraction = -100'001;
  replenishment_fixture_monthly_supply = -200'000;
  const auto &signed_values = read();
  expect_available(signed_values, 1);
  Require(signed_values.current_supply_change_monthly_raw == -200'000,
          "signed Supplies/month is preserved before clamp or integration");
  EmitSupplyCase("independent_false_and_signed_monthly", signed_values);
  replenishment_fixture_regiment_answer = true;
  replenishment_fixture_chunk_answer = false;
  replenishment_fixture_monthly_fraction = 10'000;
  replenishment_fixture_monthly_supply = 2'000'000;
  Put(army_regiment, 0x2C, std::int32_t{0});
  expect_unavailable("army_regiment_first_record_absent", 0);
  Put(army_regiment, 0x2C, std::int32_t{1});
  Put(persistent, 0x10, std::int32_t{0x06000002});
  expect_unavailable("persistent_regiment_not_found", 1);
  Put(persistent, 0x10, persistent_id);
  Put(persistent, 0xF8, std::int32_t{0x06000002});
  expect_unavailable("regiment_chunk_backlink_mismatch", 1);
  Put(persistent, 0xF8, persistent_id);
  Put(unit, 0x20, static_cast<void *>(invalid_province.data()));
  const auto before_supply = replenishment_fixture_supply_calls;
  const auto &invalid_province_row = read();
  expect_available(invalid_province_row, 1);
  Require(!invalid_province_row.current_supply_change_monthly_raw.has_value() &&
              replenishment_fixture_supply_calls == before_supply,
          "monthly supply requires the existing validated current Province");
  EmitSupplyCase("current_province_unobserved", invalid_province_row);
  Put(unit, 0x20, static_cast<void *>(province.data()));
  bindings.persistent_regiment_storage_slot = nullptr;
  bindings.can_regiment_replenish = nullptr;
  bindings.can_chunk_replenish = nullptr;
  bindings.get_regiment_monthly_replenishment_fraction = nullptr;
  bindings.get_army_monthly_supply_change = nullptr;
  const auto &legacy = read();
  Require(!legacy.regiment_replenishment.has_value() &&
              !legacy.current_supply_change_monthly_raw.has_value(),
          "legacy adapter omits only new optional subdomains");
  const auto native_legacy = BindArmyImage(0x140000000, kExecutableSha256);
  Require(native_legacy.enabled && native_legacy.persistent_regiment_storage_slot == nullptr &&
              native_legacy.can_regiment_replenish == nullptr && native_legacy.can_chunk_replenish == nullptr &&
              native_legacy.get_regiment_monthly_replenishment_fraction == nullptr &&
              native_legacy.get_army_monthly_supply_change == nullptr,
          "the real .2 binder cannot install exact .3 replenishment or monthly-supply functions");
  EmitSupplyCase("legacy_replenishment_monthly_unassigned", legacy);
}

void *merge_fixture_army = nullptr;
std::int64_t merge_part_a = 0, merge_part_b = 0;
int merge_calls_a = 0, merge_calls_b = 0;
bool merge_wrong_return = false;
std::int64_t *MergePartA(void *army, std::int64_t *output, std::uint32_t flags) {
  Require(army == merge_fixture_army && output != nullptr && flags == 0,
          "merge destination A ABI: full resolved CArmy/out/flags0");
  ++merge_calls_a;
  *output = merge_part_a;
  return merge_wrong_return ? nullptr : output;
}
std::int64_t *MergePartB(void *army, std::int64_t *output) {
  Require(army == merge_fixture_army && output != nullptr,
          "merge destination B ABI: full resolved CArmy/out");
  ++merge_calls_b;
  *output = merge_part_b;
  return output;
}
void MergeWeightFixture() {
  using namespace xar;
  using namespace xar::ck3_12002;
  constexpr std::int32_t public_id = 0x01000001, native_id = 0x02000001;
  constexpr std::int32_t regiment_id = 0x03000001;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x190> army{};
  std::array<std::byte, 0x50> regiment{};
  std::array<std::byte, 0x30> units{}, armies{}, regiments{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{}, regiment_slots{};
  std::array<std::int32_t, 1> ids{regiment_id};
  Put(unit, 0x10, public_id); Put(unit, 0x178, native_id);
  Put(army, 0x10, native_id); Put(army, 0x124, public_id);
  Put(army, 0x38, static_cast<void *>(ids.data()));
  Put(army, 0x40, std::int32_t{1}); Put(army, 0x44, std::int32_t{1});
  Put(regiment, 0x10, regiment_id); Put(regiment, 0x14, std::uint32_t{0x41725267});
  Put(regiment, 0x38, std::int32_t{900}); Put(regiment, 0x3C, std::int32_t{1500});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(regiment_slots, 0x18, static_cast<void *>(regiment.data()));
  Put(units, 0x20, static_cast<void *>(unit_slots.data())); Put(units, 0x2C, std::int32_t{2});
  Put(armies, 0x20, static_cast<void *>(army_slots.data())); Put(armies, 0x2C, std::int32_t{2});
  Put(regiments, 0x20, static_cast<void *>(regiment_slots.data())); Put(regiments, 0x2C, std::int32_t{2});
  void *units_ptr=units.data(), *armies_ptr=armies.data(), *regiments_ptr=regiments.data();
  ArmyBindings bindings{};
  bindings.enabled=true; bindings.unit_storage_slot=&units_ptr;
  bindings.internal_army_storage_slot=&armies_ptr; bindings.regiment_storage_slot=&regiments_ptr;
  bindings.get_army_current_soldiers=Current; bindings.get_army_maximum_soldiers=Maximum;
  bindings.get_merge_destination_weight_part_a=MergePartA;
  bindings.get_merge_destination_weight_part_b=MergePartB;
  reg_objects={nullptr, regiment.data(), nullptr}; merge_fixture_army=army.data();
  std::array<ArmyStrengthScope, 1> scope{{{public_id,game::ArmyStrengthScopeRole::player,{42}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  struct Case { const char *name; std::int64_t a,b; bool observed; };
  for (const auto &c: std::array<Case,5>{{
      {"role_destination_subset",50'000'000,20'000'000,true},
      {"zero_is_observed",0,0,true},
      {"negative_unknown",-1,0,false},
      {"greater_than_source_unknown",90'000'001,0,false},
      {"sum_exceeds_source_unknown",60'000'000,40'000'000,false}}}) {
    merge_part_a=c.a; merge_part_b=c.b;
    int before_a=merge_calls_a, before_b=merge_calls_b;
    Require(ReadArmyStrengthsForScope(bindings,scope,rows)==game::ReadArmyStrengthsResult::available,
            "actual production reader strength available");
    Require(rows[0].current_soldiers==900 && rows[0].merge_supply_destination_weight_raw.has_value()==c.observed,
            "role-specific operand versus unchanged source strength");
    if (c.observed) Require(*rows[0].merge_supply_destination_weight_raw==c.a+c.b,"exact operand sum");
    Require(merge_calls_a==before_a+1 && merge_calls_b==before_b+1,"one call per leaf");
    EmitSupplyCase(c.name,rows[0]);
  }
  merge_part_a=50'000'000; merge_part_b=20'000'000; merge_wrong_return=true;
  Require(ReadArmyStrengthsForScope(bindings,scope,rows)==game::ReadArmyStrengthsResult::available &&
          !rows[0].merge_supply_destination_weight_raw.has_value(),"wrong return unknown");
  EmitSupplyCase("wrong_return_unknown",rows[0]); merge_wrong_return=false;
  bindings.get_merge_destination_weight_part_b=nullptr;
  int before_a=merge_calls_a, before_b=merge_calls_b;
  Require(ReadArmyStrengthsForScope(bindings,scope,rows)==game::ReadArmyStrengthsResult::available &&
          !rows[0].merge_supply_destination_weight_raw.has_value() && merge_calls_a==before_a &&
          merge_calls_b==before_b,"missing one leaf leaves operand unknown without partial calls");
  EmitSupplyCase("binding_missing_unknown",rows[0]);
  bindings.get_merge_destination_weight_part_b=MergePartB; Put(army,0x124,std::int32_t{0x04000001});
  Require(ReadArmyStrengthsForScope(bindings,scope,rows)==game::ReadArmyStrengthsResult::available &&
          !rows[0].merge_supply_destination_weight_raw.has_value() && merge_calls_a==before_a &&
          merge_calls_b==before_b,"full CArmy to public backlink prevents leaf call");
  EmitSupplyCase("backlink_missing_unknown",rows[0]); Put(army,0x124,public_id);
  Put(army,0x10,std::int32_t{0x05000001});
  Require(ReadArmyStrengthsForScope(bindings,scope,rows)==game::ReadArmyStrengthsResult::partial &&
          !rows[0].merge_supply_destination_weight_raw.has_value() && merge_calls_a==before_a,
          "native full generation mismatch prevents leaf call");
  EmitSupplyCase("native_generation_missing_unknown",rows[0]);
  const auto legacy=BindArmyImage(0x140000000,kExecutableSha256);
  Require(legacy.enabled && legacy.get_merge_destination_weight_part_a==nullptr &&
          legacy.get_merge_destination_weight_part_b==nullptr,"unchanged .2 binder has no exact3 leaf");
}

} // namespace

int main(int argc, char **argv) {
  if (argc == 2 && std::string_view(argv[1]) == "--merge-weight-fixture") {
    MergeWeightFixture();
    return 0;
  }
  if (argc == 2 && std::string_view(argv[1]) == "--replenishment-fixture") {
    ReplenishmentFixture();
    return 0;
  }
  if (argc == 2 && std::string_view(argv[1]) == "--supply-fixture") {
    SupplyFixture();
    return 0;
  }
  if (!Test()) return 1;
  std::cout << "CK3 1.20.0.2 army offline fixtures passed\n";
  return 0;
}
