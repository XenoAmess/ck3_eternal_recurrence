#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace xar::bridge::private_observer {

enum class GovernmentRuntimeAdapterObservationStatusV1 : std::uint32_t {
  unavailable = 0,
  not_present = 1,
  available = 2,
};

enum class GovernmentRuntimeAdapterUnavailableReasonV1 : std::uint32_t {
  none = 0,
  unsupported_build,
  requires_application_main,
  requires_paused,
  player_not_present,
  government_not_present,
  government_flags_unavailable,
  feature_root_unavailable,
  feature_counter_mismatch,
  feature_registry_drift,
  script_dlc_set_unavailable,
  script_dlc_set_invalid,
  state_changed,
  store_verdict_provenance_unclosed,
};

enum class GovernmentRuntimeAdapterSelectionStatusV1 : std::uint32_t {
  unavailable = 0,
  core_supported,
  adapter_spec_ready_not_implemented,
  unsupported_nonplayer_identity,
  owner_deferred_religious,
  unavailable_feature_mismatch,
  unadapted_runtime_government,
};

struct GovernmentRuntimeFeatureInputV1 {
  std::int32_t native_index = -1;
  std::string_view key;
  bool enabled = false;
};

struct GovernmentRuntimeAdapterObserverInputV1 {
  bool exact_build_admitted = false;
  bool application_main = false;
  bool paused = false;
  bool state_identity_stable = false;
  std::uint64_t frame = 0;
  std::optional<std::int32_t> player_character_id;
  std::string_view effective_government_stable_key;
  bool government_flags_available = false;
  std::span<const std::string_view> government_flags;
  bool feature_root_available = false;
  std::span<const GovernmentRuntimeFeatureInputV1> effective_feature_flags;
  std::int32_t enabled_feature_count = -1;
  bool script_dlc_set_available = false;
  std::span<const std::string_view> script_dlc_keys;
};

struct GovernmentRuntimeFeatureIdentityV1 {
  std::int32_t native_index = -1;
  std::string key;
  bool enabled = false;

  friend bool operator==(const GovernmentRuntimeFeatureIdentityV1 &,
                         const GovernmentRuntimeFeatureIdentityV1 &) = default;
};

struct GovernmentRuntimeProductIdentityV1 {
  GovernmentRuntimeAdapterObservationStatusV1 status =
      GovernmentRuntimeAdapterObservationStatusV1::not_present;
  std::string script_dlc_key;

  friend bool operator==(const GovernmentRuntimeProductIdentityV1 &,
                         const GovernmentRuntimeProductIdentityV1 &) = default;
};

struct GovernmentRuntimeGovernmentIdentityV1 {
  GovernmentRuntimeAdapterObservationStatusV1 status =
      GovernmentRuntimeAdapterObservationStatusV1::unavailable;
  std::string stable_key;
  bool recognized_stock_key = false;
  bool religious_identity_opaque = false;
  std::vector<std::string> observed_flags;
  std::vector<std::string> applicable_stock_flags;

  friend bool operator==(const GovernmentRuntimeGovernmentIdentityV1 &,
                         const GovernmentRuntimeGovernmentIdentityV1 &) =
      default;
};

struct GovernmentRuntimeAdapterSelectionV1 {
  GovernmentRuntimeAdapterSelectionStatusV1 status =
      GovernmentRuntimeAdapterSelectionStatusV1::unavailable;
  std::optional<std::string> family;
  std::vector<std::string> required_effective_features;
  std::vector<GovernmentRuntimeFeatureIdentityV1> capability_profile_features;
  bool requirements_met = false;

  friend bool operator==(const GovernmentRuntimeAdapterSelectionV1 &,
                         const GovernmentRuntimeAdapterSelectionV1 &) = default;
};

struct GovernmentRuntimeAdapterObserverResultV1 {
  GovernmentRuntimeAdapterObservationStatusV1 status =
      GovernmentRuntimeAdapterObservationStatusV1::unavailable;
  GovernmentRuntimeAdapterUnavailableReasonV1 unavailable_reason =
      GovernmentRuntimeAdapterUnavailableReasonV1::none;
  std::uint64_t frame = 0;
  std::optional<std::int32_t> player_character_id;
  GovernmentRuntimeGovernmentIdentityV1 government;
  std::vector<GovernmentRuntimeFeatureIdentityV1> effective_feature_flags;
  std::vector<std::string> script_dlc_keys;
  std::vector<GovernmentRuntimeProductIdentityV1> runtime_products;
  GovernmentRuntimeAdapterObservationStatusV1 entitlement_status =
      GovernmentRuntimeAdapterObservationStatusV1::unavailable;
  GovernmentRuntimeAdapterUnavailableReasonV1 entitlement_unavailable_reason =
      GovernmentRuntimeAdapterUnavailableReasonV1::
          store_verdict_provenance_unclosed;
  GovernmentRuntimeAdapterSelectionV1 adapter;

  friend bool operator==(const GovernmentRuntimeAdapterObserverResultV1 &,
                         const GovernmentRuntimeAdapterObserverResultV1 &) =
      default;
};

inline constexpr std::string_view kGovernmentRuntimeAdapterObserverV1BackendId =
    "ck3-1.19.0.6-private-government-runtime-adapter-observer-v1";
inline constexpr std::size_t kGovernmentRuntimeAdapterStockGovernmentCountV1 =
    18;
inline constexpr std::size_t
    kGovernmentRuntimeAdapterStockFlagDeclarationCountV1 = 136;
inline constexpr std::size_t kGovernmentRuntimeAdapterFeatureCountV1 = 44;

std::span<const std::string_view>
GovernmentRuntimeAdapterExpectedFeatureKeysV1() noexcept;

GovernmentRuntimeAdapterObserverResultV1
EvaluateGovernmentRuntimeAdapterObserverV1(
    const GovernmentRuntimeAdapterObserverInputV1 &input);

} // namespace xar::bridge::private_observer
