#pragma once

#include "xar_bridge/activity_planning_snapshot_v1_native_binder.hpp"

#include <atomic>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityPlanningApplicationGluePrivateKeyV1 =
    "g2_activity_planning_snapshot_v1_application_glue";

enum class ActivityPlanningApplicationGlueFailureV1 : std::uint32_t {
  none = 0,
  glue_disabled,
  already_configured,
  exact_build_not_admitted,
  callbacks_missing,
  binder_rejected,
  source_adapter_rejected,
  request_invalid,
  request_already_prepared,
  execution_not_prepared,
  execution_busy,
  frame_unavailable,
  requires_application_main,
  requires_paused,
  frame_mismatch,
  operation_outside_scope,
  observer_unavailable,
};

// The caller owns the exact native operations and their context. The glue
// replaces their context with a private scoped wrapper before configuring the
// Activity4 binder, so neither operation can run outside Execute...V1.
struct ActivityPlanningApplicationGlueEnvironmentV1 {
  bool glue_enabled = false;
  ActivityPlanningNativeBinderEnvironmentV1 native_environment{};
};

struct ActivityPlanningApplicationGlueDiagnosticsV1 {
  bool installed = false;
  bool request_prepared = false;
  bool execution_active = false;
  bool result_ready = false;
  bool result_available = false;
  ActivityPlanningApplicationGlueFailureV1 failure =
      ActivityPlanningApplicationGlueFailureV1::none;
  ActivityPlanningNativeBinderFailureV1 binder_failure =
      ActivityPlanningNativeBinderFailureV1::none;
  ActivityPlanningSourceAdapterFailureV1 source_adapter_failure =
      ActivityPlanningSourceAdapterFailureV1::none;
};

struct ActivityPlanningApplicationGlueStateV1 {
  ActivityPlanningApplicationGlueEnvironmentV1 environment{};
  ActivityPlanningNativeBinderStateV1 binder{};
  ActivityPlanningSourceAdapterStateV1 source_adapter{};
  ActivityPlanningSnapshotPrivateEnvironmentV1 observer_environment{};
  ActivityPlanningStableKeyV1 prepared_activity_key{};
  ActivityPlanningSnapshotRequestV1 prepared_request{};
  ActivityPlanningSnapshotPrivateV1 result{};
  std::atomic<std::uint32_t> failure{static_cast<std::uint32_t>(
      ActivityPlanningApplicationGlueFailureV1::none)};
  std::atomic<bool> execution_active{false};
  bool installed = false;
  bool request_prepared = false;
  bool result_ready = false;
  bool result_available = false;
};

bool ConfigureActivityPlanningApplicationGlueV1(
    ActivityPlanningApplicationGlueStateV1 &state,
    const ActivityPlanningApplicationGlueEnvironmentV1 &environment) noexcept;

// Prepares exactly one pointer-free activity_feast request. It performs no
// native operation and is safe to call from the bridge worker.
bool PrepareActivityPlanningApplicationGlueV1(
    ActivityPlanningApplicationGlueStateV1 &state,
    const ActivityPlanningSnapshotRequestV1 &request) noexcept;

// The caller must enter through a private fixed application-main executor.
// Returning true means the request reached a typed terminal result; inspect
// result.status/result_available to distinguish available from unavailable.
bool ExecuteActivityPlanningApplicationGlueV1(
    ActivityPlanningApplicationGlueStateV1 &state) noexcept;

bool ReadActivityPlanningApplicationGlueResultV1(
    const ActivityPlanningApplicationGlueStateV1 &state,
    ActivityPlanningSnapshotPrivateV1 &output, bool &result_available) noexcept;

ActivityPlanningApplicationGlueDiagnosticsV1
ReadActivityPlanningApplicationGlueDiagnosticsV1(
    const ActivityPlanningApplicationGlueStateV1 &state) noexcept;

std::string_view ActivityPlanningApplicationGlueFailureKeyV1(
    ActivityPlanningApplicationGlueFailureV1 failure) noexcept;

} // namespace xar::bridge
