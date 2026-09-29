#pragma once

#include "xar_bridge/activity_feast_planner_open_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityFeastPlannerOpenPrivateStepV1 =
    "open-activity-feast-planner-v1-private";

struct ActivityFeastPlannerOpenPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityFeastPlannerOpenResultV1 result{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityFeastPlannerOpenPrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityFeastPlannerOpenPrivateV1(
    const ActivityFeastPlannerOpenPrivateQueryV1 &query);

} // namespace xar::ck3_11906
