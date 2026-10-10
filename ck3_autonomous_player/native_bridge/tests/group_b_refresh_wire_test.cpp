#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_current_daily_assault_loss.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"
#include <bit>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>

namespace {
using namespace xar;
void Check(bool value, const char *reason) { if (!value) throw std::runtime_error(reason); }
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  std::vector<Region> regions;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size); auto *result = data.get();
    regions.push_back({std::move(data), size}); return result;
  }
  template<class T> void Put(void *object, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof value);
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &region : static_cast<Memory *>(context)->regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.data.get());
      if (begin >= base && begin - base <= region.size && size <= region.size - (begin - base)) {
        std::memcpy(output, address, size); return true;
      }
    }
    return false;
  }
};
template<class T> T Load(const void *object, std::size_t offset) {
  T result{}; std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof result); return result;
}
struct Registry {
  Memory &m; void *slot, *fallback, *store, *table;
  explicit Registry(Memory &memory) : m(memory), slot(m.Allocate(8)), fallback(m.Allocate(8)),
      store(m.Allocate(0x30)), table(m.Allocate(2 * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, std::uint32_t{2});
  }
  void Add(std::uint32_t identity, void *object, std::size_t offset) {
    m.Put(table, (identity & 0xFFFFFFU) * 16 + 8, object); m.Put(object, offset, identity);
    m.Put(fallback, 0, object);
  }
};
constexpr std::uint32_t U = 0x91000001U, A = 0xA2000001U, R = 0xAB000001U, S = 0xFE000001U;
constexpr std::uint32_t WRONG_A = 0xB2000001U, WRONG_U = 0xC1000001U;
std::int32_t Current(void *descriptor, std::uint8_t flags) {
  Check(flags == 0, "new group scope must retain flags0");
  return Load<std::int32_t>(descriptor, 0xC);
}
std::uint8_t Excluded(void *) { return 0; }
std::uint8_t Eligible(void *, void *) { return 1; }
bool Skip(void *) { return true; }
bool Replenish(void *, void *) { return true; }
bool Chunk(void *) { return true; }
std::int64_t *Fraction(void *, std::int64_t *out) { *out = 0; return out; }
std::int32_t B(void *province) { return Load<std::int32_t>(province, 0x74C) <= 0 ? 0 : 4; }
std::int32_t Expected(void *siege) {
  void *province = Load<void *>(siege, 0x200);
  return Load<std::uint32_t>(province, 0x85C) != 0x50726F76U || B(province) <= 0 ? 0 : 7;
}
struct Fixture {
  Memory m; Registry units{m}, armies{m}, regiments{m}, sieges{m}, persistent{m};
  ck3_12002::ArmyBindings b{};
  void *unit = m.Allocate(0x180), *army = m.Allocate(0x208), *regiment = m.Allocate(0x150);
  void *province = m.Allocate(0x900), *siege = m.Allocate(0x3DC);
  void *state_slot = m.Allocate(8), *state = m.Allocate(0xA8), *data = m.Allocate(0x2A540 + 0x190);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  game::ArmyCurrentDailyAssaultTableV1 table{};
  Fixture() {
    b.enabled = true; b.current_daily_assault_loss_inputs_enabled = true;
    b.game_state_slot = static_cast<void **>(state_slot);
    b.unit_storage_slot = static_cast<void **>(units.slot);
    b.internal_army_storage_slot = static_cast<void **>(armies.slot);
    b.regiment_storage_slot = static_cast<void **>(regiments.slot);
    b.persistent_regiment_storage_slot = static_cast<void **>(persistent.slot);
    b.get_army_current_soldiers = Current; b.is_army_regiment_loss_writer_skipped = Skip;
    b.can_regiment_replenish = Replenish; b.can_chunk_replenish = Chunk;
    b.get_regiment_monthly_replenishment_fraction = Fraction;
    b.ordered_besieging_refill_bindings.enabled = true;
    b.ordered_besieging_refill_bindings.arrg_fallback_slot = static_cast<void **>(regiments.fallback);
    b.scoped_ordered_refill_bindings.army_fallback_slot = static_cast<void **>(armies.fallback);
    auto &t = b.current_daily_assault_table_bindings;
    t.enabled = true; t.army_registry_slot = armies.slot; t.army_fallback_slot = armies.fallback;
    t.arrg_registry_slot = regiments.slot; t.arrg_fallback_slot = regiments.fallback;
    t.siege_registry_slot = sieges.slot; t.siege_fallback_slot = sieges.fallback;
    t.read_memory = Memory::Read; t.read_context = &m;
    auto &native = b.current_province_besieging_bindings;
    native.enabled = true; native.unit_fallback_slot = static_cast<void **>(units.fallback);
    native.army_fallback_slot = static_cast<void **>(armies.fallback);
    native.province_fallback_slot = static_cast<void **>(m.Allocate(8));
    native.siege_storage_slot = static_cast<void **>(sieges.slot);
    native.army_excluded = Excluded; native.army_province_eligible = Eligible;
    native.besieging_strength = B; native.assault_expected_loss = Expected;
    auto *count = m.Allocate(4), *percentages = m.Allocate(8), *percentage_slot = m.Allocate(8);
    m.Put(count, 0, std::int32_t{1}); m.Put(percentages, 0, std::int64_t{1000000});
    m.Put(percentage_slot, 0, percentages);
    native.casualty_percentage_count = static_cast<const std::int32_t *>(count);
    native.casualty_percentage_table_slot = static_cast<const std::int64_t **>(percentage_slot);
    units.Add(U, unit, 0x10); armies.Add(A, army, 0x10); regiments.Add(R, regiment, 0x10); sieges.Add(S, siege, 8);
    m.Put(unit, 0x20, province); m.Put(unit, 0x178, A); m.Put(army, 0x124, WRONG_U);
    m.Put(regiment, 0x14, std::uint32_t{0x41725267U});
    m.Put(regiment, 0x38, std::int32_t{1}); m.Put(regiment, 0x3C, std::int32_t{1});
    m.Put(province, 0x10, std::int32_t{7}); m.Put(province, 0x85C, std::uint32_t{0x50726F76U});
    m.Put(province, 0x788, S); m.Put(siege, 0x200, province); m.Put(siege, 0x3D8, std::int32_t{1});
    Roster(army, 0x38, {R, R}); Roster(province, 0x740, {U, U});
    Roster(manager, 0x50, {A, WRONG_A}); Roster(manager, 0x30, {});
    m.Put(state_slot, 0, state); m.Put(state, 0xA0, data);
    table.physical_scan_ready = true; table.raw_groups_ready = true;
    game::ArmyDailyAssaultGroupV1 group{};
    group.native_index = 0; group.physical_slot_i64 = 9; group.siege_full_id_u32 = S;
    group.armies.references_ready = true;
    game::ArmyDailyAssaultOccurrenceV1 occurrence{};
    occurrence.native_index = 0; occurrence.raw_full_id_u32 = WRONG_A;
    group.armies.occurrences.push_back(occurrence); table.groups.push_back(group);
  }
  void Roster(void *object, std::size_t offset, std::initializer_list<std::uint32_t> ids) {
    m.Put(object, offset + 8, static_cast<std::int32_t>(ids.size()));
    m.Put(object, offset + 0xC, static_cast<std::int32_t>(ids.size()));
    if (ids.size() == 0) return;
    auto *values = m.Allocate(ids.size() * 4); std::size_t index = 0;
    for (auto identity : ids) m.Put(values, index++ * 4, identity);
    m.Put(object, offset, values);
  }
  game::ArmyCurrentDailyAssaultLossInputsV1 Observe() {
    return ck3_12003::ReadCurrentDailyAssaultLossInputs12003(b, table);
  }
};
void Emit(const std::filesystem::path &directory, const char *name,
          const game::ArmyCurrentDailyAssaultLossInputsV1 &leaf) {
  std::string wire;
  game::AppendArmyCurrentDailyAssaultLossInputsV1(wire, leaf,
    [](auto value) { return std::to_string(value); },
    [](std::string &out, std::string_view text) { out += '"'; out += text; out += '"'; });
  std::ofstream stream(directory / (std::string(name) + ".json"), std::ios::binary);
  stream << wire << '\n'; Check(static_cast<bool>(stream), "new group B wire write failed");
}
}
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "new group B wire fixture requires a new output directory");
    const std::filesystem::path directory(argv[1]); std::filesystem::create_directories(directory);
    { Fixture f; auto leaf = f.Observe(); Check(leaf.ready && leaf.groups.size() == 1, "new group base observation changed");
      const auto &group = leaf.groups[0]; Check(group.native_current_expected_loss == 7, "current native scalar erased");
      Check(group.ordered_besieging_refill_inputs_v1.has_value(), "new group scope not emitted");
      const auto &scope = *group.ordered_besieging_refill_inputs_v1;
      Check(scope.status == "available" && scope.province_id == 7 && scope.refresh_membership_ready,
            "actual group scope missing");
      Check(scope.subject_army_id == std::bit_cast<std::int32_t>(U) &&
            scope.subject_carmy_id == std::bit_cast<std::int32_t>(A), "actual fallback receiver labels lost");
      Check(scope.target_army_regiment_ids == std::vector<std::int32_t>{std::bit_cast<std::int32_t>(R)} &&
            scope.refresh_occurrences.size() == 2, "signed target/manager occurrences lost");
      Check(scope.refresh_occurrences[1].army_used_fallback && scope.refresh_occurrences[0].regiments.size() == 2 &&
            scope.refresh_occurrences[1].regiments.size() == 2, "aliases or fallback occurrence lost");
      Check(scope.target_persistent_ids_complete && scope.persistent_regiments.empty(), "character target consumes no unused physical dependencies");
      Emit(directory, "present-group-scope", leaf); }
    { Fixture f; f.m.Put(f.units.fallback, 0, static_cast<void *>(nullptr)); auto leaf = f.Observe();
      Check(leaf.ready && leaf.groups[0].native_current_expected_loss == 7 &&
            leaf.groups[0].ordered_besieging_refill_inputs_v1->status == "unavailable" &&
            !leaf.groups[0].ordered_besieging_refill_inputs_v1->refresh_membership_ready,
            "unresolved scope must be independent from current budget and remain unknown");
      Emit(directory, "unknown-group-scope", leaf); }
    { Fixture f; f.m.Put(f.province, 0x74C, std::int32_t{0}); auto leaf = f.Observe();
      Check(leaf.ready && leaf.groups[0].besieging_inputs_v1->native_besieging_strength == 0 &&
            leaf.groups[0].ordered_besieging_refill_inputs_v1->target_army_regiment_ids.empty(),
            "empty actual B targets must stay known empty");
      Emit(directory, "empty-group-targets", leaf); }
    { Fixture f; f.m.Put(f.province, 0x85C, std::uint32_t{0}); auto leaf = f.Observe();
      Check(leaf.groups[0].native_current_expected_loss == 0 && !leaf.groups[0].besieging_inputs_v1 &&
            !leaf.groups[0].ordered_besieging_refill_inputs_v1, "invalid Province must not invent scope");
      Emit(directory, "null-group-scope", leaf); }
    std::cout << "new group B producer/DTO/serializer compound GREEN: four wires\n"; return 0;
  } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
