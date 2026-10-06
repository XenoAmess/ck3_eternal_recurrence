#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_post_admission_refresh.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar;
void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  struct Event { const void *address; std::size_t size; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  std::vector<Event> events;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size); void *address = bytes.get();
    regions.push_back({std::move(bytes), size}); return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void Deny(const void *object, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(object) + offset, size});
  }
  std::size_t Reads(const void *object, std::size_t offset, std::size_t size) const {
    const auto *address = static_cast<const std::byte *>(object) + offset; std::size_t result = 0;
    for (const auto &event : events) if (event.address == address && event.size == size) ++result;
    return result;
  }
  std::size_t Attempts() const {
    std::size_t result = 0; for (const auto &row : denied) result += row.attempts; return result;
  }
  std::vector<std::vector<std::byte>> Snapshot() const {
    std::vector<std::vector<std::byte>> result;
    for (const auto &region : regions) result.emplace_back(region.bytes.get(), region.bytes.get() + region.size);
    return result;
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context); const auto begin = reinterpret_cast<std::uintptr_t>(address);
    m.events.push_back({address, size});
    for (auto &range : m.denied)
      if (begin < range.begin + range.size && range.begin < begin + size) { ++range.attempts; return false; }
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
  Memory &memory; void *slot, *fallback_slot, *store, *table;
  Registry(Memory &m, std::uint32_t capacity)
      : memory(m), slot(m.Allocate(8)), fallback_slot(m.Allocate(8)),
        store(m.Allocate(0x30)), table(m.Allocate(static_cast<std::size_t>(capacity) * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, capacity);
  }
  void Add(std::uint32_t full, void *object) {
    memory.Put(table, static_cast<std::size_t>(full & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, 0x10, full);
  }
};
constexpr std::uint32_t kArmy = 0x22000001U, kScopeArmy = 0x22000002U, kFallbackArmy = 0x22000003U;
constexpr std::uint32_t kUnit = 0x11000001U, kScopeUnit = 0x11000002U;
constexpr std::uint32_t kA = 0x2B000001U, kB = 0x2B000002U, kScopeArRg = 0x2B000003U;
constexpr std::uint32_t kFallbackArRg = 0x2B000004U, kWrongGeneration = 0x3C000001U;
constexpr std::uint32_t kInvalid = 0xFFFFFFFFU, kArRgMagic = 0x41725267U;
void *expected_scope_army = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(flags == 0 && receiver == static_cast<std::byte *>(expected_scope_army) + 0x38,
        "refresh fixture whole-current getter receiver/flags changed"); return 160;
}
std::int32_t Maximum(void *receiver) {
  Check(receiver == expected_scope_army, "refresh fixture whole-maximum getter receiver changed"); return 240;
}
struct Fixture {
  Memory memory;
  Registry armies{memory, 4}, units{memory, 3}, arrgs{memory, 5};
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x190), *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *army = memory.Allocate(0x210), *scope_army = memory.Allocate(0x210), *fallback_army = memory.Allocate(0x210);
  void *unit = memory.Allocate(0x180), *scope_unit = memory.Allocate(0x180);
  void *a = memory.Allocate(0x150), *b = memory.Allocate(0x150);
  void *scope_arrg = memory.Allocate(0x150), *fallback_arrg = memory.Allocate(0x150);
  ck3_12002::ArmyBindings bindings{};
  Fixture() {
    armies.Add(kArmy, army); armies.Add(kScopeArmy, scope_army);
    memory.Put(fallback_army, 0x10, kFallbackArmy); memory.Put(armies.fallback_slot, 0, fallback_army);
    units.Add(kUnit, unit); units.Add(kScopeUnit, scope_unit);
    memory.Put(unit, 0x18, std::uint32_t{1}); // Actual standalone admission returns false before ArRg capture.
    memory.Put(scope_unit, 0x178, kScopeArmy);
    memory.Put(army, 0x124, kUnit); memory.Put(fallback_army, 0x124, kUnit);
    memory.Put(scope_army, 0x124, kScopeUnit);
    arrgs.Add(kA, a); arrgs.Add(kB, b); arrgs.Add(kScopeArRg, scope_arrg);
    memory.Put(a, 0x14, kArRgMagic); memory.Put(b, 0x14, kArRgMagic);
    memory.Put(scope_arrg, 0x14, kArRgMagic); memory.Put(scope_arrg, 0x38, std::int32_t{160});
    memory.Put(scope_arrg, 0x3C, std::int32_t{240}); memory.Put(scope_arrg, 0x40, std::int64_t{300000});
    memory.Put(fallback_arrg, 0x10, kFallbackArRg); memory.Put(fallback_arrg, 0x14, kArRgMagic);
    memory.Put(arrgs.fallback_slot, 0, fallback_arrg);
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    Ids(static_cast<std::byte *>(manager) + 0x50, {kArmy, kArmy});
    Ids(static_cast<std::byte *>(manager) + 0x68, {});
    Ids(static_cast<std::byte *>(army) + 0x38, {kA});
    Ids(static_cast<std::byte *>(scope_army) + 0x38, {kScopeArRg});
    Ids(static_cast<std::byte *>(fallback_army) + 0x38, {kWrongGeneration});
    memory.Put(army, 0x24, std::int32_t{777}); memory.Put(army, 0x28, std::int64_t{-888});
    memory.Put(army, 0x20, std::uint8_t{1}); memory.Put(army, 0x21, std::uint8_t{2});
    memory.Put(army, 0x30, std::uint8_t{3}); memory.Put(army, 0x31, std::uint8_t{4});
    bindings.enabled = true; bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    auto &refresh = bindings.current_post_admission_refresh_bindings;
    refresh.common.enabled = true; refresh.common.game_state_slot = state_slot;
    refresh.common.army_registry_slot = armies.slot; refresh.common.army_fallback_slot = armies.fallback_slot;
    refresh.common.unit_registry_slot = units.slot; refresh.common.unit_fallback_slot = units.fallback_slot;
    refresh.common.read_memory = Memory::Read; refresh.common.read_context = &memory;
    refresh.arrg_registry_slot = arrgs.slot; refresh.arrg_fallback_slot = arrgs.fallback_slot;
    bindings.current_daily_assault_roster_admission_bindings = refresh.common;
    expected_scope_army = scope_army;
  }
  void *Ids(void *header, std::initializer_list<std::uint32_t> ids) {
    memory.Put(header, 8, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0xC, static_cast<std::int32_t>(ids.size()));
    memory.Put(header, 0, static_cast<const void *>(nullptr));
    if (ids.size() == 0) return nullptr;
    void *values = memory.Allocate(ids.size() * 4); std::size_t index = 0;
    for (auto id : ids) memory.Put(values, index++ * 4, id);
    memory.Put(header, 0, values); return values;
  }
  std::vector<game::ArmyStrengthSnapshot> Observe() {
    const auto before = memory.Snapshot();
    const std::array<ck3_12002::ArmyStrengthScope, 2> scope{{
        {static_cast<std::int32_t>(kScopeUnit), game::ArmyStrengthScopeRole::player, {}},
        {static_cast<std::int32_t>(kScopeUnit), game::ArmyStrengthScopeRole::active_war_ally, {7}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
              rows.size() == 2, "refresh optional input leaf changed whole-strength query availability");
    for (const auto &row : rows) {
      Check(row.available && row.current_soldiers == 160 && row.maximum_soldiers == 240 &&
                row.ai_base_power_raw == 300000 && row.regiment_count == 1,
            "refresh optional input leaf changed existing strength values");
      Check(row.current_daily_assault_roster_admission_v1 && row.current_post_admission_refresh_inputs_v1,
            "refresh fixture requires actual production query roster/refresh hooks");
      const auto &leaf = *row.current_post_admission_refresh_inputs_v1;
      Check(!leaf.actual_refresh_execution_ready && !leaf.actual_next_occurrence_ready && !leaf.full_callback_ready &&
                !leaf.full_daily_assault_ready && !leaf.full_monthly_ready,
            "refresh raw input observation must not claim executor/later occurrence/full callback readiness");
    }
    Check(rows[0].current_post_admission_refresh_inputs_v1 == rows[1].current_post_admission_refresh_inputs_v1,
          "refresh input leaf must be captured once and reused on both requested scope rows");
    Check(memory.Reads(manager, 0x5C, 4) == 1, "refresh collector must reuse original primary roster count");
    Check(before == memory.Snapshot(), "refresh observer must not write native caches or input vectors");
    return rows;
  }
};
const game::ArmyCurrentPostAdmissionRefreshInputsV1 &Leaf(const std::vector<game::ArmyStrengthSnapshot> &rows) {
  return *rows[0].current_post_admission_refresh_inputs_v1;
}
void Emit(const std::filesystem::path &directory, const char *name,
    const std::vector<game::ArmyStrengthSnapshot> &rows) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, rows[0], [](auto value) { return std::to_string(value); },
      [](std::string &out, const std::vector<std::int32_t> &values) {
        out += '[';
        for (std::size_t i = 0; i < values.size(); ++i) { if (i) out += ','; out += std::to_string(values[i]); }
        out += ']';
      }, [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::ofstream output(directory / (std::string("post-admission-refresh-") + name + ".json"), std::ios::binary);
  output << wire << '\n'; Check(static_cast<bool>(output), "refresh production whole-strength wire write failed");
}
void Ready(const game::ArmyCurrentPostAdmissionRefreshInputsV1 &leaf) {
  Check(leaf.ready && leaf.source_operands_ready && leaf.numeric_24_inputs_ready && leaf.numeric_28_inputs_ready &&
            leaf.status == "available" && leaf.unavailable_reason.empty(), "refresh complete source operands marked partial");
}
void SupplementalReuseAndRejectedMetadata() {
  Fixture f;
  auto &binding = f.bindings.current_post_admission_refresh_bindings;
  const auto army_selected = ck3_12003::daily_assault_roster_detail::Resolve(binding.common,
      f.armies.slot, f.armies.fallback_slot, kArmy, 0x10);
  game::ArmyCurrentDailyAssaultRosterAdmissionV1 roster{};
  roster.original_roster = ck3_12003::daily_assault_roster_detail::References(binding.common,
      static_cast<std::byte *>(f.manager) + 0x50);
  game::ArmyCurrentPreDatePendingUpdateInputsV1 pending{};
  for (const auto &raw : roster.original_roster.occurrences) {
    game::ArmyPreDatePendingOccurrenceV1 row{}; row.native_index = raw.native_index; row.raw_full_id_u32 = raw.raw_full_id_u32;
    row.original_army_resolution = army_selected.observation;
    row.original_arrg_references = ck3_12003::daily_assault_roster_detail::References(binding.common,
        static_cast<std::byte *>(f.army) + 0x38);
    game::ArmyPreDatePendingArRgV1 arrg{}; arrg.native_index = 0; arrg.raw_full_id_u32 = kA;
    arrg.arrg_resolution = ck3_12003::daily_assault_roster_detail::Resolve(binding.common,
        f.arrgs.slot, f.arrgs.fallback_slot, kA, 0x10).observation;
    arrg.current_38_raw_i32 = ck3_12003::daily_assault_roster_detail::Read<std::int32_t>(binding.common, f.a, 0x38);
    row.arrg_occurrences.push_back(arrg); pending.occurrences.push_back(row);
  }
  f.memory.Deny(f.army, 0x38, 8); f.memory.Deny(f.army, 0x44, 4); f.memory.Deny(f.a, 0x38, 4);
  auto leaf = ck3_12003::ReadCurrentPostAdmissionRefreshInputs12003(binding, roster, &pending);
  Ready(leaf);
  Check(f.memory.Attempts() == 0 && leaf.occurrences.size() == 2 &&
            leaf.occurrences[0].arrg_occurrences[0].current_38_raw_i32 == std::int32_t{0} &&
            f.memory.Reads(f.a, 0x40, 8) == 2,
        "exact same-query original vector/raw38 reuse must avoid duplicate borrowed reads and still demand40 every occurrence");
  Fixture rejected;
  rejected.Ids(static_cast<std::byte *>(rejected.army) + 0x38, {kWrongGeneration});
  rejected.memory.Put(rejected.fallback_arrg, 0x14, std::uint32_t{0});
  rejected.memory.Deny(rejected.fallback_arrg, 0x10, 4);
  rejected.memory.Deny(rejected.fallback_arrg, 0x38, 4); rejected.memory.Deny(rejected.fallback_arrg, 0x40, 8);
  const auto rows = rejected.Observe(); Ready(Leaf(rows));
  const auto &arrg = Leaf(rows).occurrences[0].arrg_occurrences[0];
  Check(arrg.identity_valid == false && !arrg.arrg_resolution.selected_full_id_u32 &&
            arrg.arrg_resolution.selected_object_ready && !arrg.current_38_raw_i32 && !arrg.value_40_raw_i64 &&
            rejected.memory.Reads(rejected.fallback_arrg, 0x38, 4) == 0 &&
            rejected.memory.Reads(rejected.fallback_arrg, 0x40, 8) == 0,
        "bad magic must establish skipped numeric contribution despite unavailable fallback fullID metadata");
}
void Scenes(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bound = ck3_12003::BindCurrentPostAdmissionRefresh12003(base, ck3_12003::kExecutableSha256);
  Check(bound.common.enabled && bound.arrg_registry_slot == reinterpret_cast<const void *>(base + 0x5D1F340) &&
            bound.arrg_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1F338) &&
            !ck3_12003::BindCurrentPostAdmissionRefresh12003(base, "wrong-build").common.enabled,
        "refresh input bindings must use exact closed ArRg slots/build");
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.army) + 0x38, {kA, kB, kA});
    f.memory.Put(f.a, 0x38, std::numeric_limits<std::int32_t>::max()); f.memory.Put(f.b, 0x38, std::int32_t{1});
    f.memory.Put(f.a, 0x40, std::numeric_limits<std::int64_t>::max()); f.memory.Put(f.b, 0x40, std::int64_t{-5});
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows); Ready(leaf);
    Check(leaf.occurrences.size() == 2 && leaf.occurrences[0].arrg_occurrences.size() == 3 &&
              leaf.occurrences[0].arrg_occurrences[0].raw_full_id_u32 == kA &&
              leaf.occurrences[0].arrg_occurrences[1].raw_full_id_u32 == kB &&
              leaf.occurrences[0].arrg_occurrences[2].raw_full_id_u32 == kA &&
              leaf.occurrences[0].arrg_occurrences[0].arrg_resolution.object_identity ==
                  leaf.occurrences[0].arrg_occurrences[2].arrg_resolution.object_identity &&
              leaf.occurrences[0].actual_army_24_raw_i32 == std::int32_t{777} &&
              leaf.occurrences[0].actual_army_28_raw_i64 == std::int64_t{-888} &&
              f.memory.Reads(f.a, 0x40, 8) == 4 && f.memory.Reads(f.b, 0x40, 8) == 2,
          "original Army/ArRg repeats and signed raw operands must survive exact input capture");
    Emit(directory, "ordered-repeats-and-wrap", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.army) + 0x38, {kWrongGeneration, kWrongGeneration});
    f.memory.Put(f.fallback_arrg, 0x38, std::int32_t{7}); f.memory.Put(f.fallback_arrg, 0x40, std::int64_t{-11});
    const auto rows = f.Observe(); Ready(Leaf(rows)); const auto &row = Leaf(rows).occurrences[0].arrg_occurrences[0];
    Check(row.raw_full_id_u32 == kWrongGeneration && row.arrg_resolution.indexed_full_id_u32 == kA &&
              row.arrg_resolution.used_fallback == true && row.arrg_resolution.selected_full_id_u32 == kFallbackArRg &&
              row.identity_valid == true && row.current_38_raw_i32 == std::int32_t{7} && row.value_40_raw_i64 == std::int64_t{-11},
          "wrong generation must preserve actual fallback identity and repeated fallback arithmetic inputs");
    Emit(directory, "wrong-generation-fallback", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.army) + 0x38, {kA, kInvalid});
    f.memory.Put(f.a, 0x14, std::uint32_t{0}); f.memory.Put(f.fallback_arrg, 0x10, kInvalid);
    f.memory.Deny(f.a, 0x38, 4); f.memory.Deny(f.a, 0x40, 8);
    f.memory.Deny(f.fallback_arrg, 0x38, 4); f.memory.Deny(f.fallback_arrg, 0x40, 8);
    const auto rows = f.Observe(); Ready(Leaf(rows));
    for (const auto &row : Leaf(rows).occurrences[0].arrg_occurrences)
      Check(row.identity_valid == false && !row.current_38_raw_i32 && !row.value_40_raw_i64,
            "selected wrong magic/sentinel rows must preserve skipped occurrence with undemanded numbers");
    Check(f.memory.Attempts() == 0, "skipped identities must not read their numeric operands");
    Emit(directory, "rejected-magic-and-sentinel", rows);
  }
  {
    Fixture f; const auto rows = f.Observe(); Ready(Leaf(rows));
    const auto &row = Leaf(rows).occurrences[0].arrg_occurrences[0];
    Check(row.identity_valid == true && row.current_38_raw_i32 == std::int32_t{0} && row.value_40_raw_i64 == std::int64_t{0},
          "legal zero inputs must be observed complete values"); Emit(directory, "legal-zero-numbers", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.army) + 0x38, {});
    f.memory.Deny(f.army, 0x38, 8); f.memory.Deny(f.arrgs.slot, 0, 8);
    f.memory.Deny(f.army, 0x24, 4); f.memory.Deny(f.army, 0x28, 8);
    const auto rows = f.Observe(); Ready(Leaf(rows));
    Check(Leaf(rows).occurrences[0].arrg_occurrences.empty() &&
              !Leaf(rows).occurrences[0].original_arrg_references.data_present &&
              !Leaf(rows).occurrences[0].actual_army_24_raw_i32 && !Leaf(rows).occurrences[0].actual_army_28_raw_i64 &&
              f.memory.Reads(f.army, 0x38, 8) == 0 && f.memory.Reads(f.arrgs.slot, 0, 8) == 0,
          "zero original vector requires no unused data/resolution while missing cache baselines remain nongating");
    Emit(directory, "known-zero-army-vector", rows);
  }
  {
    Fixture f; f.memory.Put(f.a, 0x38, std::int32_t{12}); f.memory.Deny(f.a, 0x40, 8);
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows);
    Check(!leaf.ready && leaf.numeric_24_inputs_ready && !leaf.numeric_28_inputs_ready &&
              leaf.occurrences[0].arrg_rows_ready && leaf.occurrences[0].arrg_occurrences[0].identity_valid == true &&
              leaf.occurrences[0].arrg_occurrences[0].current_38_raw_i32 == std::int32_t{12} &&
              !leaf.occurrences[0].arrg_occurrences[0].value_40_raw_i64 && f.memory.Reads(f.a, 0x40, 8) == 2,
          "positive38 still demands40; missing40 preserves independently complete24 inputs");
    Emit(directory, "missing40-positive38", rows);
  }
  {
    Fixture f; f.memory.Put(f.a, 0x40, std::int64_t{-9}); f.memory.Deny(f.a, 0x38, 4);
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows);
    Check(!leaf.ready && !leaf.numeric_24_inputs_ready && leaf.numeric_28_inputs_ready &&
              !leaf.occurrences[0].arrg_occurrences[0].current_38_raw_i32 &&
              leaf.occurrences[0].arrg_occurrences[0].value_40_raw_i64 == std::int64_t{-9},
          "missing38 must preserve independently complete28 inputs"); Emit(directory, "missing38-independent28", rows);
  }
  {
    Fixture f; f.memory.Put(f.army, 0x44, std::int32_t{-1}); f.memory.Deny(f.army, 0x38, 8);
    const auto rows = f.Observe(); const auto &row = Leaf(rows).occurrences[0];
    Check(!Leaf(rows).ready && !row.numeric_24_inputs_ready && !row.numeric_28_inputs_ready && !row.arrg_rows_ready &&
              row.original_arrg_references.count_raw_i32 == std::int32_t{-1} && row.arrg_occurrences.empty() &&
              row.original_arrg_references.unavailable_reason == "daily_assault_roster_vector_negative_count" &&
              f.memory.Reads(f.army, 0x38, 8) == 0,
          "negative original vector count remains diagnostic partial rather than zero");
    Emit(directory, "negative-army-vector-count", rows);
  }
  {
    Fixture f; f.Ids(static_cast<std::byte *>(f.manager) + 0x50, {});
    f.memory.Deny(f.manager, 0x50, 8); f.memory.Deny(f.arrgs.slot, 0, 8);
    const auto rows = f.Observe(); Ready(Leaf(rows));
    Check(Leaf(rows).occurrences.empty() && Leaf(rows).original_roster.count_raw_i32 == std::int32_t{0} &&
              f.memory.Attempts() == 0, "known-zero primary roster needs no unused roster/ArRg data");
    Emit(directory, "known-zero-roster", rows);
  }
  SupplementalReuseAndRejectedMetadata();
}
} // namespace
int main(int argc, char **argv) {
  if (argc != 3 || std::string_view(argv[1]) != "--wire-dir") {
    std::cerr << "usage: xar_bridge_ck3_12003_current_post_admission_refresh_test --wire-dir DIRECTORY\n"; return 2;
  }
  try {
    const std::filesystem::path directory(argv[2]); std::filesystem::create_directories(directory); Scenes(directory);
    std::cout << "current post-admission refresh production memory fixture GREEN: 9 new whole-strength wires\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << "current post-admission refresh fixture RED: " << error.what() << '\n'; return 1;
  }
}
