#include "native_liege17.hpp"
#include "county_character16.hpp"

namespace {
using namespace m1_county_character16;
const void* duplicate_id_address = nullptr;
std::size_t duplicate_id_reads = 0;
bool Memory17(void* context, const void* address, void* output, std::size_t size) noexcept {
  if (address == duplicate_id_address && size == sizeof(std::uint32_t)) ++duplicate_id_reads;
  return Memory16(context, address, output, size);
}

bool Run(std::string_view name, std::uint32_t actor, std::uint32_t holder,
         bool mismatched_liege, const char* raw, const std::filesystem::path& out,
         const char* assets) {
  const Case16 test{name, actor, holder, true, false, false};
  World16 world(test, assets);
  m1_native_liege17::NativeLiegeImage17 getter(raw);
  std::array<std::byte, 0x30> actor_node{}, holder_node{}, leader_node{}, mismatch_node{};
  std::array<std::byte, 0x1D8> mismatch_holder{}, duplicate_actor{};
  std::array<std::byte, 0x230> mismatch_land{};
  constexpr std::uint32_t mismatch_holder_id = 0x06000005U;
  const auto character = world.fixture.characters[0].data();
  Put(character, 0x1C, std::uint32_t{0x43686172});
  Put(world.holder.data(), 0x1C, std::uint32_t{0x43686172});
  Put(world.fixture.characters[1].data(), 0x1C, std::uint32_t{0x43686172});
  Put(world.actor_land.data(), 0x1C0, actor_node.data());
  Put(world.holder_land.data(), 0x1C0, holder_node.data());
  Put(world.leader_land.data(), 0x1C0, leader_node.data());
  Put(actor_node.data(), 0x28, character);
  Put(holder_node.data(), 0x28, character);
  Put(leader_node.data(), 0x28, world.fixture.characters[1].data());
  world.Register(actor_node); world.Register(holder_node); world.Register(leader_node);
  world.Register(mismatch_node); world.Register(mismatch_holder);
  world.Register(duplicate_actor); world.Register(mismatch_land);
  getter.SetStorage(world.fixture.store.data());
  getter.SetFallback(nullptr);
  auto& env = world.fixture.factions;
  env.immediate_liege = getter.function();

  if (mismatched_liege) {
    Put(mismatch_holder.data(), 0x18, mismatch_holder_id);
    Put(mismatch_holder.data(), 0x1C, std::uint32_t{0x43686172});
    Put(mismatch_holder.data(), 0x1C0, mismatch_land.data());
    Put(mismatch_land.data(), 0x1C0, mismatch_node.data());
    Put(mismatch_node.data(), 0x28, duplicate_actor.data());
    Put(duplicate_actor.data(), 0x18, actor);
    Put(duplicate_actor.data(), 0x1C, std::uint32_t{0x43686172});
    Put(world.fixture.slots.data(), (mismatch_holder_id & 0x00FFFFFFU) * 0x10ULL + 8,
        mismatch_holder.data());
    Put(world.duchy.data(), 0x128, mismatch_holder_id);
    m1_native_liege17::Require(getter.call(mismatch_holder.data()) == duplicate_actor.data(),
        "actual landed getter returns unregistered duplicate actor pointer");
    m1_native_liege17::Require(Get<void*>(world.fixture.slots.data(),
        (actor & 0x00FFFFFFU) * 0x10ULL + 8) == character,
        "actual character storage retains different actor pointer");
  } else {
    m1_native_liege17::Require(getter.call(world.holder.data()) == character,
        "actual native landed holder getter reaches actor");
    m1_native_liege17::Require(getter.call(character) == character,
        "actual native independent landed actor returns self");
  }

  duplicate_id_address = duplicate_actor.data() + 0x18;
  duplicate_id_reads = 0;
  auto access = world.fixture.faction_access;
  access.context = &world;
  access.capture_frame = &Frame16;
  access.read_memory = &Memory17;
  game::PlayerFactionAlertsV1 alerts{};
  const auto result = ReadPlayerFactionAlerts12004(env, access, {1}, alerts);
  const bool available = result == game::ReadPlayerFactionAlertsResultV1::available;
  const auto wire = SerializePlayerFactionAlerts12004(alerts);
  const game::AdapterDescriptor descriptor{"ck3-1.20.0.4-msvc-x64", "1.20.0.4",
      kExecutableSha256, "native-liege17-fixture", {}};
  const auto whole = SerializePlayerFactionAlertsWhole12004(alerts, 1,
      "native-liege17", descriptor);
  bool impact_ok = false, refusal_ok = false;
  if (available && alerts.targeting_factions.size() == 1 &&
      alerts.targeting_factions[0].surrender_impact) {
    const auto& impact = *alerts.targeting_factions[0].surrender_impact;
    impact_ok = impact.status == "available" && impact.member_counties.size() == 1 &&
        impact.seized_counties.size() == 1 && impact.seized_duchies.size() == 1 &&
        impact.member_counties[0].holder_character_id == std::bit_cast<std::int32_t>(holder) &&
        impact.member_counties[0].top_liege_character_id == std::bit_cast<std::int32_t>(actor);
    refusal_ok = impact.status == "unavailable" &&
        impact.unavailable_reason == "surrender_title_collection_unavailable" &&
        !impact.ordinary_branch_title_sets_ready && !impact.county_loss_complete &&
        impact.player_subrealm_county_title_ids.empty() && impact.member_counties.empty() &&
        impact.seized_counties.empty() && impact.seized_duchies.empty();
  }
  const auto actor_fragment = "\"top_liege_character_id\":" +
      std::to_string(std::bit_cast<std::int32_t>(actor));
  const auto holder_fragment = "\"holder_character_id\":" +
      std::to_string(std::bit_cast<std::int32_t>(holder));
  const bool wire_ok = !wire.empty() && !whole.empty() &&
      wire.find(actor_fragment) != std::string::npos &&
      whole.find(actor_fragment) != std::string::npos &&
      wire.find(holder_fragment) != std::string::npos &&
      whole.find(holder_fragment) != std::string::npos;
  const bool pass = mismatched_liege
      ? available && refusal_ok && duplicate_id_reads > 0 &&
          wire.find("surrender_title_collection_unavailable") != std::string::npos &&
          whole.find("surrender_title_collection_unavailable") != std::string::npos
      : available && impact_ok && wire_ok;
  getter.RequireOriginalCodeUnchanged();
  world.allocator.RequireOriginalCodeUnchanged();
  std::filesystem::create_directories(out);
  std::ofstream(out / "public-alerts.json") << wire;
  std::ofstream(out / "public-alerts-whole.json") << whole;
  std::ofstream summary(out / "SUMMARY17.json");
  summary << "{\"case\":\"" << name << "\",\"passed\":" << pass
      << ",\"available\":" << available << ",\"impact_ok\":" << impact_ok
      << ",\"impact_refusal_ok\":" << refusal_ok
      << ",\"wire_ok\":" << wire_ok << ",\"duplicate_ID_reads\":" << duplicate_id_reads
      << ",\"raw_getter118B_executed\":true,\"getter_bytes_unchanged\":true,"
      "\"native_getter_replaces_authored_liege_callback\":true,"
      "\"actual_Core_reader_projector_public_whole\":true,"
      "\"other_callbacks_authored\":true,\"Character_allocator_executed\":false,"
      "\"Game_operations\":0}\n";
  std::cout << name << " available=" << available << " impact=" << impact_ok
      << " wire=" << wire_ok << " duplicate_ID_reads=" << duplicate_id_reads
      << " passed=" << pass << '\n';
  return pass;
}
} // namespace


// New CI137 entry supplied by the model follows.

int FactionFullIdNativeLiegeMain17(int argc, char** argv) {
  if (argc != 5) return 90;
  const std::string_view selector(argv[1]);
  if (selector != "holder-zero" && selector != "top-min" && selector != "roundtrip-refusal") return 91;
  try {
    const std::filesystem::path out = std::filesystem::path(argv[2]) / selector;
    const std::string_view assets(argv[3]);
    const std::string_view raw(argv[4]);
    bool passed = false;
    if (selector == "holder-zero") {
      passed = Run("native-landed-county-holder-zero", kActor, 0U, false, raw.data(), out, assets.data());
    } else if (selector == "top-min") {
      passed = Run("native-landed-top-min", 0x80000000U, kPositiveHolder, false, raw.data(), out, assets.data());
    } else if (selector == "roundtrip-refusal") {
      passed = Run("native-landed-return-not-roundtrip", kActor, 0U, true, raw.data(), out, assets.data());
    }
    return passed ? 0 : 1;
  } catch (const std::exception&) {
    return 2;
  }
}
