#include "xar_bridge/activity_feast_stage5_start_v1.hpp"

#include <cstdlib>
#include <cstring>
#include <unordered_map>

namespace {
using namespace xar::bridge;
constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kStorage = 0x10000000;
constexpr std::uintptr_t kSlots = 0x10001000;
constexpr std::uintptr_t kActor = 0x10002000;
constexpr std::uintptr_t kExtension = 0x10003000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::int32_t kActorId = 29829;

void Check(bool condition) { if (!condition) std::abort(); }

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityHostedIdentityFrameV1 frame{3, 53219928, kActorId, true, true,
                                      true, true};
  ActivityFeastStage5StartSnapshotV1 snapshot{};
  int capture_count = 0;
  int commit_count = 0;
  bool drift = false;
  bool commit_return = true;

  template <typename T> void Put(std::uintptr_t at, T value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(T); ++index)
      bytes[at + index] = data[index];
  }
  void PutBytes(std::uintptr_t at, const std::uint8_t *data,
                std::size_t size) {
    for (std::size_t index = 0; index < size; ++index)
      bytes[at + index] = data[index];
  }
};

bool Read(void *opaque, std::uintptr_t at, void *output,
          std::size_t size) noexcept {
  const auto &fake = *static_cast<Fake *>(opaque);
  auto *destination = static_cast<std::uint8_t *>(output);
  for (std::size_t index = 0; index < size; ++index) {
    auto found = fake.bytes.find(at + index);
    if (found == fake.bytes.end()) return false;
    destination[index] = found->second;
  }
  return true;
}

bool Frame(void *opaque, ActivityHostedIdentityFrameV1 &output) noexcept {
  output = static_cast<Fake *>(opaque)->frame;
  return true;
}

bool Capture(void *opaque, const ActivityHostedIdentityFrameV1 &expected,
             ActivityFeastStage5StartSnapshotV1 &output) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (fake.frame != expected) return false;
  output = fake.snapshot;
  if (++fake.capture_count == 2 && fake.drift) output.planner += 8;
  return true;
}

bool Commit(void *opaque, std::uintptr_t base,
            std::uintptr_t planner) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  Check(base == kBase && planner == kPlanner);
  ++fake.commit_count;
  return fake.commit_return;
}

void Init(Fake &fake) {
  fake.Put(kBase + 0x4FE7EE0, static_cast<std::uint32_t>(kActorId));
  fake.Put(kBase + 0x570C130, kStorage);
  fake.Put(kBase + 0x570C138, static_cast<std::uintptr_t>(0));
  fake.Put(kStorage + 0x20, kSlots);
  fake.Put(kStorage + 0x2C, static_cast<std::uint32_t>(50000));
  fake.Put(kSlots + static_cast<std::uint32_t>(kActorId) * 16 + 8, kActor);
  fake.Put(kActor + 0x18, static_cast<std::uint32_t>(kActorId));
  fake.Put(kActor + 0x1A8, kExtension);
  fake.Put(kExtension + 0x100, static_cast<std::int64_t>(120644281));
  fake.Put(kExtension + 0x110, static_cast<std::int64_t>(4000000));
  constexpr std::uint8_t kCommit[13]{0x48,0x89,0x5C,0x24,0x10,0x57,0x48,
                                     0x81,0xEC,0x10,0x0A,0x00,0x00};
  constexpr std::uint8_t kCanStart[7]{0x48,0x89,0x5C,0x24,0x10,0x48,0x89};
  fake.PutBytes(kBase + 0x10B13F0, kCommit, sizeof(kCommit));
  fake.PutBytes(kBase + 0x10B0DA0, kCanStart, sizeof(kCanStart));
  auto &s = fake.snapshot;
  s.frame = fake.frame;
  s.planner = kPlanner;
  s.normal_cost_refresh_sequence = 2;
  s.feast_type_verified = true;
  s.generic_option_verified = true;
  s.final_can_start_observed = true;
  s.final_can_start = true;
  s.four_costs_observed = true;
  s.cost_resource_indices = {0, 6, 2, 9};
  s.cost_raw = {10000000, 0, 0, 0};
  s.balances.frame = fake.frame;
  s.balances.available = {true, false, true, false};
  s.balances.raw = {120644281, 0, 4000000, 0};
  s.hosted_identities_observed = true;
}

ActivityFeastStage5StartEnvironmentV1 StartEnv(Fake &fake) {
  return {true, kActivityHostedIdentityExeSha256V1, kBase, &fake, &Read,
          &Capture, &Commit};
}

} // namespace

int main() {
  Fake fake{};
  Init(fake);
  const ActivityHostedIdentityEnvironmentV1 balance_env{
      true, kActivityHostedIdentityExeSha256V1, kBase, &fake, &Read, &Frame};
  const auto balances = ReadActivityFeastResourceBalancesV1(balance_env,
                                                             fake.frame);
  Check(balances.status == ActivityFeastBalanceStatusV1::observed_partial);
  Check(balances.value.available ==
        (std::array<bool,4>{true,false,true,false}));
  Check(balances.value.raw[0] == 120644281 &&
        balances.value.raw[2] == 4000000);
  auto request = ActivityFeastStage5StartRequestV1{};
  request.expected = fake.frame;
  request.policy_approved = true;
  request.reserve_raw[0] = 50000000;
  auto result = StartActivityFeastStage5V1(StartEnv(fake), request);
  Check(result.status == ActivityFeastStage5StartStatusV1::submitted_pending);
  Check(result.invoked && fake.commit_count == 1 && fake.capture_count == 2);
  ActivityFeastStage5PostV1 post{};
  post.frame = fake.frame;
  post.frame.revision++;
  post.balances.frame = post.frame;
  post.balances.available = fake.snapshot.balances.available;
  post.balances.raw = fake.snapshot.balances.raw;
  post.balances.raw[0] -= fake.snapshot.cost_raw[0];
  post.hosted_identities_observed = true;
  post.hosted_count = 1;
  post.hosted[0].activity_id = 0x01000012;
  post.hosted[0].host_character_id = kActorId;
  std::memcpy(post.hosted[0].type_key.data(), "activity_feast", 14);
  post.hosted[0].type_key_size = 14;
  auto outcome = ReconcileActivityFeastStage5StartV1(result, post);
  Check(outcome.status == ActivityFeastStage5PostStatusV1::created_and_debited &&
        outcome.new_activity_id == 0x01000012 &&
        outcome.same_date_exact_debit);
  post.balances.raw[0]++;
  outcome = ReconcileActivityFeastStage5StartV1(result, post);
  Check(outcome.status ==
        ActivityFeastStage5PostStatusV1::created_debit_unresolved &&
        outcome.new_identity_observed);
  post.hosted_count = 0;
  outcome = ReconcileActivityFeastStage5StartV1(result, post);
  Check(outcome.status == ActivityFeastStage5PostStatusV1::pending);

  request.previous_submit_pending = true;
  result = StartActivityFeastStage5V1(StartEnv(fake), request);
  Check(result.status == ActivityFeastStage5StartStatusV1::rejected &&
        fake.commit_count == 1);
  request.previous_submit_pending = false;
  fake.snapshot.cost_raw[1] = 1; // Unknown treasury balance is never zero.
  result = StartActivityFeastStage5V1(StartEnv(fake), request);
  Check(result.status == ActivityFeastStage5StartStatusV1::rejected &&
        fake.commit_count == 1);
  fake.snapshot.cost_raw[1] = 0;
  fake.snapshot.final_can_start = false;
  result = StartActivityFeastStage5V1(StartEnv(fake), request);
  Check(result.status == ActivityFeastStage5StartStatusV1::rejected);
  fake.snapshot.final_can_start = true;
  fake.drift = true;
  fake.capture_count = 0;
  result = StartActivityFeastStage5V1(StartEnv(fake), request);
  Check(result.status == ActivityFeastStage5StartStatusV1::rejected &&
        fake.commit_count == 1);
  fake.drift = false;
  fake.capture_count = 0;
  fake.commit_return = false;
  result = StartActivityFeastStage5V1(StartEnv(fake), request);
  Check(result.status ==
        ActivityFeastStage5StartStatusV1::submission_outcome_unknown &&
        result.invoked && fake.commit_count == 2);

  fake.frame.revision++;
  const auto changed = ReadActivityFeastResourceBalancesV1(balance_env,
                                                             request.expected);
  Check(changed.status == ActivityFeastBalanceStatusV1::frame_rejected);
  fake.frame = request.expected;
  fake.Put(kActor + 0x18, static_cast<std::uint32_t>(kActorId + 1));
  const auto stale = ReadActivityFeastResourceBalancesV1(balance_env,
                                                           request.expected);
  Check(stale.status == ActivityFeastBalanceStatusV1::actor_unavailable);
}
