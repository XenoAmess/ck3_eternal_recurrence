// Reuse the focused stage-2 gate fixture; the new reader depends on that gate.
#ifdef _MSC_VER
#pragma warning(push)
#pragma warning(disable : 4715)
#endif
#define main ExistingStage2GateTestMain
#include "activity_stage2_gate_read_v1_test.cpp"
#undef main
#ifdef _MSC_VER
#pragma warning(pop)
#endif

#include "xar_bridge/activity_stage2_location_read_v1.hpp"

namespace {
constexpr std::uintptr_t kPhaseA = 0x10010000;
constexpr std::uintptr_t kPhaseB = 0x10012000;
constexpr std::uintptr_t kProvinceA = 0x10014000;
constexpr std::uintptr_t kProvinceB = 0x10016000;
bool mutate_on_select = false;

bool ResolveLocationProvince(void *, std::int32_t id,
                             std::uintptr_t &output) noexcept {
  if (id == 2619) output = kProvinceA;
  else if (id == 2629) output = kProvinceB;
  else return false;
  return true;
}

bool Selectable(void *opaque, std::uintptr_t planner,
                std::uintptr_t province, bool &output) noexcept {
  if (planner != kPlanner) return false;
  auto &fake = *static_cast<Fake *>(opaque);
  if (province != kProvinceA && province != kProvinceB) return false;
  output = province == kProvinceA;
  if (mutate_on_select)
    fake.Put(kConfigRows + 0x08, std::int32_t{2619});
  return true;
}

void PopulateLocation(Fake &fake) {
  Populate(fake);
  fake.Put(kBase + 0x10B0E0F,
           std::array<std::uint8_t, 14>{0x48, 0x8B, 0x89, 0x78, 0x15,
                                         0x00, 0x00, 0x49, 0x63, 0x80,
                                         0x84, 0x15, 0x00, 0x00});
  fake.Put(kBase + 0x10AF6A0,
           std::array<std::uint8_t, 14>{0x48, 0x89, 0x5C, 0x24, 0x10,
                                         0x55, 0x56, 0x57, 0x41, 0x54,
                                         0x41, 0x55, 0x41, 0x56});
  fake.Put(kPlanner + 0x1AB0, std::int32_t{2});
  fake.Put(kPlanner + 0x1AB4, std::int32_t{1});
  fake.Put(kPlanner + 0x1AC8, std::uintptr_t{0});
  fake.Put(kPlanner + 0x1AC0, kConfigRows);
  fake.Put(kPlanner + 0x1578, kConfigRows);
  fake.Put(kPlanner + 0x1584, std::int32_t{2});
  fake.Put(kType + 0x3C75, std::uint8_t{1});
  fake.Put(kConfigRows, kPhaseA);
  fake.Put(kConfigRows + 0x08, std::int32_t{0});
  fake.Put(kConfigRows + 0x38, kPhaseB);
  fake.Put(kConfigRows + 0x38 + 0x08, std::int32_t{0});
  fake.Put(kPhaseA + 0x12D0, std::int32_t{0});
  fake.Put(kPhaseB + 0x12D0, std::int32_t{3});
  fake.Put(kPhaseA + 0x70C, std::int32_t{1});
  fake.Put(kPhaseB + 0x70C, std::int32_t{0});
  fake.progress = false;
}

xar::bridge::ActivityStage2LocationEnvironmentV1 LocationEnv(Fake &fake) {
  return {Env(fake), &ResolveLocationProvince, &Selectable};
}
} // namespace

int main() {
  ExistingStage2GateTestMain();
  Fake fake{};
  PopulateLocation(fake);
  constexpr std::array<std::int32_t, 2> ids{2619, 2629};
  const auto expected = fake.frame;
  auto result = xar::bridge::ReadActivityStage2LocationV1(
      LocationEnv(fake), expected, ids);
  Expect(result.status ==
         xar::bridge::ActivityStage2LocationReadStatusV1::observed);
  Expect(result.row_count == 2 && result.active_row_index == 0);
  Expect(result.rows[0].phase_kind == 0 && result.rows[0].is_active &&
         result.rows[0].phase_active_raw == 1);
  Expect(result.rows[1].phase_kind == 3 && !result.rows[1].is_active);
  Expect(result.activity_single_location_flag &&
         result.previous_planning_stage == 1);
  Expect(result.candidate_count == 2 && result.candidates[0].can_select &&
         !result.candidates[1].can_select &&
         !result.gate.can_progress_stage2);

  mutate_on_select = true;
  result = xar::bridge::ReadActivityStage2LocationV1(
      LocationEnv(fake), expected, ids);
  Expect(result.status ==
         xar::bridge::ActivityStage2LocationReadStatusV1::frame_changed);
  mutate_on_select = false;
  fake.Put(kConfigRows + 0x08, std::int32_t{0});

  fake.Put(kPlanner + 0x1AC0, std::uintptr_t{0});
  result = xar::bridge::ReadActivityStage2LocationV1(
      LocationEnv(fake), expected, ids);
  Expect(result.status ==
         xar::bridge::ActivityStage2LocationReadStatusV1::active_row_invalid);
  fake.Put(kPlanner + 0x1AC0, kConfigRows);

  constexpr std::array<std::int32_t, 2> duplicate{2619, 2619};
  result = xar::bridge::ReadActivityStage2LocationV1(
      LocationEnv(fake), expected, duplicate);
  Expect(result.status ==
         xar::bridge::ActivityStage2LocationReadStatusV1::candidate_invalid);
  constexpr std::array<std::int32_t, 1> unresolved{9999};
  result = xar::bridge::ReadActivityStage2LocationV1(
      LocationEnv(fake), expected, unresolved);
  Expect(result.status ==
         xar::bridge::ActivityStage2LocationReadStatusV1::province_unavailable);
  std::cout << "GREEN: exact-build private activity stage-2 location read\n";
}
