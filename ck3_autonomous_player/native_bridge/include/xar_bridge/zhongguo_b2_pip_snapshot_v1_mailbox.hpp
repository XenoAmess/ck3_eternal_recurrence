#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_b2_pip_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoB2PipSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoB2PipSnapshotV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoB2PipSnapshotV1Step(std::string_view step) noexcept;
bool ParseZhongguoB2PipSnapshotRequestV1(
    std::string_view json, ZhongguoB2PipSnapshotRequestV1 &output) noexcept;

enum class ZhongguoB2PipSnapshotMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoB2PipSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoB2PipNativeEnvironmentV1 environment{};
  ZhongguoB2PipAccessV1 access{};
  ZhongguoB2PipSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};
  ZhongguoB2PipSnapshotMailboxCompletionV1 completion =
      ZhongguoB2PipSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoB2PipSnapshotResultV1 read_result =
      game::ReadZhongguoB2PipSnapshotResultV1::unavailable;
  game::ZhongguoB2PipSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoB2PipSnapshotMailboxContextV1() = default;
  ZhongguoB2PipSnapshotMailboxContextV1(
      const ZhongguoB2PipSnapshotMailboxContextV1 &) = delete;
  ZhongguoB2PipSnapshotMailboxContextV1 &operator=(
      const ZhongguoB2PipSnapshotMailboxContextV1 &) = delete;
};

bool ExecuteZhongguoB2PipSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoB2PipSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoB2PipSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteZhongguoB2PipSnapshotMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
