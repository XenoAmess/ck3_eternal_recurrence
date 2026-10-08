// SOURCE_PREPARED / NOTRUN. Root owns the single first build and execution.
// Fixture-owned callback outputs do not claim an observed native future choice.
#include "xar_bridge/ck3_12004_army.hpp"
#include "xar_bridge/ck3_12004_province.hpp"
#include "xar_bridge/ck3_12004_world.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12003_war_occupation.hpp"
#include "xar_bridge/war_occupation_targets_v1_serializer.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
using namespace xar;
using Vector = ck3_12003::WarOccupationPointerVector;
constexpr std::int32_t kActor = 29829, kDefender = 31050, kWar = 100663329;
constexpr std::int32_t kOwnUnit = 218104048, kOwnArmy = 67109093;
constexpr std::int32_t kForeignUnit = 335544362, kForeignArmy = 352321570;
constexpr std::int32_t kSiege = 318767193, kDate = 53288472;
constexpr std::array<std::int32_t, 2> kProvinces{2606, 2608};
constexpr std::array<std::string_view, 4> kScenes{
    "foreign_leader_own_eligible", "foreign_leader_own_excluded",
    "no_selected_army", "selection_unavailable"};

void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template <class Buffer, class T>
void Put(Buffer &buffer, std::size_t offset, T value) {
  Require(offset + sizeof value <= buffer.size(), "fixture store exceeds owned buffer");
  std::memcpy(buffer.data() + offset, &value, sizeof value);
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof value);
  return value;
}
std::size_t Slot(std::int32_t id) {
  return (static_cast<std::uint32_t>(id) & 0xFFFFFFU) * 0x10 + 8;
}

struct Fixture;
Fixture *active = nullptr;
void Release(void *, void *data, std::uint64_t) { delete[] static_cast<void **>(data); }
void Allocate(Vector *out, const std::vector<void *> &values) {
  if (values.empty()) return;
  out->data = new void *[values.size()];
  std::copy(values.begin(), values.end(), out->data);
  out->count = out->capacity = static_cast<std::int32_t>(values.size());
}

struct Fixture {
  std::string_view scene;
  std::array<std::byte, 0xA8> game_state{};
  std::vector<std::byte> game_data = std::vector<std::byte>(0x2F000);
  std::array<std::byte, 0x360> war{};
  std::array<std::byte, 0x30> context{}, war_store{}, character_store{}, title_store{};
  std::array<std::byte, 0x30> unit_store{}, army_store{}, siege_store{};
  std::vector<std::byte> war_slots = std::vector<std::byte>(64 * 0x10);
  std::vector<std::byte> character_slots = std::vector<std::byte>(32000 * 0x10);
  std::vector<std::byte> title_slots = std::vector<std::byte>(4096 * 0x10);
  std::vector<std::byte> unit_slots = std::vector<std::byte>(256 * 0x10);
  std::vector<std::byte> army_slots = std::vector<std::byte>(256 * 0x10);
  std::vector<std::byte> siege_slots = std::vector<std::byte>(128 * 0x10);
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  std::array<std::array<std::byte, 0x10>, 2> participants{};
  std::array<void *, 1> attackers{}, defenders{};
  std::array<std::array<std::byte, 0x130>, 2> titles{};
  std::array<std::array<std::byte, 0x90>, 2> definitions{};
  std::array<std::array<std::byte, 0x860>, 2> provinces{};
  std::vector<void *> province_slots = std::vector<void *>(3000);
  std::array<std::array<std::byte, 0x180>, 2> units{};
  std::array<std::array<std::byte, 0x210>, 2> armies{};
  std::array<std::byte, 0x460> siege{};
  std::array<std::int32_t, 2> residents{kForeignUnit, kOwnUnit};
  std::array<std::byte, 0x18> allocator_vtable{};
  std::array<std::byte, 8> allocator{};
  void *game_slot = game_state.data(), *character_slot = character_store.data();
  void *title_slot = title_store.data(), *unit_slot = unit_store.data();
  void *army_slot = army_store.data(), *siege_slot = siege_store.data();
  ck3_12003::WarOccupationTargetsBindingsV1 bindings{};
  std::vector<game::ArmySnapshot> known;
  std::size_t selection_calls = 0;

  explicit Fixture(std::string_view selected_scene);
  game::Snapshot Scope() const {
    game::Snapshot scope{};
    scope.paused = scope.map_ready = scope.has_played_character = scope.played_character_alive = true;
    scope.played_character_id = kActor;
    scope.date_raw = kDate;
    scope.player_armies.push_back(known[1]);
    game::ActiveWarSnapshot war_row{};
    war_row.war_id = kWar;
    war_row.player_side = game::PlayerWarSide::attacker;
    war_row.enemy_armies.push_back(known[0]);
    scope.active_wars.push_back(war_row);
    return scope;
  }
};

bool Contains(const void *side, std::int32_t id) {
  const auto &values = Get<Vector>(side, 8);
  for (std::int32_t index = 0; index < values.count; ++index)
    if (Get<std::int32_t>(values.data[index], 8) == id) return true;
  return false;
}
void *Context(std::int32_t id) { return id == kWar ? active->context.data() : nullptr; }
void CollectTerritory(void *, std::int32_t, const Vector *territory,
                      const Vector *, Vector *out) {
  Allocate(out, {territory->data[0]});
}
void CollectHoldings(void *character, Vector *out) {
  if (Get<std::int32_t>(character, 0x18) == kDefender)
    Allocate(out, {active->titles[0].data(), active->titles[1].data()});
}
void Count(void *, const Vector *, const Vector *, bool,
           ck3_12003::WarOccupationNativeCounts *out) { *out = {0, 1}; }
bool Related(void *) { return false; }
void *TitleProvince(void *title) {
  return Get<std::int32_t>(title, 0x10) == 2100
      ? active->provinces[0].data() : active->provinces[1].data();
}
bool Occupied(void *) { return false; }
std::int32_t Fort(void *province) { return Get<std::int32_t>(province, 0x850); }
std::int32_t Garrison(void *province) {
  return Get<std::int32_t>(province, 0x10) == 2606 ? 588 : 1050;
}
std::int32_t Strength(void *province) {
  if (Get<std::int32_t>(province, 0x10) == 2606) return 0;
  return active->scene == "foreign_leader_own_eligible" ? 1500 : 152;
}
std::int32_t *Selection(void *province, std::int32_t *out) {
  ++active->selection_calls;
  *out = Get<std::int32_t>(province, 0x10) == 2606 || active->scene == "no_selected_army"
      ? -1 : kForeignArmy;
  return out;
}
std::int64_t *Progress(void *, std::int64_t *out) { *out = 0; return out; }
std::int64_t *Total(void *, std::int64_t *out) { *out = 51353725; return out; }
std::int32_t Days(void *) { return std::numeric_limits<std::int32_t>::max(); }
std::uint8_t Excluded(void *) { return 0; }
std::uint8_t Eligible(void *army, void *) {
  return static_cast<std::uint8_t>(Get<std::int32_t>(army, 0x10) != kOwnArmy ||
      active->scene == "foreign_leader_own_eligible" || active->scene == "selection_unavailable");
}

Fixture::Fixture(std::string_view selected_scene) : scene(selected_scene) {
  active = this;
  Put(game_state, 0xA0, static_cast<void *>(game_data.data()));
  Put(game_data, ck3_12002::kWorldWarManagerOffset + 0x20, static_cast<void *>(war_store.data()));
  const auto store = [](auto &storage, auto &slots, std::int32_t capacity) {
    Put(storage, 0x20, static_cast<void *>(slots.data())); Put(storage, 0x2C, capacity);
  };
  store(war_store, war_slots, 64); store(character_store, character_slots, 32000);
  store(title_store, title_slots, 4096); store(unit_store, unit_slots, 256);
  store(army_store, army_slots, 256); store(siege_store, siege_slots, 128);
  Put(war_slots, Slot(kWar), static_cast<void *>(war.data()));
  Put(war, 8, kWar); Put(context, 0x28, kWar);
  Put(war, 0x288, kActor); Put(war, 0x28C, kDefender);
  for (std::size_t index = 0; index < 2; ++index) {
    const auto id = index == 0 ? kActor : kDefender;
    Put(characters[index], 0x18, id); Put(characters[index], 0x1C, std::uint32_t{0x43686172});
    Put(character_slots, Slot(id), static_cast<void *>(characters[index].data()));
    Put(participants[index], 8, id);
  }
  attackers[0] = participants[0].data(); defenders[0] = participants[1].data();
  Put(war, 0x28, Vector{attackers.data(), 1, 1, nullptr});
  Put(war, 0x88, Vector{defenders.data(), 1, 1, nullptr});
  for (std::size_t index = 0; index < 2; ++index) {
    const auto title_id = static_cast<std::int32_t>(2100 + index);
    Put(titles[index], 0x10, title_id); Put(titles[index], 0x48, static_cast<void *>(definitions[index].data()));
    Put(titles[index], 0x108, std::int32_t{-1}); Put(titles[index], 0x128, kDefender);
    Put(definitions[index], 0x64, std::int32_t{1}); Put(definitions[index], 0x88, kProvinces[index]);
    Put(title_slots, Slot(title_id), static_cast<void *>(titles[index].data()));
    Put(provinces[index], 0x10, kProvinces[index]); Put(provinces[index], 0x738, title_id);
    Put(provinces[index], 0x73C, std::int32_t{-1}); Put(provinces[index], 0x850, index == 0 ? 4 : 7);
    Put(provinces[index], 0x85C, std::uint32_t{0x50726F76});
    Put(provinces[index], 0x788, index == 0 ? -1 : kSiege);
    province_slots[static_cast<std::size_t>(kProvinces[index])] = provinces[index].data();
    const auto unit_id = index == 0 ? kForeignUnit : kOwnUnit;
    const auto army_id = index == 0 ? kForeignArmy : kOwnArmy;
    Put(units[index], 0x10, unit_id); Put(units[index], 0x20, static_cast<void *>(provinces[1].data()));
    Put(units[index], 0x174, index == 0 ? kDefender : kActor); Put(units[index], 0x178, army_id);
    if (scene == "no_selected_army") Put(units[index], 0x44, std::int32_t{1});
    Put(armies[index], 0x10, army_id); Put(armies[index], 0x14, std::uint32_t{0x41726D79});
    Put(armies[index], 0x120, std::int32_t{-1});
    Put(unit_slots, Slot(unit_id), static_cast<void *>(units[index].data()));
    Put(army_slots, Slot(army_id), static_cast<void *>(armies[index].data()));
    game::ArmySnapshot army{}; army.army_id = unit_id; army.controllable = index == 1;
    known.push_back(army);
  }
  Put(game_data, 0x140, static_cast<void *>(province_slots.data())); Put(game_data, 0x14C, std::int32_t{3000});
  Put(provinces[1], 0x740, static_cast<void *>(residents.data())); Put(provinces[1], 0x74C, std::int32_t{2});
  Put(siege_slots, Slot(kSiege), static_cast<void *>(siege.data()));
  Put(siege, 8, kSiege); Put(siege, 0xC, std::uint32_t{0x53696765});
  Put(siege, 0x200, static_cast<void *>(provinces[1].data()));
  Put(siege, 0x208, kForeignArmy); Put(siege, 0x3D0, std::int64_t{0});
  Put(allocator_vtable, 0x10, &Release); Put(allocator, 0, static_cast<void *>(allocator_vtable.data()));
  constexpr std::uintptr_t base = 0x140000000ULL;
  auto army_binding = ck3_12004::BindArmyImage12004(base, ck3_12004::kExecutableSha256);
  army_binding.internal_army_storage_slot = &army_slot;
  bindings.provinces = ck3_12004::BindProvinceImage12004(base, ck3_12004::kExecutableSha256, army_binding);
  Require(reinterpret_cast<std::uintptr_t>(bindings.provinces.current_besieging_army) ==
      base + ck3_12004::kCurrentBesiegingArmyGetterRva, "actual4 factory did not bind the full native selector");
  auto &province = bindings.provinces;
  province.game_state_slot = &game_slot; province.character_storage_slot = &character_slot;
  province.landed_title_storage_slot = &title_slot; province.unit_storage_slot = &unit_slot;
  province.siege_storage_slot = &siege_slot;
  province.title_province = &TitleProvince; province.is_occupied = &Occupied;
  province.fort_level = &Fort; province.garrison_size = &Garrison; province.besieging_strength = &Strength;
  province.current_besieging_army = scene == "selection_unavailable" ? nullptr : &Selection;
  province.siege_progress = &Progress; province.siege_total_work = &Total; province.siege_days_left = &Days;
  province.siege_army_excluded = &Excluded; province.siege_army_province_eligible = &Eligible;
  province.eligible_regiment_siege_work = nullptr; province.highest_eligible_siege_tier = nullptr;
  province.siege_ordinary_daily_progress = nullptr; province.siege_current_phase_length = nullptr;
  province.siege_is_blocked = nullptr; province.assault_daily_progress = nullptr;
  province.assault_daily_casualties = nullptr; province.validate_start_assault = nullptr;
  province.validate_stop_assault = nullptr;
  bindings.world = ck3_12004::BindWorldImage12004(base, ck3_12004::kExecutableSha256);
  bindings.world.game_state_slot = &game_slot; bindings.world.contains_war_participant = &Contains;
  bindings.enabled = true; bindings.character_storage_slot = &character_slot;
  bindings.vector_allocator = allocator.data(); bindings.get_war_occupation_context = &Context;
  bindings.collect_territory_participants = &CollectTerritory; bindings.collect_holding_titles = &CollectHoldings;
  bindings.count_holding = &Count; bindings.war_participants_are_liege_related = &Related;
}

void Write(const std::filesystem::path &path, const std::string &value) {
  std::ofstream stream(path, std::ios::binary);
  Require(static_cast<bool>(stream), "cannot write fresh whole fixture packet");
  stream << value << '\n';
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 3 && std::string_view(argv[1]) == "--wire-dir", "usage: --wire-dir <fresh-dir>");
    const std::filesystem::path output = argv[2];
    std::filesystem::create_directories(output);
    for (const auto scene : kScenes) {
      Fixture fixture(scene);
      const auto before_provinces = fixture.provinces;
      const auto before_units = fixture.units;
      const auto before_armies = fixture.armies;
      const auto before_siege = fixture.siege;
      game::WarOccupationTargetsV1 observation{};
      const auto read = ck3_12003::ReadWarOccupationTargetsV1(
          fixture.bindings, fixture.Scope(), kWar, observation);
      Require(read == game::ReadWarOccupationTargetsV1Result::available && observation.rows.size() == 2,
          "whole native occupation reader did not retain both objective rows");
      const auto &province = observation.rows[1];
      const auto &selection = province.current_besieging_army_selection;
      Require(province.province_id == 2608 && province.active_siege.current_work_raw == 0 &&
          province.active_siege.total_work_raw == 51353725 &&
          !province.active_siege.player_army_besieging && province.active_siege.besieging_army_id == kForeignUnit,
          "stored foreign leader or separate current/total work changed");
      if (scene == "selection_unavailable") {
        Require(!selection.observable && fixture.selection_calls == 0, "failed selector observation became empty selection");
      } else if (scene == "no_selected_army") {
        Require(selection.observable && selection.native_carmy_id == -1 && selection.controllable_observable &&
            !selection.controllable, "native-1 did not remain an observed empty selection");
      } else {
        Require(selection.observable && selection.native_carmy_id == kForeignArmy &&
            selection.public_unit_id == kForeignUnit && selection.controllable_observable && !selection.controllable,
            "native CArmy output was confused with public CUnit identity");
        Require(province.active_siege.province_unit_occurrences.size() == 2 &&
            province.active_siege.province_unit_occurrences[1].public_unit_id == kOwnUnit &&
            province.active_siege.province_unit_occurrences[1].eligible == (scene == "foreign_leader_own_eligible"),
            "independent selected-subject qualification changed with foreign leader");
      }
      Require(fixture.provinces == before_provinces && fixture.units == before_units &&
          fixture.armies == before_armies && fixture.siege == before_siege,
          "readonly whole observer changed owned Province, Unit, Army or Siege bytes");
      auto wire = game::SerializeWarOccupationTargetsV1(observation, read, 1, 2,
          "query-war-occupation-targets-v1-100663329");
      wire = game::Render12004BuildIdentity(std::move(wire), game::Ck3_12004AdapterDescriptor());
      Write(output / (std::string(scene) + ".json"),
          "{\"type\":\"command_result\",\"request_id\":\"siege-selection-whole\",\"ok\":true,\"result\":" + wire + '}');
      active = nullptr;
    }
    Write(output / "PRODUCER-RECEIPT.json",
        "{\"status\":\"PASS\",\"readiness\":\"fixture-live\",\"scene_count\":4,"
        "\"producer\":\"actual4 Province factory -> whole occupation reader -> production serializer\","
        "\"fixture_owned_callbacks\":true,\"native_EXE_callback_invoked\":false,\"game_operations\":0,"
        "\"actual_future_selection_observed\":false,\"old_GREEN_replayed\":false}");
    return 0;
  } catch (const std::exception &error) {
    active = nullptr; std::cerr << error.what() << '\n'; return 1;
  }
}
