#pragma once
#include "xar_bridge/game_contract.hpp"
namespace xar::ck3_12002 { struct ArmyBindings; }
namespace xar::ck3_12003 {
game::ArmyCurrentDailyAssaultLossInputsV1 ReadCurrentDailyAssaultLossInputs12003(
    const ck3_12002::ArmyBindings &, const game::ArmyCurrentDailyAssaultTableV1 &);
} // namespace xar::ck3_12003
