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
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
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
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &entry : memory.denied) {
      if (begin < entry.address + entry.size && entry.address < begin + size) {
        ++entry.attempts;
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.data.get());
      if (begin >= base && begin - base <= region.size &&
          size <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, address, size);
        return true;
      }
    }
    return false;
  }
};
void *At(void *base, std::size_t offset) {
  return static_cast<std::byte *>(base) + offset;
}
using Snapshot = xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1;

// All bytes are initialized before observation. Two reads use one unchanged
// frame, including actual empty source fields and other serialized branches.
struct Fixture {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *land = memory.Allocate(0x460);
  void *selected = memory.Allocate(0x120);
  void *global = memory.Allocate(0x2B8);
  void *provider = memory.Allocate(0x14C0);
  void *db = memory.Allocate(0xF00);
  void *entries = memory.Allocate(0x178);
  void *entry168 = memory.Allocate(0x80);
  void *entry170 = memory.Allocate(0x80);
  void *definition_a = memory.Allocate(0xC0);
  void *definition_b = memory.Allocate(0xC0);
  void *bad_definition = memory.Allocate(0xC0);
  void *prefix_a_rows = memory.Allocate(3 * 8);
  void *prefix_b_rows = memory.Allocate(3 * 8);
  void *list_object = memory.Allocate(0xC60);
  void *list_rows = memory.Allocate(2 * 8);
  void *thresholds = memory.Allocate(2 * 8);
  void *global_slot = memory.Allocate(8);
  void *provider_slot = memory.Allocate(8);
  void *named_slot = memory.Allocate(8);
  void *selector_global_slot = memory.Allocate(4);
  void *minimum_slot = memory.Allocate(8);
  void *maximum_slot = memory.Allocate(8);
  void *threshold_pointer_slot = memory.Allocate(8);
  void *threshold_count_slot = memory.Allocate(4);
  void *character_storage_slot = memory.Allocate(8);
  void *character_fallback_slot = memory.Allocate(8);

  void Property(void *pc, const std::vector<std::uint16_t> &keys,
                const std::vector<std::int64_t> &values) {
    Require(keys.size() == values.size(), "fixture property pair length");
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
  Fixture() {
    bindings.enabled = true;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    auto &g = bindings.gated_temporary_tail;
    g.enabled = true;
    g.global_flag_slot = global_slot;
    g.provider_slot = provider_slot;
    g.named_db_slot = named_slot;
    g.selector_global_slot = selector_global_slot;
    g.minimum_slot = minimum_slot;
    g.maximum_slot = maximum_slot;
    g.threshold_pointer_slot = threshold_pointer_slot;
    g.threshold_count_slot = threshold_count_slot;
    g.character_storage_slot = character_storage_slot;
    g.character_fallback_slot = character_fallback_slot;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(character, 0x1C0, land);
    memory.Put(land, 0x458, selected);
    memory.Put(global_slot, 0, global);
    memory.Put(global, 0x2B0, std::uint8_t{0x20});
    memory.Put(provider_slot, 0, provider);
    memory.Put(selected, 0xEC, std::int32_t{42});
    memory.Put(selector_global_slot, 0, std::int32_t{42});
    memory.Put(selected, 0xE8, std::int32_t{99});
    memory.Put(selected, 0xF8, std::int32_t{1});
    memory.Put(selected, 0xFC, std::int32_t{99});
    memory.Put(named_slot, 0, db);
    memory.Put(db, 0xEF0, entries);
    memory.Put(entries, 0x168, entry168);
    memory.Put(entries, 0x170, entry170);
    memory.Put(entry168, 0x7B, std::uint8_t{3});
    memory.Put(entry168, 0x68, std::int64_t{-50000});
    memory.Put(entry170, 0x7B, std::uint8_t{2});
    memory.Put(entry170, 0x68, std::int64_t{-250000});
    memory.Put(minimum_slot, 0, std::int64_t{0});
    memory.Put(maximum_slot, 0, std::int64_t{300000});
    memory.Put(threshold_pointer_slot, 0, thresholds);
    memory.Put(threshold_count_slot, 0, std::int32_t{2});
    memory.Put(thresholds, 0, std::int64_t{0});
    memory.Put(thresholds, 8, std::int64_t{100000});
    memory.Put(definition_a, 0x38, std::uint32_t{0x4744624F});
    memory.Put(definition_b, 0x38, std::uint32_t{0x4744624F});
    Property(At(definition_a, 0x40), {1, 0xFFFF}, {100000, -200000});
    Property(At(definition_b, 0x40), {2, 0xFFFF}, {-100000, 0});
    for (std::size_t i = 0; i < 3; ++i) {
      memory.Put(prefix_a_rows, i * 8, definition_a);
      memory.Put(prefix_b_rows, i * 8, definition_b);
    }
    memory.Put(provider, 0x1398, prefix_a_rows);
    memory.Put(provider, 0x1398 + 0xC, std::int32_t{3});
    memory.Put(provider, 0x1420, prefix_b_rows);
    memory.Put(provider, 0x1420 + 0xC, std::int32_t{3});
    memory.Put(provider, 0x14A8, prefix_b_rows);
    memory.Put(provider, 0x14A8 + 0xC, std::int32_t{3});
    Property(At(list_object, 0xA20), {3}, {0});
    Property(At(list_object, 0xBE0), {4}, {-700000});
    memory.Put(list_rows, 0, list_object);
    memory.Put(list_rows, 8, list_object);
    memory.Put(selected, 0x108, list_rows);
    memory.Put(selected, 0x114, std::int32_t{2});

    // Existing always-collected source branches have current empty headers.
    void *carrier = memory.Allocate(0x230);
    memory.Put(character, 0x1B0, carrier);
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
    memory.Deny(selected, 0xFC, 4);
    memory.Deny(selected, 0xE8, 4);
  }
  Snapshot Observe() {
    Require(bindings.enabled && bindings.gated_temporary_tail.enabled,
            "gated temporary source binding disabled");
    Require(!bindings.pre_291e210_1640_enabled && !bindings.later_direct_enabled &&
                !bindings.helper_291f0a0_enabled && !bindings.remaining_helpers_enabled &&
                !bindings.tail_direct_enabled && !bindings.post_291d7e0_sources_enabled,
            "other optional source leaf enabled");
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "gated fixture must not install native callbacks");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first == second, "gated whole source snapshots differ in fixed frame");
    Require(first.gated_temporary_tail_291c7a7.has_value(), "gated source leaf absent");
    Require(memory.Attempts() == 0, "gated skipped operands were demanded");
    return first;
  }
};
void Save(const std::filesystem::path &directory, const char *name, const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("gated-temporary-") + name + ".json"),
                       std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("gated temporary wire write failed");
}
void Prefix(const xar::game::ContextSourceGatedPrefixV1 &p, std::int32_t count,
            std::uint16_t key, std::int64_t value) {
  Require(p.ready && p.rows && p.rows->size() == static_cast<std::size_t>(count),
          "gated prefix occurrence count differs");
  for (std::int32_t i = 0; i < count; ++i) {
    const auto &row = p.rows->at(static_cast<std::size_t>(i));
    Require(row.native_index == i && row.admitted == true && row.property_block &&
                row.property_block->keys_u16 && row.property_block->values_q64 &&
                row.property_block->keys_u16->at(0) == key &&
                row.property_block->values_q64->at(0) == value,
            "gated prefix raw property operands differ");
    Require(row.definition_identity == p.rows->at(0).definition_identity &&
                row.property_identity == p.rows->at(0).property_identity,
            "gated prefix duplicated pointers lost identity");
  }
}
void List(const xar::game::ContextSourceGatedListV1 &list,
          const char *selection, std::uint16_t key, std::int64_t value) {
  Require(list.ready && list.selection == selection && list.count_raw == 2 &&
              list.rows && list.rows->size() == 2,
          "gated selected list occurrence count differs");
  for (std::size_t i = 0; i < 2; ++i) {
    const auto &row = list.rows->at(i);
    Require(row.native_index == static_cast<std::int32_t>(i) && row.property_block &&
                row.property_block->keys_u16 && row.property_block->values_q64 &&
                row.property_block->keys_u16->at(0) == key &&
                row.property_block->values_q64->at(0) == value &&
                row.property_identity == list.rows->at(0).property_identity,
            "gated selected list duplicate raw property bytes differ");
  }
}
void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  const auto &g = b.gated_temporary_tail;
  const auto address = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  Require(b.enabled && g.enabled && g.global_flag_slot == address(0x5CB87F8) &&
              g.provider_slot == address(0x5C670F8) &&
              g.selector_global_slot == address(0x5C82C68) &&
              g.named_db_slot == address(0x5D1DD50) &&
              g.minimum_slot == address(0x5C68FF0) && g.maximum_slot == address(0x5C68D10) &&
              g.threshold_pointer_slot == address(0x5456EA8) &&
              g.threshold_count_slot == address(0x5456EB4) &&
              g.character_storage_slot == address(0x5C67568) &&
              g.character_fallback_slot == address(0x5C67570),
          "gated temporary exact-build raw bindings differ");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "wrong-build").gated_temporary_tail.enabled,
          "outer exact-build factory accepted wrong build");
}
void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture f;
    f.memory.Deny(f.maximum_slot, 0, 8);
    f.memory.Deny(f.thresholds, 8, 8);
    f.memory.Deny(f.prefix_a_rows, 16, 8);
    f.memory.Deny(f.prefix_b_rows, 16, 8);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    Require(snapshot.ready && p.ready && p.temporary_admitted == true &&
                p.selected_f8_raw == 1 && !p.selected_e8_raw &&
                p.refresh_168.source.kind == "literal" &&
                p.refresh_168.source.fixed_flag_u8 == std::uint8_t{3} &&
                p.refresh_168.source.raw_fixed_q64 == -50000 &&
                p.refresh_168.clamped_q64 == 0 && !p.refresh_168.maximum_q64 &&
                p.refresh_168.fresh_rank_raw == 0 &&
                p.refresh_168.thresholds_consumed_q64 &&
                p.refresh_168.thresholds_consumed_q64->size() == 1 &&
                p.delta_prefix_1420_14a8.delta_raw == 1 &&
                p.delta_prefix_1420_14a8.weight_source.kind == "literal" &&
                p.delta_prefix_1420_14a8.weight_source.value_q64 == -250000,
            "gated literal/clamp/fresh rank/negative inner weight differs");
    Prefix(p.prefix_1398, 2, 1, 100000);
    Prefix(p.delta_prefix_1420_14a8.prefix, 2, 2, -100000);
    Require(p.prefix_1398.rows->at(0).property_block->keys_u16->at(1) == std::uint16_t{0xFFFF} &&
                p.prefix_1398.rows->at(0).property_block->values_q64->at(1) == -200000 &&
                p.delta_prefix_1420_14a8.prefix.rows->at(0).property_block->values_q64->at(1) == 0,
            "gated raw FFFF/zero/negative operands lost");
    List(p.list, "current_A20", 3, 0);
    Save(directory, "full-literal", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.global, 0x2B0, std::uint8_t{0});
    f.memory.Deny(f.character, 0x1C0, 8);
    f.memory.Deny(f.named_slot, 0, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    f.memory.Deny(f.selector_global_slot, 0, 4);
    f.memory.Deny(f.character_storage_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    Require(snapshot.ready && p.ready && p.global_bit20 == false &&
                p.temporary_admitted == false && !p.current_land_present &&
                !p.current_selected_present && p.prefix_1398.ready &&
                p.prefix_1398.rows && p.prefix_1398.rows->empty() &&
                p.delta_prefix_1420_14a8.ready && p.list.ready &&
                p.list.selection == "skipped_bit20" && p.list.rows && p.list.rows->empty() &&
                p.refresh_168.source.kind == "unconsumed",
            "false bit20 must yield known zero without other source reads");
    Save(directory, "bit20-zero", snapshot);
  }
  {
    Fixture f;
    void *tree = f.memory.Allocate(8);
    f.memory.Put(f.entry168, 0x70, tree);
    f.memory.Deny(f.entry168, 0x7B, 1);
    f.memory.Deny(f.entry168, 0x68, 8);
    f.memory.Deny(f.entries, 0x170, 8);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    Require(!snapshot.ready && !p.ready && p.prefix_1398.ready && p.list.ready &&
                !p.refresh_168.ready && !p.delta_prefix_1420_14a8.ready &&
                p.refresh_168.source.kind == "dynamic_tree_requires_current_result" &&
                p.refresh_168.source.tree_present == true &&
                !p.refresh_168.source.fixed_flag_u8 && !p.refresh_168.source.raw_fixed_q64 &&
                !p.refresh_168.fresh_rank_raw &&
                p.delta_prefix_1420_14a8.weight_source.kind == "unconsumed",
            "dynamic168 must preserve independent prefix/list and avoid fixed operands");
    Prefix(p.prefix_1398, 2, 1, 100000);
    List(p.list, "current_A20", 3, 0);
    Save(directory, "dynamic168", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.entry168, 0x7B, std::uint8_t{0});
    f.memory.Put(f.entry170, 0x7B, std::uint8_t{0});
    f.memory.Deny(f.entry168, 0x68, 8);
    f.memory.Deny(f.entry170, 0x68, 8);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    Require(snapshot.ready && p.ready && p.refresh_168.source.kind == "known_zero" &&
                p.refresh_168.source.value_q64 == 0 && !p.refresh_168.source.raw_fixed_q64 &&
                p.delta_prefix_1420_14a8.weight_source.kind == "known_zero" &&
                p.delta_prefix_1420_14a8.weight_source.value_q64 == 0 &&
                !p.delta_prefix_1420_14a8.weight_source.raw_fixed_q64,
            "null tree/zero flags must be known raw zero without68 reads");
    Save(directory, "known-zero-sources", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.selected, 0xF8, std::int32_t{0});
    f.memory.Deny(f.entries, 0x170, 8);
    f.memory.Deny(f.provider, 0x1420, 0x10);
    f.memory.Deny(f.provider, 0x14A8, 0x10);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    const auto &delta = p.delta_prefix_1420_14a8;
    Require(snapshot.ready && p.ready && p.temporary_admitted == true &&
                delta.ready && delta.delta_raw == 0 && delta.header_selection == "zero_delta" &&
                delta.prefix.ready && delta.prefix.rows && delta.prefix.rows->empty() &&
                delta.weight_source.kind == "unconsumed",
            "zero delta must retain second empty request without170/header demand");
    Prefix(p.prefix_1398, 1, 1, 100000);
    Save(directory, "delta-zero", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.selected, 0xF8, std::numeric_limits<std::int32_t>::max());
    f.memory.Deny(f.entries, 0x170, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    const auto &delta = p.delta_prefix_1420_14a8;
    Require(snapshot.ready && p.ready && p.temporary_admitted == true &&
                p.prefix_1398.native_prefix_count == std::numeric_limits<std::int32_t>::min() &&
                p.prefix_1398.rows && p.prefix_1398.rows->empty() &&
                !p.prefix_1398.header_count && !p.prefix_1398.array_present &&
                delta.ready && delta.delta_raw == std::numeric_limits<std::int32_t>::max() &&
                delta.prefix.native_prefix_count == std::numeric_limits<std::int32_t>::min() &&
                delta.prefix.rows && delta.prefix.rows->empty() &&
                !delta.prefix.header_count && !delta.prefix.array_present &&
                delta.weight_source.kind == "unconsumed",
            "wrapped bounds-empty prefixes must retain both outer requests, no170/array reads");
    Save(directory, "bounds-empty", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.selected, 0xF8, std::int32_t{-1});
    // Provider is actually unobserved, so a demanded positive delta prefix
    // remains partial. FE20 N0 is independently known empty before that read.
    f.bindings.gated_temporary_tail.provider_slot = nullptr;
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    Require(!snapshot.ready && !p.ready && p.prefix_1398.ready &&
                p.prefix_1398.selector_raw == -1 && p.prefix_1398.native_prefix_count == 0 &&
                !p.prefix_1398.header_count && !p.prefix_1398.array_present &&
                p.prefix_1398.rows && p.prefix_1398.rows->empty() &&
                !p.delta_prefix_1420_14a8.ready &&
                p.delta_prefix_1420_14a8.header_selection == "provider_14a8" &&
                p.delta_prefix_1420_14a8.weight_source.kind == "unconsumed" && p.list.ready,
            "N0 prefix must remain numeric-ready with unavailable provider");
    Save(directory, "nonpositive-no-provider", snapshot);
  }
  {
    Fixture f;
    constexpr std::uint32_t related_id = 0xAA000001U;
    f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    void *army = f.memory.Allocate(0xD0);
    void *related = f.memory.Allocate(0x1D8);
    void *related_land = f.memory.Allocate(0x460);
    void *related_selected = f.memory.Allocate(0x120);
    void *storage = f.memory.Allocate(0x30);
    void *table = f.memory.Allocate(3 * 16);
    f.memory.Put(f.character, 0x1B8, army);
    f.memory.Put(army, 0xCC, std::uint32_t{0xBB000005});
    f.memory.Put(army, 0xC8, related_id);
    f.memory.Put(f.character_storage_slot, 0, storage);
    f.memory.Put(storage, 0x20, table);
    f.memory.Put(storage, 0x2C, std::uint32_t{3});
    f.memory.Put(table, 16 + 8, related);
    f.memory.Put(related, 0x18, related_id);
    f.memory.Put(related, 0x1C, std::uint32_t{0x43686172});
    f.memory.Put(related, 0x1C0, related_land);
    f.memory.Put(related_land, 0x458, related_selected);
    f.memory.Put(related_selected, 0x108, f.list_rows);
    f.memory.Put(related_selected, 0x114, std::int32_t{2});
    f.memory.Deny(f.character_fallback_slot, 0, 8);
    f.memory.Deny(f.named_slot, 0, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    const auto &r = p.list.related;
    Require(snapshot.ready && p.ready && p.temporary_admitted == false &&
                r.attempts.size() == 2 && r.attempts[0].selection == "out_of_capacity" &&
                r.attempts[0].admitted == false && r.attempts[1].selection == "indexed_full_id" &&
                r.attempts[1].requested_full_id_raw == static_cast<std::int32_t>(related_id) &&
                r.helper_return_full_id_raw == static_cast<std::int32_t>(related_id) &&
                r.caller.requested_full_id_raw == static_cast<std::int32_t>(related_id) &&
                r.caller.selection == "indexed_full_id" && r.caller.admitted == true &&
                p.refresh_168.source.kind == "unconsumed",
            "related CC/C8 helper and caller generation resolutions differ");
    List(p.list, "related_BE0", 4, -700000);
    Save(directory, "related-be0-generation", snapshot);
  }
  {
    Fixture f;
    // A valid prefix with actual empty PCs has a known empty numeric result,
    // independently of the native evaluator activity which is not executed.
    f.Property(At(f.definition_b, 0x40), {}, {});
    f.memory.Deny(f.entries, 0x170, 8);
    f.memory.Deny(f.definition_b, 0x40, 8);
    f.memory.Deny(f.definition_b, 0x40 + 0x68, 8);
    f.memory.Deny(f.definition_b, 0x40 + 0x74, 4);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    const auto &delta = p.delta_prefix_1420_14a8;
    Require(snapshot.ready && p.ready && delta.ready && delta.prefix.ready &&
                delta.prefix.native_prefix_count == 2 && delta.prefix.rows &&
                delta.prefix.rows->size() == 2 && delta.weight_source.kind == "unconsumed",
            "valid empty-key delta prefix must stay known empty without invented170 weight");
    for (const auto &row : *delta.prefix.rows)
      Require(row.admitted == true && row.property_block &&
                  row.property_block->keys_count == 0 && !row.property_block->values_count &&
                  row.property_block->keys_u16 && row.property_block->keys_u16->empty() &&
                  row.property_block->values_q64 && row.property_block->values_q64->empty(),
              "actual zero-key prefix PC must not demand value headers");
    Save(directory, "empty-key-prefix", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    void *invalid = f.memory.Allocate(0x1D8);
    f.memory.Put(f.character_fallback_slot, 0, invalid);
    f.memory.Deny(invalid, 0x18, 4);
    f.memory.Deny(f.named_slot, 0, 8);
    f.memory.Deny(f.provider_slot, 0, 8);
    const auto snapshot = f.Observe();
    const auto &p = *snapshot.gated_temporary_tail_291c7a7;
    Require(snapshot.ready && p.ready && p.list.selection == "related_skip" &&
                p.list.related.carrier_present == false && p.list.related.attempts.empty() &&
                p.list.related.helper_return_full_id_raw == -1 &&
                p.list.related.caller.selection == "native_fallback" &&
                p.list.related.caller.magic_raw == 0U &&
                p.list.related.caller.admitted == false && !p.list.related.caller.full_id_raw,
            "helper absent carrier must return minus-one then caller tests native fallback magic");
  }
  {
    Fixture f;
    f.memory.Put(f.prefix_a_rows, 8, f.bad_definition);
    f.memory.Deny(f.bad_definition, 0x40, 0x80);
    const auto snapshot = f.Observe();
    const auto &prefix = snapshot.gated_temporary_tail_291c7a7->prefix_1398;
    Require(snapshot.ready && prefix.ready && prefix.rows && prefix.rows->size() == 2 &&
                prefix.rows->at(1).magic_raw == 0U && prefix.rows->at(1).admitted == false &&
                !prefix.rows->at(1).property_identity && !prefix.rows->at(1).property_block,
            "wrong magic prefix row must not read properties");
  }
}
} // namespace

void RunGatedTemporaryTailFixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}
