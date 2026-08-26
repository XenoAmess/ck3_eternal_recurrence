#include "xar_bridge/loaded_feature_manifest_v1_mailbox.hpp"

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
    xar::ck3_11906::LoadedFeatureManifestMailboxContextV1 &query,
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
      &xar::ck3_11906::ExecuteLoadedFeatureManifestMailboxQueryV1;
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
  return ParseLoadedFeatureManifestV1Step(
             "query-loaded-feature-manifest-v1") &&
         !ParseLoadedFeatureManifestV1Step(
             "query-loaded-feature-manifest-v1-1") &&
         ParseLoadedFeatureManifestExpectedRevisionV1(
             R"({"expected_revision":77})", revision) &&
         revision == 77 &&
         ParseLoadedFeatureManifestExpectedRevisionV1(
             R"({"step":"query-loaded-feature-manifest-v1", "expected_revision": 77, "x":1})",
             revision) &&
         revision == 77 &&
         !ParseLoadedFeatureManifestExpectedRevisionV1(
             R"({"expected_revision":0})", revision) &&
         !ParseLoadedFeatureManifestExpectedRevisionV1(
             R"({"expected_revision":077})", revision) &&
         !ParseLoadedFeatureManifestExpectedRevisionV1(
             R"({"expected_revision":77,"expected_revision":78})",
             revision) &&
         !ParseLoadedFeatureManifestExpectedRevisionV1("{}", revision);
}

bool TestDirectInvocationRejected() {
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::LoadedFeatureManifestMailboxContextV1 query{};
  query.mailbox = &mailbox;
  query.ticket.sequence = 1;
  query.request.expected_snapshot_revision = 77;
  const auto stamp = Stamp();
  return !xar::ck3_11906::ExecuteLoadedFeatureManifestMailboxQueryV1(
             &query, stamp) &&
         query.completion ==
             xar::ck3_11906::LoadedFeatureManifestMailboxCompletionV1::
                 infrastructure_rejected &&
         g_reader_calls == 0;
}

bool TestTypedCompletion(bool available) {
  g_reader_available = available;
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  xar::ck3_11906::LoadedFeatureManifestMailboxContextV1 query{};
  PrimeMailbox(mailbox, query, available ? 10 : 11);
  const auto stamp = Stamp();
  const auto calls_before = g_reader_calls;
  if (!xar::ck3_11906::ExecuteLoadedFeatureManifestMailboxQueryV1(
          &query, stamp) ||
      g_reader_calls != calls_before + 1 || query.executor_invocations != 1 ||
      query.completion !=
          xar::ck3_11906::LoadedFeatureManifestMailboxCompletionV1::completed ||
      query.result.snapshot_revision != 77 ||
      query.result.date_raw != g_snapshot.date_raw ||
      query.execution_stamp != stamp) {
    return false;
  }
  if (available) {
    return query.read_result ==
               xar::game::ReadLoadedFeatureManifestResultV1::available &&
           query.result.status ==
               xar::game::LoadedFeatureManifestStatusV1::available &&
           query.result.readiness.actionable_ready &&
           !query.result.readiness.entitlements_ready &&
           query.result.unavailable_reason.empty();
  }
  return query.read_result ==
             xar::game::ReadLoadedFeatureManifestResultV1::unavailable &&
         query.result.status ==
             xar::game::LoadedFeatureManifestStatusV1::unavailable &&
         !query.result.readiness.actionable_ready &&
         query.result.unavailable_reason == "unsupported_build";
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

game::ReadLoadedFeatureManifestResultV1 ReadLoadedFeatureManifestV1(
    const LoadedFeatureManifestNativeEnvironmentV1 &,
    const LoadedFeatureManifestAccessV1 &access,
    const LoadedFeatureManifestRequestV1 &request,
    game::LoadedFeatureManifestV1 &output) noexcept {
  ++g_reader_calls;
  game::LoadedFeatureManifestFrameV1 frame{};
  if (access.capture_frame == nullptr || access.is_main_thread == nullptr ||
      !access.is_main_thread(access.context) ||
      !access.capture_frame(access.context, frame)) {
    return game::ReadLoadedFeatureManifestResultV1::unavailable;
  }
  output = {};
  output.snapshot_revision = request.expected_snapshot_revision;
  output.date_raw = frame.date_raw;
  if (!g_reader_available) {
    output.status = game::LoadedFeatureManifestStatusV1::unavailable;
    output.unavailable_reason = "unsupported_build";
    output.effective_feature_flags.unavailable_reason = "unsupported_build";
    output.script_dlc_keys.unavailable_reason = "unsupported_build";
    return game::ReadLoadedFeatureManifestResultV1::unavailable;
  }
  output.status = game::LoadedFeatureManifestStatusV1::available;
  output.effective_feature_flags.status =
      game::LoadedFeatureComponentStatusV1::available;
  output.effective_feature_flags.native_count = 44;
  output.effective_feature_flags.items.resize(44);
  output.script_dlc_keys.status =
      game::LoadedFeatureComponentStatusV1::available;
  output.script_dlc_keys.enumerated_count = 0;
  output.readiness = {true, true, false, true, true};
  return game::ReadLoadedFeatureManifestResultV1::available;
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
    std::cerr << "loaded-feature mailbox parser fixture failed\n";
    return 1;
  }
  if (!TestDirectInvocationRejected()) {
    std::cerr << "loaded-feature direct invocation fixture failed\n";
    return 1;
  }
  if (!TestTypedCompletion(true) || !TestTypedCompletion(false)) {
    std::cerr << "loaded-feature typed completion fixture failed\n";
    return 1;
  }
  std::cout << "loaded-feature-manifest-v1 mailbox fixture passed\n";
  return 0;
}
