#pragma once

#include "xar_bridge/ck3_12004_council_candidates.hpp"
#include "xar_bridge/ck3_12004_council_action_runtime.hpp"
#include "xar_bridge/council_application_main_v1.hpp"

namespace xar::ck3_12004 {

// One combined context and persistent ACK state for the existing operations.
// The shared entry supplies the current .4 core/published-revision source frame.
// Candidate queries run here; final gates, submit and receipt use the internal
// action delegate on this same context, active stamp and wire, without copies.
using CouncilMailboxState12004 = CouncilActionMailboxState12004;
using CouncilMailboxContext12004 = CouncilActionMailboxContext12004;

bool ExecuteCouncilMailbox12004(void* context,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept;
std::string SerializeCouncilMailbox12004(
    const CouncilMailboxContext12004& context, std::string_view request_id);

} // namespace xar::ck3_12004
