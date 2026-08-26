#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/pending_character_interaction_context_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kPendingCharacterInteractionContextV1QueuedWaitBudgetMilliseconds =
        8'000;
inline constexpr std::uint32_t
    kPendingCharacterInteractionContextV1ExecutingWaitSliceMilliseconds =
        2'000;

bool ParsePendingCharacterInteractionContextV1Step(
    std::string_view step) noexcept;
bool ParsePendingCharacterInteractionContextRequestV1(
    std::string_view json, std::uint64_t &expected_revision,
    std::int32_t &pending_interaction_id) noexcept;

enum class PendingCharacterInteractionContextMailboxCompletionV1
    : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct PendingCharacterInteractionContextMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  PendingCharacterInteractionNativeEnvironmentV1 environment{};
  PendingCharacterInteractionAccessV1 access{};
  PendingCharacterInteractionContextRequestV1 request{};
  game::Snapshot expected_snapshot{};

  PendingCharacterInteractionContextMailboxCompletionV1 completion =
      PendingCharacterInteractionContextMailboxCompletionV1::not_executed;
  game::ReadPendingCharacterInteractionContextResultV1 read_result =
      game::ReadPendingCharacterInteractionContextResultV1::unavailable;
  game::PendingCharacterInteractionContextV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  PendingCharacterInteractionContextMailboxContextV1() = default;
  PendingCharacterInteractionContextMailboxContextV1(
      const PendingCharacterInteractionContextMailboxContextV1 &) = delete;
  PendingCharacterInteractionContextMailboxContextV1 &operator=(
      const PendingCharacterInteractionContextMailboxContextV1 &) = delete;
  PendingCharacterInteractionContextMailboxContextV1(
      PendingCharacterInteractionContextMailboxContextV1 &&) = delete;
  PendingCharacterInteractionContextMailboxContextV1 &operator=(
      PendingCharacterInteractionContextMailboxContextV1 &&) = delete;
};

bool ExecutePendingCharacterInteractionContextMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view PendingCharacterInteractionContextFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    PendingCharacterInteractionContextMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<
        decltype(&ExecutePendingCharacterInteractionContextMailboxQueryV1),
        MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
