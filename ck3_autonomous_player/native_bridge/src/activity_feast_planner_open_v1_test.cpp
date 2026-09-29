#include "xar_bridge/activity_feast_planner_open_v1.hpp"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string_view>
#include <unordered_map>

namespace {
using xar::bridge::ActivityFeastPlannerOpenEnvironmentV1;
using xar::bridge::ActivityFeastPlannerOpenStatusV1;
using xar::bridge::ActivityPlannerDiagFrameV1;

constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kRoot = 0x10000000;
constexpr std::uintptr_t kIdler = 0x10001000;
constexpr std::uintptr_t kGfx = 0x10002000;
constexpr std::uintptr_t kHandler = 0x10003000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::uintptr_t kWidget = 0x10005000;
constexpr std::uintptr_t kType = 0x10007000;
constexpr std::uintptr_t kStorage = 0x10008000;
constexpr std::uintptr_t kSlots = 0x10009000;
constexpr std::uintptr_t kActor = 0x1000A000;
constexpr std::uintptr_t kManager = 0x1000B000;
constexpr std::uintptr_t kTypes = 0x1000C000;
constexpr std::uintptr_t kInitialType = 0x1000E000;
constexpr std::int32_t kActorId = 29829;

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{3, 53219928, kActorId, true, true, true,
                                   true};
  bool visible = false;
  bool bad_post = false;
  std::int32_t stage_after_dispatch = 2;
  bool wrong_selected_type = false;
  std::uint32_t dispatches = 0;

  template <typename T> void Put(std::uintptr_t at, const T &value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[at + i] = data[i];
  }
  void PutBytes(std::uintptr_t at, std::string_view data) {
    for (std::size_t i = 0; i < data.size(); ++i)
      bytes[at + i] = static_cast<std::uint8_t>(data[i]);
  }
};

void Expect(bool condition) {
  if (!condition) std::abort();
}

bool Read(void *opaque, std::uintptr_t at, void *output,
          std::size_t size) noexcept {
  const auto &fake = *static_cast<Fake *>(opaque);
  auto *destination = static_cast<std::uint8_t *>(output);
  for (std::size_t i = 0; i < size; ++i) {
    const auto it = fake.bytes.find(at + i);
    if (it == fake.bytes.end()) return false;
    destination[i] = it->second;
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
             ? kGfx : 0;
}

bool Visible(void *opaque, std::uintptr_t planner, std::uintptr_t slot,
             bool &output) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (planner != kPlanner || slot != kBase + 0x1F30970) return false;
  output = fake.visible;
  return true;
}

bool Dispatch(void *opaque, std::uintptr_t handler,
             std::uintptr_t type) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (handler != kHandler || type != kType) return false;
  ++fake.dispatches;
  fake.Put(kPlanner + 0x1530, fake.wrong_selected_type ? kInitialType : kType);
  fake.Put(kPlanner + 0x1AB0, fake.stage_after_dispatch);
  if (!fake.bad_post) fake.visible = true;
  return true;
}

void Populate(Fake &fake) {
  fake.Put(kBase + 0x10AC0F3,
           std::array<std::uint8_t, 7>{0x49, 0x89, 0xB6, 0xD0, 0, 0, 0});
  fake.Put(kBase + 0x1F3097A,
           std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x78});
  fake.Put(kBase + 0x10B0DC3,
           std::array<std::uint8_t, 7>{0x48, 0x63, 0x81, 0xB0, 0x1A, 0, 0});
  fake.Put(kBase + 0x41205F0, kBase + 0x10AC480);
  fake.Put(kBase + 0x41205F0 + 7 * 8, kBase + 0x1F30970);
  fake.Put(kBase + 0x41205F0 + 11 * 8, kBase + 0xAA33F0);
  fake.Put(kBase + 0x41205F0 + 12 * 8, kBase + 0x10AE180);
  fake.Put(kBase + 0x41206C8, kBase + 0x10C8454);
  fake.Put(kBase + 0xA79700,
           std::array<std::uint8_t, 8>{0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74});
  fake.Put(kBase + 0xA79717,
           std::array<std::uint8_t, 8>{0xE8,0x74,0xFF,0xFF,0xFF,0x81,0xFF,0xA3});
  fake.Put(kBase + 0x15046C3,
           std::array<std::uint8_t, 9>{0xE8,0x78,0x9A,0x38,0xFF,0x4C,0x8B,0x70,0x68});
  fake.Put(kBase + 0x219A7DA,
           std::array<std::uint8_t, 7>{0x48,0x8B,0x05,0x47,0x57,0x62,0x03});
  fake.Put(kBase + 0x57BFF28, kInitialType);
  fake.Put(kBase + 0x4FE3DB0, kBase + 0x40DB298);
  fake.Put(kBase + 0x40DB298 + 0x58, kBase + 0x80DCB0);
  fake.Put(kBase + 0x40DB298 + 0x60, kBase + 0x80DCB0);

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
  fake.Put(kPlanner + 0x1AB0, std::int32_t{2});
  fake.Put(kPlanner + 0x1530, kInitialType);
  fake.Put(kBase + 0x570BE98, kManager);
  fake.Put(kManager + 0x68, kTypes);
  fake.Put(kManager + 0x74, std::int32_t{1});
  fake.Put(kTypes, kType);
  fake.Put(kType, kBase + 0x440E308);
  fake.Put(kType + 0xA88, std::uintptr_t{0});
  fake.PutBytes(kType + 0x18, "activity_feast");
  fake.Put(kType + 0x28, std::uint64_t{14});
  fake.Put(kType + 0x30, std::uint64_t{15});
}

ActivityFeastPlannerOpenEnvironmentV1 Env(Fake &fake) {
  ActivityFeastPlannerOpenEnvironmentV1 environment{};
  environment.diagnostic =
      {true, xar::bridge::kActivityPlannerDiagExeSha256V1, kBase,
       &fake, &Read, &Frame, &Cast, &Visible};
  environment.dispatch = &Dispatch;
  return environment;
}
} // namespace

int main() {
  Fake success{};
  Populate(success);
  auto result = xar::bridge::OpenActivityFeastPlannerV1(
      Env(success), success.frame);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::opened);
  Expect(result.native_dispatch_invoked);
  Expect(result.selected_feast_verified);
  Expect(result.after.value.widget_visible && result.after.value.stage == 2);
  Expect(success.dispatches == 1);

  Fake category_stage{};
  Populate(category_stage);
  category_stage.Put(kType + 0xA88, std::uintptr_t{0x1000F000});
  category_stage.stage_after_dispatch = 1;
  result = xar::bridge::OpenActivityFeastPlannerV1(
      Env(category_stage), category_stage.frame);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::opened);
  Expect(result.selected_feast_verified);
  Expect(result.after.value.widget_visible && result.after.value.stage == 1);
  Expect(category_stage.dispatches == 1);
  result = xar::bridge::OpenActivityFeastPlannerV1(
      Env(category_stage), category_stage.frame);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::already_open);
  Expect(result.selected_feast_verified && category_stage.dispatches == 1);

  Fake unexpected_stage{};
  Populate(unexpected_stage);
  unexpected_stage.stage_after_dispatch = 1;
  result = xar::bridge::OpenActivityFeastPlannerV1(
      Env(unexpected_stage), unexpected_stage.frame);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::postcondition_failed);
  Expect(result.selected_feast_verified);

  Fake wrong_type{};
  Populate(wrong_type);
  wrong_type.wrong_selected_type = true;
  wrong_type.stage_after_dispatch = 1;
  wrong_type.Put(kType + 0xA88, std::uintptr_t{0x1000F000});
  result = xar::bridge::OpenActivityFeastPlannerV1(
      Env(wrong_type), wrong_type.frame);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::postcondition_failed);
  Expect(!result.selected_feast_verified);
  result = xar::bridge::OpenActivityFeastPlannerV1(Env(success), success.frame);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::already_open);
  Expect(success.dispatches == 1);

  Fake missing{};
  Populate(missing);
  missing.Put(kManager + 0x74, std::int32_t{0});
  result = xar::bridge::OpenActivityFeastPlannerV1(Env(missing), missing.frame);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::type_unavailable);
  Expect(missing.dispatches == 0);

  Fake other_selection{};
  Populate(other_selection);
  other_selection.Put(kPlanner + 0x1530, std::uintptr_t{0});
  result = xar::bridge::OpenActivityFeastPlannerV1(
      Env(other_selection), other_selection.frame);
  Expect(result.status ==
         ActivityFeastPlannerOpenStatusV1::native_precondition_failed);
  Expect(other_selection.dispatches == 0);

  Fake failed{};
  Populate(failed);
  failed.bad_post = true;
  result = xar::bridge::OpenActivityFeastPlannerV1(Env(failed), failed.frame);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::postcondition_failed);
  Expect(result.native_dispatch_invoked && failed.dispatches == 1);

  Fake changed{};
  Populate(changed);
  const auto expected = changed.frame;
  ++changed.frame.revision;
  result = xar::bridge::OpenActivityFeastPlannerV1(Env(changed), expected);
  Expect(result.status == ActivityFeastPlannerOpenStatusV1::frame_changed);
  Expect(changed.dispatches == 0);

  std::cout << "GREEN: exact-build private feast planner open boundary\n";
}
