#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/ck3_12002_battle_journal.hpp"

#include <array>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string>
#include "xar_bridge/battle_terminal_transition_v1_mailbox.hpp"
#include <cstring>
#include <iostream>

namespace {
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
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
    Require(owner == current->char0.data(), "fixture owner-taking rules");
    return current->rules.data();
  }
  static std::int32_t Strength(void *) { return 31337; }
  static bool Hostile(void *a, void *d, bool) { return a != d; }
  static bool Retreat(void *c, void *, void *sink) {
    Require(!sink, "fixture retreat null sink");
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

namespace xar::ck3_11906 {
bool ReadSnapshot(const Bindings &, game::Snapshot &) noexcept { return false; }
game::BattleTerminalTransitionStatusV1 ReadBattleTerminalTransitionV1(
    const Bindings &, const game::Snapshot &,
    const game::BattleTerminalTransitionRequestV1 &,
    game::BattleTerminalTransitionSnapshotV1 &output) noexcept {
  return output.status;
}
} // namespace xar::ck3_11906


namespace {
constexpr std::int32_t kCombatId = 0x1000003;
constexpr std::int32_t kForeignSubjectId = 0x1000002;
using SideInputs = BattleTerminalSideLossInputsSnapshotV1;

const std::array<SideInputs, 2> kExpectedSideInputs{{
    {0, 17'000'007, 14'000'001, 1'000'002, 0, 2'000'004},
    {1, 8'000'003, 7'000'001, 500'001, 500'001, 0},
}};

struct NormalValuesFixture {
  Fixture f;
  Bytes<0xC0> attacker_levies{};
  Bytes<0x60> attacker_maa{}, defender_levies{}, defender_maa{};
  NormalValuesFixture() {
    f.scope.player_armies.clear();
    f.scope.date_raw = 53236632;
    Put<std::int32_t>(f.gs, 8, f.scope.date_raw);
    Put<std::int32_t>(f.combat, 0x6B0, 3);
    Put<std::int32_t>(f.combat, 0x6B4, 7);
    Put<std::int32_t>(f.combat, 0x6E0, 1);
    Put<std::int32_t>(f.unit1, 0x1C4, -1);
    // Exact .3 0x2652B50: baseline side+A8, cached current side+98,
    // levy/MAA array +28/+40, stride60, each soft value at entry+20.
    Put<std::int64_t>(f.combat, 0x20+0xA8, 17'000'007);
    Put<std::int64_t>(f.combat, 0x20+0x98, 14'000'001);
    Put<std::int64_t>(f.combat, 0x368+0xA8, 8'000'003);
    Put<std::int64_t>(f.combat, 0x368+0x98, 7'000'001);
    Put<std::int64_t>(attacker_levies, 0x20, 500'001);
    Put<std::int64_t>(attacker_levies, 0x60+0x20, 500'001);
    Put<std::int64_t>(attacker_maa, 0x20, 0);
    Put<std::int64_t>(defender_levies, 0x20, 500'001);
    Put<std::int64_t>(defender_maa, 0x20, 500'001);
    Fixture::Array(f.combat, 0x20+0x28, attacker_levies.data(), 2);
    Fixture::Array(f.combat, 0x20+0x40, attacker_maa.data(), 1);
    Fixture::Array(f.combat, 0x368+0x28, defender_levies.data(), 1);
    Fixture::Array(f.combat, 0x368+0x40, defender_maa.data(), 1);
    Require(InitializeBattleTerminalJournalStorageV1(f.b), "journal initialize");
  }

  void RemoveNativeResultObjectsAfterCapture() {
    f.combats.Set(kCombatId, nullptr);
    f.results.Set(0x1000004, nullptr);
    Put<std::int32_t>(f.province, 0x764, 0);
    Put<std::int32_t>(f.army1, 0x128, -1);
    f.combat.fill(std::byte{});
    f.result.fill(std::byte{});
    attacker_levies.fill(std::byte{});
    attacker_maa.fill(std::byte{});
    defender_levies.fill(std::byte{});
    defender_maa.fill(std::byte{});
    f.scope.date_raw += 24;
    Put<std::int32_t>(f.gs, 8, f.scope.date_raw);
  }
};

void WriteAndVerifyNativeWire(NormalValuesFixture &fixture,
                              const std::string &prefix, bool suppress) {
  auto &f = fixture.f;
  BattleTerminalTransitionSnapshotV1 result{};
  Require(ReadBattleTerminalTransitionV1(
              f.b, f.scope, {kCombatId, kForeignSubjectId, std::nullopt}, result) ==
              BattleTerminalTransitionStatusV1::available,
          "new hook values terminal reader unavailable after C/result removal");
  Require(!result.removal.prior_combat_strictly_resolves &&
              result.removal.result_strictly_resolves == false &&
              result.prior.terminal_date_raw == f.scope.date_raw-24,
          "new numeric query reread removed objects or replaced capture date");
  if (suppress) {
    Require(result.prior.terminal_kind == BattleTerminalKindV1::no_normal_result &&
                !result.prior.side_loss_inputs_in_native_order &&
                !result.prior.hard_loss_inputs,
            "native suppress branch invented normal numeric values");
  } else {
    Require(result.prior.terminal_kind == BattleTerminalKindV1::normal_result &&
                result.prior.side_loss_inputs_in_native_order &&
                *result.prior.side_loss_inputs_in_native_order == kExpectedSideInputs,
            "both side raw Q inputs were truncated or reread after capture");
    Require(result.prior.hard_loss_inputs &&
                result.prior.hard_loss_inputs->losing_side_index == 0 &&
                result.prior.hard_loss_inputs->baseline_raw == 17'000'007 &&
                result.prior.hard_loss_inputs->stored_current_raw == 14'000'001 &&
                result.prior.hard_loss_inputs->levy_soft_raw == 1'000'002 &&
                result.prior.hard_loss_inputs->men_at_arms_soft_raw == 0 &&
                result.prior.hard_loss_inputs->hard_loss_raw == 2'000'004,
            "existing losing-only projection disagrees with captured side zero");
    Require(result.prior.side_loss_inputs_in_native_order->at(1).hard_loss_raw_q100000 == 0 &&
                result.prior.side_loss_inputs_in_native_order->at(0).men_at_arms_soft_raw_q100000 == 0,
            "native legal zero was replaced by absence");
  }
  result.snapshot_revision = 2;
  const auto wire = xar::ck3_11906::SerializeBattleTerminalTransitionV1(result);
  Require(!wire.empty(), "new normal values native serializer returned empty wire");
  std::ofstream output(prefix+(suppress ? "/no-normal-result-null.json" :
                                       "/normal-result-values.json"), std::ios::binary);
  Require(output.good(), "new numeric native wire output unavailable");
  output << wire << '\n';
  Require(output.good(), "new numeric native wire output failed");
}

void CapturedNormalResultValues(const std::string &prefix) {
  NormalValuesFixture fixture;
  // Invoke the real production hook callback. No patched game function or
  // original finalizer runs in this offline fixture; its original is null.
  XarBattleTerminalHook12002V1(fixture.f.combat.data(), false);
  const auto captured = LookupBattleTerminalJournalV1(kCombatId, 0);
  Require(captured.status == BattleTerminalJournalLookupStatusV1::observed &&
              captured.event.capture_failure_flags == 0 &&
              captured.event.side_loss_inputs_observable &&
              captured.event.side_loss_inputs_in_native_order == kExpectedSideInputs,
          "genuine normal hook capture did not freeze exact both-side raw inputs");
  fixture.RemoveNativeResultObjectsAfterCapture();
  WriteAndVerifyNativeWire(fixture, prefix, false);
}

void NativeSuppressNull(const std::string &prefix) {
  NormalValuesFixture fixture;
  XarBattleTerminalHook12002V1(fixture.f.combat.data(), true);
  const auto captured = LookupBattleTerminalJournalV1(kCombatId, 0);
  Require(captured.status == BattleTerminalJournalLookupStatusV1::observed &&
              captured.event.capture_failure_flags == 0 &&
              !captured.event.side_loss_inputs_observable,
          "genuine native suppress branch published normal numeric inputs");
  fixture.RemoveNativeResultObjectsAfterCapture();
  WriteAndVerifyNativeWire(fixture, prefix, true);
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  try {
    CapturedNormalResultValues(argv[1]);
    NativeSuppressNull(argv[1]);
    std::cout << "normal-result-values GREEN (normal raw/zero and native suppress null)\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "normal-result-values RED: " << error.what() << '\n';
    return 1;
  }
}
