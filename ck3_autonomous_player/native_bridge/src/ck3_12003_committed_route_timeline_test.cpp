#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12002_routes.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
using namespace xar;
constexpr std::int32_t kUnit = 0x01000001, kArmy = 0x02000001;
int checks = 0;
void Check(bool value, const char *message) {
  ++checks;
  if (!value) throw std::runtime_error(message);
}
template <class B, class T> void Put(B &bytes, std::size_t at, T value) {
  std::memcpy(bytes.data() + at, &value, sizeof(value));
}
template <class T> T Get(const void *bytes, std::size_t at) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(bytes) + at, sizeof(value));
  return value;
}
struct Fixture {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x150> data{};
  std::array<std::byte, 0x30> units{}, armies{}, regiments{};
  std::array<std::byte, 0x20> unit_slots{}, army_slots{};
  std::array<std::byte, 0x200> unit{};
  std::array<std::byte, 0x190> army{};
  std::array<std::array<std::byte, 0x870>, 3> provinces{};
  std::array<std::array<std::byte, 0xB8>, 3> nodes{};
  std::array<std::array<std::byte, 0x10>, 3> infos{};
  std::array<std::array<std::byte, 0x30>, 3> adjacencies{};
  std::array<void *, 4> province_rows{};
  std::array<void *, 2> route{};
  std::array<std::int64_t, 2> durations{86'868, 1'134'729};
  void *state_ptr = state.data(), *jomini_ptr = jomini.data();
  void *unit_storage = units.data(), *army_storage = armies.data(), *regiment_storage = regiments.data();
  ck3_12002::ArmyBindings armies_binding{};
  ck3_12002::RouteBindings routes_binding{};
  game::Snapshot scope{};
  int duration_calls = 0;
  std::string callback_error;
  Fixture();
};
Fixture *active = nullptr;
std::int32_t State(void *) { return 7; }
std::int32_t Current(void *, std::uint8_t) { return 0; }
std::int32_t Maximum(void *) { return 0; }
std::int64_t *Progress(void *, std::int64_t *out) { *out = 40'000; return out; }
std::int64_t *FirstDuration(void *, std::int64_t *out, std::int32_t) {
  *out = active->durations.front(); return out;
}
std::int64_t *Speed(void *, std::int64_t *out) { *out = 100'000; return out; }
std::int64_t *Duration(void *unit, std::int64_t *out, const void *path, void *origin) {
  const auto count = Get<std::int32_t>(path, 0x0C);
  if (unit != active->unit.data() || origin != active->provinces[0].data() || count < 1 || count > 2)
    active->callback_error = "existing native duration ABI receiver/origin/prefix mismatch";
  ++active->duration_calls;
  *out = active->durations[static_cast<std::size_t>(count - 1)];
  return out;
}
Fixture::Fixture() {
  Put(state, 8, std::int32_t{43'823'104}); Put(state, 0xA0, data.data());
  Put(jomini, 0x20, std::uint8_t{1});
  Put(data, 0x140, province_rows.data()); Put(data, 0x14C, std::int32_t{4});
  for (std::size_t i = 0; i < 3; ++i) {
    const auto id = static_cast<std::int32_t>(i + 1);
    province_rows[i + 1] = provinces[i].data();
    Put(provinces[i], 0x10, id); Put(provinces[i], 0x85C, std::uint32_t{0x50726F76});
    Put(provinces[i], 8, nodes[i].data()); Put(nodes[i], 0xB0, infos[i].data());
    Put(infos[i], 0, id); Put(infos[i], 9, std::uint8_t{1});
    if (i < 2) {
      Put(nodes[i], 0x50, adjacencies[i].data()); Put(nodes[i], 0x5C, std::int32_t{1});
      Put(adjacencies[i], 0, std::int32_t{0}); Put(adjacencies[i], 4, id + 1);
    }
  }
  route = {infos[1].data(), infos[2].data()};
  Put(units, 0x20, unit_slots.data()); Put(units, 0x2C, std::int32_t{2});
  Put(armies, 0x20, army_slots.data()); Put(armies, 0x2C, std::int32_t{2});
  Put(unit_slots, 0x18, unit.data()); Put(army_slots, 0x18, army.data());
  Put(unit, 0x10, kUnit); Put(unit, 0x20, provinces[0].data());
  Put(unit, 0x38, route.data()); Put(unit, 0x40, std::int32_t{2}); Put(unit, 0x44, std::int32_t{2});
  Put(unit, 0x168, std::int64_t{40'000}); Put(unit, 0x174, std::int32_t{29829});
  Put(unit, 0x178, kArmy); Put(unit, 0x190, std::int64_t{100'000});
  Put(army, 0x10, kArmy); Put(army, 0x124, kUnit);
  armies_binding.enabled = true; armies_binding.game_state_slot = &state_ptr;
  armies_binding.unit_storage_slot = &unit_storage; armies_binding.internal_army_storage_slot = &army_storage;
  armies_binding.regiment_storage_slot = &regiment_storage;
  armies_binding.get_unit_state = State; armies_binding.get_army_current_soldiers = Current;
  armies_binding.get_army_maximum_soldiers = Maximum;
  armies_binding.current_movement_progress_enabled = true;
  armies_binding.get_unit_normalized_edge_progress = Progress;
  armies_binding.get_unit_first_route_edge_duration = FirstDuration;
  routes_binding.enabled = true; routes_binding.game_state_slot = &state_ptr;
  routes_binding.jomini_state_slot = &jomini_ptr; routes_binding.army_storage_slot = &unit_storage;
  routes_binding.read_unit_land_route_speed = Speed; routes_binding.read_unit_naval_route_speed = Speed;
  routes_binding.read_unit_current_edge_speed = Speed; routes_binding.read_route_travel_duration = Duration;
  scope.paused = true; scope.date_raw = 43'823'104; scope.has_played_character = true;
  scope.played_character_id = 29829;
  game::ArmySnapshot observed{}; observed.army_id = kUnit; observed.owner_character_id = 29829;
  observed.has_current_province = true; observed.current_province_id = 1; observed.controllable = true;
  scope.player_armies.push_back(observed);
}
std::vector<game::ArmyStrengthSnapshot> Read(Fixture &f) {
  active = &f;
  std::vector<game::ArmyStrengthSnapshot> rows;
  Check(ck3_12002::ReadArmyStrengths(f.armies_binding, f.scope, rows) == game::ReadArmyStrengthsResult::available,
        "production strength reader remains available");
  ck3_12002::AttachCommittedRouteTimelineToArmyRows(f.routes_binding, f.scope, rows);
  Check(rows.size() == 1 && rows[0].current_movement_progress.has_value(), "public CUnit parent binding survives");
  Check(f.callback_error.empty(), f.callback_error.c_str());
  return rows;
}
void Emit(const std::filesystem::path &directory, const char *label, const game::ArmyStrengthSnapshot &row) {
  std::string wire;
  game::AppendArmyStrengthV1(wire, row, [](auto value) { return std::to_string(value); },
    [](std::string &out, const std::vector<std::int32_t> &ids) {
      out += '[';
      for (std::size_t i = 0; i < ids.size(); ++i) { if (i != 0) out += ','; out += std::to_string(ids[i]); }
      out += ']';
    }, [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
  std::ofstream output(directory / (std::string(label) + ".json"));
  output << "{\"army_strengths\":[" << wire << "]}\n";
  Check(output.good(), "real production serialized packet written");
}
void Cases(const std::filesystem::path &directory) {
  Fixture f;
  auto rows = Read(f);
  const auto &timeline = *rows[0].current_movement_progress->committed_route_timeline;
  Check(timeline.status == game::ArmyMovementProgressStatus::available &&
        timeline.committed_route_province_ids == std::vector<std::int32_t>({2,3}) &&
        timeline.native_route_prefix_remaining_days_q100000 == std::vector<std::int64_t>({86'868,1'134'729}) &&
        timeline.native_full_route_remaining_days_q100000 == 1'134'729 &&
        f.duration_calls == 2, "native prefixes are preserved once without subtracting accumulated progress");
  Check(timeline.projected_route_arrival_date_raws.size() == 2 &&
        timeline.projected_route_arrival_date_raws.back() != f.scope.date_raw,
        "rounded dates remain distinct from unrounded native duration");
  Emit(directory, "multi-edge", rows[0]);
  f.durations = {0,0};
  rows = Read(f);
  Check(rows[0].current_movement_progress->committed_route_timeline->native_full_route_remaining_days_q100000 == 0,
        "successful native zero full remainder is preserved");
  Emit(directory, "zero-duration", rows[0]);
  Put(f.unit, 0x40, std::int32_t{0}); Put(f.unit, 0x44, std::int32_t{0});
  const auto prior_calls = f.duration_calls;
  rows = Read(f);
  const auto &empty = *rows[0].current_movement_progress->committed_route_timeline;
  Check(empty.status == game::ArmyMovementProgressStatus::not_applicable &&
        empty.committed_route_province_ids.empty() && empty.native_route_prefix_remaining_days_q100000.empty() &&
        !empty.native_full_route_remaining_days_q100000.has_value() && f.duration_calls == prior_calls,
        "observed empty route retains arrays and null final with no native call");
  Emit(directory, "empty-route", rows[0]);
  Put(f.unit, 0x40, std::int32_t{2}); Put(f.unit, 0x44, std::int32_t{2});
  f.durations = {86'868,0xFFFF'FFFFLL};
  rows = Read(f);
  const auto &missing = *rows[0].current_movement_progress->committed_route_timeline;
  Check(missing.status == game::ArmyMovementProgressStatus::unavailable &&
        missing.committed_route_province_ids.empty() && missing.native_route_prefix_remaining_days_q100000.empty() &&
        missing.projected_route_arrival_date_raws.empty() && !missing.native_full_route_remaining_days_q100000.has_value(),
        "later-prefix native failure clears every prediction instead of publishing a partial route");
  Emit(directory, "unavailable-route", rows[0]);
  f.routes_binding.enabled = false;
  rows = Read(f);
  Check(!rows[0].current_movement_progress->committed_route_timeline.has_value(),
        "disabled older adapter retains previous first-edge contract");
}
} // namespace
int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire output directory required");
    Cases(argv[1]);
    std::cout << "PASS checks=" << checks << " cases=4\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FIXTURE RED: " << error.what() << '\n';
    return 1;
  }
}
