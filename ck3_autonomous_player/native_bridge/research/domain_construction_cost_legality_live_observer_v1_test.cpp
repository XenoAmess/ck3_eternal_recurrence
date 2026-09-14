#include "domain_construction_cost_legality_live_observer_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

using namespace xar::ck3::research;

inline constexpr std::uintptr_t kFirstRow = 0x1000U;
inline constexpr std::uintptr_t kSecondRow = 0x2000U;
inline constexpr std::uintptr_t kFirstCost = 0x3000U;
inline constexpr std::uintptr_t kSecondCost = 0x4000U;
inline constexpr std::uintptr_t kFirstBalance = 0x5000U;
inline constexpr std::uintptr_t kSecondBalance = 0x6000U;
inline constexpr std::uintptr_t kHoldingObject = 0x10000U;
inline constexpr std::uintptr_t kBuildingObject = 0x11000U;
inline constexpr std::uintptr_t kCandidateObject = 0x12000U;

struct MemorySegment final {
  std::uintptr_t address = 0;
  std::array<std::uint8_t, 64> bytes{};
  std::size_t size = 0;
};

struct FixtureMemory final {
  std::array<MemorySegment, 20> segments{};
  std::size_t count = 0;
};

template <typename T>
void AddValue(FixtureMemory& memory, const std::uintptr_t address,
              const T& value) {
  assert(memory.count < memory.segments.size());
  assert(sizeof(value) <= memory.segments[0].bytes.size());
  auto& segment = memory.segments[memory.count++];
  segment.address = address;
  segment.size = sizeof(value);
  std::memcpy(segment.bytes.data(), &value, sizeof(value));
}

bool ReadFixtureMemory(void* context, const std::uintptr_t address,
                       void* destination, const std::size_t bytes) {
  const auto& memory = *static_cast<const FixtureMemory*>(context);
  for (std::size_t index = memory.count; index > 0; --index) {
    const auto& segment = memory.segments[index - 1];
    if (segment.address == address && segment.size == bytes) {
      std::memcpy(destination, segment.bytes.data(), bytes);
      return true;
    }
  }
  return false;
}

template <typename T>
void Put(std::array<std::uint8_t, 0x28>& row, const std::size_t offset,
         const T value) {
  std::memcpy(row.data() + offset, &value, sizeof(value));
}

std::array<std::uint8_t, 0x28> BuildingRow(const std::int32_t selector = 4) {
  std::array<std::uint8_t, 0x28> row{};
  Put(row, 0x00, std::int32_t{240});
  Put(row, 0x08, kHoldingObject);
  Put(row, 0x10, kBuildingObject);
  Put(row, 0x18, kCandidateObject);
  Put(row, 0x20, selector);
  row[0x24] = 1U;
  return row;
}

std::array<std::uint8_t, 0x28> HoldingRow(const std::int32_t selector = 3) {
  std::array<std::uint8_t, 0x28> row{};
  Put(row, 0x00, std::int32_t{180});
  Put(row, 0x08, kHoldingObject);
  Put(row, 0x10, kBuildingObject);
  Put(row, 0x18, kCandidateObject);
  Put(row, 0x20, selector);
  row[0x24] = 1U;
  return row;
}

DomainConstructionExactCollectorMemorySampleV1 Sample(
    const std::uintptr_t row, const std::uintptr_t cost,
    const std::uintptr_t balance,
    const DomainConstructionNativeFinalLegalityBranchV1 branch,
    const bool observed = true, const bool allowed = true) {
  DomainConstructionExactCollectorMemorySampleV1 sample{};
  sample.admission.exact_build_admitted = true;
  sample.admission.application_main_thread_id = 7U;
  sample.admission.current_thread_id = 7U;
  sample.admission.session_live = true;
  sample.admission.expected_binding = {42U, 91U, 777};
  sample.admission.observed_binding = sample.admission.expected_binding;
  sample.candidate_row_address = row;
  sample.cost_vector_address = cost;
  sample.resource_balance_vector_address = balance;
  sample.final_legality = {observed, branch, allowed};
  return sample;
}

FixtureMemory BuildingMemory() {
  FixtureMemory memory{};
  const auto row = BuildingRow();
  const std::array<std::int64_t, 8> cost{100, 0, 50, -1, 0, 0, 0, 0};
  const std::array<std::int64_t, 8> balance{101, 0, 51, 0, 0, 0, 0, 0};
  AddValue(memory, kFirstRow, row);
  AddValue(memory, kSecondRow, row);
  AddValue(memory, kFirstCost, cost);
  AddValue(memory, kSecondCost, cost);
  AddValue(memory, kFirstBalance, balance);
  AddValue(memory, kSecondBalance, balance);
  AddValue(memory, kHoldingObject + 0x10U, std::int32_t{17});
  AddValue(memory, kBuildingObject + 0x10U, std::int32_t{16777258});
  AddValue(memory, kCandidateObject + 0x10U, std::int32_t{-1});
  return memory;
}

void TestActionableAvailablePublication() {
  auto memory = BuildingMemory();
  const auto first = Sample(
      kFirstRow, kFirstCost, kFirstBalance,
      DomainConstructionNativeFinalLegalityBranchV1::building);
  const auto second = Sample(
      kSecondRow, kSecondCost, kSecondBalance,
      DomainConstructionNativeFinalLegalityBranchV1::building);
  DomainConstructionCostLegalityLiveObserverStateV1 state{};
  assert(CaptureDomainConstructionCostLegalityDoubleSampleV1(
      state, first, second, ReadFixtureMemory, &memory));
  const auto publication =
      ReadDomainConstructionCostLegalityPublicationV1(state);
  assert(publication.available);
  assert(publication.publication_generation == 2U);
  assert(publication.candidate.ready);
  assert(publication.candidate.actionable);
  assert(publication.candidate.candidate_id ==
         "building:17:4:16777258");
  assert(publication.candidate.cost_raw[0] == 100);
  assert(publication.candidate.resource_balance_raw[0] == 101);
  assert(state.accepted_publication_count == 1U);
  assert(state.typed_red_count == 0U);
  assert(state.last_red_flags ==
         domain_construction_cost_legality_live_red_none);
}

void TestKnownRejectionStillAvailable() {
  FixtureMemory memory{};
  const auto row = HoldingRow();
  const std::array<std::int64_t, 8> cost{100, 0, 20, 0, 0, 0, 0, 0};
  const std::array<std::int64_t, 8> balance{100, 0, 19, 0, 0, 0, 0, 0};
  AddValue(memory, kFirstRow, row);
  AddValue(memory, kSecondRow, row);
  AddValue(memory, kFirstCost, cost);
  AddValue(memory, kSecondCost, cost);
  AddValue(memory, kFirstBalance, balance);
  AddValue(memory, kSecondBalance, balance);
  AddValue(memory, kHoldingObject + 0x10U, std::int32_t{-1});
  AddValue(memory, kBuildingObject + 0x10U, std::int32_t{-1});
  AddValue(memory, kCandidateObject + 0x10U, std::int32_t{867});
  const auto first = Sample(
      kFirstRow, kFirstCost, kFirstBalance,
      DomainConstructionNativeFinalLegalityBranchV1::new_holding, false,
      false);
  const auto second = Sample(
      kSecondRow, kSecondCost, kSecondBalance,
      DomainConstructionNativeFinalLegalityBranchV1::new_holding, false,
      false);
  DomainConstructionCostLegalityLiveObserverStateV1 state{};
  assert(CaptureDomainConstructionCostLegalityDoubleSampleV1(
      state, first, second, ReadFixtureMemory, &memory));
  const auto publication =
      ReadDomainConstructionCostLegalityPublicationV1(state);
  assert(publication.available);
  assert(!publication.candidate.actionable);
  assert(publication.candidate.candidate_id == "holding:867:3");
  assert(publication.candidate.rejection_reason ==
         DomainConstructionCandidateRejectionReasonV1::insufficient_resource);
  assert(publication.candidate.blocking_resource_mask == 0x05U);
}

void TestIdentityBindingAndBranchDriftAreTypedRed() {
  auto memory = BuildingMemory();
  const auto first = Sample(
      kFirstRow, kFirstCost, kFirstBalance,
      DomainConstructionNativeFinalLegalityBranchV1::building);
  auto second = Sample(
      kSecondRow, kSecondCost, kSecondBalance,
      DomainConstructionNativeFinalLegalityBranchV1::building);
  DomainConstructionCostLegalityLiveObserverStateV1 state{};
  assert(CaptureDomainConstructionCostLegalityDoubleSampleV1(
      state, first, second, ReadFixtureMemory, &memory));
  const auto accepted =
      ReadDomainConstructionCostLegalityPublicationV1(state);

  AddValue(memory, kSecondRow, BuildingRow(5));
  second.admission.expected_binding = {44U, 92U, 778};
  second.admission.observed_binding = second.admission.expected_binding;
  assert(!CaptureDomainConstructionCostLegalityDoubleSampleV1(
      state, first, second, ReadFixtureMemory, &memory));
  assert((state.last_red_flags &
          domain_construction_cost_legality_live_red_generation) != 0U);
  assert((state.last_red_flags &
          domain_construction_cost_legality_live_red_proof_epoch) != 0U);
  assert((state.last_red_flags &
          domain_construction_cost_legality_live_red_date) != 0U);
  const auto retained =
      ReadDomainConstructionCostLegalityPublicationV1(state);
  const bool previous_complete_generation_retained =
      retained.available &&
      retained.publication_generation == accepted.publication_generation;
  assert(previous_complete_generation_retained);
  assert(retained.available);
  assert(retained.publication_generation == accepted.publication_generation);
  assert(retained.candidate.candidate_id == accepted.candidate.candidate_id);

  second = Sample(
      kSecondRow, kSecondCost, kSecondBalance,
      DomainConstructionNativeFinalLegalityBranchV1::building);
  second.final_legality.branch =
      DomainConstructionNativeFinalLegalityBranchV1::new_holding;
  assert(!CaptureDomainConstructionCostLegalityDoubleSampleV1(
      state, first, second, ReadFixtureMemory, &memory));
  assert((state.last_red_flags &
          domain_construction_cost_legality_live_red_branch) != 0U);

  second.final_legality.branch =
      DomainConstructionNativeFinalLegalityBranchV1::building;
  assert(!CaptureDomainConstructionCostLegalityDoubleSampleV1(
      state, first, second, ReadFixtureMemory, &memory));
  assert((state.last_red_flags &
          domain_construction_cost_legality_live_red_identity) != 0U);
}

void TestPayloadAndApplicationMainFailuresAreTypedRed() {
  auto memory = BuildingMemory();
  const auto first = Sample(
      kFirstRow, kFirstCost, kFirstBalance,
      DomainConstructionNativeFinalLegalityBranchV1::building);
  auto second = Sample(
      kSecondRow, kSecondCost, kSecondBalance,
      DomainConstructionNativeFinalLegalityBranchV1::building);
  const std::array<std::int64_t, 8> changed_cost{99, 0, 50, -1, 0, 0, 0, 0};
  const std::array<std::int64_t, 8> changed_balance{102, 0, 51, 0, 0, 0, 0, 0};
  AddValue(memory, kSecondCost, changed_cost);
  AddValue(memory, kSecondBalance, changed_balance);
  DomainConstructionCostLegalityLiveObserverStateV1 state{};
  assert(!CaptureDomainConstructionCostLegalityDoubleSampleV1(
      state, first, second, ReadFixtureMemory, &memory));
  assert((state.last_red_flags &
          domain_construction_cost_legality_live_red_cost) != 0U);
  assert((state.last_red_flags &
          domain_construction_cost_legality_live_red_resource_balance) != 0U);

  second.admission.current_thread_id = 8U;
  assert(!CaptureDomainConstructionCostLegalityDoubleSampleV1(
      state, first, second, ReadFixtureMemory, &memory));
  assert((state.last_red_flags &
          domain_construction_cost_legality_live_red_application_main) != 0U);
  assert(!ReadDomainConstructionCostLegalityPublicationV1(state).available);
}

}  // namespace

int main() {
  TestActionableAvailablePublication();
  TestKnownRejectionStillAvailable();
  TestIdentityBindingAndBranchDriftAreTypedRed();
  TestPayloadAndApplicationMainFailuresAreTypedRed();
  return 0;
}
