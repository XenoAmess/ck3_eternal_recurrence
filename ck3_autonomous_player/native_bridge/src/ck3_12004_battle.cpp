#include "xar_bridge/ck3_12004_battle.hpp"
#include "xar_bridge/battle_control_owned_entry_preceding_12004.hpp"
#include "xar_bridge/battle_control_snapshot_v1_mailbox.hpp"

#include <array>
#include <utility>
#include "xar_bridge/ck3_12004_generic_gui.hpp"
#include "xar_bridge/ck3_12003_current_stored_context.hpp"

namespace xar::ck3_12004 {
namespace {
bool CopyCarrierSource(void *, const void *source, void *destination,
                       std::size_t bytes) noexcept {
  // Reuse the existing guarded physical copy, not an older ABI factory.
  return ck3_12002::current_stored_context_12003::CopyBytes(
      destination, source, bytes);
}
} // namespace

BattleBindings BindBattleImage(
    std::uintptr_t base, std::string_view sha,
    const BattleImageDependencies &dependencies) noexcept {
  BattleBindings bindings{};
  if (base == 0 || sha != kExecutableSha256)
    return bindings;

  // Proof: combat-map/pass01..pass04-leaves/FAMILY-MAP.json, plus the current
  // typed operand ledger. Roots owned by GeneralCombat/Province are injected.
  bindings.enabled = true;
  bindings.current_person_carrier_direct = BindPersonCarrierDirect12004(
      base, kGameVersion, sha, &CopyCarrierSource);
  bindings.current_person_conditional_opinion =
      BindPersonConditionalOpinionImage12004(base, sha);
  bindings.current_person_conditional_scope_weights =
      BindPersonConditionalScopeWeightsImage12004(base, sha);
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

  // The existing nested admission reader uses this readonly subset. Callback
  // and contact-field proofs are retained in arrival-readonly-migration.
  auto &arrival = bindings.route_bindings;
  arrival.enabled = bindings.enabled;
  arrival.game_state_slot = bindings.game_state_slot;
  arrival.jomini_state_slot = bindings.jomini_state_slot;
  arrival.army_storage_slot = bindings.army_storage_slot;
  arrival.army_internal_storage_slot = bindings.army_internal_storage_slot;
  arrival.character_storage_slot = bindings.character_storage_slot;
  arrival.combat_storage_slot = bindings.combat_storage_slot;
  arrival.contact_game_mode_slot =
      reinterpret_cast<void **>(base + kGuiGlobalSlotRva12004V1);
  arrival.is_character_hostile =
      reinterpret_cast<decltype(arrival.is_character_hostile)>(base + 0x2C09620);
  arrival.is_army_empty_for_contact =
      reinterpret_cast<decltype(arrival.is_army_empty_for_contact)>(
          base + 0x24E83A0);
  arrival.is_army_in_combat =
      reinterpret_cast<decltype(arrival.is_army_in_combat)>(base + 0x24E8340);

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

namespace {
void CollectOwnedEntryPreceding(void *opaque, const void *combat,
                               std::uint32_t full_id) noexcept {
  auto &owned = *static_cast<BattleControlOwnedEntryPreceding12004 *>(opaque);
  try {
    const std::array owners{EntryPrecedingCombatOwner12004{
        reinterpret_cast<std::uintptr_t>(combat), full_id}};
    owned.entry_preceding_capture =
        CollectEntryPrecedingCaptureForCombats12004(owners);
  } catch (...) {
    // A failed independent owned copy must not invalidate the old battle.
    owned.entry_preceding_capture.reset();
  }
}
} // namespace

game::BattleControlSnapshotStatus ReadBattleControlOwnedEntryPreceding12004(
    const BattleBindings &bindings, const game::Snapshot &paused_scope,
    const game::BattleControlRequest &request, bool exact_12004_admitted,
    std::uint64_t snapshot_revision,
    BattleControlOwnedEntryPreceding12004 &owned) noexcept {
  owned = {};
  BattleAcceptedCombatCollector12004 collector{};
  if (exact_12004_admitted && snapshot_revision != 0) {
    collector.context = &owned;
    collector.collect = &CollectOwnedEntryPreceding;
  }
  const auto status = ck3_12002::ReadBattleControlSnapshotWithOwnedCombat12004(
      bindings, paused_scope, request, owned.snapshot, collector);
  if (status != game::BattleControlSnapshotStatus::available) {
    owned.entry_preceding_capture.reset();
  } else {
    owned.snapshot.snapshot_revision = snapshot_revision;
  }
  return status;
}

std::string SerializeBattleControlOwnedEntryPreceding12004(
    const BattleControlOwnedEntryPreceding12004 &owned) {
  auto json = ck3_11906::SerializeBattleControlSnapshotV1(owned.snapshot);
  if (json.empty() || json.back() != '}' || !owned.entry_preceding_capture) {
    return json;
  }
  try {
    const auto raw = SerializeEntryPrecedingCapture12004(
        *owned.entry_preceding_capture);
    constexpr std::string_view key = ",\"entry_preceding_capture_12004\":";
    if (!raw.empty() && json.size() + key.size() + raw.size() <=
        ck3_11906::kBattleControlSnapshotV1WireMaximumBytes) {
      auto appended = json;
      appended.pop_back();
      appended += key;
      appended += raw;
      appended += '}';
      return appended;
    }
  } catch (...) {
    // Retain the complete existing battle wire if its optional append failed.
  }
  return json;
}

} // namespace xar::ck3_12004
