#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004_commander_mailbox.hpp"

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
constexpr std::int32_t kCurrent = 30000;
constexpr std::int32_t kCandidate = 30001;
constexpr std::int32_t kProvince = 2669;
constexpr std::int32_t kDate = 53236608;
constexpr std::uint64_t kRevision = 11;
constexpr std::uint64_t kSequence = 7;
constexpr std::uintptr_t kSyntheticImageBase = 0x140000000ULL;
enum class Profile { actual4, legacy };
static_assert(xar::ck3_12004::kCommanderLandMovementRateRva12004 == 0x24AA920);
static_assert(xar::ck3_12004::kCommanderNavalMovementRateRva12004 == 0x24AABE0);
static_assert(xar::ck3_12004::kCommanderCurrentEdgeMovementRateRva12004 == 0x24AB5A0);
int checks = 0;

template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof(value));
  return value;
}
void Check(bool value, const char *label) {
  ++checks;
  if (!value) throw std::runtime_error(label);
}

// Only raw object memory, callbacks and the paused scope are synthetic. Each
// scene reads the complete native candidate query; no DTO or wire row is fixed
// up by the fixture. Profile selection is supplied by the sealed public seam.
struct Fixture {
  std::array<std::byte, 0x180> unit{}, army{};
  std::array<std::array<std::byte, 0x210>, 3> characters{};
  std::array<std::byte, 0x30> units{}, armies{}, character_store{};
  std::vector<std::byte> unit_slots = std::vector<std::byte>(288 * 0x10);
  std::vector<std::byte> army_slots = std::vector<std::byte>(147 * 0x10);
  std::vector<std::byte> character_slots = std::vector<std::byte>(30002 * 0x10);
  std::array<std::byte, 0x18> allocator_vtable{};
  std::array<std::byte, 0x08> allocator{};
  std::array<std::byte, 0x70> candidate_aggregator{};
  void *unit_storage = units.data();
  void *army_storage = armies.data();
  void *character_storage = character_store.data();
  void **allocated = nullptr;
  int collect_calls = 0, release_calls = 0, eligibility_calls = 0;
  int quality_calls = 0, advantage_calls = 0, current_calls = 0;
  int skill_calls = 0, land_calls = 0, naval_calls = 0, edge_calls = 0;
  int aggregator_calls = 0, siege_calls = 0;
  std::string callback_error;

  Fixture();
  CommanderBindings InstallSyntheticCallbacks(CommanderBindings bindings);
  xar::game::Snapshot Scope() const;
};
Fixture *active = nullptr;

void RequireCallback(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
void Release(void *allocator, void *data, std::uint64_t alignment) {
  RequireCallback(allocator == active->allocator.data() &&
                  data == active->allocated && alignment == 8,
                  "caller-owned candidate vector retains native allocator");
  delete[] static_cast<void **>(data);
  active->allocated = nullptr;
  ++active->release_calls;
}
void Collect(void *owner, CommanderPointerVector *output,
             bool filter_now, bool allow_guests) {
  RequireCallback(owner == active->characters[0].data() && !filter_now &&
                  allow_guests && output->allocator == active->allocator.data() &&
                  output->data == nullptr && output->count == 0 &&
                  output->capacity == 0,
                  "production pool uses player owner and original arguments");
  active->allocated = new void *[1];
  active->allocated[0] = active->characters[2].data();
  output->data = active->allocated;
  output->count = output->capacity = 1;
  ++active->collect_calls;
}
bool CanAssign(std::int32_t mode, void *candidate, void *army, void *reason) {
  RequireCallback(mode == 1 && candidate == active->characters[2].data() &&
                  army == active->army.data() && reason == nullptr,
                  "manual eligibility uses the actual Army and pool identity");
  ++active->eligibility_calls;
  return true;
}
std::int32_t BaseQuality(void *candidate) {
  RequireCallback(candidate == active->characters[2].data(),
                  "quality observes the candidate identity");
  ++active->quality_calls;
  return 125;
}
std::int32_t GenericAdvantage(void *candidate, std::int32_t context, bool flag) {
  RequireCallback(candidate == active->characters[2].data() && context == -1 &&
                  !flag, "generic advantage retains original native context");
  ++active->advantage_calls;
  return 0;
}
void *CurrentCommander(void *army) {
  RequireCallback(army == active->army.data(),
                  "actual assigned commander getter receives actual Army");
  ++active->current_calls;
  return active->characters[1].data();
}
std::int32_t TotalSkill(void *character, std::int32_t skill_index) {
  RequireCallback(character == active->characters[1].data() && skill_index == 1,
                  "total martial uses actual assigned identity and index1");
  ++active->skill_calls;
  return Get<std::int32_t>(character, 0xDC);
}
std::int64_t *LandRate(void *unit, std::int64_t *output) {
  RequireCallback(unit == active->unit.data(),
                  "land total uses selected public CUnit");
  ++active->land_calls;
  *output = 125000;
  return output;
}
std::int64_t *NavalRate(void *unit, std::int64_t *output) {
  RequireCallback(unit == active->unit.data(),
                  "naval total uses selected public CUnit");
  ++active->naval_calls;
  *output = 250000;
  return output;
}
std::int64_t *EdgeRate(void *unit, std::int64_t *output) {
  RequireCallback(unit == active->unit.data(),
                  "edge total would use selected public CUnit");
  ++active->edge_calls;
  *output = 999000;
  return output;
}
void *ModifierAggregator(void *candidate) {
  RequireCallback(candidate == active->characters[2].data(),
                  "siege modifier observes the pool candidate only");
  ++active->aggregator_calls;
  return active->candidate_aggregator.data();
}
std::int64_t *SiegeModifier(void *table, std::int64_t *output,
                            std::int32_t modifier) {
  RequireCallback(table == active->candidate_aggregator.data() + 0x68 &&
                  modifier == 0x11D, "existing effective siege modifier context");
  ++active->siege_calls;
  *output = 0;
  return output;
}

Fixture::Fixture() {
  Put(unit.data(), 0x10, kUnit);
  Put(unit.data(), 0x174, kPlayer);
  Put(unit.data(), 0x178, kArmy);
  Put(army.data(), 0x10, kArmy);
  Put(army.data(), 0x120, kCurrent);
  Put(army.data(), 0x124, kUnit);
  Put(unit_slots.data(), 287 * 0x10 + 8, unit.data());
  Put(army_slots.data(), 146 * 0x10 + 8, army.data());
  Put(units.data(), 0x20, unit_slots.data());
  Put(units.data(), 0x2C, std::int32_t{288});
  Put(armies.data(), 0x20, army_slots.data());
  Put(armies.data(), 0x2C, std::int32_t{147});
  const std::array<std::int32_t, 3> ids{kPlayer, kCurrent, kCandidate};
  for (std::size_t index = 0; index < ids.size(); ++index) {
    Put(characters[index].data(), 0x18, ids[index]);
    Put(characters[index].data(), 0x1C, std::uint32_t{0x43686172});
    Put(character_slots.data(), static_cast<std::size_t>(ids[index]) * 0x10 + 8,
        characters[index].data());
  }
  Put(characters[1].data(), 0xDC, std::int32_t{17});
  Put(character_store.data(), 0x20, character_slots.data());
  Put(character_store.data(), 0x2C, std::int32_t{30002});
  Put(allocator_vtable.data(), 0x10, &Release);
  Put(allocator.data(), 0, allocator_vtable.data());
}
CommanderBindings Fixture::InstallSyntheticCallbacks(CommanderBindings result) {
  result.armies.unit_storage_slot = &unit_storage;
  result.armies.internal_army_storage_slot = &army_storage;
  result.character_storage_slot = &character_storage;
  result.vector_allocator = allocator.data();
  result.collect_candidates = Collect;
  result.can_set_commander = CanAssign;
  result.get_native_ai_base_quality = BaseQuality;
  result.get_generic_advantage = GenericAdvantage;
  result.get_army_commander = CurrentCommander;
  result.get_character_modifier_aggregator = ModifierAggregator;
  result.read_character_modifier = SiegeModifier;
  result.read_unit_land_movement_rate = LandRate;
  result.read_unit_naval_movement_rate = NavalRate;
  result.read_unit_current_edge_movement_rate = EdgeRate;
  result.get_current_total_skill = TotalSkill;
  return result;
}
xar::game::Snapshot Fixture::Scope() const {
  xar::game::Snapshot result{};
  result.paused = result.map_ready = result.has_played_character =
      result.played_character_alive = true;
  result.played_character_id = kPlayer;
  result.date_raw = kDate;
  xar::game::ArmySnapshot selected{};
  selected.army_id = kUnit;
  selected.owner_character_id = kPlayer;
  selected.controllable = true;
  selected.has_current_province = true;
  selected.current_province_id = kProvince;
  selected.army_state = "stationary";
  selected.route_read_status = xar::game::ArmyRouteReadStatus::complete_empty;
  selected.route_source_count = 0;
  result.player_armies.push_back(selected);
  return result;
}

void ExpectNativeObservation(const Fixture &fixture,
                             const ArmyCommanderCandidatesSnapshot &output,
                             CommanderCandidatesReadResult result) {
  Check(result == CommanderCandidatesReadResult::available &&
        output.army_id == kUnit && output.native_carmy_id == kArmy &&
        output.owner_character_id == kPlayer && output.unavailable_reason.empty(),
        "whole production reader resolves current player CUnit and Army");
  Check(output.current_commander_status == "available" &&
        output.current_commander_character_id == kCurrent &&
        output.current_commander_unavailable_reason.empty() &&
        output.current_total_martial &&
        output.current_total_martial->status == "available" &&
        output.current_total_martial->source_character_id == kCurrent &&
        output.current_total_martial->skill_index == 1 &&
        output.current_total_martial->value == 17,
        "actual assigned role stays independent of player owner and candidate");
  Check(output.candidate_collection_complete && output.candidate_source_count == 1 &&
        output.candidates.size() == 1 && !output.target_province_id,
        "one complete native pool and no target query attachment");
  const auto &row = output.candidates[0];
  Check(row.character_id == kCandidate && row.available && row.can_assign &&
        row.final_eligibility_observable && row.quality_observable &&
        row.native_ai_base_quality == 125 && row.generic_advantage_points == 0 &&
        row.siege_phase_time_modifier_observable &&
        row.siege_phase_time_modifier_raw == 0 && !row.target_roll_bounds,
        "production candidate body retains eligibility quality and observed zero");
  const auto &movement = output.current_movement_speed;
  Check(movement.context_observable && movement.public_cunit_id == kUnit &&
        movement.native_carmy_id == kArmy && movement.owner_character_id == kPlayer &&
        movement.current_commander_character_id == kCurrent &&
        movement.date_raw == kDate && movement.current_province_id == kProvince &&
        movement.land.status == "available" && movement.land.raw == 125000 &&
        movement.naval.status == "available" && movement.naval.raw == 250000 &&
        movement.land.scale == 100000 && movement.naval.scale == 100000 &&
        movement.route_read_status == xar::game::ArmyRouteReadStatus::complete_empty &&
        movement.route_source_count == 0 &&
        movement.current_edge.status == "not_applicable" &&
        !movement.current_edge.raw && movement.current_edge.scale == 100000 &&
        movement.current_edge.unavailable_reason == "empty_route",
        "empty route preserves exact native rate status and unavailable reason");
  Check(fixture.collect_calls == 1 && fixture.release_calls == 1 &&
        fixture.eligibility_calls == 1 && fixture.quality_calls == 1 &&
        fixture.advantage_calls == 1 && fixture.current_calls == 1 &&
        fixture.skill_calls == 1 && fixture.land_calls == 1 &&
        fixture.naval_calls == 1 && fixture.edge_calls == 0 &&
        fixture.aggregator_calls == 1 && fixture.siege_calls == 1 &&
        fixture.allocated == nullptr && fixture.callback_error.empty(),
        "whole production path runs exact callbacks and skips empty-route edge");
}

std::string RunScene(const std::filesystem::path &directory, Profile profile) {
  Fixture fixture{};
  active = &fixture;
  const bool actual4 = profile == Profile::actual4;
  // Binders construct image-relative callback addresses only. None is executed
  // until all object slots and callbacks are replaced by the synthetic family.
  auto bindings = actual4
      ? xar::ck3_12004::BindCommanderImage12004(
            kSyntheticImageBase, xar::ck3_12004::kExecutableSha256)
      : BindCommanderImage(kSyntheticImageBase, xar::ck3_12003::kExecutableSha256);
  Check(bindings.enabled && bindings.armies.enabled &&
        bindings.current_total_martial_observer_enabled,
        "producer-selected native binder enables commander role observation");
  const std::uintptr_t land_rva = actual4
      ? xar::ck3_12004::kCommanderLandMovementRateRva12004 : 0x24AA940;
  const std::uintptr_t naval_rva = actual4
      ? xar::ck3_12004::kCommanderNavalMovementRateRva12004 : 0x24AAC00;
  const std::uintptr_t edge_rva = actual4
      ? xar::ck3_12004::kCommanderCurrentEdgeMovementRateRva12004 : 0x24AB5C0;
  Check(bindings.read_unit_land_movement_rate ==
            reinterpret_cast<CommanderBindings::MovementRateReader>(
                kSyntheticImageBase + land_rva) &&
        bindings.read_unit_naval_movement_rate ==
            reinterpret_cast<CommanderBindings::MovementRateReader>(
                kSyntheticImageBase + naval_rva) &&
        bindings.read_unit_current_edge_movement_rate ==
            reinterpret_cast<CommanderBindings::MovementRateReader>(
                kSyntheticImageBase + edge_rva),
        "native binder selects the exact proof-bound movement getter addresses");
  bindings = fixture.InstallSyntheticCallbacks(bindings);
  const auto unit_before = fixture.unit;
  const auto army_before = fixture.army;
  const auto characters_before = fixture.characters;
  ArmyCommanderCandidatesSnapshot observation{};
  const auto result = ReadArmyCommanderCandidates(
      bindings, fixture.Scope(), kUnit, observation);
  ExpectNativeObservation(fixture, observation, result);
  Check(fixture.unit == unit_before && fixture.army == army_before &&
        fixture.characters == characters_before,
        "whole query leaves the raw game object frame unchanged");
  const std::string step = "query-army-commander-candidates-v1-for-army-" +
      std::to_string(kUnit);
  const std::string serialized = actual4
      ? xar::ck3_12004::SerializeArmyCommanderCandidates12004(
            observation, result, kSequence, kRevision, kDate, step)
      : SerializeArmyCommanderCandidates(
            observation, result, kSequence, kRevision, kDate, step);
  Check(serialized.find(actual4
            ? "\"schema\":\"ck3_12004_army_commander_candidates_v1\""
            : "\"schema\":\"ck3_12003_army_commander_candidates_v1\"") !=
            std::string::npos &&
        serialized.find(actual4
            ? "\"schema\":\"ck3_12004_army_current_movement_speed_v1\""
            : "\"schema\":\"ck3_12003_army_current_movement_speed_v1\"") !=
            std::string::npos,
        "whole production serializer selects exact whole and movement schemas");
  Check(serialized.find(actual4 ? "\"native_getter_rva\":\"0x24AA920\""
                               : "\"native_getter_rva\":\"0x24AA940\"") !=
            std::string::npos &&
        serialized.find(actual4 ? "\"native_getter_rva\":\"0x24AABE0\""
                               : "\"native_getter_rva\":\"0x24AAC00\"") !=
            std::string::npos &&
        serialized.find(actual4 ? "\"native_getter_rva\":\"0x24AB5A0\""
                               : "\"native_getter_rva\":\"0x24AB5C0\"") !=
            std::string::npos,
        "whole production serializer publishes the selected native getter tuple");
  std::ofstream file(directory / (actual4 ? "01-actual4-movement.json"
                                       : "02-legacy-movement.json"),
                     std::ios::binary);
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"ok\":true,\"result\":"
       << serialized << "}\n";
  Check(bool(file), "native whole command_result packet written without row edits");
  active = nullptr;
  return serialized;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "new two-scene wire output directory required");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    const auto actual4 = RunScene(directory, Profile::actual4);
    const auto legacy = RunScene(directory, Profile::legacy);
    Check(actual4 != legacy,
          "producer-selected native metadata distinguishes the two complete packets");
    std::ofstream provenance(directory / "FIXTURE-PROVENANCE.json",
                             std::ios::binary);
    provenance << "{\"schema\":\"commander-movement-metadata-12004-fixture-provenance-v1\","
                  "\"paused_scope\":\"synthetic\",\"raw_object_memory\":\"synthetic\","
                  "\"native_getter_callbacks\":\"synthetic\",\"row_replacement\":false,"
                  "\"producer\":\"genuine selected binder whole native reader production serializer\","
                  "\"actual4_binder\":\"BindCommanderImage12004\","
                  "\"actual4_serializer\":\"SerializeArmyCommanderCandidates12004\","
                  "\"legacy_binder\":\"ck3_12003::BindCommanderImage\","
                  "\"legacy_serializer\":\"ck3_12003::SerializeArmyCommanderCandidates\","
                  "\"cases\":2,\"native_query_occurrences\":2,"
                  "\"runtime_game_execution\":false}\n";
    Check(bool(provenance), "synthetic provenance kept beside native whole packets");
    std::cout << "PASS checks=" << checks
              << " cases=2 native_query_occurrences=2\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
