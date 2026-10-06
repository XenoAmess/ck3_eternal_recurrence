#include "xar_bridge/ck3_12004_battle_journal.hpp"

namespace xar::ck3_12004 {

ck3_12002::BattleTerminalJournalInstallEnvironmentV1
BindBattleJournalImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256,
    const ck3_12002::BattleBindings &actual_battle_bindings) noexcept {
  ck3_12002::BattleTerminalJournalInstallEnvironmentV1 environment{};
  if (image_base == 0 || executable_sha256 != kExecutableSha256 ||
      !actual_battle_bindings.enabled ||
      actual_battle_bindings.game_state_slot !=
          reinterpret_cast<void **>(image_base + kGameStateSlotRva) ||
      actual_battle_bindings.army_storage_slot !=
          reinterpret_cast<void **>(image_base +
                                    kBattleJournalUnitStorageRva12004) ||
      actual_battle_bindings.army_internal_storage_slot !=
          reinterpret_cast<void **>(image_base +
                                    kBattleJournalArmyStorageRva12004) ||
      actual_battle_bindings.battle_result_storage_slot !=
          reinterpret_cast<void **>(image_base + kBattleResultStorageRva)) {
    return environment;
  }

  // These are the roots used by InitializeBattleTerminalJournalStorageV1 and
  // its capture routines, independently proven for this actual image. Reusing
  // the software environment and installer does not call an older binder or
  // substitute an older SHA. Suspended-thread admission remains caller-owned.
  environment.bindings = actual_battle_bindings;
  if (!ConfigureBattleJournalTargets12004(environment, image_base,
                                         executable_sha256)) {
    return {};
  }
  environment.exact_build_admitted = true;
  return environment;
}

bool ConfigureBattleJournalTargets12004(
    ck3_12002::BattleTerminalJournalInstallEnvironmentV1 &environment,
    std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept {
  if (image_base == 0 || executable_sha256 != kExecutableSha256)
    return false;
  environment.module_base = image_base;
  environment.terminal_target_override =
      image_base + kBattleTerminalFinalizerRva12004;
  environment.warscore_target_override =
      image_base + kBattleWarscoreWriterRva12004;
  environment.side_result_target_override =
      image_base + kBattleSideResultProjectorRva12004;
  environment.character_append_target_override =
      image_base + kBattleCharacterResultAppendRva12004;
  return true;
}

} // namespace xar::ck3_12004
