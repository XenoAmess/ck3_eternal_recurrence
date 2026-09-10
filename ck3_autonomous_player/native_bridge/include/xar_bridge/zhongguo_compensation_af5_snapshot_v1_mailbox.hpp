#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_compensation_af5_snapshot_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoCompensationAf5V1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoCompensationAf5V1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoCompensationAf5SnapshotV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoCompensationAf5SnapshotRequestV1(
    std::string_view json, ZhongguoCompensationAf5RequestV1 &output,
    std::int32_t &requested_owner_character_id) noexcept;

enum class ZhongguoCompensationAf5MailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoCompensationAf5MailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoCompensationAf5NativeEnvironmentV1 environment{};
  ZhongguoCompensationAf5AccessV1 access{};
  ZhongguoCompensationAf5RequestV1 request{};
  std::int32_t requested_owner_character_id = -1;
  game::Snapshot expected_snapshot{};
  ZhongguoCompensationAf5MailboxCompletionV1 completion =
      ZhongguoCompensationAf5MailboxCompletionV1::not_executed;
  game::ReadZhongguoCompensationAf5ResultV1 read_result =
      game::ReadZhongguoCompensationAf5ResultV1::unavailable;
  game::ZhongguoCompensationAf5SnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoCompensationAf5MailboxContextV1() = default;
  ZhongguoCompensationAf5MailboxContextV1(
      const ZhongguoCompensationAf5MailboxContextV1 &) = delete;
  ZhongguoCompensationAf5MailboxContextV1 &operator=(
      const ZhongguoCompensationAf5MailboxContextV1 &) = delete;
};

bool ExecuteZhongguoCompensationAf5MailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoCompensationAf5FailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoCompensationAf5MailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoCompensationAf5MailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
