#pragma once

#include "xar_bridge/ck3_12002_combat.hpp"
#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_12003 {

inline constexpr std::uintptr_t kCurrentProvinceResupplyEligibleRva12003 = 0x2C09D30;
inline constexpr std::uintptr_t kLoadedUnderLimitSupplyGainRva12003 = 0x5C69A50;

struct CurrentLandResupplyBindings12003 {
  bool enabled = false;
  // The established combat predicate has precisely the owner/Province ABI.
  ck3_12002::IsHoldingDefender is_resupply_eligible = nullptr;
  bool (*is_army_fleet_supply_active)(void *) = nullptr;
  void **character_storage_slot = nullptr;
  const std::int64_t *loaded_gain_raw = nullptr;
};

// Army/Unit/current Province were validated by this same Strength capture.
game::ArmyCurrentLandResupplyV1 ReadCurrentLandResupply12003(
    const CurrentLandResupplyBindings12003 &, void *army,
    void *unit, void *current_province);

} // namespace xar::ck3_12003
