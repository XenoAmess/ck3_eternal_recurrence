#pragma once

#include "domain_construction_cost_legality_collector_source_adapter_v1.hpp"

#include <cstdint>
#include <mutex>

namespace xar::ck3::research {

enum DomainConstructionCostLegalityLiveRedV1 : std::uint32_t {
  domain_construction_cost_legality_live_red_none = 0,
  domain_construction_cost_legality_live_red_exact_build = 1U << 0,
  domain_construction_cost_legality_live_red_application_main = 1U << 1,
  domain_construction_cost_legality_live_red_session = 1U << 2,
  domain_construction_cost_legality_live_red_identity = 1U << 3,
  domain_construction_cost_legality_live_red_generation = 1U << 4,
  domain_construction_cost_legality_live_red_proof_epoch = 1U << 5,
  domain_construction_cost_legality_live_red_date = 1U << 6,
  domain_construction_cost_legality_live_red_branch = 1U << 7,
  domain_construction_cost_legality_live_red_memory = 1U << 8,
  domain_construction_cost_legality_live_red_final_observation = 1U << 9,
  domain_construction_cost_legality_live_red_cost = 1U << 10,
  domain_construction_cost_legality_live_red_resource_balance = 1U << 11,
  domain_construction_cost_legality_live_red_final_legality = 1U << 12,
};

struct DomainConstructionCostLegalityPublicationV1 final {
  bool available = false;
  std::uint64_t publication_generation = 0;
  DomainConstructionCandidateCostLegalityV1 candidate;
};

struct DomainConstructionCostLegalityLiveObserverStateV1 final {
  mutable std::mutex publication_mutex;
  std::uint64_t publication_generation = 0;
  std::uint64_t accepted_publication_count = 0;
  std::uint64_t typed_red_count = 0;
  std::uint32_t last_red_flags =
      domain_construction_cost_legality_live_red_none;
  DomainConstructionCostLegalityPublicationV1 published;
};

[[nodiscard]] bool CaptureDomainConstructionCostLegalityDoubleSampleV1(
    DomainConstructionCostLegalityLiveObserverStateV1& state,
    const DomainConstructionExactCollectorMemorySampleV1& first,
    const DomainConstructionExactCollectorMemorySampleV1& second,
    DomainConstructionReadMemoryV1 read_memory, void* read_context);

[[nodiscard]] DomainConstructionCostLegalityPublicationV1
ReadDomainConstructionCostLegalityPublicationV1(
    const DomainConstructionCostLegalityLiveObserverStateV1& state);

}  // namespace xar::ck3::research
