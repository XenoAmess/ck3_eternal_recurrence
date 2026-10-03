#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12003.hpp"

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
constexpr std::int32_t kOldGeneration = 30002;
constexpr std::int32_t kStale = 0x01007532;
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

struct Fixture {
  std::array<std::byte, 0x180> unit{}, army{};
  std::array<std::array<std::byte, 0x210>, 5> characters{};
  std::array<std::byte, 0x30> units{}, armies{}, character_store{};
  std::vector<std::byte> unit_slots = std::vector<std::byte>(288 * 0x10);
  std::vector<std::byte> army_slots = std::vector<std::byte>(147 * 0x10);
  std::vector<std::byte> character_slots = std::vector<std::byte>(30003 * 0x10);
  std::array<std::byte, 0x18> allocator_vtable{};
  std::array<std::byte, 0x08> allocator{};
  void *unit_storage = units.data();
  void *army_storage = armies.data();
  void *character_storage = character_store.data();
  void **allocated = nullptr;
  bool include_stale = false;
  bool first_eligible = true;
  int collect_calls = 0, release_calls = 0, can_calls = 0;
  int quality_calls = 0, advantage_calls = 0, current_calls = 0;
  std::string callback_error;
};
Fixture *active = nullptr;

void RequireCallback(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
void Release(void *allocator, void *data, std::uint64_t alignment) {
  RequireCallback(allocator == active->allocator.data() && data == active->allocated &&
                      alignment == 8,
                  "native vector released through the selected allocator with alignment 8");
  delete[] static_cast<void **>(data);
  active->allocated = nullptr;
  ++active->release_calls;
}
void Collect(void *owner, CommanderPointerVector *output, bool filter_now, bool allow_guests) {
  RequireCallback(owner == active->characters[0].data() && !filter_now && allow_guests,
                  "collector uses current owner and exact player GUI arguments");
  RequireCallback(output->allocator == active->allocator.data() && output->data == nullptr &&
                      output->count == 0 && output->capacity == 0 && active->allocated == nullptr,
                  "collector receives fresh native caller-owned vector");
  const auto count = active->include_stale ? 3 : 2;
  active->allocated = new void *[static_cast<std::size_t>(count)];
  active->allocated[0] = active->characters[1].data();
  active->allocated[1] = active->characters[2].data();
  if (active->include_stale) active->allocated[2] = active->characters[4].data();
  output->data = active->allocated;
  output->count = count;
  output->capacity = count;
  ++active->collect_calls;
}
bool CanAssign(std::int32_t mode, void *candidate, void *army, void *reason) {
  RequireCallback(mode == 1 && army == active->army.data() && reason == nullptr,
                  "final manual eligibility uses mode 1 and internal CArmy, not public CUnit");
  RequireCallback(candidate == active->characters[1].data() || candidate == active->characters[2].data(),
                  "generation mismatch cannot reach native eligibility");
  ++active->can_calls;
  return Get<std::int32_t>(candidate, 0x18) == kFirst ? active->first_eligible : !active->first_eligible;
}
std::int32_t BaseQuality(void *candidate) {
  RequireCallback(candidate == active->characters[1].data() || candidate == active->characters[2].data(),
                  "generation mismatch cannot reach native base quality");
  ++active->quality_calls;
  return Get<std::int32_t>(candidate, 0x18) == kFirst ? 125 : -17;
}
std::int32_t GenericAdvantage(void *candidate, std::int32_t context, bool flag) {
  RequireCallback(context == -1 && !flag &&
                      (candidate == active->characters[1].data() || candidate == active->characters[2].data()),
                  "generic advantage keeps exact context and separate quality units");
  ++active->advantage_calls;
  return Get<std::int32_t>(candidate, 0x18) == kFirst ? 0 : -9;
}
void *CurrentCommander(void *army) {
  RequireCallback(army == active->army.data(), "current commander getter uses internal army");
  ++active->current_calls;
  return Get<std::int32_t>(army, 0x120) == kFirst ? active->characters[1].data() : nullptr;
}
void Emit(const std::filesystem::path &path, const ArmyCommanderCandidatesSnapshot &output,
          CommanderCandidatesReadResult result) {
  const auto json = SerializeArmyCommanderCandidates(
      output, result, 7, 11, 53236608,
      "query-army-commander-candidates-v1-for-army-" + std::to_string(output.army_id));
  std::ofstream file(path, std::ios::binary);
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"ok\":true,\"result\":"
       << json << "}\n";
  Check(bool(file), "genuine production serializer packet written");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire output directory required");
    Fixture fixture{};
    active = &fixture;
    Put(fixture.unit.data(), 0x10, std::int32_t{0});
    Put(fixture.unit.data(), 0x174, kPlayer);
    Put(fixture.unit.data(), 0x178, kArmy);
    Put(fixture.army.data(), 0x10, kArmy);
    Put(fixture.army.data(), 0x120, std::int32_t{-1});
    Put(fixture.army.data(), 0x124, std::int32_t{0});
    Put(fixture.unit_slots.data(), 8, fixture.unit.data());
    Put(fixture.unit_slots.data(), 287 * 0x10 + 8, fixture.unit.data());
    Put(fixture.army_slots.data(), 146 * 0x10 + 8, fixture.army.data());
    Put(fixture.units.data(), 0x20, fixture.unit_slots.data());
    Put(fixture.units.data(), 0x2C, std::int32_t{288});
    Put(fixture.armies.data(), 0x20, fixture.army_slots.data());
    Put(fixture.armies.data(), 0x2C, std::int32_t{147});
    const std::array<std::int32_t, 5> ids{kPlayer, kFirst, kSecond, kOldGeneration, kStale};
    for (std::size_t index = 0; index < ids.size(); ++index) {
      Put(fixture.characters[index].data(), 0x18, ids[index]);
      Put(fixture.characters[index].data(), 0x1C, std::uint32_t{0x43686172});
      if (index < 4)
        Put(fixture.character_slots.data(), static_cast<std::size_t>(ids[index]) * 0x10 + 8,
            fixture.characters[index].data());
    }
    Put(fixture.character_store.data(), 0x20, fixture.character_slots.data());
    Put(fixture.character_store.data(), 0x2C, std::int32_t{30003});
    Put(fixture.allocator_vtable.data(), 0x10, &Release);
    Put(fixture.allocator.data(), 0, fixture.allocator_vtable.data());
    CommanderBindings bindings{};
    bindings.enabled = bindings.armies.enabled = true;
    bindings.armies.unit_storage_slot = &fixture.unit_storage;
    bindings.armies.internal_army_storage_slot = &fixture.army_storage;
    bindings.character_storage_slot = &fixture.character_storage;
    bindings.vector_allocator = fixture.allocator.data();
    bindings.collect_candidates = Collect;
    bindings.can_set_commander = CanAssign;
    bindings.get_native_ai_base_quality = BaseQuality;
    bindings.get_generic_advantage = GenericAdvantage;
    bindings.get_army_commander = CurrentCommander;
    xar::game::Snapshot scope{};
    scope.paused = scope.map_ready = scope.has_played_character = scope.played_character_alive = true;
    scope.played_character_id = kPlayer;
    xar::game::ArmySnapshot row{};
    row.army_id = 0; row.owner_character_id = kPlayer; row.controllable = true;
    scope.player_armies.push_back(row);
    ArmyCommanderCandidatesSnapshot output{};
    auto result = ReadArmyCommanderCandidates(bindings, scope, 0, output);
    Check(result == CommanderCandidatesReadResult::available &&
              output.army_id == 0 && output.native_carmy_id == kArmy && output.owner_character_id == kPlayer,
          "public CUnit zero is retained and remains distinct from internal CArmy");
    Check(output.current_commander_status == "absent" && output.current_commander_character_id == -1 &&
              output.current_commander_unavailable_reason.empty(),
          "native -1 is legal absence, not unknown");
    Check(output.candidate_collection_complete && output.candidate_source_count == 2 && output.candidates.size() == 2,
          "native GUI candidate collection observed completely");
    Check(output.candidates[0].available && output.candidates[0].can_assign &&
              output.candidates[1].available && !output.candidates[1].can_assign &&
              output.candidates[1].final_eligibility_observable,
          "eligible true and native false are both observed");
    Check(output.candidates[0].quality_observable && output.candidates[0].native_ai_base_quality == 125 &&
              output.candidates[0].generic_advantage_points == 0 &&
              output.candidates[1].native_ai_base_quality == -17 && output.candidates[1].generic_advantage_points == -9,
          "separate native quality and signed advantage preserve observed zero");
    Check(fixture.release_calls == 1 && fixture.allocated == nullptr && fixture.current_calls == 0 &&
              fixture.callback_error.empty(), "first native candidate allocation released exactly once");
    Emit(std::filesystem::path(argv[1]) / "absent-mixed.json", output, result);

    fixture.first_eligible = false;
    Put(fixture.unit.data(), 0x10, kUnit);
    Put(fixture.army.data(), 0x124, kUnit);
    scope.player_armies.front().army_id = kUnit;
    Put(fixture.army.data(), 0x120, kFirst);
    result = ReadArmyCommanderCandidates(bindings, scope, kUnit, output);
    Check(result == CommanderCandidatesReadResult::available &&
              output.current_commander_status == "available" && output.current_commander_character_id == kFirst,
          "current native getter and full character identity agree");
    Check(output.candidates[0].available && !output.candidates[0].can_assign &&
              output.candidates[0].final_eligibility_observable && output.candidates[1].can_assign,
          "current commander final false is not replaced by current membership");
    Check(fixture.release_calls == 2 && fixture.allocated == nullptr && fixture.current_calls == 1 &&
              fixture.callback_error.empty(), "second native allocation and current getter observed");
    Emit(std::filesystem::path(argv[1]) / "present-current-ineligible.json", output, result);

    fixture.include_stale = true;
    result = ReadArmyCommanderCandidates(bindings, scope, kUnit, output);
    Check(result == CommanderCandidatesReadResult::partial && output.candidate_collection_complete &&
              output.candidate_source_count == 3 && output.candidates.size() == 3,
          "unresolved generation yields partial rows, not an empty observed collection");
    Check(output.candidates[0].available && output.candidates[1].available &&
              output.candidates[2].character_id == kStale && !output.candidates[2].available &&
              !output.candidates[2].final_eligibility_observable && !output.candidates[2].quality_observable &&
              output.candidates[2].unavailable_reason == "candidate_identity_unavailable",
          "raw stale full ID retained without publishing eligibility or quality");
    Check(fixture.collect_calls == 3 && fixture.release_calls == 3 && fixture.allocated == nullptr &&
              fixture.can_calls == 6 && fixture.quality_calls == 6 && fixture.advantage_calls == 6 &&
              fixture.current_calls == 2 && fixture.callback_error.empty(),
          "only two valid candidates reach native calls per read and all vector allocations are freed");
    Emit(std::filesystem::path(argv[1]) / "partial-generation.json", output, result);
    std::cout << "PASS checks=" << checks << " cases=3\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
