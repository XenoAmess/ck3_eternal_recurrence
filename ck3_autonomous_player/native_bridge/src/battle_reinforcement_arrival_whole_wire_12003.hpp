#pragma once

#include "xar_bridge/battle_reinforcement_assignment_v1_mailbox.hpp"
#include <string>

namespace xar::game {

// Exercise the integrated production serializer seam. No native row is parsed,
// spliced or replaced after serialization.
inline std::string SerializeBattleReinforcementAssignmentWithArrival12003(
    const BattleReinforcementAssignmentSnapshot &frame,
    const BattleReinforcementArrivalAdmission12003Snapshot &admission) {
  auto whole = frame;
  if (!whole.contact_projection) return {};
  whole.contact_projection->arrival_admission = admission;
  return ck3_11906::SerializeBattleReinforcementAssignmentV1(whole);
}

} // namespace xar::game
