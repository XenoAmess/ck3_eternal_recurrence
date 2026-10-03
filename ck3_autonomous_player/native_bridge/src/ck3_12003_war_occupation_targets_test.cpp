#include "xar_bridge/ck3_12003_war_occupation.hpp"
#include "xar_bridge/war_occupation_targets_v1_serializer.hpp"

#include <algorithm>
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
using Output = xar::game::WarOccupationTargetsV1;
using Result = xar::game::ReadWarOccupationTargetsV1Result;
constexpr std::int32_t kActor = 29829;
constexpr std::int32_t kAttacker = 30097;
constexpr std::int32_t kOutside = 35357;
constexpr std::int32_t kWar = 16777231;
constexpr std::array<std::int32_t, 5> kTitles{
    0x0100085F, 0, 2144, 2145, 0x02000862};
int checks = 0;

template <class Buffer, class T>
void Put(Buffer &object, std::size_t offset, T value) {
  if (offset + sizeof value > object.size()) std::abort();
  std::memcpy(object.data() + offset, &value, sizeof value);
}
template <class T> T Get(const void *object, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(object) + offset,
              sizeof value);
  return value;
}
void Check(bool value, const char *label) {
  ++checks;
  if (!value) throw std::runtime_error(label);
}

struct Fixture {
  std::array<std::byte, 0xA8> game_state{};
  std::vector<std::byte> game_data = std::vector<std::byte>(0x2F000);
  std::array<std::byte, 0x360> war{};
  std::array<std::byte, 0x30> context{};
  std::array<std::byte, 0x30> war_store{}, character_store{}, title_store{};
  std::vector<std::byte> war_slots = std::vector<std::byte>(16 * 0x10);
  std::vector<std::byte> character_slots = std::vector<std::byte>(40000 * 0x10);
  std::vector<std::byte> title_slots = std::vector<std::byte>(3000 * 0x10);
  std::array<std::array<std::byte, 0x1D8>, 3> characters{};
  std::array<std::array<std::byte, 0x10>, 2> participants{};
  std::array<void *, 1> attackers{}, defenders{};
  std::array<std::array<std::byte, 0x130>, 5> titles{};
  std::array<std::array<std::byte, 0x90>, 5> title_templates{};
  std::array<std::array<std::byte, 0x860>, 5> provinces{};
  std::vector<void *> province_slots = std::vector<void *>(3000);
  std::array<std::byte, 0x18> allocator_vtable{};
  std::array<std::byte, 8> allocator{};
  void *game_state_slot = game_state.data();
  void *character_slot = character_store.data();
  void *title_slot = title_store.data();
  void *context_return = context.data();
  void *context_fallback_slot = nullptr;
  std::int32_t war_id = kWar;
  bool empty_collection = false;
  bool invalid_collection = false;
  bool liege_related = true;
  int context_calls = 0, territory_calls = 0, holding_calls = 0;
  int count_calls = 0, allocated = 0, released = 0;
  int fort_calls = 0, garrison_calls = 0;
  std::array<std::int32_t, 5> garrisons{325, 0, 910, 0, 1400};
  std::vector<std::int32_t> counted_titles;
  std::string callback_error;

  explicit Fixture(std::int32_t selected_war = kWar) : war_id(selected_war) {
    Put(game_state, 0xA0, static_cast<void *>(game_data.data()));
    Put(game_data, xar::ck3_12002::kWorldWarManagerOffset + 0x20,
        static_cast<void *>(war_store.data()));
    Put(war_store, 0x20, static_cast<void *>(war_slots.data()));
    Put(war_store, 0x2C, std::int32_t{16});
    Put(war_slots, (static_cast<std::uint32_t>(war_id) & 0xFFFFFFU) * 0x10 + 8,
        static_cast<void *>(war.data()));
    Put(war, 0x08, war_id);
    Put(context, 0x28, war_id);
    Put(war, 0x288, kAttacker);
    Put(war, 0x28C, kActor);
    for (std::size_t index = 0; index < characters.size(); ++index) {
      const auto id = std::array{kActor, kAttacker, kOutside}[index];
      Put(characters[index], 0x18, id);
      Put(characters[index], 0x1C, std::uint32_t{0x43686172});
      Put(character_slots, static_cast<std::size_t>(id) * 0x10 + 8,
          static_cast<void *>(characters[index].data()));
    }
    Put(character_store, 0x20, static_cast<void *>(character_slots.data()));
    Put(character_store, 0x2C, std::int32_t{40000});
    Put(participants[0], 0x08, kAttacker);
    Put(participants[1], 0x08, kActor);
    attackers[0] = participants[0].data();
    defenders[0] = participants[1].data();
    Put(war, 0x28, WarOccupationPointerVector{attackers.data(), 1, 1, nullptr});
    Put(war, 0x88, WarOccupationPointerVector{defenders.data(), 1, 1, nullptr});
    Put(title_store, 0x20, static_cast<void *>(title_slots.data()));
    Put(title_store, 0x2C, std::int32_t{3000});
    for (std::size_t index = 0; index < titles.size(); ++index) {
      const auto province_id = static_cast<std::int32_t>(2610 + index);
      Put(titles[index], 0x10, kTitles[index]);
      Put(titles[index], 0x48, static_cast<void *>(title_templates[index].data()));
      Put(titles[index], 0x128, index == 4 ? kAttacker : kActor);
      Put(title_templates[index], 0x64, std::int32_t{1});
      // The verified native receiver is the title template, not CTitle itself.
      Put(title_templates[index], 0x88, province_id);
      Put(title_slots,
          (static_cast<std::uint32_t>(kTitles[index]) & 0xFFFFFFU) * 0x10 + 8,
          static_cast<void *>(titles[index].data()));
      Put(provinces[index], 0x10, province_id);
      Put(provinces[index], 0x85C, std::uint32_t{0x50726F76});
      Put(provinces[index], 0x738, kTitles[index]);
      Put(provinces[index], 0x850, std::array<std::int32_t, 5>{4, 0, 8, 1, 6}[index]);
      const auto occupier = index == 0 ? kAttacker :
          index == 2 ? kOutside : index == 4 ? kActor : std::int32_t{-1};
      Put(provinces[index], 0x73C, occupier);
      province_slots[static_cast<std::size_t>(province_id)] = provinces[index].data();
    }
    Put(game_data, 0x140, static_cast<void *>(province_slots.data()));
    Put(game_data, 0x14C, std::int32_t{3000});
    Put(allocator, 0, static_cast<void *>(allocator_vtable.data()));
  }

  xar::game::Snapshot Scope() const {
    xar::game::Snapshot scope{};
    scope.paused = scope.map_ready = scope.has_played_character =
        scope.played_character_alive = true;
    scope.played_character_id = kActor;
    scope.date_raw = 53236632;
    xar::game::ActiveWarSnapshot row{};
    row.war_id = war_id;
    row.player_side = xar::game::PlayerWarSide::defender;
    row.primary_opponent_character_id = kAttacker;
    row.player_is_primary_war_leader = true;
    scope.active_wars.push_back(row);
    return scope;
  }
};
Fixture *active = nullptr;

void CallbackCheck(bool value, const char *label) {
  if (!value && active->callback_error.empty()) active->callback_error = label;
}
void Allocate(WarOccupationPointerVector *output, const std::vector<void *> &rows) {
  CallbackCheck(output->allocator == active->allocator.data() &&
                    output->data == nullptr && output->count == 0 &&
                    output->capacity == 0,
                "native collector receives a fresh allocator-backed vector");
  if (rows.empty()) return;
  output->data = new void *[rows.size()];
  std::copy(rows.begin(), rows.end(), output->data);
  output->count = output->capacity = static_cast<std::int32_t>(rows.size());
  ++active->allocated;
}
void Release(void *allocator, void *data, std::uint64_t alignment) {
  CallbackCheck(allocator == active->allocator.data() && data != nullptr && alignment == 8,
                "native selected allocation released with allocator and alignment 8");
  delete[] static_cast<void **>(data);
  ++active->released;
}
void *GetContext(std::int32_t war_id) {
  CallbackCheck(war_id == active->war_id, "native context lookup receives full WarID");
  ++active->context_calls;
  return active->context_return;
}
void CollectTerritory(void *context, std::int32_t primary,
                      const WarOccupationPointerVector *territory,
                      const WarOccupationPointerVector *opposing,
                      WarOccupationPointerVector *output) {
  CallbackCheck(context == active->context.data() &&
                    territory->count == 1 && opposing->count == 1 &&
                    Get<std::int32_t>(territory->data[0], 8) == primary &&
                    Get<std::int32_t>(opposing->data[0], 8) != primary,
                "native territory collector gets raw ordered CWar participants");
  ++active->territory_calls;
  if (active->invalid_collection) {
    output->capacity = -1;
    return;
  }
  if (!active->empty_collection) Allocate(output, {territory->data[0]});
}
void CollectHoldings(void *character, WarOccupationPointerVector *output) {
  CallbackCheck(character == active->characters[0].data() ||
                    character == active->characters[1].data(),
                "holding collector receives generation-resolved territory character");
  ++active->holding_calls;
  if (character == active->characters[0].data()) {
    Allocate(output, {active->titles[0].data(), active->titles[1].data(),
                      active->titles[2].data(), active->titles[3].data(),
                      active->titles[0].data()});
  } else {
    Allocate(output, {active->titles[4].data()});
  }
}
void *TitleProvince(void *title) {
  for (std::size_t index = 0; index < active->titles.size(); ++index)
    if (title == active->titles[index].data()) return active->provinces[index].data();
  CallbackCheck(false, "title getter receives a real fixture title");
  return nullptr;
}
bool IsOccupied(void *province) {
  return Get<std::int32_t>(province, 0x73C) != -1;
}
std::int32_t FortLevel(void *province) {
  ++active->fort_calls;
  for (const auto &row : active->provinces)
    if (province == row.data()) return Get<std::int32_t>(province, 0x850);
  CallbackCheck(false, "fort getter receives the resolved Province pointer");
  return -1;
}
std::int32_t GarrisonSize(void *province) {
  ++active->garrison_calls;
  for (std::size_t index = 0; index < active->provinces.size(); ++index)
    if (province == active->provinces[index].data()) return active->garrisons[index];
  CallbackCheck(false, "garrison getter receives the resolved Province pointer");
  return -1;
}
bool LiegeRelated(void *war) {
  CallbackCheck(war == active->war.data(), "native liege-related check receives resolved CWar");
  return active->liege_related;
}
bool ContainsParticipant(const void *side, std::int32_t character_id) {
  const auto vector = Get<WarOccupationPointerVector>(side, 8);
  for (std::int32_t index = 0; index < vector.count; ++index)
    if (Get<std::int32_t>(vector.data[index], 8) == character_id) return true;
  return false;
}
void CountHolding(void *title, const WarOccupationPointerVector *opposing,
                  const WarOccupationPointerVector *territories,
                  bool skip_holder_filter, WarOccupationNativeCounts *output) {
  const auto holder = Get<std::int32_t>(title, 0x128);
  CallbackCheck(opposing->count == 1 && territories->count == 1 &&
                    Get<std::int32_t>(territories->data[0], 8) == holder &&
                    Get<std::int32_t>(opposing->data[0], 8) != holder,
                "per-holding native counter receives raw opposing and selected territory vectors");
  CallbackCheck(skip_holder_filter == !(holder == kActor && active->liege_related),
                "holder filter follows native defender and liege-related semantics");
  CallbackCheck(output->occupied == 0 && output->eligible == 0,
                "each native holding counter starts with zeroed scratch");
  ++active->count_calls;
  active->counted_titles.push_back(Get<std::int32_t>(title, 0x10));
  if (title == active->titles[3].data()) return;
  output->eligible = 1;
  const auto occupier = Get<std::int32_t>(TitleProvince(title), 0x73C);
  output->occupied = occupier == Get<std::int32_t>(opposing->data[0], 8) ? 1 : 0;
}
WarOccupationTargetsBindingsV1 Bindings(Fixture &fixture) {
  active = &fixture;
  Put(fixture.allocator_vtable, 0x10, &Release);
  WarOccupationTargetsBindingsV1 bindings{};
  bindings.enabled = bindings.world.enabled = bindings.provinces.enabled = true;
  bindings.world.game_state_slot = bindings.provinces.game_state_slot =
      &fixture.game_state_slot;
  bindings.world.contains_war_participant = ContainsParticipant;
  bindings.character_storage_slot = bindings.world.character_storage_slot =
      bindings.provinces.character_storage_slot = &fixture.character_slot;
  bindings.provinces.landed_title_storage_slot = &fixture.title_slot;
  bindings.provinces.title_province = TitleProvince;
  bindings.provinces.is_occupied = IsOccupied;
  bindings.provinces.fort_level = FortLevel;
  bindings.provinces.garrison_size = GarrisonSize;
  bindings.vector_allocator = fixture.allocator.data();
  bindings.get_war_occupation_context = GetContext;
  bindings.war_occupation_context_fallback_slot = &fixture.context_fallback_slot;
  bindings.collect_territory_participants = CollectTerritory;
  bindings.collect_holding_titles = CollectHoldings;
  bindings.count_holding = CountHolding;
  bindings.war_participants_are_liege_related = LiegeRelated;
  return bindings;
}

void Emit(const std::filesystem::path &path, const Output &output, Result result) {
  const auto payload = xar::game::SerializeWarOccupationTargetsV1(
      output, result, 7, 11,
      "query-war-occupation-targets-v1-" + std::to_string(output.war_id));
  std::ofstream file(path, std::ios::binary);
  file << "{\"type\":\"command_result\",\"protocol_version\":1,\"ok\":true,\"result\":"
       << payload << "}\n";
  Check(bool(file), "genuine production serializer JSON was written");
}

void CheckCallbacks(const Fixture &fixture) {
  Check(fixture.callback_error.empty(), fixture.callback_error.c_str());
  Check(fixture.allocated == fixture.released,
        "all native collector allocations released exactly once");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "native JSON output directory required");
    const auto directory = std::filesystem::path(argv[1]);
    {
      Fixture fixture;
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(),
                                                      kWar, output);
      Check(result == Result::available && output.available && output.collection_complete,
            "actual native collector and counters are available");
      Check(output.actor_character_id == kActor && output.war_id == kWar &&
                output.player_side == "defender",
            "actor side is actual defender and complete generation-bearing WarID survives");
      Check(output.side_counts.size() == 2 && output.rows.size() == 5,
            "native eligible-zero holding is excluded and duplicate eligible title is retained");
      std::vector<std::int32_t> defender_titles;
      for (const auto &row : output.rows)
        if (row.territory_side == "defender") defender_titles.push_back(row.holding_title_id);
      Check(defender_titles == std::vector<std::int32_t>{kTitles[0], 0, kTitles[2], kTitles[0]},
            "full title ID, legal zero and native stored order including duplicate are preserved");
      for (const auto &side : output.side_counts)
        Check(side.territory_side == "defender"
                  ? side.eligible == 4 && side.occupied == 2 && side.native_candidate_count == 5
                  : side.eligible == 1 && side.occupied == 1 && side.native_candidate_count == 1,
              "native counts retain territory-side semantics");
      bool outside = false, unoccupied = false;
      for (const auto &row : output.rows) {
        if (row.holding_title_id == kTitles[2])
          outside = row.is_occupied && row.occupier_side == "outside_war" &&
              row.occupying_character_id == kOutside && !row.counted_occupied_by_opposing_side;
        if (row.holding_title_id == 0)
          unoccupied = row.occupation_observable && !row.is_occupied &&
              row.occupier_side == "none" && row.occupying_character_id == -1;
      }
      Check(outside && unoccupied, "geographic occupation and native opposing-side count remain distinct");
      Check(fixture.context_calls == 2 && fixture.territory_calls == 2 &&
                fixture.holding_calls == 2 && fixture.count_calls == 6,
            "reader genuinely reaches context, territory, holding and per-holding native callbacks");
      for (const auto &row : output.rows) {
        const auto index = static_cast<std::size_t>(row.province_id - 2610);
        Check(row.fort_level_observable && row.garrison_size_observable &&
                  row.fort_level == Get<std::int32_t>(fixture.provinces[index].data(), 0x850) &&
                  row.garrison_size == fixture.garrisons[index],
              "native fort/garrison callbacks retain observed zero and nonzero values");
      }
      Check(fixture.fort_calls == 5 && fixture.garrison_calls == 5,
            "each native eligible row reaches both resolved-Province getters");
      CheckCallbacks(fixture);
      Emit(directory / "defender-ordered-native-counts.json", output, result);
    }
    {
      Fixture fixture;
      fixture.empty_collection = true;
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(),
                                                      kWar, output);
      Check(result == Result::available && output.available && output.collection_complete &&
                output.rows.empty() && output.side_counts.size() == 2,
            "two real successful empty native collections are available, not read failure");
      for (const auto &side : output.side_counts)
        Check(side.collection_complete && side.eligible == 0 && side.occupied == 0 &&
                  side.native_candidate_count == 0,
              "observed empty side publishes honest zero counts");
      Check(fixture.territory_calls == 2 && fixture.holding_calls == 0 && fixture.count_calls == 0,
            "successful empty territory collection cannot call holding counter");
      CheckCallbacks(fixture);
      Emit(directory / "available-empty-native-collections.json", output, result);
    }
    {
      Fixture fixture;
      fixture.invalid_collection = true;
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(),
                                                      kWar, output);
      Check(result == Result::unavailable && !output.available && !output.collection_complete &&
                !output.unavailable_reason.empty(),
            "native collection read failure remains unavailable, not successful empty");
      Check(fixture.holding_calls == 0 && fixture.count_calls == 0,
            "malformed native vector cannot reach holding enumeration");
      CheckCallbacks(fixture);
      Emit(directory / "unavailable-native-collection.json", output, result);
    }
    {
      Fixture fixture;
      std::array<std::byte, 0x130> newer_generation{};
      Put(newer_generation, 0x10, std::int32_t{0x03000862});
      Put(fixture.title_slots, (kTitles[4] & 0xFFFFFF) * 0x10 + 8,
          static_cast<void *>(newer_generation.data()));
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(),
                                                      kWar, output);
      Check(result == Result::unavailable && !output.available && !output.collection_complete &&
                !output.unavailable_reason.empty() && output.rows.empty() && output.side_counts.empty(),
            "mid-read holding generation mismatch clears partial rows and counts");
      Check(fixture.count_calls == 5 && fixture.holding_calls == 2,
            "generation failure occurs after the genuine first territory side was collected");
      CheckCallbacks(fixture);
      Emit(directory / "unavailable-title-generation.json", output, result);
    }
    {
      Fixture fixture;
      Put(fixture.war, 8, std::int32_t{0x0200000F});
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(),
                                                      kWar, output);
      Check(result == Result::unavailable && !output.available && !output.collection_complete,
            "full-generation WarID mismatch cannot become a low-index hit");
      Check(fixture.context_calls == 0 && fixture.territory_calls == 0 && fixture.count_calls == 0,
            "stale war never reaches native query callbacks");
      CheckCallbacks(fixture);
      Emit(directory / "unavailable-war-generation.json", output, result);
    }
    {
      Fixture fixture(0);
      fixture.empty_collection = true;
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(), 0, output);
      Check(result == Result::available && output.available && output.war_id == 0,
            "generation-zero WarID zero is a valid identity");
      CheckCallbacks(fixture);
      Emit(directory / "available-war-zero.json", output, result);
    }
    {
      Fixture fixture;
      Put(fixture.context, 0x28, std::int32_t{-1});
      fixture.context_fallback_slot = fixture.context.data();
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(),
                                                      kWar, output);
      Check(result == Result::available && output.available && output.collection_complete &&
                output.rows.size() == 5 && output.side_counts.size() == 2,
            "exact native fallback context with unmatched WarID reaches the real occupation collector");
      Check(fixture.context_calls == 2 && fixture.territory_calls == 2 &&
                fixture.holding_calls == 2 && fixture.count_calls == 6,
            "fallback is consumed by native territory and per-holding callbacks, not relabeled empty");
      CheckCallbacks(fixture);
      Emit(directory / "available-native-fallback-context.json", output, result);
    }
    {
      Fixture fixture;
      Put(fixture.context, 0x28, std::int32_t{-1});
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(),
                                                      kWar, output);
      Check(result == Result::unavailable && !output.available && !output.collection_complete &&
                output.unavailable_reason == "war_occupation_context_unavailable" &&
                output.rows.empty() && output.side_counts.empty(),
            "unmatched context outside the exact native fallback remains the observed read failure");
      Check(fixture.context_calls == 1 && fixture.territory_calls == 0 && fixture.count_calls == 0,
            "foreign unmatched context does not reach a territory collector");
      CheckCallbacks(fixture);
      Emit(directory / "unavailable-foreign-context.json", output, result);
    }
    {
      Fixture fixture;
      fixture.context_return = nullptr;
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(),
                                                      kWar, output);
      Check(result == Result::unavailable && !output.available && !output.collection_complete &&
                output.unavailable_reason == "war_occupation_context_unavailable",
            "null context remains an unavailable observation");
      Check(fixture.context_calls == 1 && fixture.territory_calls == 0 && fixture.count_calls == 0,
            "null context cannot reach a territory collector");
      CheckCallbacks(fixture);
      Emit(directory / "unavailable-null-context.json", output, result);
    }
    {
      Fixture fixture;
      Put(fixture.provinces[0], 0x850, std::int32_t{-1});
      fixture.garrisons[1] = -1;
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(Bindings(fixture), fixture.Scope(), kWar, output);
      Check(result == Result::available && output.available && output.collection_complete &&
                output.rows.size() == 5 && output.side_counts.size() == 2,
            "negative getter values do not erase the real occupation collection");
      for (const auto &row : output.rows) {
        if (row.province_id == 2610)
          Check(!row.fort_level_observable && row.garrison_size_observable && row.garrison_size == 325,
                "negative fort getter leaves garrison independently observed");
        if (row.province_id == 2611)
          Check(row.fort_level_observable && row.fort_level == 0 && !row.garrison_size_observable,
                "negative garrison is unavailable while actual fort zero stays observable");
      }
      CheckCallbacks(fixture);
      Emit(directory / "available-negative-fort-garrison.json", output, result);
    }
    for (const bool missing_fort : {true, false}) {
      Fixture fixture;
      auto bindings = Bindings(fixture);
      if (missing_fort) bindings.provinces.fort_level = nullptr;
      else bindings.provinces.garrison_size = nullptr;
      Output output{};
      const auto result = ReadWarOccupationTargetsV1(bindings, fixture.Scope(), kWar, output);
      Check(result == Result::available && output.available && output.collection_complete && output.rows.size() == 5,
            "absent optional getter preserves the complete occupation collector result");
      for (const auto &row : output.rows)
        Check(missing_fort ? !row.fort_level_observable && row.garrison_size_observable
                           : row.fort_level_observable && !row.garrison_size_observable,
              "optional native getter absence is kept separate for each scalar");
      Check(missing_fort ? fixture.fort_calls == 0 && fixture.garrison_calls == 5
                        : fixture.fort_calls == 5 && fixture.garrison_calls == 0,
            "absent native getter is never called or synthesized");
      CheckCallbacks(fixture);
      Emit(directory / (missing_fort ? "available-null-fort-getter.json" : "available-null-garrison-getter.json"),
           output, result);
    }
    std::cout << "PASS checks=" << checks << " cases=12\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
