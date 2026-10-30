#pragma once
#include "xar_bridge/ck3_12004_adapter.hpp"
#include "faction_allocator_exec10.hpp"
#include "xar_bridge/ck3_12004_faction_alerts.hpp"
#include "xar_bridge/ck3_12004_faction_mailbox.hpp"
#include <bit>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace m1_county_fullid13 {
using namespace xar;
using namespace xar::ck3_12004;

template<class T> inline void Put(void* base, std::size_t offset, T value) {
  std::memcpy(static_cast<std::byte*>(base) + offset, &value, sizeof value);
}
template<class T> inline T Get(const void* base, std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte*>(base) + offset, sizeof value);
  return value;
}
inline constexpr std::uint32_t actor_id = 0x03000001U;
inline constexpr std::uint32_t recipient_id = 0x04000002U;
inline void* local_player09 = nullptr;
inline void* LocalPlayer09(void*) { return local_player09; }
inline bool MainThread09(void*) noexcept { return true; }
inline bool Human09(std::uint32_t) { return false; }
inline std::int64_t* Power09(void*, std::int64_t* out) { *out = 11'000'000; return out; }
inline std::int64_t* Threshold09(void*, std::int64_t* out) { *out = 8'000'000; return out; }
inline std::int64_t* Growth09(void*, std::int64_t* out) { *out = 100'000; return out; }
inline std::int32_t Months09(void*) { return 20; }
inline bool AtWar09(void*) { return false; }
inline bool Danger09(void*, void*) { return true; }

// County-only Core/Faction subset of the retained owned fixture. Kept in this
// namespace so the unchanged targeting TU's anonymous fixtures cannot collide.
struct CoreAndFactionFixture09 {
  std::array<std::byte, 0xA8> state{};
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x1F8> players{};
  std::array<std::byte, 0x78> local{};
  std::vector<std::byte> game_data = std::vector<std::byte>(0x36780);
  std::array<std::byte, 0xE0> player_entry{};
  std::array<void*, 1> entries{player_entry.data()};
  std::array<std::byte, 0x30> store{};
  std::array<std::byte, 8 * 0x10> slots{};
  std::array<std::array<std::byte, 0x1D8>, 2> characters{};
  std::array<std::byte, 0x40> faction_type{};
  void* state_pointer = state.data();
  void* jomini_pointer = jomini.data();
  void* store_pointer = store.data();
  void* faction_store_pointer = nullptr;
  void* faction_fallback = nullptr;
  CoreBindings core{};
  PlayerFactionAlertsNativeEnvironmentV1 factions{};
  PlayerFactionAlertsAccessV1 faction_access{};

  CoreAndFactionFixture09() {
    Put(state.data(), 8, std::int32_t{53175816});
    Put(state.data(), 0x70, std::int32_t{2});
    Put(state.data(), 0xA0, game_data.data());
    Put(jomini.data(), 0x18, players.data());
    jomini[0x20] = std::byte{1};
    Put(players.data(), 0x1F0, std::int32_t{7});
    Put(local.data(), 0x70, std::int32_t{7});
    Put(game_data.data(), 0x222E8 + 0x58, entries.data());
    Put(game_data.data(), 0x222E8 + 0x64, std::int32_t{1});
    Put(player_entry.data(), 0xD8, std::int32_t{7});
    Put(player_entry.data(), 0xB0, actor_id);
    Put(store.data(), 0x20, slots.data());
    Put(store.data(), 0x2C, std::int32_t{8});
    Put(characters[0].data(), 0x18, actor_id);
    Put(characters[1].data(), 0x18, recipient_id);
    Put(slots.data(), (actor_id & 0x00FFFFFFU) * 0x10ULL + 8, characters[0].data());
    Put(slots.data(), (recipient_id & 0x00FFFFFFU) * 0x10ULL + 8, characters[1].data());
    local_player09 = local.data();
    core = {true, &state_pointer, &jomini_pointer, &store_pointer, &LocalPlayer09};
    factions.exact_build_admitted = true;
    factions.offline_fixture_function_overrides = true;
    factions.character_storage_slot = &store_pointer;
    factions.faction_storage_slot = &faction_store_pointer;
    factions.faction_fallback_slot = &faction_fallback;
    factions.character_is_human = &Human09;
    factions.power = &Power09;
    factions.power_threshold = &Threshold09;
    factions.discontent_per_month = &Growth09;
    factions.months_until_max_discontent = &Months09;
    factions.at_war = &AtWar09;
    factions.dangerous = &Danger09;
    faction_access.is_main_thread = &MainThread09;
  }
};
inline constexpr std::int32_t county_id09 = 0x07000003;
inline constexpr std::string_view populist09 = "populist_faction";
struct CountyWorld09;
inline CountyWorld09* county_world09 = nullptr;
inline void* ProvinceCounty09(void* title);

struct CountyWorld09 {
  CoreAndFactionFixture09 fixture;
  m1_allocator_exec10::FactionAllocatorImage allocator;
  std::array<std::byte, 0x230> land{}, recipient_land{};
  std::array<std::byte, 0x30> titles{};
  std::array<std::byte, 8 * 0x10> title_slots{};
  std::array<std::byte, 0x1A0> title{};
  std::array<std::byte, 0x68> title_definition{};
  std::array<std::byte, 0x860> province{};
  std::array<std::byte, 0x3C0> county{};
  std::array<std::array<std::byte, 0x18>, 3> county_members{};
  std::array<void*, 3> faction_objects{};
  std::array<std::int32_t, 3> joined{};
  std::array<std::int32_t, 1> held{county_id09};
  void* title_store = titles.data();
  void* null_object = nullptr;
  std::vector<std::pair<const void*, std::size_t>> ranges;
  std::uint32_t actual_source = 0;
  std::int32_t expected_exposure = -1;
  std::size_t allocator_calls = 0;
  std::size_t county_header_reads = 0, joined_id_reads = 0, faction_identity_reads = 0;

  template<class T> void Register(T& object) {
    ranges.emplace_back(&object, sizeof object);
  }

  CountyWorld09(std::uint32_t wanted, std::string_view control,
                std::string_view asset_root)
      : allocator(std::string(asset_root)) {
    county_world09 = this;
    // Reuse the retained actual-reader county graph, with the raw allocator
    // supplying Faction+10 and Faction+40, not DTO/JSON mutations.
    Put(fixture.faction_type.data(), 0x18, populist09.data());
    Put(fixture.faction_type.data(), 0x28, std::uint64_t{populist09.size()});
    Put(fixture.faction_type.data(), 0x30, std::uint64_t{populist09.size()});
    allocator.Reset(((wanted - 0x01000000U) & 0xFF000000U) | 0x00FFFFFFU);
    const bool mixed = control == "mixed";
    const std::size_t count = mixed ? 3U : 1U;
    for (std::size_t index = 0; index < count; ++index) {
      const auto full_id = index == 0U ? wanted : index == 1U ? 1U : 0xFF000002U;
      if (index != 0U) {
        Put(allocator.FirstObject(), index * 0xD0U + 0x10U,
            ((full_id - 0x01000000U) & 0xFF000000U) | 0x00FFFFFFU);
      }
      void* faction = allocator.Allocate(fixture.faction_type.data(),
          std::bit_cast<std::int32_t>(recipient_id), 29);
      ++allocator_calls;
      m1_allocator_exec10::Require(Get<std::uint32_t>(faction, 0x10) == full_id,
          "native allocator produced requested fullID");
      m1_allocator_exec10::Require(Get<std::uint32_t>(faction, 0x40) == recipient_id,
          "native allocator produced other-target");
      faction_objects[index] = faction;
      // The joined membership rows/discontent are authored later state. The
      // native creator's ID/type/target/update_day/registry stores are retained.
      Put(faction, 0x28, std::int64_t{7'000'000});
      Put(faction, 0x44, std::int32_t{-1});
      Put(faction, 0x48, static_cast<void*>(nullptr));
      Put(faction, 0x54, std::int32_t{0});
      Put(faction, 0x60, county_members[index].data());
      Put(faction, 0x6C, std::int32_t{1});
      Put(county_members[index].data(), 8, county_id09);
      Put(county_members[index].data(), 0x0C, std::uint8_t{1});
      Put(county_members[index].data(), 0x10, faction);
      joined[index] = Get<std::int32_t>(faction, 0x10);
    }
    actual_source = Get<std::uint32_t>(faction_objects[0], 0x10);
    expected_exposure = joined[0];
    if (mixed) joined = {joined[1], joined[2], joined[0]};
    fixture.faction_store_pointer = allocator.Storage();
    fixture.faction_fallback = allocator.Fallback();
    fixture.factions.expected_faction_vtable = allocator.PrimaryVtable();
    fixture.factions.character_fallback_slot = &null_object;
    fixture.factions.landed_title_storage_slot = &title_store;
    fixture.factions.landed_title_fallback_slot = &null_object;
    fixture.factions.title_province = &ProvinceCounty09;
    Put(fixture.characters[0].data(), 0x1C0, land.data());
    Put(fixture.characters[1].data(), 0x1C0, recipient_land.data());
    Put(land.data(), 0x1E0, held.data());
    Put(land.data(), 0x1EC, std::int32_t{1});
    // Targeting and contract lists are truly empty; the live reader must use
    // the nonempty county branch to produce this exposure.
    Put(titles.data(), 0x20, title_slots.data());
    Put(titles.data(), 0x2C, std::int32_t{8});
    Put(title_slots.data(), 3 * 0x10 + 8, title.data());
    Put(title.data(), 0x10, county_id09);
    Put(title.data(), 0x48, title_definition.data());
    Put(title.data(), 0x128, actor_id);
    Put(title.data(), 0x11C, std::int32_t{1});
    Put(title_definition.data(), 0x64, std::int32_t{2});
    Put(province.data(), 0x10, std::int32_t{99});
    Put(province.data(), 0x85C, std::uint32_t{0x50726F76});
    Put(province.data(), 0x848, county.data());
    Put(county.data(), 0x18, county_id09);
    Put(county.data(), 0x3B0, joined.data());
    Put(county.data(), 0x3BC, static_cast<std::int32_t>(count));
    if (control == "stale")
      Put(faction_objects[0], 0x10, actual_source ^ 0x01000000U);
    if (control == "absent") joined[0] = -1;
    if (control == "duplicate") {
      joined[1] = joined[0];
      Put(county.data(), 0x3BC, std::int32_t{2});
    }
    if (control == "empty-joined") Put(county.data(), 0x3BC, std::int32_t{0});
    if (control == "title-zero") held[0] = 0;
    Register(fixture.state); Register(fixture.jomini); Register(fixture.players);
    Register(fixture.local); Register(fixture.player_entry); Register(fixture.entries);
    Register(fixture.store); Register(fixture.slots); Register(fixture.characters);
    Register(fixture.state_pointer); Register(fixture.jomini_pointer);
    Register(fixture.store_pointer); Register(fixture.faction_store_pointer);
    Register(fixture.faction_fallback); Register(fixture.faction_type);
    ranges.emplace_back(fixture.game_data.data(), fixture.game_data.size());
    Register(land); Register(recipient_land); Register(titles); Register(title_slots);
    Register(title); Register(title_definition); Register(province); Register(county);
    Register(county_members); Register(joined); Register(held); Register(title_store);
    Register(null_object);
    ranges.emplace_back(allocator.Storage(), 0x58U);
    ranges.emplace_back(Get<void*>(allocator.Storage(), 0x20), 1024U * 16U);
    ranges.emplace_back(allocator.FirstObject(), 0x34000U);
    ranges.emplace_back(allocator.Fallback(), 0xD0U);
    ranges.emplace_back(populist09.data(), populist09.size() + 1U);
    allocator.RequireOriginalCodeUnchanged();
  }
};

inline void* ProvinceCounty09(void* title) {
  return title == county_world09->title.data() ? county_world09->province.data() : nullptr;
}
inline bool CountyMemory09(void* context, const void* address, void* output,
                    std::size_t size) noexcept {
  auto& world = *static_cast<CountyWorld09*>(context);
  const auto at = reinterpret_cast<std::uintptr_t>(address);
  for (const auto& [base, length] : world.ranges) {
    const auto begin = reinterpret_cast<std::uintptr_t>(base);
    if (at >= begin && at - begin <= length && size <= length - (at - begin)) {
      std::memcpy(output, address, size);
      if (address == world.county.data() + 0x3B0 || address == world.county.data() + 0x3BC)
        ++world.county_header_reads;
      if (at >= reinterpret_cast<std::uintptr_t>(world.joined.data()) &&
          at - reinterpret_cast<std::uintptr_t>(world.joined.data()) < sizeof world.joined)
        ++world.joined_id_reads;
      for (const auto faction : world.faction_objects)
        if (faction && address == static_cast<std::byte*>(faction) + 0x10)
          ++world.faction_identity_reads;
      return true;
    }
  }
  return false;
}
inline bool CountyFrame09(void* context, game::PlayerFactionAlertsFrameV1& output) noexcept {
  auto& world = *static_cast<CountyWorld09*>(context);
  CoreSnapshotPrefix core{};
  if (!xar::ck3_12004::ReadCoreSnapshot(world.fixture.core, core)) return false;
  output = {1, core.clock.date_raw, core.clock.paused, core.map_ready,
      core.has_played_character, core.played_character_alive, core.played_character_id};
  return true;
}

inline bool RunCounty09(const std::filesystem::path& root, std::uint32_t raw,
                        std::string_view control, std::string_view asset_root) {
  CountyWorld09 world(raw, control, asset_root);
  auto access = world.fixture.faction_access;
  access.context = &world;
  access.capture_frame = &CountyFrame09;
  access.read_memory = &CountyMemory09;
  game::PlayerFactionAlertsV1 output{};
  const auto result = ReadPlayerFactionAlerts12004(world.fixture.factions, access, {1}, output);
  const auto wire = SerializePlayerFactionAlerts12004(output);
  const game::AdapterDescriptor descriptor{"ck3-1.20.0.4-msvc-x64", "1.20.0.4",
      kExecutableSha256, "county-fullid09-fixture", {}};
  const auto whole = SerializePlayerFactionAlertsWhole12004(output, 1,
      "county-fullid09", descriptor);
  const bool available = result == game::ReadPlayerFactionAlertsResultV1::available;
  const bool positive = control == "valid" || control == "mixed";
  const bool empty = control == "empty-joined";
  const auto expected_id = world.expected_exposure;
  bool passed = false;
  if (positive) {
    const auto id_fragment = "\"faction_id\":" + std::to_string(expected_id);
    passed = available && output.targeting_factions.empty() &&
        output.county_exposures.size() == 1U &&
        output.county_exposures[0].faction_id == expected_id &&
        output.county_exposures[0].county_title_id == county_id09 &&
        output.county_exposures[0].target_character_id ==
            std::bit_cast<std::int32_t>(recipient_id) &&
        output.planner_projection.exposed_county_title_ids ==
            std::vector<std::int32_t>{county_id09} &&
        output.planner_projection.present.value_or(false) &&
        output.planner_projection.dangerous.value_or(false) &&
        output.readiness.alert_ready && !wire.empty() && !whole.empty() &&
        wire.find(id_fragment) != std::string::npos &&
        whole.find(id_fragment) != std::string::npos &&
        world.county_header_reads != 0U && world.joined_id_reads != 0U &&
        world.faction_identity_reads != 0U;
  } else if (empty) {
    passed = available && output.county_exposures.empty() &&
        output.planner_projection.exposed_county_title_ids.empty() &&
        !output.planner_projection.present.value_or(true) &&
        output.readiness.alert_ready && !wire.empty() && !whole.empty() &&
        world.county_header_reads != 0U && world.joined_id_reads == 0U;
  } else {
    passed = !available && output.county_exposures.empty() &&
        output.planner_projection.exposed_county_title_ids.empty() &&
        !output.readiness.alert_ready;
  }
  world.allocator.RequireOriginalCodeUnchanged();
  const auto name = std::to_string(raw) + "-" + std::string(control);
  const auto directory = root / name;
  std::filesystem::create_directories(directory);
  std::ofstream(directory / "public-alerts.json") << wire;
  std::ofstream(directory / "public-alerts-whole.json") << whole;
  std::ofstream summary(directory / "SUMMARY.json");
  summary << "{\"machine_id\":\"xenoamess-full-tower-eb9d2c1186\","
      "\"software_fixture\":true,\"raw_allocator_loaded_bytes\":865,"
      "\"actual_allocator_calls\":" << world.allocator_calls <<
      ",\"source_raw\":" << world.actual_source << ",\"source_signed\":"
      << std::bit_cast<std::int32_t>(world.actual_source) <<
      ",\"actual_allocator_target_raw\":" << recipient_id <<
      ",\"county_joined_native_memory_authored\":true,"
      "\"membership_authored_after_allocation\":true,"
      "\"read_project_public_and_whole_serialize_executed\":true,"
      "\"public_Handle_executed\":false,\"control\":\"" << control <<
      "\",\"available\":" << available << ",\"county_header_reads\":"
      << world.county_header_reads << ",\"joined_id_reads\":" << world.joined_id_reads <<
      ",\"faction_full_id_reads\":" << world.faction_identity_reads <<
      ",\"county_exposures\":" << output.county_exposures.size() <<
      ",\"targeting_factions\":" << output.targeting_factions.size() <<
      ",\"passed\":" << passed << "}\n";
  std::cout << "County09 " << name << " available=" << available <<
      " exposure=" << output.county_exposures.size() << " joined_reads=" <<
      world.joined_id_reads << " passed=" << passed << '\n';
  return passed;
}

struct CountyCase09 {
  std::string_view name;
  std::uint32_t raw;
  std::string_view control;
};
inline constexpr std::array<CountyCase09, 13> kCountyCases09{{
  {"fid-zero", 0U, "valid"},
  {"fid-zero-stale", 0U, "stale"},
  {"fid-min", 2147483648U, "valid"},
  {"fid-min-stale", 2147483648U, "stale"},
  {"fid-81", 2164260864U, "valid"},
  {"fid-81-stale", 2164260864U, "stale"},
  {"fid-ff", 4278190080U, "valid"},
  {"fid-ff-stale", 4278190080U, "stale"},
  {"joined-absent", 0U, "absent"},
  {"joined-duplicate", 0U, "duplicate"},
  {"title-zero", 0U, "title-zero"},
  {"joined-empty", 0U, "empty-joined"},
  {"joined-mixed", 2147483648U, "mixed"}
}};

// After dispatcher strips its --county prefix: argv[0]=--county,
// argv[1]=exact case, argv[2]=output directory, argv[3]=865B asset root.
inline int RunCountyFullId13(int argc, char** argv) {
  if (argc != 4) return 90;
  try {
    for (const auto& test : kCountyCases09) {
      if (test.name != argv[1]) continue;
      const std::filesystem::path output(argv[2]);
      std::filesystem::create_directories(output);
      return RunCounty09(output, test.raw, test.control, argv[3]) ? 0 : 1;
    }
    std::cerr << "Unknown county fullID case: " << argv[1] << '\n';
    return 91;
  } catch (const std::exception& error) {
    std::cerr << "County09 exception: " << error.what() << '\n';
    return 2;
  }
}
} // namespace m1_county_fullid13
