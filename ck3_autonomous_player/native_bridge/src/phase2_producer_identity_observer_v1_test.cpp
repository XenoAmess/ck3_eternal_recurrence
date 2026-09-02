#include "xar_bridge/phase2_producer_identity_observer_v1.hpp"

#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

using xar::bridge::Phase2ProducerIdentityEnvironmentV1;
using xar::bridge::Phase2ProducerIdentityStateV1;

struct FixtureMemory {
  std::uint32_t flush_calls = 0;
  std::uint32_t fail_flush_call = 0;
};

std::uint32_t g_original_call_count = 0;

extern "C" std::uintptr_t FixtureOriginalCall() noexcept {
  ++g_original_call_count;
  return 0x12345678;
}

void *FixtureAlloc(void *, std::size_t size, DWORD type, DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool FixtureFree(void *, void *address, std::size_t size, DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
bool FixtureProtect(void *, void *address, std::size_t size, DWORD protection,
                    DWORD &old_protection) noexcept {
  return VirtualProtect(address, size, protection, &old_protection) != FALSE;
}
bool FixtureFlush(void *context, const void *address, std::size_t size) noexcept {
  auto *fixture = static_cast<FixtureMemory *>(context);
  if (fixture != nullptr && ++fixture->flush_calls == fixture->fail_flush_call) {
    return false;
  }
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}
bool MakeExecutable(void *address, std::size_t size) {
  DWORD old = 0;
  return VirtualProtect(address, size, PAGE_EXECUTE_READ, &old) != FALSE;
}

using StubRunner = std::uintptr_t (*)(void *task) noexcept;

void *MakeRunner(void *patch) {
  std::array<std::uint8_t, 26> code{
      0x53, 0x48, 0x8B, 0xD9, 0x48, 0x83, 0xEC, 0x28,
      0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0,
      0xFF, 0xD0, 0x48, 0x83, 0xC4, 0x28, 0x5B, 0xC3};
  const auto address = reinterpret_cast<std::uint64_t>(patch);
  std::memcpy(code.data() + 10, &address, sizeof(address));
  void *runner = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
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
  constexpr std::array<std::uint8_t, 16> anchor{
      0xB8, 0x02, 0x00, 0x00, 0x00, 0x87, 0x43, 0x60,
      0xE8, 0x61, 0x70, 0x28, 0x00, 0x48, 0x8B, 0xF8};
  void *patch = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
  if (patch == nullptr) return Fail("fixture patch allocation failed");
  std::memcpy(patch, anchor.data(), anchor.size());
  static_cast<std::uint8_t *>(patch)[anchor.size()] = 0xC3;
  if (!MakeExecutable(patch, 4096)) return Fail("fixture patch protection failed");

  Phase2ProducerIdentityStateV1 state{};
  FixtureMemory fixture{};
  Phase2ProducerIdentityEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 0x140000000;
  environment.patch_target_override = reinterpret_cast<std::uintptr_t>(patch);
  environment.continue_target_override = reinterpret_cast<std::uintptr_t>(patch) + anchor.size();
  environment.original_call_target_override = reinterpret_cast<std::uintptr_t>(&FixtureOriginalCall);
  environment.memory_context = &fixture;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
  if (!xar::bridge::InstallPhase2ProducerIdentityObserverV1(state, environment)) {
    return Fail("observer install failed");
  }
  if (std::memcmp(patch, anchor.data(), anchor.size()) == 0 ||
      static_cast<std::uint8_t *>(patch)[0] != 0xFF ||
      static_cast<std::uint8_t *>(patch)[1] != 0x25) {
    return Fail("absolute detour not installed");
  }

  std::array<std::uint64_t, 3> vtable{};
  vtable[2] = environment.module_base + 0x88B480;
  std::uint64_t callback_object = reinterpret_cast<std::uintptr_t>(vtable.data());
  std::array<std::uint8_t, 0x78> task{};
  const auto callback = reinterpret_cast<std::uint64_t>(&callback_object);
  const std::uint64_t owner = 0xABCDEF;
  const std::uint32_t state1 = 1;
  std::memcpy(task.data() + 0x38, &callback, sizeof(callback));
  std::memcpy(task.data() + 0x58, &owner, sizeof(owner));
  std::memcpy(task.data() + 0x60, &state1, sizeof(state1));
  void *runner_memory = MakeRunner(patch);
  if (runner_memory == nullptr) return Fail("runner allocation failed");
#pragma warning(push)
#pragma warning(disable : 4191)
  const auto run = reinterpret_cast<StubRunner>(runner_memory);
#pragma warning(pop)
  const auto call_result = run(task.data());
  const auto diagnostics = xar::bridge::ReadPhase2ProducerIdentityDiagnosticsV1(state);
  std::uint32_t published = 0;
  std::memcpy(&published, task.data() + 0x60, sizeof(published));
  if (!diagnostics.installed ||
      diagnostics.producer_0x3B9CFD2_entry_count != 1 ||
      diagnostics.producer_0x3B9CFD7_entry_count != 1 ||
      diagnostics.read_failure_count != 0 ||
      diagnostics.last_task_pointer != reinterpret_cast<std::uintptr_t>(task.data()) ||
      diagnostics.last_callback_pointer != callback ||
      diagnostics.last_callback_vptr != reinterpret_cast<std::uintptr_t>(vtable.data()) ||
      diagnostics.last_callback_slot2 != vtable[2] ||
      diagnostics.last_callback_slot2_rva != 0x88B480 ||
      diagnostics.last_owner_pointer != owner ||
      diagnostics.last_state_before_publish != 1 ||
      diagnostics.last_state_after_publish != 2 ||
      diagnostics.last_thread_id == 0 || diagnostics.last_timestamp_qpc == 0 ||
      published != 2 || g_original_call_count != 1 || call_result != 0x12345678) {
    return Fail("producer identity telemetry or original flow mismatch");
  }

  xar::bridge::RecordPhase2ProducerIdentityObservationV1(state, 0, 0, 7, 9);
  if (xar::bridge::ReadPhase2ProducerIdentityDiagnosticsV1(state).read_failure_count < 5) {
    return Fail("read failures were not explicit");
  }
  if (!xar::bridge::UninstallPhase2ProducerIdentityObserverV1(state) ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      xar::bridge::ReadPhase2ProducerIdentityDiagnosticsV1(state).installed) {
    return Fail("uninstall did not restore exact anchor");
  }
  VirtualFree(runner_memory, 0, MEM_RELEASE);

  Phase2ProducerIdentityStateV1 rollback_state{};
  FixtureMemory rollback_fixture{};
  rollback_fixture.fail_flush_call = 2;
  environment.memory_context = &rollback_fixture;
  if (xar::bridge::InstallPhase2ProducerIdentityObserverV1(rollback_state, environment) ||
      rollback_state.installed.load() != 0 || rollback_state.stub != nullptr ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      (rollback_state.failure_flags.load() & xar::bridge::phase2_producer_identity_failure_flush) == 0 ||
      (rollback_state.failure_flags.load() & xar::bridge::phase2_producer_identity_failure_rollback) != 0) {
    return Fail("recoverable install rollback mismatch");
  }
  VirtualFree(patch, 0, MEM_RELEASE);
  std::cout << "phase2-producer-identity-observer-v1=GREEN\n";
  return 0;
}
