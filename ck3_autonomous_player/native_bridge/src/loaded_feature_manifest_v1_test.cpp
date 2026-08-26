#include "xar_bridge/loaded_feature_manifest_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

template <std::size_t Size>
using Blob = std::array<std::byte, Size>;

template <std::size_t Size, typename Value>
void Put(Blob<Size> &blob, std::size_t offset, const Value &value) {
  if (offset + sizeof(value) > blob.size()) {
    std::abort();
  }
  std::memcpy(blob.data() + offset, &value, sizeof(value));
}

template <std::size_t Size>
void *Address(Blob<Size> &blob, std::size_t offset = 0) noexcept {
  return blob.data() + offset;
}

constexpr std::array<std::pair<std::uint32_t, std::string_view>, 44>
    kFeatures{{
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
        {0x39F1, "barter_troops"},
        {0x39DB, "high_medieval_warfare_attire"},
        {0x39DC, "holy_buildings"},
        {0x39DD, "north_pacific_attire"},
        {0x39DE, "east_asian_wonders"},
        {0x39DF, "celestial_court_attire"},
        {0x4101, "symbols_of_authority"},
        {0x4102, "songs_of_the_realm"},
    }};

struct Fixture;
Fixture *g_fixture = nullptr;

struct Fixture {
  alignas(void *) Blob<0x2C0> feature_root{};
  alignas(void *) Blob<0x20> script_dlc_set{};
  alignas(void *) std::array<Blob<0x28>, 4> buckets{};
  std::array<std::uint32_t, 44> enum_table{};
  std::array<std::string, 44> feature_names{};
  void *feature_root_slot = nullptr;
  xar::game::LoadedFeatureManifestFrameV1 frame{};
  std::unordered_map<const void *, std::string> native_strings;
  bool main_thread = true;
  bool change_frame_on_second_capture = false;
  std::uint32_t capture_calls = 0;

  Fixture() {
    feature_root_slot = Address(feature_root);
    const std::uint64_t bits =
        (std::uint64_t{1} << 0) | (std::uint64_t{1} << 5) |
        (std::uint64_t{1} << 43);
    const std::int32_t enabled_count = 3;
    Put(feature_root, 0x2B0, bits);
    Put(feature_root, 0x2B8, enabled_count);
    for (std::size_t index = 0; index < kFeatures.size(); ++index) {
      enum_table[index] = kFeatures[index].first;
      feature_names[index] = kFeatures[index].second;
      native_strings.emplace(&feature_names[index], feature_names[index]);
    }

    void *bucket_base = buckets.data();
    Put(script_dlc_set, 0x08, bucket_base);
    const std::uint32_t mask = 3;
    Put(script_dlc_set, 0x14, mask);
    const std::uint8_t spill = 0;
    Put(script_dlc_set, 0x18, spill);
    const std::array<std::pair<std::size_t, std::string>, 3> dlcs{{
        {0, "The Royal Court"},
        {1, std::string("\xC3\x89", 2) + " Pack"},
        {3, "A Flavor Pack"},
    }};
    for (const auto &[index, key] : dlcs) {
      const std::uint8_t occupied = 1;
      Put(buckets[index], 0x04, occupied);
      native_strings.emplace(Address(buckets[index], 0x08), key);
    }

    frame.snapshot_revision = 91;
    frame.date_raw = 54'321;
    frame.paused = true;
    frame.map_ready = true;
    g_fixture = this;
  }
};

const std::string *__fastcall ResolveIdentifierName(
    std::int32_t identifier) noexcept {
  if (g_fixture == nullptr) {
    return nullptr;
  }
  for (std::size_t index = 0; index < kFeatures.size(); ++index) {
    if (static_cast<std::int32_t>(kFeatures[index].first) == identifier) {
      return &g_fixture->feature_names[index];
    }
  }
  return nullptr;
}

bool CaptureFrame(
    void *opaque,
    xar::game::LoadedFeatureManifestFrameV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.capture_calls;
  output = fixture.frame;
  if (fixture.change_frame_on_second_capture && fixture.capture_calls >= 2) {
    ++output.date_raw;
  }
  return true;
}

bool IsMainThread(void *opaque) noexcept {
  return static_cast<Fixture *>(opaque)->main_thread;
}

bool ReadMemory(void *, const void *address, void *output,
                std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
  std::memcpy(output, address, size);
  return true;
}

bool ReadString(void *opaque, const void *address,
                std::string &output) noexcept {
  const auto &fixture = *static_cast<Fixture *>(opaque);
  const auto found = fixture.native_strings.find(address);
  if (found == fixture.native_strings.end()) {
    output.clear();
    return false;
  }
  output = found->second;
  return true;
}

xar::ck3_11906::LoadedFeatureManifestNativeEnvironmentV1
Environment(Fixture &fixture) {
  xar::ck3_11906::LoadedFeatureManifestNativeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.offline_fixture_function_overrides = true;
  environment.feature_root_slot = &fixture.feature_root_slot;
  environment.script_dlc_set = Address(fixture.script_dlc_set);
  environment.feature_enum_table = fixture.enum_table.data();
  environment.script_identifier_name = &ResolveIdentifierName;
  return environment;
}

xar::ck3_11906::LoadedFeatureManifestAccessV1 Access(Fixture &fixture) {
  xar::ck3_11906::LoadedFeatureManifestAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &CaptureFrame;
  access.is_main_thread = &IsMainThread;
  access.read_memory = &ReadMemory;
  access.read_string = &ReadString;
  return access;
}

bool ClearedUnavailable(
    const xar::game::LoadedFeatureManifestV1 &value,
    std::string_view reason) {
  return value.status ==
             xar::game::LoadedFeatureManifestStatusV1::unavailable &&
         value.snapshot_revision == 91 && value.date_raw == 54'321 &&
         value.unavailable_reason == reason &&
         value.effective_feature_flags.status ==
             xar::game::LoadedFeatureComponentStatusV1::unavailable &&
         !value.effective_feature_flags.native_count.has_value() &&
         value.effective_feature_flags.items.empty() &&
         value.effective_feature_flags.unavailable_reason == reason &&
         value.script_dlc_keys.status ==
             xar::game::LoadedFeatureComponentStatusV1::unavailable &&
         !value.script_dlc_keys.enumerated_count.has_value() &&
         value.script_dlc_keys.keys.empty() &&
         value.script_dlc_keys.unavailable_reason == reason &&
         !value.readiness.effective_feature_flags_ready &&
         !value.readiness.script_dlc_keys_ready &&
         !value.readiness.entitlements_ready &&
         !value.readiness.same_frame_ready &&
         !value.readiness.actionable_ready;
}

bool TestAvailableAndSerializer() {
  Fixture fixture;
  const auto environment = Environment(fixture);
  const auto access = Access(fixture);
  const xar::ck3_11906::LoadedFeatureManifestRequestV1 request{91};
  xar::game::LoadedFeatureManifestV1 result{};
  if (xar::ck3_11906::ReadLoadedFeatureManifestV1(
          environment, access, request, result) !=
          xar::game::ReadLoadedFeatureManifestResultV1::available ||
      result.status !=
          xar::game::LoadedFeatureManifestStatusV1::available ||
      result.snapshot_revision != 91 || result.date_raw != 54'321 ||
      !result.unavailable_reason.empty() ||
      result.effective_feature_flags.native_count != 44 ||
      result.effective_feature_flags.items.size() != 44 ||
      !result.effective_feature_flags.items[0].enabled ||
      result.effective_feature_flags.items[1].enabled ||
      !result.effective_feature_flags.items[5].enabled ||
      !result.effective_feature_flags.items[43].enabled ||
      result.effective_feature_flags.items[43].key != "songs_of_the_realm" ||
      result.script_dlc_keys.enumerated_count != 3 ||
      !result.readiness.effective_feature_flags_ready ||
      !result.readiness.script_dlc_keys_ready ||
      result.readiness.entitlements_ready ||
      !result.readiness.same_frame_ready ||
      !result.readiness.actionable_ready) {
    return false;
  }
  const std::vector<std::string> expected_keys{
      "A Flavor Pack", "The Royal Court",
      std::string("\xC3\x89", 2) + " Pack"};
  if (result.script_dlc_keys.keys != expected_keys) {
    return false;
  }
  const auto json =
      xar::ck3_11906::SerializeLoadedFeatureManifestV1(result);
  if (json.empty() ||
      json.find("\"schema\":\"loaded-feature-manifest-v1\"") ==
          std::string::npos ||
      json.find("\"native_count\":44") == std::string::npos ||
      json.find("\"key\":\"songs_of_the_realm\",\"enabled\":true") ==
          std::string::npos ||
      json.find("\"entitlements\":{\"status\":\"unavailable\"") ==
          std::string::npos ||
      json.find("\"actionable_ready\":true") == std::string::npos) {
    return false;
  }
  auto invalid = result;
  std::swap(invalid.script_dlc_keys.keys.front(),
            invalid.script_dlc_keys.keys.back());
  return xar::ck3_11906::SerializeLoadedFeatureManifestV1(invalid).empty();
}

bool TestTypedUnavailablePaths() {
  const xar::ck3_11906::LoadedFeatureManifestRequestV1 request{91};

  Fixture counter_fixture;
  const std::int32_t wrong_count = 4;
  Put(counter_fixture.feature_root, 0x2B8, wrong_count);
  auto environment = Environment(counter_fixture);
  auto access = Access(counter_fixture);
  xar::game::LoadedFeatureManifestV1 result{};
  if (xar::ck3_11906::ReadLoadedFeatureManifestV1(
          environment, access, request, result) !=
          xar::game::ReadLoadedFeatureManifestResultV1::unavailable ||
      !ClearedUnavailable(result, "feature_counter_mismatch") ||
      xar::ck3_11906::SerializeLoadedFeatureManifestV1(result).empty()) {
    return false;
  }

  Fixture registry_fixture;
  ++registry_fixture.enum_table[4];
  environment = Environment(registry_fixture);
  access = Access(registry_fixture);
  result = {};
  if (xar::ck3_11906::ReadLoadedFeatureManifestV1(
          environment, access, request, result) !=
          xar::game::ReadLoadedFeatureManifestResultV1::unavailable ||
      !ClearedUnavailable(result, "feature_registry_drift")) {
    return false;
  }

  Fixture changed_fixture;
  changed_fixture.change_frame_on_second_capture = true;
  environment = Environment(changed_fixture);
  access = Access(changed_fixture);
  result = {};
  if (xar::ck3_11906::ReadLoadedFeatureManifestV1(
          environment, access, request, result) !=
          xar::game::ReadLoadedFeatureManifestResultV1::unavailable ||
      !ClearedUnavailable(result, "state_changed")) {
    return false;
  }

  Fixture unsupported_fixture;
  environment = Environment(unsupported_fixture);
  environment.exact_build_admitted = false;
  access = Access(unsupported_fixture);
  result = {};
  return xar::ck3_11906::ReadLoadedFeatureManifestV1(
             environment, access, request, result) ==
             xar::game::ReadLoadedFeatureManifestResultV1::unavailable &&
         ClearedUnavailable(result, "unsupported_build");
}

} // namespace

int main() {
  if (!TestAvailableAndSerializer()) {
    std::cerr << "loaded-feature reader/serializer fixture failed\n";
    return 1;
  }
  if (!TestTypedUnavailablePaths()) {
    std::cerr << "loaded-feature unavailable fixture failed\n";
    return 1;
  }
  std::cout << "loaded-feature-manifest-v1 reader fixture passed\n";
  return 0;
}
