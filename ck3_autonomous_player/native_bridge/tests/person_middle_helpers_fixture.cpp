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
void MiddleRequire(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
struct MiddleMemory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    void *pointer = data.get();
    regions.push_back({std::move(data), size});
    return pointer;
  }
  template <typename T> void Put(void *p, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
  }
  void Deny(const void *p, std::size_t offset, std::size_t bytes) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(p) + offset, bytes});
  }
  static bool Read(void *context, const void *p, void *out, std::size_t bytes) noexcept {
    auto &memory = *static_cast<MiddleMemory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(p);
    for (auto &range : memory.denied)
      if (begin < range.begin + range.size && range.begin < begin + bytes) {
        ++range.attempts; return false;
      }
    for (const auto &region : memory.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(region.data.get());
      if (begin >= base && begin - base <= region.size && bytes <= region.size - (begin - base)) {
        std::memcpy(out, p, bytes); return true;
      }
    }
    return false;
  }
};
void *MiddleAt(void *p, std::size_t offset) { return static_cast<std::byte *>(p) + offset; }
struct MiddleFixture {
  MiddleMemory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x400);
  void *component = memory.Allocate(0x300);
  void *weight_carrier = memory.Allocate(0x100);
  void *weight_values = memory.Allocate(32);
  void *manager = memory.Allocate(0x1200);
  void *manager_slot = memory.Allocate(8);
  void *rank_fallback_slot = memory.Allocate(8);
  void *empty_definition = memory.Allocate(0xC0);
  void *weight_default = memory.Allocate(0xE0);
  void *weight_guard = memory.Allocate(4);
  void *land = memory.Allocate(0x260);
  void *context = memory.Allocate(0x80);
  void *foreign = memory.Allocate(0x80);
  void *foreign_owner = memory.Allocate(0x20);
  void *modifier = memory.Allocate(0x200);
  void *modifier_base = memory.Allocate(0x3500);
  void *terminal_link = memory.Allocate(0x60);
  void *terminal_base = memory.Allocate(0x1600);
  void *foreign_terminal_link = memory.Allocate(0x60);
  void *registry_slot = memory.Allocate(8);
  void *fallback_slot = memory.Allocate(8);
  void *null_header = memory.Allocate(0x10);
  void *modifier_fallback_slot = memory.Allocate(8);

  void Property(void *pc, std::int64_t value) {
    void *keys = memory.Allocate(2), *values = memory.Allocate(8);
    memory.Put(pc, 0, keys); memory.Put(pc, 0xC, std::int32_t{1});
    memory.Put(pc, 0x68, values); memory.Put(pc, 0x74, std::int32_t{1});
    memory.Put(keys, 0, std::uint16_t{5}); memory.Put(values, 0, value);
  }
  void Header(void *p, std::size_t offset, void *data, std::int32_t count) {
    memory.Put(p, offset, data); memory.Put(p, offset + 0xC, count);
  }
  MiddleFixture() {
    bindings.enabled = true;
    bindings.read_memory = &MiddleMemory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.middle_helpers;
    b.enabled = true; b.manager_slot = manager_slot; b.rank_fallback_slot = rank_fallback_slot;
    b.weight_default_pc = weight_default; b.weight_default_guard_slot = weight_guard;
    b.subc_registry_slot = registry_slot; b.subc_fallback_slot = fallback_slot;
    b.null_land_list_header = null_header; b.modifier_default_base_slot = modifier_fallback_slot;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1B0, component); memory.Put(character, 0x1C0, land);
    memory.Put(component, 0x258, weight_carrier); memory.Put(weight_carrier, 8, character);
    memory.Put(manager_slot, 0, manager); memory.Put(rank_fallback_slot, 0, empty_definition);
    constexpr std::size_t scores[] = {0x138, 0x118, 0x158, 0x178};
    constexpr std::size_t overrides[] = {0x140, 0x120, 0x160, 0x180};
    constexpr std::size_t arrays[] = {0x10C0, 0x1058, 0x1128, 0x1190};
    constexpr std::size_t counts[] = {0x10CC, 0x1064, 0x1134, 0x119C};
    for (int i = 0; i < 4; ++i) {
      void *thresholds = memory.Allocate(24), *pointer_slot = memory.Allocate(8), *count_slot = memory.Allocate(4);
      memory.Put(thresholds, 0, std::int64_t{10}); memory.Put(thresholds, 8, std::int64_t{20});
      memory.Put(thresholds, 16, std::int64_t{40}); memory.Put(pointer_slot, 0, thresholds);
      memory.Put(count_slot, 0, std::int32_t{3});
      b.threshold_pointer_slots[i] = pointer_slot; b.threshold_count_slots[i] = count_slot;
      memory.Put(component, scores[i], std::int64_t{i == 3 ? -9 : 25});
      memory.Put(component, overrides[i], std::int32_t{i == 1 ? 1 : i == 2 ? 0 : -1});
      void *definitions = memory.Allocate(24);
      for (int j = 0; j < 3; ++j) {
        void *definition = memory.Allocate(0xC0);
        if (i != 1) Property(MiddleAt(definition, 0x40), 101 + i);
        memory.Put(definitions, j * 8, definition);
      }
      Header(manager, arrays[i], definitions, 3);
      MiddleRequire(arrays[i] + 0xC == counts[i], "middle manager header offsets");
    }
    void *weight_keys = memory.Allocate(8);
    constexpr std::uint16_t keys[] = {44, 45, 45, 47};
    constexpr std::int64_t values[] = {-40, -100000, 999, 37};
    for (int i = 0; i < 4; ++i) {
      memory.Put(weight_keys, i * 2, keys[i]); memory.Put(weight_values, i * 8, values[i]);
    }
    memory.Put(weight_carrier, 0x10 + 0x68, weight_keys);
    memory.Put(weight_carrier, 0x10 + 0x74, std::int32_t{4});
    memory.Put(weight_carrier, 0x10 + 0xD0, weight_values);
    memory.Deny(weight_values, 16, 8); // Duplicate weight key must use its first value.
    memory.Put(weight_guard, 0, std::int32_t{0});

    memory.Put(context, 8, std::uint32_t{0xAA000001U});
    memory.Put(context, 0xC, std::uint32_t{0x5362436F});
    memory.Put(context, 0x20, character); memory.Put(context, 0x30, terminal_link);
    memory.Put(terminal_link, 0x50, terminal_base);
    void *objects = memory.Allocate(16), *tokens = memory.Allocate(2);
    memory.Put(objects, 0, modifier); memory.Put(objects, 8, modifier);
    memory.Put(tokens, 0, std::uint8_t{0}); memory.Put(tokens, 1, std::uint8_t{1});
    Header(context, 0x38, objects, 2); memory.Put(context, 0x68, tokens);
    memory.Put(modifier, 0x1E0, modifier_base); memory.Put(modifier, 0x1EC, std::uint8_t{2});
    Property(MiddleAt(modifier_base, 0x13C8), 401);
    Property(MiddleAt(modifier_base, 0x1A30 + 0x13C8), 402);
    Property(MiddleAt(modifier_base, 0x1208), 403);
    memory.Put(modifier_fallback_slot, 0, modifier_base);
    memory.Put(foreign, 8, std::uint32_t{0xBB000002U});
    memory.Put(foreign, 0xC, std::uint32_t{0x5362436F});
    memory.Put(foreign_owner, 0x18, std::int32_t{29830});
    memory.Put(foreign, 0x20, foreign_owner); memory.Put(foreign, 0x30, foreign_terminal_link);
    memory.Put(foreign_terminal_link, 0x50, MiddleAt(terminal_base, 0x1C0));
    void *foreign_objects = memory.Allocate(8), *foreign_tokens = memory.Allocate(1);
    memory.Put(foreign_objects, 0, modifier); memory.Put(foreign_tokens, 0, std::uint8_t{2});
    Header(foreign, 0x38, foreign_objects, 1); memory.Put(foreign, 0x68, foreign_tokens);
    memory.Put(land, 0x1C0, context);
    void *ids218 = memory.Allocate(4), *ids248 = memory.Allocate(4);
    memory.Put(ids218, 0, std::uint32_t{0xAA000001U}); memory.Put(ids248, 0, std::uint32_t{0xBB000002U});
    Header(land, 0x218, ids218, 1); Header(land, 0x248, ids248, 1);
    void *registry = memory.Allocate(0x30), *table = memory.Allocate(48);
    memory.Put(registry_slot, 0, registry); memory.Put(registry, 0x20, table);
    memory.Put(registry, 0x2C, std::uint32_t{3}); memory.Put(table, 24, context); memory.Put(table, 40, foreign);
    memory.Put(fallback_slot, 0, context);
  }
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 Observe() {
    MiddleRequire(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
                  "middle native callbacks not assigned");
    const auto first = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto second = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    MiddleRequire(first == second, "middle whole-query snapshots differ");
    MiddleRequire(first.middle_helpers_291f260_291fb10.has_value(), "middle wire section omitted");
    return first;
  }
};
void MiddleSave(const std::filesystem::path &directory, const char *name,
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  MiddleRequire(static_cast<bool>(out), "middle wire write failed");
}
}

int RunMiddleHelpersFixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  {
    MiddleFixture f;
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.middle_helpers_291f260_291fb10;
    MiddleRequire(leaf.ready, "middle positive helpers partial");
    const auto &families = leaf.helper_291f260.families;
    MiddleRequire(families.size() == 4 && families[0].rank_raw == 2 && families[1].rank_raw == 1 &&
                  families[2].rank_raw == 0 && families[3].rank_raw == 0, "middle native rank/clamp order");
    MiddleRequire(families[0].weight_q64 == 0 && families[0].weight_native_index == 1 &&
                  families[1].admitted == false && !families[1].weight_q64 &&
                  families[2].weight_q64 == 100000 && families[3].weight_q64 == 100037,
                  "middle first weight key, missing key, zero gate or zero weight");
    const auto &fb = leaf.helper_291fb10;
    const auto &preferred = fb.preferred.rows->at(0);
    const auto &repeat = fb.list_218.rows->at(0);
    const auto &foreign = fb.list_248.rows->at(0);
    MiddleRequire(preferred.owner_matches == true && foreign.owner_matches == false &&
                  foreign.modifier_rows->at(0).base_selection == "native_modifier_fallback",
                  "middle owner or token equality branch");
    MiddleRequire(preferred.terminal_property_identity == repeat.terminal_property_identity &&
                  repeat.terminal_property_identity == foreign.terminal_property_identity &&
                  preferred.terminal_property_block->keys_count == 0,
                  "middle unconditional empty terminal alias lost");
    for (const auto &denied : f.memory.denied)
      MiddleRequire(denied.attempts == 0, "middle consumed later duplicate weight value");
    MiddleSave(directory, "middle-positive", snapshot);
  }
  {
    MiddleFixture f;
    f.memory.Put(f.character, 0x1B0, static_cast<void *>(nullptr));
    f.memory.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    f.memory.Put(f.context, 0xC, std::uint32_t{0});
    for (const auto offset : {0x10CCU, 0x1064U, 0x1134U, 0x119CU})
      f.memory.Put(f.manager, offset, std::int32_t{0});
    for (const auto *slot : f.bindings.middle_helpers.threshold_count_slots)
      f.memory.Deny(slot, 0, 4);
    f.memory.Deny(f.weight_default, 0, 0xE0);
    f.memory.Deny(f.weight_guard, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.middle_helpers_291f260_291fb10;
    MiddleRequire(leaf.ready && leaf.helper_291f260.component_present == false &&
                  leaf.helper_291fb10.land_present == false, "middle legal empty unavailable");
    for (const auto &row : leaf.helper_291f260.families)
      MiddleRequire(row.rank_raw == 0 && row.admitted == false && !row.weight_q64, "middle null component gate skip");
    for (const auto &denied : f.memory.denied)
      MiddleRequire(denied.attempts == 0, "middle empty branch demanded thresholds or weight");
    MiddleSave(directory, "middle-empty", snapshot);
  }
  {
    MiddleFixture f;
    f.memory.Deny(f.component, 0x158, 8);
    f.memory.Deny(f.foreign_terminal_link, 0x50, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.middle_helpers_291f260_291fb10;
    MiddleRequire(!leaf.ready && leaf.helper_291f260.families[0].ready &&
                  !leaf.helper_291f260.families[2].ready &&
                  leaf.helper_291fb10.preferred.ready && leaf.helper_291fb10.list_218.ready &&
                  !leaf.helper_291fb10.list_248.ready, "middle independent partial sources lost");
    MiddleSave(directory, "middle-partial", snapshot);
  }
  return 0;
}
