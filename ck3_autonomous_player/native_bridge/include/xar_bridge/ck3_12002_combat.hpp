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
};

// The same owning-thread paused snapshot supplies participant/war scope.
// No process discovery, remote reads or changes to CK3 state are performed.
CombatBindings BindCombatImage(std::uintptr_t image_base,
                              std::string_view executable_sha256) noexcept;
game::ReadCombatSimulationInputsResult ReadCombatSimulationInputs(
    const CombatBindings &bindings, const game::Snapshot &paused_scope,
    const game::CombatSimulationInputsRequest &request,
    game::CombatSimulationInputsSnapshot &output) noexcept;

} // namespace xar::ck3_12002
