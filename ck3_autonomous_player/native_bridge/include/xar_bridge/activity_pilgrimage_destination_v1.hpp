#pragma once

#include "xar_bridge/activity_typed_planner_v1.hpp"

namespace xar::bridge {

// Ephemeral application-main objects, never serialized as addresses.
struct ActivityPilgrimageDestinationStateV1 {
  ActivityPlannerDiagFrameV1 frame{};
  std::uintptr_t planner = 0;
  std::uintptr_t activity_type = 0;
  std::int32_t stage = -1;
  std::int32_t previous_stage = -1;
  std::uint8_t single_location_flag = 0;
  std::uintptr_t configuration_rows = 0;
  std::int32_t configuration_row_count = 0;
  std::uintptr_t active_row = 0;
  std::uintptr_t phase = 0;
  std::int32_t phase_kind = -1;
  std::uint8_t phase_auto_raw = 0;
  std::uint32_t province_id = 0;
  ActivityTypedPlannerSelectionV1 selection{};
  std::int64_t gold_raw = 0;
  friend bool operator==(const ActivityPilgrimageDestinationStateV1 &,
                         const ActivityPilgrimageDestinationStateV1 &) = default;
};

using ActivityPilgrimageDestinationReadStateV1 =
    bool (*)(void *, ActivityPilgrimageDestinationStateV1 &) noexcept;
using ActivityPilgrimageDestinationResolveProvinceV1 =
    bool (*)(void *, std::uint32_t, std::uintptr_t &) noexcept;
using ActivityPilgrimageDestinationCanSelectV1 =
    bool (*)(void *, std::uintptr_t, std::uintptr_t, bool &) noexcept;
using ActivityPilgrimageDestinationSelectOnceV1 =
    bool (*)(void *, std::uintptr_t, std::uintptr_t) noexcept;

struct ActivityPilgrimageDestinationEnvironmentV1 {
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityPilgrimageDestinationReadStateV1 read_state = nullptr;
  ActivityPilgrimageDestinationResolveProvinceV1 resolve_province = nullptr;
  ActivityPilgrimageDestinationCanSelectV1 can_select = nullptr;
  ActivityPilgrimageDestinationSelectOnceV1 select_once = nullptr;
};

enum class ActivityPilgrimageDestinationStatusV1 {
  can_select_observed,
  selection_verified,
  exact_build_rejected,
  callback_missing,
  precondition_rejected,
  native_call_failed,
  postcondition_failed,
};

struct ActivityPilgrimageDestinationResultV1 {
  ActivityPilgrimageDestinationStatusV1 status =
      ActivityPilgrimageDestinationStatusV1::exact_build_rejected;
  bool can_select_observed = false;
  bool can_select = false;
  bool submitted = false;
  bool needs_recovery = false;
  bool row_filled = false;
  bool selected_option_retained = false;
  bool gold_unchanged = false;
  bool frame_unchanged = false;
  // This is the software call graph fact, not an independent hosted-world read.
  bool no_start_call_made = true;
  std::int32_t planning_stage_after = -1;
  ActivityPilgrimageDestinationStateV1 before{};
  ActivityPilgrimageDestinationStateV1 after{};
};

// Native CanSelect only, one candidate. No request-defined true/false values.
ActivityPilgrimageDestinationResultV1 ReadActivityPilgrimageDestinationCanSelectV1(
    const ActivityPilgrimageDestinationEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::uint32_t province_id) noexcept;

// Private default-OFF candidate. A single native Select call. A successful
// result reports the observed stage; it does not force/claim final stage five.
ActivityPilgrimageDestinationResultV1 SelectActivityPilgrimageDestinationV1(
    const ActivityPilgrimageDestinationEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::uint32_t province_id) noexcept;

} // namespace xar::bridge
