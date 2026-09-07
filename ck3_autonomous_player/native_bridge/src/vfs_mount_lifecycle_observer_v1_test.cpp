#include "xar_bridge/vfs_mount_lifecycle_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>

namespace {

using xar::bridge::VfsMountLifecycleObserverEnvironmentV1;

constexpr std::array<std::uint8_t, 5> kCoreAnchor{
    0xE8, 0xD5, 0x52, 0x37, 0x03};
constexpr std::array<std::uint8_t, 5> kEntryAnchor{
    0x48, 0x89, 0x5C, 0x24, 0x08};
constexpr std::array<std::uint8_t, 5> kReturnAnchor{
    0x4C, 0x8D, 0x5C, 0x24, 0x50};
constexpr std::array<std::uint8_t, 8> kLookupAnchor{
    0x48, 0x63, 0x4E, 0x08, 0x48, 0x8B, 0x53, 0x38};

struct SyntheticMemory {
  std::array<std::array<std::uint8_t, 16>, 4> patches{};
  std::array<std::uint8_t, 16> core_target{};
  std::array<std::uint8_t,
             xar::bridge::kVfsMountLifecycleStubAllocationBytesV1>
      stubs{};
  std::array<std::uint8_t, 0x110> manager{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
  const void *fail_flush_address = nullptr;
  bool failed_flush = false;

  SyntheticMemory() {
    std::copy(kCoreAnchor.begin(), kCoreAnchor.end(), patches[0].begin());
    std::copy(kEntryAnchor.begin(), kEntryAnchor.end(), patches[1].begin());
    std::copy(kReturnAnchor.begin(), kReturnAnchor.end(), patches[2].begin());
    std::copy(kLookupAnchor.begin(), kLookupAnchor.end(), patches[3].begin());
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

VfsMountLifecycleObserverEnvironmentV1 Environment(
    SyntheticMemory &memory) {
  VfsMountLifecycleObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  for (std::size_t index = 0; index < memory.patches.size(); ++index) {
    environment.patch_target_overrides[index] =
        reinterpret_cast<std::uintptr_t>(memory.patches[index].data());
  }
  environment.core_init_target_override =
      reinterpret_cast<std::uintptr_t>(memory.core_target.data());
  environment.publisher_entry_continue_override =
      reinterpret_cast<std::uintptr_t>(memory.patches[1].data() + 5);
  environment.publisher_return_continue_override =
      reinterpret_cast<std::uintptr_t>(memory.patches[2].data() + 5);
  environment.settings_lookup_continue_override =
      reinterpret_cast<std::uintptr_t>(memory.patches[3].data() + 8);
  environment.manager_address_override =
      reinterpret_cast<std::uintptr_t>(memory.manager.data());
  environment.memory_context = &memory;
  environment.virtual_alloc_near_override = &AllocateNear;
  environment.virtual_free_override = &Free;
  environment.virtual_protect_override = &Protect;
  environment.flush_instruction_cache_override = &Flush;
  return environment;
}

void StoreManagerHead(SyntheticMemory &memory, std::uintptr_t head,
                      std::uint8_t ready) {
  std::memcpy(memory.manager.data() + 8, &head, sizeof(head));
  memory.manager[0xFA] = ready;
}

struct PathView16 {
  const char *data = nullptr;
  std::int32_t length = 0;
  std::uint8_t flag = 0;
  std::array<std::uint8_t, 3> padding{};
};
static_assert(sizeof(PathView16) == 16);

void TestDefaultOffAndAdmission() {
  using namespace xar::bridge;
  static_assert(!kVfsMountLifecycleObserverInstalledByDefaultV1);
  static_assert(kVfsMountLifecycleCoreInitCallRvaV1 == 0x07E7136);
  static_assert(kVfsMountLifecycleCoreInitTargetRvaV1 == 0x3B5C410);
  static_assert(kVfsMountLifecyclePublisherEntryRvaV1 == 0x3BE18C0);
  static_assert(kVfsMountLifecyclePublisherReturnRvaV1 == 0x3BE1A07);
  static_assert(kVfsMountLifecycleSettingsLookupRvaV1 == 0x3BE239C);
  static_assert(kVfsMountLifecycleManagerRvaV1 == 0x585FA30);
  static_assert(kVfsMountLifecyclePublisherSlotsV1 == 64);

  VfsMountLifecycleObserverV1State state{};
  VfsMountLifecycleObserverEnvironmentV1 environment{};
  assert(!InstallVfsMountLifecycleObserverV1(state, environment));
  assert((state.failure_flags.load() &
          vfs_mount_lifecycle_observer_failure_exact_build) != 0);

  VfsMountLifecycleObserverV1State running{};
  VfsMountLifecycleObserverEnvironmentV1 running_environment{};
  running_environment.exact_build_admitted = true;
  running_environment.module_base = 1;
  assert(!InstallVfsMountLifecycleObserverV1(running,
                                             running_environment));
  assert((running.failure_flags.load() &
          vfs_mount_lifecycle_observer_failure_primary_thread_suspended) !=
         0);
}

void TestReadOnlyLifecycleAndFiltering() {
  using namespace xar::bridge;
  SyntheticMemory memory{};
  StoreManagerHead(memory, 0x1111, 1);
  VfsMountLifecycleObserverV1State state{};
  state.manager_address =
      reinterpret_cast<std::uintptr_t>(memory.manager.data());

  constexpr char first_path[] = "game";
  constexpr char second_path[] = "game/map_data";
  RecordVfsMountPublisherEnterV1(
      state, 0xAA, reinterpret_cast<std::uintptr_t>(first_path), 0xBB, 0, 7);
  RecordVfsMountPublisherEnterV1(
      state, 0xCC, reinterpret_cast<std::uintptr_t>(second_path), 0xDD, 1, 8);
  StoreManagerHead(memory, 0x2222, 1);
  RecordVfsMountPublisherReturnV1(state, 1, 8);
  StoreManagerHead(memory, 0x3333, 1);
  RecordVfsMountPublisherReturnV1(state, 0, 7);
  RecordVfsCoreInitReturnV1(state, 0x1234, 7);

  constexpr char paths[] = "paths.settings";
  constexpr char checksummed[] = "paths_checksummed.settings";
  constexpr char near_miss[] = "paths.settingx";
  PathView16 path_view{paths, 14, 0, {}};
  PathView16 checksummed_view{checksummed, 26, 1, {}};
  PathView16 miss_view{near_miss, 14, 0, {}};
  const auto manager = reinterpret_cast<std::uintptr_t>(memory.manager.data());
  RecordVfsSettingsLookupV1(
      state, reinterpret_cast<std::uintptr_t>(&path_view), manager, 7);
  RecordVfsSettingsLookupV1(
      state, reinterpret_cast<std::uintptr_t>(&checksummed_view), manager, 7);
  RecordVfsSettingsLookupV1(
      state, reinterpret_cast<std::uintptr_t>(&miss_view), manager, 7);

  const auto diagnostics =
      ReadVfsMountLifecycleObserverV1Diagnostics(state);
  assert(diagnostics.publisher_entry_count == 2);
  assert(diagnostics.publisher_return_count == 2);
  assert(diagnostics.publisher_success_count == 1);
  assert(diagnostics.publisher_failure_count == 1);
  assert(diagnostics.publisher_correlation_miss_count == 0);
  assert(diagnostics.latest_publisher.entry_thread_id == 7);
  assert(diagnostics.latest_publisher.raw_result == 0);
  assert(diagnostics.latest_publisher.path.preview_length == 4);
  assert(diagnostics.latest_publisher.path.terminated);
  assert(std::memcmp(diagnostics.latest_publisher.path.preview.data(), "game",
                     4) == 0);
  assert(diagnostics.latest_publisher.manager_before.head == 0x1111);
  assert(diagnostics.latest_publisher.manager_after.head == 0x3333);
  assert(diagnostics.core_init_count == 1);
  assert(diagnostics.core_init_raw_al == 0x34);
  assert(diagnostics.core_init_manager.head == 0x3333);
  assert(diagnostics.paths_lookup.count == 1);
  assert(diagnostics.paths_lookup.path_length == 14);
  assert(diagnostics.paths_lookup.path_flag == 0);
  assert(diagnostics.paths_lookup.manager.head == 0x3333);
  assert(diagnostics.checksummed_lookup.count == 1);
  assert(diagnostics.checksummed_lookup.path_length == 26);
  assert(diagnostics.checksummed_lookup.path_flag == 1);
  assert(diagnostics.lookup_classification_fault_count == 0);
  assert(diagnostics.next_sequence == 7);

  RecordVfsMountPublisherReturnV1(state, 1, 99);
  assert(state.publisher_correlation_miss_count.load() == 1);
}

void TestPublisherRingOverwriteAccounting() {
  using namespace xar::bridge;
  SyntheticMemory memory{};
  VfsMountLifecycleObserverV1State state{};
  state.manager_address =
      reinterpret_cast<std::uintptr_t>(memory.manager.data());
  constexpr char path[] = "x";
  for (std::uint32_t index = 0;
       index < kVfsMountLifecyclePublisherSlotsV1 + 1; ++index) {
    RecordVfsMountPublisherEnterV1(
        state, index, reinterpret_cast<std::uintptr_t>(path), 0, 0,
        index + 1);
  }
  assert(state.publisher_entry_count.load() == 65);
  assert(state.publisher_slot_overwrite_count.load() == 1);
}

void TestFourAnchorTransactionAndRollback() {
  using namespace xar::bridge;
  SyntheticMemory memory{};
  VfsMountLifecycleObserverV1State state{};
  assert(InstallVfsMountLifecycleObserverV1(state, Environment(memory)));
  assert(state.installed.load() == 1);
  assert(state.installed_mask.load() == 0x0F);
  assert(memory.patches[0][0] == 0xE8);
  assert(memory.patches[1][0] == 0xE9);
  assert(memory.patches[2][0] == 0xE9);
  assert(memory.patches[3][0] == 0xE9);
  assert(memory.patches[3][5] == 0x90);
  assert(memory.patches[3][6] == 0x90);
  assert(memory.patches[3][7] == 0x90);
  assert(memory.allocation_count == 1);
  assert(UninstallVfsMountLifecycleObserverV1(state));
  assert(state.installed_mask.load() == 0);
  assert(std::equal(kCoreAnchor.begin(), kCoreAnchor.end(),
                    memory.patches[0].begin()));
  assert(std::equal(kEntryAnchor.begin(), kEntryAnchor.end(),
                    memory.patches[1].begin()));
  assert(std::equal(kReturnAnchor.begin(), kReturnAnchor.end(),
                    memory.patches[2].begin()));
  assert(std::equal(kLookupAnchor.begin(), kLookupAnchor.end(),
                    memory.patches[3].begin()));
  assert(memory.free_count == 1);

  SyntheticMemory drift{};
  drift.patches[3][6] ^= 1;
  VfsMountLifecycleObserverV1State drift_state{};
  assert(!InstallVfsMountLifecycleObserverV1(drift_state,
                                              Environment(drift)));
  assert(drift.allocation_count == 0);
  assert(drift_state.installed_mask.load() == 0);

  SyntheticMemory rollback{};
  rollback.fail_flush_address = rollback.patches[3].data();
  VfsMountLifecycleObserverV1State rollback_state{};
  assert(!InstallVfsMountLifecycleObserverV1(rollback_state,
                                              Environment(rollback)));
  assert(rollback_state.installed_mask.load() == 0);
  assert(std::equal(kCoreAnchor.begin(), kCoreAnchor.end(),
                    rollback.patches[0].begin()));
  assert(std::equal(kEntryAnchor.begin(), kEntryAnchor.end(),
                    rollback.patches[1].begin()));
  assert(std::equal(kReturnAnchor.begin(), kReturnAnchor.end(),
                    rollback.patches[2].begin()));
  assert(std::equal(kLookupAnchor.begin(), kLookupAnchor.end(),
                    rollback.patches[3].begin()));
  assert((rollback_state.failure_flags.load() &
          vfs_mount_lifecycle_observer_failure_flush) != 0);
}

} // namespace

int main() {
  TestDefaultOffAndAdmission();
  TestReadOnlyLifecycleAndFiltering();
  TestPublisherRingOverwriteAccounting();
  TestFourAnchorTransactionAndRollback();
  return 0;
}
