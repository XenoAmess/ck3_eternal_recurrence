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
    std::size_t total = 0;
    for (const auto &interval : denied) total += interval.attempts;
    return total;
  }
  std::size_t MissingAttempts() const {
    std::size_t total = 0;
    for (const auto &interval : unavailable) total += interval.attempts;
    return total;
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
constexpr std::uint32_t kObjectA = 0xAA000001U;
constexpr std::uint32_t kObjectB = 0xBB000002U;
constexpr std::uint32_t kFirstRite = 0xAC000001U;
constexpr std::uint32_t kFaith = 0xBC000001U;
constexpr std::uint32_t kThirdRite = 0xCC000002U;

// One fixed, zero-initialized source frame per case. The actual production
// query is read twice without changing bytes, compared in full, then emitted
// with the actual whole-snapshot serializer. No native callback is installed.
struct Fixture {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *land = memory.Allocate(0x190);
  void *provider = memory.Allocate(0x16B8);
  void *high = memory.Allocate(0xB8);
  void *low = memory.Allocate(0xB8);
  void *fallback = memory.Allocate(0xB8);
  void *provider_slot = memory.Allocate(8);
  void *upper_slot = memory.Allocate(4);
  void *lower_slot = memory.Allocate(4);
  void *provider_fallback_slot = memory.Allocate(8);
  void *list_default_header = memory.Allocate(0x18);
  void *list_default_guard = memory.Allocate(4);
  void *first_ids = memory.Allocate(2 * 4);
  void *second_ids = memory.Allocate(4);
  void *object_storage_slot = memory.Allocate(8);
  void *object_fallback_slot = memory.Allocate(8);
  void *object_store = memory.Allocate(0x30);
  void *object_table = memory.Allocate(3 * 16);
  void *object_a = memory.Allocate(0x4C8);
  void *object_b = memory.Allocate(0x4C8);
  void *table_a = memory.Allocate(0x2700);
  void *table_b = memory.Allocate(0x2700);
  void *rite_storage_slot = memory.Allocate(8);
  void *rite_fallback_slot = memory.Allocate(8);
  void *faith_storage_slot = memory.Allocate(8);
  void *faith_fallback_slot = memory.Allocate(8);
  void *rite_store = memory.Allocate(0x30);
  void *rite_table = memory.Allocate(3 * 16);
  void *faith_store = memory.Allocate(0x30);
  void *faith_table = memory.Allocate(2 * 16);
  void *first_rite = memory.Allocate(0x7B0);
  void *third_rite = memory.Allocate(0x7B0);
  void *faith = memory.Allocate(0xA0);
  void *key_a = memory.Allocate(0x40);
  void *key_b = memory.Allocate(0x40);
  void *key_nonmember = memory.Allocate(0x40);
  void *key_c = memory.Allocate(0x40);
  void *membership = memory.Allocate(3 * 8);
  void *first_descriptors = memory.Allocate(4 * 0x30);
  void *first_mapped_pc = memory.Allocate(0x78);
  void *alternate_mapped_pc = memory.Allocate(0x78);
  void *mapped_default_pc = memory.Allocate(0x78);
  void *mapped_default_guard = memory.Allocate(4);

  void Property(void *pc, const std::vector<std::uint16_t> &keys,
                const std::vector<std::int64_t> &values) {
    Require(keys.size() == values.size(), "provider192 property pair size");
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
  void Registry(void *store, void *table, std::uint32_t capacity) {
    memory.Put(store, 0x20, table);
    memory.Put(store, 0x2C, capacity);
  }
  void Descriptor(void *array, std::size_t index, void *key, void *pc) {
    memory.Put(array, index * 0x30 + 0x20, key);
    memory.Put(array, index * 0x30 + 0x28, pc);
  }
  Fixture() {
    bindings.enabled = true;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.provider192_and2920850;
    b.enabled = true;
    b.provider_slot = provider_slot;
    b.upper_slot = upper_slot;
    b.lower_slot = lower_slot;
    b.provider_fallback_slot = provider_fallback_slot;
    b.list_default_header = list_default_header;
    b.list_default_guard_slot = list_default_guard;
    b.object_storage_slot = object_storage_slot;
    b.object_fallback_slot = object_fallback_slot;
    b.rite_storage_slot = rite_storage_slot;
    b.rite_fallback_slot = rite_fallback_slot;
    b.faith_storage_slot = faith_storage_slot;
    b.faith_fallback_slot = faith_fallback_slot;
    b.mapped_default_pc = mapped_default_pc;
    b.mapped_default_guard_slot = mapped_default_guard;

    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(character, 0x192, std::int16_t{-10});
    memory.Put(character, 0x1C0, land);
    memory.Put(provider_slot, 0, provider);
    memory.Put(provider, 0x16A0, high);
    memory.Put(provider, 0x16B0, low);
    memory.Put(upper_slot, 0, std::int32_t{-20});
    memory.Put(lower_slot, 0, std::int32_t{999});
    memory.Put(provider_fallback_slot, 0, fallback);
    memory.Put(high, 0x38, std::uint32_t{0x4744624FU});
    memory.Put(low, 0x38, std::uint32_t{0x4744624FU});
    memory.Put(fallback, 0x38, std::uint32_t{0x4744624FU});
    memory.Put(high, 0x10, std::int32_t{-1});
    PC(high, 0x40, 10, 100000);
    PC(low, 0x40, 20, 200000);
    PC(fallback, 0x40, 30, 300000);

    memory.Put(first_ids, 0, kObjectA);
    memory.Put(first_ids, 4, kObjectA);
    memory.Put(second_ids, 0, kObjectB);
    memory.Put(land, 0x168, first_ids);
    memory.Put(land, 0x174, std::int32_t{2});
    memory.Put(land, 0x180, second_ids);
    memory.Put(land, 0x18C, std::int32_t{1});
    memory.Put(list_default_header, 0, first_ids);
    memory.Put(list_default_header, 0xC, std::int32_t{1});
    memory.Put(list_default_guard, 0, std::int32_t{9});
    memory.Put(object_storage_slot, 0, object_store);
    memory.Put(object_fallback_slot, 0, object_a);
    Registry(object_store, object_table, 3U);
    memory.Put(object_table, 16 + 8, object_a);
    memory.Put(object_table, 2 * 16 + 8, object_b);
    memory.Put(object_a, 8, kObjectA);
    memory.Put(object_b, 8, kObjectB);
    memory.Put(object_a, 0x4C0, table_a);
    memory.Put(object_b, 0x4C0, table_b);
    for (std::size_t i = 0; i < 4; ++i) {
      PC(table_a, 0x80 + i * 0xB30, static_cast<std::uint16_t>(11 + i),
         static_cast<std::int64_t>(101 + i));
      PC(table_a, 0x240 + i * 0xB30, static_cast<std::uint16_t>(31 + i),
         static_cast<std::int64_t>(301 + i));
      if (i < 3)
        PC(table_b, 0x240 + i * 0xB30, static_cast<std::uint16_t>(21 + i),
           static_cast<std::int64_t>(201 + i));
    }

    memory.Put(character, 0xB4, kFirstRite);
    memory.Put(rite_storage_slot, 0, rite_store);
    memory.Put(rite_fallback_slot, 0, first_rite);
    memory.Put(faith_storage_slot, 0, faith_store);
    memory.Put(faith_fallback_slot, 0, faith);
    Registry(rite_store, rite_table, 3U);
    Registry(faith_store, faith_table, 2U);
    memory.Put(rite_table, 16 + 8, first_rite);
    memory.Put(rite_table, 2 * 16 + 8, third_rite);
    memory.Put(faith_table, 16 + 8, faith);
    memory.Put(first_rite, 8, kFirstRite);
    memory.Put(first_rite, 0x4B8, kFaith);
    memory.Put(faith, 8, kFaith);
    memory.Put(faith, 0x98, kThirdRite);
    memory.Put(third_rite, 8, kThirdRite);
    memory.Put(third_rite, 0x7A0, membership);
    memory.Put(third_rite, 0x7AC, std::int32_t{3});
    memory.Put(membership, 0, key_a);
    memory.Put(membership, 8, key_b);
    memory.Put(membership, 16, key_c);
    for (void *key : {key_a, key_b, key_nonmember, key_c})
      memory.Put(key, 0x38, std::uint32_t{0x4744624FU});
    memory.Put(key_a, 0x10, std::int32_t{41});
    memory.Put(key_b, 0x10, std::int32_t{41});
    memory.Put(key_nonmember, 0x10, std::int32_t{41});
    memory.Put(key_c, 0x10, std::int32_t{42});
    Property(first_mapped_pc, {51}, {501});
    Property(alternate_mapped_pc, {59}, {599});
    Descriptor(first_descriptors, 0, key_a, first_mapped_pc);
    Descriptor(first_descriptors, 1, key_b, alternate_mapped_pc);
    Descriptor(first_descriptors, 2, key_a, alternate_mapped_pc);
    Descriptor(first_descriptors, 3, key_nonmember, alternate_mapped_pc);
    memory.Put(table_a, 0x400, first_descriptors);
    memory.Put(table_a, 0x40C, std::int32_t{4});
    for (std::size_t i = 1; i < 4; ++i) {
      void *rows = memory.Allocate(0x30);
      void *pc = memory.Allocate(0x78);
      Property(pc, {static_cast<std::uint16_t>(51 + i)},
               {static_cast<std::int64_t>(501 + i)});
      Descriptor(rows, 0, key_c, pc);
      memory.Put(table_a, 0x400 + i * 0xB30, rows);
      memory.Put(table_a, 0x40C + i * 0xB30, std::int32_t{1});
    }
    Property(mapped_default_pc, {60}, {600});
    memory.Put(mapped_default_guard, 0, std::int32_t{-1});

    // Existing always-collected source leaves have current empty headers.
    void *legacy_carrier = memory.Allocate(0x230);
    memory.Put(character, 0x1B0, legacy_carrier);
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
    memory.Deny(key_nonmember, 0x10, 4);
    memory.Deny(key_nonmember, 0x38, 4);
    memory.Deny(mapped_default_pc, 0, 0x78);
  }
  Snapshot Observe() {
    Require(bindings.enabled && bindings.provider192_and2920850.enabled,
            "provider192 source binding disabled");
    Require(!bindings.gated_temporary_tail.enabled && !bindings.after_gated_tail.enabled &&
                !bindings.pre_291e210_1640_enabled && !bindings.later_direct_enabled &&
                !bindings.helper_291f0a0_enabled && !bindings.remaining_helpers_enabled &&
                !bindings.tail_direct_enabled && !bindings.post_291d7e0_sources_enabled &&
                !bindings.trait_stage.enabled && !bindings.middle_helpers.enabled &&
                !bindings.tail_prefix_enabled && !bindings.helper_2922070_enabled,
            "other optional source leaf enabled");
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "provider192 fixture must not install native callbacks");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first == second, "provider192 whole snapshots differ in fixed frame");
    Require(first.provider192_and2920850.has_value(), "provider192 source leaf absent");
    Require(memory.Attempts() == 0, "provider192 unused source operands were demanded");
    return first;
  }
  void EmptyCurrentLists() {
    memory.Put(land, 0x174, std::int32_t{0});
    memory.Put(land, 0x18C, std::int32_t{0});
    memory.Deny(first_ids, 0, 8);
    memory.Deny(second_ids, 0, 4);
  }
};
void Save(const std::filesystem::path &directory, const char *name,
          const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("provider192-") + name + ".json"),
                       std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("provider192 wire write failed");
}
void PCValue(const auto &pc, std::uint16_t key, std::int64_t value) {
  Require(pc.property_identity && pc.property_block && pc.property_block->keys_u16 &&
              pc.property_block->values_q64 && pc.property_block->keys_u16->size() == 1 &&
              pc.property_block->values_q64->size() == 1 &&
              pc.property_block->keys_u16->at(0) == key &&
              pc.property_block->values_q64->at(0) == value,
          "provider192 raw paired property differs");
}
void EmptyPC(const auto &pc) {
  Require(pc.property_identity && pc.property_block && pc.property_block->keys_count == 0 &&
              !pc.property_block->values_count && pc.property_block->keys_u16 &&
              pc.property_block->keys_u16->empty() && pc.property_block->values_q64 &&
              pc.property_block->values_q64->empty(),
          "provider192 empty PC must retain empty keys without value demand");
}
void DirectSlots(const auto &row, std::uint16_t first_key, std::int64_t first_value,
                 bool last_empty = false) {
  Require(row.direct_ready && row.direct_rows && row.direct_rows->size() == 4,
          "provider192 exactly four direct slots required");
  for (std::size_t i = 0; i < 4; ++i) {
    const auto &slot = row.direct_rows->at(i);
    Require(slot.native_index == static_cast<std::int32_t>(i),
            "provider192 direct slot ordinal differs");
    if (last_empty && i == 3) EmptyPC(slot.pc);
    else PCValue(slot.pc, static_cast<std::uint16_t>(first_key + i),
                 first_value + static_cast<std::int64_t>(i));
  }
}
void EmptyNested(const auto &row) {
  Require(row.mapped_ready && row.nested_rows && row.nested_rows->size() == 4,
          "provider192 exactly four nested slots required");
  for (std::size_t i = 0; i < 4; ++i) {
    const auto &slot = row.nested_rows->at(i);
    Require(slot.native_index == static_cast<std::int32_t>(i) && slot.mapped_family.ready &&
                slot.mapped_family.count == 0 && slot.mapped_family.rows &&
                slot.mapped_family.rows->empty(),
            "provider192 zero nested source must be ready without membership demand");
  }
}
void FullNested(const auto &row) {
  Require(row.mapped_ready && row.nested_rows && row.nested_rows->size() == 4,
          "provider192 full nested slot count differs");
  const auto &family = row.nested_rows->at(0).mapped_family;
  Require(family.ready && family.count == 4 && family.rows && family.rows->size() == 4,
          "provider192 first mapped family occurrence count differs");
  for (std::size_t i = 0; i < 3; ++i) {
    const auto &descriptor = family.rows->at(i);
    Require(descriptor.native_index == static_cast<std::int32_t>(i) &&
                descriptor.admitted == true && descriptor.key_full_id_raw == 41 &&
                descriptor.mapping_native_index == 0 &&
                descriptor.property_identity == family.rows->at(0).property_identity,
            "provider192 mapped duplicates must choose first full ID match");
    PCValue(descriptor, 51, 501);
  }
  Require(family.rows->at(0).key_identity != family.rows->at(1).key_identity &&
              family.rows->at(0).key_identity == family.rows->at(2).key_identity &&
              family.rows->at(3).admitted == false &&
              !family.rows->at(3).key_magic_raw && !family.rows->at(3).key_full_id_raw,
          "provider192 membership must use whole pointer before key magic/ID");
  for (std::size_t i = 1; i < 4; ++i) {
    const auto &slot = row.nested_rows->at(i);
    Require(slot.native_index == static_cast<std::int32_t>(i) && slot.mapped_family.ready &&
                slot.mapped_family.rows && slot.mapped_family.rows->size() == 1,
            "provider192 remaining mapped slots differ");
    PCValue(slot.mapped_family.rows->at(0), static_cast<std::uint16_t>(51 + i),
            static_cast<std::int64_t>(501 + i));
  }
}
void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  const auto &b = bindings.provider192_and2920850;
  const auto address = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  Require(bindings.enabled && b.enabled && b.provider_slot == address(0x5C670F8) &&
              b.upper_slot == address(0x5C69FE4) && b.lower_slot == address(0x5C69FE0) &&
              b.provider_fallback_slot == address(0x5D1E0B0) &&
              b.list_default_header == address(0x5D67E60) &&
              b.list_default_guard_slot == address(0x5D67E58) &&
              b.object_storage_slot == address(0x5D1EB60) &&
              b.object_fallback_slot == address(0x5D1EB90) &&
              b.rite_storage_slot == address(0x5D1E2F8) &&
              b.rite_fallback_slot == address(0x5C67670) &&
              b.faith_storage_slot == address(0x5D1E300) &&
              b.faith_fallback_slot == address(0x5D1E2E0) &&
              b.mapped_default_pc == address(0x5DC21B0) &&
              b.mapped_default_guard_slot == address(0x5DC21A4),
          "provider192 exact-build bindings differ");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "wrong-build").provider192_and2920850.enabled,
          "provider192 exact-build factory accepted wrong build");
}
void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture f;
    f.memory.Deny(f.lower_slot, 0, 4);
    f.memory.Deny(f.provider, 0x16B0, 8);
    f.memory.Deny(f.provider_fallback_slot, 0, 8);
    f.memory.Deny(f.high, 0x10, 4);
    f.memory.Deny(f.list_default_guard, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.provider192_and2920850;
    const auto &p = leaf.provider_192;
    Require(snapshot.ready && leaf.ready && p.ready && p.provider_loaded == true &&
                p.character_192_i16 == std::int16_t{-10} && p.upper_i32 == -20 &&
                !p.lower_i32 && p.selection == "provider_16a0" && p.admitted == true &&
                leaf.list_168.ready && leaf.list_180.ready &&
                leaf.list_168.rows && leaf.list_168.rows->size() == 2 &&
                leaf.list_180.rows && leaf.list_180.rows->size() == 1 &&
                leaf.rite.membership_count == 3 && leaf.mapped_default_guard_raw == -1,
            "provider192 signed upper branch or unconditional list collection differs");
    PCValue(p.pc, 10, 100000);
    for (std::size_t i = 0; i < 2; ++i) {
      const auto &row = leaf.list_168.rows->at(i);
      Require(row.native_index == static_cast<std::int32_t>(i) && row.ready &&
                  row.resolution_selection == "registry_full_id_8" &&
                  row.requested_full_id_raw == static_cast<std::int32_t>(kObjectA) &&
                  row.selected_full_id_raw == static_cast<std::int32_t>(kObjectA) &&
                  row.object_identity == leaf.list_168.rows->at(0).object_identity &&
                  row.table_identity == leaf.list_168.rows->at(0).table_identity,
              "provider192 physical duplicate IDs lost generation or identity");
      DirectSlots(row, 11, 101);
      FullNested(row);
    }
    DirectSlots(leaf.list_180.rows->at(0), 21, 201, true);
    EmptyNested(leaf.list_180.rows->at(0));
    Save(directory, "full-upper-duplicates", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x192, std::numeric_limits<std::int16_t>::min());
    f.memory.Put(f.upper_slot, 0, std::int32_t{-1});
    f.memory.Put(f.lower_slot, 0, std::int32_t{-20000});
    f.Property(At(f.low, 0x40), {}, {});
    f.EmptyCurrentLists();
    f.memory.Deny(f.provider, 0x16A0, 8);
    f.memory.Deny(f.provider_fallback_slot, 0, 8);
    f.memory.Deny(f.low, 0x40, 8);
    f.memory.Deny(f.low, 0x40 + 0x68, 8);
    f.memory.Deny(f.low, 0x40 + 0x74, 4);
    f.memory.Deny(f.rite_storage_slot, 0, 8);
    f.memory.Deny(f.mapped_default_guard, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.provider192_and2920850;
    Require(snapshot.ready && leaf.ready && leaf.provider_192.ready &&
                leaf.provider_192.character_192_i16 == std::numeric_limits<std::int16_t>::min() &&
                leaf.provider_192.selection == "provider_16b0" &&
                leaf.provider_192.lower_i32 == -20000 && leaf.provider_192.admitted == true &&
                leaf.list_168.numeric_count == 0 && leaf.list_180.numeric_count == 0 &&
                !leaf.rite.membership_count && !leaf.mapped_default_guard_raw,
            "provider192 signed WORD lower branch or empty-demand behavior differs");
    EmptyPC(leaf.provider_192.pc);
    Save(directory, "signed-lower-empty", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x192, std::numeric_limits<std::int16_t>::max());
    f.memory.Put(f.upper_slot, 0, std::int32_t{40000});
    f.memory.Put(f.lower_slot, 0, std::int32_t{0});
    f.memory.Put(f.fallback, 0x38, std::uint32_t{0});
    f.memory.Put(f.land, 0x174, std::int32_t{0});
    f.memory.Deny(f.fallback, 0x40, 0x78);
    f.memory.Deny(f.first_ids, 0, 8);
    f.memory.Deny(f.rite_storage_slot, 0, 8);
    f.memory.Deny(f.mapped_default_guard, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.provider192_and2920850;
    Require(snapshot.ready && leaf.ready && leaf.provider_192.ready &&
                leaf.provider_192.selection == "native_fallback_5d1e0b0" &&
                leaf.provider_192.magic_u32 == 0U && leaf.provider_192.admitted == false &&
                !leaf.provider_192.pc.property_identity && leaf.list_180.ready &&
                leaf.list_180.rows && leaf.list_180.rows->size() == 1,
            "provider192 magic rejection must preserve unconditional second list");
    DirectSlots(leaf.list_180.rows->at(0), 21, 201, true);
    EmptyNested(leaf.list_180.rows->at(0));
    Save(directory, "fallback-magic-skip", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.provider_slot, 0, static_cast<void *>(nullptr));
    f.memory.Put(f.land, 0x174, std::int32_t{1});
    f.memory.Hide(f.table_a, 0x80 + 2 * 0xB30 + 0xC, 4);
    f.Descriptor(f.first_descriptors, 1, f.key_c, nullptr);
    f.memory.Deny(f.character, 0x192, 2);
    f.memory.Deny(f.upper_slot, 0, 4);
    f.memory.Deny(f.lower_slot, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.provider192_and2920850;
    Require(leaf.list_168.rows && leaf.list_168.rows->size() == 1 &&
                leaf.list_168.rows->at(0).nested_rows &&
                leaf.list_168.rows->at(0).nested_rows->size() == 4,
            "provider192 partial occurrence or nested slots absent");
    const auto &row = leaf.list_168.rows->at(0);
    const auto &mapped = row.nested_rows->at(0).mapped_family;
    Require(!snapshot.ready && !leaf.ready && !leaf.provider_192.ready &&
                leaf.provider_192.provider_loaded == false && !leaf.list_168.ready &&
                !leaf.list_168.direct_ready && !leaf.list_168.mapped_ready &&
                !row.direct_ready && !row.mapped_ready && leaf.list_180.ready &&
                row.direct_rows && row.direct_rows->size() == 4 &&
                row.direct_rows->at(2).pc.property_block &&
                !row.direct_rows->at(2).pc.property_block->keys_count &&
                mapped.rows && mapped.rows->size() == 4 && !mapped.ready &&
                mapped.rows->at(1).admitted == true &&
                mapped.rows->at(1).mapping_native_index == 1 &&
                mapped.rows->at(1).property_block &&
                !mapped.rows->at(1).property_block->keys_count &&
                mapped.rows->at(1).property_block->reason == "property_container_unavailable" &&
                f.memory.MissingAttempts() > 0,
            "provider192 missing direct slot/null mapped PC must retain independent slots");
    PCValue(row.direct_rows->at(0).pc, 11, 101);
    PCValue(row.direct_rows->at(1).pc, 12, 102);
    PCValue(row.direct_rows->at(3).pc, 14, 104);
    PCValue(mapped.rows->at(0), 51, 501);
    PCValue(mapped.rows->at(2), 51, 501);
    for (std::size_t i = 1; i < 4; ++i)
      PCValue(row.nested_rows->at(i).mapped_family.rows->at(0),
              static_cast<std::uint16_t>(51 + i), static_cast<std::int64_t>(501 + i));
    DirectSlots(leaf.list_180.rows->at(0), 21, 201, true);
    Save(directory, "partial-slots-independent", snapshot);
  }
  {
    Fixture f;
    f.Property(At(f.high, 0x40), {}, {});
    f.memory.Put(f.character, 0x1D0, f.memory.Allocate(8));
    f.memory.Put(f.list_default_guard, 0, std::int32_t{-1});
    f.memory.Deny(f.list_default_header, 0, 0x18);
    f.memory.Deny(f.land, 0x168, 0x10);
    f.memory.Deny(f.land, 0x180, 0x10);
    f.memory.Deny(f.object_storage_slot, 0, 8);
    f.memory.Deny(f.rite_storage_slot, 0, 8);
    f.memory.Deny(f.mapped_default_guard, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.provider192_and2920850;
    Require(snapshot.ready && leaf.ready && leaf.current_death_present == true &&
                leaf.list_168.header_selection == "modeled_empty_default_5d67e60" &&
                leaf.list_180.header_selection == "modeled_empty_default_5d67e60" &&
                leaf.list_168.default_init_guard_raw == -1 &&
                leaf.list_180.default_init_guard_raw == -1 &&
                leaf.list_168.numeric_count == 0 && leaf.list_180.numeric_count == 0 &&
                !leaf.list_168.count_raw && !leaf.list_180.count_raw &&
                !leaf.list_168.array_present && !leaf.list_180.array_present &&
                leaf.list_168.rows && leaf.list_168.rows->empty() &&
                leaf.list_180.rows && leaf.list_180.rows->empty(),
            "provider192 modeled default must leave physical header operands unobserved");
    EmptyPC(leaf.provider_192.pc);
    Save(directory, "modeled-default-list", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    f.memory.Put(f.character, 0x192, std::int16_t{-1});
    f.memory.Put(f.upper_slot, 0, std::int32_t{0});
    f.memory.Put(f.lower_slot, 0, std::int32_t{-2});
    f.memory.Put(f.object_storage_slot, 0, static_cast<void *>(nullptr));
    f.memory.Deny(f.first_ids, 0, 8);
    f.memory.Deny(f.character, 0x1D0, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.provider192_and2920850;
    Require(snapshot.ready && leaf.ready && leaf.current_land_present == false &&
                !leaf.current_death_present &&
                leaf.provider_192.selection == "native_fallback_5d1e0b0" &&
                leaf.list_168.header_selection == "inline_default_5d67e60" &&
                leaf.list_180.header_selection == "inline_default_5d67e60" &&
                leaf.list_168.default_init_guard_raw == 9 && leaf.list_180.default_init_guard_raw == 9 &&
                leaf.list_168.count_raw == 1 && leaf.list_180.count_raw == 1 &&
                leaf.list_168.rows && leaf.list_168.rows->size() == 1 &&
                leaf.list_180.rows && leaf.list_180.rows->size() == 1,
            "provider192 initialized default must release actual header independently");
    const auto &first = leaf.list_168.rows->at(0);
    const auto &second = leaf.list_180.rows->at(0);
    Require(first.resolution_selection == "native_fallback" &&
                second.resolution_selection == "native_fallback" &&
                !first.requested_full_id_raw && !second.requested_full_id_raw &&
                !first.selected_full_id_raw && !second.selected_full_id_raw &&
                first.object_identity == second.object_identity,
            "provider192 readable null registry must skip full-ID demand and use fallback");
    PCValue(leaf.provider_192.pc, 30, 300000);
    DirectSlots(first, 11, 101);
    FullNested(first);
    DirectSlots(second, 31, 301);
    EmptyNested(second);
    Save(directory, "initialized-default-null-registry", snapshot);
  }
}
} // namespace

void RunProvider192And2920850Fixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}
