#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar;
void Check(bool value, const char *reason) { if (!value) throw std::runtime_error(reason); }
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Event { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Event> events, denied;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    auto *address = bytes.get(); regions.push_back({std::move(bytes), size}); return address;
  }
  template <typename T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
  }
  void Deny(const void *object, std::size_t offset, std::size_t size) {
    denied.push_back({static_cast<const std::byte *>(object) + offset, size});
  }
  std::size_t Reads(const void *object, std::size_t offset, std::size_t size) const {
    const auto *address = static_cast<const std::byte *>(object) + offset;
    std::size_t count = 0;
    for (const auto &event : events) if (event.address == address && event.size == size) ++count;
    return count;
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> out;
    for (const auto &region : regions) out.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return out;
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); m.events.push_back({address, size});
    const auto start = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &denied : m.denied) {
      const auto denied_start = reinterpret_cast<std::uintptr_t>(denied.address);
      if (start < denied_start + denied.size && denied_start < start + size) return false;
    }
    for (const auto &region : m.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (start >= base && start - base <= region.size && size <= region.size - (start - base)) {
        std::memcpy(output, address, size); return true;
      }
    }
    return false;
  }
};
struct Registry {
  Memory &m;
  void *slot, *fallback_slot, *store, *table;
  Registry(Memory &memory, std::uint32_t capacity) : m(memory), slot(m.Allocate(8)),
      fallback_slot(m.Allocate(8)), store(m.Allocate(0x30)), table(m.Allocate(capacity * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, capacity);
  }
  void Add(std::uint32_t id, void *object, std::size_t full_offset) {
    m.Put(table, (id & 0xFFFFFFU) * 16 + 8, object); m.Put(object, full_offset, id);
  }
};
std::int32_t Current(void *, std::uint8_t flags) { Check(flags == 0, "existing whole-strength flags zero"); return 0; }
std::int32_t Maximum(void *) { return 0; }
constexpr std::uint32_t kArmyA = 0x02000001U, kStale = 0xFE000002U;
struct Fixture {
  Memory m;
  Registry units{m, 3}, armies{m, 7}, combat{m, 3}, regiments{m, 1};
  void *state_slot = m.Allocate(8), *state = m.Allocate(0xB0), *data = m.Allocate(0x2AA00);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *unit = m.Allocate(0x180), *army_a = m.Allocate(0x210), *fallback = m.Allocate(0x210);
  void *valid_army = m.Allocate(0x210), *empty_army = m.Allocate(0x210), *later_army = m.Allocate(0x210);
  void *valid_combat = m.Allocate(0x10), *invalid_combat = m.Allocate(0x10);
  void *source_ids = m.Allocate(6 * 4), *initial_ids = m.Allocate(2 * 4);
  void *dates_a = m.Allocate(3 * 8), *dates_fallback = m.Allocate(8), *dates_later = m.Allocate(8);
  void *later = m.Allocate(4), *due = m.Allocate(4), *before = m.Allocate(4);
  std::int32_t grace_days = 0;
  ck3_12002::ArmyBindings bindings{};
  Fixture() {
    const std::int32_t current = std::numeric_limits<std::int32_t>::max() - 7;
    const auto tomorrow = ck3_12003::PreDateTomorrowLow12003(current);
    Check(tomorrow == std::numeric_limits<std::int32_t>::min() + 16, "native signed tomorrow wrap");
    m.Put(state_slot, 0, state); m.Put(state, 0x08, current); m.Put(state, 0xA0, data);
    units.Add(0x01000001U, unit, 0x10); m.Put(unit, 0x178, kArmyA);
    armies.Add(kArmyA, army_a, 0x10); armies.Add(0x02000002U, fallback, 0x10);
    armies.Add(0x02000003U, valid_army, 0x10); armies.Add(0x02000004U, empty_army, 0x10);
    armies.Add(0x02000005U, later_army, 0x10); m.Put(armies.fallback_slot, 0, fallback);
    for (void *army : {army_a, fallback, valid_army, empty_army, later_army}) {
      m.Put(army, 0x14, 0x41726D79U); m.Put(army, 0x128, 0xFFFFFFFFU);
    }
    m.Put(army_a, 0x124, 0x01000001U);
    combat.Add(0x33000001U, valid_combat, 0x08); m.Put(valid_combat, 0x0C, 0x436F6D62U);
    m.Put(combat.fallback_slot, 0, invalid_combat); m.Put(invalid_combat, 0x08, 0xFFFFFFFFU);
    m.Put(invalid_combat, 0x0C, 0x436F6D62U); m.Put(valid_army, 0x128, 0x33000001U);
    const std::array<std::uint32_t, 6> ids{kArmyA, kArmyA, kStale, 0x02000003U, 0x02000004U, 0x02000005U};
    for (std::size_t i = 0; i < ids.size(); ++i) m.Put(source_ids, i * 4, ids[i]);
    m.Put(initial_ids, 0, 7U); m.Put(initial_ids, 4, 7U);
    m.Put(manager, 0xC8, source_ids); m.Put(manager, 0xD4, 6);
    m.Put(manager, 0x158, initial_ids); m.Put(manager, 0x164, 2);
    m.Put(later, 0, tomorrow + 1); m.Put(due, 0, tomorrow);
    m.Put(before, 0, std::numeric_limits<std::int32_t>::min());
    m.Put(dates_a, 0, later); m.Put(dates_a, 8, due);
    m.Put(army_a, 0x50, dates_a); m.Put(army_a, 0x5C, 3);
    m.Put(dates_fallback, 0, before); m.Put(fallback, 0x50, dates_fallback); m.Put(fallback, 0x5C, 1);
    m.Put(empty_army, 0x5C, -2);
    m.Put(dates_later, 0, later); m.Put(later_army, 0x50, dates_later); m.Put(later_army, 0x5C, 1);
    // These reads would be wrong: old tail after first match, dates during
    // valid Combat, and a pointer array for a nonpositive signed date count.
    m.Deny(dates_a, 16, 8); m.Deny(valid_army, 0x50, 16); m.Deny(empty_army, 0x50, 8);
    bindings.enabled = true; bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(regiments.slot);
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    bindings.timing_bindings = {true, &grace_days};
    bindings.monthly_daily_queue_bindings = {true, static_cast<void **>(armies.fallback_slot)};
    bindings.monthly_first_removal_cleanup_inputs_enabled = true;
    auto &b = bindings.current_pre_date_dated_append_bindings;
    b.common.enabled = true; b.common.game_state_slot = state_slot;
    b.common.army_registry_slot = armies.slot; b.common.army_fallback_slot = armies.fallback_slot;
    b.combat_registry_slot = combat.slot; b.combat_fallback_slot = combat.fallback_slot;
    b.common.read_memory = Memory::Read; b.common.read_context = &m;
  }
  game::ArmyStrengthSnapshot Read() {
    const std::array<ck3_12002::ArmyStrengthScope, 2> scope{{
      {0x01000001, game::ArmyStrengthScopeRole::player, {}},
      {0x01000001, game::ArmyStrengthScopeRole::player, {}}}};
    const auto memory_before = m.Snapshot();
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available,
          "dated partial must preserve available parent Strength");
    Check(m.Snapshot() == memory_before, "observer performed a memory write");
    Check(rows.size() == 2 && rows[0].current_pre_date_dated_append_inputs_v1 ==
          rows[1].current_pre_date_dated_append_inputs_v1, "global value shared across scope rows");
    return rows[0];
  }
};
void Emit(const std::filesystem::path &directory, const char *label, const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row, [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) { if (i) out += ','; out += std::to_string(values[i]); }
        out += ']';
      }, [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::filesystem::create_directories(directory);
  std::ofstream file(directory / (std::string(label) + ".json"), std::ios::binary);
  Check(static_cast<bool>(file), "fixture wire output"); file << wire << '\n';
}
void Cases(const std::filesystem::path &directory) {
  Fixture f;
  auto row = f.Read(); const auto &p = *row.current_pre_date_dated_append_inputs_v1;
  Check(p.ready && p.clock_ready && p.clock_source == "same_query_army_update_clock_v1" &&
        p.tomorrow_date_low_i32 == std::numeric_limits<std::int32_t>::min() + 16,
        "same query existing native clock source and signed wrapping tomorrow");
  Check(p.source_c8.source == "same_query_first_removal_id_list" && p.initial_158.ready,
        "same query global ID lists reused");
  Check(p.occurrences.size() == 6 && p.occurrences[0].date_entries.size() == 2 &&
        p.occurrences[1].date_entries.size() == 2 && p.occurrences[2].original_request_full_id_u32 == kStale &&
        p.occurrences[2].army_resolution.selected_full_id_u32 == 0x02000002U &&
        p.occurrences[2].army_resolution.used_fallback == true,
        "first match stops scan; duplicates and original fallback request retained");
  Check(p.occurrences[3].ready && p.occurrences[3].date_entries.empty() &&
        !p.occurrences[3].army_date_count_5c_raw_i32 && p.occurrences[4].ready &&
        p.occurrences[4].army_date_count_5c_raw_i32 == -2 && p.occurrences[5].date_scan_ready,
        "valid Combat and signed nonpositive count skip without date reads; all-later complete");
  Check(f.m.Reads(f.source_ids, 0, 4) == 0 && f.m.Reads(f.initial_ids, 0, 4) == 0 &&
        f.m.Reads(f.state, 0x08, 4) == 0 && f.m.Reads(f.dates_a, 16, 8) == 0 &&
        f.m.Reads(f.valid_army, 0x5C, 4) == 0 && f.m.Reads(f.empty_army, 0x50, 8) == 0,
        "new collector does not duplicate list/clock reads or skipped operand reads");
  Emit(directory, "nonempty-wrap-duplicates-fallback", row);
  f.m.Put(f.manager, 0x158, static_cast<void *>(nullptr));
  row = f.Read();
  Check(row.current_pre_date_dated_append_inputs_v1->ready &&
        !row.current_pre_date_dated_append_inputs_v1->initial_158.ready,
        "initial destination unavailable keeps complete append requests");
  Emit(directory, "independent-initial158-unavailable", row);
  f.m.Put(f.manager, 0x158, f.initial_ids);
  f.m.Deny(f.due, 0, 4); row = f.Read();
  Check(!row.current_pre_date_dated_append_inputs_v1->ready &&
        !row.current_pre_date_dated_append_inputs_v1->occurrences[0].ready &&
        row.current_pre_date_dated_append_inputs_v1->occurrences[2].ready,
        "required entry read failure preserves independent later fallback decision");
  Emit(directory, "required-date-read-partial", row);
  f.bindings.timing_bindings.enabled = false; f.m.Deny(f.state, 0x08, 4); row = f.Read();
  const auto &missing = *row.current_pre_date_dated_append_inputs_v1;
  Check(!missing.clock_ready && !missing.ready && missing.occurrences[3].ready && missing.occurrences[4].ready,
        "clock unavailable leaves no-date-demand branches independently ready");
  Emit(directory, "clock-unavailable-independent-skips", row);
  f.m.Put(f.manager, 0xD4, -3); row = f.Read();
  Check(row.current_pre_date_dated_append_inputs_v1->ready &&
        !row.current_pre_date_dated_append_inputs_v1->clock_ready &&
        row.current_pre_date_dated_append_inputs_v1->occurrences.empty(),
        "signed nonpositive source count returns independently of unavailable clock");
  Emit(directory, "nonpositive-source-independent-clock", row);
  Check(ck3_12003::BindPreDateDatedAppend12003(0x140000000ULL, ck3_12003::kExecutableSha256).common.enabled &&
        !ck3_12003::BindPreDateDatedAppend12003(0x140000000ULL, ck3_12002::kExecutableSha256).common.enabled,
        "exact .3 binder only");
}
} // namespace
int main(int argc, char **argv) {
  try {
    const auto directory = argc > 1 ? std::filesystem::path(argv[1]) :
        std::filesystem::current_path() / "pre-date-dated-append-new-cases";
    Cases(directory); std::cout << "pre-date dated append new fixture GREEN\n"; return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
