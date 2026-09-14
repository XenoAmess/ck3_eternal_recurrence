#pragma once

#include "domain_construction_semantic_action_core_v1.hpp"

#include <cstdint>
#include <string>

namespace xar::ck3::research {

inline constexpr std::uint32_t kDomainConstructionBuildingValidatorRvaV1 =
    0x26CD410U;
inline constexpr std::uint32_t kDomainConstructionHoldingValidatorRvaV1 =
    0x275C7F0U;
inline constexpr std::uint32_t kDomainConstructionReceiverRvaV1 =
    0x341D990U;
inline constexpr std::uint32_t kDomainConstructionReceiverFlagsV1 = 7U;

enum class DomainConstructionNativeSubmitPhaseV1 : std::uint8_t {
  idle = 0,
  pending_receipt,
  rejected,
  failed,
  applied,
};

enum class DomainConstructionNativeSubmitFailureV1 : std::uint8_t {
  none = 0,
  not_idle,
  candidate_identity,
  binding,
  exact_build,
  application_main_thread,
  native_context,
  executor_missing,
  execution_trace,
  validator_rejected,
  materialize_failed,
  receiver_rejected,
};

enum class DomainConstructionNativeExecutorKindV1 : std::uint8_t {
  offline_fixture = 0,
  exact_build_application_main,
};

enum class DomainConstructionNativeReceiptSourceV1 : std::uint8_t {
  target_building_state = 1,
  target_holding_state,
  exact_resource_deduction,
};

struct DomainConstructionNativeCommandContextV1 final {
  DomainConstructionCandidateKindV1 candidate_kind =
      DomainConstructionCandidateKindV1::building_in_holding;
  std::string candidate_id;
  DomainConstructionCandidateSnapshotBindingV1 binding;
  std::int32_t actor_or_holder_id = -1;
  std::int32_t holding_province_id = -1;
  std::int32_t candidate_selector = -1;
  std::int32_t building_type_id = -1;
  std::int32_t candidate_province_id = -1;
  std::uint32_t validator_rva = 0U;
  std::uint32_t receiver_rva = kDomainConstructionReceiverRvaV1;
  std::uint32_t receiver_flags = kDomainConstructionReceiverFlagsV1;
};

// Borrowed native values are valid only for the synchronous application-main
// call. They are never copied into the pointer-free state or receipt.
struct DomainConstructionTransientNativeSubmitContextV1 final {
  DomainConstructionCandidateSnapshotBindingV1 observed_binding;
  std::int32_t actor_or_holder_id = -1;
  std::uintptr_t new_holding_candidate_object = 0U;
  bool exact_build_identity_matches = false;
  bool application_main_thread = false;
};

struct DomainConstructionNativeExecutionTraceV1 final {
  DomainConstructionNativeExecutorKindV1 executor_kind =
      DomainConstructionNativeExecutorKindV1::offline_fixture;
  bool exact_contract_addresses_used = false;
  std::uint32_t validator_call_count = 0U;
  bool validator_allowed = false;
  std::uint32_t materialize_call_count = 0U;
  bool command_materialized = false;
  std::uint32_t receiver_call_count = 0U;
  bool receiver_accepted = false;
  std::uint64_t receiver_command_sequence = 0U;
  bool transfer_holder_zeroed = false;
  bool leftover_wrapper_lifecycle_complete = false;
  bool raw_pointer_persisted = false;
};

using DomainConstructionExactNativeExecutorV1 = bool (*)(
    void* executor_context,
    const DomainConstructionNativeCommandContextV1& command,
    const DomainConstructionTransientNativeSubmitContextV1& transient,
    DomainConstructionNativeExecutionTraceV1& trace);

struct DomainConstructionNativeSubmitStateV1 final {
  DomainConstructionNativeSubmitPhaseV1 phase =
      DomainConstructionNativeSubmitPhaseV1::idle;
  DomainConstructionNativeSubmitFailureV1 failure =
      DomainConstructionNativeSubmitFailureV1::none;
  std::uint64_t executor_call_count = 0U;
  bool pending_ack = false;
  bool production_native_path = false;
  bool applied_receipt_source_observed = false;
  DomainConstructionNativeReceiptSourceV1 applied_receipt_source =
      DomainConstructionNativeReceiptSourceV1::target_building_state;
  DomainConstructionNativeCommandContextV1 command;
  DomainConstructionNativeExecutionTraceV1 trace;
  DomainConstructionSemanticActionStateV1 semantic_action;
};

[[nodiscard]] bool BuildDomainConstructionNativeCommandContextV1(
    const DomainConstructionSemanticActionRequestV1& request,
    const DomainConstructionTransientNativeSubmitContextV1& transient,
    DomainConstructionNativeCommandContextV1& command,
    DomainConstructionNativeSubmitFailureV1& failure);

[[nodiscard]] bool BeginDomainConstructionNativeSubmitV1(
    DomainConstructionNativeSubmitStateV1& state,
    const DomainConstructionSemanticActionRequestV1& request,
    const DomainConstructionTransientNativeSubmitContextV1& transient,
    DomainConstructionNativeExecutorKindV1 executor_kind,
    DomainConstructionExactNativeExecutorV1 executor, void* executor_context);

[[nodiscard]] bool ObserveDomainConstructionNativeReceiptV1(
    DomainConstructionNativeSubmitStateV1& state,
    DomainConstructionNativeReceiptSourceV1 source,
    const DomainConstructionFreshReceiptV1& receipt);

}  // namespace xar::ck3::research
