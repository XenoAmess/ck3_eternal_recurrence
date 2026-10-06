#pragma once
#include "xar_bridge/ck3_12002_phase_advantage.hpp"
#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_12003 {
struct CurrentLandSupplyRateBindings12003 {
  bool enabled = false;
  bool (*province_component_condition)(void *) = nullptr;
  ck3_12002::ReadAdvantageModifierValue read_province_component = nullptr;
  void **character_storage_slot = nullptr;
  void **character_fallback_slot = nullptr;
  void *(*get_character_modifier_aggregator)(void *) = nullptr;
  std::int64_t *(*read_character_modifier)(void *, std::int64_t *, std::int32_t) = nullptr;
  const std::int64_t *loaded_excess_slope_raw = nullptr;
  const std::int64_t *loaded_min_loss_raw = nullptr;
  const std::int64_t *loaded_max_loss_raw = nullptr;
  const std::int64_t *loaded_divisor_floor_raw = nullptr;
};
game::ArmyCurrentLandSupplyRateInputsV1 ReadCurrentLandSupplyRateInputs12003(
    const CurrentLandSupplyRateBindings12003 &, void *army, void *unit,
    void *current_province, const game::ArmyCurrentLandResupplyV1 *same_capture_resupply);
} // namespace xar::ck3_12003
