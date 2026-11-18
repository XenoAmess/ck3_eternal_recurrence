#include "xar_bridge/ck3_1210_army_base_v1.hpp"

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
void *local_player = nullptr, **native_registry_slot = nullptr;
void *expected_unit_a = nullptr, *expected_unit_b = nullptr;
std::size_t core_calls = 0, native_calls = 0;
bool wrong_receiver = false;
std::optional<std::int32_t> forced_state;
void *mutate_during_native = nullptr;
std::uint64_t mutation_value = 0;
std::size_t mutation_size = 0;

template <class T> T Load(const void *base, std::size_t offset) {
  T out{}; std::memcpy(&out, static_cast<const std::byte *>(base) + offset, sizeof(T)); return out;
}
void *LocalPlayer(void *) { ++core_calls; return local_player; }
// ABI fixture only. Unlike the old fake model, CArmy identities are real
// bounded RAM records. Its resolver follows the real full-ID/tag/default
// branch; moving/gathering/retreat fields cover known scalar state branches.
std::int32_t FakeNativeState(void *unit) {
  ++native_calls;
  wrong_receiver = wrong_receiver || (unit != expected_unit_a && unit != expected_unit_b);
  void *army = nullptr; const auto reference = Load<std::int32_t>(unit, 0x178);
  if (native_registry_slot != nullptr && *native_registry_slot != nullptr) {
    const auto registry = *native_registry_slot;
    const auto index = static_cast<std::uint32_t>(reference) & 0x00FFFFFFU;
    const auto capacity = Load<std::int32_t>(registry, 0x2C);
    if (capacity > 0 && index < static_cast<std::uint32_t>(capacity)) {
      army = Load<void *>(Load<void *>(registry, 0x20), static_cast<std::size_t>(index) * 0x10 + 8);
      if (army != nullptr && Load<std::int32_t>(army, 0x10) != reference) army = nullptr;
    }
  }
  std::int32_t state = 1;
  if (army != nullptr && Load<std::uint32_t>(army, 0x14) == 0x41726D79U &&
      Load<std::int32_t>(army, 0x10) != -1) {
    if (Load<std::int32_t>(army, 0x1E8) != -1) state = 8;
    else if (Load<std::int32_t>(army, 0x1F8) != -1) state = 9;
    else if (Load<std::int32_t>(army, 0x5C) != 0) state = 5;
    else if (Load<std::int32_t>(unit, 0x170) > 0) state = 6;
    else if (Load<std::int32_t>(unit, 0x44) != 0) state = 7;
  }
  if (forced_state) state = *forced_state;
  if (native_calls == 1 && mutate_during_native != nullptr)
    std::memcpy(mutate_during_native, &mutation_value, mutation_size);
  return state;
}
struct Memory {
  explicit Memory(std::size_t size) : bytes(size) {}
  std::vector<std::byte> bytes;
  void *data() { return bytes.data(); }
  template <class T> void Put(std::size_t offset, T value) {
    if (offset > bytes.size() || sizeof(T) > bytes.size() - offset)
      throw std::string_view("bounded fixture write exceeded RAM");
    std::memcpy(bytes.data() + offset, &value, sizeof(T));
  }
};
struct Fixture {
  static constexpr auto player = std::bit_cast<std::int32_t>(0x81000001U);
  static constexpr std::int32_t peer = 0x02000002;
  static constexpr auto unit_a_id = std::bit_cast<std::int32_t>(0x84000000U);
  static constexpr auto unit_b_id = std::bit_cast<std::int32_t>(0x85000001U);
  static constexpr auto army_a_id = std::bit_cast<std::int32_t>(0x86000000U);
  static constexpr auto army_b_id = std::bit_cast<std::int32_t>(0x87000001U);
  Memory game{0xB0}, jomini{0x28}, players{0x200}, local{0x80}, data{0x3AD00};
  Memory entry{0xE0}, entries{8}, characters{0x40}, character_slots{3 * 0x10};
  Memory actor{0x1E0}, other{0x1E0};
  Memory units{0x58}, unit_slots{2 * 0x10}, unit_a{0x180}, unit_b{0x180};
  Memory armies{0x58}, other_armies{0x58}, army_slots{2 * 0x10};
  Memory army_a{0x208}, army_b{0x208}, clone_army_a{0x208}, no_army{0x208};
  Memory provinces{4 * 8}, province_a{0xB30}, province_b{0xB30}, province_c{0xB30};
  Memory route{2 * 8}, info_a{8}, info_b{8};
  void *game_slot = nullptr, *jomini_slot = nullptr, *character_slot = nullptr;
  void *unit_slot = nullptr, *army_slot = nullptr, *fallback_slot = nullptr;
  ArmyBaseBindingsV1 bindings{};
  std::vector<std::span<const std::byte>> readable;
  const void *deny = nullptr;
  bool guard_valid = true, switch_registry_between_passes = false;
  bool change_unit_owner_before_native = false;
  std::size_t registry_reads = 0, unit_owner_reads = 0;

  Fixture() {
    native_calls = core_calls = 0; wrong_receiver = false; forced_state.reset();
    mutate_during_native = nullptr; mutation_size = 0; mutation_value = 0;
    local_player = local.data(); expected_unit_a = unit_a.data(); expected_unit_b = unit_b.data();
    game_slot = game.data(); jomini_slot = jomini.data(); character_slot = characters.data();
    unit_slot = units.data(); army_slot = armies.data(); fallback_slot = no_army.data();
    native_registry_slot = &army_slot;
    bindings.exact_build_admitted = true;
    auto &b = bindings.player_armies;
    b.exact_build_admitted = true;
    b.core = {true, &game_slot, &jomini_slot, &character_slot, LocalPlayer};
    b.unit_registry_slot = &unit_slot; b.unit_registry_vtable = 0x104EA40C8ULL;
    b.unit_manager_vtable = 0x104EA4090ULL; b.get_unit_state = FakeNativeState;
    bindings.native_army_registry_slot = &army_slot; bindings.no_army_fallback_slot = &fallback_slot;
    bindings.native_army_registry_vtable = 0x104E9DEF0ULL;
    bindings.native_army_manager_vtable = 0x104E9E148ULL;
    bindings.native_army_vtable = 0x104E481A8ULL;
    game.Put(kGameStateDateOffset, std::int32_t{123456});
    game.Put(kGameStateSpeedOffset, std::int32_t{2}); game.Put(kGameStateDataOffset, data.data());
    jomini.Put(kJominiPlayersOffset, players.data()); jomini.Put(kJominiPausedOffset, std::uint8_t{1});
    players.Put(kPlayersLocalPlayerIdOffset, std::int32_t{0}); local.Put(kPlayerIdOffset, std::int32_t{0});
    entry.Put(kPlayerEntryLocalPlayerIdOffset, std::int32_t{0}); entry.Put(kPlayerEntryCharacterIdOffset, player);
    entries.Put(0, entry.data());
    data.Put(kPlayerCharacterManagerOffset + kPlayerManagerEntriesOffset, entries.data());
    data.Put(kPlayerCharacterManagerOffset + kPlayerManagerCountOffset, std::int32_t{1});
    characters.Put(0x20, character_slots.data()); characters.Put(0x2C, std::int32_t{3});
    actor.Put(0x18, player); actor.Put(0x1C, std::uint32_t{0x43686172U});
    other.Put(0x18, peer); other.Put(0x1C, std::uint32_t{0x43686172U});
    character_slots.Put(0x18, actor.data()); character_slots.Put(0x28, other.data());
    data.Put(kPlayerArmyUnitManagerOffsetV1, b.unit_manager_vtable);
    data.Put(kPlayerArmyUnitManagerOffsetV1 + 0x20, units.data());
    units.Put(0, b.unit_registry_vtable);
    data.Put(kArmyBaseManagerOffsetV1, bindings.native_army_manager_vtable);
    data.Put(kArmyBaseManagerOffsetV1 + kArmyBaseManagerRegistryOffsetV1, army_slot);
    for (Memory *store : std::array{&armies, &other_armies}) {
      store->Put(0, bindings.native_army_registry_vtable);
      store->Put(0x20, army_slots.data()); store->Put(0x2C, std::int32_t{2});
    }
    InitUnit(unit_a, unit_a_id, army_a_id); InitUnit(unit_b, unit_b_id, army_b_id);
    InitArmy(army_a, army_a_id, unit_a_id); InitArmy(army_b, army_b_id, unit_b_id);
    InitArmy(clone_army_a, army_a_id, unit_a_id);
    army_slots.Put(8, army_a.data()); army_slots.Put(24, army_b.data());
    InitProvince(province_a, 1); InitProvince(province_b, 2); InitProvince(province_c, 3);
    provinces.Put(8, province_a.data()); provinces.Put(16, province_b.data()); provinces.Put(24, province_c.data());
    data.Put(0x4140, provinces.data()); data.Put(0x414C, std::int32_t{4});
    info_a.Put(0, std::int32_t{2}); info_b.Put(0, std::int32_t{3});
    route.Put(0, info_a.data()); route.Put(8, info_b.data());
    for (Memory *m : std::array{&game,&jomini,&players,&local,&data,&entry,&entries,&characters,
             &character_slots,&actor,&other,&units,&unit_slots,&unit_a,&unit_b,&armies,&other_armies,
             &army_slots,&army_a,&army_b,&clone_army_a,&no_army,&provinces,&province_a,&province_b,
             &province_c,&route,&info_a,&info_b})
      readable.emplace_back(m->bytes.data(), m->bytes.size());
    for (void **slot : std::array{&game_slot,&jomini_slot,&character_slot,&unit_slot,&army_slot,&fallback_slot})
      readable.emplace_back(reinterpret_cast<const std::byte *>(slot), sizeof(void *));
  }
  static void InitUnit(Memory &m, std::int32_t id, std::int32_t reference) {
    m.Put(0x10, id); m.Put(0x14, std::uint32_t{0x556E6974U});
    m.Put(0x174, peer); m.Put(0x178, reference);
  }
  static void InitArmy(Memory &m, std::int32_t id, std::int32_t unit_id) {
    m.Put(0, std::uintptr_t{0x104E481A8ULL}); m.Put(0x10, id);
    m.Put(0x14, std::uint32_t{0x41726D79U}); m.Put(0x124, unit_id);
    m.Put(0x1E8, std::int32_t{-1}); m.Put(0x1F8, std::int32_t{-1});
  }
  static void InitProvince(Memory &m, std::int32_t id) {
    m.Put(0x10, id); m.Put(0xB24, std::uint32_t{0x50726F76U});
  }
  void Owned(bool permit = true) {
    units.Put(0x20, unit_slots.data()); units.Put(0x2C, std::int32_t{2});
    unit_slots.Put(8, unit_a.data()); unit_slots.Put(24, unit_b.data());
    unit_a.Put(0x174, player); unit_a.Put(0x20, province_a.data());
    unit_a.Put(0x38, route.data()); unit_a.Put(0x40, std::int32_t{2}); unit_a.Put(0x44, std::int32_t{2});
    bindings.player_armies.integration_native_calls_permitted = permit;
  }
  void EmptyRoute() {
    unit_a.Put(0x38, static_cast<void *>(nullptr));
    unit_a.Put(0x40, std::int32_t{0}); unit_a.Put(0x44, std::int32_t{0});
  }
  void Mutate(void *address, std::uint64_t value, std::size_t size) {
    mutate_during_native = address; mutation_value = value; mutation_size = size;
  }
  CoreSnapshotPrefix Expected() {
    CoreSnapshotPrefix out{};
    if (!ReadCoreSnapshot(bindings.player_armies.core, out)) throw std::string_view("fixture Core failed");
    core_calls = 0; return out;
  }
  static bool Copy(void *context, const void *source, void *destination, std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    if (source == f.deny) return false;
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    const auto code = reinterpret_cast<std::uintptr_t>(FakeNativeState);
    if (address >= code && address - code < kPlayerArmyStateEntryGuardV1.size() &&
        size <= kPlayerArmyStateEntryGuardV1.size() - (address - code)) {
      std::memcpy(destination, kPlayerArmyStateEntryGuardV1.data() + (address - code), size);
      if (!f.guard_valid && address == code) *static_cast<std::uint8_t *>(destination) ^= 1;
      return true;
    }
    if (source == f.data.bytes.data() + kArmyBaseManagerOffsetV1 + kArmyBaseManagerRegistryOffsetV1 &&
        ++f.registry_reads == 3 && f.switch_registry_between_passes) {
      f.army_slot = f.other_armies.data();
      f.data.Put(kArmyBaseManagerOffsetV1 + kArmyBaseManagerRegistryOffsetV1, f.army_slot);
    }
    if (source == f.unit_a.bytes.data() + 0x174 && ++f.unit_owner_reads == 2 &&
        f.change_unit_owner_before_native) f.unit_a.Put(0x174, peer);
    for (auto range : f.readable) {
      const auto begin = reinterpret_cast<std::uintptr_t>(range.data());
      if (address >= begin && address - begin <= range.size() && size <= range.size() - (address - begin)) {
        std::memcpy(destination, source, size); return true;
      }
    }
    return false;
  }
  bool Read(ArmyBaseObservationV1 &out) { return ReadArmyBaseV1(bindings, Expected(), out, {this, Copy}); }
};
int failures = 0;
void Check(bool value, std::string_view label) {
  if (!value) { ++failures; std::cerr << "FAILED " << label << '\n'; }
}
void NotFull(const ArmyBaseObservationV1 &out) {
  Check(!out.full_snapshot_available && !out.complete_active_wars_qualified,
      "Army base never grants Full/active-war qualification");
}
void Reject(Fixture &f, std::string_view reason, std::size_t calls = 0) {
  ArmyBaseObservationV1 out{}; out.available = out.army_base_qualified = true; out.player_armies.emplace();
  Check(!f.Read(out), reason); Check(out.unavailable_reason == reason, "specific unavailable reason");
  Check(!out.available && !out.same_frame_ready && !out.collection_complete && !out.army_base_qualified &&
      !out.player_armies, "failure drops stale arrays without claiming empty");
  Check(native_calls == calls && out.native_state_calls_attempted == calls, "honest native call accounting");
  NotFull(out);
}
void Binding() {
  const auto no = BindArmyBaseImageV1(0x140000000ULL, "wrong");
  Check(!no.exact_build_admitted && !no.player_armies.exact_build_admitted &&
      no.native_army_registry_slot == nullptr, "exact executable hash required");
  Check(!BindArmyBaseImageV1((std::numeric_limits<std::uintptr_t>::max)(),
      kExecutableSha256).exact_build_admitted, "base address overflow gate");
  const auto yes = BindArmyBaseImageV1(0x140000000ULL, kExecutableSha256);
  Check(yes.exact_build_admitted && !yes.player_armies.integration_native_calls_permitted &&
      reinterpret_cast<std::uintptr_t>(yes.native_army_registry_slot) == 0x146A666F0ULL &&
      reinterpret_cast<std::uintptr_t>(yes.no_army_fallback_slot) == 0x146A66698ULL &&
      yes.native_army_manager_vtable == 0x144E9E148ULL,
      "new typed owner/registry/default addresses with native calls disabled");
}
void PositiveBase() {
  Fixture f; f.Owned(); ArmyBaseObservationV1 out{};
  Check(f.Read(out) && out.available && out.collection_complete && out.army_base_qualified &&
      out.same_frame_ready && out.player_armies && out.player_armies->size() == 1 &&
      out.native_state_calls_attempted == 2 && native_calls == 2 && !wrong_receiver,
      "positive actor-owned CUnit with real full-generation CArmy RAM");
  if (out.player_armies && out.player_armies->size() == 1) {
    const auto &r = out.player_armies->front();
    Check(r.army_id == Fixture::unit_a_id && r.owner_character_id == Fixture::player &&
        r.has_current_province && r.current_province_id == 1 && r.controllable &&
        r.route_read_status == xar::game::ArmyRouteReadStatus::complete_nonempty &&
        r.route_source_count == 2 && r.route_province_ids == std::vector<std::int32_t>{2,3} &&
        r.move_target_observable && r.move_target_province_id == 3 &&
        r.army_state_code == 7 && r.army_state == "moving" && !r.in_combat && !r.retreating &&
        !r.siege_days_left && !r.siege_province_holder_character_id && !r.siege_province_in_player_subrealm,
        "complete native Army base projection, optional siege absent and full signed IDs retained");
  }
  Check(out.unit_slots_scanned == 2 && out.live_unit_rows == 2 && out.frame.local_player_id == 0 &&
      out.frame.played_character_id == Fixture::player, "collection/frame provenance"); NotFull(out);
  Fixture empty; Check(empty.Read(out) && out.player_armies && out.player_armies->empty() &&
      native_calls == 0 && out.unit_slots_scanned == 0, "complete empty Unit registry, no native state call");
  Fixture empty_route; empty_route.Owned(); empty_route.EmptyRoute();
  Check(empty_route.Read(out) && out.player_armies->front().route_read_status == xar::game::ArmyRouteReadStatus::complete_empty &&
      out.player_armies->front().route_source_count == 0 && out.player_armies->front().route_province_ids.empty() &&
      !out.player_armies->front().move_target_observable && out.player_armies->front().move_target_province_id == -1 &&
      out.player_armies->front().army_state_code == 1,
      "known empty route means not observable and null-serialized target");
  Fixture combat; combat.Owned(); forced_state = 2;
  Check(combat.Read(out) && out.player_armies->front().in_combat &&
      out.player_armies->front().army_state == "combat", "typed input plus native ABI combat projection");
  Fixture retreat; retreat.Owned(); retreat.unit_a.Put(0x170, std::int32_t{1});
  Check(retreat.Read(out) && out.player_armies->front().retreating &&
      out.player_armies->front().army_state_code == 6, "independent raw retreat predicate and native state");
  Fixture zero; zero.Owned(); zero.unit_a.Put(0x10, std::int32_t{0});
  zero.unit_a.Put(0x178, std::int32_t{0}); zero.army_a.Put(0x10, std::int32_t{0});
  Check(zero.Read(out) && out.player_armies->front().army_id == 0,
      "zero is a complete CUnit/CArmy ID, not the invalid -1 sentinel");
  Fixture no_province; no_province.Owned(); no_province.unit_a.Put(0x20, static_cast<void *>(nullptr));
  Check(no_province.Read(out) && !out.player_armies->front().has_current_province &&
      out.player_armies->front().current_province_id == -1, "absent current Province retains explicit null projection");
}
void NoArmyDefault() {
  ArmyBaseObservationV1 out{};
  Fixture absent; absent.Owned(); absent.unit_a.Put(0x178, std::int32_t{-1});
  absent.unit_a.Put(0x170, std::int32_t{1});
  Check(absent.Read(out) && out.player_armies->front().army_state_code == 1 &&
      out.player_armies->front().army_state == "regular" && out.player_armies->front().retreating &&
      out.player_armies->front().route_province_ids == std::vector<std::int32_t>{2,3},
      "legal no-CArmy default returns regular before movement/retreat branches");
  Fixture no_registry; no_registry.Owned(); no_registry.unit_a.Put(0x178, std::int32_t{-1});
  no_registry.army_slot = nullptr;
  no_registry.data.Put(kArmyBaseManagerOffsetV1 + kArmyBaseManagerRegistryOffsetV1, static_cast<void *>(nullptr));
  Check(no_registry.Read(out) && out.player_armies->front().army_state_code == 1,
      "native no-CArmy branch also admits matching null registry/owner");
  Fixture wrong_model; wrong_model.Owned(); wrong_model.unit_a.Put(0x178, std::int32_t{-1}); forced_state = 7;
  Reject(wrong_model, "army_base_no_army_state_not_regular", 2);
  Fixture bad_default; bad_default.Owned(); bad_default.unit_a.Put(0x178, std::int32_t{-1});
  bad_default.no_army.Put(0x14, std::uint32_t{0x41726D79U});
  Reject(bad_default, "army_base_no_army_default_unproven");
}
void InvalidInput() {
  { Fixture f; f.Owned(false); Reject(f, "player_armies_native_calls_not_permitted"); }
  { Fixture f; f.Owned(); f.guard_valid = false; Reject(f, "player_armies_native_state_guard_mismatch"); }
  { Fixture f; f.Owned(); f.army_a.Put(0x10, std::bit_cast<std::int32_t>(0x88000000U));
    Reject(f, "army_base_state_army_generation_unresolved"); }
  { Fixture f; f.Owned(); f.army_slots.Put(8, static_cast<void *>(nullptr));
    Reject(f, "army_base_state_army_generation_unresolved"); }
  { Fixture f; f.Owned(); f.unit_a.Put(0x178, std::int32_t{0x02000002});
    Reject(f, "army_base_state_army_generation_unresolved"); }
  { Fixture f; f.Owned(); f.army_a.Put(0x14, std::uint32_t{0});
    Reject(f, "army_base_state_army_generation_unresolved"); }
  { Fixture f; f.Owned(); f.army_a.Put(0, std::uintptr_t{0});
    Reject(f, "army_base_state_army_generation_unresolved"); }
  { Fixture f; f.Owned(); f.data.Put(kArmyBaseManagerOffsetV1, std::uintptr_t{0});
    Reject(f, "army_base_state_registry_owner_mismatch"); }
  { Fixture f; f.Owned(); f.data.Put(kArmyBaseManagerOffsetV1 + kArmyBaseManagerRegistryOffsetV1, f.other_armies.data());
    Reject(f, "army_base_state_registry_owner_mismatch"); }
  { Fixture f; f.Owned(); f.armies.Put(0, std::uintptr_t{1});
    Reject(f, "army_base_state_registry_type_mismatch"); }
  { Fixture f; f.Owned(); f.armies.Put(0x2C, kPlayerArmyStorageLimitV1 + 1);
    Reject(f, "army_base_state_registry_header_invalid"); }
  { Fixture f; f.Owned(); f.armies.Put(0x20, static_cast<void *>(nullptr));
    Reject(f, "army_base_state_registry_header_invalid"); }
  { Fixture f; f.Owned(); f.deny = f.army_a.bytes.data() + 0x10;
    Reject(f, "army_base_state_input_read_failed"); }
  { Fixture f; f.Owned(); f.army_slots.Put(8,
        reinterpret_cast<void *>((std::numeric_limits<std::uintptr_t>::max)() - 3));
    Reject(f, "army_base_state_input_address_invalid"); }
  { Fixture f; f.Owned(); f.change_unit_owner_before_native = true;
    Reject(f, "army_base_state_unit_identity_changed"); }
}
void ChangingInput() {
  { Fixture f; f.Owned(); f.Mutate(f.army_a.bytes.data() + 0x10, 0x88000000U, 4);
    Reject(f, "army_base_state_army_generation_unresolved", 1); }
  { Fixture f; f.Owned(); f.Mutate(f.army_slots.bytes.data() + 8,
        reinterpret_cast<std::uintptr_t>(f.clone_army_a.data()), sizeof(void *));
    Reject(f, "player_armies_native_state_input_changed", 1); }
  { Fixture f; f.Owned(); f.Mutate(f.data.bytes.data() + kArmyBaseManagerOffsetV1 + kArmyBaseManagerRegistryOffsetV1,
        reinterpret_cast<std::uintptr_t>(f.other_armies.data()), sizeof(void *));
    Reject(f, "army_base_state_registry_owner_mismatch", 1); }
  { Fixture f; f.Owned(); f.Mutate(f.unit_a.bytes.data() + 0x178, 0x87000001U, 4);
    Reject(f, "army_base_state_unit_identity_changed", 1); }
  { Fixture f; f.Owned(); f.switch_registry_between_passes = true;
    Reject(f, "player_armies_collection_changed", 2); }
  { Fixture f; f.Owned(); f.Mutate(f.actor.bytes.data() + 0x18, 0x82000001U, 4);
    Reject(f, "army_base_state_core_changed", 1); }
}
} // namespace
int main() {
  try { Binding(); PositiveBase(); NoArmyDefault(); InvalidInput(); ChangingInput(); }
  catch (std::string_view why) { ++failures; std::cerr << why << '\n'; }
  catch (...) { ++failures; std::cerr << "unexpected Army base fixture exception\n"; }
  if (failures == 0) std::cout << "ck3_1210 Army base NoGame fixture passed\n";
  return failures == 0 ? 0 : 1;
}
