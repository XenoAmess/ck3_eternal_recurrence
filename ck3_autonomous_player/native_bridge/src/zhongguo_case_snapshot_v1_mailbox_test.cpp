#include "xar_bridge/zhongguo_case_snapshot_v1_mailbox.hpp"

#include <windows.h>

#include <cstdint>
#include <iostream>

namespace {

xar::game::Snapshot g_snapshot{};
bool g_reader_available = true;
bool g_reader_aggregate_ready = true;
bool g_drift_snapshot = false;
std::uint32_t g_snapshot_reads = 0;
std::uint32_t g_reader_calls = 0;

void PrimeMailbox(
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::ZhongguoCaseSnapshotMailboxContextV1 &query,
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
      &xar::ck3_11906::ExecuteZhongguoCaseSnapshotMailboxQueryV1;
  mailbox.executor_context = &query;
  query.mailbox = &mailbox;
  query.ticket.sequence = sequence;
  query.request.expected_snapshot_revision = 77;
  query.request.subject_character_id = 200;
  query.request.owner_character_id = 100;
  query.request.case_kind =
      xar::ck3_11906::kZhongguoCaseSnapshotV1CaseKind;
  query.request.request_nonce = "mailbox-77";
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
  ZhongguoCaseSnapshotRequestV1 request{};
  const auto valid =
      R"({"type":"command","expected_revision":77,"case_kind":"zhongguo.b1.performance","subject_character_id":200,"owner_character_id":0,"request_nonce":"nonce:77"})";
  if (!ParseZhongguoCaseSnapshotV1Step(
          "query-zhongguo-case-snapshot-v1") ||
      ParseZhongguoCaseSnapshotV1Step(
          "query-zhongguo-case-snapshot-v1-b1") ||
      !ParseZhongguoCaseSnapshotRequestV1(valid, request) ||
      request.expected_snapshot_revision != 77 ||
      request.subject_character_id != 200 ||
      request.owner_character_id.has_value() ||
      request.request_nonce != "nonce:77") {
    return false;
  }
  const auto alias_word_nonce =
      R"({"expected_revision":77,"case_kind":"zhongguo.b1.performance","subject_character_id":200,"owner_character_id":0,"request_nonce":"owner"})";
  if (!ParseZhongguoCaseSnapshotRequestV1(alias_word_nonce, request) ||
      request.request_nonce != "owner") {
    return false;
  }
  return !ParseZhongguoCaseSnapshotRequestV1(
             R"({"expected_revision":077,"case_kind":"zhongguo.b1.performance","subject_character_id":200,"owner_character_id":0,"request_nonce":"n"})",
             request) &&
         !ParseZhongguoCaseSnapshotRequestV1(
             R"({"expected_revision":77,"expected_revision":78,"case_kind":"zhongguo.b1.performance","subject_character_id":200,"owner_character_id":0,"request_nonce":"n"})",
             request) &&
         !ParseZhongguoCaseSnapshotRequestV1(
             R"({"expected_revision":77,"case_kind":"zhongguo.other","subject_character_id":200,"owner_character_id":0,"request_nonce":"n"})",
             request) &&
         !ParseZhongguoCaseSnapshotRequestV1(
             R"({"expected_revision":77,"case_kind":"zhongguo.b1.performance","subject_character_id":0200,"owner_character_id":0,"request_nonce":"n"})",
             request) &&
         !ParseZhongguoCaseSnapshotRequestV1(
             R"({"expected_revision":77,"case_kind":"zhongguo.b1.performance","subject_character_id":200,"owner_character_id":0,"request_nonce":"bad\u0031"})",
             request) &&
         !ParseZhongguoCaseSnapshotRequestV1(
             R"({"expected_revision":77,"case_kind":"zhongguo.b1.performance","subject_character_id":200,"owner_character_id":0,"request_nonce":"n","variable_name":"zg361_b1_case_owner"})",
             request) &&
         !ParseZhongguoCaseSnapshotRequestV1(
             R"({"expected_revision":77,"case_kind":"zhongguo.b1.performance","subject_character_id":200,"owner_character_id":0,"request_nonce":"n","owner":100})",
             request) &&
         !ParseZhongguoCaseSnapshotRequestV1(
             R"({"expected_revision":77,"case_kind":"zhongguo.b1.performance","subject_character_id":200,"owner_character_id":00,"request_nonce":"n"})",
             request);
}

bool TestDirectInvocationRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::ZhongguoCaseSnapshotMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.request.expected_snapshot_revision = 77;
  const auto stamp = Stamp();
  return !xar::ck3_11906::ExecuteZhongguoCaseSnapshotMailboxQueryV1(
             &query, stamp) &&
         query.completion ==
             xar::ck3_11906::ZhongguoCaseSnapshotMailboxCompletionV1::
                 infrastructure_rejected &&
         g_reader_calls == 0;
}

bool TestTypedCompletion(bool available, bool aggregate_ready) {
  g_reader_available = available;
  g_reader_aggregate_ready = aggregate_ready;
  g_drift_snapshot = false;
  g_snapshot_reads = 0;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::ZhongguoCaseSnapshotMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, available ? 10 : 11);
  const auto stamp = Stamp();
  const auto calls_before = g_reader_calls;
  if (!xar::ck3_11906::ExecuteZhongguoCaseSnapshotMailboxQueryV1(
          &query, stamp) ||
      g_reader_calls != calls_before + 1 || query.executor_invocations != 1 ||
      query.completion !=
          xar::ck3_11906::ZhongguoCaseSnapshotMailboxCompletionV1::completed ||
      query.result.snapshot_revision != 77 ||
      query.result.date_raw != g_snapshot.date_raw ||
      query.execution_stamp != stamp) {
    return false;
  }
  if (available) {
    return query.read_result ==
               xar::game::ReadZhongguoCaseSnapshotResultV1::available &&
           query.result.status ==
               xar::game::ZhongguoCaseSnapshotStatusV1::available &&
           query.result.readiness.case_identity_ready &&
           query.result.readiness.ready == aggregate_ready;
  }
  return query.read_result ==
             xar::game::ReadZhongguoCaseSnapshotResultV1::unavailable &&
         query.result.status ==
             xar::game::ZhongguoCaseSnapshotStatusV1::unavailable &&
         query.result.unavailable_reason == "case_not_found";
}

bool TestSnapshotDriftRejected() {
  g_reader_available = true;
  g_reader_aggregate_ready = true;
  g_drift_snapshot = true;
  g_snapshot_reads = 0;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::ZhongguoCaseSnapshotMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, 12);
  const bool accepted =
      xar::ck3_11906::ExecuteZhongguoCaseSnapshotMailboxQueryV1(
          &query, Stamp());
  g_drift_snapshot = false;
  return !accepted &&
         query.completion ==
             xar::ck3_11906::ZhongguoCaseSnapshotMailboxCompletionV1::
                 infrastructure_rejected;
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  ++g_snapshot_reads;
  if (g_drift_snapshot && g_snapshot_reads > 1) {
    ++output.date_raw;
  }
  return true;
}

game::ReadZhongguoCaseSnapshotResultV1 ReadZhongguoCaseSnapshotV1(
    const ZhongguoCaseNativeEnvironmentV1 &,
    const ZhongguoCaseAccessV1 &access,
    const ZhongguoCaseSnapshotRequestV1 &request,
    game::ZhongguoCaseSnapshotV1 &output) noexcept {
  ++g_reader_calls;
  game::ZhongguoCaseFrameV1 before{};
  game::ZhongguoCaseFrameV1 after{};
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, before) ||
      !access.capture_frame(access.context, after) || before != after) {
    return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
  }
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  output.date_raw = before.date_raw;
  output.paused = before.paused;
  output.player_character_id = before.played_character_id;
  output.subject_character_id = request.subject_character_id;
  output.requested_owner_character_id = request.owner_character_id;
  output.case_kind = request.case_kind;
  output.request_nonce = request.request_nonce;
  if (!g_reader_available) {
    output.status = game::ZhongguoCaseSnapshotStatusV1::unavailable;
    output.unavailable_reason = "case_not_found";
    return game::ReadZhongguoCaseSnapshotResultV1::unavailable;
  }
  output.status = game::ZhongguoCaseSnapshotStatusV1::available;
  output.readiness.player_binding_ready = true;
  output.readiness.case_identity_ready = true;
  output.readiness.same_frame_ready = true;
  output.readiness.ready = g_reader_aggregate_ready;
  return game::ReadZhongguoCaseSnapshotResultV1::available;
}

} // namespace xar::ck3_11906

int main() {
  g_snapshot.date_raw = 54'321;
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_id = 100;
  if (!TestParsing()) {
    std::cerr << "ZhongGuo case mailbox parser fixture failed\n";
    return 1;
  }
  if (!TestDirectInvocationRejected()) {
    std::cerr << "ZhongGuo case direct invocation fixture failed\n";
    return 1;
  }
  if (!TestTypedCompletion(true, true) ||
      !TestTypedCompletion(true, false) ||
      !TestTypedCompletion(false, false)) {
    std::cerr << "ZhongGuo case typed completion fixture failed\n";
    return 1;
  }
  if (!TestSnapshotDriftRejected()) {
    std::cerr << "ZhongGuo case snapshot drift fixture failed\n";
    return 1;
  }
  return 0;
}
