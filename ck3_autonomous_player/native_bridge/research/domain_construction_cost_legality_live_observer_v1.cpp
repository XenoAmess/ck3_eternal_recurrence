#include "domain_construction_cost_legality_live_observer_v1.hpp"

#include <limits>
#include <mutex>
#include <utility>

namespace xar::ck3::research {
namespace {

std::uint32_t RedForSourceFailure(
    const DomainConstructionCollectorSourceFailureV1 failure) {
  switch (failure) {
    case DomainConstructionCollectorSourceFailureV1::none:
      return domain_construction_cost_legality_live_red_none;
    case DomainConstructionCollectorSourceFailureV1::exact_build:
      return domain_construction_cost_legality_live_red_exact_build;
    case DomainConstructionCollectorSourceFailureV1::application_main:
      return domain_construction_cost_legality_live_red_application_main;
    case DomainConstructionCollectorSourceFailureV1::session:
      return domain_construction_cost_legality_live_red_session;
    case DomainConstructionCollectorSourceFailureV1::generation:
      return domain_construction_cost_legality_live_red_generation;
    case DomainConstructionCollectorSourceFailureV1::proof_epoch:
      return domain_construction_cost_legality_live_red_proof_epoch;
    case DomainConstructionCollectorSourceFailureV1::date:
      return domain_construction_cost_legality_live_red_date;
    case DomainConstructionCollectorSourceFailureV1::row_pointer:
    case DomainConstructionCollectorSourceFailureV1::address_overflow:
    case DomainConstructionCollectorSourceFailureV1::memory_read:
      return domain_construction_cost_legality_live_red_memory;
    case DomainConstructionCollectorSourceFailureV1::candidate_identity:
      return domain_construction_cost_legality_live_red_identity;
    case DomainConstructionCollectorSourceFailureV1::final_branch:
      return domain_construction_cost_legality_live_red_branch;
    case DomainConstructionCollectorSourceFailureV1::final_observation:
      return domain_construction_cost_legality_live_red_final_observation;
    case DomainConstructionCollectorSourceFailureV1::cost_legality:
      return domain_construction_cost_legality_live_red_final_legality;
  }
  return domain_construction_cost_legality_live_red_final_legality;
}

void Reject(DomainConstructionCostLegalityLiveObserverStateV1& state,
            const std::uint32_t red_flags) {
  ++state.typed_red_count;
  state.last_red_flags = red_flags;
}

std::uint32_t CompareSamples(
    const DomainConstructionOwnedCollectorSampleV1& first,
    const DomainConstructionOwnedCollectorSampleV1& second) {
  std::uint32_t red = domain_construction_cost_legality_live_red_none;
  const auto& left = first.candidate;
  const auto& right = second.candidate;
  if (left.candidate_id != right.candidate_id ||
      left.candidate_kind != right.candidate_kind) {
    red |= domain_construction_cost_legality_live_red_identity;
  }
  if (left.binding.generation != right.binding.generation) {
    red |= domain_construction_cost_legality_live_red_generation;
  }
  if (left.binding.proof_epoch != right.binding.proof_epoch) {
    red |= domain_construction_cost_legality_live_red_proof_epoch;
  }
  if (left.binding.date_raw != right.binding.date_raw) {
    red |= domain_construction_cost_legality_live_red_date;
  }
  if (first.final_legality.branch != second.final_legality.branch) {
    red |= domain_construction_cost_legality_live_red_branch;
  }
  if (left.cost_raw != right.cost_raw ||
      left.resource_affordable != right.resource_affordable ||
      left.native_affordable != right.native_affordable ||
      left.first_blocking_resource_slot !=
          right.first_blocking_resource_slot ||
      left.blocking_resource_mask != right.blocking_resource_mask ||
      left.rejection_reason != right.rejection_reason) {
    red |= domain_construction_cost_legality_live_red_cost;
  }
  if (left.resource_balance_raw != right.resource_balance_raw) {
    red |= domain_construction_cost_legality_live_red_resource_balance;
  }
  if (first.final_legality.observed != second.final_legality.observed ||
      first.final_legality.allowed != second.final_legality.allowed ||
      left.native_final_legal != right.native_final_legal ||
      left.actionable != right.actionable) {
    red |= domain_construction_cost_legality_live_red_final_legality;
  }
  return red;
}

}  // namespace

bool CaptureDomainConstructionCostLegalityDoubleSampleV1(
    DomainConstructionCostLegalityLiveObserverStateV1& state,
    const DomainConstructionExactCollectorMemorySampleV1& first,
    const DomainConstructionExactCollectorMemorySampleV1& second,
    const DomainConstructionReadMemoryV1 read_memory, void* read_context) {
  const auto first_owned = AdaptDomainConstructionExactCollectorMemoryV1(
      first, read_memory, read_context);
  const auto second_owned = AdaptDomainConstructionExactCollectorMemoryV1(
      second, read_memory, read_context);
  std::lock_guard lock(state.publication_mutex);
  std::uint32_t red = RedForSourceFailure(first_owned.failure) |
                      RedForSourceFailure(second_owned.failure);
  if (first_owned.ready && second_owned.ready) {
    red |= CompareSamples(first_owned, second_owned);
  }
  if (!first_owned.ready || !second_owned.ready ||
      red != domain_construction_cost_legality_live_red_none) {
    Reject(state, red == domain_construction_cost_legality_live_red_none
                      ? domain_construction_cost_legality_live_red_final_legality
                      : red);
    return false;
  }
  if ((state.publication_generation & 1U) != 0U ||
      state.publication_generation >
          std::numeric_limits<std::uint64_t>::max() - 2U) {
    Reject(state, domain_construction_cost_legality_live_red_generation);
    return false;
  }

  const auto next_complete_generation = state.publication_generation + 2U;
  state.publication_generation += 1U;
  DomainConstructionCostLegalityPublicationV1 publication{};
  publication.available = true;
  publication.publication_generation = next_complete_generation;
  publication.candidate = first_owned.candidate;
  state.published = std::move(publication);
  state.publication_generation = next_complete_generation;
  ++state.accepted_publication_count;
  state.last_red_flags = domain_construction_cost_legality_live_red_none;
  return true;
}

DomainConstructionCostLegalityPublicationV1
ReadDomainConstructionCostLegalityPublicationV1(
    const DomainConstructionCostLegalityLiveObserverStateV1& state) {
  std::lock_guard lock(state.publication_mutex);
  if ((state.publication_generation & 1U) != 0U ||
      state.published.publication_generation != state.publication_generation) {
    return {};
  }
  return state.published;
}

}  // namespace xar::ck3::research
