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
void QualifierRequire(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
void *QualifierAt(void *address, std::size_t offset) {
  return static_cast<std::byte *>(address) + offset;
}
std::uint64_t QualifierWord(const void *address) {
  return static_cast<std::uint64_t>(reinterpret_cast<std::uintptr_t>(address));
}
struct QualifierMemory {
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
    blocks.push_back({reinterpret_cast<std::uintptr_t>(QualifierAt(address, offset)),
                      bytes, forbidden, 0});
  }
  static bool Read(void *context, const void *address, void *output, std::size_t bytes) noexcept {
    auto &memory = *static_cast<QualifierMemory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(address);
    // Record demand without throwing or allocating inside the production
    // noexcept query. Expected missing reads and forbidden reads are distinct.
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
      QualifierRequire(!block.forbidden || block.hits == 0,
                       "qualifier collector demanded an unconsumed operand");
  }
};
struct QualifierRelationship { std::uint8_t marker; const void *definition; };
struct QualifierScratchRow { std::uint32_t id; const void *object; };
struct QualifierFixture {
  QualifierMemory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x1D0);
  void *scratch = memory.Allocate(0x300);
  void *manager = memory.Allocate(0x60);
  void *definition_a = memory.Allocate(0x240);
  void *definition_b = memory.Allocate(0x240);
  void *definition_other = memory.Allocate(0x240);
  void *scratch_rows = nullptr;
  void *definition_rows = nullptr;
  void *Slot(const void *value) {
    auto *slot = memory.Allocate(8);
    memory.Put(slot, 0, value);
    return slot;
  }
  void SetDefinitions(const std::vector<const void *> &definitions) {
    definition_rows = definitions.empty() ? nullptr : memory.Allocate(definitions.size() * 8);
    memory.Put(manager, 0x50, definition_rows);
    memory.Put(manager, 0x5C, static_cast<std::int32_t>(definitions.size()));
    for (std::size_t i = 0; i < definitions.size(); ++i)
      memory.Put(definition_rows, i * 8, definitions[i]);
  }
  void SetScratch(const std::vector<QualifierScratchRow> &rows) {
    scratch_rows = rows.empty() ? nullptr : memory.Allocate(rows.size() * 16);
    memory.Put(scratch, 8, scratch_rows);
    memory.Put(scratch, 0x14, static_cast<std::int32_t>(rows.size()));
    for (std::size_t i = 0; i < rows.size(); ++i) {
      memory.Put(scratch_rows, i * 16, rows[i].id);
      memory.Put(scratch_rows, i * 16 + 8, rows[i].object);
    }
  }
  std::pair<void *, void *> Object(const std::vector<const void *> &definitions) {
    auto *object = memory.Allocate(0x30);
    auto *rows = definitions.empty() ? nullptr : memory.Allocate(definitions.size() * 40);
    memory.Put(object, 0x20, rows);
    memory.Put(object, 0x2C, static_cast<std::int32_t>(definitions.size()));
    for (std::size_t i = 0; i < definitions.size(); ++i) {
      memory.Put(rows, i * 40, definitions[i]);
      memory.BlockRead(rows, i * 40 + 8, 32);
    }
    return {object, rows};
  }
  void *Relationships(void *definition, const std::vector<QualifierRelationship> &relationships) {
    auto *rows = relationships.empty() ? nullptr : memory.Allocate(relationships.size() * 16);
    memory.Put(definition, 0x220, rows);
    memory.Put(definition, 0x22C, static_cast<std::int32_t>(relationships.size()));
    for (std::size_t i = 0; i < relationships.size(); ++i) {
      memory.Put(rows, i * 16, relationships[i].definition);
      memory.Put(rows, i * 16 + 0xC, relationships[i].marker);
    }
    return rows;
  }
  void Properties(void *definition, std::uint16_t key, std::int64_t value) {
    auto *keys = memory.Allocate(2);
    auto *values = memory.Allocate(8);
    memory.Put(keys, 0, key);
    memory.Put(values, 0, value);
    memory.Put(definition, 0x40, keys);
    memory.Put(definition, 0x4C, std::int32_t{1});
    memory.Put(definition, 0xA8, values);
    memory.Put(definition, 0xB4, std::int32_t{1});
  }
  QualifierFixture() {
    bindings.enabled = true;
    bindings.read_memory = &QualifierMemory::Read;
    bindings.read_context = &memory;
    bindings.qualifier_28bc0d0.enabled = true;
    bindings.qualifier_28bc0d0.manager_slot = Slot(manager);
    bindings.qualifier_28bc0d0.fallback_definition_slot = Slot(definition_a);
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172});
    memory.Put(character, 0x1B0, scratch);
    SetDefinitions({definition_a});
    SetScratch({});
  }
  auto Observe() {
    QualifierRequire(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
                     "qualifier fixture assigned a native callback");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    QualifierRequire(first == second, "qualifier repeated fixed-frame query changed DTO");
    QualifierRequire(first.qualifier_28bc0d0.has_value(), "qualifier production query leaf missing");
    memory.RequireNoForbiddenReads();
    return first;
  }
};
void QualifierSave(const std::filesystem::path &directory, const char *name,
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  if (!out) throw std::runtime_error("qualifier production wire write failed");
}
void QualifierCount(const xar::game::ContextSourceQualifier28bc0d0DefinitionV1 &row,
                    const std::vector<std::uint32_t> &ids) {
  QualifierRequire(row.ready && row.accepted_ids_u32 == ids &&
      row.repeat_count == static_cast<std::int32_t>(ids.size()),
      "qualifier final ordered unique IDs/count differ");
}
}

// Coordinating target owns main/build/run. This invokes only the new family.
void RunQualifier28bc0d0Fixture(const std::filesystem::path &directory) {
  constexpr std::uintptr_t base = 0x140000000ULL;
  const auto bound = xar::ck3_12002::BindQualifier28bc0d0Sources12003(base);
  QualifierRequire(bound.enabled &&
      bound.manager_slot == reinterpret_cast<const void *>(base + 0x5D1E2B0) &&
      bound.fallback_definition_slot == reinterpret_cast<const void *>(base + 0x5D1EBF8),
      "qualifier exact source RVA binding differs");
  {
    QualifierFixture f;
    const auto object = f.Object({f.definition_a}).first;
    f.SetDefinitions({f.definition_a, f.definition_a});
    f.SetScratch({{0U, object}, {0x80000001U, object}, {0U, object},
                  {0xFFFFFFFFU, object}, {0xFFFFFFFEU, object}});
    f.Properties(f.definition_a, std::uint16_t{0x25D}, std::int64_t{101});
    f.memory.BlockRead(f.definition_a, 0x220, 16);
    f.memory.BlockRead(const_cast<void *>(f.bindings.qualifier_28bc0d0.fallback_definition_slot), 0, 8);
    const auto s = f.Observe();
    const auto &leaf = *s.qualifier_28bc0d0;
    QualifierRequire(leaf.ready && leaf.definitions->size() == 2 &&
        !leaf.fallback_definition_object, "qualifier duplicate manager definitions collapsed");
    for (const auto &row : *leaf.definitions) {
      QualifierCount(row, {0U, 0x80000001U, 0xFFFFFFFEU});
      QualifierRequire(row.scratch_evaluations->size() == 5 &&
          row.scratch_evaluations->at(2).id_u32 == 0U &&
          row.scratch_evaluations->at(3).id_u32 == 0xFFFFFFFFU &&
          !row.scratch_evaluations->at(0).candidates->at(0).relationships &&
          row.properties->values_q64->at(0) == std::int64_t{101},
          "qualifier predicate-before-dedup/sentinel or direct laziness lost");
    }
    QualifierSave(directory, "qualifier-direct-unsigned-dedup-duplicate-definitions", s);
  }
  {
    QualifierFixture f;
    const auto [object, candidates] = f.Object({f.definition_other, f.definition_b});
    auto *relations = f.Relationships(f.definition_other,
        {{std::uint8_t{2}, f.definition_b}, {std::uint8_t{2}, f.definition_a},
         {std::uint8_t{2}, nullptr}});
    f.SetScratch({{7U, object}});
    f.memory.BlockRead(candidates, 40, 8);
    f.memory.BlockRead(relations, 32, 16);
    f.memory.BlockRead(const_cast<void *>(f.bindings.qualifier_28bc0d0.fallback_definition_slot), 0, 8, false);
    const auto s = f.Observe();
    const auto &row = s.qualifier_28bc0d0->definitions->at(0);
    QualifierCount(row, {7U});
    QualifierRequire(row.scratch_evaluations->at(0).candidates->size() == 1 &&
        row.scratch_evaluations->at(0).candidates->at(0).relationships->size() == 2 &&
        !s.qualifier_28bc0d0->fallback_definition_object &&
        f.memory.blocks.back().hits == 2,
        "qualifier first candidate/relationship match prefix differs");
    QualifierSave(directory, "qualifier-marker2-first-match-prefix", s);
  }
  {
    QualifierFixture f;
    const auto object = f.Object({f.definition_other}).first;
    auto *relations = f.Relationships(f.definition_other,
        {{std::uint8_t{9}, f.definition_b}, {std::uint8_t{2}, nullptr}});
    f.SetScratch({{8U, object}});
    f.memory.BlockRead(relations, 0, 8);
    f.memory.BlockRead(relations, 16, 16);
    const auto s = f.Observe();
    const auto &leaf = *s.qualifier_28bc0d0;
    QualifierCount(leaf.definitions->at(0), {8U});
    QualifierRequire(leaf.fallback_definition_object == QualifierWord(f.definition_a) &&
        !leaf.definitions->at(0).scratch_evaluations->at(0).candidates->at(0)
            .relationships->at(0).definition_object,
        "qualifier non2 marker did not select actual fallback lazily");
    QualifierSave(directory, "qualifier-non2-actual-fallback", s);
  }
  {
    QualifierFixture f;
    const auto object = f.Object({f.definition_other}).first;
    f.Relationships(f.definition_other, {{std::uint8_t{2}, f.definition_b}});
    f.SetScratch({{0xFFFFFFFFU, object}});
    f.memory.BlockRead(f.scratch_rows, 0, 4);
    f.memory.BlockRead(f.definition_a, 0x4C, 4);
    const auto s = f.Observe();
    const auto &row = s.qualifier_28bc0d0->definitions->at(0);
    QualifierCount(row, {});
    QualifierRequire(!row.scratch_evaluations->at(0).id_u32 && !row.properties,
        "qualifier false predicate demanded ID or zero-repeat PC");
    QualifierSave(directory, "qualifier-false-predicate-skips-id-and-pc", s);
  }
  {
    QualifierFixture f;
    f.SetDefinitions({});
    f.memory.BlockRead(const_cast<void *>(f.bindings.qualifier_28bc0d0.fallback_definition_slot), 0, 8);
    const auto s = f.Observe();
    QualifierRequire(s.qualifier_28bc0d0->ready &&
        s.qualifier_28bc0d0->definition_array_present == false &&
        s.qualifier_28bc0d0->definitions->empty() && !s.qualifier_28bc0d0->scratch_present,
        "qualifier empty manager invented a scratch observation");
    QualifierSave(directory, "qualifier-empty-manager-null-array", s);
  }
  {
    QualifierFixture f;
    f.SetDefinitions({nullptr});
    f.memory.Put(f.character, 0x1B0, static_cast<void *>(nullptr));
    const auto s = f.Observe();
    QualifierCount(s.qualifier_28bc0d0->definitions->at(0), {});
    QualifierRequire(s.qualifier_28bc0d0->scratch_present == false &&
        s.qualifier_28bc0d0->definitions->at(0).definition_object == std::uint64_t{0},
        "qualifier null scratch/readable null requested definition did not yield zero");
    QualifierSave(directory, "qualifier-null-scratch-null-requested-definition", s);
  }
  {
    QualifierFixture f;
    f.memory.Put(f.scratch, 0x14, std::int32_t{-3});
    f.memory.BlockRead(f.scratch, 8, 8);
    const auto s = f.Observe();
    QualifierCount(s.qualifier_28bc0d0->definitions->at(0), {});
    QualifierRequire(s.qualifier_28bc0d0->scratch_count_raw_i32 == std::int32_t{-3},
        "qualifier scratch explicit JLE empty count lost");
    QualifierSave(directory, "qualifier-negative-scratch-count-empty", s);
  }
  {
    QualifierFixture f;
    const auto object = f.Object({}).first;
    f.SetScratch({{22U, object}});
    f.memory.BlockRead(f.scratch_rows, 0, 4);
    const auto s = f.Observe();
    const auto &row = s.qualifier_28bc0d0->definitions->at(0);
    QualifierCount(row, {});
    QualifierRequire(row.scratch_evaluations->at(0).candidate_array_present == false,
        "qualifier zero candidate count/null readable array not observed");
    QualifierSave(directory, "qualifier-empty-candidate-null-array", s);
  }
  {
    QualifierFixture f;
    const auto object = f.Object({f.definition_other}).first;
    f.Relationships(f.definition_other, {});
    f.SetScratch({{22U, object}});
    f.memory.BlockRead(f.scratch_rows, 0, 4);
    const auto s = f.Observe();
    QualifierCount(s.qualifier_28bc0d0->definitions->at(0), {});
    QualifierRequire(s.qualifier_28bc0d0->definitions->at(0).scratch_evaluations->at(0)
        .candidates->at(0).relationship_array_present == false,
        "qualifier zero relationship count/null readable array not observed");
    QualifierSave(directory, "qualifier-empty-relationship-null-array", s);
  }
  {
    QualifierFixture f;
    const auto object = f.Object({}).first;
    f.SetScratch({{22U, object}});
    f.memory.BlockRead(object, 0x20, 8, false);
    const auto s = f.Observe();
    const auto &row = s.qualifier_28bc0d0->definitions->at(0);
    QualifierRequire(!row.ready && !row.repeat_count &&
        row.scratch_evaluations->at(0).candidate_count_raw_i32 == std::int32_t{0} &&
        !row.scratch_evaluations->at(0).candidate_array_present,
        "qualifier zero candidate count hid demanded header read failure");
    QualifierSave(directory, "qualifier-zero-candidate-count-header-unread", s);
  }
  {
    QualifierFixture f;
    const auto object = f.Object({f.definition_other}).first;
    f.Relationships(f.definition_other, {});
    f.SetScratch({{22U, object}});
    f.memory.BlockRead(f.definition_other, 0x220, 8, false);
    const auto s = f.Observe();
    const auto &row = s.qualifier_28bc0d0->definitions->at(0);
    QualifierRequire(!row.ready && !row.repeat_count &&
        row.scratch_evaluations->at(0).candidates->at(0).relationship_count_raw_i32 ==
            std::int32_t{0} &&
        !row.scratch_evaluations->at(0).candidates->at(0).relationship_array_present,
        "qualifier zero relationship count hid demanded header read failure");
    QualifierSave(directory, "qualifier-zero-relationship-count-header-unread", s);
  }
  for (const bool candidate_count : {true, false}) {
    QualifierFixture f;
    const auto object = f.Object({f.definition_other}).first;
    f.SetScratch({{12U, object}});
    if (candidate_count) f.memory.Put(object, 0x2C, std::int32_t{-1});
    else f.memory.Put(f.definition_other, 0x22C, std::int32_t{-1});
    const auto s = f.Observe();
    const auto &row = s.qualifier_28bc0d0->definitions->at(0);
    QualifierRequire(!row.ready && !row.accepted_ids_u32 && !row.repeat_count,
        "qualifier negative end-pointer loop declared empty");
    QualifierSave(directory, candidate_count ? "qualifier-negative-candidate-count-partial" :
        "qualifier-negative-relationship-count-partial", s);
  }
  {
    QualifierFixture f;
    const auto object = f.Object({f.definition_b}).first;
    f.SetDefinitions({f.definition_a, f.definition_b});
    f.SetScratch({{13U, object}});
    f.memory.BlockRead(f.definition_b, 0x220, 8, false);
    const auto s = f.Observe();
    const auto &leaf = *s.qualifier_28bc0d0;
    QualifierRequire(!leaf.ready && !leaf.definitions->at(0).ready &&
        !leaf.definitions->at(0).repeat_count, "qualifier missing first definition marked ready");
    QualifierCount(leaf.definitions->at(1), {13U});
    QualifierSave(directory, "qualifier-independent-later-definition-ready", s);
  }
  {
    QualifierFixture f;
    const auto object = f.Object({f.definition_a}).first;
    f.SetScratch({{14U, object}});
    f.memory.BlockRead(f.definition_a, 0x4C, 4, false);
    const auto s = f.Observe();
    const auto &row = s.qualifier_28bc0d0->definitions->at(0);
    QualifierRequire(!row.ready && row.accepted_ids_u32 == std::vector<std::uint32_t>{14U} &&
        row.repeat_count == std::int32_t{1} && row.properties && !row.properties->keys_count,
        "qualifier PC failure discarded independently known count");
    QualifierSave(directory, "qualifier-count-ready-properties-partial", s);
  }
  for (const bool sentinel : {true, false}) {
    QualifierFixture f;
    const auto good = f.Object({f.definition_a}).first;
    const auto unread = f.Object({}).first;
    f.SetScratch({{15U, good}, {sentinel ? 0xFFFFFFFFU : 15U, unread}});
    f.memory.BlockRead(unread, 0x20, 8, false);
    f.memory.BlockRead(f.scratch_rows, 16, 4);
    const auto s = f.Observe();
    const auto &row = s.qualifier_28bc0d0->definitions->at(0);
    QualifierRequire(!row.ready && !row.accepted_ids_u32 && !row.repeat_count &&
        row.scratch_evaluations->size() == 2 && !row.scratch_evaluations->at(1).id_u32,
        "qualifier sentinel/duplicate bypassed actual predicate demand");
    QualifierSave(directory, sentinel ? "qualifier-sentinel-predicate-partial" :
        "qualifier-duplicate-id-predicate-partial", s);
  }
  {
    QualifierFixture f;
    f.memory.Put(const_cast<void *>(f.bindings.qualifier_28bc0d0.manager_slot), 0,
                 static_cast<void *>(nullptr));
    const auto s = f.Observe();
    QualifierRequire(!s.qualifier_28bc0d0->ready &&
        s.qualifier_28bc0d0->manager_object == std::uint64_t{0} &&
        !s.qualifier_28bc0d0->definitions,
        "qualifier uninitialized manager fabricated an empty source");
    QualifierSave(directory, "qualifier-manager-null-uninitialized", s);
  }
}
