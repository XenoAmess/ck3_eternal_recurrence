#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::string_view
    kBattleReinforcementAssignmentV1StepPrefix =
        "query-battle-reinforcement-assignment-v1-";
inline constexpr std::string_view
    kBattleReinforcementAssignmentV1Capability =
        "game.command.query-battle-reinforcement-assignment-v1-N";
inline constexpr std::uint32_t
    kBattleReinforcementAssignmentV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kBattleReinforcementAssignmentV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseBattleReinforcementAssignmentV1Step(
    std::string_view step,
    game::BattleReinforcementAssignmentRequest &output) noexcept;
bool ParseBattleReinforcementAssignmentExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

enum class BattleReinforcementAssignmentMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct BattleReinforcementAssignmentMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::BattleReinforcementAssignmentRequest request{};
  std::uint64_t expected_snapshot_revision = 0;
  game::Snapshot expected_snapshot{};

  BattleReinforcementAssignmentMailboxCompletionV1 completion =
      BattleReinforcementAssignmentMailboxCompletionV1::not_executed;
  game::BattleReinforcementAssignmentSnapshot result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  BattleReinforcementAssignmentMailboxContextV1() = default;
  BattleReinforcementAssignmentMailboxContextV1(
      const BattleReinforcementAssignmentMailboxContextV1 &) = delete;
  BattleReinforcementAssignmentMailboxContextV1 &operator=(
      const BattleReinforcementAssignmentMailboxContextV1 &) = delete;
  BattleReinforcementAssignmentMailboxContextV1(
      BattleReinforcementAssignmentMailboxContextV1 &&) = delete;
  BattleReinforcementAssignmentMailboxContextV1 &operator=(
      BattleReinforcementAssignmentMailboxContextV1 &&) = delete;
};

bool ExecuteBattleReinforcementAssignmentMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view BattleReinforcementAssignmentFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    BattleReinforcementAssignmentMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

std::string SerializeBattleReinforcementAssignmentV1(
    const game::BattleReinforcementAssignmentSnapshot &snapshot);

static_assert(
    std::is_same_v<
        decltype(&ExecuteBattleReinforcementAssignmentMailboxQueryV1),
        MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
