#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
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
  struct Denied { std::uintptr_t address; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
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
  std::size_t Attempts() const {
    std::size_t count = 0;
    for (const auto &entry : denied) count += entry.attempts;
    return count;
  }
  static bool Read(void *context, const void *address, void *output, std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &entry : memory.denied) {
      if (begin < entry.address + entry.size && entry.address < begin + size) {
        ++entry.attempts; return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size &&
          size <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, address, size); return true;
      }
    }
    return false;
  }
};
using Snapshot = xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1;
constexpr std::int64_t kQ = 100000;
constexpr std::uint32_t kProvinceId = 0xCA000009U;
constexpr std::uint32_t kTitleRoot = 0xA0000001U, kTitleA = 0xA0000002U, kTitleB = 0xA0000003U;
constexpr std::uint32_t kSourceA = 0xB0000001U, kSourceB = 0xB0000002U;
struct Fixture {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *living = memory.Allocate(0x200);
  void *title_ids = memory.Allocate(4);
  void *title_default = memory.Allocate(0x10);
  void *title_root = memory.Allocate(0x340), *title_a = memory.Allocate(0x340), *title_b = memory.Allocate(0x340);
  void *definition_root = memory.Allocate(0x68), *definition_a = memory.Allocate(0x68), *definition_b = memory.Allocate(0x68);
  void *title_children = memory.Allocate(12);
  void *title_storage_slot = memory.Allocate(8), *title_fallback_slot = memory.Allocate(8);
  void *title_store = memory.Allocate(0x30), *title_table = memory.Allocate(4 * 16);
  void *province = memory.Allocate(0x860), *source_ids = memory.Allocate(12);
  void *source_storage_slot = memory.Allocate(8), *source_fallback_slot = memory.Allocate(8);
  void *source_store = memory.Allocate(0x30), *source_table = memory.Allocate(3 * 16);
  void *source_a = memory.Allocate(0xE0), *source_b = memory.Allocate(0xE0);
  void *source_def_a = memory.Allocate(0xEE0), *source_def_b = memory.Allocate(0xEE0);
  void *map_a = memory.Allocate(0x70), *map_b = memory.Allocate(0x70);
  void *tiers_a = memory.Allocate(2 * 0x548), *tiers_b = memory.Allocate(2 * 0x548);
  void *manager_slot = memory.Allocate(8), *manager = memory.Allocate(0x60);
  void *default_guard = memory.Allocate(4), *default_row = memory.Allocate(0x548);
  Fixture() {
    bindings.enabled = true;
    bindings.read_memory = &Memory::Read; bindings.read_context = &memory;
    auto &b = bindings.following_2921350;
    b.enabled = true;
    b.title_storage_slot = title_storage_slot; b.title_fallback_slot = title_fallback_slot;
    b.title_default_header = title_default;
    b.source_storage_slot = source_storage_slot; b.source_fallback_slot = source_fallback_slot;
    b.manager_slot = manager_slot; b.tier_default_guard = default_guard; b.tier_default_row = default_row;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C0, living);
    memory.Put(living, 0x1E0, title_ids); memory.Put(living, 0x1EC, std::int32_t{1});
    memory.Put(title_ids, 0, kTitleRoot);
    memory.Put(title_default, 0, title_ids); memory.Put(title_default, 0xC, std::int32_t{1});
    memory.Put(title_storage_slot, 0, title_store); memory.Put(title_fallback_slot, 0, title_a);
    memory.Put(title_store, 0x20, title_table); memory.Put(title_store, 0x2C, std::uint32_t{4});
    memory.Put(title_table, 16 + 8, title_root); memory.Put(title_table, 32 + 8, title_a);
    memory.Put(title_table, 48 + 8, title_b);
    memory.Put(title_root, 0x10, kTitleRoot); memory.Put(title_a, 0x10, kTitleA); memory.Put(title_b, 0x10, kTitleB);
    memory.Put(title_root, 0x48, definition_root); memory.Put(title_a, 0x48, definition_a);
    memory.Put(title_b, 0x48, definition_b);
    memory.Put(definition_root, 0x64, std::int32_t{3});
    memory.Put(definition_a, 0x64, std::int32_t{1}); memory.Put(definition_b, 0x64, std::int32_t{1});
    memory.Put(title_root, 0xF0, title_children); memory.Put(title_root, 0xFC, std::int32_t{3});
    memory.Put(title_children, 0, kTitleA); memory.Put(title_children, 4, kTitleA); memory.Put(title_children, 8, kTitleB);
    memory.Put(title_a, 0x338, province); memory.Put(title_b, 0x338, province);
    memory.Put(province, 0x85C, std::uint32_t{0x50726F76U}); memory.Put(province, 0x10, kProvinceId);
    memory.Put(province, 0x7A8, source_ids); memory.Put(province, 0x7B4, std::int32_t{3});
    memory.Put(source_ids, 0, kSourceA); memory.Put(source_ids, 4, kSourceA); memory.Put(source_ids, 8, kSourceB);
    memory.Put(source_storage_slot, 0, source_store); memory.Put(source_fallback_slot, 0, source_b);
    memory.Put(source_store, 0x20, source_table); memory.Put(source_store, 0x2C, std::uint32_t{3});
    memory.Put(source_table, 16 + 8, source_a); memory.Put(source_table, 32 + 8, source_b);
    memory.Put(source_a, 8, kSourceA); memory.Put(source_b, 8, kSourceB);
    memory.Put(source_a, 0x88, source_def_a); memory.Put(source_b, 0x88, source_def_b);
    memory.Put(source_def_a, 0x10, std::int32_t{0}); memory.Put(source_def_b, 0x10, std::int32_t{1});
    memory.Put(source_a, 0xC8, map_a); memory.Put(source_b, 0xC8, map_b);
    memory.Put(source_a, 0xD4, std::int32_t{0}); memory.Put(source_b, 0xD4, std::int32_t{0});
    memory.Put(source_a, 0xD8, std::uint8_t{0}); memory.Put(source_b, 0xD8, std::uint8_t{0});
    memory.Put(map_a, 4, std::uint8_t{1}); memory.Put(map_a, 8, kProvinceId);
    memory.Put(map_a, 0x30, std::int64_t{0}); // Equality at first threshold must continue.
    memory.Put(map_b, 4, std::uint8_t{0}); // Real distance termination, key/payload not demanded.
    memory.Put(source_def_a, 0xED0, tiers_a); memory.Put(source_def_b, 0xED0, tiers_b);
    memory.Put(source_def_a, 0xEDC, std::int32_t{2}); memory.Put(source_def_b, 0xEDC, std::int32_t{2});
    memory.Put(tiers_a, 0x540, std::int64_t{0}); memory.Put(tiers_b, 0x540, std::int64_t{0});
    memory.Put(tiers_a, 0x548 + 0x540, 10 * kQ); memory.Put(tiers_b, 0x548 + 0x540, 10 * kQ);
    Pc(static_cast<std::byte *>(tiers_a) + 0x380, {0, 5, 65535}, {-kQ, 2 * kQ, -3 * kQ});
    Pc(static_cast<std::byte *>(tiers_b) + 0x380, {4}, {0});
    Pc(static_cast<std::byte *>(default_row) + 0x380, {4}, {-2 * kQ});
    memory.Put(manager_slot, 0, manager); memory.Put(manager, 0x5C, std::int32_t{3});
    // Fixed empty inputs for the two existing always-collected source leaves.
    void *first = memory.Allocate(0x220), *second = memory.Allocate(0x150);
    bindings.first_storage_slot = memory.Allocate(8); bindings.first_fallback_slot = memory.Allocate(8);
    bindings.second_storage_slot = memory.Allocate(8); bindings.second_fallback_slot = memory.Allocate(8);
    memory.Put(const_cast<void *>(bindings.first_fallback_slot), 0, first);
    memory.Put(const_cast<void *>(bindings.second_fallback_slot), 0, second);
    bindings.lifestyle_fallback_header = memory.Allocate(0x10);
    bindings.house_extra_fallback_header = memory.Allocate(0x10);
    bindings.source_fallback_header = memory.Allocate(0x10);
  }
  void Pc(void *pc, std::initializer_list<std::uint16_t> keys,
          std::initializer_list<std::int64_t> values) {
    Require(keys.size() == values.size(), "following2921350 fixture PC cardinality mismatch");
    void *key_data = memory.Allocate(keys.size() * 2), *value_data = memory.Allocate(values.size() * 8);
    std::size_t i = 0;
    for (auto key : keys) memory.Put(key_data, i++ * 2, key);
    i = 0; for (auto value : values) memory.Put(value_data, i++ * 8, value);
    memory.Put(pc, 0, key_data); memory.Put(pc, 0xC, static_cast<std::int32_t>(keys.size()));
    memory.Put(pc, 0x68, value_data); memory.Put(pc, 0x74, static_cast<std::int32_t>(values.size()));
  }
  Snapshot Observe() {
    Require(bindings.following_2921350.enabled && !bindings.provider && !bindings.government &&
                !bindings.existing_token_lookup, "following2921350 fixture installs only memory reads");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    Require(first == second && first.following_2921350.has_value(),
            "following2921350 fixed whole query snapshot changed or leaf absent");
    return first;
  }
  void Cold(bool initialized) {
    memory.Put(map_b, 4, std::uint8_t{1}); memory.Put(map_b, 8, kProvinceId);
    memory.Put(map_b, 0x30, std::int64_t{-1});
    memory.Put(default_guard, 0, std::int32_t{initialized ? 1 : 0});
  }
};
void Save(const std::filesystem::path &directory, const char *name, const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("following2921350-") + name + ".json"), std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("following2921350 wire write failed");
}
void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = xar::ck3_12002::BindContextSourceInputs12003(base, xar::ck3_12003::kExecutableSha256);
  const auto address = [base](std::uintptr_t rva) { return reinterpret_cast<const void *>(base + rva); };
  const auto &s = b.following_2921350;
  Require(b.enabled && s.enabled && s.title_storage_slot == address(0x5D1DAF8) &&
              s.title_fallback_slot == address(0x5D1DAE0) && s.title_default_header == address(0x5459C88) &&
              s.source_storage_slot == address(0x5D1EC90) && s.source_fallback_slot == address(0x5D1EC48) &&
              s.manager_slot == address(0x5C671A8) && s.tier_default_row == address(0x5D65B00) &&
              s.tier_default_guard == address(0x5D65AFC), "following2921350 exact-build source bindings differ");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "wrong-build").following_2921350.enabled,
          "following2921350 source bindings accepted wrong EXE");
}
void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture f;
    f.memory.Deny(f.default_guard, 0, 4); f.memory.Deny(f.default_row, 0x38C, 4);
    f.memory.Deny(f.map_b, 8, 4); f.memory.Deny(f.map_b, 0x30, 8);
    const auto snapshot = f.Observe(); const auto &leaf = *snapshot.following_2921350;
    Require(snapshot.ready && leaf.ready && leaf.character_id == 29829 &&
                leaf.source_scope == "held_current_native_inputs" && leaf.title_source.ready &&
                leaf.title_walk.size() == 4 && leaf.title_walk[1].collected == true &&
                leaf.title_walk[2].collected == false && leaf.title_walk[3].collected == true &&
                leaf.provinces.size() == 2 && leaf.provinces[0].province_identity == leaf.provinces[1].province_identity,
            "following2921350 must dedup physical Titles and retain duplicate Province occurrences");
    const auto &a = leaf.provinces[0].sources[0]; const auto &b = leaf.provinces[0].sources[2];
    Require(leaf.manager.ready && leaf.manager.group_count_raw_i32 == 3 &&
                leaf.provinces[0].sources.size() == 3 &&
                a.map.ready && a.map.found == true && a.map.operand_q64 == 0 &&
                a.tiers.ready && a.tiers.selected_index_raw_i32 == 0 &&
                a.tiers.thresholds_q64->size() == 2 && a.tiers.pc.property_block->values_q64->at(0) == -kQ &&
                b.map.found == false && b.map.operand_q64 == 0 &&
                b.tiers.pc.property_block->keys_count == 1 && b.tiers.pc.property_block->values_q64->at(0) == 0 &&
                f.memory.Attempts() == 0, "following2921350 map absent/equality/signed/nonempty-zero raw values differ");
    Save(directory, "positive", snapshot);
  }
  {
    Fixture f; f.Cold(false); f.memory.Deny(f.default_row, 0x38C, 4);
    const auto snapshot = f.Observe(); const auto &leaf = *snapshot.following_2921350;
    Require(!snapshot.ready && !leaf.ready && leaf.reason == "tier_default_2560620_result" &&
                leaf.provinces.size() == 2 && leaf.provinces[0].sources.size() == 3 &&
                leaf.provinces[0].sources[0].tiers.ready && leaf.provinces[1].sources[0].tiers.ready &&
                leaf.provinces[0].sources[2].group_index_raw_i32 == 1 &&
                leaf.provinces[0].sources[2].tiers.selection == "cold_default_5d65b00" &&
                !leaf.provinces[0].sources[2].tiers.pc.property_block && f.memory.Attempts() == 0,
            "following2921350 cold group1 must retain precise missing PC and complete group0 source census");
    Save(directory, "cold", snapshot);
  }
  {
    Fixture f; f.Cold(true);
    const auto snapshot = f.Observe(); const auto &source = snapshot.following_2921350->provinces[0].sources[2];
    Require(snapshot.ready && snapshot.following_2921350->ready && source.tiers.ready &&
                source.tiers.selection == "initialized_default_5d65b00" && source.tiers.selected_index_raw_i32 == -1 &&
                source.tiers.thresholds_q64->size() == 1 &&
                source.tiers.pc.property_block->values_q64->at(0) == -2 * kQ,
            "following2921350 initialized default must publish actual selected numerical PC");
    Save(directory, "initialized-default", snapshot);
  }
  {
    Fixture f; f.memory.Put(f.living, 0x1EC, std::int32_t{0}); f.memory.Deny(f.living, 0x1E0, 8);
    const auto snapshot = f.Observe();
    Require(snapshot.ready && snapshot.following_2921350->ready && snapshot.following_2921350->title_walk.empty() &&
                snapshot.following_2921350->provinces.empty() && snapshot.following_2921350->manager.ready &&
                f.memory.Attempts() == 0, "following2921350 actual zero Title count must avoid array and still observe manager");
    Save(directory, "zero", snapshot);
  }
  {
    Fixture f; f.memory.Put(f.living, 0x1EC, std::int32_t{-1}); f.memory.Deny(f.living, 0x1E0, 8);
    const auto snapshot = f.Observe();
    Require(!snapshot.ready && !snapshot.following_2921350->ready &&
                snapshot.following_2921350->title_source.count_raw == -1 &&
                !snapshot.following_2921350->title_source.full_ids_u32 &&
                snapshot.following_2921350->title_walk.empty() && f.memory.Attempts() == 0,
            "following2921350 negative Title count is partial, never known empty");
    Save(directory, "negative-title-count", snapshot);
  }
  {
    Fixture f; f.memory.Deny(f.source_a, 0xC8, 8);
    const auto snapshot = f.Observe(); const auto &leaf = *snapshot.following_2921350;
    Require(!snapshot.ready && !leaf.ready && leaf.provinces.size() == 2 &&
                leaf.provinces[1].sources.size() == 3 &&
                !leaf.provinces[0].sources[0].map.ready && !leaf.provinces[0].sources[0].map.found &&
                !leaf.provinces[0].sources[0].map.operand_q64 && leaf.provinces[0].sources[2].tiers.ready &&
                f.memory.Attempts() > 0, "following2921350 unread map cannot become actual map-absent0");
    Save(directory, "partial-map", snapshot);
  }
  {
    Fixture f; f.memory.Put(f.manager_slot, 0, static_cast<void *>(nullptr));
    f.memory.Deny(f.province, 0x10, 4); f.memory.Deny(f.province, 0x7B4, 4);
    const auto snapshot = f.Observe(); const auto &leaf = *snapshot.following_2921350;
    Require(!snapshot.ready && !leaf.ready && leaf.manager.loaded == false && !leaf.manager.group_count_raw_i32 &&
                leaf.provinces.size() == 2 && leaf.provinces[0].sources.empty() && f.memory.Attempts() == 0,
            "following2921350 unloaded manager must not fabricate zero groups or demand numeric sources");
    Save(directory, "manager-unloaded", snapshot);
  }
  {
    Fixture f; f.memory.Put(f.title_root, 0x10, std::uint32_t{0xAA000001U});
    const auto snapshot = f.Observe(); const auto &leaf = *snapshot.following_2921350;
    Require(snapshot.ready && leaf.ready && leaf.title_walk.size() == 1 &&
                leaf.title_walk[0].requested_full_id_u32 == kTitleRoot &&
                leaf.title_walk[0].selection == "native_fallback" &&
                !leaf.title_walk[0].selected_full_id_u32 && leaf.provinces.size() == 1,
            "following2921350 full-generation miss must use actual native fallback Title pointer");
    Save(directory, "generation-fallback", snapshot);
  }
  {
    Fixture f; f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    const auto snapshot = f.Observe(); const auto &leaf = *snapshot.following_2921350;
    Require(snapshot.ready && leaf.ready && leaf.title_source.carrier_present == false &&
                leaf.title_source.selection == "actual_default_5459c88" &&
                leaf.title_source.count_raw == 1 && leaf.provinces.size() == 2,
            "following2921350 absent carrier must read actual default Title header, not assume empty");
    Save(directory, "actual-default-header", snapshot);
  }
}
} // namespace
void RunFollowing2921350Fixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}
