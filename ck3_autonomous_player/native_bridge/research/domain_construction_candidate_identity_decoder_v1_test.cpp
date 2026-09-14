#include "domain_construction_candidate_identity_decoder_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

namespace {

using xar::ck3::research::DecodeDomainConstructionCandidateIdentityV1;
using xar::ck3::research::DomainConstructionCandidateDecodeFailureV1;
using xar::ck3::research::DomainConstructionCandidateKindV1;

struct IdentityCell final {
  std::uintptr_t address;
  std::int32_t identity;
};

struct FixtureMemory final {
  std::array<IdentityCell, 3> cells{};
  bool reject_all = false;
};

bool ReadFixtureMemory(void* context, const std::uintptr_t address,
                       void* destination, const std::size_t bytes) {
  auto& memory = *static_cast<FixtureMemory*>(context);
  if (memory.reject_all || bytes != sizeof(std::int32_t)) {
    return false;
  }
  for (const auto& cell : memory.cells) {
    if (cell.address == address) {
      std::memcpy(destination, &cell.identity, sizeof(cell.identity));
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

std::array<std::uint8_t, 0x28> MakeRow(
    const std::uintptr_t holding, const std::uintptr_t building,
    const std::uintptr_t candidate, const std::int32_t selector) {
  std::array<std::uint8_t, 0x28> row{};
  Put(row, 0x00, std::int32_t{240});
  Put(row, 0x08, holding);
  Put(row, 0x10, building);
  Put(row, 0x18, candidate);
  Put(row, 0x20, selector);
  row[0x24] = 1;
  return row;
}

FixtureMemory MakeMemory(const std::int32_t holding,
                         const std::int32_t building,
                         const std::int32_t candidate) {
  return FixtureMemory{{IdentityCell{0x1010, holding},
                        IdentityCell{0x2010, building},
                        IdentityCell{0x3010, candidate}},
                       false};
}

void TestBuildingCandidate() {
  auto memory = MakeMemory(17, 0x0100002A, -1);
  const auto row = MakeRow(0x1000, 0x2000, 0x3000, 4);
  const auto value = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  assert(value.ready);
  assert(value.failure == DomainConstructionCandidateDecodeFailureV1::none);
  assert(value.kind ==
         DomainConstructionCandidateKindV1::building_in_holding);
  assert(value.native_ai_value == 240);
  assert(value.holding_province_id == 17);
  assert(value.building_type_id == 0x0100002A);
  assert(value.candidate_province_id == -1);
  assert(value.candidate_selector == 4);
  assert(value.candidate_id == "building:17:4:16777258");
}

void TestNewHoldingCandidate() {
  auto memory = MakeMemory(-1, -1, 867);
  const auto row = MakeRow(0x1000, 0x2000, 0x3000, 3);
  const auto first = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  const auto second = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  assert(first.ready);
  assert(first.kind == DomainConstructionCandidateKindV1::new_holding);
  assert(first.candidate_province_id == 867);
  assert(first.candidate_selector == 3);
  assert(first.candidate_id == "holding:867:3");
  assert(first.candidate_id == second.candidate_id);
}

void TestTypedFailures() {
  auto memory = MakeMemory(17, 42, -1);
  auto row = MakeRow(0x1000, 0x2000, 0x3000, 4);

  auto value = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size() - 1, ReadFixtureMemory, &memory);
  assert(!value.ready);
  assert(value.failure == DomainConstructionCandidateDecodeFailureV1::row_size);

  row[0x24] = 0;
  value = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  assert(value.failure == DomainConstructionCandidateDecodeFailureV1::row_marker);

  row = MakeRow(0x1000, 0x2000, 0x3000, -1);
  value = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  assert(value.failure == DomainConstructionCandidateDecodeFailureV1::selector);

  row = MakeRow(0, 0x2000, 0x3000, 4);
  value = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  assert(value.failure ==
         DomainConstructionCandidateDecodeFailureV1::null_pointer);

  row = MakeRow(std::numeric_limits<std::uintptr_t>::max() - 8U, 0x2000,
                0x3000, 4);
  value = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  assert(value.failure ==
         DomainConstructionCandidateDecodeFailureV1::address_overflow);

  memory.reject_all = true;
  row = MakeRow(0x1000, 0x2000, 0x3000, 4);
  value = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  assert(value.failure == DomainConstructionCandidateDecodeFailureV1::memory_read);

  memory = MakeMemory(17, 42, 867);
  value = DecodeDomainConstructionCandidateIdentityV1(
      row.data(), row.size(), ReadFixtureMemory, &memory);
  assert(value.failure ==
         DomainConstructionCandidateDecodeFailureV1::identity_shape);
}

}  // namespace

int main() {
  TestBuildingCandidate();
  TestNewHoldingCandidate();
  TestTypedFailures();
  return 0;
}
