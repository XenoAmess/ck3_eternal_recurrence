#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"
#include "xar_bridge/state_snapshot_frame_v1.hpp"
#include "ck3_12004_foundation_fixture_support.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
namespace current = xar::ck3_12004;
namespace game = xar::game;
constexpr std::int32_t kRobert = current::fixture::CoreMemory::kCharacterId;
constexpr std::int32_t kDate = 53288232;

void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template <typename T>
void Store(void *base, std::size_t offset, const T &value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template <typename T>
T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(value));
  return value;
}

struct EventMemory;
EventMemory *g_memory = nullptr;

// The reached resource/event/World/settlement operands reuse the closed actual4
// foundation fixture. Only the two definition keys and HasTrait results are new.
// All callbacks and memory below are caller-owned; no CK3 code RVA is invoked.
struct EventMemory {
  current::fixture::CoreMemory original_core{kDate, 4, true};
  current::CoreBindings core = original_core.Bindings();
  std::array<std::byte, 0x300> actor_bytes{};
  std::vector<std::byte> data{current::kEventManagerOffset12004 + 16};
  std::array<std::byte, 0x30> characters{};
  std::vector<std::byte> character_rows{
      static_cast<std::size_t>(kRobert + 1) * current::kCharacterStorageSlotStride};
  std::array<std::byte, 0x300> resources{};
  std::array<std::byte, 0x1C0> event{};
  std::array<std::byte, 0x1B0> event_definition{};
  std::array<std::byte, 0x30> pending_storage{};
  std::array<std::byte, 0x30> unit_storage{};
  std::array<std::byte, 0x30> war_storage{};
  std::array<std::byte, 0x20> globals{};
  std::array<std::byte, 0x20> ready_entry{};
  std::array<std::byte, 1> identifier_table{};
  std::array<std::uintptr_t, 1> reply_primary_table{};
  std::array<std::uintptr_t, 1> reply_secondary_table{};
  std::array<std::byte, 0x60> trait_database{};
  std::array<std::byte, 0x40> poet_definition{};
  std::array<std::byte, 0x40> journaller_definition{};
  std::array<void *, 2> trait_rows{poet_definition.data(), journaller_definition.data()};
  void *character_slot = characters.data();
  void *pending_slot = pending_storage.data();
  void *unit_slot = unit_storage.data();
  xar::ck3_12002::SettlementGlobalAccessor global_accessor = &GetGlobals;
  void *actor = actor_bytes.data();
  bool event_visible = true;
  bool poet = false;
  bool journaller = false;
  std::size_t trait_reads = 0;

  EventMemory() {
    g_memory = this;
    const auto old_actor = current::ResolveCoreCharacter(core, kRobert);
    Check(old_actor != nullptr, "owned current player did not resolve");
    std::memcpy(actor, old_actor, current::kCharacterDeathDataOffset + sizeof(void *));
    const auto old_data = Load<void *>(*core.game_state_slot, current::kGameStateDataOffset);
    std::memcpy(data.data(), old_data,
        current::kPlayerCharacterManagerOffset + current::kPlayerManagerCountOffset + 4);
    Store(*core.game_state_slot, current::kGameStateDataOffset, data.data());
    Store(characters.data(), current::kCharacterStorageSlotsOffset, character_rows.data());
    Store(characters.data(), current::kCharacterStorageCapacityOffset, kRobert + 1);
    Store(character_rows.data(), static_cast<std::size_t>(kRobert) *
        current::kCharacterStorageSlotStride + current::kCharacterStorageObjectOffset, actor);
    core.character_storage_slot = &character_slot;
    Store(actor, 0x1B0, resources.data());
    Store(resources.data(), 0x2F8, std::int32_t{120});
    Store(event.data(), 0x1B0, event_definition.data());
    Store(event.data(), 0x1BC, std::int32_t{17});
    Store(event_definition.data(), 0x1AC, std::int32_t{3});
    Store(data.data(), xar::ck3_12002::kWorldWarManagerOffset + 0x20, war_storage.data());
    Store(globals.data(), 0x10, ready_entry.data());
    Store(globals.data(), 0x1C, std::int32_t{1});
    Store(ready_entry.data(), 0x08, std::int32_t{17});
    Store(ready_entry.data(), 0x10, std::uint16_t{1});
    Store(ready_entry.data(), 0x18, std::int64_t{0});
    PutTrait(poet_definition.data(), "lifestyle_poet");
    PutTrait(journaller_definition.data(), "journaller");
    Store(trait_database.data(), 0x50, trait_rows.data());
    Store(trait_database.data(), 0x5C, std::int32_t{2});
  }
  EventMemory(const EventMemory &) = delete;
  EventMemory &operator=(const EventMemory &) = delete;
  ~EventMemory() { g_memory = nullptr; }

  static void PutTrait(void *definition, std::string_view key) noexcept {
    // Both concrete keys fit the adopted MSVC short-string layout.
    std::memcpy(static_cast<std::byte *>(definition) + 0x18, key.data(), key.size());
    Store(definition, 0x28, static_cast<std::uint64_t>(key.size()));
    Store(definition, 0x30, std::uint64_t{15});
  }
  game::Ck3_12004AdapterBindings Bindings() {
    game::Ck3_12004AdapterBindings out{};
    out.core = core;
    out.read_core_snapshot = current::ReadCoreSnapshot;
    out.armies.enabled = true;
    out.armies.game_state_slot = core.game_state_slot;
    out.armies.unit_storage_slot = &unit_slot;
    out.armies.get_unit_state = &EmptyUnitState;
    out.world.enabled = true;
    out.world.game_state_slot = core.game_state_slot;
    out.world.character_storage_slot = core.character_storage_slot;
    out.world.contains_war_participant = &EmptyContainsParticipant;
    out.world.get_war_score = &EmptyWarScore;
    out.provinces.enabled = true;
    current::SnapshotFoundationBindings foundation{};
    foundation.core = core;
    foundation.events = {core, &GetEvent, &pending_slot, &NoPending, &NoReply,
        reinterpret_cast<std::uintptr_t>(reply_primary_table.data()),
        reinterpret_cast<std::uintptr_t>(reply_secondary_table.data())};
    foundation.settlement = {true, &global_accessor, &GetIdentifierTable, &LookupIdentifier};
    foundation.event_traits.enabled = true;
    foundation.event_traits.core = core;
    foundation.event_traits.traits.enabled = true;
    foundation.event_traits.traits.get_trait_database = &GetTraitDatabase;
    foundation.event_traits.traits.character_has_trait = &HasTrait;
    out.snapshot_foundation12004 =
        std::make_shared<const current::SnapshotFoundationBindings>(foundation);
    return out;
  }
  static void *GetEvent(void *manager) {
    auto &memory = *g_memory;
    return memory.event_visible &&
        manager == memory.data.data() + current::kEventManagerOffset12004
        ? memory.event.data() : nullptr;
  }
  static bool NoPending(void *, void *) { return false; }
  static bool NoReply(void *) { return false; }
  static void *GetGlobals() { return g_memory->globals.data(); }
  static void *GetIdentifierTable() { return g_memory->identifier_table.data(); }
  static std::int32_t *LookupIdentifier(void *, std::int32_t *output, const void *) {
    *output = 17;
    return output;
  }
  static std::int32_t EmptyUnitState(void *) { return 0; }
  static bool EmptyContainsParticipant(const void *, std::int32_t) { return false; }
  static std::int32_t EmptyWarScore(void *) { return 0; }
  static void *GetTraitDatabase() { return g_memory->trait_database.data(); }
  static bool HasTrait(void *character, const void *definition) {
    auto &memory = *g_memory;
    Check(character == memory.actor, "HasTrait received an unrelated character");
    ++memory.trait_reads;
    if (definition == memory.poet_definition.data()) return memory.poet;
    if (definition == memory.journaller_definition.data()) return memory.journaller;
    throw std::runtime_error("HasTrait received an unrelated definition");
  }
};

void Write(const std::filesystem::path &path, std::string_view wire) {
  std::ofstream output(path, std::ios::binary);
  output << wire << '\n';
  Check(output.good(), "native event trait fixture wire output failed");
}
game::Snapshot Capture(game::GameAdapter &adapter) {
  game::Snapshot output;
  Check(adapter.read_snapshot(output), "actual4 complete Snapshot read failed");
  Check(output.paused && output.date_raw == kDate && output.played_character_id == kRobert,
      "Snapshot current player scope differs");
  Check(output.played_character_event_trait_membership.has_value() &&
      output.played_character_event_trait_membership->available,
      "actual trait producer was skipped or unavailable");
  Check(output.played_character_event_trait_membership->snapshot_revision == 0,
      "capture invented a publication revision");
  return output;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "usage: xar_ck3_12004_player_event_trait_pipeline_test <wire-output-dir>");
    const std::filesystem::path output(argv[1]);
    std::filesystem::create_directories(output);
    EventMemory memory;
    auto adapter = game::CreateCk3_12004AdapterFromBindings(memory.Bindings());
    Check(adapter && adapter->enabled() && game::IsCk3_12004Descriptor(adapter->descriptor()),
        "actual4 selected adapter unavailable");
    const auto before = Capture(*adapter);
    Check(before.has_active_event && !before.played_character_event_trait_membership->lifestyle_poet &&
        !before.played_character_event_trait_membership->journaller,
        "initial concrete membership or event differs");
    memory.event_visible = false;
    const auto closed_only = Capture(*adapter);
    Check(!closed_only.has_active_event &&
        !closed_only.played_character_event_trait_membership->journaller,
        "event closure fabricated a material trait gain");
    memory.journaller = true;
    Store(memory.resources.data(), 0x2F8, std::int32_t{100});
    const auto gained = Capture(*adapter);
    Check(!gained.has_active_event && gained.played_character_event_trait_membership->journaller &&
        !gained.played_character_event_trait_membership->lifestyle_poet,
        "persistent journaller result was lost after event closure");
    Check(memory.trait_reads == 6, "three complete reads did not query both concrete traits");
    const auto before_wire = xar::bridge::SerializeStateSnapshotFrameV1(before, 51);
    const auto closed_wire = xar::bridge::SerializeStateSnapshotFrameV1(closed_only, 52);
    const auto gained_wire = xar::bridge::SerializeStateSnapshotFrameV1(gained, 53);
    Check(gained_wire.find("\"event_trait_membership\":{\"schema\":") != std::string::npos &&
        gained_wire.find("\"snapshot_revision\":53") != std::string::npos &&
        gained_wire.find("\"journaller\":true") != std::string::npos,
        "production state_snapshot publisher omitted membership or actual native revision");
    Write(output / "before.json", before_wire);
    Write(output / "event-closed-without-gain.json", closed_wire);
    Write(output / "after-journaller.json", gained_wire);
    std::cout << "actual4 owned-memory trait producer -> full Snapshot -> production state_snapshot passed\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
