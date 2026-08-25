#pragma once

#include "xar_bridge/main_thread_query_mailbox_v1.hpp"
#include "xar_bridge/war_entry_assessments_v1.hpp"

#include <cstdint>
#include <type_traits>

namespace xar::ck3_11906 {

// Production is deliberately restricted to the typed war-entry callback. No
// generic effect, combat-phase or arbitrary native evaluator is reachable
// through this adapter.
inline constexpr bool
    kWarEntryAssessmentsV1MailboxAdapterProductionWired = true;

enum class WarEntryAssessmentMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  available = 1,
  query_unavailable = 2,
  infrastructure_rejected = 3,
};

// Caller-owned stable storage published through MainThreadQueryMailboxV1.
// Once TrySubmitMainThreadQueryV1 succeeds, this object must stay alive until
// the exact ticket is terminal *and* ReclaimMainThreadQueryV1 succeeds. In
// particular, timeout_executor_already_running does not permit destruction.
struct WarEntryAssessmentMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  WarEntryNativeEnvironmentV1 environment{};
  WarEntryAssessmentAccessV1 access{};
  WarEntryAssessmentsV1Request request{};

  WarEntryAssessmentMailboxCompletionV1 completion =
      WarEntryAssessmentMailboxCompletionV1::not_executed;
  game::ReadWarEntryAssessmentsV1Result read_result =
      game::ReadWarEntryAssessmentsV1Result::unavailable;
  game::WarEntryAssessmentsV1 result{};
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  WarEntryAssessmentMailboxContextV1() = default;
  WarEntryAssessmentMailboxContextV1(
      const WarEntryAssessmentMailboxContextV1 &) = delete;
  WarEntryAssessmentMailboxContextV1 &operator=(
      const WarEntryAssessmentMailboxContextV1 &) = delete;
  WarEntryAssessmentMailboxContextV1(
      WarEntryAssessmentMailboxContextV1 &&) = delete;
  WarEntryAssessmentMailboxContextV1 &operator=(
      WarEntryAssessmentMailboxContextV1 &&) = delete;
};

// Submit only as MainThreadQueryExecutorV1. The callback verifies that its
// exact context/ticket is the mailbox's currently executing slot, binds every
// frame capture to the mailbox date stamp, and then invokes the strict reader.
// A query-specific unavailable result returns true and remains structured in
// context.result.unavailable_stage. False is reserved for infrastructure or
// forged/direct-call rejection.
bool ExecuteWarEntryAssessmentMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteWarEntryAssessmentMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
