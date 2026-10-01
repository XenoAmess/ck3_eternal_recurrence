#include "xar_bridge/activity_feast_stage5_start_v1.hpp"
#include "xar_bridge/ck3_12002_activity_feast_start.hpp"

#include <array>
#include <cstring>
#include <limits>

namespace xar::bridge {
namespace {

bool Match(const ActivityFeastStage5StartEnvironmentV1 &environment,
           std::uintptr_t rva, const std::uint8_t *expected,
           std::size_t size) noexcept {
  if (rva > (std::numeric_limits<std::uintptr_t>::max)() -
                environment.module_base || environment.read_memory == nullptr)
    return false;
  std::array<std::uint8_t, 16> actual{};
  return size <= actual.size() &&
         environment.read_memory(environment.context,
                                 environment.module_base + rva, actual.data(),
                                 size) &&
         std::memcmp(actual.data(), expected, size) == 0;
}

bool Abi(const ActivityFeastStage5StartEnvironmentV1 &environment) noexcept {
  constexpr std::array<std::uint8_t, 13> kCommit{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x57, 0x48, 0x81, 0xEC, 0x10, 0x0A,
      0x00, 0x00};
  constexpr std::array<std::uint8_t, 7> kCanStart{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89};
  if (environment.admitted_executable_sha256 ==
      ck3_12002::kFeastExecutableSha256)
    return environment.enabled && environment.module_base != 0 &&
           environment.capture != nullptr &&
           Match(environment, ck3_12002::kFeastCommitRva,
                 ck3_12002::kFeastCommitPrefix.data(),
                 ck3_12002::kFeastCommitPrefix.size()) &&
           Match(environment, ck3_12002::kFeastFinalCanStartRva,
                 ck3_12002::kFeastFinalCanStartPrefix.data(),
                 ck3_12002::kFeastFinalCanStartPrefix.size());
  return environment.enabled && environment.module_base != 0 &&
         environment.admitted_executable_sha256 ==
             kActivityHostedIdentityExeSha256V1 &&
         environment.capture != nullptr &&
         Match(environment, 0x10B13F0, kCommit.data(), kCommit.size()) &&
         Match(environment, 0x10B0DA0, kCanStart.data(), kCanStart.size());
}

bool Valid(const ActivityFeastStage5StartSnapshotV1 &snapshot,
           const ActivityFeastStage5StartRequestV1 &request) noexcept {
  if (snapshot.frame != request.expected ||
      snapshot.balances.frame != request.expected || snapshot.planner == 0 ||
      snapshot.normal_cost_refresh_sequence == 0 ||
      !snapshot.feast_type_verified || !snapshot.generic_option_verified ||
      !snapshot.final_can_start_observed || !snapshot.final_can_start ||
      !snapshot.four_costs_observed ||
      !IsActivityFeastSelectedGuestRouteQualifiedV1(snapshot) ||
      !snapshot.hosted_identities_observed ||
      snapshot.hosted_count > snapshot.hosted.size())
    return false;
  for (std::size_t index = 0; index < 4; ++index) {
    const auto cost = snapshot.cost_raw[index];
    const auto reserve = request.reserve_raw[index];
    if (snapshot.cost_resource_indices[index] >= 10 || cost < 0 ||
        reserve < 0)
      return false;
    // An observed native zero cost requires no balance for that resource.
    // Unknown positive-cost balances are never treated as zero.
    if (cost == 0) continue;
    if (!snapshot.balances.available[index] ||
        cost > (std::numeric_limits<std::int64_t>::max)() - reserve ||
        snapshot.balances.raw[index] < cost + reserve)
      return false;
  }
  for (std::size_t a = 0; a < 4; ++a)
    for (std::size_t b = a + 1; b < 4; ++b)
      if (snapshot.cost_resource_indices[a] ==
          snapshot.cost_resource_indices[b])
        return false;
  return true;
}

bool Same(const ActivityFeastStage5StartSnapshotV1 &a,
          const ActivityFeastStage5StartSnapshotV1 &b) noexcept {
  if (a.frame != b.frame || a.planner != b.planner ||
      a.normal_cost_refresh_sequence != b.normal_cost_refresh_sequence ||
      a.feast_type_verified != b.feast_type_verified ||
      a.generic_option_verified != b.generic_option_verified ||
      a.final_can_start_observed != b.final_can_start_observed ||
      a.final_can_start != b.final_can_start ||
      a.four_costs_observed != b.four_costs_observed ||
      a.cost_resource_indices != b.cost_resource_indices ||
      a.cost_raw != b.cost_raw ||
      a.balances.frame != b.balances.frame ||
      a.balances.available != b.balances.available ||
      a.balances.raw != b.balances.raw ||
      a.hosted_identities_observed != b.hosted_identities_observed ||
      a.hosted_count != b.hosted_count ||
      a.outcome_values != b.outcome_values ||
      a.selected_guests.status != b.selected_guests.status ||
      a.selected_guests.frame != b.selected_guests.frame ||
      a.selected_guests.normal_refresh_sequence !=
          b.selected_guests.normal_refresh_sequence ||
      a.selected_guests.selected_nonhost_count !=
          b.selected_guests.selected_nonhost_count ||
      a.selected_guests.positive_join_count !=
          b.selected_guests.positive_join_count ||
      a.selected_guests.timely_positive_join_count !=
          b.selected_guests.timely_positive_join_count ||
      a.selected_guests.arrival_time_observed !=
          b.selected_guests.arrival_time_observed ||
      a.selected_guests.rows != b.selected_guests.rows)
    return false;
  for (std::size_t index = 0; index < a.hosted_count; ++index) {
    const auto &left = a.hosted[index];
    const auto &right = b.hosted[index];
    if (left.activity_id != right.activity_id ||
        left.host_character_id != right.host_character_id ||
        left.type_key_size != right.type_key_size ||
        left.type_key != right.type_key ||
        left.terminal_flags_observed != right.terminal_flags_observed ||
        left.native_completed != right.native_completed ||
        left.native_invalidated != right.native_invalidated)
      return false;
  }
  return true;
}

} // namespace

bool IsActivityFeastSelectedGuestRouteQualifiedV1(
    const ActivityFeastStage5StartSnapshotV1 &snapshot) noexcept {
  const auto &guests = snapshot.selected_guests;
  const auto &frame = snapshot.frame;
  const ActivityPlannerDiagFrameV1 expected{
      frame.revision, frame.date_raw, frame.actor_character_id,
      frame.application_main_thread, frame.paused, frame.map_ready,
      frame.actor_alive};
  return guests.status == ActivityFeastGuestJoinStatusV1::observed &&
         guests.frame == expected &&
         snapshot.normal_cost_refresh_sequence != 0 &&
         guests.normal_refresh_sequence ==
             snapshot.normal_cost_refresh_sequence &&
         guests.arrival_time_observed && guests.selected_nonhost_count > 0 &&
         guests.timely_positive_join_count > 0;
}

bool InvokeActivityFeastNativeCommitV1(void *, std::uintptr_t module_base,
                                      std::uintptr_t planner) noexcept {
#if defined(_WIN32)
  if (module_base == 0 || planner == 0 ||
      module_base > (std::numeric_limits<std::uintptr_t>::max)() - 0x10B13F0)
    return false;
  using Commit = void(__fastcall *)(void *);
  reinterpret_cast<Commit>(module_base + 0x10B13F0)(
      reinterpret_cast<void *>(planner));
  return true;
#else
  (void)module_base;
  (void)planner;
  return false;
#endif
}

bool InvokeActivityFeastNativeCommit12002V1(
    void *, std::uintptr_t module_base, std::uintptr_t planner) noexcept {
#if defined(_WIN32)
  if (module_base == 0 || planner == 0 ||
      module_base > (std::numeric_limits<std::uintptr_t>::max)() -
                        ck3_12002::kFeastCommitRva)
    return false;
  using Commit = void(__fastcall *)(void *);
  reinterpret_cast<Commit>(module_base + ck3_12002::kFeastCommitRva)(
      reinterpret_cast<void *>(planner));
  return true;
#else
  (void)module_base;
  (void)planner;
  return false;
#endif
}

ActivityFeastStage5StartResultV1 StartActivityFeastStage5V1(
    const ActivityFeastStage5StartEnvironmentV1 &environment,
    const ActivityFeastStage5StartRequestV1 &request) noexcept {
  ActivityFeastStage5StartResultV1 result{};
  const auto &frame = request.expected;
  if (!request.policy_approved || request.previous_submit_pending ||
      frame.revision == 0 || frame.actor_character_id <= 0 ||
      !frame.application_main_thread || !frame.paused || !frame.map_ready ||
      !frame.actor_alive || !Abi(environment))
    return result;
  ActivityFeastStage5StartSnapshotV1 first{}, final{};
  if (!environment.capture(environment.context, frame, first) ||
      !Valid(first, request) ||
      !environment.capture(environment.context, frame, final) ||
      !Valid(final, request) || !Same(final, first))
    return result;
  result.before = first;
  result.invoked = true;
  const auto invoke = environment.invoke_commit != nullptr
                          ? environment.invoke_commit
                          : environment.admitted_executable_sha256 ==
                                    ck3_12002::kFeastExecutableSha256
                                ? &InvokeActivityFeastNativeCommit12002V1
                                : &InvokeActivityFeastNativeCommitV1;
  result.status = invoke(environment.context, environment.module_base,
                         first.planner)
                      ? ActivityFeastStage5StartStatusV1::submitted_pending
                      : ActivityFeastStage5StartStatusV1::submission_outcome_unknown;
  return result;
}

ActivityFeastStage5PostResultV1 ReconcileActivityFeastStage5StartV1(
    const ActivityFeastStage5StartResultV1 &submission,
    const ActivityFeastStage5PostV1 &post) noexcept {
  ActivityFeastStage5PostResultV1 result{};
  const auto &before = submission.before;
  if (!submission.invoked || before.frame.revision == 0 ||
      post.frame.revision < before.frame.revision ||
      post.frame.actor_character_id != before.frame.actor_character_id ||
      post.frame.date_raw < before.frame.date_raw ||
      !post.frame.application_main_thread || !post.frame.paused ||
      !post.frame.map_ready || !post.frame.actor_alive ||
      post.balances.frame != post.frame ||
      !post.hosted_identities_observed ||
      post.hosted_count > post.hosted.size())
    return result;

  std::uint32_t new_count = 0;
  for (std::size_t index = 0; index < post.hosted_count; ++index) {
    const auto &candidate = post.hosted[index];
    if (candidate.host_character_id != before.frame.actor_character_id ||
        candidate.type_key_size != sizeof("activity_feast") - 1 ||
        std::memcmp(candidate.type_key.data(), "activity_feast",
                    sizeof("activity_feast") - 1) != 0)
      continue;
    bool existed = false;
    for (std::size_t old = 0; old < before.hosted_count; ++old)
      if (before.hosted[old].activity_id == candidate.activity_id)
        existed = true;
    if (!existed) {
      ++new_count;
      result.new_activity_id = candidate.activity_id;
    }
  }
  if (new_count > 1) return {};
  if (new_count == 0) {
    result.status = ActivityFeastStage5PostStatusV1::pending;
    return result;
  }
  result.new_identity_observed = true;
  result.status = ActivityFeastStage5PostStatusV1::created_debit_unresolved;
  if (post.frame.date_raw != before.frame.date_raw) return result;
  bool charged = false;
  for (std::size_t index = 0; index < 4; ++index) {
    const auto cost = before.cost_raw[index];
    if (cost == 0) continue;
    charged = true;
    if (!before.balances.available[index] ||
        !post.balances.available[index] ||
        before.balances.raw[index] <
            (std::numeric_limits<std::int64_t>::min)() + cost ||
        post.balances.raw[index] != before.balances.raw[index] - cost)
      return result;
  }
  result.same_date_exact_debit = charged;
  result.status = charged ? ActivityFeastStage5PostStatusV1::created_and_debited
                          : ActivityFeastStage5PostStatusV1::created_zero_cost;
  return result;
}

} // namespace xar::bridge
