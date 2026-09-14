#pragma once

#include "domain_construction_candidate_identity_decoder_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string>

namespace xar::ck3::research {

inline constexpr std::size_t kDomainConstructionResourceSlotCountV1 = 8;
inline constexpr std::size_t kDomainConstructionResourceVectorBytesV1 =
    kDomainConstructionResourceSlotCountV1 * sizeof(std::int64_t);
inline constexpr std::uint8_t kDomainConstructionNoBlockingResourceSlotV1 =
    0xFFU;

enum class DomainConstructionNativeFinalLegalityBranchV1 : std::uint8_t {
  building = 1,
  new_holding = 2,
};

enum class DomainConstructionCandidateCostLegalityUnavailableV1 : std::uint8_t {
  none = 0,
  candidate_identity,
  generation,
  proof_epoch,
  binding_drift,
  null_pointer,
  address_overflow,
  memory_read,
  final_legality_unobserved,
  candidate_kind_branch_mismatch,
};

enum class DomainConstructionCandidateRejectionReasonV1 : std::uint8_t {
  none = 0,
  insufficient_resource,
  building_native_final_legality_rejected,
  holding_native_final_legality_rejected,
};

struct DomainConstructionCandidateSnapshotBindingV1 final {
  std::uint64_t generation = 0;
  std::uint64_t proof_epoch = 0;
  std::int64_t date_raw = 0;
};

struct DomainConstructionNativeFinalLegalityObservationV1 final {
  bool observed = false;
  DomainConstructionNativeFinalLegalityBranchV1 branch =
      DomainConstructionNativeFinalLegalityBranchV1::building;
  bool allowed = false;
};

struct DomainConstructionCandidateCostLegalitySourceV1 final {
  DomainConstructionCandidateIdentityV1 candidate;
  DomainConstructionCandidateSnapshotBindingV1 expected_binding;
  DomainConstructionCandidateSnapshotBindingV1 observed_binding;
  std::uintptr_t cost_vector_address = 0;
  std::uintptr_t resource_balance_vector_address = 0;
  DomainConstructionNativeFinalLegalityObservationV1 final_legality;
};

struct DomainConstructionCandidateCostLegalityV1 final {
  bool ready = false;
  bool actionable = false;
  std::string candidate_id;
  DomainConstructionCandidateKindV1 candidate_kind =
      DomainConstructionCandidateKindV1::building_in_holding;
  DomainConstructionCandidateSnapshotBindingV1 binding;
  std::array<std::int64_t, kDomainConstructionResourceSlotCountV1> cost_raw{};
  std::array<std::int64_t, kDomainConstructionResourceSlotCountV1>
      resource_balance_raw{};
  std::array<bool, kDomainConstructionResourceSlotCountV1>
      resource_affordable{};
  bool native_affordable = false;
  bool native_final_legal = false;
  std::uint8_t first_blocking_resource_slot =
      kDomainConstructionNoBlockingResourceSlotV1;
  std::uint8_t blocking_resource_mask = 0;
  DomainConstructionCandidateRejectionReasonV1 rejection_reason =
      DomainConstructionCandidateRejectionReasonV1::none;
  DomainConstructionCandidateCostLegalityUnavailableV1 unavailable =
      DomainConstructionCandidateCostLegalityUnavailableV1::none;
};

[[nodiscard]] DomainConstructionCandidateCostLegalityV1
DecodeDomainConstructionCandidateCostLegalityV1(
    const DomainConstructionCandidateCostLegalitySourceV1& source,
    DomainConstructionReadMemoryV1 read_memory, void* read_context);

}  // namespace xar::ck3::research
