#include "xar_bridge/loaded_feature_manifest_v1.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>
#include <string>
#include <utility>

namespace xar::ck3_11906 {
namespace {

constexpr std::size_t kFeatureBitsetOffset = 0x2B0;
constexpr std::size_t kFeatureEnabledCountOffset = 0x2B8;
constexpr std::size_t kScriptDlcBucketBaseOffset = 0x08;
constexpr std::size_t kScriptDlcBucketMaskOffset = 0x14;
constexpr std::size_t kScriptDlcMaximumSpillOffset = 0x18;
constexpr std::size_t kScriptDlcBucketStride = 0x28;
constexpr std::size_t kScriptDlcBucketControlOffset = 0x04;
constexpr std::size_t kScriptDlcBucketKeyOffset = 0x08;
constexpr std::size_t kMsvcStringSizeOffset = 0x10;
constexpr std::size_t kMsvcStringCapacityOffset = 0x18;
constexpr std::size_t kMsvcStringInlineCapacity = 0x0F;
constexpr std::size_t kMaximumStableKeyBytes = 1'024;
constexpr std::uint32_t kMaximumScriptDlcBucketMask = 1'048'575;
constexpr std::size_t kMaximumScriptDlcPhysicalBuckets = 1'048'832;

struct FeatureDefinitionV1 {
  std::uint32_t cstring_id;
  std::string_view key;
};

constexpr std::array<FeatureDefinitionV1, kLoadedFeatureNativeCount>
    kFeatureDefinitions{{
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

bool Utf8BytewiseLess(std::string_view left,
                      std::string_view right) noexcept {
  return std::lexicographical_compare(
      left.begin(), left.end(), right.begin(), right.end(),
      [](char left_byte, char right_byte) noexcept {
        return static_cast<unsigned char>(left_byte) <
               static_cast<unsigned char>(right_byte);
      });
}

struct ObservationV1 {
  void *feature_root = nullptr;
  std::uint64_t feature_bits = 0;
  std::int32_t enabled_feature_count = 0;
  std::array<std::uint32_t, kLoadedFeatureNativeCount> compiled_ids{};
  std::vector<game::LoadedFeatureFlagItemV1> feature_items;
  void *script_dlc_bucket_base = nullptr;
  std::uint32_t script_dlc_bucket_mask = 0;
  std::uint8_t script_dlc_maximum_spill = 0;
  std::vector<std::string> script_dlc_keys_native_order;
  std::vector<std::string> script_dlc_keys;

  friend bool operator==(const ObservationV1 &,
                         const ObservationV1 &) = default;
};

bool GuardedDirectRead(const void *address, void *output,
                       std::size_t size) noexcept {
  if (address == nullptr || output == nullptr || size == 0) {
    return false;
  }
#if defined(_MSC_VER)
  __try {
    std::memcpy(output, address, size);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  std::memcpy(output, address, size);
  return true;
#endif
}

bool ReadBytes(const LoadedFeatureManifestAccessV1 &access,
               const void *address, void *output,
               std::size_t size) noexcept {
  if (access.read_memory != nullptr) {
    return access.read_memory(access.context, address, output, size);
  }
  return GuardedDirectRead(address, output, size);
}

bool CheckedAddress(const void *base, std::size_t offset,
                    const void *&output) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  if (base == nullptr ||
      offset > std::numeric_limits<std::uintptr_t>::max() - value) {
    output = nullptr;
    return false;
  }
  output = reinterpret_cast<const void *>(value + offset);
  return true;
}

template <typename Value>
bool ReadValue(const LoadedFeatureManifestAccessV1 &access,
               const void *base, std::size_t offset,
               Value &output) noexcept {
  const void *address = nullptr;
  return CheckedAddress(base, offset, address) &&
         ReadBytes(access, address, &output, sizeof(output));
}

template <typename Value>
bool ReadSlot(const LoadedFeatureManifestAccessV1 &access,
              const Value *slot, Value &output) noexcept {
  return ReadBytes(access, slot, &output, sizeof(output));
}

bool ReadNativeString(const LoadedFeatureManifestAccessV1 &access,
                      const void *native_string,
                      std::string &output) noexcept {
  output.clear();
  if (native_string == nullptr) {
    return false;
  }
  if (access.read_string != nullptr) {
    return access.read_string(access.context, native_string, output) &&
           !output.empty() && output.size() <= kMaximumStableKeyBytes;
  }

  std::size_t size = 0;
  std::size_t capacity = 0;
  if (!ReadValue(access, native_string, kMsvcStringSizeOffset, size) ||
      !ReadValue(access, native_string, kMsvcStringCapacityOffset,
                 capacity) ||
      size == 0 || size > capacity || size > kMaximumStableKeyBytes) {
    return false;
  }
  const void *bytes = native_string;
  if (capacity > kMsvcStringInlineCapacity) {
    if (!ReadValue(access, native_string, 0, bytes) || bytes == nullptr) {
      return false;
    }
  }
  try {
    output.resize(size);
  } catch (...) {
    output.clear();
    return false;
  }
  if (!ReadBytes(access, bytes, output.data(), size)) {
    output.clear();
    return false;
  }
  return std::none_of(output.begin(), output.end(), [](unsigned char value) {
    return value == 0 || value < 0x20U;
  });
}

bool EnvironmentIsExact(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment) noexcept {
  if (!environment.exact_build_admitted ||
      environment.feature_root_slot == nullptr ||
      environment.script_dlc_set == nullptr ||
      environment.feature_enum_table == nullptr ||
      environment.script_identifier_name == nullptr) {
    return false;
  }
  if (environment.offline_fixture_function_overrides) {
    return true;
  }
  if (environment.module_base == 0) {
    return false;
  }
  const auto base = environment.module_base;
  return reinterpret_cast<std::uintptr_t>(environment.feature_root_slot) ==
             base + kLoadedFeatureRootSlotRva &&
         reinterpret_cast<std::uintptr_t>(environment.script_dlc_set) ==
             base + kLoadedFeatureScriptDlcSetRva &&
         reinterpret_cast<std::uintptr_t>(environment.feature_enum_table) ==
             base + kLoadedFeatureEnumTableRva &&
         reinterpret_cast<std::uintptr_t>(
             environment.script_identifier_name) ==
             base + kLoadedFeatureScriptIdentifierNameRva;
}

bool InvokeIdentifierName(
    NativeLoadedFeatureScriptIdentifierNameV1 resolver,
    std::int32_t identifier, const std::string *&output) noexcept {
  output = nullptr;
#if defined(_MSC_VER)
  __try {
    output = resolver(identifier);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    output = nullptr;
    return false;
  }
#else
  output = resolver(identifier);
  return true;
#endif
}

std::int32_t Popcount64(std::uint64_t value) noexcept {
  std::int32_t count = 0;
  while (value != 0) {
    value &= value - 1;
    ++count;
  }
  return count;
}

void SetUnavailable(game::LoadedFeatureManifestV1 &output,
                    std::string_view reason) {
  const auto revision = output.snapshot_revision;
  const auto date_raw = output.date_raw;
  output = {};
  output.snapshot_revision = revision;
  output.date_raw = date_raw;
  output.status = game::LoadedFeatureManifestStatusV1::unavailable;
  output.unavailable_reason.assign(reason);
  output.effective_feature_flags.unavailable_reason.assign(reason);
  output.script_dlc_keys.unavailable_reason.assign(reason);
}

bool ReadFeatureFlags(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment,
    const LoadedFeatureManifestAccessV1 &access,
    ObservationV1 &output, std::string_view &failure) noexcept {
  if (!ReadSlot(access, environment.feature_root_slot,
                output.feature_root) ||
      output.feature_root == nullptr ||
      !ReadValue(access, output.feature_root, kFeatureBitsetOffset,
                 output.feature_bits) ||
      !ReadValue(access, output.feature_root, kFeatureEnabledCountOffset,
                 output.enabled_feature_count)) {
    failure = "feature_root_unavailable";
    return false;
  }
  constexpr std::uint64_t valid_mask =
      (std::uint64_t{1} << kLoadedFeatureNativeCount) - 1U;
  if ((output.feature_bits & ~valid_mask) != 0 ||
      output.enabled_feature_count < 0 ||
      output.enabled_feature_count >
          static_cast<std::int32_t>(kLoadedFeatureNativeCount) ||
      Popcount64(output.feature_bits) != output.enabled_feature_count) {
    failure = "feature_counter_mismatch";
    return false;
  }

  try {
    output.feature_items.reserve(kLoadedFeatureNativeCount);
  } catch (...) {
    failure = "internal_error";
    return false;
  }
  for (std::size_t index = 0; index < kLoadedFeatureNativeCount; ++index) {
    std::uint32_t identifier = 0;
    if (!ReadValue(access, environment.feature_enum_table,
                   index * sizeof(identifier), identifier) ||
        identifier != kFeatureDefinitions[index].cstring_id) {
      failure = "feature_registry_drift";
      return false;
    }
    output.compiled_ids[index] = identifier;
    const std::string *native_name = nullptr;
    std::string copied_name;
    if (!InvokeIdentifierName(environment.script_identifier_name,
                              static_cast<std::int32_t>(identifier),
                              native_name) ||
        native_name == nullptr ||
        !ReadNativeString(access, native_name, copied_name) ||
        copied_name != kFeatureDefinitions[index].key) {
      failure = "feature_registry_drift";
      return false;
    }
    try {
      output.feature_items.push_back(
          {static_cast<std::int32_t>(index), identifier,
           std::move(copied_name),
           (output.feature_bits & (std::uint64_t{1} << index)) != 0});
    } catch (...) {
      failure = "internal_error";
      return false;
    }
  }
  return true;
}

bool ReadScriptDlcKeys(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment,
    const LoadedFeatureManifestAccessV1 &access,
    ObservationV1 &output, std::string_view &failure) noexcept {
  if (!ReadValue(access, environment.script_dlc_set,
                 kScriptDlcBucketBaseOffset,
                 output.script_dlc_bucket_base) ||
      !ReadValue(access, environment.script_dlc_set,
                 kScriptDlcBucketMaskOffset,
                 output.script_dlc_bucket_mask) ||
      !ReadValue(access, environment.script_dlc_set,
                 kScriptDlcMaximumSpillOffset,
                 output.script_dlc_maximum_spill)) {
    failure = "script_dlc_set_unavailable";
    return false;
  }
  if (output.script_dlc_bucket_base == nullptr) {
    if (output.script_dlc_bucket_mask == 0 &&
        output.script_dlc_maximum_spill == 0) {
      return true;
    }
    failure = "script_dlc_set_unavailable";
    return false;
  }
  const auto mask = output.script_dlc_bucket_mask;
  if (mask > kMaximumScriptDlcBucketMask ||
      (mask & (mask + 1U)) != 0) {
    failure = "script_dlc_set_unavailable";
    return false;
  }
  const auto physical_count =
      static_cast<std::size_t>(mask) + 1U +
      static_cast<std::size_t>(output.script_dlc_maximum_spill);
  if (physical_count == 0 ||
      physical_count > kMaximumScriptDlcPhysicalBuckets) {
    failure = "script_dlc_set_unavailable";
    return false;
  }
  try {
    output.script_dlc_keys_native_order.reserve(physical_count);
  } catch (...) {
    failure = "internal_error";
    return false;
  }
  for (std::size_t index = 0; index < physical_count; ++index) {
    if (index > std::numeric_limits<std::size_t>::max() /
                    kScriptDlcBucketStride) {
      failure = "script_dlc_set_unavailable";
      return false;
    }
    const auto bucket_offset = index * kScriptDlcBucketStride;
    std::uint8_t control = 0;
    if (!ReadValue(access, output.script_dlc_bucket_base,
                   bucket_offset + kScriptDlcBucketControlOffset,
                   control)) {
      failure = "script_dlc_set_unavailable";
      return false;
    }
    if (control == 0 || control == 0xFF) {
      continue;
    }
    const void *key_address = nullptr;
    std::string key;
    if (!CheckedAddress(output.script_dlc_bucket_base,
                        bucket_offset + kScriptDlcBucketKeyOffset,
                        key_address) ||
        !ReadNativeString(access, key_address, key)) {
      failure = "script_dlc_key_invalid";
      return false;
    }
    try {
      output.script_dlc_keys_native_order.push_back(std::move(key));
    } catch (...) {
      failure = "internal_error";
      return false;
    }
  }
  output.script_dlc_keys = output.script_dlc_keys_native_order;
  std::sort(output.script_dlc_keys.begin(), output.script_dlc_keys.end(),
            Utf8BytewiseLess);
  if (std::adjacent_find(output.script_dlc_keys.begin(),
                         output.script_dlc_keys.end()) !=
      output.script_dlc_keys.end()) {
    failure = "script_dlc_set_unavailable";
    return false;
  }
  return true;
}

bool ReadObservation(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment,
    const LoadedFeatureManifestAccessV1 &access,
    ObservationV1 &output, std::string_view &failure) noexcept {
  output = {};
  return ReadFeatureFlags(environment, access, output, failure) &&
         ReadScriptDlcKeys(environment, access, output, failure);
}

} // namespace

LoadedFeatureManifestNativeEnvironmentV1
BindLoadedFeatureManifestNativeEnvironmentV1(
    std::uintptr_t module_base, bool exact_build_admitted) noexcept {
  LoadedFeatureManifestNativeEnvironmentV1 output{};
  output.module_base = module_base;
  output.exact_build_admitted = exact_build_admitted;
  if (module_base == 0 || !exact_build_admitted) {
    return output;
  }
  output.feature_root_slot = reinterpret_cast<void **>(
      module_base + kLoadedFeatureRootSlotRva);
  output.script_dlc_set = reinterpret_cast<void *>(
      module_base + kLoadedFeatureScriptDlcSetRva);
  output.feature_enum_table = reinterpret_cast<const std::uint32_t *>(
      module_base + kLoadedFeatureEnumTableRva);
  output.script_identifier_name = reinterpret_cast<
      NativeLoadedFeatureScriptIdentifierNameV1>(
      module_base + kLoadedFeatureScriptIdentifierNameRva);
  return output;
}

game::ReadLoadedFeatureManifestResultV1 ReadLoadedFeatureManifestV1(
    const LoadedFeatureManifestNativeEnvironmentV1 &environment,
    const LoadedFeatureManifestAccessV1 &access,
    const LoadedFeatureManifestRequestV1 &request,
    game::LoadedFeatureManifestV1 &output) noexcept {
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  try {
    if (request.expected_snapshot_revision == 0 ||
        access.capture_frame == nullptr || access.is_main_thread == nullptr ||
        !access.is_main_thread(access.context)) {
      SetUnavailable(output, "requires_application_main");
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }
    game::LoadedFeatureManifestFrameV1 before{};
    if (!access.capture_frame(access.context, before)) {
      SetUnavailable(output, "state_changed");
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }
    output.snapshot_revision = before.snapshot_revision;
    output.date_raw = before.date_raw;
    if (before.snapshot_revision != request.expected_snapshot_revision) {
      SetUnavailable(output, "state_changed");
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }
    if (!before.paused) {
      SetUnavailable(output, "requires_paused");
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }
    if (!before.map_ready) {
      SetUnavailable(output, "map_not_ready");
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }
    if (!EnvironmentIsExact(environment)) {
      SetUnavailable(output, "unsupported_build");
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }

    ObservationV1 first{};
    ObservationV1 second{};
    std::string_view failure = "internal_error";
    if (!ReadObservation(environment, access, first, failure)) {
      SetUnavailable(output, failure);
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }
    failure = "internal_error";
    if (!ReadObservation(environment, access, second, failure)) {
      SetUnavailable(output, failure);
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }
    game::LoadedFeatureManifestFrameV1 after{};
    if (!access.capture_frame(access.context, after) || after != before ||
        second != first) {
      SetUnavailable(output, "state_changed");
      return game::ReadLoadedFeatureManifestResultV1::unavailable;
    }

    output.status = game::LoadedFeatureManifestStatusV1::available;
    output.unavailable_reason.clear();
    output.effective_feature_flags.status =
        game::LoadedFeatureComponentStatusV1::available;
    output.effective_feature_flags.native_count =
        static_cast<std::int32_t>(kLoadedFeatureNativeCount);
    output.effective_feature_flags.items =
        std::move(first.feature_items);
    output.effective_feature_flags.unavailable_reason.clear();
    output.script_dlc_keys.status =
        game::LoadedFeatureComponentStatusV1::available;
    output.script_dlc_keys.enumerated_count = static_cast<std::int32_t>(
        first.script_dlc_keys.size());
    output.script_dlc_keys.keys = std::move(first.script_dlc_keys);
    output.script_dlc_keys.unavailable_reason.clear();
    output.readiness = {true, true, false, true, true};
    return game::ReadLoadedFeatureManifestResultV1::available;
  } catch (...) {
    SetUnavailable(output, "internal_error");
    return game::ReadLoadedFeatureManifestResultV1::unavailable;
  }
}

} // namespace xar::ck3_11906
