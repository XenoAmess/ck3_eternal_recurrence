#include "xar_bridge/activity_planning_snapshot_v1_application_glue.hpp"

#include <algorithm>
#include <cstring>

namespace xar::bridge {
namespace {

void SetFailure(ActivityPlanningApplicationGlueStateV1 &state,
                ActivityPlanningApplicationGlueFailureV1 failure) noexcept {
  state.failure.store(static_cast<std::uint32_t>(failure),
                      std::memory_order_release);
}

bool SameRequest(const ActivityPlanningSnapshotRequestV1 &left,
                 const ActivityPlanningSnapshotRequestV1 &right) noexcept {
  return left.expected_snapshot_revision == right.expected_snapshot_revision &&
         left.expected_date_raw == right.expected_date_raw &&
         left.expected_owner_character_id ==
             right.expected_owner_character_id &&
         left.activity_key == right.activity_key;
}

bool FrameMatches(const ActivityPlanningFrameIdentityV1 &frame,
                  const ActivityPlanningSnapshotRequestV1 &request) noexcept {
  return frame.snapshot_revision == request.expected_snapshot_revision &&
         frame.date_raw == request.expected_date_raw &&
         frame.owner_character_id == request.expected_owner_character_id &&
         frame.map_ready && frame.owner_alive;
}

bool ScopeAdmits(const ActivityPlanningApplicationGlueStateV1 &state,
                 const ActivityPlanningSnapshotRequestV1 &request) noexcept {
  return state.installed && state.request_prepared &&
         state.execution_active.load(std::memory_order_acquire) &&
         SameRequest(request, state.prepared_request);
}

bool ScopedReadFrame(void *context,
                     ActivityPlanningFrameIdentityV1 &output) noexcept {
  auto *state = static_cast<ActivityPlanningApplicationGlueStateV1 *>(context);
  if (state == nullptr || !state->installed || !state->request_prepared ||
      !state->execution_active.load(std::memory_order_acquire) ||
      state->environment.native_environment.read_frame == nullptr) {
    if (state != nullptr) {
      SetFailure(
          *state,
          ActivityPlanningApplicationGlueFailureV1::operation_outside_scope);
    }
    return false;
  }
  return state->environment.native_environment.read_frame(
      state->environment.native_environment.context, output);
}

bool ScopedReadMemory(void *context, std::uintptr_t address, void *output,
                      std::size_t size) noexcept {
  auto *state = static_cast<ActivityPlanningApplicationGlueStateV1 *>(context);
  if (state == nullptr ||
      state->environment.native_environment.read_memory == nullptr) {
    return false;
  }
  return state->environment.native_environment.read_memory(
      state->environment.native_environment.context, address, output, size);
}

bool ScopedInvokeFinalCanPlan(
    void *context, std::uintptr_t module_base, std::uintptr_t exact_entry_point,
    std::uintptr_t host_view, std::uintptr_t activity_type,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningNativeCanPlanResultV1 &output) noexcept {
  auto *state = static_cast<ActivityPlanningApplicationGlueStateV1 *>(context);
  output = {};
  if (state == nullptr || !ScopeAdmits(*state, request) || host_view == 0 ||
      activity_type == 0 ||
      state->environment.native_environment.invoke_final_can_plan == nullptr) {
    if (state != nullptr) {
      SetFailure(
          *state,
          ActivityPlanningApplicationGlueFailureV1::operation_outside_scope);
    }
    return false;
  }
  const auto &upstream = state->environment.native_environment;
  if (module_base != upstream.module_base ||
      exact_entry_point !=
          upstream.module_base + kActivityPlanningHostViewCanPlanRvaV1) {
    SetFailure(*state,
               ActivityPlanningApplicationGlueFailureV1::frame_mismatch);
    return false;
  }
  return upstream.invoke_final_can_plan(upstream.context, module_base,
                                        exact_entry_point, host_view,
                                        activity_type, request, output);
}

bool ScopedReadSemantics(
    void *context, std::uintptr_t module_base, std::uintptr_t host_view,
    std::uintptr_t activity_type,
    const ActivityPlanningSnapshotRequestV1 &request,
    ActivityPlanningNativeSemanticSampleV1 &output) noexcept {
  auto *state = static_cast<ActivityPlanningApplicationGlueStateV1 *>(context);
  output = {};
  if (state == nullptr || !ScopeAdmits(*state, request) || host_view == 0 ||
      activity_type == 0 ||
      state->environment.native_environment.read_semantics == nullptr) {
    if (state != nullptr) {
      SetFailure(
          *state,
          ActivityPlanningApplicationGlueFailureV1::operation_outside_scope);
    }
    return false;
  }
  const auto &upstream = state->environment.native_environment;
  if (module_base != upstream.module_base) {
    SetFailure(*state,
               ActivityPlanningApplicationGlueFailureV1::frame_mismatch);
    return false;
  }
  return upstream.read_semantics(upstream.context, module_base, host_view,
                                 activity_type, request, output);
}

bool ValidEnvironment(
    const ActivityPlanningApplicationGlueEnvironmentV1 &environment,
    ActivityPlanningApplicationGlueFailureV1 &failure) noexcept {
  const auto &native = environment.native_environment;
  if (!environment.glue_enabled) {
    failure = ActivityPlanningApplicationGlueFailureV1::glue_disabled;
    return false;
  }
  if (!native.exact_build_admitted || native.module_base == 0 ||
      native.admitted_executable_sha256 !=
          kActivityPlanningSnapshotExecutableSha256V1) {
    failure =
        ActivityPlanningApplicationGlueFailureV1::exact_build_not_admitted;
    return false;
  }
  if (native.context == nullptr || native.read_frame == nullptr ||
      native.read_memory == nullptr || native.rtti_dynamic_cast == nullptr ||
      native.invoke_final_can_plan == nullptr ||
      native.read_semantics == nullptr) {
    failure = ActivityPlanningApplicationGlueFailureV1::callbacks_missing;
    return false;
  }
  failure = ActivityPlanningApplicationGlueFailureV1::none;
  return true;
}

bool CopyActivityKey(std::string_view source,
                     ActivityPlanningStableKeyV1 &destination) noexcept {
  destination = {};
  if (source != kActivityPlanningSnapshotP0ActivityKeyV1 ||
      source.size() >= destination.bytes.size()) {
    return false;
  }
  std::memcpy(destination.bytes.data(), source.data(), source.size());
  destination.size = static_cast<std::uint16_t>(source.size());
  return true;
}

} // namespace

bool ConfigureActivityPlanningApplicationGlueV1(
    ActivityPlanningApplicationGlueStateV1 &state,
    const ActivityPlanningApplicationGlueEnvironmentV1 &environment) noexcept {
  if (state.installed ||
      state.execution_active.load(std::memory_order_acquire)) {
    SetFailure(state,
               ActivityPlanningApplicationGlueFailureV1::already_configured);
    return false;
  }
  ActivityPlanningApplicationGlueFailureV1 failure{};
  if (!ValidEnvironment(environment, failure)) {
    SetFailure(state, failure);
    return false;
  }

  state.environment = environment;
  state.prepared_activity_key = {};
  state.prepared_request = {};
  state.result = {};
  state.request_prepared = false;
  state.result_ready = false;
  state.result_available = false;

  auto scoped_native = environment.native_environment;
  scoped_native.context = &state;
  scoped_native.read_frame = &ScopedReadFrame;
  scoped_native.read_memory = &ScopedReadMemory;
  scoped_native.invoke_final_can_plan = &ScopedInvokeFinalCanPlan;
  scoped_native.read_semantics = &ScopedReadSemantics;
  ActivityPlanningSourceAdapterEnvironmentV1 source_environment{};
  if (!ConfigureActivityPlanningNativeBinderV1(state.binder, scoped_native,
                                               source_environment)) {
    SetFailure(state,
               ActivityPlanningApplicationGlueFailureV1::binder_rejected);
    return false;
  }
  if (!ConfigureActivityPlanningSourceAdapterV1(state.source_adapter,
                                                source_environment,
                                                state.observer_environment)) {
    SetFailure(
        state,
        ActivityPlanningApplicationGlueFailureV1::source_adapter_rejected);
    return false;
  }
  state.installed = true;
  SetFailure(state, ActivityPlanningApplicationGlueFailureV1::none);
  return true;
}

bool PrepareActivityPlanningApplicationGlueV1(
    ActivityPlanningApplicationGlueStateV1 &state,
    const ActivityPlanningSnapshotRequestV1 &request) noexcept {
  if (!state.installed || request.expected_snapshot_revision == 0 ||
      request.expected_owner_character_id <= 0) {
    SetFailure(state,
               ActivityPlanningApplicationGlueFailureV1::request_invalid);
    return false;
  }
  if (state.request_prepared || state.result_ready) {
    SetFailure(
        state,
        ActivityPlanningApplicationGlueFailureV1::request_already_prepared);
    return false;
  }
  if (!CopyActivityKey(request.activity_key, state.prepared_activity_key)) {
    SetFailure(state,
               ActivityPlanningApplicationGlueFailureV1::request_invalid);
    return false;
  }
  state.prepared_request = request;
  state.prepared_request.activity_key =
      ActivityPlanningFixedTextViewV1(state.prepared_activity_key);
  state.request_prepared = true;
  SetFailure(state, ActivityPlanningApplicationGlueFailureV1::none);
  return true;
}

bool ExecuteActivityPlanningApplicationGlueV1(
    ActivityPlanningApplicationGlueStateV1 &state) noexcept {
  if (!state.installed || !state.request_prepared || state.result_ready) {
    SetFailure(
        state,
        ActivityPlanningApplicationGlueFailureV1::execution_not_prepared);
    return false;
  }
  bool expected = false;
  if (!state.execution_active.compare_exchange_strong(
          expected, true, std::memory_order_acq_rel,
          std::memory_order_acquire)) {
    SetFailure(state, ActivityPlanningApplicationGlueFailureV1::execution_busy);
    return false;
  }

  const auto finish =
      [&state](ActivityPlanningApplicationGlueFailureV1 failure) {
        SetFailure(state, failure);
        state.execution_active.store(false, std::memory_order_release);
      };
  ActivityPlanningFrameIdentityV1 frame{};
  const auto &upstream = state.environment.native_environment;
  if (!upstream.read_frame(upstream.context, frame)) {
    finish(ActivityPlanningApplicationGlueFailureV1::frame_unavailable);
    return false;
  }
  if (!frame.application_main_thread) {
    finish(ActivityPlanningApplicationGlueFailureV1::requires_application_main);
    return false;
  }
  if (!frame.paused) {
    finish(ActivityPlanningApplicationGlueFailureV1::requires_paused);
    return false;
  }
  if (!FrameMatches(frame, state.prepared_request)) {
    finish(ActivityPlanningApplicationGlueFailureV1::frame_mismatch);
    return false;
  }

  ActivityPlanningSnapshotPrivateV1 result{};
  const bool available = ReadActivityPlanningSnapshotPrivateObserverV1(
      state.observer_environment, state.prepared_request, result);
  state.result = result;
  state.result_ready = true;
  state.result_available = available;
  const auto scoped_failure =
      static_cast<ActivityPlanningApplicationGlueFailureV1>(
          state.failure.load(std::memory_order_acquire));
  finish(available ? ActivityPlanningApplicationGlueFailureV1::none
         : scoped_failure != ActivityPlanningApplicationGlueFailureV1::none
             ? scoped_failure
             : ActivityPlanningApplicationGlueFailureV1::observer_unavailable);
  return true;
}

bool ReadActivityPlanningApplicationGlueResultV1(
    const ActivityPlanningApplicationGlueStateV1 &state,
    ActivityPlanningSnapshotPrivateV1 &output,
    bool &result_available) noexcept {
  output = {};
  result_available = false;
  if (!state.result_ready ||
      state.execution_active.load(std::memory_order_acquire))
    return false;
  output = state.result;
  result_available = state.result_available;
  return true;
}

ActivityPlanningApplicationGlueDiagnosticsV1
ReadActivityPlanningApplicationGlueDiagnosticsV1(
    const ActivityPlanningApplicationGlueStateV1 &state) noexcept {
  return {
      state.installed,
      state.request_prepared,
      state.execution_active.load(std::memory_order_acquire),
      state.result_ready,
      state.result_available,
      static_cast<ActivityPlanningApplicationGlueFailureV1>(
          state.failure.load(std::memory_order_acquire)),
      ReadActivityPlanningNativeBinderFailureV1(state.binder),
      ReadActivityPlanningSourceAdapterFailureV1(state.source_adapter),
  };
}

std::string_view ActivityPlanningApplicationGlueFailureKeyV1(
    ActivityPlanningApplicationGlueFailureV1 failure) noexcept {
  switch (failure) {
  case ActivityPlanningApplicationGlueFailureV1::none:
    return "none";
  case ActivityPlanningApplicationGlueFailureV1::glue_disabled:
    return "glue_disabled";
  case ActivityPlanningApplicationGlueFailureV1::already_configured:
    return "already_configured";
  case ActivityPlanningApplicationGlueFailureV1::exact_build_not_admitted:
    return "exact_build_not_admitted";
  case ActivityPlanningApplicationGlueFailureV1::callbacks_missing:
    return "callbacks_missing";
  case ActivityPlanningApplicationGlueFailureV1::binder_rejected:
    return "binder_rejected";
  case ActivityPlanningApplicationGlueFailureV1::source_adapter_rejected:
    return "source_adapter_rejected";
  case ActivityPlanningApplicationGlueFailureV1::request_invalid:
    return "request_invalid";
  case ActivityPlanningApplicationGlueFailureV1::request_already_prepared:
    return "request_already_prepared";
  case ActivityPlanningApplicationGlueFailureV1::execution_not_prepared:
    return "execution_not_prepared";
  case ActivityPlanningApplicationGlueFailureV1::execution_busy:
    return "execution_busy";
  case ActivityPlanningApplicationGlueFailureV1::frame_unavailable:
    return "frame_unavailable";
  case ActivityPlanningApplicationGlueFailureV1::requires_application_main:
    return "requires_application_main";
  case ActivityPlanningApplicationGlueFailureV1::requires_paused:
    return "requires_paused";
  case ActivityPlanningApplicationGlueFailureV1::frame_mismatch:
    return "frame_mismatch";
  case ActivityPlanningApplicationGlueFailureV1::operation_outside_scope:
    return "operation_outside_scope";
  case ActivityPlanningApplicationGlueFailureV1::observer_unavailable:
    return "observer_unavailable";
  }
  return "unknown";
}

} // namespace xar::bridge
