#include "domain_construction_native_submit_adapter_v1.hpp"

#include <charconv>
#include <string_view>

namespace xar::ck3::research {
namespace {

bool ParseNonnegativeInt32(const std::string_view text, std::int32_t& value) {
  if (text.empty()) return false;
  const auto* begin = text.data();
  const auto* end = begin + text.size();
  const auto result = std::from_chars(begin, end, value);
  return result.ec == std::errc{} && result.ptr == end && value >= 0;
}

bool TakeField(std::string_view& remaining, std::string_view& field) {
  const auto separator = remaining.find(':');
  if (separator == std::string_view::npos) {
    field = remaining;
    remaining = {};
    return !field.empty();
  }
  field = remaining.substr(0, separator);
  remaining.remove_prefix(separator + 1U);
  return !field.empty();
}

bool ParseBuildingIdentity(const std::string& candidate_id,
                           DomainConstructionNativeCommandContextV1& command) {
  constexpr std::string_view prefix = "building:";
  if (!std::string_view(candidate_id).starts_with(prefix)) return false;
  std::string_view remaining(candidate_id);
  remaining.remove_prefix(prefix.size());
  std::string_view holding;
  std::string_view selector;
  std::string_view building;
  return TakeField(remaining, holding) && TakeField(remaining, selector) &&
         TakeField(remaining, building) && remaining.empty() &&
         ParseNonnegativeInt32(holding, command.holding_province_id) &&
         ParseNonnegativeInt32(selector, command.candidate_selector) &&
         ParseNonnegativeInt32(building, command.building_type_id);
}

bool ParseHoldingIdentity(const std::string& candidate_id,
                          DomainConstructionNativeCommandContextV1& command) {
  constexpr std::string_view prefix = "holding:";
  if (!std::string_view(candidate_id).starts_with(prefix)) return false;
  std::string_view remaining(candidate_id);
  remaining.remove_prefix(prefix.size());
  std::string_view province;
  std::string_view selector;
  return TakeField(remaining, province) && TakeField(remaining, selector) &&
         remaining.empty() &&
         ParseNonnegativeInt32(province, command.candidate_province_id) &&
         ParseNonnegativeInt32(selector, command.candidate_selector);
}

bool BindingIsUsable(
    const DomainConstructionCandidateSnapshotBindingV1& binding) {
  return binding.generation != 0U && (binding.generation & 1U) == 0U &&
         binding.proof_epoch != 0U;
}

}  // namespace

bool BuildDomainConstructionNativeCommandContextV1(
    const DomainConstructionSemanticActionRequestV1& request,
    const DomainConstructionTransientNativeSubmitContextV1& transient,
    DomainConstructionNativeCommandContextV1& command,
    DomainConstructionNativeSubmitFailureV1& failure) {
  command = {};
  failure = DomainConstructionNativeSubmitFailureV1::none;
  if (!BindingIsUsable(request.binding) ||
      request.binding.generation != transient.observed_binding.generation ||
      request.binding.proof_epoch != transient.observed_binding.proof_epoch ||
      request.binding.date_raw != transient.observed_binding.date_raw) {
    failure = DomainConstructionNativeSubmitFailureV1::binding;
    return false;
  }
  if (transient.actor_or_holder_id < 0) {
    failure = DomainConstructionNativeSubmitFailureV1::native_context;
    return false;
  }

  command.candidate_kind = request.candidate_kind;
  command.candidate_id = request.candidate_id;
  command.binding = request.binding;
  command.actor_or_holder_id = transient.actor_or_holder_id;
  if (request.candidate_kind ==
      DomainConstructionCandidateKindV1::building_in_holding) {
    command.validator_rva = kDomainConstructionBuildingValidatorRvaV1;
    if (!ParseBuildingIdentity(request.candidate_id, command)) {
      failure = DomainConstructionNativeSubmitFailureV1::candidate_identity;
      return false;
    }
  } else if (request.candidate_kind ==
             DomainConstructionCandidateKindV1::new_holding) {
    command.validator_rva = kDomainConstructionHoldingValidatorRvaV1;
    if (!ParseHoldingIdentity(request.candidate_id, command)) {
      failure = DomainConstructionNativeSubmitFailureV1::candidate_identity;
      return false;
    }
    if (transient.new_holding_candidate_object == 0U) {
      failure = DomainConstructionNativeSubmitFailureV1::native_context;
      return false;
    }
  } else {
    failure = DomainConstructionNativeSubmitFailureV1::candidate_identity;
    return false;
  }
  return true;
}

bool BeginDomainConstructionNativeSubmitV1(
    DomainConstructionNativeSubmitStateV1& state,
    const DomainConstructionSemanticActionRequestV1& request,
    const DomainConstructionTransientNativeSubmitContextV1& transient,
    const DomainConstructionNativeExecutorKindV1 executor_kind,
    const DomainConstructionExactNativeExecutorV1 executor,
    void* executor_context) {
  if (state.phase != DomainConstructionNativeSubmitPhaseV1::idle) {
    state.failure = DomainConstructionNativeSubmitFailureV1::not_idle;
    return false;
  }
  if (!BuildDomainConstructionNativeCommandContextV1(
          request, transient, state.command, state.failure)) {
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }
  if (!transient.exact_build_identity_matches) {
    state.failure = DomainConstructionNativeSubmitFailureV1::exact_build;
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }
  if (!transient.application_main_thread) {
    state.failure =
        DomainConstructionNativeSubmitFailureV1::application_main_thread;
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }
  if (executor == nullptr) {
    state.failure = DomainConstructionNativeSubmitFailureV1::executor_missing;
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }

  ++state.executor_call_count;
  if (!executor(executor_context, state.command, transient, state.trace)) {
    state.failure = DomainConstructionNativeSubmitFailureV1::execution_trace;
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }
  if (state.trace.validator_call_count != 1U ||
      !state.trace.validator_allowed) {
    state.failure =
        DomainConstructionNativeSubmitFailureV1::validator_rejected;
    state.phase = DomainConstructionNativeSubmitPhaseV1::rejected;
    return false;
  }
  if (state.trace.materialize_call_count != 1U ||
      !state.trace.command_materialized) {
    state.failure =
        DomainConstructionNativeSubmitFailureV1::materialize_failed;
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }
  if (state.trace.executor_kind != executor_kind ||
      state.trace.receiver_call_count != 1U ||
      state.trace.raw_pointer_persisted ||
      !state.trace.transfer_holder_zeroed ||
      !state.trace.leftover_wrapper_lifecycle_complete) {
    state.failure = DomainConstructionNativeSubmitFailureV1::execution_trace;
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }
  if (!state.trace.receiver_accepted) {
    state.failure = DomainConstructionNativeSubmitFailureV1::receiver_rejected;
    state.phase = DomainConstructionNativeSubmitPhaseV1::rejected;
    return false;
  }
  if (state.trace.receiver_command_sequence == 0U) {
    state.failure = DomainConstructionNativeSubmitFailureV1::execution_trace;
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }
  if (executor_kind ==
          DomainConstructionNativeExecutorKindV1::exact_build_application_main &&
      !state.trace.exact_contract_addresses_used) {
    state.failure = DomainConstructionNativeSubmitFailureV1::execution_trace;
    state.phase = DomainConstructionNativeSubmitPhaseV1::failed;
    return false;
  }

  state.failure = DomainConstructionNativeSubmitFailureV1::none;
  state.pending_ack = true;
  // DEV19 has no shared executor wiring. A function-pointer fixture cannot
  // elevate static evidence into a production claim.
  state.production_native_path = false;
  state.phase = DomainConstructionNativeSubmitPhaseV1::pending_receipt;
  state.semantic_action.phase = DomainConstructionActionPhaseV1::pending_receipt;
  state.semantic_action.submit_call_count = 1U;
  state.semantic_action.ack_received = true;
  state.semantic_action.ack_token = state.trace.receiver_command_sequence;
  state.semantic_action.request = request;
  return true;
}

bool ObserveDomainConstructionNativeReceiptV1(
    DomainConstructionNativeSubmitStateV1& state,
    const DomainConstructionNativeReceiptSourceV1 source,
    const DomainConstructionFreshReceiptV1& receipt) {
  if (state.phase != DomainConstructionNativeSubmitPhaseV1::pending_receipt) {
    return false;
  }
  const bool source_present =
      (source ==
           DomainConstructionNativeReceiptSourceV1::target_building_state &&
       receipt.target_building_state_observed &&
       state.command.candidate_kind ==
           DomainConstructionCandidateKindV1::building_in_holding) ||
      (source ==
           DomainConstructionNativeReceiptSourceV1::target_holding_state &&
       receipt.target_holding_state_observed &&
       state.command.candidate_kind ==
           DomainConstructionCandidateKindV1::new_holding) ||
      (source ==
           DomainConstructionNativeReceiptSourceV1::exact_resource_deduction &&
       receipt.resource_balances_observed);
  if (!source_present ||
      !ObserveDomainConstructionFreshReceiptV1(state.semantic_action,
                                                receipt)) {
    return false;
  }
  state.pending_ack = false;
  state.applied_receipt_source_observed = true;
  state.applied_receipt_source = source;
  state.phase = DomainConstructionNativeSubmitPhaseV1::applied;
  return true;
}

}  // namespace xar::ck3::research
