#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

enum class ActivityStage5CanStartStatusV1 {
  observed,
  exact_build_rejected,
  callback_missing,
  planner_unavailable,
  not_stage5,
  selected_type_mismatch,
  native_identity_mismatch,
  native_evaluation_failed,
  frame_changed,
};

using ActivityStage5CanStartPredicateV1 =
    bool (*)(void *, std::uintptr_t, bool &) noexcept;

struct ActivityStage5CanStartEnvironmentV1 {
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityStage5CanStartPredicateV1 evaluate = nullptr;
};

struct ActivityStage5CanStartResultV1 {
  ActivityStage5CanStartStatusV1 status =
      ActivityStage5CanStartStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  bool final_can_start = false;
};

ActivityStage5CanStartResultV1 ReadActivityStage5CanStartV1(
    const ActivityStage5CanStartEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

std::string_view ActivityStage5CanStartStatusKeyV1(
    ActivityStage5CanStartStatusV1 status) noexcept;

} // namespace xar::bridge
