#include "xar_bridge/activity_feast_guest_candidate_v1.hpp"
#include "activity_feast_ordinary_guest_selection_v1.hpp"

#include <cstdio>
#include <cstdlib>

#define main ActivityStage5GoldFixtureMain
#include "activity_stage5_gold_cost_v1_test.cpp"
#undef main

#define Expect(condition)                                                        \
  do {                                                                           \
    if (!(condition)) {                                                          \
      std::fprintf(stderr, "guest candidate fixture failed at line %d\n",     \
                   __LINE__);                                                    \
      std::exit(1);                                                              \
    }                                                                            \
  } while (false)

namespace {

constexpr std::uintptr_t kGroups = 0x1000C000;
constexpr std::uintptr_t kRules = 0x1000D000;
constexpr std::uintptr_t kSelected = 0x1000D800;
constexpr std::uintptr_t kIds = 0x1000E000;
constexpr std::uintptr_t kGuest = 0x1000F000;
constexpr std::uintptr_t kEarlierGuest = 0x1000F800;
constexpr std::uintptr_t kWorld = 0x10010000;
constexpr std::uintptr_t kProvinceTable = 0x10011000;
constexpr std::uintptr_t kProvinces = 0x10012000;
constexpr std::uintptr_t kDestination = 0x10013000;
constexpr std::uintptr_t kActivity = 0x10014000;
constexpr std::uintptr_t kActivityRows = 0x10015000;
constexpr std::uintptr_t kLocationRow = 0x10016000;
constexpr std::int32_t kGuestId = 31000;
constexpr std::int32_t kEarlierGuestId = 30000;

struct CandidateFixture {
  Fixture *memory = nullptr;
  std::int64_t join_raw = 500000;
  std::int32_t travel_days = 5;
  bool mutate_group = false;
  std::uint32_t join_calls = 0;
};

bool Join(void *opaque, std::uintptr_t base, std::uintptr_t planner,
          std::uintptr_t character, std::int64_t &value) noexcept {
  auto &fixture = *static_cast<CandidateFixture *>(opaque);
  ++fixture.join_calls;
  if (base != kBase || planner != kPlanner ||
      (character != kGuest && character != kEarlierGuest))
    return false;
  if (fixture.mutate_group)
    fixture.memory->Put(kRules + 8, std::int32_t{2});
  value = character == kEarlierGuest ? 500000 : fixture.join_raw;
  return true;
}

std::uintptr_t Activity(void *, std::uintptr_t base,
                        std::uintptr_t planner) noexcept {
  return base == kBase && planner == kPlanner ? kActivity : 0;
}

bool Travel(void *opaque, std::uintptr_t base,
            std::uintptr_t character, std::uintptr_t destination,
            std::int32_t &days) noexcept {
  const auto &fixture = *static_cast<CandidateFixture *>(opaque);
  if (base != kBase ||
      (character != kGuest && character != kEarlierGuest) ||
      destination != kDestination)
    return false;
  days = character == kEarlierGuest ? 3 : fixture.travel_days;
  return true;
}

void AddCandidate(Fixture &fixture) {
  fixture.Put(kBase + 0x10B0796,
              std::array<std::uint8_t, 7>{0x4C, 0x8D, 0xB9, 0x90,
                                           0x15, 0, 0});
  fixture.Put(kBase + 0x10B07A3,
              std::array<std::uint8_t, 7>{0x48, 0x81, 0xC1, 0x18,
                                           0x1A, 0, 0});
  fixture.Put(kBase + 0x28D07A1,
              std::array<std::uint8_t, 5>{0xE8, 0xBA, 0xE4, 0xFF, 0xFF});
  fixture.Put(kBase + 0x151CD6E,
              std::array<std::uint8_t, 7>{0x48, 0x8B, 0x81, 0x00,
                                           0x01, 0, 0});
  fixture.Put(kBase + 0x151CD75,
              std::array<std::uint8_t, 7>{0x48, 0x8B, 0x90, 0x90,
                                           0x15, 0, 0});
  fixture.Put(kPlanner + 0x1538, kActorId);
  fixture.Put(kPlanner + 0x1590, kGroups);
  fixture.Put(kPlanner + 0x159C, std::int32_t{1});
  fixture.Fill(kGroups, 24);
  fixture.Put(kGroups, kIds);
  fixture.Put(kGroups + 0x0C, std::int32_t{1});
  fixture.Put(kIds, kGuestId);
  fixture.Put(kPlanner + 0x1A18, kRules);
  fixture.Put(kPlanner + 0x1A24, std::int32_t{1});
  fixture.Fill(kRules, 16);
  fixture.Put(kRules + 8, std::int32_t{1});
  fixture.Put(kPlanner + 0x1678, std::uintptr_t{0});
  fixture.Put(kPlanner + 0x1684, std::int32_t{0});
  fixture.Put(kSlots + kGuestId * 0x10 + 8, kGuest);
  fixture.Put(kGuest + 0x18, kGuestId);
  fixture.Put(kBase + 0x570E068, kWorld);
  fixture.Put(kWorld + 8, static_cast<std::int32_t>(fixture.frame.date_raw));
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
}

ActivityFeastGuestJoinEnvironmentV1 EnvironmentFor(
    Fixture &fixture, ActivityCostSlot12ObserverV1 &observer,
    CandidateFixture &candidate) {
  ActivityFeastGuestJoinEnvironmentV1 env{};
  env.enabled = true;
  env.diagnostic = Environment(fixture, observer).diagnostic;
  env.passive_cost = &observer;
  env.invoke_join = &Join;
  env.join_context = &candidate;
  env.invoke_activity = &Activity;
  env.invoke_travel_days = &Travel;
  env.arrival_context = &candidate;
  return env;
}

} // namespace

int main() {
  Fixture fixture{};
  Populate(fixture);
  AddCandidate(fixture);
  ActivityCostSlot12ObserverV1 observer{};
  observer.environment = {true, true, kActivityCostSlot12ExeSha256V1,
                          kBase, &fixture, &Read, &ReadCostFrame};
  CandidateFixture candidate{&fixture};
  auto env = EnvironmentFor(fixture, observer, candidate);
  const auto expected = fixture.frame;

  auto result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::no_normal_refresh);
  Expect(result.character_id == -1 && !result.native_filtered);
  Expect(RecordActivityCostSlot12NormalReturnV1(
      observer, kBase + kActivityCostSlot12ReturnRvaV1, kPlanner));
  result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::observed);
  Expect(result.character_id == kGuestId && result.native_filtered);
  Expect(result.planner_join_raw == 500000 && result.travel_days == 5);
  Expect(result.arrival_raw == expected.date_raw + 5 * 24);
  Expect(result.arrival_raw <= result.planned_start_raw);
  Expect(result.source_fingerprint != 0 && result.normal_refresh_sequence == 1);
  Expect(result.active_rule_count == 1 && result.filtered_group_count == 1 &&
         result.selected_row_count == 0);

  fixture.Put(kGroups + 0x0C, std::int32_t{2});
  fixture.Put(kIds, kEarlierGuestId);
  fixture.Put(kIds + 4, kGuestId);
  fixture.Put(kSlots + kEarlierGuestId * 0x10 + 8, kEarlierGuest);
  fixture.Put(kEarlierGuest + 0x18, kEarlierGuestId);
  result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::observed &&
         result.character_id == kEarlierGuestId);
  // Actual Murchad v8 regression: global first belongs to another category;
  // the named close-family filtered row is later in the native groups.
  ActivityGuestRuleProvenanceResultV1 close_family{};
  close_family.status = ActivityGuestRuleProvenanceStatusV1::observed;
  close_family.raw_rule_character_count = 3;
  close_family.filtered_rule_character_count = 1;
  close_family.filtered_ids[0] = static_cast<std::uint32_t>(kGuestId);
  const auto global_first = result;
  const auto ordinary = xar::ck3_12002::SelectFeastOrdinaryCloseFamilyCandidateV1(
      env, expected, close_family, global_first);
  Expect(ordinary.status == ActivityFeastGuestCandidateStatusV1::observed &&
         ordinary.character_id == kGuestId && ordinary.native_filtered &&
         ordinary.planner_join_raw > 0 && ordinary.travel_days >= 0 &&
         ordinary.arrival_raw <= ordinary.planned_start_raw &&
         ordinary.source_fingerprint == global_first.source_fingerprint &&
         ordinary.normal_refresh_sequence == global_first.normal_refresh_sequence);
  Expect(ReadActivityFeastGuestCandidateV1(env, expected, ordinary.character_id) == ordinary);
  close_family.filtered_ids[0] = 32000; // Category member absent from native filtered groups.
  Expect(xar::ck3_12002::SelectFeastOrdinaryCloseFamilyCandidateV1(
      env, expected, close_family, global_first) == global_first);
  close_family.filtered_ids[0] = static_cast<std::uint32_t>(kGuestId);
  candidate.join_raw = -1;
  Expect(xar::ck3_12002::SelectFeastOrdinaryCloseFamilyCandidateV1(
      env, expected, close_family, global_first) == global_first);
  result = ReadActivityFeastGuestCandidateV1(env, expected, kGuestId);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::observed &&
         result.character_id == kGuestId && result.native_filtered &&
         result.planner_join_raw == -1 && result.arrival_raw <= result.planned_start_raw);
  candidate.join_raw = 500000;
  candidate.travel_days = 20;
  Expect(xar::ck3_12002::SelectFeastOrdinaryCloseFamilyCandidateV1(
      env, expected, close_family, global_first) == global_first);
  result = ReadActivityFeastGuestCandidateV1(env, expected, kGuestId);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::observed &&
         result.character_id == kGuestId && result.arrival_raw > result.planned_start_raw);
  result = ReadActivityFeastGuestCandidateV1(env, expected, 32000);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::target_not_filtered &&
         result.character_id == -1 && !result.native_filtered &&
         result.source_fingerprint != 0 && result.normal_refresh_sequence == 1);
  fixture.Put(kPlanner + 0x1678, kSelected);
  fixture.Put(kPlanner + 0x1684, std::int32_t{1});
  fixture.Fill(kSelected, 16);
  fixture.Put(kSelected + 8, kGuestId);
  Expect(RecordActivityCostSlot12NormalReturnV1(
      observer, kBase + kActivityCostSlot12ReturnRvaV1, kPlanner));
  result = ReadActivityFeastGuestCandidateV1(env, expected, kGuestId);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::observed &&
         result.selected_member && result.character_id == kGuestId);
  fixture.Put(kPlanner + 0x1678, std::uintptr_t{0});
  fixture.Put(kPlanner + 0x1684, std::int32_t{0});
  Expect(RecordActivityCostSlot12NormalReturnV1(
      observer, kBase + kActivityCostSlot12ReturnRvaV1, kPlanner));
  fixture.Put(kGuest + 0x18, kGuestId + 0x01000000);
  result = ReadActivityFeastGuestCandidateV1(env, expected, kGuestId);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::native_evaluation_failed);
  fixture.Put(kGuest + 0x18, kGuestId);
  candidate.mutate_group = true;
  result = ReadActivityFeastGuestCandidateV1(env, expected, kGuestId);
  Expect(result.status == ActivityFeastGuestCandidateStatusV1::configuration_changed);
  candidate.mutate_group = false;
  fixture.Put(kRules + 8, std::int32_t{1});
  fixture.Put(kGroups + 0x0C, std::int32_t{1});
  fixture.Put(kIds, kGuestId);
  candidate.travel_days = 5;

  candidate.join_raw = -1;
  result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status ==
         ActivityFeastGuestCandidateStatusV1::no_qualified_candidate);
  Expect(result.character_id == -1 && !result.native_filtered);
  Expect(result.active_rule_count == 1 && result.filtered_group_count == 1 &&
         result.selected_row_count == 0);
  candidate.join_raw = 500000;
  candidate.travel_days = 20;
  result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status ==
         ActivityFeastGuestCandidateStatusV1::no_qualified_candidate);
  candidate.travel_days = 5;

  fixture.Put(kIds, std::int32_t{-1});
  result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status ==
         ActivityFeastGuestCandidateStatusV1::candidate_source_unavailable);
  Expect(result.character_id == -1 && !result.native_filtered);
  fixture.Put(kIds, kGuestId);

  candidate.mutate_group = true;
  result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status ==
         ActivityFeastGuestCandidateStatusV1::configuration_changed);
  candidate.mutate_group = false;

  fixture.Put(kBase + 0x151CD75,
              std::array<std::uint8_t, 7>{0, 0, 0, 0, 0, 0, 0});
  result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status ==
         ActivityFeastGuestCandidateStatusV1::exact_build_rejected);
  fixture.Put(kBase + 0x151CD75,
              std::array<std::uint8_t, 7>{0x48, 0x8B, 0x90, 0x90,
                                           0x15, 0, 0});

  fixture.Put(kBase + 0x28D07A1,
              std::array<std::uint8_t, 5>{0, 0, 0, 0, 0});
  result = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(result.status ==
         ActivityFeastGuestCandidateStatusV1::exact_build_rejected);
  return 0;
}
