#include "xar_bridge/ck3_12003_context_sources.hpp"
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
void ListPredicateRequire(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
void *ListPredicateAt(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}
std::uint64_t ListPredicateWord(const void *address) {
  return static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(address));
}
struct ListPredicateMemory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Block { std::uintptr_t begin; std::size_t size; bool forbidden; std::size_t hits = 0; };
  std::vector<Region> regions;
  std::vector<Block> blocks;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    auto *address = data.get();
    regions.push_back({std::move(data), size});
    return address;
  }
  template <typename T> void Put(void *address, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(address) + offset, &value, sizeof(value));
  }
  void BlockRead(void *address, std::size_t offset, std::size_t bytes, bool forbidden = true) {
    blocks.push_back({reinterpret_cast<std::uintptr_t>(ListPredicateAt(address, offset)),
                      bytes, forbidden, 0});
  }
  static bool Read(void *context, const void *address, void *output, std::size_t bytes) noexcept {
    auto &memory = *static_cast<ListPredicateMemory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    for (auto &block : memory.blocks) {
      if (begin < block.begin + block.size && block.begin < begin + bytes) {
        ++block.hits;
        return false;
      }
    }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.data.get());
      if (begin >= base && begin - base <= region.size &&
          bytes <= region.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, address, bytes);
        return true;
      }
    }
    return false;
  }
  void RequireNoForbiddenReads() const {
    for (const auto &block : blocks)
      ListPredicateRequire(!block.forbidden || block.hits == 0,
          "list predicate collector demanded a skipped operand");
  }
};
struct ListPredicateFixture {
  ListPredicateMemory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D0);
  void *scratch = memory.Allocate(0x600);
  void *default_header = memory.Allocate(0x50);
  void *registry = memory.Allocate(0x30);
  void *table = memory.Allocate(2 * 16);
  void *selected = memory.Allocate(0x498);
  void *receiver = memory.Allocate(0x200);
  void *fallback = memory.Allocate(0x498);
  void *fallback_receiver = memory.Allocate(0x200);
  void *rows = nullptr;
  static constexpr std::uint32_t requested = 0xAB000001U;
  void *Slot(const void *value) {
    auto *slot = memory.Allocate(8);
    memory.Put(slot, 0, value);
    return slot;
  }
  template <typename T> void *Scalar(T value) {
    auto *slot = memory.Allocate(sizeof(value));
    memory.Put(slot, 0, value);
    return slot;
  }
  void SetList(const std::vector<std::uint32_t> &keys, bool use_default = false) {
    rows = keys.empty() ? nullptr : memory.Allocate(keys.size() * 24);
    auto *header = use_default ? default_header : ListPredicateAt(scratch, 0x458);
    memory.Put(header, 0x40, rows);
    memory.Put(header, 0x4C, static_cast<std::int32_t>(keys.size()));
    for (std::size_t i = 0; i < keys.size(); ++i) {
      memory.Put(rows, i * 24 + 0x10, keys[i]);
      memory.BlockRead(rows, i * 24, 16);
      memory.BlockRead(rows, i * 24 + 0x14, 4);
    }
  }
  void Properties(void *definition, std::uint16_t key, std::int64_t value) {
    auto *keys = Scalar(key);
    auto *values = Scalar(value);
    memory.Put(definition, 0xD8, keys);
    memory.Put(definition, 0xE4, std::int32_t{1});
    memory.Put(definition, 0x140, values);
    memory.Put(definition, 0x14C, std::int32_t{1});
  }
  ListPredicateFixture() {
    bindings.enabled = true;
    bindings.read_memory = &ListPredicateMemory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.list_predicate_2530dd0;
    b.enabled = true;
    b.default_inline_header = default_header;
    b.default_header_guard_slot = Scalar(std::int32_t{0});
    b.registry_storage_slot = Slot(registry);
    b.registry_fallback_slot = Slot(fallback);
    b.named_binding_key_slot = Scalar(std::int32_t{-71});
    memory.Put(character, 0x18, std::uint32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(character, 0x1B0, scratch);
    memory.Put(registry, 0x20, table);
    memory.Put(registry, 0x2C, std::uint32_t{2});
    memory.Put(table, 16 + 8, selected);
    memory.Put(selected, 0x10, requested);
    memory.Put(selected, 0x490, receiver);
    memory.Put(receiver, 0x38, std::uint32_t{0x4744624F});
    memory.Put(fallback, 0x10, std::uint32_t{0xCD000007});
    memory.Put(fallback, 0x490, fallback_receiver);
    memory.Put(fallback_receiver, 0x38, std::uint32_t{0x4744624F});
    SetList({requested});
  }
  auto Observe() {
    ListPredicateRequire(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
        "list predicate fixture assigned a native callback");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    ListPredicateRequire(first == second, "list predicate repeated fixed-frame query changed DTO");
    ListPredicateRequire(first.list_predicate_2530dd0.has_value(), "list predicate production leaf missing");
    memory.RequireNoForbiddenReads();
    return first;
  }
};
void ListPredicateSave(const std::filesystem::path &directory, const char *name,
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!out) throw std::runtime_error("list predicate production wire write failed");
}
void ListPredicateAdmitted(const xar::game::ContextSourceListPredicate2530dd0RowV1 &row) {
  ListPredicateRequire(row.ready && row.predicate_result == true &&
      row.pc_selection == "selected_d8" && row.properties.has_value(),
      "list predicate known AL1 did not select actual D8 properties");
}
}

// The shared coordinating target owns main/build/run and invokes no earlier fixture.
void RunListPredicate2530dd0Fixture(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto bound = xar::ck3_12002::BindListPredicate2530dd0Sources12003(base);
  ListPredicateRequire(bound.enabled &&
      bound.default_inline_header == reinterpret_cast<const void *>(base + 0x54E7180) &&
      bound.default_header_guard_slot == reinterpret_cast<const void *>(base + 0x5D67818) &&
      bound.registry_storage_slot == reinterpret_cast<const void *>(base + 0x5D1DE68) &&
      bound.registry_fallback_slot == reinterpret_cast<const void *>(base + 0x5D1DE30) &&
      bound.named_binding_key_slot == reinterpret_cast<const void *>(base + 0x5D4C018),
      "list predicate exact binding RVA differs");
  {
    ListPredicateFixture f;
    f.SetList({f.requested, 0xFFFFFFFFU, f.requested});
    f.Properties(f.selected, std::uint16_t{0x25D}, std::int64_t{101});
    f.memory.BlockRead(const_cast<void *>(f.bindings.list_predicate_2530dd0.default_header_guard_slot),
                       0, 4, false);
    const auto s = f.Observe();
    const auto &leaf = *s.list_predicate_2530dd0;
    ListPredicateRequire(leaf.ready && !leaf.default_header_guard_raw &&
        leaf.header_selection == "held_scratch_458" && leaf.rows->size() == 3,
        "list predicate held source gated on unread unused default guard");
    for (const auto index : {std::size_t{0}, std::size_t{2}}) {
      const auto &row = leaf.rows->at(index);
      ListPredicateAdmitted(row);
      ListPredicateRequire(row.key_u32 == f.requested && row.selected_full_id_u32 == f.requested &&
          row.used_fallback == false && row.properties->values_q64->at(0) == std::int64_t{101},
          "list predicate full DWORD/duplicate property operand lost");
    }
    ListPredicateRequire(leaf.rows->at(1).ready && !leaf.rows->at(1).selected_object &&
        !leaf.rows->at(1).predicate_receiver, "list predicate sentinel demanded a receiver");
    ListPredicateSave(directory, "list-predicate-ordered-duplicate-full-id-sentinel", s);
  }
  {
    ListPredicateFixture f;
    f.memory.Put(f.selected, 0x10, std::uint32_t{0xBB000001});
    f.Properties(f.fallback, std::uint16_t{0x25D}, std::int64_t{202});
    f.memory.BlockRead(f.fallback, 0x10, 4);
    f.memory.BlockRead(f.fallback_receiver, 0x110, 8);
    f.memory.BlockRead(const_cast<void *>(f.bindings.list_predicate_2530dd0.named_binding_key_slot), 0, 4);
    const auto s = f.Observe();
    const auto &row = s.list_predicate_2530dd0->rows->at(0);
    ListPredicateAdmitted(row);
    ListPredicateRequire(row.used_fallback == true && row.resolution_selection == "native_fallback" &&
        row.selected_object == ListPredicateWord(f.fallback) && !row.selected_full_id_u32 &&
        row.condition_count_raw_i32 == std::int32_t{0} && !row.scope_inputs &&
        row.properties->values_q64->at(0) == std::int64_t{202},
        "list predicate generation miss lost native fallback or demanded skipped scope");
    ListPredicateSave(directory, "list-predicate-generation-miss-fallback-zero-condition", s);
  }
  {
    ListPredicateFixture f;
    f.memory.Put(const_cast<void *>(f.bindings.list_predicate_2530dd0.registry_storage_slot), 0,
                 static_cast<void *>(nullptr));
    f.memory.Put(f.fallback_receiver, 0x38, std::uint32_t{0x12345678});
    f.memory.BlockRead(f.fallback, 0x10, 4);
    f.memory.BlockRead(f.fallback_receiver, 0x15C, 4);
    f.memory.BlockRead(f.fallback_receiver, 0x110, 8);
    f.memory.BlockRead(const_cast<void *>(f.bindings.list_predicate_2530dd0.named_binding_key_slot), 0, 4);
    const auto s = f.Observe();
    const auto &row = s.list_predicate_2530dd0->rows->at(0);
    ListPredicateAdmitted(row);
    ListPredicateRequire(!row.condition_count_raw_i32 && !row.scope_inputs &&
        !row.selected_full_id_u32 && row.used_fallback == true,
        "list predicate mismatching magic demanded condition/scope IDs");
    ListPredicateSave(directory, "list-predicate-magic-mismatch-fallback-lazy", s);
  }
  {
    ListPredicateFixture f;
    auto *nonempty_selected = f.memory.Allocate(0x498);
    auto *nonempty_receiver = f.memory.Allocate(0x200);
    auto *vtable = f.memory.Allocate(0xD0);
    f.memory.Put(f.table, 8, nonempty_selected);
    f.memory.Put(nonempty_selected, 0x10, std::uint32_t{0xCD000000});
    f.memory.Put(nonempty_selected, 0x490, nonempty_receiver);
    f.memory.Put(nonempty_receiver, 0x38, std::uint32_t{0x4744624F});
    f.memory.Put(nonempty_receiver, 0x15C, std::int32_t{-2});
    f.memory.Put(nonempty_receiver, 0x110, vtable);
    f.memory.Put(vtable, 0xC8, std::uint64_t{0x140123450ULL});
    f.memory.BlockRead(nonempty_selected, 0xE4, 4);
    f.memory.BlockRead(nonempty_selected, 0x2A4, 4);
    f.SetList({0xCD000000U, f.requested});
    const auto s = f.Observe();
    const auto &leaf = *s.list_predicate_2530dd0;
    const auto &unknown = leaf.rows->at(0);
    const auto &scope = *unknown.scope_inputs;
    ListPredicateRequire(!leaf.ready && !unknown.ready && !unknown.predicate_result &&
        !unknown.pc_selection && !unknown.properties &&
        unknown.condition_count_raw_i32 == std::int32_t{-2} &&
        scope.root_scope_kind_u32 == 4U && scope.root_character_full_id_u32 == 29829U &&
        scope.named_scope_kind_u32 == 31U && scope.named_selected_full_id_u32 == 0xCD000000U &&
        scope.named_binding_key_i32 == std::int32_t{-71} &&
        scope.trigger_object == ListPredicateWord(ListPredicateAt(nonempty_receiver, 0x110)) &&
        scope.trigger_vtable == ListPredicateWord(vtable) &&
        scope.trigger_evaluator_function == std::uint64_t{0x140123450ULL},
        "list predicate nonzero actual scoped evaluator inputs lost or boolean invented");
    ListPredicateAdmitted(leaf.rows->at(1));
    ListPredicateSave(directory, "list-predicate-nonzero-scope-independent-later", s);
  }
  {
    ListPredicateFixture f;
    f.SetList({0xFFFFFFFFU, 0xFFFFFFFFU});
    f.memory.BlockRead(const_cast<void *>(f.bindings.list_predicate_2530dd0.registry_storage_slot), 0, 8);
    f.memory.BlockRead(const_cast<void *>(f.bindings.list_predicate_2530dd0.registry_fallback_slot), 0, 8);
    const auto s = f.Observe();
    const auto &leaf = *s.list_predicate_2530dd0;
    ListPredicateRequire(leaf.ready && leaf.rows->size() == 2 &&
        leaf.rows->at(0).ready && leaf.rows->at(1).ready &&
        !leaf.rows->at(0).predicate_result && !leaf.rows->at(1).properties,
        "list predicate all-sentinel list demanded contribution operands");
    ListPredicateSave(directory, "list-predicate-all-sentinel-skips-registry", s);
  }
  {
    ListPredicateFixture f;
    f.SetList({});
    const auto s = f.Observe();
    ListPredicateRequire(s.list_predicate_2530dd0->ready &&
        s.list_predicate_2530dd0->source_array_present == false &&
        s.list_predicate_2530dd0->source_count_raw == std::int32_t{0} &&
        s.list_predicate_2530dd0->rows->empty(), "list predicate zero count/null array not legal empty");
    ListPredicateSave(directory, "list-predicate-zero-held-list", s);
  }
  {
    ListPredicateFixture f;
    f.memory.Put(f.character, 0x1B0, static_cast<void *>(nullptr));
    f.memory.Put(const_cast<void *>(f.bindings.list_predicate_2530dd0.default_header_guard_slot),
                 0, std::int32_t{-2});
    f.SetList({}, true);
    const auto s = f.Observe();
    ListPredicateRequire(s.list_predicate_2530dd0->ready &&
        s.list_predicate_2530dd0->scratch_present == false &&
        s.list_predicate_2530dd0->header_selection == "static_default_54e7180" &&
        s.list_predicate_2530dd0->rows->empty(), "list predicate initialized inline default lost");
    ListPredicateSave(directory, "list-predicate-selected-default-initialized-empty", s);
  }
  {
    ListPredicateFixture f;
    f.memory.Put(f.character, 0x1B0, static_cast<void *>(nullptr));
    f.SetList({f.requested, f.requested}, true);
    f.memory.BlockRead(f.rows, 0x10, 4);
    const auto s = f.Observe();
    const auto &leaf = *s.list_predicate_2530dd0;
    ListPredicateRequire(!leaf.ready && leaf.default_header_guard_raw == std::int32_t{0} &&
        leaf.source_array_present == true && leaf.source_count_raw == std::int32_t{2} && !leaf.rows,
        "list predicate uninitialized default invented initialized rows/empty");
    ListPredicateSave(directory, "list-predicate-selected-default-uninitialized", s);
  }
  {
    ListPredicateFixture f;
    f.memory.Put(f.scratch, 0x458 + 0x4C, std::int32_t{-3});
    f.memory.BlockRead(f.rows, 0x10, 4);
    const auto s = f.Observe();
    ListPredicateRequire(!s.list_predicate_2530dd0->ready &&
        s.list_predicate_2530dd0->source_count_raw == std::int32_t{-3} &&
        !s.list_predicate_2530dd0->rows, "list predicate negative end-pointer loop invented empty");
    ListPredicateSave(directory, "list-predicate-negative-source-count", s);
  }
  {
    ListPredicateFixture f;
    f.SetList({});
    f.memory.BlockRead(f.scratch, 0x458 + 0x40, 8, false);
    const auto s = f.Observe();
    ListPredicateRequire(!s.list_predicate_2530dd0->ready &&
        s.list_predicate_2530dd0->source_count_raw == std::int32_t{0} &&
        !s.list_predicate_2530dd0->source_array_present && !s.list_predicate_2530dd0->rows,
        "list predicate zero count hid demanded array read failure");
    ListPredicateSave(directory, "list-predicate-zero-count-array-read-unavailable", s);
  }
  {
    ListPredicateFixture f;
    f.memory.Put(const_cast<void *>(f.bindings.list_predicate_2530dd0.registry_storage_slot), 0,
                 static_cast<void *>(nullptr));
    f.memory.Put(const_cast<void *>(f.bindings.list_predicate_2530dd0.registry_fallback_slot), 0,
                 static_cast<void *>(nullptr));
    const auto s = f.Observe();
    const auto &row = s.list_predicate_2530dd0->rows->at(0);
    ListPredicateRequire(!row.ready && row.used_fallback == true &&
        row.selected_object == std::uint64_t{0} && !row.predicate_result,
        "list predicate readable native null fallback invented admission");
    ListPredicateSave(directory, "list-predicate-native-null-fallback", s);
  }
  {
    ListPredicateFixture f;
    f.SetList({f.requested, f.requested});
    f.memory.BlockRead(f.rows, 0x10, 4, false);
    const auto s = f.Observe();
    const auto &leaf = *s.list_predicate_2530dd0;
    ListPredicateRequire(!leaf.ready && !leaf.rows->at(0).ready &&
        !leaf.rows->at(0).key_u32 && !leaf.rows->at(0).selected_object,
        "list predicate unread physical key fabricated a selection");
    ListPredicateAdmitted(leaf.rows->at(1));
    ListPredicateSave(directory, "list-predicate-key-read-partial-independent-later", s);
  }
  {
    ListPredicateFixture f;
    f.memory.BlockRead(f.selected, 0x10, 4, false);
    f.memory.BlockRead(const_cast<void *>(f.bindings.list_predicate_2530dd0.registry_fallback_slot), 0, 8);
    const auto s = f.Observe();
    const auto &row = s.list_predicate_2530dd0->rows->at(0);
    ListPredicateRequire(!row.ready && !row.used_fallback && !row.selected_object &&
        !row.predicate_result, "list predicate unread generation check became native miss");
    ListPredicateSave(directory, "list-predicate-full-id-read-partial-no-fallback", s);
  }
  {
    ListPredicateFixture f;
    f.memory.BlockRead(f.selected, 0xE4, 4, false);
    const auto s = f.Observe();
    const auto &row = s.list_predicate_2530dd0->rows->at(0);
    ListPredicateRequire(!row.ready && row.predicate_result == true &&
        row.pc_selection == "selected_d8" && row.properties && !row.properties->keys_count,
        "list predicate PC read failure discarded known predicate or guessed readiness");
    ListPredicateSave(directory, "list-predicate-true-properties-partial", s);
  }
}
