#include "domain_construction_cost_legality_collector_source_adapter_v1.hpp"

#include <array>
#include <limits>

namespace xar::ck3::research {
namespace {

bool CanReadCandidateRow(const std::uintptr_t address) {
  return address != 0U &&
         address <= std::numeric_limits<std::uintptr_t>::max() -
                        (kDomainConstructionCandidateRowBytesV1 - 1U);
}

DomainConstructionNativeFinalLegalityBranchV1 ExpectedFinalBranch(
    const DomainConstructionCandidateKindV1 kind) {
  return kind == DomainConstructionCandidateKindV1::building_in_holding
             ? DomainConstructionNativeFinalLegalityBranchV1::building
             : DomainConstructionNativeFinalLegalityBranchV1::new_holding;
}

DomainConstructionCollectorSourceFailureV1 MapCostFailure(
    const DomainConstructionCandidateCostLegalityUnavailableV1 failure) {
  switch (failure) {
    case DomainConstructionCandidateCostLegalityUnavailableV1::none:
      return DomainConstructionCollectorSourceFailureV1::none;
    case DomainConstructionCandidateCostLegalityUnavailableV1::candidate_identity:
      return DomainConstructionCollectorSourceFailureV1::candidate_identity;
    case DomainConstructionCandidateCostLegalityUnavailableV1::generation:
      return DomainConstructionCollectorSourceFailureV1::generation;
    case DomainConstructionCandidateCostLegalityUnavailableV1::proof_epoch:
      return DomainConstructionCollectorSourceFailureV1::proof_epoch;
    case DomainConstructionCandidateCostLegalityUnavailableV1::binding_drift:
      return DomainConstructionCollectorSourceFailureV1::cost_legality;
    case DomainConstructionCandidateCostLegalityUnavailableV1::null_pointer:
    case DomainConstructionCandidateCostLegalityUnavailableV1::address_overflow:
    case DomainConstructionCandidateCostLegalityUnavailableV1::memory_read:
      return DomainConstructionCollectorSourceFailureV1::memory_read;
    case DomainConstructionCandidateCostLegalityUnavailableV1::
        final_legality_unobserved:
      return DomainConstructionCollectorSourceFailureV1::final_observation;
    case DomainConstructionCandidateCostLegalityUnavailableV1::
        candidate_kind_branch_mismatch:
      return DomainConstructionCollectorSourceFailureV1::final_branch;
  }
  return DomainConstructionCollectorSourceFailureV1::cost_legality;
}

}  // namespace

DomainConstructionOwnedCollectorSampleV1
AdaptDomainConstructionExactCollectorMemoryV1(
    const DomainConstructionExactCollectorMemorySampleV1& source,
    const DomainConstructionReadMemoryV1 read_memory, void* read_context) {
  DomainConstructionOwnedCollectorSampleV1 output{};
  output.final_legality = source.final_legality;
  const auto& admission = source.admission;
  if (!admission.exact_build_admitted) {
    output.failure = DomainConstructionCollectorSourceFailureV1::exact_build;
    return output;
  }
  if (admission.application_main_thread_id == 0U ||
      admission.current_thread_id != admission.application_main_thread_id) {
    output.failure =
        DomainConstructionCollectorSourceFailureV1::application_main;
    return output;
  }
  if (!admission.session_live) {
    output.failure = DomainConstructionCollectorSourceFailureV1::session;
    return output;
  }
  if (admission.expected_binding.generation == 0U ||
      admission.observed_binding.generation == 0U ||
      (admission.expected_binding.generation & 1U) != 0U ||
      (admission.observed_binding.generation & 1U) != 0U ||
      admission.expected_binding.generation !=
          admission.observed_binding.generation) {
    output.failure = DomainConstructionCollectorSourceFailureV1::generation;
    return output;
  }
  if (admission.expected_binding.proof_epoch == 0U ||
      admission.observed_binding.proof_epoch == 0U ||
      admission.expected_binding.proof_epoch !=
          admission.observed_binding.proof_epoch) {
    output.failure = DomainConstructionCollectorSourceFailureV1::proof_epoch;
    return output;
  }
  if (admission.expected_binding.date_raw !=
      admission.observed_binding.date_raw) {
    output.failure = DomainConstructionCollectorSourceFailureV1::date;
    return output;
  }
  if (read_memory == nullptr || source.candidate_row_address == 0U) {
    output.failure = DomainConstructionCollectorSourceFailureV1::row_pointer;
    return output;
  }
  if (!CanReadCandidateRow(source.candidate_row_address)) {
    output.failure =
        DomainConstructionCollectorSourceFailureV1::address_overflow;
    return output;
  }

  std::array<std::uint8_t, kDomainConstructionCandidateRowBytesV1> row{};
  if (!read_memory(read_context, source.candidate_row_address, row.data(),
                   row.size())) {
    output.failure = DomainConstructionCollectorSourceFailureV1::memory_read;
    return output;
  }
  const auto identity = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), read_memory, read_context);
  if (!identity.ready) {
    output.failure =
        DomainConstructionCollectorSourceFailureV1::candidate_identity;
    return output;
  }
  if (source.final_legality.branch != ExpectedFinalBranch(identity.kind)) {
    output.failure = DomainConstructionCollectorSourceFailureV1::final_branch;
    return output;
  }

  DomainConstructionCandidateCostLegalitySourceV1 decoder_source{};
  decoder_source.candidate = identity;
  decoder_source.expected_binding = admission.expected_binding;
  decoder_source.observed_binding = admission.observed_binding;
  decoder_source.cost_vector_address = source.cost_vector_address;
  decoder_source.resource_balance_vector_address =
      source.resource_balance_vector_address;
  decoder_source.final_legality = source.final_legality;
  output.candidate = DecodeDomainConstructionCandidateCostLegalityV1(
      decoder_source, read_memory, read_context);
  if (!output.candidate.ready) {
    output.failure = MapCostFailure(output.candidate.unavailable);
    return output;
  }
  output.ready = true;
  output.failure = DomainConstructionCollectorSourceFailureV1::none;
  return output;
}

}  // namespace xar::ck3::research
