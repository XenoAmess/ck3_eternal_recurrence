#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/zhongguo_promotion_source_progress_v1.hpp"

#include <cstdint>
#include <string_view>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kZhongguoPromotionSourceProgressV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kZhongguoPromotionSourceProgressV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseZhongguoPromotionSourceProgressV1Step(std::string_view step) noexcept;
bool ParseZhongguoPromotionSourceProgressRequestV1(
    std::string_view json, ZhongguoPromotionSourceProgressRequestV1 &output,
    std::int32_t &requested_owner_character_id) noexcept;
bool ParseZhongguoReviewNowActionV1Step(std::string_view step) noexcept;
bool ParseZhongguoReviewNowActionRequestV1(
    std::string_view json, game::ZhongguoReviewNowActionRequestV1 &output) noexcept;

enum class ZhongguoPromotionSourceMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed_available = 1,
  completed_unavailable = 2,
  frame_changed = 3,
  infrastructure_rejected = 4,
};

enum class ZhongguoPromotionSourceMailboxOperationV1 : std::uint32_t {
  query_progress = 1,
  activate_review_now = 2,
};

struct ZhongguoPromotionSourceProgressMailboxContextV1 {
  ZhongguoPromotionSourceMailboxOperationV1 operation =
      ZhongguoPromotionSourceMailboxOperationV1::query_progress;
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoPromotionSourceProgressNativeEnvironmentV1 environment{};
  ZhongguoPromotionSourceProgressAccessV1 access{};
  ZhongguoPromotionSourceProgressRequestV1 request{};
  std::int32_t requested_owner_character_id = -1;
  game::Snapshot expected_snapshot{};
  ZhongguoPromotionSourceMailboxCompletionV1 completion =
      ZhongguoPromotionSourceMailboxCompletionV1::not_executed;
  game::ReadZhongguoPromotionSourceProgressResultV1 read_result =
      game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
  game::ZhongguoPromotionSourceProgressV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
};

struct ZhongguoReviewNowActionMailboxContextV1 {
  ZhongguoPromotionSourceMailboxOperationV1 operation =
      ZhongguoPromotionSourceMailboxOperationV1::activate_review_now;
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoPromotionSourceProgressNativeEnvironmentV1 environment{};
  ZhongguoScoreboardActionDispatchEnvironmentV1 dispatch_environment{};
  ZhongguoPromotionSourceProgressAccessV1 access{};
  ZhongguoReviewNowActionAccessV1 action_access{};
  game::ZhongguoReviewNowActionRequestV1 request{};
  game::Snapshot expected_snapshot{};
  ZhongguoPromotionSourceMailboxCompletionV1 completion =
      ZhongguoPromotionSourceMailboxCompletionV1::not_executed;
  game::ReadZhongguoPromotionSourceProgressResultV1 read_result =
      game::ReadZhongguoPromotionSourceProgressResultV1::unavailable;
  game::ZhongguoPromotionSourceProgressV1 source{};
  game::ZhongguoReviewNowActionAckV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;
};

bool ExecuteZhongguoPromotionSourceProgressMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecuteZhongguoReviewNowActionMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;
bool ExecuteZhongguoPromotionSourceMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ZhongguoPromotionSourceFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ZhongguoPromotionSourceMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

} // namespace xar::ck3_11906
