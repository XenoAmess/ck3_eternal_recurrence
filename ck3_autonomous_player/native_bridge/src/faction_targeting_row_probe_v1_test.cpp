#include "xar_bridge/faction_targeting_row_probe_v1.hpp"
#include "xar_bridge/faction_targeting_row_probe_v1_serializer.hpp"

#if defined(NDEBUG)
#undef NDEBUG
#endif

#include <cassert>
#include <cstddef>
#include <cstdint>
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

} // namespace

int main() {
  static_assert(!xar::bridge::kFactionTargetingRowProbePublicByDefaultV1);
  TestReady();
  TestKnownEmpty();
  TestUnavailable();
  TestStaleBinding();
  TestOddGeneration();
  TestUnpausedBinding();
  TestObserverFlagsPropagate();
  TestZeroMemberIdentityRejected();
  return 0;
}
