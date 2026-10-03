#include "xar_bridge/ck3_12003_commander_mailbox.hpp"
#include "xar_bridge/ck3_12003.hpp"

#include <array>
#include <Windows.h>
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

constexpr unsigned char kSparseFunctionCode[] = {0x40, 0x57, 0xB8, 0xFF, 0xFF, 0x00, 0x00, 0x45, 0x0F, 0xB7, 0xD8, 0x4C, 0x8B, 0xD2, 0x48, 0x8B, 0xF9, 0x66, 0x44, 0x3B, 0xC0, 0x75, 0x0A, 0x33, 0xC0, 0x48, 0x89, 0x02, 0x48, 0x8B, 0xC2, 0x5F, 0xC3, 0x4C, 0x63, 0x49, 0x0C, 0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x8B, 0x19, 0x48, 0x89, 0x74, 0x24, 0x18, 0x4C, 0x8B, 0xC3, 0x48, 0x8B, 0xC3, 0x4A, 0x8D, 0x34, 0x4B, 0x4D, 0x85, 0xC9, 0x7E, 0x21, 0x49, 0x8B, 0xD1, 0x48, 0xD1, 0xEA, 0x4C, 0x2B, 0xCA, 0x66, 0x45, 0x39, 0x1C, 0x50, 0x4B, 0x8D, 0x0C, 0x48, 0x4C, 0x8B, 0xCA, 0x4C, 0x0F, 0x42, 0xC1, 0x49, 0x8B, 0xC0, 0x48, 0x85, 0xD2, 0x75, 0xDF, 0x48, 0x3B, 0xC6, 0x48, 0x8B, 0x74, 0x24, 0x18, 0x74, 0x28, 0x66, 0x44, 0x3B, 0x18, 0x72, 0x22, 0x48, 0x2B, 0xC3, 0x48, 0xD1, 0xF8, 0x85, 0xC0, 0x78, 0x18, 0x48, 0x8B, 0x5C, 0x24, 0x10, 0x48, 0x63, 0xC8, 0x48, 0x8B, 0x47, 0x68, 0x48, 0x8B, 0x04, 0xC8, 0x49, 0x89, 0x02, 0x49, 0x8B, 0xC2, 0x5F, 0xC3, 0x48, 0x8B, 0x5C, 0x24, 0x10, 0x33, 0xC0, 0x49, 0x89, 0x02, 0x49, 0x8B, 0xC2, 0x5F, 0xC3};
using NativeSparseReader = std::int64_t *(*)(void *, std::int64_t *, std::int32_t);
NativeSparseReader native_sparse_reader = nullptr;
std::array<std::array<std::byte, 0xE0>, 2> aggregators{};
std::array<std::array<std::uint16_t, 3>, 2> specific_ids{{{{0x11D, 0x11E, 0x11F}}, {{0x11D, 0x11E, 0x11F}}}};
std::array<std::array<std::uint16_t, 3>, 2> generic_ids{{{{0x11C, 0x11D, 0x11E}}, {{0x11C, 0x11D, 0x11E}}}};
std::array<std::array<std::int64_t, 3>, 2> generic_values{{{{999, 0, 1000}}, {{1999, -10000, 2000}}}};
bool first_container_absent = false;
void *ModifierAggregator(void *candidate) {
  RequireCallback(candidate == active->characters[1].data() || candidate == active->characters[2].data(), "effective aggregator getter receives the actual candidate CCharacter");
  const auto index = candidate == active->characters[1].data() ? 0U : 1U;
  if (index == 0 && first_container_absent) return nullptr;
  return aggregators[index].data();
}
std::int64_t *ReadModifier(void *table, std::int64_t *out, std::int32_t modifier) {
  RequireCallback(modifier == 0x11D && out != nullptr, "native reader uses exact enum0x11D and writable signed raw result");
  RequireCallback(table == aggregators[0].data() + 0x68 || table == aggregators[1].data() + 0x68, "production reader must select generic aggregator+0x68, not the different specific key table");
  if (table != aggregators[0].data() + 0x68 && table != aggregators[1].data() + 0x68) return nullptr;
  return native_sparse_reader(table, out, modifier);
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
    Put(fixture.unit.data(), 0x10, kUnit);
    Put(fixture.unit.data(), 0x174, kPlayer);
    Put(fixture.unit.data(), 0x178, kArmy);
    Put(fixture.army.data(), 0x10, kArmy);
    Put(fixture.army.data(), 0x120, kFirst);
    Put(fixture.army.data(), 0x124, kUnit);
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
    row.army_id = kUnit; row.owner_character_id = kPlayer; row.controllable = true;
    scope.player_armies.push_back(row);

    void *code = VirtualAlloc(nullptr, sizeof(kSparseFunctionCode), MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    Check(code != nullptr, "isolated fixture allocates exact immutable native helper span");
    std::memcpy(code, kSparseFunctionCode, sizeof(kSparseFunctionCode));
    DWORD prior_protection = 0;
    Check(VirtualProtect(code, sizeof(kSparseFunctionCode), PAGE_EXECUTE_READ, &prior_protection) != 0,
          "isolated fixture makes the exact163B sparse helper executable");
    FlushInstructionCache(GetCurrentProcess(), code, sizeof(kSparseFunctionCode));
    native_sparse_reader = reinterpret_cast<NativeSparseReader>(code);
    for (std::size_t index = 0; index < aggregators.size(); ++index) {
      Put(aggregators[index].data(), 0, specific_ids[index].data());
      Put(aggregators[index].data(), 0xC, std::int32_t{3});
      Put(aggregators[index].data(), 0x68, generic_ids[index].data());
      Put(aggregators[index].data(), 0x74, std::int32_t{3});
      Put(aggregators[index].data(), 0xD0, generic_values[index].data());
      // The generic sparse table is exactly the native +0x68/+0x74/+0xD0 layout.
      // Whole-aggregator misuse also fails the explicit receiver check.
    }
    bindings.get_character_modifier_aggregator = ModifierAggregator;
    bindings.read_character_modifier = ReadModifier;
    const auto bound = BindCommanderImage(0x10000000, kExecutableSha256);
    Check(reinterpret_cast<std::uintptr_t>(bound.get_character_modifier_aggregator) == 0x128C3AE0 &&
              reinterpret_cast<std::uintptr_t>(bound.read_character_modifier) == 0x12303700,
          "exact .3 production binder selects the proven aggregator and generic sparse reader RVAs");
    ArmyCommanderCandidatesSnapshot output{};
    auto result = ReadArmyCommanderCandidates(bindings, scope, kUnit, output);
    Check(result == CommanderCandidatesReadResult::available && output.candidates.size() == 2,
          "new modifier read retains full candidate collection");
    Check(output.candidates[0].siege_phase_time_modifier_observable && output.candidates[0].siege_phase_time_modifier_raw == 0 &&
              output.candidates[1].siege_phase_time_modifier_observable && output.candidates[1].siege_phase_time_modifier_raw == -10000,
          "genuine production reader preserves legal zero and signed negative generic phase raw");
    Check(fixture.callback_error.empty(), fixture.callback_error.c_str());
    Emit(std::filesystem::path(argv[1]) / "phase-zero-negative.json", output, result);

    generic_values[0][1] = 10000;
    generic_ids[1][1] = 0x11E;
    generic_ids[1][2] = 0x11F;
    result = ReadArmyCommanderCandidates(bindings, scope, kUnit, output);
    Check(output.candidates[0].siege_phase_time_modifier_observable && output.candidates[0].siege_phase_time_modifier_raw == 10000 &&
              output.candidates[1].siege_phase_time_modifier_observable && output.candidates[1].siege_phase_time_modifier_raw == 0,
          "positive modifier remains signed raw and missing exact sparse key is a legitimate observed zero");
    Check(fixture.callback_error.empty(), fixture.callback_error.c_str());
    Emit(std::filesystem::path(argv[1]) / "phase-positive-missing-key.json", output, result);

    bindings.read_character_modifier = nullptr;
    result = ReadArmyCommanderCandidates(bindings, scope, kUnit, output);
    Check(result == CommanderCandidatesReadResult::available &&
              !output.candidates[0].siege_phase_time_modifier_observable && !output.candidates[1].siege_phase_time_modifier_observable &&
              output.candidates[0].quality_observable && output.candidates[1].quality_observable,
          "optional missing getter yields phase null without losing existing quality or availability");
    Emit(std::filesystem::path(argv[1]) / "phase-read-getter-unavailable.json", output, result);

    bindings.read_character_modifier = ReadModifier;
    first_container_absent = true;
    generic_ids[1][1] = 0x11D;
    generic_ids[1][2] = 0x11E;
    result = ReadArmyCommanderCandidates(bindings, scope, kUnit, output);
    Check(result == CommanderCandidatesReadResult::available && !output.candidates[0].siege_phase_time_modifier_observable &&
              output.candidates[1].siege_phase_time_modifier_observable && output.candidates[1].siege_phase_time_modifier_raw == -10000,
          "unreadable effective container is null and does not contaminate the other real candidate");
    Check(fixture.release_calls == 4 && fixture.allocated == nullptr && fixture.callback_error.empty(),
          "four new production reads retain native caller-owned collection cleanup and exact getter receivers");
    Emit(std::filesystem::path(argv[1]) / "phase-container-unavailable.json", output, result);
    VirtualFree(code, 0, MEM_RELEASE);
    std::cout << "PASS checks=" << checks << " cases=4\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
