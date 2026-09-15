#pragma once

#include "xar_bridge/government_runtime_adapter_source_adapter_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::bridge::private_observer {

inline constexpr std::string_view
    kGovernmentRuntimeAdapterBridgeBinderV1GameVersion = "1.19.0.6";
inline constexpr std::string_view
    kGovernmentRuntimeAdapterBridgeBinderV1ExecutableSha256 =
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

enum class GovernmentRuntimeAdapterBridgeBindingFailureV1 : std::uint32_t {
  none = 0,
  binding_already_attached,
  binding_disabled,
  unsupported_build,
  module_unavailable,
  campaign_access_incomplete,
  feature_access_incomplete,
  fixture_override_incomplete,
  fixture_override_forbidden,
  operation_not_prepared,
  execution_stamp_invalid,
};

using CaptureGovernmentRuntimeAdapterFixtureSampleV1 = bool (*)(
    void *context, GovernmentRuntimeAdapterCollectorSampleV1 &output) noexcept;

struct GovernmentRuntimeAdapterBridgeBindingEnvironmentV1 {
  bool binding_enabled = false;
  bool exact_build_admitted = false;
  std::string_view admitted_game_version;
  std::string_view admitted_executable_sha256;
  std::uintptr_t module_base = 0;
  bool offline_fixture = false;
  xar::ck3_11906::CampaignRootAccessV1 campaign_access;
  xar::ck3_11906::LoadedFeatureManifestAccessV1 feature_access;
  void *fixture_context = nullptr;
  CaptureGovernmentRuntimeAdapterFixtureSampleV1 fixture_capture = nullptr;
};

struct GovernmentRuntimeAdapterBridgeBindingStateV1 {
  GovernmentRuntimeAdapterBridgeBindingStateV1() noexcept = default;
  GovernmentRuntimeAdapterBridgeBindingStateV1(
      const GovernmentRuntimeAdapterBridgeBindingStateV1 &) = delete;
  GovernmentRuntimeAdapterBridgeBindingStateV1 &
  operator=(const GovernmentRuntimeAdapterBridgeBindingStateV1 &) = delete;
  GovernmentRuntimeAdapterBridgeBindingStateV1(
      GovernmentRuntimeAdapterBridgeBindingStateV1 &&) = delete;
  GovernmentRuntimeAdapterBridgeBindingStateV1 &
  operator=(GovernmentRuntimeAdapterBridgeBindingStateV1 &&) = delete;

  xar::ck3_11906::CampaignRootNativeEnvironmentV1 campaign_environment;
  xar::ck3_11906::LoadedFeatureManifestNativeEnvironmentV1 feature_environment;
  xar::ck3_11906::NativeCampaignRootCharacterResolverV1
      upstream_government_resolver = nullptr;
  xar::ck3_11906::CampaignRootAccessV1 upstream_campaign_access;
  xar::ck3_11906::LoadedFeatureManifestAccessV1 upstream_feature_access;
  void *fixture_context = nullptr;
  CaptureGovernmentRuntimeAdapterFixtureSampleV1 fixture_capture = nullptr;
  bool offline_fixture = false;
  bool attached = false;
  bool execution_active = false;
  bool government_object_identity_seen = false;
  bool government_object_identity_drift = false;
  std::uintptr_t government_object_identity = 0;
  bool script_dlc_bucket_base_seen = false;
  bool script_dlc_bucket_mask_seen = false;
  bool script_dlc_maximum_spill_seen = false;
  bool script_dlc_layout_identity_drift = false;
  std::uintptr_t script_dlc_bucket_base_identity = 0;
  std::uint32_t script_dlc_bucket_mask_identity = 0;
  std::uint8_t script_dlc_maximum_spill_identity = 0;
  std::uint64_t expected_revision = 0;
  xar::ck3_11906::MainThreadExecutionStampV1 execution_stamp;
  GovernmentRuntimeAdapterSourceAccessV1 source_access;
  GovernmentRuntimeAdapterBridgeBindingFailureV1 last_failure =
      GovernmentRuntimeAdapterBridgeBindingFailureV1::none;
};

struct GovernmentRuntimeAdapterPrivateOperationV1 {
  GovernmentRuntimeAdapterPrivateOperationV1() noexcept = default;
  GovernmentRuntimeAdapterPrivateOperationV1(
      const GovernmentRuntimeAdapterPrivateOperationV1 &) = delete;
  GovernmentRuntimeAdapterPrivateOperationV1 &
  operator=(const GovernmentRuntimeAdapterPrivateOperationV1 &) = delete;
  GovernmentRuntimeAdapterPrivateOperationV1(
      GovernmentRuntimeAdapterPrivateOperationV1 &&) = delete;
  GovernmentRuntimeAdapterPrivateOperationV1 &
  operator=(GovernmentRuntimeAdapterPrivateOperationV1 &&) = delete;

  GovernmentRuntimeAdapterBridgeBindingStateV1 *binding = nullptr;
  xar::ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  xar::ck3_11906::MainThreadQueryTicketV1 ticket;
  std::uint64_t expected_revision = 0;
  bool prepared = false;
  bool executed = false;
  bool completed = false;
  std::uint32_t executor_invocations = 0;
  GovernmentRuntimeAdapterSourceResultV1 result;
};

// Binds the already-versioned campaign-root and loaded-feature readers into
// one private source access. No command, protocol schema, or MCP surface is
// registered here.
bool BindGovernmentRuntimeAdapterBridgeV1(
    const GovernmentRuntimeAdapterBridgeBindingEnvironmentV1 &environment,
    GovernmentRuntimeAdapterBridgeBindingStateV1 &state,
    GovernmentRuntimeAdapterSourceAccessV1 &source_access) noexcept;

bool PrepareGovernmentRuntimeAdapterPrivateOperationV1(
    GovernmentRuntimeAdapterBridgeBindingStateV1 &binding,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    std::uint64_t expected_revision,
    GovernmentRuntimeAdapterPrivateOperationV1 &operation) noexcept;

// The private caller passes operation.ticket to TrySubmitMainThreadQueryV1
// after preparation. The executor accepts the operation only while that exact
// ticket owns the mailbox's executing slot.

// This is a fixed read-only MainThreadQueryMailbox executor. A typed source
// failure is a completed operation and returns true; false is reserved for an
// invalid/repeated operation container.
bool ExecuteGovernmentRuntimeAdapterPrivateOperationV1(
    void *opaque_operation,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view GovernmentRuntimeAdapterBridgeBindingFailureKeyV1(
    GovernmentRuntimeAdapterBridgeBindingFailureV1 failure) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteGovernmentRuntimeAdapterPrivateOperationV1),
                   xar::ck3_11906::MainThreadQueryExecutorV1>);

} // namespace xar::bridge::private_observer
