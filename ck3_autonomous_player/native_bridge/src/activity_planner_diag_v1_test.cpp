#include "xar_bridge/activity_planner_diag_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>
#include <unordered_map>

namespace {
using xar::bridge::ActivityPlannerDiagEnvironmentV1;
using xar::bridge::ActivityPlannerDiagFrameV1;
using xar::bridge::ActivityPlannerDiagStatusV1;

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
constexpr std::int32_t kActorId = 29829;

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{3, 53219928, kActorId, true, true, true,
                                   true};
  bool visible = false;
  bool visibility_called = false;

  template <typename T> void Put(std::uintptr_t at, const T &value) {
    const auto *data = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i) bytes[at + i] = data[i];
  }

  void PutBytes(std::uintptr_t at, std::string_view data) {
    for (std::size_t i = 0; i < data.size(); ++i)
      bytes[at + i] = static_cast<std::uint8_t>(data[i]);
  }
};

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
             ? kGfx
             : 0;
}

bool Visible(void *opaque, std::uintptr_t planner, std::uintptr_t slot,
             bool &output) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  fake.visibility_called = true;
  if (planner != kPlanner || slot != kBase + 0x1F30970) return false;
  output = fake.visible;
  return true;
}

void Populate(Fake &fake) {
  const std::array<std::uint8_t, 7> owner_write{
      0x49, 0x89, 0xB6, 0xD0, 0, 0, 0};
  const std::array<std::uint8_t, 4> widget_read{0x48, 0x8B, 0x59, 0x78};
  const std::array<std::uint8_t, 7> stage_read{
      0x48, 0x63, 0x81, 0xB0, 0x1A, 0, 0};
  fake.Put(kBase + 0x10AC0F3, owner_write);
  fake.Put(kBase + 0x1F3097A, widget_read);
  fake.Put(kBase + 0x10B0DC3, stage_read);
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
  fake.Put(kPlanner, kBase + 0x41205F0);
  fake.Put(kPlanner + 0x10, kBase + 0x41206C8);
  fake.Put(kPlanner + 0xD0, kHandler);
  fake.Put(kPlanner + 0x78, kWidget);
  fake.Put(kPlanner + 0x1AB0, std::int32_t{2});

  fake.Put(kHandler + 0x3D8, kHost);
  fake.Put(kHost, kBase + 0x4166528);
  fake.Put(kHost + 0x10, kBase + 0x4166620);
  fake.Put(kHost + 0xD0, kHandler);
  fake.Put(kHost + 0x100, kActorId);
  fake.Put(kHost + 0x268, kType);
  fake.Put(kType, kBase + 0x440E308);
  fake.PutBytes(kType + 0x18, "activity_feast");
  fake.Put(kType + 0x28, std::uint64_t{14});
  fake.Put(kType + 0x30, std::uint64_t{15});
}

ActivityPlannerDiagEnvironmentV1 Env(Fake &fake) {
  return {true, xar::bridge::kActivityPlannerDiagExeSha256V1, kBase,
          &fake, &Read, &Frame, &Cast, &Visible};
}
} // namespace

int main() {
  Fake fake{};
  Populate(fake);
  const auto expected = fake.frame;
  auto result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  assert(result.status == ActivityPlannerDiagStatusV1::observed);
  assert(result.value.planner_present && result.value.widget_attached);
  assert(!result.value.widget_visible && fake.visibility_called);
  assert(result.value.stage == 2);
  assert(result.value.host_view_activity_key_known);
  assert(std::string_view(result.value.host_view_activity_key.data(),
                          result.value.host_view_activity_key_size) ==
         "activity_feast");

  fake.visible = true;
  fake.Put(kPlanner + 0x1AB0, std::int32_t{5});
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  assert(result.status == ActivityPlannerDiagStatusV1::observed);
  assert(result.value.widget_visible && result.value.stage == 5);

  fake.Put(kPlanner + 0x78, std::uintptr_t{0});
  fake.visible = false;
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  assert(result.status == ActivityPlannerDiagStatusV1::observed);
  assert(!result.value.widget_attached && !result.value.widget_visible);

  fake.Put(kHandler + 0x3C0, std::uintptr_t{0});
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  assert(result.status == ActivityPlannerDiagStatusV1::planner_absent);
  assert(!result.value.planner_present);

  fake.Put(kHandler + 0x3C0, kPlanner);
  fake.Put(kPlanner + 0xD0, std::uintptr_t{0});
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  assert(result.status == ActivityPlannerDiagStatusV1::native_identity_mismatch);
  fake.Put(kPlanner + 0xD0, kHandler);

  auto environment = Env(fake);
  environment.admitted_executable_sha256 = "wrong-build";
  result = xar::bridge::ReadActivityPlannerDiagV1(environment, expected);
  assert(result.status == ActivityPlannerDiagStatusV1::exact_build_rejected);
  fake.frame.revision = 4;
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  assert(result.status == ActivityPlannerDiagStatusV1::frame_changed);

  std::cout << "GREEN: exact-build private activity planner diagnostic\n";
}
