#pragma once

#include "xar_bridge/activity_stage5_gold_cost_v1.hpp"

#include <array>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::array<std::string_view, 4>
    kActivityFeastCostKeysV1{"gold", "treasury", "piety", "barter_goods"};

// The callback resolves the original GetCost(name) resource index and returns
// its configured signed Q100000 value. Index 10 is the original unknown-name
// fallback, not a valid resource. The default calls the exact native getter.
using ActivityStage5InvokeNamedFeastCostV1 = bool (*)(
    void *, std::uintptr_t module_base, std::uintptr_t cost_breakdown,
    std::string_view resource_key, std::uint32_t &resource_index,
    std::int64_t &cost_raw) noexcept;

struct ActivityStage5FeastFullCostEnvironmentV1 {
  bool enabled = false;
  // Reuses the Gold reader's normal slot-12 and same-frame checks. Its single
  // Gold invocation is replaced by one bounded four-name invocation here.
  ActivityStage5GoldCostEnvironmentV1 gold{};
  // Fixture override, or a transport-owned SEH wrapper around the native
  // getter. nullptr invokes the exact native getter directly.
  ActivityStage5InvokeNamedFeastCostV1 invoke_named_cost = nullptr;
  void *named_context = nullptr;
};

enum class ActivityStage5FeastFullCostStatusV1 {
  observed,
  gold_gate_red,
  named_query_failed,
  resource_unmapped,
};

struct ActivityStage5FeastFullCostResultV1 {
  ActivityStage5FeastFullCostStatusV1 status =
      ActivityStage5FeastFullCostStatusV1::gold_gate_red;
  ActivityStage5GoldCostStatusV1 gold_gate_status =
      ActivityStage5GoldCostStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::uint64_t normal_refresh_sequence = 0;
  std::array<std::uint32_t, 4> resource_indices{};
  std::array<std::int64_t, 4> configured_cost_raw{};
  std::int64_t actor_gold_raw = 0;
  std::int64_t scale = kActivityGoldCostScaleV1;
};

ActivityStage5FeastFullCostResultV1 ReadActivityStage5FeastFullCostV1(
    const ActivityStage5FeastFullCostEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept;

// Exact CK3 1.19.0.6 GetCost(name) implementation. It first invokes the
// original getter against 11 unique stack sentinels to obtain the native
// resource index, rejects index 10, then invokes it on the real breakdown.
// It never refreshes the planner, advances a stage, or submits Start.
bool InvokeActivityStage5NativeNamedFeastCostV1(
    void *context, std::uintptr_t module_base, std::uintptr_t cost_breakdown,
    std::string_view resource_key, std::uint32_t &resource_index,
    std::int64_t &cost_raw) noexcept;

std::string_view ActivityStage5FeastFullCostStatusKeyV1(
    ActivityStage5FeastFullCostStatusV1 status) noexcept;

} // namespace xar::bridge
