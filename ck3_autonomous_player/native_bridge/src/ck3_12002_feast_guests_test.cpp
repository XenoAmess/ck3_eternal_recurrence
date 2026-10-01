#include "xar_bridge/activity_feast_guest_candidate_v1.hpp"
#include "xar_bridge/activity_feast_guest_rule_provenance_v1.hpp"
#include "xar_bridge/ck3_12002_feast_guests_abi.hpp"

#include <windows.h>

#define main ActivityPlanner12002FixtureMain
#include "ck3_12002_feast_planner_diag_test.cpp"
#undef main

namespace {
using namespace xar::bridge;
constexpr std::uintptr_t kSelected = 0x1000B000;
constexpr std::uintptr_t kCache = 0x1000C000;
constexpr std::uintptr_t kGuest = 0x1000D000;
constexpr std::uintptr_t kCandidate = 0x1000E000;
constexpr std::uintptr_t kWorld = 0x1000F000;
constexpr std::uintptr_t kProvinceTable = 0x10010000;
constexpr std::uintptr_t kProvinces = 0x10011000;
constexpr std::uintptr_t kDestination = 0x10012000;
constexpr std::uintptr_t kActivity = 0x10013000;
constexpr std::uintptr_t kLocation = 0x10014000;
constexpr std::uintptr_t kGroups = 0x10015000;
constexpr std::uintptr_t kGroupIds = 0x10016000;
constexpr std::uintptr_t kActiveRules = 0x10017000;
constexpr std::uintptr_t kRule = 0x10018000;
constexpr std::uintptr_t kOutput = 0x10019000;
constexpr std::uintptr_t kOutputRows = 0x1001A000;
constexpr std::uintptr_t kValues = 0x1001B000;
constexpr std::int32_t kGuestId = 31000;
constexpr std::int32_t kCandidateId = 31001;

void Fill(Fake &fake, std::uintptr_t base, std::size_t count) {
  for (std::size_t i = 0; i < count; ++i) fake.bytes[base + i] = 0;
}

bool CostFrame(void *context, ActivityCostSlot12FrameV1 &out) noexcept {
  const auto &frame = static_cast<Fake *>(context)->frame;
  out = {static_cast<std::int32_t>(frame.date_raw), frame.actor_character_id,
         GetCurrentThreadId(), frame.paused};
  return true;
}

struct Evaluation {
  Fake *fake = nullptr;
  std::int64_t guest_join = 500000;
  std::int64_t candidate_join = 200000;
  std::int32_t guest_days = 5;
  std::int32_t candidate_days = 3;
};

bool Join(void *opaque, std::uintptr_t base, std::uintptr_t planner,
          std::uintptr_t character, std::int64_t &out) noexcept {
  const auto &values = *static_cast<Evaluation *>(opaque);
  if (base != kBase || planner != kPlanner) return false;
  if (character == kGuest) out = values.guest_join;
  else if (character == kCandidate) out = values.candidate_join;
  else return false;
  return true;
}

std::uintptr_t Activity(void *, std::uintptr_t base,
                        std::uintptr_t planner) noexcept {
  return base == kBase && planner == kPlanner ? kActivity : 0;
}

bool Travel(void *opaque, std::uintptr_t base, std::uintptr_t character,
            std::uintptr_t destination, std::int32_t &out) noexcept {
  const auto &values = *static_cast<Evaluation *>(opaque);
  if (base != kBase || destination != kDestination) return false;
  if (character == kGuest) out = values.guest_days;
  else if (character == kCandidate) out = values.candidate_days;
  else return false;
  return true;
}

void GuestMemory(Fake &fake) {
  Fill(fake, kPlanner + 0x1500, 0x1B10 - 0x1500);
  Populate(fake);
  fake.visible = true;
  fake.Put(kPlanner + 0x1AE8, std::int32_t{5});
  fake.Put(kPlanner + 0x1508, kActorId);
  fake.Put(kPlanner + 0x1520, static_cast<std::int32_t>(fake.frame.date_raw + 240));
  fake.Put(kPlanner + 0x15B0, kLocation);
  fake.Put(kPlanner + 0x15BC, std::int32_t{1});
  Fill(fake, kLocation, 0x38);
  fake.Put(kLocation + 8, std::int32_t{2619});
  fake.Put(kPlanner + 0x16B0, kSelected);
  fake.Put(kPlanner + 0x16BC, std::int32_t{2});
  fake.Put(kPlanner + 0x1A68, kCache);
  Fill(fake, kSelected, 32);
  fake.Put(kSelected + 8, kActorId);
  fake.Put(kSelected + 24, kGuestId);
  fake.Put(kCache, std::uint8_t{1});
  fake.Put(kCache + 1, std::uint8_t{1});
  fake.Put(kSlots + kGuestId * 16 + 8, kGuest);
  fake.Put(kSlots + kCandidateId * 16 + 8, kCandidate);
  fake.Put(kGuest + 0x18, kGuestId);
  fake.Put(kCandidate + 0x18, kCandidateId);

  fake.Put(kBase + 0x5C68C50, kWorld);
  fake.Put(kWorld + 8, static_cast<std::int32_t>(fake.frame.date_raw));
  fake.Put(kWorld + 0x9C, std::int32_t{1000});
  fake.Put(kWorld + 0xA0, kProvinceTable);
  fake.Put(kProvinceTable + 0x140, kProvinces);
  fake.Put(kProvinceTable + 0x14C, std::int32_t{3000});
  fake.Put(kProvinces + 2619 * 8, kDestination);
  fake.Put(kActivity + 0x10, std::uintptr_t{0});
  fake.Put(kActivity + 0x1C, std::int32_t{0});
  for (std::size_t i = 0; i < 10; ++i)
    fake.Put(kPlanner + 0x1B10 + 0x50 + i * 0x90 + 0x78, std::int64_t{0});

  fake.Put(kBase + 0x11B5BE0, std::array<std::uint8_t, 7>{0x48,0x8B,0x83,0xB0,0x16,0,0});
  fake.Put(kBase + 0x11B5C46, std::array<std::uint8_t, 5>{0xE8,0x05,0x27,0,0});
  fake.Put(kBase + 0x11B5C58, std::array<std::uint8_t, 4>{0x88,0x0C,0x07,0x48});
  fake.Put(kBase + 0x9DFF87, std::array<std::uint8_t, 5>{0xE8,0x54,0xAE,0x1D,0x02});
  fake.Put(kBase + 0x9E002A, std::array<std::uint8_t, 4>{0x48,0x89,0x4B,0x04});
  fake.Put(kBase + 0x11B8066, std::array<std::uint8_t, 7>{0x4C,0x8D,0xB9,0xC8,0x15,0,0});
  fake.Put(kBase + 0x11B8073, std::array<std::uint8_t, 7>{0x48,0x81,0xC1,0x50,0x1A,0,0});
  fake.Put(kBase + 0x2BBE691, std::array<std::uint8_t, 5>{0xE8,0xDA,0xE3,0xFF,0xFF});
  fake.Put(kBase + 0x165B655, std::array<std::uint8_t, 7>{0x48,0x8B,0x90,0xC8,0x15,0,0});
  fake.Put(kPlanner + 0x15C8, kGroups);
  fake.Put(kPlanner + 0x15D4, std::int32_t{1});
  fake.Put(kGroups, kGroupIds);
  fake.Put(kGroups + 0xC, std::int32_t{2});
  fake.Put(kGroupIds, kGuestId);
  fake.Put(kGroupIds + 4, kCandidateId);
  fake.Put(kPlanner + 0x1A50, kActiveRules);
  fake.Put(kPlanner + 0x1A5C, std::int32_t{1});
  Fill(fake, kActiveRules, 16);
  fake.Put(kActiveRules, kRule);
  fake.Put(kActiveRules + 8, std::int32_t{0});
}

void ProvenanceMemory(Fake &fake) {
  fake.Put(kBase + 0x2BBD1B0, std::array<std::uint8_t,15>{0x4C,0x89,0x44,0x24,0x18,0x48,0x89,0x54,0x24,0x10,0x48,0x89,0x4C,0x24,0x08});
  fake.Put(kBase + 0x3765880, std::array<std::uint8_t,18>{0x48,0x89,0x5C,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x81,0xEC,0x30,0x04,0,0});
  fake.Put(kBase + 0x11B832C, std::array<std::uint8_t,5>{0xE8,0x7F,0x4E,0xA0,0x01});
  fake.Put(kBase + 0x2BBD325, std::array<std::uint8_t,5>{0xE8,0x56,0x85,0xBA,0});
  fake.Put(kRule + 0x14, std::uint32_t{0x12345678});
  fake.Put(kRule + 0x94, std::uint32_t{42});
  fake.Put(kOutput + 0x100, kOutputRows);
  fake.Put(kOutput + 0x10C, std::int32_t{1});
  fake.Put(kOutputRows + 8, std::uint32_t{42});
  fake.Put(kOutputRows + 0x10, kValues);
  fake.Put(kOutputRows + 0x1C, std::int32_t{2});
  fake.Put(kValues, std::uint16_t{4});
  fake.Put(kValues + 8, kGuestId);
  fake.Put(kValues + 16, std::uint16_t{4});
  fake.Put(kValues + 24, kCandidateId);
  fake.Put(kGroups + 0xC, std::int32_t{1});
}
} // namespace

int main() {
  Fake fake{};
  GuestMemory(fake);
  ActivityCostSlot12ObserverV1 passive{};
  passive.environment = {true, true, kActivityPlanner12002ExeSha256V1,
                         kBase, &fake, &Read, &CostFrame};
  Expect(RecordActivityCostSlot12NormalReturnV1(passive, kBase + 0x11B5B5F, kPlanner));
  Evaluation values{&fake};
  ActivityFeastGuestJoinEnvironmentV1 env{};
  env.enabled = true;
  env.diagnostic = Env(fake);
  env.passive_cost = &passive;
  env.invoke_join = &Join;
  env.join_context = &values;
  env.invoke_activity = &Activity;
  env.invoke_travel_days = &Travel;
  env.arrival_context = &values;
  const auto expected = fake.frame;
  auto selected = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(selected.status == ActivityFeastGuestJoinStatusV1::observed);
  Expect(selected.selected_nonhost_count == 1 && selected.positive_join_count == 1);
  Expect(selected.timely_positive_join_count == 1 && selected.arrival_time_observed);
  Expect(selected.rows[0].character_id == kGuestId && selected.rows[0].predicted_travel_days == 5);
  auto candidate = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(candidate.status == ActivityFeastGuestCandidateStatusV1::observed);
  Expect(candidate.character_id == kCandidateId && !candidate.selected_member);
  Expect(candidate.native_filtered && candidate.planner_join_raw == 200000);

  values.guest_join = -98700000;
  values.guest_days = 15;
  fake.Put(kCache + 1, std::uint8_t{0});
  selected = ReadActivityFeastGuestJoinV1(env, expected);
  Expect(selected.status == ActivityFeastGuestJoinStatusV1::observed);
  Expect(selected.positive_join_count == 0 && selected.timely_positive_join_count == 0);
  Expect(selected.rows[0].planner_join_raw == -98700000);
  Expect(selected.rows[0].may_not_arrive_in_time);
  candidate = ReadActivityFeastGuestCandidateV1(env, expected, kGuestId);
  Expect(candidate.status == ActivityFeastGuestCandidateStatusV1::observed);
  Expect(candidate.selected_member && candidate.planner_join_raw == -98700000);
  Expect(candidate.arrival_raw > candidate.planned_start_raw);
  values.candidate_join = -100000;
  candidate = ReadActivityFeastGuestCandidateV1(env, expected);
  Expect(candidate.status == ActivityFeastGuestCandidateStatusV1::no_qualified_candidate);

  ProvenanceMemory(fake);
  ActivityGuestRuleProvenanceObserverV1 provenance{};
  provenance.environment = passive.environment;
  Expect(VerifyActivityGuestRuleProvenanceExactAbiV1(provenance.environment));
  Expect(BeginActivityGuestRuleRefreshV1(provenance, kBase + 0x11B8331,
                                        kPlanner, kPlanner + 0x1A50, kPlanner + 0x15C8));
  RecordActivityGuestRuleEffectReturnV1(provenance, kBase + 0x2BBD32A,
                                       kRule + 0x40, kOutput);
  FinishActivityGuestRuleRefreshV1(provenance);
  ActivityCostSlot12FrameV1 frame{};
  Expect(CostFrame(&fake, frame));
  const auto observed = ReadActivityGuestRuleProvenanceV1(
      provenance, frame, kPlanner, 0x12345678, kGuestId);
  Expect(observed.status == ActivityGuestRuleProvenanceStatusV1::observed);
  Expect(observed.raw_rule_character_count == 2 && observed.filtered_rule_character_count == 1);
  Expect(observed.candidate_membership && observed.filtered_ids[0] == kGuestId);
  const auto rejected = ReadActivityGuestRuleProvenanceV1(
      provenance, frame, kPlanner, 0x12345678, kCandidateId);
  Expect(rejected.status == ActivityGuestRuleProvenanceStatusV1::observed);
  Expect(!rejected.candidate_membership);

  std::cout << "GREEN: 1.20.0.2 native selected/candidate join, arrival, authored-rule provenance\n";
  return 0;
}
