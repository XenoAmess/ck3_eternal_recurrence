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
    0x0100085F, 0x010008FD, 2144, 2145, 0x02000862};
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
    Check(argc == 2, "new county fixture needs its JSON output directory");
    Fixture fixture;
    std::array<std::array<std::byte, 0x130>, 4> counties{};
    std::array<std::array<std::byte, 0x90>, 4> definitions{};
    // Requested generation 5 resolves the slot containing generation 6 and
    // must really fail the production Component full-ID roundtrip.
    constexpr std::array<std::int32_t, 4> stored_ids{
        0x03000960, 0, 0x06000961, 0x04000962};
    for (std::size_t index = 0; index < counties.size(); ++index) {
      Put(counties[index], 0x10, stored_ids[index]);
      Put(counties[index], 0x48, static_cast<void *>(definitions[index].data()));
      Put(definitions[index], 0x64, std::int32_t{index == 3 ? 3 : 2});
      Put(fixture.title_slots,
          (static_cast<std::uint32_t>(stored_ids[index]) & 0xFFFFFFU) * 0x10 + 8,
          static_cast<void *>(counties[index].data()));
    }
    constexpr std::array<std::int32_t, 5> parent_ids{
        0x03000960, 0, 0x05000961, 0x04000962, -1};
    for (std::size_t index = 0; index < fixture.titles.size(); ++index)
      Put(fixture.titles[index], 0x108, parent_ids[index]);

    const auto bindings = Bindings(fixture);
    // Real production resolution establishes why 0 is a valid county ID and
    // why an occupied slot is insufficient for a generation-bearing request.
    Check(xar::ck3_12002::ResolveObjectiveTitle(bindings.provinces, 0) == counties[1].data(),
          "zero county ID has an actual exact-ID resolved county object");
    Check(xar::ck3_12002::ResolveObjectiveTitle(bindings.provinces, 0x05000961) == nullptr,
          "generation-mismatched parent really returns null from Component");
    Output output{};
    const auto result = ReadWarOccupationTargetsV1(bindings, fixture.Scope(), kWar, output);
    Check(result == Result::available && output.available && output.collection_complete,
          "county mapping fallbacks preserve an available complete occupation collection");
    Check(output.actor_character_id == kActor && output.war_id == kWar &&
              output.player_side == "defender" && output.date_raw == 53236632,
          "production reader preserves the paused fixture scope");
    Check(output.rows.size() == 6 && output.side_counts.size() == 2,
          "optional county failures never remove native eligible rows or side counters");
    const std::vector<std::int32_t> expected_titles{
        kTitles[0], kTitles[1], kTitles[2], kTitles[3], kTitles[0], kTitles[4]};
    std::vector<std::int32_t> actual_titles;
    for (const auto &row : output.rows) actual_titles.push_back(row.holding_title_id);
    Check(actual_titles == expected_titles, "native occurrence order and duplicate holding remain intact");
    Check(output.rows[0].county_title_id == 0x03000960 &&
              output.rows[4].county_title_id == 0x03000960,
          "resolved county full ID retains generation bits on both stored occurrences");
    Check(output.rows[1].county_title_id == 0,
          "actual tier-two county with full ID zero remains an observed zero");
    Check(output.rows[2].county_title_id == -1,
          "parent full-ID roundtrip failure leaves only county unobserved");
    Check(output.rows[3].county_title_id == -1,
          "resolved non-county parent leaves only county unobserved");
    Check(output.rows[5].county_title_id == -1,
          "absent direct parent leaves only county unobserved");
    Check(output.rows[2].occupation_observable && output.rows[2].is_occupied &&
              output.rows[2].occupier_side == "outside_war" &&
              output.rows[3].occupation_observable && !output.rows[3].is_occupied &&
              output.rows[5].occupation_observable && output.rows[5].is_occupied &&
              output.rows[5].counted_occupied_by_opposing_side,
          "fallback rows retain independently read geographic and opposing-side occupation");
    Check(output.side_counts[0].territory_side == "defender" &&
              output.side_counts[0].eligible == 5 && output.side_counts[0].occupied == 2 &&
              output.side_counts[0].native_candidate_count == 5 &&
              output.side_counts[1].territory_side == "attacker" &&
              output.side_counts[1].eligible == 1 && output.side_counts[1].occupied == 1 &&
              output.side_counts[1].native_candidate_count == 1,
          "native count results survive every optional mapping branch");
    Check(fixture.context_calls == 2 && fixture.territory_calls == 2 &&
              fixture.holding_calls == 2 && fixture.count_calls == 6,
          "new case genuinely traverses production collector callbacks and holding counts");
    CheckCallbacks(fixture);
    Emit(std::filesystem::path(argv[1]) / "county-title-mapping-production.json", output, result);
    std::cout << "PASS checks=" << checks << " cases=1\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL " << error.what() << '\n';
    return 1;
  }
}
