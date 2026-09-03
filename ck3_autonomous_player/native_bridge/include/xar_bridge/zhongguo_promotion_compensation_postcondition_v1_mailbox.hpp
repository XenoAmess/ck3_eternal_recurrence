#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_promotion_compensation_postcondition_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoPromotionCompensationV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoPromotionCompensationV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoPromotionCompensationPostconditionV1Step(
    std::string_view step) noexcept;
bool ParseZhongguoPromotionCompensationPostconditionRequestV1(
    std::string_view json, ZhongguoPromotionCompensationRequestV1 &output,
    std::int32_t &requested_owner_character_id) noexcept;

enum class ZhongguoPromotionCompensationMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct ZhongguoPromotionCompensationMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoPromotionCompensationNativeEnvironmentV1 environment{};
  ZhongguoPromotionCompensationAccessV1 access{};
  ZhongguoPromotionCompensationRequestV1 request{};
  std::int32_t requested_owner_character_id = -1;
  game::Snapshot expected_snapshot{};
  ZhongguoPromotionCompensationMailboxCompletionV1 completion =
      ZhongguoPromotionCompensationMailboxCompletionV1::not_executed;
  game::ReadZhongguoPromotionCompensationResultV1 read_result =
      game::ReadZhongguoPromotionCompensationResultV1::unavailable;
  game::ZhongguoPromotionCompensationPostconditionV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ZhongguoPromotionCompensationMailboxContextV1() = default;
  ZhongguoPromotionCompensationMailboxContextV1(
      const ZhongguoPromotionCompensationMailboxContextV1 &) = delete;
  ZhongguoPromotionCompensationMailboxContextV1 &operator=(
      const ZhongguoPromotionCompensationMailboxContextV1 &) = delete;
};

bool ExecuteZhongguoPromotionCompensationMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoPromotionCompensationFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoPromotionCompensationMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(std::is_same_v<
              decltype(&ExecuteZhongguoPromotionCompensationMailboxQueryV1),
              MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
