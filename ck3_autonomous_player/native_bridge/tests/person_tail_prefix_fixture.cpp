#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void Require(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
void *At(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
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
  void Deny(void *address, std::size_t offset, std::size_t size) {
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
    for (auto &entry : memory.denied)
      if (begin < entry.begin + entry.size && entry.begin < begin + size) {
        ++entry.attempts;
        return false;
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

struct Fixture {
  static constexpr std::uint32_t first_id = 0xAB000001U;
  static constexpr std::uint32_t owner_id = 0xBC000002U;
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *ancestor = memory.Allocate(0x1D8);
  void *fallback_character = memory.Allocate(0x1D8);
  void *land = memory.Allocate(0x400);
  void *relation_object = memory.Allocate(0x30);
  void *government = memory.Allocate(0x810);
  void *first = memory.Allocate(0x288);
  void *owner = memory.Allocate(0x168);
  void *definition275 = memory.Allocate(0x268);
  void *definition2530 = memory.Allocate(0x218);
  void *records = memory.Allocate(3 * 0x12D0);
  void *predicate_key = memory.Allocate(1);
  void *storage_slot = memory.Allocate(8);
  void *fallback_slot = memory.Allocate(8);
  void *character_storage_slot = memory.Allocate(8);
  void *character_fallback_slot = memory.Allocate(8);
  void *government_fallback_slot = memory.Allocate(8);
  void *default_relation_slot = memory.Allocate(8);

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
  Fixture() {
    bindings.enabled = true;
    bindings.tail_prefix_enabled = true;
    bindings.first_storage_slot = storage_slot;
    bindings.first_fallback_slot = fallback_slot;
    bindings.remaining_character_storage_slot = character_storage_slot;
    bindings.remaining_character_fallback_slot = character_fallback_slot;
    bindings.remaining_government_fallback_slot = government_fallback_slot;
    bindings.tail_prefix_default_relation_slot = default_relation_slot;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(character, 0x158, first_id);
    memory.Put(character, 0x1C0, land);
    memory.Put(ancestor, 0x18, std::int32_t{30000});
    memory.Put(ancestor, 0x1C, std::uint32_t{0x43686172});
    memory.Put(fallback_character, 0x18, std::int32_t{-1});
    memory.Put(fallback_character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(land, 0x1C0, relation_object);
    memory.Put(land, 0x1F8, std::int32_t{0});
    memory.Put(land, 0x3F8, government);
    memory.Put(relation_object, 0x28, ancestor);
    memory.Put(government, 0x800, predicate_key);
    memory.Put(government, 0x80C, std::uint8_t{2});
    memory.Put(character_fallback_slot, 0, fallback_character);
    memory.Put(government_fallback_slot, 0, government);
    memory.Put(default_relation_slot, 0, predicate_key);
    memory.Put(first, 0x10, first_id);
    memory.Put(first, 0x160, std::int32_t{29829});
    memory.Put(first, 0x1D8, definition275);
    memory.Put(first, 0x1E0, owner_id);
    memory.Put(first, 0x218, std::uint8_t{1});
    memory.Put(first, 0x220, definition2530);
    memory.Put(first, 0x228, std::int32_t{99});
    memory.Put(first, 0x280, std::uint8_t{2});
    memory.Put(owner, 0x10, owner_id);
    memory.Put(owner, 0x160, std::int32_t{30000});
    memory.Put(definition275, 0x260, predicate_key);
    memory.Put(definition2530, 0x38, std::uint32_t{0x4744624F});
    memory.Put(definition2530, 0x208, records);
    memory.Put(definition2530, 0x214, std::int32_t{3});
    void *storage = memory.Allocate(0x30);
    void *table = memory.Allocate(3 * 16);
    memory.Put(storage_slot, 0, storage);
    memory.Put(storage, 0x20, table);
    memory.Put(storage, 0x2C, std::uint32_t{3});
    memory.Put(table, 1 * 16 + 8, first);
    memory.Put(table, 2 * 16 + 8, owner);
    memory.Put(fallback_slot, 0, first);
    Property(At(definition275, 0x40), 111);
    Property(At(records, 2 * 0x12D0 + 0xD60), 222);
    // F20 is the actual zero-key current PC, which still produces a request.
    Property(At(records, 2 * 0x12D0 + 0x10E0), 444);
  }
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 Observe(std::size_t denied_attempts = 0) {
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "tail prefix assigned a native callback");
    Require(bindings.tail_prefix_enabled && !bindings.remaining_helpers_enabled &&
                !bindings.helper_291f0a0_enabled && !bindings.later_direct_enabled &&
                !bindings.pre_291e210_1640_enabled,
            "tail prefix fixture enabled another new leaf");
    const auto first_read = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second_read = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first_read == second_read, "tail prefix whole snapshots differ");
    Require(first_read.tail_prefix_2753860_2922530.has_value(), "tail prefix section absent");
    Require(memory.Attempts() == denied_attempts, "tail prefix unexpected field demand");
    return first_read;
  }
};
void Value(const std::optional<xar::game::ContextSourcePropertiesV1> &block, std::int64_t expected) {
  Require(block && block->keys_count == 1 && block->keys_u16 &&
              block->keys_u16->size() == 1 && block->keys_u16->at(0) == 5 &&
              block->values_q64 && block->values_q64->size() == 1 &&
              block->values_q64->at(0) == expected,
          "tail prefix selected PC values differ");
}
void Save(const std::filesystem::path &directory, const char *name,
          const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::filesystem::create_directories(directory);
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("tail prefix actual serializer wire failed");
}
} // namespace

void RunTailPrefixFixture(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  Require(bindings.tail_prefix_enabled &&
              bindings.tail_prefix_default_relation_slot == reinterpret_cast<const void *>(base + 0x5D26D50),
          "tail prefix exact binding RVA");
  {
    Fixture fixture;
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.tail_prefix_2753860_2922530;
    const auto &a = leaf.helper_2753860;
    const auto &b = leaf.helper_2922530;
    Require(leaf.ready && a.owner_admitted == true && a.relation_rows &&
                a.relation_rows->size() == 1 && a.last_character_id_18_raw == 30000,
            "tail prefix physical ancestor owner admission unavailable");
    Require(a.first_key_158_raw == static_cast<std::int32_t>(Fixture::first_id) &&
                a.owner_key_1e0_raw == static_cast<std::int32_t>(Fixture::owner_id),
            "tail prefix full generation bits lost");
    Value(a.property_block, 111);
    Require(b.ready && b.rows && b.rows->size() == 3, "tail prefix three request ordinals absent");
    for (std::size_t i = 0; i < 3; ++i)
      Require(b.rows->at(i).native_index == static_cast<std::int32_t>(i) &&
                  b.rows->at(i).admitted == true && b.rows->at(i).selected_index_raw == 2,
              "tail prefix positive upper clamp or order changed");
    Value(b.rows->at(0).property_block, 222);
    const auto &empty = b.rows->at(1).property_block;
    Require(empty && empty->keys_count == 0 && !empty->values_count &&
                empty->keys_u16 && empty->keys_u16->empty() &&
                empty->values_q64 && empty->values_q64->empty(),
            "tail prefix initialized empty F20 PC missing");
    Value(b.rows->at(2).property_block, 444);
    Save(directory, "tail-prefix-full-ancestor-order-empty", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.first, 0x218, std::uint8_t{0});
    fixture.memory.Put(fixture.definition2530, 0x38, std::uint32_t{0});
    fixture.memory.Deny(fixture.first, 0x1D8, 8);
    fixture.memory.Deny(fixture.first, 0x228, 4);
    fixture.memory.Deny(fixture.first, 0x280, 1);
    fixture.memory.Deny(fixture.character, 0x1C0, 8);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.tail_prefix_2753860_2922530;
    Require(leaf.ready && leaf.helper_2753860.caller_admitted == false &&
                !leaf.helper_2753860.definition_identity &&
                leaf.helper_2922530.admitted == false &&
                leaf.helper_2922530.rows && leaf.helper_2922530.rows->empty(),
            "tail prefix known skips demanded later fields");
    Save(directory, "tail-prefix-known-skips", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Deny(fixture.government, 0x80C, 1);
    fixture.memory.Put(fixture.definition2530, 0x208, At(fixture.records, 0x12D0));
    fixture.memory.Put(fixture.definition2530, 0x214, std::int32_t{0});
    fixture.Property(At(fixture.records, 0xD60), -222);
    fixture.Property(At(fixture.records, 0x10E0), -444);
    const auto snapshot = fixture.Observe(2);
    const auto &leaf = *snapshot.tail_prefix_2753860_2922530;
    Require(!leaf.ready && !leaf.helper_2753860.ready &&
                !leaf.helper_2753860.predicate_admitted &&
                leaf.helper_2922530.ready,
            "tail prefix partial275 blocked independent2530");
    const auto &rows = *leaf.helper_2922530.rows;
    for (const auto &row : rows)
      Require(row.count_214_raw == 0 && row.requested_index_228_raw == 99 &&
                  row.selected_index_raw == -1 && row.admitted == true,
              "tail prefix zero count added an invented positive-count gate");
    Value(rows[0].property_block, -222);
    Value(rows[2].property_block, -444);
    Save(directory, "tail-prefix-partial275-signed-zero-count", snapshot);
  }
}
