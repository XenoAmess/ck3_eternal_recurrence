#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_case_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoCaseSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoCaseSnapshotV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoCaseSnapshotV1Step(std::string_view step) noexcept;
bool ParseZhongguoCaseSnapshotRequestV1(
    std::string_view json, ZhongguoCaseSnapshotRequestV1 &output) noexcept;

enum class ZhongguoCaseSnapshotMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoCaseSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoCaseNativeEnvironmentV1 environment{};
  ZhongguoCaseAccessV1 access{};
  ZhongguoCaseSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};

  ZhongguoCaseSnapshotMailboxCompletionV1 completion =
      ZhongguoCaseSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoCaseSnapshotResultV1 read_result =
      game::ReadZhongguoCaseSnapshotResultV1::unavailable;
  game::ZhongguoCaseSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoCaseSnapshotMailboxContextV1() = default;
  ZhongguoCaseSnapshotMailboxContextV1(
      const ZhongguoCaseSnapshotMailboxContextV1 &) = delete;
  ZhongguoCaseSnapshotMailboxContextV1 &operator=(
      const ZhongguoCaseSnapshotMailboxContextV1 &) = delete;
  ZhongguoCaseSnapshotMailboxContextV1(
      ZhongguoCaseSnapshotMailboxContextV1 &&) = delete;
  ZhongguoCaseSnapshotMailboxContextV1 &operator=(
      ZhongguoCaseSnapshotMailboxContextV1 &&) = delete;
};

bool ExecuteZhongguoCaseSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoCaseSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoCaseSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteZhongguoCaseSnapshotMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
