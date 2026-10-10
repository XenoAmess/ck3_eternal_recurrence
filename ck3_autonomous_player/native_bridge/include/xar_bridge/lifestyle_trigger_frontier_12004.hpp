#pragma once
#include "xar_bridge/lifestyle_trigger_frontier_types_12004.hpp"

namespace xar::ck3_12004 {
// Called by47e once after copying the class/slots, while the existing ReadOne
// command/query frame remains alive and before its existing Validate call.
// Inputs contain owned values only; no temporary software scope is borrowed.
LifestyleTriggerFrontierPacket12004 BuildLifestylePerkTriggerFrontier12004(
    const SourceLeafReadOnlyAccess12004 &,
    const LifestyleTriggerFrontierInputs12004 &) noexcept;
} // namespace xar::ck3_12004
