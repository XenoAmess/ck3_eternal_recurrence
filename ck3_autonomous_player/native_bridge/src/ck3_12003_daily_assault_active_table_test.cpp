#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
using namespace xar;
void Check(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  const void *game_state_address = nullptr, *game_data_address = nullptr;
  const void *table_entries_address = nullptr;
  std::size_t game_state_reads = 0, game_data_reads = 0, table_entries_reads = 0;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get(); regions.push_back({std::move(bytes), size}); return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void Deny(const void *address, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset, size});
  }
  std::size_t Attempts() const {
    std::size_t total = 0;
    for (const auto &range : denied) total += range.attempts;
    return total;
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context);
    if (size == 8) {
      if (address == m.game_state_address) ++m.game_state_reads;
      if (address == m.game_data_address) ++m.game_data_reads;
      if (address == m.table_entries_address) ++m.table_entries_reads;
    }
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &range : m.denied) {
      if (begin < range.begin + range.size && range.begin < begin + size) {
        ++range.attempts; return false;
      }
    }
    for (const auto &region : m.regions) {
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
  Registry(Memory &m, std::uint32_t capacity)
      : memory(m), slot(m.Allocate(8)), fallback_slot(m.Allocate(8)),
        store(m.Allocate(0x30)), table(m.Allocate(capacity * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, capacity);
  }
  void Add(std::uint32_t full, void *object, std::size_t full_offset) {
    memory.Put(table, (full & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, full_offset, full);
  }
};
void *expected_army_a = nullptr, *expected_army_b = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(flags == 0, "daily assault fixture uses the existing whole-army strength getter");
  if (receiver == static_cast<std::byte *>(expected_army_a) + 0x38) return 150;
  if (receiver == static_cast<std::byte *>(expected_army_b) + 0x38) return 30;
  throw std::runtime_error("daily assault unexpected fake army current receiver");
}
std::int32_t Maximum(void *receiver) {
  if (receiver == expected_army_a) return 250;
  if (receiver == expected_army_b) return 60;
  throw std::runtime_error("daily assault unexpected fake army maximum receiver");
}
constexpr std::uint32_t kUnitA = 0x11000001U, kUnitB = 0x11000002U;
constexpr std::uint32_t kArmyA = 0x22000001U, kArmyB = 0x22000002U;
constexpr std::uint32_t kArmyWrongGeneration = 0x99000002U;
constexpr std::uint32_t kRegA = 0x2B000001U, kRegB = 0x2B000002U;
constexpr std::uint32_t kRegPositive = 0x2B000003U, kRegInvalid = 0xAB000004U;
constexpr std::uint32_t kRegWrongGeneration = 0xCD000002U;
constexpr std::uint32_t kSiegeHigh = 0xFE000002U, kSiegeLow = 0x01000001U, kSiegeTail = 0xFB000003U;
struct Fixture {
  Memory memory;
  Registry units{memory, 3}, armies{memory, 3}, arrgs{memory, 5}, sieges{memory, 4};
  ck3_12002::ArmyBindings bindings{};
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *entries = memory.Allocate(7 * 0x40);
  void *unit_a = memory.Allocate(0x180), *unit_b = memory.Allocate(0x180);
  void *army_a = memory.Allocate(0x208), *army_b = memory.Allocate(0x208);
  void *reg_a = memory.Allocate(0x48), *reg_b = memory.Allocate(0x48);
  void *reg_positive = memory.Allocate(0x48), *reg_invalid = memory.Allocate(0x48);
  void *reg_fallback = memory.Allocate(0x48);
  void *def_a = memory.Allocate(0x2A4), *def_b = memory.Allocate(0x2A4), *def_positive = memory.Allocate(0x2A4);
  void *siege_high = memory.Allocate(0x10), *siege_low = memory.Allocate(0x10), *siege_tail = memory.Allocate(0x10);
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
    b.read_memory = Memory::Read; b.read_context = &memory;
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    memory.game_state_address = state_slot;
    memory.game_data_address = static_cast<std::byte *>(state) + 0xA0;
    memory.table_entries_address = static_cast<std::byte *>(manager) + 0x178;
    memory.Deny(manager, 0, 8); // Inline manager prefix must never be read as a pointer.
    memory.Put(manager, 0x178, entries); memory.Put(manager, 0x180, std::int32_t{3});
    memory.Put(manager, 0x184, std::int32_t{3}); memory.Put(manager, 0x188, std::uint8_t{2});
    memory.Put(manager, 0x18C, std::uint32_t{0x3F400000U}); // Actual0.75f bits.
    units.Add(kUnitA, unit_a, 0x10); units.Add(kUnitB, unit_b, 0x10);
    armies.Add(kArmyA, army_a, 0x10); armies.Add(kArmyB, army_b, 0x10);
    memory.Put(armies.fallback_slot, 0, army_b);
    memory.Put(unit_a, 0x178, kArmyA); memory.Put(unit_b, 0x178, kArmyB);
    memory.Put(army_a, 0x124, kUnitA); memory.Put(army_b, 0x124, kUnitB);
    arrgs.Add(kRegA, reg_a, 0x10); arrgs.Add(kRegB, reg_b, 0x10);
    arrgs.Add(kRegPositive, reg_positive, 0x10); arrgs.Add(kRegInvalid, reg_invalid, 0x10);
    for (void *reg : {reg_a, reg_b, reg_positive, reg_fallback})
      memory.Put(reg, 0x14, std::uint32_t{0x41725267U});
    memory.Put(reg_fallback, 0x10, std::uint32_t{0xFFFFFFFFU});
    memory.Put(arrgs.fallback_slot, 0, reg_fallback);
    memory.Put(reg_a, 0x18, def_a); memory.Put(reg_b, 0x18, def_b);
    memory.Put(reg_positive, 0x18, def_positive);
    memory.Put(def_a, 0x2A0, std::int32_t{0}); memory.Put(def_b, 0x2A0, std::int32_t{-1});
    memory.Put(def_positive, 0x2A0, std::int32_t{1});
    memory.Put(reg_a, 0x38, std::int32_t{100}); memory.Put(reg_a, 0x3C, std::int32_t{150});
    memory.Put(reg_a, 0x40, std::int64_t{100000});
    memory.Put(reg_b, 0x38, std::int32_t{30}); memory.Put(reg_b, 0x3C, std::int32_t{60});
    memory.Put(reg_b, 0x40, std::int64_t{400000});
    memory.Put(reg_positive, 0x38, std::int32_t{50}); memory.Put(reg_positive, 0x3C, std::int32_t{100});
    memory.Put(reg_positive, 0x40, std::int64_t{200000});
    Ids(static_cast<std::byte *>(army_a) + 0x38, {kRegA, kRegPositive});
    Ids(static_cast<std::byte *>(army_b) + 0x38, {kRegB});
    sieges.Add(kSiegeHigh, siege_high, 8); sieges.Add(kSiegeLow, siege_low, 8); sieges.Add(kSiegeTail, siege_tail, 8);
    memory.Put(sieges.fallback_slot, 0, siege_low);
    Group(1, kSiegeHigh, 1, {kArmyA, kArmyA, kArmyWrongGeneration},
          {kRegA, kRegA, kRegPositive, kRegInvalid});
    Group(3, kSiegeLow, 1, {}, {kRegB, kRegWrongGeneration});
    Group(4, kSiegeTail, 2, {}, {}); // Actual displaced tail row, both legal empty lists.
    memory.Put(entries, 6 * 0x40 + 4, std::uint8_t{0xA5}); // Observed end marker, never a group.
    memory.Deny(entries, 6 * 0x40 + 8, 0x38);
    for (std::size_t slot : {0U, 2U, 5U}) {
      memory.Deny(entries, slot * 0x40, 4); memory.Deny(entries, slot * 0x40 + 8, 0x38);
    }
    memory.Deny(reg_positive, 0x38, 4); // Positive type must skip current numeric read.
    memory.Deny(reg_invalid, 0x18, 8); memory.Deny(reg_invalid, 0x38, 4);
    memory.Deny(reg_fallback, 0x18, 8); memory.Deny(reg_fallback, 0x38, 4);
    memory.Deny(entries, 3 * 0x40 + 0x10, 8);
    memory.Deny(entries, 4 * 0x40 + 0x10, 8); memory.Deny(entries, 4 * 0x40 + 0x28, 8);
    expected_army_a = army_a; expected_army_b = army_b;
  }
  void Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    if (ids.size() == 0) return;
    void *values = memory.Allocate(ids.size() * 4);
    std::size_t index = 0; for (auto id : ids) memory.Put(values, index++ * 4, id);
    memory.Put(header, 0, values);
  }
  void Group(std::size_t slot, std::uint32_t siege, std::uint8_t control,
             std::initializer_list<std::uint32_t> army_ids, std::initializer_list<std::uint32_t> reg_ids) {
    std::uint32_t hash = 0x811C9DC5U;
    for (std::uint32_t shift = 0; shift != 32; shift += 8)
      hash = (hash ^ ((siege >> shift) & 0xFFU)) * 0x1000193U;
    auto *record = static_cast<std::byte *>(entries) + slot * 0x40;
    memory.Put(record, 0, hash); memory.Put(record, 4, control); memory.Put(record, 8, siege);
    Ids(record + 0x10, army_ids); Ids(record + 0x28, reg_ids);
  }
  void Empty() {
    memory.Put(manager, 0x180, std::int32_t{0});
    for (std::size_t slot : {1U, 3U, 4U}) memory.Put(entries, slot * 0x40 + 4, std::uint8_t{0});
  }
  std::vector<game::ArmyStrengthSnapshot> Observe() {
    const std::array<ck3_12002::ArmyStrengthScope, 2> scope{{
        {static_cast<std::int32_t>(kUnitA), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kUnitB), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    std::vector<game::ArmyStrengthSnapshot> out;
    const auto result = ck3_12002::ReadArmyStrengthsForScope(bindings, scope, out);
    Check(result == game::ReadArmyStrengthsResult::available && out.size() == 2 &&
              out[0].available && out[1].available && out[0].current_soldiers == 150 &&
              out[0].maximum_soldiers == 250 && out[0].ai_base_power_raw == 300000 &&
              out[1].current_soldiers == 30 && out[1].maximum_soldiers == 60 &&
              out[1].ai_base_power_raw == 400000,
          "daily assault local partial must preserve original whole ArmyStrength values");
    Check(out[0].current_daily_assault_table_v1 && out[1].current_daily_assault_table_v1 &&
              out[0].current_daily_assault_table_v1 == out[1].current_daily_assault_table_v1 &&
              memory.game_state_reads == 1 && memory.game_data_reads == 1 &&
              memory.table_entries_reads == (out[0].current_daily_assault_table_v1->manager_loaded == true ? 1U : 0U),
          "daily assault table must reuse one GameState/GameData capture and inline-manager table sample across rows");
    return out;
  }
};
void Emit(const std::filesystem::path &directory, const char *name,
          const std::vector<game::ArmyStrengthSnapshot> &rows) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, rows[0],
      [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) {
          if (i) out += ','; out += std::to_string(values[i]);
        }
        out += ']';
      },
      [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::ofstream output(directory / (std::string("daily-assault-table-") + name + ".json"), std::ios::binary);
  output << wire << '\n';
  Check(static_cast<bool>(output), "daily assault production whole-strength wire write failed");
}
void ExactBinding() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = ck3_12003::BindCurrentDailyAssaultTable12003(base, ck3_12003::kExecutableSha256);
  const auto address = [base](std::uintptr_t rva) { return reinterpret_cast<const void *>(base + rva); };
  Check(b.enabled && b.game_state_slot == address(0x5C68C50) &&
            b.siege_registry_slot == address(0x5D1EC88) && b.siege_fallback_slot == address(0x5D1EC60) &&
            b.army_registry_slot == address(0x5D1DE48) && b.army_fallback_slot == address(0x5D1DE50) &&
            b.arrg_registry_slot == address(0x5D1F340) && b.arrg_fallback_slot == address(0x5D1F338),
        "daily assault exact frozen registry bindings differ");
  Check(!ck3_12003::BindCurrentDailyAssaultTable12003(base, "wrong-build").enabled &&
            !ck3_12002::BindArmyImage(base, ck3_12002::kExecutableSha256).current_daily_assault_table_bindings.enabled,
        "daily assault must remain absent from wrong-build and unchanged .2 binders");
}
void Cases(const std::filesystem::path &directory) {
  ExactBinding();
  {
    Fixture f; f.Empty();
    const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(table.ready && table.raw_groups_ready && table.physical_scan_ready && table.groups.empty() &&
              table.header.occupied_count_raw_i32 == 0 && table.header.end_slot_raw_i32 == 6 &&
              table.header.end_marker_control_raw_u8 == 0xA5 && table.physical_controls.size() == 6 &&
              f.memory.Attempts() == 0, "daily assault current empty must retain actual physical header/marker");
    Emit(directory, "current-empty", rows);
  }
  {
    Fixture f; const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(table.ready && table.raw_groups_ready && table.physical_scan_ready && table.groups.size() == 3 &&
              table.observed_occupied_group_count == 3 && table.groups[0].physical_slot_i64 == 1 &&
              table.groups[1].physical_slot_i64 == 3 && table.groups[2].physical_slot_i64 == 4 &&
              table.groups[0].siege_full_id_u32 == kSiegeHigh && table.groups[1].siege_full_id_u32 == kSiegeLow &&
              table.groups[2].siege_full_id_u32 == kSiegeTail && f.memory.Attempts() == 0,
          "daily assault physical order/tail and exact end must survive without sorting or marker group");
    const auto &group = table.groups[0];
    Check(group.armies.occurrences.size() == 3 &&
              group.armies.occurrences[0].raw_full_id_u32 == group.armies.occurrences[1].raw_full_id_u32 &&
              group.armies.occurrences[2].resolution.indexed_full_id_u32 == kArmyB &&
              group.armies.occurrences[2].resolution.selection == "native_fallback" &&
              group.armies.occurrences[2].resolution.selected_full_id_u32 == kArmyB &&
              group.arrgs.occurrences.size() == 4 && group.denominator_ready &&
              group.arrgs.occurrences[0].current_raw_i32 == 100 && group.arrgs.occurrences[1].current_raw_i32 == 100 &&
              group.arrgs.occurrences[2].denominator_included == false && !group.arrgs.occurrences[2].current_raw_i32 &&
              group.arrgs.occurrences[3].identity_valid == false &&
              table.groups[1].arrgs.occurrences[1].resolution.selection == "native_fallback" &&
              table.groups[1].arrgs.occurrences[1].resolution.selected_full_id_u32 == 0xFFFFFFFFU &&
              table.groups[1].arrgs.occurrences[1].denominator_included == false &&
              table.groups[2].armies.ready && table.groups[2].arrgs.ready &&
              table.groups[2].armies.occurrences.empty() && table.groups[2].arrgs.occurrences.empty(),
          "daily assault duplicates/full generation/fallback/knownskip/empty families differ");
    Emit(directory, "current-nonempty", rows);
  }
  {
    Fixture f; f.memory.Deny(f.entries, 0x40 + 0x10, 8);
    const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(!table.ready && !table.raw_groups_ready && table.physical_scan_ready && table.groups.size() == 3 &&
              !table.groups[0].armies.ready && table.groups[0].arrgs.ready && table.groups[0].denominator_ready &&
              table.groups[1].ready && table.groups[2].ready && f.memory.Attempts() == 1,
          "daily assault missing Army vector data must preserve independent complete ArRg denominator and groups");
    Emit(directory, "partial-army-vector", rows);
  }
  {
    Fixture f; f.memory.Deny(f.reg_a, 0x38, 4);
    const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(!table.ready && table.raw_groups_ready && table.groups.size() == 3 &&
              !table.groups[0].arrgs.ready && !table.groups[0].denominator_ready &&
              table.groups[0].arrgs.references_ready && table.groups[0].armies.ready &&
              table.groups[1].denominator_ready && f.memory.Attempts() == 2,
          "daily assault demanded ArRg current failure must retain full ordered references and other group values");
    Emit(directory, "partial-arrg-current", rows);
  }
  {
    Fixture f; f.memory.Deny(f.entries, 3 * 0x40 + 4, 1);
    const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(!table.ready && !table.raw_groups_ready && !table.physical_scan_ready &&
              table.header.occupied_count_raw_i32 == 3 && table.observed_occupied_group_count == 1 &&
              table.groups[0].ready && table.groups[0].denominator_ready &&
              !table.physical_controls.back().control_raw_u8 && f.memory.Attempts() == 1,
          "daily assault failed control must preserve actual complete prefix without rewriting raw count");
    Emit(directory, "partial-control", rows);
  }
  {
    Fixture f; f.memory.Put(f.entries, 6 * 0x40 + 4, std::uint8_t{0});
    const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(!table.ready && !table.physical_scan_ready && table.header.end_marker_control_raw_u8 == 0 &&
              table.groups.size() == 3 && table.groups[0].denominator_ready && f.memory.Attempts() == 0,
          "daily assault actual zero end control cannot become an invented nonzero marker or marker group");
    Emit(directory, "end-marker-zero", rows);
  }
  {
    Fixture f; f.Empty(); f.memory.Deny(f.manager, 0x184, 4);
    const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(table.ready && table.raw_groups_ready && !table.header.ready && !table.physical_scan_ready &&
              table.header.occupied_count_raw_i32 == 0 && !table.header.mask_raw_i32 &&
              !table.header.end_marker_control_raw_u8 && table.groups.empty() && f.memory.Attempts() == 1,
          "daily assault actual current zero must remain usable when undemanded physical placement metadata is missing");
    Emit(directory, "current-empty-missing-mask", rows);
  }
  {
    Fixture f; f.memory.Put(f.state, 0xA0, static_cast<void *>(nullptr));
    const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(!table.ready && !table.manager_loaded && !table.manager_identity &&
              table.unavailable_reason == "daily_assault_game_data_unavailable" &&
              !table.header.occupied_count_raw_i32 && table.groups.empty() && f.memory.Attempts() == 0,
          "daily assault missing GameData leaves inline manager unavailable without fabricating a zero table");
    Emit(directory, "manager-unavailable", rows);
  }
  {
    Fixture f; f.memory.Put(f.entries, 0x40 + 0x34, std::int32_t{-1});
    f.memory.Deny(f.entries, 0x40 + 0x28, 8);
    const auto rows = f.Observe(); const auto &table = *rows[0].current_daily_assault_table_v1;
    Check(!table.ready && !table.raw_groups_ready && table.groups[0].arrgs.count_raw_i32 == -1 &&
              !table.groups[0].arrgs.references_ready && !table.groups[0].denominator_ready &&
              !table.groups[0].arrgs.data_present && table.groups[1].denominator_ready && f.memory.Attempts() == 0,
          "daily assault negative vector extent must not be known empty or demand unused data");
    Emit(directory, "negative-arrg-count", rows);
  }
}
} // namespace
int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  Cases(directory);
  std::cout << "current daily assault active table fixture GREEN\n";
  return 0;
}
