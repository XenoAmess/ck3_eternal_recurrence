#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_workforce_owner_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoWorkforceOwnerV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoWorkforceOwnerV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoWorkforceOwnerSnapshotV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoWorkforceOwnerSnapshotRequestV1(
    std::string_view json, ZhongguoWorkforceOwnerRequestV1 &output,
    std::int32_t &requested_owner_character_id) noexcept;

enum class ZhongguoWorkforceOwnerMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoWorkforceOwnerMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoWorkforceOwnerNativeEnvironmentV1 environment{};
  ZhongguoWorkforceOwnerAccessV1 access{};
  ZhongguoWorkforceOwnerRequestV1 request{};
  std::int32_t requested_owner_character_id = -1;
  game::Snapshot expected_snapshot{};
  ZhongguoWorkforceOwnerMailboxCompletionV1 completion =
      ZhongguoWorkforceOwnerMailboxCompletionV1::not_executed;
  game::ReadZhongguoWorkforceOwnerResultV1 read_result =
      game::ReadZhongguoWorkforceOwnerResultV1::unavailable;
  game::ZhongguoWorkforceOwnerSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoWorkforceOwnerMailboxContextV1() = default;
  ZhongguoWorkforceOwnerMailboxContextV1(
      const ZhongguoWorkforceOwnerMailboxContextV1 &) = delete;
  ZhongguoWorkforceOwnerMailboxContextV1 &operator=(
      const ZhongguoWorkforceOwnerMailboxContextV1 &) = delete;
};

bool ExecuteZhongguoWorkforceOwnerMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoWorkforceOwnerFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoWorkforceOwnerMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoWorkforceOwnerMailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
