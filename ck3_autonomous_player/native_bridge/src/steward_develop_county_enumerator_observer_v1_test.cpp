#include "xar_bridge/steward_develop_county_enumerator_observer_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string_view>

namespace {

using xar::bridge::StewardDevelopCountyEnumeratorObserverEnvironmentV1;
using xar::bridge::StewardDevelopCountyEnumeratorObserverStateV1;
using xar::bridge::StewardDevelopCountyEnumeratorRawRowV1;

constexpr std::array<std::uint8_t, 24> kAnchor{
    0x41, 0x0F, 0x11, 0x01,
    0x89, 0x87, 0x0C, 0x01, 0x00, 0x00,
    0x41, 0x0F, 0x11, 0x49, 0x10,
    0x88, 0x44, 0x24, 0x20,
    0xE8, 0xFF, 0x53, 0x00, 0x00};

struct FixtureMemory {
  std::array<std::uint8_t, 24> target{kAnchor};
  std::array<std::uint8_t,
             xar::bridge::
                 kStewardDevelopCountyEnumeratorObserverStubCapacityV1>
      stub{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
  bool fail_target_flush_once = false;
  bool target_flush_failed = false;
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

bool FixtureFlush(void *context, const void *address, std::size_t) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(context);
  if (fixture.fail_target_flush_once && !fixture.target_flush_failed &&
      address == fixture.target.data()) {
    fixture.target_flush_failed = true;
    return false;
  }
  return true;
}

StewardDevelopCountyEnumeratorObserverEnvironmentV1 Environment(
    FixtureMemory &fixture) {
  StewardDevelopCountyEnumeratorObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(fixture.target.data());
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(fixture.target.data() +
                                       fixture.target.size());
  environment.enumerator_target_override = 0x123456789ABCDEF0ULL;
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

struct NativeTaskTypeFixture {
  std::array<std::uint8_t, 0x50> object{};
  std::array<char, 64> external_key{};
};

void SetTaskKey(NativeTaskTypeFixture &fixture, std::string_view key) {
  constexpr std::size_t key_offset = 0x18;
  constexpr std::size_t size_offset = key_offset + 0x10;
  constexpr std::size_t capacity_offset = key_offset + 0x18;
  assert(key.size() < fixture.external_key.size());
  std::memcpy(fixture.external_key.data(), key.data(), key.size());
  const auto data = reinterpret_cast<std::uintptr_t>(
      fixture.external_key.data());
  const auto size = static_cast<std::uint64_t>(key.size());
  const std::uint64_t capacity = fixture.external_key.size() - 1;
  std::memcpy(fixture.object.data() + key_offset, &data, sizeof(data));
  std::memcpy(fixture.object.data() + size_offset, &size, sizeof(size));
  std::memcpy(fixture.object.data() + capacity_offset, &capacity,
              sizeof(capacity));
}

struct GuiTaskStateFixture {
  std::array<std::uint8_t, 0x160> bytes{};
  std::array<StewardDevelopCountyEnumeratorRawRowV1, 40> rows{};
};

void SetGuiRows(GuiTaskStateFixture &fixture, std::int32_t count) {
  const auto data = reinterpret_cast<std::uintptr_t>(fixture.rows.data());
  const std::int32_t capacity = static_cast<std::int32_t>(fixture.rows.size());
  std::memcpy(fixture.bytes.data() + 0x100, &data, sizeof(data));
  std::memcpy(fixture.bytes.data() + 0x108, &capacity, sizeof(capacity));
  std::memcpy(fixture.bytes.data() + 0x10C, &count, sizeof(count));
  const std::uint32_t scope_word0 = 0x81001234U;
  const std::uint32_t scope_word1 = 0x02005678U;
  std::memcpy(fixture.bytes.data() + 0x120, &scope_word0,
              sizeof(scope_word0));
  std::memcpy(fixture.bytes.data() + 0x124, &scope_word1,
              sizeof(scope_word1));
}

void TestDefaultOffAndExactBuildGuards() {
  static_assert(!xar::bridge::
      kStewardDevelopCountyEnumeratorObserverInstalledByDefaultV1);
  StewardDevelopCountyEnumeratorObserverStateV1 state{};
  StewardDevelopCountyEnumeratorObserverEnvironmentV1 environment{};
  assert(!xar::bridge::InstallStewardDevelopCountyEnumeratorObserverV1(
      state, environment));
  const auto diagnostics = xar::bridge::
      ReadStewardDevelopCountyEnumeratorObserverDiagnosticsV1(state);
  assert((diagnostics.failure_flags &
          xar::bridge::
              steward_develop_county_enumerator_observer_failure_exact_build) !=
         0);
}

void TestDevelopTaskCapturesPersistentNativeRows() {
  NativeTaskTypeFixture task{};
  SetTaskKey(task, "task_develop_county");
  GuiTaskStateFixture gui{};
  SetGuiRows(gui, 2);
  gui.rows[0] = {0x1110, reinterpret_cast<std::uintptr_t>(task.object.data()),
                 0x3330};
  gui.rows[1] = {0x4440, reinterpret_cast<std::uintptr_t>(task.object.data()),
                 0x6660};

  StewardDevelopCountyEnumeratorObserverStateV1 state{};
  assert(xar::bridge::CaptureStewardDevelopCountyEnumeratorPostCallV1(
      state, reinterpret_cast<std::uintptr_t>(task.object.data()),
      reinterpret_cast<std::uintptr_t>(gui.bytes.data()), 77, 9001));
  const auto diagnostics = xar::bridge::
      ReadStewardDevelopCountyEnumeratorObserverDiagnosticsV1(state);
  const auto &row = diagnostics.observation;
  assert(row.call_count == 1);
  assert(row.task_key_read_failure_count == 0);
  assert(row.capture_read_failure_count == 0);
  assert(row.develop_capture_count == 1);
  assert(row.last_scope_word0 == 0x81001234U);
  assert(row.last_scope_word1 == 0x02005678U);
  assert(row.last_vector_count == 2);
  assert(row.last_captured_row_count == 2);
  assert(!row.last_rows_truncated);
  assert(row.rows[0].candidate == 0x1110);
  assert(row.rows[0].query_owner == 0x3330);
  assert(row.rows[1].candidate == 0x4440);
  assert(row.last_thread_id == 77);
  assert(row.last_timestamp_qpc == 9001);
}

void TestOtherTaskIsIgnoredAndUnreadableKeyIsCounted() {
  NativeTaskTypeFixture task{};
  SetTaskKey(task, "task_collect_taxes");
  GuiTaskStateFixture gui{};
  SetGuiRows(gui, 0);
  StewardDevelopCountyEnumeratorObserverStateV1 state{};
  assert(!xar::bridge::CaptureStewardDevelopCountyEnumeratorPostCallV1(
      state, reinterpret_cast<std::uintptr_t>(task.object.data()),
      reinterpret_cast<std::uintptr_t>(gui.bytes.data()), 10, 20));
  assert(!xar::bridge::CaptureStewardDevelopCountyEnumeratorPostCallV1(
      state, 0, reinterpret_cast<std::uintptr_t>(gui.bytes.data()), 11, 21));
  const auto diagnostics = xar::bridge::
      ReadStewardDevelopCountyEnumeratorObserverDiagnosticsV1(state);
  assert(diagnostics.observation.call_count == 2);
  assert(diagnostics.observation.task_key_read_failure_count == 1);
  assert(diagnostics.observation.develop_capture_count == 0);
}

void TestRowCaptureIsBoundedAndMarkedTruncated() {
  NativeTaskTypeFixture task{};
  SetTaskKey(task, "task_develop_county");
  GuiTaskStateFixture gui{};
  SetGuiRows(gui, 40);
  for (std::size_t index = 0; index < gui.rows.size(); ++index) {
    gui.rows[index].candidate = 0x1000 + index;
  }
  StewardDevelopCountyEnumeratorObserverStateV1 state{};
  assert(xar::bridge::CaptureStewardDevelopCountyEnumeratorPostCallV1(
      state, reinterpret_cast<std::uintptr_t>(task.object.data()),
      reinterpret_cast<std::uintptr_t>(gui.bytes.data()), 1, 2));
  const auto diagnostics = xar::bridge::
      ReadStewardDevelopCountyEnumeratorObserverDiagnosticsV1(state);
  assert(diagnostics.observation.last_vector_count == 40);
  assert(diagnostics.observation.last_captured_row_count == 32);
  assert(diagnostics.observation.last_rows_truncated);
  assert(diagnostics.observation.rows[31].candidate == 0x101F);
}

void TestInstallBuildsExactTrampolineAndUninstallRestores() {
  FixtureMemory fixture{};
  StewardDevelopCountyEnumeratorObserverStateV1 state{};
  const auto environment = Environment(fixture);
  assert(xar::bridge::InstallStewardDevelopCountyEnumeratorObserverV1(
      state, environment));
  assert(fixture.target[0] == 0xFF && fixture.target[1] == 0x25);
  assert(std::equal(kAnchor.begin(), kAnchor.begin() + 19,
                    fixture.stub.begin()));
  assert(ContainsU64(fixture.stub,
                     environment.enumerator_target_override));
  assert(ContainsU64(fixture.stub, environment.continue_target_override));
  assert(xar::bridge::UninstallStewardDevelopCountyEnumeratorObserverV1(
      state));
  assert(std::equal(kAnchor.begin(), kAnchor.end(), fixture.target.begin()));
  assert(fixture.free_count == 1);
}

void TestPatchFlushFailureRestoresOriginalBytes() {
  FixtureMemory fixture{};
  fixture.fail_target_flush_once = true;
  StewardDevelopCountyEnumeratorObserverStateV1 state{};
  assert(!xar::bridge::InstallStewardDevelopCountyEnumeratorObserverV1(
      state, Environment(fixture)));
  const auto diagnostics = xar::bridge::
      ReadStewardDevelopCountyEnumeratorObserverDiagnosticsV1(state);
  assert(!diagnostics.installed);
  assert((diagnostics.failure_flags &
          xar::bridge::
              steward_develop_county_enumerator_observer_failure_flush) != 0);
  assert((diagnostics.failure_flags &
          xar::bridge::
              steward_develop_county_enumerator_observer_failure_rollback) ==
         0);
  assert(std::equal(kAnchor.begin(), kAnchor.end(), fixture.target.begin()));
  assert(fixture.free_count == 1);
}

} // namespace

int main() {
  TestDefaultOffAndExactBuildGuards();
  TestDevelopTaskCapturesPersistentNativeRows();
  TestOtherTaskIsIgnoredAndUnreadableKeyIsCounted();
  TestRowCaptureIsBoundedAndMarkedTruncated();
  TestInstallBuildsExactTrampolineAndUninstallRestores();
  TestPatchFlushFailureRestoresOriginalBytes();
  return 0;
}
