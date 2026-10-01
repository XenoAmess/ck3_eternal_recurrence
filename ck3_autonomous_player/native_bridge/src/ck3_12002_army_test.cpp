#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
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
  std::array<std::byte, 0x50> army{};
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
             rows[0].move_target_province_id == 2 && rows[0].current_province_id == 1, "unit semantics and route")) return false;
  const std::array<std::int32_t, 1> owner{8};
  if (!Check(ReadArmiesForCharacters(bindings, owner, rows) && rows.size() == 1 && rows[0].owner_character_id == 8,
             "owner filtering")) return false;
  Put(u2, 0x10, std::int32_t{0x05000001});
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows) && rows.size() == 1,
             "incorrect public slot identity skipped")) return false;
  Put(u2, 0x10, std::int32_t{0x05000002});
  route_ids[1] = 99;
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows) && rows[0].route_province_ids.empty() && !rows[0].move_target_observable,
             "invalid route province does not become a target")) return false;
  route_ids[1] = 2;
  std::array<ArmyStrengthScope, 1> scope{{{0x01000001, game::ArmyStrengthScopeRole::player, {42}}}};
  std::vector<game::ArmyStrengthSnapshot> strength;
  if (!Check(ReadArmyStrengthsForScope(bindings, scope, strength) == game::ReadArmyStrengthsResult::available &&
             strength.size() == 1 && strength[0].available && strength[0].current_soldiers == 900 &&
             strength[0].maximum_soldiers == 1500 && strength[0].ai_base_power_raw == 35802467 && strength[0].native_carmy_id == 0x02000001,
             "generation resolved army strength")) return false;
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
  Put(units, 0x2C, std::int32_t{0}); Put(units, 0x20, static_cast<void *>(nullptr));
  if (!Check(ReadArmiesForCharacters(bindings, {}, rows) && rows.empty(), "empty native unit storage")) return false;
  units_ptr = nullptr;
  if (!Check(!ReadArmiesForCharacters(bindings, {}, rows), "missing storage is unavailable")) return false;
  const auto bound = BindArmyImage(0x140000000, kExecutableSha256);
  if (!Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.unit_storage_slot) == 0x145D1E380,
             "exact image binding")) return false;
  return Check(!BindArmyImage(0x140000000, "old build").enabled, "old build rejected");
}
} // namespace

int main() {
  if (!Test()) return 1;
  std::cout << "CK3 1.20.0.2 army offline fixtures passed\n";
  return 0;
}
