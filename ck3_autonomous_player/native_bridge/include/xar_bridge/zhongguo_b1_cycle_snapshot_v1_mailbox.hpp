#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_b1_cycle_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoB1CycleSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoB1CycleSnapshotV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoB1CycleSnapshotV1Step(std::string_view step) noexcept;
bool ParseZhongguoB1CycleSnapshotRequestV1(
    std::string_view json, ZhongguoB1CycleSnapshotRequestV1 &output) noexcept;

enum class ZhongguoB1CycleSnapshotMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoB1CycleSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoB1CycleNativeEnvironmentV1 environment{};
  ZhongguoB1CycleAccessV1 access{};
  ZhongguoB1CycleSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};
  ZhongguoB1CycleSnapshotMailboxCompletionV1 completion =
      ZhongguoB1CycleSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoB1CycleSnapshotResultV1 read_result =
      game::ReadZhongguoB1CycleSnapshotResultV1::unavailable;
  game::ZhongguoB1CycleSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
};

bool ExecuteZhongguoB1CycleSnapshotMailboxQueryV1(
    void *opaque_context, const MainThreadExecutionStampV1 &stamp) noexcept;
std::string_view ZhongguoB1CycleSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoB1CycleSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoB1CycleSnapshotMailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
