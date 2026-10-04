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
#include <vector>
#include "xar_bridge/ck3_12003.hpp"

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
constexpr std::array<std::int32_t, 9> kPersonIds{
    29829, 32750, 30470, 30784, 16818648, 60824, 43706, 60821, 60822};
constexpr std::array<std::int32_t, 9> kProwess{
    7, 0, -5, 19, 24, 1, 42, 2147483647, 0};
constexpr std::array<std::uint8_t, 9> kFlags{
    0, 1, 2 | 8, 4 | 64, 8 | 16, 32 | 128, 1 | 2, 0, 0};
constexpr std::array<std::int32_t, 9> kRanks{0, 1, 2, 3, 0, 0, -1, 0, -1};
constexpr std::array<const char *, 8> kKeys{
    "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
    "one_eyed", "disfigured", "incapable"};

struct PersonInputs {
  Bytes<0x38> storage{};
  std::vector<std::byte> slots;
  void *root = storage.data();
  std::array<Bytes<0x210>, 9> characters{};
  std::array<Bytes<0x40>, 8> definitions{};
  std::array<void *, 8> definition_rows{};
  Bytes<0x60> database{};
  static PersonInputs *current;
  PersonInputs() : slots(60825U * 0x10U) {
    current = this;
    Put(storage, 0x20, slots.data());
    Put<std::int32_t>(storage, 0x2C, 60825);
    for (std::size_t i = 0; i < characters.size(); ++i) {
      auto &character = characters[i];
      Put(character, 0x18, kPersonIds[i]);
      Put<std::uint32_t>(character, 0x1C, 0x43686172U);
      Put(character, 0xEC, kProwess[i]);
      void *pointer = character.data();
      std::memcpy(slots.data() + (kPersonIds[i] & 0xFFFFFF) * 0x10ULL + 8,
                  &pointer, sizeof(pointer));
    }
    // Requested full ID still points at its old slot, but the generation differs.
    Put(characters.back(), 0x18, kPersonIds.back() + 0x1000000);
    for (std::size_t i = 0; i < definitions.size(); ++i) {
      auto &definition = definitions[i];
      const auto length = std::strlen(kKeys[i]);
      Put(definition, 0x10, static_cast<std::int32_t>(i));
      std::memcpy(definition.data() + 0x18, kKeys[i], length);
      Put<std::uint64_t>(definition, 0x28, length);
      Put<std::uint64_t>(definition, 0x30, 15);
      definition_rows[i] = definition.data();
    }
    Put(database, 0x50, definition_rows.data());
    Put<std::int32_t>(database, 0x5C, 8);
  }
  static void *Database() { return current->database.data(); }
  static bool HasTrait(void *character, const void *definition) {
    const auto index = Get<std::int32_t>(const_cast<void *>(definition), 0x10);
    Require(index >= 0 && index < 8, "concrete stable trait definition ID");
    for (std::size_t i = 0; i < current->characters.size(); ++i) {
      if (character == current->characters[i].data())
        return (kFlags[i] & (1U << index)) != 0;
    }
    throw std::runtime_error("native HasTrait received an unowned person");
  }
};
PersonInputs *PersonInputs::current = nullptr;


void CurrentDeathReason(const std::string &output) {
  Fixture f;
  PersonInputs person;
  f.b.character_storage_slot = &person.root;
  f.scope.player_armies.clear();
  f.scope.date_raw = 54000000;  // Synthetic fixture date, not a paused live frame.
  Put(f.gs, 8, f.scope.date_raw);
  EnableBattleCurrentPerson12003(f.b, 0x180000000ULL,
                                xar::ck3_12003::kExecutableSha256);
  f.b.current_person_traits.get_trait_database = &PersonInputs::Database;
  f.b.current_person_traits.character_has_trait = &PersonInputs::HasTrait;
  std::array<Bytes<0x30>, 3> death_data{};
  std::array<Bytes<0x50>, 2> reasons{};
  const std::string inline_key = "death_battle";
  std::string heap_key = "death_fixture_heap_length_over15";
  std::memcpy(reasons[0].data() + 0x18, inline_key.data(), inline_key.size());
  Put<std::uint32_t>(reasons[0], 0x28,
                     static_cast<std::uint32_t>(inline_key.size()));
  Put<std::uint64_t>(reasons[0], 0x30, 15);
  Put(reasons[1], 0x18, heap_key.data());
  Put<std::uint32_t>(reasons[1], 0x28,
                     static_cast<std::uint32_t>(heap_key.size()));
  Put<std::uint64_t>(reasons[1], 0x30, heap_key.size());
  Put(death_data[0], 0x10, reasons[0].data());
  Put(death_data[1], 0x10, reasons[1].data());
  // death_data[2] contains the legitimate native null reason pointer.
  for (std::size_t i = 0; i < death_data.size(); ++i)
    Put(person.characters[i + 1], 0x1D0, death_data[i].data());
  BattleTerminalTransitionRequestV1 request{};
  request.prior_combat_id = -1;
  request.subject_public_cunit_id = -1;
  request.character_ids = {kPersonIds[0], kPersonIds[1], kPersonIds[2],
                           kPersonIds[3], kPersonIds[8]};
  BattleTerminalTransitionSnapshotV1 snapshot{};
  Require(ReadBattleTerminalTransitionV1(f.b, f.scope, request, snapshot) ==
              BattleTerminalTransitionStatusV1::available,
          "new current death-reason query unavailable");
  Require(snapshot.character_observations &&
              snapshot.character_observations->size() == 5 &&
              !snapshot.battle_terminal_transition_ready,
          "character-only reason reader invented battle terminal or lost IDs");
  const auto &rows = *snapshot.character_observations;
  for (std::size_t i = 0; i < rows.size(); ++i)
    Require(rows[i].character_id == request.character_ids[i] &&
                rows[i].current_person_state.has_value(),
            "new reason leaf detached from the strict requested full ID");
  const auto &alive = rows[0].current_person_state->death_record;
  const auto &inlined = rows[1].current_person_state->death_record;
  const auto &heaped = rows[2].current_person_state->death_record;
  const auto &no_reason = rows[3].current_person_state->death_record;
  const auto &unresolved = rows[4].current_person_state->death_record;
  Require(rows[0].alive == true &&
              alive.status == BattleCurrentPersonDeathRecordStatusV1::none &&
              !alive.reason_key && alive.unavailable_reason.empty(),
          "alive native null death marker became an unavailable/dead record");
  Require(rows[1].alive == false &&
              inlined.status == BattleCurrentPersonDeathRecordStatusV1::available &&
              inlined.reason_key == inline_key && inlined.unavailable_reason.empty(),
          "actual inline definition+18 key did not become an owned observed string");
  Require(rows[2].alive == false &&
              heaped.status == BattleCurrentPersonDeathRecordStatusV1::available &&
              heaped.reason_key == heap_key && heaped.unavailable_reason.empty(),
          "actual heap definition+18 key did not become an owned observed string");
  Require(rows[3].alive == false &&
              no_reason.status == BattleCurrentPersonDeathRecordStatusV1::available &&
              !no_reason.reason_key && no_reason.unavailable_reason.empty(),
          "native null reason was confused with no death record or read failure");
  Require(!rows[4].alive &&
              unresolved.status == BattleCurrentPersonDeathRecordStatusV1::unavailable &&
              !unresolved.reason_key &&
              unresolved.unavailable_reason == "character_unresolved",
          "strict generation mismatch fabricated death key or absence");
  const std::string original_heap = heap_key;
  std::memset(reasons[0].data() + 0x18, 'X', inline_key.size());
  heap_key.assign(heap_key.size(), 'Y');
  Require(inlined.reason_key == inline_key && heaped.reason_key == original_heap,
          "query retained borrowed native string storage");
  snapshot.snapshot_revision = 63;
  const auto wire = xar::ck3_11906::SerializeBattleTerminalTransitionV1(snapshot);
  Require(!wire.empty(), "existing terminal serializer rejected new reason leaf");
  std::ofstream file(output + "/current-death-reason.json", std::ios::binary);
  Require(file.good(), "new reason wire cannot be opened");
  file << wire << '\n';
  Require(file.good(), "new reason wire write failed");
}
} // namespace

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  try {
    CurrentDeathReason(argv[1]);
    std::cout << "death-reason GREEN (one new current-person source case)\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "death-reason RED: " << error.what() << '\n';
    return 1;
  }
}
