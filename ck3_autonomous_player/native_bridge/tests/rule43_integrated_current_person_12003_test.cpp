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
void Require(bool test, const char *message) { if (!test) throw std::runtime_error(message); }
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> bytes; std::size_t size; };
  struct ReadSpan { std::uintptr_t begin; std::size_t size; };
  std::vector<Region> regions;
  std::vector<ReadSpan> reads;
  void *Allocate(std::size_t size) {
    auto bytes = std::make_unique<std::byte[]>(size);
    void *address = bytes.get();
    regions.push_back({std::move(bytes), size});
    return address;
  }
  template<class T> void Put(void *p, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof value);
  }
  static bool Copy(void *context, const void *p, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(p);
    m.reads.push_back({begin, size});
    for (const auto &r : m.regions) {
      const auto start = reinterpret_cast<std::uintptr_t>(r.bytes.get());
      if (begin >= start && begin - start <= r.size &&
          size <= r.size - static_cast<std::size_t>(begin - start)) {
        std::memcpy(out, p, size); return true;
      }
    }
    return false;
  }
  bool ReadAt(const void *p, std::size_t offset) const {
    const auto address = reinterpret_cast<std::uintptr_t>(p) + offset;
    for (const auto &read : reads) if (address >= read.begin && address - read.begin < read.size) return true;
    return false;
  }
};
void *At(void *p, std::size_t offset) { return static_cast<std::byte *>(p) + offset; }
constexpr std::uintptr_t kBase = 0x140000000;
const void *Target(std::uint64_t rva) { return reinterpret_cast<const void *>(kBase + rva); }
struct Fixture {
  Memory m;
  xar::ck3_12002::ContextSourceBindingsV1 b{};
  void *character = m.Allocate(0x1D8);
  void *fallback_character = m.Allocate(0x1D8);
  void *carrier = m.Allocate(0x40);
  void *landed = m.Allocate(0x1D0);
  void *landed_owner = m.Allocate(0x30);
  void *diac = m.Allocate(0x30);
  void *definition = m.Allocate(0x680);
  void *provider = m.Allocate(0xF00);
  void *rule_array = m.Allocate(0x23F0);
  void *root_header = m.Allocate(0x10);
  void *descriptors = m.Allocate(5 * 0x50);
  void *vtable = m.Allocate(0xD0);
  void *rule_object = At(rule_array, 0x22F0);
  void *metadata = m.Allocate(0x60);
  void *mapper = m.Allocate(6 * 0xC8);
  void *sentinel = m.Allocate(0xC8);
  void *mode = m.Allocate(1);
  void *Slot(void *value) { auto p = m.Allocate(8); m.Put(p, 0, value); return p; }
  void Type(void *p, std::uint64_t evaluator) {
    auto table = m.Allocate(0xD0);
    m.Put(p, 0, table);
    m.Put(table, 0x58, Target(0x855AB0));
    m.Put(table, 0x60, Target(evaluator == 0x3730940 ? 0x9CFEE0 : 0x9CFEC0));
    m.Put(table, 0xC8, Target(evaluator));
  }
  Fixture() {
    b.enabled = true; b.read_memory = Memory::Copy; b.read_context = &m;
    auto &raw = b.following_diac_2920d60;
    raw.enabled = true; raw.image_base = kBase;
    raw.diac_storage_slot = Slot(nullptr); raw.diac_fallback_slot = Slot(diac);
    raw.character_storage_slot = Slot(nullptr); raw.character_fallback_slot = Slot(fallback_character);
    raw.rule_provider_slot = Slot(provider); raw.rule_mode_slot = mode;
    raw.root_registry_header = root_header; raw.root_fallback_descriptor = m.Allocate(0x50);
    raw.numeric.enabled = true;
    raw.numeric.metadata_provider_slot = Slot(metadata); raw.numeric.sentinel_metadata = sentinel;
    m.Put(character, 0x18, std::int32_t{29829}); m.Put(character, 0x1C, std::uint32_t{0x43686172});
    m.Put(character, 0x1C8, carrier); m.Put(carrier, 0x30, std::int32_t{1});
    m.Put(character, 0x1C0, landed); m.Put(landed, 0x1C0, landed_owner); m.Put(landed_owner, 0x28, character);
    m.Put(fallback_character, 0x18, std::int32_t{29829}); m.Put(fallback_character, 0x1C, std::uint32_t{0x43686172});
    m.Put(diac, 8, std::int32_t{1}); m.Put(diac, 0xC, std::uint32_t{0x44696163});
    m.Put(diac, 0x24, std::int32_t{29829}); m.Put(diac, 0x28, definition);
    m.Put(provider, 0xEF0, rule_array);
    m.Put(root_header, 0, descriptors); m.Put(root_header, 0xC, std::int32_t{5});
    m.Put(descriptors, 4 * 0x50 + 0x10, Target(0x22565B0));
    m.Put(rule_object, 0, vtable);
    m.Put(vtable, 0x58, Target(0x855AB0)); m.Put(vtable, 0x60, Target(0x9CFEC0)); m.Put(vtable, 0xC8, Target(0x372F780));
    m.Put(metadata, 0x50, mapper);
    m.Put(mapper, 4 * 0xC8 + 0xBA, std::uint8_t{1});
    m.Put(sentinel, 0xB8, std::uint8_t{1});
    Literal();
  }
  void Literal() {
    void *rows = m.Allocate(16), *declaration = m.Allocate(0x288);
    void *keys = m.Allocate(6), *values = m.Allocate(24);
    m.Put(At(definition, 0x620), 0, rows); m.Put(At(definition, 0x620), 0xC, std::int32_t{2});
    m.Put(rows, 0, declaration); m.Put(rows, 8, declaration);
    m.Put(declaration, 0, keys); m.Put(declaration, 0xC, std::int32_t{3});
    m.Put(declaration, 0x68, values); m.Put(declaration, 0x74, std::int32_t{3});
    m.Put(keys, 0, std::uint16_t{5}); m.Put(keys, 2, std::uint16_t{4}); m.Put(keys, 4, std::uint16_t{65535});
    m.Put(values, 0, std::int64_t{-199999}); m.Put(values, 8, std::int64_t{0}); m.Put(values, 16, std::int64_t{123456});
  }
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 Observe() {
    // This exercises the actual owning collector hook, guarded injected Copy,
    // dedicated Rule43 walker and literal serializer without native dispatch.
    auto snapshot = xar::ck3_12002::ReadCurrentContextSourceInputs12003(b, character, 29829);
    Require(snapshot.following_diac_2920d60.has_value(), "same-query new leaf missing");
    return snapshot;
  }
};
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const std::filesystem::path path(argv[1]);
  std::filesystem::create_directories(path.parent_path());
  std::ofstream wire(path, std::ios::binary);
  Require(static_cast<bool>(wire), "new Rule43 wire output unavailable");
  wire << "{\"cases\":[";
  bool first = true;
  const auto save = [&](const char *name, const auto &snapshot) {
    if (!first) wire << ',';
    first = false;
    wire << "{\"name\":\"" << name << "\",\"source_inputs\":"
         << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot) << '}';
  };
  const auto bound = xar::ck3_12002::BindContextSourceInputs12003(kBase, xar::ck3_12003::kExecutableSha256);
  Require(bound.following_diac_2920d60.enabled &&
      bound.following_diac_2920d60.root_registry_header == Target(0x54F2AF0), "exact binder input differs");
  {
    Fixture f;
    const auto out = f.Observe(); const auto &leaf = *out.following_diac_2920d60;
    Require(leaf.ready && leaf.selected_family == "primary_620" && !leaf.secondary &&
        leaf.numeric_inputs && leaf.numeric_inputs->declarations.size() == 2, "primary literal result differs");
    const auto &rows = leaf.numeric_inputs->declarations;
    Require(rows[0].declaration_identity == rows[1].declaration_identity &&
        rows[0].properties->values_q64->at(0) == -199999, "raw duplicate declaration lost");
    Require(!f.m.ReadAt(f.character, 0x1C0), "accepted primary read secondary");
    save("primary_literal_duplicates", out);
  }
  {
    Fixture f; f.m.Put(At(f.definition, 0x620), 0xC, std::int32_t{0});
    const auto out = f.Observe(); const auto &leaf = *out.following_diac_2920d60;
    Require(leaf.ready && leaf.selected_family == "primary_620" && !leaf.secondary &&
        leaf.numeric_inputs->declarations.empty(), "empty primary fell through");
    Require(!f.m.ReadAt(f.character, 0x1C0), "empty primary demanded secondary");
    save("primary_empty_suppresses_secondary", out);
  }
  {
    Fixture f; f.m.Put(f.fallback_character, 0x1C, std::uint32_t{0});
    const auto out = f.Observe(); const auto &leaf = *out.following_diac_2920d60;
    Require(leaf.ready && leaf.selected_family == "none" && leaf.primary.rule->result == false &&
        leaf.secondary && leaf.secondary->rule->result == false &&
        leaf.primary.rule->nodes.empty(), "known root false differs");
    Require(!f.m.ReadAt(f.rule_object, 0), "false root demanded actual node");
    Require(!f.m.ReadAt(f.diac, 0x28), "unselected numeric demanded");
    save("root_false_both_branches", out);
  }
  {
    Fixture f; f.Type(f.rule_object, 0x3730940);
    auto referent = f.m.Allocate(0x118); f.m.Put(f.rule_object, 0x40, referent);
    const auto out = f.Observe(); const auto &leaf = *out.following_diac_2920d60;
    Require(leaf.ready && leaf.primary.rule->result == true &&
        leaf.primary.rule->nodes[0].nested_present == false &&
        leaf.primary.rule->nodes[0].reference_compare_raw == 0, "null reference raw equality differs");
    save("reference_null_compare0_true", out);
  }
  {
    Fixture f; f.Type(f.rule_object, 0x3730940);
    auto referent = f.m.Allocate(0x118); f.m.Put(f.rule_object, 0x40, referent);
    f.m.Put(f.rule_object, 0x80, std::uint8_t{2});
    const auto out = f.Observe(); const auto &leaf = *out.following_diac_2920d60;
    Require(leaf.ready && leaf.selected_family == "none" && leaf.primary.rule->result == false &&
        leaf.primary.rule->nodes[0].reference_compare_raw == 2, "raw2 incorrectly coerced to bool");
    save("reference_null_compare2_false", out);
  }
  {
    Fixture f;
    auto children = f.m.Allocate(16);
    auto reference = f.m.Allocate(0x98);
    auto later = f.m.Allocate(0x98);
    auto referent = f.m.Allocate(0x118);
    auto nested = f.m.Allocate(0x98);
    f.Type(reference, 0x3730940); f.Type(nested, 0x1234567); f.Type(later, 0x372F780);
    f.m.Put(f.rule_object, 0x40, children); f.m.Put(f.rule_object, 0x4C, std::int32_t{2});
    f.m.Put(children, 0, reference); f.m.Put(children, 8, later);
    f.m.Put(reference, 0x40, referent); f.m.Put(referent, 0x110, nested);
    const auto out = f.Observe(); const auto &leaf = *out.following_diac_2920d60;
    Require(!leaf.ready && !leaf.selected_family && !leaf.secondary && !leaf.numeric_inputs &&
        leaf.reason == "evaluator_slotc8_source" &&
        leaf.primary.rule->nodes[0].children[0].children[0].path == "rule43/child0/reference",
        "actual nested first source seam lost");
    Require(!f.m.ReadAt(children, 8) && !f.m.ReadAt(reference, 0x80) &&
        !f.m.ReadAt(f.diac, 0x28), "unknown child traversed later demand");
    save("first_unknown_nested_target", out);
  }
  {
    Fixture f; f.m.Put(f.mode, 0, std::uint8_t{1});
    f.m.Put(f.rule_object, 0x4C, std::int32_t{-1});
    const auto out = f.Observe(); const auto &leaf = *out.following_diac_2920d60;
    Require(leaf.ready && leaf.primary.rule->mode_raw == 1 &&
        leaf.primary.rule->nodes[0].children_count_raw == 0 &&
        !f.m.ReadAt(f.rule_object, 0x4C), "mode1 selected wrong header");
    save("mode1_known_empty88", out);
  }
  {
    Fixture f; f.m.Put(f.diac, 0x24, std::int32_t{-1});
    const auto out = f.Observe(); const auto &leaf = *out.following_diac_2920d60;
    Require(leaf.ready && leaf.primary.rule->input_character_full_id == 29829 &&
        leaf.numeric_inputs->scope_character_full_id == -1, "rule input conflated with numeric scope");
    save("distinct_rule_character_and_scope", out);
  }
  wire << "]}";
  Require(static_cast<bool>(wire), "new Rule43 wire write failed");
  std::cout << "same-query Rule43 bounded input fixture GREEN\n";
  return 0;
}
