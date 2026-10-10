#pragma once
#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include <iosfwd>
namespace xar::ck3_12004 {
void AppendArmyNaturalPhaseEvent12004(std::ostream &, const ArmyNaturalPhaseEvent12004 &);
void AppendArmyNaturalPhaseScope12004(std::ostream &, const ArmyNaturalPhaseScope12004 &);
void AppendArmyNaturalPhaseRecord12004(std::ostream &, const ArmyNaturalPhaseRecord12004 &);
void AppendArmyNaturalPhaseJournal12004(std::ostream &, const std::vector<ArmyNaturalPhaseRecord12004> &);
void AppendArmyNaturalPhaseJournalStatus12004(std::ostream &, const ArmyNaturalPhaseJournalStatus12004 &);
} // namespace xar::ck3_12004
