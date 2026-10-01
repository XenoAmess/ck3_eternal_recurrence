#pragma once
#include "xar_bridge/ck3_12002_council_candidates.hpp"
#include "xar_bridge/ck3_12002_council_gates.hpp"
#include "xar_bridge/ck3_12002_council_assign.hpp"
#include "xar_bridge/council_application_main_v1.hpp"

namespace xar::ck3_12002 {
struct CouncilMailboxState12002 {
  game::CouncilAssignCouncillorActionAckV1 pending_ack{};
  std::uint64_t pending_submit_sequence = 0;
  bool has_pending_ack = false;
};
struct CouncilMailboxContext12002 {
  CouncilCandidatesEnvironmentV1 candidates_environment{};
  CouncilCandidatesAccessV1 candidates_access{};
  CouncilGatesEnvironment12002 gates_environment{};
  CouncilAssignSubmit12002 submit{};
  CouncilMailboxState12002* shared_state = nullptr;
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

// Caller binds the new providers and supplies a current campaign source frame
// callback to candidates_access. Execute is the existing mailbox executor ABI.
bool ExecuteCouncilMailbox12002(void* context,
    const ck3_11906::MainThreadExecutionStampV1& stamp) noexcept;
std::string SerializeCouncilMailbox12002(
    const CouncilMailboxContext12002& context, std::string_view request_id);
} // namespace xar::ck3_12002
