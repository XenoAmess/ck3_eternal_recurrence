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
constexpr std::int32_t kDate = 53236608;
int checks = 0, cases = 0;

void Check(bool value, const char *label) {
  ++checks;
  if (!value) throw std::runtime_error(label);
}
template <class T> void Put(void *object, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}

struct Fixture {
  std::array<std::byte, 0x180> unit{}, army{};
  std::array<std::byte, 0x210> owner{};
  std::array<std::byte, 0x30> units{}, armies{}, characters{};
  std::vector<std::byte> unit_slots = std::vector<std::byte>(288 * 0x10);
  std::vector<std::byte> army_slots = std::vector<std::byte>(147 * 0x10);
  std::vector<std::byte> character_slots = std::vector<std::byte>(29830 * 0x10);
  std::array<std::byte, 0x18> allocator_vtable{};
  std::array<std::byte, 0x08> allocator{};
  void *unit_storage = units.data(), *army_storage = armies.data();
  void *character_storage = characters.data();
  std::array<std::int64_t, 3> raw{1234567, 9876543, 321000};
  std::array<int, 3> behavior{0, 0, 0}, calls{0, 0, 0};
  std::int64_t other_output = 777;
  int collect_calls = 0;
  std::string callback_error;
  CommanderBindings bindings{};
  xar::game::Snapshot scope{};
  Fixture();
};
Fixture *active = nullptr;

void RequireCallback(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
void Release(void *, void *, std::uint64_t) {
  RequireCallback(false, "empty speed-only collection must not allocate or release");
}
void Collect(void *owner, CommanderPointerVector *output, bool filter, bool guests) {
  RequireCallback(owner == active->owner.data() && !filter && guests,
                  "production collection still receives resolved current player owner");
  RequireCallback(output->data == nullptr && output->count == 0 &&
                      output->capacity == 0 && output->allocator == active->allocator.data(),
                  "focused fixture retains an empty native candidate collection");
  ++active->collect_calls;
}
bool CanAssign(std::int32_t, void *, void *, void *) { return false; }
std::int32_t Quality(void *) { return 0; }
std::int32_t Advantage(void *, std::int32_t, bool) { return 0; }
void *Commander(void *) { return nullptr; }

std::int64_t *Rate(void *unit, std::int64_t *output, std::size_t index) {
  RequireCallback(unit == active->unit.data() && unit != active->army.data(),
                  "native rate RCX is the selected public CUnit, not internal CArmy");
  RequireCallback(output != nullptr && output != &active->other_output,
                  "native rate RDX is a caller-owned writable output");
  ++active->calls[index];
  *output = active->raw[index];
  if (active->behavior[index] == 1) return nullptr;
  if (active->behavior[index] == 2) return &active->other_output;
  return output;
}
std::int64_t *Land(void *unit, std::int64_t *output) { return Rate(unit, output, 0); }
std::int64_t *Naval(void *unit, std::int64_t *output) { return Rate(unit, output, 1); }
std::int64_t *Edge(void *unit, std::int64_t *output) { return Rate(unit, output, 2); }

Fixture::Fixture() {
  Put(unit.data(), 0x10, kUnit);
  Put(unit.data(), 0x174, kPlayer);
  Put(unit.data(), 0x178, kArmy);
  Put(army.data(), 0x10, kArmy);
  Put(army.data(), 0x120, std::int32_t{-1});
  Put(army.data(), 0x124, kUnit);
  Put(owner.data(), 0x18, kPlayer);
  Put(owner.data(), 0x1C, std::uint32_t{0x43686172});
  Put(unit_slots.data(), 8, unit.data());
  Put(unit_slots.data(), 287 * 0x10 + 8, unit.data());
  Put(army_slots.data(), 146 * 0x10 + 8, army.data());
  Put(character_slots.data(), kPlayer * 0x10 + 8, owner.data());
  Put(units.data(), 0x20, unit_slots.data());
  Put(units.data(), 0x2C, std::int32_t{288});
  Put(armies.data(), 0x20, army_slots.data());
  Put(armies.data(), 0x2C, std::int32_t{147});
  Put(characters.data(), 0x20, character_slots.data());
  Put(characters.data(), 0x2C, std::int32_t{29830});
  Put(allocator_vtable.data(), 0x10, &Release);
  Put(allocator.data(), 0, allocator_vtable.data());
  bindings.enabled = bindings.armies.enabled = true;
  bindings.armies.unit_storage_slot = &unit_storage;
  bindings.armies.internal_army_storage_slot = &army_storage;
  bindings.character_storage_slot = &character_storage;
  bindings.vector_allocator = allocator.data();
  bindings.collect_candidates = Collect;
  bindings.can_set_commander = CanAssign;
  bindings.get_native_ai_base_quality = Quality;
  bindings.get_generic_advantage = Advantage;
  bindings.get_army_commander = Commander;
  bindings.read_unit_land_movement_rate = Land;
  bindings.read_unit_naval_movement_rate = Naval;
  bindings.read_unit_current_edge_movement_rate = Edge;
  scope.date_raw = kDate;
  scope.paused = scope.map_ready = scope.has_played_character = scope.played_character_alive = true;
  scope.played_character_id = kPlayer;
  xar::game::ArmySnapshot row{};
  row.army_id = kUnit; row.owner_character_id = kPlayer; row.controllable = true;
  row.has_current_province = true; row.current_province_id = 2614;
  row.move_target_observable = true; row.move_target_province_id = 2610;
  row.route_read_status = xar::game::ArmyRouteReadStatus::complete_nonempty;
  row.route_source_count = 1; row.route_province_ids = {2610};
  row.army_state_code = 7; row.army_state = "moving";
  scope.player_armies.push_back(row);
}

std::array<const NativeMovementRateSnapshot *, 3> Rates(
    const ArmyCommanderCandidatesSnapshot &output) {
  const auto &speed = output.current_movement_speed;
  return {&speed.land, &speed.naval, &speed.current_edge};
}

void Emit(const std::filesystem::path &directory, const std::string &name,
          const ArmyCommanderCandidatesSnapshot &output,
          CommanderCandidatesReadResult result) {
  const auto packet = SerializeArmyCommanderCandidates(
      output, result, 7, 11, kDate,
      "query-army-commander-candidates-v1-for-army-" + std::to_string(output.army_id));
  std::ofstream file(directory / (name + ".json"), std::ios::binary);
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"ok\":true,\"result\":"
       << packet << "}\n";
  Check(bool(file), "production speed serializer packet was written");
  ++cases;
}

void RunAvailable(const std::filesystem::path &directory, const std::string &name,
                  Fixture &fixture,
                  const std::array<std::string_view, 3> &statuses,
                  const std::array<int, 3> &calls) {
  active = &fixture;
  ArmyCommanderCandidatesSnapshot output{};
  const auto id = fixture.scope.player_armies.front().army_id;
  const auto result = ReadArmyCommanderCandidates(fixture.bindings, fixture.scope, id, output);
  Check(result == CommanderCandidatesReadResult::available,
        "optional speed reads do not destroy existing commander query availability");
  const auto &speed = output.current_movement_speed;
  Check(speed.context_observable && speed.public_cunit_id == id &&
            speed.native_carmy_id == kArmy && speed.owner_character_id == kPlayer &&
            speed.date_raw == kDate,
        "movement context preserves selected public/internal full IDs, owner and paused date");
  Check(speed.current_province_id == 2614 && speed.army_state_code == 7 &&
            speed.army_state == "moving" && !speed.in_combat && !speed.retreating,
        "movement context copies current selected paused army state");
  Check(speed.current_commander_character_id == -1 &&
            speed.route_read_status == fixture.scope.player_armies.front().route_read_status &&
            speed.route_source_count == fixture.scope.player_armies.front().route_source_count &&
            speed.move_target_province_id ==
                (fixture.scope.player_armies.front().move_target_observable
                     ? std::optional<std::int32_t>(fixture.scope.player_armies.front().move_target_province_id)
                     : std::nullopt),
        "selected commander absence, route status, count and optional target are retained");
  const auto rates = Rates(output);
  for (std::size_t index = 0; index < rates.size(); ++index) {
    Check(rates[index]->status == statuses[index] && rates[index]->scale == 100000,
          "each native rate keeps independent status and Q100000 scale");
    Check(statuses[index] == "available"
              ? rates[index]->raw == fixture.raw[index]
              : !rates[index]->raw.has_value(),
          "only a successful exact out-pointer return publishes raw, including zero");
    const std::string_view reason = statuses[index] == "available" ? "" :
        statuses[index] == "not_applicable" ? "empty_route" :
        name == "speed-unresolved-route" ? "stored_route_unavailable" :
        name.starts_with("speed-missing-") ? "native_rate_callback_unavailable" :
        "native_rate_read_failed";
    Check(rates[index]->unavailable_reason == reason,
          "independent rate failure and empty-route reasons survive the production reader");
  }
  Check(fixture.calls == calls && fixture.collect_calls == 1,
        "only applicable bound callbacks execute once without extra candidate work");
  Check(fixture.callback_error.empty(), fixture.callback_error.c_str());
  Emit(directory, name, output, result);
}

void RunUnavailable(const std::filesystem::path &directory, const std::string &name,
                    Fixture &fixture, std::string_view reason) {
  active = &fixture;
  ArmyCommanderCandidatesSnapshot output{};
  const auto result = ReadArmyCommanderCandidates(
      fixture.bindings, fixture.scope, fixture.scope.player_armies.front().army_id, output);
  Check(result == CommanderCandidatesReadResult::unavailable && output.unavailable_reason == reason,
        "production reader retains existing exact-build/full-ID/current-player prerequisite");
  Check(!output.current_movement_speed.context_observable,
        "failed current-player identity does not become an observed movement context");
  for (const auto *rate : Rates(output))
    Check(rate->status == "unavailable" && !rate->raw.has_value(),
          "unread rates remain unavailable/null rather than assumed zero");
  Check(fixture.calls == std::array<int, 3>{0, 0, 0} && fixture.collect_calls == 0,
        "failed player/full-ID resolution reaches no native speed callback or collection");
  Emit(directory, name, output, result);
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "wire output directory required");
    const std::filesystem::path directory(argv[1]);
    const auto bound = BindCommanderImage(0x10000000, kExecutableSha256);
    Check(bound.enabled &&
              reinterpret_cast<std::uintptr_t>(bound.read_unit_land_movement_rate) == 0x124AA940 &&
              reinterpret_cast<std::uintptr_t>(bound.read_unit_naval_movement_rate) == 0x124AAC00 &&
              reinterpret_cast<std::uintptr_t>(bound.read_unit_current_edge_movement_rate) == 0x124AB5C0,
          "exact .3 production binder selects all three reviewed native total-rate callbacks");
    {
      Fixture f;
      RunAvailable(directory, "speed-positive-route", f, {"available", "available", "available"}, {1, 1, 1});
    }
    {
      Fixture f; f.raw = {0, 0, 0};
      RunAvailable(directory, "speed-legitimate-zero", f, {"available", "available", "available"}, {1, 1, 1});
    }
    {
      Fixture f; auto &row = f.scope.player_armies.front();
      row.route_read_status = xar::game::ArmyRouteReadStatus::complete_empty;
      row.route_source_count = 0; row.route_province_ids.clear();
      row.move_target_observable = false; row.move_target_province_id = -1;
      RunAvailable(directory, "speed-empty-route", f, {"available", "available", "not_applicable"}, {1, 1, 0});
    }
    {
      Fixture f; auto &row = f.scope.player_armies.front();
      row.route_read_status = xar::game::ArmyRouteReadStatus::unresolved_entry;
      row.route_province_ids.clear(); row.move_target_observable = false;
      RunAvailable(directory, "speed-unresolved-route", f, {"available", "available", "unavailable"}, {1, 1, 0});
    }
    constexpr std::array<const char *, 3> names{"land", "naval", "current-edge"};
    for (std::size_t index = 0; index < names.size(); ++index) {
      Fixture f;
      if (index == 0) f.bindings.read_unit_land_movement_rate = nullptr;
      if (index == 1) f.bindings.read_unit_naval_movement_rate = nullptr;
      if (index == 2) f.bindings.read_unit_current_edge_movement_rate = nullptr;
      auto statuses = std::array<std::string_view, 3>{"available", "available", "available"};
      auto calls = std::array<int, 3>{1, 1, 1};
      statuses[index] = "unavailable"; calls[index] = 0;
      RunAvailable(directory, std::string("speed-missing-") + names[index], f, statuses, calls);
    }
    for (std::size_t index = 0; index < names.size(); ++index) {
      Fixture f; f.behavior[index] = index == 1 ? 2 : 1;
      auto statuses = std::array<std::string_view, 3>{"available", "available", "available"};
      statuses[index] = "unavailable";
      RunAvailable(directory, std::string("speed-failed-") + names[index], f, statuses, {1, 1, 1});
    }
    {
      Fixture f; active = &f; f.bindings.get_generic_advantage = nullptr;
      ArmyCommanderCandidatesSnapshot output{};
      const auto result = ReadArmyCommanderCandidates(f.bindings, f.scope, kUnit, output);
      Check(result == CommanderCandidatesReadResult::unavailable &&
                output.unavailable_reason == "commander_bindings_unavailable" &&
                output.current_movement_speed.context_observable,
            "selected-unit speed observation remains independent of candidate getter availability");
      for (std::size_t index = 0; index < 3; ++index)
        Check(Rates(output)[index]->status == "available" &&
                  Rates(output)[index]->raw == f.raw[index],
              "candidate getter failure preserves each already observed native rate");
      Check(f.calls == std::array<int, 3>{1, 1, 1} && f.collect_calls == 0 && f.callback_error.empty(),
            "new speed reads happen before unavailable candidate work");
      Emit(directory, "speed-candidate-getter-unavailable", output, result);
    }
    {
      Fixture f; f.bindings = BindCommanderImage(0x10000000, "wrong-exact-build");
      RunUnavailable(directory, "speed-wrong-exact-build", f, "commander_bindings_unavailable");
    }
    {
      Fixture f; Put(f.unit.data(), 0x10, std::int32_t{kUnit ^ 0x01000000});
      RunUnavailable(directory, "speed-public-cunit-generation-mismatch", f, "public_cunit_not_found");
    }
    {
      Fixture f; Put(f.army.data(), 0x10, std::int32_t{kArmy ^ 0x01000000});
      RunUnavailable(directory, "speed-internal-carmy-generation-mismatch", f, "native_carmy_or_owner_unavailable");
    }
    {
      Fixture f; Put(f.army.data(), 0x124, std::int32_t{kUnit ^ 0x01000000});
      RunUnavailable(directory, "speed-backlink-mismatch", f, "native_carmy_or_owner_unavailable");
    }
    {
      Fixture f; Put(f.unit.data(), 0x174, std::int32_t{30000});
      RunUnavailable(directory, "speed-native-owner-mismatch", f, "native_carmy_or_owner_unavailable");
    }
    {
      Fixture f; f.scope.paused = false;
      RunUnavailable(directory, "speed-unpaused-player-scope", f, "paused_player_scope_unavailable");
    }
    {
      Fixture f; f.scope.player_armies.front().controllable = false;
      RunUnavailable(directory, "speed-uncontrollable-player-scope", f, "army_outside_current_player_scope");
    }
    {
      Fixture f; Put(f.unit.data(), 0x10, std::int32_t{0});
      Put(f.army.data(), 0x124, std::int32_t{0});
      f.scope.player_armies.front().army_id = 0;
      RunAvailable(directory, "speed-public-cunit-zero", f, {"available", "available", "available"}, {1, 1, 1});
    }
    std::cout << "PASS checks=" << checks << " cases=" << cases << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
