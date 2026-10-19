#pragma once

#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"
#include "xar_bridge/activity_typed_planner_v1.hpp"

namespace xar::bridge {

// Same callback shapes as the proven existing getters, independently named
// so this new consumer has no production dependency on old Feast/Gold TUs.
using ActivityTypedInvokeNamedCostV1 = bool (*)(
    void *, std::uintptr_t, std::uintptr_t, std::string_view,
    std::uint32_t &, std::int64_t &) noexcept;
using ActivityTypedFinalCanStartCallbackV1 = bool (*)(
    void *, std::uintptr_t, bool &) noexcept;

enum class ActivityTypedFullCostStatusV1 {
  observed,
  disabled_or_exact_build_rejected,
  frame_unavailable,
  planner_or_type_mismatch,
  selection_unavailable,
  passive_observer_contract_mismatch,
  no_normal_refresh,
  configuration_changed,
  configured_cost_unreadable,
  named_cost_failed,
  named_cost_unmapped,
  named_cost_duplicate_index,
  named_cost_indexed_disagreement,
  final_can_start_failed,
};

struct ActivityTypedFullCostEnvironmentV1 {
  bool enabled = false;
  ActivityPlannerDiagEnvironmentV1 diagnostic{};
  ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  ActivityTypedPlannerReadSelectionV1 read_selection = nullptr;
  void *selection_context = nullptr;
  // Null uses the already bound native named getter; tests provide callbacks.
  ActivityTypedInvokeNamedCostV1 invoke_named_cost = nullptr;
  void *named_context = nullptr;
  // Null uses the already bound final evaluator, not a script approximation.
  ActivityTypedFinalCanStartCallbackV1 evaluate_final_can_start = nullptr;
  void *can_start_context = nullptr;
};

struct ActivityTypedFullCostResultV1 {
  ActivityTypedFullCostStatusV1 status =
      ActivityTypedFullCostStatusV1::disabled_or_exact_build_rejected;
  ActivityTypedPlannerCostQuoteV1 quote{};
  // Observing a price does not authorize paying an unnamed positive slot.
  bool unknown_positive_configured_cost = false;
  std::string_view final_failure_display_unknown_reason =
      "final_canstart_tooltip_getter_unbound";
};

using ActivityTypedCanStartNativePredicateV1 = bool (*)(void *, void *);
using ActivityTypedCanStartNativeDestroyV1 = void (*)(void *);

// Reuses only the proven owned native string ABI. This bool reader neither
// copies the display string nor depends on an arbitrary text-size ceiling.
bool InvokeActivityTypedPlannerCanStartBoolOwnedV1(
    void *planner, ActivityTypedCanStartNativePredicateV1 predicate,
    ActivityTypedCanStartNativeDestroyV1 destroy, bool &allowed) noexcept;

// New opt-in software consumer. The historical Feast reader is unchanged.
// Reads the ten GetCost indexed totals after a normal refresh, independently
// verifies four native names, and observes final CanStart exactly once.
ActivityTypedFullCostResultV1 ReadActivityTypedPlannerFullCostV1(
    const ActivityTypedFullCostEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    const ActivityTypedPlannerContractV1 &contract) noexcept;

std::string_view ActivityTypedFullCostStatusKeyV1(
    ActivityTypedFullCostStatusV1 status) noexcept;

} // namespace xar::bridge
