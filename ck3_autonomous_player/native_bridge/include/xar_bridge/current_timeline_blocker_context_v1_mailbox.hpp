#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/current_timeline_blocker_context_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kCurrentTimelineBlockerContextV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kCurrentTimelineBlockerContextV1ExecutingWaitSliceMilliseconds = 2'000;

enum class CurrentTimelineBlockerContextMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct CurrentTimelineBlockerContextMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ZhongguoScoreboardAccessV1 access{};
  CurrentTimelineBlockerReadRequestV1 request{};
  game::Snapshot expected_snapshot{};

  CurrentTimelineBlockerContextMailboxCompletionV1 completion =
      CurrentTimelineBlockerContextMailboxCompletionV1::not_executed;
  game::ReadCurrentTimelineBlockerContextResultV1 read_result =
      game::ReadCurrentTimelineBlockerContextResultV1::unavailable;
  game::CurrentTimelineBlockerContextV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  CurrentTimelineBlockerContextMailboxContextV1() = default;
  CurrentTimelineBlockerContextMailboxContextV1(
      const CurrentTimelineBlockerContextMailboxContextV1 &) = delete;
  CurrentTimelineBlockerContextMailboxContextV1 &operator=(
      const CurrentTimelineBlockerContextMailboxContextV1 &) = delete;
  CurrentTimelineBlockerContextMailboxContextV1(
      CurrentTimelineBlockerContextMailboxContextV1 &&) = delete;
  CurrentTimelineBlockerContextMailboxContextV1 &operator=(
      CurrentTimelineBlockerContextMailboxContextV1 &&) = delete;
};

bool ExecuteCurrentTimelineBlockerContextMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view CurrentTimelineBlockerContextFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    CurrentTimelineBlockerContextMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<
        decltype(&ExecuteCurrentTimelineBlockerContextMailboxQueryV1),
        MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
