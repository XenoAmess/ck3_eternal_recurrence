#pragma once

#include "xar_bridge/activity_stage2_gate_read_v1.hpp"

#include <array>
#include <cstdint>
#include <span>
#include <string_view>

namespace xar::bridge {

inline constexpr std::size_t kActivityStage2MaximumCandidatesV1 = 8;

enum class ActivityStage2LocationReadStatusV1 {
  observed,
  exact_build_rejected,
  callback_missing,
  gate_unavailable,
  planner_unavailable,
  row_unavailable,
  active_row_invalid,
  candidate_invalid,
  province_unavailable,
  native_evaluation_failed,
  frame_changed,
};

struct ActivityStage2LocationRowV1 {
  std::int32_t index = -1;
  std::int32_t phase_kind = -1;
  std::int32_t province_id = 0;
  bool is_active = false;
  bool phase_present = false;
  std::int32_t phase_active_raw = 0;
  friend bool operator==(const ActivityStage2LocationRowV1 &,
                         const ActivityStage2LocationRowV1 &) = default;
};

struct ActivityStage2LocationCandidateV1 {
  std::int32_t province_id = 0;
  bool can_select = false;
};

using ActivityStage2ResolveProvinceV1 = bool (*)(void *, std::int32_t,
                                                  std::uintptr_t &) noexcept;
using ActivityStage2CanSelectDestinationV1 = bool (*)(
    void *, std::uintptr_t, std::uintptr_t, bool &) noexcept;

struct ActivityStage2LocationEnvironmentV1 {
  ActivityStage1OptionEnvironmentV1 option{};
  ActivityStage2ResolveProvinceV1 resolve_province = nullptr;
  ActivityStage2CanSelectDestinationV1 can_select_destination = nullptr;
};

struct ActivityStage2LocationReadResultV1 {
  ActivityStage2LocationReadStatusV1 status =
      ActivityStage2LocationReadStatusV1::exact_build_rejected;
  ActivityStage2GateReadResultV1 gate{};
  std::array<ActivityStage2LocationRowV1, kActivityStage2MaximumRowsV1> rows{};
  std::uint16_t row_count = 0;
  std::int32_t active_row_index = -1;
  bool activity_single_location_flag = false;
  std::int32_t previous_planning_stage = -1;
  std::array<ActivityStage2LocationCandidateV1,
             kActivityStage2MaximumCandidatesV1> candidates{};
  std::uint16_t candidate_count = 0;
};

ActivityStage2LocationReadResultV1 ReadActivityStage2LocationV1(
    const ActivityStage2LocationEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::span<const std::int32_t> candidate_province_ids) noexcept;

std::string_view ActivityStage2LocationReadStatusKeyV1(
    ActivityStage2LocationReadStatusV1 status) noexcept;

} // namespace xar::bridge
