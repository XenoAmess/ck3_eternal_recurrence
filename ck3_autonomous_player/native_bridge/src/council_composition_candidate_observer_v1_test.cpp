#include "xar_bridge/council_composition_candidate_observer_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <atomic>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <initializer_list>
#include <iterator>
#include <string>
#include <string_view>

namespace {

using xar::bridge::CouncilCompositionCandidateObserverEnvironmentV1;
using xar::bridge::CouncilCompositionCandidateObserverStateV1;

std::string ReadAll(const char *path) {
  std::ifstream input(path, std::ios::binary);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

bool ContainsAll(std::string_view value,
                 std::initializer_list<std::string_view> tokens) {
  for (const auto token : tokens) {
    if (value.find(token) == std::string_view::npos) return false;
  }
  return true;
}

constexpr std::array<std::uint8_t, 15> kAnchor{
    0x4C, 0x8D, 0x4D, 0x80, 0x41, 0xB0, 0x01, 0x49,
    0x8B, 0xD2, 0xE8, 0xF1, 0x3A, 0x8E, 0x01};

struct FixtureMemory {
  std::array<std::uint8_t, 15> target{kAnchor};
  std::array<std::uint8_t,
             xar::bridge::kCouncilCompositionCandidateObserverStubCapacityV1>
      stub{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
  bool fail_target_flush_once = false;
  bool target_flush_failed = false;
};

void *FixtureAlloc(void *context, std::size_t size, DWORD, DWORD) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(context);
  if (size != fixture.stub.size() || fixture.allocation_count != 0) return nullptr;
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
      ? PAGE_READWRITE : PAGE_EXECUTE_READ;
  return true;
}

bool FixtureFlush(void *context, const void *address, std::size_t) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(context);
  if (fixture.fail_target_flush_once && !fixture.target_flush_failed &&
      address == fixture.target.data()) {
    fixture.target_flush_failed = true;
    return false;
  }
  return true;
}

CouncilCompositionCandidateObserverEnvironmentV1 Environment(
    FixtureMemory &fixture, const std::atomic<std::uint32_t> &ui_thread,
    const std::atomic<bool> &paused) {
  CouncilCompositionCandidateObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.ui_thread_id_source = &ui_thread;
  environment.paused_source = &paused;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(fixture.target.data());
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(fixture.target.data() +
                                       fixture.target.size());
  environment.producer_target_override = 0x123456789ABCDEF0ULL;
  environment.memory_context = &fixture;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
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

template <std::size_t Size, typename Value>
void Put(std::array<std::uint8_t, Size> &bytes, std::size_t offset,
         const Value &value) {
  assert(offset + sizeof(value) <= bytes.size());
  std::memcpy(bytes.data() + offset, &value, sizeof(value));
}

struct CaptureFixture {
  std::array<std::uint8_t, 0x40> owner{};
  std::array<std::uint8_t, 0x60> task{};
  std::array<std::uint8_t, 0x60> task_type{};
  std::array<std::uint8_t, 0x60> position_type{};
  std::array<char, 32> position_key{};
  std::array<std::uint8_t, 0x40> candidate_a{};
  std::array<std::uint8_t, 0x40> candidate_b{};
  std::array<std::uintptr_t, 2> rows{};
  struct Vector { std::uintptr_t data; std::int32_t capacity; std::int32_t count; }
      vector{};

  CaptureFixture() {
    const std::uint32_t owner_id = 0x81001234U;
    const std::uint32_t task_id = 0x02005678U;
    const std::uint32_t a_id = 0x81000001U;
    const std::uint32_t b_id = 0x81000002U;
    Put(owner, 0x18, owner_id);
    Put(task, 0x10, task_id);
    const auto task_type_pointer =
        reinterpret_cast<std::uintptr_t>(task_type.data());
    const auto position_type_pointer =
        reinterpret_cast<std::uintptr_t>(position_type.data());
    Put(task, 0x18, task_type_pointer);
    Put(task_type, 0x38, position_type_pointer);
    constexpr std::string_view key = "councillor_steward";
    const auto key_data = reinterpret_cast<std::uintptr_t>(position_key.data());
    std::memcpy(position_key.data(), key.data(), key.size());
    Put(position_type, 0x18, key_data);
    const std::uint64_t key_size = key.size();
    const std::uint64_t key_capacity = 31;
    Put(position_type, 0x28, key_size);
    Put(position_type, 0x30, key_capacity);
    Put(candidate_a, 0x18, a_id);
    Put(candidate_b, 0x18, b_id);
    rows = {reinterpret_cast<std::uintptr_t>(candidate_a.data()),
            reinterpret_cast<std::uintptr_t>(candidate_b.data())};
    vector = {reinterpret_cast<std::uintptr_t>(rows.data()), 2, 2};
  }
};

void BindCaptureSources(CouncilCompositionCandidateObserverStateV1 &state,
                        const std::atomic<std::uint32_t> &ui_thread,
                        const std::atomic<bool> &paused) {
  state.ui_thread_id_source = &ui_thread;
  state.paused_source = &paused;
}

void TestDefaultOffAndInstallGuards() {
  static_assert(!xar::bridge::
      kCouncilCompositionCandidateObserverInstalledByDefaultV1);
  CouncilCompositionCandidateObserverStateV1 state{};
  CouncilCompositionCandidateObserverEnvironmentV1 environment{};
  assert(!xar::bridge::InstallCouncilCompositionCandidateObserverV1(
      state, environment));
  const auto diagnostics = xar::bridge::
      ReadCouncilCompositionCandidateObserverDiagnosticsV1(state);
  assert((diagnostics.failure_flags & xar::bridge::
      council_composition_candidate_observer_failure_exact_build) != 0);
}

void TestPausedUiThreadCaptureCopiesRowsOnce() {
  std::atomic<std::uint32_t> ui_thread{77};
  std::atomic<bool> paused{true};
  CouncilCompositionCandidateObserverStateV1 state{};
  BindCaptureSources(state, ui_thread, paused);
  CaptureFixture fixture{};
  assert(xar::bridge::CaptureCouncilCompositionCandidatePostCallV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.owner.data()),
      reinterpret_cast<std::uintptr_t>(fixture.task.data()),
      reinterpret_cast<std::uintptr_t>(&fixture.vector), 77, 9001));
  std::fill(fixture.candidate_a.begin(), fixture.candidate_a.end(),
            std::uint8_t{0});
  const auto diagnostics = xar::bridge::
      ReadCouncilCompositionCandidateObserverDiagnosticsV1(state);
  const auto &capture = diagnostics.observation;
  assert(capture.capture_consistent && capture.capture_complete);
  assert(capture.accepted_count == 1 && capture.last_captured_row_count == 2);
  assert(capture.last_owner_character_id == 0x81001234U);
  assert(capture.last_active_task_id == 0x02005678U);
  assert(std::string_view(capture.last_position_key.data()) ==
         "councillor_steward");
  assert(capture.rows[0].character_id == 0x81000001U);
  assert(capture.rows[0].raw_row_bytes == fixture.rows[0]);
  assert(!xar::bridge::CaptureCouncilCompositionCandidatePostCallV1(
      state, 1, 1, 1, 77, 9002));
  assert(xar::bridge::ReadCouncilCompositionCandidateObserverDiagnosticsV1(
      state).observation.ignored_after_capture_count == 1);
}

void TestCaptureGatesRejectWrongThreadAndInvalidSpan() {
  std::atomic<std::uint32_t> ui_thread{77};
  std::atomic<bool> paused{false};
  CouncilCompositionCandidateObserverStateV1 state{};
  BindCaptureSources(state, ui_thread, paused);
  CaptureFixture fixture{};
  assert(!xar::bridge::CaptureCouncilCompositionCandidatePostCallV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.owner.data()),
      reinterpret_cast<std::uintptr_t>(fixture.task.data()),
      reinterpret_cast<std::uintptr_t>(&fixture.vector), 88, 1));
  auto failure = xar::bridge::
      ReadCouncilCompositionCandidateObserverDiagnosticsV1(state).
          observation.last_capture_failure_flags;
  assert((failure & xar::bridge::
      council_composition_candidate_capture_failure_wrong_thread) != 0);
  assert((failure & xar::bridge::
      council_composition_candidate_capture_failure_not_paused) != 0);
  paused.store(true);
  fixture.vector.count = 257;
  fixture.vector.capacity = 257;
  assert(!xar::bridge::CaptureCouncilCompositionCandidatePostCallV1(
      state, reinterpret_cast<std::uintptr_t>(fixture.owner.data()),
      reinterpret_cast<std::uintptr_t>(fixture.task.data()),
      reinterpret_cast<std::uintptr_t>(&fixture.vector), 77, 2));
  failure = xar::bridge::
      ReadCouncilCompositionCandidateObserverDiagnosticsV1(state).
          observation.last_capture_failure_flags;
  assert((failure & xar::bridge::
      council_composition_candidate_capture_failure_invalid_span) != 0);
}

void TestInstallTrampolineAndRollback() {
  std::atomic<std::uint32_t> ui_thread{77};
  std::atomic<bool> paused{true};
  FixtureMemory fixture{};
  CouncilCompositionCandidateObserverStateV1 state{};
  const auto environment = Environment(fixture, ui_thread, paused);
  assert(xar::bridge::InstallCouncilCompositionCandidateObserverV1(
      state, environment));
  assert(fixture.target[0] == 0xFF && fixture.target[1] == 0x25);
  assert(ContainsU64(fixture.stub, environment.producer_target_override));
  assert(ContainsU64(fixture.stub, environment.continue_target_override));
  assert(xar::bridge::UninstallCouncilCompositionCandidateObserverV1(state));
  assert(std::equal(kAnchor.begin(), kAnchor.end(), fixture.target.begin()));
  assert(fixture.free_count == 1);

  FixtureMemory failed_fixture{};
  failed_fixture.fail_target_flush_once = true;
  CouncilCompositionCandidateObserverStateV1 failed_state{};
  assert(!xar::bridge::InstallCouncilCompositionCandidateObserverV1(
      failed_state, Environment(failed_fixture, ui_thread, paused)));
  assert(std::equal(kAnchor.begin(), kAnchor.end(),
                    failed_fixture.target.begin()));
}

void TestSerializerMatchesCaptureFixture(const char *fixture_path) {
  xar::bridge::CouncilCompositionCandidateObserverDiagnosticsV1 diagnostics{};
  diagnostics.installed = true;
  auto &capture = diagnostics.observation;
  capture.capture_consistent = true;
  capture.capture_complete = true;
  capture.call_count = 1;
  capture.accepted_count = 1;
  capture.last_ui_thread_id = 77;
  capture.last_thread_id = 77;
  capture.last_timestamp_qpc = 9001;
  capture.last_owner_character_id = 2164265524U;
  capture.last_active_task_id = 33576568U;
  std::memcpy(capture.last_position_key.data(), "councillor_steward", 19);
  capture.last_vector_capacity = 2;
  capture.last_vector_count = 2;
  capture.last_captured_row_count = 2;
  capture.rows[0] = {2164260865U, 0x1111222233334444ULL};
  capture.rows[1] = {2164260866U, 0x5555666677778888ULL};
  const auto json = xar::bridge::
      SerializeCouncilCompositionCandidateObserverDiagnosticsV1(diagnostics);
  assert(json.find("\"private_build\":true") != std::string::npos);
  assert(json.find("\"advertised\":false") != std::string::npos);
  assert(json.find("1111222233334444") != std::string::npos);
  assert(json.find("candidate_pointer") == std::string::npos);
  std::ifstream input(fixture_path, std::ios::binary);
  std::string expected{std::istreambuf_iterator<char>(input),
                       std::istreambuf_iterator<char>()};
  while (!expected.empty() &&
         (expected.back() == '\n' || expected.back() == '\r')) {
    expected.pop_back();
  }
  assert(!expected.empty());
  assert(json == expected);
}

void TestSourceContract(char **argv) {
  const auto header = ReadAll(argv[2]);
  const auto source = ReadAll(argv[3]);
  const auto bridge = ReadAll(argv[4]);
  const auto cmake = ReadAll(argv[5]);
  const auto abi = ReadAll(argv[6]);
  const auto source_fixture = ReadAll(argv[7]);
  assert(ContainsAll(header,
      {"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86",
       "0x1058200", "0x105820A", "0x105820F", "0x293BD00",
       "InstalledByDefaultV1 = false", "ui_thread_id_source",
       "paused_source", "last_raw_row_bytes"}));
  assert(ContainsAll(source,
      {"kPatchAnchor", "CaptureCouncilCompositionCandidatePostCallV1",
       "council_composition_candidate_capture_failure_wrong_thread",
       "council_composition_candidate_capture_failure_not_paused",
       "kCouncilCompositionCandidateObserverMaxNativeCapacityV1",
       "last_character_ids", "last_raw_row_bytes"}));
  assert(ContainsAll(bridge,
      {"XAR_CK3_ENABLE_COUNCIL_COMPOSITION_CANDIDATE_OBSERVER_V1",
       "g_main_thread_query_mailbox_v1.owner_thread_id",
       "g_main_thread_query_mailbox_v1.observed_paused",
       "SerializeCouncilCompositionCandidateObserverDiagnosticsV1"}));
  assert(ContainsAll(cmake,
      {"XAR_CK3_ENABLE_COUNCIL_COMPOSITION_CANDIDATE_OBSERVER_V1",
       "private exact-build paused council-candidate observer",
       "council_composition_candidate_observer_v1_test"}));
  assert(ContainsAll(abi,
      {"private-default-off", "4C8D4D8041B001498BD2E8F13A8E01",
       "E7D1A1C2A2ABF7D62478C06FFF7D592FE0CF7682F8CF53D84D90EFE8545B748A",
       "A2264828FA0A077650A1D74DD3C9861F81B7C219BC9D32DE7C11369BF6E890D8"}));
  assert(ContainsAll(source_fixture,
      {"\"default\": \"OFF\"", "same_frame_id_and_row_copy",
       "no_cross_frame_native_pointer"}));
  const std::string production_surface = header + source + bridge + cmake;
  assert(production_surface.find(
      "game.query.council-composition-candidates-v1") == std::string::npos);
}

} // namespace

int main(int argc, char **argv) {
  assert(argc == 8);
  TestDefaultOffAndInstallGuards();
  TestPausedUiThreadCaptureCopiesRowsOnce();
  TestCaptureGatesRejectWrongThreadAndInvalidSpan();
  TestInstallTrampolineAndRollback();
  TestSerializerMatchesCaptureFixture(argv[1]);
  TestSourceContract(argv);
  return 0;
}
