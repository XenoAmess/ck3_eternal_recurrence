#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <cstdint>

namespace xar::bridge {

enum class ActivityPilgrimagePlannerOpenStatusV1 {
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

using ActivityPilgrimageCanPlanV1 = bool (*)(void *, std::uintptr_t, bool &) noexcept;

using ActivityPilgrimageDispatchV1 =
    bool (*)(void *, std::uintptr_t, std::uintptr_t) noexcept;

struct ActivityPilgrimagePlannerOpenEnvironmentV1 {
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityPilgrimageDispatchV1 dispatch = nullptr;
  ActivityPilgrimageCanPlanV1 can_plan = nullptr;
};

struct ActivityPilgrimagePlannerOpenResultV1 {
  ActivityPilgrimagePlannerOpenStatusV1 status =
      ActivityPilgrimagePlannerOpenStatusV1::exact_build_rejected;
  ActivityPlannerDiagResultV1 before{};
  ActivityPlannerDiagResultV1 after{};
  bool native_dispatch_invoked = false;
  bool needs_recovery = false;
  bool can_plan_observed = false;
  bool can_plan = false;
  bool selected_pilgrimage_verified = false;
};

ActivityPilgrimagePlannerOpenResultV1 OpenActivityPilgrimagePlannerV1(
    const ActivityPilgrimagePlannerOpenEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

const char *ActivityPilgrimagePlannerOpenStatusKeyV1(
    ActivityPilgrimagePlannerOpenStatusV1 status) noexcept;

} // namespace xar::bridge
