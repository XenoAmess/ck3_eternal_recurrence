#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <cstdint>

namespace xar::bridge {

enum class ActivityFeastPlannerOpenStatusV1 {
  opened,
  already_open,
  frame_unavailable,
  frame_changed,
  exact_build_rejected,
  native_precondition_failed,
  type_unavailable,
  type_ambiguous,
  native_call_failed,
  postcondition_failed,
};

using ActivityFeastDispatchV1 =
    bool (*)(void *, std::uintptr_t, std::uintptr_t) noexcept;

struct ActivityFeastPlannerOpenEnvironmentV1 {
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityFeastDispatchV1 dispatch = nullptr;
};

struct ActivityFeastPlannerOpenResultV1 {
  ActivityFeastPlannerOpenStatusV1 status =
      ActivityFeastPlannerOpenStatusV1::exact_build_rejected;
  ActivityPlannerDiagResultV1 before{};
  ActivityPlannerDiagResultV1 after{};
  bool native_dispatch_invoked = false;
};

ActivityFeastPlannerOpenResultV1 OpenActivityFeastPlannerV1(
    const ActivityFeastPlannerOpenEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

const char *ActivityFeastPlannerOpenStatusKeyV1(
    ActivityFeastPlannerOpenStatusV1 status) noexcept;

} // namespace xar::bridge
