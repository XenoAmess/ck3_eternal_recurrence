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
#include <vector>

namespace {
void Require(bool v, const char *label) {
  if (!v) throw std::runtime_error(label);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    void *p = data.get();
    regions.push_back({std::move(data), size});
    return p;
  }
  template <typename T> void Put(void *p, std::size_t off, T value) {
    std::memcpy(static_cast<std::byte *>(p) + off, &value, sizeof(value));
  }
  void Deny(const void *p, std::size_t off, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(p) + off, size});
  }
  std::size_t Attempts() const {
    std::size_t n = 0;
    for (const auto &d : denied) n += d.attempts;
    return n;
  }
  static bool Read(void *context, const void *p, void *out, std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(p);
    for (auto &d : m.denied) {
      if (begin < d.begin + d.size && d.begin < begin + size) {
        ++d.attempts;
        return false;
      }
    }
    for (const auto &r : m.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(r.data.get());
      if (begin >= base && begin - base <= r.size &&
          size <= r.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(out, p, size);
        return true;
      }
    }
    return false;
  }
};

struct Fixture {
  Memory m;
  xar::ck3_12002::ContextSourceBindingsV1 b{};
  void *character = m.Allocate(0x1D0);
  void *component = m.Allocate(0xA8);
  void *first = m.Allocate(0x948);
  void *second = m.Allocate(0x100);
  void *third = m.Allocate(0x30);
  void *store = m.Allocate(0x30);
  void *table = m.Allocate(32);
  void *first_slot = m.Allocate(8);
  void *first_fallback_slot = m.Allocate(8);
  void *second_slot = m.Allocate(8);
  void *second_fallback_slot = m.Allocate(8);
  void *third_slot = m.Allocate(8);
  void *third_fallback_slot = m.Allocate(8);
  void *manager_slot = m.Allocate(8);
  void *manager = m.Allocate(0xEF8);
  void *definition = m.Allocate(0x100);
  void *invalid_slot = m.Allocate(8);
  void *low_slot = m.Allocate(8);
  void *high_slot = m.Allocate(8);
  void *default_pc = m.Allocate(0x80);
  void *default_guard = m.Allocate(4);
  void *static_header = m.Allocate(0x10);
  void *static_guard = m.Allocate(4);
  void *direct_pc = m.Allocate(0x80);
  void *source = m.Allocate(0xA98);
  void *direct_list = m.Allocate(16);
  void *source_list = m.Allocate(16);
  static constexpr std::uint32_t first_id = 0xAB000001U;
  void Property(void *pc, std::int64_t value) {
    void *keys = m.Allocate(2);
    void *values = m.Allocate(8);
    m.Put(pc, 0, keys);
    m.Put(pc, 0xC, std::int32_t{1});
    m.Put(pc, 0x68, values);
    m.Put(pc, 0x74, std::int32_t{1});
    m.Put(keys, 0, std::uint16_t{5});
    m.Put(values, 0, value);
  }
  Fixture() {
    b.enabled = true;
    b.helper_291f0a0_enabled = true;
    b.selector_a_storage_slot = first_slot;
    b.selector_a_initial_fallback_slot = first_fallback_slot;
    b.selector_a_second_storage_slot = second_slot;
    b.selector_a_second_fallback_slot = second_fallback_slot;
    b.helper_third_storage_slot = third_slot;
    b.helper_third_fallback_slot = third_fallback_slot;
    b.helper_manager_slot = manager_slot;
    b.helper_invalid_character_fallback_slot = invalid_slot;
    b.helper_range_first_threshold_slot = low_slot;
    b.helper_range_last_threshold_slot = high_slot;
    b.helper_default_pc = default_pc;
    b.helper_default_pc_guard_slot = default_guard;
    b.helper_source_pointer_fallback_header = static_header;
    b.helper_source_pointer_fallback_guard_slot = static_guard;
    b.read_memory = &Memory::Read;
    b.read_context = &m;
    m.Put(character, 0x18, std::int32_t{29829});
    m.Put(character, 0x1C, std::uint32_t{0x43686172});
    m.Put(character, 0xB4, first_id);
    m.Put(character, 0x1C8, component);
    m.Put(first, 8, first_id);
    m.Put(first_slot, 0, store);
    m.Put(store, 0x20, table);
    m.Put(store, 0x2C, std::uint32_t{2});
    m.Put(table, 24, first);
    m.Put(first_fallback_slot, 0, first);
    m.Put(second_fallback_slot, 0, second);
    m.Put(third_fallback_slot, 0, third);
    m.Put(manager_slot, 0, manager);
    m.Put(manager, 0xEF0, definition);
    m.Put(invalid_slot, 0, definition);
    m.Put(default_guard, 0, std::int32_t{-2});
    m.Put(static_guard, 0, std::int32_t{-2});
    m.Put(low_slot, 0, std::int64_t{-100});
    m.Put(high_slot, 0, std::int64_t{100});
    m.Put(direct_list, 0, direct_pc);
    m.Put(direct_list, 8, direct_pc);
    m.Put(first, 0x20, direct_list);
    m.Put(first, 0x2C, std::int32_t{2});
    m.Put(first, 0x938, direct_list);
    m.Put(first, 0x944, std::int32_t{2});
    m.Put(source_list, 0, source);
    m.Put(source_list, 8, source);
    m.Put(component, 0x88, source_list);
    m.Put(component, 0x94, std::int32_t{2});
    Property(direct_pc, 42);
    Property(static_cast<std::byte *>(source) + 0xA18, -9);
  }
  xar::game::ContextSourceHelper291f0a0V1 Observe() {
    const auto s = xar::ck3_12002::ReadCurrentContextSourceInputs12003(b, character, 29829);
    Require(s.helper_291f0a0.has_value(), "helper section absent");
    return *s.helper_291f0a0;
  }
};
void Save(const std::filesystem::path &dir, const char *name,
          const xar::game::ContextSourceHelper291f0a0V1 &leaf) {
  if (dir.empty()) return;
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 s{};
  s.status = "partial";
  s.character_id = 29829;
  s.reason = "other_source_families_unobserved";
  s.helper_291f0a0 = leaf;
  std::ofstream out(dir / (std::string(name) + ".json"), std::ios::binary);
  out << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(s);
  if (!out) throw std::runtime_error("helper wire write failed");
}
void Run(const std::filesystem::path &dir) {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = xar::ck3_12002::BindContextSourceInputs12003(base, xar::ck3_12003::kExecutableSha256);
  Require(b.helper_291f0a0_enabled, "exact helper enabled");
  Require(b.helper_manager_slot == reinterpret_cast<void *>(base + 0x5D1F6D0), "manager slot RVA");
  Require(b.helper_third_storage_slot == reinterpret_cast<void *>(base + 0x5D1DE88), "third registry RVA");
  Require(b.helper_third_fallback_slot == reinterpret_cast<void *>(base + 0x5D1DE00), "third fallback RVA");
  Require(b.helper_default_pc == reinterpret_cast<void *>(base + 0x5D70FC0), "default inline PC RVA");
  Require(b.helper_source_pointer_fallback_header == reinterpret_cast<void *>(base + 0x5D67E40), "source inline header RVA");
  {
    Fixture f;
    const auto s = f.Observe();
    Require(s.ready && s.primary_direct.rows->size() == 2 && s.source_a18.rows->size() == 2, "all four families ready");
    Require(s.first_key_b4_raw == static_cast<std::int32_t>(Fixture::first_id), "full generation bits retained");
    Require(s.primary_direct.rows->at(0).source_identity == s.primary_direct.rows->at(1).source_identity, "duplicates retain selected identity");
    Require(s.manager_definition_selection == "manager_ef0" && s.range_selection == "inline_default_5d70fc0", "actual default range selections");
    Require(s.manager_range.rows->at(0).admitted == false && s.predicate_admitted == true, "empty manager PC and zero DWORD equality");
    Save(dir, "four-families-default", s);
  }
  {
    Fixture f;
    void *ranges = f.m.Allocate(0x430);
    f.m.Put(f.definition, 0x58, ranges);
    f.m.Put(f.definition, 0x64, std::int32_t{2});
    f.m.Put(f.component, 0xA0, std::int64_t{10});
    f.m.Put(ranges, 0x1E0, std::int64_t{5});
    f.m.Put(ranges, 0x1E8, std::int64_t{10});
    f.m.Put(ranges, 0x218 + 0x1E0, std::int64_t{10});
    f.m.Put(ranges, 0x218 + 0x1E8, std::int64_t{20});
    f.Property(ranges, 101);
    f.Property(static_cast<std::byte *>(ranges) + 0x218, 202);
    const auto s = f.Observe();
    Require(s.ready && s.range_native_index == 1 && s.range_selection == "first_matching_stored_interval", "positive lower inclusive upper exclusive");
    Require(s.manager_range.rows->at(0).property_block->values_q64->at(0) == 202, "actual selected PC values");
    Save(dir, "range-positive-boundary", s);
  }
  {
    Fixture f;
    f.m.Put(f.character, 0x1C8, static_cast<void *>(nullptr));
    const auto s = f.Observe();
    Require(!s.ready && !s.manager_range.ready && s.recipient_source == "absent_1c8_2bfac30_unobserved", "absent recipient not invented");
    Require(s.primary_direct.ready && s.source_a18.ready && s.conditional_direct.ready, "independent three families remain available");
    Require(s.source_a18.count == 0 && s.pointer_list_guard_raw == -2, "actual initialized fallback header");
    Save(dir, "absent-recipient-independent-families", s);
  }
  {
    Fixture f;
    f.m.Put(f.manager_slot, 0, static_cast<void *>(nullptr));
    f.m.Deny(f.manager, 0x50, 0x10);
    const auto s = f.Observe();
    Require(!s.ready && s.manager_present == false && !s.manager_definition_selection, "actual lazy null manager preserved");
    Require(s.primary_direct.ready && s.source_a18.ready && s.conditional_direct.ready && f.m.Attempts() == 0, "null manager skips manager reads");
    Save(dir, "lazy-manager-uninitialized", s);
  }
  {
    Fixture f;
    f.m.Put(f.default_guard, 0, std::int32_t{0});
    const auto s = f.Observe();
    Require(!s.ready && s.default_pc_guard_raw == 0 && s.manager_range.count == 0, "current zero PC not declared initialized");
    Require(s.manager_range.reason == "helper_default_pc_not_initialized", "initializer-specific reason");
    Save(dir, "lazy-default-pc-uninitialized", s);
  }
  {
    Fixture f;
    f.m.Put(f.character, 0x15C, std::int32_t{-1});
    f.m.Deny(f.first, 0x938, 0x10);
    const auto s = f.Observe();
    Require(s.ready && s.predicate_admitted == false && s.conditional_direct.rows->empty(), "early ALfalse");
    Require(!s.predicate_second_a0_raw && !s.conditional_direct.count && f.m.Attempts() == 0, "false predicate does not demand conditional list");
    Save(dir, "early-predicate-false", s);
  }
  {
    Fixture f;
    void *keys = f.m.Allocate(8);
    void *definitions = f.m.Allocate(16);
    void *key = f.m.Allocate(1);
    f.m.Put(f.third, 0x20, key);
    f.m.Put(keys, 0, key);
    f.m.Put(f.definition, 0x40, keys);
    f.m.Put(f.definition, 0x4C, std::int32_t{1});
    f.m.Put(definitions, 0, f.definition);
    f.m.Put(definitions, 8, f.definition);
    f.m.Put(f.manager, 0x50, definitions);
    f.m.Put(f.manager, 0x5C, std::int32_t{2});
    f.m.Deny(f.manager, 0xEF0, 8);
    const auto s = f.Observe();
    Require(s.ready && s.manager_definition_selection == "first_matching_stored_definition" && f.m.Attempts() == 0, "bit-equal membership selects first without EF0 fallback");
    Save(dir, "first-matching-manager-definition", s);
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    const std::filesystem::path dir = argc == 2 ? argv[1] : "";
    if (!dir.empty()) std::filesystem::create_directories(dir);
    Run(dir);
    std::cout << "helper291F0A0 current source observer GREEN\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
