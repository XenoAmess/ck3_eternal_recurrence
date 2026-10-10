#pragma once

#include "xar_bridge/lifestyle_trigger_frontier_types_12004.hpp"

namespace xar::ck3_12004 {

// Metadata copied by a real original-return observer while the original
// 372B4EE output buffer is still alive. This leaf never installs that observer,
// calls the native target, requests a query, or allocates a clock event.
struct LifestyleRootMaskNaturalReturnBoundary12004 {
  LifestyleTriggerNaturalWitness12004 occurrence;
  std::uintptr_t receiver_vtable_identity = 0, slot_identity = 0;
  bool actual_original_return_boundary = false;
  bool output_buffer_valid_at_return = false;
  bool copied_read_frame_unchanged = false;
};

// Consumes already-owned TWO-QWORD output copies from a genuine producer.
// query_cursor/call_event/return_event must come from the existing shared13
// clock at this actual query/call/return, rather than ticket/proof metadata.
// Output admission is independent of the preferred-kind and final-AL lanes.
LifestyleTriggerLaneSource12004 AdmitLifestyleRootMaskNaturalWitness12004(
    const LifestyleTriggerFrontierInputs12004 &,
    const LifestyleTriggerNaturalWitness12004 &) noexcept;

// One guarded 16-byte copy at the real original return. No vptr/slot reread.
// A failed or incomplete read publishes neither QWORD as a complete output.
LifestyleTriggerLaneSource12004 CaptureLifestyleRootMaskNaturalReturn12004(
    const SourceLeafReadOnlyAccess12004 &,
    const LifestyleTriggerFrontierInputs12004 &,
    const LifestyleRootMaskNaturalReturnBoundary12004 &) noexcept;

} // namespace xar::ck3_12004
