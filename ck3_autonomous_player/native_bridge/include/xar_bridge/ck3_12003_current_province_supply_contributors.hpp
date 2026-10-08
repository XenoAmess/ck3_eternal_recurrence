#pragma once

#include "xar_bridge/game_contract.hpp"

namespace xar::ck3_12002 { struct ArmyBindings; }

namespace xar::ck3_12003 {

inline constexpr std::uintptr_t kSupplyContributorCommonWarSideRva12003 = 0x2C090F0;

struct CurrentProvinceSupplyContributorBindings12003 {
  bool enabled = false;
  bool (*shares_current_war_side)(void *, void *, void *) = nullptr;
};

// The current path supplies its same-query validated current Province. The
// actual4 first-route-target wrapper reuses this Province-context algorithm
// with a separately validated current target and a distinct outer DTO.
game::ArmyCurrentProvinceSupplyContributorsV1
ReadCurrentProvinceSupplyContributors12003(
    const ck3_12002::ArmyBindings &, void *subject_army,
    void *subject_unit, void *current_province);

} // namespace xar::ck3_12003
