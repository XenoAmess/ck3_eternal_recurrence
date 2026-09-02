#include "xar_bridge/g2_truce_native_callsite_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>

namespace {

using xar::bridge::G2TruceNativeCallsiteObserverV1Environment;
using xar::bridge::G2TruceNativeCallsiteObserverV1State;

constexpr std::array<std::uint8_t, 19> kAnchor0{
    0x48, 0x8D, 0x8E, 0x08, 0x01, 0x00, 0x00,
    0x4D, 0x8B, 0x47, 0x28,
    0x49, 0x8B, 0xD7,
    0xE8, 0xEC, 0x80, 0x49, 0x00};
constexpr std::array<std::uint8_t, 20> kAnchor1{
    0x48, 0x8D, 0x8E, 0x08, 0x01, 0x00, 0x00,
    0x4D, 0x8B, 0x44, 0x24, 0x28,
    0x49, 0x8B, 0xD4,
    0xE8, 0x5D, 0x7A, 0x49, 0x00};

struct FixtureMemory {
  std::array<std::uint8_t, 19> target0{kAnchor0};
  std::array<std::uint8_t, 20> target1{kAnchor1};
  std::array<std::uint8_t,
             xar::bridge::kG2TruceNativeCallsiteStubCapacityV1>
      stub0{};
  std::array<std::uint8_t,
             xar::bridge::kG2TruceNativeCallsiteStubCapacityV1>
      stub1{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
  const void *fail_flush_address = nullptr;
  bool fail_flush_once = false;
  bool failed_flush = false;
};

void *FixtureAlloc(void *context, std::size_t size, DWORD, DWORD) noexcept {
  auto &fixture = *static_cast<FixtureMemory *>(context);
  if (size != fixture.stub0.size()) return nullptr;
  if (fixture.allocation_count == 0) {
    ++fixture.allocation_count;
    return fixture.stub0.data();
  }
  if (fixture.allocation_count == 1) {
    ++fixture.allocation_count;
    return fixture.stub1.data();
  }
  return nullptr;
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
  if (fixture.fail_flush_once && !fixture.failed_flush &&
      address == fixture.fail_flush_address) {
    fixture.failed_flush = true;
    return false;
  }
  return true;
}

G2TruceNativeCallsiteObserverV1Environment Environment(
    FixtureMemory &fixture) {
  G2TruceNativeCallsiteObserverV1Environment environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.patch_target_overrides = {
      reinterpret_cast<std::uintptr_t>(fixture.target0.data()),
      reinterpret_cast<std::uintptr_t>(fixture.target1.data())};
  environment.continue_target_overrides = {
      reinterpret_cast<std::uintptr_t>(fixture.target0.data() +
                                       fixture.target0.size()),
      reinterpret_cast<std::uintptr_t>(fixture.target1.data() +
                                       fixture.target1.size())};
  environment.evaluator_target_override = 0x123456789ABCDEF0ULL;
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

void TestDefaultOffAndExactBuildGuards() {
  static_assert(
      !xar::bridge::kG2TruceNativeCallsiteObserverInstalledByDefaultV1);
  G2TruceNativeCallsiteObserverV1State state{};
  G2TruceNativeCallsiteObserverV1Environment environment{};
  assert(!xar::bridge::InstallG2TruceNativeCallsiteObserverV1(state,
                                                              environment));
  const auto diagnostics =
      xar::bridge::ReadG2TruceNativeCallsiteObserverV1Diagnostics(state);
  assert((diagnostics.failure_flags &
          xar::bridge::g2_truce_native_callsite_observer_failure_exact_build) !=
         0);
}

void TestReadOnlyPrePostRows() {
  G2TruceNativeCallsiteObserverV1State state{};
  xar::bridge::RecordG2TruceNativeCallsitePreV1(
      state, 0, 0x1008, 0x2000, 0x2030, 71, 9001);
  xar::bridge::RecordG2TruceNativeCallsitePostV1(
      state, 0, 1825, 71, 9017);
  xar::bridge::RecordG2TruceNativeCallsitePreV1(
      state, 1, 0x3008, 0x4000, 0x4030, 72, 9101);
  xar::bridge::RecordG2TruceNativeCallsitePostV1(
      state, 1, -1, 72, 9119);

  const auto diagnostics =
      xar::bridge::ReadG2TruceNativeCallsiteObserverV1Diagnostics(state);
  assert(diagnostics.callsites[0].pre_call_count == 1);
  assert(diagnostics.callsites[0].post_call_count == 1);
  assert(diagnostics.callsites[0].last_script_value == 0x1008);
  assert(diagnostics.callsites[0].last_effect_context == 0x2000);
  assert(diagnostics.callsites[0].last_evaluation_context == 0x2030);
  assert(diagnostics.callsites[0].last_pre_thread_id == 71);
  assert(diagnostics.callsites[0].last_pre_timestamp_qpc == 9001);
  assert(diagnostics.callsites[0].last_return_eax == 1825);
  assert(diagnostics.callsites[0].last_post_thread_id == 71);
  assert(diagnostics.callsites[0].last_post_timestamp_qpc == 9017);
  assert(diagnostics.callsites[1].last_return_eax == -1);
}

void TestInstallBuildsTwoExactTrampolinesAndUninstallRestores() {
  FixtureMemory fixture{};
  G2TruceNativeCallsiteObserverV1State state{};
  const auto environment = Environment(fixture);
  assert(xar::bridge::InstallG2TruceNativeCallsiteObserverV1(state,
                                                             environment));
  const auto diagnostics =
      xar::bridge::ReadG2TruceNativeCallsiteObserverV1Diagnostics(state);
  assert(diagnostics.installed_mask == 0x3);
  assert(fixture.target0[0] == 0xFF && fixture.target0[1] == 0x25);
  assert(fixture.target1[0] == 0xFF && fixture.target1[1] == 0x25);
  assert(std::equal(kAnchor0.begin(), kAnchor0.end() - 5,
                    fixture.stub0.begin()));
  assert(std::equal(kAnchor1.begin(), kAnchor1.end() - 5,
                    fixture.stub1.begin()));
  assert(ContainsU64(fixture.stub0, environment.evaluator_target_override));
  assert(ContainsU64(fixture.stub1, environment.evaluator_target_override));
  assert(ContainsU64(fixture.stub0,
                     environment.continue_target_overrides[0]));
  assert(ContainsU64(fixture.stub1,
                     environment.continue_target_overrides[1]));

  assert(xar::bridge::UninstallG2TruceNativeCallsiteObserverV1(state));
  assert(std::equal(kAnchor0.begin(), kAnchor0.end(), fixture.target0.begin()));
  assert(std::equal(kAnchor1.begin(), kAnchor1.end(), fixture.target1.begin()));
  assert(fixture.free_count == 2);
}

void TestSecondPatchFailureRollsBackFirstPatch() {
  FixtureMemory fixture{};
  fixture.fail_flush_address = fixture.target1.data();
  fixture.fail_flush_once = true;
  G2TruceNativeCallsiteObserverV1State state{};
  const auto environment = Environment(fixture);
  assert(!xar::bridge::InstallG2TruceNativeCallsiteObserverV1(state,
                                                              environment));
  const auto diagnostics =
      xar::bridge::ReadG2TruceNativeCallsiteObserverV1Diagnostics(state);
  assert(diagnostics.installed_mask == 0);
  assert((diagnostics.failure_flags &
          xar::bridge::g2_truce_native_callsite_observer_failure_flush) != 0);
  assert((diagnostics.failure_flags &
          xar::bridge::g2_truce_native_callsite_observer_failure_rollback) ==
         0);
  assert(std::equal(kAnchor0.begin(), kAnchor0.end(), fixture.target0.begin()));
  assert(std::equal(kAnchor1.begin(), kAnchor1.end(), fixture.target1.begin()));
  assert(fixture.free_count == 2);
}

} // namespace

int main() {
  TestDefaultOffAndExactBuildGuards();
  TestReadOnlyPrePostRows();
  TestInstallBuildsTwoExactTrampolinesAndUninstallRestores();
  TestSecondPatchFailureRollsBackFirstPatch();
  return 0;
}
