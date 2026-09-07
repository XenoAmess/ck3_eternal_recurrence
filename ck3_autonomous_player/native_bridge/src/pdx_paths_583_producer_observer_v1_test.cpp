#include "xar_bridge/pdx_paths_583_producer_observer_v1.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>

namespace {

using xar::bridge::PdxPaths583ProducerObserverEnvironmentV1;

constexpr std::array<std::array<std::uint8_t, 5>, 5> kAnchors{{
    {0x48, 0x89, 0x7C, 0x24, 0x30},
    {0xE8, 0xED, 0xB8, 0x04, 0x00},
    {0xE8, 0xD9, 0xB7, 0x04, 0x00},
    {0x48, 0x89, 0x4C, 0x24, 0x60},
    {0xE8, 0x54, 0x41, 0x9A, 0xFE},
}};

struct SyntheticMemory {
  std::array<std::array<std::uint8_t, 16>, 5> patches{};
  std::array<std::uint8_t, 16> lookup_target{};
  std::array<std::uint8_t, 16> insert_target{};
  std::array<std::uint8_t,
             xar::bridge::kPdxPaths583StubAllocationBytesV1> stubs{};
  std::array<std::uint8_t, 64> map{};
  std::size_t allocation_count = 0;
  std::size_t free_count = 0;
  const void *fail_flush_address = nullptr;
  bool failed_flush = false;

  SyntheticMemory() {
    for (std::size_t index = 0; index < patches.size(); ++index) {
      std::copy(kAnchors[index].begin(), kAnchors[index].end(),
                patches[index].begin());
    }
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

PdxPaths583ProducerObserverEnvironmentV1 Environment(
    SyntheticMemory &memory) {
  PdxPaths583ProducerObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  for (std::size_t index = 0; index < memory.patches.size(); ++index) {
    environment.patch_target_overrides[index] =
        reinterpret_cast<std::uintptr_t>(memory.patches[index].data());
  }
  environment.task_continue_target_override =
      reinterpret_cast<std::uintptr_t>(memory.patches[0].data() + 5);
  environment.parser_continue_target_override =
      reinterpret_cast<std::uintptr_t>(memory.patches[3].data() + 5);
  environment.lookup_target_override =
      reinterpret_cast<std::uintptr_t>(memory.lookup_target.data());
  environment.insert_target_override =
      reinterpret_cast<std::uintptr_t>(memory.insert_target.data());
  environment.map_address_override =
      reinterpret_cast<std::uintptr_t>(memory.map.data());
  environment.memory_context = &memory;
  environment.virtual_alloc_near_override = &AllocateNear;
  environment.virtual_free_override = &Free;
  environment.virtual_protect_override = &Protect;
  environment.flush_instruction_cache_override = &Flush;
  return environment;
}

void TestDefaultOffAndAdmission() {
  using namespace xar::bridge;
  static_assert(!kPdxPaths583ProducerObserverInstalledByDefaultV1);
  static_assert(kPdxPaths583TaskPatchRvaV1 == 0x3B96A2E);
  static_assert(kPdxPaths583PathsLookupCallRvaV1 == 0x3B96A4E);
  static_assert(kPdxPaths583ChecksummedLookupCallRvaV1 == 0x3B96B62);
  static_assert(kPdxPaths583ParserPatchRvaV1 == 0x3B96531);
  static_assert(kPdxPaths583InsertCallRvaV1 == 0x3B96897);
  static_assert(kPdxPaths583MapRvaV1 == 0x5764698);
  PdxPaths583ProducerObserverV1State state{};
  PdxPaths583ProducerObserverEnvironmentV1 environment{};
  assert(!InstallPdxPaths583ProducerObserverV1(state, environment));
  assert((state.failure_flags.load() &
          pdx_paths_583_producer_observer_failure_exact_build) != 0);

  PdxPaths583ProducerObserverV1State running{};
  PdxPaths583ProducerObserverEnvironmentV1 running_environment{};
  running_environment.exact_build_admitted = true;
  running_environment.module_base = 1;
  assert(!InstallPdxPaths583ProducerObserverV1(running,
                                                running_environment));
  assert((running.failure_flags.load() &
          pdx_paths_583_producer_observer_failure_primary_thread_suspended) !=
         0);
}

void TestReadOnlyProducerClassification() {
  using namespace xar::bridge;
  struct Row {
    std::uint32_t hash = 0;
    std::uint8_t control = 0;
    std::array<std::uint8_t, 3> padding{};
    std::uint32_t key = 0;
    std::array<std::uint8_t, 36> value{};
  };
  static_assert(sizeof(Row) == 48);
  struct Map {
    std::uint64_t reserved = 0;
    Row *rows = nullptr;
    std::uint32_t count = 0;
    std::uint32_t mask = 0;
    std::uint8_t max_probe = 0;
    std::array<std::uint8_t, 7> tail{};
  };
  std::array<Row, 2> rows{};
  Map map{};
  map.rows = rows.data();
  PdxPaths583ProducerObserverV1State state{};
  state.module_base = 0x100000;
  state.map_address = reinterpret_cast<std::uintptr_t>(&map);

  RecordPdxPaths583TaskEnterV1(state, 11);
  RecordPdxPaths583LookupPreV1(state, pdx_paths_583_source_paths, 11);
  RecordPdxPaths583LookupPostV1(state, pdx_paths_583_source_paths, 0, 11);
  RecordPdxPaths583LookupPreV1(state, pdx_paths_583_source_checksummed, 11);
  RecordPdxPaths583LookupPostV1(state, pdx_paths_583_source_checksummed,
                                0x1234, 11);
  RecordPdxPaths583ParserEnterV1(
      state, state.module_base + kPdxPaths583ChecksummedLiteralRvaV1, 11);

  std::uint32_t key = kPdxPaths583NamedPathIdV1;
  struct ResultPair {
    std::uint64_t row = 0;
    std::uint8_t inserted = 0;
    std::array<std::uint8_t, 7> padding{};
  } pair{};
  RecordPdxPaths583InsertPreV1(
      state, reinterpret_cast<std::uintptr_t>(&map),
      reinterpret_cast<std::uintptr_t>(&pair),
      kPdxPaths583NamedPathHashV1, reinterpret_cast<std::uintptr_t>(&key),
      0x5678, 11);
  rows[0].hash = kPdxPaths583NamedPathHashV1;
  rows[0].control = 1;
  rows[0].key = key;
  map.count = 1;
  map.max_probe = 1;
  pair.row = reinterpret_cast<std::uintptr_t>(&rows[0]);
  pair.inserted = 1;
  RecordPdxPaths583InsertPostV1(
      state, reinterpret_cast<std::uintptr_t>(&map),
      reinterpret_cast<std::uintptr_t>(&pair),
      kPdxPaths583NamedPathHashV1, reinterpret_cast<std::uintptr_t>(&key),
      reinterpret_cast<std::uintptr_t>(&pair), 11);

  const auto diagnostics =
      ReadPdxPaths583ProducerObserverV1Diagnostics(state);
  assert(diagnostics.task_enter_count == 1);
  assert(diagnostics.task_table.count == 0);
  assert(diagnostics.paths_lookup.return_count == 1);
  assert(diagnostics.paths_lookup.null_result);
  assert(diagnostics.checksummed_lookup.raw_result == 0x1234);
  assert(!diagnostics.checksummed_lookup.null_result);
  assert(diagnostics.paths_parser_enter_count == 0);
  assert(diagnostics.checksummed_parser_enter_count == 1);
  assert(diagnostics.key_583_insert_pre_count == 1);
  assert(diagnostics.key_583_insert_post_count == 1);
  assert(diagnostics.table_before.count == 0);
  assert(diagnostics.table_after.count == 1);
  assert(diagnostics.table_after.id_583_present);
  assert(diagnostics.table_after.id_583_row == pair.row);
  assert(diagnostics.result_row == pair.row);
  assert(diagnostics.result_inserted);
  assert(!diagnostics.result_pair_null);
  assert(!diagnostics.result_read_fault);

  PdxPaths583ProducerObserverV1State null_pair{};
  null_pair.map_address = reinterpret_cast<std::uintptr_t>(&map);
  RecordPdxPaths583InsertPostV1(
      null_pair, reinterpret_cast<std::uintptr_t>(&map), 0,
      kPdxPaths583NamedPathHashV1, reinterpret_cast<std::uintptr_t>(&key), 0,
      12);
  const auto null_diagnostics =
      ReadPdxPaths583ProducerObserverV1Diagnostics(null_pair);
  assert(null_diagnostics.result_pair_null);
  assert(!null_diagnostics.result_read_fault);
}

void TestFiveAnchorTransactionAndRollback() {
  using namespace xar::bridge;
  SyntheticMemory memory{};
  PdxPaths583ProducerObserverV1State state{};
  auto environment = Environment(memory);
  assert(InstallPdxPaths583ProducerObserverV1(state, environment));
  assert(state.installed.load() == 1);
  assert(state.installed_mask.load() == 0x1F);
  assert(memory.patches[0][0] == 0xE9);
  assert(memory.patches[1][0] == 0xE8);
  assert(memory.patches[2][0] == 0xE8);
  assert(memory.patches[3][0] == 0xE9);
  assert(memory.patches[4][0] == 0xE8);
  assert(memory.allocation_count == 1);
  constexpr std::array<std::uint8_t, 8> kLoadCallerSixth{
      0x48, 0x8B, 0x84, 0x24, 0x18, 0x01, 0x00, 0x00};
  constexpr std::array<std::uint8_t, 5> kPublishNativeSixth{
      0x48, 0x89, 0x44, 0x24, 0x28};
  assert(std::search(memory.stubs.begin(), memory.stubs.end(),
                     kLoadCallerSixth.begin(), kLoadCallerSixth.end()) !=
         memory.stubs.end());
  assert(std::search(memory.stubs.begin(), memory.stubs.end(),
                     kPublishNativeSixth.begin(), kPublishNativeSixth.end()) !=
         memory.stubs.end());
  assert(UninstallPdxPaths583ProducerObserverV1(state));
  assert(state.installed_mask.load() == 0);
  for (std::size_t index = 0; index < memory.patches.size(); ++index) {
    assert(std::equal(kAnchors[index].begin(), kAnchors[index].end(),
                      memory.patches[index].begin()));
  }
  assert(memory.free_count == 1);

  SyntheticMemory drift{};
  drift.patches[4][2] ^= 1;
  PdxPaths583ProducerObserverV1State drift_state{};
  assert(!InstallPdxPaths583ProducerObserverV1(drift_state,
                                                Environment(drift)));
  assert(drift.allocation_count == 0);
  assert(drift_state.installed_mask.load() == 0);

  SyntheticMemory rollback{};
  rollback.fail_flush_address = rollback.patches[4].data();
  PdxPaths583ProducerObserverV1State rollback_state{};
  assert(!InstallPdxPaths583ProducerObserverV1(rollback_state,
                                                Environment(rollback)));
  assert(rollback_state.installed_mask.load() == 0);
  for (std::size_t index = 0; index < rollback.patches.size(); ++index) {
    assert(std::equal(kAnchors[index].begin(), kAnchors[index].end(),
                      rollback.patches[index].begin()));
  }
  assert((rollback_state.failure_flags.load() &
          pdx_paths_583_producer_observer_failure_flush) != 0);
}

} // namespace

int main() {
  TestDefaultOffAndAdmission();
  TestReadOnlyProducerClassification();
  TestFiveAnchorTransactionAndRollback();
  return 0;
}
