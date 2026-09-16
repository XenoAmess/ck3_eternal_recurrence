#include "xar_bridge/physfs_mounted_data_observer_v1.hpp"

#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>

namespace {

struct FixtureMemory {
  std::array<std::uint8_t, xar::bridge::kPhysfsMountedDataPatchBytesV1>
      target{0xE8, 0x9E, 0x4A, 0x08, 0x00};
  std::array<std::uint8_t, xar::bridge::kPhysfsMountedDataStubBytesV1> stub{};
  std::size_t flush_count = 0;
  std::size_t target_protect_count = 0;
  bool report_non_executable_target_protection = false;
  bool freed = false;
};

void *AllocateNear(void *context, std::uintptr_t lower,
                   std::uintptr_t upper, std::size_t size, DWORD,
                   DWORD) noexcept {
  auto &memory = *static_cast<FixtureMemory *>(context);
  const auto address = reinterpret_cast<std::uintptr_t>(memory.stub.data());
  return size <= memory.stub.size() && address >= lower && address <= upper
      ? memory.stub.data()
      : nullptr;
}

bool Free(void *context, void *address, std::size_t,
          DWORD) noexcept {
  auto &memory = *static_cast<FixtureMemory *>(context);
  if (address != memory.stub.data()) return false;
  memory.freed = true;
  return true;
}

bool Protect(void *context, void *address, std::size_t, DWORD desired,
             DWORD &old) noexcept {
  auto &memory = *static_cast<FixtureMemory *>(context);
  if (address == memory.stub.data()) {
    old = desired == PAGE_EXECUTE_READ ? PAGE_READWRITE : PAGE_EXECUTE_READ;
    return true;
  }
  if (address == memory.target.data()) {
    ++memory.target_protect_count;
    if (memory.report_non_executable_target_protection &&
        memory.target_protect_count == 1) {
      old = PAGE_READWRITE;
      return true;
    }
    old = desired == PAGE_EXECUTE_READWRITE ? PAGE_EXECUTE_READ
                                            : PAGE_EXECUTE_READWRITE;
    return true;
  }
  return false;
}

bool Flush(void *context, const void *, std::size_t) noexcept {
  ++static_cast<FixtureMemory *>(context)->flush_count;
  return true;
}

xar::bridge::PhysfsMountedDataObserverEnvironmentV1 Environment(
    FixtureMemory &memory) {
  xar::bridge::PhysfsMountedDataObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(memory.target.data());
  environment.publisher_target_override =
      reinterpret_cast<std::uintptr_t>(memory.target.data()) + 0x100;
  environment.memory_context = &memory;
  environment.virtual_alloc_near_override = &AllocateNear;
  environment.virtual_free_override = &Free;
  environment.virtual_protect_override = &Protect;
  environment.flush_instruction_cache_override = &Flush;
  return environment;
}

} // namespace

int main() {
  static_assert(!xar::bridge::kPhysfsMountedDataObserverInstalledByDefaultV1);
  static_assert(xar::bridge::kPhysfsMountedDataSlotsV1 == 128);
  static_assert(xar::bridge::kPhysfsMountedDataPathBytesV1 == 256);

  {
    xar::bridge::PhysfsMountedDataObserverV1State state{};
    xar::bridge::PhysfsMountedDataObserverEnvironmentV1 environment{};
    assert(!xar::bridge::InstallPhysfsMountedDataObserverV1(state,
                                                            environment));
    assert((state.failure_flags.load() &
            xar::bridge::physfs_mounted_data_observer_failure_exact_build) !=
           0);
  }
  {
    FixtureMemory memory{};
    memory.report_non_executable_target_protection = true;
    const auto original = memory.target;
    auto environment = Environment(memory);
    xar::bridge::PhysfsMountedDataObserverV1State state{};
    assert(!xar::bridge::InstallPhysfsMountedDataObserverV1(state,
                                                            environment));
    assert((state.failure_flags.load() &
            xar::bridge::
                physfs_mounted_data_observer_failure_target_protection) != 0);
    assert(memory.target_protect_count == 2);
    assert(memory.target == original);
    assert(memory.freed);
  }
  {
    FixtureMemory memory{};
    auto environment = Environment(memory);
    environment.primary_thread_suspended_proven = false;
    xar::bridge::PhysfsMountedDataObserverV1State state{};
    assert(!xar::bridge::InstallPhysfsMountedDataObserverV1(state,
                                                            environment));
    assert((state.failure_flags.load() &
            xar::bridge::
                physfs_mounted_data_observer_failure_primary_thread_suspended) !=
           0);
  }
  {
    xar::bridge::PhysfsMountedDataObserverV1State state{};
    for (std::uint32_t index = 0;
         index < xar::bridge::kPhysfsMountedDataSlotsV1 + 2; ++index) {
      const std::string path = "mounted/path/" + std::to_string(index);
      xar::bridge::RecordPhysfsMountedDataV1(
          state, reinterpret_cast<std::uintptr_t>(path.c_str()),
          index % 3 == 0 ? 0U : 1U, 700 + index);
    }
    const auto diagnostics =
        xar::bridge::ReadPhysfsMountedDataObserverV1Diagnostics(state);
    assert(diagnostics.call_count == 130);
    assert(diagnostics.row_count == 128);
    assert(diagnostics.rows.front().ordinal == 3);
    assert(diagnostics.rows.back().ordinal == 130);
    assert(diagnostics.slot_overwrite_count == 2);
    assert(diagnostics.success_count + diagnostics.failure_count == 130);
    assert(diagnostics.rows.back().thread_id == 829);
    assert(diagnostics.rows.back().terminated);
    assert(!diagnostics.rows.back().read_fault);
  }
  {
    xar::bridge::PhysfsMountedDataObserverV1State state{};
    const std::string long_path(300, 'x');
    xar::bridge::RecordPhysfsMountedDataV1(
        state, reinterpret_cast<std::uintptr_t>(long_path.c_str()), 1, 42);
    auto diagnostics =
        xar::bridge::ReadPhysfsMountedDataObserverV1Diagnostics(state);
    assert(diagnostics.rows[0].preview_length == 256);
    assert(!diagnostics.rows[0].terminated);
    xar::bridge::RecordPhysfsMountedDataV1(state, 0, 0, 43);
    diagnostics =
        xar::bridge::ReadPhysfsMountedDataObserverV1Diagnostics(state);
    assert(diagnostics.rows[1].null_pointer);
  }
  {
    FixtureMemory memory{};
    const auto original = memory.target;
    auto environment = Environment(memory);
    xar::bridge::PhysfsMountedDataObserverV1State state{};
    assert(xar::bridge::InstallPhysfsMountedDataObserverV1(state,
                                                           environment));
    assert(state.installed.load() == 1);
    assert(memory.target[0] == 0xE8);
    assert(memory.target != original);
    assert(memory.flush_count >= 2);
    assert(xar::bridge::UninstallPhysfsMountedDataObserverV1(state));
    assert(memory.target == original);
    assert(memory.freed);
    assert(state.installed.load() == 0);
  }
  return 0;
}
