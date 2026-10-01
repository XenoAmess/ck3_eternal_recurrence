#pragma once

#include "xar_bridge/ck3_12002_sway_completion_execution.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002 {

// Native slot 22 has two pointer inputs and a discarded (void) result.
// See ck3_sway_completion12002_execution_install_abi.json before changing it.
using SwayCompletionNativeExecute12002 = void (*)(const void *, const void *);

inline constexpr std::array<std::uintptr_t, 3>
    kSwayCompletionExecuteSlotRvas12002{0x4837330, 0x48374D8, 0x4837410};
inline constexpr std::array<std::uintptr_t, 3>
    kSwayCompletionExecuteRvas12002{0x2CC9440, 0x2CC8490, 0x2CC71A0};

// The root owns this state and recorder through its pinned DLL lifetime.
// Install/uninstall and query belong to the existing owner-thread lifecycle.
struct SwayCompletionExecutionInstall12002 {
  SwayExecutionBindings12002 bindings;
  SwayExecutionRecorder12002 *recorder = nullptr;
  std::array<SwayCompletionNativeExecute12002 *, 3> slots{};
  std::array<SwayCompletionNativeExecute12002, 3> originals{};
  std::array<bool, 3> patched{};
  bool attached = false;
  bool fixture_slots = false;
  const char *unavailable_reason = "sway_execution_observer_not_installed";
};

// Production mode requires the already verified exact image SHA. Only three
// existing function-pointer slots are replaced; no code detour is generated.
bool InstallSwayCompletionExecution12002(
    std::uintptr_t image_base, std::string_view executable_sha256,
    SwayExecutionRecorder12002 &recorder,
    SwayCompletionExecutionInstall12002 &state) noexcept;

// Explicit fixture seam: caller-owned slots and typed originals, never RVA
// substitution or a synthetic complete game image. Production doesn't call it.
bool InstallSwayCompletionExecutionFixture12002(
    const SwayExecutionBindings12002 &bindings,
    const std::array<SwayCompletionNativeExecute12002 *, 3> &slots,
    const std::array<SwayCompletionNativeExecute12002, 3> &expected_originals,
    SwayExecutionRecorder12002 &recorder,
    SwayCompletionExecutionInstall12002 &state) noexcept;

bool UninstallSwayCompletionExecution12002(
    SwayCompletionExecutionInstall12002 &state) noexcept;

} // namespace xar::ck3_12002
