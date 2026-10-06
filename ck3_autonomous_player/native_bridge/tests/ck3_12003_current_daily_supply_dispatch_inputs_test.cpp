// SOURCE_PREPARED/NOTRUN. Root owns the first build and execution.
// Synthetic current-frame bytes enter the actual whole Strength reader and
// production whole-row serializer. This never invokes24E3430/24E4D10.
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
constexpr std::int32_t kUnit = 67108883;
constexpr std::int32_t kArmy = 33554443;
constexpr std::int32_t kRegiment = 100663299;

void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
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
  void *storage;
  void *table;
  Registry(Memory &source, std::int32_t capacity)
      : memory(source), storage(source.Allocate(0x30)),
        table(source.Allocate(static_cast<std::size_t>(capacity) * 16)) {
    memory.Put(storage, 0x20, table);
    memory.Put(storage, 0x2C, capacity);
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
  void *unit = memory.Allocate(0x180);
  void *army = memory.Allocate(0x210);
  void *other_army = memory.Allocate(0x210);
  void *regiment = memory.Allocate(0x150);
  void *regiment_ids = memory.Allocate(4);
  void *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2AA00);
  ck3_12002::ArmyBindings bindings{};
  std::int32_t grace = 30;

  static std::int32_t Current(void *receiver, std::uint8_t flags) {
    Check(active && receiver == static_cast<std::byte *>(active->army) + 0x38 && flags == 0,
          "actual whole Strength current-soldier receiver/flags changed");
    return 160;
  }
  static std::int32_t Maximum(void *receiver) {
    Check(active && receiver == active->army, "actual whole Strength maximum receiver changed");
    return 240;
  }
  Fixture() {
    active = this;
    units.Add(kUnit, unit); armies.Add(kArmy, army); regiments.Add(kRegiment, regiment);
    memory.Put(unit, 0x178, kArmy);
    memory.Put(army, 0x14, std::uint32_t{0x41726D79});
    memory.Put(army, 0x124, kUnit);
    memory.Put(other_army, 0x10, std::int32_t{kArmy + 1});
    memory.Put(army, 0x38, regiment_ids);
    memory.Put(army, 0x40, std::int32_t{1}); memory.Put(army, 0x44, std::int32_t{1});
    memory.Put(regiment_ids, 0, kRegiment);
    memory.Put(army, 0x180, std::int64_t{9000000});
    memory.Put(regiment, 0x14, std::uint32_t{0x41725267});
    memory.Put(regiment, 0x38, std::int32_t{160});
    memory.Put(regiment, 0x3C, std::int32_t{240});
    memory.Put(regiment, 0x40, std::int64_t{300000});
    memory.Put(state, 8, std::int32_t{1000});
    memory.Put(state, 0x9C, std::int32_t{30});
    memory.Put(state, 0xA0, data);
    bindings.enabled = true; bindings.game_state_slot = &state;
    bindings.unit_storage_slot = &units.storage;
    bindings.internal_army_storage_slot = &armies.storage;
    bindings.regiment_storage_slot = &regiments.storage;
    bindings.get_army_current_soldiers = Current;
    bindings.get_army_maximum_soldiers = Maximum;
    bindings.current_daily_supply_dispatch_bindings.enabled = true;
  }

  void Bucket(std::int32_t phase, const std::vector<void *> &pointers,
              std::int32_t capacity) {
    auto *header = static_cast<std::byte *>(data) + 0x2A548 + 0x190 +
                   static_cast<std::size_t>(phase) * 24;
    void *array = pointers.empty() ? nullptr : memory.Allocate(pointers.size() * 8);
    for (std::size_t i = 0; i < pointers.size(); ++i) memory.Put(array, i * 8, pointers[i]);
    memory.Put(header, 0, array);
    memory.Put(header, 8, capacity);
    memory.Put(header, 0xC, static_cast<std::int32_t>(pointers.size()));
  }

  game::ArmyStrengthSnapshot Observe() {
    const auto before = memory.Snapshot();
    const std::array<ck3_12002::ArmyStrengthScope, 1> scope{{
        {kUnit, game::ArmyStrengthScopeRole::player, {}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) ==
              game::ReadArmyStrengthsResult::available && rows.size() == 1,
          "new current dispatcher input must enter actual whole reader");
    const auto &row = rows.front();
    Check(row.available && row.army_id == kUnit && row.native_carmy_id_observable &&
              row.native_carmy_id == kArmy && row.current_soldiers == 160 &&
              row.maximum_soldiers == 240 && row.ai_base_power_raw == 300000 &&
              row.regiment_count == 1 && row.current_supply_raw == std::int64_t{9000000},
          "optional dispatcher observation changed original identity/strength/stored stock");
    Check(row.current_daily_supply_dispatch_inputs_v1.has_value(),
          "production Strength hook must attach family; direct collector/transplant is forbidden");
    const auto &inputs = *row.current_daily_supply_dispatch_inputs_v1;
    Check(inputs.subject_army_id == kUnit && inputs.subject_carmy_id == kArmy,
          "dispatcher inputs must use the actual resolved same-row Unit/CArmy");
    Check(before == memory.Snapshot(), "whole readonly query wrote fixture game-input bytes");
    return row;
  }
};

void Available(const game::ArmyCurrentDailySupplyDispatchInputsV1 &inputs) {
  Check(inputs.status == "available" && inputs.ready && !inputs.unavailable_reason,
        "readable original selected bucket must be independently available");
}

void Emit(const std::filesystem::path &directory, const char *name,
          const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row,
      [](auto value) { return std::to_string(value); },
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
  Check(static_cast<bool>(output), "new whole dispatcher wire open failed");
  output << wire << '\n';
  Check(static_cast<bool>(output), "new whole dispatcher wire write failed");
}

void Scenes(const std::filesystem::path &directory) {
  {
    Fixture fixture;
    // Four actual readable original entries. Native dispatcher never reads
    // capacity; retain2 as independent raw context without adding a policy gate.
    fixture.Bucket(0, {fixture.other_army, fixture.army, fixture.army, fixture.other_army}, 2);
    const auto row = fixture.Observe(); const auto &inputs = *row.current_daily_supply_dispatch_inputs_v1;
    Available(inputs);
    Check(inputs.current_date_raw == 1000 && inputs.native_day_index == 30 &&
              inputs.selected_bucket_phase == 0 && inputs.selected_bucket_count_raw == 4 &&
              inputs.selected_bucket_capacity_raw == 2 && inputs.selected_bucket_data_present == true &&
              inputs.subject_occurrence_indices == std::vector<std::int32_t>{1, 2} &&
              inputs.subject_dispatch_occurrence_count == 2,
          "preserve original duplicate occurrences/gaps/count without capacity-based filtering");
    Emit(directory, "01-original-ordered-subject-occurrences", row);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.state, 8, std::int32_t{0});
    fixture.memory.Put(fixture.state, 0x9C, std::int32_t{-1});
    const auto row = fixture.Observe(); const auto &inputs = *row.current_daily_supply_dispatch_inputs_v1;
    Available(inputs);
    Check(inputs.current_date_raw == 0 && inputs.native_day_index == -1 &&
              inputs.selected_bucket_phase == 15 && inputs.selected_bucket_count_raw == 0 &&
              inputs.selected_bucket_data_present == false &&
              inputs.subject_occurrence_indices == std::vector<std::int32_t>{} &&
              inputs.subject_dispatch_occurrence_count == 0,
          "unsigned native D/valid date0/complete empty bucket must survive whole wire");
    Emit(directory, "02-unsigned-day-empty-selected-bucket", row);
  }
  {
    Fixture fixture;
    fixture.Bucket(0, {fixture.other_army}, 1);
    fixture.Bucket(3, {fixture.army}, 1);
    fixture.bindings.timing_bindings.enabled = true;
    fixture.bindings.timing_bindings.loaded_grace_days = &fixture.grace;
    const auto row = fixture.Observe(); const auto &inputs = *row.current_daily_supply_dispatch_inputs_v1;
    Available(inputs);
    Check(row.army_update_clock_v1 && row.army_update_clock_v1->observed_army_bucket_phase == 3 &&
              inputs.current_date_raw == row.army_update_clock_v1->current_date_raw &&
              inputs.native_day_index == row.army_update_clock_v1->native_day_index &&
              inputs.selected_bucket_phase == 0 && inputs.selected_bucket_count_raw == 1 &&
              inputs.subject_occurrence_indices == std::vector<std::int32_t>{} &&
              inputs.subject_dispatch_occurrence_count == 0,
          "old first-membership phase is not selected-bucket subject multiplicity; reuse same-capture clock");
    Emit(directory, "03-subject-only-in-another-bucket", row);
  }
  {
    Fixture fixture;
    auto *header = static_cast<std::byte *>(fixture.data) + 0x2A548 + 0x190;
    fixture.memory.Put(header, 8, std::int32_t{1});
    fixture.memory.Put(header, 0xC, std::int32_t{1});
    const auto row = fixture.Observe(); const auto &inputs = *row.current_daily_supply_dispatch_inputs_v1;
    Check(inputs.status == "unavailable" && !inputs.ready &&
              inputs.unavailable_reason == "daily_supply_dispatch_bucket_header_invalid" &&
              inputs.current_date_raw == 1000 && inputs.native_day_index == 30 &&
              inputs.selected_bucket_phase == 0 && inputs.selected_bucket_count_raw == 1 &&
              inputs.selected_bucket_data_present == false &&
              !inputs.subject_occurrence_indices && !inputs.subject_dispatch_occurrence_count,
          "missing pointer data must remain partial without converting failure to observed zero");
    Emit(directory, "04-selected-count-with-unavailable-pointer-data", row);
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 3 && std::string_view(argv[1]) == "--wire-dir",
          "usage: current daily supply dispatcher fixture --wire-dir DIRECTORY");
    const std::filesystem::path directory(argv[2]);
    std::filesystem::create_directories(directory);
    Scenes(directory);
    std::cout << "current daily supply dispatcher whole-wire fixture emitted4 rows\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
