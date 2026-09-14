#include "xar_bridge/domain_construction_candidate_observer_v1.hpp"
#include "xar_bridge/domain_construction_candidate_observer_v1_serializer.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>

namespace {

using xar::bridge::DomainConstructionCandidateCaptureAdmissionV1;
using xar::bridge::DomainConstructionCandidateObserverEnvironmentV1;
using xar::bridge::DomainConstructionCandidateObserverStateV1;
using xar::bridge::DomainConstructionCandidateRawRowV1;

constexpr std::array<std::uint8_t, 17> kAnchor{
    0x48, 0x8D, 0x54, 0x24, 0x40,
    0xE8, 0x85, 0x29, 0xA6, 0xFE,
    0x48, 0x8B, 0x05, 0x16, 0x0D, 0x90, 0x02};

struct AdmissionFixture {
  bool readable = true;
  DomainConstructionCandidateCaptureAdmissionV1 value{};
};

bool ReadAdmission(
    void *context,
    DomainConstructionCandidateCaptureAdmissionV1 &output) noexcept {
  const auto &fixture = *static_cast<AdmissionFixture *>(context);
  if (!fixture.readable) return false;
  output = fixture.value;
  return true;
}

struct FixtureMemory {
  std::array<std::uint8_t, 17> target{kAnchor};
  std::array<std::uint8_t,
             xar::bridge::
                 kDomainConstructionCandidateObserverStubCapacityV1>
      stub{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
};

void *FixtureAlloc(void *context, std::size_t size, DWORD, DWORD) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(context);
  if (size != fixture.stub.size() || fixture.allocation_count != 0) {
    return nullptr;
  }
  ++fixture.allocation_count;
  return fixture.stub.data();
}

bool FixtureFree(void *context, void *, std::size_t, DWORD) noexcept {
  ++static_cast<FixtureMemory *>(context)->free_count;
  return true;
}

bool FixtureProtect(void *, void *, std::size_t, DWORD new_protection,
                    DWORD &old_protection) noexcept {
  old_protection = new_protection == PAGE_EXECUTE_READ
      ? PAGE_READWRITE
      : PAGE_EXECUTE_READ;
  return true;
}

bool FixtureFlush(void *, const void *, std::size_t) noexcept {
  return true;
}

DomainConstructionCandidateObserverEnvironmentV1 Environment(
    FixtureMemory &memory, AdmissionFixture &admission) {
  DomainConstructionCandidateObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 = xar::bridge::
      kDomainConstructionCandidateObserverExecutableSha256V1;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(memory.target.data());
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(memory.target.data() +
                                       memory.target.size());
  environment.producer_target_override = 0x123456789ABCDEF0ULL;
  environment.post_call_global_slot_target_override =
      0x0FEDCBA987654321ULL;
  environment.memory_context = &memory;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
  environment.capture_admission_context = &admission;
  environment.capture_admission_probe = &ReadAdmission;
  return environment;
}

template <std::size_t Size>
bool ContainsU64(const std::array<std::uint8_t, Size> &bytes,
                 std::uint64_t value) {
  std::array<std::uint8_t, sizeof(value)> encoded{};
  std::memcpy(encoded.data(), &value, sizeof(value));
  return std::search(bytes.begin(), bytes.end(), encoded.begin(),
                     encoded.end()) != bytes.end();
}

struct NativeVectorFixture {
  std::uintptr_t data = 0;
  std::int32_t capacity = 0;
  std::int32_t count = 0;
};

static_assert(sizeof(NativeVectorFixture) == 16);

void SetScore(DomainConstructionCandidateRawRowV1 &row,
              std::int64_t score) {
  std::memcpy(row.bytes.data(), &score, sizeof(score));
}

void TestDefaultOffAndExactHashGuard() {
  static_assert(!xar::bridge::
      kDomainConstructionCandidateObserverInstalledByDefaultV1);
  DomainConstructionCandidateObserverStateV1 state{};
  DomainConstructionCandidateObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      "0000000000000000000000000000000000000000000000000000000000000000";
  assert(!xar::bridge::InstallDomainConstructionCandidateObserverV1(
      state, environment));
  const auto diagnostics = xar::bridge::
      ReadDomainConstructionCandidateObserverDiagnosticsV1(state);
  assert((diagnostics.failure_flags & xar::bridge::
          domain_construction_candidate_observer_failure_exact_build) != 0);
}

void TestPausedApplicationMainGateAndFullRawCopy(
    const char *expected_fixture_path) {
  FixtureMemory memory{};
  AdmissionFixture admission{};
  admission.value.application_main_thread_id = 77;
  admission.value.paused = true;
  admission.value.proof_epoch = 42;
  admission.value.date_raw = 777;
  DomainConstructionCandidateObserverStateV1 state{};
  assert(xar::bridge::InstallDomainConstructionCandidateObserverV1(
      state, Environment(memory, admission)));

  assert(!xar::bridge::CaptureDomainConstructionCandidatePostCallV1(
      state, 0, 76, 1000));
  admission.value.paused = false;
  assert(!xar::bridge::CaptureDomainConstructionCandidatePostCallV1(
      state, 0, 77, 1001));
  admission.value.paused = true;

  std::array<DomainConstructionCandidateRawRowV1, 2> rows{};
  for (std::size_t index = 8; index < rows[0].bytes.size(); ++index) {
    rows[0].bytes[index] = static_cast<std::uint8_t>(0x10 + index);
    rows[1].bytes[index] = static_cast<std::uint8_t>(0x80 + index);
  }
  SetScore(rows[0], 100);
  SetScore(rows[1], -25);
  NativeVectorFixture vector{
      reinterpret_cast<std::uintptr_t>(rows.data()), 4, 2};
  assert(xar::bridge::CaptureDomainConstructionCandidatePostCallV1(
      state, reinterpret_cast<std::uintptr_t>(&vector), 77, 1002));

  const auto diagnostics = xar::bridge::
      ReadDomainConstructionCandidateObserverDiagnosticsV1(state);
  const auto &capture = diagnostics.observation;
  assert(capture.producer_call_count == 3);
  assert(capture.rejected_application_main_count == 1);
  assert(capture.rejected_paused_count == 1);
  assert(capture.capture_read_failure_count == 0);
  assert(capture.accepted_capture_count == 1);
  assert(capture.published_generation == 2);
  assert(capture.last_proof_epoch == 42);
  assert(capture.last_date_raw == 777);
  assert(capture.last_vector_capacity == 4);
  assert(capture.last_vector_count == 2);
  assert(capture.last_captured_row_count == 2);
  assert(!capture.last_rows_truncated);
  assert(capture.rows[0].score_raw == 100);
  assert(capture.rows[1].score_raw == -25);
  assert(capture.rows[0].row_bytes == rows[0].bytes);
  assert(capture.rows[1].row_bytes == rows[1].bytes);

  const std::string serialized = xar::bridge::
      SerializeDomainConstructionCandidateObserverV1(diagnostics);
  assert(serialized.find("\"row_bytes_hex\":") != std::string::npos);
  assert(serialized.find("\"raw_pointer_fields_persisted\":false") !=
         std::string::npos);
  assert(serialized.find(std::string(xar::bridge::
      kDomainConstructionCandidateObserverNextReverseEngineeringEntryV1)) !=
         std::string::npos);
  if (expected_fixture_path != nullptr) {
    std::ifstream input(expected_fixture_path, std::ios::binary);
    assert(input.good());
    const std::string expected{
        std::istreambuf_iterator<char>(input),
        std::istreambuf_iterator<char>()};
    assert(serialized == expected);
  }

  assert(xar::bridge::UninstallDomainConstructionCandidateObserverV1(state));
  assert(std::equal(kAnchor.begin(), kAnchor.end(), memory.target.begin()));
}

void TestExactTrampolineAndBoundedRows() {
  FixtureMemory memory{};
  AdmissionFixture admission{};
  admission.value = {12, true, 99, 1234};
  DomainConstructionCandidateObserverStateV1 state{};
  const auto environment = Environment(memory, admission);
  assert(xar::bridge::InstallDomainConstructionCandidateObserverV1(
      state, environment));
  assert(memory.target[0] == 0xFF && memory.target[1] == 0x25);
  assert(ContainsU64(memory.stub, environment.producer_target_override));
  assert(ContainsU64(memory.stub,
                     environment.post_call_global_slot_target_override));
  assert(ContainsU64(memory.stub, environment.continue_target_override));

  std::array<DomainConstructionCandidateRawRowV1, 70> rows{};
  for (std::size_t index = 0; index < rows.size(); ++index) {
    SetScore(rows[index], static_cast<std::int64_t>(index));
    rows[index].bytes[39] = static_cast<std::uint8_t>(index);
  }
  NativeVectorFixture vector{
      reinterpret_cast<std::uintptr_t>(rows.data()), 70, 70};
  assert(xar::bridge::CaptureDomainConstructionCandidatePostCallV1(
      state, reinterpret_cast<std::uintptr_t>(&vector), 12, 2000));
  const auto diagnostics = xar::bridge::
      ReadDomainConstructionCandidateObserverDiagnosticsV1(state);
  assert(diagnostics.observation.last_vector_count == 70);
  assert(diagnostics.observation.last_captured_row_count == 64);
  assert(diagnostics.observation.last_rows_truncated);
  assert(diagnostics.observation.rows[63].score_raw == 63);
  assert(diagnostics.observation.rows[63].row_bytes[39] == 63);
  assert(xar::bridge::UninstallDomainConstructionCandidateObserverV1(state));
  assert(memory.free_count == 1);
}

} // namespace

int main(int argc, char **argv) {
  TestDefaultOffAndExactHashGuard();
  TestPausedApplicationMainGateAndFullRawCopy(argc > 1 ? argv[1] : nullptr);
  TestExactTrampolineAndBoundedRows();
  return 0;
}
