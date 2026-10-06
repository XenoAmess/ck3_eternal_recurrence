#include "xar_bridge/ck3_12004_government_runtime_binder.hpp"

#include <windows.h>

#include <algorithm>
#include <array>
#include <limits>
#include <utility>

namespace xar::ck3_12004 {
namespace {
using Sample = bridge::private_observer::GovernmentRuntimeAdapterCollectorSampleV1;

// Existing read bounds and native container semantics are retained.
constexpr std::size_t kMaximumStableKeyBytes = 1'024;
constexpr std::int32_t kMaximumGovernmentFlags = 4'096;
constexpr std::uint32_t kMaximumDlcBucketMask = 1'048'575;
constexpr std::size_t kMaximumDlcPhysicalBuckets = 1'048'832;
constexpr std::size_t kGovernmentKeyOffset = 0x18;
constexpr std::size_t kGovernmentFlagsOffset = 0x50;
constexpr std::size_t kVectorCountOffset = 0x0C;
constexpr std::size_t kFeatureBitsOffset = 0x2B0;
constexpr std::size_t kFeatureCountOffset = 0x2B8;
constexpr std::size_t kDlcBucketBaseOffset = 0x08;
constexpr std::size_t kDlcBucketMaskOffset = 0x14;
constexpr std::size_t kDlcMaximumSpillOffset = 0x18;
constexpr std::size_t kDlcBucketStride = 0x28;
constexpr std::size_t kDlcBucketControlOffset = 0x04;
constexpr std::size_t kDlcBucketKeyOffset = 0x08;

// Actual .4 176B registry equals the old captured bytes, at the independently
// derived new address. Runtime identities are still checked by the new reader.
constexpr std::array<std::uint32_t, kGovernmentRuntimeNativeFeatureCount>
    kFeatureIdentifiers{
        0x3587, 0x3588, 0x34A7, 0x3538, 0x3539, 0x3270, 0x366D, 0x34DC,
        0x3773, 0x3608, 0x37CF, 0x37CE, 0x36C4, 0x377A, 0x35E0, 0x394A,
        0x3B0A, 0x3A5B, 0x3A09, 0x3A08, 0x3953, 0x3A00, 0x3A02, 0x3A01,
        0x39DA, 0x3CBB, 0x3A07, 0x3C98, 0x3CA1, 0x3A06, 0x39F7, 0x3D67,
        0x39ED, 0x39EE, 0x39EF, 0x39F0, 0x39DB, 0x39DC, 0x39DD, 0x39DE,
        0x39DF, 0x4101, 0x4102, 0x4169};

bool Utf8Less(std::string_view left, std::string_view right) noexcept {
  return std::lexicographical_compare(
      left.begin(), left.end(), right.begin(), right.end(),
      [](char lhs, char rhs) noexcept {
        return static_cast<unsigned char>(lhs) < static_cast<unsigned char>(rhs);
      });
}

template <typename Access, typename Value>
bool ReadValue(const Access &access, const void *base, std::size_t offset,
               Value &value) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  return base != nullptr && access.read_memory != nullptr &&
         offset <= std::numeric_limits<std::uintptr_t>::max() - address &&
         access.read_memory(access.context,
                            reinterpret_cast<const void *>(address + offset),
                            &value, sizeof(value));
}

template <typename Access>
bool ReadString(const Access &access, const void *native_string,
                std::string &output) {
  output.clear();
  if (native_string == nullptr) return false;
  if (access.read_string != nullptr) {
    return access.read_string(access.context, native_string, output) &&
           !output.empty() && output.size() <= kMaximumStableKeyBytes;
  }
  std::size_t size = 0, capacity = 0;
  if (!ReadValue(access, native_string, 0x10, size) ||
      !ReadValue(access, native_string, 0x18, capacity) || size == 0 ||
      size > capacity || size > kMaximumStableKeyBytes) return false;
  const void *bytes = native_string;
  if (capacity > 0x0F &&
      (!ReadValue(access, native_string, 0, bytes) || bytes == nullptr)) return false;
  output.resize(size);
  if (!access.read_memory(access.context, bytes, output.data(), size)) return false;
  return std::none_of(output.begin(), output.end(), [](unsigned char byte) {
    return byte == 0 || byte < 0x20U;
  });
}

bool InvokeGovernment(ck3_11906::NativeCampaignRootCharacterResolverV1 resolver,
                      void *character, void *&government) noexcept {
  government = nullptr;
#if defined(_MSC_VER)
  __try {
    government = resolver(character);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  government = resolver(character);
  return true;
#endif
}

bool InvokeIdentifier(ck3_11906::NativeLoadedFeatureScriptIdentifierNameV1 resolver,
                      std::int32_t id, const std::string *&name) noexcept {
  name = nullptr;
#if defined(_MSC_VER)
  __try {
    name = resolver(id);
    return true;
  } __except (EXCEPTION_EXECUTE_HANDLER) {
    return false;
  }
#else
  name = resolver(id);
  return true;
#endif
}

// The actual .4 IsType key leaf adds 0x18 and applies native CString SSO
// semantics. Current CGovernmentType/CGameDatabaseObject PMD0 and Root's typed
// Government +0x18 head/string corroboration close this receiver/member pair.
// Copy the whole runtime key; the observed stock key is not an allowlist.
bool ReadGovernmentKey(const ck3_11906::CampaignRootAccessV1 &access,
                       const void *government, std::string &output) {
  return government != nullptr &&
         ReadString(access, static_cast<const std::byte *>(government) +
                                kGovernmentKeyOffset, output);
}

bool ReadGovernment(const GovernmentRuntimeBindingsV1 &bindings,
                    const ck3_11906::CampaignRootAccessV1 &access,
                    void *character, Sample &sample, std::string_view &failure) {
  void *government = nullptr;
  void *fallback = nullptr;
  if (!ReadValue(access, bindings.government_fallback_slot, 0, fallback) ||
      !InvokeGovernment(bindings.government, character, government)) {
    failure = "government_unavailable";
    return false;
  }
  sample.government_object_identity_available = true;
  sample.government_object_identity = reinterpret_cast<std::uintptr_t>(government);
  if (government == nullptr || government == fallback) return true;
  game::CampaignRootGovernmentV1 observed{};
  const std::int32_t *identifiers = nullptr;
  if (!ReadGovernmentKey(access, government, observed.key) ||
      !ReadValue(access, government, kGovernmentFlagsOffset, identifiers) ||
      !ReadValue(access, government, kGovernmentFlagsOffset + kVectorCountOffset,
                 observed.native_flag_count) ||
      observed.native_flag_count < 0 || observed.native_flag_count > kMaximumGovernmentFlags ||
      (observed.native_flag_count != 0 && identifiers == nullptr)) {
    failure = "government_flags_unavailable";
    return false;
  }
  observed.flags.reserve(static_cast<std::size_t>(observed.native_flag_count));
  for (std::int32_t index = 0; index < observed.native_flag_count; ++index) {
    std::int32_t id = 0;
    const std::string *name = nullptr;
    std::string copied;
    if (!ReadValue(access, identifiers, static_cast<std::size_t>(index) * sizeof(id), id) ||
        !InvokeIdentifier(bindings.identifier_name, id, name) ||
        !ReadString(access, name, copied)) {
      failure = "government_flags_unavailable";
      return false;
    }
    observed.flags.push_back(std::move(copied));
  }
  std::sort(observed.flags.begin(), observed.flags.end(), Utf8Less);
  sample.campaign_root.government = std::move(observed);
  return true;
}

bool ReadFeatures(const GovernmentRuntimeBindingsV1 &bindings,
                  const ck3_11906::LoadedFeatureManifestAccessV1 &access,
                  Sample &sample, std::string_view &failure) {
  void *root = nullptr;
  std::uint64_t bits = 0;
  std::int32_t enabled_count = 0;
  if (!ReadValue(access, bindings.feature_root_slot, 0, root) || root == nullptr ||
      !ReadValue(access, root, kFeatureBitsOffset, bits) ||
      !ReadValue(access, root, kFeatureCountOffset, enabled_count)) {
    failure = "feature_root_unavailable";
    return false;
  }
  constexpr auto valid_mask = (std::uint64_t{1} << kGovernmentRuntimeNativeFeatureCount) - 1U;
  std::int32_t popcount = 0;
  for (auto remaining = bits; remaining != 0; remaining &= remaining - 1) ++popcount;
  if ((bits & ~valid_mask) != 0 || enabled_count < 0 ||
      enabled_count > static_cast<std::int32_t>(kGovernmentRuntimeNativeFeatureCount) ||
      popcount != enabled_count) {
    failure = "feature_counter_mismatch";
    return false;
  }
  const auto keys = bridge::private_observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1(
      bridge::private_observer::GovernmentRuntimeAdapterBuildProfileV1::ck3_12004);
  auto &features = sample.loaded_features.effective_feature_flags;
  features.items.reserve(kGovernmentRuntimeNativeFeatureCount);
  for (std::size_t index = 0; index < kGovernmentRuntimeNativeFeatureCount; ++index) {
    std::uint32_t id = 0;
    const std::string *native_name = nullptr;
    std::string name;
    if (!ReadValue(access, bindings.feature_registry, index * sizeof(id), id) ||
        id != kFeatureIdentifiers[index] ||
        !InvokeIdentifier(bindings.identifier_name, static_cast<std::int32_t>(id), native_name) ||
        !ReadString(access, native_name, name) || name != keys[index]) {
      failure = "feature_registry_drift";
      return false;
    }
    features.items.push_back({static_cast<std::int32_t>(index), id, std::move(name),
                             (bits & (std::uint64_t{1} << index)) != 0});
  }
  sample.feature_lifecycle_identity = reinterpret_cast<std::uintptr_t>(root);
  features.status = game::LoadedFeatureComponentStatusV1::available;
  features.native_count = static_cast<std::int32_t>(kGovernmentRuntimeNativeFeatureCount);
  features.unavailable_reason.clear();
  return true;
}

bool ReadDlc(const GovernmentRuntimeBindingsV1 &bindings,
             const ck3_11906::LoadedFeatureManifestAccessV1 &access,
             Sample &sample, std::string_view &failure) {
  void *buckets = nullptr;
  std::uint32_t mask = 0;
  std::uint8_t spill = 0;
  if (!ReadValue(access, bindings.script_dlc_set, kDlcBucketBaseOffset, buckets) ||
      !ReadValue(access, bindings.script_dlc_set, kDlcBucketMaskOffset, mask) ||
      !ReadValue(access, bindings.script_dlc_set, kDlcMaximumSpillOffset, spill)) {
    failure = "script_dlc_set_unavailable";
    return false;
  }
  auto &dlc = sample.loaded_features.script_dlc_keys;
  if (buckets == nullptr) {
    if (mask != 0 || spill != 0) {
      failure = "script_dlc_set_unavailable";
      return false;
    }
  } else {
    const auto physical_count = static_cast<std::size_t>(mask) + 1U + spill;
    if (mask > kMaximumDlcBucketMask || (mask & (mask + 1U)) != 0 ||
        physical_count > kMaximumDlcPhysicalBuckets) {
      failure = "script_dlc_set_unavailable";
      return false;
    }
    for (std::size_t index = 0; index < physical_count; ++index) {
      std::uint8_t control = 0;
      const auto offset = index * kDlcBucketStride;
      if (!ReadValue(access, buckets, offset + kDlcBucketControlOffset, control)) {
        failure = "script_dlc_set_unavailable";
        return false;
      }
      if (control == 0 || control == 0xFF) continue;
      std::string key;
      if (!ReadString(access, static_cast<const std::byte *>(buckets) + offset +
                                  kDlcBucketKeyOffset, key)) {
        failure = "script_dlc_key_invalid";
        return false;
      }
      dlc.keys.push_back(std::move(key));
    }
    std::sort(dlc.keys.begin(), dlc.keys.end(), Utf8Less);
    if (std::adjacent_find(dlc.keys.begin(), dlc.keys.end()) != dlc.keys.end()) {
      failure = "script_dlc_set_unavailable";
      return false;
    }
  }
  dlc.status = game::LoadedFeatureComponentStatusV1::available;
  dlc.enumerated_count = static_cast<std::int32_t>(dlc.keys.size());
  dlc.unavailable_reason.clear();
  sample.script_dlc_layout_identity_available = true;
  sample.script_dlc_bucket_base_identity = reinterpret_cast<std::uintptr_t>(buckets);
  sample.script_dlc_bucket_mask_identity = mask;
  sample.script_dlc_maximum_spill_identity = spill;
  return true;
}

} // namespace

GovernmentRuntimeBindingsV1 BindGovernmentRuntimeImageV1(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept {
  GovernmentRuntimeBindingsV1 output{};
  if (module_base == 0 || executable_sha256 != kExecutableSha256) return output;
  output.core = BindCoreImage(module_base, executable_sha256);
  if (!output.core.enabled) return output;
  output.module_base = module_base;
  output.government = reinterpret_cast<decltype(output.government)>(
      module_base + kGovernmentRuntimeResolverRva);
  output.identifier_name = reinterpret_cast<decltype(output.identifier_name)>(
      module_base + kGovernmentRuntimeIdentifierNameRva);
  output.government_fallback_slot = reinterpret_cast<void **>(
      module_base + kGovernmentRuntimeFallbackSlotRva);
  output.feature_root_slot = reinterpret_cast<void **>(
      module_base + kGovernmentRuntimeFeatureRootSlotRva);
  output.feature_registry = reinterpret_cast<const std::uint32_t *>(
      module_base + kGovernmentRuntimeFeatureRegistryRva);
  output.script_dlc_set = reinterpret_cast<void *>(
      module_base + kGovernmentRuntimeScriptDlcSetRva);
  output.enabled = true;
  return output;
}

bool ReadGovernmentRuntimeCollectorSampleV1(
    const GovernmentRuntimeBindingsV1 &bindings,
    const ck3_11906::CampaignRootAccessV1 &campaign_access,
    const ck3_11906::LoadedFeatureManifestAccessV1 &feature_access,
    std::uint64_t expected_revision,
    const ck3_11906::MainThreadExecutionStampV1 &stamp,
    Sample &output) noexcept {
  output = {};
  output.campaign_root.snapshot_revision = expected_revision;
  output.loaded_features.snapshot_revision = expected_revision;
  output.campaign_root.date_raw = stamp.date_raw;
  output.loaded_features.date_raw = stamp.date_raw;
  output.paused = stamp.paused;
  try {
    if (!bindings.enabled || expected_revision == 0 ||
        campaign_access.capture_frame == nullptr || campaign_access.is_main_thread == nullptr ||
        campaign_access.read_memory == nullptr ||
        feature_access.capture_frame == nullptr || feature_access.is_main_thread == nullptr ||
        feature_access.read_memory == nullptr ||
        !campaign_access.is_main_thread(campaign_access.context) ||
        !feature_access.is_main_thread(feature_access.context)) {
      output.campaign_root.unavailable_reason = "requires_application_main";
      return true;
    }
    game::CampaignRootFrameV1 before{};
    game::LoadedFeatureManifestFrameV1 feature_before{};
    void *game_state = nullptr, *jomini = nullptr;
    if (!campaign_access.capture_frame(campaign_access.context, before) ||
        !feature_access.capture_frame(feature_access.context, feature_before) ||
        before.snapshot_revision != expected_revision ||
        feature_before.snapshot_revision != expected_revision ||
        before.date_raw != stamp.date_raw || feature_before.date_raw != stamp.date_raw ||
        !before.paused || !before.map_ready || !before.has_played_character ||
        !before.played_character_alive || !feature_before.paused || !feature_before.map_ready ||
        !ReadValue(campaign_access, bindings.core.game_state_slot, 0, game_state) ||
        !ReadValue(campaign_access, bindings.core.jomini_state_slot, 0, jomini) ||
        reinterpret_cast<std::uintptr_t>(game_state) != stamp.game_state ||
        reinterpret_cast<std::uintptr_t>(jomini) != stamp.jomini_state) {
      output.campaign_root.unavailable_reason = "state_changed";
      return true;
    }
    void *character = xar::ck3_12004::ResolveCoreCharacter(bindings.core, before.played_character_id);
    if (character == nullptr) {
      output.campaign_root.unavailable_reason = "player_identity_unavailable";
      return true;
    }
    std::string_view government_failure = "internal_error";
    std::string_view feature_failure = "internal_error";
    const bool government_available = ReadGovernment(
        bindings, campaign_access, character, output, government_failure);
    const bool features_available = ReadFeatures(bindings, feature_access, output, feature_failure) &&
                                    ReadDlc(bindings, feature_access, output, feature_failure);
    game::CampaignRootFrameV1 after{};
    game::LoadedFeatureManifestFrameV1 feature_after{};
    void *game_state_after = nullptr, *jomini_after = nullptr, *feature_root_after = nullptr;
    if (!campaign_access.capture_frame(campaign_access.context, after) || after != before ||
        !feature_access.capture_frame(feature_access.context, feature_after) ||
        feature_after != feature_before ||
        !ReadValue(campaign_access, bindings.core.game_state_slot, 0, game_state_after) ||
        !ReadValue(campaign_access, bindings.core.jomini_state_slot, 0, jomini_after) ||
        game_state_after != game_state || jomini_after != jomini ||
        xar::ck3_12004::ResolveCoreCharacter(bindings.core, before.played_character_id) != character ||
        !ReadValue(feature_access, bindings.feature_root_slot, 0, feature_root_after) ||
        (features_available && reinterpret_cast<std::uintptr_t>(feature_root_after) !=
                                   output.feature_lifecycle_identity)) {
      output = {};
      output.campaign_root.snapshot_revision = expected_revision;
      output.loaded_features.snapshot_revision = expected_revision;
      output.campaign_root.date_raw = stamp.date_raw;
      output.loaded_features.date_raw = stamp.date_raw;
      output.paused = stamp.paused;
      output.campaign_root.unavailable_reason = "state_changed";
      return true;
    }
    output.campaign_lifecycle_identity = reinterpret_cast<std::uintptr_t>(game_state);
    output.campaign_root.player_character_id = before.played_character_id;
    output.campaign_root.player_character_alive = before.played_character_alive;
    if (government_available) {
      output.campaign_root.status = game::CampaignRootContextStatusV1::available;
      output.campaign_root.unavailable_reason.clear();
      output.campaign_root.readiness.player_identity_ready = true;
      output.campaign_root.readiness.government_ready = true;
      output.campaign_root.readiness.same_frame_ready = true;
    } else {
      output.campaign_root.unavailable_reason.assign(government_failure);
    }
    if (features_available) {
      output.loaded_features.status = game::LoadedFeatureManifestStatusV1::available;
      output.loaded_features.unavailable_reason.clear();
      output.loaded_features.readiness = {true, true, false, true, true};
    } else {
      output.loaded_features.unavailable_reason.assign(feature_failure);
    }
    return true;
  } catch (...) {
    output.campaign_root.status = game::CampaignRootContextStatusV1::unavailable;
    output.campaign_root.readiness = {};
    output.campaign_root.unavailable_reason = "internal_error";
    return true;
  }
}

} // namespace xar::ck3_12004
