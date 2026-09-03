#include "xar_bridge/startup_rbx_null_call_guard_v1.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace {

const char *g_failure_stage = "not_started";
std::atomic<std::uint64_t> g_call_count{0};
std::atomic<std::uintptr_t> g_last_rcx{0};
std::atomic<std::uintptr_t> g_last_rdx{0};

constexpr std::array<std::uint8_t, 16> kPatchAnchor{
    0x48, 0x89, 0x5D, 0x6F, 0x48, 0x8B, 0x55, 0x77,
    0x48, 0x8B, 0xCB, 0xE8, 0x3E, 0xC9, 0x25, 0x00};

extern "C" __declspec(noinline) void SyntheticCallTarget(
    std::uintptr_t rcx, std::uintptr_t rdx) noexcept {
  g_last_rcx.store(rcx, std::memory_order_relaxed);
  g_last_rdx.store(rdx, std::memory_order_relaxed);
  g_call_count.fetch_add(1, std::memory_order_relaxed);
}

void WriteU64(std::uint8_t *destination, std::uintptr_t value) {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(destination, &encoded, sizeof(encoded));
}

struct SyntheticCaller {
  static constexpr std::size_t kAllocationBytes = 4096;
  static constexpr std::size_t kPatchOffset = 12;
  static constexpr std::size_t kContinueOffset = kPatchOffset + 16;

  std::uint8_t *code = nullptr;
  alignas(8) std::array<std::uint8_t, 0x100> frame{};

  SyntheticCaller() {
    code = static_cast<std::uint8_t *>(VirtualAlloc(
        nullptr, kAllocationBytes, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    if (code == nullptr) {
      return;
    }
    std::memset(code, 0xCC, kAllocationBytes);
    const std::array<std::uint8_t, kPatchOffset> prefix{
        0x55, 0x53,                   // push rbp; push rbx
        0x48, 0x83, 0xEC, 0x28,       // sub rsp, 28h
        0x48, 0x8B, 0xD9,             // mov rbx, rcx
        0x48, 0x8B, 0xEA};            // mov rbp, rdx
    std::memcpy(code, prefix.data(), prefix.size());
    std::memcpy(code + kPatchOffset, kPatchAnchor.data(),
                kPatchAnchor.size());
    const std::array<std::uint8_t, 7> suffix{
        0x48, 0x83, 0xC4, 0x28, 0x5B, 0x5D, 0xC3};
    std::memcpy(code + kContinueOffset, suffix.data(), suffix.size());
    DWORD previous = 0;
    if (VirtualProtect(code, kAllocationBytes, PAGE_EXECUTE_READ, &previous) ==
            FALSE ||
        previous != PAGE_READWRITE ||
        FlushInstructionCache(GetCurrentProcess(), code, kAllocationBytes) ==
            FALSE) {
      (void)VirtualFree(code, 0, MEM_RELEASE);
      code = nullptr;
    }
  }

  ~SyntheticCaller() {
    if (code != nullptr) {
      (void)VirtualFree(code, 0, MEM_RELEASE);
    }
  }

  SyntheticCaller(const SyntheticCaller &) = delete;
  SyntheticCaller &operator=(const SyntheticCaller &) = delete;

  bool valid() const noexcept { return code != nullptr; }

  xar::bridge::StartupRbxNullCallGuardV1Environment Environment() {
    xar::bridge::StartupRbxNullCallGuardV1Environment environment{};
    environment.exact_build_admitted = true;
    environment.primary_thread_suspended_proven = true;
    environment.offline_fixture = true;
    environment.module_base = 0x140000000ULL;
    environment.patch_target_override =
        reinterpret_cast<std::uintptr_t>(code + kPatchOffset);
    environment.continue_target_override =
        reinterpret_cast<std::uintptr_t>(code + kContinueOffset);
    environment.call_target_override =
        reinterpret_cast<std::uintptr_t>(&SyntheticCallTarget);
    return environment;
  }

  bool DriftAnchor() noexcept {
    DWORD previous = 0;
    if (code == nullptr ||
        VirtualProtect(code, kAllocationBytes, PAGE_EXECUTE_READWRITE,
                       &previous) == FALSE ||
        previous != PAGE_EXECUTE_READ) {
      return false;
    }
    code[kPatchOffset + 1] ^= 1U;
    const bool flushed =
        FlushInstructionCache(GetCurrentProcess(), code + kPatchOffset, 1) !=
        FALSE;
    DWORD ignored = 0;
    return VirtualProtect(code, kAllocationBytes, previous, &ignored) !=
               FALSE &&
        flushed;
  }

  void SetCallArgument(std::uintptr_t value) noexcept {
    std::memcpy(frame.data() + 0x77, &value, sizeof(value));
  }

  std::uintptr_t StoredRbx() const noexcept {
    std::uintptr_t value = 0;
    std::memcpy(&value, frame.data() + 0x6F, sizeof(value));
    return value;
  }

  void Invoke(void *rbx_value) {
    using Function = void (*)(void *, void *) noexcept;
    reinterpret_cast<Function>(code)(rbx_value, frame.data());
  }
};

bool IsOriginal(const SyntheticCaller &fixture) {
  return std::memcmp(fixture.code + SyntheticCaller::kPatchOffset,
                     kPatchAnchor.data(), kPatchAnchor.size()) == 0;
}

bool TestAdmissionAndAnchor() {
  using namespace xar::bridge;
  StartupRbxNullCallGuardV1Environment environment{};
  environment.primary_thread_suspended_proven = true;
  environment.module_base = 0x140000000ULL;

  g_failure_stage = "exact_build_gate";
  StartupRbxNullCallGuardV1State exact_state{};
  if (InstallStartupRbxNullCallGuardV1(exact_state, environment) ||
      (exact_state.failure_flags.load() &
       startup_rbx_null_call_guard_failure_exact_build) == 0) {
    return false;
  }

  g_failure_stage = "suspended_gate";
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = false;
  StartupRbxNullCallGuardV1State suspended_state{};
  if (InstallStartupRbxNullCallGuardV1(suspended_state, environment) ||
      (suspended_state.failure_flags.load() &
       startup_rbx_null_call_guard_failure_primary_thread_suspended) ==
          0) {
    return false;
  }

  g_failure_stage = "production_override_gate";
  environment.primary_thread_suspended_proven = true;
  environment.patch_target_override = 1;
  StartupRbxNullCallGuardV1State override_state{};
  if (InstallStartupRbxNullCallGuardV1(override_state, environment) ||
      (override_state.failure_flags.load() &
       startup_rbx_null_call_guard_failure_unsupported_override) == 0) {
    return false;
  }

  g_failure_stage = "anchor_drift";
  SyntheticCaller fixture;
  if (!fixture.valid() || !fixture.DriftAnchor()) {
    return false;
  }
  auto fixture_environment = fixture.Environment();
  StartupRbxNullCallGuardV1State drift_state{};
  return !InstallStartupRbxNullCallGuardV1(drift_state,
                                                   fixture_environment) &&
      (drift_state.failure_flags.load() &
       startup_rbx_null_call_guard_failure_anchor) != 0 &&
      drift_state.stub == nullptr;
}

bool TestExecutableSemantics() {
  using namespace xar::bridge;
  g_failure_stage = "fixture";
  SyntheticCaller fixture;
  if (!fixture.valid()) {
    return false;
  }
  StartupRbxNullCallGuardV1State state{};
  const auto environment = fixture.Environment();
  g_failure_stage = "install";
  if (!InstallStartupRbxNullCallGuardV1(state, environment)) {
    return false;
  }
  if (state.original_patch_bytes != kPatchAnchor ||
      state.installed_patch_bytes[0] != 0x49 ||
      state.installed_patch_bytes[1] != 0xBB ||
      state.installed_patch_bytes[10] != 0x41 ||
      state.installed_patch_bytes[11] != 0xFF ||
      state.installed_patch_bytes[12] != 0xE3 ||
      state.installed_patch_bytes[13] != 0x90 ||
      state.installed_patch_bytes[14] != 0x90 ||
      state.installed_patch_bytes[15] != 0x90) {
    return false;
  }
  MEMORY_BASIC_INFORMATION stub_memory{};
  if (VirtualQuery(state.stub, &stub_memory, sizeof(stub_memory)) == 0 ||
      stub_memory.Protect != PAGE_EXECUTE_READ) {
    return false;
  }
  const auto *stub = static_cast<const std::uint8_t *>(state.stub);
  std::uint64_t call_target = 0;
  std::uint64_t counter_target = 0;
  std::uint64_t continue_target = 0;
  std::memcpy(&call_target, stub + 18, sizeof(call_target));
  std::memcpy(&counter_target, stub + 33, sizeof(counter_target));
  std::memcpy(&continue_target, stub + 47, sizeof(continue_target));
  if (std::memcmp(stub,
                  "\x48\x89\x5D\x6F\x48\x85\xDB\x74\x16"
                  "\x48\x8B\x55\x77\x48\x8B\xCB",
                  16) != 0 ||
      call_target != reinterpret_cast<std::uintptr_t>(&SyntheticCallTarget) ||
      counter_target !=
          reinterpret_cast<std::uintptr_t>(&state.suppressed_count) ||
      continue_target != environment.continue_target_override ||
      std::memcmp(stub + 26, "\x41\xFF\xD3\xEB\x0E", 5) != 0 ||
      std::memcmp(stub + 41, "\xF0\x49\xFF\x03", 4) != 0 ||
      std::memcmp(stub + 55, "\x41\xFF\xE3", 3) != 0) {
    return false;
  }

  g_call_count.store(0);
  g_last_rcx.store(0);
  g_last_rdx.store(0);
  constexpr std::uintptr_t kExpectedRdx = 0x123456789ABCDEF0ULL;
  fixture.SetCallArgument(kExpectedRdx);
  g_failure_stage = "null_skips_only_call";
  fixture.Invoke(nullptr);
  auto diagnostics = ReadStartupRbxNullCallGuardV1Diagnostics(state);
  if (g_call_count.load() != 0 || diagnostics.suppressed_count != 1 ||
      fixture.StoredRbx() != 0) {
    return false;
  }

  std::array<std::uint8_t, 0x100> object{};
  g_failure_stage = "nonnull_replays_call";
  fixture.Invoke(object.data());
  diagnostics = ReadStartupRbxNullCallGuardV1Diagnostics(state);
  if (g_call_count.load() != 1 ||
      g_last_rcx.load() != reinterpret_cast<std::uintptr_t>(object.data()) ||
      g_last_rdx.load() != kExpectedRdx ||
      fixture.StoredRbx() != reinterpret_cast<std::uintptr_t>(object.data()) ||
      diagnostics.suppressed_count != 1) {
    return false;
  }

  g_failure_stage = "exclusive_owner";
  StartupRbxNullCallGuardV1State second_state{};
  if (InstallStartupRbxNullCallGuardV1(second_state, environment) ||
      (second_state.failure_flags.load() &
       startup_rbx_null_call_guard_failure_already_installed) == 0) {
    return false;
  }

  g_failure_stage = "uninstall";
  if (!UninstallStartupRbxNullCallGuardV1(state) ||
      state.stub != nullptr || state.installed.load() != 0 ||
      !IsOriginal(fixture)) {
    return false;
  }
  // The restored fixture deliberately carries production rel32 bytes,
  // whose destination is meaningful only at the production RVA. Byte identity
  // is the uninstall assertion; do not execute that synthetic rel32 call.
  return g_call_count.load() == 1;
}

} // namespace

int main() {
  const bool ok = TestAdmissionAndAnchor() && TestExecutableSemantics();
  if (!ok) {
    std::fprintf(stderr,
                 "startup RBX-null call guard test failed at %s\n",
                 g_failure_stage);
    return 1;
  }
  std::puts("startup RBX-null call guard test passed");
  return 0;
}
