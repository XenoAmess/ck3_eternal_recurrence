#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityPlannerDiagExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

enum class ActivityPlannerDiagStatusV1 {
  observed,
  planner_absent,
  frame_unavailable,
  frame_changed,
  exact_build_rejected,
  native_owner_unavailable,
  native_identity_mismatch,
  native_read_failed,
  native_sample_changed,
};

struct ActivityPlannerDiagFrameV1 {
  std::uint64_t revision = 0;
  std::int64_t date_raw = 0;
  std::int32_t actor_character_id = 0;
  bool application_main_thread = false;
  bool paused = false;
  bool map_ready = false;
  bool actor_alive = false;

  friend bool operator==(const ActivityPlannerDiagFrameV1 &,
                         const ActivityPlannerDiagFrameV1 &) = default;
};

struct ActivityPlannerDiagValueV1 {
  bool planner_present = false;
  bool widget_attached = false;
  bool widget_visible = false;
  std::int32_t stage = -1;
  bool host_view_activity_key_known = false;
  std::array<char, 96> host_view_activity_key{};
  std::uint16_t host_view_activity_key_size = 0;

  friend bool operator==(const ActivityPlannerDiagValueV1 &,
                         const ActivityPlannerDiagValueV1 &) = default;
};

using ActivityPlannerDiagReadMemoryV1 =
    bool (*)(void *, std::uintptr_t, void *, std::size_t) noexcept;
using ActivityPlannerDiagReadFrameV1 =
    bool (*)(void *, ActivityPlannerDiagFrameV1 &) noexcept;
using ActivityPlannerDiagRttiCastV1 =
    std::uintptr_t (*)(void *, std::uintptr_t, std::uintptr_t,
                      std::uintptr_t) noexcept;
using ActivityPlannerDiagVisibleV1 =
    bool (*)(void *, std::uintptr_t, std::uintptr_t, bool &) noexcept;

struct ActivityPlannerDiagEnvironmentV1 {
  bool enabled = false;
  std::string_view admitted_executable_sha256{};
  std::uintptr_t module_base = 0;
  void *context = nullptr;
  ActivityPlannerDiagReadMemoryV1 read_memory = nullptr;
  ActivityPlannerDiagReadFrameV1 read_frame = nullptr;
  ActivityPlannerDiagRttiCastV1 rtti_cast = nullptr;
  ActivityPlannerDiagVisibleV1 invoke_visibility = nullptr;
};

struct ActivityPlannerDiagResultV1 {
  ActivityPlannerDiagStatusV1 status =
      ActivityPlannerDiagStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  ActivityPlannerDiagValueV1 value{};
};

ActivityPlannerDiagResultV1 ReadActivityPlannerDiagV1(
    const ActivityPlannerDiagEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

std::string_view ActivityPlannerDiagStatusKeyV1(
    ActivityPlannerDiagStatusV1 status) noexcept;

} // namespace xar::bridge
