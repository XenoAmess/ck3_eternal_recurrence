#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_action_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

// This capability means only that the exact request can cross the shared
// application-main mailbox and return a typed fail-closed result.  It is not
// the production action capability and must not be treated as permission to
// dispatch a GUI callback.
inline constexpr std::string_view
    kZhongguoScoreboardActionV1TransportCapability =
        "game.contract.zhongguo-scoreboard-action-v1-fail-closed";

inline constexpr std::uint32_t
    kZhongguoScoreboardActionV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoScoreboardActionV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoScoreboardActionV1Step(std::string_view step) noexcept;
bool ParseZhongguoScoreboardActionRequestV1(
    std::string_view json,
    game::ZhongguoScoreboardActionRequestV1 &output) noexcept;

enum class ZhongguoScoreboardActionMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed_unavailable = 1,
  completed_acknowledged = 2,
  frame_changed = 3,
  infrastructure_rejected = 4,
};

struct ZhongguoScoreboardActionMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ZhongguoScoreboardActionDispatchEnvironmentV1 dispatch_environment{};
  ZhongguoScoreboardAccessV1 state_access{};
  ZhongguoScoreboardActionAccessV1 action_access{};
  game::ZhongguoScoreboardActionRequestV1 request{};
  game::Snapshot expected_snapshot{};
  ZhongguoScoreboardProviderRevisionTrackerV1 *provider_revision_tracker =
      nullptr;

  ZhongguoScoreboardActionMailboxCompletionV1 completion =
      ZhongguoScoreboardActionMailboxCompletionV1::not_executed;
  game::ReadZhongguoScoreboardStateResultV1 state_read_result =
      game::ReadZhongguoScoreboardStateResultV1::unavailable;
  game::ZhongguoScoreboardStateV1 source{};
  game::ZhongguoScoreboardActionAckV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoScoreboardActionMailboxContextV1() = default;
  ZhongguoScoreboardActionMailboxContextV1(
      const ZhongguoScoreboardActionMailboxContextV1 &) = delete;
  ZhongguoScoreboardActionMailboxContextV1 &operator=(
      const ZhongguoScoreboardActionMailboxContextV1 &) = delete;
  ZhongguoScoreboardActionMailboxContextV1(
      ZhongguoScoreboardActionMailboxContextV1 &&) = delete;
  ZhongguoScoreboardActionMailboxContextV1 &operator=(
      ZhongguoScoreboardActionMailboxContextV1 &&) = delete;
};

bool ExecuteZhongguoScoreboardActionMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoScoreboardActionFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoScoreboardActionMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteZhongguoScoreboardActionMailboxV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
