#include "xar_bridge/phase2_wrapper_consumer_edge_observer_v1.hpp"

#include <array>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

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

using StubRunner = void (*)(std::uintptr_t, std::uint32_t) noexcept;

int Fail(const char *message) {
  std::cerr << message << '\n';
  return 1;
}

} // namespace

int main() {
  constexpr std::array<std::uint8_t, 16> anchor{
      0x40, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41, 0x55,
      0x41, 0x56, 0x41, 0x57, 0x48, 0x83, 0xEC, 0x60};
  constexpr std::array<std::uint8_t, 16> fixture_epilogue{
      0x48, 0x83, 0xC4, 0x60, 0x41, 0x5F, 0x41, 0x5E,
      0x41, 0x5D, 0x41, 0x5C, 0x5F, 0x5E, 0x5D, 0xC3};
  void *patch = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                            PAGE_READWRITE);
  if (patch == nullptr) return Fail("fixture patch allocation failed");
  std::memcpy(patch, anchor.data(), anchor.size());
  std::memcpy(static_cast<std::uint8_t *>(patch) + anchor.size(),
              fixture_epilogue.data(), fixture_epilogue.size());
  if (!MakeExecutable(patch, 4096)) return Fail("fixture patch protect failed");

  std::atomic<std::uint64_t> selected_task{0};
  xar::bridge::Phase2WrapperConsumerEdgeStateV1 state{};
  FixtureMemory fixture{};
  xar::bridge::Phase2WrapperConsumerEdgeEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = reinterpret_cast<std::uintptr_t>(patch) -
      xar::bridge::kPhase2WrapperConsumerEdgeCallRva0V1 - 5;
  environment.patch_target_override = reinterpret_cast<std::uintptr_t>(patch);
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(patch) + anchor.size();
  environment.memory_context = &fixture;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
  environment.selected_task_source = &selected_task;
  if (!xar::bridge::InstallPhase2WrapperConsumerEdgeObserverV1(
          state, environment)) {
    return Fail("offline consumer edge observer installation failed");
  }
  const auto *stub = static_cast<const std::uint8_t *>(state.stub);
  if (std::memcmp(stub + 15, "\x44\x8B\x44\x24\x40", 5) != 0 ||
      std::memcmp(stub + 20, "\x48\x8B\x54\x24\x48", 5) != 0 ||
      std::memcmp(stub + 25, "\x48\x8B\x4C\x24\x58", 5) != 0 ||
      std::memcmp(stub + 57, anchor.data(), anchor.size()) != 0) {
    return Fail("consumer edge stub argument/replay contract mismatch");
  }

#pragma warning(push)
#pragma warning(disable : 4191)
  const auto run_stub = reinterpret_cast<StubRunner>(patch);
#pragma warning(pop)
  run_stub(0x1122334455667788ULL, 7);
  auto diagnostics =
      xar::bridge::ReadPhase2WrapperConsumerEdgeDiagnosticsV1(state);
  if (!diagnostics.installed || diagnostics.failure_flags != 0 ||
      diagnostics.entry_count != 1 ||
      diagnostics.edge_0x3B9E10B_count != 0 ||
      diagnostics.edge_0x3B9E175_count != 0 ||
      diagnostics.other_caller_count != 1 ||
      diagnostics.selected_after_publish_entry_count != 0 ||
      diagnostics.last_consumer_context != 0x1122334455667788ULL ||
      diagnostics.last_item_count != 7 || diagnostics.last_thread_id == 0 ||
      diagnostics.last_timestamp_qpc == 0) {
    return Fail("consumer edge zero-selected telemetry mismatch");
  }

  selected_task.store(0x8877665544332211ULL, std::memory_order_release);
  xar::bridge::RecordPhase2WrapperConsumerEdgeObservationV1(
      state,
      environment.module_base +
          xar::bridge::kPhase2WrapperConsumerEdgeCallRva1V1 + 5,
      0x1234, 9, 11, 13);
  xar::bridge::RecordPhase2WrapperConsumerEdgeObservationV1(
      state, environment.module_base + 0x2227, 0x5678, 10, 12, 14);
  diagnostics =
      xar::bridge::ReadPhase2WrapperConsumerEdgeDiagnosticsV1(state);
  if (diagnostics.entry_count != 3 ||
      diagnostics.edge_0x3B9E10B_count != 0 ||
      diagnostics.edge_0x3B9E175_count != 1 ||
      diagnostics.other_caller_count != 2 ||
      diagnostics.selected_after_publish_entry_count != 2 ||
      diagnostics.selected_after_publish_edge_0x3B9E10B_count != 0 ||
      diagnostics.selected_after_publish_edge_0x3B9E175_count != 1 ||
      diagnostics.selected_after_publish_other_caller_count != 1 ||
      diagnostics.last_callsite_rva != 0x2222 ||
      diagnostics.last_selected_task != 0x8877665544332211ULL) {
    return Fail("post-publish edge classification mismatch");
  }

  if (!xar::bridge::UninstallPhase2WrapperConsumerEdgeObserverV1(state) ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      xar::bridge::ReadPhase2WrapperConsumerEdgeDiagnosticsV1(state)
          .installed) {
    return Fail("consumer edge uninstall did not restore exact anchor");
  }

  xar::bridge::Phase2WrapperConsumerEdgeStateV1 rollback_state{};
  FixtureMemory rollback_fixture{};
  rollback_fixture.fail_flush_call = 2;
  environment.memory_context = &rollback_fixture;
  if (xar::bridge::InstallPhase2WrapperConsumerEdgeObserverV1(
          rollback_state, environment) ||
      rollback_state.installed.load() != 0 || rollback_state.stub != nullptr ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_wrapper_consumer_edge_failure_flush) == 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_wrapper_consumer_edge_failure_rollback) != 0) {
    return Fail("recoverable consumer edge rollback mismatch");
  }

  VirtualFree(patch, 0, MEM_RELEASE);
  std::cout << "phase2-wrapper-consumer-edge-observer-v1=GREEN\n";
  return 0;
}
