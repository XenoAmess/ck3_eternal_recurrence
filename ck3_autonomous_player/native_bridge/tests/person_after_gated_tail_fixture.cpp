#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
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
    std::size_t result = 0;
    for (const auto &entry : denied) result += entry.attempts;
    return result;
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
constexpr std::uint32_t kPositionA = 0xAA000001U;
constexpr std::uint32_t kPositionB = 0xBB000002U;
constexpr std::uint32_t kPositionC = 0xCC000003U;
constexpr std::uint32_t kPositionD = 0xDD000004U;
constexpr std::uint32_t kRelated = 0xAB000001U;

// Every source byte is initialized before either query. No fake read mutates
// the frame; the production DTO is compared in full and serialized in full.
struct Fixture {
  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *carrier = memory.Allocate(0xF0);
  void *land = memory.Allocate(0x460);
  void *selected = memory.Allocate(0x190);
  void *composition_definition = memory.Allocate(0x68);
  void *level_rows = memory.Allocate(3 * 0x3D0);
  void *month_rows = memory.Allocate(3 * 0x3D0);
  void *global = memory.Allocate(0x2B8);
  void *clock = memory.Allocate(0xB0);
  void *played = memory.Allocate(0x22368);
  void *static_date = memory.Allocate(8);
  void *global_slot = memory.Allocate(8);
  void *clock_slot = memory.Allocate(8);
  void *character_storage_slot = memory.Allocate(8);
  void *character_fallback_slot = memory.Allocate(8);
  void *character_store = memory.Allocate(0x30);
  void *character_table = memory.Allocate(2 * 16);
  void *related = memory.Allocate(0x1D8);
  void *related_land = memory.Allocate(0x460);
  void *position_storage_slot = memory.Allocate(8);
  void *position_fallback_slot = memory.Allocate(8);
  void *position_store = memory.Allocate(0x30);
  void *position_table = memory.Allocate(5 * 16);
  void *position_a = memory.Allocate(0x128);
  void *position_b = memory.Allocate(0x128);
  void *position_c = memory.Allocate(0x128);
  void *position_d = memory.Allocate(0x128);
  void *definition_a = memory.Allocate(0x4200);
  void *definition_b = memory.Allocate(0x4200);
  void *definition_c = memory.Allocate(0x4200);
  void *definition_d = memory.Allocate(0x4200);
  void *other_a = memory.Allocate(0x3200);
  void *other_b = memory.Allocate(0x3200);
  void *other_c = memory.Allocate(0x3200);
  void *other_d = memory.Allocate(0x3200);
  void *current_1b8_ids = memory.Allocate(2 * 4);
  void *current_land_ids = memory.Allocate(3 * 4);
  void *related_land_ids = memory.Allocate(4);
  void *default_header = memory.Allocate(0x18);
  void *default_guard = memory.Allocate(4);
  void *selector_a_slot = memory.Allocate(8);
  void *selector_a_fallback = memory.Allocate(8);
  void *selector_b_slot = memory.Allocate(8);
  void *selector_b_fallback = memory.Allocate(8);
  void *selector_a_store = memory.Allocate(0x30);
  void *selector_b_store = memory.Allocate(0x30);
  void *selector_a_table = memory.Allocate(2 * 16);
  void *selector_b_table = memory.Allocate(2 * 16);
  void *selector_a = memory.Allocate(0x7C8);
  void *selector_b = memory.Allocate(0x528);
  void *selector_b_owner = memory.Allocate(0x130);
  void *selector_b_header = memory.Allocate(0x18);
  void *conditional_b_rows = memory.Allocate(0x1C8);
  void *conditional_a_rows = memory.Allocate(0x1C8);

  void Property(void *pc, const std::vector<std::uint16_t> &keys,
                const std::vector<std::int64_t> &values) {
    Require(keys.size() == values.size(), "after-gated property pair size");
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
  void PC(void *definition, std::size_t offset, std::uint16_t key,
          std::int64_t value) {
    Property(At(definition, offset), {key}, {value});
  }
  void Date(void *address, std::size_t offset, std::int32_t raw,
            std::int8_t day, std::int8_t month, std::int16_t year) {
    memory.Put(address, offset, raw);
    memory.Put(address, offset + 4, day);
    memory.Put(address, offset + 5, month);
    memory.Put(address, offset + 6, year);
  }
  void Registry(void *store, void *table, std::uint32_t capacity) {
    memory.Put(store, 0x20, table);
    memory.Put(store, 0x2C, capacity);
  }
  void Position(void *position, std::uint32_t full_id, void *definition,
                void *other) {
    memory.Put(position, 8, full_id);
    memory.Put(position, 0xA0, std::uint8_t{2});
    memory.Put(position, 0x110, definition);
    memory.Put(position, 0x118, other);
    memory.Put(position, 0x120, std::int32_t{-1});
    memory.Put(position, 0x124, std::uint32_t{0xEE000007U});
    memory.Put(position_table, (full_id & 0xFFFFFFU) * 16 + 8, position);
    memory.Put(other, 0x38, std::uint32_t{0x4744624FU});
  }
  void Thresholds(void *definition, const std::vector<std::int32_t> &values) {
    void *array = memory.Allocate(values.size() * 4);
    memory.Put(definition, 0x40D8, array);
    memory.Put(definition, 0x40E4, static_cast<std::int32_t>(values.size()));
    for (std::size_t i = 0; i < values.size(); ++i)
      memory.Put(array, i * 4, values[i]);
  }
  Fixture() {
    bindings.enabled = true;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.after_gated_tail;
    b.enabled = true;
    b.global_flag_slot = global_slot;
    b.clock_slot = clock_slot;
    b.static_fifth_date = static_date;
    b.character_storage_slot = character_storage_slot;
    b.character_fallback_slot = character_fallback_slot;
    b.position_storage_slot = position_storage_slot;
    b.position_fallback_slot = position_fallback_slot;
    b.default_list_header = default_header;
    b.default_list_guard_slot = default_guard;
    b.selector_a_storage_slot = selector_a_slot;
    b.selector_a_fallback_slot = selector_a_fallback;
    b.selector_b_storage_slot = selector_b_slot;
    b.selector_b_fallback_slot = selector_b_fallback;

    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(character, 0x1B8, carrier);
    memory.Put(character, 0x1C0, land);
    memory.Put(land, 0x458, selected);
    memory.Put(selected, 0x178, composition_definition);
    memory.Put(selected, 0xF8, std::int32_t{1});
    Date(selected, 0x180, 100, 1, 1, 1000);
    Date(carrier, 0xE8, 100, 1, 0, 1000);
    Date(clock, 8, 300, 1, 3, 1000);
    Date(static_date, 0, 100, 1, 0, 1000);
    memory.Put(global_slot, 0, global);
    memory.Put(global, 0x2B0, std::uint8_t{0x20});
    memory.Put(clock_slot, 0, clock);
    memory.Put(clock, 0xA0, played);
    memory.Put(composition_definition, 0x58, level_rows);
    memory.Put(composition_definition, 0x64, std::int32_t{3});
    memory.Put(composition_definition, 0x40, month_rows);
    memory.Put(composition_definition, 0x4C, std::int32_t{3});
    for (std::size_t i = 0; i < 3; ++i) {
      const auto threshold = i == 1 ? std::int32_t{99} : static_cast<std::int32_t>(i / 2);
      memory.Put(level_rows, i * 0x3D0 + 8, threshold);
      memory.Put(month_rows, i * 0x3D0 + 8,
                 i == 2 ? std::int32_t{2} : threshold);
      PC(level_rows, i * 0x3D0 + 0x10,
         static_cast<std::uint16_t>(1 + i), static_cast<std::int64_t>(101 + i));
      PC(month_rows, i * 0x3D0 + 0x10,
         static_cast<std::uint16_t>(4 + i), static_cast<std::int64_t>(104 + i));
    }
    memory.Put(carrier, 0xCC, kRelated);
    memory.Put(carrier, 0xC8, kRelated);
    memory.Put(character_storage_slot, 0, character_store);
    memory.Put(character_fallback_slot, 0, character);
    Registry(character_store, character_table, 2U);
    memory.Put(character_table, 16 + 8, related);
    memory.Put(related, 0x18, kRelated);
    memory.Put(related, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(related, 0x1C0, related_land);

    memory.Put(position_storage_slot, 0, position_store);
    memory.Put(position_fallback_slot, 0, position_a);
    Registry(position_store, position_table, 5U);
    Position(position_a, kPositionA, definition_a, other_a);
    Position(position_b, kPositionB, definition_b, other_b);
    Position(position_c, kPositionC, definition_c, other_c);
    Position(position_d, kPositionD, definition_d, other_d);
    memory.Put(current_1b8_ids, 0, kPositionA);
    memory.Put(current_1b8_ids, 4, kPositionA);
    memory.Put(carrier, 0xD0, current_1b8_ids);
    memory.Put(carrier, 0xDC, std::int32_t{2});
    memory.Put(current_land_ids, 0, kPositionB);
    memory.Put(current_land_ids, 4, kPositionB);
    memory.Put(current_land_ids, 8, kPositionD);
    memory.Put(land, 0x3B8, current_land_ids);
    memory.Put(land, 0x3C4, std::int32_t{2});
    memory.Put(related_land_ids, 0, kPositionC);
    memory.Put(related_land, 0x3B8, related_land_ids);
    memory.Put(related_land, 0x3C4, std::int32_t{1});
    memory.Put(default_header, 0, related_land_ids);
    memory.Put(default_header, 0xC, std::int32_t{1});
    memory.Put(default_guard, 0, std::int32_t{9});

    PC(definition_a, 0x2748, 10, 1000);
    PC(definition_a, 0x2AC8, 11, 1100);
    PC(other_a, 0x1940, 14, 1400);
    PC(definition_b, 0x2908, 20, 2000);
    PC(definition_b, 0x2CB8 + 2 * 0x1C0, 21, 2100);
    PC(definition_b, 0x2CB8, 25, 2500);
    PC(definition_b, 0x2AC8, 22, 2200);
    PC(other_b, 0x1B00, 23, 2300);
    PC(other_b, 0x1CC0 + 2 * 0x1C0, 24, 2400);
    PC(other_b, 0x1CC0, 26, 2600);
    PC(definition_c, 0x3658, 30, 3000);
    PC(other_c, 0x2740, 32, 3200);
    PC(definition_d, 0x2908, 40, 4000);
    PC(definition_d, 0x2CB8 + 0x1C0, 41, 4100);
    memory.Put(other_d, 0x38, std::uint32_t{0});

    memory.Put(definition_a, 0x2C88, conditional_b_rows);
    memory.Put(definition_a, 0x2C94, std::int32_t{1});
    memory.Put(definition_a, 0x2CA0, conditional_a_rows);
    memory.Put(definition_a, 0x2CAC, std::int32_t{1});
    memory.Put(conditional_b_rows, 0, std::int32_t{7});
    PC(conditional_b_rows, 8, 12, 1200);
    memory.Put(conditional_a_rows, 0, std::int32_t{13});
    PC(conditional_a_rows, 8, 13, 1300);
    memory.Put(character, 0xB0, std::uint32_t{0xBA000001U});
    memory.Put(character, 0xB4, std::uint32_t{0xCA000001U});
    memory.Put(selector_b_slot, 0, selector_b_store);
    memory.Put(selector_a_slot, 0, selector_a_store);
    memory.Put(selector_b_fallback, 0, selector_b);
    memory.Put(selector_a_fallback, 0, selector_a);
    Registry(selector_b_store, selector_b_table, 2U);
    Registry(selector_a_store, selector_a_table, 2U);
    memory.Put(selector_b_table, 16 + 8, selector_b);
    memory.Put(selector_a_table, 16 + 8, selector_a);
    memory.Put(selector_b, 0x10, std::uint32_t{0xBA000001U});
    memory.Put(selector_a, 8, std::uint32_t{0xCA000001U});
    memory.Put(selector_b, 0x20, selector_b_owner);
    memory.Put(selector_b_owner, 0x128, selector_b_header);
    void *b_keys = memory.Allocate(4);
    memory.Put(b_keys, 0, std::int32_t{7});
    memory.Put(selector_b_header, 8, b_keys);
    memory.Put(selector_b_header, 0x14, std::int32_t{1});
    void *a_keys = memory.Allocate(4);
    memory.Put(a_keys, 0, std::int32_t{13});
    memory.Put(selector_a, 0x7B8, a_keys);
    memory.Put(selector_a, 0x7C4, std::int32_t{1});

    // The original always-collected source leaves have actual empty headers.
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
  }
  Snapshot Observe() {
    Require(bindings.enabled && bindings.after_gated_tail.enabled,
            "after-gated source binding disabled");
    Require(!bindings.gated_temporary_tail.enabled &&
                !bindings.pre_291e210_1640_enabled && !bindings.later_direct_enabled &&
                !bindings.helper_291f0a0_enabled && !bindings.remaining_helpers_enabled &&
                !bindings.tail_direct_enabled && !bindings.post_291d7e0_sources_enabled &&
                !bindings.trait_stage.enabled && !bindings.middle_helpers.enabled &&
                !bindings.tail_prefix_enabled && !bindings.helper_2922070_enabled,
            "other optional source leaf enabled");
    Require(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
            "after-gated fixture must not install native callbacks");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first == second, "after-gated whole snapshots differ in fixed frame");
    Require(first.after_gated_tail_326a8e0_2920310.has_value(), "after-gated leaf absent");
    Require(memory.Attempts() == 0, "after-gated unused numeric source was demanded");
    return first;
  }
  void EmptyCurrentLists() {
    memory.Put(carrier, 0xDC, std::int32_t{0});
    memory.Put(land, 0x3C4, std::int32_t{0});
    memory.Deny(carrier, 0xD0, 8);
    memory.Deny(land, 0x3B8, 8);
  }
};

void Save(const std::filesystem::path &directory, const char *name,
          const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string("after-gated-") + name + ".json"),
                       std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("after-gated wire write failed");
}
void PCValue(const auto &pc, std::uint16_t key, std::int64_t value) {
  Require(pc.property_identity && pc.property_block &&
              pc.property_block->keys_u16 && pc.property_block->values_q64 &&
              pc.property_block->keys_u16->size() == 1 &&
              pc.property_block->values_q64->size() == 1 &&
              pc.property_block->keys_u16->at(0) == key &&
              pc.property_block->values_q64->at(0) == value,
          "after-gated paired raw property operands differ");
}
void EmptyPC(const auto &pc) {
  Require(pc.property_identity && pc.property_block &&
              pc.property_block->keys_count == 0 && !pc.property_block->values_count &&
              pc.property_block->keys_u16 && pc.property_block->keys_u16->empty() &&
              pc.property_block->values_q64 && pc.property_block->values_q64->empty(),
          "after-gated actual zero-key PC differs");
}
void FullLists(const auto &leaf) {
  const auto &first = leaf.current_1b8_court_positions;
  const auto &land = leaf.current_1c0_court_positions;
  const auto &related = leaf.related_court_positions;
  Require(first.ready && first.rows && first.rows->size() == 2 && land.ready &&
              land.rows && land.rows->size() == 2 && related.ready && related.rows &&
              related.rows->size() == 1,
          "after-gated CourtPosition family counts differ");
  for (std::size_t i = 0; i < 2; ++i) {
    const auto &a = first.rows->at(i);
    const auto &b = land.rows->at(i);
    Require(a.native_index == static_cast<std::int32_t>(i) && a.ready &&
                a.requested_full_id_raw == static_cast<std::int32_t>(kPositionA) &&
                a.position_selection == "registry_full_id_8" &&
                a.position_full_id_raw == static_cast<std::int32_t>(kPositionA) &&
                a.position_identity == first.rows->at(0).position_identity &&
                a.composite_group && a.composite_group->ready &&
                a.composite_group->conditional_b_rows &&
                a.composite_group->conditional_b_rows->at(0).admitted == true &&
                a.composite_group->conditional_a_rows &&
                a.composite_group->conditional_a_rows->at(0).admitted == true &&
                a.other_admitted == true,
            "after-gated full-ID duplicate or composite predicates differ");
    PCValue(a.base_pc, 10, 1000);
    PCValue(a.other_base_pc, 14, 1400);
    Require(b.ready && b.kind.ready && b.other_kind.ready &&
                b.kind.kind_raw == 2 && b.other_kind.kind_raw == 2 &&
                b.kind.owner_played == false && b.kind.raw_a0_u8 == std::uint8_t{2} &&
                !b.kind.threshold_count_raw && b.kind.rule.selection == std::nullopt,
            "after-gated ordinary raw kind must skip Def600");
    PCValue(b.base_pc, 20, 2000);
    PCValue(b.tier_pc, 21, 2100);
    PCValue(b.other_base_pc, 23, 2300);
    PCValue(b.other_tier_pc, 24, 2400);
  }
  const auto &c = related.rows->at(0);
  Require(c.ready && c.definition_pair_admitted == true && c.other_pair_admitted == true &&
              c.definition_pair_probes.size() == 1 && c.other_pair_probes.size() == 2 &&
              c.definition_pair_probes.at(0).count_raw == 1 &&
              c.other_pair_probes.at(0).count_raw == 0 &&
              c.other_pair_probes.at(1).count_raw == 1 &&
              c.kind.kind_raw == 2 && c.other_kind.kind_raw == 2 && !c.composite_group,
          "after-gated related pair probes/order/kind differ");
  PCValue(c.base_pc, 30, 3000);
  EmptyPC(c.tier_pc);
  EmptyPC(c.other_base_pc);
  EmptyPC(c.other_tier_pc);
}
void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  const auto &b = bindings.after_gated_tail;
  const auto address = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  Require(bindings.enabled && b.enabled &&
              b.global_flag_slot == address(0x5CB87F8) && b.clock_slot == address(0x5C68C50) &&
              b.static_fifth_date == address(0x4763CB8) &&
              b.character_storage_slot == address(0x5C67568) &&
              b.character_fallback_slot == address(0x5C67570) &&
              b.position_storage_slot == address(0x5D1DD10) &&
              b.position_fallback_slot == address(0x5D1DD08) &&
              b.default_list_header == address(0x54E7220) &&
              b.default_list_guard_slot == address(0x5D679E0) &&
              b.selector_a_storage_slot == address(0x5D1E2F8) &&
              b.selector_a_fallback_slot == address(0x5C67670) &&
              b.selector_b_storage_slot == address(0x5D1E2F0) &&
              b.selector_b_fallback_slot == address(0x5D1E2E8),
          "after-gated exact-build source bindings differ");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "wrong-build").after_gated_tail.enabled,
          "after-gated exact-build factory accepted wrong build");
}
void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture f;
    f.memory.Deny(f.level_rows, 0x3D0 + 0x10, 0x78);
    f.memory.Deny(f.month_rows, 0x3D0 + 0x10, 0x78);
    f.memory.Deny(f.carrier, 0xEC, 4);
    f.memory.Deny(f.default_guard, 0, 4);
    f.memory.Deny(f.definition_b, 0x600, 0xC4);
    f.memory.Deny(f.definition_c, 0x600, 0xC4);
    f.memory.Deny(f.position_b, 0x124, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.after_gated_tail_326a8e0_2920310;
    const auto &c = leaf.composition_326a8e0;
    Require(snapshot.ready && leaf.ready && c.ready && c.admitted == true &&
                c.receiver_selection == "current_458_178" && c.owner_mode == true &&
                c.level_raw == 1 && c.chosen_date_selection == "handle" &&
                c.completed_months_raw == 2 && c.handle_date.month_cache_i8 == std::int8_t{1} &&
                c.fifth_date.raw_i32 == 100 && !c.fifth_date.month_cache_i8 &&
                c.level_rows.rows && c.level_rows.rows->size() == 3 &&
                c.month_rows.rows && c.month_rows.rows->size() == 3,
            "after-gated signed-MAX tied raw Date must retain handle caches");
    for (std::size_t i = 0; i < 3; ++i) {
      Require(c.level_rows.rows->at(i).native_index == static_cast<std::int32_t>(i) &&
                  c.level_rows.rows->at(i).admitted == (i != 1) &&
                  c.month_rows.rows->at(i).admitted == (i != 1),
              "after-gated row threshold rejection must continue after non-prefix miss");
    }
    PCValue(c.level_rows.rows->at(0).pc, 1, 101);
    PCValue(c.level_rows.rows->at(2).pc, 3, 103);
    PCValue(c.month_rows.rows->at(0).pc, 4, 104);
    PCValue(c.month_rows.rows->at(2).pc, 6, 106);
    FullLists(leaf);
    Save(directory, "full-order-duplicates", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.position_b, 0xA0, std::uint8_t{5});
    f.Thresholds(f.definition_b, {0, -2, -3, -4});
    f.memory.Put(f.definition_b, 0x600 + 0xC0, std::int32_t{0});
    f.memory.Put(f.definition_b, 0x600 + 0x98, std::int64_t{-100000});
    f.memory.Put(f.definition_b, 0x600 + 0xB8, f.memory.Allocate(8));
    f.memory.Deny(f.definition_b, 0x600 + 0xB8, 8);
    f.memory.Deny(f.definition_b, 0x600 + 0xA8, 8);
    f.memory.Deny(f.definition_b, 0x600 + 0x14, 4);
    f.memory.Deny(f.position_b, 0x124, 4);
    f.memory.Put(f.position_c, 0xA0, std::uint8_t{5});
    f.Thresholds(f.definition_c, {0, 1, 2, 3});
    void *named_zero = f.memory.Allocate(0x80);
    f.memory.Put(f.definition_c, 0x600 + 0xC0, std::int32_t{1});
    f.memory.Put(f.definition_c, 0x600 + 0xA8, named_zero);
    f.memory.Deny(named_zero, 0x68, 8);
    f.memory.Deny(f.definition_c, 0x600 + 0x14, 4);
    f.memory.Deny(f.definition_c, 0x600 + 0x98, 8);
    f.memory.Put(f.land, 0x3C4, std::int32_t{3});
    f.memory.Put(f.position_d, 0xA0, std::uint8_t{5});
    f.Thresholds(f.definition_d, {-2, 0, 1, 2});
    void *named_literal = f.memory.Allocate(0x80);
    f.memory.Put(named_literal, 0x7B, std::uint8_t{3});
    f.memory.Put(named_literal, 0x68, std::int64_t{-50000});
    f.memory.Put(f.definition_d, 0x600 + 0xC0, std::int32_t{1});
    f.memory.Put(f.definition_d, 0x600 + 0xA8, named_literal);
    f.memory.Deny(f.definition_d, 0x600 + 0x14, 4);
    f.memory.Deny(f.definition_d, 0x600 + 0x98, 8);
    f.memory.Deny(f.other_d, 0x1B00, 0x78);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.after_gated_tail_326a8e0_2920310;
    const auto &b = leaf.current_1c0_court_positions.rows->at(0);
    const auto &c = leaf.related_court_positions.rows->at(0);
    const auto &d = leaf.current_1c0_court_positions.rows->at(2);
    Require(snapshot.ready && leaf.ready && b.kind.kind_raw == 0 &&
                b.other_kind.kind_raw == 0 && b.kind.rule.selection == "mode_zero_raw98" &&
                b.kind.rule.value_q64 == -100000 && !b.kind.rule.tree_present &&
                !b.kind.position_124_raw && c.kind.kind_raw == 1 &&
                c.kind.rule.selection == "nested_named" && c.kind.rule.named.kind == "known_zero" &&
                c.kind.rule.value_q64 == 0 && !c.kind.rule.named.raw_fixed_q64 &&
                d.kind.kind_raw == 1 && d.kind.rule.named.kind == "literal" &&
                d.kind.rule.named.raw_fixed_q64 == -50000 && d.kind.rule.value_q64 == -50000 &&
                d.other_admitted == false,
            "after-gated mode-zero and nested-named literal precedence differ");
    PCValue(b.tier_pc, 25, 2500);
    PCValue(b.other_tier_pc, 26, 2600);
    PCValue(d.tier_pc, 41, 4100);
    EmptyPC(c.tier_pc);
    EmptyPC(c.other_tier_pc);
    Save(directory, "literal-and-named-precedence", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.global, 0x2B0, std::uint8_t{0});
    f.EmptyCurrentLists();
    f.Property(At(f.definition_c, 0x3658), {}, {});
    f.Property(At(f.other_c, 0x2740), {}, {});
    f.memory.Deny(f.selected, 0x178, 0x10);
    f.memory.Deny(f.position_c, 0x120, 8);
    f.memory.Deny(f.definition_c, 0x600, 0xC4);
    f.memory.Deny(f.default_guard, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.after_gated_tail_326a8e0_2920310;
    const auto &c = leaf.related_court_positions.rows->at(0);
    Require(snapshot.ready && leaf.ready && leaf.composition_326a8e0.admitted == false &&
                leaf.composition_326a8e0.global_bit20 == false &&
                leaf.current_1b8_court_positions.numeric_count == 0 &&
                leaf.current_1c0_court_positions.numeric_count == 0 &&
                c.definition_pair_admitted == false && c.other_pair_admitted == false &&
                c.definition_pair_probes.size() == 6 && c.other_pair_probes.size() == 6 &&
                !c.kind.kind_raw && !c.other_kind.kind_raw && !c.base_pc.property_block,
            "after-gated all-six-zero pair must skip kind and both outer requests");
    Save(directory, "bit20-false-all-pairs-empty", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.position_b, 0xA0, std::uint8_t{5});
    f.Thresholds(f.definition_b, {0, 1, 2, 3});
    f.memory.Put(f.definition_b, 0x600 + 0xC0, std::int32_t{1});
    f.memory.Put(f.definition_b, 0x600 + 0xB8, f.memory.Allocate(8));
    f.memory.Deny(f.definition_b, 0x600 + 0xA8, 8);
    f.memory.Deny(f.definition_b, 0x600 + 0x14, 4);
    f.memory.Deny(f.definition_b, 0x600 + 0x98, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.after_gated_tail_326a8e0_2920310;
    const auto &b = leaf.current_1c0_court_positions.rows->at(0);
    Require(!snapshot.ready && !leaf.ready && leaf.composition_326a8e0.ready &&
                leaf.current_1b8_court_positions.ready && leaf.related_court_positions.ready &&
                !leaf.current_1c0_court_positions.ready && !b.kind.ready &&
                !b.other_kind.ready && b.kind.rule.selection == "dynamic_tree" &&
                b.kind.rule.tree_present == true && !b.kind.rule.value_q64 &&
                !b.kind.rule.raw_98_q64 && !b.kind.kind_raw &&
                b.composite_group && b.composite_group->ready,
            "after-gated dynamic rule must preserve independent families and current direct PCs");
    PCValue(b.base_pc, 20, 2000);
    PCValue(b.other_base_pc, 23, 2300);
    Save(directory, "dynamic-partial-independent", snapshot);
  }
  {
    Fixture f;
    f.memory.Put(f.global, 0x2B0, std::uint8_t{0});
    f.EmptyCurrentLists();
    f.memory.Put(f.related, 0x1C0, static_cast<void *>(nullptr));
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.after_gated_tail_326a8e0_2920310;
    const auto &list = leaf.related_court_positions;
    Require(snapshot.ready && leaf.ready && list.ready &&
                list.header_selection == "inline_default_54e7220" &&
                list.default_init_guard_raw == 9 && list.count_raw == 1 &&
                list.numeric_count == 1 && list.array_present == true &&
                list.rows && list.rows->size() == 1 && list.related.caller_admitted == true &&
                list.related.land_present == false,
            "after-gated initialized default must release actual current header");
    PCValue(list.rows->at(0).base_pc, 30, 3000);
    EmptyPC(list.rows->at(0).tier_pc);
    Save(directory, "initialized-default-list", snapshot);
  }
  {
    Fixture f;
    f.EmptyCurrentLists();
    f.memory.Put(f.related, 0x1C0, static_cast<void *>(nullptr));
    f.memory.Put(f.default_guard, 0, std::int32_t{-1});
    f.memory.Put(f.composition_definition, 0x64, std::int32_t{0});
    f.memory.Put(f.composition_definition, 0x4C, std::int32_t{0});
    f.memory.Deny(f.composition_definition, 0x58, 8);
    f.memory.Deny(f.composition_definition, 0x40, 8);
    f.memory.Deny(f.selected, 0xF8, 4);
    f.memory.Deny(f.selected, 0x180, 8);
    f.memory.Deny(f.carrier, 0xE8, 8);
    f.memory.Deny(f.clock, 8, 8);
    f.memory.Deny(f.default_header, 0, 0x18);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.after_gated_tail_326a8e0_2920310;
    const auto &list = leaf.related_court_positions;
    const auto &composition = leaf.composition_326a8e0;
    Require(snapshot.ready && leaf.ready && composition.ready && composition.admitted == true &&
                composition.level_rows.count_raw == 0 && composition.month_rows.count_raw == 0 &&
                composition.level_rows.rows && composition.level_rows.rows->empty() &&
                composition.month_rows.rows && composition.month_rows.rows->empty() &&
                !composition.level_raw && !composition.completed_months_raw &&
                list.ready && list.header_selection == "modeled_empty_default_54e7220" &&
                list.default_init_guard_raw == -1 && list.numeric_count == 0 &&
                !list.count_raw && !list.array_present && list.rows && list.rows->empty(),
            "after-gated modeled empty must retain admitted empty326 occurrence and skip physical header");
    Save(directory, "modeled-default-and-empty-composition", snapshot);
  }
}
} // namespace

void RunAfterGatedTailFixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}
