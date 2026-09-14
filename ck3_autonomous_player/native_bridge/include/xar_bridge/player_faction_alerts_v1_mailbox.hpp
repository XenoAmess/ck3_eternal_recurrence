#pragma once

#include "xar_bridge/campaign_root_context_v1.hpp"
#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/player_faction_alerts_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kPlayerFactionAlertsV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kPlayerFactionAlertsV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParsePlayerFactionAlertsV1Step(std::string_view step) noexcept;
bool ParsePlayerFactionAlertsExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

enum class PlayerFactionAlertsMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  completed = 1,
  frame_changed = 2,
  infrastructure_rejected = 3,
};

struct PlayerFactionAlertsMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  PlayerFactionAlertsNativeEnvironmentV1 environment{};
  CampaignRootNativeEnvironmentV1 campaign_root_environment{};
  PlayerFactionAlertsAccessV1 access{};
  PlayerFactionAlertsRequestV1 request{};
  game::Snapshot expected_snapshot{};

  PlayerFactionAlertsMailboxCompletionV1 completion =
      PlayerFactionAlertsMailboxCompletionV1::not_executed;
  game::ReadPlayerFactionAlertsResultV1 read_result =
      game::ReadPlayerFactionAlertsResultV1::unavailable;
  game::PlayerFactionAlertsV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  PlayerFactionAlertsMailboxContextV1() = default;
  PlayerFactionAlertsMailboxContextV1(
      const PlayerFactionAlertsMailboxContextV1 &) = delete;
  PlayerFactionAlertsMailboxContextV1 &operator=(
      const PlayerFactionAlertsMailboxContextV1 &) = delete;
  PlayerFactionAlertsMailboxContextV1(
      PlayerFactionAlertsMailboxContextV1 &&) = delete;
  PlayerFactionAlertsMailboxContextV1 &operator=(
      PlayerFactionAlertsMailboxContextV1 &&) = delete;
};

bool ExecutePlayerFactionAlertsMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

std::string_view PlayerFactionAlertsFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    PlayerFactionAlertsMailboxCompletionV1 completion,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecutePlayerFactionAlertsMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
