#include "domain_construction_candidate_cost_legality_decoder_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

using xar::ck3::research::DecodeDomainConstructionCandidateCostLegalityV1;
using xar::ck3::research::DomainConstructionCandidateCostLegalitySourceV1;
using xar::ck3::research::DomainConstructionCandidateCostLegalityUnavailableV1;
using xar::ck3::research::DomainConstructionCandidateIdentityV1;
using xar::ck3::research::DomainConstructionCandidateKindV1;
using xar::ck3::research::DomainConstructionCandidateRejectionReasonV1;
using xar::ck3::research::DomainConstructionCandidateSnapshotBindingV1;
using xar::ck3::research::DomainConstructionNativeFinalLegalityBranchV1;
using xar::ck3::research::kDomainConstructionNoBlockingResourceSlotV1;

inline constexpr std::uintptr_t kCostAddress = 0x1000U;
inline constexpr std::uintptr_t kBalanceAddress = 0x2000U;

struct FixtureMemory final {
  std::array<std::int64_t, 8> costs{};
  std::array<std::int64_t, 8> balances{};
  bool reject_cost = false;
  bool reject_balance = false;
};

bool ReadFixtureMemory(void* context, const std::uintptr_t address,
                       void* destination, const std::size_t bytes) {
  auto& memory = *static_cast<FixtureMemory*>(context);
  if (bytes != sizeof(memory.costs)) {
    return false;
  }
  if (address == kCostAddress && !memory.reject_cost) {
    std::memcpy(destination, memory.costs.data(), bytes);
    return true;
  }
  if (address == kBalanceAddress && !memory.reject_balance) {
    std::memcpy(destination, memory.balances.data(), bytes);
    return true;
  }
  return false;
}

DomainConstructionCandidateIdentityV1 BuildingIdentity() {
  DomainConstructionCandidateIdentityV1 identity{};
  identity.ready = true;
  identity.kind = DomainConstructionCandidateKindV1::building_in_holding;
  identity.holding_province_id = 17;
  identity.building_type_id = 16777258;
  identity.candidate_selector = 4;
  identity.candidate_id = "building:17:4:16777258";
  return identity;
}

DomainConstructionCandidateIdentityV1 HoldingIdentity() {
  DomainConstructionCandidateIdentityV1 identity{};
  identity.ready = true;
  identity.kind = DomainConstructionCandidateKindV1::new_holding;
  identity.candidate_province_id = 867;
  identity.candidate_selector = 3;
  identity.candidate_id = "holding:867:3";
  return identity;
}

DomainConstructionCandidateCostLegalitySourceV1 MakeSource(
    const DomainConstructionCandidateIdentityV1& identity,
    const DomainConstructionNativeFinalLegalityBranchV1 branch,
    const bool observed, const bool allowed) {
  DomainConstructionCandidateCostLegalitySourceV1 source{};
  source.candidate = identity;
  source.expected_binding = DomainConstructionCandidateSnapshotBindingV1{
      42U, 91U, 777};
  source.observed_binding = source.expected_binding;
  source.cost_vector_address = kCostAddress;
  source.resource_balance_vector_address = kBalanceAddress;
  source.final_legality = {observed, branch, allowed};
  return source;
}

void TestBuildingActionable() {
  FixtureMemory memory{};
  memory.costs = {100, 0, 50, -1, 0, 0, 0, 0};
  memory.balances = {101, 0, 51, 0, 0, 0, 0, 0};
  const auto source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);
  const auto value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.ready);
  assert(value.actionable);
  assert(value.native_affordable);
  assert(value.native_final_legal);
  assert(value.candidate_id == "building:17:4:16777258");
  assert(value.binding.generation == 42U);
  assert(value.binding.proof_epoch == 91U);
  assert(value.binding.date_raw == 777);
  assert(value.first_blocking_resource_slot ==
         kDomainConstructionNoBlockingResourceSlotV1);
  assert(value.blocking_resource_mask == 0U);
  assert(value.rejection_reason ==
         DomainConstructionCandidateRejectionReasonV1::none);
  assert(value.unavailable ==
         DomainConstructionCandidateCostLegalityUnavailableV1::none);
}

void TestStrictAffordabilityAndBlockingMask() {
  FixtureMemory memory{};
  memory.costs = {100, 0, 20, -1, 0, 0, 0, 0};
  memory.balances = {100, 0, 19, -50, 0, 0, 0, 0};
  auto source = MakeSource(
      HoldingIdentity(),
      DomainConstructionNativeFinalLegalityBranchV1::new_holding, false, false);
  const auto value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.ready);
  assert(!value.actionable);
  assert(!value.native_affordable);
  assert(!value.native_final_legal);
  assert(!value.resource_affordable[0]);
  assert(value.resource_affordable[1]);
  assert(!value.resource_affordable[2]);
  assert(value.resource_affordable[3]);
  assert(value.first_blocking_resource_slot == 0U);
  assert(value.blocking_resource_mask == 0x05U);
  assert(value.rejection_reason ==
         DomainConstructionCandidateRejectionReasonV1::insufficient_resource);
  assert(value.unavailable ==
         DomainConstructionCandidateCostLegalityUnavailableV1::none);
}

void TestNativeFinalLegalityRejections() {
  FixtureMemory memory{};
  memory.costs = {1, 0, 0, 0, 0, 0, 0, 0};
  memory.balances = {2, 0, 0, 0, 0, 0, 0, 0};

  auto source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, false);
  auto value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.ready && value.native_affordable && !value.actionable);
  assert(value.rejection_reason ==
         DomainConstructionCandidateRejectionReasonV1::
             building_native_final_legality_rejected);

  source = MakeSource(
      HoldingIdentity(),
      DomainConstructionNativeFinalLegalityBranchV1::new_holding, true, false);
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.ready && value.native_affordable && !value.actionable);
  assert(value.rejection_reason ==
         DomainConstructionCandidateRejectionReasonV1::
             holding_native_final_legality_rejected);
}

void TestBindingAndFinalObservationUnavailable() {
  FixtureMemory memory{};
  memory.balances.fill(1);
  auto source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);

  source.observed_binding.date_raw = 778;
  auto value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(!value.ready);
  assert(value.unavailable ==
         DomainConstructionCandidateCostLegalityUnavailableV1::binding_drift);

  source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);
  source.observed_binding.generation = 43U;
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable ==
         DomainConstructionCandidateCostLegalityUnavailableV1::generation);

  source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);
  source.observed_binding.proof_epoch = 0U;
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable ==
         DomainConstructionCandidateCostLegalityUnavailableV1::proof_epoch);

  source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      false, false);
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable == DomainConstructionCandidateCostLegalityUnavailableV1::
                                  final_legality_unobserved);

  source = MakeSource(
      BuildingIdentity(),
      DomainConstructionNativeFinalLegalityBranchV1::new_holding, true, true);
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable == DomainConstructionCandidateCostLegalityUnavailableV1::
                                  candidate_kind_branch_mismatch);
}

void TestMemoryAndIdentityUnavailable() {
  FixtureMemory memory{};
  memory.balances.fill(1);
  auto source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);

  source.candidate.ready = false;
  auto value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable == DomainConstructionCandidateCostLegalityUnavailableV1::
                                  candidate_identity);

  source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);
  source.candidate.kind = static_cast<DomainConstructionCandidateKindV1>(99);
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable == DomainConstructionCandidateCostLegalityUnavailableV1::
                                  candidate_identity);

  source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);
  source.cost_vector_address = 0U;
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable ==
         DomainConstructionCandidateCostLegalityUnavailableV1::null_pointer);

  source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);
  value = DecodeDomainConstructionCandidateCostLegalityV1(source, nullptr, &memory);
  assert(value.unavailable ==
         DomainConstructionCandidateCostLegalityUnavailableV1::memory_read);

  source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);
  source.cost_vector_address = std::numeric_limits<std::uintptr_t>::max() - 8U;
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable == DomainConstructionCandidateCostLegalityUnavailableV1::
                                  address_overflow);

  source = MakeSource(
      BuildingIdentity(), DomainConstructionNativeFinalLegalityBranchV1::building,
      true, true);
  memory.reject_balance = true;
  value = DecodeDomainConstructionCandidateCostLegalityV1(
      source, ReadFixtureMemory, &memory);
  assert(value.unavailable ==
         DomainConstructionCandidateCostLegalityUnavailableV1::memory_read);
}

}  // namespace

int main() {
  TestBuildingActionable();
  TestStrictAffordabilityAndBlockingMask();
  TestNativeFinalLegalityRejections();
  TestBindingAndFinalObservationUnavailable();
  TestMemoryAndIdentityUnavailable();
  return 0;
}
