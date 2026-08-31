#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_workforce_collective_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoWorkforceCollectiveSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoWorkforceCollectiveSnapshotV1ExecutingWaitSliceMilliseconds =
        2'000;

bool ParseZhongguoWorkforceCollectiveSnapshotV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoWorkforceCollectiveSnapshotRequestV1(
    std::string_view json,
    ZhongguoWorkforceCollectiveSnapshotRequestV1 &output) noexcept;

enum class ZhongguoWorkforceCollectiveSnapshotMailboxCompletionV1
    : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoWorkforceCollectiveSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoWorkforceNativeEnvironmentV1 environment{};
  ZhongguoWorkforceAccessV1 access{};
  ZhongguoWorkforceCollectiveSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};
  ZhongguoWorkforceCollectiveSnapshotMailboxCompletionV1 completion =
      ZhongguoWorkforceCollectiveSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoWorkforceCollectiveSnapshotResultV1 read_result =
      game::ReadZhongguoWorkforceCollectiveSnapshotResultV1::unavailable;
  game::ZhongguoWorkforceCollectiveSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoWorkforceCollectiveSnapshotMailboxContextV1() = default;
  ZhongguoWorkforceCollectiveSnapshotMailboxContextV1(
      const ZhongguoWorkforceCollectiveSnapshotMailboxContextV1 &) = delete;
  ZhongguoWorkforceCollectiveSnapshotMailboxContextV1 &operator=(
      const ZhongguoWorkforceCollectiveSnapshotMailboxContextV1 &) = delete;
};

bool ExecuteZhongguoWorkforceCollectiveSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoWorkforceCollectiveSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoWorkforceCollectiveSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoWorkforceCollectiveSnapshotMailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
