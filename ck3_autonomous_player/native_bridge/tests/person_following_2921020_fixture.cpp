#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Interval { std::uintptr_t address; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Interval> denied;
  std::vector<Interval> unavailable;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void Deny(const void *address, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset, size});
  }
  void Hide(const void *address, std::size_t offset, std::size_t size) {
    unavailable.push_back({reinterpret_cast<std::uintptr_t>(address) + offset, size});
  }
  std::size_t Attempts() const {
    std::size_t count = 0;
    for (const auto &entry : denied) count += entry.attempts;
    return count;
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    const auto overlaps = [begin, size](const Interval &entry) {
      return begin < entry.address + entry.size && entry.address < begin + size;
    };
    for (auto &entry : memory.denied) {
      if (overlaps(entry)) { ++entry.attempts; return false; }
    }
    for (auto &entry : memory.unavailable) {
      if (overlaps(entry)) { ++entry.attempts; return false; }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size && size <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, address, size);
        return true;
      }
    }
    return false;
  }
};
void *At(void *address, std::size_t offset) { return static_cast<std::byte *>(address) + offset; }
using Snapshot = xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1;
constexpr std::uint32_t kLege = 0xAA000001U;
struct Fixture {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *component = memory.Allocate(0x1B8);
  void *storage_slot = memory.Allocate(8);
  void *fallback_slot = memory.Allocate(8);
  void *store = memory.Allocate(0x30);
  void *registry = memory.Allocate(2 * 16);
  void *object = memory.Allocate(0x290);
  void *table = memory.Allocate(0x438 + 3 * 0x3478);
  void *definition = memory.Allocate(0x7A0);
  void *weighted_rows = memory.Allocate(4 * 0x48);
  void *definition_a = memory.Allocate(0x200);
  void *definition_b = memory.Allocate(0x200);

  void Property(void *pc, const std::vector<std::uint16_t> &keys, const std::vector<std::int64_t> &values) {
    Require(keys.size() == values.size(), "following2921020 raw PC pair size");
    memory.Put(pc, 0xC, static_cast<std::int32_t>(keys.size()));
    memory.Put(pc, 0x74, static_cast<std::int32_t>(values.size()));
    if (keys.empty()) return;
    void *key_data = memory.Allocate(keys.size() * 2);
    void *value_data = memory.Allocate(values.size() * 8);
    memory.Put(pc, 0, key_data);
    memory.Put(pc, 0x68, value_data);
    for (std::size_t i = 0; i < keys.size(); ++i) {
      memory.Put(key_data, i * 2, keys[i]);
      memory.Put(value_data, i * 8, values[i]);
    }
  }
  void *Row() { return At(table, 0x438 + 0x3478); }
  void Weight(std::size_t index, void *source, std::int64_t value) {
    memory.Put(weighted_rows, index * 0x48, source);
    memory.Put(weighted_rows, index * 0x48 + 0x30, value);
  }
  Fixture() {
    bindings.enabled = true;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    bindings.following_2921020.enabled = true;
    bindings.following_2921020.lege_storage_slot = storage_slot;
    bindings.following_2921020.lege_fallback_slot = fallback_slot;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(character, 0x1C0, component);
    memory.Put(component, 0x1B0, kLege);
    memory.Put(storage_slot, 0, store);
    memory.Put(fallback_slot, 0, object);
    memory.Put(store, 0x20, registry);
    memory.Put(store, 0x2C, std::uint32_t{2});
    memory.Put(registry, 16 + 8, object);
    memory.Put(object, 8, kLege);
    memory.Put(object, 0xC, std::uint32_t{0x4C656765U});
    memory.Put(object, 0x288, std::int32_t{29829});
    memory.Put(object, 0x70, table);
    memory.Put(object, 0x78, definition);
    memory.Put(object, 0x250, std::int8_t{1});
    memory.Put(object, 0x28, weighted_rows);
    memory.Put(object, 0x34, std::int32_t{4});
    Weight(0, definition_a, 200000);
    Weight(1, definition_a, -100000);
    Weight(2, definition_b, -200000);
    Weight(3, definition_a, 0);
    Property(At(definition_a, 0x40), {0}, {100000});
    Property(At(definition_b, 0x40), {5}, {-100000});
    Property(At(definition, 0x420), {1, 5}, {100000, 200000});
    Property(At(Row(), 0x2BF8), {4, 5}, {-100000, -100000});
    Property(At(definition, 0x5E0), {5}, {0});
    Property(At(Row(), 0x2DB8), {}, {});

    // Existing always-collected source leaves receive actual empty headers.
    void *first = memory.Allocate(0x220);
    void *second = memory.Allocate(0x150);
    bindings.first_storage_slot = memory.Allocate(8);
    bindings.first_fallback_slot = memory.Allocate(8);
    bindings.second_storage_slot = memory.Allocate(8);
    bindings.second_fallback_slot = memory.Allocate(8);
    memory.Put(const_cast<void *>(bindings.first_fallback_slot), 0, first);
    memory.Put(const_cast<void *>(bindings.second_fallback_slot), 0, second);
    bindings.lifestyle_fallback_header = memory.Allocate(0x10);
    bindings.house_extra_fallback_header = memory.Allocate(0x10);
    bindings.source_fallback_header = memory.Allocate(0x10);
  }
  void DenyOwnerHeader() {
    memory.Deny(object, 0x28, 8);
    memory.Deny(object, 0x34, 4);
    memory.Deny(weighted_rows, 0, 4 * 0x48);
  }
  void DenyLater() {
    memory.Deny(object, 0x28, 8);
    memory.Deny(object, 0x34, 4);
    memory.Deny(object, 0x70, 16);
    memory.Deny(object, 0x250, 1);
    memory.Deny(object, 0x288, 4);
  }
  Snapshot Observe() {
    Require(bindings.enabled && bindings.following_2921020.enabled, "following2921020 binding disabled");
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "following2921020 fixture must not install native evaluator callbacks");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    Require(first == second && first.following_2921020.has_value(), "following2921020 fixed-frame whole DTO differs");
    Require(memory.Attempts() == 0, "following2921020 undemanded branch was read");
    return first;
  }
};
void Save(const std::filesystem::path &directory, const char *name, const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("following2921020-") + name + ".json"), std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("following2921020 whole wire write failed");
}
void ReadyOwner(const auto &leaf) {
  Require(leaf.ready && leaf.admitted == true && leaf.owner_matches == true &&
      leaf.rank_raw_i8 == 1 && leaf.tier_selection == "direct_rank_0_2" &&
      leaf.selected_row_identity && leaf.owner_header_ready == true && leaf.composite_ready &&
      leaf.owner_weighted_header && leaf.owner_weighted_header->count == 4 &&
      leaf.owner_weighted_header->rows && leaf.owner_weighted_header->rows->size() == 4 &&
      leaf.owner_definition_blocks.size() == 2, "following2921020 positive owner demands differ");
  const auto &rows = *leaf.owner_weighted_header->rows;
  Require(rows[0].definition_identity == rows[1].definition_identity &&
      rows[0].definition_identity == rows[3].definition_identity &&
      rows[0].definition_identity != rows[2].definition_identity,
      "following2921020 full-pointer A,A,B,A sequence lost");
  Require(leaf.base_pc.property_block && leaf.base_pc.property_block->keys_u16 ==
      std::optional<std::vector<std::uint16_t>>{{1, 5}} && leaf.tier_pc.property_block &&
      leaf.tier_pc.property_block->values_q64 == std::optional<std::vector<std::int64_t>>{{-100000, -100000}},
      "following2921020 actual base/tier numeric arrays differ");
}
void KnownSkip(const auto &leaf) {
  Require(leaf.ready && leaf.admitted == false && !leaf.owner_matches &&
      !leaf.table_identity && !leaf.rank_raw_i8 && !leaf.selected_row_identity &&
      !leaf.owner_weighted_header && leaf.owner_definition_blocks.empty() &&
      !leaf.owner_header_ready && !leaf.base_pc.property_block && !leaf.tier_pc.property_block &&
      !leaf.composite_ready, "following2921020 rejected admission must keep later fields null");
}
void Run(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bound = xar::ck3_12002::BindContextSourceInputs12003(base, xar::ck3_12003::kExecutableSha256);
  Require(bound.following_2921020.enabled &&
      bound.following_2921020.lege_storage_slot == reinterpret_cast<const void *>(base + 0x5D1EC98) &&
      bound.following_2921020.lege_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1EC50),
      "following2921020 exact-build slots differ");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "wrong-build").following_2921020.enabled,
      "following2921020 outer factory accepted wrong build");
  {
    Fixture f;
    const auto snapshot = f.Observe();
    ReadyOwner(*snapshot.following_2921020);
    Save(directory, "positive-owner", snapshot);
  }
  {
    Fixture f;
    f.Weight(0, f.definition_a, std::numeric_limits<std::int64_t>::max());
    f.Weight(1, f.definition_a, 1);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2921020;
    ReadyOwner(leaf);
    Require(leaf.owner_weighted_header->rows->at(0).weight_q64 == std::numeric_limits<std::int64_t>::max() &&
        leaf.owner_weighted_header->rows->at(1).weight_q64 == 1 &&
        leaf.owner_weighted_header->rows->at(2).weight_q64 == -200000 &&
        leaf.owner_weighted_header->rows->at(3).weight_q64 == 0,
        "following2921020 raw signed wrap operands altered");
    Save(directory, "owner-wrap", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.object, 0x288, std::int32_t{31050});
    f.DenyOwnerHeader();
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2921020;
    Require(leaf.ready && leaf.owner_matches == false && !leaf.owner_weighted_header &&
        !leaf.owner_header_ready && leaf.owner_definition_blocks.empty() && leaf.composite_ready &&
        leaf.base_pc.property_block && leaf.base_pc.property_block->keys_count == 1 &&
        leaf.base_pc.property_block->values_q64 == std::optional<std::vector<std::int64_t>>{{0}} &&
        leaf.tier_pc.property_block && leaf.tier_pc.property_block->keys_count == 0,
        "following2921020 nonowner zero-valued key lost or owner header demanded");
    Save(directory, "nonowner-zero-key", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.storage_slot, 0, static_cast<void *>(nullptr));
    f.memory.Put(f.object, 0xC, std::uint32_t{0});
    f.memory.Deny(f.object, 8, 4);
    f.DenyLater();
    const auto snapshot = f.Observe();
    KnownSkip(*snapshot.following_2921020);
    Save(directory, "invalid-magic", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    f.memory.Put(f.object, 8, std::int32_t{-1});
    f.DenyLater();
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2921020;
    KnownSkip(leaf);
    Require(leaf.component_present == false && leaf.requested_full_id_raw == -1 &&
        leaf.resolution_selection == "native_fallback" && leaf.full_id_raw == -1,
        "following2921020 null carrier must request full FFFFFFFF");
    Save(directory, "invalid-sentinel", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.object, 0x34, std::int32_t{0});
    f.memory.Deny(f.object, 0x28, 8);
    f.Property(At(f.definition, 0x420), {}, {});
    f.Property(At(f.Row(), 0x2BF8), {}, {});
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2921020;
    Require(leaf.ready && leaf.owner_header_ready == true && leaf.composite_ready &&
        leaf.owner_weighted_header && leaf.owner_weighted_header->rows && leaf.owner_weighted_header->rows->empty() &&
        leaf.base_pc.property_block->keys_count == 0 && leaf.tier_pc.property_block->keys_count == 0,
        "following2921020 both empty PCs must preserve known empty owner header");
    Save(directory, "both-pcs-empty", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.object, 0x250, std::int8_t{-1});
    f.DenyOwnerHeader();
    f.memory.Deny(f.definition, 0x420, 0x380);
    f.memory.Deny(f.table, 0, 0x438 + 3 * 0x3478);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2921020;
    Require(!leaf.ready && leaf.admitted == true && leaf.rank_raw_i8 == -1 &&
        leaf.tier_selection == "diagnostic_3f7ab90_outcome_unobserved" &&
        leaf.reason == "rank_diagnostic_3f7ab90_result" && !leaf.selected_row_identity &&
        !leaf.owner_weighted_header && !leaf.owner_header_ready && !leaf.composite_ready &&
        !leaf.base_pc.property_block && !leaf.tier_pc.property_block,
        "following2921020 invalid rank fabricated row/header/composite");
    Save(directory, "invalid-rank", snapshot);
  }
  {
    Fixture f;
    f.memory.Hide(f.object, 0x34, 4);
    f.memory.Deny(f.object, 0x28, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2921020;
    Require(!leaf.ready && leaf.owner_matches == true && leaf.owner_header_ready == false &&
        leaf.owner_weighted_header && !leaf.owner_weighted_header->count && leaf.composite_ready,
        "following2921020 unread owner prefix must retain independent complete composite");
    Save(directory, "owner-header-missing", snapshot);
  }
}
} // namespace

void RunFollowing2921020Fixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}
