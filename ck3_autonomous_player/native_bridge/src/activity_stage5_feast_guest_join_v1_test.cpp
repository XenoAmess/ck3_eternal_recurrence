#include "xar_bridge/activity_stage5_feast_guest_join_v1.hpp"

#define main ActivityStage5GoldFixtureMain
#include "activity_stage5_gold_cost_v1_test.cpp"
#undef main

namespace {

constexpr std::uintptr_t kRows = 0x1000C000;
constexpr std::uintptr_t kCache = 0x1000D000;
constexpr std::uintptr_t kGuest = 0x1000E000;
constexpr std::uintptr_t kWorld = 0x1000F000;
constexpr std::uintptr_t kProvinceTable = 0x10010000;
constexpr std::uintptr_t kProvinces = 0x10011000;
constexpr std::uintptr_t kDestination = 0x10012000;
constexpr std::uintptr_t kActivity = 0x10013000;
constexpr std::uintptr_t kActivityRows = 0x10014000;
constexpr std::uintptr_t kRecords = 0x10015000;
constexpr std::uintptr_t kLocationRow = 0x10016000;
constexpr std::int32_t kGuestId = 31000;

struct GuestFixture {
  Fixture *memory = nullptr;
  std::int64_t join_raw = 500000;
  bool fail = false;
  bool mutate_frame = false;
  std::uint32_t calls = 0;
  std::int32_t travel_days = 5;
  std::uint32_t travel_calls = 0;
};

bool Invoke(void *opaque, std::uintptr_t module_base,
            std::uintptr_t planner, std::uintptr_t character,
            std::int64_t &value) noexcept {
  auto &fixture = *static_cast<GuestFixture *>(opaque);
  ++fixture.calls;
  if (module_base != kBase || planner != kPlanner ||
      character != kGuest || fixture.fail)
    return false;
  if (fixture.mutate_frame) ++fixture.memory->frame.revision;
  value = fixture.join_raw;
  return true;
}

std::uintptr_t Activity(void *, std::uintptr_t base,
                        std::uintptr_t planner) noexcept {
  return base == kBase && planner == kPlanner ? kActivity : 0;
}

bool Travel(void *opaque, std::uintptr_t base,
            std::uintptr_t character, std::uintptr_t destination,
            std::int32_t &days) noexcept {
  auto &fixture = *static_cast<GuestFixture *>(opaque);
  ++fixture.travel_calls;
  if (base != kBase || character != kGuest ||
      destination != kDestination)
    return false;
  days = fixture.travel_days;
  return true;
}

void AddGuests(Fixture &fixture) {
  fixture.Put(kBase + 0x10AE220,
              std::array<std::uint8_t, 7>{0x48, 0x8B, 0x83, 0x78,
                                           0x16, 0, 0});
  fixture.Put(kBase + 0x10AE286,
              std::array<std::uint8_t, 5>{0xE8, 0xF5, 0x27, 0, 0});
  fixture.Put(kBase + 0x10AE298,
              std::array<std::uint8_t, 4>{0x88, 0x0C, 0x07, 0x48});
  fixture.Put(kBase + 0x972827,
              std::array<std::uint8_t, 5>{0xE8, 0x54, 0xA9, 0xF5, 0x01});
  fixture.Put(kBase + 0x9728CA,
              std::array<std::uint8_t, 4>{0x48, 0x89, 0x4B, 0x04});
  fixture.Put(kPlanner + 0x1538, kActorId);
  fixture.Put(kPlanner + 0x1678, kRows);
  fixture.Put(kPlanner + 0x1684, std::int32_t{2});
  fixture.Put(kPlanner + 0x1A30, kCache);
  fixture.Fill(kRows, 32);
  fixture.Put(kRows + 8, kActorId);
  fixture.Put(kRows + 16 + 8, kGuestId);
  fixture.Put(kCache, std::uint8_t{1});
  fixture.Put(kCache + 1, std::uint8_t{1});
  fixture.Put(kSlots + kGuestId * 0x10 + 8, kGuest);
  fixture.Put(kGuest + 0x18, kGuestId);
  fixture.Put(kBase + 0x570E068, kWorld);
  fixture.Put(kWorld + 8, static_cast<std::int32_t>(fixture.frame.date_raw));
  fixture.Put(kWorld + 0x9C, std::int32_t{1000});
  fixture.Put(kWorld + 0xA0, kProvinceTable);
  fixture.Put(kProvinceTable + 0x140, kProvinces);
  fixture.Put(kProvinceTable + 0x14C, std::int32_t{3000});
  fixture.Put(kPlanner + 0x1578, kLocationRow);
  fixture.Put(kLocationRow + 8, std::int32_t{2619});
  fixture.Put(kProvinces + 2619 * 8, kDestination);
  fixture.Put(kPlanner + 0x1550,
              static_cast<std::int32_t>(fixture.frame.date_raw + 10 * 24));
  fixture.Put(kActivity + 0x10, kActivityRows);
  fixture.Put(kActivity + 0x1C, std::int32_t{0});
  fixture.Put(kActivity + 0x83C, std::int32_t{-1});
  fixture.Put(kActivity + 0x360, std::uintptr_t{0});
  fixture.Put(kActivity + 0x36C, std::int32_t{0});
}

ActivityFeastGuestJoinEnvironmentV1 EnvironmentFor(
    Fixture &fixture, ActivityCostSlot12ObserverV1 &observer,
    GuestFixture &guest) {
  ActivityFeastGuestJoinEnvironmentV1 env{};
  env.enabled = true;
  env.diagnostic = Environment(fixture, observer).diagnostic;
  env.passive_cost = &observer;
  env.invoke_join = &Invoke;
  env.join_context = &guest;
  env.invoke_activity = &Activity;
  env.invoke_travel_days = &Travel;
  env.arrival_context = &guest;
  return env;
}

void NoRowsPublished(const ActivityFeastGuestJoinResultV1 &result) {
  Expect(result.normal_refresh_sequence == 0);
  Expect(result.selected_nonhost_count == 0);
  Expect(result.positive_join_count == 0);
  Expect(result.timely_positive_join_count == 0);
  Expect(!result.arrival_time_observed);
}

} // namespace

int main() {
  Fixture fixture{};
  Populate(fixture);
  AddGuests(fixture);
  ActivityCostSlot12ObserverV1 passive{};
  passive.environment = {
      true, true, kActivityCostSlot12ExeSha256V1,
      kBase, &fixture, &Read, &ReadCostFrame};
  GuestFixture guest{&fixture};
  auto env = EnvironmentFor(fixture, passive, guest);
  const auto expected = fixture.frame;

  auto result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::no_normal_refresh);
  NoRowsPublished(result);
  Expect(RecordActivityCostSlot12NormalReturnV1(
      passive, kBase + kActivityCostSlot12ReturnRvaV1, kPlanner));

  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::observed);
  Expect(result.normal_refresh_sequence == 1);
  Expect(result.selected_nonhost_count == 1 && result.positive_join_count == 1);
  Expect(result.timely_positive_join_count == 1);
  Expect(result.rows[0].character_id == kGuestId);
  Expect(result.rows[0].planner_join_raw == guest.join_raw);
  Expect(result.rows[0].positive_join);
  Expect(result.rows[0].predicted_travel_days == 5);
  Expect(result.rows[0].predicted_arrival_raw == expected.date_raw + 5 * 24);
  Expect(!result.rows[0].may_not_arrive_in_time);
  Expect(result.arrival_time_observed);
  Expect(guest.calls == 2);
  Expect(guest.travel_calls == 2);

  fixture.Put(kCache + 1, std::uint8_t{0});
  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::cache_disagreed);
  NoRowsPublished(result);
  guest.join_raw = -100000;
  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::observed);
  Expect(result.selected_nonhost_count == 1 && result.positive_join_count == 0);
  Expect(result.timely_positive_join_count == 0);
  Expect(result.rows[0].character_id == kGuestId);

  guest.fail = true;
  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status ==
         ActivityFeastGuestJoinStatusV1::native_evaluation_failed);
  NoRowsPublished(result);
  guest.fail = false;

  guest.join_raw = 500000;
  fixture.Put(kCache + 1, std::uint8_t{1});
  fixture.Put(kActivity + 0x1C, std::int32_t{1});
  fixture.Put(kActivityRows, kGuestId);
  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::observed);
  Expect(result.rows[0].predicted_travel_days == 0);
  Expect(result.timely_positive_join_count == 1);
  const auto travel_calls_before_record = guest.travel_calls;
  fixture.Put(kActivity + 0x83C, std::int32_t{0});
  fixture.Put(kActivity + 0x360, kRecords);
  fixture.Put(kActivity + 0x36C, std::int32_t{1});
  fixture.Put(kRecords + 0x38,
              std::int32_t{0x29C55C0 + 24 * (1000 + 15)});
  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::observed);
  Expect(result.rows[0].predicted_travel_days == 15);
  Expect(result.rows[0].may_not_arrive_in_time);
  Expect(result.timely_positive_join_count == 0);
  Expect(guest.travel_calls == travel_calls_before_record);

  guest.mutate_frame = true;
  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::configuration_changed);
  NoRowsPublished(result);
  guest.mutate_frame = false;
  fixture.frame = expected;

  fixture.Put(kRows + 16 + 8, std::int32_t{-1});
  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::observed);
  Expect(result.selected_nonhost_count == 0 && result.positive_join_count == 0);
  Expect(result.arrival_time_observed);

  env.enabled = false;
  result = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(result.status == ActivityFeastGuestJoinStatusV1::exact_build_rejected);
  Expect(!InvokeActivityFeastNativePlannerGuestJoinV1(
      nullptr, 0, kPlanner, kGuest, guest.join_raw));
  Expect(InvokeActivityFeastNativePlannerActivityV1(
             nullptr, 0, kPlanner) == 0);
  Expect(!InvokeActivityFeastNativeTravelDaysV1(
      nullptr, 0, kGuest, kDestination, guest.travel_days));
  return 0;
}
