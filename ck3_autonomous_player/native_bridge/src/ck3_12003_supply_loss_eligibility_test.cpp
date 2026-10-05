#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

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
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
std::vector<std::int32_t> predicate_receivers;
bool Eligible(void *regiment) {
  const auto id = Get<std::int32_t>(regiment, 0x10);
  predicate_receivers.push_back(id);
  return id == 0x04000002;
}
std::int32_t Current(void *, std::uint8_t flags) {
  Require(flags == 0, "unchanged aggregate receiver flags");
  return 12;
}
std::int32_t Maximum(void *) { return 12; }

std::string Wire(const xar::game::ArmyStrengthSnapshot &row) {
  std::string result;
  xar::game::AppendArmyStrengthV1(result, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t index = 0; index < values.size(); ++index) {
          if (index != 0) out += ',';
          out += std::to_string(values[index]);
        }
        out += ']';
      },
      [](std::string &out, std::string_view value) {
        out += '"'; out += value; out += '"';
      });
  return result;
}

void Test() {
  using namespace xar;
  using namespace xar::ck3_12002;
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x200> army{};
  std::array<std::byte, 0x50> r1{}, r2{};
  std::array<std::byte, 0x30> units{}, armies{}, regiments{};
  std::array<std::byte, 0x30> unit_slots{}, army_slots{}, regiment_slots{};
  // Deliberately reverse numeric IDs: native stored order must survive.
  std::array<std::int32_t, 2> ids{0x04000002, 0x03000001};
  Put(unit, 0x10, std::int32_t{0x01000001});
  Put(unit, 0x178, std::int32_t{0x02000001});
  Put(army, 0x10, std::int32_t{0x02000001});
  Put(army, 0x124, std::int32_t{0x01000001});
  Put(army, 0x38, static_cast<void *>(ids.data()));
  Put(army, 0x40, std::int32_t{2}); Put(army, 0x44, std::int32_t{2});
  Put(r1, 0x10, ids[1]); Put(r2, 0x10, ids[0]);
  for (auto *row : {&r1, &r2}) Put(*row, 0x14, std::uint32_t{0x41725267});
  Put(r1, 0x38, std::int32_t{9}); Put(r1, 0x3C, std::int32_t{9});
  Put(r2, 0x38, std::int32_t{3}); Put(r2, 0x3C, std::int32_t{3});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(regiment_slots, 0x18, static_cast<void *>(r1.data()));
  Put(regiment_slots, 0x28, static_cast<void *>(r2.data()));
  for (auto *storage : {&units, &armies, &regiments}) Put(*storage, 0x2C, std::int32_t{3});
  Put(units, 0x20, static_cast<void *>(unit_slots.data()));
  Put(armies, 0x20, static_cast<void *>(army_slots.data()));
  Put(regiments, 0x20, static_cast<void *>(regiment_slots.data()));
  void *units_ptr = units.data(), *armies_ptr = armies.data(), *regiments_ptr = regiments.data();
  ArmyBindings bindings{};
  bindings.enabled = true;
  bindings.unit_storage_slot = &units_ptr;
  bindings.internal_army_storage_slot = &armies_ptr;
  bindings.regiment_storage_slot = &regiments_ptr;
  bindings.get_army_current_soldiers = Current;
  bindings.get_army_maximum_soldiers = Maximum;
  bindings.is_regiment_supply_loss_eligible = Eligible;
  const auto unit_before = unit;
  const auto army_before = army;
  const auto r1_before = r1;
  const auto r2_before = r2;
  std::array<ArmyStrengthScope, 1> scope{{{0x01000001, game::ArmyStrengthScopeRole::player, {42}}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  Require(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "production strength reader with bound supply predicate");
  const auto &roster = *rows[0].regiment_strengths;
  Require(predicate_receivers == std::vector<std::int32_t>{ids[0], ids[1]},
          "predicate receives full ArRg identities once in stored order");
  Require(roster[0].army_regiment_id == ids[0] && roster[1].army_regiment_id == ids[1] &&
          roster[0].native_supply_loss_eligible == true && roster[1].native_supply_loss_eligible == false &&
          roster[0].supply_loss_eligibility_unavailable_reason.empty(),
          "true and false are both observed values on corresponding rows");
  const auto wire = Wire(rows[0]);
  Require(wire.find("\"native_supply_loss_eligible\":true") != std::string::npos &&
          wire.find("\"native_supply_loss_eligible\":false") != std::string::npos &&
          wire.find("\"supply_loss_eligibility_unavailable_reason\":null") != std::string::npos,
          "production serializer publishes observed booleans and clear reason");
  Require(unit == unit_before && army == army_before && r1 == r1_before && r2 == r2_before,
          "readonly predicate observation preserves fixture objects");
  bindings.is_regiment_supply_loss_eligible = nullptr;
  Require(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
          !(*rows[0].regiment_strengths)[0].native_supply_loss_eligible.has_value() &&
          predicate_receivers.size() == 2,
          "unbound predicate stays unknown without suppressing parent strength");
  Require(Wire(rows[0]).find("\"native_supply_loss_eligible\":null") != std::string::npos &&
          Wire(rows[0]).find("supply_loss_eligibility_not_bound") != std::string::npos,
          "unknown wire retains explicit reason");
  bindings.is_regiment_supply_loss_eligible = Eligible;
  Put(r2, 0x10, std::int32_t{0x05000002});
  Require(ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::partial &&
          predicate_receivers.size() == 2,
          "stale generation is rejected before predicate invocation");
}
} // namespace

int main() {
  try {
    Test();
    std::cout << "PASS: supply eligibility production reader/serializer focused fixture\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
