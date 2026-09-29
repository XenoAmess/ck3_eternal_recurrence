#include "xar_bridge/activity_stage2_gate_read_v1.hpp"

#include <array>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string_view>
#include <unordered_map>

namespace {
using xar::bridge::ActivityPlannerDiagFrameV1;
using xar::bridge::ActivityStage1OptionEnvironmentV1;
using xar::bridge::ActivityStage1OptionReadStatusV1;

constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kRoot = 0x10000000;
constexpr std::uintptr_t kIdler = 0x10001000;
constexpr std::uintptr_t kGfx = 0x10002000;
constexpr std::uintptr_t kHandler = 0x10003000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::uintptr_t kWidget = 0x10005000;
constexpr std::uintptr_t kType = 0x10006000;
constexpr std::uintptr_t kCategory = 0x10007000;
constexpr std::uintptr_t kRows = 0x10008000;
constexpr std::uintptr_t kOption = 0x10009000;
constexpr std::uintptr_t kStorage = 0x1000A000;
constexpr std::uintptr_t kSlots = 0x1000B000;
constexpr std::uintptr_t kActor = 0x1000C000;
constexpr std::uintptr_t kHost = 0x1000D000;
constexpr std::uintptr_t kConfigRows = 0x1000E000;
constexpr std::int32_t kActorId = 29829;

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{3, 53219928, kActorId, true, true, true,
                                   true};
  bool shown = true;
  bool valid = true;
  bool progress = true;
  bool drift_on_valid = false;
  bool drift_on_progress = false;
  bool mutate_row_on_progress = false;
  bool lose_option_on_transition = false;
  std::string_view key = "feast_type_generic";
  int stage_two_calls = 0;

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

#define Expect(condition) do { \
  if (!(condition)) { \
    std::cerr << "stage2 gate test failed at line " << __LINE__ << '\n'; \
    std::abort(); \
  } \
} while (false)

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

bool Key(void *opaque, std::int32_t identifier,
         std::array<char, 96> &output, std::uint16_t &size) noexcept {
  const auto &fake = *static_cast<Fake *>(opaque);
  if (identifier != 42 || fake.key.empty()) return false;
  std::memcpy(output.data(), fake.key.data(), fake.key.size());
  size = static_cast<std::uint16_t>(fake.key.size());
  return true;
}

bool Selected(void *, std::uintptr_t planner,
              std::uintptr_t &output) noexcept {
  if (planner != kPlanner) return false;
  output = kOption;
  return true;
}

bool Predicate(void *opaque, std::uintptr_t entry,
               std::uintptr_t candidate, std::uintptr_t actor,
               std::uintptr_t selected, bool &output) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (candidate != kOption || actor != kActor || selected != kOption)
    return false;
  if (entry == kBase + 0x971270) output = fake.shown;
  else if (entry == kBase + 0x971370) {
    output = fake.valid;
    if (fake.drift_on_valid) fake.frame.revision = 4;
  } else return false;
  return true;
}

bool Progress(void *opaque, std::uintptr_t planner,
              bool &output) noexcept {
  if (planner != kPlanner) return false;
  auto &fake = *static_cast<Fake *>(opaque);
  output = fake.progress;
  if (fake.drift_on_progress) fake.frame.revision += 1;
  if (fake.mutate_row_on_progress)
    fake.Put(kConfigRows + 0x38 + 0x08, std::uint32_t{0});
  return true;
}

bool SetStageTwo(void *opaque, std::uintptr_t planner) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (planner != kPlanner) return false;
  ++fake.stage_two_calls;
  fake.Put(kPlanner + 0x1AB0, std::int32_t{2});
  fake.Put(kPlanner + 0x1AC8, std::uintptr_t{0});
  if (fake.lose_option_on_transition)
    fake.Put(kRows + 8, std::uintptr_t{0});
  return true;
}

void Populate(Fake &fake) {
  fake.Put(kBase + 0x10AC0F3,
           std::array<std::uint8_t, 7>{0x49, 0x89, 0xB6, 0xD0, 0, 0, 0});
  fake.Put(kBase + 0x1F3097A,
           std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x78});
  fake.Put(kBase + 0x10B0DC3,
           std::array<std::uint8_t, 7>{0x48, 0x63, 0x81, 0xB0, 0x1A, 0, 0});
  fake.Put(kBase + 0x10AEAE0,
           std::array<std::uint8_t, 7>{0x48, 0x8B, 0x81, 0x30, 0x15, 0, 0});
  fake.Put(kBase + 0x971270,
           std::array<std::uint8_t, 7>{0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B,
                                        0x10});
  fake.Put(kBase + 0x971370,
           std::array<std::uint8_t, 7>{0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B,
                                        0x10});
  fake.Put(kBase + 0x10B0DA0,
           std::array<std::uint8_t, 7>{0x48, 0x89, 0x5C, 0x24, 0x10, 0x48,
                                        0x89});
  fake.Put(kBase + 0x10B1BD0,
           std::array<std::uint8_t, 10>{0x40, 0x53, 0x48, 0x83, 0xEC,
                                         0x20, 0x8B, 0x81, 0xB0, 0x1A});
  fake.Put(kBase + 0x41205F0, kBase + 0x10AC480);
  fake.Put(kBase + 0x41205F0 + 7 * 8, kBase + 0x1F30970);
  fake.Put(kBase + 0x41205F0 + 11 * 8, kBase + 0xAA33F0);
  fake.Put(kBase + 0x41205F0 + 12 * 8, kBase + 0x10AE180);
  fake.Put(kBase + 0x41205F0 + 0xC8, kBase + 0x10AEC20);
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
  fake.Put(kHandler + 0x3D8, kHost);
  fake.Put(kHost, kBase + 0x4166528);
  fake.Put(kHost + 0x10, kBase + 0x4166620);
  fake.Put(kHost + 0xD0, kHandler);
  fake.Put(kHost + 0x100, kActorId);
  fake.Put(kHost + 0x268, kType);
  fake.Put(kPlanner, kBase + 0x41205F0);
  fake.Put(kPlanner + 0x10, kBase + 0x41206C8);
  fake.Put(kPlanner + 0xD0, kHandler);
  fake.Put(kPlanner + 0x78, kWidget);
  fake.Put(kPlanner + 0x1AB0, std::int32_t{1});
  fake.Put(kPlanner + 0x1AD0, std::uint8_t{0});
  fake.Put(kPlanner + 0x1530, kType);
  fake.Put(kType, kBase + 0x440E308);
  fake.PutBytes(kType + 0x18, "activity_feast");
  fake.Put(kType + 0x28, std::uint64_t{14});
  fake.Put(kType + 0x30, std::uint64_t{15});
  fake.Put(kType + 0xA88, kCategory);
  fake.Put(kPlanner + 0x1560, kRows);
  fake.Put(kPlanner + 0x156C, std::int32_t{1});
  fake.Put(kPlanner + 0x1AC8, kRows);
  fake.Put(kRows, kCategory);
  fake.Put(kRows + 8, kOption);
  fake.Put(kOption, kBase + 0x440E1D0);
  fake.Put(kOption + 8, std::int32_t{42});
}

ActivityStage1OptionEnvironmentV1 Env(Fake &fake) {
  return {{true, xar::bridge::kActivityPlannerDiagExeSha256V1, kBase,
           &fake, &Read, &Frame, &Cast, &Visible},
          &Key, &Selected, &Predicate, &Progress, &SetStageTwo};
}
} // namespace

int main() {
  Fake fake{};
  Populate(fake);
  fake.Put(kBase + 0x10B0E0F,
           std::array<std::uint8_t, 14>{0x48, 0x8B, 0x89, 0x78, 0x15,
                                         0x00, 0x00, 0x49, 0x63, 0x80,
                                         0x84, 0x15, 0x00, 0x00});
  fake.Put(kPlanner + 0x1AB0, std::int32_t{2});
  fake.Put(kPlanner + 0x1AC8, std::uintptr_t{0});
  fake.Put(kPlanner + 0x1578, kConfigRows);
  fake.Put(kPlanner + 0x1584, std::int32_t{2});
  fake.Put(kConfigRows + 0x08, std::uint32_t{1});
  fake.Put(kConfigRows + 0x38 + 0x08, std::uint32_t{4});
  const auto expected = fake.frame;

  auto result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status ==
         xar::bridge::ActivityStage2GateReadStatusV1::observed);
  Expect(result.configuration_row_count == 2 && result.failed_row_count == 0);
  Expect(result.can_progress_stage2 &&
         result.generic_feast_stage2_advance_ready);
  Expect(result.selected_option.generic_feast_selected);

  fake.Put(kConfigRows + 0x38 + 0x08, std::uint32_t{0});
  fake.progress = false;
  result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status ==
         xar::bridge::ActivityStage2GateReadStatusV1::observed);
  Expect(result.configuration_row_count == 2 && result.failed_row_count == 1);
  Expect(result.failed_rows[0].index == 1 &&
         result.failed_rows[0].raw_dword == 0);
  Expect(!result.can_progress_stage2 &&
         !result.generic_feast_stage2_advance_ready);

  fake.progress = true;
  result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status ==
         xar::bridge::ActivityStage2GateReadStatusV1::native_gate_mismatch);

  fake.Put(kPlanner + 0x1584, std::int32_t{0});
  fake.Put(kPlanner + 0x1578, std::uintptr_t{0});
  result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status ==
         xar::bridge::ActivityStage2GateReadStatusV1::observed &&
         result.configuration_row_count == 0 && result.failed_row_count == 0 &&
         result.can_progress_stage2);

  fake.Put(kPlanner + 0x1578, kConfigRows);
  fake.Put(kPlanner + 0x1584, std::int32_t{129});
  result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status ==
         xar::bridge::ActivityStage2GateReadStatusV1::row_vector_unavailable);

  fake.Put(kPlanner + 0x1584, std::int32_t{2});
  fake.Put(kConfigRows + 0x38 + 0x08, std::uint32_t{4});
  fake.key = "feast_type_other";
  result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status == xar::bridge::ActivityStage2GateReadStatusV1::
                              selected_option_not_generic);

  fake.key = "feast_type_generic";
  fake.frame.revision = expected.revision + 1;
  result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status ==
         xar::bridge::ActivityStage2GateReadStatusV1::frame_changed);

  fake.frame = expected;
  fake.drift_on_progress = true;
  result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status ==
         xar::bridge::ActivityStage2GateReadStatusV1::frame_changed);

  fake.frame = expected;
  fake.drift_on_progress = false;
  fake.mutate_row_on_progress = true;
  result = xar::bridge::ReadActivityStage2GateV1(Env(fake), expected);
  Expect(result.status ==
         xar::bridge::ActivityStage2GateReadStatusV1::frame_changed);

  std::cout << "GREEN: exact-build private activity stage-2 gate read\n";
}
