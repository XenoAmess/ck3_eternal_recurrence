#include "xar_bridge/government_runtime_adapter_bridge_binder_v1.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>

namespace xar::bridge::private_observer {
namespace {

using BindingFailure = GovernmentRuntimeAdapterBridgeBindingFailureV1;
using BindingState = GovernmentRuntimeAdapterBridgeBindingStateV1;

constexpr std::size_t kScriptDlcBucketBaseOffset = 0x08;
constexpr std::size_t kScriptDlcBucketMaskOffset = 0x14;
constexpr std::size_t kScriptDlcMaximumSpillOffset = 0x18;

thread_local BindingState *g_active_campaign_binding = nullptr;

template <typename Value>
void RecordStableIdentity(Value value, bool &seen, Value &identity,
                          bool &drift) noexcept {
  if (!seen) {
    seen = true;
    identity = value;
  } else if (identity != value) {
    drift = true;
  }
}

void ResetDetachedBindingState(BindingState &state) noexcept {
  state.campaign_environment = {};
  state.feature_environment = {};
  state.upstream_government_resolver = nullptr;
  state.upstream_campaign_access = {};
  state.upstream_feature_access = {};
  state.fixture_context = nullptr;
  state.fixture_capture = nullptr;
  state.offline_fixture = false;
  state.attached = false;
  state.execution_active = false;
  state.government_object_identity_seen = false;
  state.government_object_identity_drift = false;
  state.government_object_identity = 0;
  state.script_dlc_bucket_base_seen = false;
  state.script_dlc_bucket_mask_seen = false;
  state.script_dlc_maximum_spill_seen = false;
  state.script_dlc_layout_identity_drift = false;
  state.script_dlc_bucket_base_identity = 0;
  state.script_dlc_bucket_mask_identity = 0;
  state.script_dlc_maximum_spill_identity = 0;
  state.expected_revision = 0;
  state.execution_stamp = {};
  state.source_access = {};
  state.last_failure = BindingFailure::none;
}

bool CampaignAccessComplete(
    const xar::ck3_11906::CampaignRootAccessV1 &access) noexcept {
  return access.capture_frame != nullptr && access.is_main_thread != nullptr &&
         access.read_memory != nullptr;
}

bool FeatureAccessComplete(
    const xar::ck3_11906::LoadedFeatureManifestAccessV1 &access) noexcept {
  return access.capture_frame != nullptr && access.is_main_thread != nullptr &&
         access.read_memory != nullptr;
}

bool ExecutionStampValid(
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  return stamp.pump_epoch != 0 && stamp.thread_id != 0 && stamp.paused &&
         stamp.tls_initialized_flag_address != 0 &&
         stamp.tls_initialized == 1 && stamp.tls_context != 0 &&
         stamp.tls_main_thread_marker == 1 && stamp.jomini_state != 0 &&
         stamp.game_state != 0 && GetCurrentThreadId() == stamp.thread_id;
}

bool SampleMatchesExecutionBoundary(
    const BindingState &state,
    const GovernmentRuntimeAdapterCollectorSampleV1 &sample) noexcept {
  return sample.campaign_root.snapshot_revision == state.expected_revision &&
         sample.loaded_features.snapshot_revision == state.expected_revision &&
         sample.campaign_root.date_raw == state.execution_stamp.date_raw &&
         sample.loaded_features.date_raw == state.execution_stamp.date_raw &&
         sample.paused == state.execution_stamp.paused;
}

bool BindingIsApplicationMain(void *opaque) noexcept {
  const auto *state = static_cast<const BindingState *>(opaque);
  if (state == nullptr || !state->attached || !state->execution_active ||
      state->expected_revision == 0 ||
      !ExecutionStampValid(state->execution_stamp)) {
    return false;
  }
  if (state->offline_fixture) {
    return true;
  }
  return state->upstream_campaign_access.is_main_thread(
             state->upstream_campaign_access.context) &&
         state->upstream_feature_access.is_main_thread(
             state->upstream_feature_access.context);
}

bool CampaignProxyIsMainThread(void *opaque) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  return BindingIsApplicationMain(state) &&
         state->upstream_campaign_access.is_main_thread(
             state->upstream_campaign_access.context);
}

void *CampaignGovernmentResolverProxy(void *character) noexcept {
  auto *state = g_active_campaign_binding;
  if (state == nullptr || !BindingIsApplicationMain(state) ||
      state->upstream_government_resolver == nullptr) {
    return nullptr;
  }
  void *government = state->upstream_government_resolver(character);
  RecordStableIdentity(reinterpret_cast<std::uintptr_t>(government),
                       state->government_object_identity_seen,
                       state->government_object_identity,
                       state->government_object_identity_drift);
  return government;
}

bool CampaignProxyCaptureFrame(void *opaque,
                               game::CampaignRootFrameV1 &output) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  if (!CampaignProxyIsMainThread(state) ||
      !state->upstream_campaign_access.capture_frame(
          state->upstream_campaign_access.context, output)) {
    return false;
  }
  return output.snapshot_revision == state->expected_revision &&
         output.date_raw == state->execution_stamp.date_raw && output.paused;
}

bool CampaignProxyReadMemory(void *opaque, const void *address, void *output,
                             std::size_t size) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  return CampaignProxyIsMainThread(state) &&
         state->upstream_campaign_access.read_memory(
             state->upstream_campaign_access.context, address, output, size);
}

bool CampaignProxyReadString(void *opaque, const void *native_string,
                             std::string &output) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  return CampaignProxyIsMainThread(state) &&
         state->upstream_campaign_access.read_string != nullptr &&
         state->upstream_campaign_access.read_string(
             state->upstream_campaign_access.context, native_string, output);
}

bool FeatureProxyIsMainThread(void *opaque) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  return BindingIsApplicationMain(state) &&
         state->upstream_feature_access.is_main_thread(
             state->upstream_feature_access.context);
}

bool FeatureProxyCaptureFrame(
    void *opaque, game::LoadedFeatureManifestFrameV1 &output) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  if (!FeatureProxyIsMainThread(state) ||
      !state->upstream_feature_access.capture_frame(
          state->upstream_feature_access.context, output)) {
    return false;
  }
  return output.snapshot_revision == state->expected_revision &&
         output.date_raw == state->execution_stamp.date_raw && output.paused;
}

bool FeatureProxyReadMemory(void *opaque, const void *address, void *output,
                            std::size_t size) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  if (!FeatureProxyIsMainThread(state) || output == nullptr ||
      !state->upstream_feature_access.read_memory(
          state->upstream_feature_access.context, address, output, size)) {
    return false;
  }
  const auto set = reinterpret_cast<std::uintptr_t>(
      state->feature_environment.script_dlc_set);
  const auto current = reinterpret_cast<std::uintptr_t>(address);
  if (current == set + kScriptDlcBucketBaseOffset && size == sizeof(void *)) {
    void *value = nullptr;
    std::memcpy(&value, output, sizeof(value));
    RecordStableIdentity(reinterpret_cast<std::uintptr_t>(value),
                         state->script_dlc_bucket_base_seen,
                         state->script_dlc_bucket_base_identity,
                         state->script_dlc_layout_identity_drift);
  } else if (current == set + kScriptDlcBucketMaskOffset &&
             size == sizeof(std::uint32_t)) {
    std::uint32_t value = 0;
    std::memcpy(&value, output, sizeof(value));
    RecordStableIdentity(value, state->script_dlc_bucket_mask_seen,
                         state->script_dlc_bucket_mask_identity,
                         state->script_dlc_layout_identity_drift);
  } else if (current == set + kScriptDlcMaximumSpillOffset &&
             size == sizeof(std::uint8_t)) {
    std::uint8_t value = 0;
    std::memcpy(&value, output, sizeof(value));
    RecordStableIdentity(value, state->script_dlc_maximum_spill_seen,
                         state->script_dlc_maximum_spill_identity,
                         state->script_dlc_layout_identity_drift);
  }
  return true;
}

bool FeatureProxyReadString(void *opaque, const void *native_string,
                            std::string &output) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  return FeatureProxyIsMainThread(state) &&
         state->upstream_feature_access.read_string != nullptr &&
         state->upstream_feature_access.read_string(
             state->upstream_feature_access.context, native_string, output);
}

bool ReadPointer(const xar::ck3_11906::CampaignRootAccessV1 &access,
                 void **slot, std::uintptr_t &output) noexcept {
  output = 0;
  void *pointer = nullptr;
  if (slot == nullptr ||
      !access.read_memory(access.context, slot, &pointer, sizeof(pointer)) ||
      pointer == nullptr) {
    return false;
  }
  output = reinterpret_cast<std::uintptr_t>(pointer);
  return true;
}

bool ReadPointer(const xar::ck3_11906::LoadedFeatureManifestAccessV1 &access,
                 void **slot, std::uintptr_t &output) noexcept {
  output = 0;
  void *pointer = nullptr;
  if (slot == nullptr ||
      !access.read_memory(access.context, slot, &pointer, sizeof(pointer)) ||
      pointer == nullptr) {
    return false;
  }
  output = reinterpret_cast<std::uintptr_t>(pointer);
  return true;
}

bool CaptureProductionSample(
    BindingState &state,
    GovernmentRuntimeAdapterCollectorSampleV1 &output) noexcept {
  output = {};
  if (!BindingIsApplicationMain(&state)) {
    return false;
  }
  xar::ck3_11906::CampaignRootAccessV1 campaign{};
  campaign.context = &state;
  campaign.capture_frame = &CampaignProxyCaptureFrame;
  campaign.is_main_thread = &CampaignProxyIsMainThread;
  campaign.read_memory = &CampaignProxyReadMemory;
  campaign.read_string = state.upstream_campaign_access.read_string == nullptr
                             ? nullptr
                             : &CampaignProxyReadString;

  xar::ck3_11906::LoadedFeatureManifestAccessV1 feature{};
  feature.context = &state;
  feature.capture_frame = &FeatureProxyCaptureFrame;
  feature.is_main_thread = &FeatureProxyIsMainThread;
  feature.read_memory = &FeatureProxyReadMemory;
  feature.read_string = state.upstream_feature_access.read_string == nullptr
                            ? nullptr
                            : &FeatureProxyReadString;

  std::uintptr_t campaign_lifecycle_before = 0;
  std::uintptr_t feature_lifecycle_before = 0;
  std::uintptr_t campaign_lifecycle_after = 0;
  std::uintptr_t feature_lifecycle_after = 0;
  const bool lifecycle_before =
      ReadPointer(campaign, state.campaign_environment.game_state_slot,
                  campaign_lifecycle_before) &&
      ReadPointer(feature, state.feature_environment.feature_root_slot,
                  feature_lifecycle_before);

  state.government_object_identity_seen = false;
  state.government_object_identity_drift = false;
  state.government_object_identity = 0;
  auto *previous_campaign_binding = g_active_campaign_binding;
  g_active_campaign_binding = &state;
  const auto campaign_result = xar::ck3_11906::ReadCampaignRootContextV1(
      state.campaign_environment, campaign, {state.expected_revision},
      output.campaign_root);
  g_active_campaign_binding = previous_campaign_binding;

  state.script_dlc_bucket_base_seen = false;
  state.script_dlc_bucket_mask_seen = false;
  state.script_dlc_maximum_spill_seen = false;
  state.script_dlc_layout_identity_drift = false;
  state.script_dlc_bucket_base_identity = 0;
  state.script_dlc_bucket_mask_identity = 0;
  state.script_dlc_maximum_spill_identity = 0;
  const auto feature_result = xar::ck3_11906::ReadLoadedFeatureManifestV1(
      state.feature_environment, feature, {state.expected_revision},
      output.loaded_features);

  const bool lifecycle_after =
      ReadPointer(campaign, state.campaign_environment.game_state_slot,
                  campaign_lifecycle_after) &&
      ReadPointer(feature, state.feature_environment.feature_root_slot,
                  feature_lifecycle_after);
  output.paused = state.execution_stamp.paused;
  if (lifecycle_before && lifecycle_after &&
      campaign_lifecycle_before == state.execution_stamp.game_state &&
      campaign_lifecycle_before == campaign_lifecycle_after &&
      feature_lifecycle_before == feature_lifecycle_after) {
    output.campaign_lifecycle_identity = campaign_lifecycle_after;
    output.feature_lifecycle_identity = feature_lifecycle_after;
  }
  output.government_object_identity_available =
      state.government_object_identity_seen &&
      !state.government_object_identity_drift;
  output.government_object_identity = state.government_object_identity;
  output.script_dlc_layout_identity_available =
      state.script_dlc_bucket_base_seen && state.script_dlc_bucket_mask_seen &&
      state.script_dlc_maximum_spill_seen &&
      !state.script_dlc_layout_identity_drift;
  output.script_dlc_bucket_base_identity =
      state.script_dlc_bucket_base_identity;
  output.script_dlc_bucket_mask_identity =
      state.script_dlc_bucket_mask_identity;
  output.script_dlc_maximum_spill_identity =
      state.script_dlc_maximum_spill_identity;

  // Both readers publish typed unavailable rows. Returning true preserves
  // those collector failures for the source adapter instead of collapsing
  // them into an untyped capture failure.
  (void)campaign_result;
  (void)feature_result;
  return true;
}

bool BindingCapture(
    void *opaque, GovernmentRuntimeAdapterCollectorSampleV1 &output) noexcept {
  auto *state = static_cast<BindingState *>(opaque);
  if (state == nullptr || !BindingIsApplicationMain(state)) {
    output = {};
    return false;
  }
  if (state->offline_fixture) {
    return state->fixture_capture != nullptr &&
           state->fixture_capture(state->fixture_context, output) &&
           SampleMatchesExecutionBoundary(*state, output);
  }
  return CaptureProductionSample(*state, output);
}

void SetTypedExecutionFailure(
    GovernmentRuntimeAdapterSourceResultV1 &result,
    GovernmentRuntimeAdapterSourceFailureV1 failure) noexcept {
  result = {};
  result.status = GovernmentRuntimeAdapterSourceStatusV1::unavailable;
  result.failure = failure;
}

bool IsExecutingExactMailboxSlot(
    const GovernmentRuntimeAdapterPrivateOperationV1 &operation,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (operation.binding == nullptr || operation.mailbox == nullptr ||
      operation.ticket.sequence == 0 || !operation.prepared ||
      operation.executed || operation.completed ||
      operation.expected_revision == 0 || !operation.binding->attached ||
      operation.binding->execution_active || !ExecutionStampValid(stamp)) {
    return false;
  }
  const auto &mailbox = *operation.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             xar::ck3_11906::MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             operation.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             stamp.thread_id &&
         mailbox.paused_owner_verified_pump_epochs.load(
             std::memory_order_acquire) >=
             xar::ck3_11906::
                 kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs &&
         mailbox.executor ==
             &ExecuteGovernmentRuntimeAdapterPrivateOperationV1 &&
         mailbox.executor_context ==
             const_cast<GovernmentRuntimeAdapterPrivateOperationV1 *>(
                 &operation);
}

} // namespace

bool BindGovernmentRuntimeAdapterBridgeV1(
    const GovernmentRuntimeAdapterBridgeBindingEnvironmentV1 &environment,
    GovernmentRuntimeAdapterBridgeBindingStateV1 &state,
    GovernmentRuntimeAdapterSourceAccessV1 &source_access) noexcept {
  if (state.attached || state.execution_active) {
    state.last_failure = BindingFailure::binding_already_attached;
    return false;
  }
  ResetDetachedBindingState(state);
  source_access = {};
  if (!environment.binding_enabled) {
    state.last_failure = BindingFailure::binding_disabled;
    return false;
  }
  if (!environment.exact_build_admitted ||
      environment.admitted_game_version !=
          kGovernmentRuntimeAdapterBridgeBinderV1GameVersion ||
      environment.admitted_executable_sha256 !=
          kGovernmentRuntimeAdapterBridgeBinderV1ExecutableSha256) {
    state.last_failure = BindingFailure::unsupported_build;
    return false;
  }
  if (environment.module_base == 0) {
    state.last_failure = BindingFailure::module_unavailable;
    return false;
  }
  if (environment.offline_fixture) {
    if (environment.fixture_capture == nullptr) {
      state.last_failure = BindingFailure::fixture_override_incomplete;
      return false;
    }
  } else {
    if (environment.fixture_context != nullptr ||
        environment.fixture_capture != nullptr) {
      state.last_failure = BindingFailure::fixture_override_forbidden;
      return false;
    }
    if (!CampaignAccessComplete(environment.campaign_access)) {
      state.last_failure = BindingFailure::campaign_access_incomplete;
      return false;
    }
    if (!FeatureAccessComplete(environment.feature_access)) {
      state.last_failure = BindingFailure::feature_access_incomplete;
      return false;
    }
  }

  state.campaign_environment =
      xar::ck3_11906::BindCampaignRootNativeEnvironmentV1(
          environment.module_base, true);
  state.feature_environment =
      xar::ck3_11906::BindLoadedFeatureManifestNativeEnvironmentV1(
          environment.module_base, true);
  if (!environment.offline_fixture) {
    state.upstream_government_resolver = state.campaign_environment.government;
    state.campaign_environment.government = &CampaignGovernmentResolverProxy;
    state.campaign_environment.offline_fixture_function_overrides = true;
  }
  state.upstream_campaign_access = environment.campaign_access;
  state.upstream_feature_access = environment.feature_access;
  state.fixture_context = environment.fixture_context;
  state.fixture_capture = environment.fixture_capture;
  state.offline_fixture = environment.offline_fixture;
  state.attached = true;
  state.last_failure = BindingFailure::none;
  state.source_access = {true, &state, &BindingIsApplicationMain,
                         &BindingCapture};
  source_access = state.source_access;
  return true;
}

bool PrepareGovernmentRuntimeAdapterPrivateOperationV1(
    GovernmentRuntimeAdapterBridgeBindingStateV1 &binding,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    std::uint64_t expected_revision,
    GovernmentRuntimeAdapterPrivateOperationV1 &operation) noexcept {
  if (!binding.attached || binding.execution_active || expected_revision == 0 ||
      operation.binding != nullptr || operation.mailbox != nullptr ||
      operation.ticket.sequence != 0 || operation.prepared ||
      operation.executed || operation.completed ||
      operation.executor_invocations != 0) {
    binding.last_failure = BindingFailure::operation_not_prepared;
    return false;
  }
  operation.binding = &binding;
  operation.mailbox = &mailbox;
  operation.ticket = {};
  operation.expected_revision = expected_revision;
  operation.prepared = true;
  operation.executed = false;
  operation.completed = false;
  operation.executor_invocations = 0;
  operation.result = {};
  binding.last_failure = BindingFailure::none;
  return true;
}

bool ExecuteGovernmentRuntimeAdapterPrivateOperationV1(
    void *opaque_operation,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  auto *operation = static_cast<GovernmentRuntimeAdapterPrivateOperationV1 *>(
      opaque_operation);
  if (operation == nullptr || !IsExecutingExactMailboxSlot(*operation, stamp)) {
    if (operation != nullptr && operation->binding != nullptr) {
      operation->binding->last_failure =
          BindingFailure::execution_stamp_invalid;
    }
    return false;
  }

  operation->executed = true;
  ++operation->executor_invocations;
  auto &binding = *operation->binding;
  binding.last_failure = BindingFailure::none;
  binding.execution_active = true;
  binding.expected_revision = operation->expected_revision;
  binding.execution_stamp = stamp;
  try {
    (void)ReadGovernmentRuntimeAdapterSourceV1(binding.source_access,
                                               operation->result);
  } catch (...) {
    SetTypedExecutionFailure(
        operation->result,
        GovernmentRuntimeAdapterSourceFailureV1::semantic_input_rejected);
  }
  binding.execution_active = false;
  binding.expected_revision = 0;
  binding.execution_stamp = {};
  operation->completed = true;
  return true;
}

std::string_view GovernmentRuntimeAdapterBridgeBindingFailureKeyV1(
    GovernmentRuntimeAdapterBridgeBindingFailureV1 failure) noexcept {
  switch (failure) {
  case BindingFailure::none:
    return "none";
  case BindingFailure::binding_already_attached:
    return "binding_already_attached";
  case BindingFailure::binding_disabled:
    return "binding_disabled";
  case BindingFailure::unsupported_build:
    return "unsupported_build";
  case BindingFailure::module_unavailable:
    return "module_unavailable";
  case BindingFailure::campaign_access_incomplete:
    return "campaign_access_incomplete";
  case BindingFailure::feature_access_incomplete:
    return "feature_access_incomplete";
  case BindingFailure::fixture_override_incomplete:
    return "fixture_override_incomplete";
  case BindingFailure::fixture_override_forbidden:
    return "fixture_override_forbidden";
  case BindingFailure::operation_not_prepared:
    return "operation_not_prepared";
  case BindingFailure::execution_stamp_invalid:
    return "execution_stamp_invalid";
  }
  return "unknown";
}

} // namespace xar::bridge::private_observer
