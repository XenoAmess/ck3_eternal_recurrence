#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_result_case_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoResultCaseSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoResultCaseSnapshotV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoResultCaseSnapshotV1Step(std::string_view step) noexcept;
bool ParseZhongguoResultCaseSnapshotRequestV1(
    std::string_view json,
    ZhongguoResultCaseSnapshotRequestV1 &output) noexcept;

enum class ZhongguoResultCaseSnapshotMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoResultCaseSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoResultNativeEnvironmentV1 environment{};
  ZhongguoResultAccessV1 access{};
  ZhongguoResultCaseSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};

  ZhongguoResultCaseSnapshotMailboxCompletionV1 completion =
      ZhongguoResultCaseSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoResultCaseSnapshotResultV1 read_result =
      game::ReadZhongguoResultCaseSnapshotResultV1::unavailable;
  game::ZhongguoResultCaseSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoResultCaseSnapshotMailboxContextV1() = default;
  ZhongguoResultCaseSnapshotMailboxContextV1(
      const ZhongguoResultCaseSnapshotMailboxContextV1 &) = delete;
  ZhongguoResultCaseSnapshotMailboxContextV1 &operator=(
      const ZhongguoResultCaseSnapshotMailboxContextV1 &) = delete;
  ZhongguoResultCaseSnapshotMailboxContextV1(
      ZhongguoResultCaseSnapshotMailboxContextV1 &&) = delete;
  ZhongguoResultCaseSnapshotMailboxContextV1 &operator=(
      ZhongguoResultCaseSnapshotMailboxContextV1 &&) = delete;
};

bool ExecuteZhongguoResultCaseSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoResultCaseSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoResultCaseSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteZhongguoResultCaseSnapshotMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
