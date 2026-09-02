#include "xar_bridge/phase2_post_call_list_identity_observer_v1.hpp"

#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

namespace {

using xar::bridge::Phase2PostCallListIdentityEnvironmentV1;
using xar::bridge::Phase2PostCallListIdentityStateV1;

struct FixtureMemory {
  std::uint32_t flush_calls = 0;
  std::uint32_t fail_flush_call = 0;
};

void *FixtureAlloc(void *, std::size_t size, DWORD type,
                   DWORD protection) noexcept {
  return VirtualAlloc(nullptr, size, type, protection);
}
bool FixtureFree(void *, void *address, std::size_t size,
                 DWORD type) noexcept {
  return VirtualFree(address, size, type) != FALSE;
}
bool FixtureProtect(void *, void *address, std::size_t size,
                    DWORD protection, DWORD &old_protection) noexcept {
  return VirtualProtect(address, size, protection, &old_protection) != FALSE;
}
bool FixtureFlush(void *context, const void *address, std::size_t size) noexcept {
  auto *fixture = static_cast<FixtureMemory *>(context);
  ++fixture->flush_calls;
  if (fixture->flush_calls == fixture->fail_flush_call) return false;
  return FlushInstructionCache(GetCurrentProcess(), address, size) != FALSE;
}
bool MakeExecutable(void *address, std::size_t size) {
  DWORD old = 0;
  return VirtualProtect(address, size, PAGE_EXECUTE_READ, &old) != FALSE;
}

using StubRunner = void (*)(std::uintptr_t, void *, std::uintptr_t) noexcept;

void *MakeStubRunner() {
  constexpr std::array<std::uint8_t, 28> code{
      0x55, 0x48, 0x8B, 0xE9, 0x48, 0x8B, 0xC2,
      0x48, 0x83, 0xEC, 0x20, 0x4C, 0x89, 0x44,
      0x24, 0x60, 0xFF, 0xD0, 0x48, 0x83, 0xC4,
      0x20, 0x5D, 0xC3, 0x90, 0x90, 0x90, 0x90};
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

void SetTask(std::array<std::uint8_t, 0x78> &task, std::uint64_t callback,
             std::uint32_t state) {
  std::memcpy(task.data() + 0x38, &callback, sizeof(callback));
  std::memcpy(task.data() + 0x60, &state, sizeof(state));
}

void SetDescriptor(std::array<std::uint8_t, 0x28> &descriptor,
                   std::uint64_t task, std::uint64_t owner) {
  std::memcpy(descriptor.data() + 0x18, &task, sizeof(task));
  std::memcpy(descriptor.data() + 0x20, &owner, sizeof(owner));
}

template <std::size_t Count>
void SetList(std::array<std::uint8_t, 0x100> &frame,
             const std::array<std::uintptr_t, Count> &list) {
  const auto begin = reinterpret_cast<std::uintptr_t>(list.data());
  const auto count = static_cast<std::uint32_t>(Count);
  std::memcpy(frame.data() + 0xE0, &begin, sizeof(begin));
  std::memcpy(frame.data() + 0xEC, &count, sizeof(count));
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
  if (patch == nullptr) return Fail("patch allocation failed");
  std::memcpy(patch, anchor.data(), anchor.size());
  static_cast<std::uint8_t *>(patch)[anchor.size()] = 0xC3;
  if (!MakeExecutable(patch, 4096)) return Fail("patch protect failed");

  constexpr std::uintptr_t module_base = 0x10000000;
  std::array<std::array<std::uint64_t, 3>, 3> vtables{};
  vtables[0][2] = module_base + 0x1111;
  vtables[1][2] = module_base + 0x1111;
  vtables[2][2] = module_base +
      xar::bridge::kPhase2PostCallListIdentitySelectedTargetRvaV1;
  std::array<std::uint64_t, 3> callbacks{};
  std::array<std::array<std::uint8_t, 0x78>, 3> tasks{};
  std::array<std::array<std::uint8_t, 0x28>, 3> descriptors{};
  std::array<std::uintptr_t, 3> list{};
  for (std::size_t index = 0; index < 3; ++index) {
    callbacks[index] = reinterpret_cast<std::uintptr_t>(vtables[index].data());
    SetTask(tasks[index],
            reinterpret_cast<std::uintptr_t>(&callbacks[index]),
            static_cast<std::uint32_t>(index));
    SetDescriptor(descriptors[index],
                  reinterpret_cast<std::uintptr_t>(tasks[index].data()),
                  0x2000 + index);
    list[index] = reinterpret_cast<std::uintptr_t>(descriptors[index].data());
  }
  std::array<std::uint8_t, 0x100> frame{};
  SetList(frame, list);

  Phase2PostCallListIdentityStateV1 state{};
  FixtureMemory fixture{};
  Phase2PostCallListIdentityEnvironmentV1 environment{};
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
  if (!xar::bridge::InstallPhase2PostCallListIdentityObserverV1(
          state, environment)) {
    return Fail("observer installation failed");
  }
  if (std::memcmp(patch, anchor.data(), anchor.size()) == 0 ||
      static_cast<const std::uint8_t *>(patch)[0] != 0xFF) {
    return Fail("exact patch not installed");
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
      xar::bridge::ReadPhase2PostCallListIdentityDiagnosticsV1(state);
  if (!diagnostics.installed || diagnostics.failure_flags != 0 ||
      !diagnostics.snapshot_consistent || diagnostics.hit_count != 1 ||
      diagnostics.capture_count != 1 || diagnostics.last_list_count != 3 ||
      diagnostics.last_scan_count != 3 || diagnostics.last_sample_count != 3 ||
      diagnostics.last_histogram_bin_count != 2 ||
      diagnostics.last_sample_overflow_count != 0 ||
      diagnostics.last_histogram_overflow_count != 0 ||
      diagnostics.last_selected_target_count != 1 ||
      diagnostics.histogram[0].count != 2 ||
      diagnostics.histogram[0].first_owner != 0x2000 ||
      diagnostics.histogram[0].last_owner != 0x2001 ||
      diagnostics.samples[2].callback_slot2_rva !=
          xar::bridge::kPhase2PostCallListIdentitySelectedTargetRvaV1 ||
      diagnostics.samples[2].task !=
          reinterpret_cast<std::uintptr_t>(tasks[2].data())) {
    return Fail("identity/histogram capture mismatch");
  }

  constexpr std::size_t overflow_count =
      xar::bridge::kPhase2PostCallListIdentitySampleCapacityV1 + 1;
  std::vector<std::array<std::uint64_t, 3>> overflow_vtables(overflow_count);
  std::vector<std::uint64_t> overflow_callbacks(overflow_count);
  std::vector<std::array<std::uint8_t, 0x78>> overflow_tasks(overflow_count);
  std::vector<std::array<std::uint8_t, 0x28>> overflow_descriptors(
      overflow_count);
  std::vector<std::uintptr_t> overflow_list(overflow_count);
  for (std::size_t index = 0; index < overflow_count; ++index) {
    overflow_vtables[index][2] = module_base + 0x4000 + index;
    overflow_callbacks[index] =
        reinterpret_cast<std::uintptr_t>(overflow_vtables[index].data());
    SetTask(overflow_tasks[index],
            reinterpret_cast<std::uintptr_t>(&overflow_callbacks[index]), 0);
    SetDescriptor(overflow_descriptors[index],
                  reinterpret_cast<std::uintptr_t>(overflow_tasks[index].data()),
                  0x9000 + index);
    overflow_list[index] =
        reinterpret_cast<std::uintptr_t>(overflow_descriptors[index].data());
  }
  const auto overflow_begin =
      reinterpret_cast<std::uintptr_t>(overflow_list.data());
  const auto overflow_size = static_cast<std::uint32_t>(overflow_count);
  std::memcpy(frame.data() + 0xE0, &overflow_begin, sizeof(overflow_begin));
  std::memcpy(frame.data() + 0xEC, &overflow_size, sizeof(overflow_size));
  xar::bridge::RecordPhase2PostCallListIdentityObservationV1(
      state, reinterpret_cast<std::uintptr_t>(frame.data()), 7, 1234);
  diagnostics =
      xar::bridge::ReadPhase2PostCallListIdentityDiagnosticsV1(state);
  if (diagnostics.last_sample_count != 64 ||
      diagnostics.last_sample_overflow_count != 1 ||
      diagnostics.last_histogram_bin_count != 64 ||
      diagnostics.last_histogram_overflow_count != 1) {
    return Fail("bounded capacity telemetry mismatch");
  }

  if (!xar::bridge::UninstallPhase2PostCallListIdentityObserverV1(state) ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0) {
    return Fail("uninstall did not restore exact anchor");
  }
  Phase2PostCallListIdentityStateV1 rollback_state{};
  FixtureMemory rollback_fixture{};
  rollback_fixture.fail_flush_call = 2;
  environment.memory_context = &rollback_fixture;
  if (xar::bridge::InstallPhase2PostCallListIdentityObserverV1(
          rollback_state, environment) ||
      rollback_state.installed.load() != 0 || rollback_state.stub != nullptr ||
      std::memcmp(patch, anchor.data(), anchor.size()) != 0 ||
      (rollback_state.failure_flags.load() &
       xar::bridge::phase2_post_call_list_identity_failure_flush) == 0) {
    return Fail("recoverable rollback mismatch");
  }

  VirtualFree(runner_memory, 0, MEM_RELEASE);
  VirtualFree(patch, 0, MEM_RELEASE);
  std::cout << "phase2-post-call-list-identity-observer-v1=GREEN\n";
  return 0;
}
