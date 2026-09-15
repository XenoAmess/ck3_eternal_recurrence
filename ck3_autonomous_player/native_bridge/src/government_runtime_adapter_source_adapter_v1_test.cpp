#include "xar_bridge/government_runtime_adapter_source_adapter_v1.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

namespace observer = xar::bridge::private_observer;
namespace game = xar::game;
using Failure = observer::GovernmentRuntimeAdapterSourceFailureV1;
using Sample = observer::GovernmentRuntimeAdapterCollectorSampleV1;
using SourceResult = observer::GovernmentRuntimeAdapterSourceResultV1;
using SourceStatus = observer::GovernmentRuntimeAdapterSourceStatusV1;

struct FixtureContext {
  bool application_main = true;
  std::vector<Sample> samples;
  std::size_t next_sample = 0;
  std::optional<std::size_t> fail_capture;
};

bool IsApplicationMain(void *opaque) noexcept {
  const auto *context = static_cast<const FixtureContext *>(opaque);
  return context != nullptr && context->application_main;
}

bool Capture(void *opaque, Sample &output) noexcept {
  auto *context = static_cast<FixtureContext *>(opaque);
  if (context == nullptr ||
      (context->fail_capture.has_value() &&
       context->next_sample == context->fail_capture.value()) ||
      context->next_sample >= context->samples.size()) {
    return false;
  }
  try {
    output = context->samples[context->next_sample++];
    return true;
  } catch (...) {
    output = {};
    return false;
  }
}

Sample AvailableSample() {
  Sample sample{};
  sample.paused = true;
  sample.campaign_lifecycle_identity = 0xCA'11;
  sample.feature_lifecycle_identity = 0xFE'A7;
  sample.government_object_identity_available = true;
  sample.government_object_identity = 0x60'01;
  sample.script_dlc_layout_identity_available = true;
  sample.script_dlc_bucket_base_identity = 0xD1'C0;
  sample.script_dlc_bucket_mask_identity = 7;
  sample.script_dlc_maximum_spill_identity = 2;

  auto &campaign = sample.campaign_root;
  campaign.status = game::CampaignRootContextStatusV1::available;
  campaign.snapshot_revision = 701;
  campaign.date_raw = 1'220'410;
  campaign.player_character_id = 29'829;
  campaign.government = game::CampaignRootGovernmentV1{
      "feudal_government",
      {"government_uses_domain_limit", "government_is_feudal"},
      2};
  campaign.readiness.player_identity_ready = true;
  campaign.readiness.government_ready = true;
  campaign.readiness.same_frame_ready = true;

  auto &manifest = sample.loaded_features;
  manifest.status = game::LoadedFeatureManifestStatusV1::available;
  manifest.snapshot_revision = campaign.snapshot_revision;
  manifest.date_raw = campaign.date_raw;
  const auto keys = observer::GovernmentRuntimeAdapterExpectedFeatureKeysV1();
  manifest.effective_feature_flags.status =
      game::LoadedFeatureComponentStatusV1::available;
  manifest.effective_feature_flags.native_count =
      static_cast<std::int32_t>(keys.size());
  manifest.effective_feature_flags.items.reserve(keys.size());
  for (std::size_t index = 0; index < keys.size(); ++index) {
    const auto key = keys[index];
    const bool enabled = key == "roads_to_power" || key == "admin_gov";
    manifest.effective_feature_flags.items.push_back(
        {static_cast<std::int32_t>(index),
         static_cast<std::uint32_t>(1'000 + index), std::string(key), enabled});
  }
  manifest.script_dlc_keys.status =
      game::LoadedFeatureComponentStatusV1::available;
  manifest.script_dlc_keys.enumerated_count = 2;
  manifest.script_dlc_keys.keys = {"A Royal Court", "Roads to Power"};
  manifest.readiness.effective_feature_flags_ready = true;
  manifest.readiness.script_dlc_keys_ready = true;
  manifest.readiness.entitlements_ready = false;
  manifest.readiness.same_frame_ready = true;
  manifest.readiness.actionable_ready = true;
  return sample;
}

observer::GovernmentRuntimeAdapterSourceAccessV1
Access(FixtureContext &context) {
  return {true, &context, IsApplicationMain, Capture};
}

SourceResult Read(FixtureContext &context) {
  SourceResult output{};
  observer::ReadGovernmentRuntimeAdapterSourceV1(Access(context), output);
  return output;
}

bool TestAvailableOwnedObservation() {
  const auto sample = AvailableSample();
  FixtureContext context{true, {sample, sample}};
  const auto result = Read(context);
  return result.status == SourceStatus::available &&
         result.failure == Failure::none &&
         result.first_snapshot_revision == 701 &&
         result.second_snapshot_revision == 701 &&
         result.campaign_lifecycle_identity == 0xCA'11 &&
         result.feature_lifecycle_identity == 0xFE'A7 &&
         result.input.player_character_id ==
             std::optional<std::int32_t>{29'829} &&
         result.input.effective_government_stable_key == "feudal_government" &&
         result.input.government_flags.size() == 2 &&
         result.input.effective_feature_flags.size() == 44 &&
         result.input.enabled_feature_count == 2 &&
         result.input.script_dlc_keys ==
             std::vector<std::string>{"A Royal Court", "Roads to Power"} &&
         result.semantic_result.status ==
             observer::GovernmentRuntimeAdapterObservationStatusV1::available &&
         result.semantic_result.adapter.status ==
             observer::GovernmentRuntimeAdapterSelectionStatusV1::
                 core_supported &&
         result.semantic_result.adapter.requirements_met;
}

bool TestCopyOwnsCollectorData() {
  auto campaign = AvailableSample().campaign_root;
  auto features = AvailableSample().loaded_features;
  observer::GovernmentRuntimeAdapterCollectorMemoryV1 memory{};
  memory.campaign_root = &campaign;
  memory.loaded_features = &features;
  memory.paused = true;
  memory.campaign_lifecycle_identity = 41;
  memory.feature_lifecycle_identity = 43;
  memory.government_object_identity_available = true;
  memory.government_object_identity = 47;
  memory.script_dlc_layout_identity_available = true;
  memory.script_dlc_bucket_base_identity = 53;
  memory.script_dlc_bucket_mask_identity = 7;
  memory.script_dlc_maximum_spill_identity = 2;
  Sample output{};
  if (!observer::CopyGovernmentRuntimeAdapterCollectorMemoryV1(memory,
                                                               output)) {
    return false;
  }
  campaign.government->key = "changed_after_copy";
  features.script_dlc_keys.keys.clear();
  observer::GovernmentRuntimeAdapterCollectorMemoryV1 incomplete{};
  Sample rejected = output;
  return output.campaign_root.government->key == "feudal_government" &&
         output.loaded_features.script_dlc_keys.keys.size() == 2 &&
         output.campaign_lifecycle_identity == 41 &&
         output.feature_lifecycle_identity == 43 &&
         output.government_object_identity_available &&
         output.government_object_identity == 47 &&
         output.script_dlc_layout_identity_available &&
         output.script_dlc_bucket_base_identity == 53 &&
         output.script_dlc_bucket_mask_identity == 7 &&
         output.script_dlc_maximum_spill_identity == 2 &&
         !observer::CopyGovernmentRuntimeAdapterCollectorMemoryV1(incomplete,
                                                                  rejected) &&
         rejected == Sample{};
}

bool TestAdmissionAndCaptureFailures() {
  const auto sample = AvailableSample();
  FixtureContext context{true, {sample, sample}};
  SourceResult output{};
  auto access = Access(context);
  access.exact_build_admitted = false;
  observer::ReadGovernmentRuntimeAdapterSourceV1(access, output);
  const bool build = output.failure == Failure::unsupported_build;

  access = Access(context);
  access.capture = nullptr;
  observer::ReadGovernmentRuntimeAdapterSourceV1(access, output);
  const bool incomplete = output.failure == Failure::access_incomplete;

  context.application_main = false;
  observer::ReadGovernmentRuntimeAdapterSourceV1(Access(context), output);
  const bool thread = output.failure == Failure::requires_application_main;

  context = FixtureContext{true, {sample, sample}, 0, 0};
  observer::ReadGovernmentRuntimeAdapterSourceV1(Access(context), output);
  const bool first = output.failure == Failure::first_capture_failed;

  context = FixtureContext{true, {sample, sample}, 0, 1};
  observer::ReadGovernmentRuntimeAdapterSourceV1(Access(context), output);
  const bool second = output.failure == Failure::second_capture_failed;
  return build && incomplete && thread && first && second;
}

bool TestCollectorValidationFailures() {
  const auto baseline = AvailableSample();
  auto verify = [&baseline](Failure expected, const auto &mutate) -> bool {
    auto changed = baseline;
    mutate(changed);
    FixtureContext context{true, {changed, changed}};
    return Read(context).failure == expected;
  };
  return verify(Failure::requires_paused,
                [](Sample &sample) { sample.paused = false; }) &&
         verify(Failure::collector_readiness_unavailable,
                [](Sample &sample) {
                  sample.loaded_features.readiness.actionable_ready = false;
                }) &&
         verify(Failure::collector_frame_mismatch,
                [](Sample &sample) {
                  ++sample.loaded_features.snapshot_revision;
                }) &&
         verify(
             Failure::collector_lifecycle_unavailable,
             [](Sample &sample) { sample.campaign_lifecycle_identity = 0; }) &&
         verify(Failure::collector_provenance_unavailable,
                [](Sample &sample) {
                  sample.government_object_identity_available = false;
                }) &&
         verify(Failure::government_flag_count_mismatch,
                [](Sample &sample) {
                  ++sample.campaign_root.government->native_flag_count;
                }) &&
         verify(
             Failure::feature_count_mismatch,
             [](Sample &sample) {
               sample.loaded_features.effective_feature_flags.items.pop_back();
             }) &&
         verify(Failure::script_dlc_count_mismatch, [](Sample &sample) {
           sample.loaded_features.script_dlc_keys.enumerated_count = 1;
         });
}

bool TestSecondSampleDriftFailures() {
  const auto baseline = AvailableSample();
  auto verify = [&baseline](Failure expected, const auto &mutate) -> bool {
    auto changed = baseline;
    mutate(changed);
    FixtureContext context{true, {baseline, changed}};
    return Read(context).failure == expected;
  };
  return verify(Failure::collector_frame_mismatch,
                [](Sample &sample) {
                  ++sample.campaign_root.snapshot_revision;
                  ++sample.loaded_features.snapshot_revision;
                }) &&
         verify(Failure::collector_lifecycle_drift,
                [](Sample &sample) { ++sample.feature_lifecycle_identity; }) &&
         verify(Failure::player_identity_drift,
                [](Sample &sample) {
                  sample.campaign_root.player_character_id = 31'337;
                }) &&
         verify(Failure::government_identity_drift,
                [](Sample &sample) {
                  sample.campaign_root.government->key = "clan_government";
                }) &&
         verify(Failure::government_object_identity_drift,
                [](Sample &sample) { ++sample.government_object_identity; }) &&
         verify(
             Failure::feature_identity_drift,
             [](Sample &sample) {
               sample.loaded_features.effective_feature_flags.items[0].enabled =
                   !sample.loaded_features.effective_feature_flags.items[0]
                        .enabled;
             }) &&
         verify(Failure::script_dlc_identity_drift,
                [](Sample &sample) {
                  sample.loaded_features.script_dlc_keys.keys[0] =
                      "Royal Court";
                }) &&
         verify(Failure::script_dlc_layout_identity_drift, [](Sample &sample) {
           ++sample.script_dlc_bucket_mask_identity;
         });
}

bool TestSemanticRejectionIsTyped() {
  auto sample = AvailableSample();
  std::swap(sample.loaded_features.effective_feature_flags.items[0],
            sample.loaded_features.effective_feature_flags.items[1]);
  FixtureContext context{true, {sample, sample}};
  return Read(context).failure == Failure::semantic_input_rejected;
}

} // namespace

int main() {
  const bool green =
      TestAvailableOwnedObservation() && TestCopyOwnsCollectorData() &&
      TestAdmissionAndCaptureFailures() && TestCollectorValidationFailures() &&
      TestSecondSampleDriftFailures() && TestSemanticRejectionIsTyped();
  if (!green) {
    std::cerr << "government-runtime-adapter-source-adapter-v1: RED\n";
    return 1;
  }
  std::cout << "government-runtime-adapter-source-adapter-v1: GREEN\n";
  return 0;
}
