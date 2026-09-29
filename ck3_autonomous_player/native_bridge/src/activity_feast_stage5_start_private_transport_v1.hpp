#pragma once

#include "xar_bridge/activity_feast_stage5_start_v1.hpp"
#include "xar_bridge/activity_stage5_canstart_read_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityFeastStage5InputsPrivateStepV1 =
    "query-activity-feast-stage5-start-inputs-v1-private";
inline constexpr std::string_view kActivityFeastStage5StartPrivateStepV1 =
    "start-activity-feast-stage5-v1-private";
inline constexpr std::string_view kActivityFeastHostedPostPrivateStepV1 =
    "query-activity-feast-hosted-post-v1-private";

enum class ActivityFeastStage5PrivateModeV1 {
  start_inputs,
  start_attempt,
  hosted_post,
};

struct ActivityFeastStage5PrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  ActivityFeastStage5PrivateModeV1 mode =
      ActivityFeastStage5PrivateModeV1::start_inputs;
  bool policy_positive = false;
  bool previous_submit_pending = false;
  std::array<std::int64_t, 4> reserve_raw{};
  bridge::ActivityFeastStage5StartSnapshotV1 inputs{};
  bridge::ActivityFeastStage5PostV1 post{};
  bridge::ActivityFeastStage5StartResultV1 start{};
  bridge::ActivityStage5FeastFullCostStatusV1 cost_status =
      bridge::ActivityStage5FeastFullCostStatusV1::gold_gate_red;
  bridge::ActivityStage5CanStartStatusV1 can_start_status =
      bridge::ActivityStage5CanStartStatusV1::exact_build_rejected;
  bridge::ActivityFeastBalanceStatusV1 balance_status =
      bridge::ActivityFeastBalanceStatusV1::exact_build_rejected;
  bridge::ActivityHostedIdentityStatusV1 hosted_status =
      bridge::ActivityHostedIdentityStatusV1::exact_build_rejected;
  // Stage-5 invited-guest arrival/benefit source is not yet live qualified.
  bool guest_route_qualified = false;
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityFeastStage5PrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityFeastStage5PrivateV1(
    const ActivityFeastStage5PrivateQueryV1 &query);

} // namespace xar::ck3_11906
