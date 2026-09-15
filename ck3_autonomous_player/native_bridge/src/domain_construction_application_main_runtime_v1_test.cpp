#include "domain_construction_application_main_runtime_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>

#include <windows.h>

namespace {

using namespace xar::ck3;
using namespace xar::ck3::research;
using namespace xar::ck3::shared;

inline constexpr std::uintptr_t kModuleBase = 0x140000000ULL;
inline constexpr std::uintptr_t kRow = 0x1000U;
inline constexpr std::uintptr_t kCost = 0x2000U;
inline constexpr std::uintptr_t kBalance = 0x3000U;
inline constexpr std::uintptr_t kHolding = 0x4000U;
inline constexpr std::uintptr_t kBuilding = 0x5000U;
inline constexpr std::uintptr_t kCandidate = 0x6000U;

struct Segment final {
  std::uintptr_t address = 0U;
  std::array<std::uint8_t, 64> bytes{};
  std::size_t size = 0U;
};

struct MemoryFixture final {
  std::array<Segment, 16> segments{};
  std::size_t count = 0U;
  std::uint32_t reads = 0U;
};

template <typename T>
void Add(MemoryFixture& memory, const std::uintptr_t address,
         const T& value) {
  assert(memory.count < memory.segments.size());
  assert(sizeof(value) <= memory.segments[0].bytes.size());
  auto& segment = memory.segments[memory.count++];
  segment.address = address;
  segment.size = sizeof(value);
  std::memcpy(segment.bytes.data(), &value, sizeof(value));
}

bool ReadMemory(void* context, const std::uintptr_t address, void* destination,
                const std::size_t bytes) {
  auto& memory = *static_cast<MemoryFixture*>(context);
  ++memory.reads;
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
void Put(std::array<std::uint8_t, 0x28>& row, const std::size_t offset,
         const T& value) {
  std::memcpy(row.data() + offset, &value, sizeof(value));
}

MemoryFixture CandidateMemory(const bool holding) {
  MemoryFixture memory{};
  std::array<std::uint8_t, 0x28> row{};
  Put(row, 0x00U, std::int32_t{holding ? 180 : 240});
  Put(row, 0x08U, kHolding);
  Put(row, 0x10U, kBuilding);
  Put(row, 0x18U, kCandidate);
  Put(row, 0x20U, std::int32_t{holding ? 3 : 4});
  row[0x24U] = 1U;
  const std::array<std::int64_t, 8> cost{10, 0, -1, 0, 0, 0, 0, 0};
  const std::array<std::int64_t, 8> balance{100, 0, 9, 0, 0, 0, 0, 0};
  Add(memory, kRow, row);
  Add(memory, kCost, cost);
  Add(memory, kBalance, balance);
  Add(memory, kHolding + 0x10U, std::int32_t{holding ? -1 : 17});
  Add(memory, kBuilding + 0x10U,
      std::int32_t{holding ? -1 : 16777258});
  Add(memory, kCandidate + 0x10U, std::int32_t{holding ? 867 : -1});
  return memory;
}

DomainConstructionConcreteCandidateCaptureV1 Capture(const bool holding) {
  DomainConstructionConcreteCandidateCaptureV1 capture{};
  capture.expected_binding = {42U, 91U, 777};
  DomainConstructionBorrowedCollectorFrameV1 frame{};
  frame.observed_binding = capture.expected_binding;
  frame.candidate_row_address = kRow;
  frame.cost_vector_address = kCost;
  frame.resource_balance_vector_address = kBalance;
  frame.final_legality = {
      true, holding ? DomainConstructionNativeFinalLegalityBranchV1::new_holding
                    : DomainConstructionNativeFinalLegalityBranchV1::building,
      true};
  frame.new_holding_candidate_object = holding ? kCandidate : 0U;
  capture.first_publication = {frame, frame};
  capture.second_publication = {frame, frame};
  return capture;
}

struct NativeFixture final {
  std::uint32_t building_validations = 0U;
  std::uint32_t holding_validations = 0U;
  std::uint32_t materializations = 0U;
  std::uint32_t receives = 0U;
  std::uint32_t releases = 0U;
  bool saw_exact_layout = false;
};

template <typename T>
T ReadField(const void* command, const std::size_t offset) {
  T value{};
  std::memcpy(&value, static_cast<const std::byte*>(command) + offset,
              sizeof(value));
  return value;
}

bool ValidateBuilding(void* context, const void* command,
                      bool& allowed) noexcept {
  auto& fixture = *static_cast<NativeFixture*>(context);
  ++fixture.building_validations;
  fixture.saw_exact_layout =
      ReadField<std::uintptr_t>(command, 0x00U) ==
          kModuleBase + kDomainConstructionBuildingPrimaryVtableRvaV1 &&
      ReadField<std::uintptr_t>(command, 0x18U) ==
          kModuleBase + kDomainConstructionBuildingSecondaryVtableRvaV1 &&
      ReadField<std::int32_t>(command, 0x20U) == 1337 &&
      ReadField<std::int32_t>(command, 0x24U) == 17 &&
      ReadField<std::int32_t>(command, 0x28U) == 4 &&
      ReadField<std::int32_t>(command, 0x2CU) == 16777258;
  allowed = fixture.saw_exact_layout;
  return true;
}

bool ValidateHolding(void* context, const void* command,
                     const std::int32_t province,
                     const std::int32_t selector,
                     const std::uintptr_t candidate,
                     bool& allowed) noexcept {
  auto& fixture = *static_cast<NativeFixture*>(context);
  ++fixture.holding_validations;
  fixture.saw_exact_layout =
      ReadField<std::uintptr_t>(command, 0x00U) ==
          kModuleBase + kDomainConstructionHoldingPrimaryVtableRvaV1 &&
      ReadField<std::uintptr_t>(command, 0x18U) ==
          kModuleBase + kDomainConstructionHoldingSecondaryVtableRvaV1 &&
      ReadField<std::int32_t>(command, 0x20U) == 1337 &&
      ReadField<std::int32_t>(command, 0x24U) == 3 &&
      ReadField<std::uintptr_t>(command, 0x28U) == kCandidate &&
      province == 867 && selector == 3 && candidate == kCandidate;
  allowed = fixture.saw_exact_layout;
  return true;
}

bool Materialize(void* context, void*,
                 std::uintptr_t& owned_command) noexcept {
  auto& fixture = *static_cast<NativeFixture*>(context);
  ++fixture.materializations;
  owned_command = 0xBEEFU;
  return true;
}

bool Receive(void* context, std::uintptr_t& owned_command,
             const std::uint32_t flags, bool& accepted,
             std::uint64_t& sequence) noexcept {
  auto& fixture = *static_cast<NativeFixture*>(context);
  ++fixture.receives;
  accepted = owned_command == 0xBEEFU && flags == 7U;
  sequence = accepted ? 7001U : 0U;
  owned_command = 0U;
  return true;
}

bool Release(void* context, std::uintptr_t& owned_command) noexcept {
  auto& fixture = *static_cast<NativeFixture*>(context);
  ++fixture.releases;
  owned_command = 0U;
  return true;
}

DomainConstructionExactNativeCallsV1 Calls(NativeFixture& fixture) {
  return {&fixture, false, ValidateBuilding, ValidateHolding, Materialize,
          Receive, Release};
}

xar::ck3_11906::MainThreadExecutionStampV1 Stamp() {
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 91U;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_context = 0xABCDU;
  stamp.tls_main_thread_marker = 1U;
  stamp.date_raw = 777;
  return stamp;
}

DomainConstructionApplicationMainResultV1 Run(const bool holding,
                                               MemoryFixture& memory,
                                               NativeFixture& native) {
  const std::array captures{Capture(holding)};
  DomainConstructionApplicationMainRequestV1 request{};
  request.exact_build_admitted = true;
  request.session_live = true;
  request.offline_fixture = true;
  request.module_base = kModuleBase;
  request.actor_or_holder_id = 1337;
  request.candidates = captures;
  request.read_memory = ReadMemory;
  request.read_context = &memory;
  request.native_calls = Calls(native);
  DomainConstructionApplicationMainResultV1 result{};
  DomainConstructionApplicationMainExecutionV1 execution{&request, &result};
  assert(ExecuteDomainConstructionApplicationMainRuntimeV1(&execution,
                                                            Stamp()));
  return result;
}

void TestBuildingCollectorAndBackend() {
  auto memory = CandidateMemory(false);
  NativeFixture native{};
  const auto result = Run(false, memory, native);
  assert(result.executor_completed);
  assert(result.collector_ready);
  assert(result.submit_accepted);
  assert(result.red_flags == domain_construction_application_main_red_none);
  assert(result.collected_candidate_count == 1U);
  assert(!result.shared.candidate_live);
  assert(result.shared.candidate.candidate_id == "building:17:4:16777258");
  assert(result.shared.phase ==
         DomainConstructionSharedPhaseV1::pending_receipt);
  assert(!result.shared.native_submit.production_native_path);
  assert(native.building_validations == 1U);
  assert(native.holding_validations == 0U);
  assert(native.materializations == 1U);
  assert(native.receives == 1U);
  assert(native.releases == 0U);
  assert(native.saw_exact_layout);
  assert(memory.reads >= 24U);
}

void TestHoldingCollectorRetainsBorrowedPointerOnlyForCall() {
  auto memory = CandidateMemory(true);
  NativeFixture native{};
  const auto result = Run(true, memory, native);
  assert(result.submit_accepted);
  assert(result.shared.candidate.candidate_id == "holding:867:3");
  assert(native.building_validations == 0U);
  assert(native.holding_validations == 1U);
  assert(native.saw_exact_layout);
  assert(result.shared.candidate.candidate_id.find("24576") ==
         std::string::npos);
}

void TestFourReadDriftPreservesRed() {
  auto memory = CandidateMemory(false);
  NativeFixture native{};
  auto capture = Capture(false);
  capture.second_publication[1].observed_binding.proof_epoch = 92U;
  const std::array captures{capture};
  DomainConstructionApplicationMainRequestV1 request{};
  request.exact_build_admitted = true;
  request.session_live = true;
  request.offline_fixture = true;
  request.module_base = kModuleBase;
  request.actor_or_holder_id = 1337;
  request.candidates = captures;
  request.read_memory = ReadMemory;
  request.read_context = &memory;
  request.native_calls = Calls(native);
  DomainConstructionApplicationMainResultV1 result{};
  DomainConstructionApplicationMainExecutionV1 execution{&request, &result};
  assert(ExecuteDomainConstructionApplicationMainRuntimeV1(&execution,
                                                            Stamp()));
  assert(!result.submit_accepted);
  assert((result.red_flags &
          domain_construction_application_main_red_collector) != 0U);
  assert(native.materializations == 0U);
  assert(native.receives == 0U);
}

void TestApplicationMainAdmissionAndCurrentBinding() {
  auto memory = CandidateMemory(false);
  NativeFixture native{};
  const std::array captures{Capture(false)};
  DomainConstructionApplicationMainRequestV1 request{};
  request.exact_build_admitted = true;
  request.session_live = true;
  request.offline_fixture = true;
  request.module_base = kModuleBase;
  request.actor_or_holder_id = 1337;
  request.candidates = captures;
  request.read_memory = ReadMemory;
  request.read_context = &memory;
  request.native_calls = Calls(native);
  DomainConstructionApplicationMainResultV1 result{};
  DomainConstructionApplicationMainExecutionV1 execution{&request, &result};
  auto stamp = Stamp();
  stamp.tls_main_thread_marker = 0U;
  assert(ExecuteDomainConstructionApplicationMainRuntimeV1(&execution, stamp));
  assert((result.red_flags & domain_construction_application_main_red_thread) !=
         0U);
  assert(native.building_validations == 0U);

  const auto production =
      BindCurrentProcessDomainConstructionExactNativeCallsV1(kModuleBase);
  assert(production.production_exact_addresses);
  assert(production.validate_building != nullptr);
  assert(production.validate_holding != nullptr);
  assert(production.materialize != nullptr);
  assert(production.receive != nullptr);
  assert(production.release != nullptr);
}

}  // namespace

int main() {
  TestBuildingCollectorAndBackend();
  TestHoldingCollectorRetainsBorrowedPointerOnlyForCall();
  TestFourReadDriftPreservesRed();
  TestApplicationMainAdmissionAndCurrentBinding();
  return 0;
}
