#include <cstdio>
#include <cstring>
#include <exception>
#include <cstddef>
#include <stdexcept>
#include <iostream>

void RunArmyNaturalPhaseScopeFocus12004();
void RunArmyNaturalPhaseInstallFocus12004();
void RunArmyPositionRelationNaturalFocus12004();
void RunArmyPositionHelperNaturalFocus12004();
void RunArmyPositionSelectedActorNaturalFocus12004();
void RunArmyPositionSelectedActorNaturalRetryAfterMappedNext12004();
bool RunArmyPosition2C09280Focus12004();
int RunArmyPositionSameWarSide12004FocusedTests();
namespace xar::ck3_12004 {
void RunArmyPositionNaturalFocus12004();
void RunArmyPositionMembership12004NewPhaseCases();
std::size_t RunArmyPosition28B2800NewFocus12004();
int RunArmyPosition2C3A0E012004Cases();
void RunArmyRegularCoreNaturalFocus12004();
}
void RunArmyAssaultPreparationNaturalFocus12004();
void RunArmyPlacementNaturalFocus12004();
void RunArmyAssaultConsumerNaturalFocus12004();
void RunArmyDueNaturalFocus12004();
void RunArmyMonthfirstCleanupNaturalFocus12004();
void RunArmyPrefixNaturalFocus12004();
void EmitArmyNaturalOwnedJournalsPacket12004(std::ostream &);

int main(int argc, char **argv) {
  const bool retry_after_selected_actor = argc == 2 &&
      std::strcmp(argv[1], "--army-natural-connected-phase-retry-after-selected-actor") == 0;
  if (argc != 2 || (!retry_after_selected_actor &&
      std::strcmp(argv[1], "--army-natural-connected-phase") != 0)) return 64;
  try {
    if (!retry_after_selected_actor) {
    RunArmyNaturalPhaseScopeFocus12004();
    RunArmyPositionRelationNaturalFocus12004();
    if (RunArmyPositionSameWarSide12004FocusedTests() != 12)
      throw std::runtime_error("new same-war-side cases incomplete");
    xar::ck3_12004::RunArmyPositionMembership12004NewPhaseCases();
    RunArmyPositionHelperNaturalFocus12004();
    RunArmyPositionSelectedActorNaturalFocus12004();
    } else {
      RunArmyPositionSelectedActorNaturalRetryAfterMappedNext12004();
    }
    if (!RunArmyPosition2C09280Focus12004()) throw std::runtime_error("new War gate cases failed");
    xar::ck3_12004::RunArmyPositionNaturalFocus12004();
    if (xar::ck3_12004::RunArmyPosition28B2800NewFocus12004() != std::size_t{10})
      throw std::runtime_error("new holder relation cases incomplete");
    if (xar::ck3_12004::RunArmyPosition2C3A0E012004Cases() <= 0)
      throw std::runtime_error("new hierarchy cases incomplete");
    xar::ck3_12004::RunArmyRegularCoreNaturalFocus12004();
    RunArmyAssaultPreparationNaturalFocus12004();
    RunArmyPlacementNaturalFocus12004();
    // This fragment invokes39b release and38c budget in the real37 child TLS.
    RunArmyAssaultConsumerNaturalFocus12004();
    RunArmyDueNaturalFocus12004();
    RunArmyMonthfirstCleanupNaturalFocus12004();
    // Prefix's final owned install locks fixture configuration; run it last.
    RunArmyPrefixNaturalFocus12004();
    RunArmyNaturalPhaseInstallFocus12004();
    EmitArmyNaturalOwnedJournalsPacket12004(std::cout);
    std::cout << '\n';
  } catch (const std::exception &error) {
    std::fprintf(stderr, "RED army natural connected phase: %s\n", error.what()); return 1;
  }
  std::puts("GREEN army natural connected phase: source entries, shared clock, exact roster, original once, child scopes, session unknown");
  return 0;
}
