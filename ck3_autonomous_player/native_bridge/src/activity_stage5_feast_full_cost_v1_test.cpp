#include "xar_bridge/activity_stage5_feast_full_cost_v1.hpp"

// Reuse the exact paused planner and normal slot-12 fixture from the Gold
// reader without changing its production implementation or test source.
#define main ActivityStage5GoldFixtureMain
#include "activity_stage5_gold_cost_v1_test.cpp"
#undef main

#include <array>

namespace {

struct NamedFixture {
  Fixture *planner = nullptr;
  std::array<std::int64_t, 4> values{18500000, 0, -100000, 3500000};
  std::array<std::uint32_t, 4> indices{0, 3, 5, 8};
  int calls = 0;
  int fail_at = -1;
  int unmapped_at = -1;
  bool mutate_config_after_last = false;
  bool mutate_frame_after_last = false;
};

bool Named(void *opaque, std::uintptr_t base, std::uintptr_t breakdown,
           std::string_view key, std::uint32_t &index,
           std::int64_t &value) noexcept {
  auto &fixture = *static_cast<NamedFixture *>(opaque);
  if (base != kBase || breakdown != kPlanner + 0x1AD8 ||
      fixture.calls >= 4 || key != kActivityFeastCostKeysV1[fixture.calls])
    return false;
  const auto current = fixture.calls++;
  if (current == fixture.fail_at) return false;
  index = current == fixture.unmapped_at ? 10 : fixture.indices[current];
  value = fixture.values[current];
  if (current == 3 && fixture.mutate_config_after_last)
    fixture.planner->bytes[kPlanner + 0x1600] ^= 1;
  if (current == 3 && fixture.mutate_frame_after_last)
    ++fixture.planner->frame.revision;
  return true;
}

void ExpectNotPublished(const ActivityStage5FeastFullCostResultV1 &result) {
  Expect(result.normal_refresh_sequence == 0);
  for (const auto value : result.configured_cost_raw) Expect(value == 0);
}

} // namespace

int main() {
  Fixture planner{};
  Populate(planner);
  ActivityCostSlot12ObserverV1 passive{};
  passive.environment = {true, true, kActivityCostSlot12ExeSha256V1,
                         kBase, &planner, &Read, &ReadCostFrame};
  NamedFixture named{&planner};
  ActivityStage5FeastFullCostEnvironmentV1 environment{};
  environment.enabled = true;
  environment.gold = Environment(planner, passive);
  environment.invoke_named_cost = &Named;
  environment.named_context = &named;
  const auto expected = planner.frame;

  auto result = ReadActivityStage5FeastFullCostV1(environment, expected);
  Expect(result.status == ActivityStage5FeastFullCostStatusV1::gold_gate_red);
  Expect(result.gold_gate_status ==
         ActivityStage5GoldCostStatusV1::no_normal_refresh);
  Expect(named.calls == 0);
  ExpectNotPublished(result);

  Expect(RecordActivityCostSlot12NormalReturnV1(
      passive, kBase + kActivityCostSlot12ReturnRvaV1, kPlanner));
  result = ReadActivityStage5FeastFullCostV1(environment, expected);
  Expect(result.status == ActivityStage5FeastFullCostStatusV1::observed);
  Expect(result.gold_gate_status == ActivityStage5GoldCostStatusV1::observed);
  Expect(result.frame == expected && result.normal_refresh_sequence == 1);
  Expect(result.resource_indices == named.indices);
  Expect(result.configured_cost_raw == named.values);
  Expect(result.actor_gold_raw == 134000000 && result.scale == 100000);
  Expect(named.calls == 4);

  named.calls = 0;
  named.unmapped_at = 1;
  result = ReadActivityStage5FeastFullCostV1(environment, expected);
  Expect(result.status ==
         ActivityStage5FeastFullCostStatusV1::resource_unmapped);
  Expect(result.gold_gate_status ==
         ActivityStage5GoldCostStatusV1::native_query_failed);
  Expect(named.calls == 2);
  ExpectNotPublished(result);
  named.unmapped_at = -1;

  named.calls = 0;
  named.fail_at = 2;
  result = ReadActivityStage5FeastFullCostV1(environment, expected);
  Expect(result.status ==
         ActivityStage5FeastFullCostStatusV1::named_query_failed);
  Expect(named.calls == 3);
  ExpectNotPublished(result);
  named.fail_at = -1;

  named.calls = 0;
  named.mutate_config_after_last = true;
  result = ReadActivityStage5FeastFullCostV1(environment, expected);
  Expect(result.status == ActivityStage5FeastFullCostStatusV1::gold_gate_red);
  Expect(result.gold_gate_status ==
         ActivityStage5GoldCostStatusV1::configuration_changed);
  ExpectNotPublished(result);
  planner.bytes[kPlanner + 0x1600] ^= 1;
  named.mutate_config_after_last = false;

  named.calls = 0;
  named.mutate_frame_after_last = true;
  result = ReadActivityStage5FeastFullCostV1(environment, expected);
  Expect(result.status == ActivityStage5FeastFullCostStatusV1::gold_gate_red);
  Expect(result.gold_gate_status ==
         ActivityStage5GoldCostStatusV1::configuration_changed);
  ExpectNotPublished(result);
  planner.frame.revision = expected.revision;
  named.mutate_frame_after_last = false;

  std::uint32_t resource_index = 0;
  std::int64_t raw = 0;
  Expect(!InvokeActivityStage5NativeNamedFeastCostV1(
      nullptr, 0, kPlanner + 0x1AD8, "gold", resource_index, raw));
  Expect(!InvokeActivityStage5NativeNamedFeastCostV1(
      nullptr, kBase, kPlanner + 0x1AD8,
      "resource_name_too_long", resource_index, raw));
  return 0;
}
