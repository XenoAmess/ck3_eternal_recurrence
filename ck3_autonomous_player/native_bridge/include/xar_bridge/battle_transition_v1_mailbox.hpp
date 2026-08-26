#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::string_view kBattleTransitionV1StepPrefix =
    "query-battle-transition-v1-";
inline constexpr std::string_view kBattleTransitionV1Capability =
    "game.command.query-battle-transition-v1-N";
inline constexpr std::uint32_t
    kBattleTransitionV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kBattleTransitionV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseBattleTransitionV1Step(
    std::string_view step, game::BattleTransitionRequest &output) noexcept;
bool ParseBattleTransitionExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;
std::string_view BattleTransitionStatusNameV1(
    game::BattleTransitionSnapshotStatus status) noexcept;

enum class BattleTransitionMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct BattleTransitionMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::BattleTransitionRequest request{};
  std::uint64_t expected_snapshot_revision = 0;
  game::Snapshot expected_snapshot{};

  BattleTransitionMailboxCompletionV1 completion =
      BattleTransitionMailboxCompletionV1::not_executed;
  game::BattleTransitionSnapshot result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  BattleTransitionMailboxContextV1() = default;
  BattleTransitionMailboxContextV1(
      const BattleTransitionMailboxContextV1 &) = delete;
  BattleTransitionMailboxContextV1 &operator=(
      const BattleTransitionMailboxContextV1 &) = delete;
  BattleTransitionMailboxContextV1(
      BattleTransitionMailboxContextV1 &&) = delete;
  BattleTransitionMailboxContextV1 &operator=(
      BattleTransitionMailboxContextV1 &&) = delete;
};

bool ExecuteBattleTransitionMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view BattleTransitionFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    BattleTransitionMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

// Serializes all four typed semantic states. Identity, date and revision are
// present in every state; lifecycle fields are null when no stable CCombat was
// available, and side arrays are always present.
std::string SerializeBattleTransitionV1(
    const game::BattleTransitionSnapshot &snapshot);

static_assert(
    std::is_same_v<decltype(&ExecuteBattleTransitionMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
