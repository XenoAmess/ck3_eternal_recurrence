#pragma once

#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"
#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::uintptr_t kActivityFeastPlannerGuestJoinRvaV1 =
    0x10B0A80;
inline constexpr std::size_t kActivityFeastPlannerGuestLimitV1 = 128;

using ActivityFeastInvokePlannerGuestJoinV1 = bool (*)(
    void *, std::uintptr_t module_base, std::uintptr_t planner,
    std::uintptr_t character, std::int64_t &join_raw) noexcept;
using ActivityFeastInvokePlannerActivityV1 = std::uintptr_t (*)(
    void *, std::uintptr_t module_base, std::uintptr_t planner) noexcept;
using ActivityFeastInvokeTravelDaysV1 = bool (*)(
    void *, std::uintptr_t module_base, std::uintptr_t character,
    std::uintptr_t destination, std::int32_t &days) noexcept;

struct ActivityFeastGuestJoinEnvironmentV1 {
  bool enabled = false;
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  ActivityFeastInvokePlannerGuestJoinV1 invoke_join = nullptr;
  void *join_context = nullptr;
  ActivityFeastInvokePlannerActivityV1 invoke_activity = nullptr;
  ActivityFeastInvokeTravelDaysV1 invoke_travel_days = nullptr;
  void *arrival_context = nullptr;
};

enum class ActivityFeastGuestJoinStatusV1 {
  observed,
  exact_build_rejected,
  frame_changed,
  planner_unavailable,
  no_normal_refresh,
  configuration_changed,
  guest_source_unavailable,
  native_evaluation_failed,
  cache_disagreed,
  arrival_source_unavailable,
  arrival_evaluation_failed,
};

struct ActivityFeastGuestJoinRowV1 {
  std::int32_t character_id = -1;
  std::int64_t planner_join_raw = 0;
  bool positive_join = false;
  std::int32_t predicted_arrival_raw = 0;
  std::int32_t predicted_travel_days = 0;
  bool may_not_arrive_in_time = false;

  friend bool operator==(const ActivityFeastGuestJoinRowV1 &,
                         const ActivityFeastGuestJoinRowV1 &) = default;
};

struct ActivityFeastGuestJoinResultV1 {
  ActivityFeastGuestJoinStatusV1 status =
      ActivityFeastGuestJoinStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::uint64_t normal_refresh_sequence = 0;
  std::uint32_t selected_nonhost_count = 0;
  std::uint32_t positive_join_count = 0;
  std::uint32_t timely_positive_join_count = 0;
  // These are pre-Start predictions, not an accepted invitation or attendance.
  bool arrival_time_observed = false;
  std::array<ActivityFeastGuestJoinRowV1,
             kActivityFeastPlannerGuestLimitV1> rows{};
};

ActivityFeastGuestJoinResultV1 ReadActivityFeastGuestJoinV1(
    const ActivityFeastGuestJoinEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

bool InvokeActivityFeastNativePlannerGuestJoinV1(
    void *context, std::uintptr_t module_base, std::uintptr_t planner,
    std::uintptr_t character, std::int64_t &join_raw) noexcept;
std::uintptr_t InvokeActivityFeastNativePlannerActivityV1(
    void *context, std::uintptr_t module_base,
    std::uintptr_t planner) noexcept;
bool InvokeActivityFeastNativeTravelDaysV1(
    void *context, std::uintptr_t module_base, std::uintptr_t character,
    std::uintptr_t destination, std::int32_t &days) noexcept;

std::string_view ActivityFeastGuestJoinStatusKeyV1(
    ActivityFeastGuestJoinStatusV1 status) noexcept;

} // namespace xar::bridge
