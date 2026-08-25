#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::string_view kActualContactScopeV1StepPrefix =
    "query-actual-contact-scope-v1-";
inline constexpr std::string_view kActualContactScopeV1Capability =
    "game.command.query-actual-contact-scope-v1-N";
inline constexpr std::uint32_t
    kActualContactScopeV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kActualContactScopeV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseActualContactScopeV1Step(
    std::string_view step,
    game::ActualContactScopeRequest &output) noexcept;
bool ParseActualContactExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

enum class ActualContactScopeMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  available = 1,
  query_unavailable = 2,
  infrastructure_rejected = 3,
};

struct ActualContactScopeMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::ActualContactScopeRequest request{};
  ActualContactScopeMailboxCompletionV1 completion =
      ActualContactScopeMailboxCompletionV1::not_executed;
  game::ActualContactScopeSnapshot result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  ActualContactScopeMailboxContextV1() = default;
  ActualContactScopeMailboxContextV1(
      const ActualContactScopeMailboxContextV1 &) = delete;
  ActualContactScopeMailboxContextV1 &operator=(
      const ActualContactScopeMailboxContextV1 &) = delete;
};

bool ExecuteActualContactScopeMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view ActualContactScopeFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    ActualContactScopeMailboxCompletionV1 completion,
    game::ActualContactScopeStatus status,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteActualContactScopeMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
