#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_ai_owned_case_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoAiOwnedCaseSnapshotV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoAiOwnedCaseSnapshotV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoAiOwnedCaseSnapshotV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoAiOwnedCaseSnapshotRequestV1(
    std::string_view json,
    ZhongguoAiOwnedCaseSnapshotRequestV1 &output) noexcept;

enum class ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoAiOwnedCaseSnapshotMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoAiOwnedCaseNativeEnvironmentV1 environment{};
  ZhongguoAiOwnedCaseAccessV1 access{};
  ZhongguoAiOwnedCaseSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};

  ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1 completion =
      ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1::not_executed;
  game::ReadZhongguoAiOwnedCaseSnapshotResultV1 read_result =
      game::ReadZhongguoAiOwnedCaseSnapshotResultV1::unavailable;
  game::ZhongguoAiOwnedCaseSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoAiOwnedCaseSnapshotMailboxContextV1() = default;
  ZhongguoAiOwnedCaseSnapshotMailboxContextV1(
      const ZhongguoAiOwnedCaseSnapshotMailboxContextV1 &) = delete;
  ZhongguoAiOwnedCaseSnapshotMailboxContextV1 &operator=(
      const ZhongguoAiOwnedCaseSnapshotMailboxContextV1 &) = delete;
};

bool ExecuteZhongguoAiOwnedCaseSnapshotMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoAiOwnedCaseSnapshotFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoAiOwnedCaseSnapshotMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteZhongguoAiOwnedCaseSnapshotMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
