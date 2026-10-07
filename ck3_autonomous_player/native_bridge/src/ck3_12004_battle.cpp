#include "xar_bridge/ck3_12004_battle.hpp"

namespace xar::ck3_12004 {

BattleBindings BindBattleImage(
    std::uintptr_t base, std::string_view sha,
    const BattleImageDependencies &dependencies) noexcept {
  BattleBindings bindings{};
  if (base == 0 || sha != kExecutableSha256)
    return bindings;

  // Proof: combat-map/pass01..pass04-leaves/FAMILY-MAP.json, plus the current
  // typed operand ledger. Roots owned by GeneralCombat/Province are injected.
  bindings.enabled = true;
  bindings.game_state_slot =
      reinterpret_cast<void **>(base + kGameStateSlotRva);
  bindings.jomini_state_slot =
      reinterpret_cast<void **>(base + kJominiStateSlotRva);
  bindings.character_storage_slot =
      reinterpret_cast<void **>(base + kCharacterStorageSlotRva);
  bindings.combat_storage_slot =
      reinterpret_cast<void **>(base + kBattleCombatStorageRva);
  bindings.battle_result_storage_slot =
      reinterpret_cast<void **>(base + kBattleResultStorageRva);
  bindings.battle_result_fallback_slot =
      reinterpret_cast<void **>(base + kBattleResultFallbackRva);
  bindings.army_storage_slot = dependencies.combat_context.army_storage_slot;
  bindings.army_internal_storage_slot =
      dependencies.combat_context.army_internal_storage_slot;
  bindings.army_internal_fallback_slot =
      dependencies.army_internal_fallback_slot;
  bindings.regiment_storage_slot =
      dependencies.combat_context.regiment_storage_slot;
  // Independent actual4 lookup/producer/COL proofs are retained in
  // upstream-build-migration/reinforcement-ai-binding-review. The shared
  // reader still requires actual current AI membership for each subject.
  bindings.ai_war_coordinator_storage_slot =
      reinterpret_cast<void **>(base + 0x5D20550);
  bindings.ai_unit_stack_vtable = base + 0x45AA618;
  bindings.ai_subunit_stack_vtable = base + 0x45AB4C0;
  bindings.ai_war_coordinator_vtable = base + 0x45AB0C8;
  bindings.province_context = dependencies.province_context;
  bindings.resolve_province = dependencies.resolve_province;

  bindings.minimum_days_before_manual_retreat =
      reinterpret_cast<const std::int32_t *>(
          base + kBattleMinimumRetreatDaysRva);
  bindings.roll_cadence_interval =
      reinterpret_cast<const std::int32_t *>(
          base + kBattleRollCadenceIntervalRva);
  bindings.advantage_scaling = reinterpret_cast<const std::int64_t *>(
      base + kBattleAdvantageScalingRva);
  bindings.get_combat_side_strength =
      reinterpret_cast<decltype(bindings.get_combat_side_strength)>(
          base + kBattleSideStrengthRva);
  bindings.get_combat_regiment_strength =
      reinterpret_cast<decltype(bindings.get_combat_regiment_strength)>(
          base + kBattleEntryStrengthRva);
  bindings.can_order_combat_retreat =
      reinterpret_cast<decltype(bindings.can_order_combat_retreat)>(
          base + kBattleCanRetreatRva);
  bindings.get_combat_retreat_rule_state =
      reinterpret_cast<decltype(bindings.get_combat_retreat_rule_state)>(
          base + kBattleRetreatRuleRva);
  bindings.province_has_holding =
      reinterpret_cast<decltype(bindings.province_has_holding)>(
          base + kBattleProvinceHasHoldingRva);
  bindings.read_loss_province_modifier =
      reinterpret_cast<ck3_12002::ReadAdvantageModifierValue>(
          base + kBattleProvinceModifierRva);

  bindings.commander_roll_context = dependencies.combat_context;
  bindings.commander_roll_context.get_character_modifier_aggregator =
      reinterpret_cast<ck3_12002::GetCharacterModifierAggregator>(
          base + kBattleCharacterModifierAggregatorRva);
  bindings.commander_roll_context.read_character_modifier =
      reinterpret_cast<ck3_12002::ReadCharacterModifier>(
          base + kBattleCharacterModifierReadRva);
  bindings.commander_roll_context.commander_min_roll =
      reinterpret_cast<const std::int32_t *>(base + kBattleCommanderMinRollRva);
  bindings.commander_roll_context.commander_max_roll =
      reinterpret_cast<const std::int32_t *>(base + kBattleCommanderMaxRollRva);

  EnableBattleCurrentFinalizerManagerInputs(bindings, base, sha);
  return bindings;
}

void EnableBattleCurrentFinalizerManagerInputs(
    BattleBindings &bindings, std::uintptr_t base,
    std::string_view sha) noexcept {
  // The exact .4 constructor's actual RIP-relative LEA resolves 477F188.
  // This admission is independent of older manager binders.
  bindings.current_finalizer_manager_secondary_vtable =
      bindings.enabled && base != 0 && sha == kExecutableSha256
          ? base + kBattleFinalizerManagerSecondaryVtableRva
          : 0;
}

std::optional<game::BattleControlCurrentFinalizerManagerInputsV1>
ReadCurrentFinalizerManagerInputs(
    const BattleBindings &bindings, const void *strict_actual_combat,
    std::int32_t requested_full_combat_id) noexcept {
  // The memory-only implementation takes the expected actual vtable from
  // bindings. Mapped date/constructor/daily operands retain A0,2E9D0 and the
  // manager's selected same-Combat list and base+60 raw byte.
  return ck3_12002::ReadCurrentFinalizerManagerInputs12003(
      bindings, strict_actual_combat, requested_full_combat_id);
}

game::BattleControlSnapshotStatus ReadBattleControlSnapshot(
    const BattleBindings &bindings, const game::Snapshot &paused_scope,
    const game::BattleControlRequest &request,
    game::BattleControlSnapshot &output) noexcept {
  // Reuse the production double sample and its existing strict fullID checks.
  return ck3_12002::ReadBattleControlSnapshot(
      bindings, paused_scope, request, output);
}

game::BattleTransitionSnapshotStatus ReadBattleTransitionSnapshot(
    const BattleBindings &bindings, const game::Snapshot &paused_scope,
    const game::BattleTransitionRequest &request,
    game::BattleTransitionSnapshot &output) noexcept {
  return ck3_12002::ReadBattleTransitionSnapshot(
      bindings, paused_scope, request, output);
}

} // namespace xar::ck3_12004
