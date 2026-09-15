#include "domain_construction_cost_gate_collector_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace {

using namespace xar::ck3::shared;
using namespace xar::ck3::research;

constexpr std::uintptr_t kRow = 0x1000U;
constexpr std::uintptr_t kCost = 0x3000U;
constexpr std::uintptr_t kBalance = 0x5000U;
constexpr std::uintptr_t kHolding = 0x10000U;
constexpr std::uintptr_t kBuilding = 0x11000U;
constexpr std::uintptr_t kCandidate = 0x12000U;

struct Segment final {
  std::uintptr_t address = 0U;
  std::array<std::uint8_t, 64> bytes{};
  std::size_t size = 0U;
};

struct Memory final {
  std::array<Segment, 8> segments{};
  std::size_t count = 0U;
};

template <typename T>
void Add(Memory& memory, const std::uintptr_t address, const T& value) {
  assert(memory.count < memory.segments.size());
  auto& segment = memory.segments[memory.count++];
  segment.address = address;
  segment.size = sizeof(value);
  std::memcpy(segment.bytes.data(), &value, sizeof(value));
}

bool Read(void* context, const std::uintptr_t address, void* destination,
          const std::size_t bytes) {
  const auto& memory = *static_cast<const Memory*>(context);
  for (std::size_t index = memory.count; index > 0U; --index) {
    const auto& segment = memory.segments[index - 1U];
    if (segment.address == address && segment.size == bytes) {
      std::memcpy(destination, segment.bytes.data(), bytes);
      return true;
    }
  }
  return false;
}

template <typename T>
void Put(std::array<std::uint8_t, 0x28>& row,
         const std::size_t offset, const T value) {
  std::memcpy(row.data() + offset, &value, sizeof(value));
}

Memory Fixture(const std::int64_t first_cost = 100,
               const std::int64_t first_balance = 101) {
  Memory memory{};
  std::array<std::uint8_t, 0x28> row{};
  Put(row, 0x00U, std::int32_t{240});
  Put(row, 0x08U, kHolding);
  Put(row, 0x10U, kBuilding);
  Put(row, 0x18U, kCandidate);
  Put(row, 0x20U, std::int32_t{4});
  row[0x24U] = 1U;
  const std::array<std::int64_t, 8> cost{first_cost, 0, 0, 0, 0, 0, 0, 0};
  const std::array<std::int64_t, 8> balance{
      first_balance, 0, 0, 0, 0, 0, 0, 0};
  Add(memory, kRow, row);
  Add(memory, kCost, cost);
  Add(memory, kBalance, balance);
  Add(memory, kHolding + 0x10U, std::int32_t{17});
  Add(memory, kBuilding + 0x10U, std::int32_t{16777258});
  Add(memory, kCandidate + 0x10U, std::int32_t{-1});
  return memory;
}

DomainConstructionCostGateAdmissionV1 Admission() {
  return {true, true, 7U, 7U, {42U, 91U, 777}};
}

DomainConstructionCostGateRegistersV1 Registers() {
  return {kCost + 0x41U, kBalance, kRow};
}

void TestBorrowedAddressesAndTypedAdmission() {
  DomainConstructionBorrowedCollectorFrameV1 frame{};
  const auto admission = Admission();
  assert(BorrowDomainConstructionCostGateFrameV1(
             admission, Registers(), frame) ==
         DomainConstructionCostGateFailureV1::none);
  assert(frame.candidate_row_address == kRow);
  assert(frame.cost_vector_address == kCost);
  assert(frame.resource_balance_vector_address == kBalance);
  assert(frame.observed_binding.generation == 42U);
  assert(!frame.final_legality.observed);

  auto wrong_thread = admission;
  wrong_thread.current_thread_id = 8U;
  assert(BorrowDomainConstructionCostGateFrameV1(
             wrong_thread, Registers(), frame) ==
         DomainConstructionCostGateFailureV1::application_main);
  assert(frame.candidate_row_address == 0U);
  auto odd_generation = admission;
  odd_generation.binding.generation = 43U;
  assert(BorrowDomainConstructionCostGateFrameV1(
             odd_generation, Registers(), frame) ==
         DomainConstructionCostGateFailureV1::binding);
  auto invalid_address = Registers();
  invalid_address.rbp = 0x40U;
  assert(BorrowDomainConstructionCostGateFrameV1(
             admission, invalid_address, frame) ==
         DomainConstructionCostGateFailureV1::source_address);
}

void TestAffordableDoesNotBecomeActionableBeforeFinalGate() {
  auto memory = Fixture();
  const auto result = ReadDomainConstructionCostGateOwnedV1(
      Admission(), Registers(), Read, &memory);
  assert(result.failure == DomainConstructionCostGateFailureV1::none);
  assert(!result.sample.ready);
  assert(result.sample.failure ==
         DomainConstructionCollectorSourceFailureV1::final_observation);
  assert(result.sample.candidate.candidate_id ==
         "building:17:4:16777258");
  assert(result.sample.candidate.native_affordable);
  assert(result.sample.candidate.cost_raw[0] == 100);
  assert(result.sample.candidate.resource_balance_raw[0] == 101);
  assert(!result.sample.candidate.actionable);
  assert(!result.sample.final_legality.observed);
}

void TestExactNativeResourceRejectionIsObservable() {
  auto memory = Fixture(100, 100);
  const auto result = ReadDomainConstructionCostGateOwnedV1(
      Admission(), Registers(), Read, &memory);
  assert(result.failure == DomainConstructionCostGateFailureV1::none);
  assert(result.sample.ready);
  assert(result.sample.candidate.ready);
  assert(!result.sample.candidate.actionable);
  assert(!result.sample.candidate.native_affordable);
  assert(result.sample.candidate.rejection_reason ==
         DomainConstructionCandidateRejectionReasonV1::insufficient_resource);
  assert(result.sample.candidate.first_blocking_resource_slot == 0U);
}

}  // namespace

int main() {
  TestBorrowedAddressesAndTypedAdmission();
  TestAffordableDoesNotBecomeActionableBeforeFinalGate();
  TestExactNativeResourceRejectionIsObservable();
  return 0;
}
