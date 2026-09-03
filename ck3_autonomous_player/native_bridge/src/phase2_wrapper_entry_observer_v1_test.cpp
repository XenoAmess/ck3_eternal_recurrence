#include "xar_bridge/phase2_wrapper_entry_observer_v1.hpp"

#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

using xar::bridge::Phase2WrapperEntryObserverV1Environment;
using xar::bridge::Phase2WrapperEntryObserverV1State;

struct FixtureMemory {
  std::uint32_t flush_calls = 0;
  std::uint32_t fail_flush_call = 0;
};

void *FixtureAlloc(void *, std::size_t size, DWORD allocation_type,
                   DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, allocation_type, protection);
}

bool FixtureFree(void *, void *address, std::size_t size,
                 DWORD free_type) noexcept {
  return VirtualFree(address, size, free_type) != FALSE;
}

bool FixtureProtect(void *, void *address, std::size_t size,
                    DWORD protection, DWORD &old_protection) noexcept {
  return VirtualProtect(address, size, protection, &old_protection) != FALSE;
}

bool FixtureFlush(void *context, const void *address, std::size_t size) noexcept {
  auto *fixture = static_cast<FixtureMemory *>(context);
  if (fixture != nullptr) {
    ++fixture->flush_calls;
    if (fixture->flush_calls == fixture->fail_flush_call) return false;
  }
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}

bool MakeExecutable(void *address, std::size_t size) {
  DWORD old = 0;
  return VirtualProtect(address, size, PAGE_EXECUTE_READ, &old) != FALSE;
}

using StubRunner = void (*)(std::uintptr_t, std::uintptr_t, std::uintptr_t,
                            std::uintptr_t, std::uintptr_t) noexcept;

int Fail(const char *message) {
  std::cerr << message << '\n';
  return 1;
}

} // namespace

int main() {
  constexpr std::array<std::uint8_t, 15> anchor{
      0x48, 0x89, 0x5C, 0x24, 0x08,
      0x48, 0x89, 0x6C, 0x24, 0x18,
      0x48, 0x89, 0x74, 0x24, 0x20};
  void *patch = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                            PAGE_READWRITE);
  if (patch == nullptr) return Fail("fixture patch allocation failed");
  std::memcpy(patch, anchor.data(), anchor.size());
  static_cast<std::uint8_t *>(patch)[anchor.size()] = 0xC3;
  if (!MakeExecutable(patch, 4096)) return Fail("fixture patch protect failed");

  Phase2WrapperEntryObserverV1State state{};
  std::atomic<std::uint64_t> selected_task{0};
  FixtureMemory fixture{};
  Phase2WrapperEntryObserverV1Environment environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 0x1000;
  environment.patch_target_override = reinterpret_cast<std::uintptr_t>(patch);
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(patch) + anchor.size();
  environment.memory_context = &fixture;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
  environment.selected_task_source = &selected_task;
  if (!xar::bridge::InstallPhase2WrapperEntryObserverV1(state, environment)) {
    return Fail("offline wrapper observer installation failed");
  }
  if (std::memcmp(patch, anchor.data(), anchor.size()) == 0 ||
      static_cast<const std::uint8_t *>(patch)[0] != 0xFF ||
      static_cast<const std::uint8_t *>(patch)[1] != 0x25) {
    return Fail("wrapper observer patch was not installed");
  }
  const auto *stub = static_cast<const std::uint8_t *>(state.stub);
  if (std::memcmp(stub + 15, "\x4C\x8B\x84\x24\x80\x00\x00\x00", 8) != 0 ||
      std::memcmp(stub + 23, "\x48\x8B\x54\x24\x48", 5) != 0 ||
      std::memcmp(stub + 28, "\x48\x8B\x4C\x24\x58", 5) != 0 ||
      std::memcmp(stub + 60, anchor.data(), anchor.size()) != 0) {
    return Fail("wrapper observer stub argument/replay contract mismatch");
  }

#pragma warning(push)
#pragma warning(disable : 4191)
  const auto run_stub = reinterpret_cast<StubRunner>(patch);
#pragma warning(pop)
  constexpr std::uintptr_t owner = 0x1122334455667788ULL;
  constexpr std::uintptr_t producer_list = 0x8877665544332211ULL;
  run_stub(owner, 0, 0, 0, producer_list);
  auto diagnostics =
      xar::bridge::ReadPhase2WrapperEntryObserverV1Diagnostics(state);
  if (!diagnostics.installed || diagnostics.failure_flags != 0 ||
      diagnostics.entry_count != 1 || diagnostics.last_return_address == 0 ||
      diagnostics.last_callsite_rva == 0 ||
      diagnostics.last_scheduler_owner != owner ||
      diagnostics.last_producer_list != producer_list ||
      diagnostics.last_thread_id == 0 || diagnostics.last_timestamp_qpc == 0) {
    return Fail("wrapper entry telemetry mismatch");
  }

  xar::bridge::RecordPhase2WrapperEntryObservationV1(
      state, environment.module_base + 0x12345, owner, producer_list, 7, 9);
  diagnostics =
      xar::bridge::ReadPhase2WrapperEntryObserverV1Diagnostics(state);
  if (diagnostics.entry_count != 2 ||
      diagnostics.last_callsite_rva != 0x12340 ||
      diagnostics.last_scheduler_owner != owner ||
      diagnostics.last_producer_list != producer_list ||
      diagnostics.last_thread_id != 7 || diagnostics.last_timestamp_qpc != 9) {
    return Fail("wrapper callsite mapping seam mismatch");
  }

  selected_task.store(0xAABBCCDDEEFF0011ULL, std::memory_order_release);
  xar::bridge::RecordPhase2WrapperEntryObservationV1(
      state, environment.module_base + 0x23455, owner, producer_list, 8, 10);
  diagnostics =
      xar::bridge::ReadPhase2WrapperEntryObserverV1Diagnostics(state);
  if (diagnostics.selected_after_publish_entry_count != 1 ||
      diagnostics.selected_after_publish_last_task !=
          0xAABBCCDDEEFF0011ULL ||
      diagnostics.selected_after_publish_last_callsite_rva != 0x23450) {
    return Fail("wrapper post-publish classification mismatch");
  }

  if (!xar::bridge::UninstallPhase2WrapperEntryObserverV1(state) ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      xar::bridge::ReadPhase2WrapperEntryObserverV1Diagnostics(state).installed) {
    return Fail("wrapper observer uninstall did not restore exact anchor");
  }

  Phase2WrapperEntryObserverV1State rollback_state{};
  FixtureMemory rollback_fixture{};
  rollback_fixture.fail_flush_call = 2;
  environment.memory_context = &rollback_fixture;
  if (xar::bridge::InstallPhase2WrapperEntryObserverV1(rollback_state,
                                                        environment) ||
      rollback_state.installed.load() != 0 || rollback_state.stub != nullptr ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_wrapper_entry_observer_failure_flush) == 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_wrapper_entry_observer_failure_rollback) != 0) {
    return Fail("recoverable wrapper install rollback mismatch");
  }

  VirtualFree(patch, 0, MEM_RELEASE);
  std::cout << "phase2-wrapper-entry-observer-v1=GREEN\n";
  return 0;
}
