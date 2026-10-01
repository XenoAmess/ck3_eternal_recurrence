#pragma once

#include "xar_bridge/game_adapter.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <string>

namespace xar::ck3_12002 {

enum class QuerySnapshotComparison12002 {
  full_snapshot,
  war_termination_options,
  fixture_inbox_mutation,
};

// The semantic snapshot is captured with the selected adapter; this envelope
// never carries a legacy native Bindings object into the new executable.
struct QueryMailboxEnvelope {
  const game::GameAdapter *game = nullptr;
  ck3_11906::MainThreadQueryMailboxV1 *mailbox = nullptr;
  ck3_11906::MainThreadQueryTicketV1 ticket{};
  game::Snapshot expected_snapshot{};
  std::uint64_t expected_snapshot_revision = 0;
  ck3_11906::MainThreadExecutionStampV1 execution_stamp{};
  ck3_11906::MainThreadQueryExecutorV1 executor = nullptr;
  void *typed_context = nullptr;
  bool entered = false;
  bool frame_stable = false;
  QuerySnapshotComparison12002 snapshot_comparison =
      QuerySnapshotComparison12002::full_snapshot;
};

bool EnterQueryMailbox(QueryMailboxEnvelope &query,
                       const ck3_11906::MainThreadExecutionStampV1 &stamp,
                       ck3_11906::MainThreadQueryExecutorV1 executor) noexcept;
bool IsQueryOwningThread(void *opaque) noexcept;
bool CaptureQuerySnapshot(void *opaque, game::Snapshot &output) noexcept;
bool FinishQueryMailbox(QueryMailboxEnvelope &query) noexcept;

// Legacy serializers contain build provenance rather than native reads. The
// new adapter renders those fixed JSON identity fields for its selected build.
// Escaped user strings and all semantic data remain byte-for-byte unchanged.
std::string RenderQueryBuildIdentity(std::string serialized);

} // namespace xar::ck3_12002
