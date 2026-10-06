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
  std::vector<Region> regions;
  std::vector<Request> requests, denied;
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
    std::size_t count = 0;
    for (const auto &request : requests)
      if (request.address == address && request.size == size) ++count;
    return count;
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
      store(m.Allocate(0x30)), table(m.Allocate(16 * 16)) {
    m.Put(slot, 0, store); m.Put(store, 0x20, table); m.Put(store, 0x2C, std::uint32_t{16});
  }
  void Add(std::uint32_t full, void *object, std::size_t full_offset) {
    memory.Put(table, (full & 0xFFFFFFU) * 16 + 8, object);
    memory.Put(object, full_offset, full);
  }
};
constexpr std::uint32_t kUnit = 0x11000001U, kArmy = 0x22000001U;
constexpr std::uint32_t kRegiment = 0x2B000001U;
constexpr std::uint32_t kWrongGeneration = 0xAB00000CU, kInvalidArmy = 0x22000002U;
constexpr std::uint32_t kHelper = 12U, kSiege = 0xDD000001U;
void *expected_army = nullptr;
std::int32_t Current(void *receiver, std::uint8_t flags) {
  Check(receiver == static_cast<std::byte *>(expected_army) + 0x38 && flags == 0,
        "removal reference fixture current getter receiver");
  return 20;
}
std::int32_t Maximum(void *receiver) {
  Check(receiver == expected_army, "removal reference fixture maximum receiver"); return 40;
}
struct Fixture {
  Memory memory;
  Registry units{memory}, armies{memory}, arrgs{memory}, sieges{memory};
  ck3_12002::ArmyBindings bindings{};
  void *state_slot = memory.Allocate(8), *state = memory.Allocate(0xA8);
  void *data = memory.Allocate(0x2A540 + 0x500);
  void *manager = static_cast<std::byte *>(data) + 0x2A540;
  void *entries = memory.Allocate(3 * 0x40);
  void *record = static_cast<std::byte *>(entries) + 0x40;
  void *unit = memory.Allocate(0x180), *army = memory.Allocate(0x208);
  void *regiment = memory.Allocate(0x48), *regiment_ids = memory.Allocate(4);
  void *helper = memory.Allocate(0x208), *passed_fallback = memory.Allocate(0x208);
  void *invalid = memory.Allocate(0x208), *siege = memory.Allocate(0x10);
  void *army_allocator = memory.Allocate(8), *arrg_allocator = memory.Allocate(8);
  void *bucket = memory.Allocate(4 * sizeof(void *));
  std::size_t bucket_offset = 0x198U + 0x18U * (kHelper % 30U);
  Fixture() {
    bindings.enabled = true; bindings.game_state_slot = static_cast<void **>(state_slot);
    bindings.unit_storage_slot = static_cast<void **>(units.slot);
    bindings.internal_army_storage_slot = static_cast<void **>(armies.slot);
    bindings.regiment_storage_slot = static_cast<void **>(arrgs.slot);
    bindings.get_army_current_soldiers = Current; bindings.get_army_maximum_soldiers = Maximum;
    bindings.monthly_daily_queue_bindings.enabled = true;
    bindings.monthly_daily_queue_bindings.army_fallback_slot = static_cast<void **>(armies.fallback_slot);
    bindings.monthly_first_removal_cleanup_inputs_enabled = true;
    auto &b = bindings.current_daily_assault_table_bindings;
    b.enabled = true; b.game_state_slot = state_slot;
    b.army_registry_slot = armies.slot; b.army_fallback_slot = armies.fallback_slot;
    b.arrg_registry_slot = arrgs.slot; b.arrg_fallback_slot = arrgs.fallback_slot;
    b.siege_registry_slot = sieges.slot; b.siege_fallback_slot = sieges.fallback_slot;
    b.expected_army_allocator = army_allocator; b.expected_arrg_allocator = arrg_allocator;
    b.read_memory = Memory::Read; b.read_context = &memory;
    bindings.current_assault_removal_reference_bindings.enabled = true;
    bindings.current_assault_removal_reference_bindings.lookup = b;
    memory.Put(state_slot, 0, state); memory.Put(state, 0xA0, data);
    memory.Put(manager, 0x178, entries); memory.Put(manager, 0x180, std::int32_t{1});
    memory.Put(manager, 0x184, std::int32_t{1}); memory.Put(manager, 0x188, std::uint8_t{0});
    memory.Put(manager, 0x18C, std::uint32_t{0x3F400000U});
    memory.Put(entries, 2 * 0x40 + 4, std::uint8_t{0xA5});
    memory.Put(record, 4, std::uint8_t{1}); memory.Put(record, 8, kSiege);
    units.Add(kUnit, unit, 0x10); armies.Add(kArmy, army, 0x10);
    armies.Add(kHelper, helper, 0x10); armies.Add(kInvalidArmy, invalid, 0x10);
    sieges.Add(kSiege, siege, 8); memory.Put(armies.fallback_slot, 0, passed_fallback);
    memory.Put(passed_fallback, 0x10, kHelper);
    for (void *object : {army, helper, passed_fallback})
      memory.Put(object, 0x14, std::uint32_t{0x41726D79U});
    memory.Put(invalid, 0x14, std::uint32_t{0x446C7464U});
    memory.Put(unit, 0x178, kArmy); memory.Put(army, 0x124, kUnit);
    arrgs.Add(kRegiment, regiment, 0x10);
    memory.Put(regiment, 0x14, std::uint32_t{0x41725267U});
    memory.Put(regiment, 0x38, std::int32_t{20}); memory.Put(regiment, 0x3C, std::int32_t{40});
    memory.Put(regiment, 0x40, std::int64_t{100000}); memory.Put(regiment_ids, 0, kRegiment);
    memory.Put(army, 0x38, regiment_ids); memory.Put(army, 0x40, std::int32_t{1});
    memory.Put(army, 0x44, std::int32_t{1});
    Global(0x50, {12, 91, 12, 92});
    Pending({static_cast<std::int32_t>(kWrongGeneration), static_cast<std::int32_t>(kInvalidArmy),
             12, static_cast<std::int32_t>(kWrongGeneration)});
    for (std::size_t offset : {0x80U, 0x98U, 0xC8U, 0x158U}) Global(offset, {12, 8, 12, 9});
    void *records = memory.Allocate(4 * 16);
    const std::array<std::array<std::uint32_t, 4>, 4> values{{
        {12U, 1U, 2U, 3U}, {8U, 4U, 5U, 6U}, {12U, 7U, 8U, 9U}, {9U, 10U, 11U, 12U}}};
    for (std::size_t i = 0; i < values.size(); ++i) memory.Put(records, i * 16, values[i]);
    memory.Put(manager, 0xB0, records); memory.Put(manager, 0xBC, std::int32_t{4});
    Group({kWrongGeneration, kWrongGeneration, kInvalidArmy});
    memory.Put(record, 0x20, army_allocator); memory.Put(record, 0x38, arrg_allocator);
    memory.Put(manager, bucket_offset, bucket); memory.Put(manager, bucket_offset + 0xC, std::int32_t{4});
    memory.Put(bucket, 0, passed_fallback); memory.Put(bucket, sizeof(void *), helper);
    memory.Put(bucket, 2 * sizeof(void *), army); memory.Put(bucket, 3 * sizeof(void *), helper);
    expected_army = army;
  }
  void Global(std::size_t offset, const std::vector<std::int32_t> &ids) {
    void *buffer = ids.empty() ? nullptr : memory.Allocate(ids.size() * sizeof(std::int32_t));
    for (std::size_t i = 0; i < ids.size(); ++i) memory.Put(buffer, i * 4, ids[i]);
    memory.Put(manager, offset, buffer);
    memory.Put(manager, offset + 0xC, static_cast<std::int32_t>(ids.size()));
  }
  void Pending(const std::vector<std::int32_t> &ids) { Global(0x68, ids); }
  void Group(const std::vector<std::uint32_t> &ids) {
    void *buffer = ids.empty() ? nullptr : memory.Allocate(ids.size() * sizeof(std::uint32_t));
    for (std::size_t i = 0; i < ids.size(); ++i) memory.Put(buffer, i * 4, ids[i]);
    memory.Put(record, 0x10, buffer); memory.Put(record, 0x1C, static_cast<std::int32_t>(ids.size()));
  }
  std::vector<game::ArmyStrengthSnapshot> Observe() {
    const std::array<ck3_12002::ArmyStrengthScope, 1> scope{{
        {static_cast<std::int32_t>(kUnit), game::ArmyStrengthScopeRole::player, {}}}};
    std::vector<game::ArmyStrengthSnapshot> rows;
    Check(ck3_12002::ReadArmyStrengthsForScope(bindings, scope, rows) == game::ReadArmyStrengthsResult::available &&
              rows.size() == 1 && rows[0].available && rows[0].current_soldiers == 20 &&
              rows[0].maximum_soldiers == 40 && rows[0].current_assault_removal_reference_inputs_v1,
          "new removal context must preserve actual whole ArmyStrength reader");
    Check(memory.Reads(manager, 0x68, 8) == 0 && memory.Reads(manager, 0x74, 4) == 0 &&
              memory.Reads(manager, 0x50, 8) == 0 && memory.Reads(manager, 0xB0, 8) == 0,
          "new producer borrows queue and six lists/B0 without second raw read loop");
    Check(memory.Reads(passed_fallback, 0x14, 4) == 2,
          "two group fallback occurrences read current magic; pending magic is copied");
    return rows;
  }
};
const game::ArmyCurrentAssaultRemovalReferenceInputsV1 &Leaf(const std::vector<game::ArmyStrengthSnapshot> &rows) {
  return *rows[0].current_assault_removal_reference_inputs_v1;
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
  std::ofstream output(directory / (std::string("current-assault-removal-") + name + ".json"), std::ios::binary);
  output << wire << '\n'; Check(static_cast<bool>(output), "new current removal whole-strength wire output");
}
void Cases(const std::filesystem::path &directory) {
  {
    Fixture f; const auto rows = f.Observe(); const auto &leaf = Leaf(rows);
    Check(leaf.ready && leaf.reference_occurrences.size() == 7 && leaf.cleanup_targets.size() == 1 &&
              leaf.reference_occurrences[0].resolution.used_fallback == true &&
              leaf.reference_occurrences[0].resolution.object_identity != leaf.cleanup_targets[0].helper_resolution.object_identity &&
              leaf.cleanup_targets[0].helper_resolution.used_fallback == false &&
              leaf.cleanup_targets[0].selected_bucket_index_u32 == 12U &&
              leaf.cleanup_targets[0].bucket_rows->at(0).native_same_helper_pointer == false &&
              leaf.cleanup_targets[0].bucket_rows->at(1).native_same_helper_pointer == true &&
              leaf.cleanup_targets[0].bucket_rows->at(3).native_same_helper_pointer == true &&
              leaf.reference_occurrences[1].native_army_identity_valid == false,
          "actual raw generation fallback and second helper receiver/pointer-only bucket context");
    Check(f.memory.Reads(f.manager, f.bucket_offset + 0xC, 4) == 1,
          "repeated selected FullID shares one argument-specific bucket capture");
    Emit(directory, "fallback-distinct-helper", rows);
  }
  {
    Fixture f; f.memory.Put(f.bucket, 2 * sizeof(void *), static_cast<void *>(nullptr));
    const auto rows = f.Observe(); const auto &target = Leaf(rows).cleanup_targets[0];
    Check(target.ready && target.bucket_rows->at(2).pointer_identity == "native:0" &&
              target.bucket_rows->at(2).native_same_helper_pointer == false,
          "known null bucket pointer is not an unread operand");
    Emit(directory, "known-null-bucket-pointer", rows);
  }
  {
    Fixture f; f.Pending({static_cast<std::int32_t>(kInvalidArmy)});
    f.Group({kWrongGeneration, kWrongGeneration, kInvalidArmy});
    f.memory.Put(f.passed_fallback, 0x14, std::uint32_t{0x446C7464U});
    f.memory.Put(f.manager, 0x80, static_cast<void *>(nullptr)); f.memory.Put(f.manager, 0x8C, std::int32_t{1});
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows);
    Check(leaf.ready && leaf.cleanup_targets.empty() && leaf.manager_id_lists[2].ordered_army_ids == std::nullopt &&
              leaf.reference_occurrences[0].native_army_identity_valid == false,
          "known invalid magic selection never requires unused global list or bucket inputs");
    Emit(directory, "invalid-magic-unused-context", rows);
  }
  {
    Fixture f; f.memory.Deny(f.bucket, sizeof(void *), sizeof(void *));
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows);
    Check(!leaf.ready && leaf.reference_occurrences[0].ready && !leaf.cleanup_targets[0].ready &&
              !leaf.cleanup_targets[0].bucket_rows->at(1).native_same_helper_pointer,
          "actual required bucket pointer unread remains independently partial");
    Emit(directory, "required-bucket-pointer-unread", rows);
  }
  {
    Fixture f; f.memory.Put(f.manager, f.bucket_offset + 0xC, std::int32_t{-3});
    const auto rows = f.Observe(); const auto &target = Leaf(rows).cleanup_targets[0];
    Check(target.ready && target.bucket_count_raw_i32 == -3 && target.bucket_rows->empty() &&
              f.memory.Reads(f.manager, f.bucket_offset, 8) == 0,
          "source nonpositive bucket branch preserves raw negative count without unused data read");
    Emit(directory, "negative-bucket-count", rows);
  }
  {
    Fixture f; f.memory.Put(f.manager, 0x80, static_cast<void *>(nullptr));
    f.memory.Put(f.manager, 0x8C, std::int32_t{1});
    const auto rows = f.Observe(); const auto &leaf = Leaf(rows);
    Check(!leaf.ready && leaf.cleanup_targets[0].ready && leaf.reference_occurrences[0].ready &&
              !leaf.manager_id_lists[2].ordered_army_ids,
          "missing used global component preserves actual selected receiver and other finite values");
    Emit(directory, "required-global-component-unread", rows);
  }
}
} // namespace
int main(int argc, char **argv) {
  try {
    const std::filesystem::path directory = argc > 1 ? argv[1] : "current-assault-removal-reference-wire";
    std::filesystem::create_directories(directory); Cases(directory);
    std::cout << "new current assault first removal context cases passed\n"; return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n'; return 1;
  }
}
