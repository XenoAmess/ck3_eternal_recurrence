#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

// These pointers exist only during one paused native call. A transport must
// never serialize or reuse them after the frame or planner changes.
struct ActivityStage2DestinationStateV1 {
  ActivityPlannerDiagFrameV1 frame{};
  std::uintptr_t planner = 0;
  std::uintptr_t activity_type = 0;
  std::uintptr_t selected_option = 0;
  std::int32_t selected_option_id = -1;
  std::int32_t stage = -1;
  std::int32_t previous_stage = -1;
  std::uint8_t single_location_flag = 0;
  std::uintptr_t configuration_rows = 0;
  std::int32_t configuration_row_count = 0;
  std::array<std::uint32_t, 2> province_ids{};
  std::uintptr_t active_row = 0;
  bool activity_feast = false;
  bool generic_feast_option = false;
  bool activity_started = false;
  std::int64_t gold_raw = 0;

  friend bool operator==(const ActivityStage2DestinationStateV1 &,
                         const ActivityStage2DestinationStateV1 &) = default;
};

using ActivityStage2DestinationReadStateV1 =
    bool (*)(void *, ActivityStage2DestinationStateV1 &) noexcept;
using ActivityStage2DestinationResolveProvinceV1 =
    bool (*)(void *, std::uint32_t, std::uintptr_t &) noexcept;
using ActivityStage2DestinationCanSelectV1 =
    bool (*)(void *, std::uintptr_t, std::uintptr_t, bool &) noexcept;
using ActivityStage2DestinationSelectOnceV1 =
    bool (*)(void *, std::uintptr_t, std::uintptr_t) noexcept;

struct ActivityStage2DestinationEnvironmentV1 {
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityStage2DestinationReadStateV1 read_state = nullptr;
  ActivityStage2DestinationResolveProvinceV1 resolve_province = nullptr;
  ActivityStage2DestinationCanSelectV1 can_select = nullptr;
  ActivityStage2DestinationSelectOnceV1 select_once = nullptr;
};

enum class ActivityStage2DestinationStatusV1 {
  verified_stage_five,
  exact_build_rejected,
  callback_missing,
  precondition_rejected,
  native_call_failed,
  postcondition_failed,
};

struct ActivityStage2DestinationResultV1 {
  ActivityStage2DestinationStatusV1 status =
      ActivityStage2DestinationStatusV1::exact_build_rejected;
  bool submitted = false;
  // A submitted call remains pending/RED until independent recovery proves
  // the game's actual state. Never repeat it because a callback returned false.
  bool needs_recovery = false;
  bool stage_five_visible = false;
  bool rows_filled = false;
  bool selected_option_retained = false;
  bool gold_unchanged = false;
  bool frame_unchanged = false;
  bool no_activity_started = false;
};

// Private, default-OFF exact-build core. One typed ProvinceID, one original
// 0x10AF3D0 call, and an independent same-frame postcondition. The caller
// supplies native read/call wrappers and must keep the submitted result in its
// pending record until verification or cold recovery.
ActivityStage2DestinationResultV1 SelectActivityStage2DestinationV1(
    const ActivityStage2DestinationEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::uint32_t province_id) noexcept;

std::string_view ActivityStage2DestinationStatusKeyV1(
    ActivityStage2DestinationStatusV1 status) noexcept;

} // namespace xar::bridge
