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
constexpr std::int32_t kCommanderId = 0x1000008;
struct FinalFixture;
FinalFixture *g_final_fixture = nullptr;
void PrepareNativeCharacterRow(FinalFixture &);
void *AppendNativeCharacterRow(FinalFixture &, void *, void *);

template <typename T>
void PutRaw(void *address, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(address)+offset, &value, sizeof(value));
}

struct FinalFixture {
  Fixture f;
  Bytes<0x400> result{}, character_row{}, source_row{};
  std::array<char, 64> heap_key{};
  Bytes<0x210> commander{};
  Bytes<0x2A0> character_extension{};
  Bytes<0x18> jailer_relation{};
  std::uint32_t terminal_original_calls = 0;
  std::array<std::uint32_t, 2> side_original_calls{};
  std::uint32_t append_original_calls = 0;

  FinalFixture() {
    g_final_fixture = this;
    f.scope.player_armies.clear();
    f.scope.date_raw = 53236632;
    Put<std::int32_t>(f.gs, 8, f.scope.date_raw);
    Put<std::int32_t>(f.combat, 0x6B0, 3);
    Put<std::int32_t>(f.combat, 0x6B4, 7);
    Put<std::int32_t>(f.combat, 0x6E0, 1);
    Put<std::int32_t>(f.unit1, 0x1C4, -1);
    Put<std::int32_t>(f.combat, 0x20+0x74, kCommanderId);
    Put<std::int32_t>(result, 8, 0x1000004);
    f.results.Set(0x1000004, result.data());
    f.result_root = result.data();
    Put<std::int32_t>(result, 0xC4, 0); // fixture original models native cleanup
    Put<std::int64_t>(f.combat, 0x20+0xA8, 12'000'000);
    Put<std::int64_t>(f.combat, 0x20+0x98, 9'000'000);
    Put<std::int64_t>(f.combat, 0x368+0xA8, 8'000'000);
    Put<std::int64_t>(f.combat, 0x368+0x98, 7'000'000);
    // The native final-side copy uses actual integer CRegiment current counts,
    // not the entry cached fighting totals above. Defender is an empty side.
    Put<std::int32_t>(f.regiment0, 0x38, 5);
    Put<std::int32_t>(f.regiment1, 0x38, 0);
    Put<std::int32_t>(f.combat, 0x378+12, 0);
    Put<std::int32_t>(commander, 0x18, kCommanderId);
    f.characters.Set(kCommanderId, commander.data());
    Put(f.char1, 0x1B0, character_extension.data());
    Put<void *>(character_extension, 0x288, nullptr);
    PrepareNativeCharacterRow(*this);
    Require(InitializeBattleTerminalJournalStorageV1(f.b), "journal initialize");
  }

  void RemoveObjectsInsideOriginal() {
    f.combats.Set(kCombatId, nullptr);
    f.results.Set(0x1000004, nullptr);
    Put<std::int32_t>(f.province, 0x764, 0);
    Put<std::int32_t>(f.army1, 0x128, -1);
    result.fill(std::byte{});
    character_row.fill(std::byte{});
    source_row.fill(std::byte{});
    heap_key.fill('\0');
    f.combat.fill(std::byte{});
    Put<std::int32_t>(f.regiment0, 0x38, 77);
  }
};

void __fastcall FixtureSideOriginal(void *output, void *side) {
  auto &context = *g_final_fixture;
  const bool attacker = side == context.f.combat.data()+0x20;
  Require(attacker || side == context.f.combat.data()+0x368,
          "production side hook changed original RDX side argument");
  const auto index = attacker ? 0U : 1U;
  Require(output == context.result.data()+(attacker ? 0xE8 : 0x138),
          "production side hook changed original RCX output argument");
  ++context.side_original_calls[index];
  PutRaw<std::int32_t>(output, 8, Get<std::int32_t>(side, 0x74));
  PutRaw<std::int32_t>(output, 0x0C, Get<std::int32_t>(side, 0x70));
  PutRaw<std::int64_t>(output, 0x10, Get<std::int64_t>(side, 0xA8));
  const auto count = attacker ? Get<std::int32_t>(context.f.regiment0.data(), 0x38) : 0;
  PutRaw<std::int64_t>(output, 0x18, static_cast<std::int64_t>(count)*100000);
  // Void ABI: no invented RAX/returned-pointer condition, including empty side.
}

void *__fastcall FixtureAppendOriginal(void *container, void *source) {
  auto &context = *g_final_fixture;
  ++context.append_original_calls;
  return AppendNativeCharacterRow(context, container, source);
}

void __fastcall FixtureTerminalOriginal(void *combat, bool suppress) {
  auto &context = *g_final_fixture;
  Require(combat == context.f.combat.data() && !suppress,
          "production terminal hook changed original callback arguments");
  ++context.terminal_original_calls;
  XarBattleSideResultHook12002V1(context.result.data()+0xE8,
                              context.f.combat.data()+0x20);
  XarBattleSideResultHook12002V1(context.result.data()+0x138,
                              context.f.combat.data()+0x368);
  void *const appended = XarBattleCharacterResultAppendHook12002V1(
      context.result.data()+0x188, context.source_row.data());
  Require(appended == context.character_row.data()+0x38,
          "production append wrapper did not preserve original returned row");
  context.RemoveObjectsInsideOriginal();
}

// Exact native Result+188 vector: ptr, capacity+8, count+C, row stride38.
// Row MSVC owning string lives at+10, size+20, capacity+28; inline below16.
void PrepareNativeCharacterRow(FinalFixture &context) {
  auto *const early = context.character_row.data();
  PutRaw<std::int32_t>(early, 8, 0x1000001);
  PutRaw<std::int32_t>(early, 0x0C, 0x1000002);
  std::memcpy(early+0x10, "early", 5);
  PutRaw<std::uint64_t>(early, 0x20, 5);
  PutRaw<std::uint64_t>(early, 0x28, 15);
  PutRaw<std::int32_t>(early, 0x30, 0);
  PutRaw<std::uint8_t>(early, 0x34, 1);
  PutRaw<std::uint8_t>(early, 0x35, 0);
  Fixture::Array(context.result, 0x188, context.character_row.data(), 1);
  Put<std::int32_t>(context.result, 0x188+8, 2);

  constexpr char key[] = "fixture_native_candidate";
  std::memcpy(context.heap_key.data(), key, sizeof(key));
  auto *const source = context.source_row.data();
  PutRaw<std::int32_t>(source, 8, kCommanderId);
  PutRaw<std::int32_t>(source, 0x0C, 0x1000002);
  PutRaw(source, 0x10, context.heap_key.data());
  PutRaw<std::uint64_t>(source, 0x20, sizeof(key)-1);
  PutRaw<std::uint64_t>(source, 0x28, 63);
  PutRaw<std::int32_t>(source, 0x30, 1);
  PutRaw<std::uint8_t>(source, 0x34, 1);
  PutRaw<std::uint8_t>(source, 0x35, 1);
}

void *AppendNativeCharacterRow(FinalFixture &context, void *container, void *source) {
  Require(container == context.result.data()+0x188 &&
              source == context.source_row.data(),
          "append wrapper changed exact original RCX/RDX arguments");
  auto *const appended = context.character_row.data()+0x38;
  std::memcpy(appended, source, 0x38);
  PutRaw<std::int32_t>(container, 0x0C, 2);
  return appended;
}


void CheckFinalAndCharacterRows(const BattleTerminalTransitionSnapshotV1 &snapshot,
                                bool actual_jailer) {
  Require(snapshot.prior.terminal_kind == BattleTerminalKindV1::normal_result &&
              !snapshot.removal.prior_combat_strictly_resolves &&
              snapshot.removal.result_strictly_resolves == false,
          "new passive final query requires retained native result");
  Require(snapshot.prior.side_final_results_in_native_order.has_value(),
          "both post-original final side outputs absent");
  const auto &sides = *snapshot.prior.side_final_results_in_native_order;
  Require(sides[0].side_index == 0 && sides[1].side_index == 1 &&
              sides[0].selected_commander_character_id == kCommanderId &&
              sides[1].selected_commander_character_id == -1 &&
              sides[0].baseline_raw_q100000 == 12'000'000 &&
              sides[1].baseline_raw_q100000 == 8'000'000 &&
              sides[0].survivors_raw_q100000 == 500'000 &&
              sides[1].survivors_raw_q100000 == 0,
          "final outputs reread cleared objects, fighting cache or changed backing count");
  Require(snapshot.prior.character_result_rows_in_native_order &&
              snapshot.prior.character_result_rows_in_native_order->size() == 2,
          "pre-existing and late native rows were not preserved once before cleanup");
  const auto &early = snapshot.prior.character_result_rows_in_native_order->at(0);
  Require(early.native_row_index == 0 && early.left_character_id == 0x1000001 &&
              early.right_character_id == 0x1000002 && early.key == "early" &&
              early.type_raw == 0 && early.side0 && !early.target_right,
          "entry SSO row was duplicated, omitted or borrowed through cleanup");
  const auto &row = snapshot.prior.character_result_rows_in_native_order->at(1);
  Require(row.native_row_index == 1 && row.left_character_id == kCommanderId &&
              row.right_character_id == 0x1000002 && row.key == "fixture_native_candidate" &&
              row.type_raw == 1 && row.side0 && row.target_right,
          "late heap-key native candidate row fields changed during cleanup");
  Require(snapshot.prior.character_custody_in_observed_order &&
              snapshot.prior.character_custody_in_observed_order->size() == 3,
          "saved full character IDs were duplicated, inferred or omitted");
  const auto &custody = *snapshot.prior.character_custody_in_observed_order;
  Require(custody[0].character_id == 0x1000001 &&
              custody[1].character_id == 0x1000002 &&
              custody[2].character_id == kCommanderId,
          "actual full character observation order changed");
  Require(custody[0].actual_jailer_character_id == -1 &&
              custody[2].actual_jailer_character_id == -1 &&
              custody[1].actual_jailer_character_id == (actual_jailer ? 0x1000001 : -1),
          "candidate was treated as a prisoner or actual jailer identity not read");
  Require(custody[0].status == BattleTerminalCustodyStatusV1::none &&
              custody[2].status == BattleTerminalCustodyStatusV1::none &&
              custody[1].status == (actual_jailer ? BattleTerminalCustodyStatusV1::observed :
                                                  BattleTerminalCustodyStatusV1::none),
          "known absent and actual current custody status were conflated");
}

void QueryAndWrite(FinalFixture &fixture, const std::string &prefix,
                   bool actual_jailer) {
  BattleTerminalTransitionSnapshotV1 snapshot{};
  Require(ReadBattleTerminalTransitionV1(
              fixture.f.b, fixture.f.scope,
              {kCombatId, kForeignSubjectId, std::nullopt}, snapshot) ==
              BattleTerminalTransitionStatusV1::available,
          "new final/custody production reader unavailable after cleanup");
  CheckFinalAndCharacterRows(snapshot, actual_jailer);
  snapshot.snapshot_revision = 2;
  const auto wire = xar::ck3_11906::SerializeBattleTerminalTransitionV1(snapshot);
  Require(!wire.empty(), "new final/custody native serializer empty");
  std::ofstream output(prefix+(actual_jailer ? "/actual-jailer-frame.json" :
                                            "/no-jailer-frame.json"), std::ios::binary);
  Require(output.good(), "new final/custody native wire unavailable");
  output << wire << '\n';
  Require(output.good(), "new final/custody native wire write failed");
}

void NewPassiveFinalAndActualCustody(const std::string &prefix) {
  FinalFixture fixture;
  InitializeBattleTerminalJournalFixtureOriginalsV1(
      &FixtureTerminalOriginal, &FixtureSideOriginal, &FixtureAppendOriginal);
  XarBattleTerminalHook12002V1(fixture.f.combat.data(), false);
  Require(fixture.terminal_original_calls == 1 &&
              fixture.side_original_calls == std::array<std::uint32_t, 2>{1, 1} &&
              fixture.append_original_calls == 1,
          "passive wrappers did not invoke each original exactly once");
  const auto journal = LookupBattleTerminalJournalV1(kCombatId, 0);
  Require(journal.status == BattleTerminalJournalLookupStatusV1::observed &&
              journal.event.capture_failure_flags == 0,
          "new passive capture genuine journal unavailable");
  fixture.f.scope.date_raw += 24;
  Put<std::int32_t>(fixture.f.gs, 8, fixture.f.scope.date_raw);
  QueryAndWrite(fixture, prefix, false);
  Put<std::int32_t>(fixture.jailer_relation, 0, 0x1000001);
  Put(fixture.character_extension, 0x288, fixture.jailer_relation.data());
  fixture.f.scope.date_raw += 24;
  Put<std::int32_t>(fixture.f.gs, 8, fixture.f.scope.date_raw);
  QueryAndWrite(fixture, prefix, true);
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  try {
    NewPassiveFinalAndActualCustody(argv[1]);
    std::cout << "final-survivor-character GREEN (post-original outputs, cleanup and custody frames)\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "final-survivor-character RED: " << error.what() << '\n';
    return 1;
  }
}
