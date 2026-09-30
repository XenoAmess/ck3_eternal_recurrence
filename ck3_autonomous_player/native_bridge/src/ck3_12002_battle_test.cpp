#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/ck3_12002_battle_journal.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <iostream>

namespace {
using namespace xar::ck3_12002;
using namespace xar::game;
template <std::size_t N> using Bytes = std::array<std::byte, N>;
template <typename T, std::size_t N>
void Put(Bytes<N> &o, std::size_t offset, T v) {
  std::memcpy(o.data() + offset, &v, sizeof(v));
}
template <typename T> T Get(void *o, std::size_t offset) {
  T v{};
  std::memcpy(&v, static_cast<std::byte *>(o) + offset, sizeof(v));
  return v;
}
struct Store {
  Bytes<0x38> storage{};
  Bytes<0x100> slots{};
  void *root = storage.data();
  Store() {
    Put(storage, 0x20, slots.data());
    Put<std::int32_t>(storage, 0x2C, 16);
  }
  void Set(std::int32_t id, void *p) {
    Put(slots, (id & 0xFFFFFF) * 0x10 + 8, p);
  }
};
struct Fixture {
  Bytes<0xA8> gs{}, js{};
  Bytes<0x158> game_data{};
  std::array<void *, 2587> province_rows{};
  void *g = gs.data(), *j = js.data();
  Bytes<0x720> combat{};
  Bytes<0x860> province{};
  Bytes<0x200> unit0{}, unit1{};
  Bytes<0x148> army0{}, army1{};
  Bytes<0x150> regiment0{}, regiment1{};
  Bytes<0xA20> type0{}, type1{};
  Bytes<0x210> char0{}, char1{};
  Bytes<0x210> land{};
  Bytes<0x48> rules{};
  Bytes<0xD8> result{};
  Bytes<0x60> entry0{}, entry1{};
  Bytes<0x18> hard{};
  Bytes<0x1C0> coordinator{};
  Bytes<0x98> parent{};
  Bytes<0x58> subunit{};
  Store combats, units, armies, regiments, characters, results, coordinators;
  std::array<std::int32_t, 1> aids{0x1000001}, dids{0x1000002},
      combat_ids{0x1000003}, member{0x1000001};
  std::array<void *, 1> parent_rows{parent.data()},
      subunit_rows{subunit.data()}, support{province.data()};
  std::int32_t minimum = 14;
  BattleBindings b{};
  Snapshot scope{};
  static Fixture *current;
  static void *ResolveProvince(void *ctx, std::int32_t id) {
    auto &f = *static_cast<Fixture *>(ctx);
    return id == 2586 ? f.province.data() : nullptr;
  }
  static void *Rules(void *owner) {
    assert(owner == current->char0.data());
    return current->rules.data();
  }
  static std::int32_t Strength(void *) { return 31337; }
  static bool Hostile(void *a, void *d, bool) { return a != d; }
  static bool Retreat(void *c, void *, void *sink) {
    assert(!sink);
    auto &f = *current;
    auto flag = Get<std::uint8_t>(static_cast<std::byte *>(c) + 0x20, 0xC0);
    auto early = Get<std::uint8_t>(static_cast<std::byte *>(c) + 0x20, 0xC1);
    auto days =
        (f.scope.date_raw - Get<std::int32_t>(f.result.data(), 0x2C)) / 24;
    return !flag && (early || days > f.minimum) &&
           Get<std::int32_t>(c, 0x6B0) < 2 &&
           (Get<std::uint32_t>(f.rules.data(), 0x40) & (1 << 10));
  }
  template <std::size_t N>
  static void Array(Bytes<N> &o, std::size_t off, void *data,
                    std::int32_t count) {
    Put(o, off, data);
    Put(o, off + 8, count);
    Put(o, off + 12, count);
  }
  Fixture() {
    current = this;
    scope.paused = true;
    scope.map_ready = true;
    scope.has_played_character = true;
    scope.played_character_id = 0x1000001;
    scope.date_raw = 0x029C55C0 + 15 * 24;
    Put(gs, 8, scope.date_raw);
    Put<std::uint32_t>(js, 0x20, 1);
    Put(gs, 0xA0, game_data.data());
    province_rows[2586] = province.data();
    Put(game_data, 0x140, province_rows.data());
    Put<std::int32_t>(game_data, 0x14C, 2587);
    b.enabled = true;
    b.game_state_slot = &g;
    b.jomini_state_slot = &j;
    b.combat_storage_slot = &combats.root;
    b.army_storage_slot = &units.root;
    b.army_internal_storage_slot = &armies.root;
    b.regiment_storage_slot = &regiments.root;
    b.character_storage_slot = &characters.root;
    b.battle_result_storage_slot = &results.root;
    b.battle_result_fallback_slot = &result_root;
    b.ai_war_coordinator_storage_slot = &coordinators.root;
    b.minimum_days_before_manual_retreat = &minimum;
    b.get_combat_side_strength = Strength;
    b.get_combat_regiment_strength = Strength;
    b.can_order_combat_retreat = Retreat;
    b.get_combat_retreat_rule_state = Rules;
    b.resolve_province = ResolveProvince;
    b.province_context = this;
    b.ai_war_coordinator_vtable = 0xAA11;
    b.ai_unit_stack_vtable = 0xAA22;
    b.ai_subunit_stack_vtable = 0xAA33;
    Put<std::int32_t>(combat, 8, 0x1000003);
    combats.Set(0x1000003, combat.data());
    Put<std::int32_t>(province, 0x10, 2586);
    Put<std::uint32_t>(province, 0x85C, 0x50726F76);
    Put(combat, 0x6B8, province.data());
    Put<std::int32_t>(combat, 0x6B0, 1);
    Put<std::int32_t>(combat, 0x6B4, 4);
    Put<std::int32_t>(combat, 0x6E0, -1);
    Put<std::int32_t>(combat, 0x700, -1);
    Put<std::int32_t>(combat, 0x708, 0x1000004);
    Put<std::int64_t>(combat, 0x6C8, 1LL << 40);
    Put<std::int64_t>(combat, 0x710, (1LL << 40) + 17);
    Put<std::int32_t>(result, 8, 0x1000004);
    Put<std::int32_t>(result, 0x2C, 0x029C55C0);
    results.Set(0x1000004, result.data());
    Put<std::int32_t>(char0, 0x18, 0x1000001);
    Put<std::int32_t>(char1, 0x18, 0x1000002);
    characters.Set(0x1000001, char0.data());
    characters.Set(0x1000002, char1.data());
    Put(char0, 0x1C0, land.data());
    Put<std::int32_t>(land, 0x1F8, -1);
    Put<std::uint32_t>(rules, 0x40, 1 << 10);
    InitArmy(unit0, army0, 0x1000001);
    InitArmy(unit1, army1, 0x1000002);
    Put<std::int32_t>(regiment0, 0x10, 0x1000005);
    Put(regiment0, 0x18, type0.data());
    Put<std::int32_t>(regiment0, 0x140, 0x1000001);
    regiments.Set(0x1000005, regiment0.data());
    Put<std::uint8_t>(type0, 0x98A, 1);
    Put<std::uint8_t>(type0, 0xA0A, 0);
    Put<std::int32_t>(regiment1, 0x10, 0x1000006);
    Put(regiment1, 0x18, type1.data());
    Put<std::int32_t>(regiment1, 0x140, 0x1000002);
    regiments.Set(0x1000006, regiment1.data());
    Put<std::uint8_t>(type1, 0x98A, 0);
    Put<std::uint8_t>(type1, 0xA0A, 1);
    Put<std::int32_t>(entry0, 8, 0x1000005);
    Put<std::int64_t>(entry0, 0x10, 10'000'000);
    Put<std::int64_t>(entry0, 0x18, 8'000'000);
    Put<std::int64_t>(entry0, 0x20, 1'000'000);
    Put<std::int32_t>(entry1, 8, 0x1000006);
    Put<std::int64_t>(entry1, 0x10, 4'000'000);
    Array(combat, 0x30, aids.data(), 1);
    Array(combat, 0x378, dids.data(), 1);
    Array(combat, 0x48, entry0.data(), 1);
    Array(combat, 0x390, entry1.data(), 1);
    Put(combat, 0xD8, combat.data());
    Put(combat, 0x420, combat.data());
    Put<std::int32_t>(combat, 0x90, 0x1000001);
    Put<std::int32_t>(combat, 0x94, -1);
    Put<std::int32_t>(combat, 0x3D8, 0x1000002);
    Put<std::int32_t>(combat, 0x3DC, -1);
    Put<std::int64_t>(combat, 0xB8, 9'000'000);
    Put<std::int64_t>(combat, 0xC0, 9'000'000);
    Array(province, 0x758, combat_ids.data(), 1);
    ArmySnapshot a{};
    a.army_id = 0x1000001;
    a.controllable = true;
    a.in_combat = true;
    scope.player_armies.push_back(a);
    Put<std::uintptr_t>(coordinator, 0, 0xAA11);
    Put<std::int32_t>(coordinator, 0x10, 0x1000007);
    coordinators.Set(0x1000007, coordinator.data());
    Array(coordinator, 0x50, parent_rows.data(), 1);
    Put<std::uintptr_t>(parent, 0, 0xAA22);
    Put(parent, 0x58, coordinator.data());
    Array(parent, 0x40, subunit_rows.data(), 1);
    Array(parent, 8, support.data(), 1);
    Put<std::uintptr_t>(subunit, 0, 0xAA33);
    Array(subunit, 0x10, member.data(), 1);
    Put(subunit, 0x38, parent.data());
    Put(subunit, 0x40, province.data());
    Put<std::uint8_t>(subunit, 0x48, 0x13);
    Put<std::int64_t>(subunit, 0x28, 12300000);
    Put<std::int64_t>(subunit, 0x30, 56700000);
    Put<std::uint8_t>(subunit, 0x54, 1);
    Put<std::int32_t>(unit0, 0x1C4, 0x1000007);
    Put(unit0, 0x1D0, subunit.data());
    Put(unit0, 0x30, province.data());
    b.route_bindings.enabled = true;
    b.route_bindings.game_state_slot = &g;
    b.route_bindings.jomini_state_slot = &j;
    b.route_bindings.army_storage_slot = &units.root;
    b.route_bindings.is_character_hostile = Hostile;
  }
  void *result_root = result.data();
  void InitArmy(Bytes<0x200> &u, Bytes<0x148> &a, std::int32_t id) {
    Put(u, 0x10, id);
    Put(u, 0x174, id);
    Put(u, 0x178, id);
    Put(u, 0x20, province.data());
    Put(a, 0x10, id);
    Put(a, 0x124, id);
    Put<std::int32_t>(a, 0x128, 0x1000003);
    units.Set(id, u.data());
    armies.Set(id, a.data());
  }
};
Fixture *Fixture::current = nullptr;
} // namespace
int main() {
  auto admitted = BindBattleImage(0x140000000, kExecutableSha256);
  assert(admitted.enabled);
  assert(reinterpret_cast<std::uintptr_t>(admitted.combat_storage_slot) ==
         0x145D1DE70ULL);
  assert(!BindBattleImage(0x140000000, "old").enabled);
  Fixture f;
  BattleTransitionSnapshot t{};
  assert(ReadBattleTransitionSnapshot(f.b, f.scope, {0x1000003}, t) ==
         BattleTransitionSnapshotStatus::available);
  assert(t.attacker_public_cunit_ids_in_stored_order ==
         std::vector<std::int32_t>{0x1000001});
  BattleControlSnapshot c{};
  assert(ReadBattleControlSnapshot(f.b, f.scope, {0x1000001}, c) ==
         BattleControlSnapshotStatus::available);
  assert(c.base_advantage_raw == (1LL << 40));
  assert(c.resolved_advantage_raw == (1LL << 40) + 17);
  assert(c.attacker.levy_entries[0].hard_casualties_raw == 1'000'000);
  assert(!c.defender.levy_entries[0].hard_casualties_available);
  assert(c.defender.non_main_start_minus_current_minus_soft_raw == 4'000'000);
  assert(!c.attacker.stored_current_matches_derived);
  assert(c.legality.legal_now);
  Put<std::uint32_t>(f.rules, 0x38, 1 << 10);
  Put<std::uint32_t>(f.rules, 0x40, 0);
  assert(ReadBattleControlSnapshot(f.b, f.scope, {0x1000001}, c) ==
         BattleControlSnapshotStatus::available);
  assert(!c.legality.legal_now);
  assert(c.legality.reason_codes_in_native_order ==
         std::vector<std::string>{"landless"});
  Put<std::uint32_t>(f.rules, 0x40, 1 << 10);
  Put<std::uint8_t>(f.combat, 0x705, 1);
  assert(ReadBattleTransitionSnapshot(f.b, f.scope, {0x1000003}, t) ==
         BattleTransitionSnapshotStatus::state_changed);
  Put<std::uint8_t>(f.combat, 0x705, 0);
  BattleReinforcementAssignmentSnapshot re{};
  assert(ReadBattleReinforcementAssignmentV1(f.b, f.scope, {0x1000001}, re) ==
         BattleReinforcementAssignmentStatus::available);
  assert(re.signal->asking_for_help && re.signal->assigned_to_help);
  assert(re.signal->request_power_basis_raw == 12300000);
  assert(re.signal->cross_coordinator_request_power_raw == 56700000);
  assert(re.assignment->assignment_target_province_id == 2586);
  assert(re.native_order->parent_subunits_in_stored_order[0]
             .public_cunit_ids_in_stored_order ==
         std::vector<std::int32_t>{0x1000001});
  assert(re.route->assignment_eta_date_raw == f.scope.date_raw);
  assert(re.route->route_alignment == "aligned_to_assignment");
  assert(re.contact_projection->status == "available");
  assert(re.contact_projection->contact_if_now_selected_combat_id == 0x1000003);
  assert(InitializeBattleTerminalJournalStorageV1(f.b));
  BattleTerminalTransitionSnapshotV1 terminal{};
  Put<std::uint8_t>(f.combat, 0x704, 1);
  assert(ReadBattleTerminalTransitionV1(f.b, f.scope, {0x1000003, 0x1000001, 0},
                                        terminal) ==
         BattleTerminalTransitionStatusV1::unavailable);
  assert(terminal.unavailable_reason == "terminal_event_not_observed");
  Put<std::uint8_t>(f.combat, 0x704, 0);
  assert(CaptureBattleTerminalJournalEntryV1(f.combat.data(), false));
  f.combats.Set(0x1000003, nullptr);
  Put<std::int32_t>(f.province, 0x764, 0);
  Put<std::int32_t>(f.unit0, 0x170, 1);
  assert(ReadBattleTerminalTransitionV1(f.b, f.scope, {0x1000003, 0x1000001, 0},
                                        terminal) ==
         BattleTerminalTransitionStatusV1::available);
  assert(terminal.prior.terminal_kind == BattleTerminalKindV1::normal_result);
  assert(!terminal.removal.prior_combat_strictly_resolves);
  assert(terminal.successor.state ==
         BattleTerminalSuccessorStateV1::subject_retreating);
  assert(ReadBattleTransitionSnapshot(f.b, f.scope, {0x1000003}, t) ==
         BattleTransitionSnapshotStatus::combat_not_found);
  assert(t.battle_transition_ready);
  f.combats.Set(0x1000003, f.combat.data());
  Put<std::int32_t>(f.combat, 8, 0x2000003);
  assert(ReadBattleTransitionSnapshot(f.b, f.scope, {0x1000003}, t) ==
         BattleTransitionSnapshotStatus::combat_not_found);
  f.scope.paused = false;
  assert(ReadBattleControlSnapshot(f.b, f.scope, {0x1000001}, c) ==
         BattleControlSnapshotStatus::requires_paused);
  std::cout << "CK3 1.20.0.2 battle control, transition, reinforcement and "
               "terminal offline fixtures GREEN\n";
}
