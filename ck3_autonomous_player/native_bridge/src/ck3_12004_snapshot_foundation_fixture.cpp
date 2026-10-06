#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_core_frame_v1.hpp"
#include "xar_bridge/ck3_12004_family_relationships.hpp"
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
constexpr std::int32_t kRobert = 29829;
constexpr std::int32_t kSpouse = 29830;
constexpr std::int32_t kBetrothed = 29831;
constexpr std::int32_t kPending = 0x01000000;
constexpr std::int64_t kGold = -1234567;
constexpr std::int64_t kPrestige = 2345678;
constexpr std::int64_t kPiety = -3456789;

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

struct SnapshotMemory;
SnapshotMemory *g_memory = nullptr;

struct SnapshotMemory {
  current::fixture::CoreMemory original_core;
  current::CoreBindings core = original_core.Bindings();
  std::array<std::byte, 0x300> actor_bytes{};
  std::vector<std::byte> data{current::kEventManagerOffset12004 + 16};
  std::array<std::byte, 0x30> characters{};
  std::vector<std::byte> character_rows{
      static_cast<std::size_t>(kBetrothed + 1) * current::kCharacterStorageSlotStride};
  std::array<std::byte, 0x20> spouse{};
  std::array<std::byte, 0x20> betrothed{};
  std::array<std::byte, 0x30> family{};
  std::array<std::int32_t, 1> spouse_ids{kSpouse};
  std::array<std::byte, 0x300> resources{};
  std::array<std::byte, 0x1C0> event{};
  std::array<std::byte, 0x1B0> event_definition{};
  std::array<std::byte, 0x5C8> pending{};
  std::array<std::byte, 0x30> pending_storage{};
  std::array<std::byte, 0x10> pending_rows{};
  std::array<std::byte, 0x30> unit_storage{};
  std::array<std::byte, 0x30> war_storage{};
  std::array<std::byte, 0x20> globals{};
  std::array<std::byte, 0x20> ready_entry{};
  std::array<std::byte, 1> identifier_table{};
  std::array<std::uintptr_t, 1> reply_primary_table{};
  std::array<std::uintptr_t, 1> reply_secondary_table{};
  void *character_slot = characters.data();
  void *pending_slot = pending_storage.data();
  void *unit_slot = unit_storage.data();
  xar::ck3_12002::SettlementGlobalAccessor global_accessor = &GetGlobals;
  void *actor = nullptr;
  std::size_t event_calls = 0;
  std::size_t pending_calls = 0;
  std::size_t validation_calls = 0;
  std::size_t settlement_lookup_calls = 0;
  std::size_t unexpected_world_calls = 0;

  SnapshotMemory() {
    g_memory = this;
    const auto original_actor = current::ResolveCoreCharacter(core, kRobert);
    Check(original_actor != nullptr, "owned core CharacterID failed to resolve");
    std::memcpy(actor_bytes.data(), original_actor,
        current::kCharacterDeathDataOffset + sizeof(void *));
    actor = actor_bytes.data();
    const auto old_data = Load<void *>(*core.game_state_slot, current::kGameStateDataOffset);
    std::memcpy(data.data(), old_data,
        current::kPlayerCharacterManagerOffset + current::kPlayerManagerCountOffset + 4);
    Store(*core.game_state_slot, current::kGameStateDataOffset, data.data());
    Store(characters.data(), current::kCharacterStorageSlotsOffset, character_rows.data());
    Store(characters.data(), current::kCharacterStorageCapacityOffset, kBetrothed + 1);
    PutCharacter(kRobert, actor);
    PutCharacter(kSpouse, spouse.data());
    PutCharacter(kBetrothed, betrothed.data());
    core.character_storage_slot = &character_slot;

    using namespace current::family_relationships_abi;
    Store(actor, kCharacterFamilyOffset, family.data());
    Store(family.data(), kBetrothedIdOffset, kBetrothed);
    Store(family.data(), kPrimarySpouseIdOffset, kSpouse);
    Store(family.data(), kSpouseIdsOffset, spouse_ids.data());
    Store(family.data(), kSpouseCapacityOffset, std::int32_t{1});
    Store(family.data(), kSpouseCountOffset, std::int32_t{1});
    // RESOURCE-FAMILY-STRESS-MAP.json closes these actual .4 reader operands.
    Store(actor, 0x1B0, resources.data());
    Store(resources.data(), 0x100, kGold);
    Store(resources.data(), 0x130, kPrestige);
    Store(resources.data(), 0x110, kPiety);
    Store(resources.data(), 0x2F8, std::int32_t{7});

    Store(event.data(), 0x1B0, event_definition.data());
    Store(event.data(), 0x1BC, std::int32_t{77});
    Store(event_definition.data(), 0x1AC, std::int32_t{2});
    Store(pending_storage.data(), 0x20, pending_rows.data());
    Store(pending_storage.data(), 0x2C, std::int32_t{1});
    Store(pending_rows.data(), 8, pending.data());
    Store(pending.data(), 0x10, kPending);
    Store(pending.data(), 0x5C0, std::int32_t{1});
    Store(pending.data(), 0x300, kRobert);
    Store(pending.data(), 0x2F0, kSpouse);
    // Notification remains false, demanding the selected reply validator.

    // Both storage objects exist with an actual capacity of zero. The World
    // reader must return available rather than skipping disabled bindings.
    Store(data.data(), xar::ck3_12002::kWorldWarManagerOffset + 0x20, war_storage.data());

    // A registered ready name whose fixed-point Boolean is zero is lawful
    // unpublished settlement, while all accessor dependencies remain present.
    Store(globals.data(), 0x10, ready_entry.data());
    Store(globals.data(), 0x1C, std::int32_t{1});
    Store(ready_entry.data(), 0x08, std::int32_t{17});
    Store(ready_entry.data(), 0x10, std::uint16_t{1});
    Store(ready_entry.data(), 0x18, std::int64_t{0});
  }

  SnapshotMemory(const SnapshotMemory &) = delete;
  SnapshotMemory &operator=(const SnapshotMemory &) = delete;
  ~SnapshotMemory() { g_memory = nullptr; }

  void PutCharacter(std::int32_t id, void *object) noexcept {
    Store(object, current::kCharacterFullIdOffset, id);
    Store(character_rows.data(), static_cast<std::size_t>(id) *
        current::kCharacterStorageSlotStride + current::kCharacterStorageObjectOffset, object);
  }

  game::Ck3_12004AdapterBindings Bindings(bool missing_settlement_input = false) {
    game::Ck3_12004AdapterBindings out{};
    out.core = core;
    out.read_core_snapshot = current::ReadCoreSnapshot;
    out.armies.enabled = true;
    out.armies.game_state_slot = core.game_state_slot;
    out.armies.unit_storage_slot = &unit_slot;
    out.armies.get_unit_state = &UnexpectedUnitState;
    out.world.enabled = true;
    out.world.game_state_slot = core.game_state_slot;
    out.world.character_storage_slot = core.character_storage_slot;
    out.world.contains_war_participant = &UnexpectedContainsParticipant;
    out.world.get_war_score = &UnexpectedWarScore;
    out.provinces.enabled = true;
    current::SnapshotFoundationBindings foundation{};
    foundation.core = core;
    foundation.events = {core, &GetEvent, &pending_slot, &IsPendingForCharacter,
        &ValidateReply, reinterpret_cast<std::uintptr_t>(reply_primary_table.data()),
        reinterpret_cast<std::uintptr_t>(reply_secondary_table.data())};
    foundation.settlement = {true, &global_accessor,
        missing_settlement_input ? nullptr : &GetIdentifierTable, &LookupIdentifier};
    out.snapshot_foundation12004 =
        std::make_shared<const current::SnapshotFoundationBindings>(foundation);
    return out;
  }

  static void *GetEvent(void *manager) {
    auto &memory = *g_memory;
    ++memory.event_calls;
    return manager == memory.data.data() + current::kEventManagerOffset12004
        ? memory.event.data() : nullptr;
  }
  static bool IsPendingForCharacter(void *pending_object, void *character) {
    auto &memory = *g_memory;
    ++memory.pending_calls;
    return pending_object == memory.pending.data() && character == memory.actor;
  }
  static bool ValidateReply(void *opaque) {
    auto &memory = *g_memory;
    ++memory.validation_calls;
    const auto &command = *static_cast<const xar::ck3_12002::EventCommand *>(opaque);
    return command.primary_vtable == reinterpret_cast<std::uintptr_t>(memory.reply_primary_table.data()) &&
        command.secondary_vtable == reinterpret_cast<std::uintptr_t>(memory.reply_secondary_table.data()) &&
        command.instance_id == kPending && command.choice == 0 && command.flags == 0;
  }
  static void *GetGlobals() { return g_memory->globals.data(); }
  static void *GetIdentifierTable() { return g_memory->identifier_table.data(); }
  static std::int32_t *LookupIdentifier(void *table, std::int32_t *output,
      const void *name_view) {
    auto &memory = *g_memory;
    ++memory.settlement_lookup_calls;
    const auto name = Load<const char *>(name_view, 0);
    const auto size = Load<std::int32_t>(name_view, sizeof(void *));
    if (table != memory.identifier_table.data() || name == nullptr || size < 0) return nullptr;
    *output = std::string_view(name, static_cast<std::size_t>(size)) == "xa_settlement_ready" ? 17 : -1;
    return output;
  }
  static std::int32_t UnexpectedUnitState(void *) {
    ++g_memory->unexpected_world_calls;
    return 0;
  }
  static bool UnexpectedContainsParticipant(const void *, std::int32_t) {
    ++g_memory->unexpected_world_calls;
    return false;
  }
  static std::int32_t UnexpectedWarScore(const void *, void *) {
    ++g_memory->unexpected_world_calls;
    return 0;
  }
};

void Write(const std::filesystem::path &path, std::string_view wire) {
  std::ofstream output(path, std::ios::binary);
  output << wire << '\n';
  Check(output.good(), "native fixture wire output failed");
}

void CheckObserved(const game::Snapshot &observed) {
  Check(observed.date_raw == 45000000 && observed.speed == 5 && observed.paused &&
      observed.player_id == 0 && observed.map_ready && observed.has_played_character &&
      observed.played_character_id == kRobert && observed.played_character_alive,
      "actual .4 full Snapshot core differs");
  Check(observed.played_character_gold == game::FixedPointValue{kGold, 100000} &&
      observed.played_character_prestige == game::FixedPointValue{kPrestige, 100000} &&
      observed.played_character_piety == game::FixedPointValue{kPiety, 100000} &&
      observed.played_character_stress_points == 7,
      "actual .4 signed resource balances differ");
  Check(observed.played_character_betrothed_id == kBetrothed &&
      observed.played_character_primary_spouse_id == kSpouse &&
      observed.played_character_spouse_ids == std::vector<std::int32_t>{kSpouse},
      "actual .4 nonempty family differs");
  Check(observed.has_active_event && observed.active_event_instance_id == 77 &&
      observed.active_event_option_count == 2 && observed.has_pending_character_interaction &&
      observed.pending_character_interaction_id == kPending &&
      observed.pending_sender_character_id == kSpouse && !observed.pending_auto_accept_notification,
      "actual .4 event and validated pending interaction differ");
  Check(observed.active_wars.empty() && observed.player_armies.empty() &&
      !observed.has_one_life_settlement, "actual complete empty World/unpublished settlement differs");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "usage: xar_ck3_12004_snapshot_foundation_test <wire-output-dir>");
    const std::filesystem::path output(argv[1]);
    std::filesystem::create_directories(output);
    SnapshotMemory memory;
    auto adapter = game::CreateCk3_12004AdapterFromBindings(memory.Bindings());
    Check(adapter != nullptr && adapter->enabled() && adapter->supports_snapshot() &&
        game::IsCk3_12004Descriptor(adapter->descriptor()), "actual .4 factory unavailable");
    game::Snapshot observed{};
    Check(adapter->read_snapshot(observed), "actual .4 full memory-reader Snapshot unavailable");
    CheckObserved(observed);
    Check(memory.event_calls == 1 && memory.pending_calls == 1 && memory.validation_calls == 1 &&
        memory.settlement_lookup_calls == 1 && memory.unexpected_world_calls == 0,
        "selected callbacks/complete empty registries were not exercised as expected");
    Write(output / "state-snapshot-robert-paused.json",
        xar::bridge::SerializeStateSnapshotFrameV1(observed, 1));

    auto missing = game::CreateCk3_12004AdapterFromBindings(memory.Bindings(true));
    Check(missing != nullptr && missing->enabled(), "missing-input adapter lost independent core");
    game::Snapshot rejected = observed;
    Check(!missing->read_snapshot(rejected) && rejected == game::Snapshot{},
        "missing demanded settlement input published a partial full Snapshot");
    game::Snapshot core_only{};
    Check(game::ReadCk3_12002TimelineCoreSnapshot(*missing, core_only) && core_only.map_ready &&
        core_only.has_played_character && core_only.played_character_id == kRobert,
        "independent selected .4 timeline core failed with missing settlement input");
    current::CoreFrameObservationV1 core{};
    Check(current::ReadCoreSnapshot(memory.core, core.core), "independent .4 core reader failed");
    core.core_available = true;
    // This fixture calls the reader directly, without an application-main pump.
    core.application_main_observed = false;
    core.unavailable_reason = {};
    const auto core_wire = current::SerializeCoreFrameCommandResultV1(
        "snapshot-foundation-missing-settlement", core);
    Check(core_wire.find("\"complete_snapshot\":false") != std::string::npos,
        "standalone core was promoted to complete Snapshot");
    Write(output / "snapshot-foundation-missing-settlement-core.json", core_wire);
    Write(output / "snapshot-foundation-result.json",
        "{\"schema\":\"ck3_12004_snapshot_foundation_fixture_v1\","
        "\"game_version\":\"1.20.0.4\",\"adapter_id\":\"ck3-1.20.0.4-msvc-x64\","
        "\"executable_sha256\":\"" + std::string(current::kExecutableSha256) + "\","
        "\"steam_build_id\":\"25734779\",\"complete_read\":true,"
        "\"missing_settlement_full_read\":false,\"independent_core_available\":true,"
        "\"standalone_core_complete_snapshot\":false,\"native_rva_invocations\":0,"
        "\"scope\":\"offline_owned_memory\"}");
    std::cout << "actual .4 full Snapshot foundation fixture passed; offline owned memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
