#include "xar_bridge/ck3_1210_military_empty_v1.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <iostream>
#include <limits>
#include <span>
#include <string_view>
#include <vector>

namespace {
using namespace xar::ck3_1210;
std::size_t core_calls = 0, change_core_on_call = 0;
void *local_player = nullptr;
std::byte *date_address = nullptr;

void *LocalPlayer(void *) {
  ++core_calls;
  if (change_core_on_call != 0 && core_calls == change_core_on_call) {
    std::int32_t date = 0;
    std::memcpy(&date, date_address, sizeof date);
    ++date;
    std::memcpy(date_address, &date, sizeof date);
  }
  return local_player;
}

struct Memory {
  explicit Memory(std::size_t size) : bytes(size) {}
  std::vector<std::byte> bytes;
  void *data() { return bytes.data(); }
  template <class T> void Put(std::size_t offset, T value) {
    if (offset > bytes.size() || sizeof(T) > bytes.size() - offset)
      throw std::string_view("fixture write outside bounded object");
    std::memcpy(bytes.data() + offset, &value, sizeof value);
  }
};

struct Fixture {
  static constexpr std::int32_t player = std::bit_cast<std::int32_t>(0x81000001U);
  static constexpr std::int32_t peer_a = 0x02000002;
  static constexpr std::int32_t peer_b = 0x03000003;
  static constexpr std::int32_t unit_id = std::bit_cast<std::int32_t>(0x84000000U);
  static constexpr std::int32_t war_id = std::bit_cast<std::int32_t>(0x83000000U);
  Memory game{0xB0}, jomini{0x28}, players{0x200}, local{0x80};
  Memory data{0x3F400}, entry{0xE0}, entries{8};
  Memory char_store{0x40}, char_slots{4 * 0x10};
  Memory actor{0x1E0}, other_a{0x1E0}, other_b{0x1E0};
  Memory unit_store{0x58}, unit_slots{0x10}, unit{0x180};
  Memory war_store{0x58}, war_slots{0x10}, war{0x370};
  Memory attack_records{8}, defend_records{8}, attack{0x10}, defend{0x10};
  void *game_slot = nullptr, *jomini_slot = nullptr, *char_slot = nullptr;
  void *unit_slot = nullptr, *war_slot = nullptr;
  MilitaryEmptyBindingsV1 bindings{};
  std::vector<std::span<const std::byte>> readable;
  const void *deny = nullptr;
  std::size_t owner_reads = 0;
  bool change_owner_second_read = false;

  Fixture() {
    core_calls = change_core_on_call = 0;
    local_player = local.data();
    date_address = game.bytes.data() + kGameStateDateOffset;
    game_slot = game.data(); jomini_slot = jomini.data();
    char_slot = char_store.data(); unit_slot = unit_store.data(); war_slot = war_store.data();
    bindings.exact_build_admitted = true;
    bindings.core = {true, &game_slot, &jomini_slot, &char_slot, LocalPlayer};
    bindings.unit_registry_slot = &unit_slot; bindings.war_registry_slot = &war_slot;
    bindings.unit_registry_vtable = 0x104EA40C8ULL;
    bindings.war_registry_vtable = 0x104E9C188ULL;
    bindings.unit_manager_vtable = 0x104EA4090ULL;
    bindings.war_manager_vtable = 0x104E9C2C0ULL;
    game.Put(kGameStateDateOffset, std::int32_t{123456});
    game.Put(kGameStateSpeedOffset, std::int32_t{2});
    game.Put(kGameStateDataOffset, data.data());
    jomini.Put(kJominiPlayersOffset, players.data());
    jomini.Put(kJominiPausedOffset, std::uint8_t{1});
    players.Put(kPlayersLocalPlayerIdOffset, std::int32_t{0});
    local.Put(kPlayerIdOffset, std::int32_t{0});
    entry.Put(kPlayerEntryLocalPlayerIdOffset, std::int32_t{0});
    entry.Put(kPlayerEntryCharacterIdOffset, player);
    entries.Put(0, entry.data());
    data.Put(kPlayerCharacterManagerOffset + kPlayerManagerEntriesOffset, entries.data());
    data.Put(kPlayerCharacterManagerOffset + kPlayerManagerCountOffset, std::int32_t{1});
    char_store.Put(0x20, char_slots.data()); char_store.Put(0x2C, std::int32_t{4});
    InitCharacter(actor, player); InitCharacter(other_a, peer_a); InitCharacter(other_b, peer_b);
    char_slots.Put(0x18, actor.data()); char_slots.Put(0x28, other_a.data());
    char_slots.Put(0x38, other_b.data());
    data.Put(kMilitaryUnitManagerOffsetV1, bindings.unit_manager_vtable);
    data.Put(kMilitaryUnitManagerOffsetV1 + 0x20, unit_slot);
    data.Put(kMilitaryWarManagerOffsetV1, bindings.war_manager_vtable);
    data.Put(kMilitaryWarManagerOffsetV1 + 0x20, war_slot);
    unit_store.Put(0, bindings.unit_registry_vtable);
    war_store.Put(0, bindings.war_registry_vtable);
    // Initially capacity0 with null slot pointers: actual valid empty headers.
    unit.Put(0x10, unit_id); unit.Put(0x14, std::uint32_t{0x556E6974U});
    unit.Put(0x174, peer_a);
    war.Put(8, war_id); war.Put(0xC, std::uint32_t{0x5761725FU});
    attack.Put(8, peer_a); defend.Put(8, peer_b);
    attack_records.Put(0, attack.data()); defend_records.Put(0, defend.data());
    SetSide(0x20, attack_records); SetSide(0x80, defend_records);
    for (Memory *object : std::array{&game, &jomini, &players, &local, &data,
             &entry, &entries, &char_store, &char_slots, &actor, &other_a, &other_b,
             &unit_store, &unit_slots, &unit, &war_store, &war_slots, &war,
             &attack_records, &defend_records, &attack, &defend})
      readable.emplace_back(object->bytes.data(), object->bytes.size());
    for (void **slot : std::array{&game_slot, &jomini_slot, &char_slot, &unit_slot, &war_slot})
      readable.emplace_back(reinterpret_cast<const std::byte *>(slot), sizeof(void *));
  }

  static void InitCharacter(Memory &memory, std::int32_t id) {
    memory.Put(0x18, id); memory.Put(0x1C, std::uint32_t{0x43686172U});
  }
  void SetSide(std::size_t offset, Memory &records) {
    war.Put(offset + 8, records.data());
    war.Put(offset + 0x10, std::int32_t{1});
    war.Put(offset + 0x14, std::int32_t{1});
  }
  void PopulateUnrelated() {
    unit_store.Put(0x20, unit_slots.data()); unit_store.Put(0x2C, std::int32_t{1});
    unit_slots.Put(8, unit.data());
    war_store.Put(0x20, war_slots.data()); war_store.Put(0x2C, std::int32_t{1});
    war_slots.Put(8, war.data());
  }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix result{};
    if (!ReadCoreSnapshot(bindings.core, result)) throw std::string_view("fixture Core read failed");
    core_calls = 0;
    return result;
  }
  static bool Copy(void *context, const void *source, void *destination,
      std::size_t size) noexcept {
    auto &fixture = *static_cast<Fixture *>(context);
    if (source == fixture.deny) return false;
    if (source == fixture.unit.bytes.data() + 0x174 && ++fixture.owner_reads == 2 &&
        fixture.change_owner_second_read)
      fixture.unit.Put(0x174, peer_b);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    for (auto range : fixture.readable) {
      const auto begin = reinterpret_cast<std::uintptr_t>(range.data());
      if (address >= begin && address - begin <= range.size() &&
          size <= range.size() - (address - begin)) {
        std::memcpy(destination, source, size);
        return true;
      }
    }
    return false;
  }
  bool Read(const CoreSnapshotPrefix &expected, MilitaryEmptyObservationV1 &out) {
    return ReadMilitaryEmptyV1(bindings, expected, out, {this, Copy});
  }
};

int failures = 0;
void Check(bool condition, std::string_view name) {
  if (!condition) { ++failures; std::cerr << "FAILED " << name << '\n'; }
}
void Unavailable(Fixture &fixture, std::string_view reason) {
  auto expected = fixture.Expected();
  MilitaryEmptyObservationV1 out{};
  out.available = out.same_frame_ready = out.player_armies_empty_proven =
      out.active_wars_empty_proven = true;
  Check(!fixture.Read(expected, out), reason);
  Check(out.unavailable_reason == reason, "specific unavailable reason");
  Check(!out.available && !out.same_frame_ready && !out.player_armies_empty_proven &&
      !out.active_wars_empty_proven && out.partial && !out.full_snapshot_available,
      "failed read cannot retain stale success or grant Full Snapshot");
}

void Binder() {
  const auto rejected = BindMilitaryEmptyImageV1(0x140000000ULL, "bad");
  Check(!rejected.exact_build_admitted && rejected.unit_registry_slot == nullptr &&
      rejected.war_registry_slot == nullptr && !rejected.core.enabled, "exact hash gate");
  Check(!BindMilitaryEmptyImageV1((std::numeric_limits<std::uintptr_t>::max)(),
      kExecutableSha256).exact_build_admitted, "binder overflow");
  const auto accepted = BindMilitaryEmptyImageV1(0x140000000ULL, kExecutableSha256);
  Check(accepted.exact_build_admitted &&
      reinterpret_cast<std::uintptr_t>(accepted.unit_registry_slot) == 0x146A667A8ULL &&
      reinterpret_cast<std::uintptr_t>(accepted.war_registry_slot) == 0x146A666D0ULL,
      "new exact registry addresses");
}

void Success() {
  Fixture empty;
  MilitaryEmptyObservationV1 out{};
  Check(empty.Read(empty.Expected(), out) && out.available && out.same_frame_ready &&
      out.player_armies_empty_proven && out.active_wars_empty_proven &&
      out.unit_slots_scanned == 0 && out.war_slots_scanned == 0 &&
      out.partial && !out.full_snapshot_available, "real zero-capacity collections");
  Fixture populated; populated.PopulateUnrelated();
  Check(populated.Read(populated.Expected(), out) && out.live_unit_rows == 1 &&
      out.active_war_rows == 1 && out.participant_records == 2 && core_calls == 3 &&
      out.frame.played_character_id == Fixture::player,
      "complete nonempty registries, unrelated entities, signed generation-bearing IDs");
  Fixture ended; ended.PopulateUnrelated();
  ended.war.Put(0x360, std::uint8_t{1});
  ended.war.Put(0x28, static_cast<void *>(nullptr));
  Check(ended.Read(ended.Expected(), out) && out.active_war_rows == 0 &&
      out.participant_records == 0, "ended byte bypasses unused participant graph");
}

void Rejects() {
  { Fixture f; f.PopulateUnrelated(); f.unit.Put(0x174, Fixture::player);
    Unavailable(f, "player_armies_nonempty"); }
  { Fixture f; f.PopulateUnrelated(); f.attack.Put(8, Fixture::player);
    Unavailable(f, "active_wars_nonempty_rich_observation_unavailable"); }
  { Fixture f; f.PopulateUnrelated(); f.attack.Put(8, Fixture::player);
    f.defend.Put(8, Fixture::player); Unavailable(f, "military_player_on_both_sides"); }
  { Fixture f; f.unit_store.Put(0x2C, kMilitaryEmptyStorageLimitV1 + 1);
    Unavailable(f, "military_storage_header_invalid"); }
  { Fixture f; f.unit_store.Put(0x2C, std::int32_t{1});
    Unavailable(f, "military_storage_header_invalid"); }
  { Fixture f; f.data.Put(kMilitaryUnitManagerOffsetV1 + 0x20, f.war_slot);
    Unavailable(f, "military_registry_owner_mismatch"); }
  { Fixture f; f.unit_store.Put(0, std::uintptr_t{1});
    Unavailable(f, "military_registry_type_mismatch"); }
  { Fixture f; f.unit_slot = nullptr; Unavailable(f, "military_registry_owner_mismatch"); }
  { Fixture f; f.PopulateUnrelated(); f.unit.Put(0x10, std::int32_t{1});
    Unavailable(f, "military_unit_identity_invalid"); }
  { Fixture f; f.PopulateUnrelated(); f.other_a.Put(0x18, std::int32_t{0x04000002});
    Unavailable(f, "military_character_generation_unresolved"); }
  { Fixture f; f.PopulateUnrelated(); f.war.Put(8, std::int32_t{1});
    Unavailable(f, "military_war_identity_invalid"); }
  { Fixture f; f.PopulateUnrelated(); f.war.Put(0x360, std::uint8_t{2});
    Unavailable(f, "military_war_identity_invalid"); }
  { Fixture f; f.PopulateUnrelated(); f.war.Put(0x34, std::int32_t{2});
    Unavailable(f, "military_participant_header_invalid"); }
  { Fixture f; f.PopulateUnrelated(); f.attack_records.Put(0, static_cast<void *>(nullptr));
    Unavailable(f, "military_participant_record_invalid"); }
  { Fixture f; f.PopulateUnrelated(); f.deny = f.unit.bytes.data() + 0x174;
    Unavailable(f, "military_read_failed"); }
  { Fixture f; f.PopulateUnrelated();
    f.unit_slots.Put(8, reinterpret_cast<void *>((std::numeric_limits<std::uintptr_t>::max)() - 8));
    Unavailable(f, "military_address_invalid"); }
}

void ChangesAndFrames() {
  { Fixture f; f.PopulateUnrelated(); f.change_owner_second_read = true;
    Unavailable(f, "military_collections_changed"); }
  { Fixture f; f.PopulateUnrelated(); auto expected = f.Expected();
    MilitaryEmptyObservationV1 out{}; change_core_on_call = 2;
    Check(!f.Read(expected, out) && out.unavailable_reason == "core_frame_changed",
        "Core date changes between complete passes"); }
  { Fixture f; auto expected = f.Expected(); expected.played_character_id = Fixture::peer_a;
    MilitaryEmptyObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "core_frame_changed",
        "expected actor must match actual Core, not supplied owner label"); }
  { Fixture f; auto expected = f.Expected(); expected.clock.paused = false;
    MilitaryEmptyObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "requires_paused" && core_calls == 0,
        "running frame never scans registries"); }
  { Fixture f; auto expected = f.Expected(); f.actor.Put(0x1C, std::uint32_t{0});
    MilitaryEmptyObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "military_character_generation_unresolved",
        "Core presence alone does not admit malformed actual actor header"); }
}
} // namespace

int main() {
  try { Binder(); Success(); Rejects(); ChangesAndFrames(); }
  catch (std::string_view reason) { ++failures; std::cerr << reason << '\n'; }
  catch (...) { ++failures; std::cerr << "unexpected fixture exception\n"; }
  if (failures == 0) std::cout << "ck3_1210 military empty NoGame fixture passed\n";
  return failures == 0 ? 0 : 1;
}
