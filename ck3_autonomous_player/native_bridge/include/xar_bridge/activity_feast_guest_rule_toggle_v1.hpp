#pragma once

#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"
#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::bridge {

enum class ActivityFeastGuestRuleStatusV1 {
  observed_inactive,
  observed_active,
  activated,
  exact_build_rejected,
  frame_changed,
  planner_unavailable,
  window_unbound,
  rule_unavailable,
  ambiguous_rule,
  native_read_failed,
  native_action_failed,
  postcondition_failed,
};

struct ActivityFeastGuestRuleResultV1 {
  ActivityFeastGuestRuleStatusV1 status =
      ActivityFeastGuestRuleStatusV1::exact_build_rejected;
  ActivityPlannerDiagFrameV1 frame{};
  std::uint32_t native_key_hash = 0;
  std::int32_t ordered_rule_count = 0;
  std::int32_t active_rule_count = 0;
  std::int32_t filtered_group_count = 0;
  std::int32_t filtered_character_count = 0;
  bool active = false;
  bool invoked = false;
};

using ActivityFeastGuestRuleCaptureV1 = bool (*)(
    void *, const ActivityPlannerDiagFrameV1 &,
    ActivityCostSlot12CaptureV1 &) noexcept;
using ActivityFeastGuestRuleDiagV1 = ActivityPlannerDiagResultV1 (*)(
    void *, const ActivityPlannerDiagFrameV1 &) noexcept;
using ActivityFeastGuestRuleHashV1 = std::uint32_t (*)(
    void *, std::uintptr_t, std::string_view) noexcept;
using ActivityFeastGuestRuleLookupV1 = std::uintptr_t (*)(
    void *, std::uintptr_t, std::uint32_t) noexcept;
using ActivityFeastGuestRuleActiveV1 = bool (*)(
    void *, std::uintptr_t, std::uintptr_t, std::uintptr_t, bool &) noexcept;
using ActivityFeastGuestRuleToggleV1 = bool (*)(
    void *, std::uintptr_t, std::uintptr_t, std::uintptr_t) noexcept;

// Private and default OFF. Call only from the game application thread on a
// paused stage-5 feast frame. The native pointers never escape the call.
struct ActivityFeastGuestRuleEnvironmentV1 {
  bool enabled = false;
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  void *context = nullptr;
  ActivityFeastGuestRuleCaptureV1 capture = nullptr;
  ActivityFeastGuestRuleDiagV1 read_diagnostic = nullptr;
  ActivityFeastGuestRuleHashV1 hash_key = nullptr;
  ActivityFeastGuestRuleLookupV1 lookup_rule = nullptr;
  ActivityFeastGuestRuleActiveV1 read_active = nullptr;
  ActivityFeastGuestRuleToggleV1 toggle = nullptr;
};

ActivityFeastGuestRuleResultV1 ReadActivityFeastGuestRuleV1(
    const ActivityFeastGuestRuleEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::string_view authored_rule_key) noexcept;

// Policy approval must come from the caller. This is one typed category
// toggle, not a guest acceptance or activity Start action.
ActivityFeastGuestRuleResultV1 ActivateActivityFeastGuestRuleV1(
    const ActivityFeastGuestRuleEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::string_view authored_rule_key, bool policy_approved) noexcept;

std::string_view ActivityFeastGuestRuleStatusKeyV1(
    ActivityFeastGuestRuleStatusV1 status) noexcept;

} // namespace xar::bridge
