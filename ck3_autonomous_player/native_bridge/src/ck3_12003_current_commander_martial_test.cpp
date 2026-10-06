#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_target_roll.hpp"
#include "xar_bridge/ck3_12003_current_commander_martial.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace xar::ck3_12003;
constexpr std::int32_t kPlayer = 29829;
constexpr std::int32_t kUnit = 83886367;
constexpr std::int32_t kArmy = 50331794;
constexpr std::int32_t kFirst = 30000;
constexpr std::int32_t kSecond = 30001;
constexpr std::int32_t kTarget = 2669;
constexpr std::int32_t kDate = 53236608;
constexpr std::uint64_t kRevision = 11;
int checks = 0;

template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset, sizeof(value));
  return value;
}
void Check(bool value, const char *label) {
  ++checks;
  if (!value) throw std::runtime_error(label);
}

// Only raw objects, callbacks and paused scope are synthetic. Each emitted
// envelope uses the genuine whole pool reader, new role-skill helper and real
// whole-query serializer. No observation/result row is replaced by the fixture.
struct Fixture {
  std::array<std::byte, 0x180> unit{}, army{};
  std::array<std::array<std::byte, 0x210>, 3> characters{};
  std::array<std::byte, 0x30> units{}, armies{}, character_store{};
  std::vector<std::byte> unit_slots = std::vector<std::byte>(288 * 0x10);
  std::vector<std::byte> army_slots = std::vector<std::byte>(147 * 0x10);
  std::vector<std::byte> character_slots = std::vector<std::byte>(30002 * 0x10);
  std::array<std::byte, 0x18> allocator_vtable{};
  std::array<std::byte, 0x08> allocator{};
  std::array<std::array<std::byte, 0xE0>, 2> aggregators{};
  std::array<std::byte, 0xA8> game_state{};
  std::array<std::byte, 0x150> game_data{};
  std::array<std::byte, 0x860> province{};
  std::array<std::byte, 0x780> terrain{};
  std::vector<void *> province_slots = std::vector<void *>(2670);
  void *unit_storage = units.data();
  void *army_storage = armies.data();
  void *character_storage = character_store.data();
  void *game_state_pointer = game_state.data();
  void **allocated = nullptr;
  std::int32_t min_roll = 0, max_roll = 10;
  bool current_getter_mismatch = false;
  int collect_calls = 0, release_calls = 0, eligibility_calls = 0;
  int quality_calls = 0, advantage_calls = 0, current_calls = 0, skill_calls = 0;
  int terrain_calls = 0, target_modifier_calls = 0;
  std::string callback_error;

  Fixture();
  CommanderBindings Bindings();
  CommanderTargetRollBindings TargetBindings();
  xar::game::Snapshot Scope();
};
Fixture *active = nullptr;

void RequireCallback(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
void Release(void *allocator, void *data, std::uint64_t alignment) {
  RequireCallback(allocator == active->allocator.data() &&
                  data == active->allocated && alignment == 8,
                  "existing caller-owned vector allocator/alignment retained");
  delete[] static_cast<void **>(data);
  active->allocated = nullptr;
  ++active->release_calls;
}
void Collect(void *owner, CommanderPointerVector *output, bool filter_now, bool allow_guests) {
  RequireCallback(owner == active->characters[0].data() && !filter_now && allow_guests,
                  "existing manual candidate pool owner and arguments retained");
  RequireCallback(output->allocator == active->allocator.data() &&
                  output->data == nullptr && output->count == 0 && output->capacity == 0,
                  "whole reader supplies fresh caller-owned vector");
  active->allocated = new void *[2];
  active->allocated[0] = active->characters[1].data();
  active->allocated[1] = active->characters[2].data();
  output->data = active->allocated;
  output->count = output->capacity = 2;
  ++active->collect_calls;
}
bool CanAssign(std::int32_t mode, void *candidate, void *army, void *reason) {
  RequireCallback(mode == 1 && army == active->army.data() && reason == nullptr,
                  "native final player/manual eligibility remains independent");
  RequireCallback(candidate == active->characters[1].data() ||
                  candidate == active->characters[2].data(), "only pool identities reach CanAssign");
  ++active->eligibility_calls;
  return candidate == active->characters[1].data();
}
std::int32_t BaseQuality(void *candidate) {
  RequireCallback(candidate == active->characters[1].data() ||
                  candidate == active->characters[2].data(), "quality reads only pool identities");
  ++active->quality_calls;
  return candidate == active->characters[1].data() ? 125 : -17;
}
std::int32_t GenericAdvantage(void *candidate, std::int32_t context, bool flag) {
  RequireCallback(context == -1 && !flag &&
                  (candidate == active->characters[1].data() ||
                   candidate == active->characters[2].data()), "generic advantage context remains original");
  ++active->advantage_calls;
  return candidate == active->characters[1].data() ? 0 : -9;
}
void *CurrentCommander(void *army) {
  RequireCallback(army == active->army.data(), "actual commander getter receives actual CArmy");
  ++active->current_calls;
  return active->characters[active->current_getter_mismatch ? 1U : 0U].data();
}
std::int32_t TotalSkill(void *character, std::int32_t skill_index) {
  RequireCallback(character == active->characters[0].data() && skill_index == 1,
                  "total martial getter uses validated actual role receiver and constant index1");
  ++active->skill_calls;
  return Get<std::int32_t>(character, 0xDC);
}
std::int64_t *LandRate(void *unit, std::int64_t *output) {
  RequireCallback(unit == active->unit.data(), "movement uses public CUnit independently of role skill");
  *output = 111000;
  return output;
}
std::int64_t *NavalRate(void *unit, std::int64_t *output) {
  RequireCallback(unit == active->unit.data(), "naval movement uses public CUnit");
  *output = 0;
  return output;
}
void *ModifierAggregator(void *candidate) {
  const bool first = candidate == active->characters[1].data();
  RequireCallback(first || candidate == active->characters[2].data(),
                  "target helper remains bound to its candidate identities");
  return active->aggregators[first ? 0U : 1U].data();
}
std::int64_t *TargetModifier(void *table, std::int64_t *output, std::int32_t modifier) {
  RequireCallback((table == active->aggregators[0].data() ||
                   table == active->aggregators[1].data()) &&
                  (modifier == 0x115 || modifier == 0x116 ||
                   modifier == 0x500 || modifier == 0x501),
                  "missing martial callback does not alter original target modifier reads");
  ++active->target_modifier_calls;
  *output = 0;
  return output;
}
void *Terrain(void *province) {
  RequireCallback(province == active->province.data(), "target Province is resolved by existing helper");
  ++active->terrain_calls;
  return active->terrain.data();
}

Fixture::Fixture() {
  Put(unit.data(), 0x10, kUnit);
  Put(unit.data(), 0x174, kPlayer);
  Put(unit.data(), 0x178, kArmy);
  Put(army.data(), 0x10, kArmy);
  Put(army.data(), 0x120, kPlayer);
  Put(army.data(), 0x124, kUnit);
  Put(unit_slots.data(), 287 * 0x10 + 8, unit.data());
  Put(army_slots.data(), 146 * 0x10 + 8, army.data());
  Put(units.data(), 0x20, unit_slots.data());
  Put(units.data(), 0x2C, std::int32_t{288});
  Put(armies.data(), 0x20, army_slots.data());
  Put(armies.data(), 0x2C, std::int32_t{147});
  const std::array<std::int32_t, 3> ids{kPlayer, kFirst, kSecond};
  const std::array<std::int32_t, 3> martial{23, 41, 12};
  for (std::size_t index = 0; index < ids.size(); ++index) {
    Put(characters[index].data(), 0x18, ids[index]);
    Put(characters[index].data(), 0x1C, std::uint32_t{0x43686172});
    Put(characters[index].data(), 0xDC, martial[index]);
    Put(character_slots.data(), static_cast<std::size_t>(ids[index]) * 0x10 + 8,
        characters[index].data());
  }
  Put(character_store.data(), 0x20, character_slots.data());
  Put(character_store.data(), 0x2C, std::int32_t{30002});
  Put(allocator_vtable.data(), 0x10, &Release);
  Put(allocator.data(), 0, allocator_vtable.data());
  Put(game_state.data(), 0xA0, game_data.data());
  Put(game_data.data(), 0x140, province_slots.data());
  Put(game_data.data(), 0x14C, std::int32_t{2670});
  Put(province.data(), 0x10, kTarget);
  Put(province.data(), xar::ck3_12002::kObjectiveProvinceMagicOffset,
      std::uint32_t{0x50726F76});
  province_slots[static_cast<std::size_t>(kTarget)] = province.data();
  Put(terrain.data(), 0x776, std::uint16_t{0x500});
  Put(terrain.data(), 0x778, std::uint16_t{0x501});
}
CommanderBindings Fixture::Bindings() {
  CommanderBindings output{};
  output.enabled = output.armies.enabled = true;
  output.armies.unit_storage_slot = &unit_storage;
  output.armies.internal_army_storage_slot = &army_storage;
  output.character_storage_slot = &character_storage;
  output.vector_allocator = allocator.data();
  output.collect_candidates = Collect;
  output.can_set_commander = CanAssign;
  output.get_native_ai_base_quality = BaseQuality;
  output.get_generic_advantage = GenericAdvantage;
  output.get_army_commander = CurrentCommander;
  output.read_unit_land_movement_rate = LandRate;
  output.read_unit_naval_movement_rate = NavalRate;
  output.current_total_martial_observer_enabled = true;
  output.get_current_total_skill = TotalSkill;
  return output;
}
CommanderTargetRollBindings Fixture::TargetBindings() {
  CommanderTargetRollBindings output{};
  output.enabled = output.provinces.enabled = output.combat.enabled = true;
  output.provinces.game_state_slot = &game_state_pointer;
  output.combat.character_storage_slot = &character_storage;
  output.combat.get_character_modifier_aggregator = ModifierAggregator;
  output.combat.read_character_modifier = TargetModifier;
  output.combat.get_province_terrain = Terrain;
  output.combat.commander_min_roll = &min_roll;
  output.combat.commander_max_roll = &max_roll;
  return output;
}
xar::game::Snapshot Fixture::Scope() {
  xar::game::Snapshot output{};
  output.paused = output.map_ready = output.has_played_character = output.played_character_alive = true;
  output.played_character_id = kPlayer;
  output.date_raw = kDate;
  xar::game::ArmySnapshot army_scope{};
  army_scope.army_id = kUnit;
  army_scope.owner_character_id = kPlayer;
  army_scope.controllable = true;
  army_scope.has_current_province = true;
  army_scope.current_province_id = kTarget;
  army_scope.army_state = "stationary";
  army_scope.route_read_status = xar::game::ArmyRouteReadStatus::complete_empty;
  army_scope.route_source_count = 0;
  output.player_armies.push_back(army_scope);
  return output;
}
void ExpectMartial(const ArmyCommanderCandidatesSnapshot &output, std::int32_t value) {
  Check(output.current_total_martial.has_value(), "enabled current-role martial leaf exists");
  const auto &leaf = *output.current_total_martial;
  Check(leaf.status == "available" && leaf.source_character_id == kPlayer &&
        leaf.skill_index == 1 && leaf.value == value && leaf.unavailable_reason.empty() &&
        leaf.source == "native_current_assigned_commander_total_skill_cache",
        "production helper preserves exact actual-role signed cache and source identity");
}
void Emit(const std::filesystem::path &directory, const char *name,
          const ArmyCommanderCandidatesSnapshot &output, CommanderCandidatesReadResult result) {
  std::string step = "query-army-commander-candidates-v1-for-army-" + std::to_string(kUnit);
  if (output.target_province_id)
    step += "-at-province-" + std::to_string(*output.target_province_id);
  std::ofstream file(directory / name, std::ios::binary);
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"ok\":true,\"result\":"
       << SerializeArmyCommanderCandidates(output, result, 7, kRevision, kDate, step) << "}\n";
  Check(bool(file), "actual whole-query production serializer emits native envelope");
}
void RunScene(const std::filesystem::path &directory, unsigned int scene,
              std::int32_t scene_three_value = 0) {
  Fixture fixture{};
  active = &fixture;
  auto bindings = fixture.Bindings();
  if (scene == 3) Put(fixture.characters[0].data(), 0xDC, scene_three_value);
  if (scene == 4) Put(fixture.army.data(), 0x120, std::int32_t{-1});
  if (scene == 5) fixture.current_getter_mismatch = true;
  if (scene == 6) bindings.get_current_total_skill = nullptr;
  if (scene == 7) bindings.current_total_martial_observer_enabled = false;
  const auto unit_before = fixture.unit;
  const auto army_before = fixture.army;
  const auto characters_before = fixture.characters;
  ArmyCommanderCandidatesSnapshot output{};
  const auto result = ReadArmyCommanderCandidates(bindings, fixture.Scope(), kUnit, output);
  Check(result == (scene == 5 ? CommanderCandidatesReadResult::partial
                             : CommanderCandidatesReadResult::available),
        "optional skill retains existing whole-query result policy");
  Check(output.candidate_collection_complete && output.candidate_source_count == 2 &&
        output.candidates.size() == 2 && output.candidates[0].character_id == kFirst &&
        output.candidates[1].character_id == kSecond && output.candidates[0].available &&
        output.candidates[1].available && output.candidates[0].can_assign &&
        !output.candidates[1].can_assign && output.candidates[0].final_eligibility_observable &&
        output.candidates[1].final_eligibility_observable &&
        output.candidates[0].native_ai_base_quality == 125 &&
        output.candidates[1].native_ai_base_quality == -17 &&
        output.candidates[0].generic_advantage_points == 0 &&
        output.candidates[1].generic_advantage_points == -9,
        "actual role outside pool does not alter collection order, eligibility or quality");
  Check(output.current_movement_speed.context_observable &&
        output.current_movement_speed.land.status == "available" &&
        output.current_movement_speed.land.raw == 111000 &&
        output.current_movement_speed.naval.status == "available" &&
        output.current_movement_speed.naval.raw == 0 &&
        output.current_movement_speed.current_edge.status == "not_applicable",
        "optional skill availability preserves independent existing movement leaves");
  const char *name = nullptr;
  switch (scene) {
  case 1:
    ExpectMartial(output, 23);
    Check(output.current_commander_character_id == kPlayer, "actual Army role supplies the martial identity");
    name = "01-current-outside-pool.json"; break;
  case 2:
    ExpectMartial(output, 23);
    Check(Get<std::int32_t>(fixture.characters[1].data(), 0xDC) == 41 &&
          output.current_total_martial->source_character_id != kFirst,
          "independent synthetic selected-context30000/martial41 is never the actual-role receiver");
    name = "02-current-and-selected-distinct.json"; break;
  case 3:
    ExpectMartial(output, scene_three_value);
    name = scene_three_value == 0 ? "03-current-zero-negative-zero.json"
                                 : "03-current-zero-negative-negative.json"; break;
  case 4:
    Check(output.current_commander_status == "absent" &&
          output.current_commander_character_id == -1 && output.current_total_martial &&
          output.current_total_martial->status == "unavailable" &&
          !output.current_total_martial->source_character_id && !output.current_total_martial->value &&
          output.current_total_martial->unavailable_reason == "current_commander_absent" &&
          fixture.current_calls == 0, "absent role produces explicit absence without current/skill getter call");
    name = "04-current-absent.json"; break;
  case 5:
    Check(output.current_commander_status == "unavailable" && output.current_total_martial &&
          output.current_total_martial->status == "unavailable" &&
          output.current_total_martial->source_character_id == kPlayer &&
          !output.current_total_martial->value &&
          output.current_total_martial->unavailable_reason == output.current_commander_unavailable_reason &&
          output.current_commander_unavailable_reason == "current_commander_identity_unavailable",
          "current getter pointer mismatch preserves existing identity failure and complete candidate pool");
    name = "05-current-identity-unavailable.json"; break;
  case 6:
    Check(output.current_commander_status == "available" && output.current_total_martial &&
          output.current_total_martial->status == "unavailable" &&
          output.current_total_martial->source_character_id == kPlayer && !output.current_total_martial->value &&
          output.current_total_martial->unavailable_reason == "current_commander_skill_reader_unavailable",
          "enabled observer with missing callback retains role and reports unavailable skill");
    ReadArmyCommanderCandidateTargetRollBounds(fixture.TargetBindings(), kTarget, output);
    for (const auto &row : output.candidates) {
      Check(row.target_roll_bounds && row.target_roll_bounds->status == "available" &&
            row.target_roll_bounds->source_target_province_id == kTarget &&
            row.target_roll_bounds->effective_min_roll == 0 &&
            row.target_roll_bounds->effective_max_roll == 10,
            "missing martial reader does not suppress independent original target endpoints");
    }
    Check(fixture.terrain_calls == 1 && fixture.target_modifier_calls == 8,
          "single missing-skill scene uses existing target computation unchanged");
    name = "06-skill-reader-unavailable.json"; break;
  case 7:
    Check(!output.current_total_martial && output.current_commander_status == "available",
          "legacy disabled optional observer keeps old role payload without new leaf");
    Check(SerializeArmyCommanderCandidates(output, result, 7, kRevision, kDate,
          "query-army-commander-candidates-v1-for-army-" + std::to_string(kUnit)).find(
          "current_total_martial") == std::string::npos, "legacy whole serializer omits new leaf");
    name = "07-legacy-omission.json"; break;
  default: throw std::runtime_error("invalid new scene");
  }
  const bool reads_skill = scene <= 3;
  Check(fixture.skill_calls == (reads_skill ? 1 : 0), "only enabled validated actual role calls new getter once");
  Check(fixture.collect_calls == 1 && fixture.release_calls == 1 &&
        fixture.eligibility_calls == 2 && fixture.quality_calls == 2 && fixture.advantage_calls == 2 &&
        fixture.allocated == nullptr && fixture.callback_error.empty(),
        "genuine whole native pool callbacks and allocator lifecycle remain exact");
  Check(fixture.unit == unit_before && fixture.army == army_before &&
        fixture.characters == characters_before, "read-only skill observation never changes raw game objects");
  Emit(directory, name, output, result);
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "new whole-query wire output directory required");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    for (unsigned int scene = 1; scene <= 7; ++scene) {
      RunScene(directory, scene);
      if (scene == 3) RunScene(directory, scene, -7);
    }
    std::ofstream provenance(directory / "FIXTURE-PROVENANCE.json", std::ios::binary);
    provenance << "{\"schema\":\"current-commander-total-martial-fixture-provenance-v1\","
                  "\"paused_scope\":\"synthetic\",\"native_getter_callbacks\":\"synthetic\","
                  "\"raw_object_memory\":\"synthetic\",\"row_replacement\":false,"
                  "\"producer\":\"actual whole reader role helper production serializer\","
                  "\"synthetic_selected_context_character_id\":30000,"
                  "\"synthetic_selected_context_total_martial\":41,"
                  "\"cases\":7,\"native_query_occurrences\":8,\"runtime_game_execution\":false}\n";
    Check(bool(provenance), "synthetic boundary recorded alongside genuine native whole-query wires");
    std::cout << "PASS checks=" << checks << " cases=7 native_query_occurrences=8\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
