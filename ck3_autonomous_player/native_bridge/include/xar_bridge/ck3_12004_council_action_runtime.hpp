#pragma once
#include "xar_bridge/ck3_12004_council_candidates.hpp"
#include "xar_bridge/ck3_12004_council_gates.hpp"
#include "xar_bridge/ck3_12004_council_assign.hpp"
#include "xar_bridge/council_application_main_v1.hpp"

namespace xar::ck3_12004 {
struct CouncilActionMailboxState12004 {
  game::CouncilAssignCouncillorActionAckV1 pending_ack{};
  std::uint64_t pending_submit_sequence = 0;
  bool has_pending_ack = false;
};
struct CouncilActionMailboxContext12004 {
  CouncilCandidatesEnvironmentV1 candidates_environment{};
  CouncilCandidatesAccessV1 candidates_access{};
  CouncilGatesEnvironment12004 gates_environment{};
  CouncilAssignSubmit12004 submit{};
  CouncilActionMailboxState12004* shared_state = nullptr;
  bool private_action_enabled = false;
  CouncilCandidatesRequestV1 query_request{};
  game::CouncilAssignCouncillorActionRequestV1 action_request{};
  bridge::CouncilApplicationMainOperationV1 operation =
      bridge::CouncilApplicationMainOperationV1::none;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  const ck3_11906::MainThreadExecutionStampV1* active_stamp = nullptr;
  // Existing pointer-free v1 DTO/wire container. Old-version binding unused.
  bridge::CouncilApplicationMainContextV1 wire{};
};

// Root slot 41 supplies the exact .4 providers and current campaign source frame.
// This delegate owns final gates, assignment and later receipt. The combined
// Council runtime aliases this context/state and handles query_candidates,
// so Root registers one context, executor and serializer for the family.
bool ExecuteCouncilActionMailbox12004(void* context,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept;
std::string SerializeCouncilActionMailbox12004(
    const CouncilActionMailboxContext12004& context, std::string_view request_id);
} // namespace xar::ck3_12004
