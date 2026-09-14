#pragma once

#include "xar_bridge/ck3_11906.hpp"
#include "xar_bridge/culture_innovation_snapshot_v1.hpp"
#include "xar_bridge/culture_innovation_source_adapter_v1.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <type_traits>

namespace xar::ck3_11906 {

inline constexpr bool kCultureInnovationAsyncPrivateProbeEnabledByDefaultV1 =
    false;

enum class CultureInnovationMailboxCompletionV1 : std::uint32_t {
  not_executed = 0,
  terminal_available = 1,
  terminal_unavailable = 2,
  infrastructure_rejected = 3,
};

enum class CultureInnovationAsyncStateV1 : std::uint32_t {
  waiting_snapshot = 0,
  queued = 1,
  executing = 2,
  terminal_available = 3,
  terminal_unavailable = 4,
  infrastructure_failed = 5,
};

enum class CultureInnovationAsyncFailureV1 : std::uint32_t {
  none = 0,
  bindings_unavailable = 1,
  request_preparation_failed = 2,
  submission_rejected = 3,
  mailbox_executor_failed = 4,
  mailbox_infrastructure_failed = 5,
  mailbox_cancelled = 6,
  mailbox_ticket_mismatch = 7,
  mailbox_reclaim_failed = 8,
};

using ReadCultureInnovationMailboxSnapshotV1 = bool (*)(
    void *context, game::Snapshot &output) noexcept;
using ResolveCultureInnovationMailboxPlayerV1 = bool (*)(
    void *context, std::int32_t player_character_id,
    std::uintptr_t &played_character) noexcept;

// Caller-owned stable storage. Neither a native pointer nor a partial result
// crosses the mailbox boundary. Only terminal_result is eligible for worker
// thread publication after the generic mailbox reaches a terminal state.
struct CultureInnovationMailboxContextV1 {
  MainThreadQueryMailboxV1 *mailbox = nullptr;
  MainThreadQueryTicketV1 ticket{};
  Bindings bindings{};
  CultureInnovationSnapshotEnvironmentV1 environment{};
  CultureInnovationSourceAdapterContextV1 source{};
  CultureInnovationSnapshotRequestV1 request{};
  game::Snapshot expected_snapshot{};
  std::array<char, game::kCultureInnovationSnapshotIdCapacityV1>
      expected_snapshot_id{};

  void *snapshot_context = nullptr;
  ReadCultureInnovationMailboxSnapshotV1 read_snapshot = nullptr;
  ResolveCultureInnovationMailboxPlayerV1 resolve_player = nullptr;
  ReadCultureInnovationNativeSourceV1 read_source = nullptr;

  CultureInnovationMailboxCompletionV1 completion =
      CultureInnovationMailboxCompletionV1::not_executed;
  game::ReadCultureInnovationSnapshotResultV1 read_result =
      game::ReadCultureInnovationSnapshotResultV1::unavailable;
  game::CultureInnovationSnapshotV1 execution_result{};
  CultureInnovationSourceAdapterFailureV1 source_failure =
      CultureInnovationSourceAdapterFailureV1::none;
  MainThreadExecutionStampV1 execution_stamp{};
  std::uint32_t executor_invocations = 0;

  CultureInnovationMailboxContextV1() = default;
  CultureInnovationMailboxContextV1(
      const CultureInnovationMailboxContextV1 &) = delete;
  CultureInnovationMailboxContextV1 &operator=(
      const CultureInnovationMailboxContextV1 &) = delete;
};

struct CultureInnovationAsyncPrivateProbeV1 {
  CultureInnovationMailboxContextV1 query{};
  CultureInnovationAsyncStateV1 state =
      CultureInnovationAsyncStateV1::waiting_snapshot;
  CultureInnovationAsyncFailureV1 async_failure =
      CultureInnovationAsyncFailureV1::none;
  bool query_in_flight = false;
  bool terminal_published = false;
  game::CultureInnovationSnapshotV1 terminal_result{};
  CultureInnovationSourceAdapterFailureV1 terminal_source_failure =
      CultureInnovationSourceAdapterFailureV1::none;
  std::uint32_t last_submit_result = 0;
  std::uint32_t last_wait_result = 0;
  std::uint32_t last_reclaim_result = 0;
};

bool PrepareCultureInnovationMailboxQueryV1(
    CultureInnovationMailboxContextV1 &query, const Bindings &bindings,
    std::uintptr_t module_base, const game::Snapshot &snapshot,
    std::uint64_t public_revision,
    std::uint64_t native_revision) noexcept;

bool ExecuteCultureInnovationMailboxQueryV1(
    void *opaque_context,
    const MainThreadExecutionStampV1 &stamp) noexcept;

// Called by the bridge worker heartbeat. It never blocks: submission,
// execution on the application main thread, and terminal publication occur in
// separate heartbeats/pump epochs.
void DriveCultureInnovationAsyncPrivateProbeV1(
    CultureInnovationAsyncPrivateProbeV1 &probe,
    MainThreadQueryMailboxV1 &mailbox, const Bindings &bindings,
    std::uintptr_t module_base, const game::Snapshot *snapshot,
    std::uint64_t public_revision,
    std::uint64_t native_revision) noexcept;

std::string SerializeCultureInnovationAsyncPrivateProbeV1(
    const CultureInnovationAsyncPrivateProbeV1 &probe);

std::string_view CultureInnovationAsyncStateKeyV1(
    CultureInnovationAsyncStateV1 state) noexcept;
std::string_view CultureInnovationAsyncFailureKeyV1(
    CultureInnovationAsyncFailureV1 failure) noexcept;

static_assert(
    std::is_same_v<decltype(&ExecuteCultureInnovationMailboxQueryV1),
                   MainThreadQueryExecutorV1>);

} // namespace xar::ck3_11906
