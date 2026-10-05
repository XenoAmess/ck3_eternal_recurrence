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

// Every allocation is a zero-initialized, fixed source frame. Read failures
// describe unavailable addresses, never a per-read change in native values.
struct Memory {
  struct Region {
    std::unique_ptr<std::byte[]> data;
    std::size_t size;
  };
  struct Denied {
    std::uintptr_t begin;
    std::size_t size;
    bool unused;
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
  void DenyUnused(const void *address, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset,
                      size, true});
  }
  void Unavailable(const void *address, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(address) + offset,
                      size, false});
  }
  std::size_t Attempts(bool unused) const {
    std::size_t result = 0;
    for (const auto &entry : denied)
      if (entry.unused == unused) result += entry.attempts;
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

using Snapshot = xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1;

struct Fixture {
  static constexpr std::uint32_t weighted_id = 0xCD000001U;

  Memory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D8);
  void *land = memory.Allocate(0x400);
  void *government = memory.Allocate(0xAB0);
  void *subcarrier = memory.Allocate(0x10);
  void *carrier = memory.Allocate(0x280);
  void *selected = memory.Allocate(0x640);
  void *fallback_selected = memory.Allocate(0x640);
  void *weighted_pc = memory.Allocate(0x80);
  void *weighted_rows = memory.Allocate(3 * 16);
  void *weighted_storage_slot = memory.Allocate(8);
  void *weighted_fallback_slot = memory.Allocate(8);
  void *character_storage_slot = memory.Allocate(8);
  void *character_fallback_slot = memory.Allocate(8);
  void *government_fallback_slot = memory.Allocate(8);

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
    bindings.tail_direct_enabled = true;
    bindings.read_memory = &Memory::Read;
    bindings.read_context = &memory;
    bindings.remaining_character_storage_slot = character_storage_slot;
    bindings.remaining_character_fallback_slot = character_fallback_slot;
    bindings.remaining_government_fallback_slot = government_fallback_slot;
    bindings.tail_weighted_storage_slot = weighted_storage_slot;
    bindings.tail_weighted_fallback_slot = weighted_fallback_slot;

    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(character, 0x1B0, carrier);
    memory.Put(character, 0x1C0, land);
    memory.Put(land, 0x3F8, government);
    memory.Put(land, 0x1C0, subcarrier);
    memory.Put(government, 0x38, std::uint32_t{0x4744624F});
    memory.Put(character_fallback_slot, 0, character);
    memory.Put(government_fallback_slot, 0, government);
    // A non-SbCo subcarrier admits +A30 without consuming its full ID.
    memory.Put(subcarrier, 0xC, std::uint32_t{0});
    Property(At(government, 0x870), 101);
    Property(At(government, 0xA30), 201);

    memory.Put(carrier, 0x274, weighted_id);
    void *storage = memory.Allocate(0x30);
    void *table = memory.Allocate(2 * 16);
    memory.Put(weighted_storage_slot, 0, storage);
    memory.Put(storage, 0x20, table);
    memory.Put(storage, 0x2C, std::uint32_t{2});
    memory.Put(table, 16 + 8, selected);
    memory.Put(selected, 8, weighted_id);
    memory.Put(weighted_fallback_slot, 0, fallback_selected);
    memory.Put(selected, 0x630, weighted_rows);
    memory.Put(selected, 0x63C, std::int32_t{3});
    Property(weighted_pc, 301);
    for (std::size_t i = 0; i < 3; ++i)
      memory.Put(weighted_rows, i * 16, weighted_pc);
    memory.Put(weighted_rows, 0 * 16 + 8, std::int64_t{100000});
    memory.Put(weighted_rows, 1 * 16 + 8, std::int64_t{-250000});
    memory.Put(weighted_rows, 2 * 16 + 8, std::int64_t{0});

    // Existing always-collected branches observe actual empty spans. Their
    // optional leaf flags stay disabled; no native provider is installed.
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
    Require(bindings.enabled && bindings.tail_direct_enabled,
            "tail source binding disabled");
    Require(!bindings.pre_291e210_1640_enabled && !bindings.later_direct_enabled &&
                !bindings.helper_291f0a0_enabled && !bindings.remaining_helpers_enabled &&
                !bindings.post_291d7e0_sources_enabled,
            "only new tail source leaf may be enabled");
    Require(!bindings.provider && !bindings.government &&
                !bindings.existing_token_lookup,
            "native callbacks must remain null");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        bindings, character, 29829);
    Require(first == second, "tail whole snapshots differ within fixed frame");
    Require(first.tail_direct_291c5b7_291cc49.has_value(), "tail source section absent");
    Require(memory.Attempts(true) == 0, "tail skipped source fields were demanded");
    return first;
  }
};

void Value(const std::optional<xar::game::ContextSourcePropertiesV1> &block,
           std::int64_t expected) {
  Require(block && block->keys_count == 1 && block->values_count == 1 &&
              block->keys_u16 && block->keys_u16->size() == 1 &&
              block->keys_u16->at(0) == 5 && block->values_q64 &&
              block->values_q64->size() == 1 && block->values_q64->at(0) == expected,
          "tail selected property bytes differ");
}

void WeightedRows(const xar::game::ContextSourceTailWeightedV1 &weighted) {
  Require(weighted.ready && weighted.carrier_present == true &&
              weighted.key_274_raw == static_cast<std::int32_t>(Fixture::weighted_id) &&
              weighted.selection == "registry_full_id_8" &&
              weighted.count_63c == 3 && weighted.array_present == true &&
              weighted.rows && weighted.rows->size() == 3,
          "tail weighted generation or source span differs");
  const auto &rows = *weighted.rows;
  Require(rows[0].native_index == 0 && rows[1].native_index == 1 &&
              rows[2].native_index == 2 && rows[0].weight_q64 == 100000 &&
              rows[1].weight_q64 == -250000 && rows[2].weight_q64 == 0 &&
              rows[0].property_identity &&
              rows[0].property_identity == rows[1].property_identity &&
              rows[0].property_identity == rows[2].property_identity,
          "tail signed weights, zero occurrence or duplicate PCs lost");
  for (const auto &row : rows) Value(row.property_block, 301);
}

void Save(const std::filesystem::path &directory, const char *name,
          const Snapshot &snapshot) {
  if (directory.empty()) return;
  std::ofstream output(directory / (std::string(name) + ".json"), std::ios::binary);
  output << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!output) throw std::runtime_error("tail source wire write failed");
}

void ExactBindings() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto bindings = xar::ck3_12002::BindContextSourceInputs12003(
      base, xar::ck3_12003::kExecutableSha256);
  const auto address = [base](std::uintptr_t rva) {
    return reinterpret_cast<const void *>(base + rva);
  };
  Require(bindings.enabled && bindings.tail_direct_enabled,
          "exact tail source binding disabled");
  Require(bindings.tail_weighted_storage_slot == address(0x5D1E310),
          "tail weighted storage RVA");
  Require(bindings.tail_weighted_fallback_slot == address(0x5D1E2D0),
          "tail weighted fallback RVA");
  Require(bindings.remaining_character_storage_slot == address(0x5C67568) &&
              bindings.remaining_character_fallback_slot == address(0x5C67570) &&
              bindings.remaining_government_fallback_slot == address(0x5D1E2A8),
          "tail reused raw government bindings differ");
}

void Run(const std::filesystem::path &directory) {
  ExactBindings();
  {
    Fixture fixture;
    fixture.memory.DenyUnused(fixture.subcarrier, 8, 4);
    fixture.memory.DenyUnused(fixture.weighted_fallback_slot, 0, 8);
    const auto snapshot = fixture.Observe();
    const auto &tail = *snapshot.tail_direct_291c5b7_291cc49;
    const auto &government = tail.government_870_a30;
    Require(snapshot.ready && tail.ready && government.ready &&
                government.land_present == true &&
                government.government_selection == "character_land_1c0_3f8" &&
                government.government_magic_raw == 0x4744624FU &&
                government.admitted == true && government.second_land_present == true &&
                government.subcarrier_magic_raw == 0U &&
                !government.subcarrier_full_id_raw &&
                government.additional_a30_admitted == true,
            "full tail government admission differs");
    Value(government.property_870, 101);
    Value(government.property_a30, 201);
    Require(government.property_870_identity != government.property_a30_identity,
            "distinct direct tail PCs lost identity");
    WeightedRows(tail.carrier_weighted630);
    Save(directory, "full-government-weighted-duplicates", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.subcarrier, 0xC, std::uint32_t{0x5362436F});
    fixture.memory.Put(fixture.subcarrier, 8, std::uint32_t{0xFF000019});
    fixture.memory.DenyUnused(fixture.government, 0xA30, 0x80);
    const auto snapshot = fixture.Observe();
    const auto &tail = *snapshot.tail_direct_291c5b7_291cc49;
    const auto &government = tail.government_870_a30;
    Require(snapshot.ready && tail.ready && government.ready &&
                government.subcarrier_magic_raw == 0x5362436FU &&
                government.subcarrier_full_id_raw == static_cast<std::int32_t>(0xFF000019U) &&
                government.additional_a30_admitted == false &&
                !government.property_a30_identity && !government.property_a30,
            "valid SbCo should skip additional A30 before property read");
    Value(government.property_870, 101);
    WeightedRows(tail.carrier_weighted630);
    Save(directory, "subcarrier-skips-a30", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Unavailable(fixture.weighted_rows, 2 * 16 + 8, 8);
    const auto snapshot = fixture.Observe();
    const auto &tail = *snapshot.tail_direct_291c5b7_291cc49;
    const auto &weighted = tail.carrier_weighted630;
    Require(!snapshot.ready && !tail.ready && tail.government_870_a30.ready &&
                !weighted.ready && weighted.rows && weighted.rows->size() == 3 &&
                weighted.rows->at(0).weight_q64 == 100000 &&
                weighted.rows->at(1).weight_q64 == -250000 &&
                !weighted.rows->at(2).weight_q64 &&
                !weighted.rows->at(2).reason.empty() && fixture.memory.Attempts(false) == 2,
            "weighted partial must preserve independent government and copied rows");
    Value(tail.government_870_a30.property_870, 101);
    Value(tail.government_870_a30.property_a30, 201);
    for (const auto &row : *weighted.rows) Value(row.property_block, 301);
    Save(directory, "weighted-partial-government-ready", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Unavailable(fixture.government, 0x870 + 0xC, 4);
    const auto snapshot = fixture.Observe();
    const auto &tail = *snapshot.tail_direct_291c5b7_291cc49;
    const auto &government = tail.government_870_a30;
    Require(!snapshot.ready && !tail.ready && !government.ready &&
                government.property_870 && !government.property_870->keys_count &&
                government.additional_a30_admitted == true &&
                !government.reason.empty() && fixture.memory.Attempts(false) == 2,
            "government partial must retain independent weighted family");
    Value(government.property_a30, 201);
    WeightedRows(tail.carrier_weighted630);
    Save(directory, "government-partial-weighted-ready", snapshot);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.character, 0x1C0, static_cast<void *>(nullptr));
    fixture.memory.Put(fixture.character, 0x1B0, static_cast<void *>(nullptr));
    fixture.memory.DenyUnused(fixture.character, 0x1D0, 8);
    fixture.memory.DenyUnused(fixture.character_storage_slot, 0, 8);
    fixture.memory.DenyUnused(fixture.character_fallback_slot, 0, 8);
    fixture.memory.DenyUnused(fixture.government_fallback_slot, 0, 8);
    fixture.memory.DenyUnused(fixture.government, 0x38, 4);
    fixture.memory.DenyUnused(fixture.government, 0x870, 0x80);
    fixture.memory.DenyUnused(fixture.government, 0xA30, 0x80);
    fixture.memory.DenyUnused(fixture.carrier, 0x274, 4);
    fixture.memory.DenyUnused(fixture.weighted_storage_slot, 0, 8);
    fixture.memory.DenyUnused(fixture.weighted_fallback_slot, 0, 8);
    const auto snapshot = fixture.Observe();
    const auto &tail = *snapshot.tail_direct_291c5b7_291cc49;
    const auto &government = tail.government_870_a30;
    const auto &weighted = tail.carrier_weighted630;
    Require(snapshot.ready && tail.ready && government.ready && weighted.ready &&
                government.land_present == false && government.admitted == false &&
                !government.government_selection && !government.additional_a30_admitted &&
                !government.property_870 && !government.property_a30 &&
                weighted.carrier_present == false && !weighted.key_274_raw &&
                !weighted.selection && !weighted.count_63c && !weighted.array_present &&
                weighted.rows && weighted.rows->empty(),
            "native null land/carrier must remain known empty without unused reads");
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.carrier, 0x274, std::int32_t{-1});
    fixture.memory.DenyUnused(fixture.weighted_storage_slot, 0, 8);
    fixture.memory.DenyUnused(fixture.weighted_fallback_slot, 0, 8);
    const auto snapshot = fixture.Observe();
    const auto &weighted = snapshot.tail_direct_291c5b7_291cc49->carrier_weighted630;
    Require(snapshot.ready && weighted.ready && weighted.carrier_present == true &&
                weighted.key_274_raw == -1 && !weighted.selection &&
                !weighted.selected_identity && !weighted.count_63c &&
                !weighted.array_present && weighted.rows && weighted.rows->empty(),
            "key minus one must skip weighted registry lookup");
  }
  {
    Fixture fixture;
    // Same low index with a different generation is a native registry miss.
    fixture.memory.Put(fixture.selected, 8, Fixture::weighted_id ^ 0x01000000U);
    fixture.memory.DenyUnused(fixture.fallback_selected, 0x630, 8);
    fixture.memory.DenyUnused(fixture.fallback_selected, 8, 4);
    const auto snapshot = fixture.Observe();
    const auto &weighted = snapshot.tail_direct_291c5b7_291cc49->carrier_weighted630;
    Require(snapshot.ready && weighted.ready &&
                weighted.key_274_raw == static_cast<std::int32_t>(Fixture::weighted_id) &&
                weighted.selection == "native_fallback" && weighted.selected_identity &&
                weighted.count_63c == 0 && !weighted.array_present &&
                weighted.rows && weighted.rows->empty(),
            "generation miss must select current zero-count fallback without array read");
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.government, 0x38, std::uint32_t{0});
    fixture.memory.DenyUnused(fixture.government, 0x870, 0x80);
    fixture.memory.DenyUnused(fixture.government, 0xA30, 0x80);
    fixture.memory.DenyUnused(fixture.land, 0x1C0, 8);
    const auto snapshot = fixture.Observe();
    const auto &tail = *snapshot.tail_direct_291c5b7_291cc49;
    const auto &government = tail.government_870_a30;
    Require(snapshot.ready && tail.ready && government.ready &&
                government.government_magic_raw == 0U && government.admitted == false &&
                !government.second_land_present && !government.property_870 &&
                !government.property_a30,
            "wrong government magic must skip both PCs and second land admission");
    WeightedRows(tail.carrier_weighted630);
  }
  {
    Fixture fixture;
    fixture.memory.Put(fixture.subcarrier, 0xC, std::uint32_t{0x5362436F});
    fixture.memory.Put(fixture.subcarrier, 8, std::int32_t{-1});
    const auto snapshot = fixture.Observe();
    const auto &government = snapshot.tail_direct_291c5b7_291cc49->government_870_a30;
    Require(snapshot.ready && government.ready &&
                government.subcarrier_full_id_raw == -1 &&
                government.additional_a30_admitted == true,
            "SbCo minus-one ID must admit additional A30");
    Value(government.property_a30, 201);
  }
}
} // namespace

void RunPersonTailDirectSources12003(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  Run(directory);
}

#ifndef XAR_PERSON_TAIL_SOURCES_NO_MAIN
int main(int argc, char **argv) {
  try {
    const std::filesystem::path directory = argc == 2 ? argv[1] : "";
    RunPersonTailDirectSources12003(directory);
    std::cout << "tail291C5B7/291CC49 current source observer GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
#endif
