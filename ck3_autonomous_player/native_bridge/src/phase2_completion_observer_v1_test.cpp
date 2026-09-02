#include "xar_bridge/phase2_completion_observer_v1.hpp"

#include <array>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

using xar::bridge::Phase2CompletionObserverV1Environment;
using xar::bridge::Phase2CompletionObserverV1State;

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

using StubRunner = void (*)(void *task) noexcept;

void *MakeStubRunner(void *patch) {
  std::array<std::uint8_t, 26> code{
      0x53,                         // push rbx
      0x48, 0x8B, 0xD9,             // mov rbx, rcx
      0x48, 0x83, 0xEC, 0x28,       // sub rsp, 0x28
      0x48, 0xB8,                   // mov rax, patch
      0, 0, 0, 0, 0, 0, 0, 0,
      0xFF, 0xD0,                   // call rax
      0x48, 0x83, 0xC4, 0x28,       // add rsp, 0x28
      0x5B,                         // pop rbx
      0xC3};                        // ret
  const auto patch_address = reinterpret_cast<std::uint64_t>(patch);
  std::memcpy(code.data() + 10, &patch_address, sizeof(patch_address));
  void *runner = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                              PAGE_READWRITE);
  if (runner == nullptr) return nullptr;
  std::memcpy(runner, code.data(), code.size());
  if (!MakeExecutable(runner, 4096)) {
    VirtualFree(runner, 0, MEM_RELEASE);
    return nullptr;
  }
  return runner;
}

int Fail(const char *message) {
  std::cerr << message << '\n';
  return 1;
}

} // namespace

int main() {
  constexpr std::array<std::uint8_t, 15> anchor{
      0x8B, 0x43, 0x60, 0x83, 0xC0, 0xFE, 0x83, 0xF8,
      0x01, 0x0F, 0x86, 0xAD, 0x00, 0x00, 0x00};
  void *patch = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                             PAGE_READWRITE);
  if (patch == nullptr) return Fail("fixture patch allocation failed");
  std::memcpy(patch, anchor.data(), anchor.size());
  static_cast<std::uint8_t *>(patch)[anchor.size()] = 0xC3;
  if (!MakeExecutable(patch, 4096)) return Fail("fixture patch protect failed");

  Phase2CompletionObserverV1State state{};
  FixtureMemory fixture{};
  Phase2CompletionObserverV1Environment environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 0x10000000;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(patch);
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(patch) + anchor.size();
  environment.retire_target_override =
      reinterpret_cast<std::uintptr_t>(patch) + anchor.size();
  environment.memory_context = &fixture;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
  std::atomic<std::uint64_t> correlation_task{0};
  environment.correlation_task_source = &correlation_task;
  if (!xar::bridge::InstallPhase2CompletionObserverV1(state, environment)) {
    return Fail("offline observer installation failed");
  }
  if (std::memcmp(patch, anchor.data(), anchor.size()) == 0 ||
      static_cast<const std::uint8_t *>(patch)[0] != 0xFF ||
      static_cast<const std::uint8_t *>(patch)[1] != 0x25) {
    return Fail("observer patch was not installed");
  }
  const auto *stub = static_cast<const std::uint8_t *>(state.stub);
  std::uint64_t raw_counter_address = 0;
  std::memcpy(&raw_counter_address, stub + 6, sizeof(raw_counter_address));
  if (stub[3] != 0x50 || stub[4] != 0x48 || stub[5] != 0xB8 ||
      raw_counter_address !=
          reinterpret_cast<std::uintptr_t>(&state.raw_hit_count) ||
      std::memcmp(stub + 14, "\xF0\x48\xFF\x00\x58", 5) != 0) {
    return Fail("raw hook-hit counter stub mismatch");
  }

  std::array<std::uint64_t, 3> vtable{};
  vtable[2] = environment.module_base +
      xar::bridge::kPhase2SelectedCallbackTargetRvaV1;
  std::uint64_t callback_object =
      reinterpret_cast<std::uintptr_t>(vtable.data());
  std::array<std::uint8_t, 0x78> task{};
  const auto callback_address =
      reinterpret_cast<std::uintptr_t>(&callback_object);
  const std::uint32_t one_reference = 1;
  std::memcpy(task.data() + 0x38, &callback_address, sizeof(callback_address));
  std::memcpy(task.data() + 0x64, &one_reference, sizeof(one_reference));
  const auto task_address = reinterpret_cast<std::uintptr_t>(task.data());
  correlation_task.store(task_address, std::memory_order_release);
  void *runner_memory = MakeStubRunner(patch);
  if (runner_memory == nullptr) return Fail("stub runner allocation failed");
#pragma warning(push)
#pragma warning(disable : 4191)
  const auto run_stub = reinterpret_cast<StubRunner>(runner_memory);
#pragma warning(pop)

  run_stub(task.data());
  auto diagnostics =
      xar::bridge::ReadPhase2CompletionObserverV1Diagnostics(state);
  if (!diagnostics.installed || diagnostics.raw_hit_count != 1 ||
      diagnostics.raw_state2_count != 0 ||
      diagnostics.raw_state3_count != 0 ||
      diagnostics.selected_event_count != 0) {
    return Fail("non-complete raw hook telemetry mismatch");
  }

  const std::uint32_t state2 = 2;
  std::memcpy(task.data() + 0x60, &state2, sizeof(state2));
  run_stub(task.data());
  diagnostics = xar::bridge::ReadPhase2CompletionObserverV1Diagnostics(state);
  if (!diagnostics.installed || diagnostics.raw_hit_count != 2 ||
      diagnostics.raw_state2_count != 1 ||
      diagnostics.raw_state3_count != 0 ||
      diagnostics.raw_last_callback != callback_address ||
      diagnostics.raw_last_callback_slot2_target != vtable[2] ||
      diagnostics.raw_last_reference_count != 1 ||
      diagnostics.selected_event_count != 1 ||
      diagnostics.state2_count != 1 || diagnostics.state3_count != 0 ||
      diagnostics.last_state != 2 || diagnostics.last_thread_id == 0 ||
      diagnostics.last_timestamp_qpc == 0 ||
      diagnostics.last_task != task_address ||
      diagnostics.last_callback != callback_address ||
      diagnostics.last_reference_count != 1 ||
      diagnostics.correlation_match_count != 1 ||
      diagnostics.correlation_read_failure_count != 0 ||
      diagnostics.correlation_last_task != task_address ||
      diagnostics.correlation_last_callback != callback_address ||
      !diagnostics.correlation_last_callback_present ||
      diagnostics.correlation_last_state != 2 ||
      diagnostics.correlation_last_reference_count != 1 ||
      diagnostics.correlation_last_thread_id == 0 ||
      diagnostics.correlation_last_timestamp_qpc == 0 ||
      diagnostics.last_observed_retired || !diagnostics.last_will_retire) {
    return Fail("state2 telemetry mismatch");
  }

  const std::uint32_t state3 = 3;
  std::memcpy(task.data() + 0x60, &state3, sizeof(state3));
  run_stub(task.data());
  diagnostics = xar::bridge::ReadPhase2CompletionObserverV1Diagnostics(state);
  if (diagnostics.raw_hit_count != 3 ||
      diagnostics.raw_state2_count != 1 ||
      diagnostics.raw_state3_count != 1 ||
      diagnostics.selected_event_count != 2 ||
      diagnostics.state2_count != 1 || diagnostics.state3_count != 1 ||
      diagnostics.correlation_match_count != 2 ||
      diagnostics.correlation_last_state != 3 ||
      diagnostics.last_state != 3 || diagnostics.last_thread_id == 0 ||
      diagnostics.last_timestamp_qpc == 0 ||
      !diagnostics.last_observed_retired || !diagnostics.last_will_retire) {
    return Fail("state3 telemetry mismatch");
  }

  vtable[2] += 1;
  std::memcpy(task.data() + 0x60, &state2, sizeof(state2));
  run_stub(task.data());
  diagnostics = xar::bridge::ReadPhase2CompletionObserverV1Diagnostics(state);
  if (diagnostics.raw_hit_count != 4 ||
      diagnostics.raw_state2_count != 2 ||
      diagnostics.raw_state3_count != 1 ||
      diagnostics.raw_last_callback != callback_address ||
      diagnostics.raw_last_callback_slot2_target != vtable[2] ||
      diagnostics.raw_last_reference_count != 1 ||
      diagnostics.selected_event_count != 2 ||
      diagnostics.correlation_match_count != 3 ||
      diagnostics.correlation_last_task != task_address ||
      diagnostics.correlation_last_state != 2) {
    return Fail("non-selected callback leaked into telemetry");
  }

  if (!xar::bridge::UninstallPhase2CompletionObserverV1(state) ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      xar::bridge::ReadPhase2CompletionObserverV1Diagnostics(state).installed) {
    return Fail("observer uninstall did not restore exact anchor");
  }
  VirtualFree(runner_memory, 0, MEM_RELEASE);

  Phase2CompletionObserverV1State rollback_state{};
  FixtureMemory rollback_fixture{};
  rollback_fixture.fail_flush_call = 2;
  environment.memory_context = &rollback_fixture;
  if (xar::bridge::InstallPhase2CompletionObserverV1(rollback_state,
                                                      environment) ||
      rollback_state.installed.load() != 0 || rollback_state.stub != nullptr ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_completion_observer_failure_flush) == 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_completion_observer_failure_rollback) != 0) {
    return Fail("recoverable installation rollback mismatch");
  }
  VirtualFree(patch, 0, MEM_RELEASE);
  std::cout << "phase2-completion-observer-v1=GREEN\n";
  return 0;
}
