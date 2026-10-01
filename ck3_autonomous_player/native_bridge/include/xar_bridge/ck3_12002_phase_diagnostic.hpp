#pragma once

#include "xar_bridge/ck3_12002_phase.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPhaseNonreligiousDiagnosticStepPrefix =
    "query-combat-phase-nonreligious-v1-";

struct PhaseDiagnosticSnapshot {
  game::CombatSimulationInputsV3Snapshot inputs;
  game::ReadCombatSimulationInputsV3Result query_result =
      game::ReadCombatSimulationInputsV3Result::unavailable;
  bool nonreligious_ready = false;
  std::string phase_json;
};

// A diagnostic may complete with unavailable phase operands. The returned
// readiness refers exclusively to the migrated nonreligious inputs.
bool ProjectPhaseNonreligiousDiagnostic(
    game::ReadCombatSimulationInputsV3Result,
    const game::CombatSimulationInputsV3Snapshot &,
    PhaseDiagnosticSnapshot &) noexcept;

// Called by the owning-thread mailbox with its already captured paused scope.
// The existing v2/phase reader owns all native work and temporary cleanup.
bool ReadPhaseNonreligiousDiagnostic(
    const PhaseBindings &, const game::Snapshot &,
    const game::CombatSimulationInputsRequest &,
    PhaseDiagnosticSnapshot &) noexcept;

} // namespace xar::ck3_12002
