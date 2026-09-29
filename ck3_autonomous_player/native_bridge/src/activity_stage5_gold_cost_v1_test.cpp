#include "xar_bridge/activity_stage5_gold_cost_v1.hpp"

#include <windows.h>

#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <string_view>
#include <unordered_map>

namespace {

using namespace xar::bridge;
constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kRoot = 0x10000000;
constexpr std::uintptr_t kIdler = 0x10001000;
constexpr std::uintptr_t kGfx = 0x10002000;
constexpr std::uintptr_t kHandler = 0x10003000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::uintptr_t kWidget = 0x10005000;
constexpr std::uintptr_t kHost = 0x10006000;
constexpr std::uintptr_t kType = 0x10007000;
constexpr std::uintptr_t kStorage = 0x10008000;
constexpr std::uintptr_t kSlots = 0x10009000;
constexpr std::uintptr_t kActor = 0x1000A000;
constexpr std::uintptr_t kExtension = 0x1000B000;
constexpr std::int32_t kActorId = 29829;

void Expect(bool condition) {
  if (!condition) std::abort();
}

struct Fixture {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{3, 53219928, kActorId, true, true,
                                   true, true};
  std::int64_t named_gold = 18500000;
  int native_calls = 0;
  bool mutate_config_in_getter = false;
  bool mutate_revision_in_getter = false;
  bool fail_getter = false;

  template <typename T>
  void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(value); ++index)
      bytes[address + index] = source[index];
  }

  void PutBytes(std::uintptr_t address, std::string_view value) {
    for (std::size_t index = 0; index < value.size(); ++index)
      bytes[address + index] = static_cast<std::uint8_t>(value[index]);
  }

  void Fill(std::uintptr_t address, std::size_t count) {
    for (std::size_t index = 0; index < count; ++index)
      bytes[address + index] = 0;
  }
};

bool Read(void *context, std::uintptr_t address, void *output,
          std::size_t count) noexcept {
  const auto &fixture = *static_cast<Fixture *>(context);
  auto *destination = static_cast<std::uint8_t *>(output);
  for (std::size_t index = 0; index < count; ++index) {
    const auto found = fixture.bytes.find(address + index);
    if (found == fixture.bytes.end()) return false;
    destination[index] = found->second;
  }
  return true;
}

bool ReadDiagFrame(void *context,
                   ActivityPlannerDiagFrameV1 &output) noexcept {
  output = static_cast<Fixture *>(context)->frame;
  return true;
}

bool ReadCostFrame(void *context,
                   ActivityCostSlot12FrameV1 &output) noexcept {
  const auto &frame = static_cast<Fixture *>(context)->frame;
  output = {static_cast<std::int32_t>(frame.date_raw),
            frame.actor_character_id, GetCurrentThreadId(), frame.paused};
  return true;
}

std::uintptr_t Cast(void *, std::uintptr_t source,
                    std::uintptr_t source_type,
                    std::uintptr_t target_type) noexcept {
  return source == kIdler && source_type == kBase + 0x501EF28 &&
                 target_type == kBase + 0x501EF50
             ? kGfx
             : 0;
}

bool Visible(void *, std::uintptr_t planner,
             std::uintptr_t slot, bool &result) noexcept {
  result = planner == kPlanner && slot == kBase + 0x1F30970;
  return result;
}

bool NamedGold(void *context, std::uintptr_t base,
               std::uintptr_t breakdown, std::int64_t &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(context);
  if (base != kBase || breakdown != kPlanner + 0x1AD8) return false;
  ++fixture.native_calls;
  if (fixture.mutate_config_in_getter)
    fixture.bytes[kPlanner + 0x1600] ^= 1;
  if (fixture.mutate_revision_in_getter) ++fixture.frame.revision;
  if (fixture.fail_getter) return false;
  output = fixture.named_gold;
  return true;
}

void Populate(Fixture &fixture) {
  fixture.Put(kBase + 0x10AC0F3,
              std::array<std::uint8_t, 7>{0x49, 0x89, 0xB6, 0xD0, 0, 0, 0});
  fixture.Put(kBase + 0x1F3097A,
              std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x78});
  fixture.Put(kBase + 0x10B0DC3,
              std::array<std::uint8_t, 7>{0x48, 0x63, 0x81, 0xB0, 0x1A, 0, 0});
  fixture.Put(kBase + 0x41205F0, kBase + 0x10AC480);
  fixture.Put(kBase + 0x41205F0 + 7 * 8, kBase + 0x1F30970);
  fixture.Put(kBase + 0x41205F0 + 11 * 8, kBase + 0xAA33F0);
  fixture.Put(kBase + 0x41205F0 + 12 * 8, kBase + 0x10AE180);
  fixture.Put(kBase + 0x41206C8, kBase + 0x10C8454);
  fixture.Put(kBase + kActivityGetCostByNameRvaV1,
              std::array<std::uint8_t, 13>{
                  0x48, 0x89, 0x5C, 0x24, 0x18, 0x56, 0x57,
                  0x41, 0x56, 0x48, 0x83, 0xEC, 0x30});
  fixture.Put(kBase + 0x2CD9795,
              std::array<std::uint8_t, 4>{0x49, 0x8B, 0x0C, 0xC6});
  fixture.Put(kBase + 0xBDC496,
              std::array<std::uint8_t, 7>{
                  0x48, 0x8B, 0x80, 0, 0x01, 0, 0});

  fixture.Put(kBase + 0x570F7B8, kRoot);
  fixture.Put(kRoot + 0x10, kIdler);
  fixture.Put(kGfx, kBase + 0x40B1D30);
  fixture.Put(kGfx + 0x88, kHandler);
  fixture.Put(kHandler, kBase + 0x40AF630);
  fixture.Put(kBase + 0x4FE7EE0, kActorId);
  fixture.Put(kBase + 0x570C130, kStorage);
  fixture.Put(kBase + 0x570C138, std::uintptr_t{0});
  fixture.Put(kStorage + 0x20, kSlots);
  fixture.Put(kStorage + 0x2C, std::int32_t{40000});
  fixture.Put(kSlots + kActorId * 0x10 + 8, kActor);
  fixture.Put(kActor + 0x18, kActorId);
  fixture.Put(kActor + 0x1A8, kExtension);
  fixture.Put(kExtension + 0x100, std::int64_t{134000000});

  fixture.Put(kHandler + 0x3C0, kPlanner);
  fixture.Put(kHandler + 0x3D8, kHost);
  fixture.Fill(kPlanner + 0x1530, 0x1AD8 - 0x1530);
  fixture.Put(kPlanner, kBase + 0x41205F0);
  fixture.Put(kPlanner + 0x10, kBase + 0x41206C8);
  fixture.Put(kPlanner + 0xD0, kHandler);
  fixture.Put(kPlanner + 0x78, kWidget);
  fixture.Put(kPlanner + 0x1530, kType);
  fixture.Put(kPlanner + 0x1AB0, std::int32_t{5});
  for (std::size_t index = 0; index < 10; ++index)
    fixture.Put(kPlanner + 0x1AD8 + 0x50 + index * 0x90 + 0x78,
                std::int64_t{index == 0 ? 10000000 : 0});

  fixture.Put(kHost, kBase + 0x4166528);
  fixture.Put(kHost + 0x10, kBase + 0x4166620);
  fixture.Put(kHost + 0xD0, kHandler);
  fixture.Put(kHost + 0x100, kActorId);
  fixture.Put(kHost + 0x268, kType);
  fixture.Put(kType, kBase + 0x440E308);
  fixture.PutBytes(kType + 0x18, "activity_feast");
  fixture.Put(kType + 0x28, std::uint64_t{14});
  fixture.Put(kType + 0x30, std::uint64_t{15});
}

ActivityStage5GoldCostEnvironmentV1 Environment(
    Fixture &fixture, ActivityCostSlot12ObserverV1 &observer) {
  ActivityStage5GoldCostEnvironmentV1 environment{};
  environment.enabled = true;
  environment.diagnostic = {
      true, kActivityPlannerDiagExeSha256V1, kBase, &fixture,
      &Read, &ReadDiagFrame, &Cast, &Visible};
  environment.passive_cost = &observer;
  environment.invoke_gold_cost = &NamedGold;
  return environment;
}

} // namespace

int main() {
  Fixture fixture{};
  Populate(fixture);
  ActivityCostSlot12ObserverV1 observer{};
  observer.environment = {
      true, true, kActivityCostSlot12ExeSha256V1,
      kBase, &fixture, &Read, &ReadCostFrame};
  auto environment = Environment(fixture, observer);
  const auto expected = fixture.frame;
  auto result = ReadActivityStage5GoldCostV1(environment, expected);
  Expect(result.status ==
             ActivityStage5GoldCostStatusV1::no_normal_refresh &&
         fixture.native_calls == 0);
  Expect(RecordActivityCostSlot12NormalReturnV1(
      observer, kBase + kActivityCostSlot12ReturnRvaV1, kPlanner));
  result = ReadActivityStage5GoldCostV1(environment, expected);
  Expect(result.status == ActivityStage5GoldCostStatusV1::observed);
  Expect(result.gold_cost_raw == 18500000 &&
         result.actor_gold_raw == 134000000 &&
         result.scale == 100000 && result.normal_refresh_sequence == 1);
  Expect(result.gold_cost_raw != observer.latest.raw_aggregate[0]);
  Expect(fixture.native_calls == 1);

  fixture.Put(kPlanner + 0x1AB0, std::int32_t{2});
  result = ReadActivityStage5GoldCostV1(environment, expected);
  Expect(result.status == ActivityStage5GoldCostStatusV1::not_feast_stage_five);
  Expect(fixture.native_calls == 1);
  fixture.Put(kPlanner + 0x1AB0, std::int32_t{5});
  fixture.mutate_config_in_getter = true;
  result = ReadActivityStage5GoldCostV1(environment, expected);
  Expect(result.status == ActivityStage5GoldCostStatusV1::configuration_changed);
  fixture.mutate_config_in_getter = false;
  fixture.bytes[kPlanner + 0x1600] ^= 1;
  fixture.mutate_revision_in_getter = true;
  result = ReadActivityStage5GoldCostV1(environment, expected);
  Expect(result.status == ActivityStage5GoldCostStatusV1::configuration_changed);
  fixture.mutate_revision_in_getter = false;
  fixture.frame.revision = expected.revision;
  fixture.fail_getter = true;
  result = ReadActivityStage5GoldCostV1(environment, expected);
  Expect(result.status == ActivityStage5GoldCostStatusV1::native_query_failed);
  fixture.fail_getter = false;
  fixture.Put(kBase + 0x2CD9795,
              std::array<std::uint8_t, 4>{0, 0, 0, 0});
  result = ReadActivityStage5GoldCostV1(environment, expected);
  Expect(result.status == ActivityStage5GoldCostStatusV1::exact_build_rejected);
  return 0;
}
