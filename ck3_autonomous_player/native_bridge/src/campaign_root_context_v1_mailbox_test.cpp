#include "xar_bridge/campaign_root_context_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>
#include <string_view>

namespace {

xar::game::Snapshot g_snapshot{};
bool g_reader_available = true;
std::uint32_t g_reader_calls = 0;

void PrimeMailbox(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::CampaignRootContextMailboxContextV1 &query,
    std::uint64_t sequence) {
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor =
      &xar::ck3_11906::ExecuteCampaignRootContextMailboxQueryV1;
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
  return ParseCampaignRootContextV1Step(
             "query-campaign-root-context-v1") &&
         !ParseCampaignRootContextV1Step(
             "query-campaign-root-context-v1-1") &&
         ParseCampaignRootContextExpectedRevisionV1(
             R"({"expected_revision":77})", revision) &&
         revision == 77 &&
         ParseCampaignRootContextExpectedRevisionV1(
             R"({"step":"query-campaign-root-context-v1", "expected_revision": 77, "x":1})",
             revision) &&
         revision == 77 &&
         !ParseCampaignRootContextExpectedRevisionV1(
             R"({"expected_revision":0})", revision) &&
         !ParseCampaignRootContextExpectedRevisionV1(
             R"({"expected_revision":077})", revision) &&
         !ParseCampaignRootContextExpectedRevisionV1(
             R"({"expected_revision":77,"expected_revision":78})",
             revision) &&
         !ParseCampaignRootContextExpectedRevisionV1("{}", revision);
}

bool TestDirectInvocationRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::CampaignRootContextMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.request.expected_snapshot_revision = 77;
  const auto stamp = Stamp();
  return !xar::ck3_11906::ExecuteCampaignRootContextMailboxQueryV1(
             &query, stamp) &&
         query.completion ==
             xar::ck3_11906::CampaignRootContextMailboxCompletionV1::
                 infrastructure_rejected &&
         g_reader_calls == 0;
}

bool TestTypedCompletion(bool available) {
  g_reader_available = available;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::CampaignRootContextMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, available ? 10 : 11);
  const auto stamp = Stamp();
  const auto calls_before = g_reader_calls;
  if (!xar::ck3_11906::ExecuteCampaignRootContextMailboxQueryV1(
          &query, stamp) ||
      g_reader_calls != calls_before + 1 || query.executor_invocations != 1 ||
      query.completion !=
          xar::ck3_11906::CampaignRootContextMailboxCompletionV1::completed ||
      query.result.snapshot_revision != 77 ||
      query.result.date_raw != g_snapshot.date_raw ||
      query.execution_stamp != stamp) {
    return false;
  }
  if (available) {
    return query.read_result ==
               xar::game::ReadCampaignRootContextResultV1::available &&
           query.result.status ==
               xar::game::CampaignRootContextStatusV1::available &&
           query.result.readiness.ready &&
           query.result.unavailable_reason.empty();
  }
  return query.read_result ==
             xar::game::ReadCampaignRootContextResultV1::unavailable &&
         query.result.status ==
             xar::game::CampaignRootContextStatusV1::unavailable &&
         !query.result.readiness.ready &&
         query.result.unavailable_reason == "unsupported_build";
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

game::ReadCampaignRootContextResultV1 ReadCampaignRootContextV1(
    const CampaignRootNativeEnvironmentV1 &,
    const CampaignRootAccessV1 &access,
    const CampaignRootContextRequestV1 &request,
    game::CampaignRootContextV1 &output) noexcept {
  ++g_reader_calls;
  game::CampaignRootFrameV1 frame{};
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, frame)) {
    return game::ReadCampaignRootContextResultV1::unavailable;
  }
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  output.date_raw = frame.date_raw;
  if (!g_reader_available) {
    output.status = game::CampaignRootContextStatusV1::unavailable;
    output.unavailable_reason = "unsupported_build";
    return game::ReadCampaignRootContextResultV1::unavailable;
  }
  output.status = game::CampaignRootContextStatusV1::available;
  output.local_player_id = 7;
  output.player_character_id = frame.played_character_id;
  output.player_character_alive = frame.played_character_alive;
  output.top_liege_character_id = frame.played_character_id;
  output.independent = true;
  output.readiness = {true, true, true, true, true, true, true, true};
  return game::ReadCampaignRootContextResultV1::available;
}

} // namespace xar::ck3_11906

int main() {
  g_snapshot.date_raw = 54'321;
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_id = 0x02000001;
  if (!TestParsing()) {
    std::cerr << "campaign-root mailbox parser fixture failed\n";
    return 1;
  }
  if (!TestDirectInvocationRejected()) {
    std::cerr << "campaign-root direct invocation fixture failed\n";
    return 1;
  }
  if (!TestTypedCompletion(true) || !TestTypedCompletion(false)) {
    std::cerr << "campaign-root typed completion fixture failed\n";
    return 1;
  }
  std::cout << "campaign-root-context-v1 mailbox fixture passed\n";
  return 0;
}
