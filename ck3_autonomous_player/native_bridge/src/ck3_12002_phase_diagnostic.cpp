#include "xar_bridge/ck3_12002_phase_diagnostic.hpp"

namespace xar::ck3_12002 {

bool ProjectPhaseNonreligiousDiagnostic(
    game::ReadCombatSimulationInputsV3Result result,
    const game::CombatSimulationInputsV3Snapshot &inputs,
    PhaseDiagnosticSnapshot &output) noexcept {
  output = {};
  output.query_result = result;
  if (result != game::ReadCombatSimulationInputsV3Result::available &&
      result != game::ReadCombatSimulationInputsV3Result::phase_inputs_unavailable)
    return false;
  try {
    output.inputs = inputs;
    output.nonreligious_ready = inputs.base_inputs.input_observation_ready &&
        inputs.phase_event_inputs.unavailable_reason ==
            "phase_religion_and_rites_implementation_pending";
    output.phase_json = SerializeCombatPhaseInputsV3(inputs.phase_event_inputs);
    return true;
  } catch (...) {
    output = {};
    return false;
  }
}

bool ReadPhaseNonreligiousDiagnostic(
    const PhaseBindings &bindings, const game::Snapshot &scope,
    const game::CombatSimulationInputsRequest &request,
    PhaseDiagnosticSnapshot &output) noexcept {
  game::CombatSimulationInputsV3Snapshot inputs{};
  const auto result = ReadCombatSimulationInputsV3(bindings, scope, request, inputs);
  return ProjectPhaseNonreligiousDiagnostic(result, inputs, output);
}

} // namespace xar::ck3_12002
