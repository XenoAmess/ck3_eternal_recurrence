#pragma once
#include "county_fullid_cases09.hpp"

namespace m1_county_character16 {
using namespace xar;
using namespace xar::ck3_12004;
using m1_county_fullid13::Get;
using m1_county_fullid13::Put;
using m1_county_fullid13::CoreAndFactionFixture09;

inline constexpr std::int32_t kCounty = 0x07000003;
inline constexpr std::int32_t kDuchy = 0x07000004;
inline constexpr std::uint32_t kActor = 0x03000001U;
inline constexpr std::uint32_t kLeader = 0x04000002U;
inline constexpr std::uint32_t kPositiveHolder = 0x05000003U;
inline constexpr std::string_view kPopulist = "populist_faction";

struct Case16 {
  std::string_view name;
  std::uint32_t actor;
  std::uint32_t holder;
  bool surrender;
  bool stale;
  bool absent;
};
inline constexpr std::array<Case16, 10> kCases{{
  {"opinion-holder-zero", kActor, 0U, false, false, false},
  {"opinion-holder-min", kActor, 0x80000000U, false, false, false},
  {"opinion-holder-zero-stale", kActor, 0U, false, true, false},
  {"opinion-holder-min-stale", kActor, 0x80000000U, false, true, false},
  {"opinion-holder-absent", kActor, 0U, false, false, true},
  {"surrender-holder-zero", kActor, 0U, true, false, false},
  {"surrender-holder-min", kActor, 0x80000000U, true, false, false},
  {"surrender-holder-min-stale", kActor, 0x80000000U, true, true, false},
  {"surrender-top-zero", 0U, kPositiveHolder, true, false, false},
  {"surrender-top-min", 0x80000000U, kPositiveHolder, true, false, false}
}};

struct World16;
inline World16* current16 = nullptr;
inline void* Province16(void* title);
inline void* Liege16(void* character);
inline void* Government16(void* character);
inline void* Relation16(void* leader, void* actor);
inline std::uint64_t Mask16(const std::int32_t*) { return 1U; }
inline std::int32_t Opinion16(void* county);

struct World16 {
  CoreAndFactionFixture09 fixture;
  m1_allocator_exec10::FactionAllocatorImage allocator;
  Case16 test;
  std::array<std::byte, 0x1D8> holder{};
  std::array<std::byte, 0x230> actor_land{}, holder_land{}, leader_land{};
  std::array<std::byte, 0x30> titles{}, contracts{}, contract{};
  std::array<std::byte, 8U * 0x10U> title_slots{}, contract_slots{};
  std::array<std::byte, 0x1A0> title{}, duchy{};
  std::array<std::byte, 0x68> county_definition{}, duchy_definition{};
  std::array<std::byte, 0x860> province{};
  std::array<std::byte, 0x3C0> county{};
  std::array<std::byte, 0x18> county_member{};
  std::array<std::byte, 0x48> government{};
  std::array<std::byte, 0x28> relation{};
  std::array<std::int32_t, 1> targeting{}, held{kCounty}, children{kCounty};
  std::array<std::int32_t, 1> contract_ids{0x06000001};
  void* title_store = titles.data();
  void* contract_store = contracts.data();
  void* empty = nullptr;
  std::int32_t state_faith = 0;
  void* faction = nullptr;
  std::vector<std::pair<const void*, std::size_t>> ranges;
  std::size_t title_holder_reads = 0, holder_fullid_reads = 0;
  std::size_t actor_fullid_reads = 0, contract_identity_reads = 0;
  std::size_t opinion_calls = 0, liege_calls = 0;

  template<class T> void Register(T& value) { ranges.emplace_back(&value, sizeof value); }

  World16(const Case16& selected, std::string_view assets)
      : allocator(std::string(assets)), test(selected) {
    current16 = this;
    fixture.slots.fill(std::byte{0});
    Put(fixture.characters[0].data(), 0x18, test.actor);
    Put(fixture.characters[1].data(), 0x18, kLeader);
    Put(fixture.player_entry.data(), 0xB0, test.actor);
    Put(holder.data(), 0x18, test.stale ? test.holder ^ 0x01000000U : test.holder);
    Put(fixture.slots.data(), (test.actor & 0x00FFFFFFU) * 0x10ULL + 8,
        fixture.characters[0].data());
    Put(fixture.slots.data(), (kLeader & 0x00FFFFFFU) * 0x10ULL + 8,
        fixture.characters[1].data());
    Put(fixture.slots.data(), (test.holder & 0x00FFFFFFU) * 0x10ULL + 8, holder.data());
    Put(fixture.characters[0].data(), 0x1C0, actor_land.data());
    Put(fixture.characters[1].data(), 0x1C0, leader_land.data());
    Put(holder.data(), 0x1C0, holder_land.data());
    Put(fixture.faction_type.data(), 0x18, kPopulist.data());
    Put(fixture.faction_type.data(), 0x28, std::uint64_t{kPopulist.size()});
    Put(fixture.faction_type.data(), 0x30, std::uint64_t{kPopulist.size()});
    allocator.Reset(0xFFFFFFFFU);
    faction = allocator.Allocate(fixture.faction_type.data(),
        std::bit_cast<std::int32_t>(test.actor), 29);
    m1_allocator_exec10::Require(Get<std::uint32_t>(faction, 0x10) == 0U &&
        Get<std::uint32_t>(faction, 0x40) == test.actor,
        "actual native faction allocation supplies ID and target");
    Put(faction, 0x28, std::int64_t{7'000'000});
    Put(faction, 0x44, kLeader);
    Put(faction, 0x48, static_cast<void*>(nullptr));
    Put(faction, 0x54, std::int32_t{0});
    Put(faction, 0x60, county_member.data());
    Put(faction, 0x6C, std::int32_t{1});
    Put(county_member.data(), 8, kCounty);
    Put(county_member.data(), 0x0C, std::uint8_t{1});
    Put(county_member.data(), 0x10, faction);
    targeting[0] = Get<std::int32_t>(faction, 0x10);
    Put(actor_land.data(), 0x120, targeting.data());
    Put(actor_land.data(), 0x12C, std::int32_t{1});
    Put(titles.data(), 0x20, title_slots.data());
    Put(titles.data(), 0x2C, std::int32_t{8});
    Put(title_slots.data(), 3U * 0x10U + 8, title.data());
    Put(title_slots.data(), 4U * 0x10U + 8, duchy.data());
    Put(title.data(), 0x10, kCounty);
    Put(title.data(), 0x48, county_definition.data());
    Put(title.data(), 0x108, kDuchy);
    Put(title.data(), 0x11C, std::int32_t{1});
    Put(title.data(), 0x128, test.absent ? 0xFFFFFFFFU : test.holder);
    Put(county_definition.data(), 0x64, std::int32_t{2});
    Put(duchy.data(), 0x10, kDuchy);
    Put(duchy.data(), 0x48, duchy_definition.data());
    Put(duchy.data(), 0x108, std::int32_t{-1});
    Put(duchy.data(), 0x110, children.data());
    Put(duchy.data(), 0x11C, std::int32_t{1});
    Put(duchy.data(), 0x128, test.actor);
    Put(duchy_definition.data(), 0x64, std::int32_t{3});
    Put(province.data(), 0x10, std::int32_t{99});
    Put(province.data(), 0x85C, std::uint32_t{0x50726F76});
    Put(province.data(), 0x848, county.data());
    Put(county.data(), 0x18, kCounty);
    if (test.surrender) {
      Put(actor_land.data(), 0x218, contract_ids.data());
      Put(actor_land.data(), 0x224, std::int32_t{1});
      Put(holder_land.data(), 0x1E0, held.data());
      Put(holder_land.data(), 0x1EC, std::int32_t{1});
      Put(contracts.data(), 0x20, contract_slots.data());
      Put(contracts.data(), 0x2C, std::int32_t{8});
      Put(contract_slots.data(), 0x18, contract.data());
      Put(contract.data(), 8, contract_ids[0]);
      Put(contract.data(), 0x20, holder.data());
    }
    Put(relation.data(), 0x20, std::int32_t{-1});
    fixture.faction_store_pointer = allocator.Storage();
    fixture.faction_fallback = allocator.Fallback();
    auto& env = fixture.factions;
    env.expected_faction_vtable = allocator.PrimaryVtable();
    env.character_fallback_slot = &empty;
    env.landed_title_storage_slot = &title_store;
    env.landed_title_fallback_slot = &empty;
    env.vassal_contract_storage_slot = &contract_store;
    env.vassal_contract_fallback_slot = &empty;
    env.title_province = &Province16;
    env.immediate_liege = &Liege16;
    env.county_observations_12003 = true;
    env.county_opinion = &Opinion16;
    env.surrender_observations_12003 = test.surrender;
    env.government = &Government16;
    env.government_allows_mask = &Mask16;
    env.pair_relation = &Relation16;
    env.state_faith_identifier = &state_faith;
    Register(fixture.state); Register(fixture.jomini); Register(fixture.players);
    Register(fixture.local); Register(fixture.player_entry); Register(fixture.entries);
    Register(fixture.store); Register(fixture.slots); Register(fixture.characters);
    Register(fixture.state_pointer); Register(fixture.jomini_pointer);
    Register(fixture.store_pointer); Register(fixture.faction_store_pointer);
    Register(fixture.faction_fallback); Register(fixture.faction_type);
    ranges.emplace_back(fixture.game_data.data(), fixture.game_data.size());
    Register(holder); Register(actor_land); Register(holder_land); Register(leader_land);
    Register(titles); Register(contracts); Register(contract); Register(title_slots);
    Register(contract_slots); Register(title); Register(duchy); Register(county_definition);
    Register(duchy_definition); Register(province); Register(county); Register(county_member);
    Register(government); Register(relation); Register(targeting); Register(held);
    Register(children); Register(contract_ids); Register(title_store); Register(contract_store);
    Register(empty); Register(state_faith);
    ranges.emplace_back(allocator.Storage(), 0x58U);
    ranges.emplace_back(Get<void*>(allocator.Storage(), 0x20), 1024U * 16U);
    ranges.emplace_back(allocator.FirstObject(), 0x34000U);
    ranges.emplace_back(allocator.Fallback(), 0xD0U);
    ranges.emplace_back(kPopulist.data(), kPopulist.size() + 1U);
    allocator.RequireOriginalCodeUnchanged();
  }
};

inline void* Province16(void* title) {
  return title == current16->title.data() ? current16->province.data() : nullptr;
}
inline void* Liege16(void* character) {
  ++current16->liege_calls;
  if (character == current16->holder.data() ||
      character == current16->fixture.characters[0].data())
    return current16->fixture.characters[0].data();
  return nullptr;
}
inline void* Government16(void*) { return current16->government.data(); }
inline void* Relation16(void*, void*) { return current16->relation.data(); }
inline std::int32_t Opinion16(void* county) {
  ++current16->opinion_calls;
  return county == current16->county.data() ? -17 : 100;
}
inline bool Memory16(void* context, const void* address, void* output,
                     std::size_t size) noexcept {
  auto& world = *static_cast<World16*>(context);
  const auto at = reinterpret_cast<std::uintptr_t>(address);
  for (const auto& [base, length] : world.ranges) {
    const auto begin = reinterpret_cast<std::uintptr_t>(base);
    if (at >= begin && at - begin <= length && size <= length - (at - begin)) {
      std::memcpy(output, address, size);
      if (address == world.title.data() + 0x128) ++world.title_holder_reads;
      if (address == world.holder.data() + 0x18) ++world.holder_fullid_reads;
      if (address == world.fixture.characters[0].data() + 0x18) ++world.actor_fullid_reads;
      if (address == world.contract.data() + 8) ++world.contract_identity_reads;
      return true;
    }
  }
  return false;
}
inline bool Frame16(void* context, game::PlayerFactionAlertsFrameV1& output) noexcept {
  auto& world = *static_cast<World16*>(context);
  CoreSnapshotPrefix core{};
  if (!xar::ck3_12004::ReadCoreSnapshot(world.fixture.core, core)) return false;
  output = {1, core.clock.date_raw, core.clock.paused, core.map_ready,
      core.has_played_character, core.played_character_alive, core.played_character_id};
  return true;
}

inline bool Run16(const Case16& test, const std::filesystem::path& output,
                  std::string_view assets) {
  World16 world(test, assets);
  auto access = world.fixture.faction_access;
  access.context = &world;
  access.capture_frame = &Frame16;
  access.read_memory = &Memory16;
  game::PlayerFactionAlertsV1 alerts{};
  const auto result = ReadPlayerFactionAlerts12004(world.fixture.factions, access, {1}, alerts);
  const bool available = result == game::ReadPlayerFactionAlertsResultV1::available;
  const auto wire = SerializePlayerFactionAlerts12004(alerts);
  const game::AdapterDescriptor descriptor{"ck3-1.20.0.4-msvc-x64", "1.20.0.4",
      kExecutableSha256, "county-character16-fixture", {}};
  const auto whole = SerializePlayerFactionAlertsWhole12004(alerts, 1,
      "county-character16", descriptor);
  const bool observation_missing = test.stale || test.absent;
  const bool reject = test.surrender && test.stale;
  const auto holder_id = std::bit_cast<std::int32_t>(test.holder);
  const auto actor_id = std::bit_cast<std::int32_t>(test.actor);
  bool observation_ok = false, surrender_ok = !test.surrender;
  if (available && alerts.targeting_factions.size() == 1U) {
    const auto& row = alerts.targeting_factions[0];
    if (row.county_member_observations.size() == 1U) {
      const auto& observed = row.county_member_observations[0];
      observation_ok = observation_missing
          ? !observed.holder_character_id && !observed.county_opinion &&
                observed.opinion_status == "unavailable" && world.opinion_calls == 0U
          : observed.holder_character_id == holder_id && observed.county_opinion == -17 &&
                observed.opinion_status == "available" && world.opinion_calls != 0U;
    }
    if (test.surrender && row.surrender_impact) {
      const auto& impact = *row.surrender_impact;
      surrender_ok = impact.status == "available" &&
          impact.player_subrealm_county_title_ids == std::vector<std::int32_t>{kCounty} &&
          impact.member_counties.size() == 1U && impact.seized_counties.size() == 1U &&
          impact.seized_duchies.size() == 1U && impact.ordinary_branch_title_sets_ready &&
          impact.county_loss_complete && impact.member_counties[0].holder_character_id == holder_id &&
          impact.member_counties[0].top_liege_character_id == actor_id &&
          impact.seized_counties[0].holder_character_id == holder_id &&
          impact.seized_counties[0].top_liege_character_id == actor_id &&
          world.contract_identity_reads != 0U && world.liege_calls != 0U;
    }
  }
  const auto holder_fragment = "\"holder_character_id\":" + std::to_string(holder_id);
  const auto top_fragment = "\"top_liege_character_id\":" + std::to_string(actor_id);
  const bool wire_ok = !wire.empty() && !whole.empty() &&
      (observation_missing || (wire.find(holder_fragment) != std::string::npos &&
                              whole.find(holder_fragment) != std::string::npos)) &&
      (!test.surrender || reject || (wire.find(top_fragment) != std::string::npos &&
                                    whole.find(top_fragment) != std::string::npos));
  const bool pass = reject
      ? !available && alerts.targeting_factions.empty() && !alerts.readiness.alert_ready
      : available && observation_ok && surrender_ok && wire_ok &&
            world.title_holder_reads != 0U &&
            (test.absent ? world.holder_fullid_reads == 0U : world.holder_fullid_reads != 0U);
  world.allocator.RequireOriginalCodeUnchanged();
  std::filesystem::create_directories(output);
  std::ofstream(output / "public-alerts.json") << wire;
  std::ofstream(output / "public-alerts-whole.json") << whole;
  std::ofstream summary(output / "SUMMARY16.json");
  summary << "{\"machine_id\":\"xenoamess-full-tower-eb9d2c1186\",\"case\":\""
      << test.name << "\",\"software_fixture\":true,\"character_ID_memory_authored\":true,"
      "\"Character_allocator_machinecode_executed\":false,\"raw_Faction_allocator_bytes\":865,"
      "\"actual_Faction_allocator_calls\":1,\"actual_Faction_target_raw\":" << test.actor
      << ",\"holder_raw\":" << test.holder << ",\"holder_signed\":" << holder_id
      << ",\"actor_signed\":" << actor_id << ",\"surrender_enabled\":" << test.surrender
      << ",\"stale_holder\":" << test.stale << ",\"absent_holder\":" << test.absent
      << ",\"available\":" << available << ",\"observation_ok\":" << observation_ok
      << ",\"surrender_ok\":" << surrender_ok << ",\"wire_ok\":" << wire_ok
      << ",\"title_holder_reads\":" << world.title_holder_reads
      << ",\"holder_fullid_reads\":" << world.holder_fullid_reads
      << ",\"actor_fullid_reads\":" << world.actor_fullid_reads
      << ",\"contract_fullid_reads\":" << world.contract_identity_reads
      << ",\"opinion_calls\":" << world.opinion_calls << ",\"liege_calls\":" << world.liege_calls
      << ",\"actual_reader_projector_public_and_whole_serializer\":true,"
      "\"authored_alerts_DTO\":false,\"public_Handle_executed\":false,"
      "\"private_Handler_executed\":false,\"passed\":" << pass << "}\n";
  std::cout << test.name << " available=" << available << " observation=" << observation_ok
      << " surrender=" << surrender_ok << " wire=" << wire_ok << " passed=" << pass << '\n';
  return pass;
}

inline int RunCountyCharacter16(int argc, char** argv) {
  if (argc != 4) return 90;
  try {
    const std::string_view selected(argv[1]);
    bool passed = true;
    bool found = false;
    for (const auto& test : kCases) {
      if (selected != "all" && selected != test.name) continue;
      found = true;
      passed = Run16(test, std::filesystem::path(argv[2]) / test.name, argv[3]) && passed;
    }
    return !found ? 91 : passed ? 0 : 1;
  } catch (const std::exception& error) {
    std::cerr << "CountyCharacter16: " << error.what() << '\n';
    return 2;
  }
}
} // namespace m1_county_character16
