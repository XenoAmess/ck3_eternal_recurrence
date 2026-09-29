#include "xar_bridge/activity_cost_slot12_passive_v1.hpp"

#include <windows.h>

#include <array>
#include <cassert>
#include <cstring>

namespace {

constexpr std::uintptr_t kBase = 0x10000000;
constexpr std::uintptr_t kPlanner = 0x20000000;
constexpr std::uintptr_t kType = 0x30000000;
constexpr std::uintptr_t kCategoryRows = 0x40000000;
constexpr std::uintptr_t kCostOptionRows = 0x50000000;

struct Fixture {
  std::array<std::uint8_t, 0x2500> planner{};
  std::array<std::uint8_t, 0x60> type{};
  std::array<std::uint8_t, 0x10> category_rows{};
  std::array<std::uint8_t, 0x38> cost_option_rows{};
  std::array<std::uint8_t, 14> prologue{
      0x48, 0x89, 0x5C, 0x24, 0x20, 0x55, 0x56, 0x57,
      0x41, 0x54, 0x41, 0x55, 0x41, 0x56};
  std::array<std::uint8_t, 5> slot12_call{
      0xE8, 0x81, 0x49, 0x00, 0x00};
  xar::bridge::ActivityCostSlot12FrameV1 frame{
      53219928, 29829, GetCurrentThreadId(), true};
};

template <typename T>
void Put(std::array<std::uint8_t, 0x2500> &buffer,
         std::size_t offset, T value) {
  assert(offset + sizeof(T) <= buffer.size());
  std::memcpy(buffer.data() + offset, &value, sizeof(T));
}

template <typename T>
void PutType(std::array<std::uint8_t, 0x60> &buffer,
             std::size_t offset, T value) {
  assert(offset + sizeof(T) <= buffer.size());
  std::memcpy(buffer.data() + offset, &value, sizeof(T));
}

bool Read(void *opaque, std::uintptr_t address, void *output,
          std::size_t bytes) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  const auto copy = [&](std::uintptr_t base, const auto &source) {
    if (address < base || address - base > source.size() ||
        bytes > source.size() - (address - base))
      return false;
    std::memcpy(output, source.data() + (address - base), bytes);
    return true;
  };
  if (copy(kPlanner, fixture.planner) || copy(kType, fixture.type) ||
      copy(kCategoryRows, fixture.category_rows) ||
      copy(kCostOptionRows, fixture.cost_option_rows))
    return true;
  if (copy(kBase + xar::bridge::kActivityCostRefreshRvaV1,
           fixture.prologue) ||
      copy(kBase + xar::bridge::kActivityCostSlot12ReturnRvaV1 - 5,
           fixture.slot12_call))
    return true;
  return false;
}

bool ReadFrame(void *opaque,
               xar::bridge::ActivityCostSlot12FrameV1 &output) noexcept {
  output = static_cast<Fixture *>(opaque)->frame;
  return true;
}

} // namespace

int main() {
  using namespace xar::bridge;
  Fixture fixture{};
  Put(fixture.planner, 0, kBase + 0x41205F0);
  Put(fixture.planner, 0xD0, static_cast<std::uintptr_t>(0x22000000));
  Put(fixture.planner, 0x1530, kType);
  Put(fixture.planner, 0x1560, kCategoryRows);
  Put(fixture.planner, 0x156C, std::int32_t{1});
  Put(fixture.planner, 0x1578, kCostOptionRows);
  Put(fixture.planner, 0x1584, std::int32_t{1});
  Put(fixture.planner, 0x1AB0, std::int32_t{5});
  PutType(fixture.type, 0, kBase + 0x440E308);
  std::memcpy(fixture.type.data() + 0x18, "activity_feast", 14);
  PutType(fixture.type, 0x28, std::uint64_t{14});
  PutType(fixture.type, 0x30, std::uint64_t{15});
  for (std::size_t i = 0; i < 10; ++i)
    Put(fixture.planner, 0x1AD8 + 0x50 + i * 0x90 + 0x78,
        static_cast<std::int64_t>(i == 3 ? 12500000 : 0));
  ActivityCostSlot12EnvironmentV1 environment{
      true, true, kActivityCostSlot12ExeSha256V1, kBase,
      &fixture, &Read, &ReadFrame};
  assert(VerifyActivityCostSlot12ExactAbiV1(environment));
  fixture.slot12_call[0] = 0x90;
  assert(!VerifyActivityCostSlot12ExactAbiV1(environment));
  fixture.slot12_call[0] = 0xE8;
  ActivityCostSlot12ObserverV1 observer{};
  observer.environment = environment;
  ActivityCostSlot12CaptureV1 observed{};
  assert(ReadActivityCostSlot12PassiveV1(observer, fixture.frame, observed) ==
         ActivityCostSlot12ReadStatusV1::no_normal_refresh);
  assert(!RecordActivityCostSlot12NormalReturnV1(
      observer, kBase + kActivityCostSlot12ReturnRvaV1 + 1, kPlanner));
  assert(RecordActivityCostSlot12NormalReturnV1(
      observer, kBase + kActivityCostSlot12ReturnRvaV1, kPlanner));
  assert(ReadActivityCostSlot12PassiveV1(observer, fixture.frame, observed) ==
         ActivityCostSlot12ReadStatusV1::observed);
  assert(observed.sequence == 1 && observed.planning_stage == 5);
  assert(observed.raw_aggregate[3] == 12500000);
  assert(observed.raw_aggregate[0] == 0);
  fixture.planner[0x1600] ^= 1;
  assert(ReadActivityCostSlot12PassiveV1(observer, fixture.frame, observed) ==
         ActivityCostSlot12ReadStatusV1::configuration_changed);
  fixture.planner[0x1600] ^= 1;
  fixture.category_rows[3] ^= 1;
  assert(ReadActivityCostSlot12PassiveV1(observer, fixture.frame, observed) ==
         ActivityCostSlot12ReadStatusV1::configuration_changed);
  fixture.category_rows[3] ^= 1;
  fixture.cost_option_rows[7] ^= 1;
  assert(ReadActivityCostSlot12PassiveV1(observer, fixture.frame, observed) ==
         ActivityCostSlot12ReadStatusV1::configuration_changed);
  fixture.cost_option_rows[7] ^= 1;
  auto next_frame = fixture.frame;
  ++next_frame.date_raw;
  assert(ReadActivityCostSlot12PassiveV1(observer, next_frame, observed) ==
         ActivityCostSlot12ReadStatusV1::frame_changed);
  return 0;
}
