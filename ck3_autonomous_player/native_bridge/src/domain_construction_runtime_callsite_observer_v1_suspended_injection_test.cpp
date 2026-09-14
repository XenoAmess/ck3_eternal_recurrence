#include "xar_bridge/domain_construction_runtime_callsite_observer_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>
#include <string_view>

namespace {

using xar::bridge::DomainConstructionRuntimeCaptureAdmissionV1;
using xar::bridge::DomainConstructionRuntimeObserverEnvironmentV1;
using xar::bridge::DomainConstructionRuntimeObserverStateV1;

constexpr std::array<std::uint8_t, 16> kAnchor{
    0x48, 0x8D, 0x55, 0x60,
    0x48, 0x8B, 0xCE,
    0xE8, 0xBC, 0xEE, 0x04, 0x00,
    0x48, 0x8D, 0x45, 0xD0};

struct SuspendedTarget {
  PROCESS_INFORMATION process{};
  void *remote_target = nullptr;
};

void CloseSuspendedTarget(SuspendedTarget &target) {
  if (target.process.hProcess != nullptr) {
    (void)TerminateProcess(target.process.hProcess, 0);
    (void)WaitForSingleObject(target.process.hProcess, 5000);
  }
  if (target.process.hThread != nullptr) CloseHandle(target.process.hThread);
  if (target.process.hProcess != nullptr) CloseHandle(target.process.hProcess);
  target = {};
}

bool CreateSuspendedSelf(SuspendedTarget &target) {
  std::array<wchar_t, 32768> path{};
  const DWORD length = GetModuleFileNameW(nullptr, path.data(),
                                          static_cast<DWORD>(path.size()));
  if (length == 0 || length >= path.size()) return false;
  std::wstring command_line = L"\"";
  command_line.append(path.data(), length);
  command_line += L"\" --suspended-child";
  STARTUPINFOW startup{};
  startup.cb = sizeof(startup);
  if (!CreateProcessW(path.data(), command_line.data(), nullptr, nullptr,
                      FALSE, CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT,
                      nullptr, nullptr, &startup, &target.process)) {
    return false;
  }
  target.remote_target = VirtualAllocEx(
      target.process.hProcess, nullptr, 4096, MEM_RESERVE | MEM_COMMIT,
      PAGE_READWRITE);
  if (target.remote_target == nullptr) {
    CloseSuspendedTarget(target);
    return false;
  }
  SIZE_T written = 0;
  if (!WriteProcessMemory(target.process.hProcess, target.remote_target,
                          kAnchor.data(), kAnchor.size(), &written) ||
      written != kAnchor.size()) {
    CloseSuspendedTarget(target);
    return false;
  }
  DWORD previous = 0;
  if (!VirtualProtectEx(target.process.hProcess, target.remote_target, 4096,
                        PAGE_EXECUTE_READ, &previous)) {
    CloseSuspendedTarget(target);
    return false;
  }
  return true;
}

bool RemoteRead(void *context, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  auto &target = *static_cast<SuspendedTarget *>(context);
  SIZE_T read = 0;
  return ReadProcessMemory(target.process.hProcess,
                           reinterpret_cast<const void *>(address), output,
                           size, &read) != FALSE && read == size;
}

bool RemoteWrite(void *context, std::uintptr_t address, const void *source,
                 std::size_t size) noexcept {
  auto &target = *static_cast<SuspendedTarget *>(context);
  SIZE_T written = 0;
  return WriteProcessMemory(target.process.hProcess,
                            reinterpret_cast<void *>(address), source, size,
                            &written) != FALSE && written == size;
}

void *RemoteAlloc(void *context, std::size_t size, DWORD allocation_type,
                  DWORD protection) noexcept {
  auto &target = *static_cast<SuspendedTarget *>(context);
  return VirtualAllocEx(target.process.hProcess, nullptr, size,
                        allocation_type, protection);
}

bool RemoteFree(void *context, void *address, std::size_t size,
                DWORD free_type) noexcept {
  auto &target = *static_cast<SuspendedTarget *>(context);
  return VirtualFreeEx(target.process.hProcess, address, size, free_type) !=
      FALSE;
}

bool RemoteProtect(void *context, void *address, std::size_t size,
                   DWORD new_protection, DWORD &old_protection) noexcept {
  auto &target = *static_cast<SuspendedTarget *>(context);
  old_protection = 0;
  return VirtualProtectEx(target.process.hProcess, address, size,
                          new_protection, &old_protection) != FALSE;
}

bool RemoteFlush(void *context, const void *address,
                 std::size_t size) noexcept {
  auto &target = *static_cast<SuspendedTarget *>(context);
  return FlushInstructionCache(target.process.hProcess, address, size) !=
      FALSE;
}

bool FixtureAdmission(
    void *, DomainConstructionRuntimeCaptureAdmissionV1 &output) noexcept {
  output.application_main_thread_id = GetCurrentThreadId();
  output.session_live = true;
  output.paused = false;
  output.proof_epoch = 1;
  return true;
}

DomainConstructionRuntimeObserverEnvironmentV1 FixtureEnvironment(
    SuspendedTarget &target) {
  DomainConstructionRuntimeObserverEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 = xar::bridge::
      kDomainConstructionRuntimeObserverExecutableSha256V1;
  environment.primary_thread_suspended_proven = true;
  environment.offline_fixture = true;
  environment.module_base = 1;
  environment.patch_target_override =
      reinterpret_cast<std::uintptr_t>(target.remote_target);
  environment.continue_target_override =
      reinterpret_cast<std::uintptr_t>(target.remote_target) + kAnchor.size();
  environment.producer_target_override =
      reinterpret_cast<std::uintptr_t>(target.remote_target) + 0x100;
  environment.memory_context = &target;
  environment.memory_read_override = &RemoteRead;
  environment.memory_write_override = &RemoteWrite;
  environment.virtual_alloc_override = &RemoteAlloc;
  environment.virtual_free_override = &RemoteFree;
  environment.virtual_protect_override = &RemoteProtect;
  environment.flush_instruction_cache_override = &RemoteFlush;
  environment.capture_admission_probe = &FixtureAdmission;
  return environment;
}

void TestSuspendedNonCk3ExactHashRejectionAndFixtureTransaction() {
  SuspendedTarget target{};
  assert(CreateSuspendedSelf(target));

  auto wrong_hash = FixtureEnvironment(target);
  wrong_hash.offline_fixture = false;
  wrong_hash.admitted_executable_sha256 =
      "0000000000000000000000000000000000000000000000000000000000000000";
  DomainConstructionRuntimeObserverStateV1 rejected{};
  assert(!xar::bridge::InstallDomainConstructionRuntimeObserverV1(
      rejected, wrong_hash));
  const auto rejection = xar::bridge::
      ReadDomainConstructionRuntimeObserverDiagnosticsV1(rejected);
  assert((rejection.failure_flags & xar::bridge::
          domain_construction_runtime_observer_failure_exact_build) != 0);
  std::array<std::uint8_t, 16> after_rejection{};
  assert(RemoteRead(&target,
                    reinterpret_cast<std::uintptr_t>(target.remote_target),
                    after_rejection.data(), after_rejection.size()));
  assert(after_rejection == kAnchor);

  // Explicit offline fixture mode exercises the remote write/restore
  // transaction while the non-CK3 primary thread remains suspended. The
  // generated stub is deliberately never executed in this process.
  DomainConstructionRuntimeObserverStateV1 fixture{};
  assert(xar::bridge::InstallDomainConstructionRuntimeObserverV1(
      fixture, FixtureEnvironment(target)));
  std::array<std::uint8_t, 16> installed{};
  assert(RemoteRead(&target,
                    reinterpret_cast<std::uintptr_t>(target.remote_target),
                    installed.data(), installed.size()));
  assert(installed[0] == 0xFF && installed[1] == 0x25);
  assert(xar::bridge::UninstallDomainConstructionRuntimeObserverV1(
      fixture));
  std::array<std::uint8_t, 16> restored{};
  assert(RemoteRead(&target,
                    reinterpret_cast<std::uintptr_t>(target.remote_target),
                    restored.data(), restored.size()));
  assert(restored == kAnchor);

  CloseSuspendedTarget(target);
}

} // namespace

int wmain(int argc, wchar_t **argv) {
  if (argc == 2 && std::wstring_view(argv[1]) == L"--suspended-child") {
    return 0;
  }
  TestSuspendedNonCk3ExactHashRejectionAndFixtureTransaction();
  return 0;
}
