#pragma once

#include "xar_bridge/death_succession_modal_continue_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kDeathSuccessionModalContinueV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kDeathSuccessionModalContinueV1ExecutingWaitSliceMilliseconds = 2'000;

enum class DeathSuccessionModalContinueMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct DeathSuccessionModalContinueMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  ZhongguoScoreboardNativeEnvironmentV1 environment{};
  ZhongguoScoreboardAccessV1 access{};
  DeathSuccessionModalContinueRequestV1 request{};
  game::Snapshot expected_snapshot{};

  DeathSuccessionModalContinueMailboxCompletionV1 completion =
      DeathSuccessionModalContinueMailboxCompletionV1::not_executed;
  game::DeathSuccessionModalContinueReceiptV1 receipt{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  DeathSuccessionModalContinueMailboxContextV1() = default;
  DeathSuccessionModalContinueMailboxContextV1(
      const DeathSuccessionModalContinueMailboxContextV1 &) = delete;
  DeathSuccessionModalContinueMailboxContextV1 &operator=(
      const DeathSuccessionModalContinueMailboxContextV1 &) = delete;
};

bool ExecuteDeathSuccessionModalContinueMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view DeathSuccessionModalContinueFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    DeathSuccessionModalContinueMailboxCompletionV1 completion,
    std::string_view typed_reason) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteDeathSuccessionModalContinueMailboxV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
