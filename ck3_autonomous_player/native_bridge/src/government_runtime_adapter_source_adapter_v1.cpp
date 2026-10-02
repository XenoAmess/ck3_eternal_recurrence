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
  if (!sample.government_object_identity_available ||
      !sample.script_dlc_layout_identity_available) {
    return SourceFailure::collector_provenance_unavailable;
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
          static_cast<std::int32_t>(kGovernmentRuntimeAdapterFeatureCountV1) ||
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
  if (first.campaign_lifecycle_identity != second.campaign_lifecycle_identity ||
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
  if (first.government_object_identity != second.government_object_identity) {
    return SourceFailure::government_object_identity_drift;
  }
  if (first.loaded_features.effective_feature_flags !=
      second.loaded_features.effective_feature_flags) {
    return SourceFailure::feature_identity_drift;
  }
  if (first.loaded_features.script_dlc_keys !=
      second.loaded_features.script_dlc_keys) {
    return SourceFailure::script_dlc_identity_drift;
  }
  if (first.script_dlc_bucket_base_identity !=
          second.script_dlc_bucket_base_identity ||
      first.script_dlc_bucket_mask_identity !=
          second.script_dlc_bucket_mask_identity ||
      first.script_dlc_maximum_spill_identity !=
          second.script_dlc_maximum_spill_identity) {
    return SourceFailure::script_dlc_layout_identity_drift;
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
  view.feature_profile = feature_profile;
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
    output.government_object_identity_available =
        memory.government_object_identity_available;
    output.government_object_identity = memory.government_object_identity;
    output.script_dlc_layout_identity_available =
        memory.script_dlc_layout_identity_available;
    output.script_dlc_bucket_base_identity =
        memory.script_dlc_bucket_base_identity;
    output.script_dlc_bucket_mask_identity =
        memory.script_dlc_bucket_mask_identity;
    output.script_dlc_maximum_spill_identity =
        memory.script_dlc_maximum_spill_identity;
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
    output.date_raw = second.campaign_root.date_raw;
    output.campaign_lifecycle_identity = second.campaign_lifecycle_identity;
    output.feature_lifecycle_identity = second.feature_lifecycle_identity;
    const auto drift = CompareSamples(first, second);
    if (drift != SourceFailure::none) {
      return Fail(output, drift);
    }

    auto &owned = output.input;
    owned.feature_profile = access.feature_profile;
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

namespace {

void AppendGovernmentJsonString(std::string &output, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  output.push_back('"');
  for (const unsigned char character : value) {
    if (character == '"' || character == '\\') {
      output.push_back('\\');
      output.push_back(static_cast<char>(character));
    } else if (character < 0x20U) {
      output += "\\u00";
      output.push_back(hex[character >> 4U]);
      output.push_back(hex[character & 0xfU]);
    } else {
      output.push_back(static_cast<char>(character));
    }
  }
  output.push_back('"');
}

std::string_view GovernmentSourceFailureKey(SourceFailure failure) noexcept {
  switch (failure) {
  case SourceFailure::none: return "none";
  case SourceFailure::unsupported_build: return "unsupported_build";
  case SourceFailure::access_incomplete: return "access_incomplete";
  case SourceFailure::requires_application_main: return "requires_application_main";
  case SourceFailure::first_capture_failed: return "first_capture_failed";
  case SourceFailure::second_capture_failed: return "second_capture_failed";
  case SourceFailure::requires_paused: return "requires_paused";
  case SourceFailure::campaign_collector_unavailable: return "campaign_collector_unavailable";
  case SourceFailure::feature_collector_unavailable: return "feature_collector_unavailable";
  case SourceFailure::collector_readiness_unavailable: return "collector_readiness_unavailable";
  case SourceFailure::collector_frame_mismatch: return "collector_frame_mismatch";
  case SourceFailure::collector_lifecycle_unavailable: return "collector_lifecycle_unavailable";
  case SourceFailure::collector_lifecycle_drift: return "collector_lifecycle_drift";
  case SourceFailure::player_identity_drift: return "player_identity_drift";
  case SourceFailure::government_identity_drift: return "government_identity_drift";
  case SourceFailure::feature_identity_drift: return "feature_identity_drift";
  case SourceFailure::script_dlc_identity_drift: return "script_dlc_identity_drift";
  case SourceFailure::government_flag_count_mismatch: return "government_flag_count_mismatch";
  case SourceFailure::feature_count_mismatch: return "feature_count_mismatch";
  case SourceFailure::script_dlc_count_mismatch: return "script_dlc_count_mismatch";
  case SourceFailure::semantic_input_rejected: return "semantic_input_rejected";
  case SourceFailure::collector_provenance_unavailable: return "collector_provenance_unavailable";
  case SourceFailure::government_object_identity_drift: return "government_object_identity_drift";
  case SourceFailure::script_dlc_layout_identity_drift: return "script_dlc_layout_identity_drift";
  }
  return "unknown";
}

std::string_view GovernmentSelectionStatusKey(
    GovernmentRuntimeAdapterSelectionStatusV1 status) noexcept {
  using Status = GovernmentRuntimeAdapterSelectionStatusV1;
  switch (status) {
  case Status::unavailable: return "unavailable";
  case Status::core_supported: return "core_supported";
  case Status::adapter_spec_ready_not_implemented: return "adapter_spec_ready_not_implemented";
  case Status::unsupported_nonplayer_identity: return "unsupported_nonplayer_identity";
  case Status::religious_adapter_implementation_pending: return "religious_adapter_implementation_pending";
  case Status::unavailable_feature_mismatch: return "unavailable_feature_mismatch";
  case Status::unadapted_runtime_government: return "unadapted_runtime_government";
  }
  return "unavailable";
}

void AppendGovernmentJsonNames(std::string &output,
                              const std::vector<std::string> &names) {
  output.push_back('[');
  bool first = true;
  for (const auto &name : names) {
    if (!first) output.push_back(',');
    first = false;
    AppendGovernmentJsonString(output, name);
  }
  output.push_back(']');
}

void AppendGovernmentJsonFeatures(
    std::string &output,
    const std::vector<GovernmentRuntimeFeatureIdentityV1> &features) {
  output.push_back('[');
  bool first = true;
  for (const auto &feature : features) {
    if (!first) output.push_back(',');
    first = false;
    output += "{\"native_index\":" + std::to_string(feature.native_index) +
              ",\"key\":";
    AppendGovernmentJsonString(output, feature.key);
    output += feature.enabled ? ",\"enabled\":true}" : ",\"enabled\":false}";
  }
  output.push_back(']');
}

} // namespace

std::string SerializeGovernmentRuntimeAdapterSourceV1(
    const GovernmentRuntimeAdapterSourceResultV1 &result,
    GovernmentRuntimeAdapterBuildProfileV1 profile,
    std::uint64_t expected_revision) {
  const auto &semantic = result.semantic_result;
  const bool available = result.status == SourceStatus::available;
  const bool migrated = profile == GovernmentRuntimeAdapterBuildProfileV1::ck3_12002;
  const auto revision = result.second_snapshot_revision != 0
                            ? result.second_snapshot_revision
                            : expected_revision;
  std::string output =
      "{\"schema\":\"government-runtime-adapter-v1\",\"schema_version\":1,\"status\":";
  AppendGovernmentJsonString(
      output, !available ? "unavailable"
                         : semantic.status == ObservationStatus::not_present
                               ? "not_present" : "available");
  output += ",\"snapshot_revision\":" + std::to_string(revision) +
            ",\"date_raw\":" + std::to_string(result.date_raw) +
            ",\"build\":{\"version\":";
  AppendGovernmentJsonString(output, migrated ? "1.20.0.2" : "1.19.0.6");
  output += ",\"exe_sha256\":";
  AppendGovernmentJsonString(
      output, migrated
                  ? "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D"
                  : "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86");
  output += "},\"unavailable_reason\":";
  if (available) output += "null";
  else AppendGovernmentJsonString(output, GovernmentSourceFailureKey(result.failure));
  output += ",\"player_character_id\":";
  output += semantic.player_character_id.has_value()
                ? std::to_string(semantic.player_character_id.value()) : "null";
  output += ",\"government\":{\"key\":";
  AppendGovernmentJsonString(output, semantic.government.stable_key);
  output += semantic.government.recognized_stock_key
                ? ",\"recognized_stock_key\":true" : ",\"recognized_stock_key\":false";
  output += semantic.government.religious_identity_opaque
                ? ",\"religious_identity_opaque\":true" : ",\"religious_identity_opaque\":false";
  output += ",\"flags\":";
  AppendGovernmentJsonNames(output, semantic.government.observed_flags);
  output += "},\"effective_feature_flags\":{\"native_count\":";
  output += available ? std::to_string(semantic.effective_feature_flags.size()) : "null";
  output += ",\"items\":";
  AppendGovernmentJsonFeatures(output, semantic.effective_feature_flags);
  output += "},\"script_dlc_keys\":";
  AppendGovernmentJsonNames(output, semantic.script_dlc_keys);
  output += ",\"entitlements\":{\"status\":\"unavailable\","
            "\"unavailable_reason\":\"store_verdict_provenance_unclosed\"},\"adapter\":{\"status\":";
  AppendGovernmentJsonString(output, GovernmentSelectionStatusKey(semantic.adapter.status));
  output += ",\"family\":";
  if (semantic.adapter.family.has_value()) AppendGovernmentJsonString(output, semantic.adapter.family.value());
  else output += "null";
  output += semantic.adapter.requirements_met
                ? ",\"requirements_met\":true" : ",\"requirements_met\":false";
  output += ",\"required_effective_features\":";
  AppendGovernmentJsonNames(output, semantic.adapter.required_effective_features);
  output += ",\"capability_profile_features\":";
  AppendGovernmentJsonFeatures(output, semantic.adapter.capability_profile_features);
  const bool core_ready = available && semantic.status == ObservationStatus::available &&
      semantic.adapter.status == GovernmentRuntimeAdapterSelectionStatusV1::core_supported &&
      semantic.adapter.requirements_met;
  output += "},\"readiness\":{\"same_frame_ready\":";
  output += available ? "true" : "false";
  output += ",\"core_adapter_ready\":";
  output += core_ready ? "true" : "false";
  output += "},\"provenance\":{\"backend_id\":";
  AppendGovernmentJsonString(
      output, migrated ? "ck3-1.20.0.2-private-government-runtime-adapter-v1"
                       : "ck3-1.19.0.6-private-government-runtime-adapter-v1");
  output += ",\"campaign_backend_id\":";
  AppendGovernmentJsonString(
      output, migrated ? "ck3-1.20.0.2-native-campaign-root-context-v1"
                       : "ck3-1.19.0.6-native-campaign-root-context-v1");
  output += ",\"feature_backend_id\":";
  AppendGovernmentJsonString(
      output, migrated ? "ck3-1.20.0.2-native-loaded-feature-manifest-v1"
                       : "ck3-1.19.0.6-native-loaded-feature-manifest-v1");
  output += "}}";
  return output;
}

} // namespace xar::bridge::private_observer
