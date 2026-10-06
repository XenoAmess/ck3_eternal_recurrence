#include "xar_bridge/ck3_12004_tactical_daily_sentinel.hpp"

namespace xar::ck3_12004 {

ck3_11906::Bindings BindTacticalDailySentinelImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept {
  ck3_11906::Bindings result{};
  const auto core = BindCoreImage(image_base, executable_sha256);
  if (!core.enabled) return result;
  result.game_state_slot = core.game_state_slot;
  result.jomini_state_slot = core.jomini_state_slot;
  result.get_local_player = core.get_local_player;
  result.army_storage_slot = reinterpret_cast<void **>(
      image_base + kTacticalSentinelUnitStorageSlotRva12004);
  result.army_internal_storage_slot = reinterpret_cast<void **>(
      image_base + kTacticalSentinelArmyStorageSlotRva12004);
  result.combat_storage_slot = reinterpret_cast<void **>(
      image_base + kTacticalSentinelCombatStorageSlotRva12004);
  result.enabled = true;
  return result;
}

bool InitializeTacticalDailySentinelFixture12004(
    const ck3_11906::Bindings &bindings, std::string_view executable_sha256,
    ck3_11906::TacticalSetPausedV1 set_paused,
    ck3_11906::TacticalDailyOriginalV1 original) noexcept {
  if (executable_sha256 != kExecutableSha256 || !bindings.enabled) return false;
  return ck3_11906::InitializeTacticalDailySentinelFixtureV1(
      bindings, set_paused, original);
}

bool InstallTacticalDailySentinel12004(
    ck3_11906::TacticalDailySentinelDetourStateV1 &state,
    const ck3_11906::TacticalDailySentinelInstallEnvironmentV1 &environment,
    std::string_view executable_sha256) noexcept {
  if (executable_sha256 != kExecutableSha256) {
    state.failure_flags.store(
        ck3_11906::tactical_daily_install_failure_exact_build,
        std::memory_order_relaxed);
    return false;
  }
  auto actual = environment;
  if (actual.final_stage_target_override == 0) {
    actual.final_stage_target_override =
        actual.module_base + kTacticalSentinelFinalStageRva12004;
  }
  if (actual.set_paused_override == nullptr) {
    // The native third argument is the full uint32 PlayerID. The existing
    // signed software callback passes those same 32 bits under Windows x64.
    actual.set_paused_override =
        reinterpret_cast<ck3_11906::TacticalSetPausedV1>(
            actual.module_base + kTacticalSentinelSetPausedWrapperRva12004);
  }
  return ck3_11906::InstallTacticalDailySentinelV1(state, actual);
}

} // namespace xar::ck3_12004
