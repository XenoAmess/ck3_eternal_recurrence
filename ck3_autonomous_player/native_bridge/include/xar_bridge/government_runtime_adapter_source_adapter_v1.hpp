#pragma once

#include "xar_bridge/campaign_root_context_v1.hpp"
#include "xar_bridge/government_runtime_adapter_observer_v1.hpp"
#include "xar_bridge/loaded_feature_manifest_v1.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::bridge::private_observer {

enum class GovernmentRuntimeAdapterSourceStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
};

enum class GovernmentRuntimeAdapterSourceFailureV1 : std::uint32_t {
  none = 0,
  unsupported_build,
  access_incomplete,
  requires_application_main,
  first_capture_failed,
  second_capture_failed,
  requires_paused,
  campaign_collector_unavailable,
  feature_collector_unavailable,
  collector_readiness_unavailable,
  collector_frame_mismatch,
  collector_lifecycle_unavailable,
  collector_lifecycle_drift,
  player_identity_drift,
  government_identity_drift,
  feature_identity_drift,
  script_dlc_identity_drift,
  government_flag_count_mismatch,
  feature_count_mismatch,
  script_dlc_count_mismatch,
  semantic_input_rejected,
  collector_provenance_unavailable,
  government_object_identity_drift,
  script_dlc_layout_identity_drift,
};

struct GovernmentRuntimeAdapterCollectorMemoryV1 {
  const game::CampaignRootContextV1 *campaign_root = nullptr;
  const game::LoadedFeatureManifestV1 *loaded_features = nullptr;
  bool paused = false;
  std::uint64_t campaign_lifecycle_identity = 0;
  std::uint64_t feature_lifecycle_identity = 0;
  bool government_object_identity_available = false;
  std::uintptr_t government_object_identity = 0;
  bool script_dlc_layout_identity_available = false;
  std::uintptr_t script_dlc_bucket_base_identity = 0;
  std::uint32_t script_dlc_bucket_mask_identity = 0;
  std::uint8_t script_dlc_maximum_spill_identity = 0;
};

struct GovernmentRuntimeAdapterCollectorSampleV1 {
  game::CampaignRootContextV1 campaign_root;
  game::LoadedFeatureManifestV1 loaded_features;
  bool paused = false;
  std::uint64_t campaign_lifecycle_identity = 0;
  std::uint64_t feature_lifecycle_identity = 0;
  bool government_object_identity_available = false;
  std::uintptr_t government_object_identity = 0;
  bool script_dlc_layout_identity_available = false;
  std::uintptr_t script_dlc_bucket_base_identity = 0;
  std::uint32_t script_dlc_bucket_mask_identity = 0;
  std::uint8_t script_dlc_maximum_spill_identity = 0;

  friend bool
  operator==(const GovernmentRuntimeAdapterCollectorSampleV1 &,
             const GovernmentRuntimeAdapterCollectorSampleV1 &) = default;
};

using IsGovernmentRuntimeAdapterApplicationMainV1 =
    bool (*)(void *context) noexcept;
using CaptureGovernmentRuntimeAdapterCollectorSampleV1 = bool (*)(
    void *context, GovernmentRuntimeAdapterCollectorSampleV1 &output) noexcept;

struct GovernmentRuntimeAdapterSourceAccessV1 {
  bool exact_build_admitted = false;
  void *context = nullptr;
  IsGovernmentRuntimeAdapterApplicationMainV1 is_application_main = nullptr;
  CaptureGovernmentRuntimeAdapterCollectorSampleV1 capture = nullptr;
};

struct GovernmentRuntimeAdapterOwnedInputV1 {
  bool exact_build_admitted = false;
  bool application_main = false;
  bool paused = false;
  bool state_identity_stable = false;
  std::uint64_t frame = 0;
  std::optional<std::int32_t> player_character_id;
  std::string effective_government_stable_key;
  bool government_flags_available = false;
  std::vector<std::string> government_flags;
  bool feature_root_available = false;
  std::vector<GovernmentRuntimeFeatureIdentityV1> effective_feature_flags;
  std::int32_t enabled_feature_count = -1;
  bool script_dlc_set_available = false;
  std::vector<std::string> script_dlc_keys;

  GovernmentRuntimeAdapterObserverResultV1 Evaluate() const;

  friend bool
  operator==(const GovernmentRuntimeAdapterOwnedInputV1 &,
             const GovernmentRuntimeAdapterOwnedInputV1 &) = default;
};

struct GovernmentRuntimeAdapterSourceResultV1 {
  GovernmentRuntimeAdapterSourceStatusV1 status =
      GovernmentRuntimeAdapterSourceStatusV1::unavailable;
  GovernmentRuntimeAdapterSourceFailureV1 failure =
      GovernmentRuntimeAdapterSourceFailureV1::none;
  std::uint64_t first_snapshot_revision = 0;
  std::uint64_t second_snapshot_revision = 0;
  std::uint64_t campaign_lifecycle_identity = 0;
  std::uint64_t feature_lifecycle_identity = 0;
  GovernmentRuntimeAdapterOwnedInputV1 input;
  GovernmentRuntimeAdapterObserverResultV1 semantic_result;

  friend bool
  operator==(const GovernmentRuntimeAdapterSourceResultV1 &,
             const GovernmentRuntimeAdapterSourceResultV1 &) = default;
};

inline constexpr std::string_view
    kGovernmentRuntimeAdapterSourceAdapterV1GameVersion = "1.19.0.6";
inline constexpr std::string_view
    kGovernmentRuntimeAdapterSourceAdapterV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

bool CopyGovernmentRuntimeAdapterCollectorMemoryV1(
    const GovernmentRuntimeAdapterCollectorMemoryV1 &memory,
    GovernmentRuntimeAdapterCollectorSampleV1 &output) noexcept;

GovernmentRuntimeAdapterSourceStatusV1 ReadGovernmentRuntimeAdapterSourceV1(
    const GovernmentRuntimeAdapterSourceAccessV1 &access,
    GovernmentRuntimeAdapterSourceResultV1 &output) noexcept;

} // namespace xar::bridge::private_observer
