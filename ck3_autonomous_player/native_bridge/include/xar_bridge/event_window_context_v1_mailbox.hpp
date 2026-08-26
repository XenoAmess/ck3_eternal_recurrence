#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/event_window_context_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kEventWindowContextV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kEventWindowContextV1ExecutingWaitSliceMilliseconds = 2'000;

enum class EventWindowContextMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  infrastructure_rejected = 2,
};

struct EventWindowContextMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_snapshot_revision = 0;
  std::int32_t expected_event_instance_id = -1;

  EventWindowContextMailboxCompletionV1 completion =
      EventWindowContextMailboxCompletionV1::not_executed;
  game::ReadEventWindowContextResultV1 read_result =
      game::ReadEventWindowContextResultV1::unavailable;
  game::EventWindowContextV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  EventWindowContextMailboxContextV1() = default;
  EventWindowContextMailboxContextV1(
      const EventWindowContextMailboxContextV1 &) = delete;
  EventWindowContextMailboxContextV1 &operator=(
      const EventWindowContextMailboxContextV1 &) = delete;
};

bool ExecuteEventWindowContextMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view EventWindowContextFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    EventWindowContextMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteEventWindowContextMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
