#include "xar_bridge/phase2_post_call_observer_v1.hpp"

#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>

namespace {

using xar::bridge::Phase2PostCallObserverV1Environment;
using xar::bridge::Phase2PostCallObserverV1State;

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

using StubRunner = void (*)(std::uintptr_t frame, void *patch,
                            std::uintptr_t replay_object) noexcept;

void *MakeStubRunner() {
  constexpr std::array<std::uint8_t, 28> code{
      0x55,                               // push rbp
      0x48, 0x8B, 0xE9,                   // mov rbp,rcx
      0x48, 0x8B, 0xC2,                   // mov rax,rdx
      0x48, 0x83, 0xEC, 0x20,             // sub rsp,20
      0x4C, 0x89, 0x44, 0x24, 0x60,       // mov [rsp+60],r8
      0xFF, 0xD0,                         // call rax
      0x48, 0x83, 0xC4, 0x20,             // add rsp,20
      0x5D,                               // pop rbp
      0xC3,                               // ret
      0x90, 0x90, 0x90, 0x90};
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
  constexpr std::array<std::uint8_t, 14> anchor{
      0x90, 0x48, 0x8B, 0x4C, 0x24, 0x68, 0x48,
      0x85, 0xC9, 0x74, 0x11, 0x48, 0x8B, 0x01};
  void *patch = VirtualAlloc(nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
                            PAGE_READWRITE);
  if (patch == nullptr) return Fail("fixture patch allocation failed");
  std::memcpy(patch, anchor.data(), anchor.size());
  static_cast<std::uint8_t *>(patch)[anchor.size()] = 0xC3;
  if (!MakeExecutable(patch, 4096)) return Fail("fixture patch protect failed");

  constexpr std::uintptr_t module_base = 0x10000000;
  std::array<std::uint64_t, 3> vtable{};
  vtable[2] = module_base +
      xar::bridge::kPhase2PostCallSelectedCallbackTargetRvaV1;
  std::uint64_t callback_object =
      reinterpret_cast<std::uintptr_t>(vtable.data());
  std::array<std::uint8_t, 0x78> task{};
  const auto callback = reinterpret_cast<std::uintptr_t>(&callback_object);
  const std::uint32_t state2 = 2;
  std::memcpy(task.data() + 0x38, &callback, sizeof(callback));
  std::memcpy(task.data() + 0x60, &state2, sizeof(state2));
  std::array<std::uint8_t, 0x28> descriptor{};
  const auto task_address = reinterpret_cast<std::uintptr_t>(task.data());
  constexpr std::uintptr_t owner = 0x1122334455667788ULL;
  std::memcpy(descriptor.data() + 0x18, &task_address, sizeof(task_address));
  std::memcpy(descriptor.data() + 0x20, &owner, sizeof(owner));
  std::array<std::uintptr_t, 1> descriptor_list{
      reinterpret_cast<std::uintptr_t>(descriptor.data())};
  std::array<std::uint8_t, 0x100> frame{};
  const auto list_begin =
      reinterpret_cast<std::uintptr_t>(descriptor_list.data());
  const std::uint32_t list_count = 1;
  std::memcpy(frame.data() + 0xE0, &list_begin, sizeof(list_begin));
  std::memcpy(frame.data() + 0xEC, &list_count, sizeof(list_count));

  Phase2PostCallObserverV1State state{};
  FixtureMemory fixture{};
  Phase2PostCallObserverV1Environment environment{};
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = module_base;
  environment.patch_target_override = reinterpret_cast<std::uintptr_t>(patch);
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(patch) + anchor.size();
  environment.null_target_override =
      reinterpret_cast<std::uintptr_t>(patch) + anchor.size();
  environment.memory_context = &fixture;
  environment.virtual_alloc_override = &FixtureAlloc;
  environment.virtual_free_override = &FixtureFree;
  environment.virtual_protect_override = &FixtureProtect;
  environment.flush_instruction_cache_override = &FixtureFlush;
  if (!xar::bridge::InstallPhase2PostCallObserverV1(state, environment)) {
    return Fail("offline post-call observer installation failed");
  }
  if (std::memcmp(patch, anchor.data(), anchor.size()) == 0 ||
      static_cast<const std::uint8_t *>(patch)[0] != 0xFF ||
      static_cast<const std::uint8_t *>(patch)[1] != 0x25) {
    return Fail("post-call observer patch was not installed");
  }
  const auto *stub = static_cast<const std::uint8_t *>(state.stub);
  if (std::memcmp(stub + 15, "\x48\x8B\xCD\x48\xB8", 5) != 0 ||
      std::memcmp(stub + 45, "\x90\x48\x8B\x4C\x24\x68", 6) != 0 ||
      std::memcmp(stub + 54, "\x75\x0E\xFF\x25", 4) != 0) {
    return Fail("post-call observer stub capture/replay mismatch");
  }
  void *runner_memory = MakeStubRunner();
  if (runner_memory == nullptr) return Fail("stub runner allocation failed");
#pragma warning(push)
#pragma warning(disable : 4191)
  const auto run_stub = reinterpret_cast<StubRunner>(runner_memory);
#pragma warning(pop)
  std::uint64_t replay_object = 0;
  run_stub(reinterpret_cast<std::uintptr_t>(frame.data()), patch,
           reinterpret_cast<std::uintptr_t>(&replay_object));
  auto diagnostics =
      xar::bridge::ReadPhase2PostCallObserverV1Diagnostics(state);
  if (!diagnostics.installed || diagnostics.failure_flags != 0 ||
      diagnostics.hit_count != 1 || diagnostics.nonempty_list_count != 1 ||
      diagnostics.descriptor_seen_count != 1 ||
      diagnostics.selected_event_count != 1 ||
      diagnostics.selected_state2_count != 1 ||
      diagnostics.last_producer_list !=
          reinterpret_cast<std::uintptr_t>(frame.data()) + 0xE0 ||
      diagnostics.last_list_begin != list_begin || diagnostics.last_list_count != 1 ||
      diagnostics.last_task != task_address || diagnostics.last_owner != owner ||
      diagnostics.last_callback != callback ||
      diagnostics.last_callback_slot2_target != vtable[2] ||
      diagnostics.last_state != 2 || diagnostics.last_thread_id == 0 ||
      diagnostics.last_timestamp_qpc == 0 || diagnostics.read_failure_count != 0 ||
      diagnostics.scan_truncated_count != 0) {
    return Fail("selected post-call telemetry mismatch");
  }

  vtable[2] += 1;
  const std::uint32_t state0 = 0;
  std::memcpy(task.data() + 0x60, &state0, sizeof(state0));
  run_stub(reinterpret_cast<std::uintptr_t>(frame.data()), patch, 0);
  diagnostics = xar::bridge::ReadPhase2PostCallObserverV1Diagnostics(state);
  if (diagnostics.hit_count != 2 || diagnostics.descriptor_seen_count != 2 ||
      diagnostics.raw_last_task != task_address ||
      diagnostics.raw_last_callback_slot2_target != vtable[2] ||
      diagnostics.raw_last_state != 0 || diagnostics.selected_event_count != 1) {
    return Fail("non-selected raw telemetry mismatch");
  }

  if (!xar::bridge::UninstallPhase2PostCallObserverV1(state) ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      xar::bridge::ReadPhase2PostCallObserverV1Diagnostics(state).installed) {
    return Fail("post-call observer uninstall did not restore exact anchor");
  }

  Phase2PostCallObserverV1State rollback_state{};
  FixtureMemory rollback_fixture{};
  rollback_fixture.fail_flush_call = 2;
  environment.memory_context = &rollback_fixture;
  if (xar::bridge::InstallPhase2PostCallObserverV1(rollback_state,
                                                    environment) ||
      rollback_state.installed.load() != 0 || rollback_state.stub != nullptr ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_post_call_observer_failure_flush) == 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_post_call_observer_failure_rollback) != 0) {
    return Fail("recoverable post-call install rollback mismatch");
  }

  VirtualFree(runner_memory, 0, MEM_RELEASE);
  VirtualFree(patch, 0, MEM_RELEASE);
  std::cout << "phase2-post-call-observer-v1=GREEN\n";
  return 0;
}
