#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::string_view kBattleTerminalTransitionV1StepPrefix =
    "query-battle-terminal-transition-v1-";
inline constexpr std::string_view kBattleTerminalTransitionV1Capability =
    "game.command.query-battle-terminal-transition-v1";
inline constexpr std::uint32_t
    kBattleTerminalTransitionV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kBattleTerminalTransitionV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseBattleTerminalTransitionV1Step(
    std::string_view step,
    game::BattleTerminalTransitionRequestV1 &output) noexcept;
bool ParseBattleTerminalTransitionExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

enum class BattleTerminalTransitionMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct BattleTerminalTransitionMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::BattleTerminalTransitionRequestV1 request{};
  std::uint64_t expected_snapshot_revision = 0;
  game::Snapshot expected_snapshot{};

  BattleTerminalTransitionMailboxCompletionV1 completion =
      BattleTerminalTransitionMailboxCompletionV1::not_executed;
  game::BattleTerminalTransitionSnapshotV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  BattleTerminalTransitionMailboxContextV1() = default;
  BattleTerminalTransitionMailboxContextV1(
      const BattleTerminalTransitionMailboxContextV1 &) = delete;
  BattleTerminalTransitionMailboxContextV1 &operator=(
      const BattleTerminalTransitionMailboxContextV1 &) = delete;
  BattleTerminalTransitionMailboxContextV1(
      BattleTerminalTransitionMailboxContextV1 &&) = delete;
  BattleTerminalTransitionMailboxContextV1 &operator=(
      BattleTerminalTransitionMailboxContextV1 &&) = delete;
};

bool ExecuteBattleTerminalTransitionMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view BattleTerminalTransitionFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    BattleTerminalTransitionMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

std::string SerializeBattleTerminalTransitionV1(
    const game::BattleTerminalTransitionSnapshotV1 &snapshot);

static_assert(
    std::is_same_v<
        decltype(&ExecuteBattleTerminalTransitionMailboxQueryV1),
        MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
