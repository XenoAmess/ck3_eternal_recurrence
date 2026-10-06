#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12003_commander_target_roll.hpp"

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
constexpr std::uint16_t kTerrainMin = 0x500;
constexpr std::uint16_t kTerrainMax = 0x501;
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

// The callbacks, paused scope and raw object memory below are synthetic fixture
// inputs. Each whole result is produced by the actual reader, candidate adapter,
// endpoint computation and production serializer; no result row is replaced.
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
  std::array<std::array<std::int64_t, 4>, 2> modifiers{};
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
  std::int32_t candidate_count = 2;
  std::int32_t min_roll = 0, max_roll = 10;
  bool first_modifier_failure = false;
  int collect_calls = 0, release_calls = 0, terrain_calls = 0;
  int eligibility_calls = 0, modifier_calls = 0;
  std::string callback_error;

  Fixture();
  CommanderBindings CandidateBindings();
  CommanderTargetRollBindings TargetBindings();
  xar::game::Snapshot Scope();
};
Fixture *active = nullptr;

void RequireCallback(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
void Release(void *allocator, void *data, std::uint64_t alignment) {
  RequireCallback(allocator == active->allocator.data() && data == active->allocated && alignment == 8,
                  "native pool retains its existing allocator receiver and alignment");
  delete[] static_cast<void **>(data);
  active->allocated = nullptr;
  ++active->release_calls;
}
void Collect(void *owner, CommanderPointerVector *output, bool filter_now, bool allow_guests) {
  RequireCallback(owner == active->characters[0].data() && !filter_now && allow_guests,
                  "whole reader uses existing manual pool arguments");
  RequireCallback(output->allocator == active->allocator.data() && output->data == nullptr &&
                  output->count == 0 && output->capacity == 0,
                  "native pool receives caller-owned empty vector");
  if (active->candidate_count > 0) {
    active->allocated = new void *[static_cast<std::size_t>(active->candidate_count)];
    for (std::int32_t index = 0; index < active->candidate_count; ++index)
      active->allocated[index] = active->characters[static_cast<std::size_t>(index + 1)].data();
  }
  output->data = active->allocated;
  output->count = output->capacity = active->candidate_count;
  ++active->collect_calls;
}
bool CanAssign(std::int32_t mode, void *candidate, void *army, void *reason) {
  RequireCallback(mode == 1 && army == active->army.data() && reason == nullptr,
                  "whole reader preserves final player/manual eligibility");
  ++active->eligibility_calls;
  return candidate == active->characters[1].data();
}
std::int32_t BaseQuality(void *) { return 30; }
std::int32_t GenericAdvantage(void *, std::int32_t context, bool flag) {
  RequireCallback(context == -1 && !flag, "generic advantage keeps existing independent context");
  return 30;
}
void *CurrentCommander(void *army) {
  RequireCallback(army == active->army.data(), "current assignment is observed on actual fixture CArmy");
  return active->characters[1].data();
}
void *ModifierAggregator(void *candidate) {
  const bool first = candidate == active->characters[1].data();
  RequireCallback(first || candidate == active->characters[2].data(),
                  "endpoint helper resolves actual native candidate identity");
  return active->aggregators[first ? 0U : 1U].data();
}
std::int64_t *PoolModifier(void *table, std::int64_t *output, std::int32_t modifier) {
  RequireCallback((table == active->aggregators[0].data() + 0x68 ||
                   table == active->aggregators[1].data() + 0x68) && modifier == 0x11D,
                  "existing optional siege observation keeps its original receiver");
  *output = 0;
  return output;
}
std::int64_t *TargetModifier(void *table, std::int64_t *output, std::int32_t modifier) {
  const bool first = table == active->aggregators[0].data();
  RequireCallback(first || table == active->aggregators[1].data(),
                  "candidate adapter delegates to the existing endpoint helper receiver");
  std::size_t field = 0;
  switch (modifier) {
  case 0x115: field = 0; break;
  case 0x116: field = 1; break;
  case kTerrainMin: field = 2; break;
  case kTerrainMax: field = 3; break;
  default: RequireCallback(false, "unexpected endpoint modifier enum"); return nullptr;
  }
  ++active->modifier_calls;
  if (first && active->first_modifier_failure && modifier == 0x115) return nullptr;
  *output = active->modifiers[first ? 0U : 1U][field];
  return output;
}
void *Terrain(void *province) {
  RequireCallback(province == active->province.data(), "target terrain getter uses resolved requested Province");
  ++active->terrain_calls;
  return active->terrain.data();
}

Fixture::Fixture() {
  Put(unit.data(), 0x10, kUnit);
  Put(unit.data(), 0x174, kPlayer);
  Put(unit.data(), 0x178, kArmy);
  Put(army.data(), 0x10, kArmy);
  Put(army.data(), 0x120, kFirst);
  Put(army.data(), 0x124, kUnit);
  Put(unit_slots.data(), 287 * 0x10 + 8, unit.data());
  Put(army_slots.data(), 146 * 0x10 + 8, army.data());
  Put(units.data(), 0x20, unit_slots.data());
  Put(units.data(), 0x2C, std::int32_t{288});
  Put(armies.data(), 0x20, army_slots.data());
  Put(armies.data(), 0x2C, std::int32_t{147});
  const std::array<std::int32_t, 3> ids{kPlayer, kFirst, kSecond};
  for (std::size_t index = 0; index < ids.size(); ++index) {
    Put(characters[index].data(), 0x18, ids[index]);
    Put(characters[index].data(), 0x1C, std::uint32_t{0x43686172});
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
  Put(terrain.data(), 0x776, kTerrainMin);
  Put(terrain.data(), 0x778, kTerrainMax);
}
CommanderBindings Fixture::CandidateBindings() {
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
  output.get_character_modifier_aggregator = ModifierAggregator;
  output.read_character_modifier = PoolModifier;
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
void ExpectBounds(const ArmyCommanderCandidatesSnapshot &output, std::size_t index,
                  std::int32_t minimum, std::int32_t maximum) {
  Check(output.candidates[index].target_roll_bounds.has_value(), "demanded target leaf exists");
  const auto &leaf = *output.candidates[index].target_roll_bounds;
  Check(leaf.status == "available" && leaf.source_target_province_id == kTarget &&
        leaf.effective_min_roll == minimum && leaf.effective_max_roll == maximum &&
        leaf.unavailable_reason.empty(), "actual production adapter preserves expected signed endpoints");
}
void Emit(const std::filesystem::path &directory, const char *name,
          const ArmyCommanderCandidatesSnapshot &output, CommanderCandidatesReadResult result) {
  std::string step = "query-army-commander-candidates-v1-for-army-" + std::to_string(kUnit);
  if (output.target_province_id.has_value())
    step += "-at-province-" + std::to_string(*output.target_province_id);
  std::ofstream file(directory / name, std::ios::binary);
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"ok\":true,\"result\":"
       << SerializeArmyCommanderCandidates(output, result, 7, kRevision, kDate, step) << "}\n";
  Check(bool(file), "whole query emitted using unchanged production candidate serializer");
}
void RunScene(const std::filesystem::path &directory, unsigned int scene) {
  Fixture fixture{};
  active = &fixture;
  if (scene == 1) {
    fixture.modifiers[0] = {-200000, 300000, 0, 0};
    fixture.modifiers[1] = {200000, -100000, 0, 0};
  } else if (scene == 2) {
    fixture.modifiers[0] = {-99999, 0, -99999, 0};
    fixture.modifiers[1] = {-100001, 0, 0, 0};
  } else if (scene == 3) {
    fixture.modifiers[0] = {0, -1000000, 0, 0};
    fixture.modifiers[1] = {-300000, -1100000, 0, 0};
  } else if (scene == 4) {
    fixture.province_slots[static_cast<std::size_t>(kTarget)] = nullptr;
  } else if (scene == 5) {
    fixture.first_modifier_failure = true;
  } else if (scene == 6) {
    fixture.candidate_count = 0;
  }
  const auto unit_before = fixture.unit;
  const auto army_before = fixture.army;
  const auto characters_before = fixture.characters;
  ArmyCommanderCandidatesSnapshot output{};
  const auto result = ReadArmyCommanderCandidates(fixture.CandidateBindings(), fixture.Scope(), kUnit, output);
  Check(result == CommanderCandidatesReadResult::available && output.candidate_collection_complete,
        "whole existing candidate read remains complete and available");
  if (scene != 7)
    ReadArmyCommanderCandidateTargetRollBounds(fixture.TargetBindings(), kTarget, output);
  Check(output.candidate_source_count == fixture.candidate_count &&
        output.candidates.size() == static_cast<std::size_t>(fixture.candidate_count),
        "target attachment preserves native candidate order and count");
  if (scene != 6) {
    Check(output.candidates[0].character_id == kFirst && output.candidates[1].character_id == kSecond &&
          output.candidates[0].can_assign && !output.candidates[1].can_assign &&
          output.candidates[0].native_ai_base_quality == 30 && output.candidates[1].native_ai_base_quality == 30,
          "target observation preserves two distinct identities and independent final eligibility/quality");
  }
  const char *name = nullptr;
  switch (scene) {
  case 1:
    ExpectBounds(output, 0, -2, 13); ExpectBounds(output, 1, 2, 9);
    name = "01-target-distinguishes-candidates.json"; break;
  case 2:
    ExpectBounds(output, 0, 0, 10); ExpectBounds(output, 1, -1, 10);
    name = "02-separate-negative-truncation.json"; break;
  case 3:
    ExpectBounds(output, 0, 0, 0); ExpectBounds(output, 1, -3, -1);
    name = "03-available-zero-negative.json"; break;
  case 4:
    for (const auto &row : output.candidates)
      Check(row.target_roll_bounds.has_value() && row.target_roll_bounds->status == "unavailable" &&
            !row.target_roll_bounds->effective_min_roll.has_value() &&
            !row.target_roll_bounds->effective_max_roll.has_value() &&
            !row.target_roll_bounds->unavailable_reason.empty(),
            "target failure retains each independent candidate with explicit unavailable endpoints");
    Check(fixture.terrain_calls == 0 && fixture.modifier_calls == 0,
          "unresolved target demands no endpoint modifier reads");
    name = "04-target-failure-independent-pool.json"; break;
  case 5:
    Check(output.candidates[0].target_roll_bounds.has_value() &&
          output.candidates[0].target_roll_bounds->status == "unavailable" &&
          output.candidates[0].target_roll_bounds->unavailable_reason == "commander_modifier_unavailable",
          "failed candidate native modifier output stays unavailable");
    ExpectBounds(output, 1, 0, 10);
    name = "05-one-modifier-failure.json"; break;
  case 6:
    Check(output.target_province_id == kTarget && output.candidates.empty(),
          "complete zero native pool keeps requested target header");
    name = "06-complete-empty-target.json"; break;
  case 7:
    Check(!output.target_province_id.has_value() &&
          !output.candidates[0].target_roll_bounds.has_value() &&
          !output.candidates[1].target_roll_bounds.has_value(),
          "legacy request has no new optional target fields");
    Check(fixture.terrain_calls == 0 && fixture.modifier_calls == 0,
          "no-target legacy read never invokes target adapter");
    name = "07-legacy-omission.json"; break;
  default: throw std::runtime_error("invalid new scene");
  }
  Check(fixture.unit == unit_before && fixture.army == army_before &&
        fixture.characters == characters_before &&
        output.current_commander_character_id == kFirst,
        "candidate query never performs assignment or changes raw player objects");
  Check(fixture.collect_calls == 1 && fixture.eligibility_calls == fixture.candidate_count &&
        fixture.allocated == nullptr && fixture.callback_error.empty(),
        "one actual native pool is consumed and callback inputs remain exact");
  Emit(directory, name, output, result);
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "new whole-query wire output directory required");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    for (unsigned int scene = 1; scene <= 7; ++scene) RunScene(directory, scene);
    std::ofstream provenance(directory / "FIXTURE-PROVENANCE.json", std::ios::binary);
    provenance << "{\"schema\":\"commander-target-roll-fixture-provenance-v1\","
                  "\"paused_scope\":\"synthetic\",\"native_getter_callbacks\":\"synthetic\","
                  "\"raw_object_memory\":\"synthetic\",\"row_replacement\":false,"
                  "\"producer\":\"actual reader adapter helper serializer\",\"cases\":7,"
                  "\"runtime_game_execution\":false}\n";
    Check(bool(provenance), "synthetic input boundary accompanies genuine whole-query wires");
    std::cout << "PASS checks=" << checks << " cases=7\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
