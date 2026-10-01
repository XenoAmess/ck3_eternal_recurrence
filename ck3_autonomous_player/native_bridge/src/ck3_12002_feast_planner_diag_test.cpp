#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <array>
#include <cstdlib>
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
  bool flip_visibility_after_call = false;

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
  return source == kIdler && source_type == kBase + 0x5514438 &&
                 target_type == kBase + 0x5514460
             ? kGfx
             : 0;
}

bool Visible(void *opaque, std::uintptr_t planner, std::uintptr_t slot,
             bool &output) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  fake.visibility_called = true;
  if (planner != kPlanner || slot != kBase + 0x21603A0) return false;
  output = fake.visible;
  if (fake.flip_visibility_after_call) fake.visible = !fake.visible;
  return true;
}

void Populate(Fake &fake) {
  const std::array<std::uint8_t, 8> owner_write{
      0x49, 0x89, 0xB4, 0x24, 0xA0, 0, 0, 0};
  const std::array<std::uint8_t, 4> widget_read{0x48, 0x8B, 0x59, 0x60};
  const std::array<std::uint8_t, 7> stage_read{
      0x48, 0x63, 0x81, 0xE8, 0x1A, 0, 0};
  fake.Put(kBase + 0x11B2885, owner_write);
  fake.Put(kBase + 0x21603AA, widget_read);
  fake.Put(kBase + 0x11B8693, stage_read);
  fake.Put(kBase + 0x45325C8, kBase + 0x11B2E30);
  fake.Put(kBase + 0x45325C8 + 7 * 8, kBase + 0x21603A0);
  fake.Put(kBase + 0x45325C8 + 11 * 8, kBase + 0xB1F0A0);
  fake.Put(kBase + 0x45325C8 + 12 * 8, kBase + 0x11B5B30);
  fake.Put(kBase + 0x45326A0, kBase + 0x11D3404);

  fake.Put(kBase + 0x5C6A520, kRoot);
  fake.Put(kRoot + 0x10, kIdler);
  fake.Put(kGfx, kBase + 0x44BC408);
  fake.Put(kGfx + 0x88, kHandler);
  fake.Put(kHandler, kBase + 0x44BA890);
  fake.Put(kBase + 0x54DBC00, kActorId);
  fake.Put(kBase + 0x5C67568, kStorage);
  fake.Put(kBase + 0x5C67570, std::uintptr_t{0});
  fake.Put(kStorage + 0x20, kSlots);
  fake.Put(kStorage + 0x2C, std::int32_t{40000});
  fake.Put(kSlots + kActorId * 0x10 + 8, kActor);
  fake.Put(kActor + 0x18, kActorId);

  fake.Put(kHandler + 0x3C0, kPlanner);
  fake.Put(kPlanner, kBase + 0x45325C8);
  fake.Put(kPlanner + 0x10, kBase + 0x45326A0);
  fake.Put(kPlanner + 0xA0, kHandler);
  fake.Put(kPlanner + 0x60, kWidget);
  fake.Put(kPlanner + 0x1AE8, std::int32_t{2});
  fake.Put(kPlanner + 0x1500, kType);

  fake.Put(kHandler + 0x3D8, kHost);
  fake.Put(kHost, kBase + 0x457A138);
  fake.Put(kHost + 0x10, kBase + 0x457A110);
  fake.Put(kHost + 0xA0, kHandler);
  fake.Put(kHost + 0xD0, kActorId);
  fake.Put(kHost + 0x238, kType);
  fake.Put(kType, kBase + 0x48BFE50);
  fake.PutBytes(kType + 0x18, "activity_feast");
  fake.Put(kType + 0x28, std::uint64_t{14});
  fake.Put(kType + 0x30, std::uint64_t{15});
}

ActivityPlannerDiagEnvironmentV1 Env(Fake &fake) {
  return {true, xar::bridge::kActivityPlanner12002ExeSha256V1, kBase,
          &fake, &Read, &Frame, &Cast, &Visible};
}
} // namespace

int main() {
  Fake fake{};
  Populate(fake);
  const auto expected = fake.frame;
  auto result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::observed);
  Expect(result.value.planner_present && result.value.widget_attached);
  Expect(!result.value.widget_visible && fake.visibility_called);
  Expect(result.value.stage == 2);
  Expect(result.value.host_view_activity_key_known);
  Expect(std::string_view(result.value.host_view_activity_key.data(),
                          result.value.host_view_activity_key_size) ==
         "activity_feast");

  xar::bridge::ActivityPlannerIdentityV1 identity{};
  Expect(xar::bridge::ResolveActivityPlannerIdentityV1(Env(fake), expected, identity));
  Expect(identity.actor == kActor && identity.handler == kHandler &&
         identity.planner == kPlanner && identity.activity_type == kType && identity.stage == 2);
  fake.Put(kHost + 0xD0, std::int32_t{0});
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::observed);
  Expect(!result.value.host_view_activity_key_known);
  fake.Put(kHost + 0xD0, kActorId);

  fake.visible = true;
  fake.Put(kPlanner + 0x1AE8, std::int32_t{5});
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::observed);
  Expect(result.value.widget_visible && result.value.stage == 5);

  fake.Put(kPlanner + 0x60, std::uintptr_t{0});
  fake.visible = false;
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::observed);
  Expect(!result.value.widget_attached && !result.value.widget_visible);

  fake.Put(kHandler + 0x3C0, std::uintptr_t{0});
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::planner_absent);
  Expect(!result.value.planner_present);

  fake.Put(kHandler + 0x3C0, kPlanner);
  fake.Put(kPlanner + 0xA0, std::uintptr_t{0});
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::native_identity_mismatch);
  fake.Put(kPlanner + 0xA0, kHandler);

  fake.Put(kPlanner + 0x60, kWidget);
  fake.flip_visibility_after_call = true;
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::native_sample_changed);
  fake.flip_visibility_after_call = false;

  auto environment = Env(fake);
  environment.admitted_executable_sha256 = "wrong-build";
  result = xar::bridge::ReadActivityPlannerDiagV1(environment, expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::exact_build_rejected);
  fake.Put(kBase + 0x21603AA, std::array<std::uint8_t, 4>{});
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::exact_build_rejected);
  fake.Put(kBase + 0x21603AA,
           std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x60});
  fake.frame.revision = 4;
  result = xar::bridge::ReadActivityPlannerDiagV1(Env(fake), expected);
  Expect(result.status == ActivityPlannerDiagStatusV1::frame_changed);

  std::cout << "GREEN: 1.20.0.2 planner diagnostic and production identity resolver\n";
  return 0;
}
