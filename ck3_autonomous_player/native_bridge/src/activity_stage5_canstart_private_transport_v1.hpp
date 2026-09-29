#pragma once

#include "xar_bridge/activity_stage5_canstart_read_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActivityStage5CanStartPrivateStepV1 =
    "query-activity-stage5-canstart-v1-private";

struct ActivityStage5CanStartPrivateQueryV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_revision = 0;
  bridge::ActivityStage5CanStartResultV1 result{};
  bool completed = false;
  bool frame_changed = false;
  std::uint32_t invocations = 0;
  std::string failure{};
};

bool ExecuteActivityStage5CanStartPrivateV1(
    void *context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string SerializeActivityStage5CanStartPrivateV1(
    const ActivityStage5CanStartPrivateQueryV1 &query);

} // namespace xar::ck3_11906
