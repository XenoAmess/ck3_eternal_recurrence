#pragma once

#include "xar_bridge/activity_stage1_option_read_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::size_t kActivityStage2MaximumRowsV1 = 128;

enum class ActivityStage2GateReadStatusV1 {
  observed,
  exact_build_rejected,
  callback_missing,
  option_unavailable,
  not_feast_stage_two,
  selected_option_not_generic,
  planner_identity_mismatch,
  row_vector_unavailable,
  native_evaluation_failed,
  native_gate_mismatch,
  frame_changed,
};

struct ActivityStage2FailedRowV1 {
  std::int32_t index = -1;
  std::uint32_t raw_dword = 0;
};

struct ActivityStage2GateReadResultV1 {
  ActivityStage2GateReadStatusV1 status =
      ActivityStage2GateReadStatusV1::exact_build_rejected;
  ActivityStage2OptionReadResultV1 selected_option{};
  std::int32_t configuration_row_count = 0;
  std::array<ActivityStage2FailedRowV1, kActivityStage2MaximumRowsV1>
      failed_rows{};
  std::uint16_t failed_row_count = 0;
  bool can_progress_stage2 = false;
  bool generic_feast_stage2_advance_ready = false;
};

// Read-only exact-build paused query. The original stage-2 branch of
// CanProgressPlanningStage is evaluated; this never calls a setter or Start.
ActivityStage2GateReadResultV1 ReadActivityStage2GateV1(
    const ActivityStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

std::string_view ActivityStage2GateReadStatusKeyV1(
    ActivityStage2GateReadStatusV1 status) noexcept;

} // namespace xar::bridge
