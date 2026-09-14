#include "xar_bridge/government_runtime_adapter_source_adapter_v1.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <string_view>
#include <vector>

namespace xar::bridge::private_observer {
namespace {

using SourceStatus = GovernmentRuntimeAdapterSourceStatusV1;
using SourceFailure = GovernmentRuntimeAdapterSourceFailureV1;
using ObservationStatus = GovernmentRuntimeAdapterObservationStatusV1;

SourceStatus Fail(GovernmentRuntimeAdapterSourceResultV1 &output,
                  SourceFailure failure) noexcept {
  output.status = SourceStatus::unavailable;
  output.failure = failure;
  return output.status;
}

SourceFailure ValidateSample(
    const GovernmentRuntimeAdapterCollectorSampleV1 &sample) noexcept {
  if (!sample.paused) {
    return SourceFailure::requires_paused;
  }
  if (sample.campaign_root.status !=
      game::CampaignRootContextStatusV1::available) {
    return SourceFailure::campaign_collector_unavailable;
  }
  if (sample.loaded_features.status !=
      game::LoadedFeatureManifestStatusV1::available) {
    return SourceFailure::feature_collector_unavailable;
  }
  const auto &campaign_readiness = sample.campaign_root.readiness;
  const auto &feature_readiness = sample.loaded_features.readiness;
  if (!campaign_readiness.player_identity_ready ||
      !campaign_readiness.government_ready ||
      !campaign_readiness.same_frame_ready ||
      !feature_readiness.effective_feature_flags_ready ||
      !feature_readiness.script_dlc_keys_ready ||
      feature_readiness.entitlements_ready ||
      !feature_readiness.same_frame_ready ||
      !feature_readiness.actionable_ready) {
    return SourceFailure::collector_readiness_unavailable;
  }
  if (sample.campaign_root.snapshot_revision == 0 ||
      sample.campaign_root.snapshot_revision !=
          sample.loaded_features.snapshot_revision ||
      sample.campaign_root.date_raw != sample.loaded_features.date_raw) {
    return SourceFailure::collector_frame_mismatch;
  }
  if (sample.campaign_lifecycle_identity == 0 ||
      sample.feature_lifecycle_identity == 0) {
    return SourceFailure::collector_lifecycle_unavailable;
  }
  if (sample.campaign_root.government.has_value()) {
    const auto &government = sample.campaign_root.government.value();
    if (government.native_flag_count < 0 ||
        static_cast<std::size_t>(government.native_flag_count) !=
            government.flags.size()) {
      return SourceFailure::government_flag_count_mismatch;
    }
  }
  const auto &features = sample.loaded_features.effective_feature_flags;
  if (features.status != game::LoadedFeatureComponentStatusV1::available ||
      !features.native_count.has_value() ||
      features.native_count.value() !=
          static_cast<std::int32_t>(
              kGovernmentRuntimeAdapterFeatureCountV1) ||
      features.items.size() != kGovernmentRuntimeAdapterFeatureCountV1) {
    return SourceFailure::feature_count_mismatch;
  }
  const auto &dlcs = sample.loaded_features.script_dlc_keys;
  if (dlcs.status != game::LoadedFeatureComponentStatusV1::available ||
      !dlcs.enumerated_count.has_value() || dlcs.enumerated_count.value() < 0 ||
      static_cast<std::size_t>(dlcs.enumerated_count.value()) !=
          dlcs.keys.size()) {
    return SourceFailure::script_dlc_count_mismatch;
  }
  return SourceFailure::none;
}

SourceFailure CompareSamples(
    const GovernmentRuntimeAdapterCollectorSampleV1 &first,
    const GovernmentRuntimeAdapterCollectorSampleV1 &second) noexcept {
  if (first.campaign_root.snapshot_revision !=
          second.campaign_root.snapshot_revision ||
      first.loaded_features.snapshot_revision !=
          second.loaded_features.snapshot_revision ||
      first.campaign_root.date_raw != second.campaign_root.date_raw ||
      first.loaded_features.date_raw != second.loaded_features.date_raw) {
    return SourceFailure::collector_frame_mismatch;
  }
  if (first.campaign_lifecycle_identity !=
          second.campaign_lifecycle_identity ||
      first.feature_lifecycle_identity != second.feature_lifecycle_identity) {
    return SourceFailure::collector_lifecycle_drift;
  }
  if (first.campaign_root.player_character_id !=
      second.campaign_root.player_character_id) {
    return SourceFailure::player_identity_drift;
  }
  if (first.campaign_root.government != second.campaign_root.government) {
    return SourceFailure::government_identity_drift;
  }
  if (first.loaded_features.effective_feature_flags !=
      second.loaded_features.effective_feature_flags) {
    return SourceFailure::feature_identity_drift;
  }
  if (first.loaded_features.script_dlc_keys !=
      second.loaded_features.script_dlc_keys) {
    return SourceFailure::script_dlc_identity_drift;
  }
  return SourceFailure::none;
}

} // namespace

GovernmentRuntimeAdapterObserverResultV1
GovernmentRuntimeAdapterOwnedInputV1::Evaluate() const {
  std::vector<std::string_view> flag_views;
  flag_views.reserve(government_flags.size());
  for (const auto &flag : government_flags) {
    flag_views.emplace_back(flag);
  }
  std::vector<GovernmentRuntimeFeatureInputV1> feature_views;
  feature_views.reserve(effective_feature_flags.size());
  for (const auto &feature : effective_feature_flags) {
    feature_views.push_back(
        {feature.native_index, feature.key, feature.enabled});
  }
  std::vector<std::string_view> dlc_views;
  dlc_views.reserve(script_dlc_keys.size());
  for (const auto &key : script_dlc_keys) {
    dlc_views.emplace_back(key);
  }

  GovernmentRuntimeAdapterObserverInputV1 view{};
  view.exact_build_admitted = exact_build_admitted;
  view.application_main = application_main;
  view.paused = paused;
  view.state_identity_stable = state_identity_stable;
  view.frame = frame;
  view.player_character_id = player_character_id;
  view.effective_government_stable_key = effective_government_stable_key;
  view.government_flags_available = government_flags_available;
  view.government_flags = flag_views;
  view.feature_root_available = feature_root_available;
  view.effective_feature_flags = feature_views;
  view.enabled_feature_count = enabled_feature_count;
  view.script_dlc_set_available = script_dlc_set_available;
  view.script_dlc_keys = dlc_views;
  return EvaluateGovernmentRuntimeAdapterObserverV1(view);
}

bool CopyGovernmentRuntimeAdapterCollectorMemoryV1(
    const GovernmentRuntimeAdapterCollectorMemoryV1 &memory,
    GovernmentRuntimeAdapterCollectorSampleV1 &output) noexcept {
  output = {};
  if (memory.campaign_root == nullptr || memory.loaded_features == nullptr) {
    return false;
  }
  try {
    output.campaign_root = *memory.campaign_root;
    output.loaded_features = *memory.loaded_features;
    output.paused = memory.paused;
    output.campaign_lifecycle_identity = memory.campaign_lifecycle_identity;
    output.feature_lifecycle_identity = memory.feature_lifecycle_identity;
    return true;
  } catch (...) {
    output = {};
    return false;
  }
}

GovernmentRuntimeAdapterSourceStatusV1 ReadGovernmentRuntimeAdapterSourceV1(
    const GovernmentRuntimeAdapterSourceAccessV1 &access,
    GovernmentRuntimeAdapterSourceResultV1 &output) noexcept {
  output = {};
  try {
    if (!access.exact_build_admitted) {
      return Fail(output, SourceFailure::unsupported_build);
    }
    if (access.capture == nullptr || access.is_application_main == nullptr) {
      return Fail(output, SourceFailure::access_incomplete);
    }
    if (!access.is_application_main(access.context)) {
      return Fail(output, SourceFailure::requires_application_main);
    }

    GovernmentRuntimeAdapterCollectorSampleV1 first{};
    GovernmentRuntimeAdapterCollectorSampleV1 second{};
    if (!access.capture(access.context, first)) {
      return Fail(output, SourceFailure::first_capture_failed);
    }
    const auto first_failure = ValidateSample(first);
    if (first_failure != SourceFailure::none) {
      return Fail(output, first_failure);
    }
    if (!access.capture(access.context, second)) {
      return Fail(output, SourceFailure::second_capture_failed);
    }
    const auto second_failure = ValidateSample(second);
    if (second_failure != SourceFailure::none) {
      return Fail(output, second_failure);
    }

    output.first_snapshot_revision = first.campaign_root.snapshot_revision;
    output.second_snapshot_revision = second.campaign_root.snapshot_revision;
    output.campaign_lifecycle_identity = second.campaign_lifecycle_identity;
    output.feature_lifecycle_identity = second.feature_lifecycle_identity;
    const auto drift = CompareSamples(first, second);
    if (drift != SourceFailure::none) {
      return Fail(output, drift);
    }

    auto &owned = output.input;
    owned.exact_build_admitted = true;
    owned.application_main = true;
    owned.paused = true;
    owned.state_identity_stable = true;
    owned.frame = second.campaign_root.snapshot_revision;
    owned.player_character_id = second.campaign_root.player_character_id;
    owned.government_flags_available = true;
    if (second.campaign_root.government.has_value()) {
      const auto &government = second.campaign_root.government.value();
      owned.effective_government_stable_key = government.key;
      owned.government_flags = government.flags;
    }
    owned.feature_root_available = true;
    owned.effective_feature_flags.reserve(
        second.loaded_features.effective_feature_flags.items.size());
    owned.enabled_feature_count = 0;
    for (const auto &feature :
         second.loaded_features.effective_feature_flags.items) {
      owned.effective_feature_flags.push_back(
          {feature.native_index, feature.key, feature.enabled});
      if (feature.enabled) {
        ++owned.enabled_feature_count;
      }
    }
    owned.script_dlc_set_available = true;
    owned.script_dlc_keys = second.loaded_features.script_dlc_keys.keys;
    output.semantic_result = owned.Evaluate();
    if (output.semantic_result.status == ObservationStatus::unavailable) {
      return Fail(output, SourceFailure::semantic_input_rejected);
    }
    output.status = SourceStatus::available;
    output.failure = SourceFailure::none;
    return output.status;
  } catch (...) {
    return Fail(output, SourceFailure::semantic_input_rejected);
  }
}

} // namespace xar::bridge::private_observer
