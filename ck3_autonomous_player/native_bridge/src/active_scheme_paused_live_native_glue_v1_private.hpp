#pragma once

#include "xar_bridge/active_scheme_interaction_definition_resolver_v1_private.hpp"
#include "xar_bridge/active_scheme_state_v1_private_source_adapter.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view
    kActiveSchemePausedLiveNativeGlueV1PrivateStage =
        "scheme9_native_glue_candidate_callbacks_pending";

enum class ActiveSchemePausedLiveNativeGlueV1PrivateFailure : std::uint8_t {
  none,
  binding_contract,
  exact_build_mismatch,
  source_access_unavailable,
  precondition_access_unavailable,
  definition_binding_rejected,
  command_binding_rejected,
  not_bound,
  reentrant_execution,
  not_application_main_thread,
  observation_red,
  definition_red,
  precondition_red,
  action_red,
  receipt_red,
};

struct ActiveSchemePausedLiveNativeGlueV1PrivateExecution {
  std::uint32_t current_thread_id = 0;
  std::uint32_t application_main_thread_id = 0;
};

struct ActiveSchemePausedLiveNativeGlueV1PrivateEnvironment {
  bool binding_enabled = false;
  ActiveSchemeStateV1PrivateSourceAccess source_access{};
  void *precondition_context = nullptr;
  CaptureActiveSchemeSemanticActionPreconditionV1Private
      capture_precondition = nullptr;
  ActiveSchemeSemanticActionV1PrivateNativeCommandEnvironment
      command_binding{};
  ActiveSchemeInteractionDefinitionResolverV1PrivateEnvironment
      definition_binding{};
};

struct ActiveSchemePausedLiveNativeGlueV1PrivateReadiness {
  bool exact_build_bound = false;
  bool paused_observation_bound = false;
  bool stable_definition_bound = false;
  bool native_precondition_bound = false;
  bool native_single_submit_bound = false;
  bool candidate_core_ready = false;
  ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure =
      ActiveSchemePausedLiveNativeGlueV1PrivateFailure::not_bound;
};

// This object retains only callback metadata and the private adapter states.
// Native root/container/definition/character/context/command pointers remain
// call-local leases in SCHEME3/4/6/7 and are never cached here.
struct ActiveSchemePausedLiveNativeGlueV1PrivateState {
  bool attached = false;
  bool execution_active = false;
  std::uint32_t active_current_thread_id = 0;
  std::uint32_t active_application_main_thread_id = 0;
  ActiveSchemeStateV1PrivateSourceAccess source_access{};
  void *precondition_context = nullptr;
  CaptureActiveSchemeSemanticActionPreconditionV1Private
      capture_precondition = nullptr;
  ActiveSchemeInteractionDefinitionResolverV1PrivateState
      definition_state{};
  ActiveSchemeSemanticActionV1PrivateNativeCommandState command_state{};
  ActiveSchemeSemanticActionV1PrivateAccess action_access{};
  ActiveSchemeSemanticActionV1PrivateEnvironment action_environment{};
  ActiveSchemePausedLiveNativeGlueV1PrivateReadiness readiness{};
  ActiveSchemeStateV1PrivateSourceFailure last_source_failure =
      ActiveSchemeStateV1PrivateSourceFailure::callbacks_unavailable;
  ActiveSchemeSemanticActionV1PrivateFailure last_action_failure =
      ActiveSchemeSemanticActionV1PrivateFailure::action_route_unavailable;
};

bool BindActiveSchemePausedLiveNativeGlueV1Private(
    const ActiveSchemePausedLiveNativeGlueV1PrivateEnvironment &environment,
    ActiveSchemePausedLiveNativeGlueV1PrivateState &state,
    ActiveSchemePausedLiveNativeGlueV1PrivateReadiness &readiness) noexcept;

bool CaptureActiveSchemePausedLiveSnapshotV1Private(
    ActiveSchemePausedLiveNativeGlueV1PrivateState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    ActiveSchemeStateV1PrivateObservation &output,
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure &failure) noexcept;

bool ResolveActiveSchemePausedLiveDefinitionV1Private(
    ActiveSchemePausedLiveNativeGlueV1PrivateState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    std::string_view interaction_key,
    ActiveSchemeSemanticActionV1PrivateNativeInteractionLease &output,
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure &failure) noexcept;

bool CaptureActiveSchemePausedLivePreconditionV1Private(
    ActiveSchemePausedLiveNativeGlueV1PrivateState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    ActiveSchemeSemanticActionV1PrivatePrecondition &output,
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure &failure) noexcept;

ActiveSchemeSemanticActionV1PrivateAckStatus
ExecuteActiveSchemePausedLiveNativeGlueV1Private(
    ActiveSchemePausedLiveNativeGlueV1PrivateState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    const ActiveSchemeSemanticActionV1PrivateRequest &request,
    ActiveSchemeSemanticActionV1PrivateAck &ack,
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure &failure) noexcept;

ActiveSchemeSemanticActionV1PrivateReceiptStatus
VerifyActiveSchemePausedLiveNativeGlueReceiptV1Private(
    ActiveSchemePausedLiveNativeGlueV1PrivateState &state,
    const ActiveSchemePausedLiveNativeGlueV1PrivateExecution &execution,
    const ActiveSchemeSemanticActionV1PrivateAck &ack,
    ActiveSchemeSemanticActionV1PrivateReceipt &receipt,
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure &failure) noexcept;

std::string_view ActiveSchemePausedLiveNativeGlueV1PrivateFailureName(
    ActiveSchemePausedLiveNativeGlueV1PrivateFailure failure) noexcept;

} // namespace xar::bridge
