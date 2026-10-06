#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_world.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar;
namespace current = ck3_12004;
constexpr std::int32_t kUnit = 0x01000001;
constexpr std::int32_t kArmy = 0x02000001;
constexpr std::int32_t kRegiment = 0x03000001;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <class T, std::size_t N>
void Store(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Check(offset <= N && sizeof(T) <= N - offset, "fixture store out of bounds");
  std::memcpy(object.data() + offset, &value, sizeof(value));
}
template <class T>
T Load(const void *object, std::size_t offset) {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof(result));
  return result;
}

struct Fixture;
Fixture *active = nullptr;
std::int32_t State(void *);
std::int32_t CurrentSoldiers(void *, std::uint8_t);
std::int32_t MaximumSoldiers(void *);
std::int32_t DisembarkDays(const void *);
std::int64_t *SupplyCapacity(std::int64_t *, void *, void *);
std::int64_t *Attrition(void *, std::int64_t *, void *);
std::int64_t *MonthlySupply(void *, std::int64_t *, void *, void *);

// All objects and callback bodies are fixture owned. Their offsets come from
// the closed actual .4 source packet. Only the owning reader and whole row
// serializer are production code; this never calls an EXE function address.
struct Fixture {
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x150> game_data{};
  std::array<std::byte, 0x30> unit_storage{}, army_storage{}, regiment_storage{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{}, regiment_slots{};
  std::array<std::byte, 0x180> unit{};
  std::array<std::byte, 0x200> army{};
  std::array<std::byte, 0x50> regiment{};
  std::array<std::byte, 0x18> province{};
  std::array<void *, 2> provinces{nullptr, province.data()};
  std::array<std::int32_t, 2> regiment_ids{kRegiment, kRegiment};
  void *game_slot = game_state.data();
  void *unit_slot = unit_storage.data();
  void *army_slot = army_storage.data();
  void *regiment_slot = regiment_storage.data();
  current::ArmyBindings bindings{};
  std::size_t disembark_calls = 0;

  explicit Fixture(std::int32_t days, bool getter_available) {
    Store(game_state, 0xA0, static_cast<void *>(game_data.data()));
    Store(game_data, 0x140, static_cast<void *>(provinces.data()));
    Store(game_data, 0x14C, std::int32_t{2});
    Store(province, 0x10, std::int32_t{1});
    Store(unit_storage, 0x20, static_cast<void *>(unit_slots.data()));
    Store(unit_storage, 0x2C, std::int32_t{2});
    Store(army_storage, 0x20, static_cast<void *>(army_slots.data()));
    Store(army_storage, 0x2C, std::int32_t{2});
    Store(regiment_storage, 0x20, static_cast<void *>(regiment_slots.data()));
    Store(regiment_storage, 0x2C, std::int32_t{2});
    Store(unit_slots, 0x18, static_cast<void *>(unit.data()));
    Store(army_slots, 0x18, static_cast<void *>(army.data()));
    Store(regiment_slots, 0x18, static_cast<void *>(regiment.data()));
    Store(unit, 0x10, kUnit);
    Store(unit, 0x174, std::int32_t{29829});
    Store(unit, 0x178, kArmy);
    Store(unit, 0x20, static_cast<void *>(province.data()));
    Store(army, 0x10, kArmy);
    Store(army, 0x14, std::uint32_t{0x41726D79});
    Store(army, 0x124, kUnit);
    Store(army, 0x38, static_cast<void *>(regiment_ids.data()));
    Store(army, 0x40, std::int32_t{2});
    Store(army, 0x44, std::int32_t{2});
    Store(army, 0x180, std::int64_t{123450000});
    Store(army, 0x1D0, days);
    Store(regiment, 0x10, kRegiment);
    Store(regiment, 0x14, std::uint32_t{0x41725267});
    Store(regiment, 0x38, std::int32_t{50});
    Store(regiment, 0x3C, std::int32_t{100});
    Store(regiment, 0x40, std::int64_t{25000000});
    bindings.enabled = true;
    bindings.game_state_slot = &game_slot;
    bindings.unit_storage_slot = &unit_slot;
    bindings.internal_army_storage_slot = &army_slot;
    bindings.regiment_storage_slot = &regiment_slot;
    bindings.get_unit_state = State;
    bindings.get_army_current_soldiers = CurrentSoldiers;
    bindings.get_army_maximum_soldiers = MaximumSoldiers;
    bindings.current_disembark_penalty_enabled = true;
    bindings.get_army_disembark_penalty_days = getter_available ? DisembarkDays : nullptr;
    bindings.get_army_supply_capacity = SupplyCapacity;
    bindings.get_army_attrition_fraction = Attrition;
    bindings.get_army_monthly_supply_change = MonthlySupply;
  }
};

std::int32_t State(void *receiver) {
  Check(active && receiver == active->unit.data(), "unit state receiver changed");
  return 1;
}
std::int32_t CurrentSoldiers(void *receiver, std::uint8_t flags) {
  Check(active && receiver == active->army.data() + 0x38 && flags == 0,
      "current soldier receiver or flags changed");
  return 100;
}
std::int32_t MaximumSoldiers(void *receiver) {
  Check(active && receiver == active->army.data(), "maximum soldier receiver changed");
  return 200;
}
std::int32_t DisembarkDays(const void *receiver) {
  Check(active && receiver == active->army.data(), "disembark CArmy receiver changed");
  ++active->disembark_calls;
  return Load<std::int32_t>(receiver, 0x1D0);
}
std::int64_t *SupplyCapacity(std::int64_t *out, void *receiver, void *details) {
  Check(active && out && receiver == active->army.data() && details == nullptr,
      "supply capacity ABI changed");
  *out = 200000000;
  return out;
}
std::int64_t *Attrition(void *receiver, std::int64_t *out, void *details) {
  Check(active && out && receiver == active->army.data() && details == nullptr,
      "attrition fraction ABI changed");
  *out = 1250;
  return out;
}
std::int64_t *MonthlySupply(void *receiver, std::int64_t *out,
    void *province, void *details) {
  Check(active && out && receiver == active->army.data() &&
      province == active->province.data() && details == nullptr,
      "monthly supply change ABI changed");
  *out = -1200000;
  return out;
}

void AppendString(std::string &out, std::string_view value) {
  out += '"';
  for (const char ch : value) {
    if (ch == '"' || ch == '\\') out += '\\';
    out += ch;
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
void Write(const std::filesystem::path &path, std::string_view text) {
  std::ofstream file(path, std::ios::binary);
  file << text << '\n';
  Check(static_cast<bool>(file), "whole fixture artifact write failed");
}
std::string Produce(std::string_view name, std::uint64_t sequence,
    std::int32_t days, bool getter_available) {
  Fixture fixture(days, getter_available);
  active = &fixture;
  const std::array<current::ArmyStrengthScope, 1> scope{
      current::ArmyStrengthScope{kUnit, game::ArmyStrengthScopeRole::player, {}}};
  std::vector<game::ArmyStrengthSnapshot> rows;
  const auto result = current::ReadArmyStrengthsForScope12004(fixture.bindings, scope, rows);
  Check(result == game::ReadArmyStrengthsResult::available && rows.size() == 1,
      "fresh .4 whole strength reader did not produce one available row");
  const auto &row = rows.front();
  Check(row.regiment_count == 2 && row.regiment_strengths && row.regiment_strengths->size() == 2 &&
      (*row.regiment_strengths)[0].army_regiment_id == kRegiment &&
      (*row.regiment_strengths)[1].army_regiment_id == kRegiment &&
      row.current_soldiers == 100 && row.maximum_soldiers == 200,
      "whole reader lost duplicate roster occurrences or native totals");
  Check(row.current_disembark_penalty_v1.has_value(), "native current-days leaf omitted");
  const auto &landing = *row.current_disembark_penalty_v1;
  Check(landing.available == getter_available &&
      (getter_available ? landing.remaining_days == days : !landing.remaining_days) &&
      fixture.disembark_calls == static_cast<std::size_t>(getter_available),
      "signed current-days value or demanded callback count changed");
  Check(row.current_supply_raw == 123450000 && row.current_supply_capacity_raw == 200000000 &&
      row.current_supply_change_monthly_raw == -1200000 && row.current_attrition_fraction_raw == 1250,
      "current supply observations changed before serialization");
  std::string frame = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":";
  AppendString(frame, std::string("army-family-") + std::string(name));
  frame += ",\"ok\":true,\"result\":{\"step\":\"query-army-strengths-v1\","
      "\"accepted\":true,\"status\":\"available\",\"query_sequence\":";
  frame += std::to_string(sequence);
  frame += ",\"army_strengths\":[";
  game::AppendArmyStrengthV1(frame, row,
      [](auto value) { return std::to_string(value); }, AppendIds, AppendString);
  frame += "]}}";
  active = nullptr;
  return game::Render12004BuildIdentity(std::move(frame), game::Ck3_12004AdapterDescriptor());
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "usage: xar_ck3_12004_army_family_test <fresh-output-dir>");
    constexpr std::uintptr_t base = 0x140000000ULL;
    const auto native = current::BindArmyImage12004(base, current::kExecutableSha256);
    Check(native.enabled && native.current_disembark_penalty_enabled &&
        reinterpret_cast<std::uintptr_t>(native.get_army_disembark_penalty_days) == base + 0x24AA220,
        "actual .4 Army binder did not select the mapped named current-days leaf");
    Check(!current::BindArmyImage12004(base, ck3_12002::kExecutableSha256).enabled,
        "Army actual .4 binder accepted an old executable identity");
    const auto world = current::BindWorldImage12004(base, current::kExecutableSha256);
    Check(world.enabled && reinterpret_cast<std::uintptr_t>(world.get_war_score) == base + 0x249AC20 &&
        !current::BindWorldImage12004(base, ck3_12002::kExecutableSha256).enabled,
        "actual .4 World binder identity or war score address changed");
    const std::filesystem::path output(argv[1]);
    std::filesystem::create_directories(output);
    const std::array<std::string_view, 4> names{"zero", "negative", "positive", "unavailable"};
    const std::array<std::int32_t, 4> days{0, -1, 34, 0};
    std::string bundle = "{\"schema_version\":1,\"scene_order\":[\"zero\",\"negative\","
        "\"positive\",\"unavailable\"],\"samples\":{";
    for (std::size_t i = 0; i < names.size(); ++i) {
      const auto frame = Produce(names[i], i + 1, days[i], i != 3);
      Write(output / (std::string(names[i]) + ".command-result.json"), frame);
      if (i) bundle += ',';
      AppendString(bundle, names[i]);
      bundle += ':';
      bundle += frame;
    }
    bundle += "}}";
    Write(output / "army-family-12004-whole.json", bundle);
    Write(output / "PRODUCER-PROVENANCE.json",
        "{\"game_version\":\"1.20.0.4\",\"qualification\":\"fixture-only\","
        "\"producer\":\"ReadArmyStrengthsForScope12004 + AppendArmyStrengthV1\","
        "\"native_body_transplant\":false,\"backend_metadata_in_native_result\":false,"
        "\"scenes\":4,\"objects_and_callbacks\":\"synthetic fixture-owned\","
        "\"game_or_native_EXE_execution\":false}");
    std::cout << "four fresh actual4 family whole command-result fixtures emitted\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
