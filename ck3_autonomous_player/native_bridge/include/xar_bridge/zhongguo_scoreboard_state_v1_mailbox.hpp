#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_scoreboard_state_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoScoreboardStateV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoScoreboardStateV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoScoreboardStateV1Step(std::string_view step) noexcept;
bool ParseZhongguoScoreboardStateRequestV1(
    std::string_view json, ZhongguoScoreboardStateRequestV1 &output) noexcept;

enum class ZhongguoScoreboardStateMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoScoreboardStateMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ZhongguoScoreboardAccessV1 access{};
  ZhongguoScoreboardStateRequestV1 request{};
  game::Snapshot expected_snapshot{};

  ZhongguoScoreboardStateMailboxCompletionV1 completion =
      ZhongguoScoreboardStateMailboxCompletionV1::not_executed;
  game::ReadZhongguoScoreboardStateResultV1 read_result =
      game::ReadZhongguoScoreboardStateResultV1::unavailable;
  game::ZhongguoScoreboardStateV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoScoreboardStateMailboxContextV1() = default;
  ZhongguoScoreboardStateMailboxContextV1(
      const ZhongguoScoreboardStateMailboxContextV1 &) = delete;
  ZhongguoScoreboardStateMailboxContextV1 &operator=(
      const ZhongguoScoreboardStateMailboxContextV1 &) = delete;
  ZhongguoScoreboardStateMailboxContextV1(
      ZhongguoScoreboardStateMailboxContextV1 &&) = delete;
  ZhongguoScoreboardStateMailboxContextV1 &operator=(
      ZhongguoScoreboardStateMailboxContextV1 &&) = delete;
};

bool ExecuteZhongguoScoreboardStateMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoScoreboardStateFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoScoreboardStateMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteZhongguoScoreboardStateMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
