#include "xar_bridge/military_preparation_summary_v1_private_probe.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <array>
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>

namespace {

using namespace xar::bridge;

struct Fixture {
  MilitaryPreparationFrameIdentityV1 frame{42, 12345, 305419896, 0, true};
  std::array<std::int64_t, kMilitaryPreparationSummaryFieldCountV1> values{
      100000000, 120000000, 500000, 700000, 18000,
      15000, 40000, 60000, 40000, 10000};
  std::size_t definition = 0;
};

bool ReadFrame(void *context, MilitaryPreparationFrameIdentityV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}

bool Begin(void *context, std::int32_t character_id, void *&session) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  session = character_id == fixture.frame.played_character_id ? &fixture : nullptr;
  return session != nullptr;
}

bool End(void *context, void *session) noexcept { return context == session; }

bool Resolve(void *context, std::string_view key,
             const void *&definition) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  for (std::size_t index = 0;
       index < kMilitaryPreparationSummaryDefinitionKeysV1.size(); ++index) {
    if (key == kMilitaryPreparationSummaryDefinitionKeysV1[index]) {
      fixture.definition = index;
      definition = &fixture.definition;
      return true;
    }
  }
  definition = nullptr;
  return false;
}

bool Valid(void *, const void *definition) noexcept {
  return definition != nullptr;
}

bool Evaluate(void *context, const void *definition, void *session,
              std::int64_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (session != &fixture || definition != &fixture.definition ||
      fixture.definition >= fixture.values.size()) {
    return false;
  }
  output = fixture.values[fixture.definition];
  return true;
}

MilitaryPreparationSummaryEnvironmentV1 Environment(Fixture &fixture) {
  MilitaryPreparationSummaryEnvironmentV1 environment{};
  environment.observer_enabled = true;
  environment.exact_build_admitted = true;
  environment.admitted_executable_sha256 =
      kMilitaryPreparationSummaryExecutableSha256V1;
  environment.offline_fixture = true;
  environment.callback_context = &fixture;
  environment.read_frame = &ReadFrame;
  environment.begin_session = &Begin;
  environment.end_session = &End;
  environment.resolve_definition = &Resolve;
  environment.definition_is_valid = &Valid;
  environment.evaluate_fixed = &Evaluate;
  return environment;
}

void TestDefaultOffAndOneShotAvailablePublication() {
  Fixture fixture{};
  auto environment = Environment(fixture);
  environment.observer_enabled = false;
  MilitaryPreparationSummaryPrivateProbeV1 rejected{};
  assert(!InstallMilitaryPreparationSummaryPrivateProbeV1(rejected,
                                                           environment));
  assert(!rejected.installed);

  environment.observer_enabled = true;
  MilitaryPreparationSummaryPrivateProbeV1 probe{};
  assert(InstallMilitaryPreparationSummaryPrivateProbeV1(probe,
                                                          environment));
  assert(PrepareMilitaryPreparationSummaryPrivateProbeV1(
      probe, fixture.frame, fixture.frame.snapshot_revision));
  assert(!PrepareMilitaryPreparationSummaryPrivateProbeV1(
      probe, fixture.frame, fixture.frame.snapshot_revision));

  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.thread_id = 77;
  stamp.date_raw = fixture.frame.date_raw;
  stamp.paused = true;
  assert(ExecuteMilitaryPreparationSummaryPrivateProbeV1(&probe, stamp));
  assert(PublishMilitaryPreparationSummaryPrivateProbeV1(probe));
  assert(!PublishMilitaryPreparationSummaryPrivateProbeV1(probe));
  assert(probe.published_result.status ==
         MilitaryPreparationSummaryStatusV1::available);
  assert(probe.published_result.observation_ready);
  assert(probe.published_result.values.current_military_strength_raw ==
         fixture.values[0]);

  const std::string json =
      SerializeMilitaryPreparationSummaryPrivateProbeV1(probe);
  assert(json.find("\"private_build\":true") != std::string::npos);
  assert(json.find("\"advertised\":false") != std::string::npos);
  assert(json.find("\"result_published\":true") != std::string::npos);
  assert(json.find("\"status\":\"available\"") != std::string::npos);
  assert(json.find("\"raw_pointer_fields_persisted\":false") !=
         std::string::npos);
}

void TestStampDriftPublishesUnavailable() {
  Fixture fixture{};
  MilitaryPreparationSummaryPrivateProbeV1 probe{};
  assert(InstallMilitaryPreparationSummaryPrivateProbeV1(
      probe, Environment(fixture)));
  assert(PrepareMilitaryPreparationSummaryPrivateProbeV1(
      probe, fixture.frame, fixture.frame.snapshot_revision));
  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.thread_id = 77;
  stamp.date_raw = fixture.frame.date_raw + 1;
  stamp.paused = true;
  assert(ExecuteMilitaryPreparationSummaryPrivateProbeV1(&probe, stamp));
  assert(PublishMilitaryPreparationSummaryPrivateProbeV1(probe));
  assert(probe.published_result.status ==
         MilitaryPreparationSummaryStatusV1::unavailable);
  assert(probe.published_result.failure_flags ==
         military_preparation_summary_failure_frame_changed);
}

void TestMailboxPublicationDoesNotCancelQueuedWork() {
  Fixture fixture{};
  MilitaryPreparationSummaryPrivateProbeV1 probe{};
  assert(InstallMilitaryPreparationSummaryPrivateProbeV1(
      probe, Environment(fixture)));
  assert(PrepareMilitaryPreparationSummaryPrivateProbeV1(
      probe, fixture.frame, fixture.frame.snapshot_revision));

  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  const xar::ck3_11906::MainThreadQueryTicketV1 ticket{17};
  mailbox.published_sequence.store(ticket.sequence,
                                   std::memory_order_release);
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::queued,
      std::memory_order_release);
  assert(!TryPublishMilitaryPreparationSummaryPrivateProbeMailboxV1(
      probe, mailbox, ticket));
  assert(!probe.result_published);

  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::executing,
      std::memory_order_release);
  assert(!TryPublishMilitaryPreparationSummaryPrivateProbeMailboxV1(
      probe, mailbox, ticket));
  assert(!probe.result_published);

  xar::ck3_11906::MainThreadExecutionStampV1 stamp{};
  stamp.thread_id = 77;
  stamp.date_raw = fixture.frame.date_raw;
  stamp.paused = true;
  assert(ExecuteMilitaryPreparationSummaryPrivateProbeV1(&probe, stamp));
  mailbox.completed_sequence.store(ticket.sequence,
                                   std::memory_order_release);
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::completed,
      std::memory_order_release);
  assert(TryPublishMilitaryPreparationSummaryPrivateProbeMailboxV1(
      probe, mailbox, ticket));
  assert(probe.result_published);
  assert(probe.published_execution_count == 1);
  assert(probe.published_result.status ==
         MilitaryPreparationSummaryStatusV1::available);
}

void TestMailboxTerminalFailuresRemainUnavailable() {
  Fixture fixture{};
  MilitaryPreparationSummaryPrivateProbeV1 cancelled{};
  assert(InstallMilitaryPreparationSummaryPrivateProbeV1(
      cancelled, Environment(fixture)));
  assert(PrepareMilitaryPreparationSummaryPrivateProbeV1(
      cancelled, fixture.frame, fixture.frame.snapshot_revision));
  xar::ck3_11906::MainThreadQueryMailboxV1 mailbox{};
  const xar::ck3_11906::MainThreadQueryTicketV1 ticket{23};
  mailbox.published_sequence.store(ticket.sequence,
                                   std::memory_order_release);
  mailbox.completed_sequence.store(ticket.sequence,
                                   std::memory_order_release);
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::cancelled,
      std::memory_order_release);
  assert(TryPublishMilitaryPreparationSummaryPrivateProbeMailboxV1(
      cancelled, mailbox, ticket));
  assert(cancelled.published_result.status ==
         MilitaryPreparationSummaryStatusV1::unavailable);
  assert(cancelled.published_result.failure_flags ==
         military_preparation_summary_failure_application_main);

  MilitaryPreparationSummaryPrivateProbeV1 infrastructure{};
  assert(InstallMilitaryPreparationSummaryPrivateProbeV1(
      infrastructure, Environment(fixture)));
  assert(PrepareMilitaryPreparationSummaryPrivateProbeV1(
      infrastructure, fixture.frame, fixture.frame.snapshot_revision));
  mailbox.state.store(
      xar::ck3_11906::MainThreadQueryMailboxStateV1::infrastructure_failed,
      std::memory_order_release);
  assert(TryPublishMilitaryPreparationSummaryPrivateProbeMailboxV1(
      infrastructure, mailbox, ticket));
  assert(infrastructure.published_result.status ==
         MilitaryPreparationSummaryStatusV1::unavailable);
  assert(infrastructure.published_result.failure_flags ==
         military_preparation_summary_failure_frame_changed);
}

std::string ReadFile(const char *path) {
  std::ifstream input(path, std::ios::binary);
  assert(input);
  return {std::istreambuf_iterator<char>(input),
          std::istreambuf_iterator<char>()};
}

void TestPrivateBridgeSourceContract(int argc, char **argv) {
  assert(argc == 5);
  const std::string bridge = ReadFile(argv[1]);
  const std::string cmake = ReadFile(argv[2]);
  const std::string mailbox_header = ReadFile(argv[3]);
  const std::string mailbox_source = ReadFile(argv[4]);
  assert(cmake.find(
             "XAR_CK3_ENABLE_G2_MILITARY_PREPARATION_SUMMARY_PRIVATE_PROBE_V1") !=
         std::string::npos);
  assert(cmake.find(
             "Run one private exact-build paused military-preparation summary probe") !=
         std::string::npos);
  assert(bridge.find(
             "g2_military_preparation_summary_v1_private_probe") !=
         std::string::npos);
  assert(bridge.find(
             "ExecuteMilitaryPreparationSummaryPrivateProbeV1") !=
         std::string::npos);
  assert(mailbox_header.find("permitted_executor_duotrigintary") !=
         std::string::npos);
  assert(mailbox_source.find("permitted_executor_duotrigintary") !=
         std::string::npos);
}

} // namespace

int main(int argc, char **argv) {
  TestDefaultOffAndOneShotAvailablePublication();
  TestStampDriftPublishesUnavailable();
  TestMailboxPublicationDoesNotCancelQueuedWork();
  TestMailboxTerminalFailuresRemainUnavailable();
  TestPrivateBridgeSourceContract(argc, argv);
  return 0;
}
