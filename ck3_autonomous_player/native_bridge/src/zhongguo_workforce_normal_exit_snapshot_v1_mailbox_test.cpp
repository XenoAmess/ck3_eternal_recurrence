#include "xar_bridge/zhongguo_workforce_normal_exit_snapshot_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>
#include <string_view>

namespace {

enum class ReaderMode {
  available,
  unavailable,
  inconsistent,
};

xar::game::Snapshot g_snapshot{};
ReaderMode g_reader_mode = ReaderMode::available;
bool g_drift_snapshot = false;
std::uint32_t g_snapshot_reads = 0;
std::uint32_t g_reader_calls = 0;

void PrimeMailbox(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::ZhongguoWorkforceNormalExitSnapshotMailboxContextV1 &query,
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
      ExecuteZhongguoWorkforceNormalExitSnapshotMailboxQueryV1;
  mailbox.executor_context = &query;
  query.mailbox = &mailbox;
  query.ticket.sequence = sequence;
  query.request.expected_snapshot_revision = 77;
  query.request.owner_character_id = 200;
  query.request.request_nonce = "normal-exit-mailbox-77";
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
  ZhongguoWorkforceNormalExitSnapshotRequestV1 request{};
  constexpr std::string_view valid =
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":77,"owner_character_id":200,"request_nonce":"nonce:77"})";
  if (!ParseZhongguoWorkforceNormalExitSnapshotV1Step(
          "query-zhongguo-workforce-normal-exit-snapshot-v1") ||
      ParseZhongguoWorkforceNormalExitSnapshotV1Step(
          "query-zhongguo-workforce-normal-exit-snapshot-v1-received-self") ||
      !ParseZhongguoWorkforceNormalExitSnapshotRequestV1(valid, request) ||
      request.expected_snapshot_revision != 77 ||
      request.owner_character_id != 200 ||
      request.request_nonce != "nonce:77") {
    return false;
  }

  // The command envelope is deliberately an exact seven-field contract.
  constexpr std::string_view invalid[] = {
      // Wrong step.
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v2","expected_revision":77,"owner_character_id":200,"request_nonce":"n"})",
      // Extra and missing fields.
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":77,"owner_character_id":200,"request_nonce":"n","extra":1})",
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":77,"owner_character_id":200})",
      // Numeric domain and representation boundaries.
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":0,"owner_character_id":200,"request_nonce":"n"})",
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":18446744073709551616,"owner_character_id":200,"request_nonce":"n"})",
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":77,"owner_character_id":0,"request_nonce":"n"})",
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":77,"owner_character_id":2147483648,"request_nonce":"n"})",
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":077,"owner_character_id":200,"request_nonce":"n"})",
      // Duplicate fields and escaped nonce text are not part of the ABI.
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":77,"owner_character_id":200,"owner_character_id":201,"request_nonce":"n"})",
      R"({"type":"execute_step","protocol_version":1,"request_id":"step-1","step":"query-zhongguo-workforce-normal-exit-snapshot-v1","expected_revision":77,"owner_character_id":200,"request_nonce":"bad\u0031"})",
  };
  for (const auto value : invalid) {
    if (ParseZhongguoWorkforceNormalExitSnapshotRequestV1(value, request)) {
      return false;
    }
  }
  return true;
}

bool TestDirectInvocationRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::ZhongguoWorkforceNormalExitSnapshotMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.request.expected_snapshot_revision = 77;
  const auto calls_before = g_reader_calls;
  return !xar::ck3_11906::
              ExecuteZhongguoWorkforceNormalExitSnapshotMailboxQueryV1(
                  &query, Stamp()) &&
         query.completion ==
             xar::ck3_11906::
                 ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1::
                     infrastructure_rejected &&
         g_reader_calls == calls_before;
}

bool TestTypedCompletion(ReaderMode mode) {
  g_reader_mode = mode;
  g_drift_snapshot = false;
  g_snapshot_reads = 0;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::ZhongguoWorkforceNormalExitSnapshotMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, mode == ReaderMode::available ? 10 : 11);
  const auto stamp = Stamp();
  const auto calls_before = g_reader_calls;
  const bool accepted = xar::ck3_11906::
      ExecuteZhongguoWorkforceNormalExitSnapshotMailboxQueryV1(&query, stamp);
  if (mode == ReaderMode::inconsistent) {
    return !accepted && g_reader_calls == calls_before + 1 &&
           query.executor_invocations == 1 &&
           query.completion ==
               xar::ck3_11906::
                   ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1::
                       infrastructure_rejected;
  }
  if (!accepted || g_reader_calls != calls_before + 1 ||
      query.executor_invocations != 1 ||
      query.completion !=
          xar::ck3_11906::
              ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1::
                  completed ||
      query.result.snapshot_revision != 77 ||
      query.result.date_raw != g_snapshot.date_raw ||
      query.result.subject_character_id != g_snapshot.played_character_id ||
      query.result.requested_owner_character_id != 200 ||
      query.execution_stamp != stamp) {
    return false;
  }
  if (mode == ReaderMode::available) {
    return query.read_result ==
               xar::game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::
                   available &&
           query.result.status ==
               xar::game::ZhongguoWorkforceNormalExitSnapshotStatusV1::
                   available &&
           query.result.lifecycle ==
               xar::game::ZhongguoWorkforceNormalExitLifecycleV1::sealed &&
           query.result.readiness.player_subject_binding_ready &&
           query.result.readiness.owner_binding_ready &&
           query.result.readiness.lifecycle_ready &&
           query.result.readiness.same_frame_ready &&
           query.result.readiness.ready;
  }
  return query.read_result ==
             xar::game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::
                 unavailable &&
         query.result.status ==
             xar::game::ZhongguoWorkforceNormalExitSnapshotStatusV1::
                 unavailable &&
         query.result.unavailable_reason == "case_not_found" &&
         !query.result.readiness.ready;
}

bool TestSnapshotDriftRejected() {
  g_reader_mode = ReaderMode::available;
  g_drift_snapshot = true;
  g_snapshot_reads = 0;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::ZhongguoWorkforceNormalExitSnapshotMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, 12);
  const bool accepted = xar::ck3_11906::
      ExecuteZhongguoWorkforceNormalExitSnapshotMailboxQueryV1(&query, Stamp());
  g_drift_snapshot = false;
  return !accepted &&
         query.completion ==
             xar::ck3_11906::
                 ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1::
                     infrastructure_rejected;
}

bool TestFailureMappings() {
  using Completion = xar::ck3_11906::
      ZhongguoWorkforceNormalExitSnapshotMailboxCompletionV1;
  using Wait = xar::ck3_11906::MainThreadQueryWaitResultV1;
  using xar::ck3_11906::
      ZhongguoWorkforceNormalExitSnapshotFailureMessageV1;
  return ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::executor_failed, Completion::not_executed, false) ==
             "application-main Workforce normal-exit executor failed" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::infrastructure_failed, Completion::not_executed, false) ==
             "application-main Workforce normal-exit boundary drifted" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::cancelled, Completion::not_executed, false) ==
             "application-main Workforce normal-exit query was cancelled" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::timeout_cancelled_before_execution,
             Completion::not_executed, false) ==
             "application-main Workforce normal-exit query timed out" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::timeout_executor_already_running,
             Completion::not_executed, false) ==
             "application-main Workforce normal-exit executor is still running" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::ticket_mismatch, Completion::not_executed, false) ==
             "application-main Workforce normal-exit ticket mismatch" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::completed, Completion::completed, true) ==
             "application-main Workforce normal-exit result is inconsistent" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::completed, Completion::completed, false) ==
             "Workforce normal-exit completion snapshot changed" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::completed, Completion::frame_changed, true) ==
             "Workforce normal-exit application-main frame changed" &&
         ZhongguoWorkforceNormalExitSnapshotFailureMessageV1(
             Wait::completed, Completion::infrastructure_rejected, true) ==
             "application-main Workforce normal-exit executor was rejected";
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  ++g_snapshot_reads;
  if (g_drift_snapshot && g_snapshot_reads > 1) ++output.date_raw;
  return true;
}

game::ReadZhongguoWorkforceNormalExitSnapshotResultV1
ReadZhongguoWorkforceNormalExitSnapshotV1(
    const ZhongguoWorkforceNormalExitNativeEnvironmentV1 &,
    const ZhongguoWorkforceNormalExitAccessV1 &access,
    const ZhongguoWorkforceNormalExitSnapshotRequestV1 &request,
    game::ZhongguoWorkforceNormalExitSnapshotV1 &output) noexcept {
  ++g_reader_calls;
  game::ZhongguoCaseFrameV1 before{};
  game::ZhongguoCaseFrameV1 after{};
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, before) ||
      !access.capture_frame(access.context, after) || before != after) {
    return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
  }

  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  output.date_raw = before.date_raw;
  output.paused = before.paused;
  output.player_character_id = before.played_character_id;
  output.subject_character_id = before.played_character_id;
  output.requested_owner_character_id = request.owner_character_id;
  output.case_kind.assign(kZhongguoWorkforceNormalExitSnapshotV1CaseKind);
  output.request_nonce = request.request_nonce;
  if (g_reader_mode == ReaderMode::unavailable) {
    output.status =
        game::ZhongguoWorkforceNormalExitSnapshotStatusV1::unavailable;
    output.unavailable_reason = "case_not_found";
    return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::unavailable;
  }

  output.status = game::ZhongguoWorkforceNormalExitSnapshotStatusV1::available;
  output.lifecycle = game::ZhongguoWorkforceNormalExitLifecycleV1::sealed;
  output.readiness.player_subject_binding_ready = true;
  output.readiness.owner_binding_ready = true;
  output.readiness.lifecycle_ready = true;
  output.readiness.same_frame_ready = true;
  output.readiness.ready = g_reader_mode == ReaderMode::available;
  return game::ReadZhongguoWorkforceNormalExitSnapshotResultV1::available;
}

} // namespace xar::ck3_11906

int main() {
  g_snapshot.date_raw = 54'321;
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_id = 100;
  const bool ok = TestParsing() && TestDirectInvocationRejected() &&
                  TestTypedCompletion(ReaderMode::available) &&
                  TestTypedCompletion(ReaderMode::unavailable) &&
                  TestTypedCompletion(ReaderMode::inconsistent) &&
                  TestSnapshotDriftRejected() && TestFailureMappings();
  if (!ok) {
    std::cerr << "Workforce normal-exit mailbox fixture failed\n";
    return 1;
  }
  return 0;
}
