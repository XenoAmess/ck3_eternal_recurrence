#pragma once

#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"
#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::uintptr_t kActivityGetCostByNameRvaV1 = 0x2CD96C0;
inline constexpr std::int64_t kActivityGoldCostScaleV1 = 100000;

using ActivityStage5InvokeGoldCostV1 = bool (*)(
    void *, std::uintptr_t module_base, std::uintptr_t cost_breakdown,
    std::int64_t &gold_raw) noexcept;

struct ActivityStage5GoldCostEnvironmentV1 {
  // This is a private, default-off query. The caller must run it on the
  // paused application-main thread after a normal slot-12 refresh.
  bool enabled = false;
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  // For focused fixture tests; nullptr invokes the exact native getter.
  ActivityStage5InvokeGoldCostV1 invoke_gold_cost = nullptr;
};

enum class ActivityStage5GoldCostStatusV1 {
  observed,
  exact_build_rejected,
  no_normal_refresh,
  frame_changed,
  planner_unavailable,
  not_feast_stage_five,
  configuration_changed,
  actor_unavailable,
  native_query_failed,
};

struct ActivityStage5GoldCostResultV1 {
  ActivityStage5GoldCostStatusV1 status =
      ActivityStage5GoldCostStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::uint64_t normal_refresh_sequence = 0;
  std::int64_t gold_cost_raw = 0;
  std::int64_t actor_gold_raw = 0;
  std::int64_t scale = kActivityGoldCostScaleV1;
};

ActivityStage5GoldCostResultV1 ReadActivityStage5GoldCostV1(
    const ActivityStage5GoldCostEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

// Direct 1.19.0.6 implementation of the original GUI GetCost('gold') chain.
// The caller must have verified the executable and the function bytes.
bool InvokeActivityStage5NativeGoldCostV1(
    void *context, std::uintptr_t module_base,
    std::uintptr_t cost_breakdown, std::int64_t &gold_raw) noexcept;

std::string_view ActivityStage5GoldCostStatusKeyV1(
    ActivityStage5GoldCostStatusV1 status) noexcept;

} // namespace xar::bridge
