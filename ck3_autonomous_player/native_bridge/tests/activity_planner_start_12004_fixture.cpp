#include "xar_bridge/activity_feast_stage5_start_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_start.hpp"
#include "xar_bridge/ck3_12002_feast_planner_native.hpp"

#include <windows.h>

#include <array>
#include <cstring>

namespace {

constexpr std::string_view kActualSha =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::uintptr_t kModuleBase = 0x10000000;
constexpr std::uintptr_t kPlanner = 0x20000000;
constexpr std::uintptr_t kMappedCommitRva = 0x11B8D70;
// Parent's paired final-CanStart body proof closes this independent literal.
constexpr std::uintptr_t kMappedCanStartRva = 0x11B8650;

struct Fixture {
  xar::game::Snapshot snapshot{};
  xar::bridge::ActivityFeastStage5StartSnapshotV1 start{};
  std::string_view actual_sha = kActualSha;
  std::array<std::uintptr_t, 2> guard_addresses{};
  std::uint32_t guard_reads = 0;
  std::uint32_t captures = 0;
  std::uint32_t commits = 0;
};

bool ReadSnapshot(void *opaque, xar::game::Snapshot &output) noexcept {
  output = static_cast<Fixture *>(opaque)->snapshot;
  return true;
}

bool ReadGuards(void *opaque, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (fixture.guard_reads >= fixture.guard_addresses.size()) return false;
  if (address == kModuleBase + kMappedCommitRva &&
      size == xar::ck3_12002::kFeastCommitPrefix.size()) {
    std::memcpy(output, xar::ck3_12002::kFeastCommitPrefix.data(), size);
  } else if (address == kModuleBase + kMappedCanStartRva &&
             size == xar::ck3_12002::kFeastFinalCanStartPrefix.size()) {
    std::memcpy(output, xar::ck3_12002::kFeastFinalCanStartPrefix.data(), size);
  } else {
    return false;
  }
  fixture.guard_addresses[fixture.guard_reads++] = address;
  return true;
}

bool Capture(void *opaque,
             const xar::bridge::ActivityHostedIdentityFrameV1 &frame,
             xar::bridge::ActivityFeastStage5StartSnapshotV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (frame != fixture.start.frame || fixture.actual_sha != kActualSha)
    return false;
  ++fixture.captures;
  output = fixture.start;
  return true;
}

bool Commit(void *opaque, std::uintptr_t base,
            std::uintptr_t planner) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  if (fixture.actual_sha != kActualSha || base != kModuleBase ||
      planner != kPlanner || fixture.captures != 2)
    return false;
  ++fixture.commits;
  return true;
}

} // namespace

// The parent combines this single new case with other Activity4 production
// readers in one target. No native callback or game process is invoked here.
bool RunActivityPlannerStart12004Fixture() {
  using namespace xar;
  Fixture fixture{};
  fixture.snapshot.date_raw = 53238096;
  fixture.snapshot.played_character_id = 29829;
  fixture.snapshot.paused = true;
  fixture.snapshot.map_ready = true;
  fixture.snapshot.has_played_character = true;
  fixture.snapshot.played_character_alive = true;
  ck3_12002::ActivityPlanner12002NativeV1 native{};
  if (!ck3_12002::BindActivityPlanner12002V1(
          native, kModuleBase, bridge::kActivityPlanner12002ExeSha256V1,
          &fixture, &ReadSnapshot, nullptr, nullptr, 17,
          GetCurrentThreadId(), 0x30000000))
    return false;
  if (!ck3_12002::BindActivityPlanner12002V1(
          native, kModuleBase, kActualSha, &fixture, &ReadSnapshot,
          nullptr, nullptr, 17, GetCurrentThreadId(), 0x30000000))
    return false;
  const auto diagnostic =
      ck3_12002::BuildActivityPlanner12002DiagEnvironmentV1(native);
  bridge::ActivityPlannerDiagFrameV1 frame{};
  if (diagnostic.admitted_executable_sha256 != kActualSha ||
      !bridge::IsActivityPlannerSupportedBuildV1(diagnostic) ||
      diagnostic.read_frame == nullptr ||
      !diagnostic.read_frame(diagnostic.context, frame) ||
      frame.revision != 17 || frame.date_raw != fixture.snapshot.date_raw ||
      frame.actor_character_id != 29829 || !frame.paused || !frame.map_ready ||
      !frame.actor_alive)
    return false;

  auto &start = fixture.start;
  start.frame = {frame.revision, frame.date_raw, frame.actor_character_id,
                 true, true, true, true};
  start.planner = kPlanner;
  start.normal_cost_refresh_sequence = 9;
  start.feast_type_verified = true;
  start.generic_option_verified = true;
  start.final_can_start_observed = true;
  start.final_can_start = true;
  start.four_costs_observed = true;
  start.cost_resource_indices = {0, 1, 2, 3};
  start.cost_raw = {100000, 0, 0, 0};
  start.balances.frame = start.frame;
  start.balances.available = {true, false, false, false};
  start.balances.raw = {900000, 0, 0, 0};
  start.hosted_identities_observed = true;
  start.selected_guests.status = bridge::ActivityFeastGuestJoinStatusV1::observed;
  start.selected_guests.frame = frame;
  start.selected_guests.normal_refresh_sequence = start.normal_cost_refresh_sequence;
  start.selected_guests.arrival_time_observed = true;
  start.selected_guests.selected_nonhost_count = 1;
  start.selected_guests.positive_join_count = 1;
  start.selected_guests.timely_positive_join_count = 1;

  bridge::ActivityFeastStage5StartEnvironmentV1 environment{};
  environment.enabled = true;
  environment.admitted_executable_sha256 = kActualSha;
  environment.module_base = kModuleBase;
  environment.context = &fixture;
  environment.read_memory = &ReadGuards;
  environment.capture = &Capture;
  environment.invoke_commit = &Commit;
  bridge::ActivityFeastStage5StartRequestV1 request{};
  request.expected = start.frame;
  request.policy_approved = true;
  request.reserve_raw = {200000, 0, 0, 0};
  const auto result = bridge::StartActivityFeastStage5V1(environment, request);
  return result.status == bridge::ActivityFeastStage5StartStatusV1::submitted_pending &&
         result.invoked && result.before.frame == start.frame &&
         result.before.planner == kPlanner && fixture.guard_reads == 2 &&
         fixture.guard_addresses[0] == kModuleBase + kMappedCommitRva &&
         fixture.guard_addresses[1] == kModuleBase + kMappedCanStartRva &&
         fixture.captures == 2 && fixture.commits == 1;
}
