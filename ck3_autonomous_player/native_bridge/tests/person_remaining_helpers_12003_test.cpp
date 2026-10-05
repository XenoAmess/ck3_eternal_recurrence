#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
void Require(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}

struct Memory {
  struct Region {
    std::unique_ptr<std::byte[]> data;
    std::size_t size;
  };
  struct Denied {
    std::uintptr_t begin;
    std::size_t size;
    std::size_t attempts = 0;
  };
  std::vector<Region> regions;
  std::vector<Denied> denied;

  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    void *address = data.get();
    regions.push_back({std::move(data), size});
    return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void Deny(const void *address, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset, size});
  }
  std::size_t Attempts() const {
    std::size_t result = 0;
    for (const auto &entry : denied) result += entry.attempts;
    return result;
  }
  static bool Read(void *context, const void *address, void *output,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &entry : memory.denied) {
      if (begin < entry.begin + entry.size && entry.begin < begin + size) {
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

void *At(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}

struct Fixture {
  static constexpr std::uint32_t culture_id = 0xAB000001U;
  static constexpr std::uint32_t first_rite_id = 0xCD000001U;
  static constexpr std::uint32_t second_rite_id = 0xDC000001U;
  static constexpr std::uint32_t selected_rite_id = 0xEF000002U;
  static constexpr std::uint32_t outer_first_id = 0x88000001U;
  static constexpr std::uint32_t outer_second_id = 0x99000002U;
  static constexpr std::uint32_t culture_map_id = 0xAA000031U;
  static constexpr std::uint32_t inner_map_id = 0xBB000041U;

  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *land = memory.Allocate(0x400);
  void *government = memory.Allocate(0x40);
  void *culture = memory.Allocate(0x678);
  void *first_rite = memory.Allocate(0x7B0);
  void *second_rite = memory.Allocate(0xA0);
  void *selected_rite = memory.Allocate(0x7B0);
  void *outer_first = memory.Allocate(0x30);
  void *outer_second = memory.Allocate(0x188);
  void *outer0 = memory.Allocate(0x460);
  void *outer1 = memory.Allocate(0x460);
  void *culture_storage_slot = memory.Allocate(8);
  void *culture_fallback_slot = memory.Allocate(8);
  void *rite_storage_slot = memory.Allocate(8);
  void *rite_fallback_slot = memory.Allocate(8);
  void *rite_second_storage_slot = memory.Allocate(8);
  void *rite_second_fallback_slot = memory.Allocate(8);
  void *outer_first_storage_slot = memory.Allocate(8);
  void *outer_first_fallback_slot = memory.Allocate(8);
  void *outer_second_storage_slot = memory.Allocate(8);
  void *outer_second_fallback_slot = memory.Allocate(8);
  void *character_storage_slot = memory.Allocate(8);
  void *character_fallback_slot = memory.Allocate(8);
  void *government_fallback_slot = memory.Allocate(8);
  void *government_default_pc = memory.Allocate(0x80);
  void *government_default_guard = memory.Allocate(4);
  void *culture_default_pc = memory.Allocate(0x80);
  void *culture_default_guard = memory.Allocate(4);
  void *nested_default_pc = memory.Allocate(0x80);
  void *nested_default_guard = memory.Allocate(4);
  void *government_table = memory.Allocate(0x540);
  void *culture_direct_pc = memory.Allocate(0x80);
  void *culture_mapped_pc = memory.Allocate(0x80);
  void *unused_culture_mapped_pc = memory.Allocate(0x80);
  void *inner_mapped_pc = memory.Allocate(0x80);
  void *unused_inner_mapped_pc = memory.Allocate(0x80);
  void *last_inner_pc = memory.Allocate(0x80);
  void *culture_key_a = memory.Allocate(0x40);
  void *culture_key_b = memory.Allocate(0x40);
  void *culture_key_not_member = memory.Allocate(0x40);
  void *inner_key_a = memory.Allocate(0x40);
  void *inner_key_b = memory.Allocate(0x40);
  void *inner_key_not_member = memory.Allocate(0x40);
  void *last_inner_key = memory.Allocate(0x40);
  void *inner0_rows = memory.Allocate(0x90);
  void *inner1_rows = memory.Allocate(0x30);
  void *membership = memory.Allocate(5 * sizeof(void *));

  void Property(void *pc, std::int64_t value) {
    void *keys = memory.Allocate(2);
    void *values = memory.Allocate(8);
    memory.Put(pc, 0, keys);
    memory.Put(pc, 0xC, std::int32_t{1});
    memory.Put(pc, 0x68, values);
    memory.Put(pc, 0x74, std::int32_t{1});
    memory.Put(keys, 0, std::uint16_t{5});
    memory.Put(values, 0, value);
  }

  // All registry slots and backing tables remain unchanged between queries.
  void Registry(void *slot,
                const std::vector<std::pair<std::uint32_t, void *>> &objects,
                std::size_t full_id_offset) {
    void *storage = memory.Allocate(0x30);
    void *table = memory.Allocate(3 * 16);
    memory.Put(slot, 0, storage);
    memory.Put(storage, 0x20, table);
    memory.Put(storage, 0x2C, std::uint32_t{3});
    for (const auto &[full_id, object] : objects) {
      const auto index = full_id & 0xFFFFFFU;
      Require(index < 3, "fixture registry index");
      memory.Put(table, static_cast<std::size_t>(index) * 16 + 8, object);
      memory.Put(object, full_id_offset, full_id);
    }
  }
  void Key(void *key, std::uint32_t full_id) {
    memory.Put(key, 0x10, full_id);
    memory.Put(key, 0x38, std::uint32_t{0x4744624F});
  }
  void Descriptor(void *descriptor, void *key, void *pc) {
    memory.Put(descriptor, 0x20, key);
    memory.Put(descriptor, 0x28, pc);
  }

  Fixture() {
    bindings.enabled = true;
    bindings.remaining_helpers_enabled = true;
    bindings.remaining_character_storage_slot = character_storage_slot;
    bindings.remaining_character_fallback_slot = character_fallback_slot;
    bindings.remaining_government_fallback_slot = government_fallback_slot;
    bindings.remaining_government_default_pc = government_default_pc;
    bindings.remaining_government_default_guard_slot = government_default_guard;
    bindings.remaining_culture_mapped_default_pc = culture_default_pc;
    bindings.remaining_culture_mapped_default_guard_slot = culture_default_guard;
    bindings.remaining_nested_mapped_default_guard_slot = nested_default_guard;
    bindings.conditional_a_fallback_properties = nested_default_pc;
    bindings.selector_b_storage_slot = culture_storage_slot;
    bindings.selector_b_fallback_slot = culture_fallback_slot;
    bindings.selector_a_storage_slot = rite_storage_slot;
    bindings.selector_a_initial_fallback_slot = rite_fallback_slot;
    bindings.selector_a_second_storage_slot = rite_second_storage_slot;
    bindings.selector_a_second_fallback_slot = rite_second_fallback_slot;
    bindings.first_storage_slot = outer_first_storage_slot;
    bindings.first_fallback_slot = outer_first_fallback_slot;
    bindings.second_storage_slot = outer_second_storage_slot;
    bindings.second_fallback_slot = outer_second_fallback_slot;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;

    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(character, 0xB0, culture_id);
    memory.Put(character, 0xB4, first_rite_id);
    memory.Put(character, 0x158, outer_first_id);
    memory.Put(character, 0x1C0, land);
    memory.Put(land, 0x3F8, government);
    memory.Put(government, 0x38, std::uint32_t{0x4744624F});
    memory.Put(government, 0x10, std::int32_t{-2});
    memory.Put(character_fallback_slot, 0, character);
    memory.Put(government_fallback_slot, 0, government);
    memory.Put(culture, 0x14, std::uint32_t{0x43756C74});
    // Index -2 is legal in the captured source: the selected base is interior
    // to this region and signed -2 * 0x1C0 reaches its first actual PC.
    memory.Put(culture, 0x670, At(government_table, 2 * 0x1C0));
    Property(government_table, 101);
    memory.Put(government_default_guard, 0, std::int32_t{0});
    memory.Put(culture_default_guard, 0, std::int32_t{0});
    memory.Put(nested_default_guard, 0, std::int32_t{-1});

    Registry(culture_storage_slot, {{culture_id, culture}}, 0x10);
    Registry(rite_storage_slot,
             {{first_rite_id, first_rite}, {selected_rite_id, selected_rite}}, 8);
    Registry(rite_second_storage_slot, {{second_rite_id, second_rite}}, 8);
    Registry(outer_first_storage_slot, {{outer_first_id, outer_first}}, 0x10);
    Registry(outer_second_storage_slot, {{outer_second_id, outer_second}}, 0x10);
    memory.Put(culture_fallback_slot, 0, culture);
    memory.Put(rite_fallback_slot, 0, first_rite);
    memory.Put(rite_second_fallback_slot, 0, second_rite);
    memory.Put(outer_first_fallback_slot, 0, outer_first);
    memory.Put(outer_second_fallback_slot, 0, outer_second);
    memory.Put(first_rite, 0x4B8, second_rite_id);
    memory.Put(second_rite, 0x98, selected_rite_id);
    memory.Put(outer_first, 0x2C, outer_second_id);

    Key(culture_key_a, culture_map_id);
    Key(culture_key_b, culture_map_id);
    Key(culture_key_not_member, culture_map_id);
    Key(inner_key_a, inner_map_id);
    Key(inner_key_b, inner_map_id);
    Key(inner_key_not_member, inner_map_id);
    Key(last_inner_key, 0xBC000051U);
    memory.Put(membership, 0 * sizeof(void *), culture_key_a);
    memory.Put(membership, 1 * sizeof(void *), culture_key_b);
    memory.Put(membership, 2 * sizeof(void *), inner_key_a);
    memory.Put(membership, 3 * sizeof(void *), inner_key_b);
    memory.Put(membership, 4 * sizeof(void *), last_inner_key);
    for (void *rite : {first_rite, selected_rite}) {
      memory.Put(rite, 0x7A0, membership);
      memory.Put(rite, 0x7AC, std::int32_t{5});
    }

    Property(culture_direct_pc, 201);
    void *direct_pointers = memory.Allocate(2 * sizeof(void *));
    memory.Put(direct_pointers, 0, culture_direct_pc);
    memory.Put(direct_pointers, 8, culture_direct_pc);
    memory.Put(culture, 0x90, direct_pointers);
    memory.Put(culture, 0x9C, std::int32_t{2});

    Property(culture_mapped_pc, 301);
    Property(unused_culture_mapped_pc, 302);
    void *descriptor_a = memory.Allocate(0x30);
    void *descriptor_b = memory.Allocate(0x30);
    void *descriptor_not_member = memory.Allocate(0x30);
    Descriptor(descriptor_a, culture_key_a, culture_mapped_pc);
    Descriptor(descriptor_b, culture_key_b, unused_culture_mapped_pc);
    Descriptor(descriptor_not_member, culture_key_not_member,
               unused_culture_mapped_pc);
    void *culture_descriptors = memory.Allocate(4 * sizeof(void *));
    memory.Put(culture_descriptors, 0, descriptor_a);
    memory.Put(culture_descriptors, 8, descriptor_b);
    memory.Put(culture_descriptors, 16, descriptor_a);
    memory.Put(culture_descriptors, 24, descriptor_not_member);
    memory.Put(culture, 0x230, culture_descriptors);
    memory.Put(culture, 0x23C, std::int32_t{4});

    Property(At(outer0, 0x160), 401);
    Property(At(outer1, 0x160), 601);
    Property(inner_mapped_pc, 501);
    Property(unused_inner_mapped_pc, 502);
    Property(last_inner_pc, 701);
    Descriptor(At(inner0_rows, 0 * 0x30), inner_key_a, inner_mapped_pc);
    Descriptor(At(inner0_rows, 1 * 0x30), inner_key_b, unused_inner_mapped_pc);
    Descriptor(At(inner0_rows, 2 * 0x30), inner_key_not_member,
               unused_inner_mapped_pc);
    Descriptor(inner1_rows, last_inner_key, last_inner_pc);
    memory.Put(outer0, 0x450, inner0_rows);
    memory.Put(outer0, 0x45C, std::int32_t{3});
    memory.Put(outer1, 0x450, inner1_rows);
    memory.Put(outer1, 0x45C, std::int32_t{1});
    void *outer_pointers = memory.Allocate(2 * sizeof(void *));
    memory.Put(outer_pointers, 0, outer0);
    memory.Put(outer_pointers, 8, outer1);
    memory.Put(outer_second, 0x178, outer_pointers);
    memory.Put(outer_second, 0x184, std::int32_t{2});

    // A full-ID match is not QWORD membership. These distinct pointers have
    // matching IDs but are absent from the stored membership set.
    memory.Deny(culture_key_not_member, 0x38, 4);
    memory.Deny(inner_key_not_member, 0x38, 4);
  }

  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 Observe() {
    Require(bindings.enabled && bindings.remaining_helpers_enabled,
            "remaining helper binding enabled");
    Require(!bindings.pre_291e210_1640_enabled && !bindings.later_direct_enabled &&
                !bindings.helper_291f0a0_enabled,
            "only new helper leaf enabled");
    Require(!bindings.provider && !bindings.government &&
                !bindings.existing_token_lookup,
            "native callbacks never assigned");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first == second, "same-frame whole snapshots differ");
    Require(first.later_helpers_291f550_291f940.has_value(),
            "remaining helper section absent");
    Require(memory.Attempts() == 0, "skipped fields were demanded");
    return first;
  }
};

void Value(const std::optional<xar::game::ContextSourcePropertiesV1> &block,
           std::int64_t expected) {
  Require(block.has_value(), "selected property block absent");
  Require(block->keys_count == 1 && block->values_count == 1 &&
              block->keys_u16 && block->keys_u16->size() == 1 &&
              block->keys_u16->at(0) == 5 && block->values_q64 &&
              block->values_q64->size() == 1 &&
              block->values_q64->at(0) == expected,
          "selected property bytes differ");
}
void Empty(const std::optional<xar::game::ContextSourcePropertiesV1> &block) {
  Require(block && block->keys_count == 0 && !block->values_count &&
              block->keys_u16 && block->keys_u16->empty() &&
              block->values_q64 && block->values_q64->empty(),
          "actual empty fallback PC not retained");
}
void Save(const std::filesystem::path &directory, const char *name,
          const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string(name) + ".json"),
                       std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("remaining helper wire write failed");
}

void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  const auto address = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  Require(bindings.enabled && bindings.remaining_helpers_enabled,
          "exact remaining helper binding disabled");
  Require(bindings.remaining_character_storage_slot == address(0x5C67568),
          "Character registry RVA");
  Require(bindings.remaining_character_fallback_slot == address(0x5C67570),
          "Character fallback RVA");
  Require(bindings.remaining_government_fallback_slot == address(0x5D1E2A8),
          "government fallback RVA");
  Require(bindings.remaining_government_default_pc == address(0x5D65890),
          "government inline fallback PC RVA");
  Require(bindings.remaining_government_default_guard_slot == address(0x5D6588C),
          "government fallback guard RVA");
  Require(bindings.remaining_culture_mapped_default_pc == address(0x5DC2380),
          "culture mapped inline fallback PC RVA");
  Require(bindings.remaining_culture_mapped_default_guard_slot == address(0x5DC2370),
          "culture mapped fallback guard RVA");
  Require(bindings.conditional_a_fallback_properties == address(0x5DC21B0),
          "nested mapped inline fallback PC RVA");
  Require(bindings.remaining_nested_mapped_default_guard_slot == address(0x5DC21A4),
          "nested mapped fallback guard RVA");
  Require(bindings.selector_b_storage_slot == address(0x5D1E2F0) &&
              bindings.selector_b_fallback_slot == address(0x5D1E2E8),
          "Culture registry and fallback RVAs");
  Require(bindings.selector_a_storage_slot == address(0x5D1E2F8) &&
              bindings.selector_a_initial_fallback_slot == address(0x5C67670) &&
              bindings.selector_a_second_storage_slot == address(0x5D1E300) &&
              bindings.selector_a_second_fallback_slot == address(0x5D1E2E0),
          "Rite selector registry and fallback RVAs");
  Require(bindings.first_storage_slot == address(0x5D1DAF0) &&
              bindings.first_fallback_slot == address(0x5D1DAE8) &&
              bindings.second_storage_slot == address(0x5D1DE78) &&
              bindings.second_fallback_slot == address(0x5D1DE28),
          "940 outer selector registry and fallback RVAs");
}

void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture fixture;
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.later_helpers_291f550_291f940;
    const auto &a = leaf.helper_291f550;
    const auto &b = leaf.helper_291f940;
    Require(leaf.ready && a.ready && b.ready && b.direct_ready && b.mapped_ready,
            "full remaining helpers unavailable");
    Require(a.culture_key_b0_raw == static_cast<std::int32_t>(Fixture::culture_id) &&
                a.culture_full_id_raw == static_cast<std::int32_t>(Fixture::culture_id) &&
                a.government_full_id_raw == -2,
            "native signed generation or government index bits lost");
    Require(a.rite.first_key_b4_raw == static_cast<std::int32_t>(Fixture::first_rite_id) &&
                a.rite.second_key_4b8_raw == static_cast<std::int32_t>(Fixture::second_rite_id) &&
                a.rite.third_key_98_raw == static_cast<std::int32_t>(Fixture::selected_rite_id) &&
                b.first_key_158_raw == static_cast<std::int32_t>(Fixture::outer_first_id) &&
                b.second_key_2c_raw == static_cast<std::int32_t>(Fixture::outer_second_id),
            "full selector generation bits lost");
    Require(a.government_indexed.rows && a.government_indexed.rows->size() == 1 &&
                a.culture_direct.rows && a.culture_direct.rows->size() == 2 &&
                a.culture_mapped.rows && a.culture_mapped.rows->size() == 4,
            "550 stored family occurrence counts");
    Value(a.government_indexed.rows->at(0).property_block, 101);
    Value(a.culture_direct.rows->at(0).property_block, 201);
    Value(a.culture_direct.rows->at(1).property_block, 201);
    Require(a.culture_direct.rows->at(0).property_identity ==
                a.culture_direct.rows->at(1).property_identity,
            "direct duplicate PC identities lost");
    const auto &culture_rows = *a.culture_mapped.rows;
    Require(culture_rows[0].key_identity != culture_rows[1].key_identity &&
                culture_rows[0].key_identity == culture_rows[2].key_identity &&
                culture_rows[0].key_full_id_raw == culture_rows[1].key_full_id_raw &&
                culture_rows[3].admitted == false && !culture_rows[3].key_magic_raw,
            "QWORD membership or duplicate key identity changed");
    for (std::size_t i = 0; i < 3; ++i) {
      Require(culture_rows[i].admitted == true &&
                  culture_rows[i].mapping_native_index == 0 &&
                  culture_rows[i].property_identity == culture_rows[0].property_identity,
              "Culture mapper did not select first full-ID match");
      Value(culture_rows[i].property_block, 301);
    }
    Require(a.mapped_default_guard_raw == 0 && b.mapped_default_guard_raw == -1,
            "unused lazy guards not retained");
    Require(b.outer_rows && b.outer_rows->size() == 2,
            "940 outer occurrence counts");
    const auto &outer = *b.outer_rows;
    Value(outer[0].direct_property_block, 401);
    Value(outer[1].direct_property_block, 601);
    Require(outer[0].inner_mapped.rows && outer[0].inner_mapped.rows->size() == 3 &&
                outer[1].inner_mapped.rows && outer[1].inner_mapped.rows->size() == 1,
            "940 inner occurrence counts");
    const auto &inner = *outer[0].inner_mapped.rows;
    Require(inner[0].key_identity != inner[1].key_identity &&
                inner[0].key_full_id_raw == inner[1].key_full_id_raw &&
                inner[0].mapping_native_index == 0 && inner[1].mapping_native_index == 0 &&
                inner[0].property_identity == inner[1].property_identity &&
                inner[2].admitted == false && !inner[2].key_magic_raw,
            "940 first full-ID mapping or exact pointer membership changed");
    Value(inner[0].property_block, 501);
    Value(inner[1].property_block, 501);
    Value(outer[1].inner_mapped.rows->at(0).property_block, 701);
    Save(directory, "full-order-duplicates", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.government, 0x38, std::uint32_t{0});
    fixture.memory.Put(fixture.inner_key_a, 0x38, std::uint32_t{0});
    fixture.memory.Put(fixture.outer0, 0x45C, std::int32_t{1});
    fixture.memory.Put(fixture.outer1, 0x45C, std::int32_t{0});
    // Actual null storage selects the existing fallback without loading keys.
    fixture.memory.Put(fixture.culture_storage_slot, 0, static_cast<void *>(nullptr));
    fixture.memory.Put(fixture.rite_storage_slot, 0, static_cast<void *>(nullptr));
    fixture.memory.Deny(fixture.character, 0xB0, 8);
    fixture.memory.Deny(fixture.second_rite, 0x98, 4);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.later_helpers_291f550_291f940;
    const auto &a = leaf.helper_291f550;
    const auto &b = leaf.helper_291f940;
    Require(!leaf.ready && !a.ready && !a.government_indexed.ready &&
                a.culture_direct.ready && a.culture_mapped.ready,
            "550 independent families blocked by government fallback");
    Require(a.culture_selection == "native_fallback" && !a.culture_key_b0_raw &&
                !a.rite.first_key_b4_raw && !a.rite.third_key_98_raw,
            "null selector storage demanded unused full-ID keys");
    Require(a.government_default_guard_raw == 0 &&
                a.government_indexed.rows && a.government_indexed.rows->size() == 1 &&
                !a.government_indexed.reason.empty(),
            "uninitialized government fallback status missing");
    Empty(a.government_indexed.rows->at(0).property_block);
    Require(!b.ready && b.direct_ready && !b.mapped_ready &&
                b.mapped_default_guard_raw == -1 && b.outer_rows &&
                b.outer_rows->size() == 2,
            "940 direct independence or lazy marker lost");
    Value(b.outer_rows->at(0).direct_property_block, 401);
    Value(b.outer_rows->at(1).direct_property_block, 601);
    const auto &mapped = b.outer_rows->at(0).inner_mapped;
    Require(!mapped.ready && mapped.rows && mapped.rows->size() == 1 &&
                mapped.rows->at(0).admitted == true &&
                mapped.rows->at(0).key_magic_raw == 0U &&
                !mapped.rows->at(0).mapping_native_index &&
                !mapped.reason.empty(),
            "940 actual static fallback selection missing");
    Empty(mapped.rows->at(0).property_block);
    Require(b.outer_rows->at(1).inner_mapped.ready &&
                b.outer_rows->at(1).inner_mapped.rows &&
                b.outer_rows->at(1).inner_mapped.rows->empty(),
            "independent actual zero inner span unavailable");
    Save(directory, "lazy-fallback-partial-independent", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.culture, 0x14, std::uint32_t{0});
    fixture.memory.Put(fixture.outer0, 0x45C, std::int32_t{0});
    fixture.memory.Put(fixture.outer1, 0x45C, std::int32_t{0});
    fixture.memory.Put(fixture.outer1, 0x16C, std::int32_t{0});
    fixture.memory.Deny(fixture.character, 0x1C0, 8);
    fixture.memory.Deny(fixture.character, 0x1D0, 8);
    fixture.memory.Deny(fixture.culture, 0x90, 0x10);
    fixture.memory.Deny(fixture.culture, 0x230, 0x10);
    fixture.memory.Deny(fixture.culture, 0x670, 8);
    fixture.memory.Deny(fixture.selected_rite, 0x7A0, 0x10);
    fixture.memory.Deny(fixture.nested_default_guard, 0, 4);
    fixture.memory.Deny(fixture.nested_default_pc, 0, 0x80);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.later_helpers_291f550_291f940;
    const auto &a = leaf.helper_291f550;
    const auto &b = leaf.helper_291f940;
    Require(leaf.ready && a.ready && a.admitted == false &&
                !a.government_identity && !a.government_magic_raw,
            "Culture whole-helper skip demanded government");
    Require(b.ready && b.direct_ready && b.mapped_ready &&
                b.outer_rows && b.outer_rows->size() == 2 &&
                !b.rite.membership_count && !b.mapped_default_guard_raw,
            "zero inner spans demanded membership or fallback guard");
    const auto &outer = *b.outer_rows;
    Require(outer[0].direct_admitted == true && outer[1].direct_admitted == false &&
                !outer[1].direct_property_block,
            "actual zero direct gate consumed a PC");
    Value(outer[0].direct_property_block, 401);
    for (const auto &row : outer)
      Require(row.inner_mapped.ready && row.inner_mapped.count == 0 &&
                  row.inner_mapped.rows && row.inner_mapped.rows->empty(),
              "zero inner list not represented as actual empty");
    Save(directory, "culture-skip-inner-zero", snapshot);
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    const std::filesystem::path directory = argc == 2 ? argv[1] : "";
    if (!directory.empty()) std::filesystem::create_directories(directory);
    Run(directory);
    std::cout << "remaining291F550/291F940 current source observer GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
