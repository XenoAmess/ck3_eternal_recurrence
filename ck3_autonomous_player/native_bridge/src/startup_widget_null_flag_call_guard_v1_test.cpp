#include "xar_bridge/startup_widget_null_flag_call_guard_v1.hpp"

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
std::atomic<std::uintptr_t> g_last_r8{0};

constexpr std::array<std::uint8_t, 13> kPatchAnchor{
    0x45, 0x33, 0xC0, 0xB2, 0x01, 0x48, 0x8B,
    0xCF, 0xE8, 0x43, 0x7C, 0xBA, 0x02};

extern "C" __declspec(noinline) void SyntheticCallTarget(
    std::uintptr_t rcx, std::uintptr_t rdx, std::uintptr_t r8) noexcept {
  g_last_rcx.store(rcx, std::memory_order_relaxed);
  g_last_rdx.store(rdx, std::memory_order_relaxed);
  g_last_r8.store(r8, std::memory_order_relaxed);
  g_call_count.fetch_add(1, std::memory_order_relaxed);
}

void WriteU64(std::uint8_t *destination, std::uintptr_t value) {
  const auto encoded = static_cast<std::uint64_t>(value);
  std::memcpy(destination, &encoded, sizeof(encoded));
}

struct SyntheticCaller {
  static constexpr std::size_t kAllocationBytes = 4096;
  static constexpr std::size_t kPatchOffset = 8;
  static constexpr std::size_t kContinueOffset = kPatchOffset + 13;

  std::uint8_t *code = nullptr;

  SyntheticCaller() {
    code = static_cast<std::uint8_t *>(VirtualAlloc(
        nullptr, kAllocationBytes, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    if (code == nullptr) {
      return;
    }
    std::memset(code, 0xCC, kAllocationBytes);
    const std::array<std::uint8_t, kPatchOffset> prefix{
        0x57,                         // push rdi
        0x48, 0x83, 0xEC, 0x20,       // sub rsp, 20h (shadow space)
        0x48, 0x8B, 0xF9};            // mov rdi, rcx
    std::memcpy(code, prefix.data(), prefix.size());
    std::memcpy(code + kPatchOffset, kPatchAnchor.data(),
                kPatchAnchor.size());
    const std::array<std::uint8_t, 6> suffix{
        0x48, 0x83, 0xC4, 0x20, 0x5F, 0xC3}; // add rsp,20h; pop rdi; ret
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

  xar::bridge::StartupWidgetNullFlagCallGuardV1Environment Environment() {
    xar::bridge::StartupWidgetNullFlagCallGuardV1Environment environment{};
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

  void Invoke(void *widget) const {
    using Function = void (*)(void *) noexcept;
    reinterpret_cast<Function>(code)(widget);
  }
};

bool IsOriginal(const SyntheticCaller &fixture) {
  return std::memcmp(fixture.code + SyntheticCaller::kPatchOffset,
                     kPatchAnchor.data(), kPatchAnchor.size()) == 0;
}

bool TestAdmissionAndAnchor() {
  using namespace xar::bridge;
  StartupWidgetNullFlagCallGuardV1Environment environment{};
  environment.primary_thread_suspended_proven = true;
  environment.module_base = 0x140000000ULL;

  g_failure_stage = "exact_build_gate";
  StartupWidgetNullFlagCallGuardV1State exact_state{};
  if (InstallStartupWidgetNullFlagCallGuardV1(exact_state, environment) ||
      (exact_state.failure_flags.load() &
       startup_widget_null_flag_call_guard_failure_exact_build) == 0) {
    return false;
  }

  g_failure_stage = "suspended_gate";
  environment.exact_build_admitted = true;
  environment.primary_thread_suspended_proven = false;
  StartupWidgetNullFlagCallGuardV1State suspended_state{};
  if (InstallStartupWidgetNullFlagCallGuardV1(suspended_state, environment) ||
      (suspended_state.failure_flags.load() &
       startup_widget_null_flag_call_guard_failure_primary_thread_suspended) ==
          0) {
    return false;
  }

  g_failure_stage = "production_override_gate";
  environment.primary_thread_suspended_proven = true;
  environment.patch_target_override = 1;
  StartupWidgetNullFlagCallGuardV1State override_state{};
  if (InstallStartupWidgetNullFlagCallGuardV1(override_state, environment) ||
      (override_state.failure_flags.load() &
       startup_widget_null_flag_call_guard_failure_unsupported_override) == 0) {
    return false;
  }

  g_failure_stage = "anchor_drift";
  SyntheticCaller fixture;
  if (!fixture.valid() || !fixture.DriftAnchor()) {
    return false;
  }
  auto fixture_environment = fixture.Environment();
  StartupWidgetNullFlagCallGuardV1State drift_state{};
  return !InstallStartupWidgetNullFlagCallGuardV1(drift_state,
                                                   fixture_environment) &&
      (drift_state.failure_flags.load() &
       startup_widget_null_flag_call_guard_failure_anchor) != 0 &&
      drift_state.stub == nullptr;
}

bool TestExecutableSemantics() {
  using namespace xar::bridge;
  g_failure_stage = "fixture";
  SyntheticCaller fixture;
  if (!fixture.valid()) {
    return false;
  }
  StartupWidgetNullFlagCallGuardV1State state{};
  const auto environment = fixture.Environment();
  g_failure_stage = "install";
  if (!InstallStartupWidgetNullFlagCallGuardV1(state, environment)) {
    return false;
  }
  if (state.original_patch_bytes != kPatchAnchor ||
      state.installed_patch_bytes[0] != 0x49 ||
      state.installed_patch_bytes[1] != 0xBB ||
      state.installed_patch_bytes[10] != 0x41 ||
      state.installed_patch_bytes[11] != 0xFF ||
      state.installed_patch_bytes[12] != 0xE3) {
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
  std::memcpy(&call_target, stub + 15, sizeof(call_target));
  std::memcpy(&counter_target, stub + 30, sizeof(counter_target));
  std::memcpy(&continue_target, stub + 44, sizeof(continue_target));
  if (std::memcmp(stub, "\x45\x33\xC0\xB2\x01\x48\x8B\xCF\x48\x85\xFF\x74\x0F", 13) != 0 ||
      call_target != reinterpret_cast<std::uintptr_t>(&SyntheticCallTarget) ||
      counter_target !=
          reinterpret_cast<std::uintptr_t>(&state.suppressed_count) ||
      continue_target != environment.continue_target_override ||
      std::memcmp(stub + 23, "\x41\xFF\xD3\xEB\x0E", 5) != 0 ||
      std::memcmp(stub + 38, "\xF0\x49\xFF\x03", 4) != 0 ||
      std::memcmp(stub + 52, "\x41\xFF\xE3", 3) != 0) {
    return false;
  }

  g_call_count.store(0);
  g_last_rcx.store(0);
  g_last_rdx.store(0);
  g_last_r8.store(1);
  g_failure_stage = "null_skips_only_call";
  fixture.Invoke(nullptr);
  auto diagnostics = ReadStartupWidgetNullFlagCallGuardV1Diagnostics(state);
  if (g_call_count.load() != 0 || diagnostics.suppressed_count != 1) {
    return false;
  }

  std::array<std::uint8_t, 0x100> widget{};
  g_failure_stage = "nonnull_replays_call";
  fixture.Invoke(widget.data());
  diagnostics = ReadStartupWidgetNullFlagCallGuardV1Diagnostics(state);
  if (g_call_count.load() != 1 ||
      g_last_rcx.load() != reinterpret_cast<std::uintptr_t>(widget.data()) ||
      (g_last_rdx.load() & 0xFFU) != 1 || g_last_r8.load() != 0 ||
      diagnostics.suppressed_count != 1) {
    return false;
  }

  g_failure_stage = "exclusive_owner";
  StartupWidgetNullFlagCallGuardV1State second_state{};
  if (InstallStartupWidgetNullFlagCallGuardV1(second_state, environment) ||
      (second_state.failure_flags.load() &
       startup_widget_null_flag_call_guard_failure_already_installed) == 0) {
    return false;
  }

  g_failure_stage = "uninstall";
  if (!UninstallStartupWidgetNullFlagCallGuardV1(state) ||
      state.stub != nullptr || state.installed.load() != 0 ||
      !IsOriginal(fixture)) {
    return false;
  }
  // The restored fixture deliberately carries the production rel32 bytes,
  // whose destination is meaningful only at the production RVA. Byte identity
  // is the uninstall assertion; do not execute that synthetic rel32 call.
  return g_call_count.load() == 1;
}

} // namespace

int main() {
  const bool ok = TestAdmissionAndAnchor() && TestExecutableSemantics();
  if (!ok) {
    std::fprintf(stderr,
                 "startup widget null flag-call guard test failed at %s\n",
                 g_failure_stage);
    return 1;
  }
  std::puts("startup widget null flag-call guard test passed");
  return 0;
}
