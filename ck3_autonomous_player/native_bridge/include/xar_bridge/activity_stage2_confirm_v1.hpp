#pragma once

#include "xar_bridge/activity_stage1_option_read_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

using ActivityStage2SetStageFiveV1 = bool (*)(void *, std::uintptr_t) noexcept;
using ActivityStage2ReadGoldRawV1 = bool (*)(void *, std::int64_t &) noexcept;

struct ActivityStage2ConfirmEnvironmentV1 {
  ActivityStage1OptionEnvironmentV1 option{};
  ActivityStage2SetStageFiveV1 set_stage_five = nullptr;
  ActivityStage2ReadGoldRawV1 read_gold_raw = nullptr;
};

enum class ActivityStage2ConfirmStatusV1 {
  stage_five_verified,
  precondition_rejected,
  native_transition_failed,
  postcondition_failed,
};

struct ActivityStage2ConfirmResultV1 {
  ActivityStage2ConfirmStatusV1 status =
      ActivityStage2ConfirmStatusV1::precondition_rejected;
  ActivityStage2OptionReadResultV1 precondition{};
  bool can_progress_stage_two = false;
  bool submitted = false;
  bool stage_five_visible = false;
  bool selected_option_retained = false;
  bool gold_unchanged = false;
  bool frame_unchanged = false;
};

// A single original stage-setter call with argument 5. This does not invoke
// ProgressPlanningStage, whose recursive GUI path can reach activity Start.
ActivityStage2ConfirmResultV1 ConfirmActivityStage2V1(
    const ActivityStage2ConfirmEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

std::string_view ActivityStage2ConfirmStatusKeyV1(
    ActivityStage2ConfirmStatusV1 status) noexcept;

} // namespace xar::bridge
