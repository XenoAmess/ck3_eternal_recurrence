#include "xar_bridge/ck3_12004_default_routes_mailbox.hpp"
#include "xar_bridge/ck3_12004_features.hpp"
#include "xar_bridge/ck3_12004_tactical_daily_sentinel.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <unordered_map>
#include <utility>

namespace {

template <std::size_t Size> using Blob = std::array<std::byte, Size>;
template <typename Value, std::size_t Size>
void Store(Blob<Size> &blob, std::size_t offset, Value value) {
  std::memcpy(blob.data() + offset, &value, sizeof(value));
}
template <std::size_t Size>
void *Address(Blob<Size> &blob, std::size_t offset = 0) noexcept {
  return blob.data() + offset;
}

constexpr std::uintptr_t kImageBase = 0x140000000;
constexpr std::int32_t kDate = 53'236'608;
constexpr std::int32_t kPublicUnit = 83'886'367;
constexpr std::int32_t kInternalArmy = 50'331'794;
constexpr std::uint64_t kRevision = 11;
constexpr std::uint64_t kSequence = 7;
constexpr std::array<std::pair<std::uint32_t, std::string_view>, 44> kFeatures{{
    {0x3587, "garments_of_the_hre"},
    {0x3588, "fashion_of_the_abbasid_court"},
    {0x34A7, "the_northern_lords"},
    {0x3538, "hybridize_culture"},
    {0x3539, "diverge_culture"},
    {0x3270, "royal_court"},
    {0x366D, "reform_culture"},
    {0x34DC, "court_artifacts"},
    {0x3773, "the_fate_of_iberia"},
    {0x3608, "friends_and_foes"},
    {0x37CF, "tours_and_tournaments"},
    {0x37CE, "advanced_activities"},
    {0x36C4, "accolades"},
    {0x377A, "legacy_of_persia"},
    {0x35E0, "elegance_of_the_empire"},
    {0x394A, "wards_and_wardens"},
    {0x3B0A, "legends_of_the_dead"},
    {0x3A5B, "legends"},
    {0x3A09, "north_african_attire"},
    {0x3A08, "couture_of_the_capets"},
    {0x3953, "landless_playable"},
    {0x3A00, "admin_gov"},
    {0x3A02, "roads_to_power"},
    {0x3A01, "court_room_view"},
    {0x39DA, "wandering_nobles"},
    {0x3CBB, "west_slavic_attire"},
    {0x3A07, "medieval_monuments"},
    {0x3C98, "khans_of_the_steppe"},
    {0x3CA1, "nomads"},
    {0x3A06, "arctic_attire"},
    {0x39F7, "crowns_of_the_world"},
    {0x3D67, "landless_adventurer"},
    {0x39ED, "coronations"},
    {0x39EE, "all_under_heaven"},
    {0x39EF, "merit_admin"},
    {0x39F0, "advanced_aspirations"},
    {0x39DB, "high_medieval_warfare_attire"},
    {0x39DC, "holy_buildings"},
    {0x39DD, "north_pacific_attire"},
    {0x39DE, "east_asian_wonders"},
    {0x39DF, "celestial_court_attire"},
    {0x4101, "symbols_of_authority"},
    {0x4102, "songs_of_the_realm"},
    {0x4169, "by_god_alone"},
}};

struct FeatureFixture {
  Blob<0x2C0> root{};
  Blob<0x20> dlc_set{};
  std::array<Blob<0x28>, 4> buckets{};
  std::array<std::uint32_t, 44> enum_table{};
  std::array<std::string, 44> names{};
  std::unordered_map<const void *, std::string> native_strings;
  void *root_pointer = root.data();
  xar::game::LoadedFeatureManifestFrameV1 frame{};
  std::uint32_t captures = 0;

  FeatureFixture() {
    Store(root, 0x2B0, (std::uint64_t{1} << 0) |
        (std::uint64_t{1} << 5) | (std::uint64_t{1} << 43));
    Store(root, 0x2B8, std::int32_t{3});
    for (std::size_t index = 0; index < kFeatures.size(); ++index) {
      enum_table[index] = kFeatures[index].first;
      names[index] = kFeatures[index].second;
      native_strings.emplace(&names[index], names[index]);
    }
    Store(dlc_set, 0x08, static_cast<void *>(buckets.data()));
    Store(dlc_set, 0x14, std::uint32_t{3});
    Store(dlc_set, 0x18, std::uint8_t{0});
    const std::array<std::pair<std::size_t, std::string>, 3> keys{{
        {0, "The Royal Court"},
        {1, std::string("\xC3\x89", 2) + " Pack"},
        {3, "A Flavor Pack"},
    }};
    for (const auto &[index, key] : keys) {
      Store(buckets[index], 0x04, std::uint8_t{1});
      native_strings.emplace(Address(buckets[index], 0x08), key);
    }
    frame.snapshot_revision = kRevision;
    frame.date_raw = kDate;
    frame.paused = true;
    frame.map_ready = true;
  }
};
FeatureFixture *g_features = nullptr;

const std::string *__fastcall ResolveName(std::int32_t id) noexcept {
  if (g_features == nullptr) return nullptr;
  for (std::size_t index = 0; index < kFeatures.size(); ++index) {
    if (static_cast<std::int32_t>(kFeatures[index].first) == id) {
      return &g_features->names[index];
    }
  }
  return nullptr;
}
bool CaptureFeatureFrame(void *context,
    xar::game::LoadedFeatureManifestFrameV1 &output) noexcept {
  auto &fixture = *static_cast<FeatureFixture *>(context);
  ++fixture.captures;
  output = fixture.frame;
  return true;
}
bool OnMainThread(void *) noexcept { return true; }
bool ReadFeatureMemory(void *, const void *address, void *output,
    std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) return false;
  std::memcpy(output, address, size);
  return true;
}
bool ReadFeatureString(void *context, const void *address,
    std::string &output) noexcept {
  const auto &fixture = *static_cast<FeatureFixture *>(context);
  const auto found = fixture.native_strings.find(address);
  if (found == fixture.native_strings.end()) return false;
  output = found->second;
  return true;
}

struct ComponentStorage {
  Blob<0x40> header{};
  Blob<512 * 0x10> slots{};
  void *pointer = header.data();
  ComponentStorage() {
    Store(header, 0x20, static_cast<void *>(slots.data()));
    Store(header, 0x2C, std::int32_t{512});
  }
  void Add(std::int32_t id, void *object) {
    const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
    Store(slots, static_cast<std::size_t>(index) * 0x10 + 0x08, object);
  }
};

struct SentinelFixture {
  Blob<0x100> game_state{};
  Blob<0x100> jomini{};
  Blob<0x100> player{};
  Blob<0x220> unit{};
  Blob<0x180> army{};
  ComponentStorage units;
  ComponentStorage armies;
  ComponentStorage combats;
  void *game_state_pointer = game_state.data();
  void *jomini_pointer = jomini.data();
  std::uint32_t pause_calls = 0;
  std::uint32_t original_calls = 0;

  SentinelFixture() {
    Store(game_state, 0x08, kDate);
    Store(jomini, 0x20, std::uint8_t{1});
    Store(player, 0x70, std::int32_t{7});
    Store(unit, 0x10, kPublicUnit);
    Store(unit, 0x18, std::int32_t{0});
    Store(unit, 0x30, static_cast<void *>(nullptr));
    Store(unit, 0x170, std::int32_t{0});
    Store(unit, 0x174, std::int32_t{29'829});
    Store(unit, 0x178, kInternalArmy);
    Store(army, 0x10, kInternalArmy);
    Store(army, 0x120, std::int32_t{30'000});
    Store(army, 0x124, kPublicUnit);
    Store(army, 0x128, std::int32_t{-1});
    units.Add(kPublicUnit, unit.data());
    armies.Add(kInternalArmy, army.data());
  }
};
SentinelFixture *g_sentinel = nullptr;

void *__fastcall GetLocalPlayer(void *) noexcept {
  return g_sentinel == nullptr ? nullptr : g_sentinel->player.data();
}
void __fastcall SetPaused(void *, bool, std::int32_t) noexcept {
  if (g_sentinel != nullptr) ++g_sentinel->pause_calls;
}
void __fastcall OriginalDay() noexcept {
  if (g_sentinel != nullptr) ++g_sentinel->original_calls;
}

bool Write(const std::filesystem::path &directory,
    std::string_view name, const std::string &packet) {
  if (packet.empty()) return false;
  std::ofstream stream(directory / name, std::ios::binary);
  stream << packet << '\n';
  return stream.good();
}

bool ProduceFeaturePacket(const std::filesystem::path &directory) {
  using namespace xar::ck3_12004;
  FeatureFixture fixture;
  g_features = &fixture;
  auto environment = BindLoadedFeatureManifestNativeEnvironmentV1(kImageBase, true);
  if (reinterpret_cast<std::uintptr_t>(environment.feature_root_slot) !=
          kImageBase + kLoadedFeatureRootSlotRva ||
      reinterpret_cast<std::uintptr_t>(environment.feature_enum_table) !=
          kImageBase + kLoadedFeatureEnumTableRva ||
      reinterpret_cast<std::uintptr_t>(environment.script_dlc_set) !=
          kImageBase + kLoadedFeatureScriptDlcSetRva ||
      reinterpret_cast<std::uintptr_t>(environment.script_identifier_name) !=
          kImageBase + kLoadedFeatureScriptIdentifierNameRva) return false;
  const auto rejected = BindLoadedFeatureManifestNativeEnvironmentV1(kImageBase, false);
  if (rejected.feature_root_slot != nullptr) return false;
  environment.offline_fixture_function_overrides = true;
  environment.feature_root_slot = &fixture.root_pointer;
  environment.feature_enum_table = fixture.enum_table.data();
  environment.script_dlc_set = fixture.dlc_set.data();
  environment.script_identifier_name = &ResolveName;
  LoadedFeatureManifestAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &CaptureFeatureFrame;
  access.is_main_thread = &OnMainThread;
  access.read_memory = &ReadFeatureMemory;
  access.read_string = &ReadFeatureString;
  xar::game::LoadedFeatureManifestV1 manifest{};
  const auto before_root = fixture.root;
  const auto before_set = fixture.dlc_set;
  const auto before_buckets = fixture.buckets;
  if (ReadLoadedFeatureManifestV1(environment, access,
          LoadedFeatureManifestRequestV1{kRevision}, manifest) !=
      xar::game::ReadLoadedFeatureManifestResultV1::available ||
      fixture.captures != 2 ||
      manifest.effective_feature_flags.items.size() != 44 ||
      manifest.script_dlc_keys.keys.size() != 3 ||
      !manifest.readiness.actionable_ready ||
      manifest.readiness.entitlements_ready ||
      fixture.root != before_root || fixture.dlc_set != before_set ||
      fixture.buckets != before_buckets) return false;
  return Write(directory, "01-loaded-feature-manifest.json",
      SerializeLoadedFeatureManifestResult12004("fixture-manifest", kSequence, manifest));
}

bool ProduceSentinelPackets(const std::filesystem::path &directory) {
  using namespace xar::ck3_11906;
  SentinelFixture fixture;
  g_sentinel = &fixture;
  auto bindings = xar::ck3_12004::BindTacticalDailySentinelImage12004(
      kImageBase, xar::ck3_12004::kExecutableSha256);
  if (!bindings.enabled ||
      reinterpret_cast<std::uintptr_t>(bindings.game_state_slot) !=
          kImageBase + xar::ck3_12004::kGameStateSlotRva ||
      reinterpret_cast<std::uintptr_t>(bindings.jomini_state_slot) !=
          kImageBase + xar::ck3_12004::kJominiStateSlotRva ||
      reinterpret_cast<std::uintptr_t>(bindings.army_storage_slot) !=
          kImageBase + xar::ck3_12004::kTacticalSentinelUnitStorageSlotRva12004 ||
      reinterpret_cast<std::uintptr_t>(bindings.army_internal_storage_slot) !=
          kImageBase + xar::ck3_12004::kTacticalSentinelArmyStorageSlotRva12004 ||
      reinterpret_cast<std::uintptr_t>(bindings.combat_storage_slot) !=
          kImageBase + xar::ck3_12004::kTacticalSentinelCombatStorageSlotRva12004) return false;
  if (xar::ck3_12004::BindTacticalDailySentinelImage12004(
          kImageBase, "unadmitted").enabled) return false;
  bindings.game_state_slot = &fixture.game_state_pointer;
  bindings.jomini_state_slot = &fixture.jomini_pointer;
  bindings.army_storage_slot = &fixture.units.pointer;
  bindings.army_internal_storage_slot = &fixture.armies.pointer;
  bindings.combat_storage_slot = &fixture.combats.pointer;
  bindings.get_local_player = &GetLocalPlayer;
  const auto before_game = fixture.game_state;
  const auto before_jomini = fixture.jomini;
  const auto before_unit = fixture.unit;
  const auto before_army = fixture.army;
  if (!xar::ck3_12004::InitializeTacticalDailySentinelFixture12004(
          bindings, xar::ck3_12004::kExecutableSha256, &SetPaused, &OriginalDay)) return false;
  constexpr std::string_view arm_step =
      "research-arm-tactical-daily-sentinel-v1-53236608-to-53236632-speed-1-mode-terminal-a-1-83886367";
  TacticalDailySentinelArmRequestV1 request{};
  if (!ParseTacticalDailySentinelArmStepV1(arm_step, request)) return false;
  const auto arm_result = ArmTacticalDailySentinelV1(request);
  const auto armed = ReadTacticalDailySentinelStatusV1();
  if (arm_result != TacticalDailySentinelArmStatusV1::armed ||
      armed.state != TacticalDailySentinelStateV1::armed ||
      armed.generation != 1 || armed.army_count != 1 || armed.combat_count != 0 ||
      armed.starting_date_raw != kDate || armed.target_date_raw != kDate + 24 ||
      armed.completed_daily_ticks != 0 || armed.trigger_flags != 0) return false;
  if (!Write(directory, "02-sentinel-arm.json",
          xar::ck3_12004::SerializeTacticalDailySentinelArmResult12004(
              "fixture-arm", arm_step, arm_result, armed))) return false;
  constexpr std::string_view cancel_step =
      "research-cancel-tactical-daily-sentinel-v1-generation-1";
  std::uint64_t generation = 0;
  if (!ParseTacticalDailySentinelCancelStepV1(cancel_step, generation)) return false;
  const auto cancel_result = CancelTacticalDailySentinelV1(generation);
  const auto idle = ReadTacticalDailySentinelStatusV1();
  if (cancel_result != TacticalDailySentinelCancelStatusV1::canceled ||
      idle.state != TacticalDailySentinelStateV1::idle ||
      idle.generation != armed.generation ||
      idle.starting_date_raw != armed.starting_date_raw ||
      idle.target_date_raw != armed.target_date_raw ||
      idle.army_count != armed.army_count ||
      fixture.pause_calls != 0 || fixture.original_calls != 0 ||
      fixture.game_state != before_game || fixture.jomini != before_jomini ||
      fixture.unit != before_unit || fixture.army != before_army) return false;
  return Write(directory, "03-sentinel-cancel.json",
      xar::ck3_12004::SerializeTacticalDailySentinelCancelResult12004(
          "fixture-cancel", cancel_step, cancel_result)) &&
      Write(directory, "04-sentinel-status-idle.json",
          xar::ck3_12004::SerializeTacticalDailySentinelResult12004(
              "fixture-status", kTacticalDailySentinelStatusStepV1, idle));
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 2) {
    std::cerr << "Expected one output directory\n";
    return 2;
  }
  const std::filesystem::path directory(argv[1]);
  std::filesystem::create_directories(directory);
  if (!ProduceFeaturePacket(directory) || !ProduceSentinelPackets(directory)) {
    std::cerr << "Actual4 default route whole producer failed\n";
    return 1;
  }
  if (!Write(directory, "FIXTURE-PROVENANCE.json",
      "{\"schema\":\"actual4-default-routes-fixture-provenance-v1\","
      "\"producer\":\"xar_ck3_12004_default_manifest_sentinel_test\","
      "\"whole_packets\":4,\"synthetic_memory\":true,\"synthetic_callbacks\":true,"
      "\"native_functions_invoked_in_game\":false,\"detour_installed\":false,"
      "\"native_collector_and_arm_cancel_used\":true,"
      "\"date_advanced\":false,\"pause_callback_calls\":0,"
      "\"original_tick_calls\":0,\"watched_public_cunit_id\":83886367,"
      "\"native_carmy_id\":50331794,\"fixture_native_player_id\":7,"
      "\"public_paused_player_character_id\":29829}")) return 1;
  std::cout << "Actual4 default manifest/sentinel: 4 genuine whole packets\n";
  return 0;
}
