#pragma once

#include "xar_bridge/activity_planner_diag_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityPlannerDiagPrivateStepV1 =
    "query-activity-planner-diag-v1-private";

struct ActivityPlannerDiagPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityPlannerDiagResultV1 diagnostic{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityPlannerDiagPrivateQueryV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityPlannerDiagPrivateQueryV1(
    const ActivityPlannerDiagPrivateQueryV1 &query);

} // namespace xar::ck3_11906
