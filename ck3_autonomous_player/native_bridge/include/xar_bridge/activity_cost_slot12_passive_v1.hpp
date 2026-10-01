#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityCostSlot12ExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::uintptr_t kActivityCostRefreshRvaV1 = 0x10B2B30;
inline constexpr std::uintptr_t kActivityCostSlot12ReturnRvaV1 = 0x10AE1AF;
inline constexpr std::size_t kActivityCostPatchBytesV1 = 14;

struct ActivityCostSlot12FrameV1 {
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::uint32_t thread_id = 0;
  bool paused = false;
};

using ActivityCostReadMemoryV1 = bool (*)(void *, std::uintptr_t, void *,
                                          std::size_t) noexcept;
using ActivityCostReadFrameV1 = bool (*)(void *,
                                         ActivityCostSlot12FrameV1 &) noexcept;

struct ActivityCostSlot12EnvironmentV1 {
  bool enabled = false;
  bool primary_thread_suspended = false;
  std::string_view executable_sha256{};
  std::uintptr_t module_base = 0;
  void *context = nullptr;
  ActivityCostReadMemoryV1 read_memory = nullptr;
  ActivityCostReadFrameV1 read_frame = nullptr;
};

struct ActivityCostSlot12CaptureV1 {
  std::uint64_t sequence = 0;
  ActivityCostSlot12FrameV1 frame{};
  std::uintptr_t planner = 0;
  std::uintptr_t owner = 0;
  std::uintptr_t activity_type = 0;
  std::int32_t planning_stage = -1;
  std::uint64_t configuration_fingerprint = 0;
  std::array<std::int64_t, 10> raw_aggregate{};
};

enum class ActivityCostSlot12ReadStatusV1 {
  observed,
  exact_build_rejected,
  no_normal_refresh,
  frame_changed,
  configuration_changed,
};

struct ActivityCostSlot12ObserverV1 {
  ActivityCostSlot12EnvironmentV1 environment{};
  std::array<std::uint8_t, kActivityCostPatchBytesV1> original_bytes{};
  void *trampoline = nullptr;
  bool installed = false;
  std::mutex capture_mutex{};
  ActivityCostSlot12CaptureV1 latest{};
};

// Records only normal refresh returns: 1.19.0.6 0x10B2B30 or 1.20.0.2
// 0x11BA6D0 selected by the admitted SHA. It never
// calls the recomputation, ProgressPlanningStage, or a start command.
bool RecordActivityCostSlot12NormalReturnV1(
    ActivityCostSlot12ObserverV1 &observer, std::uintptr_t caller_return,
    std::uintptr_t planner) noexcept;

ActivityCostSlot12ReadStatusV1 ReadActivityCostSlot12PassiveV1(
    ActivityCostSlot12ObserverV1 &observer,
    const ActivityCostSlot12FrameV1 &expected,
    ActivityCostSlot12CaptureV1 &output) noexcept;

bool VerifyActivityCostSlot12ExactAbiV1(
    const ActivityCostSlot12EnvironmentV1 &environment) noexcept;
bool InstallActivityCostSlot12PassiveV1(
    ActivityCostSlot12ObserverV1 &observer,
    const ActivityCostSlot12EnvironmentV1 &environment) noexcept;

} // namespace xar::bridge
