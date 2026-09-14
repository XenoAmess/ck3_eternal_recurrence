#include "xar_bridge/steward_develop_county_candidates_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>

namespace {

xar::game::Snapshot g_snapshot{};
bool g_reader_available = true;
std::uint32_t g_reader_calls = 0;

void PrimeMailbox(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::StewardDevelopCountyCandidatesMailboxContextV1 &query,
    std::uint64_t sequence) {
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor = &xar::ck3_11906::
      ExecuteStewardDevelopCountyCandidatesMailboxQueryV1;
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
  return ParseStewardDevelopCountyCandidatesV1Step(
             "query-steward-develop-county-candidates-v1") &&
         !ParseStewardDevelopCountyCandidatesV1Step(
             "query-steward-develop-county-candidates-v1-1") &&
         ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"expected_revision":77})", revision) &&
         revision == 77 &&
         ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"step":"query-steward-develop-county-candidates-v1", "expected_revision": 77, "x":1})",
             revision) &&
         revision == 77 &&
         !ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"expected_revision":0})", revision) &&
         !ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"expected_revision":077})", revision) &&
         !ParseStewardDevelopCountyCandidatesExpectedRevisionV1(
             R"({"expected_revision":77,"expected_revision":78})",
             revision) &&
         !ParseStewardDevelopCountyCandidatesExpectedRevisionV1("{}",
                                                                 revision);
}

bool TestDirectInvocationRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::StewardDevelopCountyCandidatesMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.request.expected_snapshot_revision = 77;
  const auto stamp = Stamp();
  return !xar::ck3_11906::
              ExecuteStewardDevelopCountyCandidatesMailboxQueryV1(
                  &query, stamp) &&
         query.completion ==
             xar::ck3_11906::
                 StewardDevelopCountyCandidatesMailboxCompletionV1::
                     infrastructure_rejected &&
         g_reader_calls == 0;
}

bool TestTypedCompletion(bool available) {
  g_reader_available = available;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::StewardDevelopCountyCandidatesMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, available ? 10 : 11);
  const auto stamp = Stamp();
  const auto calls_before = g_reader_calls;
  if (!xar::ck3_11906::
           ExecuteStewardDevelopCountyCandidatesMailboxQueryV1(&query,
                                                                stamp) ||
      g_reader_calls != calls_before + 1 || query.executor_invocations != 1 ||
      query.completion !=
          xar::ck3_11906::
              StewardDevelopCountyCandidatesMailboxCompletionV1::completed ||
      query.result.snapshot_revision != 77 ||
      (available && query.result.observed_date_raw != g_snapshot.date_raw) ||
      (!available && query.result.observed_date_raw.has_value()) ||
      query.execution_stamp != stamp) {
    return false;
  }
  if (available) {
    return query.read_result ==
               xar::game::ReadStewardDevelopCountyCandidatesResultV1::
                   available &&
           query.result.status ==
               xar::game::StewardDevelopCountyCandidatesStatusV1::available &&
           query.result.player_character_id == 0x02000001 &&
           query.result.steward_character_id == 0x02000002 &&
           query.result.same_frame_stable && query.result.readiness.ready &&
           query.result.unavailable_reason ==
               xar::game::StewardDevelopCountyFailureReasonV1::none;
  }
  return query.read_result ==
             xar::game::ReadStewardDevelopCountyCandidatesResultV1::
                 unavailable &&
         query.result.status ==
             xar::game::StewardDevelopCountyCandidatesStatusV1::unavailable &&
         !query.result.same_frame_stable && !query.result.readiness.ready &&
         query.result.unavailable_reason ==
             xar::game::StewardDevelopCountyFailureReasonV1::
                 native_reader_not_frozen;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

game::ReadStewardDevelopCountyCandidatesResultV1
ReadStewardDevelopCountyCandidatesV1(
    const StewardDevelopCountyCandidatesNativeEnvironmentV1 &,
    const StewardDevelopCountyCandidatesAccessV1 &access,
    const StewardDevelopCountyCandidatesRequestV1 &request,
    game::StewardDevelopCountyCandidatesV1 &output) noexcept {
  ++g_reader_calls;
  game::StewardDevelopCountyCandidatesFrameV1 frame{};
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, frame)) {
    return game::ReadStewardDevelopCountyCandidatesResultV1::unavailable;
  }
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  if (!g_reader_available) {
    output.status = game::StewardDevelopCountyCandidatesStatusV1::unavailable;
    output.unavailable_reason =
        game::StewardDevelopCountyFailureReasonV1::native_reader_not_frozen;
    return game::ReadStewardDevelopCountyCandidatesResultV1::unavailable;
  }
  output.status = game::StewardDevelopCountyCandidatesStatusV1::available;
  output.observed_date_raw = frame.date_raw;
  output.player_character_id = 0x02000001;
  output.steward_character_id = 0x02000002;
  output.shown = true;
  output.valid = true;
  output.steward_increase_development_value_raw = 5'000'000;
  output.current_gold_raw = 8'000'000;
  output.no_ai_increase_development = false;
  output.has_active_improve_development_directive = true;
  output.same_frame_stable = true;
  output.readiness.ready = true;
  return game::ReadStewardDevelopCountyCandidatesResultV1::available;
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
    std::cerr << "steward develop-county mailbox parser fixture failed\n";
    return 1;
  }
  if (!TestDirectInvocationRejected()) {
    std::cerr << "steward develop-county direct invocation fixture failed\n";
    return 1;
  }
  if (!TestTypedCompletion(true) || !TestTypedCompletion(false)) {
    std::cerr << "steward develop-county typed completion fixture failed\n";
    return 1;
  }
  std::cout << "steward-develop-county-candidates-v1 mailbox fixture passed\n";
  return 0;
}
