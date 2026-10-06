#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/ck3_12002.hpp"
#include "xar_bridge/ck3_12003_adapter.hpp"
#include "xar_bridge/ck3_12004_adapter.hpp"

#include <atomic>
#include <string_view>

namespace xar::ck3_12002 {
namespace {

void RemoveArmyRoutes(game::Snapshot &snapshot) {
  const auto remove = [](game::ArmySnapshot &army) {
    army.route_province_ids.clear();
    army.move_target_province_id = -1;
  };
  for (auto &army : snapshot.player_armies) remove(army);
  for (auto &war : snapshot.active_wars) {
    for (auto &army : war.allied_armies) remove(army);
    for (auto &army : war.enemy_armies) remove(army);
  }
}

bool MatchesQuerySnapshot(const QueryMailboxEnvelope &query,
                          const game::Snapshot &observed,
                          bool finishing) noexcept {
  if (query.snapshot_comparison == QuerySnapshotComparison12002::core_frame) {
    const auto &expected = query.expected_snapshot;
    return observed.date_raw == expected.date_raw &&
           observed.speed == expected.speed &&
           observed.paused == expected.paused &&
           observed.player_id == expected.player_id &&
           observed.map_ready == expected.map_ready &&
           observed.has_played_character == expected.has_played_character &&
           observed.played_character_id == expected.played_character_id &&
           observed.played_character_alive == expected.played_character_alive;
  }
  if (finishing && query.snapshot_comparison ==
                       QuerySnapshotComparison12002::fixture_inbox_mutation) {
    const auto &expected = query.expected_snapshot;
    // The fixed fixture script applies effects immediately. Preserve the
    // paused player/date scope while accepting its intended world changes.
    return observed.paused == expected.paused &&
           observed.date_raw == expected.date_raw &&
           observed.player_id == expected.player_id &&
           observed.map_ready == expected.map_ready &&
           observed.has_played_character == expected.has_played_character &&
           observed.played_character_id == expected.played_character_id &&
           observed.played_character_alive == expected.played_character_alive;
  }
  if (query.snapshot_comparison !=
      QuerySnapshotComparison12002::war_termination_options)
    return observed == query.expected_snapshot;
  try {
    auto expected = query.expected_snapshot;
    auto current = observed;
    // Paused native pathfinding can finish after the published frame. These
    // two route fields do not belong to the war-termination options input.
    RemoveArmyRoutes(expected);
    RemoveArmyRoutes(current);
    return expected == current;
  } catch (...) { return false; }
}

bool OwnsSlot(const QueryMailboxEnvelope &query) noexcept {
  if (query.game == nullptr || query.mailbox == nullptr ||
      query.executor == nullptr || query.ticket.sequence == 0 ||
      query.expected_snapshot_revision == 0 || !query.entered ||
      !query.game->enabled() ||
      (!game::IsReviewedCrozierAdapter(*query.game) &&
       !game::IsCk3_12004Descriptor(query.game->descriptor())) ||
      GetCurrentThreadId() != query.execution_stamp.thread_id) {
    return false;
  }
  const auto &mailbox = *query.mailbox;
  return mailbox.state.load(std::memory_order_acquire) ==
             ck3_11906::MainThreadQueryMailboxStateV1::executing &&
         !mailbox.stop_requested.load(std::memory_order_acquire) &&
         mailbox.failure_flags.load(std::memory_order_acquire) == 0 &&
         mailbox.published_sequence.load(std::memory_order_acquire) ==
             query.ticket.sequence &&
         mailbox.owner_thread_id.load(std::memory_order_acquire) ==
             query.execution_stamp.thread_id &&
         mailbox.executor == query.executor &&
         mailbox.executor_context == &query;
}

bool ReadQuerySnapshot(const QueryMailboxEnvelope &query,
                       game::Snapshot &output) noexcept {
  if (query.snapshot_comparison == QuerySnapshotComparison12002::core_frame) {
    return game::IsCk3_12004Descriptor(query.game->descriptor()) &&
           game::ReadCk3_12002TimelineCoreSnapshot(*query.game, output);
  }
  return game::ReadSnapshot(*query.game, output);
}

void ReplaceIdentity(std::string &value, std::string_view from,
                     std::string_view to) {
  std::size_t at = 0;
  while ((at = value.find(from, at)) != std::string::npos) {
    value.replace(at, from.size(), to);
    at += to.size();
  }
}

} // namespace

bool EnterQueryMailbox(QueryMailboxEnvelope &query,
                       const ck3_11906::MainThreadExecutionStampV1 &stamp,
                       ck3_11906::MainThreadQueryExecutorV1 executor) noexcept {
  if (query.entered || executor == nullptr || stamp.pump_epoch == 0 ||
      stamp.thread_id == 0 || !stamp.paused || stamp.tls_initialized != 1 ||
      stamp.tls_main_thread_marker != 1 || stamp.tls_context == 0 ||
      stamp.jomini_state == 0 || stamp.game_state == 0) {
    return false;
  }
  query.execution_stamp = stamp;
  query.executor = executor;
  query.entered = true;
  game::Snapshot snapshot{};
  if (!CaptureQuerySnapshot(&query, snapshot)) {
    return false;
  }
  return true;
}

bool IsQueryOwningThread(void *opaque) noexcept {
  const auto *query = static_cast<const QueryMailboxEnvelope *>(opaque);
  return query != nullptr && OwnsSlot(*query);
}

bool CaptureQuerySnapshot(void *opaque, game::Snapshot &output) noexcept {
  const auto *query = static_cast<const QueryMailboxEnvelope *>(opaque);
  output = {};
  return query != nullptr && OwnsSlot(*query) &&
         ReadQuerySnapshot(*query, output) &&
         MatchesQuerySnapshot(*query, output, false) && output.paused &&
         output.date_raw == query->execution_stamp.date_raw;
}

bool FinishQueryMailbox(QueryMailboxEnvelope &query) noexcept {
  game::Snapshot snapshot{};
  query.frame_stable = OwnsSlot(query) &&
      ReadQuerySnapshot(query, snapshot) &&
      MatchesQuerySnapshot(query, snapshot, true) && snapshot.paused &&
      snapshot.date_raw == query.execution_stamp.date_raw;
  return query.frame_stable;
}

std::string RenderQueryBuildIdentity(std::string serialized) {
  ReplaceIdentity(serialized, "\"game_version\":\"1.19.0.6\"",
                  "\"game_version\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"exact_ck3_build\":\"1.19.0.6\"",
                  "\"exact_ck3_build\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"exact_build\":\"1.19.0.6\"",
                  "\"exact_build\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"version\":\"1.19.0.6\"",
                  "\"version\":\"1.20.0.2\"");
  ReplaceIdentity(serialized, "\"backend_id\":\"ck3-1.19.0.6-native-",
                  "\"backend_id\":\"ck3-1.20.0.2-native-");
  ReplaceIdentity(serialized,
                  "\"2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86\"",
                  "\"AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D\"");
  ReplaceIdentity(serialized,
                  "\"played-character-event-icon-indicators-1.19.0.6-v1\"",
                  "\"played-character-event-icon-indicators-1.20.0.2-v1\"");
  return serialized;
}

} // namespace xar::ck3_12002
