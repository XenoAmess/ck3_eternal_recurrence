#include "xar_bridge/ck3_12004.hpp"
#include "xar_bridge/actual_army_pre_date_prefix_observer_12004.hpp"
#include "xar_bridge/actual_army_daily_assault_preparation_observer_12004.hpp"
#include "xar_bridge/actual_army_assault_placement_observer_12004.hpp"
#include <cstdio>
#include <string>

namespace {
unsigned checks = 0;
unsigned failures = 0;
unsigned target_callbacks = 0;
void Check(bool condition) noexcept {
  ++checks;
  if (!condition) ++failures;
}
bool Read(void *, const void *, void *, std::size_t) noexcept {
  ++target_callbacks;
  return false;
}
void *Allocate(void *, std::size_t, DWORD, DWORD) noexcept {
  ++target_callbacks;
  return nullptr;
}
bool Free(void *, void *, std::size_t, DWORD) noexcept {
  ++target_callbacks;
  return false;
}
bool Protect(void *, void *, std::size_t, DWORD, DWORD &) noexcept {
  ++target_callbacks;
  return false;
}
bool Flush(void *, const void *, std::size_t) noexcept {
  ++target_callbacks;
  return false;
}
template<class Environment>
void SetCallbacks(Environment &environment) noexcept {
  environment.bindings.read_memory = &Read;
  environment.virtual_alloc_override = &Allocate;
  environment.virtual_free_override = &Free;
  environment.virtual_protect_override = &Protect;
  environment.flush_instruction_cache_override = &Flush;
}
}

int main() {
  using namespace xar::ck3_12004;
  constexpr std::uintptr_t image = 0x10000000;
  const std::string_view canonical = xar::ck3_12004::kExecutableSha256;
  std::string wrong(canonical);
  wrong[0] = '0';

  ActualArmyPreDatePrefixInstallEnvironment12004 prefix{};
  prefix.bindings = BindActualArmyPreDatePrefixImage12004(image, canonical);
  SetCallbacks(prefix);
  Check(prefix.bindings.enabled && prefix.bindings.image_base == image);
  ActualArmyPreDatePrefixDetourState12004 prefix_state{};
  Check(!InstallActualArmyPreDatePrefixObserver12004(prefix_state, prefix, canonical));
  Check(prefix_state.failure_flags.load() == actual_army_prefix_install_quiescence);
  Check(prefix_state.callback_target == 0 && prefix_state.trampoline == nullptr && prefix_state.installed.load() == 0);
  Check(!BindActualArmyPreDatePrefixImage12004(image, wrong).enabled);
  ActualArmyPreDatePrefixDetourState12004 wrong_prefix{};
  Check(!InstallActualArmyPreDatePrefixObserver12004(wrong_prefix, prefix, wrong));
  Check(wrong_prefix.failure_flags.load() == actual_army_prefix_install_exact_build);

  ActualArmyDailyAssaultPreparationInstallEnvironment12004 preparation{};
  preparation.bindings = BindActualArmyDailyAssaultPreparationImage12004(image, canonical);
  SetCallbacks(preparation);
  Check(preparation.bindings.enabled && preparation.bindings.image_base == image);
  ActualArmyDailyAssaultPreparationDetourState12004 preparation_state{};
  Check(!InstallActualArmyDailyAssaultPreparationObserver12004(preparation_state, preparation, canonical));
  Check(preparation_state.failure_flags.load() == actual_army_preparation_install_quiescence);
  Check(preparation_state.callback_target == 0 && preparation_state.trampoline == nullptr && preparation_state.installed.load() == 0);
  Check(!BindActualArmyDailyAssaultPreparationImage12004(image, wrong).enabled);
  ActualArmyDailyAssaultPreparationDetourState12004 wrong_preparation{};
  Check(!InstallActualArmyDailyAssaultPreparationObserver12004(wrong_preparation, preparation, wrong));
  Check(wrong_preparation.failure_flags.load() == actual_army_preparation_install_exact_build);

  ActualArmyAssaultPlacementInstallEnvironment12004 placement{};
  placement.bindings = BindActualArmyAssaultPlacementImage12004(image, canonical);
  SetCallbacks(placement);
  Check(placement.bindings.enabled && placement.bindings.image_base == image);
  ActualArmyAssaultPlacementDetourState12004 placement_state{};
  Check(!InstallActualArmyAssaultPlacementObserver12004(placement_state, placement, canonical));
  Check(placement_state.failure_flags.load() == actual_army_placement_install_quiescence);
  Check(placement_state.callback_target == 0 && placement_state.trampoline == nullptr && placement_state.installed.load() == 0);
  Check(!BindActualArmyAssaultPlacementImage12004(image, wrong).enabled);
  ActualArmyAssaultPlacementDetourState12004 wrong_placement{};
  Check(!InstallActualArmyAssaultPlacementObserver12004(wrong_placement, placement, wrong));
  Check(wrong_placement.failure_flags.load() == actual_army_placement_install_exact_build);

  Check(target_callbacks == 0);
  std::printf("canonical_descriptor_bind_enabled=3 install_phase_quiescence=3 wrong_digest_rejected=3 target_callbacks=%u checks=%u failures=%u\n", target_callbacks, checks, failures);
  return failures == 0 ? 0 : 1;
}
