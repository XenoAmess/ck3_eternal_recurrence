#include "domain_construction_candidate_cost_legality_decoder_v1.hpp"

#include <array>
#include <limits>

namespace xar::ck3::research {
namespace {

bool BindingsEqual(
    const DomainConstructionCandidateSnapshotBindingV1& left,
    const DomainConstructionCandidateSnapshotBindingV1& right) {
  return left.generation == right.generation &&
         left.proof_epoch == right.proof_epoch &&
         left.date_raw == right.date_raw;
}

bool CanReadResourceVector(const std::uintptr_t address) {
  return address != 0U &&
         address <= std::numeric_limits<std::uintptr_t>::max() -
                        (kDomainConstructionResourceVectorBytesV1 - 1U);
}

DomainConstructionNativeFinalLegalityBranchV1 BranchForCandidate(
    const DomainConstructionCandidateKindV1 kind) {
  return kind == DomainConstructionCandidateKindV1::building_in_holding
             ? DomainConstructionNativeFinalLegalityBranchV1::building
             : DomainConstructionNativeFinalLegalityBranchV1::new_holding;
}

}  // namespace

DomainConstructionCandidateCostLegalityV1
DecodeDomainConstructionCandidateCostLegalityV1(
    const DomainConstructionCandidateCostLegalitySourceV1& source,
    const DomainConstructionReadMemoryV1 read_memory, void* read_context) {
  DomainConstructionCandidateCostLegalityV1 result{};
  if (!source.candidate.ready || source.candidate.candidate_id.empty()) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::candidate_identity;
    return result;
  }
  if (source.candidate.kind !=
          DomainConstructionCandidateKindV1::building_in_holding &&
      source.candidate.kind != DomainConstructionCandidateKindV1::new_holding) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::candidate_identity;
    return result;
  }
  result.candidate_id = source.candidate.candidate_id;
  result.candidate_kind = source.candidate.kind;

  if (source.expected_binding.generation == 0U ||
      source.observed_binding.generation == 0U ||
      (source.expected_binding.generation & 1U) != 0U ||
      (source.observed_binding.generation & 1U) != 0U) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::generation;
    return result;
  }
  if (source.expected_binding.proof_epoch == 0U ||
      source.observed_binding.proof_epoch == 0U) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::proof_epoch;
    return result;
  }
  if (!BindingsEqual(source.expected_binding, source.observed_binding)) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::binding_drift;
    return result;
  }
  result.binding = source.observed_binding;

  if (read_memory == nullptr) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::memory_read;
    return result;
  }
  if (source.cost_vector_address == 0U ||
      source.resource_balance_vector_address == 0U) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::null_pointer;
    return result;
  }
  if (!CanReadResourceVector(source.cost_vector_address) ||
      !CanReadResourceVector(source.resource_balance_vector_address)) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::address_overflow;
    return result;
  }

  std::array<std::int64_t, kDomainConstructionResourceSlotCountV1> costs{};
  std::array<std::int64_t, kDomainConstructionResourceSlotCountV1> balances{};
  if (!read_memory(read_context, source.cost_vector_address, costs.data(),
                   kDomainConstructionResourceVectorBytesV1) ||
      !read_memory(read_context, source.resource_balance_vector_address,
                   balances.data(), kDomainConstructionResourceVectorBytesV1)) {
    result.unavailable =
        DomainConstructionCandidateCostLegalityUnavailableV1::memory_read;
    return result;
  }
  result.cost_raw = costs;
  result.resource_balance_raw = balances;

  result.native_affordable = true;
  for (std::size_t slot = 0; slot < kDomainConstructionResourceSlotCountV1;
       ++slot) {
    const bool affordable = costs[slot] <= 0 || costs[slot] < balances[slot];
    result.resource_affordable[slot] = affordable;
    if (!affordable) {
      result.native_affordable = false;
      result.blocking_resource_mask = static_cast<std::uint8_t>(
          result.blocking_resource_mask | (1U << slot));
      if (result.first_blocking_resource_slot ==
          kDomainConstructionNoBlockingResourceSlotV1) {
        result.first_blocking_resource_slot =
            static_cast<std::uint8_t>(slot);
      }
    }
  }

  if (!result.native_affordable) {
    result.ready = true;
    result.rejection_reason =
        DomainConstructionCandidateRejectionReasonV1::insufficient_resource;
    return result;
  }
  if (!source.final_legality.observed) {
    result.unavailable = DomainConstructionCandidateCostLegalityUnavailableV1::
        final_legality_unobserved;
    return result;
  }
  if (source.final_legality.branch != BranchForCandidate(source.candidate.kind)) {
    result.unavailable = DomainConstructionCandidateCostLegalityUnavailableV1::
        candidate_kind_branch_mismatch;
    return result;
  }

  result.ready = true;
  result.native_final_legal = source.final_legality.allowed;
  result.actionable = result.native_final_legal;
  if (!result.native_final_legal) {
    result.rejection_reason =
        source.final_legality.branch ==
                DomainConstructionNativeFinalLegalityBranchV1::building
            ? DomainConstructionCandidateRejectionReasonV1::
                  building_native_final_legality_rejected
            : DomainConstructionCandidateRejectionReasonV1::
                  holding_native_final_legality_rejected;
  }
  return result;
}

}  // namespace xar::ck3::research
