#pragma once

#include "xar_bridge/activity_feast_guest_candidate_v1.hpp"
#include "xar_bridge/activity_stage5_canstart_read_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityFeastGuestCandidatePrivateStepV1 =
    "query-activity-feast-guest-candidate-v1";
inline constexpr std::string_view kActivityFeastGuestRouteProofPrivateStepV1 =
    "query-activity-feast-stage5-guest-route-proof-v1-private";

struct ActivityFeastGuestCandidatePrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  bool route_proof = false;
  bridge::ActivityFeastGuestCandidateResultV1 candidate{};
  bridge::ActivityFeastGuestJoinResultV1 selected_guests{};
  bridge::ActivityStage5CanStartResultV1 start_gate{};
  bool route_proof_consistent = false;
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityFeastGuestCandidatePrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityFeastGuestCandidatePrivateV1(
    const ActivityFeastGuestCandidatePrivateQueryV1 &query);
std::string SerializeActivityFeastGuestRouteProofPrivateV1(
    const ActivityFeastGuestCandidatePrivateQueryV1 &query);

} // namespace xar::ck3_11906
