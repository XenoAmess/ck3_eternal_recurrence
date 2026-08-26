#include "xar_bridge/battle_transition_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>
#include <string_view>

namespace {

xar::game::Snapshot g_outer_snapshot{};
xar::game::BattleTransitionSnapshot g_native_result{};
xar::game::BattleTransitionSnapshotStatus g_native_status =
    xar::game::BattleTransitionSnapshotStatus::available;
std::uint32_t g_snapshot_reads = 0;
std::uint32_t g_transition_reads = 0;

int Fail(std::string_view message) {
  std::cerr << message << '\n';
  return 1;
}

bool Contains(std::string_view text, std::string_view needle) {
  return text.find(needle) != std::string_view::npos;
}

xar::game::Snapshot CompleteOuterSnapshot() {
  xar::game::Snapshot result{};
  result.map_ready = true;
  result.paused = true;
  result.date_raw = 53'178'624;
  result.has_played_character = true;
  result.played_character_alive = true;
  result.played_character_id = 29'829;
  xar::game::ArmySnapshot retreating{};
  retreating.army_id = 83'886'341;
  retreating.owner_character_id = 29'829;
  retreating.has_current_province = true;
  retreating.current_province_id = 2'586;
  retreating.in_combat = true;
  retreating.retreating = true;
  retreating.controllable = true;
  result.player_armies.push_back(retreating);
  return result;
}

xar::game::BattleTransitionSnapshot CompleteTransition() {
  xar::game::BattleTransitionSnapshot result{};
  result.status = xar::game::BattleTransitionSnapshotStatus::available;
  result.snapshot_revision = 49;
  result.observed_date_raw = 53'178'624;
  result.combat_id = 335'544'325;
  result.province_id = 2'586;
  result.phase = "pursuit";
  result.phase_raw = 2;
  result.phase_day = 0;
  result.winner_side = "defender";
  result.winner_raw = 1;
  result.forced_winner_side = "none";
  result.forced_winner_raw = -1;
  result.finalized = false;
  result.battle_result_id = 553'648'135;
  result.attacker_public_cunit_ids_in_stored_order = {83'886'341};
  result.defender_public_cunit_ids_in_stored_order = {357, 358};
  result.battle_transition_ready = true;
  return result;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  ++g_snapshot_reads;
  output = g_outer_snapshot;
  return true;
}

game::BattleTransitionSnapshotStatus ReadBattleTransitionSnapshot(
    const Bindings &, const game::BattleTransitionRequest &,
    game::BattleTransitionSnapshot &output) noexcept {
  ++g_transition_reads;
  output = g_native_result;
  return g_native_status;
}

} // namespace xar::ck3_11906

int main() {
  using namespace xar;
  using namespace xar::ck3_11906;

  game::BattleTransitionRequest request{};
  if (!ParseBattleTransitionV1Step(
          "query-battle-transition-v1-335544325", request) ||
      request.combat_id != 335'544'325 ||
      ParseBattleTransitionV1Step(
          "query-battle-transition-v1-0335544325", request) ||
      ParseBattleTransitionV1Step(
          "query-battle-transition-v1-335544325-extra", request) ||
      ParseBattleTransitionV1Step(
          "query-battle-transition-v1-2147483648", request)) {
    return Fail("battle-transition canonical step parser failed");
  }
  std::uint64_t revision = 0;
  if (!ParseBattleTransitionExpectedRevisionV1(
          "{\"expected_revision\":49}", revision) ||
      revision != 49 ||
      ParseBattleTransitionExpectedRevisionV1(
          "{\"expected_revision\":049}", revision) ||
      ParseBattleTransitionExpectedRevisionV1(
          "{\"expected_revision\":49,\"expected_revision\":50}",
          revision)) {
    return Fail("battle-transition expected revision parser failed");
  }

  const auto complete = CompleteTransition();
  const auto json = SerializeBattleTransitionV1(complete);
  if (json.empty() ||
      !Contains(json, "\"status\":\"available\"") ||
      !Contains(json, "\"combat_id\":335544325") ||
      !Contains(json, "\"phase\":\"pursuit\"") ||
      !Contains(json, "\"winner_side\":\"defender\"") ||
      !Contains(json, "\"battle_result_id\":553648135") ||
      !Contains(json,
                "\"attacker_public_cunit_ids_in_stored_order\":[83886341]") ||
      !Contains(json,
                "\"defender_public_cunit_ids_in_stored_order\":[357,358]")) {
    return Fail("battle-transition available serializer lost lifecycle fields");
  }
  auto missing = game::BattleTransitionSnapshot{};
  missing.status =
      game::BattleTransitionSnapshotStatus::combat_not_found;
  missing.snapshot_revision = 50;
  missing.observed_date_raw = 53'178'648;
  missing.combat_id = 335'544'325;
  missing.battle_transition_ready = true;
  const auto missing_json = SerializeBattleTransitionV1(missing);
  if (missing_json.empty() ||
      !Contains(missing_json, "\"status\":\"combat_not_found\"") ||
      !Contains(missing_json, "\"province_id\":null") ||
      !Contains(missing_json, "\"finalized\":null") ||
      !Contains(missing_json,
                "\"attacker_public_cunit_ids_in_stored_order\":[]")) {
    return Fail("battle-transition missing-combat discriminant was lost");
  }
  auto changed = missing;
  changed.status = game::BattleTransitionSnapshotStatus::state_changed;
  changed.battle_transition_ready = false;
  if (SerializeBattleTransitionV1(changed).empty()) {
    return Fail("battle-transition state_changed was not serializable");
  }
  auto unavailable = changed;
  unavailable.status = game::BattleTransitionSnapshotStatus::unavailable;
  if (SerializeBattleTransitionV1(unavailable).empty()) {
    return Fail("battle-transition unavailable was not serializable");
  }
  auto invalid = complete;
  invalid.defender_public_cunit_ids_in_stored_order.push_back(83'886'341);
  if (!SerializeBattleTransitionV1(invalid).empty()) {
    return Fail("battle-transition admitted a CUnit on both sides");
  }

  g_outer_snapshot = CompleteOuterSnapshot();
  g_native_result = complete;
  g_native_result.snapshot_revision = 0;
  g_native_status = game::BattleTransitionSnapshotStatus::available;
  g_snapshot_reads = 0;
  g_transition_reads = 0;

  MainThreadQueryMailboxV1 mailbox{};
  BattleTransitionMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 17;
  query.request.combat_id = 335'544'325;
  query.expected_snapshot_revision = 49;
  query.expected_snapshot = g_outer_snapshot;
  mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(query.ticket.sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor = &ExecuteBattleTransitionMailboxQueryV1;
  mailbox.executor_context = &query;

  MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 3;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = 1;
  stamp.tls_initialized = 1;
  stamp.tls_context = 2;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 3;
  stamp.game_state = 4;
  stamp.date_raw = g_outer_snapshot.date_raw;
  stamp.paused = true;
  if (!ExecuteBattleTransitionMailboxQueryV1(&query, stamp) ||
      query.completion != BattleTransitionMailboxCompletionV1::completed ||
      query.executor_invocations != 1 || g_snapshot_reads != 2 ||
      g_transition_reads != 1 || query.result.snapshot_revision != 49 ||
      query.result.combat_id != 335'544'325 ||
      SerializeBattleTransitionV1(query.result).empty()) {
    return Fail("battle-transition application-main executor contract failed");
  }

  std::cout << "battle_transition_v1_mailbox_test: ok\n";
  return 0;
}
