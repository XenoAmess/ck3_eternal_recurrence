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
#include <optional>
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
    for (const auto &interval : denied) count += interval.attempts;
    return count;
  }
  std::size_t MissingAttempts() const {
    std::size_t count = 0;
    for (const auto &interval : unavailable) count += interval.attempts;
    return count;
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    const auto overlaps = [begin, size](const Interval &interval) {
      return begin < interval.address + interval.size && interval.address < begin + size;
    };
    for (auto &interval : memory.denied) {
      if (overlaps(interval)) { ++interval.attempts; return false; }
    }
    for (auto &interval : memory.unavailable) {
      if (overlaps(interval)) { ++interval.attempts; return false; }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.bytes.get());
      if (begin >= base && begin - base <= region.size &&
          size <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, address, size);
        return true;
      }
    }
    return false;
  }
};
void *At(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}
using Snapshot = xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1;
constexpr std::uint32_t kAccoladeA = 0xAA000001U;
constexpr std::uint32_t kAccoladeB = 0xBB000002U;

// Source bytes are fixed and zero-initialized before observation. Deliberate
// missing reads are distinct from forbidden reads of unused numeric fields.
// The whole production DTO is compared twice and serialized without a wrapper.
struct Fixture {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *list_component = memory.Allocate(0x60);
  void *own_component = memory.Allocate(0x580);
  void *list_ids = memory.Allocate(2 * 4);
  void *storage_slot = memory.Allocate(8);
  void *fallback_slot = memory.Allocate(8);
  void *store = memory.Allocate(0x30);
  void *table = memory.Allocate(3 * 16);
  void *accolade_a = memory.Allocate(0x68);
  void *accolade_b = memory.Allocate(0x68);
  void *attributes_a = memory.Allocate(3 * 0x18);
  void *attributes_b = memory.Allocate(2 * 0x18);
  void *definition_a = memory.Allocate(0x3D0);
  void *definition_b = memory.Allocate(0x3D0);
  void *definition_c = memory.Allocate(0x3D0);
  void *definition_d = memory.Allocate(0x3D0);
  void *ranked_a = memory.Allocate(2 * 0x5F8);
  void *ranked_b = memory.Allocate(2 * 0x5F8);
  void *list_default_header = memory.Allocate(0x18);
  void *list_default_guard = memory.Allocate(4);
  void *ranked_default_row = memory.Allocate(0x5F8);
  void *ranked_default_guard = memory.Allocate(4);

  void Property(void *pc, const std::vector<std::uint16_t> &keys,
                const std::vector<std::int64_t> &values) {
    Require(keys.size() == values.size(), "following2920b50 property pair size");
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
  void PC(void *address, std::size_t offset, std::uint16_t key, std::int64_t value) {
    Property(At(address, offset), {key}, {value});
  }
  void Attribute(void *array, std::size_t index, std::int32_t rank, void *definition) {
    memory.Put(array, index * 0x18 + 8, rank);
    memory.Put(array, index * 0x18 + 0x10, definition);
  }
  Fixture() {
    bindings.enabled = true;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.following_2920b50;
    b.enabled = true;
    b.accolade_storage_slot = storage_slot;
    b.accolade_fallback_slot = fallback_slot;
    b.list_default_header = list_default_header;
    b.list_default_guard_slot = list_default_guard;
    b.ranked_default_row = ranked_default_row;
    b.ranked_default_guard_slot = ranked_default_guard;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(character, 0x1C8, list_component);
    memory.Put(character, 0x1B0, own_component);
    memory.Put(list_component, 0x50, list_ids);
    memory.Put(list_component, 0x5C, std::int32_t{2});
    memory.Put(list_ids, 0, kAccoladeA);
    memory.Put(list_ids, 4, kAccoladeA);
    memory.Put(own_component, 0x570, kAccoladeB);
    memory.Put(storage_slot, 0, store);
    memory.Put(fallback_slot, 0, accolade_a);
    memory.Put(store, 0x20, table);
    memory.Put(store, 0x2C, std::uint32_t{3});
    memory.Put(table, 16 + 8, accolade_a);
    memory.Put(table, 2 * 16 + 8, accolade_b);
    memory.Put(accolade_a, 8, kAccoladeA);
    // The first family does not gate on Acco magic.
    memory.Put(accolade_a, 0xC, std::uint32_t{0});
    memory.Put(accolade_b, 8, kAccoladeB);
    memory.Put(accolade_b, 0xC, std::uint32_t{0x4163636FU});
    memory.Put(accolade_a, 0x58, attributes_a);
    memory.Put(accolade_a, 0x64, std::int32_t{3});
    memory.Put(accolade_b, 0x58, attributes_b);
    memory.Put(accolade_b, 0x64, std::int32_t{2});
    for (void *definition : {definition_a, definition_b, definition_c, definition_d})
      memory.Put(definition, 0x38, std::uint32_t{0x4744624FU});
    memory.Put(definition_a, 0x3C0, ranked_a);
    memory.Put(definition_a, 0x3CC, std::int32_t{2});
    memory.Put(definition_b, 0x3C0, ranked_b);
    memory.Put(definition_b, 0x3CC, std::int32_t{2});
    Attribute(attributes_a, 0, 1, definition_a);
    Attribute(attributes_a, 1, 2, definition_b);
    Attribute(attributes_a, 2, 1, definition_a);
    Attribute(attributes_b, 0, 2, definition_a);
    Attribute(attributes_b, 1, 1, definition_b);
    PC(ranked_a, 0x10, 11, 1100);
    PC(ranked_a, 0x5F8 + 0x10, 12, 1200);
    PC(ranked_a, 0x1D0, 21, 2100);
    PC(ranked_a, 0x5F8 + 0x1D0, 22, 2200);
    PC(ranked_b, 0x10, 13, 1300);
    PC(ranked_b, 0x5F8 + 0x10, 14, 1400);
    PC(ranked_b, 0x1D0, 23, 2300);
    PC(ranked_b, 0x5F8 + 0x1D0, 24, 2400);
    memory.Put(list_default_header, 0, list_ids);
    memory.Put(list_default_header, 0xC, std::int32_t{2});
    memory.Put(list_default_guard, 0, std::int32_t{9});
    memory.Put(ranked_default_guard, 0, std::int32_t{9});
    PC(ranked_default_row, 0x10, 99, 9900);
    PC(ranked_default_row, 0x1D0, 98, 9800);

    // Actual empty headers for the existing always-collected source leaves.
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
  Snapshot Observe() {
    Require(bindings.enabled && bindings.following_2920b50.enabled,
            "following2920b50 source binding disabled");
    Require(!bindings.gated_temporary_tail.enabled && !bindings.after_gated_tail.enabled &&
                !bindings.provider192_and2920850.enabled &&
                !bindings.pre_291e210_1640_enabled && !bindings.later_direct_enabled &&
                !bindings.helper_291f0a0_enabled && !bindings.remaining_helpers_enabled &&
                !bindings.tail_direct_enabled && !bindings.post_291d7e0_sources_enabled &&
                !bindings.trait_stage.enabled && !bindings.middle_helpers.enabled &&
                !bindings.tail_prefix_enabled && !bindings.helper_2922070_enabled,
            "other optional source leaf enabled");
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "following2920b50 fixture must not install native callbacks");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first == second, "following2920b50 whole snapshots differ in fixed frame");
    Require(first.following_2920b50.has_value(), "following2920b50 source leaf absent");
    Require(memory.Attempts() == 0, "following2920b50 unused numeric operands were demanded");
    return first;
  }
  void DenyListRanks() {
    for (std::size_t i = 0; i < 3; ++i) memory.Deny(attributes_a, i * 0x18 + 8, 4);
  }
};
void Save(const std::filesystem::path &directory, const char *name,
          const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("following2920b50-") + name + ".json"),
                       std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("following2920b50 wire write failed");
}
void PCValue(const auto &pc, std::uint16_t key, std::int64_t value) {
  Require(pc.property_identity && pc.property_block && pc.property_block->keys_u16 &&
              pc.property_block->values_q64 && pc.property_block->keys_u16->size() == 1 &&
              pc.property_block->values_q64->size() == 1 &&
              pc.property_block->keys_u16->at(0) == key &&
              pc.property_block->values_q64->at(0) == value,
          "following2920b50 raw paired property differs");
}
void EmptyPC(const auto &pc) {
  Require(pc.property_identity && pc.property_block && pc.property_block->keys_count == 0 &&
              !pc.property_block->values_count && pc.property_block->keys_u16 &&
              pc.property_block->keys_u16->empty() && pc.property_block->values_q64 &&
              pc.property_block->values_q64->empty(),
          "following2920b50 empty PC must retain source occurrence without value demand");
}
void OwnIndexed(const auto &leaf) {
  const auto &own = leaf.own_1b0_570;
  const auto &occurrence = own.occurrence;
  Require(own.ready && own.component_present == true && occurrence.ready &&
              occurrence.resolution_selection == "registry_full_id_8" &&
              occurrence.requested_full_id_raw == static_cast<std::int32_t>(kAccoladeB) &&
              occurrence.accolade_magic_u32 == 0x4163636FU &&
              occurrence.accolade_full_id_raw == static_cast<std::int32_t>(kAccoladeB) &&
              occurrence.admitted == true && occurrence.preflight_ready &&
              occurrence.preflight_all_valid == true && occurrence.attributes &&
              occurrence.attributes->size() == 2,
          "following2920b50 own generation/preflight differs");
  const auto &a = occurrence.attributes->at(0);
  const auto &b = occurrence.attributes->at(1);
  Require(a.ready && b.ready && a.rank_raw_i32 == 2 && a.index_raw_i32 == 1 &&
              b.rank_raw_i32 == 1 && b.index_raw_i32 == 0 &&
              a.selection == "indexed_ranked_row" && b.selection == "indexed_ranked_row" &&
              !a.ranked_default_init_guard_raw && !b.ranked_default_init_guard_raw,
          "following2920b50 own rank must select actual peer PC without default demand");
  PCValue(a.pc, 22, 2200);
  PCValue(b.pc, 23, 2300);
}
void NoNumericPreflight(const auto &occurrence, bool invalid) {
  Require(occurrence.attributes && occurrence.attributes->size() == 2 &&
              occurrence.preflight_all_valid == (invalid ? std::optional<bool>{false}
                                                        : std::optional<bool>{}) &&
              occurrence.preflight_ready == invalid && occurrence.ready == invalid,
          "following2920b50 preflight prefix or availability differs");
  for (const auto &attribute : *occurrence.attributes) {
    Require(!attribute.ready && !attribute.rank_raw_i32 && !attribute.index_raw_i32 &&
                !attribute.ranked_count_raw && !attribute.ranked_array_present &&
                !attribute.selection && !attribute.ranked_default_init_guard_raw &&
                !attribute.pc.property_block && !attribute.pc.property_identity,
            "following2920b50 incomplete preflight leaked numeric attribute inputs");
  }
  Require(occurrence.attributes->at(0).preflight_valid == true &&
              occurrence.attributes->at(0).reason.empty(),
          "following2920b50 first valid preflight row differs");
  if (invalid)
    Require(occurrence.attributes->at(1).preflight_valid == false &&
                occurrence.attributes->at(1).reason.empty(),
            "following2920b50 observed invalid must be known whole-occurrence skip");
  else
    Require(!occurrence.attributes->at(1).preflight_valid &&
                !occurrence.attributes->at(1).definition_magic_u32 &&
                !occurrence.attributes->at(1).reason.empty(),
            "following2920b50 unread magic must block all numeric attributes");
}
void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  const auto &b = bindings.following_2920b50;
  const auto address = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  Require(bindings.enabled && b.enabled && b.accolade_storage_slot == address(0x5D1ECA0) &&
              b.accolade_fallback_slot == address(0x5D1EC40) &&
              b.list_default_header == address(0x5D67E80) &&
              b.list_default_guard_slot == address(0x5D67E78) &&
              b.ranked_default_row == address(0x5D68FB0) &&
              b.ranked_default_guard_slot == address(0x5D68FA8),
          "following2920b50 exact-build bindings differ");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "wrong-build").following_2920b50.enabled,
          "following2920b50 exact-build factory accepted wrong build");
}
void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture f;
    f.memory.Deny(f.list_default_guard, 0, 4);
    f.memory.Deny(f.ranked_default_guard, 0, 4);
    f.memory.Deny(f.ranked_default_row, 0, 0x5F8);
    f.memory.Deny(f.accolade_a, 0xC, 4);
    f.memory.Deny(f.ranked_a, 0x1D0, 0x78);
    f.memory.Deny(f.ranked_a, 0x5F8 + 0x10, 0x78);
    f.memory.Deny(f.ranked_b, 0x10, 0x78);
    f.memory.Deny(f.ranked_b, 0x5F8 + 0x1D0, 0x78);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2920b50;
    const auto &list = leaf.list_1c8_50;
    Require(snapshot.ready && leaf.ready && list.ready && list.component_present == true &&
                list.header_selection == "current_1c8_50" && list.count_raw == 2 &&
                list.rows && list.rows->size() == 2,
            "following2920b50 indexed physical duplicate list differs");
    for (std::size_t i = 0; i < 2; ++i) {
      const auto &occurrence = list.rows->at(i);
      Require(occurrence.native_index == static_cast<std::int32_t>(i) && occurrence.ready &&
                  occurrence.requested_full_id_raw == static_cast<std::int32_t>(kAccoladeA) &&
                  occurrence.selected_full_id_raw == static_cast<std::int32_t>(kAccoladeA) &&
                  occurrence.object_identity == list.rows->at(0).object_identity &&
                  occurrence.admitted == true && !occurrence.accolade_magic_u32 &&
                  !occurrence.accolade_full_id_raw && occurrence.preflight_ready &&
                  occurrence.preflight_all_valid == true && occurrence.attributes &&
                  occurrence.attributes->size() == 3,
              "following2920b50 list resolution must not add own Acco admission");
      for (std::size_t j = 0; j < 3; ++j) {
        const auto &attribute = occurrence.attributes->at(j);
        Require(attribute.ready && attribute.native_index == static_cast<std::int32_t>(j) &&
                    attribute.preflight_valid == true &&
                    attribute.selection == "indexed_ranked_row" &&
                    !attribute.ranked_default_init_guard_raw,
                "following2920b50 indexed attribute ordinal or default demand differs");
      }
      PCValue(occurrence.attributes->at(0).pc, 11, 1100);
      PCValue(occurrence.attributes->at(1).pc, 14, 1400);
      PCValue(occurrence.attributes->at(2).pc, 11, 1100);
      Require(occurrence.attributes->at(0).pc.property_identity ==
                  occurrence.attributes->at(2).pc.property_identity,
              "following2920b50 repeated attribute PC identity lost");
    }
    OwnIndexed(leaf);
    Save(directory, "indexed-duplicates", snapshot);
  }
  {
    Fixture f;
    f.Attribute(f.attributes_a, 1, 2, f.definition_c);
    f.memory.Put(f.definition_c, 0x38, std::uint32_t{0});
    f.DenyListRanks();
    f.memory.Deny(f.attributes_a, 2 * 0x18 + 0x10, 8);
    f.memory.Deny(f.ranked_default_guard, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2920b50;
    Require(snapshot.ready && leaf.ready && leaf.list_1c8_50.ready &&
                leaf.list_1c8_50.rows && leaf.list_1c8_50.rows->size() == 2,
            "following2920b50 invalid preflight must produce known whole-list-occurrence skips");
    for (const auto &occurrence : *leaf.list_1c8_50.rows) NoNumericPreflight(occurrence, true);
    OwnIndexed(leaf);
    Save(directory, "preflight-invalid-whole", snapshot);
  }
  {
    Fixture f;
    f.Attribute(f.attributes_a, 1, 2, f.definition_c);
    f.memory.Hide(f.definition_c, 0x38, 4);
    f.DenyListRanks();
    f.memory.Deny(f.attributes_a, 2 * 0x18 + 0x10, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2920b50;
    Require(!snapshot.ready && !leaf.ready && !leaf.list_1c8_50.ready &&
                leaf.list_1c8_50.rows && leaf.list_1c8_50.rows->size() == 2 &&
                f.memory.MissingAttempts() > 0,
            "following2920b50 unknown preflight must preserve other family and block whole occurrence");
    for (const auto &occurrence : *leaf.list_1c8_50.rows) NoNumericPreflight(occurrence, false);
    OwnIndexed(leaf);
    Save(directory, "preflight-unknown-whole", snapshot);
  }
  {
    Fixture f;
    f.Attribute(f.attributes_a, 0, 0, f.definition_c);
    f.memory.Put(f.ranked_default_guard, 0, std::int32_t{0});
    f.memory.Deny(f.definition_c, 0x3C0, 8);
    f.memory.Deny(f.definition_c, 0x3CC, 4);
    f.memory.Deny(f.ranked_default_row, 0, 0x5F8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2920b50;
    Require(!snapshot.ready && !leaf.ready && !leaf.list_1c8_50.ready &&
                leaf.list_1c8_50.rows && leaf.list_1c8_50.rows->size() == 2,
            "following2920b50 cold default must retain partial attribute requests");
    for (const auto &occurrence : *leaf.list_1c8_50.rows) {
      Require(occurrence.preflight_ready && occurrence.preflight_all_valid == true &&
                  occurrence.attributes && occurrence.attributes->size() == 3,
              "following2920b50 complete preflight must preserve independent indexed attributes");
      const auto &cold = occurrence.attributes->at(0);
      Require(!cold.ready && cold.rank_raw_i32 == 0 && cold.index_raw_i32 == -1 &&
                  !cold.ranked_count_raw && !cold.ranked_array_present &&
                  cold.selection == "uninitialized_default_5d68fb0" &&
                  cold.ranked_default_init_guard_raw == 0 &&
                  cold.reason == "ranked_default_initialization_result" &&
                  !cold.pc.property_block && !cold.pc.property_identity,
              "following2920b50 negative index must expose precise cold default without header/PC demand");
      Require(occurrence.attributes->at(1).ready && occurrence.attributes->at(2).ready,
              "following2920b50 cold default hid complete indexed attributes");
      PCValue(occurrence.attributes->at(1).pc, 14, 1400);
      PCValue(occurrence.attributes->at(2).pc, 11, 1100);
    }
    OwnIndexed(leaf);
    Save(directory, "cold-ranked-default-partial", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.list_component, 0x5C, std::int32_t{1});
    f.Attribute(f.attributes_a, 0, std::numeric_limits<std::int32_t>::min(), f.definition_c);
    f.Attribute(f.attributes_a, 2, 0, f.definition_d);
    f.memory.Put(f.definition_c, 0x3CC, std::int32_t{-3});
    f.memory.Deny(f.definition_c, 0x3C0, 8);
    f.memory.Deny(f.definition_d, 0x3C0, 8);
    f.memory.Deny(f.definition_d, 0x3CC, 4);
    f.Property(At(f.ranked_default_row, 0x10), {}, {});
    f.memory.Deny(f.ranked_default_row, 0x10, 8);
    f.memory.Deny(f.ranked_default_row, 0x10 + 0x68, 8);
    f.memory.Deny(f.ranked_default_row, 0x10 + 0x74, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2920b50;
    Require(snapshot.ready && leaf.ready && leaf.list_1c8_50.rows &&
                leaf.list_1c8_50.rows->size() == 1 &&
                leaf.list_1c8_50.rows->at(0).attributes &&
                leaf.list_1c8_50.rows->at(0).attributes->size() == 3,
            "following2920b50 initialized default occurrence differs");
    const auto &attributes = *leaf.list_1c8_50.rows->at(0).attributes;
    Require(attributes.at(0).ready && attributes.at(2).ready &&
                attributes.at(0).rank_raw_i32 == std::numeric_limits<std::int32_t>::min() &&
                attributes.at(0).index_raw_i32 == std::numeric_limits<std::int32_t>::max() &&
                attributes.at(0).ranked_count_raw == -3 && !attributes.at(0).ranked_array_present &&
                attributes.at(2).index_raw_i32 == -1 && !attributes.at(2).ranked_count_raw &&
                attributes.at(0).selection == "initialized_default_5d68fb0" &&
                attributes.at(2).selection == "initialized_default_5d68fb0" &&
                attributes.at(0).ranked_default_init_guard_raw == 9 &&
                attributes.at(2).ranked_default_init_guard_raw == 9 &&
                attributes.at(0).pc.property_identity == attributes.at(2).pc.property_identity,
            "following2920b50 wrap32/negative count/default selection differs");
    EmptyPC(attributes.at(0).pc);
    PCValue(attributes.at(1).pc, 14, 1400);
    EmptyPC(attributes.at(2).pc);
    OwnIndexed(leaf);
    Save(directory, "initialized-ranked-default-empty", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1C8, static_cast<void *>(nullptr));
    f.memory.Put(f.list_default_guard, 0, std::int32_t{0});
    f.memory.Put(f.storage_slot, 0, static_cast<void *>(nullptr));
    f.memory.Deny(f.list_default_header, 0, 0x18);
    f.memory.Deny(f.own_component, 0x570, 4);
    f.memory.Deny(f.accolade_a, 8, 4);
    f.memory.Deny(f.accolade_a, 0x58, 0x10);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.following_2920b50;
    const auto &list = leaf.list_1c8_50;
    const auto &own = leaf.own_1b0_570.occurrence;
    Require(snapshot.ready && leaf.ready && list.ready && list.component_present == false &&
                list.header_selection == "modeled_empty_default_5d67e80" &&
                list.default_init_guard_raw == 0 && list.numeric_count == 0 &&
                !list.count_raw && !list.array_present && list.rows && list.rows->empty() &&
                leaf.own_1b0_570.ready && own.ready && own.resolution_selection == "native_fallback" &&
                !own.requested_full_id_raw && !own.selected_full_id_raw &&
                own.accolade_magic_u32 == 0U && !own.accolade_full_id_raw && own.admitted == false &&
                !own.attribute_count_raw && !own.attribute_array_present && own.attributes &&
                own.attributes->empty() && own.preflight_ready && own.preflight_all_valid == false,
            "following2920b50 modeled empty list/own magic rejection must skip raw ID and attributes");
    Save(directory, "modeled-list-and-own-magic-skip", snapshot);
  }
}
} // namespace

void RunFollowing2920b50Fixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}
