#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"
#include "xar_bridge/ck3_12003_context_sources.hpp"

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
void ConferenceRequire(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
struct ConferenceMemory {
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
    auto &memory = *static_cast<ConferenceMemory *>(context);
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
void *ConferenceAt(void *p, std::size_t offset) { return static_cast<std::byte *>(p) + offset; }
struct ConferenceFixture {
  ConferenceMemory memory;
  xar::ck3_12002::ContextSourceBindingsV1 bindings{};
  void *character = memory.Allocate(0x400);
  void *carrier = memory.Allocate(0x90);
  void *conference = memory.Allocate(0x80);
  void *config = memory.Allocate(0xAB10);
  void *records = memory.Allocate(3 * 0x1530);
  void *default_pack = memory.Allocate(0x1530);
  void *default_guard = memory.Allocate(4);
  void *conf_registry_slot = memory.Allocate(8);
  void *conf_registry = memory.Allocate(0x30);
  void *conf_table = memory.Allocate(32);
  void *conf_fallback_slot = memory.Allocate(8);
  void *relation_registry_slot = memory.Allocate(8);
  void *relation_registry = memory.Allocate(0x30);
  void *relation_table = memory.Allocate(48);
  void *relation_fallback_slot = memory.Allocate(8);
  void *first = memory.Allocate(0x230);
  void *second = memory.Allocate(0x230);
  void *group_a = memory.Allocate(1);
  void *group_b = memory.Allocate(1);
  void *selected_pack = ConferenceAt(records, 0x1530);

  void Property(std::size_t offset, std::int64_t value) {
    void *pc = ConferenceAt(selected_pack, offset);
    void *keys = memory.Allocate(2), *values = memory.Allocate(8);
    memory.Put(pc, 0, keys); memory.Put(pc, 0xC, std::int32_t{1});
    memory.Put(pc, 0x68, values); memory.Put(pc, 0x74, std::int32_t{1});
    memory.Put(keys, 0, std::uint16_t{7}); memory.Put(values, 0, value);
  }
  ConferenceFixture() {
    bindings.enabled = true;
    bindings.read_memory = &ConferenceMemory::Read;
    bindings.read_context = &memory;
    auto &b = bindings.conference_24b1d00;
    b.enabled = true;
    b.conf_registry_slot = conf_registry_slot; b.conf_fallback_slot = conf_fallback_slot;
    b.relation_registry_slot = relation_registry_slot; b.relation_fallback_slot = relation_fallback_slot;
    b.inline_default_pack = default_pack; b.default_guard_slot = default_guard;
    memory.Put(character, 0x18, std::int32_t{29829});
    memory.Put(character, 0x1C, std::uint32_t{0x43686172U});
    memory.Put(character, 0x1C8, carrier);
    memory.Put(carrier, 0x80, std::uint32_t{0xCC000001U});
    memory.Put(conference, 8, std::uint32_t{0xCC000001U});
    memory.Put(conference, 0xC, std::uint32_t{0x436F6E66U});
    memory.Put(conference, 0x38, config); memory.Put(conference, 0x60, std::int64_t{5});
    memory.Put(conference, 0x68, std::uint32_t{0xAA000001U});
    memory.Put(character, 0x158, std::uint32_t{0xBB000002U});
    memory.Put(conf_registry_slot, 0, conf_registry); memory.Put(conf_fallback_slot, 0, conference);
    memory.Put(conf_registry, 0x20, conf_table); memory.Put(conf_registry, 0x2C, std::uint32_t{2});
    memory.Put(conf_table, 24, conference);
    memory.Put(config, 0xAB08, std::uint8_t{1});
    memory.Put(config, 0x160, records); memory.Put(config, 0x16C, std::int32_t{3});
    memory.Put(records, 0x10, std::int64_t{-100});
    memory.Put(records, 0x1530 + 0x10, std::int64_t{5});
    memory.Put(records, 2 * 0x1530 + 0x10, std::int64_t{99});
    memory.Put(default_guard, 0, std::int32_t{0});
    memory.Deny(records, 0x10, 8); // Last qualifying row stops before an earlier match.
    memory.Put(relation_registry_slot, 0, relation_registry);
    memory.Put(relation_fallback_slot, 0, second);
    memory.Put(relation_registry, 0x20, relation_table);
    memory.Put(relation_registry, 0x2C, std::uint32_t{3});
    memory.Put(relation_table, 24, first); memory.Put(relation_table, 40, second);
    memory.Put(first, 0x10, std::uint32_t{0xAA000001U});
    memory.Put(second, 0x10, std::uint32_t{0xBB000002U});
    memory.Put(second, 0x160, std::int32_t{29829});
    // Both actual QWORD+220 values are null; equality still selects category2.
    const std::vector<std::pair<std::size_t, std::int64_t>> properties = {
      {0x30U, 101}, {0x1F0U, 102}, {0x3B0U, 103}, {0x570U, 201}, {0x730U, 202},
      {0xAB0U, 301}, {0xC70U, 302}, {0xE30U, 303},
      {0xFF0U, 401}, {0x11B0U, 402}, {0x1370U, 403},
    };
    for (const auto &[offset, value] : properties) Property(offset, value);
    // PC8F0 remains actual initialized empty and must still emit one request.
  }
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 Observe() {
    ConferenceRequire(!bindings.provider && !bindings.government && !bindings.existing_token_lookup,
                      "conference native callbacks assigned");
    const auto first_snapshot = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    const auto second_snapshot = xar::ck3_12002::ReadCurrentContextSourceInputs12003(bindings, character, 29829);
    ConferenceRequire(first_snapshot == second_snapshot, "conference whole-query samples differ");
    ConferenceRequire(first_snapshot.conference_24b1d00.has_value(), "conference leaf omitted");
    return first_snapshot;
  }
};
void ConferenceSave(const std::filesystem::path &directory, const char *name,
    const xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 &snapshot) {
  if (directory.empty()) return;
  std::ofstream out(directory / (std::string(name) + ".json"), std::ios::binary);
  out << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot);
  ConferenceRequire(static_cast<bool>(out), "conference wire write failed");
}
void ConferenceMappedReady(const xar::game::ContextSourceConference24b1d00V1 &leaf) {
  ConferenceRequire(leaf.ready && leaf.admitted == true && leaf.pack.ready &&
                    leaf.pack.selected_native_index == 1 && leaf.pack.probes->size() == 2 &&
                    leaf.pack.probes->at(0).native_index == 2 && leaf.pack.probes->at(1).native_index == 1 &&
                    !leaf.pack.default_guard_raw, "conference last qualifying mapped pack");
  ConferenceRequire(leaf.families.size() == 4 && leaf.families[3].pc_offset == 0x8F0U &&
                    leaf.families[3].property_block->keys_count == 0,
                    "conference fourth legal empty PC missing");
}
}

void RunConference24b1d00Fixture(const std::filesystem::path &directory) {
  if (!directory.empty()) std::filesystem::create_directories(directory);
  {
    ConferenceFixture f;
    f.memory.Deny(f.default_guard, 0, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.conference_24b1d00;
    ConferenceMappedReady(leaf);
    ConferenceRequire(leaf.category == "same_identity" && leaf.owner_matches == true &&
                      leaf.first_group_identity == leaf.second_group_identity &&
                      leaf.families[0].pc_offset == 0xAB0U && leaf.families[1].pc_offset == 0xE30U &&
                      leaf.families[2].pc_offset == 0x570U, "conference equal null QWORD category");
    for (const auto &denied : f.memory.denied)
      ConferenceRequire(denied.attempts == 0, "conference mapped row demanded earlier row/default guard");
    ConferenceSave(directory, "conference-mapped-same-identity", snapshot);
  }
  {
    ConferenceFixture f;
    f.memory.Put(f.conference, 0x68, std::uint32_t{0xBB000002U});
    f.memory.Deny(f.second, 0x220, 8);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.conference_24b1d00;
    ConferenceMappedReady(leaf);
    ConferenceRequire(leaf.category == "same_id" && !leaf.first_group_identity && !leaf.second_group_identity &&
                      leaf.families[0].pc_offset == 0x30U && leaf.families[1].pc_offset == 0x3B0U,
                      "conference full generation ID equality");
    for (const auto &denied : f.memory.denied)
      ConferenceRequire(denied.attempts == 0, "conference equal IDs demanded group pointer");
    ConferenceSave(directory, "conference-mapped-same-id", snapshot);
  }
  {
    ConferenceFixture f;
    f.memory.Put(f.first, 0x220, f.group_a); f.memory.Put(f.second, 0x220, f.group_b);
    f.memory.Put(f.second, 0x160, std::int32_t{29830});
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.conference_24b1d00;
    ConferenceMappedReady(leaf);
    ConferenceRequire(leaf.category == "different" && leaf.owner_matches == false &&
                      leaf.families[0].pc_offset == 0x11B0U && leaf.families[1].pc_offset == 0x1370U &&
                      leaf.families[2].pc_offset == 0x730U, "conference differing ID/identity and foreign owner");
    ConferenceSave(directory, "conference-mapped-different", snapshot);
  }
  {
    ConferenceFixture f;
    f.memory.Put(f.config, 0xAB08, std::uint8_t{0});
    f.memory.Deny(f.config, 0x160, 0x10);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.conference_24b1d00;
    ConferenceRequire(!leaf.ready && !leaf.pack.ready && leaf.pack.default_guard_raw == 0 &&
                      leaf.pack.selection == "inline_default_54ebab0" && !leaf.pack.count_raw,
                      "conference actual default guard0 readiness");
    for (const auto &row : leaf.families)
      ConferenceRequire(!row.ready && row.property_block && row.property_block->keys_count == 0,
                        "conference uninitialized inline bytes lost or fabricated ready");
    for (const auto &denied : f.memory.denied)
      ConferenceRequire(denied.attempts == 0, "conference disabled pack demanded list header");
    ConferenceSave(directory, "conference-default-guard", snapshot);
  }
  {
    ConferenceFixture f;
    f.memory.Deny(f.conference, 0x68, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.conference_24b1d00;
    ConferenceRequire(!leaf.ready && !leaf.families[0].ready && !leaf.families[1].ready &&
                      leaf.families[2].ready && leaf.families[3].ready,
                      "conference missing first key lost independent final families");
    ConferenceSave(directory, "conference-partial-first", snapshot);
  }
  {
    ConferenceFixture f;
    f.memory.Deny(f.second, 0x160, 4);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.conference_24b1d00;
    ConferenceRequire(!leaf.ready && !leaf.families[0].ready && leaf.families[1].ready &&
                      !leaf.families[2].ready && leaf.families[3].ready && leaf.category == "same_identity",
                      "conference missing owner lost independent category common");
    ConferenceSave(directory, "conference-partial-owner", snapshot);
  }
  {
    ConferenceFixture f;
    f.memory.Put(f.conf_registry_slot, 0, static_cast<void *>(nullptr));
    f.memory.Put(f.conference, 0xC, std::uint32_t{0});
    f.memory.Deny(f.conference, 8, 4); f.memory.Deny(f.character, 0x1C, 4);
    f.memory.Deny(f.config, 0xAB08, 1);
    const auto snapshot = f.Observe();
    const auto &leaf = *snapshot.conference_24b1d00;
    ConferenceRequire(leaf.ready && leaf.admitted == false && leaf.conference_admitted == false &&
                      !leaf.conference.full_id_raw && !leaf.character_magic_raw && !leaf.pack.selection,
                      "conference caller wrong magic known zero");
    for (const auto &row : leaf.families)
      ConferenceRequire(row.ready && row.admitted == false && !row.property_block,
                        "conference skipped family demanded a PC");
    for (const auto &denied : f.memory.denied)
      ConferenceRequire(denied.attempts == 0, "conference false gate demanded helper operands");
    ConferenceSave(directory, "conference-skipped", snapshot);
  }
}
