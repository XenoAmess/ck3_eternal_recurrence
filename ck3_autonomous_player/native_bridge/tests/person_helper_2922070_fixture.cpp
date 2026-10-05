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
#include <utility>
#include <vector>

namespace {
void Require(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
void *At(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
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

struct Fixture {
  static constexpr std::uint32_t query_first_id = 0xFE000001U;
  static constexpr std::uint32_t first_a_id = 0x02000002U;
  static constexpr std::uint32_t first_b_id = 0xE0000003U;
  static constexpr std::uint32_t character_b_id = 0xBC000002U;
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *character_a = memory.Allocate(0x1D8);
  void *character_b = memory.Allocate(0x1D8);
  void *fallback_character = memory.Allocate(0x1D8);
  void *land = memory.Allocate(0x400);
  void *land_a = memory.Allocate(0x400);
  void *land_b = memory.Allocate(0x400);
  void *subject = memory.Allocate(0x30);
  void *subject_a = memory.Allocate(0x30);
  void *subject_b = memory.Allocate(0x30);
  void *government = memory.Allocate(0x4D8);
  void *query_first = memory.Allocate(0x288);
  void *first_a = memory.Allocate(0x288);
  void *first_b = memory.Allocate(0x288);
  void *definition_query = memory.Allocate(0x218);
  void *definition_a = memory.Allocate(0x218);
  void *definition_b = memory.Allocate(0x218);
  void *records_query = memory.Allocate(0x12D0);
  void *records_a = memory.Allocate(0x12D0);
  void *records_b = memory.Allocate(2 * 0x12D0);
  void *descendant_a = memory.Allocate(0x28);
  void *descendant_b = memory.Allocate(0x28);
  void *member_false = memory.Allocate(0x38);
  void *member_true = memory.Allocate(0x38);
  void *descendant_data = memory.Allocate(3 * 4);
  void *membership_data = memory.Allocate(3 * 4);
  void *first_storage_slot = memory.Allocate(8);
  void *first_fallback_slot = memory.Allocate(8);
  void *character_storage_slot = memory.Allocate(8);
  void *character_fallback_slot = memory.Allocate(8);
  void *government_fallback_slot = memory.Allocate(8);
  void *descendant_storage_slot = memory.Allocate(8);
  void *descendant_fallback_slot = memory.Allocate(8);
  void *descendant_fallback_header = memory.Allocate(0x10);
  void *membership_storage_slot = memory.Allocate(8);
  void *membership_fallback_slot = memory.Allocate(8);
  void *membership_fallback_header = memory.Allocate(0x10);

  void Registry(void *slot, std::uint32_t capacity,
                const std::vector<std::pair<std::uint32_t, void *>> &entries) {
    void *store = memory.Allocate(0x30);
    void *table = memory.Allocate(static_cast<std::size_t>(capacity) * 16);
    memory.Put(slot, 0, store);
    memory.Put(store, 0x20, table);
    memory.Put(store, 0x2C, capacity);
    for (const auto &[index, pointer] : entries)
      memory.Put(table, static_cast<std::size_t>(index) * 16 + 8, pointer);
  }
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
  void Character(void *pointer, std::uint32_t id, std::uint32_t first_id,
                 void *selected_land, void *selected_subject) {
    memory.Put(pointer, 0x18, id);
    memory.Put(pointer, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(pointer, 0x158, first_id);
    memory.Put(pointer, 0x1C0, selected_land);
    memory.Put(selected_land, 0x1C0, selected_subject);
    memory.Put(selected_land, 0x3F8, government);
    memory.Put(selected_subject, 0x28, pointer);
    memory.Put(selected_land, 0x1E0, membership_data);
    memory.Put(selected_land, 0x1EC, std::int32_t{3});
  }
  void First(void *pointer, std::uint32_t id, std::uint32_t owner_id,
             void *definition, void *records, std::int32_t count, std::int32_t requested) {
    memory.Put(pointer, 0x10, id);
    memory.Put(pointer, 0x160, owner_id);
    memory.Put(pointer, 0x220, definition);
    memory.Put(pointer, 0x228, requested);
    memory.Put(pointer, 0x280, std::uint8_t{2});
    memory.Put(definition, 0x38, std::uint32_t{0x4744624FU});
    memory.Put(definition, 0x208, records);
    memory.Put(definition, 0x214, count);
  }
  Fixture() {
    bindings.enabled = true;
    bindings.helper_2922070_enabled = true;
    bindings.first_storage_slot = first_storage_slot;
    bindings.first_fallback_slot = first_fallback_slot;
    bindings.remaining_character_storage_slot = character_storage_slot;
    bindings.remaining_character_fallback_slot = character_fallback_slot;
    bindings.remaining_government_fallback_slot = government_fallback_slot;
    bindings.helper_2922070_descendant_storage_slot = descendant_storage_slot;
    bindings.helper_2922070_descendant_fallback_slot = descendant_fallback_slot;
    bindings.helper_2922070_descendant_fallback_header = descendant_fallback_header;
    bindings.helper_2922070_membership_storage_slot = membership_storage_slot;
    bindings.helper_2922070_membership_fallback_slot = membership_fallback_slot;
    bindings.helper_2922070_membership_fallback_header = membership_fallback_header;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    memory.Put(government, 0x4D6, std::uint8_t{5});
    memory.Put(government, 0x40, std::uint64_t{0x1000000400ULL});
    memory.Put(character_fallback_slot, 0, fallback_character);
    memory.Put(government_fallback_slot, 0, government);
    memory.Put(first_fallback_slot, 0, query_first);
    memory.Put(descendant_fallback_slot, 0, descendant_a);
    memory.Put(membership_fallback_slot, 0, member_true);
    memory.Put(fallback_character, 0x18, std::int32_t{-1});
    memory.Put(fallback_character, 0x1C, std::uint32_t{0x43686172U});
    // Equal full IDs on distinct A/query pointers must survive pointer dedup.
    Character(character, 29829U, query_first_id, land, subject);
    Character(character_a, 29829U, first_a_id, land_a, subject_a);
    Character(character_b, character_b_id, first_b_id, land_b, subject_b);
    memory.Put(land, 0x218, descendant_data);
    memory.Put(land, 0x224, std::int32_t{3});
    memory.Put(descendant_a, 8, std::uint32_t{0xA1000001U});
    memory.Put(descendant_a, 0x20, character_a);
    memory.Put(descendant_b, 8, std::uint32_t{0xB2000002U});
    memory.Put(descendant_b, 0x20, character_b);
    memory.Put(descendant_data, 0, std::uint32_t{0xA1000001U});
    memory.Put(descendant_data, 4, std::uint32_t{0xB2000002U});
    memory.Put(descendant_data, 8, std::uint32_t{0xA1000001U});
    memory.Put(member_false, 0x10, std::uint32_t{0x11000001U});
    memory.Put(member_true, 0x10, std::uint32_t{0x22000002U});
    memory.Put(member_true, 0x32, std::uint8_t{1});
    memory.Put(membership_data, 0, std::uint32_t{0x11000001U});
    memory.Put(membership_data, 4, std::uint32_t{0x22000002U});
    memory.Put(membership_data, 8, std::uint32_t{0x33000003U});
    Registry(first_storage_slot, 4U, {{1U, query_first}, {2U, first_a}, {3U, first_b}});
    Registry(character_storage_slot, 29830U, {{29829U, character_a}, {2U, character_b}});
    Registry(descendant_storage_slot, 3U, {{1U, descendant_a}, {2U, descendant_b}});
    Registry(membership_storage_slot, 3U, {{1U, member_false}, {2U, member_true}});
    First(query_first, query_first_id, 29829U, definition_query, records_query, 1, 7);
    First(first_a, first_a_id, 29829U, definition_a, records_a, 1, -9);
    // Native signed clamp count0/request9 yields index-1 at the real prior record.
    First(first_b, first_b_id, character_b_id, definition_b, At(records_b, 0x12D0), 0, 9);
    Property(At(records_a, 0xBA0), std::int64_t{111});
    Property(At(records_b, 0xBA0), std::int64_t{222});
    // The query BA0 current PC is initialized empty and still emits a request.
  }
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 Observe(std::size_t denied_attempts = 0) {
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "2922070 assigned a native callback");
    Require(bindings.helper_2922070_enabled && !bindings.tail_prefix_enabled &&
                !bindings.remaining_helpers_enabled && !bindings.helper_291f0a0_enabled &&
                !bindings.later_direct_enabled && !bindings.pre_291e210_1640_enabled,
            "2922070 fixture enabled another leaf");
    const auto a = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto b = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    Require(a == b, "2922070 whole same-frame snapshots differ");
    Require(a.helper_2922070.has_value(), "2922070 section absent");
    Require(memory.Attempts() == denied_attempts, "2922070 unexpected source demand");
    return a;
  }
};
void Value(const std::optional<xar::game::ContextSourcePropertiesV1> &block, std::int64_t expected) {
  Require(block && block->keys_count == 1 && block->keys_u16 &&
              block->keys_u16->size() == 1 && block->keys_u16->at(0) == std::uint16_t{5} &&
              block->values_q64 && block->values_q64->size() == 1 && block->values_q64->at(0) == expected,
          "2922070 actual BA0 PC differs");
}
void Save(const std::filesystem::path &directory, const char *name,
          const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::filesystem::create_directories(directory);
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("2922070 actual serializer wire failed");
}
} // namespace

void RunHelper2922070Fixture(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bound = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  Require(bound.helper_2922070_enabled &&
              bound.helper_2922070_descendant_storage_slot == reinterpret_cast<const void *>(base + 0x5D1EB88) &&
              bound.helper_2922070_descendant_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1EB40) &&
              bound.helper_2922070_descendant_fallback_header == reinterpret_cast<const void *>(base + 0x54596D8) &&
              bound.helper_2922070_membership_storage_slot == reinterpret_cast<const void *>(base + 0x5D1DAF8) &&
              bound.helper_2922070_membership_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1DAE0) &&
              bound.helper_2922070_membership_fallback_header == reinterpret_cast<const void *>(base + 0x5459C88),
          "2922070 exact binding RVAs differ");
  {
    Fixture fixture;
    fixture.memory.Deny(fixture.subject, 8, 4);
    fixture.memory.Deny(fixture.membership_data, 8, 4);
    fixture.memory.Deny(fixture.descendant_fallback_slot, 0, 8);
    fixture.memory.Deny(fixture.membership_fallback_slot, 0, 8);
    fixture.memory.Deny(fixture.first_fallback_slot, 0, 8);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.helper_2922070;
    Require(leaf.ready && leaf.gate_ready && leaf.collection_ready && leaf.rows_ready &&
                leaf.walk_nodes && leaf.walk_nodes->size() == 4 &&
                leaf.characters && leaf.characters->size() == 4 &&
                leaf.character_order == std::vector<std::int32_t>({0, 3, 1}),
            "2922070 DFS duplicates/stable equal IDs/pointer dedup differ");
    Require(leaf.membership_rows && leaf.membership_rows->size() == 3 &&
                leaf.output_ids == std::vector<std::int32_t>({
                    static_cast<std::int32_t>(Fixture::first_a_id),
                    static_cast<std::int32_t>(Fixture::query_first_id),
                    static_cast<std::int32_t>(Fixture::first_b_id)}),
            "2922070 full DWORD append membership differs");
    for (const auto &row : *leaf.membership_rows)
      Require(row.scans.size() == 2 && row.admitted == true && row.appended == true,
              "2922070 failed first-match membership short circuit");
    const auto &rows = *leaf.rows;
    Require(rows.size() == 3 && rows[0].input_index == 0 && rows[1].input_index == 2 &&
                rows[2].input_index == 1 && rows[0].selected_index_raw == 0 &&
                rows[1].count_214_raw == 0 && rows[1].selected_index_raw == -1,
            "2922070 unsigned final order/signed zero-count index differs");
    Value(rows[0].property_block, std::int64_t{111});
    Value(rows[1].property_block, std::int64_t{222});
    Require(rows[2].property_block && rows[2].property_block->keys_count == 0 &&
                !rows[2].property_block->values_count && rows[2].property_block->keys_u16 &&
                rows[2].property_block->keys_u16->empty() && rows[2].property_block->values_q64 &&
                rows[2].property_block->values_q64->empty(),
            "2922070 empty initialized BA0 request lost");
    Save(directory, "helper-2922070-full-dfs-equal-id-order-zero-count", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.first_a, 0x280, std::uint8_t{3});
    fixture.memory.Put(fixture.definition_b, 0x38, std::uint32_t{0});
    fixture.memory.Deny(fixture.first_a, 0x220, 8);
    fixture.memory.Deny(fixture.first_b, 0x228, 4);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.helper_2922070;
    Require(leaf.ready && leaf.rows && leaf.rows->size() == 3 &&
                leaf.rows->at(0).admitted == false && !leaf.rows->at(0).definition_identity &&
                leaf.rows->at(1).admitted == false && !leaf.rows->at(1).requested_index_228_raw &&
                leaf.rows->at(2).admitted == true && leaf.rows->at(2).native_index == 2,
            "2922070 row guards demanded later fields or compressed native ordinals");
    Save(directory, "helper-2922070-row-skips-retain-ordinal", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.government, 0x4D6, std::uint8_t{4});
    fixture.memory.Deny(fixture.land, 0x1C0, 8);
    fixture.memory.Deny(fixture.land, 0x218, 8);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.helper_2922070;
    Require(leaf.ready && leaf.gate_ready && leaf.admitted == false &&
                !leaf.character_land_present && !leaf.walk_nodes && !leaf.rows,
            "2922070 government known skip demanded downstream fields");
    Save(directory, "helper-2922070-government-known-skip", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.subject, 0xC, std::uint32_t{0x5362436FU});
    fixture.memory.Put(fixture.subject, 8, std::uint32_t{0xFF000004U});
    fixture.memory.Deny(fixture.land, 0x218, 8);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.helper_2922070;
    Require(leaf.ready && leaf.admitted == false &&
                leaf.subject_id_8_raw == static_cast<std::int32_t>(0xFF000004U) && !leaf.walk_nodes,
            "2922070 legitimate negative generation ID SbCo skip lost");
    Save(directory, "helper-2922070-sbco-negative-generation-known-skip", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.descendant_storage_slot, 0, static_cast<void *>(nullptr));
    fixture.memory.Deny(fixture.descendant_data, 0, 12);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.helper_2922070;
    Require(leaf.ready && leaf.walk_nodes && leaf.walk_nodes->at(0).edges.size() == 3 &&
                !leaf.walk_nodes->at(0).edges[0].requested_id_raw &&
                leaf.walk_nodes->at(0).edges[0].selection == "native_fallback" &&
                leaf.character_order == std::vector<std::int32_t>({0, 3}) &&
                leaf.rows && leaf.rows->size() == 2,
            "2922070 null descendant store demanded unused key or lost fallback occurrences");
    Save(directory, "helper-2922070-null-descendant-store-lazy-key", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Deny(fixture.character_a, 0x18, 4);
    const auto snapshot = fixture.Observe(2);
    const auto &leaf = *snapshot.helper_2922070;
    Require(!leaf.ready && leaf.gate_ready && leaf.admitted == true &&
                !leaf.collection_ready && !leaf.rows_ready && leaf.walk_nodes &&
                leaf.walk_nodes->at(0).edges.size() == 1 &&
                leaf.walk_nodes->at(0).edges[0].holder_identity &&
                !leaf.walk_nodes->at(0).edges[0].holder_id_18_raw && !leaf.characters,
            "2922070 unavailable DFS read discarded raw gate/holder receipt");
    Save(directory, "helper-2922070-partial-holder-id", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Deny(At(fixture.records_query, 0xBA0), 0xC, 4);
    const auto snapshot = fixture.Observe(2);
    const auto &leaf = *snapshot.helper_2922070;
    Require(!leaf.ready && leaf.gate_ready && leaf.collection_ready && !leaf.rows_ready &&
                leaf.rows && leaf.rows->size() == 3 && leaf.rows->at(2).property_identity,
            "2922070 partial PC hid complete collection/ordered rows");
    Value(leaf.rows->at(0).property_block, std::int64_t{111});
    Value(leaf.rows->at(1).property_block, std::int64_t{222});
    Save(directory, "helper-2922070-partial-pc-independent-collection", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.land, 0x224, std::int32_t{0});
    fixture.memory.Put(fixture.land, 0x1EC, std::int32_t{0});
    fixture.memory.Deny(fixture.query_first, 0x280, 1);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.helper_2922070;
    Require(leaf.ready && leaf.character_order == std::vector<std::int32_t>({0}) &&
                leaf.characters && !leaf.characters->at(0).character_id_18_raw &&
                leaf.output_ids && leaf.output_ids->empty() && leaf.rows && leaf.rows->empty(),
            "2922070 singleton/zero membership invented comparator or row demands");
    Save(directory, "helper-2922070-singleton-empty-membership", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.land, 0x224, std::int32_t{0});
    fixture.memory.Put(fixture.membership_storage_slot, 0, static_cast<void *>(nullptr));
    fixture.memory.Deny(fixture.membership_data, 0, 4);
    const auto snapshot = fixture.Observe(2);
    const auto &leaf = *snapshot.helper_2922070;
    Require(!leaf.ready && leaf.gate_ready && leaf.membership_rows &&
                leaf.membership_rows->size() == 1 &&
                !leaf.membership_rows->at(0).scans[0].requested_id_raw &&
                !leaf.membership_rows->at(0).admitted && !leaf.rows,
            "2922070 membership null store skipped actually demanded key");
    Save(directory, "helper-2922070-null-membership-store-key-demand-partial", snapshot);
  }
}
