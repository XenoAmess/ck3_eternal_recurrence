#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_career_hc_workforce_postcondition_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoCareerHcWorkforceV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoCareerHcWorkforceV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoCareerHcWorkforcePostconditionV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoCareerHcWorkforcePostconditionRequestV1(
    std::string_view json,
    ZhongguoCareerHcWorkforcePostconditionRequestV1 &output,
    std::int32_t &requested_owner_character_id) noexcept;

enum class ZhongguoCareerHcWorkforceMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoCareerHcWorkforceMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoCareerHcWorkforceNativeEnvironmentV1 environment{};
  ZhongguoCareerHcWorkforceAccessV1 access{};
  ZhongguoCareerHcWorkforcePostconditionRequestV1 request{};
  std::int32_t requested_owner_character_id = -1;
  game::Snapshot expected_snapshot{};
  ZhongguoCareerHcWorkforceMailboxCompletionV1 completion =
      ZhongguoCareerHcWorkforceMailboxCompletionV1::not_executed;
  game::ReadZhongguoCareerHcWorkforcePostconditionResultV1 read_result =
      game::ReadZhongguoCareerHcWorkforcePostconditionResultV1::unavailable;
  game::ZhongguoCareerHcWorkforcePostconditionV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoCareerHcWorkforceMailboxContextV1() = default;
  ZhongguoCareerHcWorkforceMailboxContextV1(
      const ZhongguoCareerHcWorkforceMailboxContextV1 &) = delete;
  ZhongguoCareerHcWorkforceMailboxContextV1 &operator=(
      const ZhongguoCareerHcWorkforceMailboxContextV1 &) = delete;
};

bool ExecuteZhongguoCareerHcWorkforceMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoCareerHcWorkforceFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoCareerHcWorkforceMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoCareerHcWorkforceMailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
