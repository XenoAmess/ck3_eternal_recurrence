#pragma once

#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_12002 {

using GetArmyCommander = void *(*)(void *);
using GetCommanderAdvantage = std::int32_t (*)(void *, std::int32_t, bool);
using GetProvinceTerrain = void *(*)(void *);
using EvaluateRegimentStatsAtProvince = void *(*)(void *, void *, void *);
using IsSpecialCombatRegiment = bool (*)(void *);
using GetCharacterModifierAggregator = void *(*)(void *);
using ReadCharacterModifier = std::int64_t *(*)(void *, std::int64_t *, std::int32_t);
using GetCombatRules = void *(*)();
using ReadCounterCurrentChunk = std::int64_t *(*)(const void *, std::int64_t *);
using ResolveCounterClasses = void (*)(void *, void *, void *, std::int64_t);
using GetCounterContextScale = std::int64_t *(*)(std::int64_t *, void *, void *);
using GetKnightEffectivenessContext = void *(*)(void *);
using ReadKnightEffectiveness = std::int64_t *(*)(std::int64_t *, void *, std::uint64_t);
using IsHoldingDefender = bool (*)(void *, void *);
using MaaGetObject = void *(*)(void *);
using MaaGetPietyRank = std::int32_t (*)(void *);
using MaaGetTier = void *(*)(std::int32_t, void *);
using MaaGetSelectorFactor = std::int64_t *(*)(std::int64_t *, void *, void *);
using MaaGetTypeEnvironment = const void *(*)(void *, void *);
using MaaGetLinkedEnvironment = void *(*)(void *, void *, void *, const void *);

struct CombatBindings {
  bool enabled = false;
  void **game_state_slot = nullptr;
  void **army_storage_slot = nullptr;
  void **army_internal_storage_slot = nullptr;
  void **regiment_storage_slot = nullptr;
  void **character_storage_slot = nullptr;
  void **combat_storage_slot = nullptr;
  GetArmyCommander get_army_commander = nullptr;
  GetCommanderAdvantage get_commander_advantage = nullptr;
  GetProvinceTerrain get_province_terrain = nullptr;
  EvaluateRegimentStatsAtProvince evaluate_regiment_stats_at_province = nullptr;
  IsSpecialCombatRegiment is_special_combat_regiment = nullptr;
  GetCharacterModifierAggregator get_character_modifier_aggregator = nullptr;
  ReadCharacterModifier read_character_modifier = nullptr;
  GetCombatRules get_combat_rules = nullptr;
  ReadCounterCurrentChunk read_counter_current_chunk = nullptr;
  ResolveCounterClasses resolve_counter_classes = nullptr;
  GetCounterContextScale get_counter_context_scale = nullptr;
  GetKnightEffectivenessContext get_knight_effectiveness_context = nullptr;
  ReadKnightEffectiveness read_knight_effectiveness = nullptr;
  IsHoldingDefender is_holding_defender = nullptr;
  const std::int32_t *commander_min_roll = nullptr;
  const std::int32_t *commander_max_roll = nullptr;
  const std::int32_t *knight_damage_per_prowess = nullptr;
  const std::int32_t *knight_toughness_per_prowess = nullptr;
  const std::int32_t *minimum_combat_width = nullptr;
  const std::int64_t *base_combat_width_ratio = nullptr;
  bool ordinary_stat_inputs_enabled = false;
  void **ordinary_regiment_storage_slot = nullptr;
  void **ordinary_regiment_fallback_slot = nullptr;
  void **ordinary_selector_storage_slot = nullptr;
  void **ordinary_selector_fallback_slot = nullptr;
  void **ordinary_character_fallback_slot = nullptr;
  std::array<const std::int64_t *, 5> ordinary_stat_loaded_bases{};
  bool maa_stat_inputs_enabled = false;
  bool knight_model_association_enabled = false;
  void **maa_culture_storage_slot = nullptr, **maa_culture_fallback_slot = nullptr;
  void **maa_army_regiment_fallback_slot = nullptr;
  void **maa_accolade_storage_slot = nullptr, **maa_accolade_fallback_slot = nullptr;
  MaaGetObject maa_get_government = nullptr, maa_get_actual_army = nullptr;
  MaaGetObject maa_get_title_holder = nullptr;
  MaaGetPietyRank maa_get_piety_rank = nullptr;
  MaaGetTier maa_get_tier = nullptr;
  MaaGetSelectorFactor maa_get_selector_factor = nullptr;
  std::array<MaaGetTypeEnvironment, 3> maa_get_type_environment{};
  std::array<MaaGetLinkedEnvironment, 3> maa_get_linked_environment{};
};

// Source-closed only for exact .3; the unchanged .2 binder leaves this disabled.
void EnableOrdinaryRegimentStatInputs12003(
    CombatBindings &, std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
void EnableMaaRegimentStatInputs12003(
    CombatBindings &, std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
void EnableKnightModelAssociation12003(
    CombatBindings &, std::uintptr_t image_base, std::string_view executable_sha256) noexcept;

// The same owning-thread paused snapshot supplies participant/war scope.
// No process discovery, remote reads or changes to CK3 state are performed.
CombatBindings BindCombatImage(std::uintptr_t image_base,
                              std::string_view executable_sha256) noexcept;
// Readonly terrain tuple for an already validated actual Province. The caller
// binds it to its existing CombatID/province/date/revision frame.
game::CombatTerrainSnapshot ReadProvinceTerrainSnapshot(
    const CombatBindings &, void *actual_province) noexcept;

// Readonly endpoints for an already selected battle commander and actual
// combat terrain. Reuses the v2 modifier reader; never calls native RNG.
game::BattleControlNextRollBoundsSnapshot ReadSelectedCommanderNextRollBounds(
    const CombatBindings &, std::int32_t province_id, void *terrain,
    std::int32_t selected_character_id) noexcept;

// Actual ongoing MAA counter census; caller supplies the same paused sample.
// Copies battle Entry Q100000 counts and never invokes outgoing/counter writes.
game::BattleControlCounterInputsV1 ReadActiveBattleCounterInputsV1(
    const CombatBindings &, const void *actual_combat,
    const game::BattleControlSnapshot &) noexcept;

game::ReadCombatSimulationInputsResult ReadCombatSimulationInputs(
    const CombatBindings &bindings, const game::Snapshot &paused_scope,
    const game::CombatSimulationInputsRequest &request,
    game::CombatSimulationInputsSnapshot &output) noexcept;

} // namespace xar::ck3_12002
