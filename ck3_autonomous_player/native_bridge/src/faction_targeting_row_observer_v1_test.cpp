#include "xar_bridge/faction_targeting_row_observer_v1.hpp"
#include "xar_bridge/faction_targeting_row_observer_v1_serializer.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>

namespace {

using xar::bridge::FactionTargetingRowCaptureAdmissionV1;
using xar::bridge::FactionTargetingRowObserverEnvironmentV1;
using xar::bridge::FactionTargetingRowObserverStateV1;

constexpr std::array<std::uint8_t, 15> kAnchor{
    0xE8, 0x7D, 0x98, 0xBD, 0xFF,
    0x48, 0x89, 0x44, 0x24, 0x20,
    0x48, 0x8D, 0x54, 0x24, 0x30};

struct AdmissionFixture {
  FactionTargetingRowCaptureAdmissionV1 value{};
  bool readable = true;
  bool drift_on_second = false;
  std::size_t calls = 0;
};

bool ReadAdmission(
    void *context,
    FactionTargetingRowCaptureAdmissionV1 &output) noexcept {
  auto &fixture = *static_cast<AdmissionFixture *>(context);
  ++fixture.calls;
  if (!fixture.readable) return false;
  output = fixture.value;
  if (fixture.drift_on_second && fixture.calls == 2) {
    ++output.snapshot_revision;
  }
  return true;
}

struct FixtureMemory {
  std::array<std::uint8_t, 15> target{kAnchor};
  std::array<std::uint8_t,
             xar::bridge::kFactionTargetingRowObserverStubCapacityV1>
      stub{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
  std::size_t read_count = 0;
};

bool FixtureRead(void *context, std::uintptr_t address, void *output,
                 std::size_t size) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(context);
  ++fixture.read_count;
  if (address == 0 || output == nullptr || size == 0) return false;
  std::memcpy(output, reinterpret_cast<const void *>(address), size);
  return true;
}

bool FixtureWrite(void *, std::uintptr_t address, const void *source,
                  std::size_t size) noexcept {
  if (address == 0 || source == nullptr || size == 0) return false;
  std::memcpy(reinterpret_cast<void *>(address), source, size);
  return true;
}

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

struct ResolvedFactionFixture {
  std::array<std::uint8_t, 0x10> prefix{};
  std::uint32_t faction_id = 0;
};

static_assert(offsetof(ResolvedFactionFixture, faction_id) == 0x10);

struct ResolverFixture {
  std::array<ResolvedFactionFixture, 3> factions{};
  bool fail = false;
};

bool ResolveIdentity(void *context, std::uint32_t faction_id,
                     std::uintptr_t &resolved) noexcept {
  auto &fixture = *static_cast<ResolverFixture *>(context);
  resolved = 0;
  if (fixture.fail) return false;
  for (auto &faction : fixture.factions) {
    if (faction.faction_id == faction_id) {
      resolved = reinterpret_cast<std::uintptr_t>(&faction);
      return true;
    }
  }
  return false;
}

FactionTargetingRowObserverEnvironmentV1 Environment(
    FixtureMemory &memory, AdmissionFixture &admission,
    ResolverFixture &resolver) {
  FactionTargetingRowObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      xar::bridge::kFactionTargetingRowObserverExecutableSha256V1;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(memory.target.data());
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(memory.target.data() +
                                       memory.target.size());
  environment.original_getter_target_override = 0x123456789ABCDEF0ULL;
  environment.identity_resolver_target_override = 0x0FEDCBA987654321ULL;
  environment.memory_context = &memory;
  environment.memory_read_override = &FixtureRead;
  environment.memory_write_override = &FixtureWrite;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
  environment.capture_admission_context = &admission;
  environment.capture_admission_probe = &ReadAdmission;
  environment.identity_resolver_context = &resolver;
  environment.identity_resolver_override = &ResolveIdentity;
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

struct FactionRowFixture {
  std::uint32_t faction_id = 0;
  std::array<std::uint8_t, 20> opaque{};
};

static_assert(sizeof(FactionRowFixture) == 0x18);

struct TargetingContainerFixture {
  std::uintptr_t row_data = 0;
  std::uint32_t unresolved_word_at_0x08 = 0;
  std::int32_t count = 0;
};

static_assert(sizeof(TargetingContainerFixture) == 16);

void TestDefaultOffAndExactHashGuard() {
  static_assert(!xar::bridge::kFactionTargetingRowObserverInstalledByDefaultV1);
  FactionTargetingRowObserverStateV1 state{};
  FactionTargetingRowObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      "0000000000000000000000000000000000000000000000000000000000000000";
  assert(!xar::bridge::InstallFactionTargetingRowObserverV1(state,
                                                            environment));
  const auto diagnostics =
      xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert((diagnostics.failure_flags &
          xar::bridge::faction_targeting_row_observer_failure_exact_build) !=
         0);
}

std::string TestAdmissionBeforeReadAndStableIdentityCapture() {
  FixtureMemory memory{};
  AdmissionFixture admission{};
  admission.value = {77, true, 42, 412, 777, 29829};
  ResolverFixture resolver{};
  resolver.factions[0].faction_id = 42;
  resolver.factions[1].faction_id = 7;
  FactionTargetingRowObserverStateV1 state{};
  const auto environment = Environment(memory, admission, resolver);
  assert(xar::bridge::InstallFactionTargetingRowObserverV1(state,
                                                           environment));
  assert(memory.target[0] == 0xFF && memory.target[1] == 0x25);
  assert(ContainsU64(memory.stub,
                     environment.original_getter_target_override));
  assert(ContainsU64(memory.stub, environment.continue_target_override));

  const auto reads_after_install = memory.read_count;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(state, 1, 76, 1000));
  assert(memory.read_count == reads_after_install);
  admission.value.paused = false;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(state, 1, 77, 1001));
  assert(memory.read_count == reads_after_install);
  admission.value.paused = true;

  std::array<FactionRowFixture, 2> rows{{{42, {}}, {7, {}}}};
  TargetingContainerFixture container{
      reinterpret_cast<std::uintptr_t>(rows.data()), 0xA5A5A5A5U, 2};
  assert(xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 77, 1002));

  const auto diagnostics =
      xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  const auto &capture = diagnostics.observation;
  assert(capture.callback_count == 3);
  assert(capture.rejected_application_main_count == 1);
  assert(capture.rejected_paused_count == 1);
  assert(capture.accepted_capture_count == 1);
  assert(capture.published_generation == 2);
  assert(capture.last_proof_epoch == 42);
  assert(capture.last_snapshot_revision == 412);
  assert(capture.last_date_raw == 777);
  assert(capture.last_player_character_id == 29829);
  assert(capture.last_faction_count == 2);
  assert(capture.last_faction_ids[0] == 7);
  assert(capture.last_faction_ids[1] == 42);

  const std::string serialized =
      xar::bridge::SerializeFactionTargetingRowObserverV1(diagnostics);
  assert(serialized.find("\"faction_ids\":[7,42]") != std::string::npos);
  assert(serialized.find("\"raw_pointer_fields_persisted\":false") !=
         std::string::npos);
  assert(serialized.find("\"raw_row_bytes_persisted\":false") !=
         std::string::npos);
  assert(serialized.find(std::to_string(
             reinterpret_cast<std::uintptr_t>(&rows[0]))) ==
         std::string::npos);
  assert(serialized.find(std::to_string(container.row_data)) ==
         std::string::npos);

  assert(xar::bridge::UninstallFactionTargetingRowObserverV1(state));
  assert(std::equal(kAnchor.begin(), kAnchor.end(), memory.target.begin()));
  assert(memory.free_count == 1);
  return serialized;
}

void TestTransactionalRejectionKeepsPreviousGeneration() {
  FixtureMemory memory{};
  AdmissionFixture admission{};
  admission.value = {12, true, 9, 99, 1234, 29829};
  ResolverFixture resolver{};
  resolver.factions[0].faction_id = 11;
  FactionTargetingRowObserverStateV1 state{};
  assert(xar::bridge::InstallFactionTargetingRowObserverV1(
      state, Environment(memory, admission, resolver)));

  FactionRowFixture row{11, {}};
  TargetingContainerFixture container{
      reinterpret_cast<std::uintptr_t>(&row), 0xFFFFFFFFU, 1};
  assert(xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2000));
  auto before =
      xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(before.observation.published_generation == 2);

  resolver.fail = true;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2001));
  auto after =
      xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.last_faction_ids[0] == 11);

  resolver.fail = false;
  admission.calls = 0;
  admission.drift_on_second = true;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&container), 12, 2002));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.rejected_state_change_count == 1);

  TargetingContainerFixture oversized{0, 0, 65};
  admission.calls = 0;
  admission.drift_on_second = false;
  assert(!xar::bridge::CaptureFactionTargetingRowsV1(
      state, reinterpret_cast<std::uintptr_t>(&oversized), 12, 2003));
  after = xar::bridge::ReadFactionTargetingRowObserverDiagnosticsV1(state);
  assert(after.observation.published_generation == 2);
  assert(after.observation.span_read_failure_count == 1);
  assert(xar::bridge::UninstallFactionTargetingRowObserverV1(state));
}

void CheckFixture(const std::string &actual, const char *path) {
  if (path == nullptr) return;
  std::ifstream input(path, std::ios::binary);
  assert(input.good());
  const std::string expected{std::istreambuf_iterator<char>(input),
                             std::istreambuf_iterator<char>()};
  assert(actual == expected);
}

} // namespace

int main(int argc, char **argv) {
  TestDefaultOffAndExactHashGuard();
  const auto serialized = TestAdmissionBeforeReadAndStableIdentityCapture();
  TestTransactionalRejectionKeepsPreviousGeneration();
  CheckFixture(serialized, argc > 1 ? argv[1] : nullptr);
  if (argc == 1) std::cout << serialized;
  return 0;
}
