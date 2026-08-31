#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_incident_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoIncidentSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoIncidentSnapshotV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoIncidentSnapshotV1Step(std::string_view step) noexcept;
bool ParseZhongguoIncidentSnapshotRequestV1(
    std::string_view json,
    ZhongguoIncidentSnapshotRequestV1 &output) noexcept;

enum class ZhongguoIncidentSnapshotMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoIncidentSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoIncidentNativeEnvironmentV1 environment{};
  ZhongguoIncidentAccessV1 access{};
  ZhongguoIncidentSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};

  ZhongguoIncidentSnapshotMailboxCompletionV1 completion =
      ZhongguoIncidentSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoIncidentSnapshotResultV1 read_result =
      game::ReadZhongguoIncidentSnapshotResultV1::unavailable;
  game::ZhongguoIncidentSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoIncidentSnapshotMailboxContextV1() = default;
  ZhongguoIncidentSnapshotMailboxContextV1(
      const ZhongguoIncidentSnapshotMailboxContextV1 &) = delete;
  ZhongguoIncidentSnapshotMailboxContextV1 &operator=(
      const ZhongguoIncidentSnapshotMailboxContextV1 &) = delete;
  ZhongguoIncidentSnapshotMailboxContextV1(
      ZhongguoIncidentSnapshotMailboxContextV1 &&) = delete;
  ZhongguoIncidentSnapshotMailboxContextV1 &operator=(
      ZhongguoIncidentSnapshotMailboxContextV1 &&) = delete;
};

bool ExecuteZhongguoIncidentSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoIncidentSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoIncidentSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteZhongguoIncidentSnapshotMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
