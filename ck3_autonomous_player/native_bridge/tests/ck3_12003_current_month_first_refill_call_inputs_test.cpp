// SOURCE_PREPARED / NOTRUN. Root owns FIRST build and execution.
// New whole production Strength reader/serializer fixture; synthetic storage/getters.
#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
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
#include <vector>

namespace {
using namespace xar;
constexpr std::int32_t kUnit = 67108883, kArmy = 33554443, kRegiment = 100663299;
void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  std::vector<Region> regions;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template <class T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof value);
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> result;
    for (const auto &region : regions)
      result.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return result;
  }
};
struct Registry {
  Memory &memory;
  void *storage, *table;
  Registry(Memory &source, std::int32_t capacity)
      : memory(source), storage(source.Allocate(0x30)),
        table(source.Allocate(static_cast<std::size_t>(capacity) * 16)) {
    memory.Put(storage, 0x20, table); memory.Put(storage, 0x2C, capacity);
  }
  void Add(std::int32_t id, void *object) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    memory.Put(table, static_cast<std::size_t>(index) * 16 + 8, object);
    memory.Put(object, 0x10, id);
  }
};
struct Fixture;
Fixture *active = nullptr;
struct Fixture {
  Memory memory;
  Registry units{memory, 20}, armies{memory, 12}, regiments{memory, 4};
  void *unit = memory.Allocate(0x180), *army = memory.Allocate(0x210);
  void *regiment = memory.Allocate(0x150), *state = memory.Allocate(0xC8);
  void *regiment_ids = memory.Allocate(4);
  ck3_12002::ArmyBindings bindings{};
  static std::int32_t Current(void *receiver, std::uint8_t flags) {
    Check(active && receiver == static_cast<std::byte *>(active->army) + 0x38 && flags == 0,
          "whole current-soldier getter ABI changed");
    return 160;
  }
  static std::int32_t Maximum(void *receiver) {
    Check(active && receiver == active->army, "whole maximum-soldier receiver changed");
    return 240;
  }
  explicit Fixture(std::uint8_t flags) {
    active = this;
    units.Add(kUnit, unit); armies.Add(kArmy, army); regiments.Add(kRegiment, regiment);
    memory.Put(unit, 0x178, kArmy); memory.Put(army, 0x124, kUnit);
    memory.Put(army, 0x14, std::uint32_t{0x41726D79});
    memory.Put(army, 0x38, regiment_ids); memory.Put(army, 0x40, std::int32_t{1});
    memory.Put(army, 0x44, std::int32_t{1}); memory.Put(regiment_ids, 0, kRegiment);
    memory.Put(army, 0x180, std::int64_t{9000000});
    memory.Put(regiment, 0x14, std::uint32_t{0x41725267});
    memory.Put(regiment, 0x38, std::int32_t{160}); memory.Put(regiment, 0x3C, std::int32_t{240});
    memory.Put(regiment, 0x40, std::int64_t{300000});
    memory.Put(state, 8, std::int32_t{1000}); memory.Put(state, 0xC0, flags);
    // Adjacent bytes are deliberately nonzero; the native operand is only a BYTE.
    memory.Put(state, 0xC1, std::uint8_t{255}); memory.Put(state, 0xC2, std::uint8_t{255});
    bindings.enabled = true; bindings.game_state_slot = &state;
    bindings.unit_storage_slot = &units.storage; bindings.internal_army_storage_slot = &armies.storage;
    bindings.regiment_storage_slot = &regiments.storage;
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    bindings.current_month_first_refill_call_bindings.enabled = true;
  }
  game::ArmyStrengthSnapshot Observe() {
    const auto before = memory.Snapshot();
    const std::array<ck3_12002::ArmyStrengthScope, 1> scope{{
        {kUnit, game::ArmyStrengthScopeRole::player, {}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) ==
              game::ReadArmyStrengthsResult::available && rows.size() == 1,
          "month-first family must enter actual whole Strength reader without changing availability");
    const auto &row = rows[0];
    Check(row.available && row.army_id == kUnit && row.native_carmy_id == kArmy &&
              row.current_soldiers == 160 && row.maximum_soldiers == 240 &&
              row.regiment_count == 1 && row.ai_base_power_raw == 300000 &&
              row.current_supply_raw == std::int64_t{9000000}, "original observed scalars changed");
    Check(row.current_month_first_refill_call_inputs_v1.has_value(),
          "production hook must attach family; direct leaf transplant forbidden");
    Check(memory.Snapshot() == before, "readonly capture wrote fixture game memory");
    return row;
  }
};
void Emit(const std::filesystem::path &directory, const char *name,
          const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row, [](auto value) { return std::to_string(value); },
      [](std::string &output, const std::vector<std::int32_t> &values) {
        output += '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
          if (i != 0) output += ',';
          output += std::to_string(values[i]);
        }
        output += ']';
      }, [](std::string &output, std::string_view value) {
        output += '"'; output += value; output += '"';
      });
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  Check(static_cast<bool>(output), "month-first whole wire open failed");
  output << wire << '\n';
  Check(static_cast<bool>(output), "month-first whole wire write failed");
}
void Scenes(const std::filesystem::path &directory) {
  struct Scene { const char *name; std::uint8_t flags; bool expected; };
  constexpr std::array<Scene, 5> scenes{{
      {"01-flags0-skip", 0, false}, {"02-flags1-not-month-first", 1, false},
      {"03-flags2-month-first", 2, true}, {"04-flags3-other-bit-preserved", 3, true},
      {"05-flags255-byte-width", 255, true}}};
  for (const auto &scene : scenes) {
    Fixture fixture(scene.flags);
    const auto row = fixture.Observe();
    const auto &leaf = *row.current_month_first_refill_call_inputs_v1;
    Check(leaf.status == "available" && leaf.ready && !leaf.unavailable_reason &&
              leaf.subject_army_id == kUnit && leaf.subject_carmy_id == kArmy &&
              leaf.game_state_calendar_flags_raw_u8 == scene.flags &&
              leaf.month_first_mask_2_set == scene.expected, "native BYTE/mask2 input differs from sealed literal");
    Emit(directory, scene.name, row);
  }
  Fixture fixture(2); fixture.state = nullptr;
  const auto row = fixture.Observe();
  const auto &leaf = *row.current_month_first_refill_call_inputs_v1;
  Check(leaf.status == "unavailable" && !leaf.ready &&
            leaf.unavailable_reason == "native_month_first_game_state_unavailable" &&
            leaf.subject_army_id == kUnit && leaf.subject_carmy_id == kArmy &&
            !leaf.game_state_calendar_flags_raw_u8 && !leaf.month_first_mask_2_set,
        "unread GameState must retain null, not synthetic flag0");
  Emit(directory, "06-game-state-unavailable", row);
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir", "new FIRST fixture requires --wire-dir PATH");
    const std::filesystem::path directory(argv[2]);
    std::filesystem::create_directories(directory);
    Scenes(directory);
    std::cout << "PASS: six new whole month-first call-input wires; synthetic memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "MONTH-FIRST FIRST RED: " << error.what() << '\n';
    return 1;
  }
}
