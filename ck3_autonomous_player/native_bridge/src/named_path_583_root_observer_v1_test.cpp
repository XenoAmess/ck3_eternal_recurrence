#include "xar_bridge/named_path_583_root_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>

namespace {

using xar::bridge::NamedPath583RootObserverEnvironmentV1;

constexpr std::array<std::uint8_t, 5> kResolverAnchor{
    0xE8, 0xE9, 0x61, 0x87, 0x00};
constexpr std::array<std::uint8_t, 11> kMoveAnchor{
    0x48, 0x8B, 0xD0, 0x48, 0x8B, 0xCF,
    0xE8, 0x11, 0x72, 0x4C, 0xFD};

struct SyntheticMemory {
  std::array<std::uint8_t, 16> resolver_target{};
  std::array<std::uint8_t, 16> move_target{};
  std::array<std::uint8_t, 16> resolver_patch{};
  std::array<std::uint8_t, 16> move_patch{};
  std::array<std::uint8_t,
             xar::bridge::kNamedPath583StubAllocationBytesV1> stubs{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
  const void *fail_flush_address = nullptr;
  bool failed_flush = false;

  SyntheticMemory() {
    std::copy(kResolverAnchor.begin(), kResolverAnchor.end(),
              resolver_patch.begin());
    std::copy(kMoveAnchor.begin(), kMoveAnchor.end(), move_patch.begin());
  }
};

void *AllocateNear(void *context, std::uintptr_t lower,
                   std::uintptr_t upper, std::size_t size, DWORD,
                   DWORD) noexcept {
  auto &memory = *static_cast<SyntheticMemory *>(context);
  const auto address = reinterpret_cast<std::uintptr_t>(memory.stubs.data());
  if (memory.allocation_count != 0 || size != memory.stubs.size() ||
      address < lower || address > upper) {
    return nullptr;
  }
  ++memory.allocation_count;
  return memory.stubs.data();
}

bool Free(void *context, void *, std::size_t, DWORD) noexcept {
  ++static_cast<SyntheticMemory *>(context)->free_count;
  return true;
}

bool Protect(void *, void *, std::size_t, DWORD next,
             DWORD &previous) noexcept {
  previous = next == PAGE_EXECUTE_READ ? PAGE_READWRITE : PAGE_EXECUTE_READ;
  return true;
}

bool Flush(void *context, const void *address, std::size_t) noexcept {
  auto &memory = *static_cast<SyntheticMemory *>(context);
  if (memory.fail_flush_address == address && !memory.failed_flush) {
    memory.failed_flush = true;
    return false;
  }
  return true;
}

NamedPath583RootObserverEnvironmentV1 Environment(
    SyntheticMemory &memory) {
  NamedPath583RootObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.patch_target_overrides = {
      reinterpret_cast<std::uintptr_t>(memory.resolver_patch.data()),
      reinterpret_cast<std::uintptr_t>(memory.move_patch.data())};
  environment.move_continue_target_override =
      reinterpret_cast<std::uintptr_t>(memory.move_patch.data() +
                                       kMoveAnchor.size());
  environment.resolver_target_override =
      reinterpret_cast<std::uintptr_t>(memory.resolver_target.data());
  environment.move_target_override =
      reinterpret_cast<std::uintptr_t>(memory.move_target.data());
  environment.memory_context = &memory;
  environment.virtual_alloc_near_override = &AllocateNear;
  environment.virtual_free_override = &Free;
  environment.virtual_protect_override = &Protect;
  environment.flush_instruction_cache_override = &Flush;
  return environment;
}

struct SyntheticString {
  union {
    std::array<char, 16> local;
    const char *pointer;
  } storage{};
  std::uint64_t length = 0;
  std::uint64_t capacity = 0;
};
static_assert(offsetof(SyntheticString, length) == 0x10);
static_assert(offsetof(SyntheticString, capacity) == 0x18);

SyntheticString LocalString(const char *value) {
  SyntheticString result{};
  result.length = std::strlen(value);
  result.capacity = 15;
  std::memcpy(result.storage.local.data(), value, result.length);
  return result;
}

SyntheticString HeapString(const char *value) {
  SyntheticString result{};
  result.storage.pointer = value;
  result.length = std::strlen(value);
  result.capacity = result.length + 8;
  if (result.capacity < 16) result.capacity = 16;
  return result;
}

void TestDefaultOffAndAdmission() {
  using namespace xar::bridge;
  static_assert(!kNamedPath583RootObserverInstalledByDefaultV1);
  static_assert(kNamedPath583ResolverCallRvaV1 == 0x3320A82);
  static_assert(kNamedPath583ResolverTargetRvaV1 == 0x3B96C70);
  static_assert(kNamedPath583MovePatchRvaV1 == 0x331F9E4);
  static_assert(kNamedPath583MoveTargetRvaV1 == 0x07E6C00);
  NamedPath583RootObserverV1State state{};
  NamedPath583RootObserverEnvironmentV1 environment{};
  assert(!InstallNamedPath583RootObserverV1(state, environment));
  assert((state.failure_flags.load() &
          named_path_583_root_observer_failure_exact_build) != 0);

  NamedPath583RootObserverV1State running{};
  NamedPath583RootObserverEnvironmentV1 running_environment{};
  running_environment.exact_build_admitted = true;
  running_environment.module_base = 1;
  assert(!InstallNamedPath583RootObserverV1(running, running_environment));
  assert((running.failure_flags.load() &
          named_path_583_root_observer_failure_primary_thread_suspended) != 0);

  NamedPath583RootObserverV1State override_denied{};
  NamedPath583RootObserverEnvironmentV1 override_environment{};
  override_environment.exact_build_admitted = true;
  override_environment.primary_thread_suspended_proven = true;
  override_environment.module_base = 1;
  override_environment.move_target_override = 2;
  assert(!InstallNamedPath583RootObserverV1(override_denied,
                                             override_environment));
  assert((override_denied.failure_flags.load() &
          named_path_583_root_observer_failure_unsupported_override) != 0);
}

void TestCorrelatedReadOnlySnapshots() {
  using namespace xar::bridge;
  auto resolver = HeapString("map_data");
  auto temporary = LocalString("default.map");
  auto root = LocalString("old-root");
  NamedPath583RootObserverV1State state{};

  RecordNamedPath583ResolverV1(
      state, reinterpret_cast<std::uintptr_t>(&resolver), 0x1234);
  RecordNamedPath583MovePreV1(
      state, reinterpret_cast<std::uintptr_t>(&root),
      reinterpret_cast<std::uintptr_t>(&temporary), 0x1234);
  root = HeapString("map_data/default.map");
  temporary = LocalString("");
  RecordNamedPath583MovePostV1(
      state, reinterpret_cast<std::uintptr_t>(&root),
      reinterpret_cast<std::uintptr_t>(&temporary),
      reinterpret_cast<std::uintptr_t>(&root), 0x1234);

  const auto diagnostics = ReadNamedPath583RootObserverV1Diagnostics(state);
  assert(diagnostics.sequence == 1);
  assert(diagnostics.thread_id == 0x1234);
  assert(diagnostics.resolver_count == 1);
  assert(diagnostics.move_pre_count == 1);
  assert(diagnostics.move_post_count == 1);
  assert(diagnostics.correlation_miss_count == 0);
  assert(diagnostics.move_pre_seen && diagnostics.move_post_seen);
  assert(diagnostics.resolver.object ==
         reinterpret_cast<std::uintptr_t>(&resolver));
  assert(diagnostics.resolver.length == 8);
  assert(diagnostics.temporary_before.length == 11);
  assert(diagnostics.root_before.length == 8);
  assert(diagnostics.root_after.length == 20);
  assert(diagnostics.temporary_after.length == 0);
  assert(!diagnostics.resolver.read_fault);
  assert(!diagnostics.root_after.read_fault);

  RecordNamedPath583MovePreV1(state, 0, 0, 0x9999);
  const auto missed = ReadNamedPath583RootObserverV1Diagnostics(state);
  assert(missed.correlation_miss_count == 1);
}

void TestNullResolverIsNotAReadFault() {
  using namespace xar::bridge;
  NamedPath583RootObserverV1State state{};
  RecordNamedPath583ResolverV1(state, 0, 77);
  const auto diagnostics = ReadNamedPath583RootObserverV1Diagnostics(state);
  assert(diagnostics.resolver_count == 1);
  assert(diagnostics.resolver.object == 0);
  assert(diagnostics.resolver.null_result);
  assert(!diagnostics.resolver.read_fault);

  NamedPath583RootObserverV1State unreadable{};
  RecordNamedPath583ResolverV1(unreadable, 1, 78);
  const auto fault = ReadNamedPath583RootObserverV1Diagnostics(unreadable);
  assert(!fault.resolver.null_result);
  assert(fault.resolver.read_fault);
}

void TestAnchorDriftPreventsAnyAllocation() {
  using namespace xar::bridge;
  SyntheticMemory memory{};
  memory.move_patch[3] ^= 0x01;
  NamedPath583RootObserverV1State state{};
  const auto environment = Environment(memory);
  assert(!InstallNamedPath583RootObserverV1(state, environment));
  assert(memory.allocation_count == 0);
  assert(state.installed_mask.load() == 0);
  assert((state.failure_flags.load() &
          named_path_583_root_observer_failure_anchor) != 0);
}

void TestTransactionalInstallAndRestore() {
  using namespace xar::bridge;
  SyntheticMemory memory{};
  NamedPath583RootObserverV1State state{};
  const auto environment = Environment(memory);
  assert(InstallNamedPath583RootObserverV1(state, environment));
  assert(state.installed.load() == 1);
  assert(state.installed_mask.load() == 3);
  assert(memory.resolver_patch[0] == 0xE8);
  assert(memory.move_patch[0] == 0xE9);
  assert(std::any_of(memory.stubs.begin(), memory.stubs.end(),
                     [](std::uint8_t value) { return value != 0; }));
  assert(UninstallNamedPath583RootObserverV1(state));
  assert(state.installed.load() == 0);
  assert(state.installed_mask.load() == 0);
  assert(std::equal(kResolverAnchor.begin(), kResolverAnchor.end(),
                    memory.resolver_patch.begin()));
  assert(std::equal(kMoveAnchor.begin(), kMoveAnchor.end(),
                    memory.move_patch.begin()));
  assert(memory.free_count == 1);
}

void TestSecondPatchFailureRollsBackFirst() {
  using namespace xar::bridge;
  SyntheticMemory memory{};
  memory.fail_flush_address = memory.move_patch.data();
  NamedPath583RootObserverV1State state{};
  const auto environment = Environment(memory);
  assert(!InstallNamedPath583RootObserverV1(state, environment));
  assert(state.installed_mask.load() == 0);
  assert(std::equal(kResolverAnchor.begin(), kResolverAnchor.end(),
                    memory.resolver_patch.begin()));
  assert(std::equal(kMoveAnchor.begin(), kMoveAnchor.end(),
                    memory.move_patch.begin()));
  assert((state.failure_flags.load() &
          named_path_583_root_observer_failure_flush) != 0);
  assert((state.failure_flags.load() &
          named_path_583_root_observer_failure_rollback) == 0);
  assert(memory.free_count == 1);
}

} // namespace

int main() {
  TestDefaultOffAndAdmission();
  TestCorrelatedReadOnlySnapshots();
  TestNullResolverIsNotAReadFault();
  TestAnchorDriftPreventsAnyAllocation();
  TestTransactionalInstallAndRestore();
  TestSecondPatchFailureRollsBackFirst();
  return 0;
}
