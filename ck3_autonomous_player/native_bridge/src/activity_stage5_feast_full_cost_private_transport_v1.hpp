#pragma once

#include "xar_bridge/activity_stage5_canstart_read_v1.hpp"
#include "xar_bridge/activity_stage5_feast_full_cost_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "activity_stage5_canstart_failure_display_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityStage5FeastFullCostPrivateStepV1 =
    "query-activity-stage5-feast-full-cost-v1-private";

struct ActivityStage5FeastFullCostPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityCostSlot12ObserverV1 *passive_cost = nullptr;
  bridge::ActivityStage5FeastFullCostResultV1 cost{};
  bridge::ActivityStage5CanStartResultV1 can_start{};
  ActivityStage5FailureDisplayV1 can_start_failure_display{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityStage5FeastFullCostPrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityStage5FeastFullCostPrivateV1(
    const ActivityStage5FeastFullCostPrivateQueryV1 &query);

} // namespace xar::ck3_11906
