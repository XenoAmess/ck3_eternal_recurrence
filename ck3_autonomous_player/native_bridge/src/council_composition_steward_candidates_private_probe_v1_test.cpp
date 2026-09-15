#include "xar_bridge/council_composition_steward_candidates_private_probe_v1.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>

namespace {

using Frame = xar::ck3_11906::CouncilCompositionStewardCandidatesFrameV1;
using NativeVector =
    xar::ck3_11906::CouncilCompositionStewardNativeCandidateVectorV1;

struct Candidate {
  std::int32_t id = -1;
};

struct Fixture {
  std::array<Candidate, 3> candidates{{{30}, {10}, {20}}};
  std::array<std::uintptr_t, 3> pointers{};
  Frame frame{};
  std::uint32_t capture_calls = 0;
  std::uint32_t producer_calls = 0;
  std::uint32_t release_calls = 0;
};

xar::game::Snapshot g_snapshot{};

bool Capture(void *opaque, Frame &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.capture_calls;
  output = fixture.frame;
  return true;
}

bool MainThread(void *) noexcept { return true; }

bool Produce(void *opaque, std::uintptr_t owner, std::uintptr_t task,
             bool gui_mode, NativeVector &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.producer_calls;
  if (owner != fixture.frame.played_character ||
      task != fixture.frame.active_task || !gui_mode) {
    return false;
  }
  output.data_address =
      reinterpret_cast<std::uintptr_t>(fixture.pointers.data());
  output.capacity = 64;
  output.count = static_cast<std::int32_t>(fixture.pointers.size());
  return true;
}

bool Release(void *opaque, NativeVector &vector) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.release_calls;
  vector = {};
  return true;
}

bool Readable(void *, std::uintptr_t address, std::size_t size) noexcept {
  return address != 0 && size == 3 * sizeof(std::uintptr_t);
}

bool ReadPointer(void *, std::uintptr_t address,
                 std::uintptr_t &candidate) noexcept {
  candidate = *reinterpret_cast<const std::uintptr_t *>(address);
  return candidate != 0;
}

bool ReadId(void *, std::uintptr_t candidate,
            std::int32_t &character_id) noexcept {
  if (candidate == 0)
    return false;
  character_id = reinterpret_cast<const Candidate *>(candidate)->id;
  return true;
}

bool Resolve(void *opaque, std::int32_t character_id,
             std::uintptr_t &candidate) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  candidate = 0;
  for (auto &row : fixture.candidates) {
    if (row.id == character_id) {
      candidate = reinterpret_cast<std::uintptr_t>(&row);
      return true;
    }
  }
  return false;
}

void Prime(
    xar::bridge::CouncilCompositionStewardCandidatesPrivateProbeV1 &probe,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox, std::uint64_t sequence) {
  mailbox.state.store(xar::ck3_11906::MainThreadQueryMailboxStateV1::executing);
  mailbox.failure_flags.store(0);
  mailbox.stop_requested.store(false);
  mailbox.published_sequence.store(sequence);
  mailbox.owner_thread_id.store(GetCurrentThreadId());
  mailbox.paused_owner_verified_pump_epochs.store(
      xar::ck3_11906::kMainThreadQueryMinimumPausedOwnerVerifiedPumpEpochs);
  mailbox.executor =
      &xar::bridge::ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1;
  mailbox.executor_context = &probe;
  probe.ticket.sequence = sequence;
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

Fixture MakeFixture() {
  Fixture fixture{};
  const std::string snapshot_id = "native:3";
  std::copy(snapshot_id.begin(), snapshot_id.end(),
            fixture.frame.snapshot_id.begin());
  fixture.frame.public_revision = 4;
  fixture.frame.native_revision = 3;
  fixture.frame.date_raw = g_snapshot.date_raw;
  fixture.frame.paused = true;
  fixture.frame.map_ready = true;
  fixture.frame.has_played_character = true;
  fixture.frame.played_character_alive = true;
  fixture.frame.played_character_id = g_snapshot.played_character_id;
  fixture.frame.played_character = 0x11110000;
  fixture.frame.played_character_identity_round_trip = true;
  fixture.frame.active_task_id = 7159;
  fixture.frame.active_task = 0x22220000;
  fixture.frame.active_task_identity_round_trip = true;
  const std::string position = "councillor_steward";
  std::copy(position.begin(), position.end(),
            fixture.frame.position_key.begin());
  return fixture;
}

void ResetPointers(Fixture &fixture) {
  for (std::size_t index = 0; index < fixture.pointers.size(); ++index) {
    fixture.pointers[index] =
        reinterpret_cast<std::uintptr_t>(&fixture.candidates[index]);
  }
}

void InstallAndPrepare(
    Fixture &fixture,
    xar::ck3_11906::MainThreadQueryMailboxV1 &mailbox,
    xar::ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1 &binding,
    xar::bridge::CouncilCompositionStewardCandidatesPrivateProbeV1 &probe) {
  using namespace xar;
  ResetPointers(fixture);
  binding.attached = true;
  assert(
      bridge::
          ConfigureCouncilCompositionStewardCandidatesPrivateProbeTransportV1(
              probe, mailbox, {}, binding));

  ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      ck3_11906::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  environment.module_base = 0x10000000;
  environment.producer_address =
      environment.module_base +
      ck3_11906::kCouncilCompositionStewardCandidatesProducerRvaV1;
  ck3_11906::CouncilCompositionStewardCandidatesAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &MainThread;
  access.produce = &Produce;
  access.release = &Release;
  access.is_readable_span = &Readable;
  access.read_candidate_pointer = &ReadPointer;
  access.read_candidate_id = &ReadId;
  access.resolve_candidate = &Resolve;
  assert(bridge::InstallCouncilCompositionStewardCandidatesPrivateProbeV1(
      probe, environment, access));
  assert(bridge::PrepareCouncilCompositionStewardCandidatesPrivateProbeV1(
      probe, g_snapshot, 4, 3));
}

void TestOnePausedSameFrameQuery() {
  using namespace xar;
  auto fixture = MakeFixture();
  ResetPointers(fixture);
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1 binding{};
  binding.attached = true;
  bridge::CouncilCompositionStewardCandidatesPrivateProbeV1 probe{};
  assert(
      bridge::
          ConfigureCouncilCompositionStewardCandidatesPrivateProbeTransportV1(
              probe, mailbox, {}, binding));

  ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      ck3_11906::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  environment.module_base = 0x10000000;
  environment.producer_address =
      environment.module_base +
      ck3_11906::kCouncilCompositionStewardCandidatesProducerRvaV1;
  ck3_11906::CouncilCompositionStewardCandidatesAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &MainThread;
  access.produce = &Produce;
  access.release = &Release;
  access.is_readable_span = &Readable;
  access.read_candidate_pointer = &ReadPointer;
  access.read_candidate_id = &ReadId;
  access.resolve_candidate = &Resolve;
  assert(bridge::InstallCouncilCompositionStewardCandidatesPrivateProbeV1(
      probe, environment, access));
  assert(bridge::PrepareCouncilCompositionStewardCandidatesPrivateProbeV1(
      probe, g_snapshot, 4, 3));
  assert(!bridge::PrepareCouncilCompositionStewardCandidatesPrivateProbeV1(
      probe, g_snapshot, 4, 3));

  Prime(probe, mailbox, 8);
  const auto stamp = Stamp();
  assert(bridge::ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1(
      &probe, stamp));
  assert(
      bridge::PublishCouncilCompositionStewardCandidatesPrivateProbeV1(probe));
  assert(
      !bridge::PublishCouncilCompositionStewardCandidatesPrivateProbeV1(probe));
  assert(fixture.capture_calls == 2 && fixture.producer_calls == 1 &&
         fixture.release_calls == 1);
  assert(probe.published_result.status ==
         game::CouncilCompositionStewardCandidatesStatusV1::available);
  assert(probe.published_result.candidate_count == 3);
  assert(probe.published_result.candidates[0].character_id == 10);
  assert(probe.published_result.candidates[0].native_collection_ordinal == 1);
  assert(probe.published_result.candidates[1].character_id == 20);
  assert(probe.published_result.candidates[2].character_id == 30);
  assert(probe.published_result.temporary_vector_released);
  const auto json =
      bridge::SerializeCouncilCompositionStewardCandidatesPrivateProbeV1(probe);
  assert(json.find("\"private_build\":true") != std::string::npos);
  assert(json.find("\"advertised\":false") != std::string::npos);
  assert(json.find("\"status\":\"available\"") != std::string::npos);
  assert(json.find("\"character_id\":10") != std::string::npos);
  assert(json.find("\"temporary_vector_released\":true") != std::string::npos);
  assert(json.find("\"raw_pointer_fields_persisted\":false") !=
         std::string::npos);
}

void TestDirectInvocationAndDriftFailClosed() {
  using namespace xar;
  auto fixture = MakeFixture();
  ResetPointers(fixture);
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1 binding{};
  binding.attached = true;
  bridge::CouncilCompositionStewardCandidatesPrivateProbeV1 probe{};
  assert(
      bridge::
          ConfigureCouncilCompositionStewardCandidatesPrivateProbeTransportV1(
              probe, mailbox, {}, binding));
  ck3_11906::CouncilCompositionStewardCandidatesEnvironmentV1 environment{};
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      ck3_11906::kCouncilCompositionStewardCandidatesReaderExecutableSha256V1;
  environment.module_base = 0x10000000;
  environment.producer_address =
      environment.module_base +
      ck3_11906::kCouncilCompositionStewardCandidatesProducerRvaV1;
  ck3_11906::CouncilCompositionStewardCandidatesAccessV1 access{};
  access.context = &fixture;
  access.capture_frame = &Capture;
  access.is_main_thread = &MainThread;
  access.produce = &Produce;
  access.release = &Release;
  access.is_readable_span = &Readable;
  access.read_candidate_pointer = &ReadPointer;
  access.read_candidate_id = &ReadId;
  access.resolve_candidate = &Resolve;
  assert(bridge::InstallCouncilCompositionStewardCandidatesPrivateProbeV1(
      probe, environment, access));
  assert(bridge::PrepareCouncilCompositionStewardCandidatesPrivateProbeV1(
      probe, g_snapshot, 4, 3));
  auto stamp = Stamp();
  assert(!bridge::ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1(
      &probe, stamp));
  Prime(probe, mailbox, 9);
  stamp.date_raw += 1;
  assert(bridge::ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1(
      &probe, stamp));
  assert(
      bridge::PublishCouncilCompositionStewardCandidatesPrivateProbeV1(probe));
  assert(probe.published_result.status ==
         game::CouncilCompositionStewardCandidatesStatusV1::unavailable);
  assert(probe.published_result.unavailable_reason ==
         game::CouncilCompositionStewardCandidatesFailureV1::date_drift);
  assert(fixture.producer_calls == 0 && fixture.release_calls == 0);
}

void TestMailboxPublicationPreservesPendingAndPublishesCompleted() {
  using namespace xar;
  auto fixture = MakeFixture();
  ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1 binding{};
  bridge::CouncilCompositionStewardCandidatesPrivateProbeV1 probe{};
  InstallAndPrepare(fixture, mailbox, binding, probe);

  const ck3_11906::MainThreadQueryTicketV1 ticket{17};
  probe.ticket = ticket;
  mailbox.published_sequence.store(ticket.sequence,
                                   std::memory_order_release);
  mailbox.state.store(ck3_11906::MainThreadQueryMailboxStateV1::queued,
                      std::memory_order_release);
  assert(!bridge::
              TryPublishCouncilCompositionStewardCandidatesPrivateProbeMailboxV1(
                  probe, mailbox, ticket));
  assert(mailbox.state.load(std::memory_order_acquire) ==
         ck3_11906::MainThreadQueryMailboxStateV1::queued);
  assert(!probe.result_published);

  mailbox.state.store(ck3_11906::MainThreadQueryMailboxStateV1::executing,
                      std::memory_order_release);
  assert(!bridge::
              TryPublishCouncilCompositionStewardCandidatesPrivateProbeMailboxV1(
                  probe, mailbox, ticket));
  assert(mailbox.state.load(std::memory_order_acquire) ==
         ck3_11906::MainThreadQueryMailboxStateV1::executing);
  assert(!probe.result_published);

  Prime(probe, mailbox, ticket.sequence);
  assert(bridge::ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1(
      &probe, Stamp()));
  mailbox.completed_sequence.store(ticket.sequence,
                                   std::memory_order_release);
  mailbox.state.store(ck3_11906::MainThreadQueryMailboxStateV1::completed,
                      std::memory_order_release);
  assert(bridge::
             TryPublishCouncilCompositionStewardCandidatesPrivateProbeMailboxV1(
                 probe, mailbox, ticket));
  assert(probe.result_published);
  assert(probe.published_execution_count == 1);
  assert(probe.published_result.status ==
         game::CouncilCompositionStewardCandidatesStatusV1::available);
}

void TestMailboxTerminalFailuresPublishUnavailable() {
  using namespace xar;
  auto executor_fixture = MakeFixture();
  ck3_11906::MainThreadQueryMailboxV1 executor_mailbox{};
  ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1
      executor_binding{};
  bridge::CouncilCompositionStewardCandidatesPrivateProbeV1 executor_probe{};
  InstallAndPrepare(executor_fixture, executor_mailbox, executor_binding,
                    executor_probe);
  const ck3_11906::MainThreadQueryTicketV1 executor_ticket{23};
  executor_probe.ticket = executor_ticket;
  executor_mailbox.published_sequence.store(executor_ticket.sequence,
                                            std::memory_order_release);
  executor_mailbox.completed_sequence.store(executor_ticket.sequence,
                                            std::memory_order_release);
  executor_mailbox.state.store(
      ck3_11906::MainThreadQueryMailboxStateV1::executor_failed,
      std::memory_order_release);
  assert(bridge::
             TryPublishCouncilCompositionStewardCandidatesPrivateProbeMailboxV1(
                 executor_probe, executor_mailbox, executor_ticket));
  assert(executor_probe.published_result.status ==
         game::CouncilCompositionStewardCandidatesStatusV1::unavailable);
  assert(executor_probe.published_result.unavailable_reason ==
         game::CouncilCompositionStewardCandidatesFailureV1::
             application_main_thread_required);

  auto infrastructure_fixture = MakeFixture();
  ck3_11906::MainThreadQueryMailboxV1 infrastructure_mailbox{};
  ck3_11906::CouncilCompositionStewardCandidatesBindingStateV1
      infrastructure_binding{};
  bridge::CouncilCompositionStewardCandidatesPrivateProbeV1
      infrastructure_probe{};
  InstallAndPrepare(infrastructure_fixture, infrastructure_mailbox,
                    infrastructure_binding, infrastructure_probe);
  const ck3_11906::MainThreadQueryTicketV1 infrastructure_ticket{29};
  infrastructure_probe.ticket = infrastructure_ticket;
  infrastructure_mailbox.published_sequence.store(
      infrastructure_ticket.sequence, std::memory_order_release);
  infrastructure_mailbox.completed_sequence.store(
      infrastructure_ticket.sequence, std::memory_order_release);
  infrastructure_mailbox.state.store(
      ck3_11906::MainThreadQueryMailboxStateV1::infrastructure_failed,
      std::memory_order_release);
  assert(bridge::
             TryPublishCouncilCompositionStewardCandidatesPrivateProbeMailboxV1(
                 infrastructure_probe, infrastructure_mailbox,
                 infrastructure_ticket));
  assert(infrastructure_probe.published_result.status ==
         game::CouncilCompositionStewardCandidatesStatusV1::unavailable);
  assert(infrastructure_probe.published_result.unavailable_reason ==
         game::CouncilCompositionStewardCandidatesFailureV1::
             frame_capture_failed);
}

std::string ReadFile(const char *path) {
  std::ifstream input(path, std::ios::binary);
  assert(input);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

void TestPrivateBridgeSourceContract(int argc, char **argv) {
  assert(argc == 5);
  const auto bridge = ReadFile(argv[1]);
  const auto cmake = ReadFile(argv[2]);
  const auto mailbox_header = ReadFile(argv[3]);
  const auto mailbox_source = ReadFile(argv[4]);
  constexpr std::string_view option =
      "XAR_CK3_ENABLE_G2_COUNCIL_COMPOSITION_STEWARD_CANDIDATES_PRIVATE_"
      "PROBE_V1";
  assert(cmake.find(option) != std::string::npos);
  assert(cmake.find(
             "Run one private exact-build paused steward-candidate query") !=
         std::string::npos);
  assert(bridge.find("BindCouncilCompositionStewardCandidatesV1") !=
         std::string::npos);
  assert(
      bridge.find("ExecuteCouncilCompositionStewardCandidatesPrivateProbeV1") !=
      std::string::npos);
  const auto drive_begin = bridge.find(
      "void DriveCouncilCompositionStewardCandidatesPrivateProbeV1(");
  assert(drive_begin != std::string::npos);
  const auto drive_end = bridge.find("\n#endif", drive_begin);
  assert(drive_end != std::string::npos);
  const auto drive = bridge.substr(drive_begin, drive_end - drive_begin);
  assert(drive.find(
             "TryPublishCouncilCompositionStewardCandidatesPrivateProbeMailboxV1") !=
         std::string::npos);
  assert(drive.find("ReclaimMainThreadQueryV1") != std::string::npos);
  assert(drive.find("WaitForMainThreadQueryV1") == std::string::npos);
  assert(mailbox_header.find("permitted_executor_tritrigintary") !=
         std::string::npos);
  assert(mailbox_source.find("permitted_executor_tritrigintary") !=
         std::string::npos);
  const auto hello = bridge.find("std::string HelloFrame");
  const auto heartbeat = bridge.find("std::string HeartbeatFrame", hello);
  assert(hello != std::string::npos && heartbeat != std::string::npos);
  assert(
      bridge.substr(hello, heartbeat - hello)
          .find("g2_council_composition_steward_candidates_private_probe_v1") ==
      std::string::npos);
}

} // namespace

namespace xar::ck3_11906 {

bool ReadSnapshot(const Bindings &, game::Snapshot &output) noexcept {
  output = g_snapshot;
  return true;
}

} // namespace xar::ck3_11906

int main(int argc, char **argv) {
  g_snapshot.date_raw = 53'178'264;
  g_snapshot.paused = true;
  g_snapshot.map_ready = true;
  g_snapshot.has_played_character = true;
  g_snapshot.played_character_alive = true;
  g_snapshot.played_character_id = 29'829;
  TestOnePausedSameFrameQuery();
  TestDirectInvocationAndDriftFailClosed();
  TestMailboxPublicationPreservesPendingAndPublishesCompleted();
  TestMailboxTerminalFailuresPublishUnavailable();
  TestPrivateBridgeSourceContract(argc, argv);
  return 0;
}
