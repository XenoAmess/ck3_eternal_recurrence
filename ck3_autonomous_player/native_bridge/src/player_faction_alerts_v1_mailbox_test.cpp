#include "xar_bridge/player_faction_alerts_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>

namespace {

xar::game::Snapshot g_snapshot{};
bool g_reader_available = true;
std::uint32_t g_reader_calls = 0;

void PrimeMailbox(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::PlayerFactionAlertsMailboxContextV1 &query,
    std::uint64_t sequence) {
  mailbox.state.store(xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor =
      &xar::ck3_11906::ExecutePlayerFactionAlertsMailboxQueryV1;
  mailbox.executor_context = &query;
  query.mailbox = &mailbox;
  query.ticket.sequence = sequence;
  query.request.expected_snapshot_revision = 77;
  query.expected_snapshot = g_snapshot;
}

xar::ck3_11906::MainThreadExecutionStampV1 Stamp() {
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = 9;
  stamp.thread_id = GetCurrentThreadId();
  stamp.paused = true;
  stamp.date_raw = g_snapshot.date_raw;
  stamp.tls_initialized_flag_address = 0x1000;
  stamp.tls_initialized = 1;
  stamp.tls_context = 0x2000;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 0x3000;
  stamp.game_state = 0x4000;
  return stamp;
}

bool TestParsing() {
  using namespace xar::ck3_11906;
  std::uint64_t revision = 0;
  return ParsePlayerFactionAlertsV1Step("query-player-faction-alerts-v1") &&
         !ParsePlayerFactionAlertsV1Step("query-player-faction-alerts-v1-x") &&
         ParsePlayerFactionAlertsExpectedRevisionV1(
             R"({"expected_revision":77})", revision) && revision == 77 &&
         !ParsePlayerFactionAlertsExpectedRevisionV1(
             R"({"expected_revision":0})", revision) &&
         !ParsePlayerFactionAlertsExpectedRevisionV1(
             R"({"expected_revision":077})", revision) &&
         !ParsePlayerFactionAlertsExpectedRevisionV1(
             R"({"expected_revision":77,"expected_revision":78})",
             revision);
}

bool TestDirectInvocationRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::PlayerFactionAlertsMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.request.expected_snapshot_revision = 77;
  return !xar::ck3_11906::ExecutePlayerFactionAlertsMailboxQueryV1(
             &query, Stamp()) &&
         query.completion ==
             xar::ck3_11906::PlayerFactionAlertsMailboxCompletionV1::
                 infrastructure_rejected;
}

bool TestTypedCompletion(bool available) {
  g_reader_available = available;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::PlayerFactionAlertsMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, available ? 10 : 11);
  const auto calls_before = g_reader_calls;
  const auto stamp = Stamp();
  if (!xar::ck3_11906::ExecutePlayerFactionAlertsMailboxQueryV1(
          &query, stamp) ||
      g_reader_calls != calls_before + 1 || query.executor_invocations != 1 ||
      query.completion !=
          xar::ck3_11906::PlayerFactionAlertsMailboxCompletionV1::completed ||
      query.result.snapshot_revision != 77 ||
      query.result.date_raw != g_snapshot.date_raw ||
      query.execution_stamp != stamp) {
    return false;
  }
  if (available) {
    return query.read_result ==
               xar::game::ReadPlayerFactionAlertsResultV1::available &&
           query.result.status ==
               xar::game::PlayerFactionAlertsStatusV1::available &&
           query.result.targeting_faction_count == 2 &&
           query.result.readiness.targeting_count_ready &&
           query.result.readiness.same_frame_ready &&
           !query.result.readiness.alert_ready;
  }
  return query.read_result ==
             xar::game::ReadPlayerFactionAlertsResultV1::unavailable &&
         query.result.status ==
             xar::game::PlayerFactionAlertsStatusV1::unavailable &&
         query.result.unavailable_reason ==
             xar::game::PlayerFactionAlertsFailureReasonV1::
                 native_reader_not_frozen;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

bool ReadCampaignRootTargetingFactionCountV1(
    const CampaignRootNativeEnvironmentV1 &, const CampaignRootAccessV1 &,
    std::int32_t, std::int32_t &output) noexcept {
  output = 2;
  return true;
}

game::ReadPlayerFactionAlertsResultV1 ReadPlayerFactionAlertsV1(
    const PlayerFactionAlertsNativeEnvironmentV1 &,
    const PlayerFactionAlertsAccessV1 &access,
    const PlayerFactionAlertsRequestV1 &request,
    game::PlayerFactionAlertsV1 &output) noexcept {
  ++g_reader_calls;
  game::PlayerFactionAlertsFrameV1 frame{};
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, frame)) {
    return game::ReadPlayerFactionAlertsResultV1::unavailable;
  }
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  output.date_raw = frame.date_raw;
  if (!g_reader_available) {
    output.unavailable_reason =
        game::PlayerFactionAlertsFailureReasonV1::native_reader_not_frozen;
    return game::ReadPlayerFactionAlertsResultV1::unavailable;
  }
  output.status = game::PlayerFactionAlertsStatusV1::available;
  output.player_character_id = frame.played_character_id;
  output.targeting_faction_count = 2;
  output.readiness = {true, true, false, false, false, true, false, false};
  output.component_unavailable_reasons.targeting_rows =
      kPlayerFactionAlertsV1TargetingRowsUnavailableReason;
  output.component_unavailable_reasons.county_exposure =
      kPlayerFactionAlertsV1CountyExposureUnavailableReason;
  return game::ReadPlayerFactionAlertsResultV1::available;
}

} // namespace xar::ck3_11906

int main() {
  g_snapshot.date_raw = 54'321;
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_id = 0x02000001;
  if (!TestParsing() || !TestDirectInvocationRejected() ||
      !TestTypedCompletion(true) || !TestTypedCompletion(false)) {
    std::cerr << "player-faction-alerts-v1 mailbox fixture failed\n";
    return 1;
  }
  std::cout << "player-faction-alerts-v1 mailbox fixture passed\n";
  return 0;
}
