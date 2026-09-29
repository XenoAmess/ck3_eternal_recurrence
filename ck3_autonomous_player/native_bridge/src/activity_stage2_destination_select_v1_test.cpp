#include "xar_bridge/activity_stage2_destination_select_v1.hpp"

#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <unordered_map>

namespace {
using namespace xar::bridge;

constexpr std::uintptr_t kBase = 0x140000000;
constexpr std::uintptr_t kPlanner = 0x10004000;
constexpr std::uintptr_t kType = 0x10006000;
constexpr std::uintptr_t kOption = 0x10009000;
constexpr std::uintptr_t kRows = 0x1000A000;
constexpr std::uintptr_t kProvince = 0x1000B000;
constexpr std::uint32_t kProvinceId = 1234;

#define Expect(condition) do { \
  if (!(condition)) { \
    std::cerr << "destination select test failed at line " << __LINE__ << '\n'; \
    std::abort(); \
  } \
} while (false)

struct Fake {
  std::unordered_map<std::uintptr_t, std::uint8_t> bytes{};
  ActivityStage2DestinationStateV1 state{};
  bool native_eligible = true;
  bool fail_select = false;
  bool fail_post_read = false;
  bool drift_on_predicate = false;
  bool leave_one_row_unfilled = false;
  bool choose_wrong_province = false;
  bool change_option = false;
  bool change_gold = false;
  bool change_frame = false;
  bool start_activity = false;
  int reads = 0;
  int predicate_calls = 0;
  int select_calls = 0;

  template <typename T> void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t index = 0; index < sizeof(value); ++index)
      bytes[address + index] = source[index];
  }
};

bool ReadMemory(void *context, std::uintptr_t address, void *output,
                std::size_t size) noexcept {
  const auto &fake = *static_cast<Fake *>(context);
  auto *destination = static_cast<std::uint8_t *>(output);
  for (std::size_t index = 0; index < size; ++index) {
    const auto it = fake.bytes.find(address + index);
    if (it == fake.bytes.end()) return false;
    destination[index] = it->second;
  }
  return true;
}

bool ReadState(void *context,
               ActivityStage2DestinationStateV1 &output) noexcept {
  auto &fake = *static_cast<Fake *>(context);
  ++fake.reads;
  if (fake.fail_post_read && fake.select_calls != 0) return false;
  output = fake.state;
  return true;
}

bool ResolveProvince(void *, std::uint32_t province_id,
                     std::uintptr_t &output) noexcept {
  if (province_id != kProvinceId) return false;
  output = kProvince;
  return true;
}

bool CanSelect(void *context, std::uintptr_t planner,
               std::uintptr_t province, bool &output) noexcept {
  auto &fake = *static_cast<Fake *>(context);
  if (planner != kPlanner || province != kProvince) return false;
  ++fake.predicate_calls;
  output = fake.native_eligible;
  if (fake.drift_on_predicate) ++fake.state.frame.revision;
  return true;
}

bool SelectOnce(void *context, std::uintptr_t planner,
                std::uintptr_t province) noexcept {
  auto &fake = *static_cast<Fake *>(context);
  if (planner != kPlanner || province != kProvince) return false;
  ++fake.select_calls;
  if (fake.fail_select) return false;
  fake.state.stage = 5;
  fake.state.previous_stage = 2;
  fake.state.active_row = 0;
  fake.state.province_ids = {fake.choose_wrong_province ? kProvinceId + 1
                                                      : kProvinceId,
                             fake.leave_one_row_unfilled ? 0 : kProvinceId};
  if (fake.change_option) fake.state.selected_option = kOption + 8;
  if (fake.change_gold) ++fake.state.gold_raw;
  if (fake.change_frame) ++fake.state.frame.date_raw;
  if (fake.start_activity) fake.state.activity_started = true;
  return true;
}

void Populate(Fake &fake) {
  fake.Put(kBase + 0x10AF6A0,
           std::array<std::uint8_t, 8>{0x48, 0x89, 0x5C, 0x24, 0x10,
                                       0x55, 0x56, 0x57});
  fake.Put(kBase + 0x10AF3D0,
           std::array<std::uint8_t, 9>{0x48, 0x89, 0x5C, 0x24, 0x08,
                                       0x48, 0x89, 0x6C, 0x24});
  fake.Put(kBase + 0x10AF407,
           std::array<std::uint8_t, 6>{0x8B, 0x42, 0x10, 0x89, 0x41, 0x08});
  fake.Put(kBase + 0x10AF423,
           std::array<std::uint8_t, 7>{0x40, 0x38, 0xBD, 0x75, 0x3C,
                                       0x00, 0x00});
  fake.Put(kBase + 0x10AF430,
           std::array<std::uint8_t, 6>{0x8B, 0x8B, 0xB4, 0x1A, 0x00,
                                       0x00});
  fake.Put(kBase + 0x10AF4A1,
           std::array<std::uint8_t, 8>{0xBA, 0x05, 0x00, 0x00, 0x00,
                                       0x48, 0x8B, 0xCB});
  fake.Put(kProvince + 0x10, kProvinceId);
  fake.state.frame = {3, 53219928, 29829, true, true, true, true};
  fake.state.planner = kPlanner;
  fake.state.activity_type = kType;
  fake.state.selected_option = kOption;
  fake.state.selected_option_id = 42;
  fake.state.stage = 2;
  fake.state.previous_stage = 1;
  fake.state.single_location_flag = 1;
  fake.state.configuration_rows = kRows;
  fake.state.configuration_row_count = 2;
  fake.state.province_ids = {0, 0};
  fake.state.active_row = kRows;
  fake.state.activity_feast = true;
  fake.state.generic_feast_option = true;
  fake.state.gold_raw = 10000000;
}

ActivityStage2DestinationEnvironmentV1 Environment(Fake &fake) {
  return {{true, kActivityPlannerDiagExeSha256V1, kBase, &fake,
           &ReadMemory, nullptr, nullptr, nullptr},
          &ReadState, &ResolveProvince, &CanSelect, &SelectOnce};
}
} // namespace

int main() {
  using Status = ActivityStage2DestinationStatusV1;
  Fake good{};
  Populate(good);
  auto result = SelectActivityStage2DestinationV1(
      Environment(good), good.state.frame, kProvinceId);
  Expect(result.status == Status::verified_stage_five && result.submitted &&
         !result.needs_recovery && result.rows_filled &&
         result.selected_option_retained && result.gold_unchanged &&
         result.frame_unchanged && result.no_activity_started &&
         good.predicate_calls == 1 && good.select_calls == 1);

  Fake second_row{};
  Populate(second_row);
  second_row.state.active_row = kRows + 0x38;
  result = SelectActivityStage2DestinationV1(
      Environment(second_row), second_row.state.frame, kProvinceId);
  Expect(result.status == Status::verified_stage_five &&
         second_row.select_calls == 1);

  Fake illegal{};
  Populate(illegal);
  illegal.native_eligible = false;
  result = SelectActivityStage2DestinationV1(
      Environment(illegal), illegal.state.frame, kProvinceId);
  Expect(result.status == Status::precondition_rejected && !result.submitted &&
         illegal.select_calls == 0);

  Fake wrong_branch{};
  Populate(wrong_branch);
  wrong_branch.state.previous_stage = 3;
  result = SelectActivityStage2DestinationV1(
      Environment(wrong_branch), wrong_branch.state.frame, kProvinceId);
  Expect(result.status == Status::precondition_rejected &&
         wrong_branch.select_calls == 0);
  wrong_branch.state.previous_stage = 1;
  wrong_branch.state.single_location_flag = 0;
  result = SelectActivityStage2DestinationV1(
      Environment(wrong_branch), wrong_branch.state.frame, kProvinceId);
  Expect(result.status == Status::precondition_rejected &&
         wrong_branch.select_calls == 0);

  Fake invalid_row{};
  Populate(invalid_row);
  invalid_row.state.active_row = kRows + 1;
  result = SelectActivityStage2DestinationV1(
      Environment(invalid_row), invalid_row.state.frame, kProvinceId);
  Expect(result.status == Status::precondition_rejected &&
         invalid_row.select_calls == 0);

  Fake drift{};
  Populate(drift);
  drift.drift_on_predicate = true;
  const auto expected = drift.state.frame;
  result = SelectActivityStage2DestinationV1(
      Environment(drift), expected, kProvinceId);
  Expect(result.status == Status::precondition_rejected &&
         drift.select_calls == 0);

  Fake failed{};
  Populate(failed);
  failed.fail_select = true;
  result = SelectActivityStage2DestinationV1(
      Environment(failed), failed.state.frame, kProvinceId);
  Expect(result.status == Status::native_call_failed && result.submitted &&
         result.needs_recovery && failed.select_calls == 1);

  Fake uncertain{};
  Populate(uncertain);
  uncertain.fail_post_read = true;
  result = SelectActivityStage2DestinationV1(
      Environment(uncertain), uncertain.state.frame, kProvinceId);
  Expect(result.status == Status::postcondition_failed && result.submitted &&
         result.needs_recovery && uncertain.select_calls == 1);

  Fake incomplete{};
  Populate(incomplete);
  incomplete.leave_one_row_unfilled = true;
  result = SelectActivityStage2DestinationV1(
      Environment(incomplete), incomplete.state.frame, kProvinceId);
  Expect(result.status == Status::postcondition_failed && result.submitted &&
         !result.rows_filled && result.needs_recovery);

  Fake wrong_result{};
  Populate(wrong_result);
  wrong_result.choose_wrong_province = true;
  result = SelectActivityStage2DestinationV1(
      Environment(wrong_result), wrong_result.state.frame, kProvinceId);
  Expect(result.status == Status::postcondition_failed && result.submitted &&
         !result.rows_filled && result.needs_recovery);

  Fake paid{};
  Populate(paid);
  paid.change_gold = true;
  result = SelectActivityStage2DestinationV1(
      Environment(paid), paid.state.frame, kProvinceId);
  Expect(result.status == Status::postcondition_failed && result.submitted &&
         !result.gold_unchanged && result.needs_recovery);

  Fake started{};
  Populate(started);
  started.start_activity = true;
  result = SelectActivityStage2DestinationV1(
      Environment(started), started.state.frame, kProvinceId);
  Expect(result.status == Status::postcondition_failed && result.submitted &&
         !result.no_activity_started && result.needs_recovery);

  Fake changed{};
  Populate(changed);
  changed.change_option = true;
  changed.change_frame = true;
  result = SelectActivityStage2DestinationV1(
      Environment(changed), changed.state.frame, kProvinceId);
  Expect(result.status == Status::postcondition_failed && result.submitted &&
         !result.selected_option_retained && !result.frame_unchanged &&
         result.needs_recovery);

  std::cout << "GREEN: exact-build private activity stage-2 destination core\n";
}
