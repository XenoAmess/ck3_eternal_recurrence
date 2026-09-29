#include "xar_bridge/activity_stage5_canstart_read_v1.hpp"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string_view>
#include <unordered_map>

namespace {
using xar::bridge::ActivityPlannerDiagFrameV1;
using xar::bridge::ActivityStage5CanStartEnvironmentV1;
using xar::bridge::ActivityStage5CanStartStatusV1;

constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kRoot = 0x10000000;
constexpr std::uintptr_t kIdler = 0x10001000;
constexpr std::uintptr_t kGfx = 0x10002000;
constexpr std::uintptr_t kHandler = 0x10003000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::uintptr_t kWidget = 0x10005000;
constexpr std::uintptr_t kType = 0x10006000;
constexpr std::uintptr_t kStorage = 0x10007000;
constexpr std::uintptr_t kSlots = 0x10008000;
constexpr std::uintptr_t kActor = 0x10009000;
constexpr std::int32_t kActorId = 29829;

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{3, 53219928, kActorId, true, true, true,
                                   true};
  bool can_start = true;
  bool drift_on_evaluate = false;
  std::uint32_t evaluation_count = 0;

  template <typename T> void Put(std::uintptr_t at, const T &value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(value); ++index)
      bytes[at + index] = data[index];
  }
  void PutBytes(std::uintptr_t at, std::string_view value) {
    for (std::size_t index = 0; index < value.size(); ++index)
      bytes[at + index] = static_cast<std::uint8_t>(value[index]);
  }
};

void Expect(bool condition) {
  if (!condition) std::abort();
}

bool Read(void *opaque, std::uintptr_t address, void *output,
          std::size_t size) noexcept {
  const auto &fake = *static_cast<Fake *>(opaque);
  auto *destination = static_cast<std::uint8_t *>(output);
  for (std::size_t index = 0; index < size; ++index) {
    const auto it = fake.bytes.find(address + index);
    if (it == fake.bytes.end()) return false;
    destination[index] = it->second;
  }
  return true;
}

bool Frame(void *opaque, ActivityPlannerDiagFrameV1 &output) noexcept {
  output = static_cast<Fake *>(opaque)->frame;
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

bool Visible(void *, std::uintptr_t planner, std::uintptr_t slot,
             bool &output) noexcept {
  if (planner != kPlanner || slot != kBase + 0x1F30970) return false;
  output = true;
  return true;
}

bool Evaluate(void *opaque, std::uintptr_t planner, bool &output) noexcept {
  if (planner != kPlanner) return false;
  auto &fake = *static_cast<Fake *>(opaque);
  ++fake.evaluation_count;
  output = fake.can_start;
  if (fake.drift_on_evaluate) fake.frame.revision = 4;
  return true;
}

void Populate(Fake &fake) {
  fake.Put(kBase + 0x10AC0F3,
           std::array<std::uint8_t, 7>{0x49, 0x89, 0xB6, 0xD0, 0, 0, 0});
  fake.Put(kBase + 0x1F3097A,
           std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x78});
  fake.Put(kBase + 0x10B0DC3,
           std::array<std::uint8_t, 7>{0x48, 0x63, 0x81, 0xB0, 0x1A, 0, 0});
  fake.Put(kBase + 0x10B0DA0,
           std::array<std::uint8_t, 7>{0x48, 0x89, 0x5C, 0x24, 0x10, 0x48,
                                        0x89});
  fake.Put(kBase + 0x10B1018,
           std::array<std::uint8_t, 7>{0x48, 0x8D, 0x91, 0x30, 0x15, 0, 0});
  fake.Put(kBase + 0x41205F0, kBase + 0x10AC480);
  fake.Put(kBase + 0x41205F0 + 7 * 8, kBase + 0x1F30970);
  fake.Put(kBase + 0x41205F0 + 11 * 8, kBase + 0xAA33F0);
  fake.Put(kBase + 0x41205F0 + 12 * 8, kBase + 0x10AE180);
  fake.Put(kBase + 0x41206C8, kBase + 0x10C8454);

  fake.Put(kBase + 0x570F7B8, kRoot);
  fake.Put(kRoot + 0x10, kIdler);
  fake.Put(kGfx, kBase + 0x40B1D30);
  fake.Put(kGfx + 0x88, kHandler);
  fake.Put(kHandler, kBase + 0x40AF630);
  fake.Put(kBase + 0x4FE7EE0, kActorId);
  fake.Put(kBase + 0x570C130, kStorage);
  fake.Put(kBase + 0x570C138, std::uintptr_t{0});
  fake.Put(kStorage + 0x20, kSlots);
  fake.Put(kStorage + 0x2C, std::int32_t{40000});
  fake.Put(kSlots + kActorId * 0x10 + 8, kActor);
  fake.Put(kActor + 0x18, kActorId);

  fake.Put(kHandler + 0x3C0, kPlanner);
  fake.Put(kHandler + 0x3D8, std::uintptr_t{0});
  fake.Put(kPlanner, kBase + 0x41205F0);
  fake.Put(kPlanner + 0x10, kBase + 0x41206C8);
  fake.Put(kPlanner + 0xD0, kHandler);
  fake.Put(kPlanner + 0x78, kWidget);
  fake.Put(kPlanner + 0x1AB0, std::int32_t{5});
  fake.Put(kPlanner + 0x1530, kType);
  fake.Put(kType, kBase + 0x440E308);
  fake.PutBytes(kType + 0x18, "activity_feast");
  fake.Put(kType + 0x28, std::uint64_t{14});
  fake.Put(kType + 0x30, std::uint64_t{15});
}

ActivityStage5CanStartEnvironmentV1 Env(Fake &fake) {
  return {{true, xar::bridge::kActivityPlannerDiagExeSha256V1, kBase,
           &fake, &Read, &Frame, &Cast, &Visible},
          &Evaluate};
}
} // namespace

int main() {
  Fake fake{};
  Populate(fake);
  const auto expected = fake.frame;
  auto result = xar::bridge::ReadActivityStage5CanStartV1(Env(fake), expected);
  Expect(result.status == ActivityStage5CanStartStatusV1::observed &&
         result.final_can_start && fake.evaluation_count == 1);

  fake.can_start = false;
  result = xar::bridge::ReadActivityStage5CanStartV1(Env(fake), expected);
  Expect(result.status == ActivityStage5CanStartStatusV1::observed &&
         !result.final_can_start && fake.evaluation_count == 2);

  fake.Put(kPlanner + 0x1AB0, std::int32_t{1});
  result = xar::bridge::ReadActivityStage5CanStartV1(Env(fake), expected);
  Expect(result.status == ActivityStage5CanStartStatusV1::not_stage5 &&
         fake.evaluation_count == 2);
  fake.Put(kPlanner + 0x1AB0, std::int32_t{5});

  fake.PutBytes(kType + 0x18, "activity_war__");
  result = xar::bridge::ReadActivityStage5CanStartV1(Env(fake), expected);
  Expect(result.status == ActivityStage5CanStartStatusV1::selected_type_mismatch &&
         fake.evaluation_count == 2);
  fake.PutBytes(kType + 0x18, "activity_feast");

  fake.drift_on_evaluate = true;
  result = xar::bridge::ReadActivityStage5CanStartV1(Env(fake), expected);
  Expect(result.status == ActivityStage5CanStartStatusV1::frame_changed &&
         fake.evaluation_count == 3);
  std::cout << "GREEN: exact-build private activity stage-5 CanStart read\n";
}
