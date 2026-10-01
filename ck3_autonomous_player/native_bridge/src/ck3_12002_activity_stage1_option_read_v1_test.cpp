// Ported production boundary fixture for the independently recovered 1.20.0.2 ABI.
#include "xar_bridge/activity_stage1_option_read_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

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
constexpr std::uintptr_t kAutoRows = 0x10009500;
constexpr std::uintptr_t kStorage = 0x1000A000;
constexpr std::uintptr_t kSlots = 0x1000B000;
constexpr std::uintptr_t kActor = 0x1000C000;
constexpr std::uintptr_t kHost = 0x1000D000;
constexpr std::int32_t kActorId = 29829;

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityPlannerDiagFrameV1 frame{3, 53219928, kActorId, true, true, true,
                                   true};
  bool shown = true;
  bool valid = true;
  bool progress = true;
  bool drift_on_valid = false;
  bool lose_option_on_transition = false;
  bool auto_row_present = true;
  bool auto_row_out_of_range = false;
  std::string_view key = "feast_type_generic";
  int stage_two_calls = 0;
  int original_progress_calls = 0;

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
    std::cerr << "stage1 option test failed at line " << __LINE__ << '\n'; \
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
  return source == kIdler && source_type == kBase + 0x5514438 &&
                 target_type == kBase + 0x5514460
             ? kGfx
             : 0;
}

bool Visible(void *, std::uintptr_t planner, std::uintptr_t slot,
             bool &output) noexcept {
  if (planner != kPlanner || slot != kBase + 0x21603A0) return false;
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
  if (entry == kBase + 0x9DEA70) output = fake.shown;
  else if (entry == kBase + 0x9DEB70) {
    output = fake.valid;
    if (fake.drift_on_valid) fake.frame.revision = 4;
  } else return false;
  return true;
}

bool Progress(void *opaque, std::uintptr_t planner,
              bool &output) noexcept {
  if (planner != kPlanner) return false;
  output = static_cast<Fake *>(opaque)->progress;
  return true;
}

bool SetStageTwo(void *opaque, std::uintptr_t planner) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (planner != kPlanner) return false;
  ++fake.stage_two_calls;
  fake.Put(kPlanner + 0x1AE8, std::int32_t{2});
  fake.Put(kPlanner + 0x1B00, std::uintptr_t{0});
  if (fake.lose_option_on_transition)
    fake.Put(kRows + 8, std::uintptr_t{0});
  return true;
}

bool FindAutoRow(void *opaque, std::uintptr_t planner,
                 std::uintptr_t &output) noexcept {
  if (planner != kPlanner) return false;
  const auto &fake = *static_cast<Fake *>(opaque);
  output = !fake.auto_row_present
      ? 0 : fake.auto_row_out_of_range ? kAutoRows + 0x38 : kAutoRows;
  return true;
}

bool ProgressNonzero(void *opaque, std::uintptr_t planner) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (planner != kPlanner) return false;
  ++fake.original_progress_calls;
  fake.Put(kPlanner + 0x1AF8, kAutoRows);
  fake.Put(kPlanner + 0x1AF4, std::int32_t{1});
  fake.Put(kAutoRows + 8, std::int32_t{0});
  fake.Put(kPlanner + 0x1B08, std::uint8_t{0});
  fake.Put(kPlanner + 0x1AE8, std::int32_t{2});
  fake.Put(kPlanner + 0x1B00, std::uintptr_t{0});
  if (fake.lose_option_on_transition)
    fake.Put(kRows + 8, std::uintptr_t{0});
  return true;
}

void Populate(Fake &fake) {
  fake.Put(kBase + 0x11B2885,
           std::array<std::uint8_t, 8>{0x49, 0x89, 0xB4, 0x24, 0xA0, 0, 0, 0});
  fake.Put(kBase + 0x21603AA,
           std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x60});
  fake.Put(kBase + 0x11B8693,
           std::array<std::uint8_t, 7>{0x48, 0x63, 0x81, 0xE8, 0x1A, 0, 0});
  fake.Put(kBase + 0x11B64C0,
           std::array<std::uint8_t, 7>{0x48, 0x8B, 0x81, 0x00, 0x15, 0, 0});
  fake.Put(kBase + 0x9DEA70,
           std::array<std::uint8_t, 7>{0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B,
                                        0x10});
  fake.Put(kBase + 0x9DEB70,
           std::array<std::uint8_t, 7>{0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B,
                                        0x10});
  fake.Put(kBase + 0x11B8670,
           std::array<std::uint8_t, 7>{0x48, 0x89, 0x5C, 0x24, 0x10, 0x48,
                                        0x89});
  fake.Put(kBase + 0x11B95D0,
           std::array<std::uint8_t, 15>{0x40, 0x53, 0x48, 0x81, 0xEC,
                                      0xA0, 0, 0, 0, 0x8B, 0x81, 0xE8, 0x1A, 0, 0});
  fake.Put(kBase + 0x11B5950,
           std::array<std::uint8_t, 13>{0x48, 0x8B, 0x81, 0xB0, 0x15, 0,
                                         0, 0x48, 0x63, 0x89, 0xBC, 0x15, 0});
  fake.Put(kBase + 0x11B8CD0,
           std::array<std::uint8_t, 10>{0x40, 0x53, 0x48, 0x83, 0xEC,
                                         0x20, 0x48, 0x63, 0x81, 0xE8});
  fake.Put(kBase + 0x45325C8, kBase + 0x11B2E30);
  fake.Put(kBase + 0x45325C8 + 7 * 8, kBase + 0x21603A0);
  fake.Put(kBase + 0x45325C8 + 11 * 8, kBase + 0xB1F0A0);
  fake.Put(kBase + 0x45325C8 + 12 * 8, kBase + 0x11B5B30);
  fake.Put(kBase + 0x45325C8 + 0xC8, kBase + 0x11B6550);
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
  fake.Put(kHandler + 0x3D8, kHost);
  fake.Put(kHost, kBase + 0x457A138);
  fake.Put(kHost + 0x10, kBase + 0x457A110);
  fake.Put(kHost + 0xA0, kHandler);
  fake.Put(kHost + 0xD0, kActorId);
  fake.Put(kHost + 0x238, kType);
  fake.Put(kPlanner, kBase + 0x45325C8);
  fake.Put(kPlanner + 0x10, kBase + 0x45326A0);
  fake.Put(kPlanner + 0xA0, kHandler);
  fake.Put(kPlanner + 0x60, kWidget);
  fake.Put(kPlanner + 0x1AE8, std::int32_t{1});
  fake.Put(kPlanner + 0x1B08, std::uint8_t{0});
  fake.Put(kPlanner + 0x15B0, kAutoRows);
  fake.Put(kPlanner + 0x15BC, std::int32_t{1});
  fake.Put(kAutoRows, kType);
  fake.Put(kAutoRows + 8, std::int32_t{1});
  fake.Put(kPlanner + 0x1500, kType);
  fake.Put(kType, kBase + 0x48BFE50);
  fake.PutBytes(kType + 0x18, "activity_feast");
  fake.Put(kType + 0x28, std::uint64_t{14});
  fake.Put(kType + 0x30, std::uint64_t{15});
  fake.Put(kType + 0x960, kCategory);
  fake.Put(kPlanner + 0x1598, kRows);
  fake.Put(kPlanner + 0x15A4, std::int32_t{1});
  fake.Put(kPlanner + 0x1B00, kRows);
  fake.Put(kRows, kCategory);
  fake.Put(kRows + 8, kOption);
  fake.Put(kOption, kBase + 0x48BFD18);
  fake.Put(kOption + 8, std::int32_t{42});
}

ActivityStage1OptionEnvironmentV1 Env(Fake &fake) {
  return {{true, xar::bridge::kActivityPlanner12002ExeSha256V1, kBase,
           &fake, &Read, &Frame, &Cast, &Visible},
          &Key, &Selected, &Predicate, &Progress, &SetStageTwo,
          &FindAutoRow, &ProgressNonzero};
}
} // namespace

int main() {
  Fake fake{};
  Populate(fake);
  const auto expected = fake.frame;
  auto result = xar::bridge::ReadActivityStage1OptionV1(Env(fake), expected);
  Expect(result.status == ActivityStage1OptionReadStatusV1::observed);
  Expect(result.generic_feast_confirm_ready && result.shown && result.valid &&
         result.can_progress);
  Expect(std::string_view(result.option_key.data(), result.option_key_size) ==
         "feast_type_generic");

  fake.shown = false;
  result = xar::bridge::ReadActivityStage1OptionV1(Env(fake), expected);
  Expect(result.status == ActivityStage1OptionReadStatusV1::observed &&
         !result.generic_feast_confirm_ready && !result.shown);
  fake.shown = true;
  fake.valid = false;
  result = xar::bridge::ReadActivityStage1OptionV1(Env(fake), expected);
  Expect(result.status == ActivityStage1OptionReadStatusV1::observed &&
         !result.generic_feast_confirm_ready && !result.valid);
  fake.valid = true;
  fake.key = "feast_type_other";
  result = xar::bridge::ReadActivityStage1OptionV1(Env(fake), expected);
  Expect(result.status == ActivityStage1OptionReadStatusV1::observed &&
         !result.generic_feast_confirm_ready);
  fake.key = "feast_type_generic";
  fake.drift_on_valid = true;
  result = xar::bridge::ReadActivityStage1OptionV1(Env(fake), expected);
  Expect(result.status == ActivityStage1OptionReadStatusV1::frame_changed);
  fake.drift_on_valid = false;
  fake.frame = expected;
  fake.shown = false;
  auto confirm = xar::bridge::ConfirmActivityStage1V1(Env(fake), expected);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::precondition_rejected &&
         confirm.reject_reason ==
             xar::bridge::ActivityStage1ConfirmRejectReasonV1::option_not_ready &&
         fake.stage_two_calls == 0);
  fake.shown = true;
  fake.Put(kPlanner + 0x1B08, std::uint8_t{1});
  fake.auto_row_present = false;
  confirm = xar::bridge::ConfirmActivityStage1V1(Env(fake), expected);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::precondition_rejected &&
         confirm.reject_reason ==
             xar::bridge::ActivityStage1ConfirmRejectReasonV1::stage_auto_row_absent &&
         confirm.planner_stage_auto_observed &&
         confirm.planner_stage_auto_raw == 1 &&
         fake.stage_two_calls == 0 && fake.original_progress_calls == 0);
  fake.auto_row_present = true;
  confirm = xar::bridge::ConfirmActivityStage1V1(Env(fake), expected);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::stage_two_verified &&
         confirm.submitted && confirm.stage_two_visible &&
         confirm.selected_option_retained && fake.stage_two_calls == 0 &&
         fake.original_progress_calls == 1);
  Expect(xar::bridge::ReadActivityStage2OptionV1(Env(fake), expected).status ==
         xar::bridge::ActivityStage2OptionReadStatusV1::observed);
  Populate(fake);
  fake.auto_row_out_of_range = true;
  fake.Put(kPlanner + 0x1B08, std::uint8_t{1});
  confirm = xar::bridge::ConfirmActivityStage1V1(Env(fake), expected);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::precondition_rejected &&
         confirm.reject_reason ==
             xar::bridge::ActivityStage1ConfirmRejectReasonV1::stage_auto_row_unverified &&
         !confirm.submitted && fake.original_progress_calls == 1);
  fake.auto_row_out_of_range = false;
  fake.Put(kPlanner + 0x1B08, std::uint8_t{2});
  confirm = xar::bridge::ConfirmActivityStage1V1(Env(fake), expected);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::precondition_rejected &&
         confirm.reject_reason ==
             xar::bridge::ActivityStage1ConfirmRejectReasonV1::stage_auto_nonzero &&
         fake.original_progress_calls == 1);
  fake.bytes.erase(kPlanner + 0x1B08);
  confirm = xar::bridge::ConfirmActivityStage1V1(Env(fake), expected);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::precondition_rejected &&
         confirm.reject_reason ==
             xar::bridge::ActivityStage1ConfirmRejectReasonV1::stage_auto_read_failed &&
         !confirm.planner_stage_auto_observed &&
         fake.stage_two_calls == 0);
  fake.Put(kPlanner + 0x1B08, std::uint8_t{0});
  confirm = xar::bridge::ConfirmActivityStage1V1(Env(fake), expected);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::stage_two_verified &&
         confirm.reject_reason ==
             xar::bridge::ActivityStage1ConfirmRejectReasonV1::none &&
         confirm.planner_stage_auto_observed &&
         confirm.planner_stage_auto_raw == 0 &&
         confirm.submitted && confirm.stage_two_visible &&
         confirm.selected_option_retained && fake.stage_two_calls == 1);
  const auto stage_two =
      xar::bridge::ReadActivityStage2OptionV1(Env(fake), expected);
  Expect(stage_two.status ==
             xar::bridge::ActivityStage2OptionReadStatusV1::observed &&
         stage_two.generic_feast_selected &&
         std::string_view(stage_two.option_key.data(),
                          stage_two.option_key_size) ==
             "feast_type_generic");
  Fake lost{};
  Populate(lost);
  lost.lose_option_on_transition = true;
  confirm = xar::bridge::ConfirmActivityStage1V1(Env(lost), lost.frame);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::postcondition_failed &&
         confirm.submitted && confirm.stage_two_visible &&
         !confirm.selected_option_retained && lost.stage_two_calls == 1);
  Expect(xar::bridge::ReadActivityStage2OptionV1(Env(lost), lost.frame).status ==
         xar::bridge::ActivityStage2OptionReadStatusV1::option_identity_mismatch);
  Fake lost_nonzero{};
  Populate(lost_nonzero);
  lost_nonzero.Put(kPlanner + 0x1B08, std::uint8_t{1});
  lost_nonzero.lose_option_on_transition = true;
  confirm = xar::bridge::ConfirmActivityStage1V1(Env(lost_nonzero),
                                                 lost_nonzero.frame);
  Expect(confirm.status ==
             xar::bridge::ActivityStage1ConfirmStatusV1::postcondition_failed &&
         confirm.submitted && confirm.stage_two_visible &&
         !confirm.selected_option_retained &&
         lost_nonzero.original_progress_calls == 1);
  std::cout << "GREEN: CK3 1.20.0.2 exact-build private activity stage-1 option read\n";
}
