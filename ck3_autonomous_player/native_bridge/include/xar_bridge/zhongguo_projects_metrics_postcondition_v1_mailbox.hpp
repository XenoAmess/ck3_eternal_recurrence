#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_projects_metrics_postcondition_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoProjectsMetricsV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoProjectsMetricsV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoProjectsMetricsPostconditionV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoProjectsMetricsPostconditionRequestV1(
    std::string_view json, ZhongguoProjectsMetricsPostconditionRequestV1 &output,
    std::int32_t &requested_owner_character_id) noexcept;

enum class ZhongguoProjectsMetricsMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoProjectsMetricsMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoProjectsMetricsNativeEnvironmentV1 environment{};
  ZhongguoProjectsMetricsAccessV1 access{};
  ZhongguoProjectsMetricsPostconditionRequestV1 request{};
  std::int32_t requested_owner_character_id = -1;
  game::Snapshot expected_snapshot{};
  ZhongguoProjectsMetricsMailboxCompletionV1 completion =
      ZhongguoProjectsMetricsMailboxCompletionV1::not_executed;
  game::ReadZhongguoProjectsMetricsPostconditionResultV1 read_result =
      game::ReadZhongguoProjectsMetricsPostconditionResultV1::unavailable;
  game::ZhongguoProjectsMetricsPostconditionV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoProjectsMetricsMailboxContextV1() = default;
  ZhongguoProjectsMetricsMailboxContextV1(
      const ZhongguoProjectsMetricsMailboxContextV1 &) = delete;
  ZhongguoProjectsMetricsMailboxContextV1 &operator=(
      const ZhongguoProjectsMetricsMailboxContextV1 &) = delete;
};

bool ExecuteZhongguoProjectsMetricsMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoProjectsMetricsFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoProjectsMetricsMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoProjectsMetricsMailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
