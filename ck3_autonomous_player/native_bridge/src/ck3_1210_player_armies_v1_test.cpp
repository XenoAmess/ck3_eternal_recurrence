#include "xar_bridge/ck3_1210_player_armies_v1.hpp"

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
void *local_player = nullptr, *expected_unit_a = nullptr, *expected_unit_b = nullptr;
std::byte *date_address = nullptr, *actor_id_address = nullptr;
std::size_t core_calls = 0, fake_native_calls = 0;
bool change_date = false, change_actor = false, native_state_changes = false;
bool native_receiver_invalid = false;
std::int32_t state_a = 7, state_b = 2;

void *LocalPlayer(void *) {
  ++core_calls;
  if (core_calls == 2 && change_date) {
    const std::int32_t value = 999999;
    std::memcpy(date_address, &value, sizeof value);
  }
  if (core_calls == 2 && change_actor) {
    const std::int32_t value = std::bit_cast<std::int32_t>(0x82000001U);
    std::memcpy(actor_id_address, &value, sizeof value);
  }
  return local_player;
}
// Real C++ ABI: the receiver is the original CUnit pointer in RCX and the
// result is int32. Only fake fixture memory is touched; no game code executes.
std::int32_t FakeNativeState(void *unit) {
  ++fake_native_calls;
  if (unit == expected_unit_a)
    return native_state_changes && fake_native_calls == 2 ? 8 : state_a;
  if (unit == expected_unit_b) return state_b;
  native_receiver_invalid = true;
  return 0;
}

struct Memory {
  explicit Memory(std::size_t size) : bytes(size) {}
  std::vector<std::byte> bytes;
  void *data() { return bytes.data(); }
  template <class T> void Put(std::size_t offset, T value) {
    if (offset > bytes.size() || sizeof(T) > bytes.size() - offset)
      throw std::string_view("fixture write outside bounded memory");
    std::memcpy(bytes.data() + offset, &value, sizeof value);
  }
};

struct Fixture {
  static constexpr auto player = std::bit_cast<std::int32_t>(0x81000001U);
  static constexpr std::int32_t peer = 0x02000002;
  static constexpr auto id_a = std::bit_cast<std::int32_t>(0x84000000U);
  static constexpr auto id_b = std::bit_cast<std::int32_t>(0x85000001U);
  Memory game{0xB0}, jomini{0x28}, players{0x200}, local{0x80};
  Memory data{0x3AD00}, entry{0xE0}, entries{8};
  Memory char_store{0x40}, char_slots{3 * 0x10}, actor{0x1E0}, other{0x1E0};
  Memory unit_store{0x58}, slots{2 * 0x10}, unit_a{0x180}, unit_b{0x180};
  Memory province_array{4 * 8}, province_a{0xB30}, province_b{0xB30}, province_c{0xB30};
  Memory route{2 * 8}, info_a{8}, info_b{8};
  void *game_slot = nullptr, *jomini_slot = nullptr, *char_slot = nullptr, *unit_slot = nullptr;
  PlayerArmiesBindingsV1 bindings{};
  std::vector<std::span<const std::byte>> readable;
  const void *deny = nullptr;
  bool state_guard_valid = true, route_changes = false;
  std::size_t info_b_reads = 0;

  Fixture() {
    core_calls = fake_native_calls = 0;
    change_date = change_actor = native_state_changes = native_receiver_invalid = false;
    state_a = 7; state_b = 2;
    local_player = local.data(); expected_unit_a = unit_a.data(); expected_unit_b = unit_b.data();
    date_address = game.bytes.data() + kGameStateDateOffset;
    actor_id_address = actor.bytes.data() + kCharacterFullIdOffset;
    game_slot = game.data(); jomini_slot = jomini.data();
    char_slot = char_store.data(); unit_slot = unit_store.data();
    bindings.exact_build_admitted = true;
    bindings.core = {true, &game_slot, &jomini_slot, &char_slot, LocalPlayer};
    bindings.unit_registry_slot = &unit_slot;
    bindings.unit_registry_vtable = 0x104EA40C8ULL;
    bindings.unit_manager_vtable = 0x104EA4090ULL;
    bindings.get_unit_state = FakeNativeState;
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
    char_store.Put(0x20, char_slots.data()); char_store.Put(0x2C, std::int32_t{3});
    actor.Put(0x18, player); actor.Put(0x1C, std::uint32_t{0x43686172U});
    other.Put(0x18, peer); other.Put(0x1C, std::uint32_t{0x43686172U});
    char_slots.Put(0x18, actor.data()); char_slots.Put(0x28, other.data());
    data.Put(kPlayerArmyUnitManagerOffsetV1, bindings.unit_manager_vtable);
    data.Put(kPlayerArmyUnitManagerOffsetV1 + 0x20, unit_slot);
    unit_store.Put(0, bindings.unit_registry_vtable);
    InitUnit(unit_a, id_a); InitUnit(unit_b, id_b);
    InitProvince(province_a, 1); InitProvince(province_b, 2); InitProvince(province_c, 3);
    province_array.Put(8, province_a.data()); province_array.Put(16, province_b.data());
    province_array.Put(24, province_c.data());
    data.Put(0x4140, province_array.data()); data.Put(0x414C, std::int32_t{4});
    info_a.Put(0, std::int32_t{2}); info_b.Put(0, std::int32_t{3});
    route.Put(0, info_a.data()); route.Put(8, info_b.data());
    for (Memory *memory : std::array{&game,&jomini,&players,&local,&data,&entry,&entries,
             &char_store,&char_slots,&actor,&other,&unit_store,&slots,&unit_a,&unit_b,
             &province_array,&province_a,&province_b,&province_c,&route,&info_a,&info_b})
      readable.emplace_back(memory->bytes.data(), memory->bytes.size());
    for (void **slot : std::array{&game_slot,&jomini_slot,&char_slot,&unit_slot})
      readable.emplace_back(reinterpret_cast<const std::byte *>(slot), sizeof(void *));
  }
  static void InitProvince(Memory &memory, std::int32_t id) {
    memory.Put(0x10, id); memory.Put(0xB24, std::uint32_t{0x50726F76U});
  }
  static void InitUnit(Memory &memory, std::int32_t id) {
    memory.Put(0x10, id); memory.Put(0x14, std::uint32_t{0x556E6974U});
    memory.Put(0x174, peer); memory.Put(0x178, std::int32_t{-1});
  }
  void Populate() {
    unit_store.Put(0x20, slots.data()); unit_store.Put(0x2C, std::int32_t{2});
    slots.Put(8, unit_a.data()); slots.Put(24, unit_b.data());
  }
  void Owned(bool calls_permitted = true) {
    Populate(); bindings.integration_native_calls_permitted = calls_permitted;
    unit_a.Put(0x174, player); unit_a.Put(0x20, province_a.data());
    unit_a.Put(0x38, route.data()); unit_a.Put(0x40, std::int32_t{2});
    unit_a.Put(0x44, std::int32_t{2});
  }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix expected{};
    if (!ReadCoreSnapshot(bindings.core, expected)) throw std::string_view("fixture Core failed");
    core_calls = 0; return expected;
  }
  static bool Copy(void *context, const void *source, void *destination,
      std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    if (source == f.deny) return false;
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    const auto code = reinterpret_cast<std::uintptr_t>(FakeNativeState);
    if (address >= code && address - code < kPlayerArmyStateEntryGuardV1.size() &&
        size <= kPlayerArmyStateEntryGuardV1.size() - (address - code)) {
      // A bounded fixture code view tests exact entry validation; the callable
      // target remains FakeNativeState. No executable memory is patched.
      std::memcpy(destination, kPlayerArmyStateEntryGuardV1.data() + (address - code), size);
      if (!f.state_guard_valid && address == code)
        *static_cast<std::uint8_t *>(destination) ^= 1;
      return true;
    }
    if (source == f.info_b.data() && ++f.info_b_reads == 2 && f.route_changes)
      f.info_b.Put(0, std::int32_t{2});
    for (auto range : f.readable) {
      const auto begin = reinterpret_cast<std::uintptr_t>(range.data());
      if (address >= begin && address - begin <= range.size() &&
          size <= range.size() - (address - begin)) {
        std::memcpy(destination, source, size); return true;
      }
    }
    return false;
  }
  bool Read(const CoreSnapshotPrefix &expected, PlayerArmiesObservationV1 &out) {
    return ReadPlayerArmiesV1(bindings, expected, out, {this, Copy});
  }
};

int failures = 0;
void Check(bool condition, std::string_view name) {
  if (!condition) { ++failures; std::cerr << "FAILED " << name << '\n'; }
}
void Reject(Fixture &f, std::string_view reason) {
  PlayerArmiesObservationV1 out{};
  out.player_armies.emplace(); out.available = out.collection_complete = true;
  Check(!f.Read(f.Expected(), out), reason);
  Check(out.unavailable_reason == reason, "specific failure reason");
  Check(!out.available && !out.same_frame_ready && !out.collection_complete &&
      !out.player_armies.has_value() && out.partial && !out.full_snapshot_available &&
      !out.complete_army_snapshot_qualified,
      "unavailable never retains old arrays or grants Full qualification");
}
void Binder() {
  const auto rejected = BindPlayerArmiesImageV1(0x140000000ULL, "bad");
  Check(!rejected.exact_build_admitted && !rejected.core.enabled &&
      rejected.unit_registry_slot == nullptr && rejected.get_unit_state == nullptr, "exact SHA rejection");
  Check(!BindPlayerArmiesImageV1((std::numeric_limits<std::uintptr_t>::max)(),
      kExecutableSha256).exact_build_admitted, "bind overflow");
  const auto good = BindPlayerArmiesImageV1(0x140000000ULL, kExecutableSha256);
  Check(good.exact_build_admitted && !good.integration_native_calls_permitted &&
      reinterpret_cast<std::uintptr_t>(good.get_unit_state) == 0x140D39110ULL &&
      reinterpret_cast<std::uintptr_t>(good.unit_registry_slot) == 0x146A667A8ULL,
      "correct new addresses, native calls default disabled");
}
void Success() {
  Fixture empty; PlayerArmiesObservationV1 out{};
  Check(empty.Read(empty.Expected(), out) && out.player_armies && out.player_armies->empty() &&
      out.collection_complete && fake_native_calls == 0, "real empty scan with no native calls");
  Fixture unrelated; unrelated.Populate();
  unrelated.unit_a.Put(0x20, reinterpret_cast<void *>(std::uintptr_t{1}));
  Check(unrelated.Read(unrelated.Expected(), out) && out.player_armies->empty() &&
      out.live_unit_rows == 2 && fake_native_calls == 0,
      "nonowned units counted but tactical graph not traversed");
  Fixture owned; owned.Owned();
  Check(owned.Read(owned.Expected(), out) && out.player_armies && out.player_armies->size() == 1,
      "one actual actor-owned positive row");
  if (out.player_armies && out.player_armies->size() == 1) {
    const auto &row = out.player_armies->front();
    Check(row.army_id == Fixture::id_a && row.owner_character_id == Fixture::player &&
        row.controllable && row.current_province_id == 1 &&
        row.route_province_ids == std::vector<std::int32_t>{2,3} &&
        row.route_source_count == 2 && row.move_target_province_id == 3 &&
        row.route_read_status == PlayerArmyRouteReadStatusV1::complete_nonempty &&
        row.army_state_code == 7 && row.army_state == "moving" && !row.in_combat &&
        !row.retreating && !row.soldiers && !row.siege_days_left,
        "full signed IDs, correct Province4140 map, complete route and explicit unknowns");
  }
  Check(core_calls == 3 && fake_native_calls == 2 && out.native_state_calls_attempted == 2 &&
      !native_receiver_invalid && out.partial && !out.full_snapshot_available &&
      !out.complete_army_snapshot_qualified, "ABI receiver and two fresh state calls without Full credit");
  Fixture two; two.Owned(); two.unit_b.Put(0x174, Fixture::player);
  two.unit_b.Put(0x170, std::int32_t{3});
  Check(two.Read(two.Expected(), out) && out.player_armies->size() == 2 &&
      out.player_armies->at(1).army_id == Fixture::id_b &&
      !out.player_armies->at(1).current_province_id &&
      out.player_armies->at(1).route_source_count == 0 &&
      out.player_armies->at(1).route_province_ids.empty() &&
      !out.player_armies->at(1).move_target_province_id &&
      out.player_armies->at(1).route_read_status == PlayerArmyRouteReadStatusV1::complete_empty &&
      out.player_armies->at(1).in_combat && out.player_armies->at(1).retreating &&
      out.native_state_calls_attempted == 4, "multiple owned rows and genuinely empty route/current absence");
}
void Failures() {
  { Fixture f; f.Owned(false); Reject(f, "player_armies_native_calls_not_permitted");
    Check(fake_native_calls == 0, "permission gate makes zero calls"); }
  { Fixture f; f.Owned(); f.state_guard_valid = false;
    Reject(f, "player_armies_native_state_guard_mismatch"); Check(fake_native_calls == 0, "guard before call"); }
  { Fixture f; f.Owned(); f.bindings.get_unit_state = nullptr; Reject(f, "player_armies_native_state_unavailable"); }
  { Fixture f; f.Owned(); state_a = 0;
    Reject(f, "player_armies_native_state_invalid"); Check(fake_native_calls == 1, "failed native result still counted"); }
  { Fixture f; f.Populate(); f.unit_a.Put(0x14, std::uint32_t{0}); Reject(f, "player_armies_unit_identity_invalid"); }
  { Fixture f; f.Populate(); f.unit_a.Put(0x10, Fixture::id_b); Reject(f, "player_armies_unit_identity_invalid"); }
  { Fixture f; f.Populate(); f.other.Put(0x18, std::int32_t{0x03000002});
    Reject(f, "player_armies_character_generation_unresolved"); }
  { Fixture f; f.unit_store.Put(0x2C, kPlayerArmyStorageLimitV1 + 1);
    Reject(f, "player_armies_storage_header_invalid"); }
  { Fixture f; f.data.Put(kPlayerArmyUnitManagerOffsetV1 + 0x20, f.char_slot);
    Reject(f, "player_armies_registry_owner_mismatch"); }
  { Fixture f; f.unit_store.Put(0, std::uintptr_t{1}); Reject(f, "player_armies_registry_type_mismatch"); }
  { Fixture f; f.Owned(); f.province_a.Put(0xB24, std::uint32_t{0}); Reject(f, "player_armies_province_identity_invalid"); }
  { Fixture f; f.Owned(); f.province_array.Put(8, f.province_b.data()); Reject(f, "player_armies_province_identity_invalid"); }
  { Fixture f; f.Owned(); f.info_a.Put(0, std::int32_t{4}); Reject(f, "player_armies_province_header_or_id_invalid"); }
  { Fixture f; f.Owned(); f.unit_a.Put(0x44, std::int32_t{3}); Reject(f, "player_armies_route_header_invalid"); }
  { Fixture f; f.Owned(); f.unit_a.Put(0x38, static_cast<void *>(nullptr)); Reject(f, "player_armies_route_header_invalid"); }
  { Fixture f; f.Owned(); f.unit_a.Put(0x40, kPlayerArmyRouteLimitV1 + 1);
    f.unit_a.Put(0x44, kPlayerArmyRouteLimitV1 + 1); Reject(f, "player_armies_route_scope_exceeded"); }
  { Fixture f; f.Owned(); f.route.Put(8, static_cast<void *>(nullptr)); Reject(f, "player_armies_route_entry_unresolved"); }
  { Fixture f; f.Owned(); f.deny = f.info_a.data(); Reject(f, "player_armies_read_failed"); }
  { Fixture f; f.Populate();
    f.slots.Put(8, reinterpret_cast<void *>((std::numeric_limits<std::uintptr_t>::max)() - 8));
    Reject(f, "player_armies_address_invalid"); }
}
void Changes() {
  { Fixture f; f.Owned(); f.route_changes = true; Reject(f, "player_armies_collection_changed"); }
  { Fixture f; f.Owned(); native_state_changes = true; Reject(f, "player_armies_collection_changed"); }
  { Fixture f; f.Owned(); auto expected = f.Expected(); change_date = true;
    PlayerArmiesObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "core_frame_changed" && !out.player_armies,
        "actual Core date drift rejects positive rows"); }
  { Fixture f; f.Owned(); auto expected = f.Expected(); change_actor = true;
    PlayerArmiesObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "core_frame_changed", "actor generation drift"); }
  { Fixture f; f.Owned(); auto expected = f.Expected(); expected.clock.paused = false;
    PlayerArmiesObservationV1 out{};
    Check(!f.Read(expected, out) && out.unavailable_reason == "requires_paused" && fake_native_calls == 0,
        "running Core cannot invoke state getter"); }
}
} // namespace

int main() {
  try { Binder(); Success(); Failures(); Changes(); }
  catch (std::string_view reason) { ++failures; std::cerr << reason << '\n'; }
  catch (...) { ++failures; std::cerr << "unexpected fixture exception\n"; }
  if (failures == 0) std::cout << "ck3_1210 player armies NoGame fixture passed\n";
  return failures == 0 ? 0 : 1;
}
