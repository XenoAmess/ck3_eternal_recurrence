#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"

#include "xar_bridge/activity_typed_planner_v1.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kActivityPilgrimageStage1OptionKeyV1 =
    kOrdinaryPilgrimagePiousContractV1.special_option_key;

enum class ActivityPilgrimageStage1OptionReadStatusV1 {
  observed,
  exact_build_rejected,
  callback_missing,
  planner_unavailable,
  not_pilgrimage_stage1,
  option_unavailable,
  option_identity_mismatch,
  option_key_unavailable,
  native_evaluation_failed,
  frame_changed,
};

using ActivityPilgrimageStage1ResolveKeyV1 = bool (*)(void *, std::int32_t,
                                              std::array<char, 96> &,
                                              std::uint16_t &) noexcept;
using ActivityPilgrimageStage1SelectedOptionV1 = bool (*)(void *, std::uintptr_t,
                                                  std::uintptr_t &) noexcept;
using ActivityPilgrimageStage1PredicateV1 = bool (*)(void *, std::uintptr_t,
                                            std::uintptr_t, std::uintptr_t,
                                            std::uintptr_t, bool &) noexcept;
using ActivityPilgrimageStage1CanProgressV1 = bool (*)(void *, std::uintptr_t,
                                              bool &) noexcept;
using ActivityPilgrimageStage1SetStageTwoV1 = bool (*)(void *, std::uintptr_t) noexcept;
using ActivityPilgrimageStage1FindAutoRowV1 = bool (*)(void *, std::uintptr_t,
                                            std::uintptr_t &) noexcept;
using ActivityPilgrimageStage1ProgressNonzeroV1 = bool (*)(void *,
                                                 std::uintptr_t) noexcept;

struct ActivityPilgrimageStage1OptionEnvironmentV1 {
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityPilgrimageStage1ResolveKeyV1 resolve_key = nullptr;
  ActivityPilgrimageStage1SelectedOptionV1 selected_option = nullptr;
  ActivityPilgrimageStage1PredicateV1 option_predicate = nullptr;
  ActivityPilgrimageStage1CanProgressV1 can_progress = nullptr;
  ActivityPilgrimageStage1SetStageTwoV1 set_stage_two = nullptr;
  ActivityPilgrimageStage1FindAutoRowV1 find_auto_row = nullptr;
  ActivityPilgrimageStage1ProgressNonzeroV1 progress_nonzero = nullptr;
};

struct ActivityPilgrimageStage1OptionReadResultV1 {
  ActivityPilgrimageStage1OptionReadStatusV1 status =
      ActivityPilgrimageStage1OptionReadStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::array<char, 96> option_key{};
  std::uint16_t option_key_size = 0;
  bool shown = false;
  bool valid = false;
  bool can_progress = false;
  bool pious_pilgrimage_confirm_ready = false;
};

ActivityPilgrimageStage1OptionReadResultV1 ReadActivityPilgrimageStage1OptionV1(
    const ActivityPilgrimageStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

enum class ActivityPilgrimageStage2OptionReadStatusV1 {
  observed,
  exact_build_rejected,
  callback_missing,
  planner_unavailable,
  not_pilgrimage_stage_two,
  option_identity_mismatch,
  option_key_unavailable,
  frame_changed,
};

struct ActivityPilgrimageStage2OptionReadResultV1 {
  ActivityPilgrimageStage2OptionReadStatusV1 status =
      ActivityPilgrimageStage2OptionReadStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::array<char, 96> option_key{};
  std::uint16_t option_key_size = 0;
  bool pious_pilgrimage_selected = false;
};

ActivityPilgrimageStage2OptionReadResultV1 ReadActivityPilgrimageStage2OptionV1(
    const ActivityPilgrimageStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;
std::string_view ActivityPilgrimageStage2OptionReadStatusKeyV1(
    ActivityPilgrimageStage2OptionReadStatusV1 status) noexcept;

enum class ActivityPilgrimageStage1ConfirmStatusV1 {
  stage_two_verified,
  precondition_rejected,
  native_transition_failed,
  postcondition_failed,
};

enum class ActivityPilgrimageStage1ConfirmRejectReasonV1 {
  none,
  option_not_ready,
  stage_setter_callback_missing,
  stage_setter_abi_mismatch,
  stage_notification_slot_mismatch,
  planner_identity_changed,
  stage_auto_read_failed,
  stage_auto_nonzero,
  stage_auto_row_unverified,
  stage_auto_row_absent,
  stage_progress_abi_mismatch,
  frame_changed,
};

struct ActivityPilgrimageStage1ConfirmResultV1 {
  ActivityPilgrimageStage1ConfirmStatusV1 status =
      ActivityPilgrimageStage1ConfirmStatusV1::precondition_rejected;
  ActivityPilgrimageStage1OptionReadResultV1 precondition{};
  ActivityPilgrimageStage1ConfirmRejectReasonV1 reject_reason =
      ActivityPilgrimageStage1ConfirmRejectReasonV1::none;
  bool planner_stage_auto_observed = false;
  std::uint8_t planner_stage_auto_raw = 0;
  bool submitted = false;
  bool needs_recovery = false;
  bool stage_two_visible = false;
  bool selected_option_retained = false;
};

// On stage-auto byte 0, calls only the original stage setter at 0x10B1BD0.
// On byte 1 with a verified original auto row, calls 0x10B1330 once: that
// exact-build branch performs row bookkeeping and reaches stage 2 without the
// auto-advance tail. Never call 0x10B1330 on byte 0: it can reach Start.
ActivityPilgrimageStage1ConfirmResultV1 ConfirmActivityPilgrimageStage1V1(
    const ActivityPilgrimageStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

std::string_view ActivityPilgrimageStage1ConfirmStatusKeyV1(
    ActivityPilgrimageStage1ConfirmStatusV1 status) noexcept;
std::string_view ActivityPilgrimageStage1ConfirmRejectReasonKeyV1(
    ActivityPilgrimageStage1ConfirmRejectReasonV1 reason) noexcept;

std::string_view ActivityPilgrimageStage1OptionReadStatusKeyV1(
    ActivityPilgrimageStage1OptionReadStatusV1 status) noexcept;

// Actual selected option producer for the fixed pious contract. Read-only.
// required_stage is observed, not advanced; cost/Start request stage 5.
bool ReadActivityPilgrimageSelectedOptionV1(
    const ActivityPilgrimageStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected, std::int32_t required_stage,
    ActivityTypedPlannerSelectionV1 &output) noexcept;

} // namespace xar::bridge
