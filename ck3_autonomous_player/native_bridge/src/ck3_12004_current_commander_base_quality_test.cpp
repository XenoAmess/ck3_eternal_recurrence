#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/ck3_12004_army_support.hpp"
#include "xar_bridge/ck3_12004_commander_mailbox.hpp"
#include "xar_bridge/ck3_12004_current_commander_base_quality.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
using namespace xar::ck3_12003;
constexpr std::int32_t kPlayer = 29829;
constexpr std::int32_t kUnit = 83886367;
constexpr std::int32_t kArmy = 50331794;
constexpr std::int32_t kCurrent = 30000;
constexpr std::int32_t kCandidateA = 30001;
constexpr std::int32_t kCandidateB = 30002;
constexpr std::int32_t kProvince = 2669;
constexpr std::int32_t kDate = 53288448;
constexpr std::uint64_t kRevision = 11;
constexpr std::uint64_t kSequence = 7;
constexpr std::uintptr_t kSyntheticImageBase = 0x140000000ULL;
constexpr std::string_view kSource =
    "native_current_assigned_commander_ai_base_quality";
enum class Scene { outside_pool, zero, unavailable, comparison };
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

// Synthetic raw storage, callbacks and paused frame enter the real binder,
// whole Army reader and production serializer. No DTO/result row is repaired.
struct Fixture {
  explicit Fixture(Scene selected);
  CommanderBindings InstallCallbacks(CommanderBindings result);
  xar::game::Snapshot Scope() const;
  std::size_t CharacterIndex(const void *character) const;
  bool InPool(const void *character) const;

  Scene scene;
  std::array<std::byte, 0x180> unit{}, army{};
  std::array<std::array<std::byte, 0x210>, 4> characters{};
  std::array<std::byte, 0x30> units{}, armies{}, character_store{};
  std::vector<std::byte> unit_slots = std::vector<std::byte>(288 * 0x10);
  std::vector<std::byte> army_slots = std::vector<std::byte>(147 * 0x10);
  std::vector<std::byte> character_slots = std::vector<std::byte>(30003 * 0x10);
  std::array<std::byte, 0x18> allocator_vtable{};
  std::array<std::byte, 0x08> allocator{};
  std::array<std::array<std::byte, 0x70>, 4> aggregators{};
  std::array<std::size_t, 2> pool{};
  void *unit_storage = units.data();
  void *army_storage = armies.data();
  void *character_storage = character_store.data();
  void **allocated = nullptr;
  int collect_calls = 0, release_calls = 0, eligibility_calls = 0;
  int advantage_calls = 0, current_calls = 0, skill_calls = 0;
  int land_calls = 0, naval_calls = 0, edge_calls = 0;
  int aggregator_calls = 0, siege_calls = 0;
  std::vector<std::int32_t> quality_receiver_ids;
  std::string callback_error;
};
Fixture *active = nullptr;

void Require(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
std::size_t Fixture::CharacterIndex(const void *character) const {
  for (std::size_t index = 0; index < characters.size(); ++index)
    if (character == characters[index].data()) return index;
  return characters.size();
}
bool Fixture::InPool(const void *character) const {
  return character == characters[pool[0]].data() ||
         character == characters[pool[1]].data();
}
void Release(void *allocator, void *data, std::uint64_t alignment) {
  Require(allocator == active->allocator.data() && data == active->allocated &&
              alignment == 8,
          "production pool allocator release keeps its receiver and alignment");
  delete[] static_cast<void **>(data);
  active->allocated = nullptr;
  ++active->release_calls;
}
void Collect(void *owner, CommanderPointerVector *output,
             bool filter_now, bool allow_guests) {
  Require(owner == active->characters[0].data() && !filter_now && allow_guests &&
              output->allocator == active->allocator.data() &&
              output->data == nullptr && output->count == 0 &&
              output->capacity == 0,
          "real collector requests the existing player pool");
  active->allocated = new void *[2];
  for (std::size_t index = 0; index < active->pool.size(); ++index)
    active->allocated[index] = active->characters[active->pool[index]].data();
  output->data = active->allocated;
  output->count = output->capacity = 2;
  ++active->collect_calls;
}
bool CanAssign(std::int32_t mode, void *candidate, void *army, void *reason) {
  Require(mode == 1 && active->InPool(candidate) &&
              army == active->army.data() && reason == nullptr,
          "candidate final eligibility remains player mode1 for actual Army");
  ++active->eligibility_calls;
  return candidate != active->characters[1].data();
}
std::int32_t BaseQuality(void *character) {
  const auto index = active->CharacterIndex(character);
  Require(index >= 1 && index < active->characters.size(),
          "quality uses a resolved current or pool Character receiver");
  if (index >= active->characters.size()) return 0;
  active->quality_receiver_ids.push_back(Get<std::int32_t>(character, 0x18));
  if (index == 1) return active->scene == Scene::zero ? 0 : 37;
  return index == 2 ? 25 : 15;
}
std::int32_t GenericAdvantage(void *candidate, std::int32_t context, bool flag) {
  Require(active->InPool(candidate) && context == -1 && !flag,
          "existing generic advantage is read for independent pool rows only");
  ++active->advantage_calls;
  const auto index = active->CharacterIndex(candidate);
  return index == 1 ? 9 : index == 2 ? 7 : 2;
}
void *CurrentCommander(void *army) {
  Require(army == active->army.data(),
          "GetArmyCommander receives the raw actual internal Army");
  ++active->current_calls;
  return active->scene == Scene::unavailable
      ? nullptr : active->characters[1].data();
}
std::int32_t TotalSkill(void *character, std::int32_t skill_index) {
  Require(character == active->characters[1].data() && skill_index == 1,
          "existing martial remains actual assigned current receiver/index1");
  ++active->skill_calls;
  return Get<std::int32_t>(character, 0xDC);
}
std::int64_t *LandRate(void *unit, std::int64_t *output) {
  Require(unit == active->unit.data(), "land getter keeps public Unit receiver");
  ++active->land_calls;
  *output = 125000;
  return output;
}
std::int64_t *NavalRate(void *unit, std::int64_t *output) {
  Require(unit == active->unit.data(), "naval getter keeps public Unit receiver");
  ++active->naval_calls;
  *output = 250000;
  return output;
}
std::int64_t *EdgeRate(void *unit, std::int64_t *output) {
  Require(unit == active->unit.data(), "edge getter keeps public Unit receiver");
  ++active->edge_calls;
  *output = 999000;
  return output;
}
void *ModifierAggregator(void *candidate) {
  Require(active->InPool(candidate), "siege modifier retains candidate scope");
  ++active->aggregator_calls;
  const auto index = active->CharacterIndex(candidate);
  return index < active->aggregators.size()
      ? active->aggregators[index].data() : nullptr;
}
std::int64_t *SiegeModifier(void *table, std::int64_t *output,
                            std::int32_t modifier) {
  Require(modifier == 0x11D, "existing siege modifier ordinal is unchanged");
  std::size_t index = 0;
  for (; index < active->aggregators.size(); ++index)
    if (table == active->aggregators[index].data() + 0x68) break;
  Require(index < active->aggregators.size(),
          "siege modifier table belongs to its actual pool receiver");
  ++active->siege_calls;
  *output = index == 3 ? -10000 : 0;
  return output;
}

Fixture::Fixture(Scene selected) : scene(selected) {
  pool = scene == Scene::comparison ? std::array<std::size_t, 2>{1, 2}
                                    : std::array<std::size_t, 2>{2, 3};
  Put(unit.data(), 0x10, kUnit);
  Put(unit.data(), 0x170, std::int32_t{0});
  Put(unit.data(), 0x174, kPlayer);
  Put(unit.data(), 0x178, kArmy);
  Put(army.data(), 0x10, kArmy);
  Put(army.data(), 0x120, kCurrent);
  Put(army.data(), 0x124, kUnit);
  Put(army.data(), 0x128, std::int32_t{-1});
  Put(unit_slots.data(), 287 * 0x10 + 8, unit.data());
  Put(army_slots.data(), 146 * 0x10 + 8, army.data());
  Put(units.data(), 0x20, unit_slots.data());
  Put(units.data(), 0x2C, std::int32_t{288});
  Put(armies.data(), 0x20, army_slots.data());
  Put(armies.data(), 0x2C, std::int32_t{147});
  const std::array<std::int32_t, 4> ids{
      kPlayer, kCurrent, kCandidateA, kCandidateB};
  for (std::size_t index = 0; index < ids.size(); ++index) {
    Put(characters[index].data(), 0x18, ids[index]);
    Put(characters[index].data(), 0x1C, std::uint32_t{0x43686172});
    Put(character_slots.data(), static_cast<std::size_t>(ids[index]) * 0x10 + 8,
        characters[index].data());
  }
  Put(characters[1].data(), 0xDC, std::int32_t{17});
  Put(character_store.data(), 0x20, character_slots.data());
  Put(character_store.data(), 0x2C, std::int32_t{30003});
  Put(allocator_vtable.data(), 0x10, &Release);
  Put(allocator.data(), 0, allocator_vtable.data());
}
CommanderBindings Fixture::InstallCallbacks(CommanderBindings result) {
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
  xar::game::Snapshot scope{};
  scope.paused = scope.map_ready = scope.has_played_character =
      scope.played_character_alive = true;
  scope.played_character_id = kPlayer;
  scope.date_raw = kDate;
  xar::game::ArmySnapshot selected{};
  selected.army_id = kUnit;
  selected.owner_character_id = kPlayer;
  selected.controllable = true;
  selected.has_current_province = true;
  selected.current_province_id = kProvince;
  selected.army_state = "stationary";
  selected.route_read_status = xar::game::ArmyRouteReadStatus::complete_empty;
  selected.route_source_count = 0;
  scope.player_armies.push_back(selected);
  return scope;
}

void Expect(const Fixture &fixture,
            const ArmyCommanderCandidatesSnapshot &out,
            CommanderCandidatesReadResult result) {
  const bool unavailable = fixture.scene == Scene::unavailable;
  Check(result == (unavailable ? CommanderCandidatesReadResult::partial
                               : CommanderCandidatesReadResult::available) &&
            out.army_id == kUnit && out.native_carmy_id == kArmy &&
            out.owner_character_id == kPlayer &&
            out.current_commander_character_id == kCurrent,
        "whole reader keeps full public/internal/current/owner identity distinct");
  Check(out.current_commander_status == (unavailable ? "unavailable" : "available"),
        "actual current helper agreement determines current role availability");
  Check(out.current_native_ai_base_quality.has_value(),
        "actual4 observer emits the new independent current quality leaf");
  const auto &quality = *out.current_native_ai_base_quality;
  Check(quality.source == kSource && quality.source_character_id == kCurrent,
        "new quality binds the actual Army role source identity");
  if (unavailable) {
    Check(quality.status == "unavailable" && !quality.value &&
              quality.unavailable_reason == "current_commander_identity_unavailable" &&
              out.current_commander_unavailable_reason ==
                  "current_commander_identity_unavailable",
          "failed current helper cannot become a legal zero or candidate substitute");
    Check(out.current_total_martial &&
              out.current_total_martial->status == "unavailable" &&
              !out.current_total_martial->value &&
              out.current_total_martial->source_character_id == kCurrent,
          "existing current martial failure stays bound to that role");
  } else {
    Check(quality.status == "available" &&
              quality.value == (fixture.scene == Scene::zero ? 0 : 37) &&
              quality.unavailable_reason.empty(),
          "raw current quality including legitimate zero is published");
    Check(out.current_total_martial &&
              out.current_total_martial->status == "available" &&
              out.current_total_martial->source_character_id == kCurrent &&
              out.current_total_martial->skill_index == 1 &&
              out.current_total_martial->value == 17,
          "native quality is independent of the adopted total martial input");
  }
  Check(out.candidate_collection_complete && out.candidate_source_count == 2 &&
            out.candidates.size() == 2 && !out.target_province_id,
        "new leaf does not replace the real native candidate pool");
  for (std::size_t index = 0; index < fixture.pool.size(); ++index) {
    const auto character_index = fixture.pool[index];
    const auto &row = out.candidates[index];
    const auto id = Get<std::int32_t>(
        fixture.characters[character_index].data(), 0x18);
    const std::int32_t expected_quality = character_index == 1 ? 37
        : character_index == 2 ? 25 : 15;
    const std::int32_t expected_advantage = character_index == 1 ? 9
        : character_index == 2 ? 7 : 2;
    Check(row.character_id == id && row.available &&
              row.final_eligibility_observable &&
              row.can_assign == (character_index != 1) && row.quality_observable &&
              row.native_ai_base_quality == expected_quality &&
              row.generic_advantage_points == expected_advantage &&
              row.siege_phase_time_modifier_observable &&
              row.siege_phase_time_modifier_raw == (character_index == 3 ? -10000 : 0) &&
              !row.target_roll_bounds,
          "whole candidate row keeps its own eligibility quality and generic inputs");
  }
  const auto &movement = out.current_movement_speed;
  Check(movement.context_observable && movement.public_cunit_id == kUnit &&
            movement.native_carmy_id == kArmy &&
            movement.owner_character_id == kPlayer &&
            movement.current_commander_character_id == kCurrent &&
            movement.date_raw == kDate && movement.current_province_id == kProvince &&
            movement.land.status == "available" && movement.land.raw == 125000 &&
            movement.naval.status == "available" && movement.naval.raw == 250000 &&
            movement.current_edge.status == "not_applicable" &&
            !movement.current_edge.raw &&
            movement.current_edge.unavailable_reason == "empty_route",
        "new quality leaves complete old movement fields intact");
  const std::vector<std::int32_t> receivers = unavailable
      ? std::vector<std::int32_t>{kCandidateA, kCandidateB}
      : fixture.scene == Scene::comparison
          ? std::vector<std::int32_t>{kCurrent, kCurrent, kCandidateA}
          : std::vector<std::int32_t>{kCurrent, kCandidateA, kCandidateB};
  Check(fixture.quality_receiver_ids == receivers &&
            fixture.collect_calls == 1 && fixture.release_calls == 1 &&
            fixture.eligibility_calls == 2 && fixture.advantage_calls == 2 &&
            fixture.current_calls == 1 && fixture.skill_calls == (unavailable ? 0 : 1) &&
            fixture.land_calls == 1 && fixture.naval_calls == 1 &&
            fixture.edge_calls == 0 && fixture.aggregator_calls == 2 &&
            fixture.siege_calls == 2 && fixture.allocated == nullptr &&
            fixture.callback_error.empty(),
        "new quality adds only the validated current receiver callback");
}

void RunScene(const std::filesystem::path &directory, Scene scene,
              std::string_view filename) {
  Fixture fixture(scene);
  active = &fixture;
  // The binder constructs exact actual4 image-relative addresses. Every slot
  // and callback used by the subsequent read is replaced before any call.
  auto bindings = xar::ck3_12004::BindCommanderImage12004(
      kSyntheticImageBase, xar::ck3_12004::kExecutableSha256);
  Check(bindings.enabled && bindings.armies.enabled &&
            bindings.current_total_martial_observer_enabled &&
            bindings.current_native_ai_base_quality_observer_enabled &&
            bindings.get_native_ai_base_quality ==
                reinterpret_cast<decltype(bindings.get_native_ai_base_quality)>(
                    kSyntheticImageBase + 0x2C0B250),
        "genuine actual4 binder supplies existing proof-bound quality callback");
  bindings = fixture.InstallCallbacks(bindings);
  const auto unit_before = fixture.unit;
  const auto army_before = fixture.army;
  const auto characters_before = fixture.characters;
  ArmyCommanderCandidatesSnapshot observation{};
  const auto result = ReadArmyCommanderCandidates(
      bindings, fixture.Scope(), kUnit, observation);
  Expect(fixture, observation, result);
  Check(fixture.unit == unit_before && fixture.army == army_before &&
            fixture.characters == characters_before,
        "readonly whole reader preserves its synthetic raw object frame");
  const auto step = "query-army-commander-candidates-v1-for-army-" +
      std::to_string(kUnit);
  const auto serialized = xar::ck3_12004::SerializeArmyCommanderCandidates12004(
      observation, result, kSequence, kRevision, kDate, step);
  Check(serialized.find("\"schema\":\"ck3_12004_army_commander_candidates_v1\"") !=
            std::string::npos &&
            serialized.find("\"current_native_ai_base_quality\":") !=
                std::string::npos,
        "complete native actual4 serializer owns the new current leaf body");
  std::ofstream file(directory / std::string(filename), std::ios::binary);
  // The original protocol envelope encloses the complete production result.
  // No result keys, candidate rows or role leaf are authored as wire substitutes.
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"ok\":true,\"result\":"
       << serialized << "}\n";
  Check(bool(file), "complete original native command_result packet is written");
  active = nullptr;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "producer requires one positional output directory");
    const std::filesystem::path directory(argv[1]);
    std::filesystem::create_directories(directory);
    RunScene(directory, Scene::outside_pool, "quality-current-outside-pool.json");
    RunScene(directory, Scene::zero, "quality-current-zero.json");
    RunScene(directory, Scene::unavailable, "quality-current-unavailable.json");
    RunScene(directory, Scene::comparison, "quality-candidate-comparison.json");
    std::ofstream provenance(directory / "FIXTURE-PROVENANCE.json", std::ios::binary);
    provenance << "{\"schema\":\"current-commander-native-base-quality-12004-fixture-provenance-v1\","
                  "\"source_base\":\"2a9eadce8f96c886aa62759c1a001658413f49f4\","
                  "\"quality_source\":\"native_current_assigned_commander_ai_base_quality\","
                  "\"actual4_callback_rva\":\"0x2C0B250\","
                  "\"binder\":\"BindCommanderImage12004\","
                  "\"reader\":\"ReadArmyCommanderCandidates\","
                  "\"serializer\":\"SerializeArmyCommanderCandidates12004\","
                  "\"paused_scope\":\"synthetic\",\"raw_storage\":\"synthetic\","
                  "\"getter_callbacks\":\"synthetic\",\"row_replacement\":false,"
                  "\"game_function_body_execution\":false,\"game_sdk_execution\":false,"
                  "\"public_cunit_id\":83886367,\"native_carmy_id\":50331794,"
                  "\"owner_character_id\":29829,\"current_character_id\":30000,"
                  "\"snapshot_revision\":11,\"date_raw\":53288448,\"query_sequence\":7,"
                  "\"cases\":4,\"whole_native_packets\":4,"
                  "\"quality_receivers\":[[30000,30001,30002],[30000,30001,30002],"
                  "[30001,30002],[30000,30000,30001]]}\n";
    Check(bool(provenance), "raw frame and callback receiver provenance is preserved");
    std::cout << "PASS checks=" << checks << " cases=4 whole_native_packets=4\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
