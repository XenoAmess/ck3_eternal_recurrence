#include "xar_bridge/faction_targeting_row_probe_v1.hpp"
#include "xar_bridge/faction_targeting_row_probe_v1_serializer.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>

namespace {

using xar::bridge::FactionTargetingRowObserverDiagnosticsV1;
using xar::bridge::FactionTargetingRowProbeBindingV1;
using xar::bridge::FactionTargetingRowProbeTerminalV1;

constexpr FactionTargetingRowProbeBindingV1 kBinding{
    true, 42, 412, 777, 29829};

FactionTargetingRowObserverDiagnosticsV1 BaseObserver(
    std::uint32_t faction_count) {
  FactionTargetingRowObserverDiagnosticsV1 observer{};
  observer.installed = true;
  observer.observation.published_generation = 2;
  observer.observation.last_proof_epoch = kBinding.proof_epoch;
  observer.observation.last_snapshot_revision = kBinding.snapshot_revision;
  observer.observation.last_date_raw = kBinding.date_raw;
  observer.observation.last_player_character_id =
      kBinding.player_character_id;
  observer.observation.last_campaign_root_targeting_faction_count =
      static_cast<std::int32_t>(faction_count);
  observer.observation.last_faction_count = faction_count;
  return observer;
}

FactionTargetingRowObserverDiagnosticsV1 ReadyObserver() {
  auto observer = BaseObserver(2);
  auto &capture = observer.observation;
  capture.last_faction_ids[0] = 7;
  capture.last_faction_ids[1] = 42;
  capture.last_target_character_ids[0] = kBinding.player_character_id;
  capture.last_target_character_ids[1] = kBinding.player_character_id;
  capture.last_leader_present[1] = 1;
  capture.last_leader_character_ids[1] = 4001;
  capture.last_leader_present_in_character_members[1] = 1;
  capture.last_character_member_counts[1] = 2;
  const auto member_base =
      xar::bridge::
          kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
  capture.last_character_member_ids[member_base] = 4001;
  capture.last_character_member_ids[member_base + 1] = 4002;
  return observer;
}

void TestReady() {
  const auto result = xar::bridge::ProbeFactionTargetingRowsV1(
      ReadyObserver(), kBinding);
  assert(result.terminal == FactionTargetingRowProbeTerminalV1::ready);
  assert(result.unavailable_reasons == 0);
  assert(result.observer_failure_flags == 0);
  assert(result.published_generation == 2);
  assert(result.observed_binding.snapshot_revision ==
         kBinding.snapshot_revision);
  assert(result.faction_count == 2);
  assert(result.factions[0].faction_id == 7);
  assert(!result.factions[0].leader_present);
  assert(result.factions[0].character_member_count == 0);
  assert(result.factions[1].faction_id == 42);
  assert(result.factions[1].leader_present);
  assert(result.factions[1].leader_character_id == 4001);
  assert(result.factions[1].leader_present_in_character_members);
  assert(result.factions[1].character_member_count == 2);
  assert(result.factions[1].character_member_ids[0] == 4001);
  assert(result.factions[1].character_member_ids[1] == 4002);
  assert(xar::bridge::FactionTargetingRowProbeTerminalNameV1(
             result.terminal) == "ready");
  const std::string wire =
      xar::bridge::SerializeFactionTargetingRowProbeV1(result);
  assert(wire.find("\"terminal\":\"ready\"") != std::string::npos);
  assert(wire.find("\"raw_pointers_persisted\":false") !=
         std::string::npos);
  assert(wire.find("\"leader_character_id\":null") !=
         std::string::npos);
  assert(wire.find("\"leader_character_id\":4001") !=
         std::string::npos);
  assert(wire.find("\"character_member_ids\":[4001,4002]") !=
         std::string::npos);
}

void TestKnownEmpty() {
  const auto result = xar::bridge::ProbeFactionTargetingRowsV1(
      BaseObserver(0), kBinding);
  assert(result.terminal == FactionTargetingRowProbeTerminalV1::known_empty);
  assert(result.unavailable_reasons == 0);
  assert(result.faction_count == 0);
  assert(xar::bridge::FactionTargetingRowProbeTerminalNameV1(
             result.terminal) == "known-empty");
  const std::string wire =
      xar::bridge::SerializeFactionTargetingRowProbeV1(result);
  assert(wire.find("\"terminal\":\"known-empty\"") !=
         std::string::npos);
  assert(wire.find("\"faction_count\":0,\"factions\":[]") !=
         std::string::npos);
}

void TestUnavailable() {
  FactionTargetingRowObserverDiagnosticsV1 observer{};
  const auto result = xar::bridge::ProbeFactionTargetingRowsV1(
      observer, kBinding);
  assert(result.terminal == FactionTargetingRowProbeTerminalV1::unavailable);
  assert((result.unavailable_reasons &
          xar::bridge::
              faction_targeting_row_probe_unavailable_observer_not_installed) !=
         0);
  assert((result.unavailable_reasons &
          xar::bridge::faction_targeting_row_probe_unavailable_no_generation) !=
         0);
  const std::string wire =
      xar::bridge::SerializeFactionTargetingRowProbeV1(result);
  assert(wire.find("\"terminal\":\"unavailable\"") !=
         std::string::npos);
  assert(wire.find("\"faction_count\":0,\"factions\":[]") !=
         std::string::npos);
}

void TestStaleBinding() {
  auto required = kBinding;
  ++required.snapshot_revision;
  const auto result = xar::bridge::ProbeFactionTargetingRowsV1(
      ReadyObserver(), required);
  assert(result.terminal == FactionTargetingRowProbeTerminalV1::unavailable);
  assert((result.unavailable_reasons &
          xar::bridge::faction_targeting_row_probe_unavailable_stale_binding) !=
         0);
  assert(result.faction_count == 0);
}

void TestOddGeneration() {
  auto observer = ReadyObserver();
  observer.observation.published_generation = 3;
  const auto result = xar::bridge::ProbeFactionTargetingRowsV1(
      observer, kBinding);
  assert(result.terminal == FactionTargetingRowProbeTerminalV1::unavailable);
  assert((result.unavailable_reasons &
          xar::bridge::faction_targeting_row_probe_unavailable_odd_generation) !=
         0);
}

void TestUnpausedBinding() {
  auto required = kBinding;
  required.paused = false;
  const auto result = xar::bridge::ProbeFactionTargetingRowsV1(
      ReadyObserver(), required);
  assert(result.terminal == FactionTargetingRowProbeTerminalV1::unavailable);
  assert((result.unavailable_reasons &
          xar::bridge::faction_targeting_row_probe_unavailable_unpaused) !=
         0);
}

void TestObserverFlagsPropagate() {
  auto observer = ReadyObserver();
  observer.failure_flags =
      xar::bridge::faction_targeting_row_observer_failure_member_identity |
      xar::bridge::faction_targeting_row_observer_failure_member_ownership;
  const auto result = xar::bridge::ProbeFactionTargetingRowsV1(
      observer, kBinding);
  assert(result.terminal == FactionTargetingRowProbeTerminalV1::unavailable);
  assert((result.unavailable_reasons &
          xar::bridge::faction_targeting_row_probe_unavailable_observer_failure) !=
         0);
  assert(result.observer_failure_flags == observer.failure_flags);
}

void TestZeroMemberIdentityRejected() {
  auto observer = ReadyObserver();
  const auto member_base =
      xar::bridge::
          kFactionTargetingRowObserverMaximumCharacterMembersPerFactionV1;
  observer.observation.last_character_member_ids[member_base] = 0;
  const auto result = xar::bridge::ProbeFactionTargetingRowsV1(
      observer, kBinding);
  assert(result.terminal == FactionTargetingRowProbeTerminalV1::unavailable);
  assert((result.unavailable_reasons &
          xar::bridge::faction_targeting_row_probe_unavailable_invalid_capture) !=
         0);
  assert(result.faction_count == 0);
}

std::string ReadText(const char *path) {
  std::ifstream input(path, std::ios::binary);
  assert(input.good());
  return std::string(std::istreambuf_iterator<char>(input),
                     std::istreambuf_iterator<char>());
}

void TestAsyncPrivateBridgeSourceContract(int argc, char **argv) {
  if (argc == 1) {
    return;
  }
  assert(argc == 6);
  const auto bridge = ReadText(argv[1]);
  const auto cmake = ReadText(argv[2]);
  const auto mailbox_header = ReadText(argv[3]);
  const auto mailbox_source = ReadText(argv[4]);
  const auto async_fixture = ReadText(argv[5]);

  const auto driver_begin = bridge.find(
      "void DriveFactionTargetingRowAsyncPrivateProbeV1(");
  assert(driver_begin != std::string::npos);
  const auto driver_end = bridge.find(
      "#if defined(XAR_CK3_ENABLE_G2_COUNCIL_COMPOSITION", driver_begin);
  assert(driver_end != std::string::npos);
  const auto driver = bridge.substr(driver_begin, driver_end - driver_begin);
  assert(driver.find("TrySubmitMainThreadQueryV1") != std::string::npos);
  assert(driver.find("ExecuteCampaignRootContextMailboxQueryV1") !=
         std::string::npos);
  assert(driver.find("WaitForMainThreadQueryV1") == std::string::npos);

  const auto queued = driver.find("MainThreadQueryMailboxStateV1::queued");
  const auto queued_return = driver.find("return;", queued);
  const auto executing =
      driver.find("MainThreadQueryMailboxStateV1::executing", queued_return);
  const auto executing_return = driver.find("return;", executing);
  const auto reclaim = driver.find("ReclaimMainThreadQueryV1", executing_return);
  assert(queued != std::string::npos && queued_return != std::string::npos);
  assert(executing != std::string::npos &&
         executing_return != std::string::npos);
  assert(reclaim != std::string::npos);
  assert(queued < queued_return && queued_return < executing &&
         executing < executing_return && executing_return < reclaim);
  assert(driver.find("PublishFactionTargetingRowAdmissionV1(query)") !=
         std::string::npos);
  assert(driver.find("awaiting_observer") != std::string::npos);
  assert(driver.find("PublishFactionTargetingRowTerminalV1(observer)") !=
         std::string::npos);

  const auto startup = bridge.find("XarCk3BridgePrepareStartup(LPVOID)");
  assert(startup != std::string::npos);
  const auto install = bridge.find("InstallFactionTargetingRowObserverV1", startup);
  assert(install != std::string::npos);
  assert(bridge.find("primary_thread_suspended", startup) < install);
  assert(bridge.find("ReadFactionTargetingRowCaptureAdmissionV1", startup) <
         install);

  assert(bridge.find("\\\"g2_faction_targeting_row_probe_v1_async\\\"") !=
         std::string::npos);
  assert(bridge.find("\\\"advertised\\\":false") != std::string::npos);
  assert(bridge.find("\\\"terminal_published\\\"") != std::string::npos);
  assert(bridge.find("\\\"terminal_result\\\"") != std::string::npos);
  assert(bridge.find("result += \"null\"") != std::string::npos);

  assert(cmake.find(
             "XAR_CK3_ENABLE_G2_FACTION_TARGETING_ROW_ASYNC_PRIVATE_PROBE_V1") !=
         std::string::npos);
  assert(cmake.find("src/faction_targeting_row_observer_v1.cpp") !=
         std::string::npos);
  assert(cmake.find("src/faction_targeting_row_probe_v1.cpp") !=
         std::string::npos);
  assert(mailbox_header.find("permitted_executor_nonary") !=
         std::string::npos);
  assert(mailbox_source.find("executor != mailbox.permitted_executor_nonary") !=
         std::string::npos);
  assert(async_fixture.find(
             "xar.g2.faction-targeting-row-async-glue.source-contract.v1") !=
         std::string::npos);
  assert(async_fixture.find(
             "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86") !=
         std::string::npos);
  assert(async_fixture.find("\"queued_is_terminal\": false") !=
         std::string::npos);
  assert(async_fixture.find("\"executing_is_terminal\": false") !=
         std::string::npos);
  assert(async_fixture.find("\"queued_or_executing_reclaimed\": false") !=
         std::string::npos);
  assert(async_fixture.find("\"blocking_wait_used\": false") !=
         std::string::npos);
  assert(async_fixture.find(
             "capture_faction_targeting_row_probe_v1_paused_live_heartbeat") !=
         std::string::npos);
}

} // namespace

int main(int argc, char **argv) {
  static_assert(!xar::bridge::kFactionTargetingRowProbePublicByDefaultV1);
  TestReady();
  TestKnownEmpty();
  TestUnavailable();
  TestStaleBinding();
  TestOddGeneration();
  TestUnpausedBinding();
  TestObserverFlagsPropagate();
  TestZeroMemberIdentityRejected();
  TestAsyncPrivateBridgeSourceContract(argc, argv);
  return 0;
}
