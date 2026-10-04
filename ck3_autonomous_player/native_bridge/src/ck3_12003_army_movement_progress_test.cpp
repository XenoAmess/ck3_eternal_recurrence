#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace xar;
constexpr std::int32_t kUnit = 0x01000001;
constexpr std::int32_t kArmy = 0x02000001;
int checks = 0, cases = 0;

void Check(bool value, const char *label) {
  ++checks;
  if (!value) throw std::runtime_error(label);
}
template <class T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x150> data{};
  std::array<std::byte, 0x30> units{}, armies{}, regiments{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{};
  std::array<std::byte, 0x200> unit{};
  std::array<std::byte, 0x190> army{};
  std::array<std::byte, 0x18> province{};
  std::array<void *, 2> provinces{};
  std::int32_t edge_id = 1;
  std::array<void *, 1> route{};
  void *state_pointer = state.data(), *unit_storage = units.data();
  void *army_storage = armies.data(), *regiment_storage = regiments.data();
  std::int64_t progress_raw = 0, duration_raw = 0;
  std::int32_t unit_state = 7;
  int progress_calls = 0, duration_calls = 0;
  std::string callback_error;
  ck3_12002::ArmyBindings bindings{};
  game::Snapshot scope{};
  Fixture();
};
Fixture *active = nullptr;

void CallbackCheck(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
std::int32_t State(void *unit) {
  CallbackCheck(unit == active->unit.data(), "state getter receiver is public CUnit");
  return active->unit_state;
}
std::int32_t Current(void *regiments, std::uint8_t flags) {
  CallbackCheck(regiments == active->army.data() + 0x38 && flags == 0,
                "strength native sum receives current CArmy regiment array");
  return 0;
}
std::int32_t Maximum(void *army) {
  CallbackCheck(army == active->army.data(), "maximum getter receiver is resolved CArmy");
  return 0;
}
std::int64_t *Progress(void *unit, std::int64_t *output) {
  CallbackCheck(unit == active->unit.data() && output != nullptr,
                "progress getter receiver is public CUnit and writable out-pointer");
  ++active->progress_calls;
  *output = active->progress_raw;
  return output;
}
std::int64_t *Duration(void *unit, std::int64_t *output, std::int32_t route_index) {
  CallbackCheck(unit == active->unit.data() && output != nullptr && route_index == 0,
                "duration getter uses public CUnit and first current route edge");
  ++active->duration_calls;
  *output = active->duration_raw;
  return output;
}

Fixture::Fixture() {
  provinces = {nullptr, province.data()};
  route = {&edge_id};
  Put(state, 0xA0, static_cast<void *>(data.data()));
  Put(data, 0x140, static_cast<void *>(provinces.data()));
  Put(data, 0x14C, std::int32_t{2});
  Put(province, 0x10, std::int32_t{1});
  Put(units, 0x20, static_cast<void *>(unit_slots.data()));
  Put(units, 0x2C, std::int32_t{2});
  Put(armies, 0x20, static_cast<void *>(army_slots.data()));
  Put(armies, 0x2C, std::int32_t{2});
  Put(regiments, 0x2C, std::int32_t{0});
  Put(unit_slots, 0x18, static_cast<void *>(unit.data()));
  Put(army_slots, 0x18, static_cast<void *>(army.data()));
  Put(unit, 0x10, kUnit);
  Put(unit, 0x20, static_cast<void *>(province.data()));
  Put(unit, 0x38, static_cast<void *>(route.data()));
  Put(unit, 0x40, std::int32_t{1});
  Put(unit, 0x44, std::int32_t{1});
  Put(unit, 0x168, std::int64_t{0});
  Put(unit, 0x174, std::int32_t{29829});
  Put(unit, 0x178, kArmy);
  Put(unit, 0x190, std::int64_t{0});
  Put(army, 0x10, kArmy);
  Put(army, 0x124, kUnit);
  bindings.enabled = true;
  bindings.game_state_slot = &state_pointer;
  bindings.unit_storage_slot = &unit_storage;
  bindings.internal_army_storage_slot = &army_storage;
  bindings.regiment_storage_slot = &regiment_storage;
  bindings.get_unit_state = State;
  bindings.get_army_current_soldiers = Current;
  bindings.get_army_maximum_soldiers = Maximum;
  bindings.current_movement_progress_enabled = true;
  bindings.get_unit_normalized_edge_progress = Progress;
  bindings.get_unit_first_route_edge_duration = Duration;
  scope.paused = true;
  scope.has_played_character = true;
  scope.played_character_id = 29829;
  game::ArmySnapshot observed{};
  observed.army_id = kUnit;
  observed.owner_character_id = 29829;
  observed.controllable = true;
  scope.player_armies.push_back(observed);
}

game::ArmyStrengthSnapshot Read(Fixture &fixture) {
  active = &fixture;
  std::vector<game::ArmyStrengthSnapshot> rows;
  Check(ck3_12002::ReadArmyStrengths(fixture.bindings, fixture.scope, rows) ==
            game::ReadArmyStrengthsResult::available && rows.size() == 1,
        "actual production paused scoped army read stays available");
  Check(rows.front().available && rows.front().army_id == kUnit &&
            rows.front().native_carmy_id == kArmy && rows.front().current_soldiers == 0 &&
            rows.front().maximum_soldiers == 0 && rows.front().regiment_count == 0,
        "zero current strength is valid independent of optional movement status");
  Check(fixture.callback_error.empty(), fixture.callback_error.c_str());
  return rows.front();
}

std::string Serialize(const game::ArmyStrengthSnapshot &row) {
  std::string result;
  game::AppendArmyStrengthV1(result, row,
      [](auto value) { return std::to_string(value); },
      [](std::string &output, const std::vector<std::int32_t> &ids) {
        output += '[';
        bool first = true;
        for (auto id : ids) {
          if (!first) output += ',';
          first = false;
          output += std::to_string(id);
        }
        output += ']';
      }, [](std::string &output, std::string_view value) {
        output += '"'; output += value; output += '"';
      });
  return result;
}
void Emit(const std::filesystem::path &directory, const char *name,
          const game::ArmyStrengthSnapshot &row) {
  std::ofstream output(directory / (std::string(name) + ".json"));
  output << "{\"army_strengths\":[" << Serialize(row) << "]}\n";
  Check(output.good(), "genuine production serialized JSON is written");
}

void AvailableGroup(const std::filesystem::path &directory) {
  Fixture fixture;
  auto row = Read(fixture);
  Check(row.current_movement_progress.has_value(), "exact .3 additive block exists");
  const auto &progress = *row.current_movement_progress;
  Check(progress.status == game::ArmyMovementProgressStatus::available &&
            progress.unit_state_raw == 7 && progress.accumulated_movement_weight_raw == 0 &&
            progress.cached_edge_speed_raw == 0 && progress.normalized_edge_progress_raw == 0 &&
            progress.first_route_edge_remaining_duration_raw == 0 && progress.unavailable_reason.empty(),
        "all observed native zeros survive DTO as available without ETA inference");
  Check(fixture.progress_calls == 1 && fixture.duration_calls == 1,
        "two applicable movement callbacks execute exactly once");
  Emit(directory, "movement-progress-zero", row);
  Put(fixture.unit, 0x38, static_cast<void *>(nullptr));
  Put(fixture.unit, 0x40, std::int32_t{0});
  Put(fixture.unit, 0x44, std::int32_t{0});
  row = Read(fixture);
  Check(row.current_movement_progress->status == game::ArmyMovementProgressStatus::not_applicable &&
            !row.current_movement_progress->normalized_edge_progress_raw.has_value() &&
            !row.current_movement_progress->first_route_edge_remaining_duration_raw.has_value() &&
            fixture.progress_calls == 1 && fixture.duration_calls == 1,
        "observed empty route is not applicable and reaches no movement getter");
  fixture.bindings.current_movement_progress_enabled = false;
  row = Read(fixture);
  Check(!row.current_movement_progress.has_value() &&
            Serialize(row).find("current_movement_progress") == std::string::npos,
        "older disabled producer omits the optional block");
  ++cases;
}

void UnavailableGroup(const std::filesystem::path &directory) {
  Fixture fixture;
  fixture.bindings.get_unit_normalized_edge_progress = nullptr;
  fixture.bindings.get_unit_first_route_edge_duration = nullptr;
  auto row = Read(fixture);
  Check(row.current_movement_progress.has_value(), "unavailable movement remains an independent block");
  const auto &progress = *row.current_movement_progress;
  Check(progress.status == game::ArmyMovementProgressStatus::unavailable &&
            progress.unit_state_raw == 7 && progress.accumulated_movement_weight_raw == 0 &&
            progress.cached_edge_speed_raw == 0 && !progress.normalized_edge_progress_raw.has_value() &&
            !progress.first_route_edge_remaining_duration_raw.has_value() &&
            progress.unavailable_reason == "movement_getters_unavailable" &&
            fixture.progress_calls == 0 && fixture.duration_calls == 0,
        "missing native getters retain null while readable context retains zero");
  Emit(directory, "movement-progress-unavailable", row);
  fixture.bindings.get_unit_normalized_edge_progress = Progress;
  fixture.bindings.get_unit_first_route_edge_duration = Duration;
  fixture.duration_raw = 4294967295LL;
  row = Read(fixture);
  Check(row.current_movement_progress->status == game::ArmyMovementProgressStatus::partial &&
            row.current_movement_progress->normalized_edge_progress_raw == 0 &&
            !row.current_movement_progress->first_route_edge_remaining_duration_raw.has_value(),
        "positive duration sentinel 4294967295 becomes null, preserving observed progress zero");
  fixture.progress_raw = 4294967295LL;
  fixture.duration_raw = 0;
  row = Read(fixture);
  Check(row.current_movement_progress->status == game::ArmyMovementProgressStatus::partial &&
            !row.current_movement_progress->normalized_edge_progress_raw.has_value() &&
            row.current_movement_progress->first_route_edge_remaining_duration_raw == 0,
        "positive normalized-progress sentinel becomes null, preserving observed duration zero");
  fixture.progress_raw = 0;
  fixture.duration_raw = -100000;
  row = Read(fixture);
  Check(row.current_movement_progress->status == game::ArmyMovementProgressStatus::available &&
            row.current_movement_progress->first_route_edge_remaining_duration_raw == -100000,
        "a signed negative native duration is retained without clamping");
  ++cases;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire output directory is required");
    const std::filesystem::path directory(argv[1]);
    AvailableGroup(directory);
    UnavailableGroup(directory);
    std::cout << "PASS checks=" << checks << " cases=" << cases << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n';
    return 1;
  }
}
