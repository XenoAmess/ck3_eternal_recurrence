// Reuse the established simulated-memory fixture; the new cases publish only
// the independently recovered 1.20 layout and exercise the production readers.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4715)
#endif
#define main ExistingStage2ConfirmFixtureMain
#include "activity_stage2_confirm_v1_test.cpp"
#undef main
#ifdef _MSC_VER
#pragma warning(pop)
#endif

#include "xar_bridge/activity_stage2_destination_select_v1.hpp"
#include "xar_bridge/activity_stage2_location_read_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

using namespace xar::bridge;

namespace {
constexpr std::uintptr_t kConfigRows12002 = 0x1000E000;
constexpr std::uintptr_t kPhase12002 = 0x10010000;
constexpr std::uintptr_t kProvince12002 = 0x10012000;

std::uintptr_t Cast12002(void *, std::uintptr_t source,
                        std::uintptr_t source_type,
                        std::uintptr_t target_type) noexcept {
  return source == kIdler && source_type == kBase + 0x5514438 &&
                 target_type == kBase + 0x5514460 ? kGfx : 0;
}

bool Visible12002(void *, std::uintptr_t planner, std::uintptr_t entry,
                 bool &output) noexcept {
  if (planner != kPlanner || entry != kBase + 0x21603A0) return false;
  output = true;
  return true;
}

bool Selected12002(void *opaque, std::uintptr_t planner,
                   std::uintptr_t &output) noexcept {
  return planner == kPlanner && Read(opaque, kRows + 8, &output, sizeof(output));
}

bool Predicate12002(void *opaque, std::uintptr_t entry,
                    std::uintptr_t candidate, std::uintptr_t actor,
                    std::uintptr_t selected, bool &output) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (candidate != kOption || actor != kActor || selected != kOption) return false;
  if (entry == kBase + 0x9DEA70) output = fake.shown;
  else if (entry == kBase + 0x9DEB70) output = fake.valid;
  else return false;
  return true;
}

void Populate12002(Fake &fake) {
  // Shared actor database and stable strings are supplied by the old fixture;
  // every migrated native field below uses its new absolute layout.
  Populate(fake);
  fake.Put(kBase + 0x11B2885,
      std::array<std::uint8_t, 8>{0x49, 0x89, 0xB4, 0x24, 0xA0, 0, 0, 0});
  fake.Put(kBase + 0x21603AA,
      std::array<std::uint8_t, 4>{0x48, 0x8B, 0x59, 0x60});
  fake.Put(kBase + 0x11B8693,
      std::array<std::uint8_t, 7>{0x48, 0x63, 0x81, 0xE8, 0x1A, 0, 0});
  fake.Put(kBase + 0x11B64C0,
      std::array<std::uint8_t, 7>{0x48, 0x8B, 0x81, 0, 0x15, 0, 0});
  for (const auto entry : {0x9DEA70u, 0x9DEB70u})
    fake.Put(kBase + entry,
      std::array<std::uint8_t, 7>{0x4C, 0x8B, 0xDC, 0x49, 0x89, 0x5B, 0x10});
  fake.Put(kBase + 0x11B8670,
      std::array<std::uint8_t, 7>{0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89});
  fake.Put(kBase + 0x11B86DF,
      std::array<std::uint8_t, 14>{0x48, 0x8B, 0x89, 0xB0, 0x15, 0, 0,
                                 0x49, 0x63, 0x80, 0xBC, 0x15, 0, 0});
  fake.Put(kBase + 0x11B8D53,
      std::array<std::uint8_t, 5>{0xBA, 5, 0, 0, 0});
  fake.Put(kBase + 0x11B95D0,
      std::array<std::uint8_t, 15>{0x40, 0x53, 0x48, 0x81, 0xEC, 0xA0,
                                 0, 0, 0, 0x8B, 0x81, 0xE8, 0x1A, 0, 0});
  fake.Put(kBase + 0x11B6F50,
      std::array<std::uint8_t, 14>{0x48, 0x89, 0x5C, 0x24, 0x10, 0x55, 0x56,
                                 0x57, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56});
  fake.Put(kBase + 0x11B6C80,
      std::array<std::uint8_t, 9>{0x48, 0x89, 0x5C, 0x24, 8, 0x48, 0x89, 0x6C, 0x24});
  fake.Put(kBase + 0x11B6CB7,
      std::array<std::uint8_t, 6>{0x8B, 0x42, 0x10, 0x89, 0x41, 8});
  fake.Put(kBase + 0x11B6CD3,
      std::array<std::uint8_t, 7>{0x40, 0x38, 0xBD, 0xED, 0x3B, 0, 0});
  fake.Put(kBase + 0x11B6CE0,
      std::array<std::uint8_t, 6>{0x8B, 0x8B, 0xEC, 0x1A, 0, 0});
  fake.Put(kBase + 0x11B6D51,
      std::array<std::uint8_t, 8>{0xBA, 5, 0, 0, 0, 0x48, 0x8B, 0xCB});

  fake.Put(kBase + 0x45325C8, kBase + 0x11B2E30);
  fake.Put(kBase + 0x45325C8 + 7 * 8, kBase + 0x21603A0);
  fake.Put(kBase + 0x45325C8 + 11 * 8, kBase + 0xB1F0A0);
  fake.Put(kBase + 0x45325C8 + 12 * 8, kBase + 0x11B5B30);
  fake.Put(kBase + 0x45325C8 + 0xC8, kBase + 0x11B6550);
  fake.Put(kBase + 0x45326A0, kBase + 0x11D3404);
  fake.Put(kBase + 0x5C6A520, kRoot);
  fake.Put(kGfx, kBase + 0x44BC408);
  fake.Put(kHandler, kBase + 0x44BA890);
  fake.Put(kBase + 0x54DBC00, kActorId);
  fake.Put(kBase + 0x5C67568, kStorage);
  fake.Put(kBase + 0x5C67570, std::uintptr_t{0});
  fake.Put(kHandler + 0x3C0, kPlanner);
  fake.Put(kHandler + 0x3D8, std::uintptr_t{0});
  fake.Put(kPlanner, kBase + 0x45325C8);
  fake.Put(kPlanner + 0x10, kBase + 0x45326A0);
  fake.Put(kPlanner + 0xA0, kHandler);
  fake.Put(kPlanner + 0x60, kWidget);
  fake.Put(kPlanner + 0x1AE8, std::int32_t{2});
  fake.Put(kPlanner + 0x1AEC, std::int32_t{1});
  fake.Put(kPlanner + 0x1B08, std::uint8_t{0});
  fake.Put(kPlanner + 0x1500, kType);
  fake.Put(kType, kBase + 0x48BFE50);
  fake.Put(kType + 0x960, kCategory);
  fake.Put(kType + 0x3BED, std::uint8_t{1});
  fake.Put(kPlanner + 0x1598, kRows);
  fake.Put(kPlanner + 0x15A4, std::int32_t{1});
  fake.Put(kPlanner + 0x15B0, kConfigRows12002);
  fake.Put(kPlanner + 0x15BC, std::int32_t{2});
  fake.Put(kPlanner + 0x1AF8, kConfigRows12002);
  fake.Put(kPlanner + 0x1B00, std::uintptr_t{0});
  fake.Put(kOption, kBase + 0x48BFD18);
  fake.Put(kConfigRows12002, kPhase12002);
  fake.Put(kConfigRows12002 + 8, std::uint32_t{0});
  fake.Put(kConfigRows12002 + 0x38, std::uintptr_t{0});
  fake.Put(kConfigRows12002 + 0x38 + 8, std::uint32_t{0});
  fake.Put(kPhase12002 + 0x1160, std::int32_t{0});
  fake.Put(kPhase12002 + 0x69C, std::uint8_t{1});
  fake.Put(kProvince12002 + 0x10, std::uint32_t{2619});
}

ActivityStage1OptionEnvironmentV1 Env12002(Fake &fake) {
  return {{true, kActivityPlanner12002ExeSha256V1, kBase, &fake,
           &Read, &Frame, &Cast12002, &Visible12002},
          &Key, &Selected12002, &Predicate12002, &Progress, nullptr};
}

bool SetFive12002(void *opaque, std::uintptr_t planner) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (planner != kPlanner) return false;
  ++fake.stage_five_calls;
  fake.Put(kPlanner + 0x1AE8, std::int32_t{5});
  if (fake.change_gold_on_transition) ++fake.gold_raw;
  return true;
}

bool ResolveProvince12002(void *, std::int32_t id,
                         std::uintptr_t &province) noexcept {
  if (id != 2619) return false;
  province = kProvince12002;
  return true;
}

bool ResolveUnsignedProvince12002(void *ctx, std::uint32_t id,
                                 std::uintptr_t &province) noexcept {
  return id <= 0x7FFFFFFFu && ResolveProvince12002(ctx, static_cast<std::int32_t>(id), province);
}

bool CanSelect12002(void *, std::uintptr_t planner,
                    std::uintptr_t province, bool &selectable) noexcept {
  if (planner != kPlanner || province != kProvince12002) return false;
  selectable = true;
  return true;
}

bool ReadDestination12002(void *opaque, ActivityStage2DestinationStateV1 &state) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  state.frame = fake.frame;
  state.planner = kPlanner;
  state.activity_type = kType;
  state.selected_option = kOption;
  state.selected_option_id = 42;
  state.activity_feast = true;
  state.generic_feast_option = true;
  state.gold_raw = fake.gold_raw;
  state.configuration_rows = kConfigRows12002;
  state.configuration_row_count = 2;
  state.single_location_flag = 1;
  return Read(opaque, kPlanner + 0x1AE8, &state.stage, sizeof(state.stage)) &&
      Read(opaque, kPlanner + 0x1AEC, &state.previous_stage, sizeof(state.previous_stage)) &&
      Read(opaque, kPlanner + 0x1AF8, &state.active_row, sizeof(state.active_row)) &&
      Read(opaque, kConfigRows12002 + 8, &state.province_ids[0], sizeof(state.province_ids[0])) &&
      Read(opaque, kConfigRows12002 + 0x38 + 8, &state.province_ids[1], sizeof(state.province_ids[1]));
}

bool SelectDestination12002(void *opaque, std::uintptr_t planner,
                           std::uintptr_t province) noexcept {
  auto &fake = *static_cast<Fake *>(opaque);
  if (planner != kPlanner || province != kProvince12002) return false;
  ++fake.stage_five_calls;
  fake.Put(kConfigRows12002 + 8, std::uint32_t{2619});
  fake.Put(kConfigRows12002 + 0x38 + 8, std::uint32_t{2619});
  fake.Put(kPlanner + 0x1AE8, std::int32_t{5});
  return true;
}
} // namespace

int main() {
  Fake fake{};
  Populate12002(fake);
  fake.progress = false;
  const auto option = Env12002(fake);
  constexpr std::array<std::int32_t, 1> candidates{2619};
  const auto location = ReadActivityStage2LocationV1(
      {option, &ResolveProvince12002, &CanSelect12002}, fake.frame, candidates);
  Expect(location.status == ActivityStage2LocationReadStatusV1::observed);
  Expect(location.row_count == 2 && location.active_row_index == 0);
  Expect(location.rows[0].phase_kind == 0 && location.rows[0].phase_active_raw == 1);
  Expect(!location.gate.can_progress_stage2 && location.candidates[0].can_select);

  auto destination_environment = ActivityStage2DestinationEnvironmentV1{
      option.diagnostic, &ReadDestination12002, &ResolveUnsignedProvince12002,
      &CanSelect12002, &SelectDestination12002};
  auto destination = SelectActivityStage2DestinationV1(destination_environment, fake.frame, 2619);
  Expect(destination.status == ActivityStage2DestinationStatusV1::verified_stage_five);
  Expect(destination.submitted && destination.rows_filled && destination.gold_unchanged);
  Expect(destination.no_activity_started && fake.stage_five_calls == 1);

  fake = {};
  Populate12002(fake);
  fake.Put(kConfigRows12002 + 8, std::uint32_t{2619});
  fake.Put(kConfigRows12002 + 0x38 + 8, std::uint32_t{2619});
  auto gate = ReadActivityStage2GateV1(Env12002(fake), fake.frame);
  Expect(gate.status == ActivityStage2GateReadStatusV1::observed && gate.can_progress_stage2);
  auto confirm = ConfirmActivityStage2V1({Env12002(fake), &SetFive12002, &Gold}, fake.frame);
  Expect(confirm.status == ActivityStage2ConfirmStatusV1::stage_five_verified);
  Expect(confirm.submitted && confirm.selected_option_retained && fake.stage_five_calls == 1);

  fake = {};
  Populate12002(fake);
  fake.change_gold_on_transition = true;
  confirm = ConfirmActivityStage2V1({Env12002(fake), &SetFive12002, &Gold}, fake.frame);
  Expect(confirm.status == ActivityStage2ConfirmStatusV1::postcondition_failed);
  Expect(confirm.submitted && !confirm.gold_unchanged && fake.stage_five_calls == 1);
  std::cout << "GREEN: 1.20.0.2 feast Stage2 location, destination and confirm production paths\n";
  return 0;
}
