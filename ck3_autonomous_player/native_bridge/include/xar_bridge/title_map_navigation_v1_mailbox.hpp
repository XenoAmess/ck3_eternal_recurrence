#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/title_map_navigation_v1_camera.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::uint32_t
    kTitleMapNavigationV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kTitleMapNavigationV1ExecutingWaitSliceMilliseconds = 2'000;
inline constexpr std::uint32_t
    kTitleMapNavigationV1TotalSettleBudgetMilliseconds = 15'000;
inline constexpr std::uint32_t
    kTitleMapNavigationV1MaximumApplicationMainCallbacks = 600;

bool ParseTitleMapNavigationV1Step(std::string_view step) noexcept;
bool ParseTitleMapNavigationRequestV1(
    std::string_view json, TitleMapNavigationRequestV1 &output) noexcept;

enum class TitleMapNavigationMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  advanced = 1,
  infrastructure_rejected = 2,
};

enum class TitleMapNavigationMailboxRunResultV1 : std::uint32_t {
  terminal = 0,
  submission_rejected = 1,
  wait_failed = 2,
  reclaim_failed = 3,
  settle_budget_exhausted = 4,
};

struct TitleMapNavigationMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  TitleMapNavigationNativeEnvironmentV1 title_environment{};
  TitleMapNavigationCameraEnvironmentV1 camera_environment{};
  TitleMapNavigationCameraAccessV1 access{};
  game::Snapshot expected_snapshot{};
  game::TitleMapNavigationCommandV1 command{};

  TitleMapNavigationMailboxCompletionV1 completion =
      TitleMapNavigationMailboxCompletionV1::not_executed;
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint64_t last_ticket_sequence = 0;
  std::uint64_t dispatch_ticket_sequence = 0;
  std::uint64_t dispatch_pump_epoch = 0;
  std::uint64_t last_pump_epoch = 0;
  std::uint32_t callback_count = 0;
  std::uint32_t poll_count = 0;

  TitleMapNavigationMailboxContextV1() = default;
  TitleMapNavigationMailboxContextV1(
      const TitleMapNavigationMailboxContextV1 &) = delete;
  TitleMapNavigationMailboxContextV1 &operator=(
      const TitleMapNavigationMailboxContextV1 &) = delete;
  TitleMapNavigationMailboxContextV1(
      TitleMapNavigationMailboxContextV1 &&) = delete;
  TitleMapNavigationMailboxContextV1 &operator=(
      TitleMapNavigationMailboxContextV1 &&) = delete;
};

bool ExecuteTitleMapNavigationMailboxV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

// Worker-thread orchestration.  Each pending result is reclaimed before a
// fresh ticket is submitted.  The owning-thread executor never waits or spins.
TitleMapNavigationMailboxRunResultV1 RunTitleMapNavigationMailboxV1(
    TitleMapNavigationMailboxContextV1 &query,
    std::uint32_t total_budget_milliseconds =
        kTitleMapNavigationV1TotalSettleBudgetMilliseconds,
    std::uint32_t maximum_callbacks =
        kTitleMapNavigationV1MaximumApplicationMainCallbacks) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteTitleMapNavigationMailboxV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
