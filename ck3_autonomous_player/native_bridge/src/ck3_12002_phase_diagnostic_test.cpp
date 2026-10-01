#include "xar_bridge/ck3_12002_phase_diagnostic.hpp"

#include <cassert>
#include <iostream>

int main() {
  using namespace xar;
  using Result = game::ReadCombatSimulationInputsV3Result;
  ck3_12002::PhaseDiagnosticSnapshot diagnostic{};
  game::CombatSimulationInputsV3Snapshot inputs{};
  inputs.base_inputs.input_observation_ready = true;
  inputs.base_inputs.target_province_id = 701;
  inputs.phase_event_inputs.unavailable_reason = "phase_religion_and_rites_owner_deferred";
  inputs.phase_event_inputs.characters.emplace_back();
  inputs.phase_event_inputs.characters.back().character_id = 123;
  inputs.phase_event_inputs.characters.back().martial = 29;
  assert(ck3_12002::ProjectPhaseNonreligiousDiagnostic(Result::phase_inputs_unavailable,
                                                      inputs, diagnostic));
  assert(diagnostic.nonreligious_ready);
  assert(diagnostic.inputs.base_inputs.target_province_id == 701);
  assert(diagnostic.phase_json.find("\"martial\":29") != std::string::npos);
  assert(diagnostic.phase_json.find("\"complete_phase_inputs_ready\":false") != std::string::npos);
  assert(diagnostic.phase_json.find("91EDCEED") == std::string::npos);
  inputs.phase_event_inputs.unavailable_reason =
      "phase_nonreligious_operand_unavailable:identity_traits_tracks";
  assert(ck3_12002::ProjectPhaseNonreligiousDiagnostic(Result::phase_inputs_unavailable,
                                                      inputs, diagnostic));
  assert(!diagnostic.nonreligious_ready);
  assert(diagnostic.phase_json.find("identity_traits_tracks") != std::string::npos);
  assert(!ck3_12002::ProjectPhaseNonreligiousDiagnostic(Result::requires_paused,
                                                       inputs, diagnostic));
  assert(diagnostic.query_result == Result::requires_paused);
  assert(diagnostic.phase_json.empty() && diagnostic.inputs.base_inputs.target_province_id == -1);

  game::CombatSimulationInputsRequest request{};
  request.target_province_id = 1;
  request.attacker_entry_province_id = 2;
  request.attacker_army_ids = {11};
  request.defender_army_ids = {12};
  game::Snapshot scope{};
  auto bindings = ck3_12002::BindPhaseImage(1, ck3_12002::kExecutableSha256);
  assert(bindings.enabled);
  // Pure address bindings are intentionally never dereferenced: both reader
  // preconditions below return before resolving a game object or calling native.
  assert(!ck3_12002::ReadPhaseNonreligiousDiagnostic(bindings, scope, request, diagnostic));
  assert(diagnostic.query_result == Result::requires_paused);
  scope.paused = true;
  assert(!ck3_12002::ReadPhaseNonreligiousDiagnostic(bindings, scope, request, diagnostic));
  assert(diagnostic.query_result == Result::no_played_character);
  bindings = ck3_12002::BindPhaseImage(1, "old-build");
  assert(!ck3_12002::ReadPhaseNonreligiousDiagnostic(bindings, scope, request, diagnostic));
  assert(diagnostic.query_result == Result::unavailable);
  std::cout << "PASS nonreligious phase diagnostic projection and paused preconditions\n";
}
