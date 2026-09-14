#include "xar_bridge/culture_innovation_snapshot_v1_mailbox.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <windows.h>

#include <cassert>
#include <fstream>
#include <iterator>
#include <string>

namespace {

using namespace xar::ck3_11906;

struct Fixture {
  xar::game::Snapshot snapshot{};
  CultureInnovationSourceSampleV1 first{};
  CultureInnovationSourceSampleV1 second{};
  std::uint32_t snapshot_reads = 0;
  std::uint32_t source_reads = 0;
  bool source_available = true;
};

Fixture *g_read_snapshot_fixture = nullptr;

bool FakeReadSnapshot(void *opaque, xar::game::Snapshot &output) noexcept {
  auto *fixture = static_cast<Fixture *>(opaque);
  if (fixture == nullptr) return false;
  ++fixture->snapshot_reads;
  output = fixture->snapshot;
  return true;
}

bool FakeResolvePlayer(void *opaque, std::int32_t player_character_id,
                       std::uintptr_t &played_character) noexcept {
  const auto *fixture = static_cast<const Fixture *>(opaque);
  if (fixture == nullptr ||
      fixture->snapshot.played_character_id != player_character_id) {
    played_character = 0;
    return false;
  }
  played_character = 0x1234;
  return true;
}

bool FakeReadSource(void *opaque, std::uintptr_t played_character,
                    CultureInnovationSourceSampleV1 &output) noexcept {
  auto *adapter =
      static_cast<CultureInnovationSourceAdapterContextV1 *>(opaque);
  auto *fixture = adapter == nullptr
                      ? nullptr
                      : static_cast<Fixture *>(adapter->native.context);
  if (adapter == nullptr || fixture == nullptr || played_character != 0x1234 ||
      !fixture->source_available) {
    if (adapter != nullptr) {
      adapter->last_failure =
          CultureInnovationSourceAdapterFailureV1::
              innovation_metadata_unavailable;
    }
    output = {};
    return false;
  }
  output = fixture->source_reads++ == 0 ? fixture->first : fixture->second;
  adapter->last_failure = CultureInnovationSourceAdapterFailureV1::none;
  return true;
}

template <std::size_t Size>
void Fixed(std::array<char, Size> &output, std::string_view value) {
  assert(value.size() < output.size());
  output.fill('\0');
  std::copy(value.begin(), value.end(), output.begin());
}

Fixture BaseFixture() {
  Fixture fixture{};
  fixture.snapshot.date_raw = 48'000;
  fixture.snapshot.paused = true;
  fixture.snapshot.map_ready = true;
  fixture.snapshot.has_played_character = true;
  fixture.snapshot.played_character_alive = true;
  fixture.snapshot.played_character_id = 0;

  auto &sample = fixture.first;
  sample.player_character_id = 0;
  sample.player_identity_round_trip = true;
  sample.state.culture_id = 0;
  sample.state.culture_head_presence =
      xar::game::CultureInnovationPresenceV1::absent;
  sample.state.culture_head_character_id = -1;
  sample.state.fascination_presence =
      xar::game::CultureInnovationPresenceV1::present;
  assert(AssignCultureInnovationStableKeyV1(
      "innovation_crop_rotation",
      sample.state.current_fascination_key));
  sample.state.era_count = 1;
  assert(AssignCultureInnovationStableKeyV1(
      "culture_era_tribal", sample.state.eras[0].key));
  sample.state.eras[0].progress_raw = 0;
  sample.state.innovation_count = 1;
  auto &innovation = sample.state.innovations[0];
  assert(AssignCultureInnovationStableKeyV1(
      "innovation_crop_rotation", innovation.key));
  assert(AssignCultureInnovationStableKeyV1(
      "culture_era_tribal", innovation.era_key));
  assert(AssignCultureInnovationStableKeyV1(
      "culture_group_civic", innovation.group_key));
  assert(AssignCultureInnovationStableKeyV1(
      "stewardship", innovation.skill_key));
  innovation.progress_raw = 0;
  innovation.is_active = true;
  innovation.can_gain_progress = true;
  innovation.can_be_fascination = true;
  innovation.is_fascination = true;
  fixture.second = fixture.first;
  return fixture;
}

void Prepare(Fixture &fixture, CultureInnovationMailboxContextV1 &query,
             MainThreadQueryMailboxV1 &mailbox,
             MainThreadExecutionStampV1 &stamp) {
  query.mailbox = &mailbox;
  query.ticket.sequence = 9;
  query.environment.exact_build_admitted = true;
  query.environment.admitted_executable_sha256 =
      kCultureInnovationSnapshotExecutableSha256V1;
  query.environment.offline_fixture = true;
  query.source.native.context = &fixture;
  query.request.expected_snapshot_id = "native:77";
  query.request.expected_public_revision = 77;
  query.request.expected_native_revision = 977;
  query.request.expected_date_raw = fixture.snapshot.date_raw;
  query.request.expected_player_character_id =
      fixture.snapshot.played_character_id;
  query.expected_snapshot = fixture.snapshot;
  query.snapshot_context = &fixture;
  query.read_snapshot = &FakeReadSnapshot;
  query.resolve_player = &FakeResolvePlayer;
  query.read_source = &FakeReadSource;

  mailbox.state.store(MainThreadQueryMailboxStateV1::executing);
  mailbox.published_sequence.store(query.ticket.sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor = &ExecuteCultureInnovationMailboxQueryV1;
  mailbox.executor_context = &query;

  stamp.pump_epoch = 44;
  stamp.thread_id = GetCurrentThreadId();
  stamp.tls_initialized_flag_address = 0x1000;
  stamp.tls_initialized = 1;
  stamp.tls_context = 0x2000;
  stamp.tls_main_thread_marker = 1;
  stamp.jomini_state = 0x3000;
  stamp.game_state = 0x4000;
  stamp.date_raw = fixture.snapshot.date_raw;
  stamp.paused = true;
}

void TestAvailableTerminalAndLegalZero() {
  auto fixture = BaseFixture();
  CultureInnovationMailboxContextV1 query{};
  MainThreadQueryMailboxV1 mailbox{};
  MainThreadExecutionStampV1 stamp{};
  Prepare(fixture, query, mailbox, stamp);
  assert(ExecuteCultureInnovationMailboxQueryV1(&query, stamp));
  assert(query.completion ==
         CultureInnovationMailboxCompletionV1::terminal_available);
  assert(query.execution_result.status ==
         xar::game::CultureInnovationSnapshotStatusV1::available);
  assert(query.execution_result.state.culture_id == 0);
  assert(query.execution_result.state.eras[0].progress_raw == 0);
  assert(query.execution_result.state.innovations[0].progress_raw == 0);
  assert(query.execution_result.public_revision == 77);
  assert(query.execution_result.native_revision == 977);
  assert(query.execution_result.proof_epoch == 44);
  assert(query.execution_result.date_raw == fixture.snapshot.date_raw);
  assert(fixture.source_reads == 2);
}

void TestTypedUnavailableRetainsFrameBinding() {
  auto fixture = BaseFixture();
  fixture.source_available = false;
  CultureInnovationMailboxContextV1 query{};
  MainThreadQueryMailboxV1 mailbox{};
  MainThreadExecutionStampV1 stamp{};
  Prepare(fixture, query, mailbox, stamp);
  assert(ExecuteCultureInnovationMailboxQueryV1(&query, stamp));
  assert(query.completion ==
         CultureInnovationMailboxCompletionV1::terminal_unavailable);
  assert(query.execution_result.status ==
         xar::game::CultureInnovationSnapshotStatusV1::unavailable);
  assert(query.execution_result.unavailable_reason ==
         xar::game::CultureInnovationSnapshotFailureV1::
             native_source_read_failed);
  assert(query.source_failure ==
         CultureInnovationSourceAdapterFailureV1::
             innovation_metadata_unavailable);
  assert(query.execution_result.public_revision == 77);
  assert(query.execution_result.native_revision == 977);
  assert(query.execution_result.proof_epoch == 44);
  assert(query.execution_result.date_raw == 48'000);
  assert(query.execution_result.player_character_id == 0);
}

void TestNativeSampleDriftIsTyped() {
  auto fixture = BaseFixture();
  fixture.second.state.innovations[0].progress_raw = 1;
  CultureInnovationMailboxContextV1 query{};
  MainThreadQueryMailboxV1 mailbox{};
  MainThreadExecutionStampV1 stamp{};
  Prepare(fixture, query, mailbox, stamp);
  assert(ExecuteCultureInnovationMailboxQueryV1(&query, stamp));
  assert(query.completion ==
         CultureInnovationMailboxCompletionV1::terminal_unavailable);
  assert(query.execution_result.unavailable_reason ==
         xar::game::CultureInnovationSnapshotFailureV1::native_sample_drift);
  assert(query.execution_result.public_revision == 77);
  assert(query.execution_result.proof_epoch == 44);
}

void TestTerminalOnlyHeartbeatPublication() {
  CultureInnovationAsyncPrivateProbeV1 probe{};
  const auto pending = SerializeCultureInnovationAsyncPrivateProbeV1(probe);
  assert(pending.find("\"terminal_published\":false") !=
         std::string::npos);
  assert(pending.find("\"terminal_result\":null") != std::string::npos);

  auto fixture = BaseFixture();
  CultureInnovationMailboxContextV1 query{};
  MainThreadQueryMailboxV1 mailbox{};
  MainThreadExecutionStampV1 stamp{};
  Prepare(fixture, query, mailbox, stamp);
  assert(ExecuteCultureInnovationMailboxQueryV1(&query, stamp));
  probe.state = CultureInnovationAsyncStateV1::terminal_available;
  probe.terminal_published = true;
  probe.terminal_result = query.execution_result;
  const auto terminal = SerializeCultureInnovationAsyncPrivateProbeV1(probe);
  assert(terminal.find("\"terminal_published\":true") !=
         std::string::npos);
  assert(terminal.find("\"snapshot_id\":\"native:77\"") !=
         std::string::npos);
  assert(terminal.find("\"culture_id\":0") != std::string::npos);
  assert(terminal.find("\"progress_raw\":0") != std::string::npos);
  assert(terminal.find("\"raw_pointers_persisted\":false") !=
         std::string::npos);
}

void TestCandidateManifest(const char *path) {
  assert(path != nullptr);
  std::ifstream input(path, std::ios::binary);
  assert(input);
  const std::string manifest((std::istreambuf_iterator<char>(input)),
                             std::istreambuf_iterator<char>());
  assert(manifest.find("\"default_enabled\": false") !=
         std::string::npos);
  assert(manifest.find("\"ck3_started\": false") != std::string::npos);
  assert(manifest.find("\"public_mcp_schema_changed\": false") !=
         std::string::npos);
  assert(manifest.find("\"fixed_slot_index\": 40") !=
         std::string::npos);
  assert(manifest.find("\"fixed_slot\": \"permitted_executor_quadragintary\"") !=
         std::string::npos);
  assert(manifest.find("\"reserved_slot_indices\": [36, 37, 38, 39]") !=
         std::string::npos);
  assert(manifest.find("a84ce64e164e9ccef79eb1e7221bb22f487cdea1") !=
         std::string::npos);
  assert(manifest.find("3e6f9141b88b5978cf6b2f8670f1a3d5edbe10b8") !=
         std::string::npos);
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  if (g_read_snapshot_fixture == nullptr) return false;
  output = g_read_snapshot_fixture->snapshot;
  return true;
}

} // namespace xar::ck3_11906

int main(int argc, char **argv) {
  assert(argc == 2);
  TestAvailableTerminalAndLegalZero();
  TestTypedUnavailableRetainsFrameBinding();
  TestNativeSampleDriftIsTyped();
  TestTerminalOnlyHeartbeatPublication();
  TestCandidateManifest(argv[1]);
  return 0;
}
