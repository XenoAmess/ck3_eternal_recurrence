#pragma once

#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"
#include <atomic>

namespace xar::bridge {

enum class ActivityPilgrimageCostLifecycleStatusV1 {
  untouched, disabled, installed, conflicting_legacy_gate,
  invalid_cold_environment, install_failed, already_attempted, stopped,
};

struct ActivityPilgrimageCostLifecycleV1 {
  // Process-life static owner. Neither Stop nor an ordinary bridge restart
  // may destroy or repurpose the installed hook, observer or callbacks.
  ActivityCostSlot12ObserverV1 observer{};
  std::atomic<bool> attempted{false};
  std::atomic<bool> queries_enabled{false};
  std::atomic<ActivityPilgrimageCostLifecycleStatusV1> status{
      ActivityPilgrimageCostLifecycleStatusV1::untouched};
};

using ActivityPilgrimageCostInstallCallbackV1 = bool (*)(
    ActivityCostSlot12ObserverV1 &, const ActivityCostSlot12EnvironmentV1 &) noexcept;

ActivityPilgrimageCostLifecycleStatusV1 InstallActivityPilgrimageCostColdV1(
    ActivityPilgrimageCostLifecycleV1 &state,
    const ActivityCostSlot12EnvironmentV1 &cold_environment,
    bool execution_gate_enabled = false,
    bool legacy_feast_gate_enabled = false,
    ActivityPilgrimageCostInstallCallbackV1 fixture_installer = nullptr) noexcept;

ActivityCostSlot12ObserverV1 *GetActivityPilgrimageCostObserverForQueriesV1(
    ActivityPilgrimageCostLifecycleV1 &state) noexcept;

// Revokes future query permission only. No code restoration or backing free
// is attempted without a new suspended-primary native uninstall contract.
void StopActivityPilgrimageCostQueriesV1(
    ActivityPilgrimageCostLifecycleV1 &state) noexcept;

} // namespace xar::bridge
