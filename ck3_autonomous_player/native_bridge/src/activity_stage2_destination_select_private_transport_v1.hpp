#pragma once

#include "xar_bridge/activity_stage2_destination_select_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityStage2DestinationSelectPrivateStepV1 =
    "select-activity-feast-stage2-destination-v1-private";

struct ActivityStage2DestinationSelectPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  std::int32_t province_id = 0;
  bridge::ActivityStage2DestinationResultV1 result{};
  bridge::ActivityStage2DestinationStateV1 before{};
  bridge::ActivityStage2DestinationStateV1 after{};
  bool before_read = false;
  bool after_read = false;
  bool completed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityStage2DestinationSelectPrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityStage2DestinationSelectPrivateV1(
    const ActivityStage2DestinationSelectPrivateQueryV1 &query);

} // namespace xar::ck3_11906
