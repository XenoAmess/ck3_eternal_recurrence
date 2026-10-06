#include "xar_bridge/activity_stage2_gate_read_v1.hpp"
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
constexpr std::uintptr_t kStage2GateBranchRva = 0x10B0E0F;
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

bool ExactStage2Branch(const ActivityPlannerDiagEnvironmentV1 &environment)
    noexcept {
  constexpr std::array<std::uint8_t, 14> expected{
      0x48, 0x8B, 0x89, 0x78, 0x15, 0x00, 0x00,
      0x49, 0x63, 0x80, 0x84, 0x15, 0x00, 0x00};
  std::array<std::uint8_t, expected.size()> actual{};
  constexpr std::array<std::uint8_t, 14> expected_12002{
      0x48, 0x8B, 0x89, 0xB0, 0x15, 0x00, 0x00,
      0x49, 0x63, 0x80, 0xBC, 0x15, 0x00, 0x00};
  const bool current = IsActivityPlannerCrozierBuildV1(environment);
  return ReadAt(environment, environment.module_base,
                Activity12004RvaV1(environment.admitted_executable_sha256,
                                   current ? 0x11B86DF : kStage2GateBranchRva), actual) &&
         actual == (current ? expected_12002 : expected);
}

bool ResolvePlanner(const ActivityPlannerDiagEnvironmentV1 &environment,
                    const ActivityPlannerDiagFrameV1 &expected,
                    std::uintptr_t &planner) noexcept {
  if (IsActivityPlannerCrozierBuildV1(environment)) {
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

struct RowSnapshot {
  std::uintptr_t data = 0;
  std::int32_t count = 0;
  std::array<std::uint32_t, kActivityStage2MaximumRowsV1> values{};

  friend bool operator==(const RowSnapshot &, const RowSnapshot &) = default;
};

bool ReadRows(const ActivityPlannerDiagEnvironmentV1 &environment,
              std::uintptr_t planner, RowSnapshot &output) noexcept {
  if (!ReadAt(environment, planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1578), output.data) ||
      !ReadAt(environment, planner,
              ActivityPlannerObjectOffsetV1(environment, 0x1584), output.count) ||
      output.count < 0 ||
      output.count > static_cast<std::int32_t>(kActivityStage2MaximumRowsV1) ||
      (output.count != 0 && output.data == 0))
    return false;
  for (std::int32_t index = 0; index < output.count; ++index) {
    if (!ReadAt(environment, output.data,
                static_cast<std::size_t>(index) * kRowStride + 0x08,
                output.values[static_cast<std::size_t>(index)]))
      return false;
  }
  return true;
}

} // namespace

ActivityStage2GateReadResultV1 ReadActivityStage2GateV1(
    const ActivityStage1OptionEnvironmentV1 &environment,
    const ActivityPlannerDiagFrameV1 &expected) noexcept {
  ActivityStage2GateReadResultV1 result{};
  const auto &diagnostic = environment.diagnostic;
  if (!diagnostic.enabled || diagnostic.module_base == 0 ||
      (diagnostic.admitted_executable_sha256 !=
           kActivityPlannerDiagExeSha256V1 &&
       !IsActivityPlannerCrozierBuildV1(diagnostic)) ||
      !ExactStage2Branch(diagnostic))
    return result;
  if (environment.can_progress == nullptr || diagnostic.read_frame == nullptr) {
    result.status = ActivityStage2GateReadStatusV1::callback_missing;
    return result;
  }
  ActivityPlannerDiagFrameV1 first_frame{};
  if (!diagnostic.read_frame(diagnostic.context, first_frame) ||
      first_frame != expected) {
    result.status = ActivityStage2GateReadStatusV1::frame_changed;
    return result;
  }
  result.selected_option = ReadActivityStage2OptionV1(environment, expected);
  if (result.selected_option.status !=
      ActivityStage2OptionReadStatusV1::observed) {
    switch (result.selected_option.status) {
    case ActivityStage2OptionReadStatusV1::exact_build_rejected:
      result.status = ActivityStage2GateReadStatusV1::exact_build_rejected;
      break;
    case ActivityStage2OptionReadStatusV1::not_feast_stage_two:
      result.status = ActivityStage2GateReadStatusV1::not_feast_stage_two;
      break;
    case ActivityStage2OptionReadStatusV1::frame_changed:
      result.status = ActivityStage2GateReadStatusV1::frame_changed;
      break;
    default:
      result.status = ActivityStage2GateReadStatusV1::option_unavailable;
      break;
    }
    return result;
  }
  if (!result.selected_option.generic_feast_selected) {
    result.status =
        ActivityStage2GateReadStatusV1::selected_option_not_generic;
    return result;
  }
  std::uintptr_t first_planner = 0;
  if (!ResolvePlanner(diagnostic, expected, first_planner)) {
    result.status = ActivityStage2GateReadStatusV1::planner_identity_mismatch;
    return result;
  }
  RowSnapshot first_rows{};
  if (!ReadRows(diagnostic, first_planner, first_rows)) {
    result.status = ActivityStage2GateReadStatusV1::row_vector_unavailable;
    return result;
  }
  result.configuration_row_count = first_rows.count;
  for (std::int32_t index = 0; index < first_rows.count; ++index) {
    const auto value = first_rows.values[static_cast<std::size_t>(index)];
    if (value != 0) continue;
    result.failed_rows[result.failed_row_count++] = {index, value};
  }
  if (!environment.can_progress(diagnostic.context, first_planner,
                                result.can_progress_stage2)) {
    result.status = ActivityStage2GateReadStatusV1::native_evaluation_failed;
    return result;
  }
  std::uintptr_t final_planner = 0;
  RowSnapshot final_rows{};
  const auto final_option = ReadActivityStage2OptionV1(environment, expected);
  if (final_option.status != ActivityStage2OptionReadStatusV1::observed ||
      !final_option.generic_feast_selected ||
      final_option.option_key_size != result.selected_option.option_key_size ||
      final_option.option_key != result.selected_option.option_key ||
      !ResolvePlanner(diagnostic, expected, final_planner) ||
      final_planner != first_planner ||
      !ReadRows(diagnostic, final_planner, final_rows) ||
      final_rows != first_rows) {
    result.status = ActivityStage2GateReadStatusV1::frame_changed;
    return result;
  }
  if (result.can_progress_stage2 != (result.failed_row_count == 0)) {
    result.status = ActivityStage2GateReadStatusV1::native_gate_mismatch;
    return result;
  }
  result.generic_feast_stage2_advance_ready = result.can_progress_stage2;
  result.status = ActivityStage2GateReadStatusV1::observed;
  return result;
}

std::string_view ActivityStage2GateReadStatusKeyV1(
    ActivityStage2GateReadStatusV1 status) noexcept {
  switch (status) {
  case ActivityStage2GateReadStatusV1::observed: return "observed";
  case ActivityStage2GateReadStatusV1::exact_build_rejected:
    return "exact_build_rejected";
  case ActivityStage2GateReadStatusV1::callback_missing:
    return "callback_missing";
  case ActivityStage2GateReadStatusV1::option_unavailable:
    return "option_unavailable";
  case ActivityStage2GateReadStatusV1::not_feast_stage_two:
    return "not_feast_stage_two";
  case ActivityStage2GateReadStatusV1::selected_option_not_generic:
    return "selected_option_not_generic";
  case ActivityStage2GateReadStatusV1::planner_identity_mismatch:
    return "planner_identity_mismatch";
  case ActivityStage2GateReadStatusV1::row_vector_unavailable:
    return "row_vector_unavailable";
  case ActivityStage2GateReadStatusV1::native_evaluation_failed:
    return "native_evaluation_failed";
  case ActivityStage2GateReadStatusV1::native_gate_mismatch:
    return "native_gate_mismatch";
  case ActivityStage2GateReadStatusV1::frame_changed:
    return "frame_changed";
  }
  return "unknown";
}

} // namespace xar::bridge
