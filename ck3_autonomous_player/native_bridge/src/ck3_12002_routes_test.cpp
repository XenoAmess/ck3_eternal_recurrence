#include "xar_bridge/ck3_12002_routes.hpp"

#ifdef NDEBUG
#undef NDEBUG
#endif

#include <array>
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

using namespace xar;
namespace {
template <class T, class B> void Put(B &b, std::size_t at, T value) {
  std::memcpy(b.data() + at, &value, sizeof(T));
}
template <class T> T Get(const void *p, std::size_t at) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(p) + at, sizeof(T));
  return value;
}
using Unit = std::array<std::byte, 0x200>;
using Army = std::array<std::byte, 0x140>;
using Province = std::array<std::byte, 0x870>;
using Combat = std::array<std::byte, 0x720>;
struct Storage {
  std::array<std::byte, 0x30> object{};
  std::array<std::byte, 16 * 8> slots{};
  void *pointer = object.data();
  Storage() { Put(object, 0x20, slots.data()); Put(object, 0x2C, std::int32_t{8}); }
  template <class B> void Add(std::int32_t id, B &b, std::size_t id_at) {
    Put(b, id_at, id);
    Put(slots, (static_cast<std::uint32_t>(id) & 0xFFFFFFU) * 16 + 8, b.data());
  }
};
void *g_origin = nullptr;
void *g_front = nullptr;
void *g_tail = nullptr;
std::array<void *, 2> g_path{};
int g_destroyed = 0;
int g_path_builds = 0;
std::int64_t g_duration = 100'000;
bool g_empty = false;
bool g_fort_defender = false;
void *g_changing_clock = nullptr;
std::int32_t MoveMode(void *, void *, std::int32_t) { return 0; }
void *Origin(void *) { return g_origin; }
void *Constructor(void *p) {
  std::memset(p, 0, 0x130);
  return p;
}
void *Context(void *p, void *) { std::memset(p, 0, 0x70); return p; }
bool BuildPath(void *, void *, void *, std::int32_t route_kind, void *p) {
  assert(route_kind == 2);
  void *const rows = g_path.data();
  std::memcpy(p, &rows, sizeof(void *));
  std::int32_t n = 1;
  std::memcpy(static_cast<std::byte *>(p) + 8, &n, 4);
  std::memcpy(static_cast<std::byte *>(p) + 12, &n, 4);
  ++g_path_builds;
  return true;
}
void *Destroy(void *p, std::int32_t flags) {
  assert(flags == 0);
  assert(Get<std::int32_t>(p, 0x20) == 1);
  ++g_destroyed;
  return p;
}
std::int64_t *Speed(void *, std::int64_t *p) { *p = 100'000; return p; }
void *Front(void *) { return g_front; }
void *Tail(void *) { return g_tail; }
std::int64_t *Duration(void *, std::int64_t *p, const void *path, void *) {
  *p = g_duration * Get<std::int32_t>(path, 0x0C);
  if (g_changing_clock != nullptr) {
    const auto date = Get<std::int32_t>(g_changing_clock, 8) + 24;
    std::memcpy(static_cast<std::byte *>(g_changing_clock) + 8, &date, 4);
  }
  return p;
}
bool Hostile(void *a, void *b, bool include_same_side) {
  assert(!include_same_side);
  return (Get<std::int32_t>(a, 0x18) == 0x1000001) !=
         (Get<std::int32_t>(b, 0x18) == 0x1000001);
}
bool Empty(void *) { return g_empty; }
bool InCombat(void *a) { return Get<std::int32_t>(a, 0x128) > 0; }
std::int32_t *Holder(void *p, std::int32_t *out) { *out = Get<std::int32_t>(p, 0x73C); return out; }
bool Defender(void *, void *) { return g_fort_defender; }

struct Fixture {
  static constexpr std::int32_t subject_id = 0x1000001;
  static constexpr std::int32_t enemy_id = 0x1000002;
  static constexpr std::int32_t enemy2_id = 0x1000003;
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x150> data{};
  void *state_ptr = state.data();
  void *jomini_ptr = jomini.data();
  void *mode_ptr = nullptr;
  std::array<std::byte, 0x1C8> mode_root{};
  std::array<std::byte, 0x30> mode{};
  Storage units, armies, regiments, characters, combats, results;
  std::array<Unit, 3> unit{};
  std::array<Army, 3> army{};
  std::array<std::array<std::byte, 0x40>, 3> regiment{};
  std::array<std::array<std::byte, 0x30>, 3> character{};
  std::array<Province, 3> province{};
  std::array<void *, 5> province_array{};
  std::array<std::array<std::byte, 0xB8>, 3> node{};
  std::array<std::array<std::byte, 0x10>, 3> info{};
  std::array<std::array<std::byte, 0x60>, 3> adjacency{};
  std::array<std::byte, 0x20> gate{};
  std::array<std::int32_t, 3> province_units{subject_id, enemy_id, enemy2_id};
  std::array<std::int32_t, 2> province_combats{0x1000001, 0x1000002};
  std::array<Combat, 2> combat{};
  std::array<std::array<std::int32_t, 2>, 2> attacker_ids{};
  std::array<std::array<std::int32_t, 2>, 2> defender_ids{};
  std::array<std::array<std::int32_t, 1>, 3> regiment_ids{};
  ck3_12002::RouteBindings binding{};
  game::Snapshot scope{};

  Fixture() {
    g_origin = province[0].data();
    g_path = {info[1].data(), info[2].data()};
    g_destroyed = g_path_builds = 0;
    g_duration = 100'000; g_empty = false; g_fort_defender = false;
    g_changing_clock = nullptr;
    Put(state, 8, std::int32_t{43'823'104});
    Put(state, 0xA0, data.data());
    Put(jomini, 0x20, std::uint8_t{1});
    Put(data, 0x140, province_array.data());
    Put(data, 0x14C, std::int32_t{5});
    Put(mode_root, 0x1C0, mode.data()); mode_ptr = mode_root.data();
    Put(gate, 0x1B, std::uint8_t{1});
    for (std::size_t i = 0; i < 3; ++i) {
      const auto id = subject_id + static_cast<std::int32_t>(i);
      units.Add(id, unit[i], 0x10); armies.Add(id, army[i], 0x10);
      regiments.Add(id, regiment[i], 0x10); characters.Add(id, character[i], 0x18);
      Put(unit[i], 0x20, province[i == 0 ? 0 : 1].data());
      Put(unit[i], 0x174, id); Put(unit[i], 0x178, id);
      Put(army[i], 0x124, id); Put(army[i], 0x128, std::int32_t{-1});
      regiment_ids[i] = {id};
      Put(army[i], 0x38, regiment_ids[i].data()); Put(army[i], 0x44, std::int32_t{1});
      Put(regiment[i], 0x14, std::uint32_t{0x41725267}); Put(regiment[i], 0x38, std::int32_t{100});
      Put(character[i], 0x1C, std::uint32_t{0x43686172});
      const auto pid = static_cast<std::int32_t>(i) + 2;
      province_array[pid] = province[i].data();
      Put(province[i], 0x10, pid); Put(province[i], 0x85C, std::uint32_t{0x50726F76});
      Put(province[i], 8, node[i].data()); Put(province[i], 0x20, gate.data());
      Put(province[i], 0x73C, enemy_id);
      Put(province[i], 0x740, province_units.data()); Put(province[i], 0x74C, std::int32_t{3});
      Put(province[i], 0x758, province_combats.data()); Put(province[i], 0x764, std::int32_t{0});
      Put(info[i], 0, pid); Put(info[i], 9, std::uint8_t{1});
      Put(node[i], 0xB0, info[i].data()); Put(node[i], 0x50, adjacency[i].data());
      Put(node[i], 0x5C, std::int32_t{2});
      int k = 0;
      for (int j = 0; j < 3; ++j) if (j != static_cast<int>(i)) {
        Put(adjacency[i], k * 0x30 + 4, std::int32_t{j + 2});
        Put(adjacency[i], k * 0x30, std::int32_t{0}); ++k;
      }
    }
    binding.enabled = true;
    binding.game_state_slot = &state_ptr; binding.jomini_state_slot = &jomini_ptr;
    binding.army_storage_slot = &units.pointer; binding.army_internal_storage_slot = &armies.pointer;
    binding.regiment_storage_slot = &regiments.pointer; binding.character_storage_slot = &characters.pointer;
    binding.combat_storage_slot = &combats.pointer; binding.battle_result_storage_slot = &results.pointer;
    binding.contact_game_mode_slot = &mode_ptr;
    binding.read_unit_land_route_speed = Speed; binding.read_unit_naval_route_speed = Speed;
    binding.read_unit_current_edge_speed = Speed; binding.read_route_travel_duration = Duration;
    binding.get_army_move_mode = MoveMode; binding.resolve_move_origin = Origin;
    binding.construct_move_path_context = Context; binding.construct_army_move_path = Constructor;
    binding.build_army_move_route = BuildPath; binding.destroy_move_army_command = Destroy;
    binding.is_character_hostile = Hostile; binding.is_army_empty_for_contact = Empty;
    binding.is_army_in_combat = InCombat; binding.read_province_holder_character_id = Holder;
    binding.classify_contact_defender_by_holder = Defender; binding.classify_contact_defender_fallback = Defender;
    scope.paused = true; scope.date_raw = 43'823'104;
    game::ArmySnapshot own{}; own.army_id = subject_id; own.controllable = true;
    own.has_current_province = true; own.current_province_id = 2;
    scope.player_armies = {own};
    decltype(scope.active_wars)::value_type war{};
    auto enemy = own; enemy.army_id = enemy_id; enemy.controllable = false; enemy.current_province_id = 3;
    war.enemy_armies = {enemy}; scope.active_wars = {war};
  }
  void ContactProvince() {
    Put(unit[0], 0x20, province[1].data());
    scope.player_armies[0].current_province_id = 3;
  }
  void AddCombat(std::size_t i, std::int32_t primary_enemy) {
    const auto id = subject_id + static_cast<std::int32_t>(i);
    combats.Add(id, combat[i], 8); Put(combat[i], 0x0C, std::uint32_t{0x436F6D62});
    Put(combat[i], 0x6B8, province[1].data()); Put(combat[i], 0x708, std::int32_t{-1});
    Put(combat[i], 0x90, subject_id); Put(combat[i], 0x3D8, primary_enemy);
    attacker_ids[i][0] = subject_id; defender_ids[i][0] = primary_enemy;
    Put(combat[i], 0x30, attacker_ids[i].data()); Put(combat[i], 0x3C, std::int32_t{1});
    Put(combat[i], 0x378, defender_ids[i].data()); Put(combat[i], 0x384, std::int32_t{1});
    Put(combat[i], 0xD8, combat[i].data()); Put(combat[i], 0x420, combat[i].data());
  }
};
} // namespace

int main() {
  using namespace ck3_12002;
  assert(!BindRouteImage(0x140000000ULL, "old-hash").enabled);
  const auto exact = BindRouteImage(0x140000000ULL, kExecutableSha256);
  assert(exact.enabled && reinterpret_cast<std::uintptr_t>(exact.read_route_travel_duration) == 0x1424AADA0ULL);
  assert(reinterpret_cast<std::uintptr_t>(exact.combat_storage_slot) == 0x145D1DE70ULL);
  Fixture f;
  std::vector<std::int32_t> committed_ids{99}, committed_dates{99};
  assert(ReadCommittedRouteTimeline(f.binding, f.scope, Fixture::subject_id,
                                    committed_ids, committed_dates));
  assert(committed_ids.empty() && committed_dates.empty());
  Put(f.jomini, 0x20, std::uint8_t{0});
  Put(f.jomini, 0x24, std::int32_t{1});
  f.scope.paused = false;
  assert(!ReadCommittedRouteTimeline(f.binding, f.scope, Fixture::subject_id,
                                     committed_ids, committed_dates));
  Put(f.jomini, 0x20, std::uint8_t{1});
  f.scope.paused = true;
  assert(ReadCommittedRouteTimeline(f.binding, f.scope, Fixture::subject_id,
                                    committed_ids, committed_dates));
  const game::RouteContactHorizonRequest request{Fixture::subject_id, 3, {Fixture::enemy_id}};
  game::RouteContactHorizonSnapshot route{};
  assert(ReadRouteContactHorizon(f.binding, f.scope, request, route) == game::RouteContactHorizonStatus::available);
  assert(route.subject_route.arrival_date_raws == std::vector<std::int32_t>{43'823'128});
  assert(!route.one_day_contact_free && route.conflicts.size() == 1);
  assert(route.conflicts[0].kind == "same_province" && g_path_builds == 2 && g_destroyed == 2);
  std::array<void *, 1> active{f.info[1].data()};
  std::array<void *, 1> opposite{f.info[0].data()};
  Put(f.unit[0], 0x38, active.data()); Put(f.unit[0], 0x40, std::int32_t{1});
  Put(f.unit[0], 0x44, std::int32_t{1}); Put(f.unit[0], 0x190, std::int64_t{100'000});
  Put(f.unit[1], 0x38, opposite.data()); Put(f.unit[1], 0x40, std::int32_t{1});
  Put(f.unit[1], 0x44, std::int32_t{1}); Put(f.unit[1], 0x190, std::int64_t{100'000});
  f.scope.player_armies[0].route_province_ids = {3};
  f.scope.active_wars[0].enemy_armies[0].route_province_ids = {2};
  assert(ReadCommittedRouteTimeline(f.binding, f.scope, Fixture::subject_id,
                                    committed_ids, committed_dates));
  assert(committed_ids == std::vector<std::int32_t>{3});
  assert(committed_dates == std::vector<std::int32_t>{43'823'128});
  assert(ReadRouteContactHorizon(f.binding, f.scope, request, route) == game::RouteContactHorizonStatus::available);
  assert(g_path_builds == 2 && g_destroyed == 2);
  assert(std::any_of(route.conflicts.begin(), route.conflicts.end(), [](const auto &c) { return c.kind == "opposing_edge"; }));
  // New native origin selection is inlined. Exercise its migrated local
  // branch with locked movement, adding the unfinished first edge before
  // projecting the hypothetical route from that edge's destination.
  f.binding.resolve_move_origin = nullptr;
  f.binding.read_route_progress = Speed; f.binding.get_route_front = Front; f.binding.get_route_tail = Tail;
  std::int64_t cutoff = 50'000; f.binding.movement_locked_threshold = &cutoff;
  g_front = g_tail = f.province[1].data(); g_path[0] = f.info[2].data();
  auto detour = request; detour.target_province_id = 4;
  assert(ReadRouteContactHorizon(f.binding, f.scope, detour, route) == game::RouteContactHorizonStatus::available);
  assert(route.subject_route.route_province_ids == (std::vector<std::int32_t>{3, 4}));
  assert(route.subject_route.arrival_date_raws == (std::vector<std::int32_t>{43'823'128, 43'823'152}));
  f.binding.resolve_move_origin = Origin; g_path[0] = f.info[1].data();
  Put(f.unit[0], 0x44, std::int32_t{0}); Put(f.unit[1], 0x44, std::int32_t{0});
  f.scope.player_armies[0].route_province_ids.clear();
  f.scope.active_wars[0].enemy_armies[0].route_province_ids.clear();
  g_duration = 149'999;
  assert(ReadRouteContactHorizon(f.binding, f.scope, request, route) == game::RouteContactHorizonStatus::available);
  assert(route.subject_route.arrival_date_raws[0] == 43'823'128);
  g_duration = 150'000;
  assert(ReadRouteContactHorizon(f.binding, f.scope, request, route) == game::RouteContactHorizonStatus::available);
  assert(route.subject_route.arrival_date_raws[0] == 43'823'152 && route.one_day_contact_free);
  g_duration = 0xFFFFFFFFLL;
  assert(ReadRouteContactHorizon(f.binding, f.scope, request, route) == game::RouteContactHorizonStatus::timeline_unavailable);
  g_duration = 100'000;
  auto bad_scope = request; bad_scope.hostile_army_ids = {Fixture::enemy2_id};
  assert(ReadRouteContactHorizon(f.binding, f.scope, bad_scope, route) == game::RouteContactHorizonStatus::hostile_scope_mismatch);
  g_changing_clock = f.state.data();
  assert(ReadRouteContactHorizon(f.binding, f.scope, request, route) == game::RouteContactHorizonStatus::state_changed);
  g_changing_clock = nullptr; Put(f.state, 8, f.scope.date_raw);

  f.ContactProvince();
  const game::ActualContactScopeRequest contact_request{Fixture::subject_id, 3};
  game::ActualContactScopeSnapshot contact{};
  assert(ReadActualContactScope(f.binding, f.scope, contact_request, contact) == game::ActualContactScopeStatus::available);
  assert(contact.transition_kind == "create_new" && contact.defender_seed_character_id == Fixture::enemy_id);
  assert(contact.attacker_army_ids == std::vector<std::int32_t>{Fixture::subject_id});
  assert(contact.defender_army_ids == (std::vector<std::int32_t>{Fixture::enemy_id, Fixture::enemy2_id}));
  assert(contact.actual_contact_scope_ready && contact.combat_v3_participant_scope_ready);
  // Old Province offsets deliberately contain irrelevant values; new arrays
  // and magic predicates must be sufficient even with no native vtables.
  Put(f.province[1], 0x754, std::int32_t{-99}); Put(f.province[1], 0x76C, std::int32_t{-99});
  assert(ReadActualContactScope(f.binding, f.scope, contact_request, contact) == game::ActualContactScopeStatus::available);
  f.AddCombat(0, Fixture::enemy_id); f.AddCombat(1, Fixture::enemy2_id);
  Put(f.province[1], 0x764, std::int32_t{2});
  assert(ReadActualContactScope(f.binding, f.scope, contact_request, contact) == game::ActualContactScopeStatus::available);
  assert(contact.transition_kind == "join_existing" && contact.selected_combat_id == Fixture::enemy_id);
  assert(contact.selected_combat_array_index == 1 && contact.join_side == "attacker");
  // Native candidate selection overwrites earlier compatible rows.
  Put(f.army[0], 0x128, Fixture::enemy_id); Put(f.army[2], 0x128, Fixture::enemy_id);
  assert(ReadActualContactScope(f.binding, f.scope, contact_request, contact) == game::ActualContactScopeStatus::available);
  assert(contact.scope_kind == "post_contact_observation" && contact.transition_kind == "in_combat");
  Put(f.unit[0], 0x10, std::int32_t{0x2000001});
  assert(ReadActualContactScope(f.binding, f.scope, contact_request, contact) == game::ActualContactScopeStatus::subject_army_not_found);
  Put(f.unit[0], 0x10, Fixture::subject_id);
  Put(f.jomini, 0x20, std::uint8_t{0}); f.scope.paused = false;
  assert(ReadActualContactScope(f.binding, f.scope, contact_request, contact) == game::ActualContactScopeStatus::requires_paused);
  std::cout << "ck3_12002_routes fixture PASS: projected timing, contact order, new province ABI, full ID, clock change, paused gate\n";
}
