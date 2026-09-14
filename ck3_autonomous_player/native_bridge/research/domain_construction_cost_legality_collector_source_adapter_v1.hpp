#pragma once

#include "domain_construction_candidate_cost_legality_decoder_v1.hpp"

#include <cstdint>

namespace xar::ck3::research {

enum class DomainConstructionCollectorSourceFailureV1 : std::uint8_t {
  none = 0,
  exact_build,
  application_main,
  session,
  generation,
  proof_epoch,
  date,
  row_pointer,
  address_overflow,
  memory_read,
  candidate_identity,
  final_branch,
  final_observation,
  cost_legality,
};

struct DomainConstructionCollectorAdmissionV1 final {
  bool exact_build_admitted = false;
  std::uint32_t application_main_thread_id = 0;
  std::uint32_t current_thread_id = 0;
  bool session_live = false;
  DomainConstructionCandidateSnapshotBindingV1 expected_binding;
  DomainConstructionCandidateSnapshotBindingV1 observed_binding;
};

struct DomainConstructionExactCollectorMemorySampleV1 final {
  DomainConstructionCollectorAdmissionV1 admission;
  std::uintptr_t candidate_row_address = 0;
  std::uintptr_t cost_vector_address = 0;
  std::uintptr_t resource_balance_vector_address = 0;
  DomainConstructionNativeFinalLegalityObservationV1 final_legality;
};

struct DomainConstructionOwnedCollectorSampleV1 final {
  bool ready = false;
  DomainConstructionCollectorSourceFailureV1 failure =
      DomainConstructionCollectorSourceFailureV1::none;
  DomainConstructionCandidateCostLegalityV1 candidate;
  DomainConstructionNativeFinalLegalityObservationV1 final_legality;
};

[[nodiscard]] DomainConstructionOwnedCollectorSampleV1
AdaptDomainConstructionExactCollectorMemoryV1(
    const DomainConstructionExactCollectorMemorySampleV1& source,
    DomainConstructionReadMemoryV1 read_memory, void* read_context);

}  // namespace xar::ck3::research
