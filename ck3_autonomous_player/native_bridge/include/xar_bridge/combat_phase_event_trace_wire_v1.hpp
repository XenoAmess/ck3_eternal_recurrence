#pragma once

#include "xar_bridge/combat_phase_event_trace_ring_v1.hpp"

#include <cstddef>
#include <string>

namespace xar::ck3_11906 {

// The enclosing command_result and protocol header also consume frame space.
// Keep the trace fragment below 900 KiB so it can never make the bridge's
// frozen 1 MiB frame limit fail only after the managed one-day trace ran.
inline constexpr std::size_t kCombatPhaseEventTraceWireMaximumBytesV1 =
    900U * 1024U;

// Serializes only stable IDs, values, bounded strings and per-process opaque
// event identity tokens.  Native object/code addresses are intentionally not
// published.  A bounded seven-record capture can be returned while the
// independent original_trace_ready gate remains false.
std::string SerializeCombatPhaseEventTraceRingDrainV1(
    const CombatPhaseEventTraceRingDrainV1 &drain);

} // namespace xar::ck3_11906
