#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityStage1OptionKeyV1 =
    "feast_type_generic";

enum class ActivityStage1OptionReadStatusV1 {
  observed,
  exact_build_rejected,
  callback_missing,
  planner_unavailable,
  not_feast_stage1,
  option_unavailable,
  option_identity_mismatch,
  option_key_unavailable,
  native_evaluation_failed,
  frame_changed,
};

using ActivityStage1ResolveKeyV1 = bool (*)(void *, std::int32_t,
                                              std::array<char, 96> &,
                                              std::uint16_t &) noexcept;
using ActivityStage1SelectedOptionV1 = bool (*)(void *, std::uintptr_t,
                                                  std::uintptr_t &) noexcept;
using ActivityStage1PredicateV1 = bool (*)(void *, std::uintptr_t,
                                            std::uintptr_t, std::uintptr_t,
                                            std::uintptr_t, bool &) noexcept;
using ActivityStage1CanProgressV1 = bool (*)(void *, std::uintptr_t,
                                              bool &) noexcept;
using ActivityStage1SetStageTwoV1 = bool (*)(void *, std::uintptr_t) noexcept;

struct ActivityStage1OptionEnvironmentV1 {
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityStage1ResolveKeyV1 resolve_key = nullptr;
  ActivityStage1SelectedOptionV1 selected_option = nullptr;
  ActivityStage1PredicateV1 option_predicate = nullptr;
  ActivityStage1CanProgressV1 can_progress = nullptr;
  ActivityStage1SetStageTwoV1 set_stage_two = nullptr;
};

struct ActivityStage1OptionReadResultV1 {
  ActivityStage1OptionReadStatusV1 status =
      ActivityStage1OptionReadStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::array<char, 96> option_key{};
  std::uint16_t option_key_size = 0;
  bool shown = false;
  bool valid = false;
  bool can_progress = false;
  bool generic_feast_confirm_ready = false;
};

ActivityStage1OptionReadResultV1 ReadActivityStage1OptionV1(
    const ActivityStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

enum class ActivityStage2OptionReadStatusV1 {
  observed,
  exact_build_rejected,
  callback_missing,
  planner_unavailable,
  not_feast_stage_two,
  option_identity_mismatch,
  option_key_unavailable,
  frame_changed,
};

struct ActivityStage2OptionReadResultV1 {
  ActivityStage2OptionReadStatusV1 status =
      ActivityStage2OptionReadStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::array<char, 96> option_key{};
  std::uint16_t option_key_size = 0;
  bool generic_feast_selected = false;
};

ActivityStage2OptionReadResultV1 ReadActivityStage2OptionV1(
    const ActivityStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;
std::string_view ActivityStage2OptionReadStatusKeyV1(
    ActivityStage2OptionReadStatusV1 status) noexcept;

enum class ActivityStage1ConfirmStatusV1 {
  stage_two_verified,
  precondition_rejected,
  native_transition_failed,
  postcondition_failed,
};

struct ActivityStage1ConfirmResultV1 {
  ActivityStage1ConfirmStatusV1 status =
      ActivityStage1ConfirmStatusV1::precondition_rejected;
  ActivityStage1OptionReadResultV1 precondition{};
  bool submitted = false;
  bool stage_two_visible = false;
  bool selected_option_retained = false;
};

// Calls only the original stage setter at 0x10B1BD0 with argument 2. The
// public ProgressPlanningStage routine auto-advances later stages, including
// the activity-start branch, and must not be used for this bounded action.
ActivityStage1ConfirmResultV1 ConfirmActivityStage1V1(
    const ActivityStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

std::string_view ActivityStage1ConfirmStatusKeyV1(
    ActivityStage1ConfirmStatusV1 status) noexcept;

std::string_view ActivityStage1OptionReadStatusKeyV1(
    ActivityStage1OptionReadStatusV1 status) noexcept;

} // namespace xar::bridge
