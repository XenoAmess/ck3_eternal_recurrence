#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <cstdint>
#include <string_view>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr std::string_view kRouteContactHorizonV1StepPrefix =
    "query-route-contact-horizon-v1-";
inline constexpr std::size_t kRouteContactHorizonV1MaximumHostiles = 64;

// A paused CK3 map can enter the verified application-main pump much less
// frequently than the worker polls the pipe.  Keep one queued ticket published
// across that low-frequency window instead of cancelling it after the generic
// two-second slice.  The bridge client's ten-second command deadline leaves a
// bounded margin for completion validation and serialization.
inline constexpr std::uint32_t
    kRouteContactHorizonV1QueuedWaitBudgetMilliseconds = 8'000;
inline constexpr std::uint32_t
    kRouteContactHorizonV1ExecutingWaitSliceMilliseconds = 2'000;

bool ParseRouteContactHorizonV1Step(
    std::string_view step,
    game::RouteContactHorizonRequest &output) noexcept;

// Strict command-envelope gate used before any snapshot/native read.  The
// revision is an unquoted canonical positive uint64 JSON number.
bool ParseRouteContactExpectedRevisionV1(
    std::string_view json, std::uint64_t &output) noexcept;

// Bridge-side preflight.  The caller-provided list is accepted only when it
// is the canonical exact union of every non-retreating enemy army across the
// paused snapshot's active wars and the subject is player-controllable.
bool RouteContactHostileScopeMatchesSnapshotV1(
    const game::Snapshot &snapshot,
    const game::RouteContactHorizonRequest &request);

enum class RouteContactHorizonMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  available = 1,
  query_unavailable = 2,
  infrastructure_rejected = 3,
};

// Caller-owned stable storage.  The Bindings value contains only exact-build
// function/global addresses and remains owned by this typed request until the
// mailbox ticket reaches a terminal state and is reclaimed.
struct RouteContactHorizonMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  game::RouteContactHorizonRequest request{};

  RouteContactHorizonMailboxCompletionV1 completion =
      RouteContactHorizonMailboxCompletionV1::not_executed;
  game::RouteContactHorizonSnapshot result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  RouteContactHorizonMailboxContextV1() = default;
  RouteContactHorizonMailboxContextV1(
      const RouteContactHorizonMailboxContextV1 &) = delete;
  RouteContactHorizonMailboxContextV1 &operator=(
      const RouteContactHorizonMailboxContextV1 &) = delete;
  RouteContactHorizonMailboxContextV1(
      RouteContactHorizonMailboxContextV1 &&) = delete;
  RouteContactHorizonMailboxContextV1 &operator=(
      RouteContactHorizonMailboxContextV1 &&) = delete;
};

bool ExecuteRouteContactHorizonMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

// Produces a stable command-error detail without changing the wire schema.
// The worker passes the mailbox wait terminal, the typed executor completion,
// and the reader status so a live failure cannot collapse back to a generic
// "query failed" result.  completion_snapshot_stable is meaningful only for
// the otherwise-successful completed/available/available path.
std::string_view RouteContactHorizonFailureMessageV1(
    MainThreadQueryWaitResultV1 wait,
    RouteContactHorizonMailboxCompletionV1 completion,
    game::RouteContactHorizonStatus status,
    bool completion_snapshot_stable) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteRouteContactHorizonMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
