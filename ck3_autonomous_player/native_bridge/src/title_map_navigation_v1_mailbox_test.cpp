#include "xar_bridge/title_map_navigation_v1_mailbox.hpp"

#include <windows.h>

#include <array>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string_view>
#include <thread>

namespace {

void TestAssert(bool condition, const char *expression, int line) noexcept {
  if (condition) {
    return;
  }
  std::fprintf(stderr, "test assertion failed at line %d: %s\n", line,
               expression);
  std::fflush(stderr);
  std::_Exit(3);
}

#undef assert
#define assert(expression) TestAssert((expression), #expression, __LINE__)

xar::game::Snapshot g_snapshot{};
std::atomic<std::uint32_t> g_advance_calls{0};

xar::ck3_11906::MainThreadExecutionStampV1 Stamp(
    std::uint64_t pump_epoch) {
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.pump_epoch = pump_epoch;
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

void PrimeExecuting(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::TitleMapNavigationMailboxContextV1 &query,
    std::uint64_t sequence, std::uint64_t pump_epoch) {
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor =
      &xar::ck3_11906::ExecuteTitleMapNavigationMailboxV1;
  mailbox.executor_context = &query;
  query.mailbox = &mailbox;
  query.ticket.sequence = sequence;
  query.command.request.expected_snapshot_revision = 17;
  query.command.request.title_key = "c_bianzhou";
  query.expected_snapshot = g_snapshot;
  query.completion =
      xar::ck3_11906::TitleMapNavigationMailboxCompletionV1::not_executed;
  query.last_pump_epoch = pump_epoch == 0 ? 0 : pump_epoch - 1;
}

bool TestParsing() {
  using namespace xar::ck3_11906;
  TitleMapNavigationRequestV1 request{};
  return ParseTitleMapNavigationV1Step("center-map-on-landed-title-v1") &&
         !ParseTitleMapNavigationV1Step(
             "center-map-on-landed-title-v1-c_bianzhou") &&
         ParseTitleMapNavigationRequestV1(
             R"({"expected_revision":17,"title_key":"c_bianzhou"})",
             request) &&
         request.expected_snapshot_revision == 17 &&
         request.title_key == "c_bianzhou" &&
         ParseTitleMapNavigationRequestV1(
             R"({"title_key":"b_kaifeng","expected_revision":0})",
             request) &&
         request.expected_snapshot_revision == 0 &&
         request.title_key == "b_kaifeng" &&
         !ParseTitleMapNavigationRequestV1(
             R"({"expected_revision":017,"title_key":"c_bianzhou"})",
             request) &&
         !ParseTitleMapNavigationRequestV1(
             R"({"expected_revision":17,"expected_revision":18,"title_key":"c_bianzhou"})",
             request) &&
         !ParseTitleMapNavigationRequestV1(
             R"({"expected_revision":17,"title_key":"汴州"})", request) &&
         !ParseTitleMapNavigationRequestV1(
             R"({"expected_revision":17,"title_key":"c_bian\u007ahou"})",
             request) &&
         !ParseTitleMapNavigationRequestV1(
             R"({"expected_revision":17,"title_key":"c_bianzhou","title_key":"b_kaifeng"})",
             request);
}

bool TestDirectAndSamePumpRejection() {
  using Completion =
      xar::ck3_11906::TitleMapNavigationMailboxCompletionV1;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::TitleMapNavigationMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.command.request.expected_snapshot_revision = 17;
  const auto direct_stamp = Stamp(10);
  if (xar::ck3_11906::ExecuteTitleMapNavigationMailboxV1(&query,
                                                         direct_stamp) ||
      query.completion != Completion::infrastructure_rejected) {
    return false;
  }

  // Context is deliberately non-assignable; same-pump rejection uses a
  // separate object below.
  return true;
}

bool TestSamePumpPollRejected() {
  using Completion =
      xar::ck3_11906::TitleMapNavigationMailboxCompletionV1;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::TitleMapNavigationMailboxContextV1 query{};
  PrimeExecuting(mailbox, query, 10, 10);
  query.last_pump_epoch = 10;
  query.last_ticket_sequence = 9;
  const auto same_stamp = Stamp(10);
  return !xar::ck3_11906::ExecuteTitleMapNavigationMailboxV1(&query,
                                                             same_stamp) &&
         query.completion == Completion::infrastructure_rejected &&
         query.command.status ==
             xar::game::TitleMapNavigationCommandStatusV1::state_changed;
}

bool TestCrossPumpRunner() {
  using MailboxState =
      xar::ck3_11906::MainThreadQueryMailboxStateV1;
  using Run = xar::ck3_11906::TitleMapNavigationMailboxRunResultV1;
  using Status = xar::game::TitleMapNavigationCommandStatusV1;

  g_advance_calls.store(0);
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  mailbox.state.store(MailboxState::idle);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.executor_submission_enabled = true;
  mailbox.permitted_executor =
      &xar::ck3_11906::ExecuteTitleMapNavigationMailboxV1;
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);

  xar::ck3_11906::TitleMapNavigationMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.command.request.expected_snapshot_revision = 17;
  query.command.request.title_key = "c_bianzhou";
  query.expected_snapshot = g_snapshot;

  std::atomic<bool> stop{false};
  std::atomic<DWORD> pump_thread_id{0};
  std::thread pump([&]() {
    pump_thread_id.store(GetCurrentThreadId(), std::memory_order_release);
    std::uint64_t pump_epoch = 100;
    while (!stop.load(std::memory_order_acquire)) {
      auto expected = MailboxState::queued;
      if (mailbox.state.compare_exchange_strong(
              expected, MailboxState::executing,
              std::memory_order_acq_rel, std::memory_order_acquire)) {
        const auto executor = mailbox.executor;
        void *const context = mailbox.executor_context;
        const auto sequence =
            mailbox.published_sequence.load(std::memory_order_acquire);
        const bool succeeded =
            executor != nullptr && context != nullptr &&
            executor(context, Stamp(pump_epoch++));
        mailbox.executor_succeeded = succeeded;
        mailbox.completed_sequence.store(sequence,
                                         std::memory_order_release);
        mailbox.state.store(succeeded ? MailboxState::completed
                                      : MailboxState::executor_failed,
                            std::memory_order_release);
      } else {
        Sleep(1);
      }
    }
  });
  while (pump_thread_id.load(std::memory_order_acquire) == 0) {
    Sleep(1);
  }
  mailbox.owner_thread_id.store(pump_thread_id.load(std::memory_order_acquire),
                                std::memory_order_release);

  const auto result =
      xar::ck3_11906::RunTitleMapNavigationMailboxV1(query, 2'000, 8);
  stop.store(true, std::memory_order_release);
  pump.join();

  return result == Run::terminal && query.command.status == Status::centered &&
         query.command.dispatched && query.dispatch_ticket_sequence == 1 &&
         query.dispatch_pump_epoch == 100 && query.last_pump_epoch == 101 &&
         query.callback_count == 2 && query.poll_count == 1 &&
         g_advance_calls.load() == 2 &&
         mailbox.state.load() == MailboxState::idle;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

game::TitleMapNavigationCommandStatusV1 AdvanceTitleMapNavigationCommandV1(
    const TitleMapNavigationNativeEnvironmentV1 &,
    const TitleMapNavigationCameraEnvironmentV1 &,
    const TitleMapNavigationCameraAccessV1 &access,
    game::TitleMapNavigationCommandV1 &command) noexcept {
  game::TitleMapNavigationFrameV1 frame{};
  if (access.title.is_owning_thread == nullptr ||
      access.title.capture_frame == nullptr ||
      !access.title.is_owning_thread(access.title.context) ||
      !access.title.capture_frame(access.title.context, frame)) {
    command.status =
        game::TitleMapNavigationCommandStatusV1::state_changed;
    return command.status;
  }
  const auto call = g_advance_calls.fetch_add(1) + 1;
  command.binding = frame;
  command.initialized = true;
  if (call == 1) {
    command.dispatched = true;
    command.status = game::TitleMapNavigationCommandStatusV1::pending;
    return command.status;
  }
  command.camera.settled = true;
  command.status = game::TitleMapNavigationCommandStatusV1::centered;
  return command.status;
}

bool IsTitleMapNavigationTerminalV1(
    game::TitleMapNavigationCommandStatusV1 status) noexcept {
  return status != game::TitleMapNavigationCommandStatusV1::pending;
}

} // namespace xar::ck3_11906

int main() {
  g_snapshot.date_raw = 53'182'008;
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_id = 0x02000001;

  assert(TestParsing());
  assert(TestDirectAndSamePumpRejection());
  assert(TestSamePumpPollRejected());
  assert(TestCrossPumpRunner());
  return 0;
}
