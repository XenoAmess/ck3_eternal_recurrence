#include "xar_bridge/activity_pilgrimage_cost_lifecycle_v1.hpp"

namespace xar::bridge {

ActivityPilgrimageCostLifecycleStatusV1 InstallActivityPilgrimageCostColdV1(
    ActivityPilgrimageCostLifecycleV1 &state,
    const ActivityCostSlot12EnvironmentV1 &source,
    bool enabled, bool legacy_enabled,
    ActivityPilgrimageCostInstallCallbackV1 fixture_installer) noexcept {
  using Status = ActivityPilgrimageCostLifecycleStatusV1;
  if (!enabled) return Status::disabled;
  bool expected = false;
  if (!state.attempted.compare_exchange_strong(expected, true,
          std::memory_order_acq_rel)) return Status::already_attempted;
  const auto reject = [&state](Status status) noexcept {
    state.queries_enabled.store(false, std::memory_order_release);
    auto expected_status = Status::untouched;
    (void)state.status.compare_exchange_strong(expected_status, status,
        std::memory_order_acq_rel);
    return status;
  };
  if (legacy_enabled) return reject(Status::conflicting_legacy_gate);
  if (state.observer.installed || !source.enabled ||
      !source.primary_thread_suspended || source.module_base == 0 ||
      !IsActivity12004BuildV1(source.executable_sha256) ||
      source.read_memory == nullptr || source.read_frame == nullptr ||
      source.typed_contract != nullptr)
    return reject(Status::invalid_cold_environment);
  auto environment = source;
  environment.typed_contract = &kOrdinaryPilgrimagePiousContractV1;
  const auto install = fixture_installer != nullptr ? fixture_installer
                                                   : &InstallActivityCostSlot12PassiveV1;
  if (!install(state.observer, environment) || !state.observer.installed ||
      state.observer.environment.typed_contract == nullptr ||
      !IsPilgrimageContractV1(
          *state.observer.environment.typed_contract))
    return reject(Status::install_failed);
  auto expected_status = Status::untouched;
  if (!state.status.compare_exchange_strong(expected_status, Status::installed,
          std::memory_order_acq_rel)) return Status::stopped;
  state.queries_enabled.store(true, std::memory_order_release);
  if (state.status.load(std::memory_order_acquire) != Status::installed) {
    state.queries_enabled.store(false, std::memory_order_release);
    return Status::stopped;
  }
  return Status::installed;
}

ActivityCostSlot12ObserverV1 *GetActivityPilgrimageCostObserverForQueriesV1(
    ActivityPilgrimageCostLifecycleV1 &state) noexcept {
  if (!state.queries_enabled.load(std::memory_order_acquire) ||
      state.status.load(std::memory_order_acquire) !=
          ActivityPilgrimageCostLifecycleStatusV1::installed)
    return nullptr;
  return &state.observer;
}

void StopActivityPilgrimageCostQueriesV1(
    ActivityPilgrimageCostLifecycleV1 &state) noexcept {
  state.queries_enabled.store(false, std::memory_order_release);
  // Prevent a hot restart even if Stop arrived before the cold entry.
  state.attempted.store(true, std::memory_order_release);
  state.status.store(ActivityPilgrimageCostLifecycleStatusV1::stopped,
                     std::memory_order_release);
  // The original fixed hook and callback backing stay alive for process life.
}

} // namespace xar::bridge
