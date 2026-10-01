#include "xar_bridge/activity_stage2_location_read_v1.hpp"
#include "xar_bridge/ck3_12002_feast_planner.hpp"

#include <limits>

namespace xar::bridge {
namespace {

constexpr std::uintptr_t kRootRva = 0x570F7B8;
constexpr std::uintptr_t kIdlerSourceTypeRva = 0x501EF28;
constexpr std::uintptr_t kIdlerGfxTypeRva = 0x501EF50;
constexpr std::uintptr_t kGfxVtableRva = 0x40B1D30;
constexpr std::uintptr_t kHandlerVtableRva = 0x40AF630;
constexpr std::uintptr_t kPlannerVtableRva = 0x41205F0;
constexpr std::uintptr_t kCanSelectRva = 0x10AF6A0;
constexpr std::size_t kRowStride = 0x38;

bool Add(std::uintptr_t base, std::size_t offset,
         std::uintptr_t &result) noexcept {
  if (base == 0 || offset > (std::numeric_limits<std::uintptr_t>::max)() - base)
    return false;
  result = base + offset;
  return true;
}

template <typename T>
bool ReadAt(const ActivityPlannerDiagEnvironmentV1 &environment,
            std::uintptr_t base, std::size_t offset, T &value) noexcept {
  std::uintptr_t address = 0;
  return environment.read_memory != nullptr && Add(base, offset, address) &&
         environment.read_memory(environment.context, address, &value,
                                 sizeof(value));
}

bool ExactCanSelect(const ActivityPlannerDiagEnvironmentV1 &environment)
    noexcept {
  constexpr std::array<std::uint8_t, 14> expected{
      0x48, 0x89, 0x5C, 0x24, 0x10, 0x55, 0x56,
      0x57, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56};
  std::array<std::uint8_t, expected.size()> actual{};
  return ReadAt(environment, environment.module_base,
                IsActivityPlanner12002V1(environment) ? 0x11B6F50 : kCanSelectRva,
                actual) &&
         actual == expected;
}

bool ResolvePlanner(const ActivityPlannerDiagEnvironmentV1 &environment,
                    const ActivityPlannerDiagFrameV1 &expected,
                    std::uintptr_t &planner) noexcept {
  if (IsActivityPlanner12002V1(environment)) {
    ActivityPlannerIdentityV1 identity{};
    if (!ResolveActivityPlannerIdentityV1(environment, expected, identity) ||
        identity.stage != 2)
      return false;
    planner = identity.planner;
    return true;
  }
  std::uintptr_t root = 0, idler = 0, gfx = 0, handler = 0;
  std::uintptr_t gfx_vtable = 0, handler_vtable = 0, planner_vtable = 0;
  std::uintptr_t owner = 0;
  std::int32_t stage = -1;
  if (!ReadAt(environment, environment.module_base,
              ActivityPlannerRvaV1(environment, kRootRva), root) ||
      root == 0 || !ReadAt(environment, root, 0x10, idler) || idler == 0 ||
      environment.rtti_cast == nullptr)
    return false;
  gfx = environment.rtti_cast(
      environment.context, idler,
      environment.module_base + ActivityPlannerRvaV1(environment, kIdlerSourceTypeRva),
      environment.module_base + ActivityPlannerRvaV1(environment, kIdlerGfxTypeRva));
  return gfx != 0 && ReadAt(environment, gfx, 0, gfx_vtable) &&
         gfx_vtable == environment.module_base + ActivityPlannerRvaV1(environment, kGfxVtableRva) &&
         ReadAt(environment, gfx, 0x88, handler) && handler != 0 &&
         ReadAt(environment, handler, 0, handler_vtable) &&
         handler_vtable == environment.module_base + ActivityPlannerRvaV1(environment, kHandlerVtableRva) &&
         ReadAt(environment, handler, 0x3C0, planner) && planner != 0 &&
         ReadAt(environment, planner, 0, planner_vtable) &&
         planner_vtable == environment.module_base + ActivityPlannerRvaV1(environment, kPlannerVtableRva) &&
         ReadAt(environment, planner, 0xD0, owner) && owner == handler &&
         ReadAt(environment, planner,
                ActivityPlannerObjectOffsetV1(environment, 0x1AB0), stage) && stage == 2;
}

struct NativeRows {
  std::uintptr_t data = 0;
  std::int32_t count = 0;
  std::uintptr_t active = 0;
  std::uintptr_t activity = 0;
  std::uint8_t single_location = 0;
  std::int32_t previous_stage = -1;
  std::array<ActivityStage2LocationRowV1, kActivityStage2MaximumRowsV1> rows{};
  friend bool operator==(const NativeRows &, const NativeRows &) = default;
};

bool ReadRows(const ActivityPlannerDiagEnvironmentV1 &environment,
              std::uintptr_t planner, NativeRows &output) noexcept {
  if (!ReadAt(environment, planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1578), output.data) ||
      !ReadAt(environment, planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1584), output.count) ||
      output.count < 1 ||
      output.count > static_cast<std::int32_t>(kActivityStage2MaximumRowsV1) ||
      output.data == 0 ||
      !ReadAt(environment, planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1AC0), output.active) ||
      !ReadAt(environment, planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1530), output.activity) ||
      output.activity == 0 ||
      !ReadAt(environment, output.activity,
              ActivityPlannerTypeOffsetV1(environment, 0x3C75),
              output.single_location) ||
      !ReadAt(environment, planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1AB4), output.previous_stage))
    return false;
  for (std::int32_t index = 0; index < output.count; ++index) {
    std::uintptr_t row = 0, phase = 0;
    auto &item = output.rows[static_cast<std::size_t>(index)];
    if (!Add(output.data, static_cast<std::size_t>(index) * kRowStride,
             row) ||
        !ReadAt(environment, row, 0, phase) ||
        !ReadAt(environment, row, 8, item.province_id))
      return false;
    item.index = index;
    item.is_active = output.active == row;
    if (phase != 0) {
      // Native FindAutoRow tests one byte; the DTO keeps its existing integer
      // representation without reading unrelated adjacent fields.
      std::uint8_t active = 0;
      if (!ReadAt(environment, phase,
                    IsActivityPlanner12002V1(environment) ? 0x1160 : 0x12D0,
                    item.phase_kind) ||
          !ReadAt(environment, phase,
                    IsActivityPlanner12002V1(environment) ? 0x69C : 0x70C,
                    active))
        return false;
      item.phase_active_raw = active;
    }
    item.phase_present = phase != 0;
  }
  return true;
}

} // namespace

ActivityStage2LocationReadResultV1 ReadActivityStage2LocationV1(
    const ActivityStage2LocationEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected,
    std::span<const std::int32_t> candidate_province_ids) noexcept {
  ActivityStage2LocationReadResultV1 result{};
  const auto &diagnostic = environment.option.diagnostic;
  if (!diagnostic.enabled || diagnostic.module_base == 0 ||
      (diagnostic.admitted_executable_sha256 !=
           kActivityPlannerDiagExeSha256V1 &&
       !IsActivityPlanner12002V1(diagnostic)) ||
      !ExactCanSelect(diagnostic))
    return result;
  if (diagnostic.read_frame == nullptr ||
      environment.resolve_province == nullptr ||
      environment.can_select_destination == nullptr) {
    result.status = ActivityStage2LocationReadStatusV1::callback_missing;
    return result;
  }
  if (candidate_province_ids.empty() ||
      candidate_province_ids.size() > kActivityStage2MaximumCandidatesV1) {
    result.status = ActivityStage2LocationReadStatusV1::candidate_invalid;
    return result;
  }
  for (std::size_t i = 0; i < candidate_province_ids.size(); ++i) {
    if (candidate_province_ids[i] < 1) {
      result.status = ActivityStage2LocationReadStatusV1::candidate_invalid;
      return result;
    }
    for (std::size_t j = 0; j < i; ++j) {
      if (candidate_province_ids[j] == candidate_province_ids[i]) {
        result.status = ActivityStage2LocationReadStatusV1::candidate_invalid;
        return result;
      }
    }
  }
  ActivityPlannerDiagFrameV1 frame{};
  if (!diagnostic.read_frame(diagnostic.context, frame) || frame != expected) {
    result.status = ActivityStage2LocationReadStatusV1::frame_changed;
    return result;
  }
  result.gate = ReadActivityStage2GateV1(environment.option, expected);
  if (result.gate.status != ActivityStage2GateReadStatusV1::observed) {
    result.status = ActivityStage2LocationReadStatusV1::gate_unavailable;
    return result;
  }
  std::uintptr_t planner = 0;
  NativeRows first{};
  if (!ResolvePlanner(diagnostic, expected, planner)) {
    result.status = ActivityStage2LocationReadStatusV1::planner_unavailable;
    return result;
  }
  if (!ReadRows(diagnostic, planner, first)) {
    result.status = ActivityStage2LocationReadStatusV1::row_unavailable;
    return result;
  }
  std::int32_t active_index = -1;
  for (std::int32_t i = 0; i < first.count; ++i) {
    if (first.rows[static_cast<std::size_t>(i)].is_active) active_index = i;
  }
  if (active_index < 0) {
    result.status = ActivityStage2LocationReadStatusV1::active_row_invalid;
    return result;
  }
  result.rows = first.rows;
  result.row_count = static_cast<std::uint16_t>(first.count);
  result.active_row_index = active_index;
  result.activity_single_location_flag = first.single_location != 0;
  result.previous_planning_stage = first.previous_stage;
  for (const auto province_id : candidate_province_ids) {
    std::uintptr_t province = 0;
    if (!environment.resolve_province(diagnostic.context, province_id,
                                      province) || province == 0) {
      result.status = ActivityStage2LocationReadStatusV1::province_unavailable;
      return result;
    }
    bool selectable = false;
    if (!environment.can_select_destination(diagnostic.context, planner,
                                            province, selectable)) {
      result.status =
          ActivityStage2LocationReadStatusV1::native_evaluation_failed;
      return result;
    }
    result.candidates[result.candidate_count++] = {province_id, selectable};
  }
  std::uintptr_t final_planner = 0;
  NativeRows final{};
  const auto final_option = ReadActivityStage2OptionV1(environment.option,
                                                       expected);
  if (!diagnostic.read_frame(diagnostic.context, frame) || frame != expected ||
      final_option.status != ActivityStage2OptionReadStatusV1::observed ||
      !final_option.generic_feast_selected ||
      final_option.option_key != result.gate.selected_option.option_key ||
      final_option.option_key_size !=
          result.gate.selected_option.option_key_size ||
      !ResolvePlanner(diagnostic, expected, final_planner) || final_planner != planner ||
      !ReadRows(diagnostic, final_planner, final) || final != first) {
    result.status = ActivityStage2LocationReadStatusV1::frame_changed;
    return result;
  }
  result.status = ActivityStage2LocationReadStatusV1::observed;
  return result;
}

std::string_view ActivityStage2LocationReadStatusKeyV1(
    ActivityStage2LocationReadStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage2LocationReadStatusV1::observed: return "observed";
  case ActivityStage2LocationReadStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityStage2LocationReadStatusV1::callback_missing:
    return "callback_missing";
  case ActivityStage2LocationReadStatusV1::gate_unavailable:
    return "gate_unavailable";
  case ActivityStage2LocationReadStatusV1::planner_unavailable:
    return "planner_unavailable";
  case ActivityStage2LocationReadStatusV1::row_unavailable:
    return "row_unavailable";
  case ActivityStage2LocationReadStatusV1::active_row_invalid:
    return "active_row_invalid";
  case ActivityStage2LocationReadStatusV1::candidate_invalid:
    return "candidate_invalid";
  case ActivityStage2LocationReadStatusV1::province_unavailable:
    return "province_unavailable";
  case ActivityStage2LocationReadStatusV1::native_evaluation_failed:
    return "native_evaluation_failed";
  case ActivityStage2LocationReadStatusV1::frame_changed:
    return "frame_changed";
  }
  return "unknown";
}

} // namespace xar::bridge
