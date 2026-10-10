#pragma once

#include "xar_bridge/lifestyle_trigger_frontier_types_12004.hpp"

namespace xar::ck3_12004 {

inline constexpr std::uintptr_t kTriggerDescriptorValidatorCallerRva12004 = 0x372E0AE;
inline constexpr std::uintptr_t kTriggerDescriptorValidatorReturnRva12004 = 0x372E0B0;

// Implements 16e's descriptor_al lane from 47e's same-query owned copies.
// The source projection has no physical rootScope alias. This adapter does
// not reread it, the descriptor, its target or the table provider. A concrete
// target model can be added only after that exact target's body is closed.
LifestyleTriggerLaneSource12004 ReadLifestyleDescriptorFrontier12004(
    const SourceLeafReadOnlyAccess12004 &,
    const LifestyleTriggerFrontierInputs12004 &) noexcept;

// A Root-owned observer may pass a separate actual original-once witness.
// This consumer validates the existing clock/frame/operand/return facts;
// it creates no event, invokes no native function, and infers no scope alias
// from the copied source projection. It preserves observed AL=0 as a value.
LifestyleTriggerLaneSource12004 QualifyLifestyleDescriptorNaturalWitness12004(
    const LifestyleTriggerFrontierInputs12004 &,
    const LifestyleTriggerNaturalWitness12004 &) noexcept;

} // namespace xar::ck3_12004
