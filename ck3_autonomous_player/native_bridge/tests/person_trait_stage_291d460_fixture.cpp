#include "xar_bridge/ck3_12003_context_sources.hpp"
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
void TraitRequire(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
struct TraitMemory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    auto *p = data.get();
    regions.push_back({std::move(data), size});
    return p;
  }
  template <class T> void Put(void *p, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
  }
  void Deny(const void *p, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(p) + offset, size});
  }
  std::size_t Attempts() const {
    std::size_t count = 0;
    for (const auto &row : denied) count += row.attempts;
    return count;
  }
  static bool Read(void *context, const void *p, void *out, std::size_t size) noexcept {
    auto &memory = *static_cast<TraitMemory *>(context);
    const auto address = reinterpret_cast<std::uintptr_t>(p);
    for (auto &row : memory.denied) {
      if (address < row.begin + row.size && row.begin < address + size) {
        ++row.attempts;
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto begin = reinterpret_cast<std::uintptr_t>(region.data.get());
      if (address >= begin && address - begin <= region.size &&
          size <= region.size - static_cast<std::size_t>(address - begin)) {
        std::memcpy(out, p, size);
        return true;
      }
    }
    return false;
  }
  void *Slot(void *value) {
    auto *out = Allocate(8);
    Put(out, 0, value);
    return out;
  }
  void Property(void *p, std::initializer_list<std::pair<std::uint16_t, std::int64_t>> pairs) {
    auto *keys = Allocate(pairs.size() * 2);
    auto *values = Allocate(pairs.size() * 8);
    Put(p, 0, keys);
    Put(p, 0xC, static_cast<std::int32_t>(pairs.size()));
    Put(p, 0x68, values);
    Put(p, 0x74, static_cast<std::int32_t>(pairs.size()));
    std::size_t i = 0;
    for (const auto &[key, value] : pairs) {
      Put(keys, i * 2, key); Put(values, i * 8, value); ++i;
    }
  }
};
void *TraitAt(void *p, std::size_t offset) {
  return static_cast<std::byte *>(p) + offset;
}
struct TraitFixture {
  TraitMemory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *database = memory.Allocate(0x60);
  void *definition0 = memory.Allocate(0x2A0);
  void *definition1 = memory.Allocate(0x2A0);
  void *rite = memory.Allocate(0x980);
  void *culture = memory.Allocate(0x528);
  void *provider = memory.Allocate(0x1640);
  void *owner1 = memory.Allocate(0xC0);
  void *owner_other = memory.Allocate(0xC0);
  void *map_rows = memory.Allocate(5 * 0x38);
  void *trait_ids = memory.Allocate(3 * 4);
  void *growth_values = memory.Allocate(3 * 8);
  void *growth_tracks0 = memory.Allocate(0x650);
  void *growth_levels0 = memory.Allocate(3 * 0x200);

  TraitFixture() {
    bindings.enabled = true;
    bindings.trait_stage.enabled = true;
    bindings.read_memory = TraitMemory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.trait_stage;
    b.trait_database_slot = memory.Slot(database);
    b.trait_definition_fallback_slot = memory.Slot(definition0);
    b.definition_provider_slot = memory.Slot(provider);
    b.selector_a_storage_slot = memory.Slot(nullptr);
    b.selector_a_fallback_slot = memory.Slot(rite);
    b.selector_b_storage_slot = memory.Slot(nullptr);
    b.selector_b_fallback_slot = memory.Slot(culture);
    memory.Put(character, 0xF8, trait_ids);
    memory.Put(character, 0x104, std::int32_t{3});
    memory.Put(character, 0xB4, std::int32_t{-7});
    memory.Put(character, 0xB0, std::int32_t{-8});
    memory.Put(trait_ids, 0, std::int32_t{0});
    memory.Put(trait_ids, 4, std::int32_t{1});
    memory.Put(trait_ids, 8, std::int32_t{0});
    auto *definitions = memory.Allocate(2 * 8);
    memory.Put(database, 0x50, definitions);
    memory.Put(database, 0x5C, std::int32_t{2});
    memory.Put(definitions, 0, definition0);
    memory.Put(definitions, 8, definition1);
    memory.Put(definition0, 0x10, std::int32_t{0});
    memory.Put(definition1, 0x10, std::int32_t{1});
    memory.Property(TraitAt(definition0, 0xA0), {{5, 10}});
    memory.Property(TraitAt(definition1, 0xA0), {{5, 200}});
    memory.Property(TraitAt(owner1, 0x40), {{5, 300}});
    memory.Property(TraitAt(owner_other, 0x40), {{5, 400}});
    memory.Put(provider, 0x1620, owner1);
    memory.Put(provider, 0x1630, owner_other);
    memory.Put(rite, 0x958, map_rows);
    memory.Put(rite, 0x964, std::int32_t{0});
    memory.Put(rite, 0x968, std::uint8_t{3});
    memory.Put(map_rows, 4, std::uint8_t{1});
    memory.Put(map_rows, 8, definition0);
    memory.Put(map_rows, 0x10, std::int32_t{1});
    memory.Put(map_rows, 0x38 + 4, std::uint8_t{2});
    memory.Put(map_rows, 0x38 + 8, definition1);
    memory.Put(map_rows, 0x38 + 0x10, std::int32_t{-2});

    auto *primary_owner = memory.Allocate(0x130);
    auto *primary_header = memory.Allocate(0x18);
    auto *primary_keys = memory.Allocate(4);
    memory.Put(culture, 0x20, primary_owner);
    memory.Put(primary_owner, 0x128, primary_header);
    memory.Put(primary_header, 8, primary_keys);
    memory.Put(primary_header, 0x14, std::int32_t{1});
    memory.Put(primary_keys, 0, std::int32_t{-7});
    auto *nested_array = memory.Allocate(8);
    auto *nested_object = memory.Allocate(0x1020);
    auto *nested_keys = memory.Allocate(4);
    memory.Put(culture, 0x518, nested_array);
    memory.Put(culture, 0x524, std::int32_t{1});
    memory.Put(nested_array, 0, nested_object);
    memory.Put(nested_object, 0x1010, nested_keys);
    memory.Put(nested_object, 0x101C, std::int32_t{1});
    memory.Put(nested_keys, 0, std::int32_t{123});
    auto *a_keys = memory.Allocate(4);
    memory.Put(a_keys, 0, std::int32_t{-3});
    memory.Put(rite, 0x7B8, a_keys);
    memory.Put(rite, 0x7C4, std::int32_t{1});
    auto *b_rows = memory.Allocate(3 * 0x1C8);
    auto *a_rows = memory.Allocate(2 * 0x1C8);
    auto *base = TraitAt(definition0, 0xA0);
    memory.Put(base, 0x1C0, b_rows);
    memory.Put(base, 0x1CC, std::int32_t{3});
    memory.Put(base, 0x1D8, a_rows);
    memory.Put(base, 0x1E4, std::int32_t{2});
    memory.Put(b_rows, 0, std::int32_t{-7});
    memory.Property(TraitAt(b_rows, 8), {{5, 20}});
    memory.Put(b_rows, 0x1C8, std::int32_t{123});
    memory.Property(TraitAt(b_rows, 0x1C8 + 8), {{5, 30}});
    memory.Put(b_rows, 2 * 0x1C8, std::int32_t{777});
    memory.Deny(b_rows, 2 * 0x1C8 + 8, 0x80);
    memory.Put(a_rows, 0, std::int32_t{-3});
    memory.Property(TraitAt(a_rows, 8), {{5, 40}});
    memory.Put(a_rows, 0x1C8, std::int32_t{9});
    memory.Deny(a_rows, 0x1C8 + 8, 0x80);
    memory.Put(character, 0x140, growth_values);
    memory.Put(character, 0x14C, std::int32_t{3});
    memory.Put(growth_values, 0, std::int64_t{25});
    memory.Put(growth_values, 8, std::int64_t{0});
    memory.Put(growth_values, 16, std::int64_t{999});
    memory.Put(definition0, 0x290, growth_tracks0);
    memory.Put(definition0, 0x29C, std::int32_t{1});
    memory.Put(definition1, 0x29C, std::int32_t{1});
    memory.Deny(definition1, 0x290, 8);
    memory.Put(growth_tracks0, 0x20, growth_levels0);
    memory.Put(growth_tracks0, 0x2C, std::int32_t{3});
    memory.Property(growth_levels0, {{5, 5}});
    memory.Put(growth_levels0, 0x1F0, std::int64_t{10});
    memory.Property(TraitAt(growth_levels0, 0x200), {{5, 7}});
    memory.Put(growth_levels0, 0x200 + 0x1F0, std::int64_t{20});
    memory.Put(growth_levels0, 0x400 + 0x1F0, std::int64_t{30});
    memory.Deny(growth_levels0, 0x400, 0x80);
  }
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 Observe() {
    TraitRequire(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
                 "trait fixture has native callback");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    TraitRequire(first == second, "trait whole source snapshots differ within fixed frame");
    TraitRequire(first.trait_stage_291d460.has_value(), "trait source leaf absent");
    return first;
  }
};
void TraitSave(const std::filesystem::path &directory, const char *name,
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  TraitRequire(static_cast<bool>(output), "trait genuine wire write failed");
}
}

void RunTraitStage291d460Fixture(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindTraitStage291d46012003(base);
  const auto address = [](std::uintptr_t rva) { return reinterpret_cast<const void *>(base + rva); };
  TraitRequire(bindings.enabled && bindings.trait_database_slot == address(0x5C67528) &&
      bindings.trait_definition_fallback_slot == address(0x5D1E318) &&
      bindings.definition_provider_slot == address(0x5C670F8) &&
      bindings.selector_a_storage_slot == address(0x5D1E2F8) &&
      bindings.selector_a_fallback_slot == address(0x5C67670) &&
      bindings.selector_b_storage_slot == address(0x5D1E2F0) &&
      bindings.selector_b_fallback_slot == address(0x5D1E2E8), "trait exact raw binding differs");
  {
    TraitFixture fixture;
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.trait_stage_291d460;
    TraitRequire(leaf.ready && leaf.rows && leaf.rows->size() == 3, "positive trait source unavailable");
    const auto &first = leaf.rows->at(0);
    const auto &second = leaf.rows->at(1);
    const auto &duplicate = leaf.rows->at(2);
    TraitRequire(first.composite_ready && first.composite_groups.size() == 3 &&
        first.growth_tracks.size() == 1 && first.growth_tracks[0].thresholds_read &&
        *first.growth_tracks[0].thresholds_read == std::vector<std::int64_t>{10, 20, 30} &&
        first.growth_tracks[0].admitted_prefix_count == 2, "growth prefix threshold stop differs");
    TraitRequire(second.composite_ready && second.composite_groups.size() == 1 &&
        second.growth_tracks.size() == 1 && second.growth_tracks[0].current_value_raw == 0 &&
        !second.growth_tracks[0].level_count, "nonpositive growth demanded level definitions");
    TraitRequire(first.side.kind_raw == 1 && second.side.kind_raw == -2 &&
        second.side.probes.size() == 2 && first.side.property_identity != second.side.property_identity,
        "full-pointer probe collision or signed nonzero kind changed");
    TraitRequire(duplicate.definition_identity == first.definition_identity &&
        duplicate.growth_trait_match_index == 0 && duplicate.growth_tracks[0].current_value_raw == 25 &&
        duplicate.side.property_identity == first.side.property_identity,
        "duplicate trait did not retain first-growth match and contribution");
    TraitRequire(fixture.memory.Attempts() == 0, "positive trait queried unused conditional or level bytes");
    TraitSave(directory, "trait-stage-positive-growth", snapshot);
  }
  {
    TraitFixture fixture;
    fixture.memory.Deny(fixture.rite, 0x958, 8);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.trait_stage_291d460;
    TraitRequire(!leaf.ready && leaf.rows && leaf.rows->at(0).composite_ready &&
        !leaf.rows->at(0).side.ready && leaf.rows->at(1).composite_ready,
        "partial side suppressed independent full composites");
    TraitSave(directory, "trait-stage-side-partial", snapshot);
  }
  {
    TraitFixture fixture;
    fixture.memory.Put(fixture.character, 0x104, std::int32_t{0});
    fixture.memory.Deny(fixture.character, 0xF8, 8);
    fixture.memory.Deny(fixture.character, 0xB0, 8);
    fixture.memory.Deny(fixture.character, 0x1A5, 1);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.trait_stage_291d460;
    TraitRequire(leaf.ready && leaf.trait_count == 0 && leaf.rows && leaf.rows->empty() &&
        !leaf.selector_a_identity && !leaf.selector_b_identity && fixture.memory.Attempts() == 0,
        "empty trait list demanded selector/provider/growth fields");
    TraitSave(directory, "trait-stage-empty-traits", snapshot);
  }
  {
    TraitFixture fixture;
    fixture.memory.Put(fixture.character, 0x104, std::int32_t{1});
    fixture.memory.Put(fixture.character, 0x1A5, std::uint8_t{1});
    auto *pc = TraitAt(fixture.definition0, 0xA0);
    fixture.memory.Put(pc, 0xC, std::int32_t{0});
    fixture.memory.Put(pc, 0x1CC, std::int32_t{0});
    fixture.memory.Put(pc, 0x1E4, std::int32_t{0});
    fixture.memory.Put(fixture.map_rows, 4, std::uint8_t{0});
    fixture.memory.Deny(fixture.definition0, 0x29C, 4);
    fixture.memory.Deny(fixture.character, 0x140, 0x10);
    fixture.memory.Deny(fixture.character, 0xB0, 4);
    fixture.memory.Deny(fixture.bindings.trait_stage.definition_provider_slot, 0, 8);
    const auto snapshot = fixture.Observe();
    const auto &leaf = *snapshot.trait_stage_291d460;
    TraitRequire(leaf.ready && leaf.rows && leaf.rows->size() == 1 &&
        leaf.rows->at(0).growth_selection == "empty_character_flag" &&
        !leaf.rows->at(0).track_count_raw && leaf.rows->at(0).side.kind_raw == 0 &&
        !leaf.rows->at(0).side.property_block && fixture.memory.Attempts() == 0,
        "flag-empty growth or neutral side demanded unused operands");
    TraitSave(directory, "trait-stage-flag-neutral-empty", snapshot);
  }
}
