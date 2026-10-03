#include "xar_bridge/ck3_12002_battle.hpp"
#include "xar_bridge/ck3_12002_battle_journal.hpp"

#include <array>
#include <cstdlib>
#include <fstream>
#include <stdexcept>
#include <string>
#include "xar_bridge/battle_transition_v1_mailbox.hpp"
#include "xar_bridge/ck3_12003_battle_current_state.hpp"
#include <charconv>
#include <vector>
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
  std::vector<std::byte> slots;
  void *root = storage.data();
  Store() : slots(16 * 16) { Refresh(); }
  void Refresh() {
    Put(storage, 0x20, slots.data());
    Put<std::int32_t>(storage, 0x2C, static_cast<std::int32_t>(slots.size() / 16));
  }
  void Set(std::int32_t id, void *p) {
    const auto off = (static_cast<std::uint32_t>(id) & 0xFFFFFFU) * 16ULL + 8;
    if (slots.size() < off + 8) slots.resize(off + 8);
    std::memcpy(slots.data() + off, &p, sizeof(p));
    Refresh();
  }
};
struct Fixture {
  Bytes<0xA8> gs{}, js{};
  Bytes<0x158> game_data{};
  std::array<void *, 2641> province_rows{};
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
    return id == 2640 ? f.province.data() : nullptr;
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
    province_rows[2640] = province.data();
    Put(game_data, 0x140, province_rows.data());
    Put<std::int32_t>(game_data, 0x14C, 2641);
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
    Put<std::int32_t>(province, 0x10, 2640);
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
game::BattleTransitionSnapshotStatus ReadBattleTransitionSnapshot(
    const Bindings &, const game::BattleTransitionRequest &,
    game::BattleTransitionSnapshot &output) noexcept { return output.status; }
} // namespace xar::ck3_11906

namespace {
std::string Number(std::uint64_t value) {
  std::array<char, 32> buffer{};
  const auto result =
      std::to_chars(buffer.data(), buffer.data() + buffer.size(), value);
  if (result.ec != std::errc{}) {
    return "0";
  }
  return std::string(buffer.data(), result.ptr);
}


void AppendJsonString(std::string &result, std::string_view value) {
  constexpr char hex[] = "0123456789ABCDEF";
  result += '"';
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      result += '\\';
      result += static_cast<char>(character);
    } else if (character < 0x20U) {
      result += "\\u00";
      result += hex[(character >> 4U) & 0x0FU];
      result += hex[character & 0x0FU];
    } else {
      result += static_cast<char>(character);
    }
  }
  result += '"';
}


std::string BattleTransitionResultFrame(
    std::string_view request_id, std::string_view step,
    std::uint64_t query_sequence,
    const xar::game::BattleTransitionSnapshot &snapshot) {
  const auto payload =
      xar::ck3_11906::SerializeBattleTransitionV1(snapshot);
  const auto status =
      xar::ck3_11906::BattleTransitionStatusNameV1(snapshot.status);
  if (payload.empty() || status.empty()) {
    return {};
  }
  std::string result =
      "{\"type\":\"command_result\",\"protocol_version\":1,"
      "\"request_id\":";
  AppendJsonString(result, request_id);
  result += ",\"ok\":true,\"result\":{\"step\":";
  AppendJsonString(result, step);
  result += ",\"accepted\":true,\"status\":";
  AppendJsonString(result, status);
  result += ",\"query_sequence\":";
  result += Number(query_sequence);
  result += ",\"snapshot_revision\":";
  result += Number(snapshot.snapshot_revision);
  result += ",\"battle_transition_snapshot\":";
  result += payload;
  result += "}}";
  return result;
}


constexpr std::int32_t kActualCombat = 1577058305;
constexpr std::int32_t kRebelOwner = 70766;
constexpr std::int32_t kDefenderOwner0 = 30097;
constexpr std::int32_t kDefenderOwner1 = 35357;
constexpr std::int32_t kRegiment0 = 0x1000005;
constexpr std::int32_t kRegiment1 = 0x1000006;
constexpr std::int32_t kRegiment2 = 0x1000008;
constexpr std::int32_t kRegiment3 = 0x1000009;

// The five CUnit/CArmy/owner pairs and CombatID reuse the retained foreign
// combat identity shape. Byte-backed troop values below are synthetic fixture
// inputs, never current gameplay strength or live evidence.
struct ForeignFixture : Fixture {
  std::array<Bytes<0x200>, 3> extra_units{};
  std::array<Bytes<0x148>, 3> extra_armies{};
  Bytes<0x210> extra_character{};
  std::array<Bytes<0x150>, 2> extra_regiments{};
  std::array<Bytes<0x60>, 2> extra_entries{};
  Bytes<0x18> attacker_hard{};
  std::array<Bytes<0x18>, 2> defender_hard{};
  std::array<std::int32_t, 3> actual_attackers{167772260, 461, 462};
  std::array<std::int32_t, 2> actual_defenders{33554713, 150995083};
  std::array<std::int32_t, 1> actual_combat_ids{kActualCombat};

  template <std::size_t N, std::size_t M>
  void Pair(Bytes<N> &u, Bytes<M> &a, std::int32_t public_id,
            std::int32_t internal_id, std::int32_t owner_id) {
    Put(u, 0x10, public_id);
    Put(u, 0x174, owner_id);
    Put(u, 0x178, internal_id);
    Put(a, 0x10, internal_id);
    Put(a, 0x124, public_id);
    Put(a, 0x128, kActualCombat);
    units.Set(public_id, u.data());
    armies.Set(internal_id, a.data());
  }
  void Entry(Bytes<0x60> &entry, Bytes<0x150> &regiment,
             std::int32_t regiment_id, std::int32_t army_id, void *type,
             std::int64_t start, std::int64_t fighting_value, std::int64_t soft) {
    Put(regiment, 0x10, regiment_id);
    Put(regiment, 0x18, type);
    Put(regiment, 0x140, army_id);
    regiments.Set(regiment_id, regiment.data());
    Put(entry, 8, regiment_id);
    Put(entry, 0x10, start);
    Put(entry, 0x18, fighting_value);
    Put(entry, 0x20, soft);
  }
  ForeignFixture() {
    scope.played_character_id = 29829;
    scope.player_armies.clear();
    scope.date_raw = 53236632;
    Put<std::int32_t>(gs, 8, static_cast<std::int32_t>(scope.date_raw));
    Put(combat, 8, kActualCombat);
    combats.Set(kActualCombat, combat.data());
    Put<std::int32_t>(combat, 0x6B0, 1);
    Put<std::int32_t>(combat, 0x6B4, 3);
    Put<std::int32_t>(combat, 0x6C0, 2412);
    Put<std::int32_t>(combat, 0x6C4, 1206);
    Put<std::int64_t>(combat, 0x6C8, -1'100'000);
    Put<std::int64_t>(combat, 0x710, -1'300'000);
    Put<std::int32_t>(char0, 0x18, kRebelOwner);
    Put<std::int32_t>(char1, 0x18, kDefenderOwner0);
    Put<std::int32_t>(extra_character, 0x18, kDefenderOwner1);
    characters.Set(kRebelOwner, char0.data());
    characters.Set(kDefenderOwner0, char1.data());
    characters.Set(kDefenderOwner1, extra_character.data());
    Pair(unit0, army0, 251658381, 167772260, kRebelOwner);
    Pair(extra_units[0], extra_armies[0], 473, 461, kRebelOwner);
    Pair(extra_units[1], extra_armies[1], 474, 462, kRebelOwner);
    Pair(unit1, army1, 50331920, 33554713, kDefenderOwner0);
    Pair(extra_units[2], extra_armies[2], 83886484, 150995083, kDefenderOwner1);
    Array(combat, 0x30, actual_attackers.data(), 3);
    Array(combat, 0x378, actual_defenders.data(), 2);
    Array(province, 0x758, actual_combat_ids.data(), 1);
    Entry(entry0, regiment0, kRegiment0, 167772260, type0.data(),
          10'000'000, 7'000'000, 2'000'000);
    Entry(extra_entries[0], extra_regiments[0], kRegiment2, 462, type1.data(),
          5'000'000, 2'000'000, 1'000'000);
    Entry(entry1, regiment1, kRegiment1, 33554713, type0.data(),
          8'000'000, 6'000'000, 1'000'000);
    Entry(extra_entries[1], extra_regiments[1], kRegiment3, 150995083, type1.data(),
          3'000'000, 1'000'000, 1'000'000);
    Array(combat, 0x48, entry0.data(), 1); // attacker levy
    Array(combat, 0x60, extra_entries[0].data(), 1); // attacker MAA
    Array(combat, 0x390, entry1.data(), 1); // defender levy
    Array(combat, 0x3A8, extra_entries[1].data(), 1); // defender MAA
    Put(attacker_hard, 8, kRebelOwner);
    Put<std::int64_t>(attacker_hard, 0x10, 7'000'000);
    Put(defender_hard[0], 8, kDefenderOwner0);
    Put<std::int64_t>(defender_hard[0], 0x10, 5'000'000);
    Put(defender_hard[1], 8, kDefenderOwner1);
    Put<std::int64_t>(defender_hard[1], 0x10, 6'000'000);
    Array(combat, 0x78, attacker_hard.data(), 1);
    Array(combat, 0x3C0, defender_hard.data(), 2);
    // Native tick-start caches legally differ from the current entry sums.
    Put<std::int64_t>(combat, 0xB8, 111'000'000);
    Put<std::int64_t>(combat, 0xC0, 222'000'000);
    Put<std::int64_t>(combat, 0x400, 333'000'000);
    Put<std::int64_t>(combat, 0x408, 444'000'000);
  }
};

void WriteWire(const std::string &prefix, const std::string &name,
               const std::string &wire) {
  std::ofstream stream(prefix + "/" + name, std::ios::binary);
  Require(stream.good(), "wire output could not open");
  stream << wire << '\n';
  Require(stream.good(), "wire output failed");
}

std::string ReadAndSerialize(ForeignFixture &f,
                             BattleTransitionSnapshot &result,
                             const std::string &prefix, const char *name) {
  Require(ReadBattleTransitionSnapshot(f.b, f.scope, {kActualCombat}, result) ==
              BattleTransitionSnapshotStatus::available,
          "production lifecycle reader did not retain foreign combat");
  xar::ck3_12003::AttachBattleCurrentObservationV1(f.b, f.scope, result);
  result.snapshot_revision = 2;
  const auto wire = xar::ck3_11906::SerializeBattleTransitionV1(result);
  Require(!wire.empty(), "production reader -> serializer returned empty wire");
  const auto frame = BattleTransitionResultFrame("native-fixture",
      "query-battle-transition-v1-1577058305", 2, result);
  Require(!frame.empty(), "production envelope serialization returned empty frame");
  WriteWire(prefix, std::string(name) + ".json", wire);
  WriteWire(prefix, std::string(name) + "-frame.json", frame);
  return wire;
}

void ForeignBothSides(const std::string &prefix) {
  ForeignFixture f;
  BattleTransitionSnapshot result{};
  ReadAndSerialize(f, result, prefix, "foreign-both-sides");
  Require(result.battle_transition_ready && result.current_observation &&
              result.current_observation->available,
          "actual foreign shape was blocked by player eligibility");
  Require(result.attacker_public_cunit_ids_in_stored_order ==
              std::vector<std::int32_t>{251658381, 473, 474} &&
              result.defender_public_cunit_ids_in_stored_order ==
              std::vector<std::int32_t>{50331920, 83886484},
          "actual foreign army order or generation-zero public IDs changed");
  const auto &o = *result.current_observation;
  Require(o.base_combat_width == 2412 && o.final_combat_width == 1206 &&
              o.base_advantage_raw == -1'100'000 &&
              o.resolved_advantage_raw == -1'300'000 && o.scale == 100'000,
          "native current width or signed advantage fields changed");
  Require(o.attacker.derived_current_fighting_raw == 9'000'000 &&
              o.attacker.derived_soft_casualties_raw == 3'000'000 &&
              o.defender.derived_current_fighting_raw == 7'000'000 &&
              o.defender.derived_soft_casualties_raw == 2'000'000,
          "two native buckets not summed once or tick-start cache substituted");
  Require(o.attacker.derived_main_fighting_entry_hard_casualties_raw == 1'000'000 &&
              o.attacker.non_main_start_minus_current_minus_soft_raw == 2'000'000 &&
              o.defender.derived_main_fighting_entry_hard_casualties_raw == 1'000'000 &&
              o.defender.non_main_start_minus_current_minus_soft_raw == 1'000'000,
          "non-main residual was labeled or added as main hard loss");
  Require(o.attacker.participant_hard_total_raw == 7'000'000 &&
              o.defender.participant_hard_total_raw == 11'000'000 &&
              o.defender.participant_hard_ledger.size() == 2 &&
              o.defender.participant_hard_ledger[0].participant_character_id == kDefenderOwner0 &&
              o.defender.participant_hard_ledger[0].hard_casualties_raw == 5'000'000 &&
              o.defender.participant_hard_ledger[1].participant_character_id == kDefenderOwner1 &&
              o.defender.participant_hard_ledger[1].hard_casualties_raw == 6'000'000,
          "owner hard ledger order or independent loss total changed");
}

void LegalZero(const std::string &prefix) {
  ForeignFixture f;
  Put<std::int32_t>(f.combat, 0x6C0, 0);
  Put<std::int32_t>(f.combat, 0x6C4, 0);
  Put<std::int64_t>(f.combat, 0x6C8, 0);
  Put<std::int64_t>(f.combat, 0x710, 0);
  for (auto *entry : {&f.entry0, &f.entry1, &f.extra_entries[0], &f.extra_entries[1]}) {
    Put<std::int64_t>(*entry, 0x10, 0);
    Put<std::int64_t>(*entry, 0x18, 0);
    Put<std::int64_t>(*entry, 0x20, 0);
  }
  Put<std::int64_t>(f.attacker_hard, 0x10, 0);
  Put<std::int64_t>(f.defender_hard[0], 0x10, 0);
  Put<std::int64_t>(f.defender_hard[1], 0x10, 0);
  BattleTransitionSnapshot result{};
  ReadAndSerialize(f, result, prefix, "legal-zero");
  Require(result.current_observation && result.current_observation->available,
          "legal zero observation was treated unavailable");
  const auto &o = *result.current_observation;
  Require(o.base_combat_width == 0 && o.final_combat_width == 0 &&
              o.base_advantage_raw == 0 && o.resolved_advantage_raw == 0 &&
              o.attacker.derived_current_fighting_raw == 0 &&
              o.attacker.derived_soft_casualties_raw == 0 &&
              o.attacker.derived_main_fighting_entry_hard_casualties_raw == 0 &&
              o.attacker.non_main_start_minus_current_minus_soft_raw == 0 &&
              o.attacker.participant_hard_total_raw == 0,
          "legal native zero fields became invented nonzero/null");
}

void StaleRegiment(const std::string &prefix) {
  ForeignFixture f;
  Put<std::int32_t>(f.extra_regiments[0], 0x10, kRegiment2 + 0x1000000);
  BattleTransitionSnapshot result{};
  ReadAndSerialize(f, result, prefix, "stale-regiment");
  Require(result.status == BattleTransitionSnapshotStatus::available &&
              result.battle_transition_ready && result.phase_day == 3,
          "stale leaf discarded stable foreign lifecycle");
  Require(result.current_observation && !result.current_observation->available &&
              result.current_observation->unavailable_reason ==
                  "combat_side_graph_or_casualty_totals_unavailable",
          "stale regiment generation was accepted or lost reason");
}

void MalformedHardLedger(const std::string &prefix) {
  ForeignFixture f;
  Put<std::int32_t>(f.combat, 0x3CC, 3); // count exceeds the two-row capacity
  BattleTransitionSnapshot result{};
  ReadAndSerialize(f, result, prefix, "malformed-hard-ledger");
  Require(result.battle_transition_ready && result.current_observation &&
              !result.current_observation->available &&
              result.current_observation->unavailable_reason ==
                  "combat_side_graph_or_casualty_totals_unavailable",
          "malformed owner loss vector was accepted or broke lifecycle");
}

void PausedScopeUnavailable(const std::string &prefix) {
  ForeignFixture f;
  BattleTransitionSnapshot result{};
  Require(ReadBattleTransitionSnapshot(f.b, f.scope, {kActualCombat}, result) ==
              BattleTransitionSnapshotStatus::available,
          "scope fixture base lifecycle failed");
  f.scope.paused = false;
  xar::ck3_12003::AttachBattleCurrentObservationV1(f.b, f.scope, result);
  result.snapshot_revision = 2;
  Require(result.battle_transition_ready && result.current_observation &&
              !result.current_observation->available &&
              result.current_observation->unavailable_reason ==
                  "paused_exact_combat_scope_unavailable",
          "unpaused additive read did not preserve unavailable observation");
  const auto wire = xar::ck3_11906::SerializeBattleTransitionV1(result);
  Require(!wire.empty(), "scope unavailable wire failed");
  WriteWire(prefix, "scope-unavailable.json", wire);
  WriteWire(prefix, "scope-unavailable-frame.json", BattleTransitionResultFrame(
      "native-fixture", "query-battle-transition-v1-1577058305", 2, result));
}

void AbsentCombat(const std::string &prefix) {
  ForeignFixture f;
  f.combats.Set(kActualCombat, nullptr);
  BattleTransitionSnapshot result{};
  Require(ReadBattleTransitionSnapshot(f.b, f.scope, {kActualCombat}, result) ==
              BattleTransitionSnapshotStatus::combat_not_found,
          "absent combat lifecycle classification changed");
  xar::ck3_12003::AttachBattleCurrentObservationV1(f.b, f.scope, result);
  result.snapshot_revision = 2;
  Require(result.battle_transition_ready && !result.current_observation,
          "absent combat invented current observation");
  const auto wire = xar::ck3_11906::SerializeBattleTransitionV1(result);
  Require(!wire.empty(), "absent combat wire failed");
  WriteWire(prefix, "absent-combat.json", wire);
  WriteWire(prefix, "absent-combat-frame.json", BattleTransitionResultFrame(
      "native-fixture", "query-battle-transition-v1-1577058305", 2, result));
}
} // namespace

#include "xar_bridge/ck3_12002_combat.hpp"
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"
#endif
#include <functional>
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
// Unused legacy mailbox leaves are linked by the production serializer TU.
// The focused cases invoke ck3_12002's real reader directly.
namespace xar::ck3_11906 {
game::BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const Bindings &, const game::BattleControlRequest &,
    game::BattleControlSnapshot &output) noexcept {
  output = {};
  return output.status;
}
bool ReadCurrentBattleKnightV1(
    const Bindings &, const game::Snapshot &,
    const game::BattleControlSnapshot &,
    const game::CurrentBattleKnightRequestV1 &,
    game::CurrentBattleKnightSnapshotV1 &output) noexcept {
  output = {};
  return false;
}
} // namespace xar::ck3_11906
#endif

namespace {
constexpr std::int32_t kRollSelected0 = 0x01000003;
constexpr std::int32_t kRollSelected1 = 0x01000004;
constexpr std::int32_t kRollCandidate0 = 0x01000005;
constexpr std::int32_t kRollCandidate1 = 0x01000006;

void RequireRoll(bool condition, const std::string &description) {
  if (!condition) {
    throw std::runtime_error(description);
  }
}

struct SelectedRollFixture {
  Fixture battle;
  Bytes<0x220> selected0{}, selected1{}, candidate0{}, candidate1{};
  Bytes<0x860> army_province{};
  Bytes<0x790> terrain{};
  std::array<std::array<std::int64_t, 4>, 2> modifiers{{
      {100'000, 200'000, 300'000, 400'000},
      {-100'000, 0, 100'000, 200'000}}};
  std::int32_t minimum_roll = 0, maximum_roll = 10;
  int terrain_queries = 0, modifier_queries = 0, candidate_queries = 0;
  bool wrong_province = false;
  static SelectedRollFixture *current;

  static void *ProvinceResolver(void *context, std::int32_t id) {
    auto &f = *static_cast<SelectedRollFixture *>(context);
    if (id == 2640) return f.battle.province.data();
    if (id == 2639) return f.army_province.data();
    return nullptr;
  }
  static void *ProvinceTerrain(void *province) {
    auto &f = *current;
    ++f.terrain_queries;
    if (province != f.battle.province.data()) {
      f.wrong_province = true;
      return nullptr;
    }
    return f.terrain.data();
  }
  static void *Aggregator(void *character) {
    auto &f = *current;
    if (character == f.candidate0.data() || character == f.candidate1.data()) {
      ++f.candidate_queries;
    }
    return character;
  }
  static std::int64_t *Modifier(void *aggregator, std::int64_t *output,
                               std::int32_t index) {
    auto &f = *current;
    ++f.modifier_queries;
    std::size_t entry = 4;
    if (index == 0x115) entry = 0;
    if (index == 0x116) entry = 1;
    if (index == 0x200) entry = 2;
    if (index == 0x201) entry = 3;
    if (entry == 4) return nullptr;
    if (aggregator == f.selected0.data()) {
      *output = f.modifiers[0][entry];
    } else if (aggregator == f.selected1.data()) {
      *output = f.modifiers[1][entry];
    } else {
      ++f.candidate_queries;
      *output = 99'900'000;
    }
    return output;
  }
  static void *RuleState(void *owner) {
    return owner == current->battle.char0.data()
               ? current->battle.rules.data() : nullptr;
  }
  static bool Retreat(void *combat, void *, void *sink) {
    if (sink != nullptr) return false;
    auto &f = current->battle;
    auto *side = static_cast<std::byte *>(combat) + 0x20;
    const auto days = (f.scope.date_raw - Get<std::int32_t>(f.result.data(), 0x2C)) / 24;
    return !Get<std::uint8_t>(side, 0xC0) &&
           (Get<std::uint8_t>(side, 0xC1) || days > f.minimum) &&
           Get<std::int32_t>(combat, 0x6B0) < 2 &&
           (Get<std::uint32_t>(f.rules.data(), 0x40) & (1U << 10));
  }
  void Character(Bytes<0x220> &object, std::int32_t id) {
    Put(object, 0x18, id);
    Put<std::uint32_t>(object, 0x1C, 0x43686172U);
    battle.characters.Set(id, object.data());
  }
  SelectedRollFixture() {
    current = this;
    Character(selected0, kRollSelected0);
    Character(selected1, kRollSelected1);
    Character(candidate0, kRollCandidate0);
    Character(candidate1, kRollCandidate1);
    Put(battle.combat, 0x94, kRollSelected0);
    Put(battle.combat, 0x3DC, kRollSelected1);
    Put(battle.army0, 0x120, kRollCandidate0);
    Put(battle.army1, 0x120, kRollCandidate1);
    Put<std::int32_t>(army_province, 0x10, 2639);
    Put<std::uint32_t>(army_province, 0x85C, 0x50726F76U);
    battle.province_rows[2639] = army_province.data();
    Put(battle.unit0, 0x20, army_province.data());
    Put(battle.unit1, 0x20, army_province.data());
    Put<std::uint16_t>(terrain, 0x776, 0x200);
    Put<std::uint16_t>(terrain, 0x778, 0x201);
    battle.b.resolve_province = ProvinceResolver;
    battle.b.province_context = this;
    battle.b.get_combat_retreat_rule_state = RuleState;
    battle.b.can_order_combat_retreat = Retreat;
    auto &context = battle.b.commander_roll_context;
    context.enabled = true;
    context.game_state_slot = &battle.g;
    context.character_storage_slot = &battle.characters.root;
    context.get_province_terrain = ProvinceTerrain;
    context.get_character_modifier_aggregator = Aggregator;
    context.read_character_modifier = Modifier;
    context.commander_min_roll = &minimum_roll;
    context.commander_max_roll = &maximum_roll;
  }
};
SelectedRollFixture *SelectedRollFixture::current = nullptr;

struct RollExpectation {
  bool available = true;
  std::int32_t minimum = 0, maximum = 0;
  const char *reason = "";
};

void CheckRollBounds(const BattleControlNextRollBoundsSnapshot &bounds,
                     const RollExpectation &expected, const std::string &label) {
  RequireRoll(bounds.available == expected.available, label + " availability");
  RequireRoll(bounds.effective_min_roll == expected.minimum &&
              bounds.effective_max_roll == expected.maximum, label + " endpoints");
  RequireRoll(bounds.unavailable_reason == expected.reason, label + " reason: " + bounds.unavailable_reason);
}

int RunSelectedCommanderRollFixtures(const char *output_directory) {
  try {
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
    std::string cases;
#else
    (void)output_directory;
#endif
    int case_count = 0;
    const auto add = [&](const char *name,
                         const std::function<void(SelectedRollFixture &)> &configure,
                         std::array<RollExpectation, 2> expected) {
      SelectedRollFixture f;
      configure(f);
      BattleControlSnapshot snapshot;
      const auto result = ReadBattleControlSnapshot(f.battle.b, f.battle.scope,
                                                    {0x01000001}, snapshot);
      const std::string prefix = std::string(name) + ": ";
      RequireRoll(result == BattleControlSnapshotStatus::available, prefix + "reader status");
      RequireRoll(!f.wrong_province, prefix + "terrain queried outside actual combat province");
      RequireRoll(f.candidate_queries == 0, prefix + "army candidate queried");
      CheckRollBounds(snapshot.attacker.selected_commander_next_roll_bounds, expected[0], prefix + "attacker");
      CheckRollBounds(snapshot.defender.selected_commander_next_roll_bounds, expected[1], prefix + "defender");
      RequireRoll(snapshot.province_id == 2640 && Get<std::int32_t>(f.army_province.data(), 0x10) == 2639,
                  prefix + "actual combat province identity");
      RequireRoll(snapshot.attacker.selected_commander_character_id != Get<std::int32_t>(f.battle.army0.data(), 0x120),
                  prefix + "actual selected differs from army candidate");
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
      // Production application-main mailbox assigns this transport revision.
      snapshot.snapshot_revision = static_cast<std::uint64_t>(case_count + 1);
      const auto battle_wire = xar::ck3_11906::SerializeBattleControlSnapshotV1(snapshot);
      const auto resume_wire = xar::ck3_11906::SerializeActiveCombatResumeInputsV1(snapshot);
      RequireRoll(!battle_wire.empty() && !resume_wire.empty(), prefix + "production serialization");
      if (case_count) cases += ',';
      cases += "{\"name\":\"" + std::string(name) + "\",\"expected_reader_status\":\"available\"";
      cases += ",\"battle_control_snapshot\":" + battle_wire;
      cases += ",\"active_combat_resume_inputs_v1\":" + resume_wire;
      cases += ",\"expected_bounds\":[";
      for (std::size_t side = 0; side != 2; ++side) {
        if (side) cases += ',';
        cases += expected[side].available
                     ? "[" + std::to_string(expected[side].minimum) + "," + std::to_string(expected[side].maximum) + "]"
                     : "null";
      }
      cases += "],\"expected_unavailable_reasons\":[";
      for (std::size_t side = 0; side != 2; ++side) {
        if (side) cases += ',';
        cases += expected[side].available ? "null" : "\"" + std::string(expected[side].reason) + "\"";
      }
      cases += "],\"selected_character_modifier_raw\":[";
      for (std::size_t side = 0; side != 2; ++side) {
        if (side) cases += ',';
        cases += "[" + std::to_string(f.modifiers[side][0]) + "," + std::to_string(f.modifiers[side][1]) + "]";
      }
      cases += "],\"terrain_modifier_raw\":[";
      for (std::size_t side = 0; side != 2; ++side) {
        if (side) cases += ',';
        cases += "[" + std::to_string(f.modifiers[side][2]) + "," + std::to_string(f.modifiers[side][3]) + "]";
      }
      cases += "],\"actual_selected_character_ids\":[" + std::to_string(kRollSelected0) + "," + std::to_string(kRollSelected1);
      cases += "],\"army_candidate_character_ids\":[" + std::to_string(kRollCandidate0) + "," + std::to_string(kRollCandidate1);
      cases += "],\"actual_combat_province_id\":2640,\"army_current_province_id\":2639,\"terrain_query_count\":" + std::to_string(f.terrain_queries);
      cases += ",\"modifier_query_count\":" + std::to_string(f.modifier_queries) + "}";
#endif
      ++case_count;
    };
    const std::array<RollExpectation, 2> baseline{{{true, 4, 16, ""}, {true, 0, 12, ""}}};
    const std::array<RollExpectation, 2> inapplicable{{
        {false, 0, 0, "next_main_roll_not_applicable_in_phase"},
        {false, 0, 0, "next_main_roll_not_applicable_in_phase"}}};
    add("actual_selected_differs_from_army_candidate", [](auto &) {}, baseline);
    add("signed_fractional_modifiers_truncate_toward_zero", [](auto &f) {
      f.modifiers[0] = {-150'000, -250'001, 299'999, 499'999};
    }, {{{true, 1, 12, ""}, {true, 0, 12, ""}}});
    add("valid_absent_selected_commander", [](auto &f) {
      Put<std::int32_t>(f.battle.combat, 0x94, -1);
      Put<std::int32_t>(f.battle.combat, 0x3DC, -1);
    }, {{{true, 0, 0, ""}, {true, 0, 0, ""}}});
    add("maneuver_phase", [](auto &f) { Put<std::int32_t>(f.battle.combat, 0x6B0, 0); }, inapplicable);
    add("finalized_main_phase", [](auto &f) { Put<std::uint8_t>(f.battle.combat, 0x704, 1); }, inapplicable);
    add("unbound_commander_roll_context", [](auto &f) { f.battle.b.commander_roll_context = {}; }, {{{false, 0, 0, "commander_roll_bindings_unavailable"}, {false, 0, 0, "commander_roll_bindings_unavailable"}}});
#ifdef XAR_SELECTED_ROLL_WIRE_FIXTURE
    const std::string payload = "{\"schema_version\":1,\"actual\":0,\"executable_sha256\":\"94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6\",\"cases\":[" + cases + "]}";
    if (output_directory && *output_directory) {
      std::ofstream output(std::string(output_directory) + "/actual_selected_roll_cases.json", std::ios::binary);
      RequireRoll(static_cast<bool>(output), "open wire output");
      output << payload << '\n';
      RequireRoll(static_cast<bool>(output), "write wire output");
    }
#endif
    std::cout << "Actual-selected commander next-roll-bounds focused fixtures GREEN: " << case_count << " new cases; actual=0\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "Actual-selected commander next-roll-bounds focused fixture RED: " << error.what() << '\n';
    return 1;
  }
}
} // namespace

int main(int argc, char **argv) {
  if (argc > 1 && std::string_view(argv[1]) == "--selected-roll-only") {
    return RunSelectedCommanderRollFixtures(argc > 2 ? argv[2] : "");
  }
  if (RunSelectedCommanderRollFixtures("") != 0) {
    return 1;
  }

  if (argc != 2) return 2;
  int failures = 0;
  for (const auto &item : std::array{
      std::pair{"foreign-both-sides", &ForeignBothSides},
      std::pair{"legal-zero", &LegalZero},
      std::pair{"stale-regiment", &StaleRegiment},
      std::pair{"malformed-hard-ledger", &MalformedHardLedger},
      std::pair{"scope-unavailable", &PausedScopeUnavailable},
      std::pair{"absent-combat", &AbsentCombat}}) {
    try {
      item.second(argv[1]);
      std::cout << item.first << " GREEN\n";
    } catch (const std::exception &error) {
      ++failures;
      std::cerr << item.first << " RED: " << error.what() << '\n';
    }
  }
  return failures ? 1 : 0;
}
