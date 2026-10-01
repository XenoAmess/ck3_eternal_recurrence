#pragma once

#include "xar_bridge/ck3_12002_nonwar_mailbox.hpp"
#include "xar_bridge/game_adapter.hpp"
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
#include "xar_bridge/ck3_12002_council_transport.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
#include "xar_bridge/ck3_12002_faction_gift_router.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
#include "xar_bridge/ck3_12002_sway_mailbox.hpp"
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
#include "xar_bridge/ck3_12002_prisoner_mailbox.hpp"
#endif

namespace xar::bridge {
struct ActivityCostSlot12ObserverV1;
struct ActivityGuestRuleProvenanceObserverV1;
}

namespace xar::ck3_12002 {

// One worker owns these existing domain ledgers across MCP reconnections.
struct NonwarPrivateState12002 {
  std::uint64_t faction_query_sequence = 0;
#if defined(XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1)
  CouncilTransportState12002 council{};
#endif
#if defined(XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1)
  FactionGiftPrivateState12002 gift{};
#endif
#if defined(XAR_CK3_ENABLE_G2_ACTIVE_SCHEME_PRIVATE_CANDIDATE_V1)
  ActiveSwayState12002 sway{};
#endif
#if defined(XAR_CK3_ENABLE_G2_PRISONER_COLLECTION_PRIVATE_QUERY_V1)
  PrisonerPrivateWorkerState12002 prisoner{};
#endif
};

void PopulateNonwarRouterExecutors12002(NonwarMailboxExecutorsV1 &) noexcept;
bool IsNonwarPrivateStep12002(std::string_view step) noexcept;
void PollNonwarPrivateState12002(NonwarPrivateState12002 &) noexcept;
bool HandleNonwarPrivate12002(
    const game::GameAdapter &, ck3_11906::MainThreadQueryMailboxV1 &,
    const game::Snapshot &, std::uint64_t revision, std::string_view step,
    std::string_view payload, std::string_view request_id,
    NonwarPrivateState12002 &, std::string &serialized, std::string &failure,
    bridge::ActivityCostSlot12ObserverV1 *cost = nullptr,
    bridge::ActivityGuestRuleProvenanceObserverV1 *provenance = nullptr) noexcept;

} // namespace xar::ck3_12002
