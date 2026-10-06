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
#include <vector>

namespace {
using namespace xar;
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Request { const void *address; std::size_t size; };
  struct Denied { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Request> requests;
  std::vector<Denied> denied;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *pointer = bytes.get(); regions.push_back({std::move(bytes), size}); return pointer;
  }
  template <typename T> void Put(void *pointer, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(pointer) + offset, &value, sizeof(value));
  }
  void Deny(const void *pointer, std::size_t offset, std::size_t size) {
    denied.push_back({static_cast<const std::byte *>(pointer) + offset, size});
  }
  std::size_t Reads(const void *pointer, std::size_t offset, std::size_t size) const {
    const auto *address = static_cast<const std::byte *>(pointer) + offset;
    std::size_t total = 0;
    for (const auto &request : requests)
      if (request.address == address && request.size == size) ++total;
    return total;
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    memory.requests.push_back({address, size});
    for (const auto &range : memory.denied)
      if (address == range.address && size == range.size) return false;
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size && size <= region.size - (begin - base)) {
        std::memcpy(output, address, size); return true;
      }
    }
    return false;
  }
};
struct Registry {
  Memory &memory;
  void *slot, *fallback_slot, *store, *table;
  Registry(Memory &m) : memory(m), slot(m.Allocate(8)), fallback_slot(m.Allocate(8)),
      store(m.Allocate(0x30)), table(m.Allocate(2 * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, std::uint32_t{2});
  }
  void Add(std::uint32_t full, void *object, std::size_t full_offset) {
    memory.Put(table, (full & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, full_offset, full);
  }
};
constexpr std::uint32_t kUnit = 0x11000001U, kArmy = 0x22000001U, kReg = 0x2B000001U;
constexpr std::uint32_t kSiege = 0xDD000001U;
void *expected_army = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(receiver == static_cast<std::byte *>(expected_army) + 0x38 && flags == 0,
        "release fixture current getter receiver");
  return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(receiver == expected_army, "release fixture maximum getter receiver"); return 40;
}
struct Fixture {
  Memory memory;
  Registry units{memory}, armies{memory}, arrgs{memory}, sieges{memory};
  ck3_12002::ArmyBindings bindings{};
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *entries = memory.Allocate(3 * 0x40);
  void *record = static_cast<std::byte *>(entries) + 0x40;
  void *unit = memory.Allocate(0x180), *army = memory.Allocate(0x208);
  void *reg = memory.Allocate(0x48), *definition = memory.Allocate(0x2A4);
  void *siege = memory.Allocate(0x10);
  void *army_allocator = memory.Allocate(8), *arrg_allocator = memory.Allocate(8);
  Fixture() {
    bindings.enabled = true; bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    auto &b = bindings.current_daily_assault_table_bindings;
    b.enabled = true; b.game_state_slot = state_slot;
    b.army_registry_slot = armies.slot; b.army_fallback_slot = armies.fallback_slot;
    b.arrg_registry_slot = arrgs.slot; b.arrg_fallback_slot = arrgs.fallback_slot;
    b.siege_registry_slot = sieges.slot; b.siege_fallback_slot = sieges.fallback_slot;
    b.expected_army_allocator = army_allocator; b.expected_arrg_allocator = arrg_allocator;
    b.read_memory = Memory::Read; b.read_context = &memory;
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    memory.Put(manager, 0x178, entries); memory.Put(manager, 0x180, std::int32_t{1});
    memory.Put(manager, 0x184, std::int32_t{1}); memory.Put(manager, 0x188, std::uint8_t{0});
    memory.Put(manager, 0x18C, std::uint32_t{0x3F400000U});
    memory.Put(entries, 2 * 0x40 + 4, std::uint8_t{0xA5});
    std::uint32_t hash = 0x811C9DC5U;
    for (std::uint32_t shift = 0; shift != 32; shift += 8)
      hash = (hash ^ ((kSiege >> shift) & 0xFFU)) * 0x1000193U;
    memory.Put(record, 0, hash); memory.Put(record, 4, std::uint8_t{1}); memory.Put(record, 8, kSiege);
    units.Add(kUnit, unit, 0x10); armies.Add(kArmy, army, 0x10);
    arrgs.Add(kReg, reg, 0x10); sieges.Add(kSiege, siege, 8);
    memory.Put(unit, 0x178, kArmy); memory.Put(army, 0x124, kUnit);
    memory.Put(reg, 0x14, std::uint32_t{0x41725267U}); memory.Put(reg, 0x18, definition);
    memory.Put(definition, 0x2A0, std::int32_t{0});
    memory.Put(reg, 0x38, std::int32_t{20}); memory.Put(reg, 0x3C, std::int32_t{40});
    memory.Put(reg, 0x40, std::int64_t{100000});
    void *ids = memory.Allocate(4); memory.Put(ids, 0, kReg);
    memory.Put(army, 0x38, ids); memory.Put(army, 0x40, std::int32_t{1});
    memory.Put(army, 0x44, std::int32_t{1});
    Header(0x10, nullptr, 0, 17, nullptr); Header(0x28, nullptr, 0, 9, arrg_allocator);
    expected_army = army;
  }
  void Header(std::size_t offset, const void *pointer, std::int32_t count,
              std::int32_t capacity, const void *allocator) {
    memory.Put(record, offset, pointer); memory.Put(record, offset + 8, capacity);
    memory.Put(record, offset + 0xC, count); memory.Put(record, offset + 0x10, allocator);
  }
  std::vector<game::ArmyStrengthSnapshot> Observe() {
    const std::array<ck3_12002::ArmyStrengthScope, 1> scope{{
        {static_cast<std::int32_t>(kUnit), game::ArmyStrengthScopeRole::player, {}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
              rows.size() == 1 && rows[0].available && rows[0].current_soldiers == 20 &&
              rows[0].maximum_soldiers == 40 && rows[0].current_daily_assault_table_v1,
          "release header must preserve actual whole ArmyStrength production reader");
    Check(rows[0].current_daily_assault_table_v1->groups.size() == 1,
          "release header fixture actual group before end marker");
    for (std::size_t offset : {0x10U, 0x28U}) {
      Check(memory.Reads(record, offset, 8) == 1 && memory.Reads(record, offset + 0xC, 4) == 1 &&
                memory.Reads(record, offset + 8, 4) == 1 && memory.Reads(record, offset + 0x10, 8) == 1,
            "raw headers reuse one count/data/allocator and add one capacity capture");
    }
    return rows;
  }
};
const game::ArmyDailyAssaultGroupV1 &Group(const std::vector<game::ArmyStrengthSnapshot> &rows) {
  return rows[0].current_daily_assault_table_v1->groups[0];
}
void Emit(const std::filesystem::path &directory, const char *name,
          const std::vector<game::ArmyStrengthSnapshot> &rows) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, rows[0], [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
          if (i) out += ',';
          out += std::to_string(values[i]);
        }
        out += ']';
      }, [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::ofstream output(directory / (std::string("daily-assault-release-header-") + name + ".json"), std::ios::binary);
  output << wire << '\n'; Check(static_cast<bool>(output), "release header actual whole-strength wire output");
}
void Cases(const std::filesystem::path &directory) {
  {
    Fixture f; void *buffer = f.memory.Allocate(4);
    f.Header(0x28, buffer, 0, 9, f.arrg_allocator);
    const auto rows = f.Observe(); const auto &g = Group(rows);
    Check(g.arrgs.ready && !g.arrgs.data_present && g.arrgs.occurrences.empty() &&
              g.arrgs.release_header_v1->ready && g.arrgs.release_header_v1->data_present == true &&
              g.arrgs.release_header_v1->capacity_raw_i32 == 9 &&
              g.armies.release_header_v1->data_present == false &&
              g.armies.release_header_v1->capacity_raw_i32 == 17 &&
              g.armies.allocator_witness->matches_expected == false,
          "allocated-empty actual buffer and actual null data cannot be inferred from zero count");
    Emit(directory, "zero-count-nonnull", rows);
  }
  {
    Fixture f; void *buffer = f.memory.Allocate(4);
    f.Header(0x28, buffer, -3, -5, f.arrg_allocator);
    const auto rows = f.Observe(); const auto &g = Group(rows);
    Check(!g.arrgs.ready && g.arrgs.release_header_v1->ready &&
              g.arrgs.release_header_v1->count_raw_i32 == -3 &&
              g.arrgs.release_header_v1->capacity_raw_i32 == -5 &&
              g.arrgs.release_header_v1->data_present == true,
          "negative reference count does not hide actual normal-return release operands");
    Emit(directory, "negative-count-nonnull", rows);
  }
  {
    Fixture f; void *reg_ids = f.memory.Allocate(8), *army_ids = f.memory.Allocate(4);
    f.memory.Put(reg_ids, 0, kReg); f.memory.Put(reg_ids, 4, kReg); f.memory.Put(army_ids, 0, kArmy);
    f.Header(0x28, reg_ids, 2, 7, f.arrg_allocator); f.Header(0x10, army_ids, 1, 3, f.army_allocator);
    const auto rows = f.Observe(); const auto &g = Group(rows);
    Check(g.arrgs.ready && g.arrgs.occurrences.size() == 2 && g.armies.occurrences.size() == 1 &&
              g.arrgs.data_identity == g.arrgs.release_header_v1->data_identity &&
              g.arrgs.release_header_v1->capacity_raw_i32 == 7 &&
              g.armies.release_header_v1->capacity_raw_i32 == 3,
          "positive vector shares actual data/count capture and retains duplicate occurrences");
    Emit(directory, "positive-shared-read", rows);
  }
  {
    Fixture f; f.memory.Deny(f.record, 0x30, 4);
    const auto rows = f.Observe(); const auto &g = Group(rows);
    Check(g.arrgs.ready && !g.arrgs.release_header_v1->ready &&
              g.arrgs.release_header_v1->status == "partial" &&
              g.arrgs.release_header_v1->data_present == false &&
              !g.arrgs.release_header_v1->capacity_raw_i32,
          "actual null branch preserves unknown capacity independently of complete legacy references");
    Emit(directory, "null-data-unknown-capacity", rows);
  }
  {
    Fixture f; f.memory.Deny(f.record, 0x28, 8);
    const auto rows = f.Observe(); const auto &g = Group(rows);
    Check(g.arrgs.ready && !g.arrgs.release_header_v1->ready &&
              !g.arrgs.release_header_v1->data_present &&
              g.arrgs.release_header_v1->capacity_raw_i32 == 9,
          "missing zero-count actual data read remains unknown rather than fabricated null");
    Emit(directory, "zero-count-unknown-data", rows);
  }
  {
    Fixture f; void *buffer = f.memory.Allocate(4);
    f.Header(0x28, buffer, 0, 9, f.army_allocator);
    const auto rows = f.Observe(); const auto &g = Group(rows);
    Check(g.arrgs.release_header_v1->ready && g.arrgs.release_header_v1->data_present == true &&
              g.arrgs.allocator_witness->matches_expected == false,
          "actual noncanonical buffer callback receiver is exposed independently of raw header readiness");
    Emit(directory, "nonnull-noncanonical", rows);
  }
}
} // namespace
int main(int argc, char **argv) {
  try {
    const std::filesystem::path directory = argc > 1 ? argv[1] : "daily-assault-release-header-wire";
    std::filesystem::create_directories(directory); Cases(directory);
    std::cout << "new daily assault release header cases passed\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
