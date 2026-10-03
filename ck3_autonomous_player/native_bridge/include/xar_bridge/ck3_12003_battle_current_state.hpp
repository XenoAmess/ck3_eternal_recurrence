#pragma once

#include "xar_bridge/ck3_12002_battle.hpp"

namespace xar::ck3_12003 {

// The production caller binds the reviewed BattleBindings only after its
// exact 1.20.0.3 descriptor gate. This additive leaf never changes a completed
// ID-only lifecycle read, and requires no player-controlled army.
void AttachBattleCurrentObservationV1(
    const ck3_12002::BattleBindings &, const game::Snapshot &paused_scope,
    game::BattleTransitionSnapshot &) noexcept;

} // namespace xar::ck3_12003
