#pragma once

#include <cstdint>

namespace xar::game {

// Current same-Combat manager operands. Availability does not predict a future
// dispatch or a complete suppression sweep; raw zero remains an observation.
struct BattleControlCurrentFinalizerManagerInputsV1 {
  std::int32_t source_combat_id = -1;
  bool combat_manager_row_admitted = false;
  std::uint8_t pending_suppression_sweep_raw = 0;
  bool pending_suppression_sweep = false;

  friend bool operator==(
      const BattleControlCurrentFinalizerManagerInputsV1 &,
      const BattleControlCurrentFinalizerManagerInputsV1 &) = default;
};

} // namespace xar::game
