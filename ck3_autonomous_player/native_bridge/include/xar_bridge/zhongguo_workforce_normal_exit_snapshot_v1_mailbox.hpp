#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoWorkforceNormalExitSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoWorkforceNormalExitSnapshotV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoWorkforceNormalExitSnapshotV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoWorkforceNormalExitSnapshotRequestV1(
    std::string_view json,
    ZhongguoWorkforceNormalExitSnapshotRequestV1 &output) noexcept;

enum class ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1
    : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoWorkforceNormalExitSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoWorkforceNormalExitNativeEnvironmentV1 environment{};
  ZhongguoWorkforceNormalExitAccessV1 access{};
  ZhongguoWorkforceNormalExitSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};
  ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1 completion =
      ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoWorkforceNormalExitSnapshotResultV1 read_result =
      game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
  game::ZhongguoWorkforceNormalExitSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoWorkforceNormalExitSnapshotMailboxContextV1() = default;
  ZhongguoWorkforceNormalExitSnapshotMailboxContextV1(
      const ZhongguoWorkforceNormalExitSnapshotMailboxContextV1 &) = delete;
  ZhongguoWorkforceNormalExitSnapshotMailboxContextV1 &operator=(
      const ZhongguoWorkforceNormalExitSnapshotMailboxContextV1 &) = delete;
};

bool ExecuteZhongguoWorkforceNormalExitSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoWorkforceNormalExitSnapshotMailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
