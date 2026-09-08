#pragma once

#include <windows.h>

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kCoatOfArmsDesignerProbeV1Capability =
    "game.command.probe-coat-of-arms-source-v1";
inline constexpr std::string_view kCoatOfArmsDesignerProbeV1Step =
    "probe-coat-of-arms-source-v1";
inline constexpr std::string_view kCoatOfArmsDesignerProbeV1BackendId =
    "ck3-1.19.0.6-native-coat-of-arms-designer-probe-v1";
inline constexpr std::uintptr_t kCoatOfArmsUpdatePasteContentsRvaV1 = 0xB73500;
inline constexpr std::uintptr_t kCoatOfArmsPasteFromClipboardRvaV1 = 0xB71F00;
inline constexpr std::uintptr_t kClipboardWriteFunctionSlotRvaV1 = 0x4FE09A8;
inline constexpr std::uintptr_t kClipboardReadFunctionSlotRvaV1 = 0x4FE09B0;
inline constexpr std::uintptr_t kClipboardFreeFunctionSlotRvaV1 = 0x4FE1260;
inline constexpr std::size_t kCoatOfArmsUpdatePastePatchBytesV1 = 19;
inline constexpr std::size_t kCoatOfArmsProbeMaximumSourceBytesV1 =
    128U * 1024U;
inline constexpr std::uint32_t
    kCoatOfArmsDesignerProbeQueuedWaitBudgetMillisecondsV1 = 8'000;
inline constexpr std::uint32_t
    kCoatOfArmsDesignerProbeExecutingWaitSliceMillisecondsV1 = 2'000;

enum CoatOfArmsDesignerProbeInstallFailureV1 : std::uint32_t {
  coat_of_arms_probe_install_failure_none = 0,
  coat_of_arms_probe_install_failure_exact_build = 1U << 0,
  coat_of_arms_probe_install_failure_update_target_identity = 1U << 1,
  coat_of_arms_probe_install_failure_paste_target_identity = 1U << 2,
  coat_of_arms_probe_install_failure_clipboard_functions = 1U << 3,
  coat_of_arms_probe_install_failure_trampoline = 1U << 4,
  coat_of_arms_probe_install_failure_page_protect = 1U << 5,
};

enum class CoatOfArmsDesignerProbeRequestStateV1 : std::uint32_t {
  idle = 0,
  queued = 1,
  executing = 2,
  completed = 3,
  cancelled = 4,
};

enum class CoatOfArmsDesignerProbeSubmitResultV1 : std::uint32_t {
  submitted = 0,
  hook_unavailable = 1,
  busy = 2,
  invalid_request = 3,
  event_unavailable = 4,
};

enum class CoatOfArmsDesignerProbeWaitResultV1 : std::uint32_t {
  completed = 0,
  timeout_cancelled_before_execution = 1,
  timeout_executor_already_running = 2,
  infrastructure_failed = 3,
};

struct CoatOfArmsDesignerProbeResultV1 {
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::size_t source_bytes = 0;
  bool designer_observed = false;
  bool clipboard_written = false;
  bool clipboard_readback_matched = false;
  bool detected = false;
  bool apply_requested = false;
  bool paste_invoked = false;
  bool applied = false;
  std::uint32_t candidate_index = 0;
  std::uint32_t preview_coat_of_arms_handle = 0;
  std::uint32_t active_coat_of_arms_index = 0;
  std::string reason;
};

struct CoatOfArmsDesignerProbeRequestV1 {
  std::atomic<CoatOfArmsDesignerProbeRequestStateV1> state{
      CoatOfArmsDesignerProbeRequestStateV1::idle};
  HANDLE completion_event = nullptr;
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t date_raw = 0;
  std::string source;
  bool apply = false;
  CoatOfArmsDesignerProbeResultV1 result{};

  CoatOfArmsDesignerProbeRequestV1() = default;
  CoatOfArmsDesignerProbeRequestV1(const CoatOfArmsDesignerProbeRequestV1 &) =
      delete;
  CoatOfArmsDesignerProbeRequestV1 &
  operator=(const CoatOfArmsDesignerProbeRequestV1 &) = delete;
};

struct CoatOfArmsDesignerProbeHookStateV1 {
  std::atomic<CoatOfArmsDesignerProbeRequestV1 *> pending_request{nullptr};
  std::atomic<std::uint64_t> observed_calls{0};
  std::atomic<std::uint64_t> executed_requests{0};
  std::atomic<std::uint32_t> active_hook_calls{0};
  std::atomic<std::uint32_t> failure_flags{0};
  std::atomic<bool> installed{false};
  std::uintptr_t module_base = 0;
  bool exact_build_admitted = false;
  void *update_target = nullptr;
  void *update_trampoline = nullptr;
  void *paste_from_clipboard = nullptr;
  void *clipboard_write_slot = nullptr;
  void *clipboard_read_slot = nullptr;
  void *clipboard_free_slot = nullptr;
  std::array<std::uint8_t, kCoatOfArmsUpdatePastePatchBytesV1> original_bytes{};
};

bool InstallCoatOfArmsDesignerProbeHookV1(
    CoatOfArmsDesignerProbeHookStateV1 &state, std::uintptr_t module_base,
    bool exact_build_admitted) noexcept;

bool RetryDeferredCoatOfArmsDesignerProbeHookV1(
    CoatOfArmsDesignerProbeHookStateV1 &state) noexcept;

CoatOfArmsDesignerProbeSubmitResultV1 TrySubmitCoatOfArmsDesignerProbeV1(
    CoatOfArmsDesignerProbeHookStateV1 &hook,
    CoatOfArmsDesignerProbeRequestV1 &request) noexcept;

CoatOfArmsDesignerProbeWaitResultV1
WaitForCoatOfArmsDesignerProbeV1(CoatOfArmsDesignerProbeRequestV1 &request,
                                 std::uint32_t timeout_milliseconds) noexcept;

bool ReclaimCoatOfArmsDesignerProbeV1(
    CoatOfArmsDesignerProbeHookStateV1 &hook,
    CoatOfArmsDesignerProbeRequestV1 &request) noexcept;

std::string_view CoatOfArmsDesignerProbeFailureMessageV1(
    CoatOfArmsDesignerProbeWaitResultV1 wait) noexcept;

extern "C" void __fastcall
XarCoatOfArmsUpdatePasteContentsHookV1(void *designer) noexcept;

} // namespace xar::ck3_11906
